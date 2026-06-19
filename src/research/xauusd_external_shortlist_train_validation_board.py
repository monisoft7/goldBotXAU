"""v0_53 fixed-rule train/validation board for the external XAUUSD shortlist."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any, Callable

from src.data.xauusd_csv_loader import load_xauusd_m15_csvs

BOARD_VERSION = "v0_53"
SOURCE_TRIAGE_VERSIONS = ["v0_52", "v0_52_1"]
DEFAULT_OUTPUT = Path("reports") / "xauusd_external_shortlist_board_v0_53.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"
DEFAULT_V0_52_REPORT = Path("reports") / "xauusd_external_strategy_idea_triage_v0_52.json"
DEFAULT_V0_52_1_REPORT = Path("reports") / "xauusd_kimi_external_idea_addendum_v0_52_1.json"

PASSED = "external_shortlist_candidate_passed_train_validation"
NONE_PASSED = "no_external_shortlist_candidate_passed"
BLOCKED_MISSING_DATA = "blocked_missing_required_data"
BOARD_FAILED = "board_failed"

SHORTLIST = (
    "prior_day_liquidity_sweep_reversal",
    "london_opening_range_breakout_or_first_candle_direction",
    "asian_range_london_breakout_confirmation",
)

GATE = {
    "train_profit_factor_min": 1.20,
    "validation_profit_factor_min": 1.15,
    "validation_trades_min": 50,
    "train_expectancy_min_exclusive": 0.0,
    "validation_expectancy_min_exclusive": 0.0,
    "max_consecutive_losses_max": 8,
    "validation_pf_min_train_pf_ratio": 0.75,
    "oos_used": False,
}


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    split: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Trade:
    candidate_id: str
    split: str
    entry_timestamp: str
    exit_timestamp: str
    side: str
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    return_r: float
    exit_reason: str


Rule = Callable[[list[Candle]], list[Trade]]


def build_xauusd_external_shortlist_train_validation_board_v0_53(
    *,
    data_dir: str | Path = "data",
    pattern: str = "xauusd_m15_*.csv",
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_triage_path: str | Path = DEFAULT_V0_52_REPORT,
    source_addendum_path: str | Path = DEFAULT_V0_52_1_REPORT,
) -> dict[str, Any]:
    """Evaluate the finalized external shortlist on train/validation candles only."""
    try:
        manifest = _read_json(Path(manifest_path))
        source_triage = _read_json(Path(source_triage_path))
        source_addendum = _read_json(Path(source_addendum_path))
        source_blockers = _source_blockers(source_triage, source_addendum)
        manifest_blockers = _manifest_blockers(manifest)
        if source_blockers or manifest_blockers:
            return _blocked_report(
                blockers=[*source_blockers, *manifest_blockers],
                data_files_used=[],
                split_candle_counts={"train": 0, "validation": 0, "excluded_oos": 0, "other": 0},
            )

        assert manifest is not None
        load_result = load_xauusd_m15_csvs(data_dir=data_dir, pattern=pattern)
        candles, split_counts = _split_candles(load_result.records, manifest)
        evaluation_candles = [candle for candle in candles if candle.split in {"train", "validation"}]
        blockers: list[str] = []
        if not load_result.files:
            blockers.append("m15_data_files_missing")
        if not evaluation_candles:
            blockers.append("train_validation_m15_rows_missing")
        if split_counts["train"] <= 0:
            blockers.append("train_m15_rows_missing")
        if split_counts["validation"] <= 0:
            blockers.append("validation_m15_rows_missing")
        if blockers:
            return _blocked_report(
                blockers=blockers,
                data_files_used=[path.as_posix() for path in load_result.files],
                split_candle_counts=split_counts,
            )

        candidate_results = [_evaluate_candidate(candidate_id, evaluation_candles) for candidate_id in SHORTLIST]
        passed = [result for result in candidate_results if result["passed_gate"] is True]
        best = max(candidate_results, key=_candidate_sort_key)
        board_status = PASSED if passed else NONE_PASSED
        next_step = (
            "lock fixed candidate artifact and prepare one-time OOS protocol"
            if passed
            else "broaden non-OOS research or stop current branch"
        )

        return _base_report(
            board_status=board_status,
            candidate_results=candidate_results,
            best_candidate=best,
            blockers=[],
            warnings=_warnings(candidate_results, split_counts),
            next_recommended_step=next_step,
            data_files_used=[path.as_posix() for path in load_result.files],
            split_candle_counts=split_counts,
        )
    except Exception as exc:
        return _base_report(
            board_status=BOARD_FAILED,
            candidate_results=[],
            best_candidate=None,
            blockers=[f"board_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair v0_53 board implementation or input artifacts before rerunning",
            data_files_used=[],
            split_candle_counts={"train": 0, "validation": 0, "excluded_oos": 0, "other": 0},
        )


def save_xauusd_external_shortlist_train_validation_board(
    report: dict[str, Any],
    output: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _blocked_report(
    *,
    blockers: list[str],
    data_files_used: list[str],
    split_candle_counts: dict[str, int],
) -> dict[str, Any]:
    return _base_report(
        board_status=BLOCKED_MISSING_DATA,
        candidate_results=[],
        best_candidate=None,
        blockers=blockers,
        warnings=[],
        next_recommended_step="restore required v0_52/v0_52_1 reports and train/validation M15 data before rerunning v0_53",
        data_files_used=data_files_used,
        split_candle_counts=split_candle_counts,
    )


def _evaluate_candidate(candidate_id: str, candles: list[Candle]) -> dict[str, Any]:
    trades = _rules()[candidate_id](candles)
    trade_records = [_trade_record(trade) for trade in trades]
    train_trades = [record for record in trade_records if record["split"] == "train"]
    validation_trades = [record for record in trade_records if record["split"] == "validation"]
    train_metrics = _metrics(train_trades)
    validation_metrics = _metrics(validation_trades)
    gate_failures = _gate_failures(train_metrics, validation_metrics)
    passed = not gate_failures
    return {
        "candidate_id": candidate_id,
        "fixed_before_evaluation": True,
        "timeframe": "M15",
        "fixed_rules": _fixed_rule_specs()[candidate_id],
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "combined_trade_count": len(trade_records),
        "split_trade_counts": {"train": len(train_trades), "validation": len(validation_trades)},
        "passed_gate": passed,
        "gate_failures": gate_failures,
        "candidate_disposition": "requires_locked_artifact_before_oos" if passed else "rejected_do_not_retune",
        "do_not_retune": not passed,
        "candidate_created": False,
        "trade_sample": trade_records[:5],
        "safety": _safety_flags(),
    }


def _rules() -> dict[str, Rule]:
    return {
        "prior_day_liquidity_sweep_reversal": _prior_day_liquidity_sweep_trades,
        "london_opening_range_breakout_or_first_candle_direction": _london_first_candle_trades,
        "asian_range_london_breakout_confirmation": _asian_range_breakout_trades,
    }


def _prior_day_liquidity_sweep_trades(candles: list[Candle]) -> list[Trade]:
    grouped = _candles_by_day(candles)
    days = sorted(grouped)
    trades: list[Trade] = []
    for index, day in enumerate(days[1:], start=1):
        previous = grouped[days[index - 1]]
        current = grouped[day]
        previous_high = max(candle.high for candle in previous)
        previous_low = min(candle.low for candle in previous)
        midpoint = (previous_high + previous_low) / 2.0
        long_taken = False
        short_taken = False
        for candle_index, candle in enumerate(current):
            if not _in_window(candle.timestamp, time(7, 0), time(20, 0)):
                continue
            if not long_taken and candle.low < previous_low and candle.close > previous_low:
                trade = _simulate_prior_day_sweep(
                    candidate_id="prior_day_liquidity_sweep_reversal",
                    side="long",
                    entry_candle=candle,
                    future=current[candle_index + 1 :],
                    stop_price=candle.low,
                    target_price=midpoint,
                    sweep_extreme=candle.low,
                    previous_low=previous_low,
                    previous_high=previous_high,
                )
                if trade is not None:
                    trades.append(trade)
                    long_taken = True
            if not short_taken and candle.high > previous_high and candle.close < previous_high:
                trade = _simulate_prior_day_sweep(
                    candidate_id="prior_day_liquidity_sweep_reversal",
                    side="short",
                    entry_candle=candle,
                    future=current[candle_index + 1 :],
                    stop_price=candle.high,
                    target_price=midpoint,
                    sweep_extreme=candle.high,
                    previous_low=previous_low,
                    previous_high=previous_high,
                )
                if trade is not None:
                    trades.append(trade)
                    short_taken = True
    return sorted(trades, key=lambda trade: (trade.entry_timestamp, trade.side))


def _simulate_prior_day_sweep(
    *,
    candidate_id: str,
    side: str,
    entry_candle: Candle,
    future: list[Candle],
    stop_price: float,
    target_price: float,
    sweep_extreme: float,
    previous_low: float,
    previous_high: float,
) -> Trade | None:
    entry = entry_candle.close
    risk = entry - stop_price if side == "long" else stop_price - entry
    target_is_beyond_entry = target_price > entry if side == "long" else target_price < entry
    if risk <= 0.0 or not target_is_beyond_entry:
        return None
    time_exit = _time_exit_candle(future, time(20, 0))
    if time_exit is None:
        return None
    next_candle = future[0] if future else None
    if next_candle is not None:
        invalid = next_candle.close < sweep_extreme if side == "long" else next_candle.close > sweep_extreme
        if invalid:
            return _trade(candidate_id, side, entry_candle, next_candle, entry, next_candle.close, stop_price, target_price, "invalidated_next_candle")
    for candle in future:
        if candle.timestamp >= _combine_time(entry_candle.timestamp, time(20, 0)):
            break
        if side == "long":
            if candle.low <= stop_price:
                return _trade(candidate_id, side, entry_candle, candle, entry, stop_price, stop_price, target_price, "stop")
            if candle.high >= target_price:
                return _trade(candidate_id, side, entry_candle, candle, entry, target_price, stop_price, target_price, "target_midpoint_previous_day_range")
        else:
            if candle.high >= stop_price:
                return _trade(candidate_id, side, entry_candle, candle, entry, stop_price, stop_price, target_price, "stop")
            if candle.low <= target_price:
                return _trade(candidate_id, side, entry_candle, candle, entry, target_price, stop_price, target_price, "target_midpoint_previous_day_range")
    del previous_low, previous_high
    return _trade(candidate_id, side, entry_candle, time_exit, entry, time_exit.close, stop_price, target_price, "time_exit_20_00_utc")


def _london_first_candle_trades(candles: list[Candle]) -> list[Trade]:
    trades: list[Trade] = []
    for _day, day_candles in _candles_by_day(candles).items():
        first = _candle_at(day_candles, time(7, 0))
        if first is None:
            continue
        candle_range = first.high - first.low
        if candle_range <= 0.0:
            continue
        body_ratio = abs(first.close - first.open) / candle_range
        if body_ratio < 0.20:
            continue
        if first.close > first.open:
            side = "long"
            stop = first.low
            risk = first.close - stop
            target = first.close + 1.5 * risk
        elif first.close < first.open:
            side = "short"
            stop = first.high
            risk = stop - first.close
            target = first.close - 1.5 * risk
        else:
            continue
        if risk <= 0.0:
            continue
        future = [candle for candle in day_candles if candle.timestamp > first.timestamp]
        trade = _simulate_stop_target_time_exit(
            candidate_id="london_opening_range_breakout_or_first_candle_direction",
            side=side,
            entry_candle=first,
            future=future,
            stop_price=stop,
            target_price=target,
            exit_time=time(12, 0),
            target_reason="target_1_5r",
            time_exit_reason="time_exit_12_00_utc",
        )
        if trade is not None:
            trades.append(trade)
    return sorted(trades, key=lambda trade: (trade.entry_timestamp, trade.side))


def _asian_range_breakout_trades(candles: list[Candle]) -> list[Trade]:
    trades: list[Trade] = []
    for _day, day_candles in _candles_by_day(candles).items():
        asian = [candle for candle in day_candles if _in_window(candle.timestamp, time(0, 0), time(7, 0))]
        if not asian:
            continue
        asian_high = max(candle.high for candle in asian)
        asian_low = min(candle.low for candle in asian)
        asian_range = asian_high - asian_low
        if asian_range <= 0.0:
            continue
        midpoint = (asian_high + asian_low) / 2.0
        long_taken = False
        short_taken = False
        for candle_index, candle in enumerate(day_candles):
            if not _in_window(candle.timestamp, time(7, 0), time(11, 0)):
                continue
            if not long_taken and candle.close > asian_high:
                trade = _simulate_asian_breakout(
                    side="long",
                    entry_candle=candle,
                    future=day_candles[candle_index + 1 :],
                    stop_price=midpoint,
                    target_price=candle.close + asian_range,
                    asian_low=asian_low,
                    asian_high=asian_high,
                )
                if trade is not None:
                    trades.append(trade)
                    long_taken = True
            if not short_taken and candle.close < asian_low:
                trade = _simulate_asian_breakout(
                    side="short",
                    entry_candle=candle,
                    future=day_candles[candle_index + 1 :],
                    stop_price=midpoint,
                    target_price=candle.close - asian_range,
                    asian_low=asian_low,
                    asian_high=asian_high,
                )
                if trade is not None:
                    trades.append(trade)
                    short_taken = True
    return sorted(trades, key=lambda trade: (trade.entry_timestamp, trade.side))


def _simulate_asian_breakout(
    *,
    side: str,
    entry_candle: Candle,
    future: list[Candle],
    stop_price: float,
    target_price: float,
    asian_low: float,
    asian_high: float,
) -> Trade | None:
    entry = entry_candle.close
    risk = entry - stop_price if side == "long" else stop_price - entry
    if risk <= 0.0:
        return None
    time_exit = _time_exit_candle(future, time(20, 0))
    if time_exit is None:
        return None
    next_candle = future[0] if future else None
    if next_candle is not None and asian_low <= next_candle.close <= asian_high:
        return _trade(
            "asian_range_london_breakout_confirmation",
            side,
            entry_candle,
            next_candle,
            entry,
            next_candle.close,
            stop_price,
            target_price,
            "invalidated_next_candle_close_back_inside_asian_range",
        )
    return _simulate_stop_target_time_exit(
        candidate_id="asian_range_london_breakout_confirmation",
        side=side,
        entry_candle=entry_candle,
        future=future,
        stop_price=stop_price,
        target_price=target_price,
        exit_time=time(20, 0),
        target_reason="target_1_0_asian_range",
        time_exit_reason="time_exit_20_00_utc",
    )


def _simulate_stop_target_time_exit(
    *,
    candidate_id: str,
    side: str,
    entry_candle: Candle,
    future: list[Candle],
    stop_price: float,
    target_price: float,
    exit_time: time,
    target_reason: str,
    time_exit_reason: str,
) -> Trade | None:
    entry = entry_candle.close
    time_exit = _time_exit_candle(future, exit_time)
    if time_exit is None:
        return None
    exit_boundary = _combine_time(entry_candle.timestamp, exit_time)
    for candle in future:
        if candle.timestamp >= exit_boundary:
            break
        if side == "long":
            if candle.low <= stop_price:
                return _trade(candidate_id, side, entry_candle, candle, entry, stop_price, stop_price, target_price, "stop")
            if candle.high >= target_price:
                return _trade(candidate_id, side, entry_candle, candle, entry, target_price, stop_price, target_price, target_reason)
        else:
            if candle.high >= stop_price:
                return _trade(candidate_id, side, entry_candle, candle, entry, stop_price, stop_price, target_price, "stop")
            if candle.low <= target_price:
                return _trade(candidate_id, side, entry_candle, candle, entry, target_price, stop_price, target_price, target_reason)
    return _trade(candidate_id, side, entry_candle, time_exit, entry, time_exit.close, stop_price, target_price, time_exit_reason)


def _trade(
    candidate_id: str,
    side: str,
    entry_candle: Candle,
    exit_candle: Candle,
    entry_price: float,
    exit_price: float,
    stop_price: float,
    target_price: float,
    exit_reason: str,
) -> Trade:
    risk = entry_price - stop_price if side == "long" else stop_price - entry_price
    direction = 1.0 if side == "long" else -1.0
    return Trade(
        candidate_id=candidate_id,
        split=entry_candle.split,
        entry_timestamp=entry_candle.timestamp.isoformat(),
        exit_timestamp=exit_candle.timestamp.isoformat(),
        side=side,
        entry_price=entry_price,
        exit_price=exit_price,
        stop_price=stop_price,
        target_price=target_price,
        return_r=direction * (exit_price - entry_price) / risk if risk > 0.0 else 0.0,
        exit_reason=exit_reason,
    )


def _trade_record(trade: Trade) -> dict[str, Any]:
    return {
        "candidate_id": trade.candidate_id,
        "split": trade.split,
        "entry_timestamp": trade.entry_timestamp,
        "exit_timestamp": trade.exit_timestamp,
        "side": trade.side,
        "entry_price": trade.entry_price,
        "exit_price": trade.exit_price,
        "stop_price": trade.stop_price,
        "target_price": trade.target_price,
        "return_r": trade.return_r,
        "won": trade.return_r > 0.0,
        "exit_reason": trade.exit_reason,
    }


def _metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(trade["return_r"]) for trade in trades]
    gross_profit = sum(value for value in returns if value > 0.0)
    gross_loss = abs(sum(value for value in returns if value < 0.0))
    if not returns:
        profit_factor: float | str = 0.0
    elif gross_loss == 0.0 and gross_profit > 0.0:
        profit_factor = "inf"
    else:
        profit_factor = gross_profit / gross_loss if gross_loss else 0.0
    return {
        "trades": len(returns),
        "wins": sum(1 for value in returns if value > 0.0),
        "losses": sum(1 for value in returns if value < 0.0),
        "win_rate": _rate(sum(1 for value in returns if value > 0.0), len(returns)),
        "gross_profit_r": gross_profit,
        "gross_loss_r": gross_loss,
        "profit_factor": profit_factor,
        "expectancy_r": sum(returns) / len(returns) if returns else 0.0,
        "max_consecutive_losses": _max_consecutive_losses(returns),
        "side_counts": _counts(trades, "side"),
        "exit_reason_counts": _counts(trades, "exit_reason"),
    }


def _gate_failures(train: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    train_pf = _pf_value(train["profit_factor"])
    validation_pf = _pf_value(validation["profit_factor"])
    if train_pf < GATE["train_profit_factor_min"]:
        failures.append("train_profit_factor_below_fixed_gate")
    if validation_pf < GATE["validation_profit_factor_min"]:
        failures.append("validation_profit_factor_below_fixed_gate")
    if int(validation["trades"]) < GATE["validation_trades_min"]:
        failures.append("validation_trades_below_fixed_gate")
    if float(train["expectancy_r"]) <= GATE["train_expectancy_min_exclusive"]:
        failures.append("train_expectancy_not_positive")
    if float(validation["expectancy_r"]) <= GATE["validation_expectancy_min_exclusive"]:
        failures.append("validation_expectancy_not_positive")
    if int(train["max_consecutive_losses"]) > GATE["max_consecutive_losses_max"]:
        failures.append("train_max_consecutive_losses_above_fixed_gate")
    if int(validation["max_consecutive_losses"]) > GATE["max_consecutive_losses_max"]:
        failures.append("validation_max_consecutive_losses_above_fixed_gate")
    if not _validation_pf_ratio_passes(train_pf, validation_pf):
        failures.append("validation_profit_factor_less_than_0_75_train_profit_factor")
    return failures


def _base_report(
    *,
    board_status: str,
    candidate_results: list[dict[str, Any]],
    best_candidate: dict[str, Any] | None,
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
    data_files_used: list[str],
    split_candle_counts: dict[str, int],
) -> dict[str, Any]:
    return {
        "board_version": BOARD_VERSION,
        "board_status": board_status,
        "source_triage_versions": list(SOURCE_TRIAGE_VERSIONS),
        "tested_candidate_ids": list(SHORTLIST),
        "candidate_results": candidate_results,
        "best_candidate_id": best_candidate.get("candidate_id") if best_candidate else None,
        "best_candidate_metrics": best_candidate_metrics(best_candidate),
        "best_candidate_passed_gate": best_candidate.get("passed_gate") if best_candidate else False,
        "rejected_do_not_retune_candidates": [
            result["candidate_id"] for result in candidate_results if result.get("passed_gate") is not True
        ],
        "fixed_gate": dict(GATE),
        "timeframe": "M15",
        "data_files_used": data_files_used,
        "split_candle_counts": split_candle_counts,
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
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def best_candidate_metrics(best_candidate: dict[str, Any] | None) -> dict[str, Any] | None:
    if best_candidate is None:
        return None
    return {
        "train": best_candidate["train_metrics"],
        "validation": best_candidate["validation_metrics"],
    }


def _split_candles(records: list[dict[str, float | str]], manifest: dict[str, Any]) -> tuple[list[Candle], dict[str, int]]:
    policy = manifest["split_policy"]
    train_end = _dt(str(policy["train_end"]))
    validation_start = _dt(str(policy["validation_start"]))
    validation_end = _dt(str(policy["validation_end"]))
    counts = {"train": 0, "validation": 0, "excluded_oos": 0, "other": 0}
    candles: list[Candle] = []
    for record in records:
        timestamp = _dt(str(record["timestamp"]))
        if timestamp <= train_end:
            split = "train"
        elif validation_start <= timestamp <= validation_end:
            split = "validation"
        elif timestamp > validation_end:
            split = "excluded_oos"
        else:
            split = "other"
        counts[split] += 1
        candles.append(
            Candle(
                timestamp=timestamp,
                split=split,
                open=float(record["open"]),
                high=float(record["high"]),
                low=float(record["low"]),
                close=float(record["close"]),
                volume=float(record["volume"]),
            )
        )
    return sorted(candles, key=lambda candle: candle.timestamp), counts


def _candles_by_day(candles: list[Candle]) -> dict[str, list[Candle]]:
    grouped: dict[str, list[Candle]] = {}
    for candle in candles:
        grouped.setdefault(candle.timestamp.date().isoformat(), []).append(candle)
    return {day: sorted(day_candles, key=lambda candle: candle.timestamp) for day, day_candles in sorted(grouped.items())}


def _candle_at(candles: list[Candle], candle_time: time) -> Candle | None:
    return next((candle for candle in candles if candle.timestamp.time() == candle_time), None)


def _time_exit_candle(candles: list[Candle], exit_time: time) -> Candle | None:
    eligible = [candle for candle in candles if candle.timestamp.time() < exit_time]
    return eligible[-1] if eligible else None


def _in_window(timestamp: datetime, start: time, end: time) -> bool:
    value = timestamp.time()
    return start <= value < end


def _combine_time(timestamp: datetime, value: time) -> datetime:
    return datetime.combine(timestamp.date(), value)


def _fixed_rule_specs() -> dict[str, dict[str, Any]]:
    return {
        "prior_day_liquidity_sweep_reversal": {
            "timeframe": "M15",
            "reference": "previous_completed_trading_day_high_low",
            "entry": "close_back_inside_previous_day_range_after_sweep",
            "session_filter_utc": "07:00-20:00",
            "per_day_limit": "one_long_sweep_and_one_short_sweep",
            "stop": "sweep_candle_extreme",
            "target": "midpoint_of_previous_day_range",
            "time_exit_utc": "20:00",
            "invalidation": "next_m15_close_beyond_sweep_extreme_in_breakout_direction",
        },
        "london_opening_range_breakout_or_first_candle_direction": {
            "timeframe": "M15",
            "london_anchor_utc": "07:00",
            "first_candle_utc": "07:00-07:15",
            "direction": "first_candle_body_direction_with_body_at_least_20pct_range",
            "entry": "close_of_07_00_utc_candle",
            "stop": "first_candle_opposite_extreme",
            "target": "1.5R",
            "time_exit_utc": "12:00",
            "invalidation": "skip_zero_or_invalid_stop_distance",
        },
        "asian_range_london_breakout_confirmation": {
            "timeframe": "M15",
            "asian_range_utc": "00:00-06:59",
            "entry_window_utc": "07:00-11:00",
            "direction": "first_m15_close_outside_asian_range",
            "per_day_limit": "first_valid_breakout_per_direction",
            "stop": "asian_midpoint",
            "target": "1.0_asian_range_from_entry",
            "time_exit_utc": "20:00",
            "invalidation": "next_m15_close_back_inside_asian_range",
        },
    }


def _source_blockers(source_triage: dict[str, Any] | None, source_addendum: dict[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if source_triage is None:
        blockers.append("source_v0_52_report_missing_or_invalid")
    else:
        if source_triage.get("triage_version") != "v0_52":
            blockers.append("source_v0_52_version_mismatch")
        if source_triage.get("shortlist_for_v0_53") != list(SHORTLIST):
            blockers.append("source_v0_52_shortlist_mismatch")
    if source_addendum is None:
        blockers.append("source_v0_52_1_report_missing_or_invalid")
    else:
        if source_addendum.get("addendum_version") != "v0_52_1":
            blockers.append("source_v0_52_1_version_mismatch")
        if source_addendum.get("final_shortlist_for_v0_53") != list(SHORTLIST):
            blockers.append("source_v0_52_1_shortlist_mismatch")
        if source_addendum.get("shortlist_changed") is not False:
            blockers.append("source_v0_52_1_shortlist_changed")
    return blockers


def _manifest_blockers(manifest: dict[str, Any] | None) -> list[str]:
    if manifest is None:
        return ["dataset_manifest_missing_or_invalid"]
    policy = manifest.get("split_policy")
    if not isinstance(policy, dict):
        return ["dataset_manifest_split_policy_missing"]
    required = {"train_end", "validation_start", "validation_end", "oos_start"}
    missing = sorted(required.difference(policy))
    if missing:
        return [f"dataset_manifest_split_policy_missing:{','.join(missing)}"]
    return []


def _warnings(candidate_results: list[dict[str, Any]], split_candle_counts: dict[str, int]) -> list[str]:
    warnings = [
        "research_only_external_shortlist_board_not_execution",
        "fixed_rules_only_no_retune_no_threshold_search_no_parameter_grid",
        "oos_candles_on_disk_excluded_from_evaluation",
        "same_candle_stop_and_target_resolution_is_conservative_stop_first",
    ]
    if split_candle_counts.get("excluded_oos", 0) > 0:
        warnings.append(f"excluded_oos_candle_count:{split_candle_counts['excluded_oos']}")
    if sum(1 for result in candidate_results if result.get("passed_gate") is True) > 1:
        warnings.append("multiple_external_shortlist_candidates_passed_fixed_train_validation_gate")
    return warnings


def _candidate_sort_key(result: dict[str, Any]) -> tuple[bool, float, float, int, float]:
    validation = result["validation_metrics"]
    train = result["train_metrics"]
    return (
        bool(result["passed_gate"]),
        _pf_value(validation["profit_factor"]),
        float(validation["expectancy_r"]),
        int(validation["trades"]),
        _pf_value(train["profit_factor"]),
    )


def _validation_pf_ratio_passes(train_pf: float, validation_pf: float) -> bool:
    if train_pf == float("inf"):
        return validation_pf == float("inf")
    return validation_pf >= GATE["validation_pf_min_train_pf_ratio"] * train_pf


def _pf_value(value: Any) -> float:
    if value == "inf":
        return float("inf")
    return float(value or 0.0)


def _max_consecutive_losses(returns: list[float]) -> int:
    max_losses = 0
    current = 0
    for value in returns:
        if value < 0.0:
            current += 1
            max_losses = max(max_losses, current)
        else:
            current = 0
    return max_losses


def _counts(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item[key])
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


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


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
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
