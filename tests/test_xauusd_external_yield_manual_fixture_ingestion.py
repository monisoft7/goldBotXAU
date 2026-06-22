from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_external_yield_manual_fixture_ingestion import (
    ingest_external_yield_manual_fixture_csv,
)

ROOT = Path(__file__).resolve().parents[1]


def _fixture_text() -> str:
    return """series_id,observation_date,value,source_name,release_timestamp,vintage_date,value_unit,source_reference,quality_flag
DGS10,2026-06-18,4.12,FRED / Federal Reserve Economic Data,2026-06-19T20:15:00+00:00,2026-06-19,percent,inline test fixture only,sample_valid
DFII10,2026-06-18,.,FRED / Federal Reserve Economic Data,2026-06-19T20:15:00+00:00,2026-06-19,percent,explicit missing marker policy sample,source_missing_marker
DGS2,2026-06-17,4.70,FRED / Federal Reserve Economic Data,2026-06-18T20:15:00+00:00,2026-06-18,percent,inline test fixture only,sample_valid
DGS10,2026-06-18,4.13,FRED / Federal Reserve Economic Data,2026-06-19T20:15:00+00:00,2026-06-19,percent,intentional duplicate fixture rejection,sample_duplicate_expected_rejection
BADYIELD,2026/06/18,not_numeric,,2026-06-19T20:15:00,2026-06-17,percent,intentional invalid fixture rejection,sample_invalid_expected_rejection
"""


def test_valid_manual_fixture_rows_ingest_and_normalize_in_memory() -> None:
    report = ingest_external_yield_manual_fixture_csv(_fixture_text())

    assert report["ingestion_version"] == "v0_76"
    assert report["source_schema_version"] == "v0_74"
    assert report["source_validator_version"] == "v0_75"
    assert report["records_seen"] == 5
    assert report["records_valid"] == 3
    assert report["records_rejected"] == 2
    assert report["normalized_record_count"] == 3
    assert report["fixture_source"] == "inline_or_test_fixture_only"


def test_invalid_rows_are_rejected_through_v0_75_validator() -> None:
    report = ingest_external_yield_manual_fixture_csv(_fixture_text())

    reasons = report["rejection_reasons"]
    assert reasons["duplicate_series_id_observation_date"] == 1
    assert reasons["invalid_series_id"] == 1
    assert reasons["invalid_observation_date"] == 1
    assert reasons["invalid_non_numeric_value"] == 1
    assert reasons["empty_source_name"] == 1
    assert reasons["release_timestamp_missing_timezone"] == 1


def test_rows_are_sorted_deterministically_and_coverage_is_reported() -> None:
    report = ingest_external_yield_manual_fixture_csv(_fixture_text())

    keys = [
        (record["series_id"], record["observation_date"])
        for record in report["normalized_records"]
    ]
    assert keys == [
        ("DFII10", "2026-06-18"),
        ("DGS10", "2026-06-18"),
        ("DGS2", "2026-06-17"),
    ]
    assert report["coverage_by_series"] == {
        "DFII10": {
            "record_count": 1,
            "first_observation_date": "2026-06-18",
            "last_observation_date": "2026-06-18",
        },
        "DGS10": {
            "record_count": 1,
            "first_observation_date": "2026-06-18",
            "last_observation_date": "2026-06-18",
        },
        "DGS2": {
            "record_count": 1,
            "first_observation_date": "2026-06-17",
            "last_observation_date": "2026-06-17",
        },
    }


def test_duplicates_and_missing_values_follow_policy() -> None:
    report = ingest_external_yield_manual_fixture_csv(_fixture_text())

    assert report["duplicate_count"] == 1
    assert report["duplicate_keys"] == [{"series_id": "DGS10", "observation_date": "2026-06-18"}]
    assert report["explicit_missing_value_count"] == 1
    missing = [
        record
        for record in report["normalized_records"]
        if record["series_id"] == "DFII10"
    ][0]
    assert missing["value"] is None
    assert missing["value_policy"] == "explicit_missing_marker"


def test_no_data_csv_file_is_created_or_touched_by_ingestion() -> None:
    data_dir = ROOT / "data"
    before = {path: path.stat().st_mtime_ns for path in data_dir.glob("*.csv")}

    ingest_external_yield_manual_fixture_csv(_fixture_text())

    after = {path: path.stat().st_mtime_ns for path in data_dir.glob("*.csv")}
    assert after == before


def test_no_external_or_strategy_surfaces_are_performed() -> None:
    report = ingest_external_yield_manual_fixture_csv(_fixture_text())

    for key in (
        "external_api_called",
        "external_data_downloaded",
        "dataset_file_created",
        "market_csv_created",
        "data_csv_touched",
        "asof_alignment_performed",
        "forward_fill_applied",
        "intraday_timestamp_inferred",
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


def test_report_includes_required_ingestion_and_safety_fields() -> None:
    report = ingest_external_yield_manual_fixture_csv(_fixture_text())

    expected_fields = {
        "ingestion_version",
        "ingestion_status",
        "source_schema_version",
        "source_validator_version",
        "external_api_called",
        "external_data_downloaded",
        "dataset_file_created",
        "market_csv_created",
        "data_csv_touched",
        "fixture_source",
        "records_seen",
        "records_valid",
        "records_rejected",
        "rejection_reasons",
        "normalized_record_count",
        "duplicate_count",
        "coverage_by_series",
        "allowed_series_ids",
        "required_columns",
        "optional_columns",
        "no_lookahead_policy_confirmed",
        "asof_alignment_performed",
        "forward_fill_applied",
        "intraday_timestamp_inferred",
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
    assert report["ingestion_status"] == "external_yield_manual_fixture_ingestion_completed_with_expected_rejections"
    assert report["recommended_next_step"] == "v0_77_external_yield_asof_alignment_design_no_strategy"


def test_cli_writes_report_from_inline_fixture_only() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ingest_xauusd_external_yield_manual_fixture_v0_76.py"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(completed.stdout)
    assert report["ingestion_version"] == "v0_76"
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["data_csv_touched"] is False
    assert report["asof_alignment_performed"] is False
