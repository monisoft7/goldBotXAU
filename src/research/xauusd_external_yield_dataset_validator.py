"""In-memory validation for v0_74 external yield sample records."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

VALIDATOR_VERSION = "v0_75"
SOURCE_SCHEMA_VERSION = "v0_74"

ALLOWED_SERIES_IDS = ("DGS10", "DGS2", "DFII10", "DFII5", "T10YIE", "DFF")
REQUIRED_COLUMNS = ("series_id", "observation_date", "value", "source_name")
OPTIONAL_COLUMNS = (
    "release_timestamp",
    "vintage_date",
    "value_unit",
    "source_reference",
    "quality_flag",
)
EXPLICIT_MISSING_VALUE_MARKERS = ("", ".", "NA", "N/A", "NULL", "null", None)
FUTURE_LABEL_CANDIDATES = (
    "nominal_yield_rising",
    "nominal_yield_falling",
    "real_yield_rising",
    "real_yield_falling",
    "yield_shock_up",
    "yield_shock_down",
    "gold_yield_pressure_aligned",
    "gold_yield_decoupling",
)


def _parse_yyyy_mm_dd(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _is_numeric_or_missing_marker(value: Any) -> bool:
    if value in EXPLICIT_MISSING_VALUE_MARKERS:
        return True
    if isinstance(value, bool):
        return False
    try:
        Decimal(str(value))
    except (InvalidOperation, ValueError):
        return False
    return True


def _release_timestamp_has_timezone(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _reason_counts(reasons: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for reason in reasons:
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def validate_external_yield_sample_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate sample records only; never fetch, download, align, or write market data."""

    rejected_indices: set[int] = set()
    rejection_reasons: list[str] = []
    duplicate_keys: set[tuple[str, str]] = set()
    seen_keys: set[tuple[str, str]] = set()
    explicit_missing_value_count = 0

    sortable_rows: list[tuple[str, str, int]] = []
    for index, record in enumerate(records):
        record_reasons: list[str] = []

        for column in REQUIRED_COLUMNS:
            if column not in record:
                record_reasons.append(f"missing_required_column:{column}")

        series_id = record.get("series_id")
        observation_date = record.get("observation_date")
        source_name = record.get("source_name")
        value = record.get("value")

        if "series_id" in record and series_id not in ALLOWED_SERIES_IDS:
            record_reasons.append("invalid_series_id")

        parsed_observation_date = _parse_yyyy_mm_dd(observation_date)
        if "observation_date" in record and parsed_observation_date is None:
            record_reasons.append("invalid_observation_date")

        if "value" in record:
            if value in EXPLICIT_MISSING_VALUE_MARKERS:
                explicit_missing_value_count += 1
            elif not _is_numeric_or_missing_marker(value):
                record_reasons.append("invalid_non_numeric_value")

        if "source_name" in record and (not isinstance(source_name, str) or not source_name.strip()):
            record_reasons.append("empty_source_name")

        if "vintage_date" in record and record.get("vintage_date") not in EXPLICIT_MISSING_VALUE_MARKERS:
            parsed_vintage_date = _parse_yyyy_mm_dd(record.get("vintage_date"))
            if parsed_vintage_date is None:
                record_reasons.append("invalid_vintage_date")
            elif parsed_observation_date is not None and parsed_vintage_date < parsed_observation_date:
                record_reasons.append("vintage_date_before_observation_date")

        if "release_timestamp" in record and record.get("release_timestamp") not in EXPLICIT_MISSING_VALUE_MARKERS:
            if not _release_timestamp_has_timezone(record.get("release_timestamp")):
                record_reasons.append("release_timestamp_missing_timezone")

        if isinstance(series_id, str) and isinstance(observation_date, str):
            sortable_rows.append((series_id, observation_date, index))
            key = (series_id, observation_date)
            if key in seen_keys:
                duplicate_keys.add(key)
                record_reasons.append("duplicate_series_id_observation_date")
            seen_keys.add(key)

        if record_reasons:
            rejected_indices.add(index)
            rejection_reasons.extend(record_reasons)

    sorted_sample_keys = [
        {"series_id": series_id, "observation_date": observation_date, "input_index": index}
        for series_id, observation_date, index in sorted(sortable_rows)
    ]
    rejected_record_count = len(rejected_indices)
    valid_record_count = len(records) - rejected_record_count
    status = (
        "external_yield_sample_validator_completed"
        if rejected_record_count == 0
        else "external_yield_sample_validator_completed_with_expected_fixture_rejections"
    )

    return {
        "validator_version": VALIDATOR_VERSION,
        "validator_status": status,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
        "sample_records_validated": len(records),
        "valid_record_count": valid_record_count,
        "rejected_record_count": rejected_record_count,
        "rejection_reasons": _reason_counts(rejection_reasons),
        "duplicate_count": len(duplicate_keys),
        "duplicate_keys": [
            {"series_id": series_id, "observation_date": observation_date}
            for series_id, observation_date in sorted(duplicate_keys)
        ],
        "allowed_series_ids": list(ALLOWED_SERIES_IDS),
        "required_columns": list(REQUIRED_COLUMNS),
        "optional_columns": list(OPTIONAL_COLUMNS),
        "explicit_missing_value_markers_allowed": [marker for marker in EXPLICIT_MISSING_VALUE_MARKERS if marker is not None],
        "explicit_missing_value_count": explicit_missing_value_count,
        "records_sortable_by_series_id_observation_date": len(sortable_rows) == len(records),
        "sorted_sample_keys": sorted_sample_keys,
        "no_lookahead_policy_confirmed": True,
        "no_lookahead_policy": (
            "Sample validation confirms only schema-level observability rules. Future XAUUSD alignment must use "
            "backward as-of only after official release timestamps or documented assumptions are available."
        ),
        "allowed_forward_fill_policy": (
            "Forward fill is documented as a future daily-yield policy only after official observability; it is "
            "not applied to intraday XAUUSD samples in v0_75."
        ),
        "asof_alignment_performed": False,
        "forward_fill_applied": False,
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
        "recommended_next_step": "v0_76_external_yield_manual_fixture_ingestion_design_no_strategy",
        "warnings": [
            "sample_fixture_validation_only_not_data_import",
            "external_series_are_not_fetched",
            "no_asof_alignment_to_xauusd_performed",
            "yield_labels_are_not_trade_blockers",
        ],
    }
