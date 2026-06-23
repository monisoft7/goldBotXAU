from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

from src.research import xauusd_executable_candidate_train_validation as v83
from src.research.xauusd_executable_candidate_train_validation import (
    BLOCKED,
    CANDIDATE_ID,
    EVALUATION_VERSION,
    FAILED,
    FIXED_GATES,
    NEXT_IF_FAILED,
    NEXT_IF_PASSED,
    PASSED,
    Candle,
    build_xauusd_executable_candidate_train_validation_v0_83,
)

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_REPORT_FIELDS = {
    "evaluation_version",
    "evaluation_status",
    "candidate_id",
    "source_design_version",
    "train_validation_only",
    "oos_used",
    "oos_allowed_now",
    "train_metrics",
    "validation_metrics",
    "combined_train_validation_metrics",
    "train_trade_count",
    "validation_trade_count",
    "train_win_rate",
    "validation_win_rate",
    "train_profit_factor",
    "validation_profit_factor",
    "train_expectancy_R",
    "validation_expectancy_R",
    "train_max_drawdown_R",
    "validation_max_drawdown_R",
    "train_max_consecutive_losses",
    "validation_max_consecutive_losses",
    "cost_sensitivity_summary",
    "gate_results",
    "passed_all_train_validation_gates",
    "candidate_promotable_to_oos_review",
    "next_step_if_passed",
    "next_step_if_failed",
    "recommended_next_step",
    "failure_reasons",
    "trade_records_output_path_or_null",
    "trade_recommendation_output",
    "live_allowed",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "executable_order_request_created",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "existing_strategy_rules_modified",
    "rejected_candidates_modified",
    "v0_26_traded_as_is",
    "external_api_called",
    "external_data_downloaded",
    "dataset_file_created",
    "market_csv_created",
    "data_csv_touched",
}


@lru_cache(maxsize=1)
def _real_report() -> dict:
    return build_xauusd_executable_candidate_train_validation_v0_83(
        data_dir=ROOT / "data",
        manifest_path=ROOT / "reports" / "xauusd_dataset_manifest_v0_5.json",
        source_design_path=ROOT / "reports" / "xauusd_executable_fixed_rule_candidate_design_v0_82.json",
    )


def test_real_evaluation_identity_and_required_fields() -> None:
    report = _real_report()

    assert report["evaluation_version"] == EVALUATION_VERSION
    assert report["evaluation_status"] in {PASSED, FAILED, BLOCKED}
    assert report["candidate_id"] == CANDIDATE_ID
    assert report["source_design_version"] == "v0_82"
    assert REQUIRED_REPORT_FIELDS.issubset(report)
    json.dumps(report)


def test_evaluation_uses_train_validation_only_and_keeps_oos_closed() -> None:
    report = _real_report()

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["oos_allowed_now"] is False
    assert report["oos_rows_read"] is False
    assert report["oos_rows_counted"] == 0
    for counts in report["split_candle_counts"].values():
        assert "excluded_oos" not in counts
        assert counts["train"] > 0
        assert counts["validation"] > 0
    for split_range in report["data_ranges_used"].values():
        assert split_range["end"] < "2026-01-01T00:00:00"


def test_candidate_rules_are_preserved_and_no_search_or_retune_occurs() -> None:
    design_path = ROOT / "reports" / "xauusd_executable_fixed_rule_candidate_design_v0_82.json"
    before = design_path.read_text(encoding="utf-8")
    report = _real_report()
    after = design_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_rules_preserved"] is True
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["existing_strategy_rules_modified"] is False
    assert report["rejected_candidates_modified"] is False
    assert report["v0_26_traded_as_is"] is False


def test_long_and_short_side_mapping_are_explicit() -> None:
    report = _real_report()

    assert report["explicit_side_mapping"]["long"] == "bullish_displacement_plus_controlled_retest_hold"
    assert report["explicit_side_mapping"]["short"] == "bearish_displacement_plus_controlled_retest_hold"


def test_gate_calculations_are_deterministic_and_decision_follows_fixed_gates() -> None:
    first = _real_report()
    second = _real_report()

    assert first["gate_results"] == second["gate_results"]
    assert first["train_metrics"] == second["train_metrics"]
    assert first["validation_metrics"] == second["validation_metrics"]
    all_gates_passed = all(result["passed"] is True for result in first["gate_results"].values())
    assert first["passed_all_train_validation_gates"] is all_gates_passed
    assert first["evaluation_status"] == (PASSED if all_gates_passed else FAILED)
    assert first["candidate_promotable_to_oos_review"] is all_gates_passed
    assert first["recommended_next_step"] == (NEXT_IF_PASSED if all_gates_passed else NEXT_IF_FAILED)
    assert first["fixed_gate"] == FIXED_GATES


def test_no_trade_recommendation_execution_external_or_data_csv_side_effects() -> None:
    data_csv_mtimes = {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}
    report = _real_report()

    assert report["trade_recommendation_output"] is False
    assert report["live_allowed"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["executable_order_request_created"] is False
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["data_csv_touched"] is False
    assert {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")} == data_csv_mtimes


def test_report_metrics_and_cost_sensitivity_are_present() -> None:
    report = _real_report()

    assert report["train_trade_count"] == report["train_metrics"]["trades"]
    assert report["validation_trade_count"] == report["validation_metrics"]["trades"]
    assert report["train_win_rate"] == report["train_metrics"]["win_rate"]
    assert report["validation_win_rate"] == report["validation_metrics"]["win_rate"]
    assert report["cost_sensitivity_summary"]["cost_sensitivity_required"] is True
    assert "cost_sensitivity_required" in report["gate_results"]
    assert report["trade_records_output_path_or_null"] is None


def test_one_position_no_overlap_behavior_is_enforced_on_synthetic_rows() -> None:
    start = datetime(2025, 1, 2, 8, 0)
    m15 = []
    price = 100.0
    for index in range(16):
        timestamp = start + timedelta(minutes=15 * index)
        m15.append(Candle(timestamp, "train", price, price + 0.2, price - 0.2, price, 1.0))
    first_displacement_time = datetime(2025, 1, 2, 12, 30)
    m15.append(Candle(first_displacement_time, "train", 100.0, 101.4, 99.9, 101.2, 1.0))
    m15.append(Candle(first_displacement_time + timedelta(minutes=15), "train", 101.2, 102.8, 101.0, 102.6, 1.0))

    m5 = []
    for index in range(36):
        timestamp = first_displacement_time + timedelta(minutes=5 * (index + 1))
        if index == 0:
            m5.append(Candle(timestamp, "train", 100.2, 100.7, 100.0, 100.5, 1.0))
        else:
            m5.append(Candle(timestamp, "train", 100.5, 101.0, 100.3, 100.6, 1.0))

    trades = v83._evaluate_fixed_candidate(m15, m5, cost_r_per_trade=0.03)

    assert len(trades) == 1
    assert trades[0].entry_timestamp == "2025-01-02T12:35:00"
    assert trades[0].exit_timestamp > "2025-01-02T12:45:00"
