from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_external_yield_dataset_validator import validate_external_yield_sample_records

ROOT = Path(__file__).resolve().parents[1]


def _valid_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "series_id": "DGS10",
        "observation_date": "2026-06-18",
        "value": "4.12",
        "source_name": "FRED / Federal Reserve Economic Data",
        "release_timestamp": "2026-06-19T20:15:00+00:00",
        "vintage_date": "2026-06-19",
        "value_unit": "percent",
        "source_reference": "inline sample only",
        "quality_flag": "sample_valid",
    }
    record.update(overrides)
    return record


def test_valid_sample_records_pass() -> None:
    report = validate_external_yield_sample_records([
        _valid_record(series_id="DGS10"),
        _valid_record(series_id="DGS2", observation_date="2026-06-19", value=4.15),
    ])

    assert report["validator_status"] == "external_yield_sample_validator_completed"
    assert report["sample_records_validated"] == 2
    assert report["valid_record_count"] == 2
    assert report["rejected_record_count"] == 0
    assert report["records_sortable_by_series_id_observation_date"] is True


def test_missing_required_columns_fail_safely() -> None:
    record = _valid_record()
    del record["source_name"]

    report = validate_external_yield_sample_records([record])

    assert report["rejected_record_count"] == 1
    assert report["rejection_reasons"]["missing_required_column:source_name"] == 1


def test_invalid_series_id_fails_safely() -> None:
    report = validate_external_yield_sample_records([_valid_record(series_id="US10Y")])

    assert report["rejected_record_count"] == 1
    assert report["rejection_reasons"]["invalid_series_id"] == 1


def test_invalid_observation_date_fails_safely() -> None:
    report = validate_external_yield_sample_records([_valid_record(observation_date="2026/06/18")])

    assert report["rejected_record_count"] == 1
    assert report["rejection_reasons"]["invalid_observation_date"] == 1


def test_non_numeric_value_fails_unless_explicit_missing_marker_policy_allows_it() -> None:
    invalid = validate_external_yield_sample_records([_valid_record(value="not_numeric")])
    missing_marker = validate_external_yield_sample_records([_valid_record(value=".")])

    assert invalid["rejected_record_count"] == 1
    assert invalid["rejection_reasons"]["invalid_non_numeric_value"] == 1
    assert missing_marker["rejected_record_count"] == 0
    assert missing_marker["explicit_missing_value_count"] == 1


def test_duplicate_series_id_observation_date_is_flagged() -> None:
    report = validate_external_yield_sample_records([
        _valid_record(series_id="DGS10"),
        _valid_record(series_id="DGS10"),
    ])

    assert report["duplicate_count"] == 1
    assert report["rejected_record_count"] == 1
    assert report["rejection_reasons"]["duplicate_series_id_observation_date"] == 1


def test_invalid_vintage_date_relationship_is_rejected() -> None:
    report = validate_external_yield_sample_records([_valid_record(vintage_date="2026-06-17")])

    assert report["rejected_record_count"] == 1
    assert report["rejection_reasons"]["vintage_date_before_observation_date"] == 1


def test_timezone_less_release_timestamp_is_rejected() -> None:
    report = validate_external_yield_sample_records([_valid_record(release_timestamp="2026-06-19T20:15:00")])

    assert report["rejected_record_count"] == 1
    assert report["rejection_reasons"]["release_timestamp_missing_timezone"] == 1


def test_report_includes_required_validation_and_safety_fields() -> None:
    report = validate_external_yield_sample_records([_valid_record()])

    expected_fields = {
        "validator_version",
        "validator_status",
        "source_schema_version",
        "external_api_called",
        "external_data_downloaded",
        "dataset_file_created",
        "market_csv_created",
        "data_csv_touched",
        "sample_records_validated",
        "valid_record_count",
        "rejected_record_count",
        "rejection_reasons",
        "duplicate_count",
        "allowed_series_ids",
        "required_columns",
        "optional_columns",
        "no_lookahead_policy_confirmed",
        "asof_alignment_performed",
        "forward_fill_applied",
        "future_label_candidates_preserved",
        "labels_used_as_trade_blockers",
        "labels_used_for_strategy_testing",
        "approved_for_strategy_testing",
        "approved_for_trade_filtering",
        "train_validation_only",
        "oos_used",
        "repeated_oos_review",
        "retune_performed",
        "threshold_search_performed",
        "parameter_grid_performed",
        "executable_candidate_created",
        "demo_execution_allowed",
        "order_send_called",
        "order_check_called",
        "live_allowed",
        "trade_recommendation_output",
        "recommended_next_step",
    }
    assert expected_fields <= set(report)
    assert report["validator_version"] == "v0_75"
    assert report["source_schema_version"] == "v0_74"
    assert report["allowed_series_ids"] == ["DGS10", "DGS2", "DFII10", "DFII5", "T10YIE", "DFF"]
    assert report["required_columns"] == ["series_id", "observation_date", "value", "source_name"]
    assert report["optional_columns"] == [
        "release_timestamp",
        "vintage_date",
        "value_unit",
        "source_reference",
        "quality_flag",
    ]


def test_no_external_or_trading_surfaces_are_performed() -> None:
    report = validate_external_yield_sample_records([_valid_record()])

    for key in (
        "external_api_called",
        "external_data_downloaded",
        "dataset_file_created",
        "market_csv_created",
        "data_csv_touched",
        "asof_alignment_performed",
        "forward_fill_applied",
        "labels_used_as_trade_blockers",
        "labels_used_for_strategy_testing",
        "approved_for_strategy_testing",
        "approved_for_trade_filtering",
        "oos_used",
        "repeated_oos_review",
        "retune_performed",
        "threshold_search_performed",
        "parameter_grid_performed",
        "executable_candidate_created",
        "demo_execution_allowed",
        "order_send_called",
        "order_check_called",
        "live_allowed",
        "trade_recommendation_output",
        "strategy_rules_created",
        "strategy_rules_modified",
        "trade_signals_output",
    ):
        assert report[key] is False
    assert report["train_validation_only"] is True
    assert report["no_lookahead_policy_confirmed"] is True


def test_no_data_csv_file_is_touched_by_validator() -> None:
    data_dir = ROOT / "data"
    before = {
        path: path.stat().st_mtime_ns
        for path in data_dir.glob("*.csv")
    }

    validate_external_yield_sample_records([_valid_record()])

    after = {
        path: path.stat().st_mtime_ns
        for path in data_dir.glob("*.csv")
    }
    assert after == before


def test_cli_writes_report_from_inline_sample_fixture_only() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_xauusd_external_yield_sample_v0_75.py"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(completed.stdout)
    assert report["validator_version"] == "v0_75"
    assert report["validator_status"] == "external_yield_sample_validator_completed_with_expected_fixture_rejections"
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["data_csv_touched"] is False
    assert report["asof_alignment_performed"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["recommended_next_step"] == "v0_76_external_yield_manual_fixture_ingestion_design_no_strategy"
