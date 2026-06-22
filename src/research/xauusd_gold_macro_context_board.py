"""Gold macro context board for DXY and oil layers.

This module is a report-only reducer. It reads prior checkpoint reports and
decides the next diagnostic research step without creating strategy rules,
signals, filters, aligned datasets, or execution paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BOARD_VERSION = "v0_71"
REPORT_FILENAME = "xauusd_gold_macro_context_board_v0_71.json"

SOURCE_VERSIONS_CONSIDERED = [
    "v0_65",
    "v0_66",
    "v0_67",
    "v0_68",
    "v0_68_1",
    "v0_69",
    "v0_70",
]

REQUIRED_FALSE_SAFETY_FIELDS = [
    "labels_used_as_trade_blockers",
    "labels_used_for_strategy_testing",
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
    "oos_used",
    "repeated_oos_review",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "executable_candidate_created",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
    "aligned_dataset_created",
    "data_csv_touched",
    "strategy_rules_created",
    "strategy_rules_modified",
    "trade_signals_output",
]


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _report_path(root: Path, filename: str) -> Path:
    return root / "reports" / filename


def _safety_state() -> dict[str, bool]:
    state = {field: False for field in REQUIRED_FALSE_SAFETY_FIELDS}
    state["train_validation_only"] = True
    return state


def _dxy_context_summary(dxy_report: dict[str, Any] | None) -> dict[str, Any]:
    if dxy_report is None:
        return {
            "status": "missing_v0_68_report",
            "selected_proxy_symbol": None,
            "fallback_proxy_symbol": None,
            "event_study_status": None,
            "event_count": 0,
            "clear_lead_count": 0,
            "research_lead_available": False,
            "strategy_board_recommended": False,
        }
    clear_lead_count = int(dxy_report.get("clear_lead_count") or 0)
    return {
        "status": "dxy_context_reviewed",
        "feasibility_status": "dxy_proxy_context_feasibility_completed",
        "selected_proxy_symbol": dxy_report.get("selected_proxy_symbol"),
        "fallback_proxy_symbol": dxy_report.get("secondary_proxy_symbol"),
        "event_study_status": dxy_report.get("study_status"),
        "event_count": dxy_report.get("event_count"),
        "clear_lead_count": clear_lead_count,
        "research_lead_available": clear_lead_count > 0,
        "strategy_board_recommended": False,
        "decision_note": "DXY event study completed with no clear leads, so no DXY-conditioned strategy board is recommended.",
    }


def _oil_context_summary(
    oil_audit: dict[str, Any] | None,
    oil_design: dict[str, Any] | None,
) -> dict[str, Any]:
    if oil_audit is None or oil_design is None:
        return {
            "status": "missing_oil_inputs",
            "audit_present": oil_audit is not None,
            "design_present": oil_design is not None,
            "selected_proxy_symbol": None,
            "fallback_proxy_symbol": None,
            "label_design_status": None,
            "label_count": 0,
            "ready_for_diagnostic_event_study": False,
        }
    selected = oil_design.get("selected_proxy_symbol_or_null")
    fallback = oil_design.get("fallback_proxy_symbol_or_null")
    labels_defined = oil_design.get("labels_defined", [])
    return {
        "status": "oil_context_reviewed",
        "feasibility_status": oil_audit.get("audit_status"),
        "quality_design_status": oil_design.get("design_status"),
        "selected_proxy_symbol": selected,
        "fallback_proxy_symbol": fallback,
        "usable_proxy_symbols": oil_audit.get("usable_proxy_symbols"),
        "quality_scores_by_symbol": oil_design.get("quality_scores_by_symbol"),
        "label_design_status": oil_design.get("design_status"),
        "labels_defined": [
            label.get("label_name") if isinstance(label, dict) else label for label in labels_defined
        ],
        "label_count": oil_design.get("label_count"),
        "ready_for_diagnostic_event_study": bool(selected)
        and oil_design.get("design_status") == "oil_proxy_quality_and_label_design_completed",
    }


def build_gold_macro_context_board(root: Path) -> dict[str, Any]:
    root = root.resolve()
    dxy_report = _read_json(_report_path(root, "xauusd_dxy_conditioned_event_study_v0_68.json"))
    oil_audit = _read_json(_report_path(root, "xauusd_oil_proxy_context_audit_v0_69.json"))
    oil_design = _read_json(_report_path(root, "xauusd_oil_proxy_quality_and_label_design_v0_70.json"))

    missing_inputs = []
    if dxy_report is None:
        missing_inputs.append("reports/xauusd_dxy_conditioned_event_study_v0_68.json")
    if oil_audit is None:
        missing_inputs.append("reports/xauusd_oil_proxy_context_audit_v0_69.json")
    if oil_design is None:
        missing_inputs.append("reports/xauusd_oil_proxy_quality_and_label_design_v0_70.json")

    dxy_summary = _dxy_context_summary(dxy_report)
    oil_summary = _oil_context_summary(oil_audit, oil_design)
    dxy_clear_lead_count = int(dxy_summary.get("clear_lead_count") or 0)
    oil_ready = bool(oil_summary.get("ready_for_diagnostic_event_study"))

    if missing_inputs:
        board_status = "gold_macro_context_board_blocked_missing_inputs"
        next_step = "repair_missing_macro_context_inputs_before_v0_72"
        decision = "blocked_missing_inputs"
        reason = "The board requires the current DXY event-study report plus v0_69/v0_70 oil reports before choosing the next diagnostic step."
    elif oil_ready:
        board_status = "gold_macro_context_board_completed"
        next_step = "v0_72_oil_conditioned_event_study_no_strategy"
        decision = "run_oil_conditioned_event_study_next"
        reason = "DXY has no clear leads, while oil has feasible ranked proxies and descriptive labels ready for a diagnostic event study."
    else:
        board_status = "gold_macro_context_board_completed"
        next_step = "review_oil_inputs_before_yield_real_yield_feasibility"
        decision = "oil_not_ready_review_before_new_context_family"
        reason = "Oil inputs are present but not ready for diagnostic study, so yield/real-yield feasibility should still wait until oil readiness is resolved."

    layers_ready = []
    layers_not_ready = []
    if oil_ready:
        layers_ready.append("oil")
    else:
        layers_not_ready.append("oil")
    if dxy_clear_lead_count > 0:
        layers_ready.append("dxy")
    else:
        layers_not_ready.append("dxy_no_clear_leads")

    report: dict[str, Any] = {
        "board_version": BOARD_VERSION,
        "board_status": board_status,
        "source_versions_considered": SOURCE_VERSIONS_CONSIDERED,
        "missing_inputs": missing_inputs,
        "dxy_context_summary": dxy_summary,
        "oil_context_summary": oil_summary,
        "context_layers_ready_for_diagnostic_study": layers_ready,
        "context_layers_not_ready": layers_not_ready,
        "dxy_clear_lead_count": dxy_clear_lead_count,
        "oil_event_study_completed": False,
        "oil_ready_for_event_study": oil_ready,
        "dxy_alone_gives_research_lead": dxy_clear_lead_count > 0,
        "yield_real_yield_feasibility_should_wait": oil_ready,
        "macro_context_decision": decision,
        "next_research_step": next_step,
        "decision_reason": reason,
        "rejected_next_steps": [
            {
                "step": "dxy_conditioned_strategy_board",
                "reason": "DXY event study produced no clear leads.",
            },
            {
                "step": "new_strategy_creation",
                "reason": "This board is decision/reporting only and does not create strategy logic.",
            },
            {
                "step": "oos_review",
                "reason": "The macro context board is train/validation-only research infrastructure.",
            },
            {
                "step": "live_or_demo_execution",
                "reason": "Execution remains outside this research-only board.",
            },
            {
                "step": "yield_real_yield_feasibility_next",
                "reason": "Yield/real-yield can wait until the oil-conditioned diagnostic event study is attempted, unless oil inputs are missing.",
            },
        ],
    }
    report.update(_safety_state())
    return report


def write_gold_macro_context_board(root: Path, output_path: Path | None = None) -> dict[str, Any]:
    report = build_gold_macro_context_board(root)
    destination = output_path or root.resolve() / "reports" / REPORT_FILENAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
