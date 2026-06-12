"""Train-only advisor idea triage profiler for XAUUSD M15 research."""

from __future__ import annotations

import bisect
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_m15_csvs
from src.data.xauusd_dataset_manifest import build_xauusd_dataset_manifest
from src.research.oos_guard import OOSGuard

PROFILER_VERSION = "v0_16"
ATR_PERIOD_BARS = 96
ROLLING_LOW_ATR_BARS = 60 * 24 * 4
FIXED_LOW_ATR_THRESHOLD = 1.3230733892270252
FORWARD_HORIZONS = (1, 4, 8, 16)
WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
SAFETY_FLAGS = {
    "demo_enabled": False,
    "live_enabled": False,
    "order_send_allowed": False,
    "execution_queue_enabled": False,
    "buy_sell_output_allowed": False,
    "execution_logic_present": False,
    "trade_recommendation_output_present": False,
    "research_candidate_logic_present": False,
    "trade_simulation_added": False,
    "oos_evaluated": False,
}


def profile_advisor_ideas(
    data_dir: str | Path = "data",
    pattern: str = "xauusd_m15_*.csv",
) -> dict[str, Any]:
    manifest = build_xauusd_dataset_manifest(data_dir, pattern).to_dict()
    if manifest["readiness"]["ready_for_strategy_research"] is not True:
        return _base_report(status="data_not_ready", manifest=manifest, oos_guard=None)

    try:
        candles = load_xauusd_m15_csvs(data_dir, pattern).records
        guard = OOSGuard(manifest)
        train_candles = guard.filter_candles(candles, "train")
        rows = _enriched_rows([_normal_row(candle) for candle in train_candles])
        advisor_ideas = _advisor_ideas(rows)
        ranking = _ranking(advisor_ideas)
        return _base_report(
            status="profile_ready",
            manifest=manifest,
            oos_guard=guard.report(),
            train_candle_count=len(train_candles),
            advisor_ideas=advisor_ideas,
            ranking=ranking,
        )
    except Exception as exc:
        return _base_report(
            status="profile_failed",
            manifest=manifest,
            oos_guard=None,
            errors=[str(exc)],
        )


