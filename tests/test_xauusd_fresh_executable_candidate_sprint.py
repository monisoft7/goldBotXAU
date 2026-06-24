from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.research import xauusd_executable_candidate_train_validation as v83
from src.research.xauusd_fresh_executable_candidate_sprint import (
    BLOCKED,
    FAILED,
    FIXED_GATES,
    MAX_CANDIDATE_COUNT_ALLOWED,
    NEXT_IF_BLOCKED,
    NEXT_IF_FAILED,
    NEXT_IF_PASSED,
    PASSED,
    SOURCE_CLOSED_CANDIDATE_ID,
    SPRINT_VERSION,
    build_xauusd_fresh_executable_candidate_sprint_v0_85,
)

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_CANDIDATES = [
    "xauusd_ny_opening_range_breakout_executable_v0_85_a",
    "xauusd_london_to_ny_liquidity_sweep_reversal_executable_v0_85_b",
    "xauusd_impulse_pullback_continuation_executable_v0_85_c",
]

REQUIRED_REPORT_FIELDS = {
    "sprint_version",
    "sprint_status",
    "source_closed_candidate_id",
    "source_closure_version",
    "candidates_evaluated",
    "candidate_count",
    "max_candidate_count_allowed",
    "train_validation_only",
    "oos_used",
    "candidate_results",
    "passing_candidates",
    "failing_candidates",
    "selected_candidate_id_or_null",
    "selected_candidate_reason_or_null",
    "gate_results_by_candidate",
    "train_metrics_by_candidate",
    "validation_metrics_by_candidate",
    "cost_sensitivity_summary_by_candidate",
    "trade_count_by_candidate",
    "failure_reasons_by_candidate",
    "passed_all_train_validation_gates",
    "candidate_promotable_to_oos_review",
    "recommended_next_step",
    "rejected_next_steps",
    "no_oos_reason_if_not_passed",
    "no_demo_reason",
    "no_live_reason",
    "demo_execution_allowed",
    "live_allowed",
    "order_send_called",
    "order_check_called",
    "executable_order_request_created",
    "trade_recommendation_output",
    "user_facing_buy_sell_signal_output",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "broad_search_performed",
    "validation_used_for_parameter_choice",
    "existing_strategy_rules_modified",
    "rejected_candidates_modified",
    "v0_26_traded_as_is",
    "closed_v0_82_rescued_again",
    "external_api_called",
    "external_data_downloaded",
    "dataset_file_created",
    "market_csv_created",
    "data_csv_touched",
}


@lru_cache(maxsize=1)
def _real_report() -> dict:
    return build_xauusd_fresh_executable_candidate_sprint_v0_85(
        data_dir=ROOT / "data",
        manifest_path=ROOT / "reports" / "xauusd_dataset_manifest_v0_5.json",
        source_closure_path=ROOT / "reports" / "xauusd_trading_decision_sprint_v0_84.json",
    )


def test_real_sprint_identity_and_required_fields() -> None:
    report = _real_report()

    assert report["sprint_version"] == SPRINT_VERSION
    assert report["sprint_status"] in {PASSED, FAILED, BLOCKED}
    assert report["source_closed_candidate_id"] == SOURCE_CLOSED_CANDIDATE_ID
    assert report["source_closure_version"] == "v0_84"
    assert REQUIRED_REPORT_FIELDS.issubset(report)
    json.dumps(report)


def test_exactly_three_fresh_candidates_and_no_more_are_evaluated() -> None:
    report = _real_report()

    assert report["max_candidate_count_allowed"] == MAX_CANDIDATE_COUNT_ALLOWED == 3
    assert report["candidate_count"] == 3
    assert report["candidates_evaluated"] == EXPECTED_CANDIDATES
    assert set(report["candidate_results"]) == set(EXPECTED_CANDIDATES)
    assert SOURCE_CLOSED_CANDIDATE_ID not in report["candidate_results"]


def test_train_validation_only_and_oos_remains_closed() -> None:
    report = _real_report()

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["oos_allowed_now"] is False
    assert report["oos_rows_read"] is False
    assert report["oos_rows_counted"] == 0
    for split_range in report["data_ranges_used"].values():
        assert split_range["end"] < "2026-01-01T00:00:00"


