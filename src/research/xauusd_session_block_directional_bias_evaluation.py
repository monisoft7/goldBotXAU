"""v0_56 fixed-rule train/validation evaluation for the session block candidate.

This module evaluates exactly one v0_55 design on existing local M15 data. It
does not run OOS, tune parameters, create an executable candidate, or touch any
broker/execution API.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_m15_csvs

EVALUATION_VERSION = "v0_56"
SOURCE_DESIGN_VERSION = "v0_55"
SOURCE_PROFILER_VERSION = "v0_54"
CANDIDATE_ID = "session_block_directional_bias_candidate"
SESSION_BLOCK_ID = "asian_00_06"
SESSION_START = time(0, 0)
SESSION_END = time(7, 0)
SESSION_EXPECTED_M15_CANDLES = 28

DEFAULT_OUTPUT = Path("reports") / "xauusd_session_block_bias_eval_v0_56.json"
DEFAULT_SOURCE_DESIGN = Path("reports") / "xauusd_session_volatility_design_v0_55.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"

PASSED = "session_block_candidate_passed_train_validation"
REJECTED = "session_block_candidate_rejected"
BLOCKED_MISSING_DESIGN = "blocked_missing_v0_55_design"
BLOCKED_MISSING_DATA = "blocked_missing_required_data"
EVALUATION_FAILED = "evaluation_failed"

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


def build_xauusd_session_block_directional_bias_evaluation_v0_56(
    *,
    data_dir: str | Path = "data",
    pattern: str = "xauusd_m15_*.csv",
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_design_path: str | Path = DEFAULT_SOURCE_DESIGN,
) -> dict[str, Any]:
    """Evaluate the fixed v0_55 session block design on train/validation only."""
    try:
        source_design = _read_json(Path(source_design_path))
        selected_design = _selected_design(source_design)
        source_blockers = _source_design_blockers(source_design, selected_design)
        manifest = _read_json(Path(manifest_path))
        manifest_blockers = _manifest_blockers(manifest)
        if source_blockers:
            return _base_report(
                evaluation_status=BLOCKED_MISSING_DESIGN,
                source_design=source_design,
                selected_design=selected_design,
                data_files_used=[],
                split_candle_counts=_empty_counts(),
                data_ranges_used={},
                train_metrics={},
                validation_metrics={},
                metrics_by_session_block={},
                metrics_by_volatility_regime_if_available={},
                trades=[],
                gate_failures=source_blockers,
                blockers=source_blockers,
                warnings=[],
                next_recommended_step="restore v0_55 design report before rerunning v0_56",
            )
        if manifest_blockers:
            return _base_report(
                evaluation_status=BLOCKED_MISSING_DATA,
                source_design=source_design,
                selected_design=selected_design,
                data_files_used=[],
                split_candle_counts=_empty_counts(),
                data_ranges_used={},
                train_metrics={},
                validation_metrics={},
                metrics_by_session_block={},
                metrics_by_volatility_regime_if_available={},
                trades=[],
                gate_failures=manifest_blockers,
                blockers=manifest_blockers,
                warnings=[],
                next_recommended_step="restore dataset manifest and train/validation M15 data before rerunning v0_56",
            )

        assert manifest is not None
        assert selected_design is not None
        load_result = load_xauusd_m15_csvs(data_dir=data_dir, pattern=pattern)
        candles, split_counts = _split_candles(load_result.records, manifest)
        evaluation_candles = [candle for candle in candles if candle.split in {"train", "validation"}]
        data_blockers: list[str] = []
        if not load_result.files:
            data_blockers.append("m15_data_files_missing")
        if split_counts["train"] <= 0:
            data_blockers.append("train_m15_rows_missing")
        if split_counts["validation"] <= 0:
            data_blockers.append("validation_m15_rows_missing")
        if not evaluation_candles:
            data_blockers.append("train_validation_m15_rows_missing")
        if data_blockers:
            return _base_report(
                evaluation_status=BLOCKED_MISSING_DATA,
                source_design=source_design,
                selected_design=selected_design,
                data_files_used=[path.as_posix() for path in load_result.files],
                split_candle_counts=split_counts,
                data_ranges_used=_data_ranges(candles),
                train_metrics={},
                validation_metrics={},
                metrics_by_session_block={},
                metrics_by_volatility_regime_if_available={},
                trades=[],
                gate_failures=data_blockers,
                blockers=data_blockers,
                warnings=[],
                next_recommended_step="restore train/validation M15 data before rerunning v0_56",
            )

        trades = _session_block_trades(evaluation_candles)
        train_trades = [trade for trade in trades if trade["split"] == "train"]
        validation_trades = [trade for trade in trades if trade["split"] == "validation"]
        train_metrics = _metrics(train_trades)
        validation_metrics = _metrics(validation_trades)
        gate_failures = _gate_failures(train_metrics, validation_metrics)
        passed = not gate_failures
        status = PASSED if passed else REJECTED
        next_step = (
            "v0_57 lock fixed candidate artifact and prepare one-time OOS protocol, no OOS yet."
            if passed
            else "stop session_block branch or return to profiler leads."
        )

        return _base_report(
            evaluation_status=status,
            source_design=source_design,
            selected_design=selected_design,
            data_files_used=[path.as_posix() for path in load_result.files],
            split_candle_counts=split_counts,
            data_ranges_used=_data_ranges(candles),
            train_metrics=train_metrics,
            validation_metrics=validation_metrics,
            metrics_by_session_block={
                SESSION_BLOCK_ID: {
                    "train": train_metrics,
                    "validation": validation_metrics,
                    "combined": _metrics(trades),
                }
            },
            metrics_by_volatility_regime_if_available={},
            trades=trades,
            gate_failures=gate_failures,
            blockers=gate_failures,
            warnings=_warnings(trades, split_counts),
            next_recommended_step=next_step,
        )
    except Exception as exc:
        return _base_report(
            evaluation_status=EVALUATION_FAILED,
            source_design=None,
            selected_design=None,
            data_files_used=[],
            split_candle_counts=_empty_counts(),
            data_ranges_used={},
            train_metrics={},
            validation_metrics={},
            metrics_by_session_block={},
            metrics_by_volatility_regime_if_available={},
            trades=[],
            gate_failures=[f"evaluation_exception:{type(exc).__name__}:{exc}"],
            blockers=[f"evaluation_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair v0_56 evaluator implementation or input artifacts before deciding",
        )


def save_xauusd_session_block_directional_bias_evaluation(
    report: dict[str, Any],
    output: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _session_block_trades(candles: list[Candle]) -> list[dict[str, Any]]:
    grouped = _candles_by_day(candles)
    days = sorted(grouped)
    trades: list[dict[str, Any]] = []
    for index, day in enumerate(days):
        current_block = _complete_session_block(grouped[day])
        if current_block is None:
            continue
        previous_block = _previous_complete_block(grouped, days, index)
        if previous_block is None:
            continue
        entry = current_block[0]
        stop_price = min(candle.low for candle in previous_block)
        if entry.open <= stop_price:
            continue
        exit_candle = current_block[-1]
        stop_candle = next((candle for candle in current_block if candle.low <= stop_price), None)
        if stop_candle is not None:
            realized_exit = stop_price
            exit_timestamp = stop_candle.timestamp
            exit_reason = "structural_stop_prior_completed_session_low"
        else:
            realized_exit = exit_candle.close
            exit_timestamp = exit_candle.timestamp
            exit_reason = "time_exit_final_m15_close_inside_fixed_session_block"
        risk_points = entry.open - stop_price
        return_r = (realized_exit - entry.open) / risk_points if risk_points > 0.0 else 0.0
        trades.append(
            {
                "candidate_id": CANDIDATE_ID,
                "split": entry.split,
                "session_block": SESSION_BLOCK_ID,
                "entry_timestamp": entry.timestamp.isoformat(),
                "exit_timestamp": exit_timestamp.isoformat(),
                "side": "long",
                "entry_price": entry.open,
                "exit_price": realized_exit,
                "stop_price": stop_price,
                "return_points": realized_exit - entry.open,
                "risk_points": risk_points,
                "return_r": return_r,
                "won": return_r > 0.0,
                "exit_reason": exit_reason,
                "year": entry.timestamp.strftime("%Y"),
                "month": entry.timestamp.strftime("%Y-%m"),
            }
        )
    return sorted(trades, key=lambda trade: str(trade["entry_timestamp"]))


def _base_report(
    *,
    evaluation_status: str,
    source_design: dict[str, Any] | None,
    selected_design: dict[str, Any] | None,
    data_files_used: list[str],
    split_candle_counts: dict[str, int],
    data_ranges_used: dict[str, Any],
    train_metrics: dict[str, Any],
    validation_metrics: dict[str, Any],
    metrics_by_session_block: dict[str, Any],
    metrics_by_volatility_regime_if_available: dict[str, Any],
    trades: list[dict[str, Any]],
    gate_failures: list[str],
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    passed = evaluation_status == PASSED
    rejected = evaluation_status == REJECTED
    return {
        "evaluation_version": EVALUATION_VERSION,
        "evaluation_status": evaluation_status,
        "source_design_version": SOURCE_DESIGN_VERSION,
        "source_profiler_version": SOURCE_PROFILER_VERSION,
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": _candidate_rules_preserved(source_design, selected_design),
        "selected_candidate_rules": selected_design or {},
        "selected_candidate_rules_sha256": _rules_hash(selected_design),
        "evaluated_candidate_count": 1 if selected_design is not None else 0,
        "other_v0_55_candidates_evaluated": False,
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
        "data_csv_added_to_git": False,
        "timeframe": "M15",
        "fixed_gate": dict(GATE),
        "data_files_used": data_files_used,
        "split_candle_counts": split_candle_counts,
        "data_ranges_used": data_ranges_used,
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "metrics_by_session_block": metrics_by_session_block,
        "metrics_by_volatility_regime_if_available": metrics_by_volatility_regime_if_available,
        "trade_distribution_by_year": _distribution_by_split(trades, "year"),
        "trade_distribution_by_month": _distribution_by_split(trades, "month"),
        "side_distribution": _distribution_by_split(trades, "side"),
        "sample_concentration_risk": _sample_concentration_risk(trades),
        "gate_failures": gate_failures,
        "candidate_passed_train_validation_gate": passed,
        "candidate_locking_allowed_pre_oos": passed,
        "rejected_do_not_retune": rejected,
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def _metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(trade["return_r"]) for trade in trades]
    point_returns = [float(trade["return_points"]) for trade in trades]
    gross_profit = sum(value for value in returns if value > 0.0)
    gross_loss = abs(sum(value for value in returns if value < 0.0))
    if not returns:
        profit_factor: float | str = 0.0
    elif gross_loss == 0.0 and gross_profit > 0.0:
        profit_factor = "inf"
    else:
        profit_factor = gross_profit / gross_loss if gross_loss else 0.0
    wins = sum(1 for value in returns if value > 0.0)
    losses = sum(1 for value in returns if value < 0.0)
    return {
        "trades": len(returns),
        "wins": wins,
        "losses": losses,
        "win_rate": _rate(wins, len(returns)),
        "gross_profit_r": gross_profit,
        "gross_loss_r": gross_loss,
        "profit_factor": profit_factor,
        "expectancy_r": sum(returns) / len(returns) if returns else 0.0,
        "mean_return_points": sum(point_returns) / len(point_returns) if point_returns else 0.0,
        "median_return_points": _median(point_returns),
        "max_consecutive_losses": _max_consecutive_losses(returns),
        "side_counts": _counts(trades, "side"),
        "exit_reason_counts": _counts(trades, "exit_reason"),
    }


def _gate_failures(train: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    train_pf = _pf_value(train.get("profit_factor"))
    validation_pf = _pf_value(validation.get("profit_factor"))
    if train_pf < GATE["train_profit_factor_min"]:
        failures.append("train_profit_factor_below_fixed_gate")
    if validation_pf < GATE["validation_profit_factor_min"]:
        failures.append("validation_profit_factor_below_fixed_gate")
    if int(validation.get("trades", 0)) < GATE["validation_trades_min"]:
        failures.append("validation_trades_below_fixed_gate")
    if float(train.get("expectancy_r", 0.0)) <= GATE["train_expectancy_min_exclusive"]:
        failures.append("train_expectancy_not_positive")
    if float(validation.get("expectancy_r", 0.0)) <= GATE["validation_expectancy_min_exclusive"]:
        failures.append("validation_expectancy_not_positive")
    if int(train.get("max_consecutive_losses", 0)) > GATE["max_consecutive_losses_max"]:
        failures.append("train_max_consecutive_losses_above_fixed_gate")
    if int(validation.get("max_consecutive_losses", 0)) > GATE["max_consecutive_losses_max"]:
        failures.append("validation_max_consecutive_losses_above_fixed_gate")
    if not _validation_pf_ratio_passes(train_pf, validation_pf):
        failures.append("validation_profit_factor_less_than_0_75_train_profit_factor")
    return failures


def _source_design_blockers(source_design: dict[str, Any] | None, selected_design: dict[str, Any] | None) -> list[str]:
    if source_design is None:
        return ["source_v0_55_design_missing_or_invalid"]
    blockers: list[str] = []
    if source_design.get("design_version") != SOURCE_DESIGN_VERSION:
        blockers.append("source_design_version_mismatch")
    if source_design.get("source_profiler_version") != SOURCE_PROFILER_VERSION:
        blockers.append("source_profiler_version_mismatch")
    if source_design.get("recommended_candidate_for_v0_56") != CANDIDATE_ID:
        blockers.append("source_design_recommended_candidate_mismatch")
    if source_design.get("train_validation_only") is not True:
        blockers.append("source_design_train_validation_only_not_true")
    if source_design.get("oos_used") is not False:
        blockers.append("source_design_oos_state_invalid")
    if selected_design is None:
        blockers.append("source_candidate_design_missing")
    elif not _design_matches_fixed_contract(selected_design):
        blockers.append("source_candidate_design_rules_do_not_match_v0_56_contract")
    return blockers


def _selected_design(source_design: dict[str, Any] | None) -> dict[str, Any] | None:
    if source_design is None:
        return None
    for design in source_design.get("candidate_designs", []):
        if isinstance(design, dict) and design.get("candidate_design_id") == CANDIDATE_ID:
            return design
    return None


def _design_matches_fixed_contract(design: dict[str, Any]) -> bool:
    return (
        design.get("candidate_design_id") == CANDIDATE_ID
        and "asian_00_06" in str(design.get("exact_entry_rule", ""))
        and "first M15 open" in str(design.get("exact_entry_rule", ""))
        and "Current v0_54 train value implies long" in str(design.get("exact_direction_rule", ""))
        and "final M15 close" in str(design.get("take_profit_or_exit_logic", ""))
        and "prior completed fixed session block range" in str(design.get("stop_loss_logic", ""))
        and str(design.get("volatility_filter")) == "None in this design; volatility filters are reserved for separate v0_55 designs."
    )


def _candidate_rules_preserved(source_design: dict[str, Any] | None, selected_design: dict[str, Any] | None) -> bool:
    return source_design is not None and selected_design is not None and not _source_design_blockers(source_design, selected_design)


def _manifest_blockers(manifest: dict[str, Any] | None) -> list[str]:
    if manifest is None:
        return ["dataset_manifest_missing_or_invalid"]
    policy = manifest.get("split_policy")
    if not isinstance(policy, dict):
        return ["dataset_manifest_split_policy_missing"]
    required = {"train_end", "validation_start", "validation_end", "oos_start"}
    missing = sorted(required.difference(policy))
    return [f"dataset_manifest_split_policy_missing:{','.join(missing)}"] if missing else []


def _split_candles(records: list[dict[str, float | str]], manifest: dict[str, Any]) -> tuple[list[Candle], dict[str, int]]:
    policy = manifest["split_policy"]
    train_end = _dt(str(policy["train_end"]))
    validation_start = _dt(str(policy["validation_start"]))
    validation_end = _dt(str(policy["validation_end"]))
    oos_start = _dt(str(policy["oos_start"]))
    counts = _empty_counts()
    candles: list[Candle] = []
    for record in records:
        timestamp = _dt(str(record["timestamp"]))
        if timestamp <= train_end:
            split = "train"
        elif validation_start <= timestamp <= validation_end:
            split = "validation"
        elif timestamp >= oos_start:
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


def _complete_session_block(candles: list[Candle]) -> list[Candle] | None:
    block = [candle for candle in candles if _in_window(candle.timestamp, SESSION_START, SESSION_END)]
    if len(block) != SESSION_EXPECTED_M15_CANDLES:
        return None
    if block[0].timestamp.time() != SESSION_START:
        return None
    return block


def _previous_complete_block(grouped: dict[str, list[Candle]], days: list[str], current_index: int) -> list[Candle] | None:
    for previous_index in range(current_index - 1, -1, -1):
        previous = _complete_session_block(grouped[days[previous_index]])
        if previous is not None:
            return previous
    return None


def _candles_by_day(candles: list[Candle]) -> dict[str, list[Candle]]:
    grouped: dict[str, list[Candle]] = {}
    for candle in candles:
        grouped.setdefault(candle.timestamp.date().isoformat(), []).append(candle)
    return {day: sorted(rows, key=lambda candle: candle.timestamp) for day, rows in sorted(grouped.items())}


def _data_ranges(candles: list[Candle]) -> dict[str, Any]:
    return {
        split: {
            "start": split_candles[0].timestamp.isoformat() if split_candles else None,
            "end": split_candles[-1].timestamp.isoformat() if split_candles else None,
            "candle_count": len(split_candles),
        }
        for split, split_candles in (
            ("train", [candle for candle in candles if candle.split == "train"]),
            ("validation", [candle for candle in candles if candle.split == "validation"]),
            ("excluded_oos", [candle for candle in candles if candle.split == "excluded_oos"]),
        )
    }


def _warnings(trades: list[dict[str, Any]], split_candle_counts: dict[str, int]) -> list[str]:
    warnings = [
        "fixed_rule_train_validation_research_only_not_oos",
        "oos_candles_on_disk_excluded_from_evaluation",
        "same_candle_stop_resolution_is_stop_first",
    ]
    if split_candle_counts.get("excluded_oos", 0) > 0:
        warnings.append(f"excluded_oos_candle_count:{split_candle_counts['excluded_oos']}")
    warnings.extend(_sample_concentration_risk(trades)["warnings"])
    return warnings


def _sample_concentration_risk(trades: list[dict[str, Any]]) -> dict[str, Any]:
    reasons: list[str] = []
    validation = [trade for trade in trades if trade["split"] == "validation"]
    if _max_share(validation, "month") > 0.35:
        reasons.append("validation_trades_concentrated_in_single_month")
    if _max_share(validation, "year") > 0.75:
        reasons.append("validation_trades_concentrated_in_single_year")
    if _max_share(trades, "side") > 0.95:
        reasons.append("trades_concentrated_in_single_side_by_fixed_design")
    return {
        "risk_level": "high" if reasons else "low",
        "risk_present": bool(reasons),
        "reasons": reasons,
        "validation_month_max_share": _max_share(validation, "month"),
        "validation_year_max_share": _max_share(validation, "year"),
        "side_max_share": _max_share(trades, "side"),
        "warnings": [f"sample_concentration_risk:{reason}" for reason in reasons],
    }


def _distribution_by_split(trades: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    return {
        split: _counts([trade for trade in trades if trade["split"] == split], key)
        for split in ("train", "validation")
    } | {"combined": _counts(trades, key)}


def _max_share(trades: list[dict[str, Any]], key: str) -> float:
    if not trades:
        return 0.0
    counts = _counts(trades, key)
    return max(counts.values()) / len(trades)


def _counts(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item[key])
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


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


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def _in_window(timestamp: datetime, start: time, end: time) -> bool:
    return start <= timestamp.time() < end


def _rules_hash(selected_design: dict[str, Any] | None) -> str | None:
    if selected_design is None:
        return None
    text = json.dumps(selected_design, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _empty_counts() -> dict[str, int]:
    return {"train": 0, "validation": 0, "excluded_oos": 0, "other": 0}


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
