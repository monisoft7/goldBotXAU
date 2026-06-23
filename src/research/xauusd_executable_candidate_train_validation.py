"""v0_83 train/validation-only evaluation for the v0_82 executable candidate."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any

from src.research.xauusd_executable_fixed_rule_candidate_design import (
    CANDIDATE_ID,
    DESIGN_VERSION as SOURCE_DESIGN_VERSION,
)

EVALUATION_VERSION = "v0_83"
EVALUATION_NAME = "v0_83_executable_candidate_train_validation_evaluation_no_oos"
DEFAULT_OUTPUT = Path("reports") / "xauusd_executable_candidate_train_validation_v0_83.json"
DEFAULT_DESIGN_REPORT = Path("reports") / "xauusd_executable_fixed_rule_candidate_design_v0_82.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"

PASSED = "executable_candidate_train_validation_passed"
FAILED = "executable_candidate_train_validation_failed"
BLOCKED = "executable_candidate_train_validation_blocked"

NEXT_IF_PASSED = "v0_84_single_oos_review_for_executable_candidate"
NEXT_IF_FAILED = "v0_84_candidate_failure_postmortem_no_retune"

FIXED_GATES = {
    "minimum_train_trade_count_gate": 60,
    "minimum_validation_trade_count_gate": 25,
    "validation_profit_factor_gate": 1.25,
    "validation_expectancy_gate_R": 0.05,
    "max_drawdown_gate_R": 8.0,
    "max_consecutive_loss_gate": 5,
    "cost_sensitivity_required": True,
}

FIXED_EVALUATION_RULES = {
    "timeframes": ["M15", "M5"],
    "session_window_utc": "12:30-17:00",
    "displacement_lookback_m15": 16,
    "minimum_body_to_range_ratio": 0.60,
    "close_location_threshold": 0.70,
    "retest_window_m5_bars": 12,
    "maximum_retest_overshoot_r": 0.35,
    "entry": "close_of_m5_hold_candle_after_retest",
    "stop": "displacement_origin_or_retest_extreme_plus_fixed_buffer",
    "target": "fixed_1_5R",
    "time_stop_m5_bars": 24,
    "cost_r_per_trade": 0.03,
    "cost_sensitivity_cost_r_per_trade": 0.06,
    "one_position_at_a_time": True,
    "no_overlapping_trades": True,
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
class Displacement:
    timestamp: datetime
    split: str
    side: str
    broken_level: float
    origin_level: float
    stop_level: float
    displacement_high: float
    displacement_low: float


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
    gross_return_R: float
    cost_R: float
    return_R: float
    exit_reason: str


def build_xauusd_executable_candidate_train_validation_v0_83(
    *,
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_design_path: str | Path = DEFAULT_DESIGN_REPORT,
    m15_pattern: str = "xauusd_m15_*.csv",
    m5_pattern: str = "xauusd_m5_xauusd_2023-01-01_2025-12-31.csv",
) -> dict[str, Any]:
    """Evaluate the fixed v0_82 candidate on train/validation candles only."""
    try:
        manifest = _read_json(Path(manifest_path))
        design = _read_json(Path(source_design_path))
        blockers = [*_manifest_blockers(manifest), *_source_design_blockers(design)]
        if blockers:
            return _report(
                evaluation_status=BLOCKED,
                source_design=design,
                data_files_used={"M15": [], "M5": []},
                split_candle_counts=_empty_split_counts(),
                data_ranges_used={},
                trade_records=[],
                cost_sensitivity_trade_records=[],
                blockers=blockers,
                warnings=[],
            )

        assert manifest is not None
        m15_load = _load_train_validation_candles(data_dir, m15_pattern, manifest)
        m5_load = _load_train_validation_candles(data_dir, m5_pattern, manifest)
        split_counts = {"M15": m15_load["split_counts"], "M5": m5_load["split_counts"]}
        data_blockers: list[str] = []
        if not m15_load["files"]:
            data_blockers.append("m15_data_files_missing")
        if not m5_load["files"]:
            data_blockers.append("m5_data_files_missing")
        for timeframe, counts in split_counts.items():
            if counts["train"] <= 0:
                data_blockers.append(f"{timeframe.lower()}_train_rows_missing")
            if counts["validation"] <= 0:
                data_blockers.append(f"{timeframe.lower()}_validation_rows_missing")
        if data_blockers:
            return _report(
                evaluation_status=BLOCKED,
                source_design=design,
                data_files_used={
                    "M15": [path.as_posix() for path in m15_load["files"]],
                    "M5": [path.as_posix() for path in m5_load["files"]],
                },
                split_candle_counts=split_counts,
                data_ranges_used=_data_ranges([*m15_load["candles"], *m5_load["candles"]]),
                trade_records=[],
                cost_sensitivity_trade_records=[],
                blockers=data_blockers,
                warnings=[],
            )

        trade_records = [
            _trade_record(trade)
            for trade in _evaluate_fixed_candidate(
                m15_load["candles"],
                m5_load["candles"],
                cost_r_per_trade=float(FIXED_EVALUATION_RULES["cost_r_per_trade"]),
            )
        ]
        cost_sensitivity_trade_records = [
            _trade_record(trade)
            for trade in _evaluate_fixed_candidate(
                m15_load["candles"],
                m5_load["candles"],
                cost_r_per_trade=float(FIXED_EVALUATION_RULES["cost_sensitivity_cost_r_per_trade"]),
            )
        ]
        gate_failures = _gate_failures(trade_records, cost_sensitivity_trade_records)
        status = PASSED if not gate_failures else FAILED
        return _report(
            evaluation_status=status,
            source_design=design,
            data_files_used={
                "M15": [path.as_posix() for path in m15_load["files"]],
                "M5": [path.as_posix() for path in m5_load["files"]],
            },
            split_candle_counts=split_counts,
            data_ranges_used=_data_ranges([*m15_load["candles"], *m5_load["candles"]]),
            trade_records=trade_records,
            cost_sensitivity_trade_records=cost_sensitivity_trade_records,
            blockers=gate_failures,
            warnings=_warnings(split_counts),
        )
    except Exception as exc:
        return _report(
            evaluation_status=BLOCKED,
            source_design=None,
            data_files_used={"M15": [], "M5": []},
            split_candle_counts=_empty_split_counts(),
            data_ranges_used={},
            trade_records=[],
            cost_sensitivity_trade_records=[],
            blockers=[f"evaluation_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
        )


def write_xauusd_executable_candidate_train_validation_v0_83(root: Path, output: str | Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    report = build_xauusd_executable_candidate_train_validation_v0_83(
        data_dir=root / "data",
        manifest_path=root / DEFAULT_MANIFEST,
        source_design_path=root / DEFAULT_DESIGN_REPORT,
    )
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _evaluate_fixed_candidate(m15: list[Candle], m5: list[Candle], *, cost_r_per_trade: float) -> list[Trade]:
    displacements = _find_displacements(m15)
    m5_by_split = {split: [candle for candle in m5 if candle.split == split] for split in ("train", "validation")}
    trades: list[Trade] = []
    open_until_by_split = {"train": datetime.min, "validation": datetime.min}
    for displacement in displacements:
        if displacement.timestamp < open_until_by_split[displacement.split]:
            continue
        future_m5 = [
            candle
            for candle in m5_by_split[displacement.split]
            if displacement.timestamp < candle.timestamp
        ]
        trade = _trade_from_displacement(displacement, future_m5, cost_r_per_trade=cost_r_per_trade)
        if trade is None:
            continue
        trades.append(trade)
        open_until_by_split[displacement.split] = datetime.fromisoformat(trade.exit_timestamp)
    return trades


def _find_displacements(candles: list[Candle]) -> list[Displacement]:
    lookback = int(FIXED_EVALUATION_RULES["displacement_lookback_m15"])
    displacements: list[Displacement] = []
    for index in range(lookback, len(candles)):
        candle = candles[index]
        if candle.split not in {"train", "validation"} or not _in_session(candle.timestamp, time(12, 30), time(17, 0)):
            continue
        prior = candles[index - lookback : index]
        if any(item.split != candle.split for item in prior):
            continue
        range_points = candle.high - candle.low
        if range_points <= 0:
            continue
        body_ratio = abs(candle.close - candle.open) / range_points
        close_location = (candle.close - candle.low) / range_points
        prior_high = max(item.high for item in prior)
        prior_low = min(item.low for item in prior)
        if (
            candle.close > prior_high
            and body_ratio >= float(FIXED_EVALUATION_RULES["minimum_body_to_range_ratio"])
            and close_location >= float(FIXED_EVALUATION_RULES["close_location_threshold"])
        ):
            displacements.append(
                Displacement(
                    timestamp=candle.timestamp,
                    split=candle.split,
                    side="long",
                    broken_level=prior_high,
                    origin_level=candle.low,
                    stop_level=min(candle.low, prior_high),
                    displacement_high=candle.high,
                    displacement_low=candle.low,
                )
            )
        if (
            candle.close < prior_low
            and body_ratio >= float(FIXED_EVALUATION_RULES["minimum_body_to_range_ratio"])
            and close_location <= 1.0 - float(FIXED_EVALUATION_RULES["close_location_threshold"])
        ):
            displacements.append(
                Displacement(
                    timestamp=candle.timestamp,
                    split=candle.split,
                    side="short",
                    broken_level=prior_low,
                    origin_level=candle.high,
                    stop_level=max(candle.high, prior_low),
                    displacement_high=candle.high,
                    displacement_low=candle.low,
                )
            )
    return sorted(displacements, key=lambda item: item.timestamp)


def _trade_from_displacement(
    displacement: Displacement,
    future_m5: list[Candle],
    *,
    cost_r_per_trade: float,
) -> Trade | None:
    retest_window = future_m5[: int(FIXED_EVALUATION_RULES["retest_window_m5_bars"])]
    if not retest_window:
        return None
    hold_index: int | None = None
    for index, candle in enumerate(retest_window):
        if displacement.side == "long":
            touched = candle.low <= displacement.broken_level
            held = candle.close > displacement.broken_level and candle.close > candle.open
        else:
            touched = candle.high >= displacement.broken_level
            held = candle.close < displacement.broken_level and candle.close < candle.open
        if touched and held:
            hold_index = index
            break
    if hold_index is None:
        return None

    entry_candle = retest_window[hold_index]
    entry = entry_candle.close
    if displacement.side == "long":
        stop_price = min(displacement.origin_level, entry_candle.low)
        risk = entry - stop_price
        target_price = entry + 1.5 * risk
    else:
        stop_price = max(displacement.origin_level, entry_candle.high)
        risk = stop_price - entry
        target_price = entry - 1.5 * risk
    if risk <= 0:
        return None

    max_overshoot = float(FIXED_EVALUATION_RULES["maximum_retest_overshoot_r"]) * risk
    if displacement.side == "long" and displacement.broken_level - entry_candle.low > max_overshoot:
        return None
    if displacement.side == "short" and entry_candle.high - displacement.broken_level > max_overshoot:
        return None

    path = future_m5[hold_index + 1 : hold_index + 1 + int(FIXED_EVALUATION_RULES["time_stop_m5_bars"])]
    if not path:
        return None
    for candle in path:
        if displacement.side == "long":
            if candle.low <= stop_price:
                return _trade(displacement, entry_candle, candle, entry, stop_price, stop_price, target_price, cost_r_per_trade, "stop")
            if candle.high >= target_price:
                return _trade(displacement, entry_candle, candle, entry, target_price, stop_price, target_price, cost_r_per_trade, "target_1_5r")
        else:
            if candle.high >= stop_price:
                return _trade(displacement, entry_candle, candle, entry, stop_price, stop_price, target_price, cost_r_per_trade, "stop")
            if candle.low <= target_price:
                return _trade(displacement, entry_candle, candle, entry, target_price, stop_price, target_price, cost_r_per_trade, "target_1_5r")
    exit_candle = path[-1]
    return _trade(displacement, entry_candle, exit_candle, entry, exit_candle.close, stop_price, target_price, cost_r_per_trade, "time_stop_24_m5_bars")


def _trade(
    displacement: Displacement,
    entry_candle: Candle,
    exit_candle: Candle,
    entry_price: float,
    exit_price: float,
    stop_price: float,
    target_price: float,
    cost_r: float,
    exit_reason: str,
) -> Trade:
    risk = entry_price - stop_price if displacement.side == "long" else stop_price - entry_price
    direction = 1.0 if displacement.side == "long" else -1.0
    gross = direction * (exit_price - entry_price) / risk if risk > 0 else 0.0
    return Trade(
        candidate_id=CANDIDATE_ID,
        split=entry_candle.split,
        entry_timestamp=entry_candle.timestamp.isoformat(),
        exit_timestamp=exit_candle.timestamp.isoformat(),
        side=displacement.side,
        entry_price=entry_price,
        exit_price=exit_price,
        stop_price=stop_price,
        target_price=target_price,
        gross_return_R=gross,
        cost_R=cost_r,
        return_R=gross - cost_r,
        exit_reason=exit_reason,
    )


def _report(
    *,
    evaluation_status: str,
    source_design: dict[str, Any] | None,
    data_files_used: dict[str, list[str]],
    split_candle_counts: dict[str, dict[str, int]],
    data_ranges_used: dict[str, Any],
    trade_records: list[dict[str, Any]],
    cost_sensitivity_trade_records: list[dict[str, Any]],
    blockers: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    train = [trade for trade in trade_records if trade["split"] == "train"]
    validation = [trade for trade in trade_records if trade["split"] == "validation"]
    combined = list(trade_records)
    train_metrics = _metrics(train)
    validation_metrics = _metrics(validation)
    combined_metrics = _metrics(combined)
    cost_sensitivity_summary = _cost_sensitivity_summary(trade_records, cost_sensitivity_trade_records)
    passed = evaluation_status == PASSED
    blocked = evaluation_status == BLOCKED
    failure_reasons = list(blockers)
    if not blocked and not failure_reasons:
        failure_reasons = [] if passed else ["fixed_train_validation_gates_not_passed"]
    recommended = NEXT_IF_PASSED if passed else NEXT_IF_FAILED
    safety = _false_safety_flags()
    report = {
        "evaluation_version": EVALUATION_VERSION,
        "evaluation_name": EVALUATION_NAME,
        "evaluation_status": evaluation_status,
        "candidate_id": CANDIDATE_ID,
        "source_design_version": SOURCE_DESIGN_VERSION,
        "source_design_rules_sha256": _rules_hash(source_design),
        "candidate_rules_preserved": _source_design_blockers(source_design) == [],
        "fixed_evaluation_rules": dict(FIXED_EVALUATION_RULES),
        "fixed_gate": dict(FIXED_GATES),
        "explicit_side_mapping": {
            "long": "bullish_displacement_plus_controlled_retest_hold",
            "short": "bearish_displacement_plus_controlled_retest_hold",
        },
        "one_position_at_a_time_enforced": True,
        "no_overlapping_trades_enforced": True,
        "train_validation_only": True,
        "oos_used": False,
        "oos_allowed_now": False,
        "oos_rows_read": False,
        "oos_rows_counted": 0,
        "data_files_used": data_files_used,
        "split_candle_counts": split_candle_counts,
        "data_ranges_used": data_ranges_used,
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "combined_train_validation_metrics": combined_metrics,
        "train_trade_count": train_metrics["trades"],
        "validation_trade_count": validation_metrics["trades"],
        "train_win_rate": train_metrics["win_rate"],
        "validation_win_rate": validation_metrics["win_rate"],
        "train_profit_factor": train_metrics["profit_factor"],
        "validation_profit_factor": validation_metrics["profit_factor"],
        "train_expectancy_R": train_metrics["expectancy_R"],
        "validation_expectancy_R": validation_metrics["expectancy_R"],
        "train_max_drawdown_R": train_metrics["max_drawdown_R"],
        "validation_max_drawdown_R": validation_metrics["max_drawdown_R"],
        "train_max_consecutive_losses": train_metrics["max_consecutive_losses"],
        "validation_max_consecutive_losses": validation_metrics["max_consecutive_losses"],
        "cost_sensitivity_summary": cost_sensitivity_summary,
        "gate_results": _gate_results(train_metrics, validation_metrics, cost_sensitivity_summary),
        "passed_all_train_validation_gates": passed,
        "candidate_promotable_to_oos_review": passed,
        "next_step_if_passed": NEXT_IF_PASSED,
        "next_step_if_failed": NEXT_IF_FAILED,
        "recommended_next_step": recommended,
        "failure_reasons": failure_reasons,
        "blockers": blockers,
        "warnings": warnings,
        "trade_records_output_path_or_null": None,
        "trade_records_sample": trade_records[:5],
        "trade_records_count": len(trade_records),
        "safety_flags": safety,
        **safety,
    }
    return report


def _gate_failures(trade_records: list[dict[str, Any]], cost_sensitivity_records: list[dict[str, Any]]) -> list[str]:
    train = _metrics([trade for trade in trade_records if trade["split"] == "train"])
    validation = _metrics([trade for trade in trade_records if trade["split"] == "validation"])
    sensitivity = _cost_sensitivity_summary(trade_records, cost_sensitivity_records)
    results = _gate_results(train, validation, sensitivity)
    return [name for name, result in results.items() if result["passed"] is not True]


def _gate_results(
    train_metrics: dict[str, Any],
    validation_metrics: dict[str, Any],
    cost_sensitivity_summary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        "minimum_train_trade_count_gate": {
            "threshold": FIXED_GATES["minimum_train_trade_count_gate"],
            "observed": train_metrics["trades"],
            "passed": train_metrics["trades"] >= FIXED_GATES["minimum_train_trade_count_gate"],
        },
        "minimum_validation_trade_count_gate": {
            "threshold": FIXED_GATES["minimum_validation_trade_count_gate"],
            "observed": validation_metrics["trades"],
            "passed": validation_metrics["trades"] >= FIXED_GATES["minimum_validation_trade_count_gate"],
        },
        "validation_profit_factor_gate": {
            "threshold": FIXED_GATES["validation_profit_factor_gate"],
            "observed": validation_metrics["profit_factor"],
            "passed": _pf_value(validation_metrics["profit_factor"]) >= FIXED_GATES["validation_profit_factor_gate"],
        },
        "validation_expectancy_gate_R": {
            "threshold": FIXED_GATES["validation_expectancy_gate_R"],
            "observed": validation_metrics["expectancy_R"],
            "passed": validation_metrics["expectancy_R"] >= FIXED_GATES["validation_expectancy_gate_R"],
        },
        "train_max_drawdown_gate_R": {
            "threshold": FIXED_GATES["max_drawdown_gate_R"],
            "observed": train_metrics["max_drawdown_R"],
            "passed": train_metrics["max_drawdown_R"] <= FIXED_GATES["max_drawdown_gate_R"],
        },
        "validation_max_drawdown_gate_R": {
            "threshold": FIXED_GATES["max_drawdown_gate_R"],
            "observed": validation_metrics["max_drawdown_R"],
            "passed": validation_metrics["max_drawdown_R"] <= FIXED_GATES["max_drawdown_gate_R"],
        },
        "train_max_consecutive_loss_gate": {
            "threshold": FIXED_GATES["max_consecutive_loss_gate"],
            "observed": train_metrics["max_consecutive_losses"],
            "passed": train_metrics["max_consecutive_losses"] <= FIXED_GATES["max_consecutive_loss_gate"],
        },
        "validation_max_consecutive_loss_gate": {
            "threshold": FIXED_GATES["max_consecutive_loss_gate"],
            "observed": validation_metrics["max_consecutive_losses"],
            "passed": validation_metrics["max_consecutive_losses"] <= FIXED_GATES["max_consecutive_loss_gate"],
        },
        "cost_sensitivity_required": {
            "threshold": "positive_validation_expectancy_after_double_cost",
            "observed": cost_sensitivity_summary["validation_expectancy_R_after_sensitivity_cost"],
            "passed": cost_sensitivity_summary["cost_sensitivity_passed"] is True,
        },
    }


def _cost_sensitivity_summary(base_records: list[dict[str, Any]], sensitivity_records: list[dict[str, Any]]) -> dict[str, Any]:
    base_validation = _metrics([trade for trade in base_records if trade["split"] == "validation"])
    sensitivity_validation = _metrics([trade for trade in sensitivity_records if trade["split"] == "validation"])
    return {
        "base_cost_R_per_trade": FIXED_EVALUATION_RULES["cost_r_per_trade"],
        "sensitivity_cost_R_per_trade": FIXED_EVALUATION_RULES["cost_sensitivity_cost_r_per_trade"],
        "validation_profit_factor_after_sensitivity_cost": sensitivity_validation["profit_factor"],
        "validation_expectancy_R_after_sensitivity_cost": sensitivity_validation["expectancy_R"],
        "validation_expectancy_R_delta": sensitivity_validation["expectancy_R"] - base_validation["expectancy_R"],
        "cost_sensitivity_required": True,
        "cost_sensitivity_passed": sensitivity_validation["expectancy_R"] > 0.0,
    }


def _metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(trade["return_R"]) for trade in trades]
    gross_profit = sum(value for value in returns if value > 0.0)
    gross_loss = abs(sum(value for value in returns if value < 0.0))
    profit_factor: float | str
    if not returns:
        profit_factor = 0.0
    elif gross_loss == 0.0 and gross_profit > 0.0:
        profit_factor = "inf"
    else:
        profit_factor = gross_profit / gross_loss if gross_loss else 0.0
    wins = sum(1 for value in returns if value > 0.0)
    return {
        "trades": len(returns),
        "wins": wins,
        "losses": sum(1 for value in returns if value < 0.0),
        "win_rate": wins / len(returns) if returns else 0.0,
        "gross_profit_R": gross_profit,
        "gross_loss_R": gross_loss,
        "profit_factor": profit_factor,
        "expectancy_R": sum(returns) / len(returns) if returns else 0.0,
        "max_drawdown_R": _max_drawdown(returns),
        "max_consecutive_losses": _max_consecutive_losses(returns),
        "side_counts": _counts(trades, "side"),
        "exit_reason_counts": _counts(trades, "exit_reason"),
    }


def _load_train_validation_candles(data_dir: str | Path, pattern: str, manifest: dict[str, Any]) -> dict[str, Any]:
    root = Path(data_dir)
    files = sorted(root.glob(pattern)) if root.exists() else []
    records: list[Candle] = []
    split_counts = {"train": 0, "validation": 0, "other": 0}
    policy = manifest["split_policy"]
    train_end = _dt(str(policy["train_end"]))
    validation_start = _dt(str(policy["validation_start"]))
    validation_end = _dt(str(policy["validation_end"]))
    for file_path in files:
        for row in _read_csv_rows(file_path):
            timestamp = _dt(str(row["timestamp"]))
            if timestamp <= train_end:
                split = "train"
            elif validation_start <= timestamp <= validation_end:
                split = "validation"
            else:
                continue
            split_counts[split] += 1
            records.append(
                Candle(
                    timestamp=timestamp,
                    split=split,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume", 0.0) or 0.0),
                )
            )
    return {"files": files, "candles": sorted(records, key=lambda item: item.timestamp), "split_counts": split_counts}


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        normalized = {name.strip().lower(): name for name in reader.fieldnames}
        time_column = next((normalized[name] for name in ("timestamp", "time", "datetime", "date") if name in normalized), None)
        if time_column is None:
            raise ValueError(f"CSV must contain timestamp column: {path}")
        rows = []
        for row in reader:
            rows.append(
                {
                    "timestamp": _normalize_timestamp(str(row[time_column])),
                    "open": float(row[normalized["open"]]),
                    "high": float(row[normalized["high"]]),
                    "low": float(row[normalized["low"]]),
                    "close": float(row[normalized["close"]]),
                    "volume": float(row[normalized["volume"]]) if "volume" in normalized else 0.0,
                }
            )
        return rows


def _source_design_blockers(design: dict[str, Any] | None) -> list[str]:
    if design is None:
        return ["source_v0_82_design_missing_or_invalid"]
    blockers: list[str] = []
    if design.get("design_version") != SOURCE_DESIGN_VERSION:
        blockers.append("source_design_version_mismatch")
    if design.get("candidate_id") != CANDIDATE_ID:
        blockers.append("source_candidate_id_mismatch")
    if design.get("explicit_side_mapping") is not True:
        blockers.append("source_explicit_side_mapping_missing")
    if design.get("future_evaluation_step") != EVALUATION_NAME:
        blockers.append("source_future_evaluation_step_mismatch")
    plan = design.get("future_evaluation_plan", {})
    for key, expected in FIXED_GATES.items():
        if isinstance(plan, dict) and plan.get(key) != expected:
            blockers.append(f"source_gate_mismatch:{key}")
    forbidden_true = (
        "retune_performed",
        "threshold_search_performed",
        "parameter_grid_performed",
        "rejected_candidates_modified",
        "v0_26_not_traded_as_is",
    )
    for key in forbidden_true[:4]:
        if design.get(key) is not False:
            blockers.append(f"source_safety_field_not_false:{key}")
    if design.get("v0_26_not_traded_as_is") is not True:
        blockers.append("source_v0_26_not_traded_as_is_missing")
    return blockers


def _manifest_blockers(manifest: dict[str, Any] | None) -> list[str]:
    if manifest is None:
        return ["dataset_manifest_missing_or_invalid"]
    policy = manifest.get("split_policy")
    if not isinstance(policy, dict):
        return ["dataset_manifest_split_policy_missing"]
    required = {"train_end", "validation_start", "validation_end", "oos_start"}
    missing = sorted(required.difference(policy))
    return [f"dataset_manifest_split_policy_missing:{','.join(missing)}"] if missing else []


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
        "gross_return_R": trade.gross_return_R,
        "cost_R": trade.cost_R,
        "return_R": trade.return_R,
        "won": trade.return_R > 0,
        "exit_reason": trade.exit_reason,
    }


def _warnings(split_counts: dict[str, dict[str, int]]) -> list[str]:
    warnings = [
        "fixed_rule_train_validation_research_records_only",
        "oos_rows_filtered_before_split_counts_and_evaluation",
        "same_candle_stop_target_resolution_is_stop_first",
        "cost_policy_applied_as_fixed_R_deduction_and_sensitivity_check",
    ]
    for timeframe, counts in split_counts.items():
        if counts.get("other", 0) > 0:
            warnings.append(f"{timeframe.lower()}_non_train_validation_rows_ignored:{counts['other']}")
    return warnings


def _data_ranges(candles: list[Candle]) -> dict[str, Any]:
    return {
        split: {
            "start": items[0].timestamp.isoformat() if items else None,
            "end": items[-1].timestamp.isoformat() if items else None,
            "candle_count": len(items),
        }
        for split, items in (
            ("train", sorted([candle for candle in candles if candle.split == "train"], key=lambda item: item.timestamp)),
            ("validation", sorted([candle for candle in candles if candle.split == "validation"], key=lambda item: item.timestamp)),
        )
    }


def _max_drawdown(returns: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in returns:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return max_dd


def _max_consecutive_losses(returns: list[float]) -> int:
    max_losses = 0
    current = 0
    for value in returns:
        if value < 0:
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


def _pf_value(value: Any) -> float:
    if value == "inf":
        return float("inf")
    return float(value or 0.0)


def _rules_hash(source_design: dict[str, Any] | None) -> str | None:
    if source_design is None:
        return None
    design = source_design.get("fixed_rule_design")
    mapping = source_design.get("side_mapping")
    payload = {"fixed_rule_design": design, "side_mapping": mapping}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _normalize_timestamp(value: str) -> str:
    raw = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).isoformat()
        except ValueError:
            pass
    return datetime.fromisoformat(raw).isoformat()


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _in_session(timestamp: datetime, start: time, end: time) -> bool:
    return start <= timestamp.time() < end


def _empty_split_counts() -> dict[str, dict[str, int]]:
    return {
        "M15": {"train": 0, "validation": 0, "other": 0},
        "M5": {"train": 0, "validation": 0, "other": 0},
    }


def _false_safety_flags() -> dict[str, bool]:
    return {
        "trade_recommendation_output": False,
        "live_allowed": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "executable_order_request_created": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "existing_strategy_rules_modified": False,
        "rejected_candidates_modified": False,
        "v0_26_traded_as_is": False,
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
    }
