"""Train/validation-only session structure atlas for local XAUUSD low-TF data."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

from src.data.xauusd_low_tf_dataset_catalog import (
    DEFAULT_MANIFEST_PATH,
    build_low_tf_dataset_catalog,
    load_profiler_rows_from_catalog,
)

PROFILER_VERSION = "v0_25"
LOW_TF_ALLOWED = {"M5", "M10"}
FAMILIES = (
    "asia_range_to_london_expansion",
    "london_to_ny_handoff_continuation_or_reversal",
    "ny_opening_range_followthrough_or_reversal",
    "compression_then_expansion",
    "trend_day_vs_mean_reversion_day_shape",
)
SESSION_BLOCKS = {
    "block_00_06": range(0, 6),
    "block_06_12": range(6, 12),
    "block_12_18": range(12, 18),
    "block_18_24": range(18, 24),
}
MIN_TRAIN_SAMPLES = 50
MIN_VALIDATION_SAMPLES = 20
MATERIAL_EDGE = 0.06
MAX_VALIDATION_DEGRADATION = 0.12
SAFETY_FLAGS = {
    "demo_enabled": False,
    "live_enabled": False,
    "order_send_allowed": False,
    "execution_queue_enabled": False,
    "buy_sell_output_allowed": False,
    "execution_logic_present": False,
    "trade_recommendation_output_present": False,
    "strategy_candidate_created": False,
    "candidate_registry_promotion_created": False,
    "oos_evaluated": False,
    "threshold_search_used": False,
    "parameter_grid_used": False,
    "rejected_candidate_retuned": False,
}


def profile_xauusd_session_structure_atlas(
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    pattern: str = "xauusd_m*.csv",
) -> dict[str, Any]:
    """Build a fixed, diagnostic atlas over M5/M10 train/validation rows only."""
    catalog = build_low_tf_dataset_catalog(data_dir=data_dir, manifest_path=manifest_path, pattern=pattern)
    rows = [
        row
        for row in load_profiler_rows_from_catalog(catalog)
        if row.get("source_timeframe") in LOW_TF_ALLOWED and row.get("split") in {"train", "validation"}
    ]
    data_files_used = _data_files_used(catalog)
    if not rows:
        return _base_report(
            status="blocked_need_train_validation_low_tf_data",
            catalog=catalog,
            rows=[],
            data_files_used=[],
            family_results=_empty_family_results(),
        )

    day_profiles = _day_profiles(rows)
    family_results = {
        family: _family_result(day_profiles, family)
        for family in FAMILIES
    }
    strongest_family = _strongest_family(family_results)
    recommended_next_step = _recommended_next_step(family_results)
    return _base_report(
        status="profile_ready",
        catalog=catalog,
        rows=rows,
        data_files_used=data_files_used,
        family_results=family_results,
        strongest_family=strongest_family,
        recommended_next_step=recommended_next_step,
    )


def _base_report(
    *,
    status: str,
    catalog: dict[str, Any],
    rows: list[dict[str, Any]],
    data_files_used: list[str],
    family_results: dict[str, Any],
    strongest_family: dict[str, Any] | None = None,
    recommended_next_step: str = "blocked_inconclusive",
) -> dict[str, Any]:
    return {
        "profiler_version": PROFILER_VERSION,
        "status": status,
        "purpose": "diagnostic_session_structure_research_atlas_only",
        "data_files_used": data_files_used,
        "oos_rows_used": 0,
        "families_profiled": list(FAMILIES),
        "split_policy": catalog.get("split_policy", {}),
        "dataset": {
            "profiled_splits": ["train", "validation"],
            "source_timeframes_allowed": sorted(LOW_TF_ALLOWED),
            "source_timeframes_used": sorted({str(row["source_timeframe"]) for row in rows}),
            "train_row_count": sum(1 for row in rows if row.get("split") == "train"),
            "validation_row_count": sum(1 for row in rows if row.get("split") == "validation"),
            "oos_row_count_used": 0,
        },
        "low_tf_catalog": catalog,
        "fixed_research_design": {
            "time_basis": "dataset_timestamp_hour_buckets_only",
            "session_blocks": {name: f"{min(hours):02d}-{max(hours) + 1:02d}" for name, hours in SESSION_BLOCKS.items()},
            "families": {
                "asia_range_to_london_expansion": "Compare fixed block_00_06 range with fixed block_06_12 range.",
                "london_to_ny_handoff_continuation_or_reversal": "Compare fixed block_06_12 direction with fixed block_12_18 direction.",
                "ny_opening_range_followthrough_or_reversal": "Compare fixed hour_12 opening range direction with fixed hours_13_16 direction.",
                "compression_then_expansion": "Use each day's lowest fixed six-hour block with a following block, then measure next-block expansion.",
                "trend_day_vs_mean_reversion_day_shape": "Compare fixed first-half day direction with fixed second-half day direction.",
            },
            "minimum_train_samples": MIN_TRAIN_SAMPLES,
            "minimum_validation_samples": MIN_VALIDATION_SAMPLES,
            "material_edge_over_neutral": MATERIAL_EDGE,
            "maximum_validation_degradation": MAX_VALIDATION_DEGRADATION,
            "threshold_search_used": False,
            "parameter_grid_used": False,
        },
        "family_results": family_results,
        "strongest_family": strongest_family,
        "any_family_strong_enough_for_future_single_fixed_candidate": any(
            result["strong_enough_for_future_single_fixed_candidate"] for result in family_results.values()
        ),
        "recommended_next_step": recommended_next_step,
        "safety": dict(SAFETY_FLAGS),
        "notes": [
            "This atlas is diagnostic research only and does not create a strategy candidate.",
            "OOS-only and mixed-OOS files are quarantined by the low-timeframe catalog before rows are loaded.",
            "Window labels are dataset timestamp hour buckets, not timezone claims.",
        ],
    }


def _empty_family_results() -> dict[str, Any]:
    return {
        family: {
            "train_result": _empty_split_result(),
            "validation_result": _empty_split_result(),
            "sample_size": {"train": 0, "validation": 0},
            "stability_assessment": {
                "label": "inconclusive",
                "stable": False,
                "reason": "No train/validation M5 or M10 rows were available.",
            },
            "degradation_assessment": {
                "primary_metric_train": 0.0,
                "primary_metric_validation": 0.0,
                "validation_degradation": 0.0,
                "within_fixed_limit": False,
            },
            "strong_enough_for_future_single_fixed_candidate": False,
        }
        for family in FAMILIES
    }


def _empty_split_result() -> dict[str, Any]:
    return {
        "sample_count": 0,
        "label_rates": {},
        "dominant_behavior": "insufficient",
        "primary_metric_rate": 0.0,
        "edge_over_neutral": 0.0,
        "average_expansion_ratio": 0.0,
        "median_expansion_ratio": 0.0,
        "timeframe_counts": {},
        "reference_windows": [],
        "response_windows": [],
    }


def _day_profiles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        timestamp = datetime.fromisoformat(str(row["timestamp"]))
        grouped[(str(row["source_timeframe"]), str(row["split"]), timestamp.date().isoformat())].append(row)

    profiles: list[dict[str, Any]] = []
    for key in sorted(grouped):
        source_timeframe, split, day = key
        day_rows = sorted(grouped[key], key=lambda row: str(row["timestamp"]))
        blocks = {
            block_name: _window_metrics(
                [
                    row
                    for row in day_rows
                    if datetime.fromisoformat(str(row["timestamp"])).hour in block_hours
                ]
            )
            for block_name, block_hours in SESSION_BLOCKS.items()
        }
        opening_hour = _window_metrics(
            [row for row in day_rows if datetime.fromisoformat(str(row["timestamp"])).hour == 12]
        )
        post_open = _window_metrics(
            [row for row in day_rows if datetime.fromisoformat(str(row["timestamp"])).hour in {13, 14, 15}]
        )
        first_half = _window_metrics(
            [row for row in day_rows if datetime.fromisoformat(str(row["timestamp"])).hour < 12]
        )
        second_half = _window_metrics(
            [row for row in day_rows if datetime.fromisoformat(str(row["timestamp"])).hour >= 12]
        )
        profiles.append(
            {
                "source_timeframe": source_timeframe,
                "split": split,
                "date": day,
                "blocks": blocks,
                "hour_12_opening_range": opening_hour,
                "hours_13_16_following_range": post_open,
                "first_half_day": first_half,
                "second_half_day": second_half,
            }
        )
    return profiles


def _window_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "row_count": 0,
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "range": 0.0,
            "move": 0.0,
            "abs_move": 0.0,
            "direction": 0,
            "average_bar_range": 0.0,
        }
    ordered = sorted(rows, key=lambda row: str(row["timestamp"]))
    open_price = float(ordered[0]["open"])
    close_price = float(ordered[-1]["close"])
    high = max(float(row["high"]) for row in ordered)
    low = min(float(row["low"]) for row in ordered)
    move = close_price - open_price
    bar_ranges = [float(row["high"]) - float(row["low"]) for row in ordered]
    return {
        "row_count": len(ordered),
        "open": open_price,
        "high": high,
        "low": low,
        "close": close_price,
        "range": high - low,
        "move": move,
        "abs_move": abs(move),
        "direction": _sign(move),
        "average_bar_range": _average(bar_ranges),
    }


def _family_result(day_profiles: list[dict[str, Any]], family: str) -> dict[str, Any]:
    event_builder = {
        "asia_range_to_london_expansion": _asia_to_london_event,
        "london_to_ny_handoff_continuation_or_reversal": _london_to_ny_event,
        "ny_opening_range_followthrough_or_reversal": _ny_opening_range_event,
        "compression_then_expansion": _compression_expansion_event,
        "trend_day_vs_mean_reversion_day_shape": _trend_day_event,
    }[family]
    events = [event for profile in day_profiles if (event := event_builder(profile)) is not None]
    train_result = _split_result([event for event in events if event["split"] == "train"])
    validation_result = _split_result([event for event in events if event["split"] == "validation"])
    stability = _stability_assessment(train_result, validation_result)
    degradation = _degradation_assessment(train_result, validation_result)
    strong = stability["label"] == "stable"
    return {
        "train_result": train_result,
        "validation_result": validation_result,
        "sample_size": {
            "train": train_result["sample_count"],
            "validation": validation_result["sample_count"],
        },
        "stability_assessment": stability,
        "degradation_assessment": degradation,
        "strong_enough_for_future_single_fixed_candidate": strong,
    }


def _asia_to_london_event(profile: dict[str, Any]) -> dict[str, Any] | None:
    early = profile["blocks"]["block_00_06"]
    later = profile["blocks"]["block_06_12"]
    if not _usable_pair(early, later):
        return None
    expansion = later["range"] > early["range"]
    return _event(
        profile,
        label="later_expansion" if expansion else "no_later_expansion",
        primary_value=1.0 if expansion else 0.0,
        expansion_ratio=_safe_ratio(later["range"], early["range"]),
        reference_window="block_00_06",
        response_window="block_06_12",
    )


def _london_to_ny_event(profile: dict[str, Any]) -> dict[str, Any] | None:
    prior = profile["blocks"]["block_06_12"]
    handoff = profile["blocks"]["block_12_18"]
    return _directional_pair_event(profile, prior, handoff, "block_06_12", "block_12_18")


def _ny_opening_range_event(profile: dict[str, Any]) -> dict[str, Any] | None:
    opening = profile["hour_12_opening_range"]
    following = profile["hours_13_16_following_range"]
    return _directional_pair_event(profile, opening, following, "hour_12", "hours_13_16")


def _compression_expansion_event(profile: dict[str, Any]) -> dict[str, Any] | None:
    ordered_blocks = list(SESSION_BLOCKS)
    available = [
        (index, name, profile["blocks"][name])
        for index, name in enumerate(ordered_blocks[:-1])
        if profile["blocks"][name]["row_count"] > 0 and profile["blocks"][ordered_blocks[index + 1]]["row_count"] > 0
    ]
    if not available:
        return None
    index, name, compressed = min(available, key=lambda item: (float(item[2]["average_bar_range"]), item[0]))
    next_name = ordered_blocks[index + 1]
    expanded = profile["blocks"][next_name]
    expansion = expanded["range"] > compressed["range"]
    return _event(
        profile,
        label="next_block_expansion" if expansion else "no_next_block_expansion",
        primary_value=1.0 if expansion else 0.0,
        expansion_ratio=_safe_ratio(expanded["range"], compressed["range"]),
        reference_window=name,
        response_window=next_name,
    )


def _trend_day_event(profile: dict[str, Any]) -> dict[str, Any] | None:
    first = profile["first_half_day"]
    second = profile["second_half_day"]
    return _directional_pair_event(profile, first, second, "hours_00_12", "hours_12_24")


def _directional_pair_event(
    profile: dict[str, Any],
    prior: dict[str, Any],
    later: dict[str, Any],
    reference_window: str,
    response_window: str,
) -> dict[str, Any] | None:
    if not _usable_pair(prior, later) or prior["direction"] == 0 or later["direction"] == 0:
        return None
    continuation = prior["direction"] == later["direction"]
    return _event(
        profile,
        label="continuation" if continuation else "reversal",
        primary_value=1.0 if continuation else 0.0,
        expansion_ratio=_safe_ratio(later["range"], prior["range"]),
        reference_window=reference_window,
        response_window=response_window,
    )


def _event(
    profile: dict[str, Any],
    *,
    label: str,
    primary_value: float,
    expansion_ratio: float,
    reference_window: str,
    response_window: str,
) -> dict[str, Any]:
    return {
        "source_timeframe": profile["source_timeframe"],
        "split": profile["split"],
        "date": profile["date"],
        "label": label,
        "primary_value": primary_value,
        "expansion_ratio": expansion_ratio,
        "reference_window": reference_window,
        "response_window": response_window,
    }


def _split_result(events: list[dict[str, Any]]) -> dict[str, Any]:
    labels = sorted({str(event["label"]) for event in events})
    label_rates = {
        label: _rate(sum(1 for event in events if event["label"] == label), len(events))
        for label in labels
    }
    primary_label, primary_rate = _primary_label_rate(label_rates)
    expansion_ratios = [float(event["expansion_ratio"]) for event in events if event["expansion_ratio"] is not None]
    return {
        "sample_count": len(events),
        "label_rates": label_rates,
        "dominant_behavior": primary_label,
        "primary_metric_rate": primary_rate,
        "edge_over_neutral": primary_rate - 0.5 if events else 0.0,
        "average_expansion_ratio": _average(expansion_ratios),
        "median_expansion_ratio": _median(expansion_ratios),
        "timeframe_counts": _counts(events, "source_timeframe"),
        "reference_windows": sorted({str(event["reference_window"]) for event in events}),
        "response_windows": sorted({str(event["response_window"]) for event in events}),
    }


def _stability_assessment(train_result: dict[str, Any], validation_result: dict[str, Any]) -> dict[str, Any]:
    if train_result["sample_count"] < MIN_TRAIN_SAMPLES or validation_result["sample_count"] < MIN_VALIDATION_SAMPLES:
        return {
            "label": "inconclusive",
            "stable": False,
            "reason": "Fixed minimum train/validation sample sizes were not met.",
        }
    if train_result["dominant_behavior"] != validation_result["dominant_behavior"]:
        return {
            "label": "weak",
            "stable": False,
            "reason": "Dominant train and validation behavior did not match.",
        }
    validation_degradation = float(train_result["primary_metric_rate"]) - float(validation_result["primary_metric_rate"])
    if (
        train_result["edge_over_neutral"] >= MATERIAL_EDGE
        and validation_result["edge_over_neutral"] >= MATERIAL_EDGE
        and validation_degradation <= MAX_VALIDATION_DEGRADATION
    ):
        return {
            "label": "stable",
            "stable": True,
            "reason": "Dominant behavior matched with material train/validation edge and limited degradation.",
        }
    return {
        "label": "weak",
        "stable": False,
        "reason": "Dominant behavior matched, but edge or degradation failed the fixed stability requirements.",
    }


def _degradation_assessment(train_result: dict[str, Any], validation_result: dict[str, Any]) -> dict[str, Any]:
    degradation = float(train_result["primary_metric_rate"]) - float(validation_result["primary_metric_rate"])
    return {
        "primary_metric_train": train_result["primary_metric_rate"],
        "primary_metric_validation": validation_result["primary_metric_rate"],
        "validation_degradation": degradation,
        "within_fixed_limit": degradation <= MAX_VALIDATION_DEGRADATION,
    }


def _strongest_family(family_results: dict[str, Any]) -> dict[str, Any] | None:
    stable = [
        (family, result)
        for family, result in family_results.items()
        if result["strong_enough_for_future_single_fixed_candidate"] is True
    ]
    if not stable:
        return None
    family, result = max(
        stable,
        key=lambda item: (
            float(item[1]["validation_result"]["edge_over_neutral"]),
            int(item[1]["validation_result"]["sample_count"]),
        ),
    )
    return {
        "family": family,
        "dominant_behavior": result["validation_result"]["dominant_behavior"],
        "validation_primary_metric_rate": result["validation_result"]["primary_metric_rate"],
        "validation_edge_over_neutral": result["validation_result"]["edge_over_neutral"],
        "validation_sample_count": result["validation_result"]["sample_count"],
    }


def _recommended_next_step(family_results: dict[str, Any]) -> str:
    labels = [result["stability_assessment"]["label"] for result in family_results.values()]
    if any(label == "stable" for label in labels):
        return "create_one_fixed_session_candidate_v0_26"
    if labels and all(label == "weak" for label in labels):
        return "abandon_session_structure_family"
    return "blocked_inconclusive"


def _data_files_used(catalog: dict[str, Any]) -> list[str]:
    return sorted(
        str(entry["filename"])
        for entry in catalog.get("entries", [])
        if entry.get("usable_for_profiler") is True and entry.get("source_timeframe") in LOW_TF_ALLOWED
    )


def _usable_pair(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return first["row_count"] > 0 and second["row_count"] > 0 and first["range"] > 0


def _primary_label_rate(label_rates: dict[str, float]) -> tuple[str, float]:
    if not label_rates:
        return "insufficient", 0.0
    return max(label_rates.items(), key=lambda item: (item[1], item[0]))


def _counts(events: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        value = str(event[key])
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _average(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _median(values: list[float]) -> float:
    return median(values) if values else 0.0


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0
