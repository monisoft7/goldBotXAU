"""Train-only descriptive XAUUSD market behavior profiler."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_m15_csvs
from src.data.xauusd_dataset_manifest import build_xauusd_dataset_manifest
from src.research.oos_guard import OOSGuard

PROFILER_VERSION = "v0_10"
ATR_PERIOD_BARS = 96
IMPULSE_THRESHOLDS = (1.0, 1.5, 2.0)


def profile_xauusd_market(
    data_dir: str | Path = "data",
    pattern: str = "xauusd_m15_*.csv",
) -> dict[str, Any]:
    manifest = build_xauusd_dataset_manifest(data_dir, pattern).to_dict()
    if manifest["readiness"]["ready_for_strategy_research"] is not True:
        return _base_report(
            status="data_not_ready",
            manifest=manifest,
            oos_guard=None,
            train_candles=[],
        )

    try:
        candles = load_xauusd_m15_csvs(data_dir, pattern).records
        guard = OOSGuard(manifest)
        train_candles = guard.filter_candles(candles, "train")
        rows = [_normal_row(candle) for candle in train_candles]
        return _base_report(
            status="profile_ready",
            manifest=manifest,
            oos_guard=guard.report(),
            train_candles=train_candles,
            train_profile=_train_profile(rows),
            atr_profile=_atr_profile(rows),
            hour_profile=_hour_profile(rows),
            block_profile=_block_profile(rows),
            impulse_diagnostic=_impulse_diagnostic(rows),
            candidate_direction_hints=_candidate_direction_hints(rows),
        )
    except Exception as exc:
        return _base_report(
            status="profile_failed",
            manifest=manifest,
            oos_guard=None,
            train_candles=[],
            errors=[str(exc)],
        )


def _base_report(
    *,
    status: str,
    manifest: dict[str, Any],
    oos_guard: dict[str, bool] | None,
    train_candles: list[dict[str, float | str]],
    train_profile: dict[str, Any] | None = None,
    atr_profile: dict[str, Any] | None = None,
    hour_profile: dict[str, Any] | None = None,
    block_profile: dict[str, Any] | None = None,
    impulse_diagnostic: dict[str, Any] | None = None,
    candidate_direction_hints: dict[str, Any] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    dataset = manifest.get("dataset", {})
    splits = manifest.get("splits", {})
    return {
        "profiler_version": PROFILER_VERSION,
        "status": status,
        "dataset": {
            "candle_count": dataset.get("candle_count", 0),
            "train_candle_count": len(train_candles) if train_candles else _split_count(splits, "train"),
            "validation_candle_count": _split_count(splits, "validation"),
            "oos_candle_count": _split_count(splits, "out_of_sample"),
            "profiled_split": "train",
        },
        "oos_guard": oos_guard
        or {
            "oos_locked": True,
            "oos_access_attempted": False,
            "oos_access_allowed": False,
        },
        "train_profile": train_profile or _empty_train_profile(),
        "atr_profile": atr_profile or _empty_atr_profile(),
        "hour_profile": hour_profile or _empty_hour_profile(),
        "block_profile": block_profile or _empty_block_profile(),
        "impulse_diagnostic": impulse_diagnostic or _empty_impulse_diagnostic(),
        "candidate_direction_hints": candidate_direction_hints
        or {
            "reversion_bias_detected": False,
            "continuation_bias_detected": False,
            "insufficient_evidence": True,
            "notes": ["Train-only profile unavailable or insufficient."],
        },
        "safety": {
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
            "execution_queue_enabled": False,
            "buy_sell_output_allowed": False,
            "strategy_logic_added": False,
            "trade_simulation_added": False,
        },
        "errors": errors or [],
    }


def _train_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ranges = [_range(row) for row in rows]
    bodies = [_body_size(row) for row in rows]
    volumes = [row["volume"] for row in rows]
    return {
        "timestamp_start": rows[0]["timestamp"] if rows else None,
        "timestamp_end": rows[-1]["timestamp"] if rows else None,
        "candle_count": len(rows),
        "average_range": _average(ranges),
        "median_range": _median(ranges),
        "average_body_size": _average(bodies),
        "median_body_size": _median(bodies),
        "average_volume": _average(volumes),
        "flat_candle_count": sum(1 for row in rows if _direction(row) == 0),
    }


def _atr_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = _enriched_rows(rows)
    ratios = [row["range_to_atr"] for row in enriched if row["range_to_atr"] is not None]
    return {
        "atr_period_bars": ATR_PERIOD_BARS,
        "atr_available_count": len(ratios),
        "range_to_atr_mean": _average(ratios),
        "range_to_atr_median": _median(ratios),
        "range_to_atr_p80": _percentile(ratios, 0.80),
        "range_to_atr_p90": _percentile(ratios, 0.90),
        "range_to_atr_p95": _percentile(ratios, 0.95),
    }


def _hour_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = _enriched_rows(rows)
    return {
        f"{hour:02d}": _hour_summary([row for row in enriched if row["hour"] == hour])
        for hour in range(24)
    }


def _block_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = _enriched_rows(rows)
    blocks = {
        "block_00_06": range(0, 6),
        "block_06_12": range(6, 12),
        "block_12_18": range(12, 18),
        "block_18_24": range(18, 24),
    }
    return {
        name: _block_summary([row for row in enriched if row["hour"] in hours])
        for name, hours in blocks.items()
    }


def _impulse_diagnostic(rows: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = _enriched_rows(rows)
    return {
        f"range_to_atr_gte_{threshold:.1f}": _impulse_summary(
            [row for row in enriched if _ratio_at_least(row, threshold)]
        )
        for threshold in IMPULSE_THRESHOLDS
    }


def _candidate_direction_hints(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bins = _impulse_diagnostic(rows)
    high_bin = bins["range_to_atr_gte_1.5"]
    samples = high_bin["sample_count"]
    reversion_rate = high_bin["reversal_4bar_rate"]
    continuation_rate = high_bin["persistence_4bar_rate"]
    insufficient = samples < 50 or (reversion_rate == 0 and continuation_rate == 0)
    reversion_bias = not insufficient and reversion_rate >= continuation_rate + 0.05
    continuation_bias = not insufficient and continuation_rate >= reversion_rate + 0.05
    notes = [
        "Train-only descriptive hints; not strategy rules or approval.",
        f"Fixed impulse bin >= 1.5 ATR sample_count={samples}.",
    ]
    if reversion_bias:
        notes.append("Train profile shows higher 4-bar reversal frequency in the fixed impulse bin.")
    elif continuation_bias:
        notes.append("Train profile shows higher 4-bar persistence frequency in the fixed impulse bin.")
    else:
        notes.append("Train profile does not show a clear fixed-bin directional tendency.")
    return {
        "reversion_bias_detected": reversion_bias,
        "continuation_bias_detected": continuation_bias,
        "insufficient_evidence": insufficient,
        "notes": notes,
    }


def _enriched_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    true_ranges = _true_ranges(rows)
    enriched: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        atr = None
        if index >= ATR_PERIOD_BARS - 1:
            atr = sum(true_ranges[index - ATR_PERIOD_BARS + 1 : index + 1]) / ATR_PERIOD_BARS
        range_to_atr = _range(row) / atr if atr and atr > 0 else None
        next_1bar_move = _next_net_move(rows, index, 1)
        next_4bar_move = _next_net_move(rows, index, 4)
        enriched.append(
            {
                **row,
                "hour": datetime.fromisoformat(row["timestamp"]).hour,
                "range_to_atr": range_to_atr,
                "next_1bar_move": next_1bar_move,
                "next_4bar_move": next_4bar_move,
                "next_1bar_abs_return_to_atr": _abs_to_atr(next_1bar_move, atr),
                "next_4bar_abs_return_to_atr": _abs_to_atr(next_4bar_move, atr),
                "direction": _direction(row),
            }
        )
    return enriched


def _hour_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "candle_count": len(rows),
        "average_range_to_atr": _average(_values(rows, "range_to_atr")),
        "median_range_to_atr": _median(_values(rows, "range_to_atr")),
        "average_next_1bar_abs_return_to_atr": _average(_values(rows, "next_1bar_abs_return_to_atr")),
        "average_next_4bar_abs_return_to_atr": _average(_values(rows, "next_4bar_abs_return_to_atr")),
    }


def _block_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    persistence, reversal = _persistence_reversal_rates(rows, "next_4bar_move")
    return {
        "candle_count": len(rows),
        "average_range_to_atr": _average(_values(rows, "range_to_atr")),
        "median_range_to_atr": _median(_values(rows, "range_to_atr")),
        "average_next_4bar_abs_return_to_atr": _average(_values(rows, "next_4bar_abs_return_to_atr")),
        "directional_persistence_4bar_rate": persistence,
        "reversal_4bar_rate": reversal,
    }


def _impulse_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    persistence_1bar, reversal_1bar = _persistence_reversal_rates(rows, "next_1bar_move")
    persistence_4bar, reversal_4bar = _persistence_reversal_rates(rows, "next_4bar_move")
    return {
        "sample_count": len(rows),
        "persistence_1bar_rate": persistence_1bar,
        "persistence_4bar_rate": persistence_4bar,
        "reversal_1bar_rate": reversal_1bar,
        "reversal_4bar_rate": reversal_4bar,
        "average_next_4bar_abs_return_to_atr": _average(_values(rows, "next_4bar_abs_return_to_atr")),
    }


def _persistence_reversal_rates(rows: list[dict[str, Any]], move_key: str) -> tuple[float, float]:
    usable = [
        row
        for row in rows
        if row["direction"] != 0 and row[move_key] is not None and _sign(float(row[move_key])) != 0
    ]
    if not usable:
        return 0.0, 0.0
    persistent = sum(1 for row in usable if _sign(row["direction"]) == _sign(float(row[move_key])))
    reversed_count = sum(1 for row in usable if _sign(row["direction"]) == -_sign(float(row[move_key])))
    return persistent / len(usable), reversed_count / len(usable)


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
    ranges: list[float] = []
    previous_close: float | None = None
    for row in rows:
        if previous_close is None:
            ranges.append(_range(row))
        else:
            ranges.append(
                max(
                    _range(row),
                    abs(row["high"] - previous_close),
                    abs(row["low"] - previous_close),
                )
            )
        previous_close = row["close"]
    return ranges


def _next_net_move(rows: list[dict[str, Any]], index: int, bars: int) -> float | None:
    final_index = index + bars
    if final_index >= len(rows):
        return None
    return rows[final_index]["close"] - rows[index]["close"]


def _range(row: dict[str, Any]) -> float:
    return float(row["high"] - row["low"])


def _body_size(row: dict[str, Any]) -> float:
    return abs(float(row["close"] - row["open"]))


def _direction(row: dict[str, Any]) -> float:
    return float(row["close"] - row["open"])


def _abs_to_atr(move: float | None, atr: float | None) -> float | None:
    if move is None or atr is None or atr <= 0:
        return None
    return abs(move) / atr


def _ratio_at_least(row: dict[str, Any], threshold: float) -> bool:
    ratio = row["range_to_atr"]
    return ratio is not None and ratio >= threshold


def _values(rows: list[dict[str, Any]], key: str) -> list[float]:
    return [float(row[key]) for row in rows if row[key] is not None]


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


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _split_count(splits: dict[str, Any], split_name: str) -> int:
    return int(splits.get(split_name, {}).get("candle_count", 0))


def _empty_train_profile() -> dict[str, Any]:
    return {
        "timestamp_start": None,
        "timestamp_end": None,
        "candle_count": 0,
        "average_range": 0.0,
        "median_range": 0.0,
        "average_body_size": 0.0,
        "median_body_size": 0.0,
        "average_volume": 0.0,
        "flat_candle_count": 0,
    }


def _empty_atr_profile() -> dict[str, Any]:
    return {
        "atr_period_bars": ATR_PERIOD_BARS,
        "atr_available_count": 0,
        "range_to_atr_mean": 0.0,
        "range_to_atr_median": 0.0,
        "range_to_atr_p80": 0.0,
        "range_to_atr_p90": 0.0,
        "range_to_atr_p95": 0.0,
    }


def _empty_hour_profile() -> dict[str, Any]:
    return {f"{hour:02d}": _hour_summary([]) for hour in range(24)}


def _empty_block_profile() -> dict[str, Any]:
    return {
        "block_00_06": _block_summary([]),
        "block_06_12": _block_summary([]),
        "block_12_18": _block_summary([]),
        "block_18_24": _block_summary([]),
    }


def _empty_impulse_diagnostic() -> dict[str, Any]:
    return {
        f"range_to_atr_gte_{threshold:.1f}": _impulse_summary([])
        for threshold in IMPULSE_THRESHOLDS
    }
