"""v0_32 read-only forward observation export plan."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLAN_VERSION = "v0_32"
CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"
DEFAULT_JOURNAL_PROTOCOL = Path("reports") / "xauusd_paper_shadow_journal_protocol_v0_31.json"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_forward_observation_export_plan_v0_32.json"
NEXT_RECOMMENDED_STEP = "v0_33 build read-only forward observation exporter and journal runner, no execution"

ALLOWED_FUTURE_SYMBOL_NAMES = ["XAUUSD", "XAUUSD.", "XAUUSDm"]
ALLOWED_FUTURE_TIMEFRAMES = ["M5", "M10"]
EXPECTED_CSV_SCHEMA = [
    "timestamp_utc",
    "symbol",
    "timeframe",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "source",
]


def build_xauusd_forward_observation_export_plan_v0_32(
    *,
    journal_protocol_path: str | Path = DEFAULT_JOURNAL_PROTOCOL,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
) -> dict[str, Any]:
    journal_file = Path(journal_protocol_path)
    candidate_file = Path(candidate_report_path)

    journal_protocol, journal_errors = _read_json_object(journal_file, "v0_31_journal_protocol")
    candidate_report, candidate_errors = _read_json_object(candidate_file, "candidate_report")
    blockers = [*journal_errors, *candidate_errors]
    if journal_protocol is not None:
        blockers.extend(_journal_protocol_blockers(journal_protocol))
    if candidate_report is not None:
        blockers.extend(_candidate_blockers(candidate_report))

    fixed_rules = _fixed_rules(candidate_report)
    plan_status = "export_plan_ready_not_started" if not blockers else "blocked_export_plan_prerequisites_not_met"

    return {
        "plan_version": PLAN_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "source_reports": {
            "paper_shadow_journal_protocol": str(journal_file),
            "candidate_report": str(candidate_file),
        },
        "plan_status": plan_status,
        "blockers": blockers,
        "real_market_observation_started": False,
        "mt5_called": False,
        "data_exported": False,
        "observation_run": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
        "allowed_future_timeframes": ALLOWED_FUTURE_TIMEFRAMES,
        "future_observation_mode": "journal_only",
        "future_observation_inputs": {
            "candidate_id": CANDIDATE_ID,
            "allowed_symbol_names": ALLOWED_FUTURE_SYMBOL_NAMES,
            "allowed_timeframes": ALLOWED_FUTURE_TIMEFRAMES,
            "allowed_read_only_exporter": {
                "name": "xauusd_forward_observation_readonly_csv_exporter_v0_33",
                "status": "planned_not_built",
                "permitted_outputs": ["csv_bar_data_for_journal_records"],
                "prohibited_capabilities": [
                    "account access",
                    "position access",
                    "route creation",
                    "request submission",
                    "queue creation",
                ],
            },
            "observation_date_range_requirements": {
                "mode": "prospective_forward_only",
                "must_be_declared_before_collection": True,
                "start_utc_required": True,
                "end_utc_required": True,
                "minimum_start_constraint": "after v0_32 approval and not before the declared v0_33 collection window",
                "excluded_ranges": [
                    "train_validation_source_data_through_2025-12-31",
                    "locked_or_unavailable_v0_29_oos_detail_reconstruction",
                ],
                "chronological_order_required": True,
                "timeframe_alignment_required": True,
            },
            "expected_csv_schema": EXPECTED_CSV_SCHEMA,
            "no_execution_guarantee": {
                "csv_output_only": True,
                "journal_records_only": True,
                "no_account_or_position_fields": True,
                "no_directional_instruction_fields": True,
                "no_trade_recommendation_fields": True,
            },
        },
        "future_journal_read_plan": {
            "read_csv_only": True,
            "required_timeframes": ALLOWED_FUTURE_TIMEFRAMES,
            "required_symbol_filter": ALLOWED_FUTURE_SYMBOL_NAMES,
            "journal_record_schema_source": "reports/xauusd_paper_shadow_journal_protocol_v0_31.json",
            "allowed_record_purpose": "observation records for locked candidate governance review",
        },
        "candidate_rules_lock": {
            "fixed_rules_hash_sha256": _stable_hash(fixed_rules) if fixed_rules else None,
            "fixed_rules_source": str(candidate_file),
            "rule_change_allowed": False,
            "threshold_search_allowed": False,
            "parameter_grid_allowed": False,
            "parameter_optimization_allowed": False,
            "retune_allowed": False,
        },
        "non_actions_performed": {
            "market_data_exported": False,
            "mt5_called": False,
            "real_observation_run": False,
            "new_backtest_evaluated": False,
            "new_oos_run_performed": False,
            "repeated_oos_review": False,
            "candidate_rules_changed": False,
            "new_strategy_variant_created": False,
        },
        "safety": _safety_summary(),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


def save_xauusd_forward_observation_export_plan(
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


def _journal_protocol_blockers(journal_protocol: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if journal_protocol.get("protocol_version") != "v0_31":
        blockers.append("journal_protocol_version_not_v0_31")
    if journal_protocol.get("candidate_id") != CANDIDATE_ID:
        blockers.append("journal_protocol_candidate_id_mismatch")
    if journal_protocol.get("journal_status") != "framework_ready_not_started":
        blockers.append("journal_status_not_framework_ready_not_started")
    if journal_protocol.get("real_market_observation_started") is not False:
        blockers.append("real_market_observation_already_started")
    if journal_protocol.get("execution_allowed") is not False:
        blockers.append("journal_execution_allowed_not_false")
    if journal_protocol.get("demo_allowed") is not False:
        blockers.append("journal_demo_allowed_not_false")
    if journal_protocol.get("live_allowed") is not False:
        blockers.append("journal_live_allowed_not_false")
    if journal_protocol.get("repeated_oos_review") is not False:
        blockers.append("journal_repeated_oos_review_not_false")
    if journal_protocol.get("candidate_rules_modified") is not False:
        blockers.append("journal_candidate_rules_modified_not_false")

    safety = journal_protocol.get("safety", {})
    if isinstance(safety, dict):
        if safety.get("order_send_allowed") is not False:
            blockers.append("journal_order_send_allowed_not_false")
        if safety.get("order_check_allowed") is not False:
            blockers.append("journal_order_check_allowed_not_false")
        if safety.get("execution_queue_allowed") is not False:
            blockers.append("journal_execution_queue_allowed_not_false")
    else:
        blockers.append("journal_safety_not_object")
    return blockers


def _candidate_blockers(candidate_report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if candidate_report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("candidate_report_candidate_id_mismatch")
    fixed_rules = _fixed_rules(candidate_report)
    if not fixed_rules:
        blockers.append("candidate_fixed_rules_missing")
        return blockers
    if fixed_rules.get("threshold_search_used") is not False:
        blockers.append("candidate_rules_threshold_search_not_false")
    if fixed_rules.get("parameter_grid_used") is not False:
        blockers.append("candidate_rules_parameter_grid_not_false")
    if fixed_rules.get("retuning_used") is not False:
        blockers.append("candidate_rules_retuning_not_false")
    return blockers


def _fixed_rules(candidate_report: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(candidate_report, dict):
        return {}
    fixed_rules = candidate_report.get("fixed_rules")
    return fixed_rules if isinstance(fixed_rules, dict) else {}


def _safety_summary() -> dict[str, Any]:
    return {
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_path_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "execution_queue_allowed": False,
        "recommendation_output_allowed": False,
        "directional_instruction_output_allowed": False,
        "trade_recommendation_output_allowed": False,
        "new_backtest_allowed": False,
        "new_oos_evaluation_allowed": False,
        "oos_repeat_allowed": False,
        "candidate_rules_modified": False,
        "threshold_search_allowed": False,
        "parameter_grid_allowed": False,
        "parameter_optimization_allowed": False,
        "retune_allowed": False,
        "martingale_allowed": False,
        "averaging_into_loss_allowed": False,
    }


def _stable_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
