"""External yield / real-yield dataset schema contract for XAUUSD research.

This module is schema/design infrastructure only. It does not fetch external
data, create market datasets, define trade signals, or approve labels as trade
filters.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "v0_74"
SCHEMA_STATUS_COMPLETED = "external_yield_dataset_schema_completed"
SOURCE_YIELD_FEASIBILITY_VERSION = "v0_73"
RECOMMENDED_NEXT_STEP = "v0_75_external_yield_sample_fixture_validator_no_strategy"

CANDIDATE_SERIES = [
    {
        "series_id": "DGS10",
        "description": "10-year Treasury nominal yield",
        "source_name": "FRED / Federal Reserve Economic Data",
        "source_url_or_reference": "FRED series DGS10 reference only; no API call performed",
        "expected_value_unit": "percent",
    },
    {
        "series_id": "DGS2",
        "description": "2-year Treasury nominal yield",
        "source_name": "FRED / Federal Reserve Economic Data",
        "source_url_or_reference": "FRED series DGS2 reference only; no API call performed",
        "expected_value_unit": "percent",
    },
    {
        "series_id": "DFII10",
        "description": "10-year TIPS real yield",
        "source_name": "FRED / Federal Reserve Economic Data",
        "source_url_or_reference": "FRED series DFII10 reference only; no API call performed",
        "expected_value_unit": "percent",
    },
    {
        "series_id": "DFII5",
        "description": "5-year TIPS real yield",
        "source_name": "FRED / Federal Reserve Economic Data",
        "source_url_or_reference": "FRED series DFII5 reference only; no API call performed",
        "expected_value_unit": "percent",
    },
    {
        "series_id": "T10YIE",
        "description": "10-year inflation breakeven",
        "source_name": "FRED / Federal Reserve Economic Data",
        "source_url_or_reference": "FRED series T10YIE reference only; no API call performed",
        "expected_value_unit": "percent",
    },
    {
        "series_id": "DFF",
        "description": "effective Fed funds rate",
        "source_name": "FRED / Federal Reserve Economic Data",
        "source_url_or_reference": "FRED series DFF reference only; no API call performed",
        "expected_value_unit": "percent",
    },
]

REQUIRED_SCHEMA_FIELDS = [
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
]

ACCEPTED_FUTURE_FILE_FORMATS = ["CSV", "JSONL"]
REQUIRED_FUTURE_COLUMNS = ["series_id", "observation_date", "value", "source_name"]
OPTIONAL_FUTURE_COLUMNS = [
    "release_timestamp",
    "vintage_date",
    "value_unit",
    "source_reference",
    "quality_flag",
]

RELEASE_TIMESTAMP_POLICY = (
    "Future imports must preserve an explicit release_timestamp when available. "
    "If unavailable, the series-specific official release-time assumption must be "
    "documented before intraday XAUUSD alignment is allowed."
)
TIMEZONE_POLICY = (
    "observation_date is a calendar date. release_timestamp, when present, must be "
    "timezone-aware UTC or include a source timezone that can be converted to UTC."
)
REVISION_POLICY = (
    "Future loaders must record vintage_date when available and must not replace "
    "historical values silently; revised and vintage values need explicit provenance."
)
MISSING_VALUE_POLICY = (
    "Missing, '.', blank, non-numeric, and source-holiday values must be flagged and "
    "excluded from label calculation unless a documented backward-only fill is valid."
)
ASOF_ALIGNMENT_POLICY = (
    "XAUUSD rows may use only the latest eligible yield observation whose observation "
    "date and release timestamp are not after the XAUUSD timestamp."
)
NO_LOOKAHEAD_POLICY = (
    "Forward, nearest-future, or same-day pre-release alignment is disallowed. Any "
    "ambiguous timestamp policy must fail closed before label calculation."
)
ALLOWED_FORWARD_FILL_POLICY = (
    "Forward fill may be considered only after a value is officially observable and "
    "only until the next scheduled observation or source holiday boundary; it is not "
    "a trade blocker or approval gate."
)

FUTURE_LABEL_CANDIDATES = [
    "nominal_yield_rising",
    "nominal_yield_falling",
    "real_yield_rising",
    "real_yield_falling",
    "yield_shock_up",
    "yield_shock_down",
    "gold_yield_pressure_aligned",
    "gold_yield_decoupling",
]


def build_external_yield_dataset_schema_report(root: Path | None = None) -> dict[str, Any]:
    """Build the v0_74 schema report without reading, downloading, or importing market data."""
    return {
        "schema_version": SCHEMA_VERSION,
        "schema_status": SCHEMA_STATUS_COMPLETED,
        "source_yield_feasibility_version": SOURCE_YIELD_FEASIBILITY_VERSION,
        "external_dataset_required": True,
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
        "candidate_series": CANDIDATE_SERIES,
        "required_schema_fields": REQUIRED_SCHEMA_FIELDS,
        "accepted_future_file_formats": ACCEPTED_FUTURE_FILE_FORMATS,
        "required_future_columns": REQUIRED_FUTURE_COLUMNS,
        "optional_future_columns": OPTIONAL_FUTURE_COLUMNS,
        "release_timestamp_policy": RELEASE_TIMESTAMP_POLICY,
        "timezone_policy": TIMEZONE_POLICY,
        "revision_policy": REVISION_POLICY,
        "missing_value_policy": MISSING_VALUE_POLICY,
        "asof_alignment_policy": ASOF_ALIGNMENT_POLICY,
        "no_lookahead_policy": NO_LOOKAHEAD_POLICY,
        "allowed_forward_fill_policy": ALLOWED_FORWARD_FILL_POLICY,
        "future_label_candidates": FUTURE_LABEL_CANDIDATES,
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
        "warnings": [
            "schema_design_only_not_data_import",
            "external_series_are_references_only_not_fetched",
            "future_yield_labels_are_not_trade_blockers",
            "no_strategy_testing_or_trade_filtering_approval",
        ],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def write_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
