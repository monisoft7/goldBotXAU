"""v0_30 post-OOS governance and paper-shadow protocol design."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GOVERNANCE_VERSION = "v0_30"
CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"
SOURCE_OOS_REVIEW_VERSION = "v0_29"
SOURCE_OOS_DECISION = "oos_passed_research_validation"
DEFAULT_MARKER = Path("reports") / "xauusd_oos_review_v0_29.marker.json"
DEFAULT_REPAIR_REPORT = Path("reports") / "xauusd_oos_review_repair_v0_29_1.json"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_post_oos_governance_v0_30.json"

NEXT_RECOMMENDED_STEP = "v0_31 build read-only paper-shadow journal simulator, no execution"


def build_xauusd_post_oos_governance_v0_30(
    *,
    marker_path: str | Path = DEFAULT_MARKER,
    repair_report_path: str | Path = DEFAULT_REPAIR_REPORT,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
) -> dict[str, Any]:
    marker_file = Path(marker_path)
    repair_file = Path(repair_report_path)
    candidate_file = Path(candidate_report_path)

    marker, marker_errors = _read_json_object(marker_file, "oos_marker")
    repair_report, repair_errors = _read_json_object(repair_file, "oos_repair_report")
    candidate_report, candidate_errors = _read_json_object(candidate_file, "candidate_report")

    blockers = [*marker_errors, *repair_errors, *candidate_errors]
    if marker is not None:
        blockers.extend(_marker_blockers(marker))
    if repair_report is not None:
        blockers.extend(_repair_blockers(repair_report))
    if candidate_report is not None:
        blockers.extend(_candidate_blockers(candidate_report))

    source_decision = marker.get("decision") if marker else None
    repeat_allowed = marker.get("repeat_review_allowed") if marker else None
    detailed_metrics_available = _detailed_metrics_available(repair_report)
    candidate_rules = candidate_report.get("fixed_rules", {}) if candidate_report else {}

    governance_status = (
        "post_oos_governance_created_design_only"
        if not blockers
        else "blocked_post_oos_governance_prerequisites_not_met"
    )

    return {
        "governance_version": GOVERNANCE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "source_reports": {
            "oos_marker": str(marker_file),
            "oos_repair_report": str(repair_file),
            "candidate_report": str(candidate_file),
        },
        "source_oos_review_version": SOURCE_OOS_REVIEW_VERSION,
        "source_oos_marker_decision": source_decision,
        "detailed_oos_metrics_available": False,
        "detailed_oos_metrics_confirmed_unavailable": detailed_metrics_available is False,
        "repeat_oos_review_allowed": False,
        "repeat_oos_review_allowed_source_value": repeat_allowed,
        "one_time_oos_review_completed": not blockers and source_decision == SOURCE_OOS_DECISION,
        "governance_status": governance_status,
        "blockers": blockers,
        "paper_shadow_protocol_status": "design_only_not_started",
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "candidate_rules_lock": {
            "candidate_rules_modified": False,
            "rule_change_allowed": False,
            "threshold_search_allowed": False,
            "parameter_grid_allowed": False,
            "parameter_optimization_allowed": False,
            "retune_allowed": False,
            "fixed_rules_hash_sha256": _stable_hash(candidate_rules) if candidate_rules else None,
            "fixed_rules_source": str(candidate_file),
        },
        "post_oos_robustness_checklist": _post_oos_robustness_checklist(),
        "future_paper_shadow_prerequisites": _future_paper_shadow_prerequisites(),
        "future_paper_shadow_pass_fail_criteria": _future_paper_shadow_pass_fail_criteria(),
        "non_actions_performed": {
            "new_oos_run_performed": False,
            "new_data_evaluated": False,
            "candidate_rules_changed": False,
            "new_variant_created_from_oos_result": False,
            "paper_shadow_observation_started": False,
            "journal_simulator_built": False,
        },
        "safety": _safety_summary(),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


def save_xauusd_post_oos_governance_report(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json_object(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_missing: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{label}_invalid_json: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{label}_not_object: {path}"]
    return payload, []


def _marker_blockers(marker: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if marker.get("review_version") != SOURCE_OOS_REVIEW_VERSION:
        blockers.append("oos_marker_review_version_unexpected")
    if marker.get("candidate_id") != CANDIDATE_ID:
        blockers.append("oos_marker_candidate_id_mismatch")
    if marker.get("decision") != SOURCE_OOS_DECISION:
        blockers.append("oos_marker_decision_not_completed_passed_research_validation")
    if marker.get("repeat_review_allowed") is not False:
        blockers.append("oos_marker_repeat_review_allowed_not_false")
    return blockers


def _repair_blockers(repair_report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if repair_report.get("repair_version") != "v0_29_1":
        blockers.append("oos_repair_report_version_unexpected")
    if repair_report.get("marker_decision_preserved") != SOURCE_OOS_DECISION:
        blockers.append("oos_repair_marker_decision_not_preserved")
    if repair_report.get("repeat_review_allowed") is not False:
        blockers.append("oos_repair_repeat_review_allowed_not_false")
    if _detailed_metrics_available(repair_report) is not False:
        blockers.append("detailed_oos_metrics_unavailability_not_confirmed")
    safety = repair_report.get("safety", {})
    if not isinstance(safety, dict) or safety.get("one_time_oos_review_completed") is not True:
        blockers.append("one_time_oos_review_not_completed")
    return blockers


def _candidate_blockers(candidate_report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if candidate_report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("candidate_report_candidate_id_mismatch")
    fixed_rules = candidate_report.get("fixed_rules")
    if not isinstance(fixed_rules, dict):
        blockers.append("candidate_fixed_rules_missing")
    else:
        if fixed_rules.get("threshold_search_used") is not False:
            blockers.append("candidate_rules_threshold_search_not_false")
        if fixed_rules.get("parameter_grid_used") is not False:
            blockers.append("candidate_rules_parameter_grid_not_false")
        if fixed_rules.get("retuning_used") is not False:
            blockers.append("candidate_rules_retuning_not_false")
    nested_candidate = candidate_report.get("candidate")
    nested_research_only = nested_candidate.get("research_only") if isinstance(nested_candidate, dict) else None
    if candidate_report.get("research_only", nested_research_only) is not True:
        blockers.append("candidate_report_research_only_not_true")
    return blockers


def _detailed_metrics_available(repair_report: dict[str, Any] | None) -> bool | None:
    if repair_report is None:
        return None
    if repair_report.get("detailed_oos_metrics_available") is not False:
        return repair_report.get("detailed_oos_metrics_available")
    restored = repair_report.get("restored_main_report")
    if isinstance(restored, dict) and restored.get("oos_result") is not None:
        return True
    return False


def _post_oos_robustness_checklist() -> list[dict[str, Any]]:
    return [
        {
            "check": "one_time_oos_marker_present_and_locked",
            "required": True,
            "status": "required_before_any_future_observation",
        },
        {
            "check": "repeat_oos_review_disallowed",
            "required": True,
            "status": "required_before_any_future_observation",
        },
        {
            "check": "detailed_oos_metrics_treated_as_unavailable",
            "required": True,
            "status": "active_governance_constraint",
        },
        {
            "check": "candidate_rules_remain_locked",
            "required": True,
            "status": "active_governance_constraint",
        },
        {
            "check": "no_rule_change_from_oos_result",
            "required": True,
            "status": "active_governance_constraint",
        },
        {
            "check": "no_new_data_evaluation_in_v0_30",
            "required": True,
            "status": "satisfied_by_design",
        },
        {
            "check": "no_execution_path_created",
            "required": True,
            "status": "satisfied_by_design",
        },
        {
            "check": "manual_review_required_before_future_phase",
            "required": True,
            "status": "required_before_any_future_observation",
        },
    ]


def _future_paper_shadow_prerequisites() -> dict[str, Any]:
    return {
        "locked_candidate_rules": True,
        "read_only_market_data": True,
        "no_order_path": True,
        "journal_only_observations": True,
        "risk_notes_only": True,
        "manual_review_required": True,
        "no_trade_recommendation_output": True,
        "no_directional_instruction_output": True,
        "no_retune": True,
        "no_threshold_search": True,
        "no_parameter_grid": True,
        "no_parameter_optimization": True,
        "no_new_variant_from_oos_result": True,
    }


def _future_paper_shadow_pass_fail_criteria() -> dict[str, Any]:
    return {
        "phase_status": "not_started",
        "pass_requires_all": [
            "candidate rules hash matches the locked v0_26 source before and after journal generation",
            "market data source is read-only and cannot write, route, or submit anything",
            "every journal row is observation-only and contains no recommendation field",
            "every journal row records data timestamp, timeframe, reference block, response block, data quality note, and risk note",
            "manual reviewer signs off that no rule change, retune, threshold search, or parameter search was proposed",
            "manual reviewer signs off that the journal is complete enough for governance review",
            "zero safety violations are found by project health checks",
        ],
        "fail_if_any": [
            "the candidate rule hash changes",
            "a repeated OOS review is attempted",
            "new historical data is evaluated as a substitute for the missing detailed OOS metrics",
            "any execution, broker, account, or queue path is introduced",
            "journal output contains a recommendation or directional instruction",
            "the observation process proposes retuning, threshold search, parameter search, or a new variant",
            "manual review is missing or rejects journal integrity",
        ],
    }


def _safety_summary() -> dict[str, Any]:
    return {
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_path_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "execution_queue_allowed": False,
        "trade_recommendation_output_allowed": False,
        "directional_instruction_output_allowed": False,
        "oos_repeat_allowed": False,
        "new_oos_evaluation_allowed": False,
        "candidate_rules_modified": False,
        "martingale_allowed": False,
        "averaging_into_loss_allowed": False,
    }


def _stable_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
