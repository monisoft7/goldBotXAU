"""v0_84 last-chance trading decision sprint for the v0_82 executable candidate."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, time
from pathlib import Path
from typing import Any, Callable

from src.research import xauusd_executable_candidate_train_validation as v83

SPRINT_VERSION = "v0_84"
SPRINT_NAME = "v0_84_trading_decision_sprint"
DEFAULT_OUTPUT = Path("reports") / "xauusd_trading_decision_sprint_v0_84.json"
DEFAULT_BASELINE_REPORT = Path("reports") / "xauusd_executable_candidate_train_validation_v0_83.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"
DEFAULT_DESIGN_REPORT = Path("reports") / "xauusd_executable_fixed_rule_candidate_design_v0_82.json"

PASSED = "trading_decision_sprint_passed_ready_for_single_oos"
FAILED = "trading_decision_sprint_failed_close_candidate"
BLOCKED = "trading_decision_sprint_blocked_missing_diagnostics"

NEXT_IF_PASSED = "v0_85_single_oos_review_for_rescued_executable_candidate"
NEXT_IF_FAILED = "v0_85_fresh_executable_candidate_family_selection_sprint"
NEXT_IF_BLOCKED = "v0_85_repair_trade_diagnostics_then_decide"

LONG_ONLY = "long_only_variant"
SHORT_ONLY = "short_only_variant"
NY_CORE_ONLY = "ny_core_only_variant"
REDUCE_OVERTRADING = "reduce_overtrading_time_filter_variant"
CLOSE_NO_VARIANT = "close_candidate_no_variant"

NY_CORE_START = time(13, 0)
NY_CORE_END = time(16, 0)
REENTRY_CLUSTER_MINUTES = 30


def build_xauusd_trading_decision_sprint_v0_84(
    *,
    root: str | Path = ".",
    data_dir: str | Path | None = None,
    manifest_path: str | Path | None = None,
    source_design_path: str | Path | None = None,
    baseline_report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run the v0_84 train/validation-only decision sprint."""
    root_path = Path(root)
    data_path = Path(data_dir) if data_dir is not None else root_path / "data"
    manifest_file = Path(manifest_path) if manifest_path is not None else root_path / DEFAULT_MANIFEST
    design_file = Path(source_design_path) if source_design_path is not None else root_path / DEFAULT_DESIGN_REPORT
    baseline_file = Path(baseline_report_path) if baseline_report_path is not None else root_path / DEFAULT_BASELINE_REPORT

    baseline = _read_json(baseline_file)
    if baseline is None:
        baseline = v83.build_xauusd_executable_candidate_train_validation_v0_83(
            data_dir=data_path,
            manifest_path=manifest_file,
            source_design_path=design_file,
        )

    try:
        manifest = v83._read_json(manifest_file)
        if manifest is None:
            return _blocked_report(baseline, ["dataset_manifest_missing_or_invalid"])
        m15_load = v83._load_train_validation_candles(data_path, "xauusd_m15_*.csv", manifest)
        m5_load = v83._load_train_validation_candles(
            data_path,
            "xauusd_m5_xauusd_2023-01-01_2025-12-31.csv",
            manifest,
        )
        if not m15_load["candles"] or not m5_load["candles"]:
            return _blocked_report(baseline, ["missing_train_validation_candles_for_trade_reconstruction"])

        base_trades = _evaluate_variant_records(
            m15_load["candles"],
            m5_load["candles"],
            variant_type=None,
            cost_r_per_trade=float(v83.FIXED_EVALUATION_RULES["cost_r_per_trade"]),
        )
        sensitivity_trades = _evaluate_variant_records(
            m15_load["candles"],
            m5_load["candles"],
            variant_type=None,
            cost_r_per_trade=float(v83.FIXED_EVALUATION_RULES["cost_sensitivity_cost_r_per_trade"]),
        )
    except Exception as exc:
        return _blocked_report(baseline, [f"trade_reconstruction_failed:{type(exc).__name__}:{exc}"])

    train_trades = [trade for trade in base_trades if trade["split"] == "train"]
    if not train_trades:
        return _blocked_report(baseline, ["train_trade_records_missing"])

    diagnostics = _train_only_diagnostics(train_trades, sensitivity_trades)
    selected = select_rescue_decision_from_train_diagnostics(diagnostics)

    rescue_train_metrics = None
    rescue_validation_metrics = None
    gate_results: dict[str, Any] = {}
    rescue_variant_id = None
    rescue_variant_rules = None
    passed_all = False
    failure_reasons: list[str]
    rescue_variant_created = selected != CLOSE_NO_VARIANT
    rescue_variant_evaluated_count = 0

    if rescue_variant_created:
        rescue_variant_id = f"{v83.CANDIDATE_ID}_{selected}_v0_84"
        rescue_variant_rules = _variant_rules_summary(selected)
        variant_trades = _evaluate_variant_records(
            m15_load["candles"],
            m5_load["candles"],
            variant_type=selected,
            cost_r_per_trade=float(v83.FIXED_EVALUATION_RULES["cost_r_per_trade"]),
        )
        variant_sensitivity_trades = _evaluate_variant_records(
            m15_load["candles"],
            m5_load["candles"],
            variant_type=selected,
            cost_r_per_trade=float(v83.FIXED_EVALUATION_RULES["cost_sensitivity_cost_r_per_trade"]),
        )
        rescue_variant_evaluated_count = 1
        rescue_train_metrics = v83._metrics([trade for trade in variant_trades if trade["split"] == "train"])
        rescue_validation_metrics = v83._metrics([trade for trade in variant_trades if trade["split"] == "validation"])
        sensitivity = v83._cost_sensitivity_summary(variant_trades, variant_sensitivity_trades)
        rescue_validation_metrics = {**rescue_validation_metrics, "cost_sensitivity_summary": sensitivity}
        gate_results = v83._gate_results(rescue_train_metrics, rescue_validation_metrics, sensitivity)
        passed_all = all(result["passed"] is True for result in gate_results.values())
        failure_reasons = [name for name, result in gate_results.items() if result["passed"] is not True]
    else:
        failure_reasons = ["train_only_diagnostics_do_not_justify_one_allowed_structural_rescue_variant"]

    status = PASSED if passed_all else FAILED
    safety = _safety_flags()
    return {
        "sprint_version": SPRINT_VERSION,
        "sprint_name": SPRINT_NAME,
        "sprint_status": status,
        "source_candidate_id": v83.CANDIDATE_ID,
        "source_design_version": "v0_82",
        "source_evaluation_version": "v0_83",
        "baseline_v0_83_status": baseline.get("evaluation_status"),
        "baseline_v0_83_summary": _baseline_summary(baseline),
        "train_only_diagnostics_available": True,
        "trade_detail_available": True,
        "trade_detail_source": "reconstructed_deterministically_from_v0_83_evaluator",
        "validation_used_for_rescue_selection": False,
        "train_side_diagnostics": diagnostics["side"],
        "train_session_diagnostics": diagnostics["session"],
        "train_drawdown_diagnostics": diagnostics["drawdown"],
        "train_consecutive_loss_diagnostics": diagnostics["consecutive_loss"],
        "train_overtrading_diagnostics": diagnostics["overtrading"],
        "train_cost_sensitivity_diagnostics": diagnostics["cost_sensitivity"],
        "selected_rescue_decision": selected,
        "selected_rescue_reason": _selected_reason(selected, diagnostics),
        "rescue_variant_created": rescue_variant_created,
        "rescue_variant_id_or_null": rescue_variant_id,
        "rescue_variant_type_or_null": selected if rescue_variant_created else None,
        "rescue_variant_rules_summary_or_null": rescue_variant_rules,
        "rescue_variant_evaluated_count": rescue_variant_evaluated_count,
        "rescue_variant_train_metrics_or_null": rescue_train_metrics,
        "rescue_variant_validation_metrics_or_null": rescue_validation_metrics,
        "gate_results": gate_results,
        "passed_all_train_validation_gates": passed_all,
        "candidate_promotable_to_oos_review": passed_all,
        "candidate_closed": not passed_all,
        "do_not_retune": True,
        "do_not_loosen_gates": True,
        "oos_allowed_now": False,
        "demo_allowed_now": False,
        "live_allowed_now": False,
        "recommended_next_step": NEXT_IF_PASSED if passed_all else NEXT_IF_FAILED,
        "failure_reasons": failure_reasons,
        "rejected_next_steps": [
            "normal_postmortem_only_without_decision",
            "run_oos_in_v0_84",
            "retune_numeric_thresholds",
            "loosen_validation_gates",
            "broad_parameter_search",
            "parameter_grid",
            "demo_live_or_order_path",
            "resurrect_v0_26",
        ],
        **safety,
        "safety_flags": safety,
    }


