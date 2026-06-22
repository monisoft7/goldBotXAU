from __future__ import annotations

import json
from pathlib import Path

from src.research.xauusd_external_yield_dataset_schema import (
    ACCEPTED_FUTURE_FILE_FORMATS,
    FUTURE_LABEL_CANDIDATES,
    REQUIRED_FUTURE_COLUMNS,
    REQUIRED_SCHEMA_FIELDS,
    build_external_yield_dataset_schema_report,
)


def test_schema_report_has_required_status_and_series_references(tmp_path: Path) -> None:
    report = build_external_yield_dataset_schema_report(tmp_path)

    assert report["schema_version"] == "v0_74"
    assert report["schema_status"] == "external_yield_dataset_schema_completed"
    assert report["source_yield_feasibility_version"] == "v0_73"
    assert report["external_dataset_required"] is True
    assert [series["series_id"] for series in report["candidate_series"]] == [
        "DGS10",
        "DGS2",
        "DFII10",
        "DFII5",
        "T10YIE",
        "DFF",
    ]
    assert all("no API call performed" in series["source_url_or_reference"] for series in report["candidate_series"])


def test_no_external_api_download_or_dataset_file_is_created(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_csv = data_dir / "local.csv"
    data_csv.write_text("timestamp,close\n2024-01-01,1\n", encoding="utf-8")
    before = data_csv.read_text(encoding="utf-8")

    report = build_external_yield_dataset_schema_report(tmp_path)

    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["data_csv_touched"] is False
    assert data_csv.read_text(encoding="utf-8") == before
    assert list(data_dir.glob("*.csv")) == [data_csv]


def test_schema_includes_all_required_fields_and_future_columns(tmp_path: Path) -> None:
    report = build_external_yield_dataset_schema_report(tmp_path)

    assert report["required_schema_fields"] == REQUIRED_SCHEMA_FIELDS
    assert report["accepted_future_file_formats"] == ACCEPTED_FUTURE_FILE_FORMATS
    assert report["required_future_columns"] == REQUIRED_FUTURE_COLUMNS
    assert report["optional_future_columns"] == [
        "release_timestamp",
        "vintage_date",
        "value_unit",
        "source_reference",
        "quality_flag",
    ]
    for field in [
        "series_id",
        "observation_date",
        "value",
        "value_unit",
        "source_name",
        "source_url_or_reference",
        "release_frequency",
        "release_timestamp_policy",
        "timezone_policy",
        "missing_value_policy",
        "revision_policy",
        "asof_alignment_policy",
        "no_lookahead_policy",
        "allowed_forward_fill_policy",
        "data_quality_flags",
    ]:
        assert field in report["required_schema_fields"]


def test_asof_and_no_lookahead_policy_is_explicit(tmp_path: Path) -> None:
    report = build_external_yield_dataset_schema_report(tmp_path)

    assert "latest eligible yield observation" in report["asof_alignment_policy"]
    assert "not after the XAUUSD timestamp" in report["asof_alignment_policy"]
    assert "Forward, nearest-future" in report["no_lookahead_policy"]
    assert "fail closed" in report["no_lookahead_policy"]
    assert "officially observable" in report["allowed_forward_fill_policy"]


def test_labels_remain_future_candidates_only_not_trade_blockers(tmp_path: Path) -> None:
    report = build_external_yield_dataset_schema_report(tmp_path)

    assert report["future_label_candidates"] == FUTURE_LABEL_CANDIDATES
    assert report["labels_used_as_trade_blockers"] is False
    assert report["labels_used_for_strategy_testing"] is False
    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False


def test_no_strategy_rules_trade_signals_oos_or_search_is_created(tmp_path: Path) -> None:
    report = build_external_yield_dataset_schema_report(tmp_path)

    assert report["strategy_rules_created"] is False
    assert report["strategy_rules_modified"] is False
    assert report["trade_signals_output"] is False
    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False


def test_report_includes_all_required_schema_and_safety_fields(tmp_path: Path) -> None:
    report = build_external_yield_dataset_schema_report(tmp_path)
    required_report_fields = {
        "schema_version",
        "schema_status",
        "source_yield_feasibility_version",
        "external_dataset_required",
        "external_api_called",
        "external_data_downloaded",
        "dataset_file_created",
        "market_csv_created",
        "data_csv_touched",
        "candidate_series",
        "required_schema_fields",
        "accepted_future_file_formats",
        "required_future_columns",
        "optional_future_columns",
        "release_timestamp_policy",
        "timezone_policy",
        "revision_policy",
        "missing_value_policy",
        "asof_alignment_policy",
        "no_lookahead_policy",
        "allowed_forward_fill_policy",
        "future_label_candidates",
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

    assert required_report_fields <= set(report)
    assert report["recommended_next_step"] == "v0_75_external_yield_sample_fixture_validator_no_strategy"
    json.dumps(report)
