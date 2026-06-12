"""Strategy research harness with locked out-of-sample access."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.backtest.metrics import calculate_metrics
from src.data.xauusd_csv_loader import load_xauusd_m15_csvs
from src.data.xauusd_dataset_manifest import build_xauusd_dataset_manifest
from src.research.oos_guard import OOSGuard
from src.research.strategy_candidate import NullResearchCandidate, ResearchCandidate
from src.strategies.xauusd_atr_impulse_reversion import XauusdAtrImpulseReversionCandidate
from src.strategies.xauusd_low_atr_range_expansion_followthrough import (
    XauusdLowAtrRangeExpansionFollowthroughCandidate,
)
from src.strategies.xauusd_low_atr_x_hour_16_response import XauusdLowAtrXHour16ResponseCandidate
from src.strategies.xauusd_multi_bar_exhaustion_reversion import XauusdMultiBarExhaustionReversionCandidate
from src.strategies.xauusd_session_volatility_expansion import XauusdSessionVolatilityExpansionCandidate

HARNESS_VERSION = "v0_6"
V0_7_CANDIDATE_ID = "xauusd_atr_impulse_reversion_v0_7"
V0_8_CANDIDATE_ID = "xauusd_multi_bar_exhaustion_reversion_v0_8"
V0_11_CANDIDATE_ID = "xauusd_session_volatility_expansion_v0_11"
V0_14_CANDIDATE_ID = "xauusd_low_atr_range_expansion_followthrough_v0_14"
V0_17_CANDIDATE_ID = "xauusd_low_atr_x_hour_16_v0_17"


def run_strategy_research_harness(
    data_dir: str | Path = "data",
    pattern: str = "xauusd_m15_*.csv",
    candidate: ResearchCandidate | None = None,
    candidate_id: str | None = None,
    compact: bool = False,
) -> dict[str, Any]:
    active_candidate = candidate or _candidate_from_id(candidate_id)
    try:
        active_candidate.validate()
    except ValueError as exc:
        return _base_report(
            status="candidate_rejected",
            candidate=active_candidate,
            reason=str(exc),
            blocker=str(exc),
            compact=compact,
        )

    manifest = build_xauusd_dataset_manifest(data_dir, pattern).to_dict()
    if manifest["readiness"]["ready_for_strategy_research"] is not True:
        return _base_report(
            status="data_not_ready",
            candidate=active_candidate,
            manifest=manifest,
            reason="dataset_manifest_not_ready",
            blocker="dataset_manifest_not_ready",
            compact=compact,
        )

    try:
        candles = load_xauusd_m15_csvs(data_dir, pattern).records
        guard = OOSGuard(manifest)
        train_candles = guard.filter_candles(candles, "train")
        validation_candles = guard.filter_candles(candles, "validation")
        train_outcomes = active_candidate.run_on_split(train_candles, "train")
        validation_outcomes = active_candidate.run_on_split(validation_candles, "validation")
        train_metrics = calculate_metrics(train_outcomes).to_dict()
        validation_metrics = calculate_metrics(validation_outcomes).to_dict()
        validation_gate = _validation_gate(train_metrics, validation_metrics)
        is_null = active_candidate.is_null_candidate
        gate_passed = validation_gate["passed"]
        return _base_report(
            status="harness_ready" if is_null else "candidate_evaluated",
            candidate=active_candidate,
            manifest=manifest,
            oos_guard=guard.report(),
            train_candle_count=len(train_candles),
            validation_candle_count=len(validation_candles),
            train_metrics=train_metrics,
            validation_metrics=validation_metrics,
            validation_gate=validation_gate,
            eligible_for_oos_review=False if is_null else gate_passed,
            reason="null_candidate_no_strategy_edge"
            if is_null
            else ("validation_gate_passed" if gate_passed else "validation_gate_failed"),
            compact=compact,
        )
    except Exception as exc:
        return _base_report(
            status="run_failed",
            candidate=active_candidate,
            manifest=manifest,
            reason=str(exc),
            blocker=str(exc),
            compact=compact,
        )


def _base_report(
    *,
    status: str,
    candidate: ResearchCandidate,
    reason: str,
    manifest: dict[str, Any] | None = None,
    blocker: str | None = None,
    oos_guard: dict[str, bool] | None = None,
    train_candle_count: int | None = None,
    validation_candle_count: int | None = None,
    train_metrics: dict[str, Any] | None = None,
    validation_metrics: dict[str, Any] | None = None,
    validation_gate: dict[str, Any] | None = None,
    eligible_for_oos_review: bool = False,
    compact: bool = False,
) -> dict[str, Any]:
    manifest = manifest or {}
    dataset = manifest.get("dataset", {})
    splits = manifest.get("splits", {})
    empty_metrics = calculate_metrics([]).to_dict()
    report = {
        "research_harness_version": HARNESS_VERSION,
        "status": status,
        "candidate": {
            "candidate_id": candidate.candidate_id,
            "candidate_name": candidate.candidate_name,
            "candidate_version": candidate.candidate_version,
            "family_name": candidate.family_name,
            "is_null_candidate": candidate.is_null_candidate,
            "parameters": candidate.parameters(),
        },
        "dataset": {
            "candle_count": dataset.get("candle_count", 0),
            "train_candle_count": train_candle_count if train_candle_count is not None else _split_count(splits, "train"),
            "validation_candle_count": (
                validation_candle_count if validation_candle_count is not None else _split_count(splits, "validation")
            ),
            "oos_candle_count": _split_count(splits, "out_of_sample"),
        },
        "oos_guard": oos_guard
        or {
            "oos_locked": True,
            "oos_access_attempted": False,
            "oos_access_allowed": False,
        },
        "results": {
            "train_metrics": train_metrics or empty_metrics,
            "validation_metrics": validation_metrics or empty_metrics,
            "out_of_sample_result": "locked_not_evaluated",
        },
        "validation_gate": validation_gate or _validation_gate(empty_metrics, empty_metrics),
        "decision": {
            "eligible_for_oos_review": eligible_for_oos_review,
            "reason": reason,
        },
        "safety": {
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
            "execution_queue_enabled": False,
            "buy_sell_output_allowed": False,
            "oos_evaluated": False,
            "research_candidate_logic_present": not candidate.is_null_candidate,
            "execution_logic_present": False,
            "trade_recommendation_output_present": False,
        },
        "errors": [blocker] if blocker else [],
    }
    if compact:
        report["results"]["train_metrics"] = _compact_metrics(report["results"]["train_metrics"])
        report["results"]["validation_metrics"] = _compact_metrics(report["results"]["validation_metrics"])
    return report


def _split_count(splits: dict[str, Any], split_name: str) -> int:
    return int(splits.get(split_name, {}).get("candle_count", 0))


def _candidate_from_id(candidate_id: str | None) -> ResearchCandidate:
    if candidate_id in {None, "", "null_research_harness_test"}:
        return NullResearchCandidate()
    if candidate_id == V0_7_CANDIDATE_ID:
        return XauusdAtrImpulseReversionCandidate()
    if candidate_id == V0_8_CANDIDATE_ID:
        return XauusdMultiBarExhaustionReversionCandidate()
    if candidate_id == V0_11_CANDIDATE_ID:
        return XauusdSessionVolatilityExpansionCandidate()
    if candidate_id == V0_14_CANDIDATE_ID:
        return XauusdLowAtrRangeExpansionFollowthroughCandidate()
    if candidate_id == V0_17_CANDIDATE_ID:
        return XauusdLowAtrXHour16ResponseCandidate()
    raise ValueError(f"Unknown research candidate: {candidate_id}")


def _validation_gate(train_metrics: dict[str, Any], validation_metrics: dict[str, Any]) -> dict[str, Any]:
    thresholds = {
        "minimum_train_trades": 100,
        "minimum_validation_trades": 30,
        "minimum_train_profit_factor": 1.05,
        "minimum_validation_profit_factor": 1.10,
        "minimum_validation_expectancy": 0.0,
        "maximum_validation_max_consecutive_losses": 8,
    }
    checks = [
        ("not_enough_train_trades", train_metrics["trade_count"] >= thresholds["minimum_train_trades"]),
        (
            "not_enough_validation_trades",
            validation_metrics["trade_count"] >= thresholds["minimum_validation_trades"],
        ),
        (
            "train_profit_factor_below_minimum",
            _metric_float(train_metrics["profit_factor"]) >= thresholds["minimum_train_profit_factor"],
        ),
        (
            "validation_profit_factor_below_minimum",
            _metric_float(validation_metrics["profit_factor"]) >= thresholds["minimum_validation_profit_factor"],
        ),
        (
            "validation_expectancy_below_minimum",
            validation_metrics["expectancy"] >= thresholds["minimum_validation_expectancy"],
        ),
        (
            "validation_max_consecutive_losses_too_high",
            validation_metrics["max_consecutive_losses"] <= thresholds["maximum_validation_max_consecutive_losses"],
        ),
    ]
    reasons = [reason for reason, passed in checks if not passed]
    return {
        "passed": not reasons,
        "reasons": reasons,
        **thresholds,
    }


def _metric_float(value: Any) -> float:
    if value == "inf":
        return float("inf")
    return float(value)


def _compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "final_equity_r": _final_equity(metrics),
        "trade_count": metrics["trade_count"],
        "win_rate": metrics["win_rate"],
        "profit_factor": metrics["profit_factor"],
        "expectancy": metrics["expectancy"],
        "max_drawdown": metrics["max_drawdown"],
        "max_consecutive_losses": metrics["max_consecutive_losses"],
        "gross_profit": metrics["gross_profit"],
        "gross_loss": metrics["gross_loss"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "out_of_sample_result": metrics["out_of_sample_result"],
    }


def _final_equity(metrics: dict[str, Any]) -> float:
    curve = metrics.get("equity_curve", [])
    if not curve:
        return 0.0
    return float(curve[-1])
