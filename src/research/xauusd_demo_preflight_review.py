"""v0_37 design-only demo preflight review for the locked XAUUSD candidate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research.xauusd_forward_observation_runner import CANDIDATE_ID

REVIEW_VERSION = "v0_37"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_OOS_REPAIR_REPORT = Path("reports") / "xauusd_oos_review_repair_v0_29_1.json"
DEFAULT_LEDGER_REPORT = Path("reports") / "xauusd_forward_observation_ledger_v0_36_cycle_2026-06-16.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_demo_preflight_review_v0_37.json"

BLOCKED_INSUFFICIENT_FORWARD_OBSERVATION = "blocked_insufficient_forward_observation"
BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE = "blocked_forward_observation_integrity_issue"
READY_FOR_DEMO_PREFLIGHT_DESIGN = "ready_for_demo_preflight_design"

MIN_RECORDS_PER_TIMEFRAME = 3
MIN_INDEPENDENT_OBSERVATION_SESSIONS = 3
REQUIRED_TIMEFRAMES = ["M5", "M10"]
READY_LEDGER_STATUS = "ready_for_demo_preflight_review"

RAW_MARKET_FIELD_SET = {"open", "high", "low", "close"}
RAW_MARKET_CONTAINER_KEYS = {
    "raw_market_data",
    "raw_ohlc_rows",
    "ohlc_rows",
    "market_rows",
    "csv_rows",
    "normalized_csv_rows",
}


def build_xauusd_demo_preflight_review_v0_37(
    *,
    ledger_report_path: str | Path = DEFAULT_LEDGER_REPORT,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    oos_repair_report_path: str | Path = DEFAULT_OOS_REPAIR_REPORT,
) -> dict[str, Any]:
    ledger_path = Path(ledger_report_path)
    candidate_path = Path(candidate_report_path)
    oos_path = Path(oos_repair_report_path)

    ledger, ledger_errors = _read_json_object(ledger_path, "forward_observation_ledger")
    candidate, candidate_errors = _read_json_object(candidate_path, "v0_26_candidate_report")
    oos_repair, oos_errors = _read_json_object(oos_path, "v0_29_1_oos_repair_report")

    integrity_blockers: list[str] = []
    insufficient_blockers: list[str] = []
    integrity_blockers.extend(ledger_errors)
    integrity_blockers.extend(candidate_errors)
    integrity_blockers.extend(oos_errors)

    candidate_fixed_rules = _candidate_fixed_rules(candidate)

    if candidate is not None:
        integrity_blockers.extend(_candidate_report_blockers(candidate))
    if oos_repair is not None:
        integrity_blockers.extend(_oos_repair_blockers(oos_repair))
    if ledger is not None:
        ledger_integrity, ledger_insufficient = _ledger_blockers(ledger)
        integrity_blockers.extend(ledger_integrity)
        insufficient_blockers.extend(ledger_insufficient)

    integrity_blockers = _dedupe(integrity_blockers)
    insufficient_blockers = _dedupe(insufficient_blockers)
    if integrity_blockers:
        decision = BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE
    elif insufficient_blockers:
        decision = BLOCKED_INSUFFICIENT_FORWARD_OBSERVATION
    else:
        decision = READY_FOR_DEMO_PREFLIGHT_DESIGN

    return {
        "review_version": REVIEW_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "review_status": "completed" if decision == READY_FOR_DEMO_PREFLIGHT_DESIGN else "blocked",
        "decision": decision,
        "decision_options": [
            BLOCKED_INSUFFICIENT_FORWARD_OBSERVATION,
            BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE,
            READY_FOR_DEMO_PREFLIGHT_DESIGN,
        ],
        "source_reports": {
            "candidate_report": str(candidate_path),
            "oos_repair_report": str(oos_path),
            "forward_observation_ledger": str(ledger_path),
        },
        "input_confirmations": _input_confirmations(candidate, oos_repair, ledger),
        "minimum_demo_preflight_review_requirements": {
            "minimum_records_per_timeframe": {
                "required_timeframes": REQUIRED_TIMEFRAMES,
                "minimum_count": MIN_RECORDS_PER_TIMEFRAME,
                "observed": _ledger_counts(ledger),
                "passed": not any("record_count_below_requirement" in item for item in insufficient_blockers),
            },
            "minimum_independent_observation_sessions": {
                "minimum_count": MIN_INDEPENDENT_OBSERVATION_SESSIONS,
                "observed": _ledger_session_count(ledger),
                "passed": "independent_observation_sessions_below_requirement" not in insufficient_blockers,
            },
            "ledger_blockers_empty": {
                "observed": _ledger_reported_blockers(ledger),
                "passed": not any("ledger_blockers_not_empty" in item for item in integrity_blockers),
            },
            "raw_market_data_not_embedded": {
                "observed": _ledger_raw_market_data_embedded(ledger),
                "passed": not any("raw_market_data" in item for item in integrity_blockers),
            },
        },
        "integrity_blockers": integrity_blockers,
        "insufficient_forward_observation_blockers": insufficient_blockers,
        "candidate_rules_preserved": not integrity_blockers and _candidate_rules_preserved(candidate_fixed_rules),
        "candidate_rules_snapshot": candidate_fixed_rules,
        "future_audit_placeholders": _future_audit_placeholders(),
        "demo_preflight_design_scope": {
            "design_only": True,
            "demo_execution_created": False,
            "broker_execution_path_created": False,
            "candidate_rules_altered": False,
            "v0_26_rules_remain_locked": True,
        },
        "safety_state": _safety_state(),
        "non_actions_performed": {
            "demo_execution_created": False,
            "live_trading_created": False,
            "order_send_created": False,
            "order_check_created": False,
            "execution_queue_created": False,
            "broker_execution_path_created": False,
            "new_backtest_evaluated": False,
            "new_oos_run_performed": False,
            "repeated_oos_review": False,
            "candidate_rules_changed": False,
            "new_strategy_variant_created": False,
            "threshold_search_performed": False,
            "parameter_grid_performed": False,
            "parameter_optimization_performed": False,
            "retune_performed": False,
            "raw_market_csv_embedded": False,
        },
        "next_recommended_step": (
            "draft v0_38 demo preflight safety checklist design only; no broker or order execution"
            if decision == READY_FOR_DEMO_PREFLIGHT_DESIGN
            else "repair blockers or collect additional read-only forward observation evidence before any checklist design"
        ),
    }


def save_xauusd_demo_preflight_review(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
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


def _candidate_report_blockers(report: dict[str, Any]) -> list[str]:
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
        blockers.append("oos_safety_not_object")
        return blockers
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


def _ledger_blockers(report: dict[str, Any]) -> tuple[list[str], list[str]]:
    integrity: list[str] = []
    insufficient: list[str] = []
    if report.get("candidate_id") != CANDIDATE_ID:
        integrity.append("ledger_candidate_id_mismatch")
    if report.get("candidate_rules_modified") is not False:
        integrity.append("ledger_candidate_rules_modified")
    if report.get("repeated_oos_review") is not False:
        integrity.append("ledger_repeated_oos_review")
    if report.get("raw_market_data_embedded") is not False:
        integrity.append("ledger_raw_market_data_embedded_not_false")
    if _contains_embedded_raw_market_data(report):
        integrity.append("ledger_raw_market_data_payload_detected")
    if report.get("blockers") != []:
        integrity.append("ledger_blockers_not_empty")
    if report.get("quality_gate_status") != READY_LEDGER_STATUS:
        integrity.append("ledger_quality_gate_status_not_ready_for_demo_preflight_review")

    for key in (
        "demo_allowed",
        "execution_allowed",
        "live_allowed",
        "order_send_allowed",
        "order_check_allowed",
        "demo_preflight_allowed",
    ):
        if report.get(key) is not False:
            integrity.append(f"ledger_{key}_not_false")

    rules_lock = report.get("candidate_rules_lock", {})
    if not isinstance(rules_lock, dict):
        integrity.append("ledger_candidate_rules_lock_not_object")
    else:
        for key in (
            "rule_change_allowed",
            "threshold_search_allowed",
            "parameter_grid_allowed",
            "parameter_optimization_allowed",
            "retune_allowed",
        ):
            if rules_lock.get(key) is not False:
                integrity.append(f"ledger_candidate_rules_lock_{key}_not_false")

    counts = _ledger_counts(report)
    for timeframe in REQUIRED_TIMEFRAMES:
        if counts.get(timeframe, 0) < MIN_RECORDS_PER_TIMEFRAME:
            insufficient.append(f"{timeframe}_record_count_below_requirement")
    if _ledger_session_count(report) < MIN_INDEPENDENT_OBSERVATION_SESSIONS:
        insufficient.append("independent_observation_sessions_below_requirement")
    return integrity, insufficient


def _input_confirmations(
    candidate: dict[str, Any] | None,
    oos_repair: dict[str, Any] | None,
    ledger: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "candidate_id_is_locked_v0_26": (candidate or {}).get("candidate_id") == CANDIDATE_ID,
        "candidate_rules_modified": _candidate_rules_modified(candidate, ledger),
        "one_time_oos_review_completed": _oos_safety(oos_repair).get("one_time_oos_review_completed") is True,
        "repeat_oos_review_allowed": _oos_safety(oos_repair).get("repeat_review_allowed"),
        "ledger_quality_gate_status": (ledger or {}).get("quality_gate_status"),
        "journal_record_count_by_timeframe": _ledger_counts(ledger),
        "independent_observation_session_count": _ledger_session_count(ledger),
        "ledger_blockers": _ledger_reported_blockers(ledger),
        "raw_market_data_embedded": _ledger_raw_market_data_embedded(ledger),
    }


def _future_audit_placeholders() -> list[dict[str, Any]]:
    return [
        _audit_placeholder("spread/slippage realism audit"),
        _audit_placeholder("static macro blackout sensitivity audit"),
        _audit_placeholder("broker connection safety audit"),
    ]


def _audit_placeholder(name: str) -> dict[str, Any]:
    return {
        "audit": name,
        "status": "future_design_placeholder_only",
        "alters_v0_26_rules": False,
        "creates_demo_execution": False,
        "creates_broker_execution_path": False,
    }


def _candidate_fixed_rules(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(report, dict):
        return None
    fixed_rules = report.get("fixed_rules")
    if isinstance(fixed_rules, dict):
        return dict(fixed_rules)
    candidate = report.get("candidate", {})
    if isinstance(candidate, dict) and isinstance(candidate.get("fixed_rules"), dict):
        return dict(candidate["fixed_rules"])
    return None


def _candidate_rules_preserved(fixed_rules: dict[str, Any] | None) -> bool:
    return isinstance(fixed_rules, dict) and fixed_rules.get("retuning_used") is False


def _candidate_rules_modified(candidate: dict[str, Any] | None, ledger: dict[str, Any] | None) -> bool | None:
    if isinstance(ledger, dict) and ledger.get("candidate_rules_modified") is not None:
        return ledger.get("candidate_rules_modified")
    if not isinstance(candidate, dict):
        return None
    safety = candidate.get("safety", {})
    if isinstance(safety, dict):
        changed_flags = [
            safety.get("threshold_search_used"),
            safety.get("parameter_grid_used"),
            safety.get("rejected_candidate_retuned"),
        ]
        return any(flag is not False for flag in changed_flags)
    return None


def _oos_safety(report: dict[str, Any] | None) -> dict[str, Any]:
    safety = (report or {}).get("safety", {})
    return safety if isinstance(safety, dict) else {}


def _ledger_counts(report: dict[str, Any] | None) -> dict[str, int]:
    counts = (report or {}).get("journal_record_count_by_timeframe", {})
    if not isinstance(counts, dict):
        return {}
    return {str(key): int(value) for key, value in counts.items() if isinstance(value, int)}


def _ledger_session_count(report: dict[str, Any] | None) -> int:
    value = (report or {}).get("independent_observation_session_count", 0)
    return value if isinstance(value, int) else 0


def _ledger_reported_blockers(report: dict[str, Any] | None) -> list[Any]:
    blockers = (report or {}).get("blockers", [])
    return blockers if isinstance(blockers, list) else [blockers]


def _ledger_raw_market_data_embedded(report: dict[str, Any] | None) -> bool | None:
    if not isinstance(report, dict):
        return None
    return report.get("raw_market_data_embedded")


def _contains_embedded_raw_market_data(value: Any) -> bool:
    if isinstance(value, dict):
        keys = set(value)
        if RAW_MARKET_FIELD_SET.issubset(keys):
            return True
        if keys.intersection(RAW_MARKET_CONTAINER_KEYS):
            return True
        return any(_contains_embedded_raw_market_data(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_embedded_raw_market_data(item) for item in value)
    return False


def _safety_state() -> dict[str, bool]:
    return {
        "local_read_only": True,
        "demo_allowed": False,
        "live_allowed": False,
        "execution_allowed": False,
        "execution_queue_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "broker_execution_path_allowed": False,
        "demo_preflight_execution_allowed": False,
        "order_send_created": False,
        "order_check_created": False,
        "recommendation_output_allowed": False,
        "directional_instruction_output_allowed": False,
        "trade_recommendation_output_allowed": False,
        "buy_sell_output_allowed": False,
        "candidate_rules_modified": False,
        "rule_change_allowed": False,
        "threshold_search_allowed": False,
        "parameter_grid_allowed": False,
        "parameter_optimization_allowed": False,
        "retune_allowed": False,
        "new_oos_evaluation_allowed": False,
        "oos_repeat_allowed": False,
        "raw_market_data_embedded": False,
        "martingale_allowed": False,
        "averaging_into_loss_allowed": False,
    }


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
