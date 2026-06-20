"""v0_54 empirical XAUUSD edge profiler.

This module maps fixed event behavior on train/validation data only. It does
not create strategy candidates, run OOS, or evaluate executable trade rules.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from statistics import mean
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_csv

PROFILER_VERSION = "v0_54"
SOURCE_PREVIOUS_BOARD_VERSION = "v0_53"
PURPOSE = "empirical_edge_mapping_not_strategy_backtest"
DEFAULT_OUTPUT = Path("reports") / "xauusd_edge_profiler_v0_54.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"
DEFAULT_SOURCE_BOARD = Path("reports") / "xauusd_external_shortlist_board_v0_53.json"

COMPLETED_WITH_LEADS = "edge_profile_completed_with_research_leads"
COMPLETED_NO_CLEAR_LEADS = "edge_profile_completed_no_clear_leads"
BLOCKED_MISSING_DATA = "blocked_missing_required_data"
PROFILER_FAILED = "profiler_failed"

EVENT_FAMILIES = (
    "session_return_profile",
    "prior_day_high_low_sweep_profile",
    "asian_range_breakout_profile",
    "london_opening_candle_profile",
    "ny_first_hour_profile",
    "failed_m15_swing_breakout_profile",
    "sequential_m5_move_profile",
    "volatility_regime_profile",
)

M15_HORIZONS = (1, 2, 4, 8)
M5_HORIZONS = (1, 3, 6, 12)
MIN_EVENTS_PER_SPLIT_FOR_CLEAR_LEAD = 20


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    split: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str


@dataclass(frozen=True)
class EventObservation:
    event_family_id: str
    split: str
    timestamp: datetime
    behavior: str
    returns: dict[str, float]


def build_xauusd_edge_profiler_v0_54(
    *,
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_board_path: str | Path = DEFAULT_SOURCE_BOARD,
    m15_pattern: str = "xauusd_m15_*.csv",
    m5_pattern: str = "xauusd_m5_xauusd_*.csv",
) -> dict[str, Any]:
    """Build fixed empirical event profiles from existing train/validation rows."""
    try:
        manifest = _read_json(Path(manifest_path))
        source_board = _read_json(Path(source_board_path))
        blockers = [*_manifest_blockers(manifest), *_source_blockers(source_board)]
        if blockers:
            return _blocked_report(blockers)

        assert manifest is not None
        m15, m15_files, m15_counts = _load_candles(data_dir, m15_pattern, manifest, "M15")
        m5, m5_files, m5_counts = _load_candles(data_dir, m5_pattern, manifest, "M5")
        m15_eval = [candle for candle in m15 if candle.split in {"train", "validation"}]
        m5_eval = [candle for candle in m5 if candle.split in {"train", "validation"}]

        data_blockers: list[str] = []
        if not m15_files or not m15_eval:
            data_blockers.append("train_validation_m15_rows_missing")
        if not m5_files or not m5_eval:
            data_blockers.append("train_validation_m5_rows_missing")
        if data_blockers:
            report = _blocked_report(data_blockers)
            report["data_ranges_used"] = _data_ranges(m15_eval, m5_eval)
            report["timeframes_used"] = _timeframes_used(m15_eval, m5_eval)
            report["data_files_used"] = [*[path.as_posix() for path in m15_files], *[path.as_posix() for path in m5_files]]
            report["split_candle_counts"] = {"M15": m15_counts, "M5": m5_counts}
            return report

        family_events = {
            "session_return_profile": _session_return_events(m15_eval),
            "prior_day_high_low_sweep_profile": _prior_day_sweep_events(m15_eval),
            "asian_range_breakout_profile": _asian_range_breakout_events(m15_eval),
            "london_opening_candle_profile": _london_opening_candle_events(m15_eval),
            "ny_first_hour_profile": _ny_first_hour_events(m15_eval),
            "failed_m15_swing_breakout_profile": _failed_m15_swing_events(m15_eval),
            "sequential_m5_move_profile": _sequential_m5_events(m5_eval),
            "volatility_regime_profile": _volatility_regime_events(m15_eval),
        }
        results = [_family_result(family_id, family_events[family_id]) for family_id in EVENT_FAMILIES]
        leads = _strongest_leads(results)
        status = COMPLETED_WITH_LEADS if leads else COMPLETED_NO_CLEAR_LEADS
        next_step = (
            "v0_55 fixed-rule candidate design for top 1-2 leads, no OOS"
            if leads
            else "stop current branch or broaden data/features"
        )

        return _base_report(
            profiler_status=status,
            event_family_results=results,
            data_ranges_used=_data_ranges(m15_eval, m5_eval),
            timeframes_used=_timeframes_used(m15_eval, m5_eval),
            data_files_used=[*[path.as_posix() for path in m15_files], *[path.as_posix() for path in m5_files]],
            split_candle_counts={"M15": m15_counts, "M5": m5_counts},
            blockers=[],
            warnings=_top_level_warnings(results, m15_counts, m5_counts),
            next_recommended_step=next_step,
        )
    except Exception as exc:
        return _base_report(
            profiler_status=PROFILER_FAILED,
            event_family_results=[],
            data_ranges_used={},
            timeframes_used=[],
            data_files_used=[],
            split_candle_counts={},
            blockers=[f"profiler_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair v0_54 profiler implementation or input artifacts before continuing",
        )


def save_xauusd_edge_profiler(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _blocked_report(blockers: list[str]) -> dict[str, Any]:
    return _base_report(
        profiler_status=BLOCKED_MISSING_DATA,
        event_family_results=[],
        data_ranges_used={},
        timeframes_used=[],
        data_files_used=[],
        split_candle_counts={},
        blockers=blockers,
        warnings=[],
        next_recommended_step="restore required train/validation M15/M5 data and v0_53 board report before rerunning v0_54",
    )


def _base_report(
    *,
    profiler_status: str,
    event_family_results: list[dict[str, Any]],
    data_ranges_used: dict[str, Any],
    timeframes_used: list[str],
    data_files_used: list[str],
    split_candle_counts: dict[str, Any],
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    leads = _strongest_leads(event_family_results)
    weak = [result["event_family_id"] for result in event_family_results if result.get("recommended_action") == "reject_as_weak_or_unstable"]
    return {
        "profiler_version": PROFILER_VERSION,
        "profiler_status": profiler_status,
        "source_previous_board_version": SOURCE_PREVIOUS_BOARD_VERSION,
        "purpose": PURPOSE,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "data_csv_added_to_git": False,
        "data_ranges_used": data_ranges_used,
        "timeframes_used": timeframes_used,
        "data_files_used": data_files_used,
        "split_candle_counts": split_candle_counts,
        "event_families_profiled": list(EVENT_FAMILIES),
        "event_family_results": event_family_results,
        "strongest_empirical_leads": leads,
        "rejected_or_weak_leads": weak,
        "sample_size_warnings": _collect_notes(event_family_results, "sample_size_warnings"),
        "concentration_warnings": _collect_notes(event_family_results, "concentration_warnings"),
        "implementation_warnings": [
            "fixed_utc_ny_first_hour_fallback_used_no_dst_model",
            "volatility_quartiles_are_descriptive_labels_not_optimized_thresholds",
        ],
        "recommended_v0_55_research_plan": _research_plan(leads),
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def _family_result(event_family_id: str, events: list[EventObservation]) -> dict[str, Any]:
    train = [event for event in events if event.split == "train"]
    validation = [event for event in events if event.split == "validation"]
    horizons = _horizons(events)
    primary_horizon = horizons[-1] if horizons else "none"
    train_summary = _split_summary(train, primary_horizon)
    validation_summary = _split_summary(validation, primary_horizon)
    sample_notes = _sample_notes(event_family_id, train, validation)
    concentration_notes = _concentration_notes(event_family_id, events)
    score = _suitability_score(
        event_family_id=event_family_id,
        train_summary=train_summary,
        validation_summary=validation_summary,
        event_count_train=len(train),
        event_count_validation=len(validation),
    )
    action = _recommended_action(score, len(train), len(validation))
    return {
        "event_family_id": event_family_id,
        "event_count_train": len(train),
        "event_count_validation": len(validation),
        "total_event_count": len(events),
        "direction_or_behavior_measured": _behavior_measured(event_family_id),
        "forward_horizons_measured": horizons,
        "train_summary": train_summary,
        "validation_summary": validation_summary,
        "stability_notes": _stability_notes(train_summary, validation_summary),
        "sample_concentration_notes": concentration_notes,
        "sample_size_warnings": sample_notes,
        "concentration_warnings": concentration_notes,
        "candidate_suitability_score": score,
        "recommended_action": action,
    }


def _session_return_events(candles: list[Candle]) -> list[EventObservation]:
    blocks = {
        "asian_00_06": (time(0, 0), time(7, 0)),
        "london_morning_07_11": (time(7, 0), time(12, 0)),
        "ny_core_12_16": (time(12, 0), time(17, 0)),
        "late_us_17_20": (time(17, 0), time(21, 0)),
    }
    events: list[EventObservation] = []
    for _day, day_candles in _by_day(candles).items():
        for block_id, (start, end) in blocks.items():
            block = [candle for candle in day_candles if _in_window(candle.timestamp, start, end)]
            if not block:
                continue
            events.append(
                EventObservation(
                    event_family_id="session_return_profile",
                    split=block[0].split,
                    timestamp=block[0].timestamp,
                    behavior=block_id,
                    returns={
                        "block_return_points": block[-1].close - block[0].open,
                        "block_range_points": max(candle.high for candle in block) - min(candle.low for candle in block),
                    },
                )
            )
    return events


def _prior_day_sweep_events(candles: list[Candle]) -> list[EventObservation]:
    grouped = _by_day(candles)
    days = sorted(grouped)
    events: list[EventObservation] = []
    for index, day in enumerate(days[1:], start=1):
        previous = grouped[days[index - 1]]
        current = grouped[day]
        previous_high = max(candle.high for candle in previous)
        previous_low = min(candle.low for candle in previous)
        long_done = False
        short_done = False
        for candle_index, candle in enumerate(current):
            if candle.high > previous_high and candle.close < previous_high and not short_done:
                events.append(_m15_forward_event("prior_day_high_low_sweep_profile", candle, current, candle_index, -1.0, "high_sweep_close_back_below"))
                short_done = True
            if candle.low < previous_low and candle.close > previous_low and not long_done:
                events.append(_m15_forward_event("prior_day_high_low_sweep_profile", candle, current, candle_index, 1.0, "low_sweep_close_back_above"))
                long_done = True
    return events


def _asian_range_breakout_events(candles: list[Candle]) -> list[EventObservation]:
    events: list[EventObservation] = []
    for _day, day_candles in _by_day(candles).items():
        asian = [candle for candle in day_candles if _in_window(candle.timestamp, time(0, 0), time(7, 0))]
        if not asian:
            continue
        high = max(candle.high for candle in asian)
        low = min(candle.low for candle in asian)
        high_done = False
        low_done = False
        for index, candle in enumerate(day_candles):
            if not _in_window(candle.timestamp, time(7, 0), time(20, 0)):
                continue
            if candle.close > high and not high_done:
                events.append(_m15_forward_event("asian_range_breakout_profile", candle, day_candles, index, 1.0, "close_above_asian_range"))
                high_done = True
            if candle.close < low and not low_done:
                events.append(_m15_forward_event("asian_range_breakout_profile", candle, day_candles, index, -1.0, "close_below_asian_range"))
                low_done = True
    return events


def _london_opening_candle_events(candles: list[Candle]) -> list[EventObservation]:
    events: list[EventObservation] = []
    for _day, day_candles in _by_day(candles).items():
        candle = _at_time(day_candles, time(7, 0))
        if candle is None:
            continue
        candle_range = max(candle.high - candle.low, 0.0)
        if candle_range <= 0.0:
            continue
        direction = 1.0 if candle.close > candle.open else -1.0 if candle.close < candle.open else 0.0
        if direction == 0.0:
            continue
        bucket = _body_bucket(abs(candle.close - candle.open) / candle_range)
        later = [item for item in day_candles if time(7, 15) <= item.timestamp.time() < time(12, 0)]
        if not later:
            continue
        events.append(
            EventObservation(
                event_family_id="london_opening_candle_profile",
                split=candle.split,
                timestamp=candle.timestamp,
                behavior=f"{'up' if direction > 0 else 'down'}_{bucket}",
                returns={"follow_fade_07_15_12_00": direction * (later[-1].close - later[0].open)},
            )
        )
    return events


def _ny_first_hour_events(candles: list[Candle]) -> list[EventObservation]:
    events: list[EventObservation] = []
    for _day, day_candles in _by_day(candles).items():
        first_hour = [candle for candle in day_candles if _in_window(candle.timestamp, time(13, 0), time(14, 0))]
        later = [candle for candle in day_candles if _in_window(candle.timestamp, time(14, 0), time(17, 0))]
        if not first_hour or not later:
            continue
        direction = 1.0 if first_hour[-1].close > first_hour[0].open else -1.0 if first_hour[-1].close < first_hour[0].open else 0.0
        if direction == 0.0:
            continue
        events.append(
            EventObservation(
                event_family_id="ny_first_hour_profile",
                split=first_hour[0].split,
                timestamp=first_hour[0].timestamp,
                behavior="fixed_13_00_14_00_up" if direction > 0 else "fixed_13_00_14_00_down",
                returns={"continuation_14_00_17_00": direction * (later[-1].close - later[0].open)},
            )
        )
    return events


def _failed_m15_swing_events(candles: list[Candle]) -> list[EventObservation]:
    events: list[EventObservation] = []
    for index in range(20, len(candles)):
        window = candles[index - 20 : index]
        candle = candles[index]
        if candle.split not in {"train", "validation"}:
            continue
        prior_high = max(item.high for item in window)
        prior_low = min(item.low for item in window)
        if candle.high > prior_high and candle.close < prior_high:
            events.append(_m15_forward_event("failed_m15_swing_breakout_profile", candle, candles, index, -1.0, "failed_high_breakout"))
        elif candle.low < prior_low and candle.close > prior_low:
            events.append(_m15_forward_event("failed_m15_swing_breakout_profile", candle, candles, index, 1.0, "failed_low_breakout"))
    return events


def _sequential_m5_events(candles: list[Candle]) -> list[EventObservation]:
    events: list[EventObservation] = []
    for streak in (3, 5, 7):
        for index in range(streak - 1, len(candles)):
            window = candles[index - streak + 1 : index + 1]
            if len({item.split for item in window}) != 1 or window[-1].split not in {"train", "validation"}:
                continue
            directions = [_direction(item.close - item.open) for item in window]
            if directions[0] == 0 or any(direction != directions[0] for direction in directions):
                continue
            sign = float(directions[0])
            returns = {
                f"horizon_{horizon}_m5_bars": _forward_return(candles, index, horizon, sign)
                for horizon in M5_HORIZONS
                if index + horizon < len(candles) and candles[index + horizon].split == window[-1].split
            }
            if returns:
                events.append(
                    EventObservation(
                        event_family_id="sequential_m5_move_profile",
                        split=window[-1].split,
                        timestamp=window[-1].timestamp,
                        behavior=f"{streak}_bar_{'up' if sign > 0 else 'down'}_streak",
                        returns=returns,
                    )
                )
    return events


def _volatility_regime_events(candles: list[Candle]) -> list[EventObservation]:
    day_ranges: dict[str, float] = {}
    day_rows = _by_day(candles)
    for day, rows in day_rows.items():
        day_ranges[day] = max(item.high for item in rows) - min(item.low for item in rows)
    values = sorted(day_ranges.values())
    if len(values) < 4:
        return []
    q1, q2, q3 = _quartiles(values)
    events: list[EventObservation] = []
    for day, rows in day_rows.items():
        label = _vol_label(day_ranges[day], q1, q2, q3)
        events.append(
            EventObservation(
                event_family_id="volatility_regime_profile",
                split=rows[0].split,
                timestamp=rows[0].timestamp,
                behavior=label,
                returns={"same_day_close_open_points": rows[-1].close - rows[0].open},
            )
        )
    return events


def _m15_forward_event(
    family_id: str,
    candle: Candle,
    candles: list[Candle],
    index: int,
    sign: float,
    behavior: str,
) -> EventObservation:
    returns = {
        f"horizon_{horizon}_m15_bars": _forward_return(candles, index, horizon, sign)
        for horizon in M15_HORIZONS
        if index + horizon < len(candles) and candles[index + horizon].split == candle.split
    }
    same_day = [item for item in candles[index + 1 :] if item.timestamp.date() == candle.timestamp.date() and item.timestamp.time() < time(20, 0)]
    if same_day:
        returns["same_day_to_20_00"] = sign * (same_day[-1].close - candle.close)
    return EventObservation(family_id, candle.split, candle.timestamp, behavior, returns)


def _split_summary(events: list[EventObservation], primary_horizon: str) -> dict[str, Any]:
    behavior_summaries: dict[str, Any] = {}
    for behavior in sorted({event.behavior for event in events}):
        behavior_events = [event for event in events if event.behavior == behavior]
        horizons = sorted({horizon for event in behavior_events for horizon in event.returns})
        behavior_summaries[behavior] = {
            "event_count": len(behavior_events),
            "mean_return_points_by_horizon": {
                horizon: _mean([event.returns[horizon] for event in behavior_events if horizon in event.returns])
                for horizon in horizons
            },
            "positive_rate_by_horizon": {
                horizon: _rate(sum(1 for event in behavior_events if event.returns.get(horizon, 0.0) > 0.0), sum(1 for event in behavior_events if horizon in event.returns))
                for horizon in horizons
            },
        }
    dominant = _dominant_behavior(behavior_summaries, primary_horizon)
    primary_mean = (
        behavior_summaries.get(dominant, {}).get("mean_return_points_by_horizon", {}).get(primary_horizon, 0.0)
        if dominant
        else 0.0
    )
    return {
        "event_count": len(events),
        "primary_horizon": primary_horizon,
        "dominant_behavior": dominant,
        "dominant_behavior_mean_return_points": primary_mean,
        "behavior_summaries": behavior_summaries,
    }


def _suitability_score(
    *,
    event_family_id: str,
    train_summary: dict[str, Any],
    validation_summary: dict[str, Any],
    event_count_train: int,
    event_count_validation: int,
) -> dict[str, Any]:
    consistency = _consistency_score(train_summary, validation_summary)
    asymmetry = _asymmetry_score(train_summary, validation_summary)
    dimensions = {
        "sample_size": _sample_size_score(event_count_train, event_count_validation),
        "train_validation_consistency": consistency,
        "directional_asymmetry": asymmetry,
        "structural_market_logic": _structural_score(event_family_id),
        "implementation_clarity": _implementation_score(event_family_id),
        "difference_from_failed_candidates": _difference_score(event_family_id),
        "oos_safety": 5,
    }
    return {"dimensions": dimensions, "total_score": sum(dimensions.values()), "score_range": "0_to_5_each_dimension"}


def _recommended_action(score: dict[str, Any], train_count: int, validation_count: int) -> str:
    dimensions = score["dimensions"]
    if (
        train_count >= MIN_EVENTS_PER_SPLIT_FOR_CLEAR_LEAD
        and validation_count >= MIN_EVENTS_PER_SPLIT_FOR_CLEAR_LEAD
        and score["total_score"] >= 27
        and dimensions["train_validation_consistency"] >= 3
        and dimensions["directional_asymmetry"] >= 3
    ):
        return "promote_to_fixed_rule_candidate_design"
    if score["total_score"] >= 21 and train_count >= 10 and validation_count >= 10:
        return "keep_for_observation_only"
    return "reject_as_weak_or_unstable"


def _strongest_leads(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    promoted = [result for result in results if result.get("recommended_action") == "promote_to_fixed_rule_candidate_design"]
    ranked = sorted(
        promoted,
        key=lambda item: (
            item["candidate_suitability_score"]["total_score"],
            item["event_count_validation"],
            abs(float(item["validation_summary"]["dominant_behavior_mean_return_points"])),
        ),
        reverse=True,
    )
    return [
        {
            "event_family_id": item["event_family_id"],
            "candidate_suitability_total_score": item["candidate_suitability_score"]["total_score"],
            "dominant_behavior": item["validation_summary"]["dominant_behavior"],
            "validation_primary_mean_return_points": item["validation_summary"]["dominant_behavior_mean_return_points"],
            "recommended_v0_55_focus": f"design one fixed-rule candidate around {item['event_family_id']} dominant behavior only; no OOS",
        }
        for item in ranked[:2]
    ]


def _research_plan(leads: list[dict[str, Any]]) -> list[str]:
    if not leads:
        return ["No v0_55 candidate design yet; stop current branch or broaden non-OOS descriptive features."]
    return [
        f"v0_55 fixed-rule candidate design for {lead['event_family_id']} using predeclared train/validation-only rules; no OOS"
        for lead in leads
    ]


def _load_candles(
    data_dir: str | Path,
    pattern: str,
    manifest: dict[str, Any],
    timeframe: str,
) -> tuple[list[Candle], list[Path], dict[str, int]]:
    root = Path(data_dir)
    files = sorted(root.glob(pattern)) if root.exists() else []
    records: list[dict[str, float | str]] = []
    for file_path in files:
        records.extend(load_xauusd_csv(file_path))
    candles = [_record_to_candle(record, manifest, timeframe) for record in records]
    candles = sorted(candles, key=lambda candle: candle.timestamp)
    counts = {"train": 0, "validation": 0, "excluded_oos": 0, "other": 0}
    for candle in candles:
        counts[candle.split] += 1
    return candles, files, counts


def _record_to_candle(record: dict[str, float | str], manifest: dict[str, Any], timeframe: str) -> Candle:
    timestamp = _dt(str(record["timestamp"]))
    split = _split(timestamp, manifest)
    return Candle(
        timestamp=timestamp,
        split=split,
        open=float(record["open"]),
        high=float(record["high"]),
        low=float(record["low"]),
        close=float(record["close"]),
        volume=float(record["volume"]),
        timeframe=timeframe,
    )


def _split(timestamp: datetime, manifest: dict[str, Any]) -> str:
    policy = manifest["split_policy"]
    if timestamp <= _dt(str(policy["train_end"])):
        return "train"
    if _dt(str(policy["validation_start"])) <= timestamp <= _dt(str(policy["validation_end"])):
        return "validation"
    if timestamp >= _dt(str(policy["oos_start"])):
        return "excluded_oos"
    return "other"


def _data_ranges(m15: list[Candle], m5: list[Candle]) -> dict[str, Any]:
    return {
        "M15": _range_for(m15),
        "M5": _range_for(m5),
    }


def _range_for(candles: list[Candle]) -> dict[str, Any]:
    train = [candle for candle in candles if candle.split == "train"]
    validation = [candle for candle in candles if candle.split == "validation"]
    return {
        "train_start": train[0].timestamp.isoformat() if train else None,
        "train_end": train[-1].timestamp.isoformat() if train else None,
        "validation_start": validation[0].timestamp.isoformat() if validation else None,
        "validation_end": validation[-1].timestamp.isoformat() if validation else None,
    }


def _timeframes_used(m15: list[Candle], m5: list[Candle]) -> list[str]:
    used: list[str] = []
    if m15:
        used.append("M15")
    if m5:
        used.append("M5")
    return used


def _top_level_warnings(results: list[dict[str, Any]], m15_counts: dict[str, int], m5_counts: dict[str, int]) -> list[str]:
    warnings = [
        "empirical_profiler_only_not_strategy_backtest",
        "oos_rows_explicitly_excluded_from_event_statistics",
        "ny_first_hour_uses_fixed_13_00_14_00_utc_fallback_no_dst_handling",
    ]
    if m15_counts.get("excluded_oos", 0):
        warnings.append(f"m15_excluded_oos_candle_count:{m15_counts['excluded_oos']}")
    if m5_counts.get("excluded_oos", 0):
        warnings.append(f"m5_excluded_oos_candle_count:{m5_counts['excluded_oos']}")
    if not _strongest_leads(results):
        warnings.append("no_event_family_promoted_to_strategy_candidate_design")
    return warnings


def _sample_notes(event_family_id: str, train: list[EventObservation], validation: list[EventObservation]) -> list[str]:
    notes: list[str] = []
    if len(train) < MIN_EVENTS_PER_SPLIT_FOR_CLEAR_LEAD:
        notes.append(f"{event_family_id}:train_event_count_below_clear_lead_floor")
    if len(validation) < MIN_EVENTS_PER_SPLIT_FOR_CLEAR_LEAD:
        notes.append(f"{event_family_id}:validation_event_count_below_clear_lead_floor")
    return notes


def _concentration_notes(event_family_id: str, events: list[EventObservation]) -> list[str]:
    notes: list[str] = []
    for split in ("train", "validation"):
        split_events = [event for event in events if event.split == split]
        max_share = _max_month_share(split_events)
        if split_events and max_share > 0.50:
            notes.append(f"{event_family_id}:{split}_events_concentrated_in_single_month")
    return notes


def _stability_notes(train_summary: dict[str, Any], validation_summary: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    if train_summary["dominant_behavior"] == validation_summary["dominant_behavior"] and train_summary["dominant_behavior"]:
        notes.append("dominant_behavior_consistent_train_validation")
    else:
        notes.append("dominant_behavior_differs_between_train_validation")
    if _same_sign(train_summary["dominant_behavior_mean_return_points"], validation_summary["dominant_behavior_mean_return_points"]):
        notes.append("dominant_behavior_mean_return_same_sign")
    else:
        notes.append("dominant_behavior_mean_return_sign_unstable")
    return notes


def _collect_notes(results: list[dict[str, Any]], key: str) -> list[str]:
    notes: list[str] = []
    for result in results:
        notes.extend(result.get(key, []))
    return notes


def _horizons(events: list[EventObservation]) -> list[str]:
    return sorted({horizon for event in events for horizon in event.returns})


def _dominant_behavior(behavior_summaries: dict[str, Any], primary_horizon: str) -> str | None:
    candidates = [
        (behavior, abs(float(summary["mean_return_points_by_horizon"].get(primary_horizon, 0.0))), summary["event_count"])
        for behavior, summary in behavior_summaries.items()
        if primary_horizon in summary["mean_return_points_by_horizon"]
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[1], item[2], item[0]))[0]


def _behavior_measured(event_family_id: str) -> str:
    mapping = {
        "session_return_profile": "fixed_session_block_return_and_range",
        "prior_day_high_low_sweep_profile": "failed_prior_day_sweep_fade_after_fixed_horizons",
        "asian_range_breakout_profile": "asian_range_breakout_continuation_after_fixed_horizons",
        "london_opening_candle_profile": "opening_candle_follow_or_fade_into_12_00",
        "ny_first_hour_profile": "fixed_13_00_14_00_utc_first_hour_follow_or_fade",
        "failed_m15_swing_breakout_profile": "failed_20_candle_swing_breakout_reversal_after_fixed_horizons",
        "sequential_m5_move_profile": "fixed_3_5_7_m5_streak_continuation_after_fixed_horizons",
        "volatility_regime_profile": "descriptive_daily_range_quartile_behavior",
    }
    return mapping[event_family_id]


def _sample_size_score(train_count: int, validation_count: int) -> int:
    floor = min(train_count, validation_count)
    if floor >= 100:
        return 5
    if floor >= 50:
        return 4
    if floor >= 20:
        return 3
    if floor >= 10:
        return 2
    if floor > 0:
        return 1
    return 0


def _consistency_score(train_summary: dict[str, Any], validation_summary: dict[str, Any]) -> int:
    same_behavior = train_summary["dominant_behavior"] == validation_summary["dominant_behavior"] and train_summary["dominant_behavior"] is not None
    same_sign = _same_sign(train_summary["dominant_behavior_mean_return_points"], validation_summary["dominant_behavior_mean_return_points"])
    if same_behavior and same_sign:
        return 5
    if same_sign:
        return 3
    if same_behavior:
        return 2
    return 1


def _asymmetry_score(train_summary: dict[str, Any], validation_summary: dict[str, Any]) -> int:
    magnitude = min(
        abs(float(train_summary["dominant_behavior_mean_return_points"])),
        abs(float(validation_summary["dominant_behavior_mean_return_points"])),
    )
    if magnitude >= 2.0:
        return 5
    if magnitude >= 1.0:
        return 4
    if magnitude >= 0.35:
        return 3
    if magnitude >= 0.1:
        return 2
    if magnitude > 0:
        return 1
    return 0


def _structural_score(event_family_id: str) -> int:
    return {
        "session_return_profile": 4,
        "prior_day_high_low_sweep_profile": 5,
        "asian_range_breakout_profile": 5,
        "london_opening_candle_profile": 4,
        "ny_first_hour_profile": 4,
        "failed_m15_swing_breakout_profile": 4,
        "sequential_m5_move_profile": 3,
        "volatility_regime_profile": 3,
    }[event_family_id]


def _implementation_score(event_family_id: str) -> int:
    return 4 if event_family_id in {"ny_first_hour_profile", "volatility_regime_profile"} else 5


def _difference_score(event_family_id: str) -> int:
    return {
        "session_return_profile": 5,
        "prior_day_high_low_sweep_profile": 3,
        "asian_range_breakout_profile": 3,
        "london_opening_candle_profile": 3,
        "ny_first_hour_profile": 5,
        "failed_m15_swing_breakout_profile": 4,
        "sequential_m5_move_profile": 5,
        "volatility_regime_profile": 5,
    }[event_family_id]


def _by_day(candles: list[Candle]) -> dict[str, list[Candle]]:
    grouped: dict[str, list[Candle]] = {}
    for candle in candles:
        grouped.setdefault(candle.timestamp.date().isoformat(), []).append(candle)
    return {day: sorted(rows, key=lambda item: item.timestamp) for day, rows in sorted(grouped.items())}


def _at_time(candles: list[Candle], value: time) -> Candle | None:
    return next((candle for candle in candles if candle.timestamp.time() == value), None)


def _in_window(timestamp: datetime, start: time, end: time) -> bool:
    return start <= timestamp.time() < end


def _forward_return(candles: list[Candle], index: int, horizon: int, sign: float) -> float:
    return sign * (candles[index + horizon].close - candles[index].close)


def _direction(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def _body_bucket(ratio: float) -> str:
    if ratio < 0.20:
        return "body_lt_20pct_range"
    if ratio < 0.50:
        return "body_20_50pct_range"
    return "body_ge_50pct_range"


def _quartiles(values: list[float]) -> tuple[float, float, float]:
    return values[len(values) // 4], values[len(values) // 2], values[(3 * len(values)) // 4]


def _vol_label(value: float, q1: float, q2: float, q3: float) -> str:
    if value <= q1:
        return "low_volatility_quartile"
    if value <= q2:
        return "medium_low_volatility_quartile"
    if value <= q3:
        return "medium_high_volatility_quartile"
    return "high_volatility_quartile"


def _max_month_share(events: list[EventObservation]) -> float:
    if not events:
        return 0.0
    counts: dict[str, int] = {}
    for event in events:
        month = event.timestamp.strftime("%Y-%m")
        counts[month] = counts.get(month, 0) + 1
    return max(counts.values()) / len(events)


def _same_sign(first: Any, second: Any) -> bool:
    first_value = float(first)
    second_value = float(second)
    return (first_value > 0 and second_value > 0) or (first_value < 0 and second_value < 0)


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _manifest_blockers(manifest: dict[str, Any] | None) -> list[str]:
    if manifest is None:
        return ["dataset_manifest_missing_or_invalid"]
    policy = manifest.get("split_policy")
    if not isinstance(policy, dict):
        return ["dataset_manifest_split_policy_missing"]
    required = {"train_end", "validation_start", "validation_end", "oos_start"}
    missing = sorted(required.difference(policy))
    return [f"dataset_manifest_split_policy_missing:{','.join(missing)}"] if missing else []


def _source_blockers(source_board: dict[str, Any] | None) -> list[str]:
    if source_board is None:
        return ["source_v0_53_board_missing_or_invalid"]
    blockers: list[str] = []
    if source_board.get("board_version") != SOURCE_PREVIOUS_BOARD_VERSION:
        blockers.append("source_v0_53_board_version_mismatch")
    if source_board.get("oos_used") is not False:
        blockers.append("source_v0_53_oos_state_invalid")
    return blockers


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "descriptive_profiler_only": True,
        "strategy_backtest": False,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
        "trade_recommendation_output_present": False,
        "data_csv_added_to_git": False,
    }
