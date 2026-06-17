"""v0_38 design-only demo/broker safety preflight checklist for XAUUSD."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research.xauusd_forward_observation_runner import CANDIDATE_ID

PREFLIGHT_VERSION = "v0_38"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_OOS_REPAIR_REPORT = Path("reports") / "xauusd_oos_review_repair_v0_29_1.json"
DEFAULT_DEMO_PREFLIGHT_REVIEW = Path("reports") / "xauusd_demo_preflight_review_v0_37.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_demo_broker_safety_preflight_v0_38.json"

BLOCKED_PREFLIGHT_INTEGRITY_ISSUE = "blocked_preflight_integrity_issue"
DEMO_PREFLIGHT_SAFETY_DESIGN_READY = "demo_preflight_safety_design_ready"


def build_xauusd_demo_broker_safety_preflight_v0_38(
    *,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    oos_repair_report_path: str | Path = DEFAULT_OOS_REPAIR_REPORT,
    demo_preflight_review_path: str | Path = DEFAULT_DEMO_PREFLIGHT_REVIEW,
) -> dict[str, Any]:
    candidate_path = Path(candidate_report_path)
    oos_path = Path(oos_repair_report_path)
    review_path = Path(demo_preflight_review_path)

    candidate, candidate_errors = _read_json_object(candidate_path, "v0_26_candidate_report")
    oos_repair, oos_errors = _read_json_object(oos_path, "v0_29_1_oos_repair_report")
    prior_review, review_errors = _read_json_object(review_path, "v0_37_demo_preflight_review")

    blocking_conditions: list[str] = []
    blocking_conditions.extend(candidate_errors)
    blocking_conditions.extend(oos_errors)
    blocking_conditions.extend(review_errors)
    if candidate is not None:
        blocking_conditions.extend(_candidate_blockers(candidate))
    if oos_repair is not None:
        blocking_conditions.extend(_oos_repair_blockers(oos_repair))
    if prior_review is not None:
        blocking_conditions.extend(_prior_review_blockers(prior_review))

    blocking_conditions = _dedupe(blocking_conditions)
    decision = (
        BLOCKED_PREFLIGHT_INTEGRITY_ISSUE
        if blocking_conditions
        else DEMO_PREFLIGHT_SAFETY_DESIGN_READY
    )

    return {
        "preflight_version": PREFLIGHT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "preflight_status": "blocked" if blocking_conditions else "completed",
        "decision": decision,
        "decision_options": [
            BLOCKED_PREFLIGHT_INTEGRITY_ISSUE,
            DEMO_PREFLIGHT_SAFETY_DESIGN_READY,
        ],
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": not blocking_conditions and _candidate_rules_preserved(candidate),
        "design_only": True,
        "demo_execution_created": False,
        "broker_execution_path_created": False,
        "mt5_connection_created": False,
        "order_send_created": False,
        "order_check_created": False,
        "execution_queue_created": False,
        "buy_sell_output_allowed": False,
        "trade_recommendation_output_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
        "source_reports": {
            "candidate_report": str(candidate_path),
            "oos_repair_report": str(oos_path),
            "demo_preflight_review": str(review_path),
        },
        "required_future_demo_preflight_checks": _required_future_demo_preflight_checks(),
        "blocking_conditions": blocking_conditions,
        "required_confirmations_before_future_demo_consideration": _required_confirmations(
            candidate,
            oos_repair,
            prior_review,
        ),
        "explicit_non_actions": _explicit_non_actions(),
        "next_recommended_step": (
            "human review of v0_38 safety checklist, then design a separate read-only broker facts audit only"
            if decision == DEMO_PREFLIGHT_SAFETY_DESIGN_READY
            else "repair v0_38 integrity blockers before any further demo preflight design work"
        ),
    }


def save_xauusd_demo_broker_safety_preflight(
    report: dict[str, Any],
    output_path: str | Path = DEFAULT_OUTPUT,
) -> None:
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


def _candidate_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("candidate_id_mismatch")
    if report.get("report_version") != "v0_26":
        blockers.append("candidate_report_version_not_v0_26")
    fixed_rules = report.get("fixed_rules")
    nested_candidate = report.get("candidate", {})
    nested_fixed_rules = nested_candidate.get("fixed_rules") if isinstance(nested_candidate, dict) else None
    if not isinstance(fixed_rules, dict):
        blockers.append("candidate_fixed_rules_missing")
    if not isinstance(nested_fixed_rules, dict):
        blockers.append("candidate_nested_fixed_rules_missing")
    if isinstance(fixed_rules, dict) and isinstance(nested_fixed_rules, dict) and fixed_rules != nested_fixed_rules:
        blockers.append("candidate_fixed_rules_mismatch")
    if isinstance(fixed_rules, dict):
        for key in ("threshold_search_used", "parameter_grid_used", "retuning_used"):
            if fixed_rules.get(key) is not False:
                blockers.append(f"candidate_fixed_rules_{key}_not_false")
    safety = report.get("safety", {})
    if not isinstance(safety, dict):
        blockers.append("candidate_safety_not_object")
    else:
        for key in (
            "demo_enabled",
            "live_enabled",
            "order_send_allowed",
            "order_check_allowed",
            "execution_queue_enabled",
            "trade_recommendation_output_present",
            "threshold_search_used",
            "parameter_grid_used",
            "rejected_candidate_retuned",
        ):
            if safety.get(key) is not False:
                blockers.append(f"candidate_safety_{key}_not_false")
    return blockers


def _oos_repair_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    safety = report.get("safety", {})
    if not isinstance(safety, dict):
        return ["oos_safety_not_object"]
    if safety.get("one_time_oos_review_completed") is not True:
        blockers.append("one_time_oos_review_not_completed")
    if safety.get("oos_evaluated") is not True:
        blockers.append("oos_not_evaluated_once")
    if safety.get("repeat_review_allowed") is not False:
        blockers.append("repeat_oos_review_allowed")
    if report.get("repeat_review_allowed") is not False:
        blockers.append("oos_repair_repeat_review_allowed")
    if safety.get("candidate_rules_modified") is not False:
        blockers.append("oos_candidate_rules_modified")
    return blockers


def _prior_review_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if report.get("review_version") != "v0_37":
        blockers.append("prior_review_version_not_v0_37")
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("prior_review_candidate_id_mismatch")
    if report.get("decision") != "ready_for_demo_preflight_design":
        blockers.append("prior_review_not_ready_for_demo_preflight_design")
    if report.get("candidate_rules_preserved") is not True:
        blockers.append("prior_review_candidate_rules_not_preserved")
    if report.get("integrity_blockers") != []:
        blockers.append("prior_review_integrity_blockers_not_empty")
    if report.get("insufficient_forward_observation_blockers") != []:
        blockers.append("prior_review_insufficient_observation_blockers_not_empty")

    safety = report.get("safety_state", {})
    if not isinstance(safety, dict):
        blockers.append("prior_review_safety_state_not_object")
    else:
        for key in (
            "demo_allowed",
            "live_allowed",
            "execution_allowed",
            "broker_execution_path_allowed",
            "order_send_allowed",
            "order_check_allowed",
            "execution_queue_allowed",
            "buy_sell_output_allowed",
            "trade_recommendation_output_allowed",
            "new_oos_evaluation_allowed",
            "oos_repeat_allowed",
            "threshold_search_allowed",
            "parameter_grid_allowed",
            "retune_allowed",
        ):
            if safety.get(key) is not False:
                blockers.append(f"prior_review_safety_{key}_not_false")
    return blockers


def _required_future_demo_preflight_checks() -> list[dict[str, Any]]:
    return [
        _check(
            "candidate_lock",
            "confirm v0_26 candidate id and fixed rules match committed v0_26 report exactly",
            "candidate id mismatch, rule mismatch, retune, threshold search, or parameter grid detected",
        ),
        _check(
            "oos_lock",
            "confirm OOS was reviewed once only and repeat review remains disallowed",
            "missing locked OOS marker, repeat review allowed, or any attempt to recreate OOS metrics",
        ),
        _check(
            "execution_absence",
            "confirm no demo/live execution surface, broker path, account connection, order functions, or queue exists",
            "any execution path, broker adapter, account connection, order function wrapper, or queue is present",
        ),
        _check(
            "output_language",
            "confirm outputs remain non-directional and contain no trading instructions or recommendations",
            "any directional instruction or recommendation-style trading output is present",
        ),
        _check(
            "broker_facts_design",
            "define a future read-only broker facts audit covering symbol contract, digits, tick size, lot step, min/max lot, margin mode, session hours, swaps, commission, spread source, and slippage assumptions",
            "broker facts are missing, manually unverifiable, or would require execution code in this version",
        ),
        _check(
            "risk_controls_design",
            "define future human-approved risk constraints before any demo consideration: account type, max loss, max lots, one-position cap, emergency stop, and no averaging into loss",
            "risk constraints are absent, ambiguous, or allow discretionary escalation",
        ),
        _check(
            "operator_approval",
            "require explicit human approval after reviewing this checklist and a separate future read-only facts audit",
            "approval token, approver, timestamp, or reviewed artifact list is missing",
        ),
    ]


def _check(check_id: str, required_confirmation: str, blocking_condition: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "required_confirmation": required_confirmation,
        "blocking_condition": blocking_condition,
        "required_before_demo_execution_can_be_considered": True,
        "creates_execution": False,
        "alters_candidate_rules": False,
    }


def _required_confirmations(
    candidate: dict[str, Any] | None,
    oos_repair: dict[str, Any] | None,
    prior_review: dict[str, Any] | None,
) -> dict[str, Any]:
    oos_safety = (oos_repair or {}).get("safety", {})
    if not isinstance(oos_safety, dict):
        oos_safety = {}
    prior_safety = (prior_review or {}).get("safety_state", {})
    if not isinstance(prior_safety, dict):
        prior_safety = {}
    return {
        "candidate_id_locked": (candidate or {}).get("candidate_id") == CANDIDATE_ID,
        "candidate_rules_preserved": _candidate_rules_preserved(candidate),
        "one_time_oos_review_completed": oos_safety.get("one_time_oos_review_completed") is True,
        "repeat_oos_review_allowed": oos_safety.get("repeat_review_allowed"),
        "prior_review_ready_for_design": (prior_review or {}).get("decision") == "ready_for_demo_preflight_design",
        "prior_review_demo_allowed": prior_safety.get("demo_allowed"),
        "prior_review_execution_allowed": prior_safety.get("execution_allowed"),
        "prior_review_order_send_allowed": prior_safety.get("order_send_allowed"),
        "prior_review_order_check_allowed": prior_safety.get("order_check_allowed"),
    }


def _candidate_rules_preserved(report: dict[str, Any] | None) -> bool:
    if not isinstance(report, dict):
        return False
    fixed_rules = report.get("fixed_rules")
    nested_candidate = report.get("candidate", {})
    nested_fixed_rules = nested_candidate.get("fixed_rules") if isinstance(nested_candidate, dict) else None
    if not isinstance(fixed_rules, dict) or not isinstance(nested_fixed_rules, dict):
        return False
    return (
        fixed_rules == nested_fixed_rules
        and fixed_rules.get("retuning_used") is False
        and fixed_rules.get("threshold_search_used") is False
        and fixed_rules.get("parameter_grid_used") is False
    )


def _explicit_non_actions() -> dict[str, bool]:
    return {
        "mt5_imported": False,
        "mt5_initialized": False,
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


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
