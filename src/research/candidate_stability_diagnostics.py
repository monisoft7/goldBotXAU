"""Train-only stability diagnostics for rejected research candidates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.backtest.metrics import calculate_metrics
from src.data.xauusd_csv_loader import load_xauusd_m15_csvs
from src.data.xauusd_dataset_manifest import build_xauusd_dataset_manifest
from src.research.candidate_registry import candidate_registry_by_id
from src.research.oos_guard import OOSGuard
from src.research.strategy_research_runner import V0_11_CANDIDATE_ID
from src.strategies.xauusd_session_volatility_expansion import XauusdSessionVolatilityExpansionCandidate

DIAGNOSTIC_VERSION = "v0_12"
DEFAULT_CANDIDATE_ID = V0_11_CANDIDATE_ID
ATR_REGIME_THRESHOLDS = {
    "low_mid": 1.3230733892270252,
    "mid_high": 1.7216007380924383,
    "high_extreme": 2.1671266144165635,
}


@dataclass(frozen=True)
class NeutralTradeRecord:
    opened_at: str
    closed_at: str
    result_r: float
    holding_bars: int
    reason_code: str
    range_to_atr: float

    def exposed(self) -> dict[str, float | int | str]:
        return {
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "result_r": self.result_r,
            "holding_bars": self.holding_bars,
            "reason_code": self.reason_code,
        }


def diagnose_candidate_stability(
    data_dir: str | Path = "data",
    pattern: str = "xauusd_m15_*.csv",
    candidate_id: str = DEFAULT_CANDIDATE_ID,
) -> dict[str, Any]:
    registry_entry = candidate_registry_by_id().get(candidate_id)
    candidate = _candidate_from_id(candidate_id)
    if candidate is None or registry_entry is None:
        return _base_report(
            status="candidate_not_found",
            candidate=None,
            registry_entry=registry_entry,
            manifest={},
            reason=f"unknown_candidate:{candidate_id}",
        )

    manifest = build_xauusd_dataset_manifest(data_dir, pattern).to_dict()
    if manifest["readiness"]["ready_for_strategy_research"] is not True:
        return _base_report(
            status="data_not_ready",
            candidate=candidate,
            registry_entry=registry_entry,
            manifest=manifest,
            reason="dataset_manifest_not_ready",
        )

    try:
        candles = load_xauusd_m15_csvs(data_dir, pattern).records
        guard = OOSGuard(manifest)
        train_candles = guard.filter_candles(candles, "train")
        records = _simulate_neutral_train_records(candidate, train_candles)
        outcomes = [record.result_r for record in records]
        overall = _overall_metrics(outcomes)
        breakdowns = _build_breakdowns(records)
        stability_summary = _stability_summary(overall, breakdowns)
        return _base_report(
            status="diagnostic_ready",
            candidate=candidate,
            registry_entry=registry_entry,
            manifest=manifest,
            oos_guard=guard.report(),
            train_overall_metrics=overall,
            breakdowns=breakdowns,
            stability_summary=stability_summary,
            diagnostic_decision=_diagnostic_decision(stability_summary),
        )
    except Exception as exc:
        return _base_report(
            status="diagnostic_failed",
            candidate=candidate,
            registry_entry=registry_entry,
            manifest=manifest,
            reason=str(exc),
        )


def _candidate_from_id(candidate_id: str) -> XauusdSessionVolatilityExpansionCandidate | None:
    if candidate_id == DEFAULT_CANDIDATE_ID:
        return XauusdSessionVolatilityExpansionCandidate()
    return None


def _base_report(
    *,
    status: str,
    candidate: XauusdSessionVolatilityExpansionCandidate | None,
    registry_entry: dict[str, Any] | None,
    manifest: dict[str, Any],
    reason: str | None = None,
    oos_guard: dict[str, bool] | None = None,
    train_overall_metrics: dict[str, Any] | None = None,
    breakdowns: dict[str, list[dict[str, Any]]] | None = None,
    stability_summary: dict[str, Any] | None = None,
    diagnostic_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = manifest.get("dataset", {})
    splits = manifest.get("splits", {})
    empty_overall = _overall_metrics([])
    report = {
        "diagnostic_version": DIAGNOSTIC_VERSION,
        "status": status,
        "candidate": {
            "candidate_id": candidate.candidate_id if candidate else None,
            "candidate_version": candidate.candidate_version if candidate else None,
            "family_name": candidate.family_name if candidate else None,
            "status_before_diagnostic": (registry_entry or {}).get("status"),
            "do_not_retune": (registry_entry or {}).get("do_not_retune") is True,
        },
        "dataset": {
            "candle_count": int(dataset.get("candle_count", 0) or 0),
            "train_candle_count": _split_count(splits, "train"),
            "validation_candle_count": _split_count(splits, "validation"),
            "oos_candle_count": _split_count(splits, "out_of_sample"),
            "diagnostic_split": "train",
        },
        "oos_guard": oos_guard
        or {
            "oos_locked": True,
            "oos_access_attempted": False,
            "oos_access_allowed": False,
        },
        "train_overall_metrics": train_overall_metrics or empty_overall,
        "breakdowns": breakdowns or _empty_breakdowns(),
        "stability_summary": stability_summary or _empty_stability_summary(),
        "diagnostic_decision": diagnostic_decision or _diagnostic_decision(_empty_stability_summary()),
        "safety": {
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
            "execution_queue_enabled": False,
            "buy_sell_output_allowed": False,
            "strategy_logic_added": False,
            "parameter_tuning_added": False,
            "oos_evaluated": False,
        },
        "errors": [reason] if reason else [],
    }
    return report


def _split_count(splits: dict[str, Any], split_name: str) -> int:
    return int(splits.get(split_name, {}).get("candle_count", 0) or 0)


def _simulate_neutral_train_records(
    candidate: XauusdSessionVolatilityExpansionCandidate,
    candles: list[dict[str, float | str]],
) -> list[NeutralTradeRecord]:
    candidate.validate()
    rows = [_normal_row(candle) for candle in candles]
    minimum_rows = max(candidate.atr_period_bars, candidate.reference_lookback_bars) + 1
    if len(rows) < minimum_rows:
        return []

    true_ranges = _true_ranges(rows)
    records: list[NeutralTradeRecord] = []
    index = max(candidate.atr_period_bars, candidate.reference_lookback_bars)
    while index < len(rows) - 1:
        atr = sum(true_ranges[index - candidate.atr_period_bars + 1 : index + 1]) / candidate.atr_period_bars
        if atr <= 0:
            index += 1
            continue

        scenario = candidate._scenario(rows, index, atr)
        if scenario is None:
            index += 1
            continue

        result_r, exit_index, reason_code = _simulate_neutral_outcome(candidate, rows, index, scenario, atr)
        entry_index = index + 1
        records.append(
            NeutralTradeRecord(
                opened_at=str(rows[entry_index]["timestamp"]),
                closed_at=str(rows[exit_index]["timestamp"]),
                result_r=result_r,
                holding_bars=max(1, exit_index - entry_index + 1),
                reason_code=reason_code,
                range_to_atr=(rows[index]["high"] - rows[index]["low"]) / atr,
            )
        )
        index = max(index + 1, exit_index + candidate.cooldown_bars_after_trade + 1)

    return records


def _simulate_neutral_outcome(
    candidate: XauusdSessionVolatilityExpansionCandidate,
    rows: list[dict[str, float | str]],
    signal_index: int,
    scenario: str,
    atr: float,
) -> tuple[float, int, str]:
    signal = rows[signal_index]
    entry_index = signal_index + 1
    entry = float(rows[entry_index]["open"])
    final_index = min(entry_index + candidate.max_hold_bars - 1, len(rows) - 1)

    if scenario == "upper_session_expansion":
        stop = float(signal["low"]) - candidate.stop_atr_buffer * atr
        risk = entry - stop
        if risk <= 0:
            return -candidate.cost_r_per_trade, entry_index, "invalid_risk"
        target = entry + candidate.target_r * risk
        for index in range(entry_index, final_index + 1):
            row = rows[index]
            if float(row["low"]) <= stop:
                return -1.0 - candidate.cost_r_per_trade, index, "risk_limit"
            if float(row["high"]) >= target:
                return candidate.target_r - candidate.cost_r_per_trade, index, "target_reached"
        timeout_r = (float(rows[final_index]["close"]) - entry) / risk
        return timeout_r - candidate.cost_r_per_trade, final_index, "time_exit"

    stop = float(signal["high"]) + candidate.stop_atr_buffer * atr
    risk = stop - entry
    if risk <= 0:
        return -candidate.cost_r_per_trade, entry_index, "invalid_risk"
    target = entry - candidate.target_r * risk
    for index in range(entry_index, final_index + 1):
        row = rows[index]
        if float(row["high"]) >= stop:
            return -1.0 - candidate.cost_r_per_trade, index, "risk_limit"
        if float(row["low"]) <= target:
            return candidate.target_r - candidate.cost_r_per_trade, index, "target_reached"
    timeout_r = (entry - float(rows[final_index]["close"])) / risk
    return timeout_r - candidate.cost_r_per_trade, final_index, "time_exit"


def _normal_row(candle: dict[str, float | str]) -> dict[str, float | str]:
    timestamp = datetime.fromisoformat(str(candle["timestamp"]))
    return {
        "timestamp": timestamp.isoformat(),
        "hour": float(timestamp.hour),
        "open": float(candle["open"]),
        "high": float(candle["high"]),
        "low": float(candle["low"]),
        "close": float(candle["close"]),
    }


def _true_ranges(rows: list[dict[str, float | str]]) -> list[float]:
    ranges: list[float] = []
    previous_close: float | None = None
    for row in rows:
        high = float(row["high"])
        low = float(row["low"])
        if previous_close is None:
            ranges.append(high - low)
        else:
            ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
        previous_close = float(row["close"])
    return ranges


def _build_breakdowns(records: list[NeutralTradeRecord]) -> dict[str, list[dict[str, Any]]]:
    return {
        "by_year": _bucket_metrics(records, lambda record: str(_closed_at(record).year)),
        "by_quarter": _bucket_metrics(records, _quarter_bucket),
        "by_month": _bucket_metrics(records, lambda record: _closed_at(record).strftime("%Y-%m")),
        "by_hour": _bucket_metrics(records, lambda record: f"{_closed_at(record).hour:02d}"),
        "by_session_block": _bucket_metrics(records, _session_block),
        "by_atr_regime": _bucket_metrics(records, _atr_regime),
    }


def _bucket_metrics(
    records: list[NeutralTradeRecord],
    bucket_fn: Callable[[NeutralTradeRecord], str],
) -> list[dict[str, Any]]:
    buckets: dict[str, list[float]] = {}
    for record in records:
        buckets.setdefault(bucket_fn(record), []).append(record.result_r)
    return [
        {"bucket": bucket, **_compact_metrics(outcomes)}
        for bucket, outcomes in sorted(buckets.items(), key=lambda item: item[0])
    ]


def _closed_at(record: NeutralTradeRecord) -> datetime:
    return datetime.fromisoformat(record.closed_at)


def _quarter_bucket(record: NeutralTradeRecord) -> str:
    closed = _closed_at(record)
    quarter = ((closed.month - 1) // 3) + 1
    return f"{closed.year}-Q{quarter}"


def _session_block(record: NeutralTradeRecord) -> str:
    hour = _closed_at(record).hour
    if hour < 6:
        return "block_00_06"
    if hour < 12:
        return "block_06_12"
    if hour < 18:
        return "block_12_18"
    return "block_18_24"


def _atr_regime(record: NeutralTradeRecord) -> str:
    if record.range_to_atr < ATR_REGIME_THRESHOLDS["low_mid"]:
        return "low_atr"
    if record.range_to_atr < ATR_REGIME_THRESHOLDS["mid_high"]:
        return "mid_atr"
    if record.range_to_atr < ATR_REGIME_THRESHOLDS["high_extreme"]:
        return "high_atr"
    return "extreme_atr"


def _overall_metrics(outcomes: list[float]) -> dict[str, Any]:
    metrics = calculate_metrics(outcomes, out_of_sample_result="locked_not_evaluated").to_dict()
    return {
        "trade_count": metrics["trade_count"],
        "win_rate": metrics["win_rate"],
        "profit_factor": metrics["profit_factor"],
        "expectancy": metrics["expectancy"],
        "max_drawdown": metrics["max_drawdown"],
        "max_consecutive_losses": metrics["max_consecutive_losses"],
        "final_equity_r": _final_equity(metrics),
        "gross_profit": metrics["gross_profit"],
        "gross_loss": metrics["gross_loss"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
    }


def _compact_metrics(outcomes: list[float]) -> dict[str, Any]:
    metrics = calculate_metrics(outcomes, out_of_sample_result="locked_not_evaluated").to_dict()
    return {
        "trade_count": metrics["trade_count"],
        "win_rate": metrics["win_rate"],
        "profit_factor": metrics["profit_factor"],
        "expectancy": metrics["expectancy"],
        "final_equity_r": _final_equity(metrics),
        "max_consecutive_losses": metrics["max_consecutive_losses"],
        "gross_profit": metrics["gross_profit"],
        "gross_loss": metrics["gross_loss"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
    }


def _final_equity(metrics: dict[str, Any]) -> float:
    curve = metrics.get("equity_curve", [])
    if not curve:
        return 0.0
    return float(curve[-1])


def _stability_summary(overall: dict[str, Any], breakdowns: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    buckets = [
        bucket
        for name in ("by_year", "by_quarter", "by_month", "by_session_block", "by_atr_regime")
        for bucket in breakdowns[name]
        if bucket["trade_count"] >= 3
    ]
    positive = [bucket for bucket in buckets if bucket["final_equity_r"] > 0]
    negative = [bucket for bucket in buckets if bucket["final_equity_r"] < 0]
    flat = [bucket for bucket in buckets if bucket["final_equity_r"] == 0]
    best = max(buckets, key=lambda bucket: bucket["final_equity_r"], default=None)
    worst = min(buckets, key=lambda bucket: bucket["final_equity_r"], default=None)
    consistency_score = len(positive) / len(buckets) if buckets else 0.0
    train_failure_scope = _train_failure_scope(overall, buckets, negative)
    return {
        "positive_bucket_count": len(positive),
        "negative_bucket_count": len(negative),
        "flat_bucket_count": len(flat),
        "best_bucket": _bucket_ref(best),
        "worst_bucket": _bucket_ref(worst),
        "consistency_score": consistency_score,
        "train_failure_scope": train_failure_scope,
    }


def _train_failure_scope(
    overall: dict[str, Any],
    buckets: list[dict[str, Any]],
    negative: list[dict[str, Any]],
) -> str:
    if overall["trade_count"] < 30 or len(buckets) < 3:
        return "inconclusive"
    profit_factor = float("inf") if overall["profit_factor"] == "inf" else float(overall["profit_factor"])
    if profit_factor >= 1.0:
        return "inconclusive"
    if len(negative) > len(buckets) / 2:
        return "broad_failure"
    total_loss = sum(float(bucket["gross_loss"]) for bucket in buckets)
    worst_losses = sorted((float(bucket["gross_loss"]) for bucket in negative), reverse=True)
    concentrated_loss = sum(worst_losses[: max(1, len(buckets) // 4)])
    if total_loss > 0 and concentrated_loss / total_loss >= 0.6:
        return "concentrated_failure"
    return "inconclusive"


def _bucket_ref(bucket: dict[str, Any] | None) -> dict[str, Any] | None:
    if bucket is None:
        return None
    return {
        "bucket": bucket["bucket"],
        "trade_count": bucket["trade_count"],
        "final_equity_r": bucket["final_equity_r"],
        "profit_factor": bucket["profit_factor"],
    }


def _diagnostic_decision(stability_summary: dict[str, Any]) -> dict[str, Any]:
    scope = stability_summary["train_failure_scope"]
    if scope == "broad_failure":
        next_action = "abandon_family"
        reasons = ["train_profit_factor_below_1", "losses_spread_across_meaningful_train_buckets"]
    elif scope == "concentrated_failure":
        next_action = "design_new_family_from_train_profile"
        reasons = ["train_profit_factor_below_1", "losses_concentrated_in_minority_train_buckets"]
    else:
        next_action = "needs_manual_review"
        reasons = ["train_only_diagnostic_inconclusive"]
    return {
        "retune_allowed": False,
        "oos_review_allowed": False,
        "next_action": next_action,
        "reasons": reasons,
    }


def _empty_breakdowns() -> dict[str, list[dict[str, Any]]]:
    return {
        "by_year": [],
        "by_quarter": [],
        "by_month": [],
        "by_hour": [],
        "by_session_block": [],
        "by_atr_regime": [],
    }


def _empty_stability_summary() -> dict[str, Any]:
    return {
        "positive_bucket_count": 0,
        "negative_bucket_count": 0,
        "flat_bucket_count": 0,
        "best_bucket": None,
        "worst_bucket": None,
        "consistency_score": 0.0,
        "train_failure_scope": "inconclusive",
    }
