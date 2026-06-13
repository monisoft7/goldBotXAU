"""Diagnostic-only low-timeframe spike behavior profiler for XAUUSD."""

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

PROFILER_VERSION = "v0_22"
ATR_PERIOD_BARS = 96
FORWARD_HORIZONS = (1, 3, 6)
MIN_STABLE_SAMPLES = 30
SPIKE_BUCKETS = (
    ("range_to_atr_1_5_to_2_0", 1.5, 2.0),
    ("range_to_atr_2_0_to_3_0", 2.0, 3.0),
    ("range_to_atr_gte_3_0", 3.0, None),
)
SAFETY_FLAGS = {
    "demo_enabled": False,
    "live_enabled": False,
    "order_send_allowed": False,
    "execution_queue_enabled": False,
    "buy_sell_output_allowed": False,
    "execution_logic_present": False,
    "trade_recommendation_output_present": False,
    "research_candidate_logic_present": False,
    "strategy_candidate_created": False,
    "trade_simulation_added": False,
    "oos_evaluated": False,
}


def profile_low_tf_spike_behavior(
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    pattern: str = "xauusd_m*.csv",
) -> dict[str, Any]:
    catalog = build_low_tf_dataset_catalog(data_dir=data_dir, manifest_path=manifest_path, pattern=pattern)
    rows = load_profiler_rows_from_catalog(catalog)
    if not rows:
        return _base_report(
            status="blocked_need_train_validation_low_tf_data",
            catalog=catalog,
            rows=[],
            spike_events=[],
            grouped_behavior=[],
            stability_assessment=_empty_stability_assessment(),
        )

    enriched = _enriched_rows(rows)
    spike_events = [row for row in enriched if row["spike_size_bucket"] is not None]
    grouped_behavior = _grouped_behavior(spike_events)
    stability_assessment = _stability_assessment(grouped_behavior)
    return _base_report(
        status="profile_ready",
        catalog=catalog,
        rows=rows,
        spike_events=spike_events,
        grouped_behavior=grouped_behavior,
        stability_assessment=stability_assessment,
    )


def _base_report(
    *,
    status: str,
    catalog: dict[str, Any],
    rows: list[dict[str, Any]],
    spike_events: list[dict[str, Any]],
    grouped_behavior: list[dict[str, Any]],
    stability_assessment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "profiler_version": PROFILER_VERSION,
        "status": status,
        "purpose": "diagnostic_low_timeframe_spike_behavior_profile_only",
        "dataset": {
            "profiled_splits": ["train", "validation"],
            "train_row_count": sum(1 for row in rows if row.get("split") == "train"),
            "validation_row_count": sum(1 for row in rows if row.get("split") == "validation"),
            "oos_row_count_used": 0,
            "source_timeframes": sorted({str(row["source_timeframe"]) for row in rows}) if rows else [],
        },
        "low_tf_catalog": catalog,
        "spike_definition": {
            "atr_period_bars": ATR_PERIOD_BARS,
            "spike_basis": "candle_range_to_trailing_average_true_range",
            "spike_buckets": [
                {"bucket": name, "range_to_atr_gte": lower, "range_to_atr_lt": upper}
                for name, lower, upper in SPIKE_BUCKETS
            ],
            "forward_horizons_bars": list(FORWARD_HORIZONS),
            "behavior_labels": ["fade", "continuation", "flat_or_unavailable"],
        },
        "event_counts": {
            "spike_event_count": len(spike_events),
            "train_spike_event_count": sum(1 for row in spike_events if row["split"] == "train"),
            "validation_spike_event_count": sum(1 for row in spike_events if row["split"] == "validation"),
        },
        "grouped_behavior": grouped_behavior,
        "stability_assessment": stability_assessment,
        "safety": dict(SAFETY_FLAGS),
        "notes": [
            "This is diagnostic profiling only and does not create a strategy candidate.",
            "OOS-only and mixed OOS files are quarantined by the low-timeframe catalog.",
            "Validation is summarized separately as a held-back check, not used for threshold retuning.",
        ],
    }


