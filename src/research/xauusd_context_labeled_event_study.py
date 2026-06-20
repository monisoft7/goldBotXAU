"""v0_63 context-labeled retrospective event study for prior XAUUSD outcomes.

This module labels historical train/validation outcomes with the fixed v0_62
timestamp-only context labels. It does not change strategy rules, optimize
labels, create a candidate, run OOS, or create any execution surface.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_m15_csvs
from src.research import xauusd_external_shortlist_train_validation_board as v53
from src.research import xauusd_second_tier_fixed_rule_board as v60
from src.research import xauusd_session_block_directional_bias_evaluation as v56
from src.research.xauusd_market_context_labeler import TIMESTAMP_ONLY_LABELS, _labels_for_timestamp

CONTEXT_STUDY_VERSION = "v0_63"
SOURCE_LABELER_VERSION = "v0_62"
SOURCE_PRIOR_VERSIONS = ["v0_53", "v0_56", "v0_60"]
DEFAULT_OUTPUT = Path("reports") / "xauusd_context_labeled_event_study_v0_63.json"
DEFAULT_LABEL_REPORT = Path("reports") / "xauusd_market_context_labels_v0_62.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"
DEFAULT_V0_53_REPORT = Path("reports") / "xauusd_external_shortlist_board_v0_53.json"
DEFAULT_V0_56_REPORT = Path("reports") / "xauusd_session_block_bias_eval_v0_56.json"
DEFAULT_V0_60_REPORT = Path("reports") / "xauusd_second_tier_board_v0_60.json"
DEFAULT_V0_55_REPORT = Path("reports") / "xauusd_session_volatility_design_v0_55.json"

COMPLETED_WITH_LEADS = "context_labeled_event_study_completed_with_leads"
COMPLETED_NO_CLEAR_LEADS = "context_labeled_event_study_completed_no_clear_leads"
BLOCKED_MISSING_V0_62_LABELS = "blocked_missing_v0_62_labels"
FAILED = "context_study_failed"

CANDIDATES_TO_ANALYZE = [
    "asian_range_london_breakout_confirmation",
    "ny_liquidity_sweep_reversal",
    "prior_day_liquidity_sweep_reversal",
    "failed_m15_swing_breakout_reversal",
    "sequential_m5_move_mean_reversion",
    "session_block_directional_bias_candidate",
]

CONTEXT_LABELS_TO_ATTACH = [
    "asian_session",
    "london_morning_session",
    "ny_core_session",
    "late_us_session",
    "off_session_or_low_activity",
    "session_transition_asian_to_london",
    "session_transition_london_to_ny",
    "friday_late_session",
    "monday_reopen_window",
    "likely_market_open",
    "market_closed_weekend",
]


def build_xauusd_context_labeled_event_study_v0_63(
    *,
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST,
    label_report_path: str | Path = DEFAULT_LABEL_REPORT,
    source_v0_53_path: str | Path = DEFAULT_V0_53_REPORT,
    source_v0_56_path: str | Path = DEFAULT_V0_56_REPORT,
    source_v0_60_path: str | Path = DEFAULT_V0_60_REPORT,
    source_v0_55_path: str | Path = DEFAULT_V0_55_REPORT,
    candidate_event_records: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Build the retrospective context-labeled event study."""
    try:
        label_report = _read_json(Path(label_report_path))
        label_blockers = _label_report_blockers(label_report)
        if label_blockers:
            return _base_report(
                context_study_status=BLOCKED_MISSING_V0_62_LABELS,
                source_label_report=label_report,
                candidate_results_by_context={},
                strongest_context_conditioned_leads=[],
                weak_or_unstable_contexts=[],
                source_rejection_state={},
                source_recompute_summary={},
                blockers=label_blockers,
                warnings=[],
                next_recommended_step="restore reports/xauusd_market_context_labels_v0_62.json before v0_63 event study",
            )

        source_reports = {
            "v0_53": _read_json(Path(source_v0_53_path)),
            "v0_56": _read_json(Path(source_v0_56_path)),
            "v0_60": _read_json(Path(source_v0_60_path)),
        }
        source_rejection_state = _source_rejection_state(source_reports)
        source_blockers = _source_blockers(source_reports, source_rejection_state)
        if candidate_event_records is None:
            candidate_event_records = _recompute_candidate_events(
                data_dir=Path(data_dir),
                manifest_path=Path(manifest_path),
                source_v0_55_path=Path(source_v0_55_path),
            )

        candidate_results_by_context = {
            candidate_id: _candidate_context_results(candidate_id, candidate_event_records.get(candidate_id, []))
            for candidate_id in CANDIDATES_TO_ANALYZE
        }
        all_context_results = [
            result
            for candidate_results in candidate_results_by_context.values()
            for result in candidate_results.values()
        ]
        leads = sorted(
            [result for result in all_context_results if _is_context_lead(result)],
            key=_lead_sort_key,
            reverse=True,
        )
        weak_or_unstable = [
            _weak_context_note(result)
            for result in all_context_results
            if not _is_context_lead(result) and (
                result["trade_count_validation"] > 0 or result["trade_count_train"] > 0
            )
        ][:20]
        status = COMPLETED_WITH_LEADS if leads else COMPLETED_NO_CLEAR_LEADS
        recommended_plan = (
            "fixed context-gated candidate design for top one lead only, no OOS."
            if leads
            else "add external datasets such as holiday/economic calendar/DXY before further context testing."
        )
        warnings = [
            "retrospective_event_study_only_not_strategy",
            "labels_attached_after_fixed_prior_outcomes_not_used_as_trade_blockers",
            "all_source_prior_branches_preserved_as_rejected_do_not_retune",
        ]
        if source_blockers:
            warnings.extend(source_blockers)

        return _base_report(
            context_study_status=status,
            source_label_report=label_report,
            candidate_results_by_context=candidate_results_by_context,
            strongest_context_conditioned_leads=[_lead_summary(lead) for lead in leads],
            weak_or_unstable_contexts=weak_or_unstable,
            source_rejection_state=source_rejection_state,
            source_recompute_summary={
                candidate_id: {
                    "trade_count_train": sum(1 for trade in records if trade.get("split") == "train"),
                    "trade_count_validation": sum(1 for trade in records if trade.get("split") == "validation"),
                }
                for candidate_id, records in candidate_event_records.items()
            },
            blockers=[],
            warnings=warnings,
            next_recommended_step=recommended_plan,
        )
    except Exception as exc:
        return _base_report(
            context_study_status=FAILED,
            source_label_report=None,
            candidate_results_by_context={},
            strongest_context_conditioned_leads=[],
            weak_or_unstable_contexts=[],
            source_rejection_state={},
            source_recompute_summary={},
            blockers=[f"context_study_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair v0_63 event study implementation or input artifacts before continuing",
        )


def save_xauusd_context_labeled_event_study(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _recompute_candidate_events(
    *,
    data_dir: Path,
    manifest_path: Path,
    source_v0_55_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    manifest = _read_json(manifest_path)
    if manifest is None:
        raise ValueError("dataset_manifest_missing_or_invalid")

    m15_load = load_xauusd_m15_csvs(data_dir=data_dir, pattern="xauusd_m15_*.csv")
    m5_load = load_xauusd_m15_csvs(data_dir=data_dir, pattern="xauusd_m5_xauusd_2023-01-01_2025-12-31.csv")
    m15_v53, _ = v53._split_candles(m15_load.records, manifest)
    m15_v60, _ = v60._split_candles(m15_load.records, manifest)
    m5_v60, _ = v60._split_candles(m5_load.records, manifest)
    m15_v56, _ = v56._split_candles(m15_load.records, manifest)
    events: dict[str, list[dict[str, Any]]] = {}

    for candidate_id in (
        "prior_day_liquidity_sweep_reversal",
        "asian_range_london_breakout_confirmation",
    ):
        trades = v53._rules()[candidate_id]([candle for candle in m15_v53 if candle.split in {"train", "validation"}])
        events[candidate_id] = [v53._trade_record(trade) for trade in trades]

    for candidate_id, candles in (
        ("failed_m15_swing_breakout_reversal", m15_v60),
        ("ny_liquidity_sweep_reversal", m15_v60),
        ("sequential_m5_move_mean_reversion", m5_v60),
    ):
        trades = v60._rules()[candidate_id]([candle for candle in candles if candle.split in {"train", "validation"}])
        events[candidate_id] = [v60._trade_record(trade) for trade in trades]

    source_design = _read_json(source_v0_55_path)
    selected_design = v56._selected_design(source_design)
    source_blockers = v56._source_design_blockers(source_design, selected_design)
    events["session_block_directional_bias_candidate"] = (
        []
        if source_blockers
        else v56._session_block_trades([candle for candle in m15_v56 if candle.split in {"train", "validation"}])
    )
    return events


def _candidate_context_results(candidate_id: str, trades: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    labeled_trades = [_with_context_labels(trade) for trade in trades]
    return {
        label: _context_result(candidate_id, label, [trade for trade in labeled_trades if label in trade["context_labels"]])
        for label in CONTEXT_LABELS_TO_ATTACH
    }


def _context_result(candidate_id: str, label: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    train = [trade for trade in trades if trade.get("split") == "train"]
    validation = [trade for trade in trades if trade.get("split") == "validation"]
    train_metrics = _metrics(train)
    validation_metrics = _metrics(validation)
    concentration = _concentration_risk(validation)
    sample_sufficiency = _sample_sufficiency(train_metrics["trades"], validation_metrics["trades"])
    consistency = _train_validation_consistency(train_metrics, validation_metrics)
    return {
        "candidate_id": candidate_id,
        "context_label": label,
        "trade_count_train": train_metrics["trades"],
        "trade_count_validation": validation_metrics["trades"],
        "train_profit_factor": train_metrics["profit_factor"],
        "validation_profit_factor": validation_metrics["profit_factor"],
        "train_expectancy": train_metrics["expectancy_r"],
        "validation_expectancy": validation_metrics["expectancy_r"],
        "max_consecutive_losses": {
            "train": train_metrics["max_consecutive_losses"],
            "validation": validation_metrics["max_consecutive_losses"],
        },
        "sample_sufficiency": sample_sufficiency,
        "train_validation_consistency": consistency,
        "context_concentration_risk": concentration,
        "interpretive_note": _interpretive_note(sample_sufficiency, consistency, concentration),
    }


def _with_context_labels(trade: dict[str, Any]) -> dict[str, Any]:
    timestamp = _parse_timestamp(str(trade["entry_timestamp"]))
    enriched = dict(trade)
    enriched["context_labels"] = [label for label in _labels_for_timestamp(timestamp) if label in CONTEXT_LABELS_TO_ATTACH]
    enriched["entry_year"] = timestamp.strftime("%Y")
    enriched["entry_month"] = timestamp.strftime("%Y-%m")
    return enriched


def _metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(trade.get("return_r", 0.0)) for trade in trades]
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
        "profit_factor": profit_factor,
        "expectancy_r": sum(returns) / len(returns) if returns else 0.0,
        "max_consecutive_losses": _max_consecutive_losses(returns),
    }


def _sample_sufficiency(train_count: int, validation_count: int) -> str:
    if validation_count < 25:
        return "insufficient_validation_sample"
    if train_count < 25:
        return "insufficient_train_sample"
    return "sufficient_for_context_lead_screen"


def _train_validation_consistency(train: dict[str, Any], validation: dict[str, Any]) -> str:
    train_expectancy = float(train["expectancy_r"])
    validation_expectancy = float(validation["expectancy_r"])
    validation_pf = _pf_value(validation["profit_factor"])
    train_pf = _pf_value(train["profit_factor"])
    if train_expectancy > 0.0 and validation_expectancy > 0.0 and validation_pf >= 1.15 and train_pf >= 0.75:
        return "consistent_positive_train_validation"
    if train_expectancy <= 0.0 < validation_expectancy:
        return "validation_positive_train_weak"
    if train_expectancy > 0.0 >= validation_expectancy:
        return "train_positive_validation_weak"
    return "weak_or_negative_train_validation"


def _concentration_risk(validation_trades: list[dict[str, Any]]) -> dict[str, Any]:
    month_share = _max_share(validation_trades, "entry_month")
    year_share = _max_share(validation_trades, "entry_year")
    reasons: list[str] = []
    if month_share > 0.35:
        reasons.append("validation_trades_concentrated_in_single_month")
    if year_share > 0.75:
        reasons.append("validation_trades_concentrated_in_single_year")
    return {
        "risk_level": "high" if reasons else "low",
        "risk_present": bool(reasons),
        "reasons": reasons,
        "validation_month_max_share": month_share,
        "validation_year_max_share": year_share,
    }


def _interpretive_note(sample_sufficiency: str, consistency: str, concentration: dict[str, Any]) -> str:
    if sample_sufficiency != "sufficient_for_context_lead_screen":
        return "context slice is descriptive only because sample is insufficient for lead screening"
    if concentration["risk_present"]:
        return "context slice has enough trades but concentration risk blocks a clear lead"
    if consistency == "consistent_positive_train_validation":
        return "context slice is a fixed-label retrospective lead only, not an executable candidate"
    return "context slice does not show consistent train/validation strength"


def _is_context_lead(result: dict[str, Any]) -> bool:
    return (
        result["sample_sufficiency"] == "sufficient_for_context_lead_screen"
        and result["train_validation_consistency"] == "consistent_positive_train_validation"
        and result["context_concentration_risk"]["risk_present"] is False
    )


def _lead_sort_key(result: dict[str, Any]) -> tuple[float, float, int, float]:
    return (
        _pf_value(result["validation_profit_factor"]),
        float(result["validation_expectancy"]),
        int(result["trade_count_validation"]),
        _pf_value(result["train_profit_factor"]),
    )


def _lead_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": result["candidate_id"],
        "context_label": result["context_label"],
        "trade_count_train": result["trade_count_train"],
        "trade_count_validation": result["trade_count_validation"],
        "train_profit_factor": result["train_profit_factor"],
        "validation_profit_factor": result["validation_profit_factor"],
        "train_expectancy": result["train_expectancy"],
        "validation_expectancy": result["validation_expectancy"],
        "lead_scope": "retrospective_context_conditioned_research_lead_only",
    }


def _weak_context_note(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": result["candidate_id"],
        "context_label": result["context_label"],
        "sample_sufficiency": result["sample_sufficiency"],
        "train_validation_consistency": result["train_validation_consistency"],
        "context_concentration_risk": result["context_concentration_risk"]["risk_level"],
        "interpretive_note": result["interpretive_note"],
    }


def _base_report(
    *,
    context_study_status: str,
    source_label_report: dict[str, Any] | None,
    candidate_results_by_context: dict[str, Any],
    strongest_context_conditioned_leads: list[dict[str, Any]],
    weak_or_unstable_contexts: list[dict[str, Any]],
    source_rejection_state: dict[str, Any],
    source_recompute_summary: dict[str, Any],
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    return {
        "context_study_version": CONTEXT_STUDY_VERSION,
        "context_study_status": context_study_status,
        "source_labeler_version": SOURCE_LABELER_VERSION,
        "source_labeler_status": source_label_report.get("labeler_status") if isinstance(source_label_report, dict) else None,
        "source_prior_versions_considered": list(SOURCE_PRIOR_VERSIONS),
        "labels_considered": list(CONTEXT_LABELS_TO_ATTACH),
        "labels_used_as_trade_blockers": False,
        "strategy_rules_changed": False,
        "gates_lowered": False,
        "candidate_results_by_context": candidate_results_by_context,
        "strongest_context_conditioned_leads": strongest_context_conditioned_leads,
        "weak_or_unstable_contexts": weak_or_unstable_contexts,
        "source_rejection_state": source_rejection_state,
        "source_recompute_summary": source_recompute_summary,
        "revived_candidate_allowed": False,
        "approved_for_strategy_testing": False,
        "approved_for_trade_filtering": False,
        "recommended_v0_64_plan": next_recommended_step,
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
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def _source_rejection_state(source_reports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    v0_53 = source_reports.get("v0_53") or {}
    v0_56 = source_reports.get("v0_56") or {}
    v0_60 = source_reports.get("v0_60") or {}
    return {
        "v0_53_rejected_do_not_retune_candidates": v0_53.get("rejected_do_not_retune_candidates", []),
        "v0_56_rejected_do_not_retune": v0_56.get("rejected_do_not_retune"),
        "v0_60_rejected_do_not_retune_candidates": v0_60.get("rejected_do_not_retune_candidates", []),
        "all_requested_prior_branches_remain_rejected_do_not_retune": (
            "asian_range_london_breakout_confirmation" in v0_53.get("rejected_do_not_retune_candidates", [])
            and "prior_day_liquidity_sweep_reversal" in v0_53.get("rejected_do_not_retune_candidates", [])
            and v0_56.get("rejected_do_not_retune") is True
            and all(
                candidate in v0_60.get("rejected_do_not_retune_candidates", [])
                for candidate in (
                    "failed_m15_swing_breakout_reversal",
                    "ny_liquidity_sweep_reversal",
                    "sequential_m5_move_mean_reversion",
                )
            )
        ),
    }


def _source_blockers(
    source_reports: dict[str, dict[str, Any] | None],
    source_rejection_state: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    for version, report in source_reports.items():
        if report is None:
            blockers.append(f"source_{version}_report_missing_or_invalid")
    if source_rejection_state.get("all_requested_prior_branches_remain_rejected_do_not_retune") is not True:
        blockers.append("source_rejected_do_not_retune_state_not_fully_confirmed")
    return blockers


def _label_report_blockers(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return ["source_v0_62_label_report_missing_or_invalid"]
    blockers: list[str] = []
    if report.get("labeler_version") != SOURCE_LABELER_VERSION:
        blockers.append("source_v0_62_labeler_version_mismatch")
    if report.get("labeler_status") != "market_context_labeler_completed":
        blockers.append("source_v0_62_labeler_not_completed")
    if report.get("labels_are_trade_blockers") is not False:
        blockers.append("source_v0_62_labels_trade_blocker_state_invalid")
    available = set(report.get("timestamp_only_labels", []))
    missing = sorted(set(CONTEXT_LABELS_TO_ATTACH).difference(available))
    if missing:
        blockers.append(f"source_v0_62_missing_required_labels:{','.join(missing)}")
    return blockers


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


def _max_share(trades: list[dict[str, Any]], key: str) -> float:
    if not trades:
        return 0.0
    counts = Counter(str(trade.get(key)) for trade in trades)
    return max(counts.values()) / len(trades)


def _pf_value(value: Any) -> float:
    if value == "inf":
        return float("inf")
    return float(value or 0.0)


def _parse_timestamp(value: str) -> datetime:
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
        "retrospective_event_study_only": True,
        "labels_used_as_trade_blockers": False,
        "strategy_rules_changed": False,
        "gates_lowered": False,
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
        "profitability_claimed": False,
        "data_csv_added_to_git": False,
    }
