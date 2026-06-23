"""Master trading path re-entry board for XAUUSD research."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BOARD_VERSION = "v0_81"
COMPLETED_STATUS = "master_trading_path_reentry_completed"
BLOCKED_STATUS = "master_trading_path_reentry_blocked"
RECOMMENDED_NEXT_STEP = "v0_82_executable_fixed_rule_candidate_design_no_oos"

SOURCE_REPORTS: dict[str, str] = {
    "v0_68": "xauusd_dxy_conditioned_event_study_v0_68.json",
    "v0_71": "xauusd_gold_macro_context_board_v0_71.json",
    "v0_72": "xauusd_oil_conditioned_event_study_v0_72.json",
    "v0_73": "xauusd_yield_context_feasibility_v0_73.json",
    "v0_80": "xauusd_external_yield_context_readiness_board_v0_80.json",
}

FALSE_SAFETY_FIELDS = (
    "external_api_called",
    "external_data_downloaded",
    "dataset_file_created",
    "market_csv_created",
    "data_csv_touched",
    "real_xauusd_data_used_for_new_test",
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
    "strategy_rules_modified",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
)

V0_82_REQUIREMENTS = [
    "explicit_direction_side_mapping",
    "entry_condition",
    "invalidation_stop_concept",
    "target_exit_concept",
    "train_validation_evaluation_plan",
    "cost_spread_policy",
    "minimum_trade_count_gate",
    "no_oos_until_train_validation_passes",
    "no_demo_until_oos_passes",
]

V0_82_FORBIDDEN_ACTIONS = [
    "oos_review",
    "demo_live_execution",
    "order_send",
    "order_check",
    "trade_recommendation_output",
    "retune_rejected_candidates",
    "threshold_search",
    "parameter_grid",
    "data_csv_modification",
    "external_api_download",
    "context_label_trade_filter_approval",
]


def _read_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_source_reports(root: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    reports_dir = root / "reports"
    reports: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for version, filename in SOURCE_REPORTS.items():
        path = reports_dir / filename
        if path.exists():
            reports[version] = _read_report(path)
        else:
            missing.append(filename)
    return reports, missing


def _context_layers_summary(reports: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    dxy = reports.get("v0_68", {})
    oil = reports.get("v0_72", {})
    yield_feasibility = reports.get("v0_73", {})
    yield_readiness = reports.get("v0_80", {})
    return {
        "dxy": {
            "source_version": dxy.get("study_version", "v0_68"),
            "status": dxy.get("study_status"),
            "clear_lead_count": dxy.get("clear_lead_count"),
            "standalone_context_lead_available": dxy.get("clear_lead_count") not in {None, 0},
            "strategy_or_trade_filter_approved": False,
        },
        "oil": {
            "source_version": oil.get("study_version", "v0_72"),
            "status": oil.get("study_status"),
            "clear_lead_count": oil.get("clear_lead_count"),
            "standalone_context_lead_available": oil.get("clear_lead_count") not in {None, 0},
            "strategy_or_trade_filter_approved": False,
        },
        "yield": {
            "source_versions": ["v0_73", "v0_80"],
            "local_proxy_status": yield_feasibility.get("audit_status"),
            "local_yield_proxy_available": yield_feasibility.get("local_yield_proxy_available"),
            "readiness_status": yield_readiness.get("readiness_status"),
            "readiness_decision": yield_readiness.get("readiness_decision"),
            "ready_for_future_human_sample_preflight": (
                yield_readiness.get("readiness_decision") == "ready_for_human_supplied_external_yield_sample_preflight"
            ),
            "standalone_context_lead_available": False,
            "strategy_or_trade_filter_approved": False,
        },
    }


def _prior_strategy_state_summary() -> dict[str, Any]:
    return {
        "historical_v0_26_oos_research_validation_exists": True,
        "v0_26_execution_path_closed": True,
        "v0_47_direction_board_passed": False,
        "v0_48_new_directional_candidate_passed": False,
        "v0_51_expanded_retest_promoted_candidate": False,
        "v0_53_external_shortlist_candidate_passed": False,
        "v0_56_session_block_candidate_passed": False,
        "v0_60_second_tier_candidate_passed": False,
        "v0_63_context_labeled_event_study_clear_leads": False,
        "current_train_validation_passed_executable_candidate": False,
        "rejected_candidates_must_not_be_retuned": True,
    }


def _safety_flags() -> dict[str, bool]:
    flags = {field: False for field in FALSE_SAFETY_FIELDS}
    flags["train_validation_only"] = True
    return flags


def _required_sources_safe(reports: dict[str, dict[str, Any]]) -> bool:
    unsafe_fields = (
        "external_api_called",
        "external_data_downloaded",
        "dataset_file_created",
        "market_csv_created",
        "data_csv_touched",
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
        "strategy_rules_modified",
    )
    for report in reports.values():
        if any(report.get(field) is True for field in unsafe_fields):
            return False
        if report.get("train_validation_only", True) is not True:
            return False
    return True


def build_master_trading_path_reentry_board(root: Path) -> dict[str, Any]:
    reports, missing = _load_source_reports(root)
    context_summary = _context_layers_summary(reports)
    no_context_lead = all(
        layer.get("standalone_context_lead_available") is False for layer in context_summary.values()
    )
    source_safe = _required_sources_safe(reports)
    board_complete = not missing and no_context_lead and source_safe

    board_status = COMPLETED_STATUS if board_complete else BLOCKED_STATUS
    recommended_primary_path = (
        "design_one_fixed_rule_executable_candidate_without_oos"
        if board_complete
        else "repair_missing_or_unsafe_source_context_before_reentry"
    )
    recommended_next_step = RECOMMENDED_NEXT_STEP if board_complete else "repair_v0_81_source_inputs"

    safety = _safety_flags()
    report: dict[str, Any] = {
        "board_version": BOARD_VERSION,
        "board_status": board_status,
        "context_infrastructure_status": "complete_but_not_primary_path_for_next_step"
        if board_complete
        else "blocked_pending_source_repair",
        "context_layers_summary": context_summary,
        "rejected_paths": [
            "continue_dxy_expansion_without_critical_blocker",
            "continue_oil_expansion_without_critical_blocker",
            "continue_yield_context_expansion_without_critical_blocker",
            "trade_v0_26_as_is",
            "retune_rejected_candidates",
            "run_oos_without_current_train_validation_passed_executable_candidate",
            "demo_or_live_execution",
        ],
        "prior_strategy_state_summary": _prior_strategy_state_summary(),
        "v0_26_tradeability_status": {
            "candidate_id": "xauusd_compression_then_expansion_v0_26",
            "tradeable_as_is": False,
            "reason": "execution audit found no reliable executable direction or side mapping",
            "direction_side_mapping_resolved": False,
            "recommended_for_trading": False,
        },
        "current_executable_candidate_available": False,
        "current_executable_candidate_id_or_null": None,
        "oos_allowed_now": False,
        "demo_allowed_now": False,
        "live_allowed_now": False,
        "strategy_testing_allowed_now": False,
        "recommended_primary_path": recommended_primary_path,
        "recommended_next_step": recommended_next_step,
        "reason_for_reentry": (
            "The context-infrastructure detour has reached a safe stopping point: DXY and oil produced no clear "
            "standalone leads, yield context is ready only for a future human-supplied sample preflight, and the "
            "project still lacks a current executable fixed-rule candidate."
        ),
        "reason_not_continue_context_expansion": (
            "No critical blocker requires more DXY, oil, or yield infrastructure before returning to the main "
            "trading path; additional context work would not resolve the missing executable direction/side mapping."
        ),
        "v0_82_requirements": V0_82_REQUIREMENTS,
        "v0_82_forbidden_actions": V0_82_FORBIDDEN_ACTIONS,
        "missing_source_reports": missing,
        "source_versions_considered": list(SOURCE_REPORTS),
        "source_safety_closed": source_safe,
        "safety_flags": safety,
        "real_xauusd_data_used_for_new_test": False,
        **safety,
    }
    return report


def write_master_trading_path_reentry_board(root: Path) -> dict[str, Any]:
    report = build_master_trading_path_reentry_board(root)
    output_path = root / "reports" / "xauusd_master_trading_path_reentry_board_v0_81.json"
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
