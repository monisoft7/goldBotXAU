"""v0_48 train/validation-only new directional strategy discovery board."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.data.xauusd_low_tf_dataset_catalog import (
    DEFAULT_MANIFEST_PATH,
    build_low_tf_dataset_catalog,
    load_profiler_rows_from_catalog,
)
from src.research import xauusd_session_structure_atlas as atlas

BOARD_VERSION = "v0_48"
PRIOR_PATH_CLOSED = "xauusd_compression_then_expansion_v0_26"
PRIOR_PATH_CLOSURE_REASON = "no_executable_direction_rule_and_v0_47_direction_board_failed"
DEFAULT_OUTPUT = Path("reports") / "xauusd_new_directional_discovery_v0_48.json"

NO_CANDIDATE_PASSED = "no_new_directional_candidate_passed"
ONE_CANDIDATE_PASSED = "new_directional_candidate_passed_train_validation"
BLOCKED_MISSING_DATA = "blocked_missing_required_data"
BOARD_FAILED = "board_failed"

GATE = {
    "train_profit_factor_min": 1.20,
    "validation_profit_factor_min": 1.15,
    "validation_trades_min": 25,
    "train_expectancy_min_exclusive": 0.0,
    "validation_expectancy_min_exclusive": 0.0,
    "oos_used": False,
}

FAMILIES = (
    {
        "candidate_id": "session_open_range_breakout_directional",
        "description": "Internal long when block_06_12 closes above the fixed block_00_06 range; internal short when it closes below that range.",
    },
    {
        "candidate_id": "prior_block_breakout_continuation_directional",
        "description": "Internal long when a fixed current block closes above the prior block high; internal short when it closes below the prior block low.",
    },
    {
        "candidate_id": "failed_breakout_reversal_directional",
        "description": "Internal short after an upside breakout closes back inside the prior block range; internal long after a downside breakout closes back inside.",
    },
    {
        "candidate_id": "trend_pullback_continuation_directional",
        "description": "Internal long when a fixed uptrend/pullback sequence resolves upward; internal short when a fixed downtrend/pullback sequence resolves downward.",
    },
)


@dataclass(frozen=True)
class DayProfile:
    source_timeframe: str
    split: str
    date: str
    blocks: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class DirectionSignal:
    source_timeframe: str
    split: str
    date: str
    side: str
    reference_window: str
    signal_window: str
    evaluation_window: str
    reference_range: float
    evaluation_open: float
    evaluation_close: float


FamilyRule = Callable[[DayProfile], list[DirectionSignal]]


def build_xauusd_new_directional_strategy_discovery_board_v0_48(
    *,
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    pattern: str = "xauusd_m*.csv",
) -> dict[str, Any]:
    """Evaluate a fixed, non-OOS board of new directional strategy families."""
    try:
        catalog = build_low_tf_dataset_catalog(data_dir=data_dir, manifest_path=manifest_path, pattern=pattern)
        rows = [
            row
            for row in load_profiler_rows_from_catalog(catalog)
            if row.get("source_timeframe") in atlas.LOW_TF_ALLOWED and row.get("split") in {"train", "validation"}
        ]
        profiles = _day_profiles(rows)
        blockers: list[str] = []
        if not rows:
            blockers.append("train_validation_m5_m10_rows_missing")
        if not profiles:
            blockers.append("train_validation_session_profiles_missing")
        if blockers:
            return _blocked_report(blockers, catalog)

        candidate_results = [_evaluate_family(family["candidate_id"], profiles) for family in FAMILIES]
        passed = [result for result in candidate_results if result["passed_gate"] is True]
        best = max(candidate_results, key=_candidate_sort_key)

        if passed:
            status = ONE_CANDIDATE_PASSED
            next_step = "lock the new candidate artifact, then prepare one-time OOS protocol"
        else:
            status = NO_CANDIDATE_PASSED
            next_step = "stop current research branch or create a broader non-OOS research plan"

        return _base_report(
            board_status=status,
            catalog=catalog,
            candidate_results=candidate_results,
            best_candidate=best,
            blockers=[],
            warnings=_warnings(candidate_results),
            next_recommended_step=next_step,
        )
    except Exception as exc:
        return _base_report(
            board_status=BOARD_FAILED,
            catalog=None,
            candidate_results=[],
            best_candidate=None,
            blockers=[f"board_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair board implementation or input artifacts before rerunning v0_48",
        )


def save_xauusd_new_directional_strategy_discovery_board(
    report: dict[str, Any],
    output: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _blocked_report(blockers: list[str], catalog: dict[str, Any] | None) -> dict[str, Any]:
    return _base_report(
        board_status=BLOCKED_MISSING_DATA,
        catalog=catalog,
        candidate_results=[],
        best_candidate=None,
        blockers=blockers,
        warnings=[],
        next_recommended_step="repair required train/validation data artifacts before v0_48 evaluation",
    )


def _day_profiles(rows: list[dict[str, Any]]) -> list[DayProfile]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        timestamp = str(row["timestamp"])
        day = timestamp.split("T", 1)[0]
        key = (str(row["source_timeframe"]), str(row["split"]), day)
        grouped.setdefault(key, []).append(row)

    profiles: list[DayProfile] = []
    for source_timeframe, split, day in sorted(grouped):
        day_rows = sorted(grouped[(source_timeframe, split, day)], key=lambda row: str(row["timestamp"]))
        blocks = {
            name: atlas._window_metrics(
                [
                    row
                    for row in day_rows
                    if int(str(row["timestamp"]).split("T", 1)[1].split(":", 1)[0]) in hours
                ]
            )
            for name, hours in atlas.SESSION_BLOCKS.items()
        }
        if any(block["row_count"] > 0 for block in blocks.values()):
            profiles.append(DayProfile(source_timeframe=source_timeframe, split=split, date=day, blocks=blocks))
    return profiles


def _evaluate_family(candidate_id: str, profiles: list[DayProfile]) -> dict[str, Any]:
    rule = _family_rules()[candidate_id]
    signals: list[DirectionSignal] = []
    skipped_profiles = 0
    for profile in profiles:
        profile_signals = rule(profile)
        if not profile_signals:
            skipped_profiles += 1
        signals.extend(profile_signals)

    trades = [_trade_result(signal) for signal in signals]
    train_metrics = _split_metrics([trade for trade in trades if trade["split"] == "train"])
    validation_metrics = _split_metrics([trade for trade in trades if trade["split"] == "validation"])
    gate_failures = _gate_failures(train_metrics, validation_metrics)
    family = next(item for item in FAMILIES if item["candidate_id"] == candidate_id)
    passed = not gate_failures
    return {
        "candidate_id": candidate_id,
        "family_name": candidate_id,
        "family_description": family["description"],
        "fixed_before_evaluation": True,
        "prior_path_closed": PRIOR_PATH_CLOSED,
        "candidate_disposition": "requires_locked_artifact_before_oos" if passed else "rejected_do_not_retune",
        "do_not_retune": not passed,
        "metric_horizon": "next_fixed_six_hour_block_after_signal_close",
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "combined_trade_count": len(trades),
        "skipped_profile_count": skipped_profiles,
        "passed_gate": passed,
        "gate_failures": gate_failures,
        "safety": _safety_flags(),
    }


def _family_rules() -> dict[str, FamilyRule]:
    return {
        "session_open_range_breakout_directional": _session_open_range_breakout_signals,
        "prior_block_breakout_continuation_directional": _prior_block_breakout_signals,
        "failed_breakout_reversal_directional": _failed_breakout_reversal_signals,
        "trend_pullback_continuation_directional": _trend_pullback_continuation_signals,
    }


def _session_open_range_breakout_signals(profile: DayProfile) -> list[DirectionSignal]:
    reference = profile.blocks["block_00_06"]
    signal = profile.blocks["block_06_12"]
    evaluation = profile.blocks["block_12_18"]
    if not _usable_triplet(reference, signal, evaluation):
        return []
    close = float(signal["close"])
    if close > float(reference["high"]):
        side = "long"
    elif close < float(reference["low"]):
        side = "short"
    else:
        return []
    return [_signal(profile, side, "block_00_06", "block_06_12", "block_12_18")]


def _prior_block_breakout_signals(profile: DayProfile) -> list[DirectionSignal]:
    names = list(atlas.SESSION_BLOCKS)
    signals: list[DirectionSignal] = []
    for index in range(len(names) - 2):
        prior_name, current_name, evaluation_name = names[index], names[index + 1], names[index + 2]
        prior = profile.blocks[prior_name]
        current = profile.blocks[current_name]
        evaluation = profile.blocks[evaluation_name]
        if not _usable_triplet(prior, current, evaluation):
            continue
        close = float(current["close"])
        if close > float(prior["high"]):
            signals.append(_signal(profile, "long", prior_name, current_name, evaluation_name))
        elif close < float(prior["low"]):
            signals.append(_signal(profile, "short", prior_name, current_name, evaluation_name))
    return signals


def _failed_breakout_reversal_signals(profile: DayProfile) -> list[DirectionSignal]:
    names = list(atlas.SESSION_BLOCKS)
    signals: list[DirectionSignal] = []
    for index in range(len(names) - 2):
        prior_name, current_name, evaluation_name = names[index], names[index + 1], names[index + 2]
        prior = profile.blocks[prior_name]
        current = profile.blocks[current_name]
        evaluation = profile.blocks[evaluation_name]
        if not _usable_triplet(prior, current, evaluation):
            continue
        prior_high = float(prior["high"])
        prior_low = float(prior["low"])
        close = float(current["close"])
        broke_up_failed = float(current["high"]) > prior_high and prior_low <= close <= prior_high
        broke_down_failed = float(current["low"]) < prior_low and prior_low <= close <= prior_high
        if broke_up_failed:
            signals.append(_signal(profile, "short", prior_name, current_name, evaluation_name))
        elif broke_down_failed:
            signals.append(_signal(profile, "long", prior_name, current_name, evaluation_name))
    return signals


def _trend_pullback_continuation_signals(profile: DayProfile) -> list[DirectionSignal]:
    trend = profile.blocks["block_00_06"]
    pullback = profile.blocks["block_06_12"]
    resolution = profile.blocks["block_12_18"]
    evaluation = profile.blocks["block_18_24"]
    if not _usable_triplet(trend, pullback, resolution) or evaluation["row_count"] <= 0:
        return []
    trend_direction = int(trend["direction"])
    pullback_direction = int(pullback["direction"])
    if trend_direction == 0 or pullback_direction != -trend_direction:
        return []
    close = float(resolution["close"])
    if trend_direction > 0 and close > float(pullback["high"]):
        return [_signal(profile, "long", "block_06_12", "block_12_18", "block_18_24")]
    if trend_direction < 0 and close < float(pullback["low"]):
        return [_signal(profile, "short", "block_06_12", "block_12_18", "block_18_24")]
    return []


def _signal(
    profile: DayProfile,
    side: str,
    reference_window: str,
    signal_window: str,
    evaluation_window: str,
) -> DirectionSignal:
    reference = profile.blocks[reference_window]
    evaluation = profile.blocks[evaluation_window]
    return DirectionSignal(
        source_timeframe=profile.source_timeframe,
        split=profile.split,
        date=profile.date,
        side=side,
        reference_window=reference_window,
        signal_window=signal_window,
        evaluation_window=evaluation_window,
        reference_range=max(float(reference["range"]), 0.0000001),
        evaluation_open=float(evaluation["open"]),
        evaluation_close=float(evaluation["close"]),
    )


def _trade_result(signal: DirectionSignal) -> dict[str, Any]:
    direction = 1.0 if signal.side == "long" else -1.0
    return_r = direction * (signal.evaluation_close - signal.evaluation_open) / signal.reference_range
    return {
        "source_timeframe": signal.source_timeframe,
        "split": signal.split,
        "date": signal.date,
        "side": signal.side,
        "reference_window": signal.reference_window,
        "signal_window": signal.signal_window,
        "evaluation_window": signal.evaluation_window,
        "return_r": return_r,
        "won": return_r > 0,
    }


def _split_metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(trade["return_r"]) for trade in trades]
    gross_profit = sum(value for value in returns if value > 0)
    gross_loss = abs(sum(value for value in returns if value < 0))
    if not returns:
        profit_factor: float | str = 0.0
    elif gross_loss == 0 and gross_profit > 0:
        profit_factor = "inf"
    else:
        profit_factor = gross_profit / gross_loss if gross_loss else 0.0
    return {
        "trades": len(returns),
        "wins": sum(1 for value in returns if value > 0),
        "losses": sum(1 for value in returns if value < 0),
        "win_rate": _rate(sum(1 for value in returns if value > 0), len(returns)),
        "gross_profit_r": gross_profit,
        "gross_loss_r": gross_loss,
        "profit_factor": profit_factor,
        "expectancy_r": sum(returns) / len(returns) if returns else 0.0,
        "max_consecutive_losses": _max_consecutive_losses(returns),
        "timeframe_counts": _counts(trades, "source_timeframe"),
    }


def _gate_failures(train: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if _pf_value(train["profit_factor"]) < GATE["train_profit_factor_min"]:
        failures.append("train_profit_factor_below_fixed_gate")
    if _pf_value(validation["profit_factor"]) < GATE["validation_profit_factor_min"]:
        failures.append("validation_profit_factor_below_fixed_gate")
    if int(validation["trades"]) < GATE["validation_trades_min"]:
        failures.append("validation_trades_below_fixed_gate")
    if float(train["expectancy_r"]) <= GATE["train_expectancy_min_exclusive"]:
        failures.append("train_expectancy_not_positive")
    if float(validation["expectancy_r"]) <= GATE["validation_expectancy_min_exclusive"]:
        failures.append("validation_expectancy_not_positive")
    return failures


def _base_report(
    *,
    board_status: str,
    catalog: dict[str, Any] | None,
    candidate_results: list[dict[str, Any]],
    best_candidate: dict[str, Any] | None,
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    return {
        "board_version": BOARD_VERSION,
        "board_status": board_status,
        "prior_path_closed": PRIOR_PATH_CLOSED,
        "prior_path_closure_reason": PRIOR_PATH_CLOSURE_REASON,
        "prior_path_executable_status": "closed_as_execution_path",
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "directional_families_evaluated": [family["candidate_id"] for family in FAMILIES],
        "fixed_gate": dict(GATE),
        "candidate_results": candidate_results,
        "best_candidate_id": best_candidate.get("candidate_id") if best_candidate else None,
        "best_candidate_metrics": best_candidate_metrics(best_candidate),
        "best_candidate_passed_gate": best_candidate.get("passed_gate") if best_candidate else False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "data_csv_added": False,
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "data_files_used": _data_files_used(catalog) if catalog else [],
        "safety": _safety_flags(),
    }


def best_candidate_metrics(best_candidate: dict[str, Any] | None) -> dict[str, Any] | None:
    if best_candidate is None:
        return None
    return {
        "train": best_candidate["train_metrics"],
        "validation": best_candidate["validation_metrics"],
    }


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


def _warnings(candidate_results: list[dict[str, Any]]) -> list[str]:
    warnings = [
        "research_only_new_directional_board_not_demo_execution",
        "v0_26_path_closed_as_execution_path_preserved_as_historical_evidence",
        "combined_m5_m10_counts_are_not_treated_as_independent_oos_evidence",
    ]
    if sum(1 for result in candidate_results if result["passed_gate"] is True) > 1:
        warnings.append("multiple_new_directional_families_passed_fixed_train_validation_gate")
    return warnings


def _safety_flags() -> dict[str, Any]:
    return {
        "research_only": True,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "oos_used": False,
        "repeated_oos_review": False,
        "trade_recommendation_output_present": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
    }


def _data_files_used(catalog: dict[str, Any]) -> list[str]:
    return sorted(
        str(entry["filename"])
        for entry in catalog.get("entries", [])
        if entry.get("usable_for_profiler") is True and entry.get("source_timeframe") in atlas.LOW_TF_ALLOWED
    )


def _usable_triplet(first: dict[str, Any], second: dict[str, Any], third: dict[str, Any]) -> bool:
    return first["row_count"] > 0 and second["row_count"] > 0 and third["row_count"] > 0 and float(first["range"]) > 0


def _pf_value(value: Any) -> float:
    if value == "inf":
        return float("inf")
    return float(value or 0.0)


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


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0
