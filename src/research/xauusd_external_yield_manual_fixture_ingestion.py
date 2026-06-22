"""Manual fixture ingestion for v0_76 external yield samples.

This module accepts controlled CSV-like fixture content only. It validates rows
with the v0_75 sample validator, normalizes valid rows in memory, and returns a
report; it never downloads, aligns, forward-fills, or writes market datasets.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO
from typing import Any

from src.research.xauusd_external_yield_dataset_validator import (
    ALLOWED_SERIES_IDS,
    EXPLICIT_MISSING_VALUE_MARKERS,
    FUTURE_LABEL_CANDIDATES,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    SOURCE_SCHEMA_VERSION,
    VALIDATOR_VERSION,
    validate_external_yield_sample_records,
)

INGESTION_VERSION = "v0_76"
FIXTURE_SOURCE = "inline_or_test_fixture_only"
RECOMMENDED_NEXT_STEP = "v0_77_external_yield_asof_alignment_design_no_strategy"


def parse_manual_fixture_csv(text: str) -> list[dict[str, object]]:
    """Parse CSV-like manual fixture content into record dictionaries."""

    reader = csv.DictReader(StringIO(text.strip()))
    records: list[dict[str, object]] = []
    for row in reader:
        records.append({key: value for key, value in row.items() if key is not None})
    return records


def _record_rejection_reasons(record: dict[str, object]) -> dict[str, int]:
    return validate_external_yield_sample_records([record])["rejection_reasons"]


def _duplicate_rejected_indices(records: list[dict[str, object]]) -> set[int]:
    seen: set[tuple[object, object]] = set()
    duplicate_indices: set[int] = set()
    for index, record in enumerate(records):
        key = (record.get("series_id"), record.get("observation_date"))
        if key[0] is None or key[1] is None:
            continue
        if key in seen:
            duplicate_indices.add(index)
        seen.add(key)
    return duplicate_indices


def _normalize_value(value: object) -> tuple[float | None, str]:
    if value in EXPLICIT_MISSING_VALUE_MARKERS:
        return None, "explicit_missing_marker"
    return float(Decimal(str(value))), "numeric_observed"


def _normalize_valid_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    duplicate_indices = _duplicate_rejected_indices(records)
    normalized: list[dict[str, object]] = []

    for index, record in enumerate(records):
        if index in duplicate_indices or _record_rejection_reasons(record):
            continue

        value, value_policy = _normalize_value(record.get("value"))
        normalized_record: dict[str, object] = {
            "series_id": record["series_id"],
            "observation_date": record["observation_date"],
            "value": value,
            "value_policy": value_policy,
            "source_name": record["source_name"],
            "input_index": index,
        }
        for column in OPTIONAL_COLUMNS:
            if column in record:
                normalized_record[column] = record[column]
        normalized.append(normalized_record)

    return sorted(normalized, key=lambda row: (str(row["series_id"]), str(row["observation_date"]), int(row["input_index"])))


def _coverage_by_series(normalized_records: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    coverage: dict[str, dict[str, object]] = {}
    for record in normalized_records:
        series_id = str(record["series_id"])
        observation_date = str(record["observation_date"])
        if series_id not in coverage:
            coverage[series_id] = {
                "record_count": 0,
                "first_observation_date": observation_date,
                "last_observation_date": observation_date,
            }
        coverage[series_id]["record_count"] = int(coverage[series_id]["record_count"]) + 1
        coverage[series_id]["first_observation_date"] = min(
            str(coverage[series_id]["first_observation_date"]),
            observation_date,
        )
        coverage[series_id]["last_observation_date"] = max(
            str(coverage[series_id]["last_observation_date"]),
            observation_date,
        )
    return dict(sorted(coverage.items()))


def ingest_external_yield_manual_fixture(records: list[dict[str, object]]) -> dict[str, object]:
    """Validate and normalize a controlled manual fixture in memory."""

    validation = validate_external_yield_sample_records(records)
    normalized_records = _normalize_valid_records(records)
    records_rejected = int(validation["rejected_record_count"])
    ingestion_status = (
        "external_yield_manual_fixture_ingestion_completed"
        if records_rejected == 0
        else "external_yield_manual_fixture_ingestion_completed_with_expected_rejections"
    )

    return {
        "ingestion_version": INGESTION_VERSION,
        "ingestion_status": ingestion_status,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "source_validator_version": VALIDATOR_VERSION,
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
        "fixture_source": FIXTURE_SOURCE,
        "records_seen": len(records),
        "records_valid": int(validation["valid_record_count"]),
        "records_rejected": records_rejected,
        "rejection_reasons": validation["rejection_reasons"],
        "normalized_record_count": len(normalized_records),
        "normalized_records": normalized_records,
        "duplicate_count": validation["duplicate_count"],
        "duplicate_keys": validation["duplicate_keys"],
        "coverage_by_series": _coverage_by_series(normalized_records),
        "allowed_series_ids": list(ALLOWED_SERIES_IDS),
        "required_columns": list(REQUIRED_COLUMNS),
        "optional_columns": list(OPTIONAL_COLUMNS),
        "explicit_missing_value_count": validation["explicit_missing_value_count"],
        "explicit_missing_value_markers_allowed": validation["explicit_missing_value_markers_allowed"],
        "no_lookahead_policy_confirmed": True,
        "asof_alignment_performed": False,
        "forward_fill_applied": False,
        "intraday_timestamp_inferred": False,
        "future_label_candidates_preserved": list(FUTURE_LABEL_CANDIDATES),
        "labels_used_as_trade_blockers": False,
        "labels_used_for_strategy_testing": False,
        "approved_for_strategy_testing": False,
        "approved_for_trade_filtering": False,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "executable_candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "trade_recommendation_output": False,
        "strategy_rules_created": False,
        "strategy_rules_modified": False,
        "trade_signals_output": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "warnings": [
            "manual_fixture_ingestion_only_not_external_data_download",
            "normalized_records_are_report_summary_only_not_persistent_dataset",
            "no_xauusd_asof_alignment_performed",
            "yield_labels_are_not_trade_blockers",
        ],
    }


def ingest_external_yield_manual_fixture_csv(text: str) -> dict[str, object]:
    return ingest_external_yield_manual_fixture(parse_manual_fixture_csv(text))