def write_xauusd_trading_decision_sprint_v0_84(root: Path, output: str | Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    report = build_xauusd_trading_decision_sprint_v0_84(root=root)
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def select_rescue_decision_from_train_diagnostics(diagnostics: dict[str, Any]) -> str:
    """Select exactly one allowed rescue decision from train-only diagnostics."""
    side = diagnostics.get("side", {})
    long_metrics = side.get("long", {})
    short_metrics = side.get("short", {})
    if _side_clearly_worse(short_metrics, long_metrics):
        return LONG_ONLY
    if _side_clearly_worse(long_metrics, short_metrics):
        return SHORT_ONLY

    session = diagnostics.get("session", {})
    worst_bucket = str(session.get("worst_drawdown_bucket") or "")
    edge = session.get("edge_combined", {})
    core = session.get("ny_core_1300_1600", {})
    if (
        worst_bucket in {"edge_combined", "ny_open_edge_1230_1300", "ny_late_edge_1600_1700", "hour_12", "hour_16"}
        and float(edge.get("expectancy_R", 0.0)) < 0.0
        and float(core.get("expectancy_R", 0.0)) > float(edge.get("expectancy_R", 0.0))
    ):
        return NY_CORE_ONLY

    overtrading = diagnostics.get("overtrading", {})
    if (
        overtrading.get("clear_reentry_cluster_damage") is True
        and float(overtrading.get("cluster_trade_loss_R", 0.0)) < 0.0
    ):
        return REDUCE_OVERTRADING

    return CLOSE_NO_VARIANT


def _evaluate_variant_records(
    m15: list[v83.Candle],
    m5: list[v83.Candle],
    *,
    variant_type: str | None,
    cost_r_per_trade: float,
) -> list[dict[str, Any]]:
    setup_filter = _setup_filter(variant_type)
    displacements = [item for item in v83._find_displacements(m15) if setup_filter(item)]
    m5_by_split = {split: [candle for candle in m5 if candle.split == split] for split in ("train", "validation")}
    records: list[dict[str, Any]] = []
    open_until_by_split = {"train": datetime.min, "validation": datetime.min}
    last_entry_by_split = {"train": datetime.min, "validation": datetime.min}
    for displacement in displacements:
        if displacement.timestamp < open_until_by_split[displacement.split]:
            continue
        future_m5 = [candle for candle in m5_by_split[displacement.split] if displacement.timestamp < candle.timestamp]
        trade = v83._trade_from_displacement(displacement, future_m5, cost_r_per_trade=cost_r_per_trade)
        if trade is None:
            continue
        if variant_type == REDUCE_OVERTRADING:
            entry_timestamp = datetime.fromisoformat(trade.entry_timestamp)
            if (entry_timestamp - last_entry_by_split[trade.split]).total_seconds() < REENTRY_CLUSTER_MINUTES * 60:
                continue
            last_entry_by_split[trade.split] = entry_timestamp
        records.append(v83._trade_record(trade))
        open_until_by_split[displacement.split] = datetime.fromisoformat(trade.exit_timestamp)
    return records


def _setup_filter(variant_type: str | None) -> Callable[[v83.Displacement], bool]:
    if variant_type is None:
        return lambda _: True
    if variant_type == LONG_ONLY:
        return lambda item: item.side == "long"
    if variant_type == SHORT_ONLY:
        return lambda item: item.side == "short"
    if variant_type == NY_CORE_ONLY:
        return lambda item: NY_CORE_START <= item.timestamp.time() < NY_CORE_END
    if variant_type == REDUCE_OVERTRADING:
        return lambda _: True
    return lambda _: False


def _train_only_diagnostics(
    train_trades: list[dict[str, Any]],
    sensitivity_trades: list[dict[str, Any]],
) -> dict[str, Any]:
    train_sensitivity = [trade for trade in sensitivity_trades if trade["split"] == "train"]
    return {
        "side": _side_diagnostics(train_trades),
        "session": _session_diagnostics(train_trades),
        "drawdown": _drawdown_diagnostics(train_trades),
        "consecutive_loss": _consecutive_loss_diagnostics(train_trades),
        "overtrading": _overtrading_diagnostics(train_trades),
        "cost_sensitivity": _train_cost_sensitivity(train_trades, train_sensitivity),
    }


def _side_diagnostics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    total_loss = sum(abs(float(trade["return_R"])) for trade in trades if float(trade["return_R"]) < 0.0)
    result: dict[str, Any] = {}
    for side in ("long", "short"):
        side_trades = [trade for trade in trades if trade["side"] == side]
        metrics = v83._metrics(side_trades)
        loss = sum(abs(float(trade["return_R"])) for trade in side_trades if float(trade["return_R"]) < 0.0)
        result[side] = {**metrics, "loss_R_share": loss / total_loss if total_loss else 0.0}
    return result


def _session_diagnostics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {
        "ny_open_edge_1230_1300": [],
        "ny_core_1300_1600": [],
        "ny_late_edge_1600_1700": [],
    }
    hourly: dict[str, list[dict[str, Any]]] = {}
    for trade in trades:
        entry_time = _entry_dt(trade).time()
        hour_key = f"hour_{_entry_dt(trade).hour:02d}"
        hourly.setdefault(hour_key, []).append(trade)
        if time(12, 30) <= entry_time < NY_CORE_START:
            buckets["ny_open_edge_1230_1300"].append(trade)
        elif NY_CORE_START <= entry_time < NY_CORE_END:
            buckets["ny_core_1300_1600"].append(trade)
        elif NY_CORE_END <= entry_time < time(17, 0):
            buckets["ny_late_edge_1600_1700"].append(trade)
    summary = {name: v83._metrics(items) for name, items in buckets.items()}
    summary["edge_combined"] = v83._metrics(
        buckets["ny_open_edge_1230_1300"] + buckets["ny_late_edge_1600_1700"]
    )
    summary["hourly"] = {name: v83._metrics(items) for name, items in sorted(hourly.items())}
    all_buckets = {**{name: metrics for name, metrics in summary.items() if name != "hourly"}, **summary["hourly"]}
    summary["worst_drawdown_bucket"] = max(
        all_buckets,
        key=lambda name: float(all_buckets[name].get("max_drawdown_R", 0.0)),
    )
    return summary


def _drawdown_diagnostics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    segment = _max_drawdown_segment(trades)
    return {
        "overall_train_max_drawdown_R": v83._metrics(trades)["max_drawdown_R"],
        "max_drawdown_segment": segment,
    }


def _max_drawdown_segment(trades: list[dict[str, Any]]) -> dict[str, Any]:
    equity = 0.0
    peak = 0.0
    peak_index = -1
    worst = {"drawdown_R": 0.0, "start_index": 0, "end_index": -1}
    for index, trade in enumerate(trades):
        equity += float(trade["return_R"])
        if equity > peak:
            peak = equity
            peak_index = index
        drawdown = peak - equity
        if drawdown > worst["drawdown_R"]:
            worst = {"drawdown_R": drawdown, "start_index": peak_index + 1, "end_index": index}
    segment = trades[worst["start_index"] : worst["end_index"] + 1]
    return {
        "drawdown_R": worst["drawdown_R"],
        "trade_count": len(segment),
        "start_entry_timestamp": segment[0]["entry_timestamp"] if segment else None,
        "end_entry_timestamp": segment[-1]["entry_timestamp"] if segment else None,
        "side_counts": dict(Counter(str(trade["side"]) for trade in segment)),
        "entry_hour_counts": dict(Counter(f"{_entry_dt(trade).hour:02d}" for trade in segment)),
        "negative_return_R": sum(float(trade["return_R"]) for trade in segment if float(trade["return_R"]) < 0.0),
    }


def _consecutive_loss_diagnostics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    best: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for trade in trades:
        if float(trade["return_R"]) < 0.0:
            current.append(trade)
            if len(current) > len(best):
                best = list(current)
        else:
            current = []
    return {
        "max_consecutive_losses": len(best),
        "start_entry_timestamp": best[0]["entry_timestamp"] if best else None,
        "end_entry_timestamp": best[-1]["entry_timestamp"] if best else None,
        "side_counts": dict(Counter(str(trade["side"]) for trade in best)),
        "entry_hour_counts": dict(Counter(f"{_entry_dt(trade).hour:02d}" for trade in best)),
        "loss_R": sum(float(trade["return_R"]) for trade in best),
    }


def _overtrading_diagnostics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(trades, key=_entry_dt)
    clustered: list[dict[str, Any]] = []
    previous: datetime | None = None
    for trade in ordered:
        entry = _entry_dt(trade)
        if previous is not None and (entry - previous).total_seconds() <= REENTRY_CLUSTER_MINUTES * 60:
            clustered.append(trade)
        previous = entry
    cluster_loss = sum(float(trade["return_R"]) for trade in clustered)
    share = len(clustered) / len(ordered) if ordered else 0.0
    return {
        "reentry_cluster_minutes": REENTRY_CLUSTER_MINUTES,
        "clustered_trade_count": len(clustered),
        "clustered_trade_share": share,
        "cluster_trade_loss_R": cluster_loss,
        "clear_reentry_cluster_damage": share >= 0.20 and cluster_loss < 0.0,
    }


def _train_cost_sensitivity(
    train_trades: list[dict[str, Any]],
    sensitivity_trades: list[dict[str, Any]],
) -> dict[str, Any]:
    base = v83._metrics(train_trades)
    sensitivity = v83._metrics(sensitivity_trades)
    return {
        "base_cost_R_per_trade": v83.FIXED_EVALUATION_RULES["cost_r_per_trade"],
        "sensitivity_cost_R_per_trade": v83.FIXED_EVALUATION_RULES["cost_sensitivity_cost_r_per_trade"],
        "train_expectancy_R": base["expectancy_R"],
        "train_expectancy_R_after_sensitivity_cost": sensitivity["expectancy_R"],
        "train_expectancy_R_delta": sensitivity["expectancy_R"] - base["expectancy_R"],
        "train_profit_factor_after_sensitivity_cost": sensitivity["profit_factor"],
    }


def _side_clearly_worse(candidate: dict[str, Any], other: dict[str, Any]) -> bool:
    return (
        float(candidate.get("expectancy_R", 0.0)) < 0.0
        and float(candidate.get("loss_R_share", 0.0)) >= 0.60
        and int(candidate.get("max_consecutive_losses", 0)) >= int(other.get("max_consecutive_losses", 0)) + 2
    )


def _variant_rules_summary(variant_type: str) -> dict[str, Any]:
    if variant_type == NY_CORE_ONLY:
        return {
            "variant_type": NY_CORE_ONLY,
            "rule": "Evaluate only fixed v0_82 setups whose M15 displacement timestamp is >=13:00 and <16:00 UTC.",
            "baseline_rules_preserved": True,
            "stop_target_cost_rules_preserved": True,
            "numeric_thresholds_retuned": False,
        }
    if variant_type == LONG_ONLY:
        return {"variant_type": LONG_ONLY, "rule": "Evaluate only long fixed v0_82 setups.", "baseline_rules_preserved": True}
    if variant_type == SHORT_ONLY:
        return {"variant_type": SHORT_ONLY, "rule": "Evaluate only short fixed v0_82 setups.", "baseline_rules_preserved": True}
    if variant_type == REDUCE_OVERTRADING:
        return {
            "variant_type": REDUCE_OVERTRADING,
            "rule": f"Skip a setup if its entry is within {REENTRY_CLUSTER_MINUTES} minutes of the prior variant entry in the same split.",
            "baseline_rules_preserved": True,
        }
    return {}


def _selected_reason(selected: str, diagnostics: dict[str, Any]) -> str:
    if selected == NY_CORE_ONLY:
        worst = diagnostics["session"]["worst_drawdown_bucket"]
        edge = diagnostics["session"]["edge_combined"]
        return (
            f"Train-only diagnostics put the worst drawdown bucket in {worst}; "
            f"edge-window expectancy_R={edge['expectancy_R']} while the 13:00-16:00 core is stronger."
        )
    if selected == CLOSE_NO_VARIANT:
        return "Train-only diagnostics did not show one clear allowed structural failure concentration."
    if selected in {LONG_ONLY, SHORT_ONLY}:
        return "Train-only side diagnostics show one side clearly causing most drawdown/consecutive-loss damage."
    return "Train-only re-entry diagnostics show clear clustered-entry damage."


def _baseline_summary(report: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "candidate_id",
        "evaluation_status",
        "train_trade_count",
        "validation_trade_count",
        "validation_profit_factor",
        "validation_expectancy_R",
        "train_max_drawdown_R",
        "validation_max_drawdown_R",
        "train_max_consecutive_losses",
        "validation_max_consecutive_losses",
        "failure_reasons",
    )
    return {key: report.get(key) for key in keys}


def _blocked_report(baseline: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    safety = _safety_flags()
    return {
        "sprint_version": SPRINT_VERSION,
        "sprint_name": SPRINT_NAME,
        "sprint_status": BLOCKED,
        "source_candidate_id": v83.CANDIDATE_ID,
        "source_design_version": "v0_82",
        "source_evaluation_version": "v0_83",
        "baseline_v0_83_status": baseline.get("evaluation_status"),
        "baseline_v0_83_summary": _baseline_summary(baseline),
        "train_only_diagnostics_available": False,
        "trade_detail_available": False,
        "train_side_diagnostics": {},
        "train_session_diagnostics": {},
        "train_drawdown_diagnostics": {},
        "train_consecutive_loss_diagnostics": {},
        "train_overtrading_diagnostics": {},
        "selected_rescue_decision": CLOSE_NO_VARIANT,
        "selected_rescue_reason": "Required train-only diagnostics or trade reconstruction were unavailable.",
        "rescue_variant_created": False,
        "rescue_variant_id_or_null": None,
        "rescue_variant_type_or_null": None,
        "rescue_variant_rules_summary_or_null": None,
        "rescue_variant_train_metrics_or_null": None,
        "rescue_variant_validation_metrics_or_null": None,
        "gate_results": {},
        "passed_all_train_validation_gates": False,
        "candidate_promotable_to_oos_review": False,
        "candidate_closed": False,
        "do_not_retune": True,
        "do_not_loosen_gates": True,
        "oos_allowed_now": False,
        "demo_allowed_now": False,
        "live_allowed_now": False,
        "recommended_next_step": NEXT_IF_BLOCKED,
        "failure_reasons": reasons,
        "rejected_next_steps": ["run_oos_in_v0_84", "retune_numeric_thresholds", "demo_live_or_order_path"],
        **safety,
        "safety_flags": safety,
    }


def _safety_flags() -> dict[str, bool]:
    return {
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "executable_order_request_created": False,
        "trade_recommendation_output": False,
        "user_facing_buy_sell_signal_output": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "broad_search_performed": False,
        "existing_strategy_rules_modified": False,
        "rejected_candidates_modified": False,
        "v0_26_traded_as_is": False,
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
    }


def _entry_dt(trade: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(str(trade["entry_timestamp"]))


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
