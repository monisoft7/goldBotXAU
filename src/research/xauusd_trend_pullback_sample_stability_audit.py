"""v0_49 sample sufficiency and stability audit for the v0_48 trend pullback candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.data.xauusd_low_tf_dataset_catalog import (
    DEFAULT_MANIFEST_PATH,
    build_low_tf_dataset_catalog,
    load_profiler_rows_from_catalog,
)
from src.research import xauusd_session_structure_atlas as atlas
from src.research import xauusd_new_directional_strategy_discovery_board as board_v0_48

AUDIT_VERSION = "v0_49"
SOURCE_BOARD_VERSION = "v0_48"
CANDIDATE_ID = "trend_pullback_continuation_directional"
DEFAULT_SOURCE_BOARD = Path("reports") / "xauusd_new_directional_discovery_v0_48.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_trend_pullback_stability_audit_v0_49.json"

PROMISING_INSUFFICIENT_SAMPLE = "promising_but_insufficient_validation_sample"
UNSTABLE_REJECT = "unstable_reject"
STABLE_ENOUGH = "stable_enough_for_candidate_locking_pre_oos_review"
AUDIT_FAILED = "audit_failed_missing_required_data"

VALIDATION_TRADE_MINIMUM = int(board_v0_48.GATE["validation_trades_min"])
FIXED_COST_R_PER_TRADE = 0.05


def build_xauusd_trend_pullback_stability_audit_v0_49(
    *,
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    source_board_path: str | Path = DEFAULT_SOURCE_BOARD,
    pattern: str = "xauusd_m*.csv",
    cost_r_per_trade: float = FIXED_COST_R_PER_TRADE,
) -> dict[str, Any]:
    """Audit the v0_48 best candidate without retuning, OOS, or execution."""
    source_board_file = Path(source_board_path)
    source_board = _read_json(source_board_file)
    source_candidate = _source_candidate(source_board) if source_board else None
    source_blockers = _source_blockers(source_board, source_candidate)

    try:
        catalog = build_low_tf_dataset_catalog(data_dir=data_dir, manifest_path=manifest_path, pattern=pattern)
        rows = [
            row
            for row in load_profiler_rows_from_catalog(catalog)
            if row.get("source_timeframe") in atlas.LOW_TF_ALLOWED and row.get("split") in {"train", "validation"}
        ]
        profiles = board_v0_48._day_profiles(rows)
        if not rows:
            source_blockers.append("train_validation_m5_m10_rows_missing")
        if not profiles:
            source_blockers.append("train_validation_session_profiles_missing")
    except Exception as exc:
        catalog = None
        profiles = []
        source_blockers.append(f"train_validation_data_load_failed:{type(exc).__name__}:{exc}")

    if source_blockers:
        return _base_report(
            audit_status=AUDIT_FAILED,
            source_board=source_board,
            source_candidate=source_candidate,
            trades=[],
            train_metrics={},
            validation_metrics={},
            cost_sensitivity={},
            sample_concentration_risk=_empty_concentration_risk(),
            stability_decision=AUDIT_FAILED,
            candidate_locking_allowed_pre_oos=False,
            blockers=source_blockers,
            warnings=[],
            next_recommended_step="repair required v0_48 board or train/validation data before rerunning v0_49",
            data_files_used=_data_files_used(catalog) if catalog else [],
        )

    trades = _trend_pullback_trades(profiles)
    train_trades = [trade for trade in trades if trade["split"] == "train"]
    validation_trades = [trade for trade in trades if trade["split"] == "validation"]
    train_metrics = board_v0_48._split_metrics(train_trades)
    validation_metrics = board_v0_48._split_metrics(validation_trades)
    metric_warnings = _metric_match_warnings(source_candidate, train_metrics, validation_metrics)
    cost_sensitivity = _cost_sensitivity(trades, cost_r_per_trade=cost_r_per_trade)
    concentration = _sample_concentration_risk(trades)

    blockers: list[str] = []
    warnings = [
        "audit_only_no_oos_no_demo_promotion",
        "candidate_rules_reconstructed_from_v0_48_fixed_family_rule",
        *metric_warnings,
        *concentration["warnings"],
    ]
    validation_count_passed = int(validation_metrics["trades"]) >= VALIDATION_TRADE_MINIMUM
    if not validation_count_passed:
        blockers.append("validation_trade_count_below_fixed_minimum_blocks_candidate_locking")
    if cost_sensitivity["edge_broken_by_fixed_cost"] is True:
        blockers.append("fixed_cost_sensitivity_breaks_train_or_validation_edge")

    stability_decision = _stability_decision(
        train_metrics=train_metrics,
        validation_metrics=validation_metrics,
        validation_count_passed=validation_count_passed,
        cost_breaks_edge=cost_sensitivity["edge_broken_by_fixed_cost"],
        concentration=concentration,
    )
    candidate_locking_allowed = stability_decision == STABLE_ENOUGH

    return _base_report(
        audit_status="completed",
        source_board=source_board,
        source_candidate=source_candidate,
        trades=trades,
        train_metrics=train_metrics,
        validation_metrics=validation_metrics,
        cost_sensitivity=cost_sensitivity,
        sample_concentration_risk=concentration,
        stability_decision=stability_decision,
        candidate_locking_allowed_pre_oos=candidate_locking_allowed,
        blockers=blockers,
        warnings=warnings,
        next_recommended_step=_next_step(stability_decision),
        data_files_used=_data_files_used(catalog) if catalog else [],
    )


def save_xauusd_trend_pullback_stability_audit(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _trend_pullback_trades(profiles: list[board_v0_48.DayProfile]) -> list[dict[str, Any]]:
    rule = board_v0_48._family_rules()[CANDIDATE_ID]
    trades: list[dict[str, Any]] = []
    for profile in profiles:
        for signal in rule(profile):
            trade = board_v0_48._trade_result(signal)
            trade["year"] = trade["date"][:4]
            trade["month"] = trade["date"][:7]
            trade["session_or_block"] = f"{trade['signal_window']}->{trade['evaluation_window']}"
            trades.append(trade)
    return trades


def _base_report(
    *,
    audit_status: str,
    source_board: dict[str, Any] | None,
    source_candidate: dict[str, Any] | None,
    trades: list[dict[str, Any]],
    train_metrics: dict[str, Any],
    validation_metrics: dict[str, Any],
    cost_sensitivity: dict[str, Any],
    sample_concentration_risk: dict[str, Any],
    stability_decision: str,
    candidate_locking_allowed_pre_oos: bool,
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
    data_files_used: list[str],
) -> dict[str, Any]:
    validation_trade_count = int(validation_metrics.get("trades", 0))
    report = {
        "audit_version": AUDIT_VERSION,
        "audit_status": audit_status,
        "source_board_version": SOURCE_BOARD_VERSION,
        "source_board_status": source_board.get("board_status") if source_board else None,
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": _candidate_rules_preserved(source_board, source_candidate, warnings),
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "validation_trade_count": validation_trade_count,
        "validation_trade_minimum": VALIDATION_TRADE_MINIMUM,
        "validation_trade_count_passed": validation_trade_count >= VALIDATION_TRADE_MINIMUM,
        "trade_distribution_by_split": _distribution_by_split(trades),
        "trade_distribution_by_year": _distribution(trades, "year"),
        "trade_distribution_by_month": _distribution(trades, "month"),
        "trade_distribution_by_session_or_block": _distribution(trades, "session_or_block"),
        "side_distribution": _distribution(trades, "side"),
        "win_loss_streaks": _win_loss_streaks(trades),
        "train_validation_degradation": _train_validation_degradation(train_metrics, validation_metrics),
        "sample_concentration_risk": sample_concentration_risk,
        "cost_sensitivity_if_available": cost_sensitivity,
        "stability_decision": stability_decision,
        "candidate_locking_allowed_pre_oos": candidate_locking_allowed_pre_oos,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "trade_recommendation_output_present": False,
        "data_csv_added": False,
        "data_files_used": data_files_used,
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }
    return report


def _source_blockers(source_board: dict[str, Any] | None, source_candidate: dict[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if source_board is None:
        return ["source_v0_48_board_missing_or_invalid"]
    if source_board.get("board_version") != SOURCE_BOARD_VERSION:
        blockers.append("source_board_version_mismatch")
    if source_board.get("train_validation_only") is not True:
        blockers.append("source_board_not_train_validation_only")
    if source_board.get("oos_used") is not False:
        blockers.append("source_board_oos_used")
    if source_board.get("repeated_oos_review") is not False:
        blockers.append("source_board_repeated_oos_review")
    for flag in ("retune_performed", "threshold_search_performed", "parameter_grid_performed"):
        if source_board.get(flag) is not False:
            blockers.append(f"source_board_{flag}_not_false")
    if source_board.get("best_candidate_id") != CANDIDATE_ID:
        blockers.append("source_board_best_candidate_not_trend_pullback")
    if source_candidate is None:
        blockers.append("source_trend_pullback_candidate_missing")
    elif source_candidate.get("fixed_before_evaluation") is not True:
        blockers.append("source_candidate_not_fixed_before_evaluation")
    return blockers


def _source_candidate(source_board: dict[str, Any] | None) -> dict[str, Any] | None:
    if not source_board:
        return None
    for candidate in source_board.get("candidate_results", []):
        if isinstance(candidate, dict) and candidate.get("candidate_id") == CANDIDATE_ID:
            return candidate
    return None


def _metric_match_warnings(
    source_candidate: dict[str, Any] | None,
    train_metrics: dict[str, Any],
    validation_metrics: dict[str, Any],
) -> list[str]:
    if not source_candidate:
        return ["source_candidate_metrics_unavailable_for_rule_preservation_check"]
    warnings: list[str] = []
    for split, metrics in (("train", train_metrics), ("validation", validation_metrics)):
        source_metrics = source_candidate.get(f"{split}_metrics", {})
        for key in ("trades", "wins", "losses", "profit_factor", "expectancy_r"):
            if not _same_metric(source_metrics.get(key), metrics.get(key)):
                warnings.append(f"reconstructed_{split}_{key}_differs_from_v0_48_source")
    return warnings


def _same_metric(left: Any, right: Any) -> bool:
    if left == right:
        return True
    try:
        return abs(float(left) - float(right)) < 0.000000001
    except (TypeError, ValueError):
        return False


def _candidate_rules_preserved(
    source_board: dict[str, Any] | None,
    source_candidate: dict[str, Any] | None,
    warnings: list[str],
) -> bool:
    if source_board is None or source_candidate is None:
        return False
    if source_candidate.get("fixed_before_evaluation") is not True:
        return False
    return not any(warning.startswith("reconstructed_") for warning in warnings)


def _cost_sensitivity(trades: list[dict[str, Any]], *, cost_r_per_trade: float) -> dict[str, Any]:
    adjusted_trades = [
        {**trade, "return_r": float(trade["return_r"]) - cost_r_per_trade, "raw_return_r": trade["return_r"]}
        for trade in trades
    ]
    train = board_v0_48._split_metrics([trade for trade in adjusted_trades if trade["split"] == "train"])
    validation = board_v0_48._split_metrics([trade for trade in adjusted_trades if trade["split"] == "validation"])
    train_edge_ok = _pf_value(train.get("profit_factor")) >= 1.0 and float(train.get("expectancy_r", 0.0)) > 0
    validation_edge_ok = _pf_value(validation.get("profit_factor")) >= 1.0 and float(validation.get("expectancy_r", 0.0)) > 0
    return {
        "available": True,
        "method": "fixed_existing_framework_cost_r_per_trade_deduction",
        "cost_r_per_trade": cost_r_per_trade,
        "train_metrics_after_cost": train,
        "validation_metrics_after_cost": validation,
        "train_edge_ok_after_cost": train_edge_ok,
        "validation_edge_ok_after_cost": validation_edge_ok,
        "edge_broken_by_fixed_cost": not (train_edge_ok and validation_edge_ok),
    }


def _sample_concentration_risk(trades: list[dict[str, Any]]) -> dict[str, Any]:
    validation = [trade for trade in trades if trade["split"] == "validation"]
    reasons: list[str] = []
    warnings: list[str] = []
    if len(validation) < VALIDATION_TRADE_MINIMUM:
        reasons.append("validation_trade_count_below_fixed_minimum")
    for key, label, threshold in (
        ("month", "month", 0.5),
        ("side", "side", 0.75),
        ("session_or_block", "session_or_block", 0.75),
    ):
        share = _max_share(validation, key)
        if validation and share >= threshold:
            reasons.append(f"validation_trades_concentrated_in_single_{label}")
    risk_level = "high" if reasons else "low"
    if reasons:
        warnings.extend(f"sample_concentration_risk:{reason}" for reason in reasons)
    return {
        "risk_level": risk_level,
        "risk_present": bool(reasons),
        "reasons": reasons,
        "validation_trade_count": len(validation),
        "validation_month_max_share": _max_share(validation, "month"),
        "validation_side_max_share": _max_share(validation, "side"),
        "validation_session_or_block_max_share": _max_share(validation, "session_or_block"),
        "warnings": warnings,
    }


def _empty_concentration_risk() -> dict[str, Any]:
    return {
        "risk_level": "unknown",
        "risk_present": True,
        "reasons": ["audit_failed_missing_required_data"],
        "validation_trade_count": 0,
        "validation_month_max_share": 0.0,
        "validation_side_max_share": 0.0,
        "validation_session_or_block_max_share": 0.0,
        "warnings": [],
    }


def _stability_decision(
    *,
    train_metrics: dict[str, Any],
    validation_metrics: dict[str, Any],
    validation_count_passed: bool,
    cost_breaks_edge: bool,
    concentration: dict[str, Any],
) -> str:
    if cost_breaks_edge:
        return UNSTABLE_REJECT
    if not validation_count_passed:
        return PROMISING_INSUFFICIENT_SAMPLE
    if concentration.get("risk_level") == "high":
        return UNSTABLE_REJECT
    strong_train = _pf_value(train_metrics.get("profit_factor")) >= float(board_v0_48.GATE["train_profit_factor_min"])
    strong_validation = _pf_value(validation_metrics.get("profit_factor")) >= float(
        board_v0_48.GATE["validation_profit_factor_min"]
    )
    positive_expectancy = (
        float(train_metrics.get("expectancy_r", 0.0)) > 0 and float(validation_metrics.get("expectancy_r", 0.0)) > 0
    )
    if strong_train and strong_validation and positive_expectancy:
        return STABLE_ENOUGH
    return UNSTABLE_REJECT


def _next_step(stability_decision: str) -> str:
    if stability_decision == PROMISING_INSUFFICIENT_SAMPLE:
        return "collect more train/validation-equivalent evidence or stop; do not lock candidate or run OOS"
    if stability_decision == STABLE_ENOUGH:
        return "human pre-OOS review of the locked candidate artifact; demo execution remains blocked"
    if stability_decision == UNSTABLE_REJECT:
        return "reject this fixed candidate branch without retuning or OOS"
    return "repair required data before deciding"


def _distribution_by_split(trades: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        split: {
            "trades": len(split_trades),
            "wins": sum(1 for trade in split_trades if trade["won"] is True),
            "losses": sum(1 for trade in split_trades if trade["return_r"] < 0),
        }
        for split, split_trades in _group_by_split(trades).items()
    }


def _distribution(trades: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {"train": {}, "validation": {}}
    for trade in trades:
        split = str(trade["split"])
        value = str(trade[key])
        result.setdefault(split, {})
        result[split][value] = result[split].get(value, 0) + 1
    return {split: dict(sorted(values.items())) for split, values in sorted(result.items())}


def _group_by_split(trades: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped = {"train": [], "validation": []}
    for trade in trades:
        grouped.setdefault(str(trade["split"]), []).append(trade)
    return grouped


def _win_loss_streaks(trades: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        split: {
            "max_consecutive_wins": _max_consecutive(split_trades, won=True),
            "max_consecutive_losses": _max_consecutive(split_trades, won=False),
        }
        for split, split_trades in _group_by_split(sorted(trades, key=lambda trade: (trade["split"], trade["date"]))).items()
    }


def _max_consecutive(trades: list[dict[str, Any]], *, won: bool) -> int:
    best = 0
    current = 0
    for trade in trades:
        trade_won = bool(trade["won"])
        if trade_won is won:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _train_validation_degradation(train_metrics: dict[str, Any], validation_metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "profit_factor_delta_validation_minus_train": _pf_value(validation_metrics.get("profit_factor"))
        - _pf_value(train_metrics.get("profit_factor")),
        "expectancy_delta_validation_minus_train": float(validation_metrics.get("expectancy_r", 0.0))
        - float(train_metrics.get("expectancy_r", 0.0)),
        "validation_pf_improved_vs_train": _pf_value(validation_metrics.get("profit_factor"))
        > _pf_value(train_metrics.get("profit_factor")),
        "validation_expectancy_improved_vs_train": float(validation_metrics.get("expectancy_r", 0.0))
        > float(train_metrics.get("expectancy_r", 0.0)),
    }


def _max_share(trades: list[dict[str, Any]], key: str) -> float:
    if not trades:
        return 0.0
    counts: dict[str, int] = {}
    for trade in trades:
        value = str(trade[key])
        counts[value] = counts.get(value, 0) + 1
    return max(counts.values()) / len(trades)


def _pf_value(value: Any) -> float:
    if value == "inf":
        return float("inf")
    return float(value or 0.0)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _data_files_used(catalog: dict[str, Any]) -> list[str]:
    return sorted(
        str(entry["filename"])
        for entry in catalog.get("entries", [])
        if entry.get("usable_for_profiler") is True and entry.get("source_timeframe") in atlas.LOW_TF_ALLOWED
    )


def _safety_flags() -> dict[str, Any]:
    return {
        "research_only": True,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
        "trade_recommendation_output_present": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "oos_used": False,
        "repeated_oos_review": False,
    }
