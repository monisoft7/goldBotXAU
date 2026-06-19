"""v0_60 standardized second-tier fixed-rule train/validation board."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any, Callable

from src.data.xauusd_csv_loader import load_xauusd_m15_csvs

BOARD_VERSION = "v0_60"
SOURCE_STANDARDIZATION_VERSION = "v0_59"
DEFAULT_OUTPUT = Path("reports") / "xauusd_second_tier_board_v0_60.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"
DEFAULT_V0_59_REPORT = Path("reports") / "xauusd_research_lab_warning_standardization_v0_59.json"

PASSED = "second_tier_candidate_passed_train_validation"
NONE_PASSED = "no_second_tier_candidate_passed"
BLOCKED_MISSING_POLICY_DOCS = "blocked_missing_v0_59_policy_docs"
BLOCKED_MISSING_DATA = "blocked_missing_required_data"
BOARD_FAILED = "board_failed"

CANDIDATES = (
    "failed_m15_swing_breakout_reversal",
    "ny_liquidity_sweep_reversal",
    "sequential_m5_move_mean_reversion",
)

POLICY_DOCUMENTS = {
    "cost_policy": "docs/research_lab_cost_policy.md",
    "timestamp_session_policy": "docs/research_lab_timestamp_and_session_policy.md",
    "gap_classification_policy": "docs/research_lab_gap_classification_policy.md",
    "gate_policy": "docs/research_lab_gate_policy.md",
}

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


def build_xauusd_second_tier_fixed_rule_board_v0_60(
    *,
    data_dir: str | Path = "data",
    m15_pattern: str = "xauusd_m15_*.csv",
    m5_pattern: str = "xauusd_m5_xauusd_2023-01-01_2025-12-31.csv",
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_standardization_path: str | Path = DEFAULT_V0_59_REPORT,
    policy_root: str | Path = ".",
) -> dict[str, Any]:
    """Evaluate exactly the v0_60 second-tier ideas on train/validation rows."""
    try:
        manifest = _read_json(Path(manifest_path))
        standardization = _read_json(Path(source_standardization_path))
        policy_blockers = _policy_blockers(standardization, Path(policy_root))
        manifest_blockers = _manifest_blockers(manifest)
        if policy_blockers:
            return _blocked_report(
                board_status=BLOCKED_MISSING_POLICY_DOCS,
                blockers=policy_blockers,
                data_files_used={"M15": [], "M5": []},
                split_candle_counts=_empty_split_counts(),
                timestamp_basis=_timestamp_basis(standardization),
            )
        if manifest_blockers:
            return _blocked_report(
                board_status=BLOCKED_MISSING_DATA,
                blockers=manifest_blockers,
                data_files_used={"M15": [], "M5": []},
                split_candle_counts=_empty_split_counts(),
                timestamp_basis=_timestamp_basis(standardization),
            )

        assert manifest is not None
        m15_load = load_xauusd_m15_csvs(data_dir=data_dir, pattern=m15_pattern)
        m5_load = load_xauusd_m15_csvs(data_dir=data_dir, pattern=m5_pattern)
        m15_candles, m15_split_counts = _split_candles(m15_load.records, manifest)
        m5_candles, m5_split_counts = _split_candles(m5_load.records, manifest)
        m15_eval = [candle for candle in m15_candles if candle.split in {"train", "validation"}]
        m5_eval = [candle for candle in m5_candles if candle.split in {"train", "validation"}]

        data_blockers: list[str] = []
        if not m15_load.files:
            data_blockers.append("m15_data_files_missing")
        if not m5_load.files:
            data_blockers.append("m5_data_files_missing")
        if not m15_eval:
            data_blockers.append("train_validation_m15_rows_missing")
        if not m5_eval:
            data_blockers.append("train_validation_m5_rows_missing")
        for timeframe, counts in (("m15", m15_split_counts), ("m5", m5_split_counts)):
            if counts["train"] <= 0:
                data_blockers.append(f"train_{timeframe}_rows_missing")
            if counts["validation"] <= 0:
                data_blockers.append(f"validation_{timeframe}_rows_missing")
        split_counts = {"M15": m15_split_counts, "M5": m5_split_counts}
        data_files_used = {
            "M15": [path.as_posix() for path in m15_load.files],
            "M5": [path.as_posix() for path in m5_load.files],
        }
        if data_blockers:
            return _blocked_report(
                board_status=BLOCKED_MISSING_DATA,
                blockers=data_blockers,
                data_files_used=data_files_used,
                split_candle_counts=split_counts,
                timestamp_basis=_timestamp_basis(standardization),
            )

        candles_by_candidate = {
            "failed_m15_swing_breakout_reversal": m15_eval,
            "ny_liquidity_sweep_reversal": m15_eval,
            "sequential_m5_move_mean_reversion": m5_eval,
        }
        candidate_results = [
            _evaluate_candidate(candidate_id, candles_by_candidate[candidate_id]) for candidate_id in CANDIDATES
        ]
        passed = [result for result in candidate_results if result["passed_gate"] is True]
        best = max(candidate_results, key=_candidate_sort_key)
        board_status = PASSED if passed else NONE_PASSED
        next_step = (
            "lock fixed candidate artifact and prepare one-time OOS protocol, no OOS yet."
            if passed
            else "broaden non-OOS research or consider adding external features such as DXY/yields/news calendar before further strategy tests."
        )

        return _base_report(
            board_status=board_status,
            candidate_results=candidate_results,
            best_candidate=best,
            blockers=[],
            warnings=_warnings(candidate_results, split_counts),
            next_recommended_step=next_step,
            data_files_used=data_files_used,
            split_candle_counts=split_counts,
            timestamp_basis=_timestamp_basis(standardization),
        )
    except Exception as exc:
        return _base_report(
            board_status=BOARD_FAILED,
            candidate_results=[],
            best_candidate=None,
            blockers=[f"board_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair v0_60 board implementation or input artifacts before rerunning",
            data_files_used={"M15": [], "M5": []},
            split_candle_counts=_empty_split_counts(),
            timestamp_basis=None,
        )


def save_xauusd_second_tier_fixed_rule_board(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _blocked_report(
    *,
    board_status: str,
    blockers: list[str],
    data_files_used: dict[str, list[str]],
    split_candle_counts: dict[str, dict[str, int]],
    timestamp_basis: str | None,
) -> dict[str, Any]:
    next_step = (
        "restore required v0_59 policy docs and standardization report before rerunning v0_60"
        if board_status == BLOCKED_MISSING_POLICY_DOCS
        else "restore required train/validation M15 and M5 data before rerunning v0_60"
    )
    return _base_report(
        board_status=board_status,
        candidate_results=[],
        best_candidate=None,
        blockers=blockers,
        warnings=[],
        next_recommended_step=next_step,
        data_files_used=data_files_used,
        split_candle_counts=split_candle_counts,
        timestamp_basis=timestamp_basis,
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
        "timeframe": _fixed_rule_specs()[candidate_id]["timeframe"],
        "fixed_rules": _fixed_rule_specs()[candidate_id],
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "combined_trade_count": len(trade_records),
        "split_trade_counts": {"train": len(train_trades), "validation": len(validation_trades)},
        "passed_gate": passed,
        "gate_failures": gate_failures,
        "candidate_disposition": "requires_locked_artifact_before_oos" if passed else "rejected_do_not_retune",
        "do_not_retune": not passed,
        "executable_candidate_created": False,
        "trade_sample": trade_records[:5],
        "safety": _safety_flags(),
    }


def _rules() -> dict[str, Rule]:
    return {
        "failed_m15_swing_breakout_reversal": _failed_m15_swing_breakout_reversal_trades,
        "ny_liquidity_sweep_reversal": _ny_liquidity_sweep_reversal_trades,
        "sequential_m5_move_mean_reversion": _sequential_m5_move_mean_reversion_trades,
    }


def _failed_m15_swing_breakout_reversal_trades(candles: list[Candle]) -> list[Trade]:
    trades: list[Trade] = []
    for index in range(20, len(candles)):
        candle = candles[index]
        if not _in_session(candle.timestamp, time(7, 0), time(20, 0)):
            continue
        prior = candles[index - 20 : index]
        if any(item.split != candle.split for item in prior):
            continue
        prior_high = max(item.high for item in prior)
        prior_low = min(item.low for item in prior)
        midpoint = (prior_high + prior_low) / 2.0
        future = _future_same_split(candles, index, max_items=8)
        if candle.high > prior_high and candle.close < prior_high:
            trade = _simulate_reversal(
                candidate_id="failed_m15_swing_breakout_reversal",
                side="short",
                entry_candle=candle,
                future=future,
                stop_price=candle.high,
                target_price=midpoint,
                breakout_extreme=candle.high,
                max_bars=8,
                target_reason="target_midpoint_prior_20_m15_range",
                time_exit_reason="time_exit_8_m15_bars_or_20_00_utc",
            )
            if trade is not None:
                trades.append(trade)
        if candle.low < prior_low and candle.close > prior_low:
            trade = _simulate_reversal(
                candidate_id="failed_m15_swing_breakout_reversal",
                side="long",
                entry_candle=candle,
                future=future,
                stop_price=candle.low,
                target_price=midpoint,
                breakout_extreme=candle.low,
                max_bars=8,
                target_reason="target_midpoint_prior_20_m15_range",
                time_exit_reason="time_exit_8_m15_bars_or_20_00_utc",
            )
            if trade is not None:
                trades.append(trade)
    return sorted(trades, key=lambda trade: (trade.entry_timestamp, trade.side))


def _ny_liquidity_sweep_reversal_trades(candles: list[Candle]) -> list[Trade]:
    trades: list[Trade] = []
    for _day, day_candles in _candles_by_day(candles).items():
        reference = [candle for candle in day_candles if _in_session(candle.timestamp, time(0, 0), time(12, 0))]
        if not reference:
            continue
        range_high = max(candle.high for candle in reference)
        range_low = min(candle.low for candle in reference)
        midpoint = (range_high + range_low) / 2.0
        long_taken = False
        short_taken = False
        for index, candle in enumerate(day_candles):
            if not _in_window_inclusive(candle.timestamp, time(12, 30), time(14, 30)):
                continue
            future = day_candles[index + 1 :]
            if not short_taken and candle.high > range_high and candle.close < range_high:
                trade = _simulate_reversal(
                    candidate_id="ny_liquidity_sweep_reversal",
                    side="short",
                    entry_candle=candle,
                    future=future,
                    stop_price=candle.high,
                    target_price=midpoint,
                    breakout_extreme=candle.high,
                    max_bars=None,
                    target_reason="target_midpoint_00_00_12_00_range",
                    time_exit_reason="time_exit_20_00_utc",
                )
                if trade is not None:
                    trades.append(trade)
                    short_taken = True
            if not long_taken and candle.low < range_low and candle.close > range_low:
                trade = _simulate_reversal(
                    candidate_id="ny_liquidity_sweep_reversal",
                    side="long",
                    entry_candle=candle,
                    future=future,
                    stop_price=candle.low,
                    target_price=midpoint,
                    breakout_extreme=candle.low,
                    max_bars=None,
                    target_reason="target_midpoint_00_00_12_00_range",
                    time_exit_reason="time_exit_20_00_utc",
                )
                if trade is not None:
                    trades.append(trade)
                    long_taken = True
    return sorted(trades, key=lambda trade: (trade.entry_timestamp, trade.side))


def _sequential_m5_move_mean_reversion_trades(candles: list[Candle]) -> list[Trade]:
    trades: list[Trade] = []
    up_streak = 0
    down_streak = 0
    for index in range(1, len(candles)):
        if candles[index].split != candles[index - 1].split:
            up_streak = 0
            down_streak = 0
        current = candles[index]
        previous = candles[index - 1]
        if current.close > previous.close:
            up_streak += 1
            down_streak = 0
        elif current.close < previous.close:
            down_streak += 1
            up_streak = 0
        else:
            up_streak = 0
            down_streak = 0
        if not _in_session(current.timestamp, time(7, 0), time(20, 0)):
            continue
        first_index = index - 4
        if first_index < 0:
            continue
        first = candles[first_index]
        future = _future_same_split(candles, index, max_items=12)
        if up_streak == 5:
            trade = _simulate_sequential_reversion(
                side="short",
                entry_candle=current,
                first_candle=first,
                future=future,
                streak_close=current.close,
            )
            if trade is not None:
                trades.append(trade)
        if down_streak == 5:
            trade = _simulate_sequential_reversion(
                side="long",
                entry_candle=current,
                first_candle=first,
                future=future,
                streak_close=current.close,
            )
            if trade is not None:
                trades.append(trade)
    return sorted(trades, key=lambda trade: (trade.entry_timestamp, trade.side))


def _simulate_reversal(
    *,
    candidate_id: str,
    side: str,
    entry_candle: Candle,
    future: list[Candle],
    stop_price: float,
    target_price: float,
    breakout_extreme: float,
    max_bars: int | None,
    target_reason: str,
    time_exit_reason: str,
) -> Trade | None:
    entry = entry_candle.close
    risk = entry - stop_price if side == "long" else stop_price - entry
    target_is_beyond_entry = target_price > entry if side == "long" else target_price < entry
    if risk <= 0.0 or not target_is_beyond_entry:
        return None
    eligible = _eligible_future(entry_candle, future, max_bars=max_bars, exit_time=time(20, 0))
    if not eligible:
        return None
    next_candle = future[0] if future else None
    if next_candle is not None:
        invalid = next_candle.close < breakout_extreme if side == "long" else next_candle.close > breakout_extreme
        if invalid:
            return _trade(candidate_id, side, entry_candle, next_candle, entry, next_candle.close, stop_price, target_price, "invalidated_next_candle_close_beyond_extreme")
    for candle in eligible:
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
    time_exit = eligible[-1]
    return _trade(candidate_id, side, entry_candle, time_exit, entry, time_exit.close, stop_price, target_price, time_exit_reason)


def _simulate_sequential_reversion(
    *,
    side: str,
    entry_candle: Candle,
    first_candle: Candle,
    future: list[Candle],
    streak_close: float,
) -> Trade | None:
    entry = entry_candle.close
    stop_distance = abs(entry - first_candle.open)
    if stop_distance <= 0.0:
        return None
    stop_price = entry - stop_distance if side == "long" else entry + stop_distance
    target_price = first_candle.open
    target_is_beyond_entry = target_price > entry if side == "long" else target_price < entry
    if not target_is_beyond_entry:
        return None
    eligible = future[:12]
    if not eligible:
        return None
    next_candle = future[0] if future else None
    if next_candle is not None:
        invalid = next_candle.close < streak_close if side == "long" else next_candle.close > streak_close
        if invalid:
            return _trade(
                "sequential_m5_move_mean_reversion",
                side,
                entry_candle,
                next_candle,
                entry,
                next_candle.close,
                stop_price,
                target_price,
                "invalidated_next_m5_close_continued_streak_direction",
            )
    for candle in eligible:
        if side == "long":
            if candle.low <= stop_price:
                return _trade("sequential_m5_move_mean_reversion", side, entry_candle, candle, entry, stop_price, stop_price, target_price, "stop")
            if candle.high >= target_price:
                return _trade("sequential_m5_move_mean_reversion", side, entry_candle, candle, entry, target_price, stop_price, target_price, "target_first_candle_open")
        else:
            if candle.high >= stop_price:
                return _trade("sequential_m5_move_mean_reversion", side, entry_candle, candle, entry, stop_price, stop_price, target_price, "stop")
            if candle.low <= target_price:
                return _trade("sequential_m5_move_mean_reversion", side, entry_candle, candle, entry, target_price, stop_price, target_price, "target_first_candle_open")
    time_exit = eligible[-1]
    return _trade("sequential_m5_move_mean_reversion", side, entry_candle, time_exit, entry, time_exit.close, stop_price, target_price, "time_exit_12_m5_bars")


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
    data_files_used: dict[str, list[str]],
    split_candle_counts: dict[str, dict[str, int]],
    timestamp_basis: str | None,
) -> dict[str, Any]:
    return {
        "board_version": BOARD_VERSION,
        "board_status": board_status,
        "source_standardization_version": SOURCE_STANDARDIZATION_VERSION,
        "standardized_policy_references": dict(POLICY_DOCUMENTS),
        "tested_candidate_ids": list(CANDIDATES),
        "candidate_results": candidate_results,
        "best_candidate_id": best_candidate.get("candidate_id") if best_candidate else None,
        "best_candidate_metrics": best_candidate_metrics(best_candidate),
        "best_candidate_passed_gate": best_candidate.get("passed_gate") if best_candidate else False,
        "rejected_do_not_retune_candidates": [
            result["candidate_id"] for result in candidate_results if result.get("passed_gate") is not True
        ],
        "fixed_gate": dict(GATE),
        "data_files_used": data_files_used,
        "split_candle_counts": split_candle_counts,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "gates_lowered": False,
        "past_metrics_changed": False,
        "executable_candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "data_csv_added_to_git": False,
        "timestamp_basis_reported": timestamp_basis is not None,
        "timestamp_basis": timestamp_basis,
        "cost_policy_reference": POLICY_DOCUMENTS["cost_policy"],
        "gap_policy_reference": POLICY_DOCUMENTS["gap_classification_policy"],
        "gate_policy_reference": POLICY_DOCUMENTS["gate_policy"],
        "timestamp_session_policy_reference": POLICY_DOCUMENTS["timestamp_session_policy"],
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


def _future_same_split(candles: list[Candle], index: int, *, max_items: int) -> list[Candle]:
    split = candles[index].split
    future: list[Candle] = []
    for future_index in range(index + 1, len(candles)):
        candle = candles[future_index]
        if candle.split != split:
            break
        future.append(candle)
        if len(future) >= max_items:
            break
    return future


def _eligible_future(entry_candle: Candle, future: list[Candle], *, max_bars: int | None, exit_time: time) -> list[Candle]:
    same_day_before_exit = [
        candle
        for candle in future
        if candle.timestamp.date() == entry_candle.timestamp.date() and candle.timestamp.time() < exit_time
    ]
    return same_day_before_exit[:max_bars] if max_bars is not None else same_day_before_exit


def _in_session(timestamp: datetime, start: time, end: time) -> bool:
    value = timestamp.time()
    return start <= value < end


def _in_window_inclusive(timestamp: datetime, start: time, end: time) -> bool:
    value = timestamp.time()
    return start <= value <= end


def _fixed_rule_specs() -> dict[str, dict[str, Any]]:
    return {
        "failed_m15_swing_breakout_reversal": {
            "timeframe": "M15",
            "session_filter_utc": "07:00-20:00",
            "swing_lookback_completed_m15_candles": 20,
            "short_setup": "current_high_breaks_prior_20_high_and_close_back_below_prior_20_high",
            "long_setup": "current_low_breaks_prior_20_low_and_close_back_above_prior_20_low",
            "entry": "close_of_current_m15_candle",
            "stop": "failed_breakout_candle_extreme",
            "target": "midpoint_of_prior_20_m15_range",
            "time_exit": "after_8_m15_bars_or_20_00_utc",
            "invalidation": "next_m15_close_beyond_failed_breakout_extreme_in_breakout_direction",
        },
        "ny_liquidity_sweep_reversal": {
            "timeframe": "M15",
            "reference_range_utc": "00:00-12:00",
            "entry_window_utc": "12:30-14:30",
            "short_setup": "sweep_above_reference_high_and_close_back_below_reference_high",
            "long_setup": "sweep_below_reference_low_and_close_back_above_reference_low",
            "entry": "close_of_sweep_m15_candle",
            "stop": "sweep_candle_extreme",
            "target": "midpoint_of_00_00_12_00_range",
            "time_exit": "20:00_utc",
            "invalidation": "next_m15_close_beyond_sweep_extreme_in_breakout_direction",
            "timestamp_policy": "fixed_utc_windows_with_timestamp_basis_reported",
        },
        "sequential_m5_move_mean_reversion": {
            "timeframe": "M5",
            "session_filter_utc": "07:00-20:00",
            "streak_length": 5,
            "short_setup": "exactly_5_consecutive_m5_closes_higher_than_previous_close",
            "long_setup": "exactly_5_consecutive_m5_closes_lower_than_previous_close",
            "entry": "close_of_5th_m5_candle",
            "stop": "entry_plus_or_minus_distance_from_first_candle_open_to_fifth_candle_close",
            "target": "open_of_first_candle_in_streak",
            "time_exit": "after_12_m5_bars",
            "invalidation": "next_m5_close_continues_streak_direction_beyond_5th_candle_close",
            "news_calendar_filter": "none_in_v0_60",
        },
    }


def _policy_blockers(standardization: dict[str, Any] | None, root: Path) -> list[str]:
    blockers: list[str] = []
    if standardization is None:
        blockers.append("source_v0_59_standardization_report_missing_or_invalid")
    else:
        if standardization.get("standardization_version") != SOURCE_STANDARDIZATION_VERSION:
            blockers.append("source_v0_59_standardization_version_mismatch")
        if standardization.get("standardization_status") != "lab_warning_standardization_completed":
            blockers.append("source_v0_59_standardization_not_completed")
        for field in (
            "cost_policy_documented",
            "timestamp_policy_documented",
            "gap_classification_policy_documented",
            "gate_policy_documented",
        ):
            if standardization.get(field) is not True:
                blockers.append(f"source_v0_59_{field}_not_true")
    for label, relative_path in POLICY_DOCUMENTS.items():
        if not (root / relative_path).exists():
            blockers.append(f"{label}_document_missing:{relative_path}")
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


def _timestamp_basis(standardization: dict[str, Any] | None) -> str | None:
    if not isinstance(standardization, dict):
        return None
    policy = standardization.get("timestamp_session_policy")
    if not isinstance(policy, dict):
        return None
    basis = policy.get("timestamp_basis")
    return str(basis) if basis is not None else None


def _warnings(candidate_results: list[dict[str, Any]], split_candle_counts: dict[str, dict[str, int]]) -> list[str]:
    warnings = [
        "research_only_second_tier_board_not_execution",
        "fixed_rules_only_no_retune_no_threshold_search_no_parameter_grid",
        "oos_candles_on_disk_excluded_from_evaluation",
        "v0_59_cost_policy_referenced_metrics_remain_raw_r_without_retroactive_cost_recompute",
        "timestamp_basis_reported_from_v0_59_unknown_or_broker_server_time",
        "same_candle_stop_and_target_resolution_is_conservative_stop_first",
    ]
    for timeframe, counts in sorted(split_candle_counts.items()):
        if counts.get("excluded_oos", 0) > 0:
            warnings.append(f"{timeframe.lower()}_excluded_oos_candle_count:{counts['excluded_oos']}")
    if sum(1 for result in candidate_results if result.get("passed_gate") is True) > 1:
        warnings.append("multiple_second_tier_candidates_passed_fixed_train_validation_gate")
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


def _empty_split_counts() -> dict[str, dict[str, int]]:
    empty = {"train": 0, "validation": 0, "excluded_oos": 0, "other": 0}
    return {"M15": dict(empty), "M5": dict(empty)}


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "gates_lowered": False,
        "past_metrics_changed": False,
        "executable_candidate_created": False,
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
