"""v0_79 fixture-only application of external yield labels.

This module applies the v0_78 label contract to controlled in-memory fixture
records and synthetic target timestamps only. It does not read XAUUSD data,
download yield data, export datasets, create signals, or change strategy rules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.research.xauusd_external_yield_asof_alignment_design import (
    design_external_yield_asof_alignment,
)
from src.research.xauusd_external_yield_label_design import (
    SOURCE_ALIGNMENT_VERSION,
    SOURCE_INGESTION_VERSION,
    SOURCE_SCHEMA_VERSION,
    SOURCE_VALIDATOR_VERSION,
    build_label_definitions,
)

APPLICATION_VERSION = "v0_79"
SOURCE_LABEL_DESIGN_VERSION = "v0_78"
RECOMMENDED_NEXT_STEP = "v0_80_external_yield_context_readiness_board_no_strategy"
SYNTHETIC_SHOCK_THRESHOLD_PERCENTAGE_POINTS = 0.15

LABELS_REQUESTED = [
    "nominal_yield_rising",
    "nominal_yield_falling",
    "real_yield_rising",
    "real_yield_falling",
    "yield_shock_up",
    "yield_shock_down",
    "gold_yield_pressure_aligned",
    "gold_yield_decoupling",
    "breakeven_inflation_rising",
    "breakeven_inflation_falling",
    "fed_funds_pressure_tightening",
    "fed_funds_pressure_easing",
]


def _parse_aware_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(UTC)


def _alignable_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    alignable: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    duplicate_keys: set[tuple[str, str]] = set()
    for record in records:
        series_id = record.get("series_id")
        observation_date = record.get("observation_date")
        if isinstance(series_id, str) and isinstance(observation_date, str):
            key = (series_id, observation_date)
            if key in seen:
                duplicate_keys.add(key)
            seen.add(key)

    for index, record in enumerate(records):
        series_id = record.get("series_id")
        observation_date = record.get("observation_date")
        release_timestamp = _parse_aware_timestamp(record.get("release_timestamp"))
        value = record.get("value")
        if (
            not isinstance(series_id, str)
            or not isinstance(observation_date, str)
            or (series_id, observation_date) in duplicate_keys
            or release_timestamp is None
            or value is None
        ):
            continue
        aligned_record = dict(record)
        aligned_record["_input_index"] = index
        aligned_record["_release_timestamp_utc"] = release_timestamp
        aligned_record["value"] = float(value)
        alignable.append(aligned_record)

    return sorted(
        alignable,
        key=lambda row: (
            str(row["series_id"]),
            row["_release_timestamp_utc"],
            str(row["observation_date"]),
            int(row["_input_index"]),
        ),
    )


def _latest_record(
    alignable_records: list[dict[str, object]],
    series_id: str,
    target_timestamp: datetime,
) -> dict[str, object] | None:
    candidates = [
        record
        for record in alignable_records
        if record["series_id"] == series_id and record["_release_timestamp_utc"] <= target_timestamp
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            row["_release_timestamp_utc"],
            str(row["observation_date"]),
            int(row["_input_index"]),
        ),
    )


def _prior_record(
    alignable_records: list[dict[str, object]],
    selected: dict[str, object],
) -> dict[str, object] | None:
    candidates = [
        record
        for record in alignable_records
        if record["series_id"] == selected["series_id"]
        and record["_release_timestamp_utc"] < selected["_release_timestamp_utc"]
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            row["_release_timestamp_utc"],
            str(row["observation_date"]),
            int(row["_input_index"]),
        ),
    )


def _series_delta(
    alignable_records: list[dict[str, object]],
    series_id: str,
    target_timestamp: datetime,
) -> float | None:
    selected = _latest_record(alignable_records, series_id, target_timestamp)
    if selected is None:
        return None
    prior = _prior_record(alignable_records, selected)
    if prior is None:
        return None
    return float(selected["value"]) - float(prior["value"])


def _average_delta(
    alignable_records: list[dict[str, object]],
    required_series: list[str],
    target_timestamp: datetime,
) -> float | None:
    deltas = [
        _series_delta(alignable_records, series_id, target_timestamp)
        for series_id in required_series
    ]
    if any(delta is None for delta in deltas):
        return None
    return sum(float(delta) for delta in deltas) / len(deltas)


def _direction_from_delta(delta: float | None) -> str | None:
    if delta is None or delta == 0:
        return None
    return "rising" if delta > 0 else "falling"


def _boolean_or_not_applicable(value: bool | None, reason: str) -> dict[str, object]:
    if value is None:
        return {"status": "not_applicable", "value": None, "reason": reason}
    return {"status": "applied", "value": value, "reason": "computed_from_prior_released_fixture_observation"}


def _label_results_for_target(
    alignable_records: list[dict[str, object]],
    target: dict[str, object],
    required_series_by_label: dict[str, list[str]],
) -> dict[str, dict[str, object]]:
    target_timestamp = _parse_aware_timestamp(target.get("target_timestamp"))
    if target_timestamp is None:
        return {
            label: _boolean_or_not_applicable(None, "invalid_synthetic_target_timestamp")
            for label in LABELS_REQUESTED
        }

    nominal_delta = _average_delta(
        alignable_records,
        required_series_by_label["nominal_yield_rising"],
        target_timestamp,
    )
    real_delta = _average_delta(
        alignable_records,
        required_series_by_label["real_yield_rising"],
        target_timestamp,
    )
    shock_delta = _average_delta(
        alignable_records,
        required_series_by_label["yield_shock_up"],
        target_timestamp,
    )
    breakeven_delta = _average_delta(alignable_records, ["T10YIE"], target_timestamp)
    fed_funds_delta = _average_delta(alignable_records, ["DFF"], target_timestamp)

    nominal_direction = _direction_from_delta(_series_delta(alignable_records, "DGS10", target_timestamp))
    real_direction = _direction_from_delta(_series_delta(alignable_records, "DFII10", target_timestamp))
    synthetic_gold_direction = target.get("synthetic_gold_context_direction")

    expected_gold_direction: str | None = None
    mixed_yield_pressure = False
    if nominal_direction is not None and real_direction is not None:
        mixed_yield_pressure = nominal_direction != real_direction
        if not mixed_yield_pressure:
            expected_gold_direction = "down" if nominal_direction == "rising" else "up"

    gold_context_missing = synthetic_gold_direction not in {"up", "down"}
    aligned: bool | None
    decoupled: bool | None
    if nominal_direction is None or real_direction is None or gold_context_missing:
        aligned = None
        decoupled = None
    elif mixed_yield_pressure:
        aligned = False
        decoupled = True
    else:
        aligned = synthetic_gold_direction == expected_gold_direction
        decoupled = synthetic_gold_direction != expected_gold_direction

    nominal_rising = None if nominal_delta is None else nominal_delta > 0
    nominal_falling = None if nominal_delta is None else nominal_delta < 0
    real_rising = None if real_delta is None else real_delta > 0
    real_falling = None if real_delta is None else real_delta < 0
    shock_up = (
        None
        if shock_delta is None
        else shock_delta >= SYNTHETIC_SHOCK_THRESHOLD_PERCENTAGE_POINTS
    )
    shock_down = (
        None
        if shock_delta is None
        else shock_delta <= -SYNTHETIC_SHOCK_THRESHOLD_PERCENTAGE_POINTS
    )
    breakeven_rising = None if breakeven_delta is None else breakeven_delta > 0
    breakeven_falling = None if breakeven_delta is None else breakeven_delta < 0
    fed_funds_tightening = None if fed_funds_delta is None else fed_funds_delta > 0
    fed_funds_easing = None if fed_funds_delta is None else fed_funds_delta < 0

    return {
        "nominal_yield_rising": _boolean_or_not_applicable(nominal_rising, "missing_prior_released_nominal_yield_observation"),
        "nominal_yield_falling": _boolean_or_not_applicable(nominal_falling, "missing_prior_released_nominal_yield_observation"),
        "real_yield_rising": _boolean_or_not_applicable(real_rising, "missing_prior_released_real_yield_observation"),
        "real_yield_falling": _boolean_or_not_applicable(real_falling, "missing_prior_released_real_yield_observation"),
        "yield_shock_up": _boolean_or_not_applicable(
            shock_up,
            "missing_prior_released_shock_reference_observation",
        ),
        "yield_shock_down": _boolean_or_not_applicable(
            shock_down,
            "missing_prior_released_shock_reference_observation",
        ),
        "gold_yield_pressure_aligned": _boolean_or_not_applicable(
            aligned,
            "missing_prior_released_yield_pressure_or_synthetic_gold_context_direction",
        ),
        "gold_yield_decoupling": _boolean_or_not_applicable(
            decoupled,
            "missing_prior_released_yield_pressure_or_synthetic_gold_context_direction",
        ),
        "breakeven_inflation_rising": _boolean_or_not_applicable(
            breakeven_rising,
            "missing_prior_released_breakeven_observation",
        ),
        "breakeven_inflation_falling": _boolean_or_not_applicable(
            breakeven_falling,
            "missing_prior_released_breakeven_observation",
        ),
        "fed_funds_pressure_tightening": _boolean_or_not_applicable(
            fed_funds_tightening,
            "missing_prior_released_fed_funds_observation",
        ),
        "fed_funds_pressure_easing": _boolean_or_not_applicable(
            fed_funds_easing,
            "missing_prior_released_fed_funds_observation",
        ),
    }


def _label_counts(target_results: list[dict[str, object]]) -> dict[str, dict[str, int]]:
    counts = {
        label: {"true": 0, "false": 0, "not_applicable": 0}
        for label in LABELS_REQUESTED
    }
    for result in target_results:
        labels = result["labels"]
        assert isinstance(labels, dict)
        for label, payload in labels.items():
            assert isinstance(payload, dict)
            if payload["status"] == "not_applicable":
                counts[label]["not_applicable"] += 1
            elif payload["value"] is True:
                counts[label]["true"] += 1
            else:
                counts[label]["false"] += 1
    return counts


def _default_fixture_records() -> list[dict[str, object]]:
    series_values = {
        "DGS10": (4.10, 4.30, 4.95),
        "DGS2": (4.70, 4.88, 5.20),
        "DFII10": (1.90, 2.12, 2.80),
        "DFII5": (1.70, 1.91, 2.30),
        "T10YIE": (2.20, 2.10, 2.60),
        "DFF": (4.95, 5.05, 5.25),
    }
    observation_dates = ["2026-06-17", "2026-06-18", "2026-06-19"]
    release_timestamps = [
        "2026-06-18T20:15:00+00:00",
        "2026-06-19T20:15:00+00:00",
        "2026-06-20T20:15:00+00:00",
    ]
    records: list[dict[str, object]] = []
    for series_id, values in series_values.items():
        for index, value in enumerate(values):
            records.append(
                {
                    "series_id": series_id,
                    "observation_date": observation_dates[index],
                    "value": value,
                    "source_name": "synthetic fixture only",
                    "release_timestamp": release_timestamps[index],
                    "value_unit": "percent",
                    "source_reference": "v0_79 controlled in-memory fixture",
                    "quality_flag": "synthetic_fixture",
                }
            )
    return records


def _default_synthetic_targets() -> list[dict[str, object]]:
    return [
        {
            "target_timestamp": "2026-06-18T21:00:00+00:00",
            "synthetic_gold_context_direction": "down",
            "synthetic_gold_context_note": "synthetic direction only; not real XAUUSD data",
        },
        {
            "target_timestamp": "2026-06-19T21:00:00+00:00",
            "synthetic_gold_context_direction": "down",
            "synthetic_gold_context_note": "synthetic direction only; not real XAUUSD data",
        },
    ]


def apply_external_yield_labels_to_fixture(
    records: list[dict[str, object]] | None = None,
    synthetic_targets: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Apply v0_78 labels to controlled synthetic fixture snapshots."""

    fixture_records = _default_fixture_records() if records is None else records
    targets = _default_synthetic_targets() if synthetic_targets is None else synthetic_targets
    target_timestamps = [str(target["target_timestamp"]) for target in targets]
    alignment_report = design_external_yield_asof_alignment(fixture_records, target_timestamps)
    alignable = _alignable_records(fixture_records)
    required_series_by_label = {
        label["label_name"]: label["required_series"]
        for label in build_label_definitions()
    }

    target_results: list[dict[str, object]] = []
    for target in targets:
        target_results.append(
            {
                "target_timestamp": target["target_timestamp"],
                "synthetic_gold_context_direction": target.get("synthetic_gold_context_direction"),
                "labels": _label_results_for_target(alignable, target, required_series_by_label),
            }
        )

    label_counts = _label_counts(target_results)
    labels_applied = [
        label for label, counts in label_counts.items() if counts["true"] + counts["false"] > 0
    ]
    labels_not_applicable = [
        label for label, counts in label_counts.items() if counts["not_applicable"] > 0
    ]
    application_status = (
        "external_yield_label_fixture_application_completed"
        if not labels_not_applicable
        else "external_yield_label_fixture_application_completed_with_not_applicable_labels"
    )

    return {
        "application_version": APPLICATION_VERSION,
        "application_status": application_status,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "source_validator_version": SOURCE_VALIDATOR_VERSION,
        "source_ingestion_version": SOURCE_INGESTION_VERSION,
        "source_alignment_version": SOURCE_ALIGNMENT_VERSION,
        "source_label_design_version": SOURCE_LABEL_DESIGN_VERSION,
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
        "real_xauusd_data_used": False,
        "synthetic_target_timestamps_used": True,
        "aligned_dataset_created": False,
        "label_dataset_exported": False,
        "labels_requested": list(LABELS_REQUESTED),
        "labels_applied": labels_applied,
        "labels_not_applicable": labels_not_applicable,
        "label_counts": label_counts,
        "target_label_results": target_results,
        "fixture_record_count": len(fixture_records),
        "synthetic_target_timestamp_count": len(targets),
        "alignment_summary": alignment_report["alignment_summary"],
        "records_alignable": alignment_report["records_alignable"],
        "records_not_alignable": alignment_report["records_not_alignable"],
        "no_lookahead_policy_confirmed": True,
        "backward_asof_only": True,
        "forward_fill_applied": False,
        "intraday_timestamp_inferred": False,
        "synthetic_thresholds_used": True,
        "synthetic_thresholds": {
            "yield_shock_threshold_percentage_points": SYNTHETIC_SHOCK_THRESHOLD_PERCENTAGE_POINTS,
            "policy": "fixed illustrative fixture threshold only; not searched, tuned, or approved as a strategy parameter",
        },
        "threshold_search_performed": False,
        "labels_used_as_trade_blockers": False,
        "labels_used_for_strategy_testing": False,
        "approved_for_strategy_testing": False,
        "approved_for_trade_filtering": False,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "parameter_grid_performed": False,
        "executable_candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "trade_recommendation_output": False,
        "trade_signals_output": False,
        "strategy_rules_created": False,
        "strategy_rules_modified": False,
        "synthetic_gold_context_used": True,
        "synthetic_gold_context_real_xauusd_data_used": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "warnings": [
            "fixture_label_application_only_not_real_data_ingestion",
            "synthetic_gold_context_direction_is_not_real_xauusd_data",
            "fixed_synthetic_thresholds_are_not_strategy_parameters",
            "labels_are_not_trade_blockers_or_trade_filters",
        ],
    }


def build_label_fixture_application_report() -> dict[str, object]:
    return apply_external_yield_labels_to_fixture()