def _enriched_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["source_timeframe"]), str(row["split"]))].append(row)

    enriched: list[dict[str, Any]] = []
    for (timeframe, _split), timeframe_rows in grouped.items():
        ordered = sorted(timeframe_rows, key=lambda row: str(row["timestamp"]))
        true_ranges = _true_ranges(ordered)
        for index, row in enumerate(ordered):
            atr = _trailing_average(true_ranges, index, ATR_PERIOD_BARS)
            range_to_atr = _safe_ratio(_range(row), atr)
            hour = datetime.fromisoformat(row["timestamp"]).hour
            enriched_row = {
                **row,
                "source_timeframe": timeframe,
                "atr": atr,
                "range_to_atr": range_to_atr,
                "spike_size_bucket": _spike_bucket(range_to_atr),
                "hour_bucket": f"{hour:02d}",
                "session_bucket": _session_bucket(hour),
                "event_direction": _sign(float(row["close"]) - float(row["open"])),
            }
            for horizon in FORWARD_HORIZONS:
                enriched_row[f"forward_{horizon}bar_behavior"] = _forward_behavior(ordered, index, horizon, atr)
            enriched.append(enriched_row)
    return sorted(enriched, key=lambda row: (str(row["source_timeframe"]), str(row["timestamp"])))


def _grouped_behavior(spike_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in spike_events:
        grouped[
            (
                str(event["source_timeframe"]),
                str(event["spike_size_bucket"]),
                str(event["session_bucket"]),
                str(event["hour_bucket"]),
            )
        ].append(event)

    summaries: list[dict[str, Any]] = []
    for key in sorted(grouped):
        source_timeframe, spike_size_bucket, session_bucket, hour_bucket = key
        events = grouped[key]
        train_events = [event for event in events if event["split"] == "train"]
        validation_events = [event for event in events if event["split"] == "validation"]
        train_result = _split_result(train_events)
        validation_result = _split_result(validation_events)
        summaries.append(
            {
                "source_timeframe": source_timeframe,
                "spike_size_bucket": spike_size_bucket,
                "session_bucket": session_bucket,
                "hour_bucket": hour_bucket,
                "train_result": train_result,
                "validation_result": validation_result,
                "stable_enough_for_future_fixed_candidate": _stable_pair(train_result, validation_result),
            }
        )
    return summaries


def _split_result(events: list[dict[str, Any]]) -> dict[str, Any]:
    horizon_results = {f"forward_{horizon}bar": _horizon_result(events, horizon) for horizon in FORWARD_HORIZONS}
    primary = horizon_results["forward_3bar"]
    tendency = _dominant_tendency(primary)
    return {
        "sample_count": len(events),
        "median_range_to_atr": _median([float(event["range_to_atr"]) for event in events if event["range_to_atr"] is not None]),
        "forward_behavior": horizon_results,
        "fade_vs_continuation_tendency": tendency,
    }


def _horizon_result(events: list[dict[str, Any]], horizon: int) -> dict[str, Any]:
    behaviors = [event[f"forward_{horizon}bar_behavior"] for event in events]
    usable = [behavior for behavior in behaviors if behavior["label"] != "flat_or_unavailable"]
    fade_count = sum(1 for behavior in usable if behavior["label"] == "fade")
    continuation_count = sum(1 for behavior in usable if behavior["label"] == "continuation")
    moves = [float(behavior["move_to_atr"]) for behavior in usable if behavior["move_to_atr"] is not None]
    total = len(usable)
    return {
        "usable_count": total,
        "fade_rate": fade_count / total if total else 0.0,
        "continuation_rate": continuation_count / total if total else 0.0,
        "average_forward_move_to_atr": _average(moves),
        "median_forward_move_to_atr": _median(moves),
    }


def _stability_assessment(grouped_behavior: list[dict[str, Any]]) -> dict[str, Any]:
    stable_groups = [group for group in grouped_behavior if group["stable_enough_for_future_fixed_candidate"] is True]
    if stable_groups:
        action = "consider_future_fixed_candidate"
        rationale = "At least one fixed timeframe/bucket/session/hour group has matching train and validation tendency."
    elif grouped_behavior:
        action = "abandon_or_continue_diagnostics_before_any_candidate"
        rationale = "No grouped behavior met the fixed stability requirements."
    else:
        action = "blocked_no_spike_events"
        rationale = "No spike events were available after split-safe filtering."
    return {
        "stable_group_count": len(stable_groups),
        "stable_groups": stable_groups[:20],
        "recommended_v0_23_action": action,
        "rationale": rationale,
        "minimum_stable_samples_per_split": MIN_STABLE_SAMPLES,
    }


def _empty_stability_assessment() -> dict[str, Any]:
    return {
        "stable_group_count": 0,
        "stable_groups": [],
        "recommended_v0_23_action": "blocked_need_train_validation_low_tf_data",
        "rationale": "No train/validation low-timeframe rows were available to profile.",
        "minimum_stable_samples_per_split": MIN_STABLE_SAMPLES,
    }


def _true_ranges(rows: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    previous_close: float | None = None
    for row in rows:
        current_range = _range(row)
        if previous_close is None:
            values.append(current_range)
        else:
            values.append(max(current_range, abs(float(row["high"]) - previous_close), abs(float(row["low"]) - previous_close)))
        previous_close = float(row["close"])
    return values


def _trailing_average(values: list[float], index: int, period: int) -> float | None:
    if index < period:
        return None
    window = values[index - period : index]
    return mean(window) if window else None


def _forward_behavior(rows: list[dict[str, Any]], index: int, horizon: int, atr: float | None) -> dict[str, Any]:
    final_index = index + horizon
    if final_index >= len(rows) or atr is None or atr <= 0:
        return {"label": "flat_or_unavailable", "move_to_atr": None}
    event_direction = _sign(float(rows[index]["close"]) - float(rows[index]["open"]))
    forward_move = float(rows[final_index]["close"]) - float(rows[index]["close"])
    forward_direction = _sign(forward_move)
    if event_direction == 0 or forward_direction == 0:
        label = "flat_or_unavailable"
    elif event_direction == forward_direction:
        label = "continuation"
    else:
        label = "fade"
    return {"label": label, "move_to_atr": forward_move / atr}


def _stable_pair(train_result: dict[str, Any], validation_result: dict[str, Any]) -> bool:
    if train_result["sample_count"] < MIN_STABLE_SAMPLES or validation_result["sample_count"] < MIN_STABLE_SAMPLES:
        return False
    train_primary = train_result["forward_behavior"]["forward_3bar"]
    validation_primary = validation_result["forward_behavior"]["forward_3bar"]
    train_tendency = train_result["fade_vs_continuation_tendency"]
    validation_tendency = validation_result["fade_vs_continuation_tendency"]
    if train_tendency not in {"fade", "continuation"} or train_tendency != validation_tendency:
        return False
    metric = f"{train_tendency}_rate"
    return abs(float(train_primary[metric]) - float(validation_primary[metric])) <= 0.20


def _dominant_tendency(metrics: dict[str, Any]) -> str:
    fade_rate = float(metrics["fade_rate"])
    continuation_rate = float(metrics["continuation_rate"])
    if metrics["usable_count"] <= 0 or abs(fade_rate - continuation_rate) < 0.05:
        return "mixed_or_insufficient"
    return "fade" if fade_rate > continuation_rate else "continuation"


def _spike_bucket(range_to_atr: float | None) -> str | None:
    if range_to_atr is None:
        return None
    for name, lower, upper in SPIKE_BUCKETS:
        if range_to_atr >= lower and (upper is None or range_to_atr < upper):
            return name
    return None


def _session_bucket(hour: int) -> str:
    if hour < 6:
        return "block_00_06"
    if hour < 12:
        return "block_06_12"
    if hour < 18:
        return "block_12_18"
    return "block_18_24"


def _range(row: dict[str, Any]) -> float:
    return float(row["high"]) - float(row["low"])


def _safe_ratio(numerator: float, denominator: float | None) -> float | None:
    if denominator is None or denominator <= 0:
        return None
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
