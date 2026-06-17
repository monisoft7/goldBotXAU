"""v0_41 final non-execution demo readiness gate for locked XAUUSD candidate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research.xauusd_forward_observation_runner import CANDIDATE_ID

GATE_VERSION = "v0_41"
DEFAULT_V0_37_REPORT = Path("reports") / "xauusd_demo_preflight_review_v0_37.json"
DEFAULT_V0_38_REPORT = Path("reports") / "xauusd_demo_broker_safety_preflight_v0_38.json"
DEFAULT_V0_39_REPORT = Path("reports") / "xauusd_broker_facts_audit_v0_39.json"
DEFAULT_V0_40_REPORT = Path("reports") / "xauusd_demo_risk_envelope_v0_40.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_final_demo_readiness_gate_v0_41.json"

BLOCKED_MISSING_REQUIRED_REPORT = "blocked_missing_required_report"
BLOCKED_CANDIDATE_INTEGRITY_ISSUE = "blocked_candidate_integrity_issue"
BLOCKED_OOS_OR_RULE_LOCK_ISSUE = "blocked_oos_or_rule_lock_issue"
BLOCKED_FORWARD_OR_PREFLIGHT_ISSUE = "blocked_forward_or_preflight_issue"
BLOCKED_BROKER_FACTS_ISSUE = "blocked_broker_facts_issue"
BLOCKED_RISK_ENVELOPE_ISSUE = "blocked_risk_envelope_issue"
FINAL_DEMO_READINESS_GATE_PASSED_PENDING_HUMAN_AUTHORIZATION = (
    "final_demo_readiness_gate_passed_pending_human_authorization"
)

EXPECTED_DECISIONS = {
    "v0_37": "ready_for_demo_preflight_design",
    "v0_38": "demo_preflight_safety_design_ready",
    "v0_39": "broker_facts_audit_ready_for_risk_envelope_design",
    "v0_40": "demo_risk_envelope_design_ready",
}

REQUIRED_FIXED_RISK_ENVELOPE = {
    "starting_demo_lot": 0.01,
    "max_demo_lot": 0.01,
    "max_positions": 1,
    "max_consecutive_losses_before_stop": 2,
    "max_daily_demo_loss_R": 2.0,
    "max_session_demo_loss_R": 1.0,
    "no_martingale": True,
    "no_averaging_into_loss": True,
    "no_position_scaling": True,
}

DECISION_OPTIONS = [
    BLOCKED_MISSING_REQUIRED_REPORT,
    BLOCKED_CANDIDATE_INTEGRITY_ISSUE,
    BLOCKED_OOS_OR_RULE_LOCK_ISSUE,
    BLOCKED_FORWARD_OR_PREFLIGHT_ISSUE,
    BLOCKED_BROKER_FACTS_ISSUE,
    BLOCKED_RISK_ENVELOPE_ISSUE,
    FINAL_DEMO_READINESS_GATE_PASSED_PENDING_HUMAN_AUTHORIZATION,
]


def build_xauusd_final_demo_readiness_gate_v0_41(
    *,
    v0_37_report_path: str | Path = DEFAULT_V0_37_REPORT,
    v0_38_report_path: str | Path = DEFAULT_V0_38_REPORT,
    v0_39_report_path: str | Path = DEFAULT_V0_39_REPORT,
    v0_40_report_path: str | Path = DEFAULT_V0_40_REPORT,
) -> dict[str, Any]:
    paths = {
        "v0_37": Path(v0_37_report_path),
        "v0_38": Path(v0_38_report_path),
        "v0_39": Path(v0_39_report_path),
        "v0_40": Path(v0_40_report_path),
    }
    reports: dict[str, dict[str, Any] | None] = {}
    read_blockers: list[str] = []
    for version, path in paths.items():
        payload, blockers = _read_json_object(path, version)
        reports[version] = payload
        read_blockers.extend(blockers)

    candidate_blockers = _candidate_integrity_blockers(reports)
    oos_blockers = _oos_and_rule_lock_blockers(reports)
    forward_blockers = _forward_or_preflight_blockers(reports)
    broker_blockers = _broker_facts_blockers(reports)
    risk_blockers = _risk_envelope_blockers(reports)

    blocker_groups = {
        BLOCKED_MISSING_REQUIRED_REPORT: read_blockers,
        BLOCKED_CANDIDATE_INTEGRITY_ISSUE: candidate_blockers,
        BLOCKED_OOS_OR_RULE_LOCK_ISSUE: oos_blockers,
        BLOCKED_FORWARD_OR_PREFLIGHT_ISSUE: forward_blockers,
        BLOCKED_BROKER_FACTS_ISSUE: broker_blockers,
        BLOCKED_RISK_ENVELOPE_ISSUE: risk_blockers,
    }
    decision = _decision(blocker_groups)
    passed = decision == FINAL_DEMO_READINESS_GATE_PASSED_PENDING_HUMAN_AUTHORIZATION

    return {
        "gate_version": GATE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gate_status": "completed" if passed else "blocked",
        "decision": decision,
        "decision_options": DECISION_OPTIONS,
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": not candidate_blockers,
        "source_reports": {version: str(path) for version, path in paths.items()},
        "required_report_statuses": _required_report_statuses(reports),
        "final_blockers": _flatten_blockers(blocker_groups),
        "accepted_warnings": _accepted_warnings(reports.get("v0_40")),
        "fixed_demo_risk_summary": _fixed_demo_risk_summary(reports.get("v0_40")),
        "human_authorization_required": True,
        "future_demo_execution_design_allowed_to_be_considered": passed,
        "demo_allowed": False,
        "execution_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "broker_execution_path_allowed": False,
        "buy_sell_output_allowed": False,
        "trade_recommendation_output_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
        "explicit_non_actions": _explicit_non_actions(),
        "next_recommended_step": _next_recommended_step(decision),
    }


def save_xauusd_final_demo_readiness_gate(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json_object(path: Path, version: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{version}_report_missing: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{version}_report_invalid_json: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{version}_report_not_object: {path}"]
    return payload, []


def _candidate_integrity_blockers(reports: dict[str, dict[str, Any] | None]) -> list[str]:
    blockers: list[str] = []
    for version, report in reports.items():
        if report is None:
            continue
        if report.get("candidate_id") != CANDIDATE_ID:
            blockers.append(f"{version}_candidate_id_mismatch")
        if report.get("candidate_rules_preserved") is not True:
            blockers.append(f"{version}_candidate_rules_not_preserved")
    return blockers


def _oos_and_rule_lock_blockers(reports: dict[str, dict[str, Any] | None]) -> list[str]:
    blockers: list[str] = []
    v0_37 = reports.get("v0_37")
    if isinstance(v0_37, dict):
        confirmations = v0_37.get("input_confirmations", {})
        if not isinstance(confirmations, dict) or confirmations.get("one_time_oos_review_completed") is not True:
            blockers.append("v0_37_one_time_oos_review_not_confirmed")
        if not isinstance(confirmations, dict) or confirmations.get("repeat_oos_review_allowed") is not False:
            blockers.append("v0_37_repeat_oos_review_not_disallowed")
        if not isinstance(confirmations, dict) or confirmations.get("candidate_id_is_locked_v0_26") is not True:
            blockers.append("v0_37_candidate_lock_not_confirmed")
        if not isinstance(confirmations, dict) or confirmations.get("candidate_rules_modified") is not False:
            blockers.append("v0_37_candidate_rules_modified")
    for version, report in reports.items():
        if not isinstance(report, dict):
            continue
        if report.get("repeated_oos_review") is not None and report.get("repeated_oos_review") is not False:
            blockers.append(f"{version}_repeated_oos_review_not_false")
        if _nested_value(report, ("safety_state", "oos_repeat_allowed")) is not None and _nested_value(
            report, ("safety_state", "oos_repeat_allowed")
        ) is not False:
            blockers.append(f"{version}_oos_repeat_allowed_not_false")
        if _nested_value(report, ("explicit_non_actions", "oos_review_repeated")) is not None and _nested_value(
            report, ("explicit_non_actions", "oos_review_repeated")
        ) is not False:
            blockers.append(f"{version}_explicit_oos_review_repeated_not_false")
    return blockers


def _forward_or_preflight_blockers(reports: dict[str, dict[str, Any] | None]) -> list[str]:
    blockers: list[str] = []
    v0_37 = reports.get("v0_37")
    if isinstance(v0_37, dict):
        if v0_37.get("decision") != EXPECTED_DECISIONS["v0_37"]:
            blockers.append("v0_37_decision_not_ready_for_demo_preflight_design")
        if _as_list(v0_37.get("integrity_blockers")):
            blockers.append("v0_37_integrity_blockers_not_empty")
        if _as_list(v0_37.get("insufficient_forward_observation_blockers")):
            blockers.append("v0_37_insufficient_forward_observation_blockers_not_empty")
        blockers.extend(_surface_blockers("v0_37", v0_37, _v0_37_false_surfaces()))

    v0_38 = reports.get("v0_38")
    if isinstance(v0_38, dict):
        if v0_38.get("decision") != EXPECTED_DECISIONS["v0_38"]:
            blockers.append("v0_38_decision_not_demo_preflight_safety_design_ready")
        if v0_38.get("design_only") is not True:
            blockers.append("v0_38_design_only_not_true")
        if _as_list(v0_38.get("blocking_conditions")):
            blockers.append("v0_38_blocking_conditions_not_empty")
        blockers.extend(_surface_blockers("v0_38", v0_38, _v0_38_false_surfaces()))

    return blockers


def _broker_facts_blockers(reports: dict[str, dict[str, Any] | None]) -> list[str]:
    v0_39 = reports.get("v0_39")
    if not isinstance(v0_39, dict):
        return []
    blockers: list[str] = []
    if v0_39.get("decision") != EXPECTED_DECISIONS["v0_39"]:
        blockers.append("v0_39_decision_not_ready_for_risk_envelope_design")
    if _as_list(v0_39.get("broker_fact_blockers")):
        blockers.append("v0_39_broker_fact_blockers_not_empty")
    if _as_list(v0_39.get("missing_facts")):
        blockers.append("v0_39_missing_facts_not_empty")
    if v0_39.get("design_or_read_only") is not True:
        blockers.append("v0_39_design_or_read_only_not_true")
    blockers.extend(_surface_blockers("v0_39", v0_39, _v0_39_false_surfaces()))
    return blockers


def _risk_envelope_blockers(reports: dict[str, dict[str, Any] | None]) -> list[str]:
    v0_40 = reports.get("v0_40")
    if not isinstance(v0_40, dict):
        return []
    blockers: list[str] = []
    if v0_40.get("decision") != EXPECTED_DECISIONS["v0_40"]:
        blockers.append("v0_40_decision_not_demo_risk_envelope_design_ready")
    if _as_list(v0_40.get("blockers")):
        blockers.append("v0_40_blockers_not_empty")
    envelope = v0_40.get("fixed_risk_envelope", {})
    if not isinstance(envelope, dict):
        blockers.append("v0_40_fixed_risk_envelope_missing")
    else:
        for key, expected in REQUIRED_FIXED_RISK_ENVELOPE.items():
            if envelope.get(key) != expected:
                blockers.append(f"v0_40_fixed_risk_envelope_{key}_invalid")
    warnings = _as_list(v0_40.get("warnings"))
    if "tick_value_contract_size_mismatch" in warnings and v0_40.get("conservative_tick_value") != 1.0:
        blockers.append("v0_40_tick_value_contract_size_mismatch_not_conservatively_handled")
    unaccepted_warnings = [warning for warning in warnings if warning != "tick_value_contract_size_mismatch"]
    if unaccepted_warnings:
        blockers.append("v0_40_unaccepted_warnings_present")
    blockers.extend(_surface_blockers("v0_40", v0_40, _v0_40_false_surfaces()))
    return blockers


def _surface_blockers(version: str, report: dict[str, Any], false_surfaces: tuple[tuple[str, ...], ...]) -> list[str]:
    blockers: list[str] = []
    for path in false_surfaces:
        value = _nested_value(report, path)
        if value is not None and value is not False:
            blockers.append(f"{version}_{'_'.join(path)}_not_false")
    return blockers


def _required_report_statuses(reports: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    for version, report in reports.items():
        if not isinstance(report, dict):
            statuses[version] = {"present": False}
            continue
        status_field = {
            "v0_37": "review_status",
            "v0_38": "preflight_status",
            "v0_39": "audit_status",
            "v0_40": "envelope_status",
        }[version]
        statuses[version] = {
            "present": True,
            "status": report.get(status_field),
            "decision": report.get("decision"),
            "expected_decision": EXPECTED_DECISIONS[version],
            "candidate_id": report.get("candidate_id"),
            "candidate_rules_preserved": report.get("candidate_rules_preserved"),
        }
    return statuses


def _accepted_warnings(v0_40: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(v0_40, dict):
        return []
    warnings = _as_list(v0_40.get("warnings"))
    if "tick_value_contract_size_mismatch" not in warnings or v0_40.get("conservative_tick_value") != 1.0:
        return []
    return [
        {
            "warning": "tick_value_contract_size_mismatch",
            "reported_tick_value": v0_40.get("reported_tick_value"),
            "derived_tick_value": v0_40.get("derived_tick_value"),
            "conservative_tick_value": v0_40.get("conservative_tick_value"),
        }
    ]


def _fixed_demo_risk_summary(v0_40: dict[str, Any] | None) -> dict[str, Any]:
    envelope = v0_40.get("fixed_risk_envelope", {}) if isinstance(v0_40, dict) else {}
    if not isinstance(envelope, dict):
        envelope = {}
    return {key: envelope.get(key) for key in REQUIRED_FIXED_RISK_ENVELOPE}


def _decision(blocker_groups: dict[str, list[str]]) -> str:
    for decision in DECISION_OPTIONS[:-1]:
        if blocker_groups.get(decision):
            return decision
    return FINAL_DEMO_READINESS_GATE_PASSED_PENDING_HUMAN_AUTHORIZATION


def _flatten_blockers(blocker_groups: dict[str, list[str]]) -> list[dict[str, str]]:
    final_blockers: list[dict[str, str]] = []
    for category, blockers in blocker_groups.items():
        for blocker in blockers:
            final_blockers.append({"category": category, "blocker": blocker})
    return final_blockers


def _explicit_non_actions() -> dict[str, bool]:
    return {
        "mt5_imported": False,
        "mt5_initialized": False,
        "mt5_connection_created": False,
        "broker_adapter_created": False,
        "demo_execution_created": False,
        "live_execution_created": False,
        "order_send_called_or_wrapped": False,
        "order_check_called_or_wrapped": False,
        "execution_queue_created": False,
        "candidate_rules_changed": False,
        "oos_review_repeated": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "trade_recommendation_output_created": False,
    }


def _next_recommended_step(decision: str) -> str:
    if decision == FINAL_DEMO_READINESS_GATE_PASSED_PENDING_HUMAN_AUTHORIZATION:
        return (
            "human authorization may consider a separate limited demo execution design; "
            "this gate does not permit execution"
        )
    if decision == BLOCKED_MISSING_REQUIRED_REPORT:
        return "restore all required v0_37 through v0_40 reports before final readiness review"
    if decision == BLOCKED_CANDIDATE_INTEGRITY_ISSUE:
        return "repair candidate id or candidate rule preservation evidence before continuing"
    if decision == BLOCKED_OOS_OR_RULE_LOCK_ISSUE:
        return "restore one-time OOS and locked-rule confirmations before continuing"
    if decision == BLOCKED_FORWARD_OR_PREFLIGHT_ISSUE:
        return "repair v0_37 or v0_38 readiness evidence without creating execution"
    if decision == BLOCKED_BROKER_FACTS_ISSUE:
        return "repair v0_39 broker facts evidence before final readiness review"
    return "repair v0_40 fixed demo risk envelope evidence before final readiness review"


def _v0_37_false_surfaces() -> tuple[tuple[str, ...], ...]:
    return (
        ("safety_state", "demo_allowed"),
        ("safety_state", "demo_preflight_execution_allowed"),
        ("safety_state", "execution_allowed"),
        ("safety_state", "execution_queue_allowed"),
        ("safety_state", "live_allowed"),
        ("safety_state", "order_send_allowed"),
        ("safety_state", "order_send_created"),
        ("safety_state", "order_check_allowed"),
        ("safety_state", "order_check_created"),
        ("safety_state", "broker_execution_path_allowed"),
        ("safety_state", "buy_sell_output_allowed"),
        ("safety_state", "trade_recommendation_output_allowed"),
        ("safety_state", "recommendation_output_allowed"),
        ("safety_state", "directional_instruction_output_allowed"),
        ("safety_state", "retune_allowed"),
        ("safety_state", "threshold_search_allowed"),
        ("safety_state", "parameter_grid_allowed"),
        ("non_actions_performed", "demo_execution_created"),
        ("non_actions_performed", "execution_queue_created"),
        ("non_actions_performed", "broker_execution_path_created"),
        ("non_actions_performed", "order_send_created"),
        ("non_actions_performed", "order_check_created"),
        ("non_actions_performed", "repeated_oos_review"),
        ("non_actions_performed", "retune_performed"),
        ("non_actions_performed", "threshold_search_performed"),
        ("non_actions_performed", "parameter_grid_performed"),
    )


def _v0_38_false_surfaces() -> tuple[tuple[str, ...], ...]:
    return (
        ("demo_execution_created",),
        ("broker_execution_path_created",),
        ("mt5_connection_created",),
        ("order_send_created",),
        ("order_check_created",),
        ("execution_queue_created",),
        ("buy_sell_output_allowed",),
        ("trade_recommendation_output_allowed",),
        ("repeated_oos_review",),
        ("retune_performed",),
        ("threshold_search_performed",),
        ("parameter_grid_performed",),
        ("explicit_non_actions", "demo_execution_created"),
        ("explicit_non_actions", "execution_queue_created"),
        ("explicit_non_actions", "order_send_called_or_wrapped"),
        ("explicit_non_actions", "order_check_called_or_wrapped"),
    )


def _v0_39_false_surfaces() -> tuple[tuple[str, ...], ...]:
    return (
        ("broker_execution_path_created",),
        ("order_send_created",),
        ("order_send_called",),
        ("order_check_created",),
        ("order_check_called",),
        ("execution_queue_created",),
        ("buy_sell_output_allowed",),
        ("trade_recommendation_output_allowed",),
        ("repeated_oos_review",),
        ("retune_performed",),
        ("threshold_search_performed",),
        ("parameter_grid_performed",),
    )


def _v0_40_false_surfaces() -> tuple[tuple[str, ...], ...]:
    return (
        ("demo_execution_allowed",),
        ("broker_execution_path_created",),
        ("order_send_allowed",),
        ("order_check_allowed",),
        ("execution_queue_created",),
        ("buy_sell_output_allowed",),
        ("trade_recommendation_output_allowed",),
        ("repeated_oos_review",),
        ("retune_performed",),
        ("threshold_search_performed",),
        ("parameter_grid_performed",),
        ("explicit_non_actions", "demo_execution_created"),
        ("explicit_non_actions", "execution_queue_created"),
        ("explicit_non_actions", "order_send_called_or_wrapped"),
        ("explicit_non_actions", "order_check_called_or_wrapped"),
    )


def _nested_value(report: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = report
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
