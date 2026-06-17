"""Print a compact local Codex context pack for goldBotXAU."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.project_health_check import build_project_health_report
from src.research.candidate_registry import research_candidate_registry

CONTEXT_VERSION = "v0_43"


def _latest_known_test_count(root: Path) -> int | None:
    handoff_path = root / "docs" / "next_codex_handoff.md"
    if not handoff_path.exists():
        return None
    text = handoff_path.read_text(encoding="utf-8")
    match = re.search(r"Current test baseline:\s*(\d+)\s+passed", text)
    return int(match.group(1)) if match else None


def _recommended_next_step(root: Path) -> str:
    handoff_path = root / "docs" / "next_codex_handoff.md"
    if not handoff_path.exists():
        return "ask_director"
    for line in handoff_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Next safe task:"):
            return line.split(":", 1)[1].strip() or "ask_director"
    return "ask_director"


def _rejected_candidate_versions(registry: dict[str, Any]) -> list[str]:
    versions: list[str] = []
    for candidate in registry["candidates"]:
        status = str(candidate.get("status"))
        if not (status == "rejected" or status.startswith("rejected_")) or candidate.get("do_not_retune") is not True:
            continue
        match = re.search(r"_(v\d+_\d+)(?:_|$)", str(candidate["candidate_id"]))
        if match:
            versions.append(match.group(1))
    return sorted(versions, key=lambda version: tuple(int(part) for part in version[1:].split("_")))


def _oos_repair_summary(root: Path) -> dict[str, Any] | None:
    repair_path = root / "reports" / "xauusd_oos_review_repair_v0_29_1.json"
    if not repair_path.exists():
        return None
    report = json.loads(repair_path.read_text(encoding="utf-8"))
    return {
        "repair_version": report.get("repair_version"),
        "marker_report_mismatch_detected": report.get("marker_report_mismatch_detected"),
        "overwritten_report_detected": report.get("overwritten_report_detected"),
        "marker_decision_preserved": report.get("marker_decision_preserved"),
        "detailed_oos_metrics_available": report.get("detailed_oos_metrics_available"),
        "repeat_review_allowed": report.get("repeat_review_allowed"),
    }


def _post_oos_governance_summary(root: Path) -> dict[str, Any] | None:
    governance_path = root / "reports" / "xauusd_post_oos_governance_v0_30.json"
    if not governance_path.exists():
        return None
    report = json.loads(governance_path.read_text(encoding="utf-8"))
    return {
        "governance_version": report.get("governance_version"),
        "candidate_id": report.get("candidate_id"),
        "source_oos_marker_decision": report.get("source_oos_marker_decision"),
        "detailed_oos_metrics_available": report.get("detailed_oos_metrics_available"),
        "repeat_oos_review_allowed": report.get("repeat_oos_review_allowed"),
        "governance_status": report.get("governance_status"),
        "paper_shadow_protocol_status": report.get("paper_shadow_protocol_status"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
    }


def _paper_shadow_journal_summary(root: Path) -> dict[str, Any] | None:
    journal_path = root / "reports" / "xauusd_paper_shadow_journal_protocol_v0_31.json"
    if not journal_path.exists():
        return None
    report = json.loads(journal_path.read_text(encoding="utf-8"))
    return {
        "protocol_version": report.get("protocol_version"),
        "candidate_id": report.get("candidate_id"),
        "journal_status": report.get("journal_status"),
        "data_source_status": report.get("data_source_status"),
        "real_market_observation_started": report.get("real_market_observation_started"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "candidate_rules_modified": report.get("candidate_rules_modified"),
    }


def _forward_observation_plan_summary(root: Path) -> dict[str, Any] | None:
    plan_path = root / "reports" / "xauusd_forward_observation_export_plan_v0_32.json"
    if not plan_path.exists():
        return None
    report = json.loads(plan_path.read_text(encoding="utf-8"))
    return {
        "plan_version": report.get("plan_version"),
        "candidate_id": report.get("candidate_id"),
        "plan_status": report.get("plan_status"),
        "real_market_observation_started": report.get("real_market_observation_started"),
        "mt5_called": report.get("mt5_called"),
        "data_exported": report.get("data_exported"),
        "observation_run": report.get("observation_run"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "candidate_rules_modified": report.get("candidate_rules_modified"),
        "allowed_future_timeframes": report.get("allowed_future_timeframes"),
        "future_observation_mode": report.get("future_observation_mode"),
    }


def _forward_observation_runner_summary(root: Path) -> dict[str, Any] | None:
    runner_path = root / "reports" / "xauusd_forward_observation_runner_protocol_v0_33.json"
    if not runner_path.exists():
        return None
    report = json.loads(runner_path.read_text(encoding="utf-8"))
    return {
        "runner_version": report.get("runner_version"),
        "candidate_id": report.get("candidate_id"),
        "runner_status": report.get("runner_status"),
        "data_source_status": report.get("data_source_status"),
        "real_market_observation_started": report.get("real_market_observation_started"),
        "mt5_called_in_tests": report.get("mt5_called_in_tests"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "candidate_rules_modified": report.get("candidate_rules_modified"),
        "allowed_timeframes": report.get("allowed_timeframes"),
        "future_mode": report.get("future_mode"),
    }


def _forward_observation_journal_summary(root: Path) -> dict[str, Any] | None:
    journal_path = root / "reports" / "xauusd_forward_observation_journal_v0_34.json"
    if not journal_path.exists():
        return None
    report = json.loads(journal_path.read_text(encoding="utf-8"))
    return {
        "observation_version": report.get("observation_version"),
        "candidate_id": report.get("candidate_id"),
        "observation_status": report.get("observation_status"),
        "real_market_observation_started": report.get("real_market_observation_started"),
        "journal_record_count": report.get("journal_record_count"),
        "timeframes_used": report.get("timeframes_used"),
        "data_files_used": report.get("data_files_used"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "order_send_allowed": report.get("order_send_allowed"),
        "order_check_allowed": report.get("order_check_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "candidate_rules_modified": report.get("candidate_rules_modified"),
    }


def _forward_observation_schema_adapter_summary(root: Path) -> dict[str, Any] | None:
    adapter_path = root / "reports" / "xauusd_forward_observation_schema_adapter_protocol_v0_34_1.json"
    if not adapter_path.exists():
        return None
    report = json.loads(adapter_path.read_text(encoding="utf-8"))
    spread_policy = report.get("spread_policy", {})
    return {
        "adapter_version": report.get("adapter_version"),
        "candidate_id": report.get("candidate_id"),
        "adapter_status": report.get("adapter_status"),
        "mt5_called": report.get("mt5_called"),
        "data_exported_from_mt5": report.get("data_exported_from_mt5"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "candidate_rules_modified": report.get("candidate_rules_modified"),
        "expected_output_schema": report.get("expected_output_schema"),
        "supported_timeframes": report.get("supported_timeframes"),
        "spread_warning": spread_policy.get("warning") if isinstance(spread_policy, dict) else None,
    }


def _forward_observation_consolidated_summary(root: Path) -> dict[str, Any] | None:
    consolidated_path = root / "reports" / "xauusd_forward_observation_consolidated_v0_34_2.json"
    if not consolidated_path.exists():
        return None
    report = json.loads(consolidated_path.read_text(encoding="utf-8"))
    return {
        "consolidation_version": report.get("consolidation_version"),
        "candidate_id": report.get("candidate_id"),
        "consolidation_status": report.get("consolidation_status"),
        "observation_mode": report.get("observation_mode"),
        "raw_market_data_embedded": report.get("raw_market_data_embedded"),
        "timeframes_observed": report.get("timeframes_observed"),
        "journal_record_count_by_timeframe": report.get("journal_record_count_by_timeframe"),
        "total_journal_record_count": report.get("total_journal_record_count"),
        "expansion_observed_count": report.get("expansion_observed_count"),
        "no_expansion_observed_count": report.get("no_expansion_observed_count"),
        "observation_quality_status": report.get("observation_quality_status"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "order_send_allowed": report.get("order_send_allowed"),
        "order_check_allowed": report.get("order_check_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "candidate_rules_modified": report.get("candidate_rules_modified"),
    }


def _forward_observation_ledger_summary(root: Path) -> dict[str, Any] | None:
    ledger_path = root / "reports" / "xauusd_forward_observation_ledger_v0_36_cycle_2026-06-16.json"
    if not ledger_path.exists():
        ledger_path = root / "reports" / "xauusd_forward_observation_ledger_v0_35.json"
    if not ledger_path.exists():
        return None
    report = json.loads(ledger_path.read_text(encoding="utf-8"))
    return {
        "ledger_version": report.get("ledger_version"),
        "candidate_id": report.get("candidate_id"),
        "ledger_status": report.get("ledger_status"),
        "raw_market_data_embedded": report.get("raw_market_data_embedded"),
        "input_consolidated_report_count": len(report.get("input_consolidated_reports", []))
        if isinstance(report.get("input_consolidated_reports"), list)
        else None,
        "total_unique_journal_records": report.get("total_unique_journal_records"),
        "timeframes_observed": report.get("timeframes_observed"),
        "journal_record_count_by_timeframe": report.get("journal_record_count_by_timeframe"),
        "independent_observation_session_count": report.get("independent_observation_session_count"),
        "expansion_observed_count": report.get("expansion_observed_count"),
        "no_expansion_observed_count": report.get("no_expansion_observed_count"),
        "quality_gate_status": report.get("quality_gate_status"),
        "demo_preflight_allowed": report.get("demo_preflight_allowed"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "order_send_allowed": report.get("order_send_allowed"),
        "order_check_allowed": report.get("order_check_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "candidate_rules_modified": report.get("candidate_rules_modified"),
    }


def _demo_preflight_review_summary(root: Path) -> dict[str, Any] | None:
    review_path = root / "reports" / "xauusd_demo_preflight_review_v0_37.json"
    if not review_path.exists():
        return None
    report = json.loads(review_path.read_text(encoding="utf-8"))
    confirmations = report.get("input_confirmations", {})
    return {
        "review_version": report.get("review_version"),
        "candidate_id": report.get("candidate_id"),
        "review_status": report.get("review_status"),
        "decision": report.get("decision"),
        "candidate_rules_preserved": report.get("candidate_rules_preserved"),
        "journal_record_count_by_timeframe": confirmations.get("journal_record_count_by_timeframe")
        if isinstance(confirmations, dict)
        else None,
        "independent_observation_session_count": confirmations.get("independent_observation_session_count")
        if isinstance(confirmations, dict)
        else None,
        "integrity_blockers": report.get("integrity_blockers"),
        "insufficient_forward_observation_blockers": report.get("insufficient_forward_observation_blockers"),
        "demo_allowed": report.get("safety_state", {}).get("demo_allowed")
        if isinstance(report.get("safety_state"), dict)
        else None,
        "execution_allowed": report.get("safety_state", {}).get("execution_allowed")
        if isinstance(report.get("safety_state"), dict)
        else None,
        "order_send_allowed": report.get("safety_state", {}).get("order_send_allowed")
        if isinstance(report.get("safety_state"), dict)
        else None,
        "order_check_allowed": report.get("safety_state", {}).get("order_check_allowed")
        if isinstance(report.get("safety_state"), dict)
        else None,
    }


def _demo_broker_safety_preflight_summary(root: Path) -> dict[str, Any] | None:
    preflight_path = root / "reports" / "xauusd_demo_broker_safety_preflight_v0_38.json"
    if not preflight_path.exists():
        return None
    report = json.loads(preflight_path.read_text(encoding="utf-8"))
    return {
        "preflight_version": report.get("preflight_version"),
        "candidate_id": report.get("candidate_id"),
        "preflight_status": report.get("preflight_status"),
        "decision": report.get("decision"),
        "candidate_rules_preserved": report.get("candidate_rules_preserved"),
        "design_only": report.get("design_only"),
        "blocking_conditions": report.get("blocking_conditions"),
        "demo_execution_created": report.get("demo_execution_created"),
        "broker_execution_path_created": report.get("broker_execution_path_created"),
        "mt5_connection_created": report.get("mt5_connection_created"),
        "order_send_created": report.get("order_send_created"),
        "order_check_created": report.get("order_check_created"),
        "execution_queue_created": report.get("execution_queue_created"),
        "buy_sell_output_allowed": report.get("buy_sell_output_allowed"),
        "trade_recommendation_output_allowed": report.get("trade_recommendation_output_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "retune_performed": report.get("retune_performed"),
        "threshold_search_performed": report.get("threshold_search_performed"),
        "parameter_grid_performed": report.get("parameter_grid_performed"),
    }


def _broker_facts_audit_summary(root: Path) -> dict[str, Any] | None:
    audit_path = root / "reports" / "xauusd_broker_facts_audit_v0_39.json"
    if not audit_path.exists():
        return None
    report = json.loads(audit_path.read_text(encoding="utf-8"))
    return {
        "audit_version": report.get("audit_version"),
        "candidate_id": report.get("candidate_id"),
        "audit_status": report.get("audit_status"),
        "decision": report.get("decision"),
        "candidate_rules_preserved": report.get("candidate_rules_preserved"),
        "design_or_read_only": report.get("design_or_read_only"),
        "mt5_read_only_metadata_access": report.get("mt5_read_only_metadata_access"),
        "mt5_initialized": report.get("mt5_initialized"),
        "mt5_shutdown_called": report.get("mt5_shutdown_called"),
        "order_send_created": report.get("order_send_created"),
        "order_send_called": report.get("order_send_called"),
        "order_check_created": report.get("order_check_created"),
        "order_check_called": report.get("order_check_called"),
        "execution_queue_created": report.get("execution_queue_created"),
        "broker_execution_path_created": report.get("broker_execution_path_created"),
        "buy_sell_output_allowed": report.get("buy_sell_output_allowed"),
        "trade_recommendation_output_allowed": report.get("trade_recommendation_output_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "retune_performed": report.get("retune_performed"),
        "threshold_search_performed": report.get("threshold_search_performed"),
        "parameter_grid_performed": report.get("parameter_grid_performed"),
    }


def _demo_risk_envelope_summary(root: Path) -> dict[str, Any] | None:
    envelope_path = root / "reports" / "xauusd_demo_risk_envelope_v0_40.json"
    if not envelope_path.exists():
        return None
    report = json.loads(envelope_path.read_text(encoding="utf-8"))
    envelope = report.get("fixed_risk_envelope", {})
    execution_disabled = all(
        report.get(key) is False
        for key in (
            "demo_execution_allowed",
            "order_send_allowed",
            "order_check_allowed",
            "broker_execution_path_created",
            "execution_queue_created",
            "buy_sell_output_allowed",
            "trade_recommendation_output_allowed",
            "repeated_oos_review",
            "retune_performed",
            "threshold_search_performed",
            "parameter_grid_performed",
        )
    )
    return {
        "version": report.get("envelope_version"),
        "decision": report.get("decision"),
        "safety_locked": execution_disabled,
        "lot": envelope.get("starting_demo_lot") if isinstance(envelope, dict) else None,
        "warnings": len(report.get("warnings", [])) if isinstance(report.get("warnings"), list) else None,
        "blockers": len(report.get("blockers", [])) if isinstance(report.get("blockers"), list) else None,
    }


def _final_demo_readiness_gate_summary(root: Path) -> dict[str, Any] | None:
    gate_path = root / "reports" / "xauusd_final_demo_readiness_gate_v0_41.json"
    if not gate_path.exists():
        return None
    report = json.loads(gate_path.read_text(encoding="utf-8"))
    blockers = report.get("final_blockers", [])
    warnings = report.get("accepted_warnings", [])
    return {
        "gate_version": report.get("gate_version"),
        "decision": report.get("decision"),
        "gate_status": report.get("gate_status"),
        "final_blockers": len(blockers) if isinstance(blockers, list) else None,
        "accepted_warnings": len(warnings) if isinstance(warnings, list) else None,
        "human_auth_required": report.get("human_authorization_required"),
        "future_design_consideration": report.get("future_demo_execution_design_allowed_to_be_considered"),
        "safety_locked": all(
            report.get(key) is False
            for key in (
                "demo_allowed",
                "execution_allowed",
                "order_send_allowed",
                "order_check_allowed",
                "broker_execution_path_allowed",
                "repeated_oos_review",
            )
        ),
    }


def _limited_demo_execution_summary(root: Path) -> dict[str, Any] | None:
    execution_path = root / "reports" / "xauusd_limited_demo_execution_v0_42.json"
    if not execution_path.exists():
        return None
    report = json.loads(execution_path.read_text(encoding="utf-8"))
    return {
        "executor_version": report.get("executor_version"),
        "executor_status": report.get("executor_status"),
        "candidate_id": report.get("candidate_id"),
        "candidate_rules_preserved": report.get("candidate_rules_preserved"),
        "demo_only": report.get("demo_only"),
        "live_allowed": report.get("live_allowed"),
        "order_send_default_allowed": report.get("order_send_default_allowed"),
        "order_send_called": report.get("order_send_called"),
        "order_check_called": report.get("order_check_called"),
        "order_request_present": report.get("order_request_present", False),
        "order_request_complete": report.get("order_request_complete", False),
        "order_request_missing_fields": report.get("order_request_missing_fields", []),
        "order_request_validation_status": report.get("order_request_validation_status", "missing_order_request"),
        "macro_event_lock_enabled": report.get("macro_event_lock_enabled"),
        "macro_event_lock_status": report.get("macro_event_lock_status"),
        "approval_token_required": report.get("approval_token_required"),
    }


def _signal_order_request_summary(root: Path) -> dict[str, Any] | None:
    request_path = root / "reports" / "xauusd_signal_order_request_v0_43.json"
    if not request_path.exists():
        return None
    report = json.loads(request_path.read_text(encoding="utf-8"))
    return {
        "builder_version": report.get("builder_version"),
        "builder_status": report.get("builder_status"),
        "candidate_id": report.get("candidate_id"),
        "candidate_rules_preserved": report.get("candidate_rules_preserved"),
        "dry_run": report.get("dry_run"),
        "signal_evaluated": report.get("signal_evaluated"),
        "signal_qualified": report.get("signal_qualified"),
        "signal_reason": report.get("signal_reason"),
        "order_request_present": report.get("order_request_present"),
        "order_request_complete": report.get("order_request_complete"),
        "order_request_missing_fields": report.get("order_request_missing_fields"),
        "order_request_validation_status": report.get("order_request_validation_status"),
        "macro_event_lock_status": report.get("macro_event_lock_status"),
        "order_send_called": report.get("order_send_called"),
        "order_check_called": report.get("order_check_called"),
        "live_allowed": report.get("live_allowed"),
    }


def _forward_observation_cycle_protocol_summary(root: Path) -> dict[str, Any] | None:
    protocol_path = root / "reports" / "xauusd_forward_observation_cycle_protocol_v0_36.json"
    if not protocol_path.exists():
        return None
    report = json.loads(protocol_path.read_text(encoding="utf-8"))
    return {
        "cycle_protocol_version": report.get("cycle_protocol_version"),
        "candidate_id": report.get("candidate_id"),
        "orchestrator_status": report.get("orchestrator_status"),
        "approval_token_required": report.get("approval_token_required"),
        "read_only_forward_observation_allowed": report.get("read_only_forward_observation_allowed"),
        "demo_preflight_allowed": report.get("demo_preflight_allowed"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "order_send_allowed": report.get("order_send_allowed"),
        "order_check_allowed": report.get("order_check_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "candidate_rules_modified": report.get("candidate_rules_modified"),
        "raw_market_data_embedded": report.get("raw_market_data_embedded"),
        "supported_timeframes": report.get("supported_timeframes"),
    }


def build_codex_context(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    health = build_project_health_report(root)
    registry = research_candidate_registry()

    return {
        "context_version": CONTEXT_VERSION,
        "project": "goldBotXAU",
        "current_tests": _latest_known_test_count(root),
        "health": {
            "status": health["status"],
            "recommended_action": health["recommended_action"],
            "oos_locked": health["project_state"]["oos_locked"],
            "eligible_for_oos_review_count": health["project_state"]["eligible_for_oos_review_count"],
            "rejected_candidate_count": health["project_state"]["rejected_candidate_count"],
        },
        "latest_oos_repair": _oos_repair_summary(root),
        "latest_post_oos_governance": _post_oos_governance_summary(root),
        "latest_paper_shadow_journal": _paper_shadow_journal_summary(root),
        "latest_forward_observation_plan": _forward_observation_plan_summary(root),
        "latest_forward_observation_runner": _forward_observation_runner_summary(root),
        "latest_forward_observation_journal": _forward_observation_journal_summary(root),
        "latest_forward_observation_schema_adapter": _forward_observation_schema_adapter_summary(root),
        "latest_forward_observation_consolidated": _forward_observation_consolidated_summary(root),
        "latest_forward_observation_ledger": _forward_observation_ledger_summary(root),
        "latest_forward_observation_cycle_protocol": _forward_observation_cycle_protocol_summary(root),
        "latest_demo_preflight_review": _demo_preflight_review_summary(root),
        "latest_demo_broker_safety_preflight": _demo_broker_safety_preflight_summary(root),
        "latest_broker_facts_audit": _broker_facts_audit_summary(root),
        "latest_demo_risk_envelope": _demo_risk_envelope_summary(root),
        "latest_final_demo_readiness_gate": _final_demo_readiness_gate_summary(root),
        "latest_limited_demo_execution": _limited_demo_execution_summary(root),
        "latest_signal_order_request": _signal_order_request_summary(root),
        "rejected_do_not_retune_candidates": _rejected_candidate_versions(registry),
        "current_safety_rules": {
            "demo_only_scaffold": True,
            "no_live": True,
            "no_order_send_by_default": True,
            "no_order_check": True,
            "no_execution_queue": True,
            "no_buy_sell_output": True,
            "no_trade_recommendation_output": True,
            "oos_locked": True,
        },
        "recommended_next_step": _recommended_next_step(root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Print compact Codex context for goldBotXAU.")
    parser.add_argument("--json", action="store_true", help="Print the context as JSON.")
    parser.add_argument("--output", type=Path, help="Optional path to write the JSON context.")
    args = parser.parse_args()

    context = build_codex_context(ROOT)
    context_text = json.dumps(context, indent=2, sort_keys=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(context_text + "\n", encoding="utf-8")

    if args.json:
        print(context_text)
    else:
        print(f"Codex context {context['context_version']} for {context['project']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
