"""v0_85 fresh executable candidate sprint on train/validation data only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Callable

from src.research import xauusd_executable_candidate_train_validation as v83
from src.research.xauusd_executable_candidate_train_validation import Candle, Trade

SPRINT_VERSION = "v0_85"
SPRINT_NAME = "v0_85_fresh_executable_candidate_sprint"
DEFAULT_OUTPUT = Path("reports") / "xauusd_fresh_executable_candidate_sprint_v0_85.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"
DEFAULT_V0_84_REPORT = Path("reports") / "xauusd_trading_decision_sprint_v0_84.json"

SOURCE_CLOSED_CANDIDATE_ID = "xauusd_ny_displacement_retest_executable_v0_82"
SOURCE_CLOSURE_VERSION = "v0_84"

PASSED = "fresh_executable_candidate_sprint_passed_candidate_ready_for_single_oos"
FAILED = "fresh_executable_candidate_sprint_failed_all_candidates"
BLOCKED = "fresh_executable_candidate_sprint_blocked"

NEXT_IF_PASSED = "v0_86_single_oos_review_for_selected_executable_candidate"
NEXT_IF_FAILED = "v0_86_strategy_family_review_or_stop"
NEXT_IF_BLOCKED = "v0_86_repair_evaluator_then_rerun_sprint"

MAX_CANDIDATE_COUNT_ALLOWED = 3

FIXED_GATES = dict(v83.FIXED_GATES)
BASE_COST_R = float(v83.FIXED_EVALUATION_RULES["cost_r_per_trade"])
SENSITIVITY_COST_R = float(v83.FIXED_EVALUATION_RULES["cost_sensitivity_cost_r_per_trade"])
TARGET_R = 1.5
TIME_STOP_M5_BARS = 24


@dataclass(frozen=True)
class CandidateDefinition:
    candidate_id: str
    family: str
    concept: str
    fixed_rules: dict[str, Any]
    explicit_side_mapping: dict[str, str]
    evaluator: Callable[[list[Candle], list[Candle], float], list[Trade]]


@dataclass(frozen=True)
class Setup:
    candidate_id: str
    split: str
    timestamp: datetime
    side: str
    entry_price: float
    stop_price: float
    target_price: float
    exit_path: list[Candle]
    exit_reason_suffix: str


def build_xauusd_fresh_executable_candidate_sprint_v0_85(
    *,
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_closure_path: str | Path = DEFAULT_V0_84_REPORT,
    m15_pattern: str = "xauusd_m15_*.csv",
    m5_pattern: str = "xauusd_m5_xauusd_2023-01-01_2025-12-31.csv",
) -> dict[str, Any]:
    """Evaluate exactly three fixed fresh candidate families on train/validation only."""
    candidates = _candidate_definitions()
    try:
        blockers = _source_closure_blockers(_read_json(Path(source_closure_path)))
        manifest = v83._read_json(Path(manifest_path))
        blockers.extend(v83._manifest_blockers(manifest))
        if blockers:
            return _report(
                sprint_status=BLOCKED,
                candidates=candidates,
                candidate_results={},
                data_files_used={"M15": [], "M5": []},
                split_candle_counts=v83._empty_split_counts(),
                data_ranges_used={},
                blockers=blockers,
            )

        assert manifest is not None
        m15_load = v83._load_train_validation_candles(data_dir, m15_pattern, manifest)
        m5_load = v83._load_train_validation_candles(data_dir, m5_pattern, manifest)
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
                sprint_status=BLOCKED,
                candidates=candidates,
                candidate_results={},
                data_files_used={
                    "M15": [path.as_posix() for path in m15_load["files"]],
                    "M5": [path.as_posix() for path in m5_load["files"]],
                },
                split_candle_counts=split_counts,
                data_ranges_used=v83._data_ranges([*m15_load["candles"], *m5_load["candles"]]),
                blockers=data_blockers,
            )

        candidate_results: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            base_trades = [
                v83._trade_record(trade)
                for trade in candidate.evaluator(m15_load["candles"], m5_load["candles"], BASE_COST_R)
            ]
            sensitivity_trades = [
                v83._trade_record(trade)
                for trade in candidate.evaluator(m15_load["candles"], m5_load["candles"], SENSITIVITY_COST_R)
            ]
            candidate_results[candidate.candidate_id] = _candidate_result(candidate, base_trades, sensitivity_trades)

        sprint_status = PASSED if any(result["passed_all_train_validation_gates"] for result in candidate_results.values()) else FAILED
        return _report(
            sprint_status=sprint_status,
            candidates=candidates,
            candidate_results=candidate_results,
            data_files_used={
                "M15": [path.as_posix() for path in m15_load["files"]],
                "M5": [path.as_posix() for path in m5_load["files"]],
            },
            split_candle_counts=split_counts,
            data_ranges_used=v83._data_ranges([*m15_load["candles"], *m5_load["candles"]]),
            blockers=[],
        )
    except Exception as exc:
        return _report(
            sprint_status=BLOCKED,
            candidates=candidates,
            candidate_results={},
            data_files_used={"M15": [], "M5": []},
            split_candle_counts=v83._empty_split_counts(),
            data_ranges_used={},
            blockers=[f"sprint_exception:{type(exc).__name__}:{exc}"],
        )


def write_xauusd_fresh_executable_candidate_sprint_v0_85(root: Path, output: str | Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    report = build_xauusd_fresh_executable_candidate_sprint_v0_85(
        data_dir=root / "data",
        manifest_path=root / DEFAULT_MANIFEST,
        source_closure_path=root / DEFAULT_V0_84_REPORT,
    )
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _candidate_definitions() -> list[CandidateDefinition]:
    return [
        CandidateDefinition(
            candidate_id="xauusd_ny_opening_range_breakout_executable_v0_85_a",
            family="ny_opening_range_breakout_continuation",
            concept="NY opening range breakout continuation.",
            fixed_rules={
                "timeframes": ["M15", "M5"],
                "ny_session_window_utc": "12:30-17:00",
                "opening_range_window_utc": "12:30-13:00",
                "breakout_confirmation_window_utc": "13:00-16:00",
                "breakout_confirmation": "M5 close outside fixed opening range with matching candle direction",
                "stop_invalidation": "opposite opening range boundary",
                "target_exit": "fixed_1_5R",
                "time_stop_m5_bars": TIME_STOP_M5_BARS,
                "cost_r_per_trade": BASE_COST_R,
                "cost_sensitivity_cost_r_per_trade": SENSITIVITY_COST_R,
                "one_position_at_a_time": True,
                "no_overlapping_trades": True,
                "numeric_threshold_search": False,
                "parameter_grid": False,
            },
            explicit_side_mapping={
                "long": "close_above_opening_range_high_continuation",
                "short": "close_below_opening_range_low_continuation",
            },
            evaluator=_evaluate_opening_range_breakout,
        ),
        CandidateDefinition(
            candidate_id="xauusd_london_to_ny_liquidity_sweep_reversal_executable_v0_85_b",
            family="london_to_ny_liquidity_sweep_reversal",
            concept="Prior London/session high-low sweep then reversal during NY.",
            fixed_rules={
                "timeframes": ["M15", "M5"],
                "prior_session_window_utc": "07:00-12:00",
                "ny_reversal_window_utc": "12:30-16:00",
                "sweep_condition": "M15 high above prior-session high or low below prior-session low",
                "rejection_close_back_condition": "M15 close back inside prior-session range",
                "stop_invalidation": "sweep extreme",
                "target_exit": "fixed_1_5R",
                "time_stop_m5_bars": TIME_STOP_M5_BARS,
                "cost_r_per_trade": BASE_COST_R,
                "cost_sensitivity_cost_r_per_trade": SENSITIVITY_COST_R,
                "one_position_at_a_time": True,
                "no_overlapping_trades": True,
                "numeric_threshold_search": False,
                "parameter_grid": False,
            },
            explicit_side_mapping={
                "long": "sell_side_sweep_reclaim_reversal",
                "short": "buy_side_sweep_reject_reversal",
            },
            evaluator=_evaluate_london_to_ny_sweep_reversal,
        ),
        CandidateDefinition(
            candidate_id="xauusd_impulse_pullback_continuation_executable_v0_85_c",
            family="impulse_pullback_continuation",
            concept="Directional impulse followed by controlled pullback continuation.",
            fixed_rules={
                "timeframes": ["M15", "M5"],
                "session_window_utc": "12:30-17:00",
                "impulse_condition": "three M15 closes in direction and move at least two prior-20-M15 average ranges",
                "pullback_condition": "next M5 pullback retraces 25%-60% of impulse without breaking origin",
                "continuation_trigger": "M5 close resumes through prior M5 high for long or prior M5 low for short",
                "stop_invalidation": "impulse origin or pullback extreme",
                "target_exit": "fixed_1_5R",
                "time_stop_m5_bars": TIME_STOP_M5_BARS,
                "cost_r_per_trade": BASE_COST_R,
                "cost_sensitivity_cost_r_per_trade": SENSITIVITY_COST_R,
                "one_position_at_a_time": True,
                "no_overlapping_trades": True,
                "numeric_threshold_search": False,
                "parameter_grid": False,
            },
            explicit_side_mapping={
                "long": "bullish_impulse_controlled_pullback_continuation",
                "short": "bearish_impulse_controlled_pullback_continuation",
            },
            evaluator=_evaluate_impulse_pullback_continuation,
        ),
    ]


def _evaluate_opening_range_breakout(m15: list[Candle], m5: list[Candle], cost_r_per_trade: float) -> list[Trade]:
    m15_by_day_split = _candles_by_day_split(m15)
    m5_by_day_split = _candles_by_day_split(m5)
    trades: list[Trade] = []
    open_until_by_split = {"train": datetime.min, "validation": datetime.min}
    for (session_day, split), day_m15 in sorted(m15_by_day_split.items()):
        opening = [c for c in day_m15 if _in_time(c.timestamp, time(12, 30), time(13, 0))]
        if len(opening) < 2:
            continue
        range_high = max(c.high for c in opening)
        range_low = min(c.low for c in opening)
        day_m5 = m5_by_day_split.get((session_day, split), [])
        for index, candle in enumerate(day_m5):
            if candle.timestamp < open_until_by_split[split] or not _in_time(candle.timestamp, time(13, 0), time(16, 0)):
                continue
            if candle.close > range_high and candle.close > candle.open:
                setup = _setup_from_prices(
                    "xauusd_ny_opening_range_breakout_executable_v0_85_a",
                    candle,
                    "long",
                    candle.close,
                    range_low,
                    "time_stop_24_m5_bars",
                    day_m5[index + 1 :],
                )
            elif candle.close < range_low and candle.close < candle.open:
                setup = _setup_from_prices(
                    "xauusd_ny_opening_range_breakout_executable_v0_85_a",
                    candle,
                    "short",
                    candle.close,
                    range_high,
                    "time_stop_24_m5_bars",
                    day_m5[index + 1 :],
                )
            else:
                setup = None
            trade = _trade_from_setup(setup, cost_r_per_trade) if setup else None
            if trade is None:
                continue
            trades.append(trade)
            open_until_by_split[split] = datetime.fromisoformat(trade.exit_timestamp)
            break
    return trades


def _evaluate_london_to_ny_sweep_reversal(m15: list[Candle], m5: list[Candle], cost_r_per_trade: float) -> list[Trade]:
    m15_by_day_split = _candles_by_day_split(m15)
    m5_by_day_split = _candles_by_day_split(m5)
    trades: list[Trade] = []
    open_until_by_split = {"train": datetime.min, "validation": datetime.min}
    for (session_day, split), day_m15 in sorted(m15_by_day_split.items()):
        prior_session = [c for c in day_m15 if _in_time(c.timestamp, time(7, 0), time(12, 0))]
        if not prior_session:
            continue
        prior_high = max(c.high for c in prior_session)
        prior_low = min(c.low for c in prior_session)
        day_m5 = m5_by_day_split.get((session_day, split), [])
        for candle in day_m15:
            if candle.timestamp < open_until_by_split[split] or not _in_time(candle.timestamp, time(12, 30), time(16, 0)):
                continue
            future_m5 = [item for item in day_m5 if item.timestamp > candle.timestamp]
            if candle.low < prior_low and candle.close > prior_low and candle.close > candle.open:
                setup = _setup_from_prices(
                    "xauusd_london_to_ny_liquidity_sweep_reversal_executable_v0_85_b",
                    candle,
                    "long",
                    candle.close,
                    candle.low,
                    "time_stop_24_m5_bars",
                    future_m5,
                )
            elif candle.high > prior_high and candle.close < prior_high and candle.close < candle.open:
                setup = _setup_from_prices(
                    "xauusd_london_to_ny_liquidity_sweep_reversal_executable_v0_85_b",
                    candle,
                    "short",
                    candle.close,
                    candle.high,
                    "time_stop_24_m5_bars",
                    future_m5,
                )
            else:
                setup = None
            trade = _trade_from_setup(setup, cost_r_per_trade) if setup else None
            if trade is None:
                continue
            trades.append(trade)
            open_until_by_split[split] = datetime.fromisoformat(trade.exit_timestamp)
            break
    return trades


def _evaluate_impulse_pullback_continuation(m15: list[Candle], m5: list[Candle], cost_r_per_trade: float) -> list[Trade]:
    m5_by_day_split = _candles_by_day_split(m5)
    trades: list[Trade] = []
    open_until_by_split = {"train": datetime.min, "validation": datetime.min}
    for index in range(22, len(m15)):
        impulse_window = m15[index - 2 : index + 1]
        candle = impulse_window[-1]
        if candle.split not in {"train", "validation"}:
            continue
        if candle.timestamp < open_until_by_split[candle.split] or not _in_time(candle.timestamp, time(12, 30), time(17, 0)):
            continue
        prior = [item for item in m15[index - 22 : index - 2] if item.split == candle.split]
        if len(prior) < 20:
            continue
        avg_range = sum(item.high - item.low for item in prior) / len(prior)
        if avg_range <= 0:
            continue
        first, second, third = impulse_window
        impulse_up = first.close < second.close < third.close and third.close - first.open >= 2.0 * avg_range
        impulse_down = first.close > second.close > third.close and first.open - third.close >= 2.0 * avg_range
        if not (impulse_up or impulse_down):
            continue
        side = "long" if impulse_up else "short"
        impulse_high = max(item.high for item in impulse_window)
        impulse_low = min(item.low for item in impulse_window)
        impulse_range = impulse_high - impulse_low
        if impulse_range <= 0:
            continue
        day_m5 = m5_by_day_split.get((candle.timestamp.date(), candle.split), [])
        future_m5 = [item for item in day_m5 if candle.timestamp < item.timestamp]
        setup = _impulse_pullback_setup(
            "xauusd_impulse_pullback_continuation_executable_v0_85_c",
            candle,
            side,
            impulse_high,
            impulse_low,
            impulse_range,
            future_m5,
        )
        trade = _trade_from_setup(setup, cost_r_per_trade) if setup else None
        if trade is None:
            continue
        trades.append(trade)
        open_until_by_split[candle.split] = datetime.fromisoformat(trade.exit_timestamp)
    return trades


def _impulse_pullback_setup(
    candidate_id: str,
    source_candle: Candle,
    side: str,
    impulse_high: float,
    impulse_low: float,
    impulse_range: float,
    future_m5: list[Candle],
) -> Setup | None:
    pullback_window = future_m5[:12]
    for index, candle in enumerate(pullback_window):
        if side == "long":
            retrace = (impulse_high - candle.low) / impulse_range
            controlled = 0.25 <= retrace <= 0.60 and candle.low > impulse_low
            trigger = candle.close > candle.open and (
                index == 0 or candle.close > max(item.high for item in pullback_window[:index])
            )
            stop_price = min(impulse_low, candle.low)
        else:
            retrace = (candle.high - impulse_low) / impulse_range
            controlled = 0.25 <= retrace <= 0.60 and candle.high < impulse_high
            trigger = candle.close < candle.open and (
                index == 0 or candle.close < min(item.low for item in pullback_window[:index])
            )
            stop_price = max(impulse_high, candle.high)
        if not controlled or not trigger:
            continue
        return _setup_from_prices(
            candidate_id,
            candle,
            side,
            candle.close,
            stop_price,
            "time_stop_24_m5_bars",
            future_m5[index + 1 :],
        )
    return None


def _setup_from_prices(
    candidate_id: str,
    candle: Candle,
    side: str,
    entry: float,
    stop_price: float,
    exit_reason_suffix: str,
    exit_path: list[Candle],
) -> Setup | None:
    risk = entry - stop_price if side == "long" else stop_price - entry
    if risk <= 0 or not exit_path:
        return None
    target = entry + TARGET_R * risk if side == "long" else entry - TARGET_R * risk
    return Setup(
        candidate_id=candidate_id,
        split=candle.split,
        timestamp=candle.timestamp,
        side=side,
        entry_price=entry,
        stop_price=stop_price,
        target_price=target,
        exit_path=exit_path[:TIME_STOP_M5_BARS],
        exit_reason_suffix=exit_reason_suffix,
    )


def _trade_from_setup(setup: Setup, cost_r_per_trade: float) -> Trade | None:
    if not setup.exit_path:
        return None
    for candle in setup.exit_path:
        if setup.side == "long":
            if candle.low <= setup.stop_price:
                return _trade(setup, candle, setup.stop_price, cost_r_per_trade, "stop")
            if candle.high >= setup.target_price:
                return _trade(setup, candle, setup.target_price, cost_r_per_trade, "target_1_5r")
        else:
            if candle.high >= setup.stop_price:
                return _trade(setup, candle, setup.stop_price, cost_r_per_trade, "stop")
            if candle.low <= setup.target_price:
                return _trade(setup, candle, setup.target_price, cost_r_per_trade, "target_1_5r")
    return _trade(setup, setup.exit_path[-1], setup.exit_path[-1].close, cost_r_per_trade, setup.exit_reason_suffix)


def _trade(setup: Setup, exit_candle: Candle, exit_price: float, cost_r: float, exit_reason: str) -> Trade:
    risk = setup.entry_price - setup.stop_price if setup.side == "long" else setup.stop_price - setup.entry_price
    direction = 1.0 if setup.side == "long" else -1.0
    gross = direction * (exit_price - setup.entry_price) / risk if risk > 0 else 0.0
    return Trade(
        candidate_id=setup.candidate_id,
        split=setup.split,
        entry_timestamp=setup.timestamp.isoformat(),
        exit_timestamp=exit_candle.timestamp.isoformat(),
        side=setup.side,
        entry_price=setup.entry_price,
        exit_price=exit_price,
        stop_price=setup.stop_price,
        target_price=setup.target_price,
        gross_return_R=gross,
        cost_R=cost_r,
        return_R=gross - cost_r,
        exit_reason=exit_reason,
    )


def _candidate_result(
    candidate: CandidateDefinition,
    trade_records: list[dict[str, Any]],
    sensitivity_records: list[dict[str, Any]],
) -> dict[str, Any]:
    train = v83._metrics([trade for trade in trade_records if trade["split"] == "train"])
    validation = v83._metrics([trade for trade in trade_records if trade["split"] == "validation"])
    sensitivity = v83._cost_sensitivity_summary(trade_records, sensitivity_records)
    gates = v83._gate_results(train, validation, sensitivity)
    failures = [name for name, result in gates.items() if result["passed"] is not True]
    passed = not failures
    return {
        "candidate_id": candidate.candidate_id,
        "candidate_family": candidate.family,
        "candidate_status": "passed_train_validation_gates" if passed else "failed_train_validation_gates",
        "concept": candidate.concept,
        "fixed_rules": dict(candidate.fixed_rules),
        "explicit_side_mapping": dict(candidate.explicit_side_mapping),
        "one_position_at_a_time_enforced": True,
        "no_overlapping_trades_enforced": True,
        "train_metrics": train,
        "validation_metrics": validation,
        "cost_sensitivity_summary": sensitivity,
        "gate_results": gates,
        "failure_reasons": failures,
        "passed_all_train_validation_gates": passed,
        "candidate_promotable_to_oos_review": passed,
        "trade_count": {"train": train["trades"], "validation": validation["trades"], "total": len(trade_records)},
        "trade_records_output_path_or_null": None,
        "trade_records_sample": trade_records[:3],
    }


def _report(
    *,
    sprint_status: str,
    candidates: list[CandidateDefinition],
    candidate_results: dict[str, dict[str, Any]],
    data_files_used: dict[str, list[str]],
    split_candle_counts: dict[str, dict[str, int]],
    data_ranges_used: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    passing = [candidate_id for candidate_id, result in candidate_results.items() if result.get("passed_all_train_validation_gates") is True]
    failing = [candidate_id for candidate_id in candidate_results if candidate_id not in passing]
    selected = _select_candidate(candidate_results) if passing else None
    blocked = sprint_status == BLOCKED
    selected_reason = _selected_reason(candidate_results[selected]) if selected else None
    recommended_next_step = NEXT_IF_BLOCKED if blocked else NEXT_IF_PASSED if selected else NEXT_IF_FAILED
    safety = _false_safety_flags()
    report = {
        "sprint_version": SPRINT_VERSION,
        "sprint_name": SPRINT_NAME,
        "sprint_status": sprint_status,
        "source_closed_candidate_id": SOURCE_CLOSED_CANDIDATE_ID,
        "source_closure_version": SOURCE_CLOSURE_VERSION,
        "candidates_evaluated": [candidate.candidate_id for candidate in candidates if candidate.candidate_id in candidate_results or not blocked],
        "candidate_count": len(candidate_results) if candidate_results else len(candidates),
        "max_candidate_count_allowed": MAX_CANDIDATE_COUNT_ALLOWED,
        "train_validation_only": True,
        "oos_used": False,
        "oos_allowed_now": False,
        "oos_rows_read": False,
        "oos_rows_counted": 0,
        "fixed_gate": dict(FIXED_GATES),
        "candidate_definitions": [_candidate_definition_record(candidate) for candidate in candidates],
        "candidate_results": candidate_results,
        "passing_candidates": passing,
        "failing_candidates": failing,
        "selected_candidate_id_or_null": selected,
        "selected_candidate_reason_or_null": selected_reason,
        "gate_results_by_candidate": {key: value["gate_results"] for key, value in candidate_results.items()},
        "train_metrics_by_candidate": {key: value["train_metrics"] for key, value in candidate_results.items()},
        "validation_metrics_by_candidate": {key: value["validation_metrics"] for key, value in candidate_results.items()},
        "cost_sensitivity_summary_by_candidate": {
            key: value["cost_sensitivity_summary"] for key, value in candidate_results.items()
        },
        "trade_count_by_candidate": {key: value["trade_count"] for key, value in candidate_results.items()},
        "failure_reasons_by_candidate": {key: value["failure_reasons"] for key, value in candidate_results.items()},
        "passed_all_train_validation_gates": selected is not None,
        "candidate_promotable_to_oos_review": selected is not None,
        "recommended_next_step": recommended_next_step,
        "rejected_next_steps": _rejected_next_steps(selected, blocked),
        "no_oos_reason_if_not_passed": None if selected else "no_candidate_passed_all_fixed_train_validation_gates",
        "no_demo_reason": "fresh_candidate_sprint_is_research_only_no_demo_execution_path",
        "no_live_reason": "fresh_candidate_sprint_is_research_only_no_live_execution_path",
        "data_files_used": data_files_used,
        "split_candle_counts": split_candle_counts,
        "data_ranges_used": data_ranges_used,
        "blockers": blockers,
        "warnings": [
            "fixed_rule_train_validation_research_records_only",
            "oos_rows_filtered_before_split_counts_and_evaluation",
            "same_candle_stop_target_resolution_is_stop_first",
            "cost_policy_applied_as_fixed_R_deduction_and_sensitivity_check",
            "closed_v0_82_not_rescued_or_retuned",
        ],
        "safety_flags": safety,
        **safety,
    }
    return report


def _select_candidate(candidate_results: dict[str, dict[str, Any]]) -> str | None:
    passing = [result for result in candidate_results.values() if result.get("passed_all_train_validation_gates") is True]
    if not passing:
        return None
    passing.sort(
        key=lambda result: (
            v83._pf_value(result["validation_metrics"]["profit_factor"]),
            -float(result["validation_metrics"]["max_drawdown_R"]),
            float(result["validation_metrics"]["expectancy_R"]),
        ),
        reverse=True,
    )
    return str(passing[0]["candidate_id"])


def _selected_reason(result: dict[str, Any]) -> str:
    metrics = result["validation_metrics"]
    return (
        "selected_by_fixed_tiebreak_higher_validation_pf_then_lower_validation_drawdown_then_higher_validation_expectancy_R:"
        f"pf={metrics['profit_factor']},max_drawdown_R={metrics['max_drawdown_R']},expectancy_R={metrics['expectancy_R']}"
    )


def _candidate_definition_record(candidate: CandidateDefinition) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "candidate_family": candidate.family,
        "concept": candidate.concept,
        "fixed_rules": dict(candidate.fixed_rules),
        "explicit_side_mapping": dict(candidate.explicit_side_mapping),
        "one_sided_by_design": False,
        "fully_fixed_before_evaluation": True,
    }


def _source_closure_blockers(report: dict[str, Any] | None) -> list[str]:
    if report is None:
        return ["source_v0_84_closure_report_missing_or_invalid"]
    blockers: list[str] = []
    if report.get("sprint_version") != SOURCE_CLOSURE_VERSION:
        blockers.append("source_closure_version_mismatch")
    if report.get("source_candidate_id") != SOURCE_CLOSED_CANDIDATE_ID:
        blockers.append("source_closed_candidate_id_mismatch")
    if report.get("sprint_status") != "trading_decision_sprint_failed_close_candidate":
        blockers.append("source_candidate_not_closed_by_v0_84")
    if report.get("candidate_closed") is not True:
        blockers.append("source_candidate_closed_flag_missing")
    return blockers


def _rejected_next_steps(selected: str | None, blocked: bool) -> list[str]:
    rejected = [
        "run_oos_in_v0_85",
        "rescue_v0_82_again",
        "retune_failed_candidates",
        "loosen_fixed_gates",
        "numeric_threshold_search",
        "parameter_grid",
        "validation_based_rule_change",
        "demo_live_or_order_path",
        "create_trade_recommendation_output",
        "touch_data_csv_or_create_market_dataset",
        "external_api_or_download",
    ]
    if blocked:
        rejected.append("promote_candidate_before_evaluator_repair")
    if selected is None:
        rejected.append("promote_failed_candidate_to_oos")
    return rejected


def _candles_by_day_split(candles: list[Candle]) -> dict[tuple[date, str], list[Candle]]:
    grouped: dict[tuple[date, str], list[Candle]] = {}
    for candle in candles:
        if candle.split not in {"train", "validation"}:
            continue
        grouped.setdefault((candle.timestamp.date(), candle.split), []).append(candle)
    return {key: sorted(value, key=lambda item: item.timestamp) for key, value in grouped.items()}


def _in_time(timestamp: datetime, start: time, end: time) -> bool:
    return start <= timestamp.time() < end


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _false_safety_flags() -> dict[str, bool]:
    return {
        "demo_execution_allowed": False,
        "live_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "executable_order_request_created": False,
        "trade_recommendation_output": False,
        "user_facing_buy_sell_signal_output": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "broad_search_performed": False,
        "validation_used_for_parameter_choice": False,
        "existing_strategy_rules_modified": False,
        "rejected_candidates_modified": False,
        "v0_26_traded_as_is": False,
        "closed_v0_82_rescued_again": False,
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
    }
