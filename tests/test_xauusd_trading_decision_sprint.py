from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.research.xauusd_trading_decision_sprint import (
    BLOCKED,
    CLOSE_NO_VARIANT,
    FAILED,
    NEXT_IF_FAILED,
    NEXT_IF_PASSED,
    NY_CORE_ONLY,
    PASSED,
    SPRINT_VERSION,
    build_xauusd_trading_decision_sprint_v0_84,
    select_rescue_decision_from_train_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _real_report() -> dict:
    return build_xauusd_trading_decision_sprint_v0_84(root=ROOT)


def test_report_identity_and_hard_decision_fields() -> None:
    report = _real_report()

    assert report["sprint_version"] == SPRINT_VERSION
    assert report["sprint_status"] in {PASSED, FAILED, BLOCKED}
    assert report["source_candidate_id"] == "xauusd_ny_displacement_retest_executable_v0_82"
    assert report["source_design_version"] == "v0_82"
    assert report["source_evaluation_version"] == "v0_83"
    assert report["baseline_v0_83_status"] == "executable_candidate_train_validation_failed"
    assert report["selected_rescue_decision"] in {NY_CORE_ONLY, CLOSE_NO_VARIANT}
    assert report["recommended_next_step"] in {NEXT_IF_PASSED, NEXT_IF_FAILED, "v0_85_repair_trade_diagnostics_then_decide"}
    json.dumps(report)


def test_train_only_diagnostics_choose_rescue_without_validation() -> None:
    report = _real_report()

    assert report["train_only_diagnostics_available"] is True
    assert report["trade_detail_available"] is True
    assert report["validation_used_for_rescue_selection"] is False
    assert report["selected_rescue_decision"] == NY_CORE_ONLY
    assert report["rescue_variant_created"] is True
    assert report["rescue_variant_type_or_null"] == NY_CORE_ONLY
    assert "validation" not in report["selected_rescue_reason"].lower()


def test_at_most_one_rescue_variant_is_evaluated_and_gates_are_fixed() -> None:
    report = _real_report()

    assert report["rescue_variant_evaluated_count"] <= 1
    assert report["gate_results"]["minimum_train_trade_count_gate"]["threshold"] == 60
    assert report["gate_results"]["minimum_validation_trade_count_gate"]["threshold"] == 25
    assert report["gate_results"]["validation_profit_factor_gate"]["threshold"] == 1.25
    assert report["gate_results"]["validation_expectancy_gate_R"]["threshold"] == 0.05
    assert report["gate_results"]["train_max_drawdown_gate_R"]["threshold"] == 8.0
    assert report["gate_results"]["train_max_consecutive_loss_gate"]["threshold"] == 5
    assert report["do_not_loosen_gates"] is True


def test_rescue_variant_fails_fixed_gates_and_closes_candidate() -> None:
    report = _real_report()

    assert report["passed_all_train_validation_gates"] is False
    assert report["candidate_promotable_to_oos_review"] is False
    assert report["candidate_closed"] is True
    assert report["sprint_status"] == FAILED
    assert report["recommended_next_step"] == NEXT_IF_FAILED
    assert "validation_profit_factor_gate" in report["failure_reasons"]


def test_no_oos_demo_live_order_recommendation_or_search_side_effects() -> None:
    before_mtimes = {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}
    report = _real_report()
    after_mtimes = {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["oos_allowed_now"] is False
    assert report["demo_allowed_now"] is False
    assert report["live_allowed_now"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["executable_order_request_created"] is False
    assert report["trade_recommendation_output"] is False
    assert report["user_facing_buy_sell_signal_output"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["broad_search_performed"] is False
    assert report["data_csv_touched"] is False
    assert before_mtimes == after_mtimes


def test_candidate_identity_and_rejected_candidate_safety_are_preserved() -> None:
    report = _real_report()

    assert report["source_candidate_id"] == "xauusd_ny_displacement_retest_executable_v0_82"
    assert report["existing_strategy_rules_modified"] is False
    assert report["rejected_candidates_modified"] is False
    assert report["v0_26_traded_as_is"] is False
    assert report["do_not_retune"] is True


def test_selector_closes_candidate_when_no_clear_train_only_variant_exists() -> None:
    diagnostics = {
        "side": {
            "long": {"expectancy_R": 0.1, "loss_R_share": 0.5, "max_consecutive_losses": 3},
            "short": {"expectancy_R": 0.1, "loss_R_share": 0.5, "max_consecutive_losses": 3},
        },
        "session": {
            "worst_drawdown_bucket": "ny_core_1300_1600",
            "edge_combined": {"expectancy_R": 0.1},
            "ny_core_1300_1600": {"expectancy_R": 0.1},
        },
        "overtrading": {"clear_reentry_cluster_damage": False, "cluster_trade_loss_R": 0.0},
    }

    assert select_rescue_decision_from_train_diagnostics(diagnostics) == CLOSE_NO_VARIANT
