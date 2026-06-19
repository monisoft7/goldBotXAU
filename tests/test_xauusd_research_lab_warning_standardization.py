from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_research_lab_warning_standardization import (
    BLOCKED_MISSING_V0_58,
    COMPLETED,
    STANDARDIZATION_VERSION,
    build_xauusd_research_lab_warning_standardization_v0_59,
)

ROOT = Path(__file__).resolve().parents[1]


def _build_report() -> dict[str, object]:
    return build_xauusd_research_lab_warning_standardization_v0_59(root=ROOT)


def test_v0_58_report_is_required(tmp_path: Path) -> None:
    report = build_xauusd_research_lab_warning_standardization_v0_59(
        source_report_path=tmp_path / "missing_v0_58.json",
        root=ROOT,
    )

    assert report["standardization_status"] == BLOCKED_MISSING_V0_58
    assert report["blockers"] == ["missing_v0_58_integrity_report"]


def test_standardization_report_completed_from_checked_in_v0_58() -> None:
    report = _build_report()

    assert report["standardization_version"] == STANDARDIZATION_VERSION
    assert report["standardization_status"] == COMPLETED
    assert report["source_integrity_audit_version"] == "v0_58"
    assert report["source_integrity_decision"] == "lab_integrity_passed_with_warnings"
    assert report["critical_findings_from_v0_58"] == []
    assert report["blockers"] == []


def test_cost_policy_is_documented() -> None:
    report = _build_report()

    assert report["cost_policy_documented"] is True
    assert report["cost_policy"]["existing_tools_apply_costs_consistently"] is False
    assert report["cost_policy"]["cost_fields_missing_or_inconsistent_warning"] is True
    assert report["cost_policy"]["historical_metrics_recomputed"] is False


def test_timestamp_session_policy_is_documented() -> None:
    report = _build_report()

    assert report["timestamp_policy_documented"] is True
    assert report["timestamp_session_policy"]["timestamp_basis"] == "unknown_or_broker_server_time"
    assert report["timestamp_session_policy"]["broker_timezone_provably_utc"] is False
    assert report["timestamp_session_policy"]["future_session_research_must_state_timestamp_basis"] is True
    assert report["timestamp_session_policy"]["timestamp_shift_performed"] is False


def test_gap_classification_policy_is_documented() -> None:
    report = _build_report()
    policy = report["gap_classification_policy"]

    assert report["gap_classification_policy_documented"] is True
    assert policy["classification_enums"] == [
        "expected_weekend_or_market_closure_gap",
        "unexpected_intraday_gap",
        "zero_range_candle_warning",
        "duplicate_or_non_monotonic_error",
    ]
    assert policy["duplicate_or_non_monotonic_timestamps_are_critical"] is True
    assert policy["expected_weekend_or_market_closure_gaps_are_warnings"] is True
    assert policy["zero_range_candles_are_warnings_unless_excessive"] is True
    assert policy["data_deleted_or_altered"] is False
    assert policy["classifications_by_timeframe"]["M5"]["duplicate_or_non_monotonic_error"] is False


def test_gate_policy_and_low_frequency_risk_are_documented() -> None:
    report = _build_report()

    assert report["gate_policy_documented"] is True
    assert report["low_frequency_false_negative_risk_documented"] is True
    assert report["gate_policy"]["validation_trade_minimum"] == 50
    assert report["gate_policy"]["validation_trade_minimum_lowered"] is False
    assert report["gate_policy"]["gates_lowered"] is False


def test_warnings_addressed_include_v0_58_warning_classes() -> None:
    report = _build_report()

    warnings = set(report["warnings_addressed"])
    assert "costs_not_applied_consistently_across_all_train_validation_tools" in warnings
    assert "broker_timestamp_basis_not_explicitly_encoded_in_csv" in warnings
    assert "fixed_validation_trade_floor_may_be_mismatched_to_low_frequency_strategy_families" in warnings
    assert "m5_missing_candle_gaps_detected" in warnings
    assert "m5_zero_or_negative_ranges_detected" in warnings


def test_gates_metrics_and_research_safety_are_unchanged() -> None:
    report = _build_report()

    assert report["strategy_metrics_changed"] is False
    assert report["gates_lowered"] is False
    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False


def test_execution_and_live_safety_remain_blocked() -> None:
    report = _build_report()

    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["safety"]["execution_queue_created"] is False
    assert report["safety"]["scheduler_created"] is False
    assert report["safety"]["auto_execute_order"] is False


def test_data_csv_not_staged_or_committed() -> None:
    report = _build_report()
    completed = subprocess.run(
        ["git", "status", "--short", "--", "data/*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert report["data_csv_added_to_git"] is False
    assert completed.stdout.strip() == ""


def test_cli_writes_required_report(tmp_path: Path) -> None:
    output = tmp_path / "xauusd_research_lab_warning_standardization_v0_59.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "standardize_xauusd_research_lab_warnings_v0_59.py"),
            "--json",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["standardization_status"] == COMPLETED
    assert output_report["standardization_version"] == STANDARDIZATION_VERSION
