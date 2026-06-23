from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_external_yield_label_fixture_application import (
    LABELS_REQUESTED,
    SYNTHETIC_SHOCK_THRESHOLD_PERCENTAGE_POINTS,
    apply_external_yield_labels_to_fixture,
    build_label_fixture_application_report,
)

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_REPORT_FIELDS = {
    "application_version",
    "application_status",
    "source_schema_version",
    "source_validator_version",
    "source_ingestion_version",
    "source_alignment_version",
    "source_label_design_version",
    "external_api_called",
    "external_data_downloaded",
    "dataset_file_created",
    "market_csv_created",
    "data_csv_touched",
    "real_xauusd_data_used",
    "synthetic_target_timestamps_used",
    "aligned_dataset_created",
    "label_dataset_exported",
    "labels_requested",
    "labels_applied",
    "labels_not_applicable",
    "label_counts",
    "fixture_record_count",
    "synthetic_target_timestamp_count",
    "no_lookahead_policy_confirmed",
    "backward_asof_only",
    "forward_fill_applied",
    "intraday_timestamp_inferred",
    "synthetic_thresholds_used",
    "threshold_search_performed",
    "labels_used_as_trade_blockers",
    "labels_used_for_strategy_testing",
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
    "train_validation_only",
    "oos_used",
    "repeated_oos_review",
    "retune_performed",
    "parameter_grid_performed",
    "executable_candidate_created",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
    "recommended_next_step",
}


def _target_labels(report: dict[str, object], target_timestamp: str) -> dict[str, dict[str, object]]:
    for target in report["target_label_results"]:
        assert isinstance(target, dict)
        if target["target_timestamp"] == target_timestamp:
            labels = target["labels"]
            assert isinstance(labels, dict)
            return labels
    raise AssertionError(f"target not found: {target_timestamp}")


def test_labels_apply_deterministically_to_synthetic_fixtures() -> None:
    first = build_label_fixture_application_report()
    second = build_label_fixture_application_report()

    assert first == second
    assert first["labels_requested"] == LABELS_REQUESTED
    assert set(first["labels_applied"]) == set(LABELS_REQUESTED)
    labels = _target_labels(first, "2026-06-19T21:00:00+00:00")
    assert labels["nominal_yield_rising"]["value"] is True
    assert labels["nominal_yield_falling"]["value"] is False
    assert labels["real_yield_rising"]["value"] is True
    assert labels["real_yield_falling"]["value"] is False
    assert labels["yield_shock_up"]["value"] is True
    assert labels["yield_shock_down"]["value"] is False
    assert labels["gold_yield_pressure_aligned"]["value"] is True
    assert labels["gold_yield_decoupling"]["value"] is False
    assert labels["breakeven_inflation_rising"]["value"] is False
    assert labels["breakeven_inflation_falling"]["value"] is True
    assert labels["fed_funds_pressure_tightening"]["value"] is True
    assert labels["fed_funds_pressure_easing"]["value"] is False


def test_missing_required_series_produces_not_applicable_labels() -> None:
    from src.research.xauusd_external_yield_label_fixture_application import _default_fixture_records

    fixture_records = [
        record for record in _default_fixture_records() if record["series_id"] != "DFII10"
    ]
    missing_report = apply_external_yield_labels_to_fixture(records=fixture_records)
    labels = _target_labels(missing_report, "2026-06-19T21:00:00+00:00")

    assert labels["real_yield_rising"]["status"] == "not_applicable"
    assert labels["real_yield_falling"]["status"] == "not_applicable"
    assert labels["yield_shock_up"]["status"] == "not_applicable"
    assert labels["gold_yield_pressure_aligned"]["status"] == "not_applicable"
    assert "real_yield_rising" in missing_report["labels_not_applicable"]


def test_no_future_released_after_target_observations_are_used() -> None:
    report = build_label_fixture_application_report()
    labels = _target_labels(report, "2026-06-19T21:00:00+00:00")
    alignment_summary = [
        row
        for row in report["alignment_summary"]
        if row["target_timestamp"] == "2026-06-19T21:00:00+00:00"
    ][0]

    assert alignment_summary["series_results"]["DGS10"]["value"] == 4.3
    assert alignment_summary["series_results"]["DGS10"]["release_timestamp"] == "2026-06-19T20:15:00+00:00"
    assert labels["yield_shock_up"]["value"] is True
    assert report["no_lookahead_policy_confirmed"] is True
    assert report["backward_asof_only"] is True


def test_fixed_synthetic_thresholds_are_documented_and_not_searched() -> None:
    report = build_label_fixture_application_report()

    assert report["synthetic_thresholds_used"] is True
    assert report["synthetic_thresholds"]["yield_shock_threshold_percentage_points"] == SYNTHETIC_SHOCK_THRESHOLD_PERCENTAGE_POINTS
    assert "not searched" in report["synthetic_thresholds"]["policy"]
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False


def test_no_real_data_external_access_or_dataset_exports() -> None:
    before = {
        path: path.stat().st_mtime_ns
        for path in (ROOT / "data").glob("*.csv")
    }
    report = build_label_fixture_application_report()
    after = {
        path: path.stat().st_mtime_ns
        for path in (ROOT / "data").glob("*.csv")
    }

    assert before == after
    assert report["real_xauusd_data_used"] is False
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["data_csv_touched"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["aligned_dataset_created"] is False
    assert report["label_dataset_exported"] is False
    assert report["forward_fill_applied"] is False
    assert report["intraday_timestamp_inferred"] is False


def test_labels_are_not_strategy_trade_or_execution_surface() -> None:
    report = build_label_fixture_application_report()

    assert report["labels_used_as_trade_blockers"] is False
    assert report["labels_used_for_strategy_testing"] is False
    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["strategy_rules_created"] is False
    assert report["strategy_rules_modified"] is False
    assert report["trade_signals_output"] is False
    assert report["trade_recommendation_output"] is False
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["executable_candidate_created"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False


def test_report_includes_all_required_application_and_safety_fields() -> None:
    report = build_label_fixture_application_report()

    assert REQUIRED_REPORT_FIELDS <= set(report)
    assert report["application_version"] == "v0_79"
    assert report["application_status"] == "external_yield_label_fixture_application_completed_with_not_applicable_labels"
    assert report["source_schema_version"] == "v0_74"
    assert report["source_validator_version"] == "v0_75"
    assert report["source_ingestion_version"] == "v0_76"
    assert report["source_alignment_version"] == "v0_77"
    assert report["source_label_design_version"] == "v0_78"
    assert report["fixture_record_count"] == 18
    assert report["synthetic_target_timestamp_count"] == 2
    assert report["recommended_next_step"] == "v0_80_external_yield_context_readiness_board_no_strategy"


def test_script_writes_report_without_external_data_access() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "apply_xauusd_external_yield_label_fixture_v0_79.py"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["application_version"] == "v0_79"
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert (ROOT / "reports" / "xauusd_external_yield_label_fixture_application_v0_79.json").exists()