def test_each_candidate_has_explicit_side_mapping_and_fixed_rules() -> None:
    report = _real_report()

    for definition in report["candidate_definitions"]:
        mapping = definition["explicit_side_mapping"]
        assert definition["one_sided_by_design"] is False
        assert definition["fully_fixed_before_evaluation"] is True
        assert mapping["long"]
        assert mapping["short"]
        assert definition["fixed_rules"]["one_position_at_a_time"] is True
        assert definition["fixed_rules"]["no_overlapping_trades"] is True
        assert definition["fixed_rules"]["numeric_threshold_search"] is False
        assert definition["fixed_rules"]["parameter_grid"] is False


def test_no_search_retune_or_validation_based_rule_change_occurs() -> None:
    report = _real_report()

    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["broad_search_performed"] is False
    assert report["validation_used_for_parameter_choice"] is False
    for result in report["candidate_results"].values():
        assert result["fixed_rules"]["numeric_threshold_search"] is False
        assert result["fixed_rules"]["parameter_grid"] is False


def test_v0_82_is_not_rescued_v0_26_not_traded_and_rejected_candidates_untouched() -> None:
    report = _real_report()

    assert report["closed_v0_82_rescued_again"] is False
    assert report["v0_26_traded_as_is"] is False
    assert report["rejected_candidates_modified"] is False
    assert report["existing_strategy_rules_modified"] is False
    assert "rescue_v0_82_again" in report["rejected_next_steps"]
    assert all(SOURCE_CLOSED_CANDIDATE_ID not in candidate_id for candidate_id in report["candidates_evaluated"])


def test_gates_are_unchanged_from_v0_83_and_decision_follows_all_gates() -> None:
    report = _real_report()

    assert FIXED_GATES == v83.FIXED_GATES
    assert report["fixed_gate"] == v83.FIXED_GATES
    for candidate_id, gates in report["gate_results_by_candidate"].items():
        all_gates_passed = all(result["passed"] is True for result in gates.values())
        assert report["candidate_results"][candidate_id]["passed_all_train_validation_gates"] is all_gates_passed
        assert report["candidate_results"][candidate_id]["candidate_promotable_to_oos_review"] is all_gates_passed
        if not all_gates_passed:
            assert candidate_id in report["failing_candidates"]


def test_selected_candidate_exists_only_if_all_gates_pass_and_failed_candidates_are_not_promoted() -> None:
    report = _real_report()
    selected = report["selected_candidate_id_or_null"]

    if selected is None:
        assert report["sprint_status"] == FAILED
        assert report["passing_candidates"] == []
        assert report["passed_all_train_validation_gates"] is False
        assert report["candidate_promotable_to_oos_review"] is False
        assert report["recommended_next_step"] == NEXT_IF_FAILED
        assert "promote_failed_candidate_to_oos" in report["rejected_next_steps"]
    else:
        assert report["sprint_status"] == PASSED
        assert selected in report["passing_candidates"]
        assert report["candidate_results"][selected]["passed_all_train_validation_gates"] is True
        assert report["passed_all_train_validation_gates"] is True
        assert report["candidate_promotable_to_oos_review"] is True
        assert report["recommended_next_step"] == NEXT_IF_PASSED
    assert report["recommended_next_step"] in {NEXT_IF_PASSED, NEXT_IF_FAILED, NEXT_IF_BLOCKED}


def test_no_demo_live_order_recommendation_external_or_data_csv_side_effects() -> None:
    data_csv_mtimes = {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}
    report = _real_report()

    assert report["demo_execution_allowed"] is False
    assert report["live_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["executable_order_request_created"] is False
    assert report["trade_recommendation_output"] is False
    assert report["user_facing_buy_sell_signal_output"] is False
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["data_csv_touched"] is False
    assert {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")} == data_csv_mtimes


def test_report_includes_candidate_metrics_gate_results_and_cost_sensitivity() -> None:
    report = _real_report()

    for candidate_id in EXPECTED_CANDIDATES:
        assert candidate_id in report["train_metrics_by_candidate"]
        assert candidate_id in report["validation_metrics_by_candidate"]
        assert candidate_id in report["gate_results_by_candidate"]
        assert candidate_id in report["cost_sensitivity_summary_by_candidate"]
        assert candidate_id in report["trade_count_by_candidate"]
        assert candidate_id in report["failure_reasons_by_candidate"]
        assert report["trade_count_by_candidate"][candidate_id]["train"] == report["train_metrics_by_candidate"][candidate_id]["trades"]
        assert report["trade_count_by_candidate"][candidate_id]["validation"] == report["validation_metrics_by_candidate"][candidate_id]["trades"]
        assert report["cost_sensitivity_summary_by_candidate"][candidate_id]["cost_sensitivity_required"] is True
        assert "cost_sensitivity_required" in report["gate_results_by_candidate"][candidate_id]