def _base_report(
    *,
    status: str,
    manifest: dict[str, Any],
    oos_guard: dict[str, bool] | None,
    train_candle_count: int | None = None,
    advisor_ideas: dict[str, Any] | None = None,
    ranking: dict[str, Any] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    dataset = manifest.get("dataset", {})
    splits = manifest.get("splits", {})
    return {
        "profiler_version": PROFILER_VERSION,
        "status": status,
        "dataset": {
            "candle_count": int(dataset.get("candle_count", 0) or 0),
            "train_candle_count": train_candle_count if train_candle_count is not None else _split_count(splits, "train"),
            "validation_candle_count": _split_count(splits, "validation"),
            "oos_candle_count": _split_count(splits, "out_of_sample"),
            "discovery_split": "train",
        },
        "oos_guard": oos_guard
        or {
            "oos_locked": True,
            "oos_access_attempted": False,
            "oos_access_allowed": False,
        },
        "advisor_ideas": advisor_ideas or _empty_advisor_ideas(),
        "ranking": ranking or _empty_ranking(),
        "safety": dict(SAFETY_FLAGS),
        "errors": errors or [],
    }


def _advisor_ideas(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "hour_16_isolated": _hour_16_isolated(rows),
        "low_atr_x_hour_16": _low_atr_x_hour_16(rows),
        "asia_range_pre_qualifier": _asia_range_pre_qualifier(rows),
        "day_of_week_filter": _day_of_week_filter(rows),
        "htf_trend_filter": _htf_trend_filter(rows),
        "v0_11_rescue_train_fix": {
            "status": "rejected_not_allowed",
            "eligible_for_ranking": False,
            "reason": "v0_11 is rejected/do_not_retune and v0_12 recommended abandon_family",
        },
    }


def _hour_16_isolated(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hour_rows = [row for row in rows if row["hour"] == 16]
    return {
        "status": "profiled",
        "timestamp_label": "dataset_hour_16",
        "timestamp_note": "advisor called it UTC, project treats it as dataset hour",
        "contexts": {
            "all_dataset_hour_16_candles": _context_metrics(hour_rows),
            "hour_16_near_high": _context_metrics([row for row in hour_rows if row["close_location_fraction"] >= 0.75]),
            "hour_16_near_low": _context_metrics([row for row in hour_rows if row["close_location_fraction"] <= 0.25]),
            "hour_16_middle_close": _context_metrics(
                [row for row in hour_rows if 0.25 < row["close_location_fraction"] < 0.75]
            ),
        },
    }


def _low_atr_x_hour_16(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hour_rows = [row for row in rows if row["hour"] == 16]
    fixed = [row for row in hour_rows if _lt(row["range_to_atr"], FIXED_LOW_ATR_THRESHOLD)]
    rolling = [row for row in hour_rows if row["rolling_low_atr"] is True]
    return {
        "status": "profiled",
        "timestamp_label": "dataset_hour_16",
        "timestamp_note": "advisor called it UTC, project treats it as dataset hour",
        "definitions": {
            "fixed_low_atr": {"range_to_atr_lt": FIXED_LOW_ATR_THRESHOLD},
            "rolling_low_atr": {
                "basis": "current range_to_atr below trailing 35th percentile",
                "trailing_bars": ROLLING_LOW_ATR_BARS,
                "minimum_history_required": ROLLING_LOW_ATR_BARS,
            },
        },
        "contexts": {
            "hour_16_fixed_low_atr_all": _context_metrics(fixed),
            "hour_16_fixed_low_atr_near_high": _context_metrics(
                [row for row in fixed if row["close_location_fraction"] >= 0.75]
            ),
            "hour_16_fixed_low_atr_near_low": _context_metrics(
                [row for row in fixed if row["close_location_fraction"] <= 0.25]
            ),
            "hour_16_fixed_low_atr_after_compression": _context_metrics(
                [row for row in fixed if _lt(row["prior_8bar_avg_range_to_atr"], 0.75)]
            ),
            "hour_16_rolling_low_atr_all": _context_metrics(rolling),
            "hour_16_rolling_low_atr_near_high": _context_metrics(
                [row for row in rolling if row["close_location_fraction"] >= 0.75]
            ),
            "hour_16_rolling_low_atr_near_low": _context_metrics(
                [row for row in rolling if row["close_location_fraction"] <= 0.25]
            ),
            "hour_16_rolling_low_atr_after_compression": _context_metrics(
                [row for row in rolling if _lt(row["prior_8bar_avg_range_to_atr"], 0.75)]
            ),
        },
    }


def _asia_range_pre_qualifier(rows: list[dict[str, Any]]) -> dict[str, Any]:
    quiet_by_date = _quiet_00_06_by_date(rows)
    active_rows = [row for row in rows if 12 <= row["hour"] <= 18 and row["date"] in quiet_by_date]
    return {
        "status": "profiled",
        "naming": "neutral_pre_active_quietness",
        "pre_active_block": "block_00_06",
        "active_evaluation_hours": "dataset_hours_12_through_18",
        "range_boundary_logic_present": False,
        "contexts": {
            "active_after_quiet_00_06": _context_metrics([row for row in active_rows if quiet_by_date[row["date"]]]),
            "active_after_nonquiet_00_06": _context_metrics(
                [row for row in active_rows if not quiet_by_date[row["date"]]]
            ),
        },
    }


def _day_of_week_filter(rows: list[dict[str, Any]]) -> dict[str, Any]:
    contexts = {
        name: _context_metrics([row for row in rows if row["weekday"] == index])
        for index, name in enumerate(WEEKDAY_NAMES)
    }
    strongest_abs, weakest_abs = _strongest_weakest(contexts, "average_abs_forward_move_to_atr")
    strongest_imbalance, weakest_imbalance = _strongest_weakest(contexts, "directional_imbalance_abs")
    return {
        "status": "profiled",
        "rule_recommendation_allowed": False,
        "contexts": contexts,
        "strongest_weekday_by_average_abs_forward_move_to_atr": strongest_abs,
        "weakest_weekday_by_average_abs_forward_move_to_atr": weakest_abs,
        "strongest_weekday_by_directional_imbalance": strongest_imbalance,
        "weakest_weekday_by_directional_imbalance": weakest_imbalance,
    }


def _htf_trend_filter(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "profiled",
        "data_source": "M15_derived_proxy_only",
        "external_higher_timeframe_fetch_used": False,
        "labels": ["positive_slope", "negative_slope", "flat_slope"],
        "contexts": {
            "positive_slope": _context_metrics([row for row in rows if row["htf_proxy_slope"] == "positive_slope"]),
            "negative_slope": _context_metrics([row for row in rows if row["htf_proxy_slope"] == "negative_slope"]),
            "flat_slope": _context_metrics([row for row in rows if row["htf_proxy_slope"] == "flat_slope"]),
        },
    }


def _context_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        f"next_{horizon}bar": _horizon_metrics(rows, horizon)
        for horizon in FORWARD_HORIZONS
    }


def _horizon_metrics(rows: list[dict[str, Any]], horizon: int) -> dict[str, Any]:
    moves = [row[f"next_{horizon}bar_net_move_to_atr"] for row in rows]
    usable = [float(move) for move in moves if move is not None]
    positives = [move for move in usable if move > 0]
    negatives = [move for move in usable if move < 0]
    return {
        "sample_count": len(usable),
        "average_forward_net_move_to_atr": _average(usable),
        "median_forward_net_move_to_atr": _median(usable),
        "average_abs_forward_move_to_atr": _average([abs(move) for move in usable]),
        "positive_forward_rate": len(positives) / len(usable) if usable else 0.0,
        "negative_forward_rate": len(negatives) / len(usable) if usable else 0.0,
        "near_flat_forward_rate": sum(1 for move in usable if abs(move) < 0.15) / len(usable) if usable else 0.0,
    }


def _ranking(advisor_ideas: dict[str, Any]) -> dict[str, Any]:
    eligible = {
        "hour_16_isolated": advisor_ideas["hour_16_isolated"],
        "low_atr_x_hour_16": advisor_ideas["low_atr_x_hour_16"],
        "asia_range_pre_qualifier": advisor_ideas["asia_range_pre_qualifier"],
        "day_of_week_filter": advisor_ideas["day_of_week_filter"],
        "htf_trend_filter": advisor_ideas["htf_trend_filter"],
    }
    scored = [_score_idea(name, idea) for name, idea in eligible.items()]
    ranked = sorted(scored, key=lambda item: item["score"], reverse=True)
    best = ranked[0] if ranked else {"idea": None, "score": 0.0, "best_context": None}
    direction_map = {
        "hour_16_isolated": "investigate_hour_16_isolated",
        "low_atr_x_hour_16": "investigate_low_atr_x_hour_16",
        "asia_range_pre_qualifier": "investigate_asia_pre_qualifier",
        "day_of_week_filter": "investigate_day_filter",
        "htf_trend_filter": "investigate_htf_proxy_filter",
    }
    if best["score"] >= 1.25:
        next_direction = direction_map[str(best["idea"])]
        action = "build_fixed_candidate"
        candidate_id = f"xauusd_{best['idea']}_v0_17"
    elif best["score"] >= 0.25:
        next_direction = direction_map[str(best["idea"])]
        action = "run_more_diagnostics"
        candidate_id = None
    elif ranked:
        next_direction = "no_edge_found"
        action = "stop_strategy_search_temporarily"
        candidate_id = None
    else:
        next_direction = "needs_more_diagnostics"
        action = "run_more_diagnostics"
        candidate_id = None
    return {
        "ranked_ideas": ranked,
        "recommended_next_research_direction": next_direction,
        "recommended_v0_17_action": action,
        "recommended_v0_17_candidate_id": candidate_id,
        "reasons": [
            "Train-only descriptive context ranking; validation and OOS were not used.",
            "Contexts with sample_count below 50 are penalized and below 30 are strongly penalized.",
            "v0_11_rescue_train_fix is not eligible because the family is rejected/do_not_retune.",
        ],
    }


def _score_idea(name: str, idea: dict[str, Any]) -> dict[str, Any]:
    best_context = None
    best_horizon = None
    best_score = -999.0
    for context_name, horizons in idea.get("contexts", {}).items():
        for horizon_name, metrics in horizons.items():
            sample_count = int(metrics["sample_count"])
            imbalance = abs(float(metrics["positive_forward_rate"]) - float(metrics["negative_forward_rate"]))
            average_abs = float(metrics["average_abs_forward_move_to_atr"])
            score = imbalance * 2.0
            if sample_count >= 80 and imbalance >= 0.08:
                score += 0.75
            if imbalance >= 0.05:
                score += min(average_abs, 2.0) * 0.35
            if sample_count < 30:
                score -= 2.0
            elif sample_count < 50:
                score -= 0.75
            if score > best_score:
                best_score = score
                best_context = context_name
                best_horizon = horizon_name
    return {
        "idea": name,
        "score": round(best_score, 6),
        "best_context": best_context,
        "best_horizon": best_horizon,
    }


def _enriched_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    true_ranges = _true_ranges(rows)
    sorted_rolling_ranges: list[float] = []
    range_to_atr_history: list[float] = []
    enriched: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        atr = None
        if index >= ATR_PERIOD_BARS - 1:
            atr = sum(true_ranges[index - ATR_PERIOD_BARS + 1 : index + 1]) / ATR_PERIOD_BARS
        range_to_atr = _safe_ratio(_range(row), atr)
        prior_8 = _prior_average(enriched, "range_to_atr", 8)
        prior_16 = _prior_average(enriched, "range_to_atr", 16)
        rolling_low = False
        if range_to_atr is not None and len(range_to_atr_history) >= ROLLING_LOW_ATR_BARS:
            rolling_low = range_to_atr < _percentile_sorted(sorted_rolling_ranges, 0.35)
        hour = datetime.fromisoformat(row["timestamp"]).hour
        enriched_row = {
            **row,
            "atr": atr,
            "range_to_atr": range_to_atr,
            "body_to_range": _safe_ratio(abs(row["close"] - row["open"]), _range(row)),
            "close_location_fraction": _safe_ratio(row["close"] - row["low"], _range(row)),
            "prior_8bar_avg_range_to_atr": prior_8,
            "prior_16bar_avg_range_to_atr": prior_16,
            "prior_8bar_net_move_to_atr": _prior_net_move_to_atr(rows, index, 8, atr),
            "hour": hour,
            "weekday": datetime.fromisoformat(row["timestamp"]).weekday(),
            "date": datetime.fromisoformat(row["timestamp"]).date().isoformat(),
            "session_block": _session_block(hour),
            "rolling_low_atr": rolling_low,
            "h1_proxy_slope_8": _proxy_slope(rows, index, 4 * 8),
            "h4_proxy_slope_6": _proxy_slope(rows, index, 16 * 6),
            "htf_proxy_slope": _htf_proxy_label(rows, index),
        }
        for horizon in FORWARD_HORIZONS:
            enriched_row[f"next_{horizon}bar_net_move_to_atr"] = _forward_move_to_atr(rows, index, horizon, atr)
        enriched.append(enriched_row)
        if range_to_atr is not None:
            range_to_atr_history.append(range_to_atr)
            bisect.insort(sorted_rolling_ranges, range_to_atr)
            if len(range_to_atr_history) > ROLLING_LOW_ATR_BARS:
                expired = range_to_atr_history[-ROLLING_LOW_ATR_BARS - 1]
                del sorted_rolling_ranges[bisect.bisect_left(sorted_rolling_ranges, expired)]
    return enriched


def _quiet_00_06_by_date(rows: list[dict[str, Any]]) -> dict[str, bool]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["session_block"] == "block_00_06":
            grouped[row["date"]].append(row)
    result: dict[str, bool] = {}
    for date, day_rows in grouped.items():
        values = [row["range_to_atr"] for row in day_rows if row["range_to_atr"] is not None]
        if len(values) >= 12:
            result[date] = _average([float(value) for value in values]) < 0.85
    return result


def _strongest_weakest(contexts: dict[str, Any], metric_name: str) -> tuple[str | None, str | None]:
    scored: list[tuple[str, float]] = []
    for name, horizons in contexts.items():
        metrics = horizons["next_4bar"]
        if metric_name == "directional_imbalance_abs":
            value = abs(metrics["positive_forward_rate"] - metrics["negative_forward_rate"])
        else:
            value = float(metrics[metric_name])
        scored.append((name, value))
    if not scored:
        return None, None
    ordered = sorted(scored, key=lambda item: item[1])
    return ordered[-1][0], ordered[0][0]


def _normal_row(candle: dict[str, float | str]) -> dict[str, Any]:
    return {
        "timestamp": str(candle["timestamp"]),
        "open": float(candle["open"]),
        "high": float(candle["high"]),
        "low": float(candle["low"]),
        "close": float(candle["close"]),
        "volume": float(candle.get("volume", 0.0)),
    }


def _true_ranges(rows: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    previous_close: float | None = None
    for row in rows:
        values.append(
            _range(row)
            if previous_close is None
            else max(_range(row), abs(row["high"] - previous_close), abs(row["low"] - previous_close))
        )
        previous_close = row["close"]
    return values


def _forward_move_to_atr(rows: list[dict[str, Any]], index: int, bars: int, atr: float | None) -> float | None:
    final_index = index + bars
    if final_index >= len(rows) or atr is None or atr <= 0:
        return None
    return (rows[final_index]["close"] - rows[index]["close"]) / atr


def _prior_net_move_to_atr(rows: list[dict[str, Any]], index: int, bars: int, atr: float | None) -> float | None:
    prior_index = index - bars
    if prior_index < 0 or atr is None or atr <= 0:
        return None
    return (rows[index]["close"] - rows[prior_index]["close"]) / atr


def _proxy_slope(rows: list[dict[str, Any]], index: int, lookback: int) -> float | None:
    prior_index = index - lookback
    if prior_index < 0:
        return None
    return rows[index]["close"] - rows[prior_index]["close"]


def _htf_proxy_label(rows: list[dict[str, Any]], index: int) -> str:
    h1 = _proxy_slope(rows, index, 4 * 8)
    h4 = _proxy_slope(rows, index, 16 * 6)
    if h1 is None or h4 is None:
        return "flat_slope"
    if h1 > 0 and h4 > 0:
        return "positive_slope"
    if h1 < 0 and h4 < 0:
        return "negative_slope"
    return "flat_slope"


def _session_block(hour: int) -> str:
    if hour < 6:
        return "block_00_06"
    if hour < 12:
        return "block_06_12"
    if hour < 18:
        return "block_12_18"
    return "block_18_24"


def _range(row: dict[str, Any]) -> float:
    return float(row["high"] - row["low"])


def _prior_average(rows: list[dict[str, Any]], key: str, bars: int) -> float | None:
    values = [row[key] for row in rows[-bars:] if row.get(key) is not None]
    if not values:
        return None
    return _average([float(value) for value in values])


def _safe_ratio(numerator: float, denominator: float | None) -> float | None:
    if denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _lt(value: float | None, threshold: float) -> bool:
    return value is not None and value < threshold


def _average(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _median(values: list[float]) -> float:
    return median(values) if values else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentile)
    return ordered[index]


def _percentile_sorted(ordered: list[float], percentile: float) -> float:
    if not ordered:
        return 0.0
    index = round((len(ordered) - 1) * percentile)
    return ordered[index]


def _split_count(splits: dict[str, Any], split_name: str) -> int:
    return int(splits.get(split_name, {}).get("candle_count", 0) or 0)


def _empty_advisor_ideas() -> dict[str, Any]:
    return {
        "hour_16_isolated": {"status": "not_profiled", "timestamp_label": "dataset_hour_16", "contexts": {}},
        "low_atr_x_hour_16": {"status": "not_profiled", "timestamp_label": "dataset_hour_16", "contexts": {}},
        "asia_range_pre_qualifier": {
            "status": "not_profiled",
            "range_boundary_logic_present": False,
            "contexts": {
                "active_after_quiet_00_06": _context_metrics([]),
                "active_after_nonquiet_00_06": _context_metrics([]),
            },
        },
        "day_of_week_filter": {"status": "not_profiled", "contexts": {}},
        "htf_trend_filter": {
            "status": "not_profiled",
            "data_source": "M15_derived_proxy_only",
            "external_higher_timeframe_fetch_used": False,
            "contexts": {},
        },
        "v0_11_rescue_train_fix": {
            "status": "rejected_not_allowed",
            "eligible_for_ranking": False,
            "reason": "v0_11 is rejected/do_not_retune and v0_12 recommended abandon_family",
        },
    }


def _empty_ranking() -> dict[str, Any]:
    return {
        "ranked_ideas": [],
        "recommended_next_research_direction": "needs_more_diagnostics",
        "recommended_v0_17_action": "run_more_diagnostics",
        "recommended_v0_17_candidate_id": None,
        "reasons": ["Profile unavailable."],
    }
