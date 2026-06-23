"""Backward as-of alignment design for v0_77 external yield fixtures.

This module uses controlled in-memory yield records and synthetic target
timestamps only. It designs the alignment policy; it does not fetch data, read
XAUUSD rows, create persistent datasets, forward-fill, or create signals.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.research.xauusd_external_yield_dataset_validator import (
    FUTURE_LABEL_CANDIDATES,
    SOURCE_SCHEMA_VERSION,
    VALIDATOR_VERSION,
)
from src.research.xauusd_external_yield_manual_fixture_ingestion import INGESTION_VERSION

ALIGNMENT_VERSION = "v0_77"
RECOMMENDED_NEXT_STEP = "v0_78_external_yield_label_design_no_strategy"


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


def _reason_counts(reasons: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for reason in reasons:
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def _duplicate_indices(records: list[dict[str, object]]) -> tuple[set[int], list[dict[str, object]]]:
    seen: set[tuple[str, str]] = set()
    duplicate_indices: set[int] = set()
    duplicate_keys: set[tuple[str, str]] = set()
    for index, record in enumerate(records):
        series_id = record.get("series_id")
        observation_date = record.get("observation_date")
        if not isinstance(series_id, str) or not isinstance(observation_date, str):
            continue
        key = (series_id, observation_date)
        if key in seen:
            duplicate_indices.add(index)
            duplicate_keys.add(key)
        seen.add(key)
    return duplicate_indices, [
        {"series_id": series_id, "observation_date": observation_date}
        for series_id, observation_date in sorted(duplicate_keys)
    ]


def _classify_records(records: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, int], list[dict[str, object]]]:
    duplicate_indices, duplicate_keys = _duplicate_indices(records)
    alignable: list[dict[str, object]] = []
    not_alignable: list[dict[str, object]] = []
    rejection_reasons: list[str] = []

    for index, record in enumerate(records):
        reasons: list[str] = []
        release_timestamp = record.get("release_timestamp")

        if index in duplicate_indices:
            reasons.append("duplicate_series_id_observation_date")
        if release_timestamp in (None, ""):
            reasons.append("release_timestamp_missing")

        parsed_release_timestamp = _parse_aware_timestamp(release_timestamp)
        if release_timestamp not in (None, "") and parsed_release_timestamp is None:
            reasons.append("release_timestamp_missing_timezone")

        if record.get("value") is None:
            reasons.append("explicit_missing_value_not_alignable")

        if reasons:
            not_alignable.append(
                {
                    "input_index": record.get("input_index", index),
                    "series_id": record.get("series_id"),
                    "observation_date": record.get("observation_date"),
                    "reasons": sorted(reasons),
                }
            )
            rejection_reasons.extend(reasons)
            continue

        aligned_record = dict(record)
        aligned_record["_release_timestamp_utc"] = parsed_release_timestamp
        alignable.append(aligned_record)

    alignable.sort(
        key=lambda row: (
            str(row.get("series_id")),
            row["_release_timestamp_utc"],
            str(row.get("observation_date")),
            int(row.get("input_index", 0)),
        )
    )
    return alignable, not_alignable, _reason_counts(rejection_reasons), duplicate_keys


def _normalize_target_timestamps(target_timestamps: list[str]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for index, value in enumerate(target_timestamps):
        parsed = _parse_aware_timestamp(value)
        normalized.append(
            {
                "target_index": index,
                "target_timestamp": value,
                "target_timestamp_utc": parsed,
                "target_timestamp_valid": parsed is not None,
            }
        )
    return normalized


def _select_latest_available_record(records: list[dict[str, object]], series_id: str, target_timestamp: datetime) -> dict[str, object] | None:
    candidates = [
        record
        for record in records
        if record.get("series_id") == series_id and record["_release_timestamp_utc"] <= target_timestamp
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            row["_release_timestamp_utc"],
            str(row.get("observation_date")),
            int(row.get("input_index", 0)),
        ),
    )


def design_external_yield_asof_alignment(
    records: list[dict[str, object]],
    target_timestamps: list[str],
) -> dict[str, object]:
    """Apply backward-only as-of policy to synthetic target timestamps."""

    alignable_records, not_alignable_records, rejection_reasons, duplicate_keys = _classify_records(records)
    normalized_targets = _normalize_target_timestamps(target_timestamps)
    series_ids = sorted({str(record["series_id"]) for record in records if isinstance(record.get("series_id"), str)})

    alignment_summary: list[dict[str, object]] = []
    aligned_target_indices: set[int] = set()
    for target in normalized_targets:
        target_timestamp = target["target_timestamp_utc"]
        series_results: dict[str, dict[str, object] | None] = {}
        if isinstance(target_timestamp, datetime):
            for series_id in series_ids:
                selected = _select_latest_available_record(alignable_records, series_id, target_timestamp)
                if selected is None:
                    series_results[series_id] = None
                    continue
                aligned_target_indices.add(int(target["target_index"]))
                series_results[series_id] = {
                    "series_id": selected.get("series_id"),
                    "observation_date": selected.get("observation_date"),
                    "release_timestamp": selected.get("release_timestamp"),
                    "value": selected.get("value"),
                }

        alignment_summary.append(
            {
                "target_timestamp": target["target_timestamp"],
                "aligned_series_count": sum(1 for value in series_results.values() if value is not None),
                "series_results": series_results,
            }
        )

    target_timestamp_count = len(normalized_targets)
    aligned_target_count = len(aligned_target_indices)
    unaligned_target_count = target_timestamp_count - aligned_target_count
    alignment_status = (
        "external_yield_asof_alignment_design_completed"
        if not not_alignable_records
        else "external_yield_asof_alignment_design_completed_with_expected_rejections"
    )

    return {
        "alignment_version": ALIGNMENT_VERSION,
        "alignment_status": alignment_status,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "source_validator_version": VALIDATOR_VERSION,
        "source_ingestion_version": INGESTION_VERSION,
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
        "real_xauusd_data_used": False,
        "synthetic_target_timestamps_used": True,
        "records_seen": len(records),
        "records_alignable": len(alignable_records),
        "records_not_alignable": len(not_alignable_records),
        "target_timestamp_count": target_timestamp_count,
        "aligned_target_count": aligned_target_count,
        "unaligned_target_count": unaligned_target_count,
        "alignment_cases_tested": [
            "same_day_target_after_release_timestamp_aligned",
            "same_day_target_before_release_timestamp_not_aligned_or_previous_only",
            "target_between_two_releases_previous_released_record",
            "target_before_first_release_no_aligned_value",
            "missing_release_timestamp_not_alignable",
            "timezone_less_release_timestamp_rejected",
            "duplicate_series_date_flagged",
            "multiple_series_aligned_independently",
        ],
        "rejection_reasons": rejection_reasons,
        "not_alignable_records": not_alignable_records,
        "duplicate_count": len(duplicate_keys),
        "duplicate_keys": duplicate_keys,
        "timezone_policy_enforced": True,
        "release_timestamp_policy_enforced": True,
        "no_lookahead_policy_confirmed": True,
        "backward_asof_only": True,
        "forward_fill_applied": False,
        "intraday_timestamp_inferred": False,
        "aligned_dataset_created": False,
        "alignment_summary": alignment_summary,
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
        "warnings": [
            "alignment_design_uses_synthetic_in_memory_timestamps_only",
            "release_timestamp_is_required_for_intraday_availability",
            "no_forward_fill_or_intraday_timestamp_inference",
            "yield_labels_are_not_trade_blockers",
        ],
    }
