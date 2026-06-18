"""v0_43 dry-run signal-to-order-request builder for locked XAUUSD candidate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.execution.xauusd_limited_demo_executor import (
    DEFAULT_MACRO_EVENT_WINDOWS,
    DEFAULT_READINESS_GATE_REPORT,
    DEFAULT_RISK_ENVELOPE_REPORT,
    LOT,
    MacroEventWindow,
    SYMBOL,
    _macro_event_lock_status,
    _number,
)
from src.research.xauusd_forward_observation_runner import CANDIDATE_ID

BUILDER_VERSION = "v0_43"
DEFAULT_OUTPUT = Path("reports") / "xauusd_signal_order_request_v0_43.json"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_LIMITED_DEMO_EXECUTOR_REPORT = Path("reports") / "xauusd_limited_demo_execution_v0_42.json"
ALLOWED_EXECUTABLE_INTERNAL_SIDES = frozenset({"long", "short"})
REVIEW_ONLY_UNASSIGNED_SIDE = "direction_unassigned_review_only"
DIRECTION_UNASSIGNED_NON_EXECUTABLE = "direction_unassigned_non_executable"

BLOCKED_READINESS_OR_RISK_REPORT_MISSING = "blocked_readiness_or_risk_report_missing"
BLOCKED_MACRO_EVENT_WINDOW = "blocked_macro_event_window"
BLOCKED_CANDIDATE_SIGNAL_UNAVAILABLE = "blocked_candidate_signal_unavailable"
NO_QUALIFIED_SIGNAL_NOW = "no_qualified_signal_now"
BLOCKED_INCOMPLETE_ORDER_REQUEST = "blocked_incomplete_order_request"
ORDER_REQUEST_BUILT_DRY_RUN_ONLY = "order_request_built_dry_run_only"

STATUS_OPTIONS = [
    BLOCKED_READINESS_OR_RISK_REPORT_MISSING,
    BLOCKED_MACRO_EVENT_WINDOW,
    BLOCKED_CANDIDATE_SIGNAL_UNAVAILABLE,
    NO_QUALIFIED_SIGNAL_NOW,
    BLOCKED_INCOMPLETE_ORDER_REQUEST,
    ORDER_REQUEST_BUILT_DRY_RUN_ONLY,
]

EXPECTED_READINESS_DECISION = "final_demo_readiness_gate_passed_pending_human_authorization"
EXPECTED_RISK_DECISION = "demo_risk_envelope_design_ready"

SignalProvider = Callable[[], dict[str, Any] | None]


def build_xauusd_signal_order_request_v0_43(
    *,
    symbol: str = SYMBOL,
    lot: float = LOT,
    dry_run: bool = True,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    readiness_gate_report_path: str | Path = DEFAULT_READINESS_GATE_REPORT,
    risk_envelope_report_path: str | Path = DEFAULT_RISK_ENVELOPE_REPORT,
    limited_demo_executor_report_path: str | Path = DEFAULT_LIMITED_DEMO_EXECUTOR_REPORT,
    signal_snapshot: dict[str, Any] | None = None,
    current_signal_snapshot: dict[str, Any] | None = None,
    signal_provider: SignalProvider | None = None,
    macro_event_lock_enabled: bool = True,
    macro_event_windows: list[MacroEventWindow | dict[str, Any]] | None = None,
    current_time: datetime | None = None,
) -> dict[str, Any]:
    """Build a complete internal order request only when a locked signal is qualified.

    v0_43 is dry-run only. It prepares request data for review and never calls
    any trading function.
    """

    candidate_path = Path(candidate_report_path)
    readiness_path = Path(readiness_gate_report_path)
    risk_path = Path(risk_envelope_report_path)
    limited_executor_path = Path(limited_demo_executor_report_path)

    candidate_report, candidate_read_blockers = _read_json_object(candidate_path, "candidate_report")
    readiness_report, readiness_read_blockers = _read_json_object(readiness_path, "readiness_gate_report")
    risk_report, risk_read_blockers = _read_json_object(risk_path, "risk_envelope_report")
    limited_executor_report, limited_read_blockers = _read_json_object(
        limited_executor_path,
        "limited_demo_executor_report",
    )

    blockers = [
        *candidate_read_blockers,
        *readiness_read_blockers,
        *risk_read_blockers,
        *limited_read_blockers,
    ]
    warnings: list[str] = []

    blockers.extend(_candidate_blockers(candidate_report))
    blockers.extend(_readiness_blockers(readiness_report))
    blockers.extend(_risk_blockers(risk_report))
    blockers.extend(_limited_executor_blockers(limited_executor_report))

    if symbol != SYMBOL:
        blockers.append("symbol_must_equal_XAUUSD")
    if _number(lot) != LOT:
        blockers.append("lot_must_equal_0.01")
    if dry_run is not True:
        blockers.append("dry_run_must_remain_true")

    macro_status, macro_window_used = _macro_event_lock_status(
        enabled=macro_event_lock_enabled,
        windows=macro_event_windows or DEFAULT_MACRO_EVENT_WINDOWS,
        current_time=current_time,
    )
    if macro_status == BLOCKED_MACRO_EVENT_WINDOW:
        blockers.append("macro_event_lock_active")

    signal_evaluated = False
    signal_qualified = False
    signal_reason = "signal_not_evaluated"
    order_request: dict[str, Any] | None = None

    pre_signal_status = _pre_signal_status(blockers)
    if pre_signal_status is None:
        signal_evaluated = True
        signal = _resolve_signal(
            signal_snapshot=signal_snapshot,
            current_signal_snapshot=current_signal_snapshot,
            signal_provider=signal_provider,
        )
        signal_qualified = bool(signal.get("qualified"))
        signal_reason = str(signal.get("reason") or ("qualified_signal" if signal_qualified else "no_qualified_signal_now"))
        if signal_qualified:
            order_request = _build_order_request(symbol=symbol, lot=lot, signal=signal)
            order_validation = _order_request_validation(order_request)
            if not order_validation["complete"]:
                blockers.append("order_request_incomplete")
        else:
            order_validation = _order_request_validation(None)
    else:
        signal_reason = f"blocked_before_signal_evaluation:{pre_signal_status}"
        order_validation = _order_request_validation(None)

    blockers = _dedupe(blockers)
    warnings = _dedupe(warnings)
    builder_status = _builder_status(
        blockers=blockers,
        signal_qualified=signal_qualified,
        order_request_complete=bool(order_validation["complete"]),
    )

    if builder_status != ORDER_REQUEST_BUILT_DRY_RUN_ONLY and builder_status != BLOCKED_INCOMPLETE_ORDER_REQUEST:
        order_request = None
        order_validation = _order_request_validation(None)

    return {
        "builder_version": BUILDER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "builder_status": builder_status,
        "status_options": STATUS_OPTIONS,
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": True,
        "dry_run": True,
        "source_candidate": _source_candidate(candidate_path, candidate_report),
        "source_readiness_gate_report": str(readiness_path),
        "source_risk_envelope_report": str(risk_path),
        "source_limited_demo_executor_report": str(limited_executor_path),
        "signal_evaluated": signal_evaluated,
        "signal_qualified": signal_qualified,
        "signal_reason": signal_reason,
        "signal_diagnostics": signal.get("diagnostics", {}) if signal_evaluated and isinstance(signal, dict) else {},
        "direction_assigned": order_validation["direction_assigned"],
        "direction_source": order_validation["direction_source"],
        "executable_side_valid": order_validation["executable_side_valid"],
        "order_request_present": order_validation["present"],
        "order_request_complete": order_validation["complete"],
        "order_request_missing_fields": order_validation["missing_fields"],
        "order_request_validation_status": order_validation["status"],
        "invalid_order_request_reasons": order_validation["invalid_reasons"],
        "order_request": order_request,
        "macro_event_lock_enabled": macro_event_lock_enabled,
        "macro_event_lock_status": macro_status,
        "macro_event_window_used": macro_window_used,
        "blockers": blockers,
        "warnings": warnings,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
        "explicit_non_actions": _explicit_non_actions(),
        "next_recommended_step": _next_recommended_step(builder_status),
    }


def save_xauusd_signal_order_request(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json_object(path: Path, name: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{name}_missing: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{name}_invalid_json: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{name}_not_object: {path}"]
    return payload, []


def _candidate_blockers(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return ["candidate_report_unavailable"]
    blockers: list[str] = []
    candidate = report.get("candidate", {})
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("candidate_id_mismatch")
    if not isinstance(candidate, dict) or candidate.get("rules_are_fixed_from_atlas_family") is not True:
        blockers.append("candidate_rules_not_confirmed_fixed")
    if _nested_flag(report, candidate, "threshold_search_used") is not False:
        blockers.append("candidate_threshold_search_not_false")
    if _nested_flag(report, candidate, "parameter_grid_used") is not False:
        blockers.append("candidate_parameter_grid_not_false")
    return blockers


def _readiness_blockers(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return ["readiness_gate_report_unavailable"]
    blockers: list[str] = []
    if report.get("decision") != EXPECTED_READINESS_DECISION:
        blockers.append("v0_41_readiness_decision_not_passed")
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("v0_41_candidate_id_mismatch")
    if report.get("candidate_rules_preserved") is not True:
        blockers.append("v0_41_candidate_rules_not_preserved")
    return blockers


def _risk_blockers(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return ["risk_envelope_report_unavailable"]
    blockers: list[str] = []
    envelope = report.get("fixed_risk_envelope")
    if report.get("decision") != EXPECTED_RISK_DECISION:
        blockers.append("v0_40_risk_decision_not_ready")
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("v0_40_candidate_id_mismatch")
    if not isinstance(envelope, dict):
        blockers.append("fixed_risk_envelope_missing")
    else:
        if envelope.get("starting_demo_lot") != LOT or envelope.get("max_demo_lot") != LOT:
            blockers.append("fixed_risk_lot_not_0.01")
        if envelope.get("max_positions") != 1:
            blockers.append("fixed_risk_max_positions_not_1")
    return blockers


def _limited_executor_blockers(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return ["limited_demo_executor_report_unavailable"]
    blockers: list[str] = []
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("v0_42_candidate_id_mismatch")
    if report.get("candidate_rules_preserved") is not True:
        blockers.append("v0_42_candidate_rules_not_preserved")
    if report.get("order_send_called") is not False:
        blockers.append("v0_42_order_send_called_not_false")
    if report.get("order_check_called") is not False:
        blockers.append("v0_42_order_check_called_not_false")
    return blockers


def _pre_signal_status(blockers: list[str]) -> str | None:
    if any("readiness" in blocker or "risk" in blocker or "limited_demo_executor" in blocker for blocker in blockers):
        return BLOCKED_READINESS_OR_RISK_REPORT_MISSING
    if "macro_event_lock_active" in blockers:
        return BLOCKED_MACRO_EVENT_WINDOW
    if any("candidate" in blocker for blocker in blockers):
        return BLOCKED_CANDIDATE_SIGNAL_UNAVAILABLE
    if any(blocker in {"symbol_must_equal_XAUUSD", "lot_must_equal_0.01", "dry_run_must_remain_true"} for blocker in blockers):
        return BLOCKED_INCOMPLETE_ORDER_REQUEST
    return None


def _resolve_signal(
    *,
    signal_snapshot: dict[str, Any] | None,
    current_signal_snapshot: dict[str, Any] | None,
    signal_provider: SignalProvider | None,
) -> dict[str, Any]:
    if signal_snapshot is not None and current_signal_snapshot is not None:
        signal = dict(signal_snapshot)
        diagnostics = dict(signal.get("diagnostics", {})) if isinstance(signal.get("diagnostics"), dict) else {}
        diagnostics["current_signal_snapshot_ignored"] = True
        signal["diagnostics"] = diagnostics
        return signal
    if signal_snapshot is not None:
        return dict(signal_snapshot)
    if current_signal_snapshot is not None:
        return dict(current_signal_snapshot)
    if signal_provider is None:
        return {"qualified": False, "reason": "no_current_signal_snapshot_supplied"}
    try:
        signal = signal_provider()
    except Exception as exc:
        return {"qualified": False, "reason": f"signal_provider_failed:{exc}"}
    if not isinstance(signal, dict):
        return {"qualified": False, "reason": "signal_provider_returned_no_signal"}
    return dict(signal)


def _build_order_request(*, symbol: str, lot: float, signal: dict[str, Any]) -> dict[str, Any]:
    request = {
        "symbol": symbol,
        "lot": lot,
        "demo_only": True,
        "candidate_id": CANDIDATE_ID,
        "side": signal.get("side"),
        "direction_source": signal.get("direction_source"),
        "order_type": signal.get("order_type", "market"),
        "action": signal.get("action", "prepare_demo_order"),
        "risk_reference": signal.get("risk_reference"),
    }
    for key in ("stop_loss", "stop_distance", "take_profit", "exit_rule"):
        if key in signal:
            request[key] = signal[key]
    return request


def _order_request_validation(order_request: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(order_request, dict):
        return {
            "present": False,
            "complete": False,
            "missing_fields": [
                "order_request",
                "symbol",
                "lot",
                "demo_only",
                "side",
                "order_type",
                "action",
                "risk_reference",
                "stop_loss_or_stop_distance",
                "take_profit_or_exit_rule",
                "candidate_id",
            ],
            "status": "missing_order_request",
            "invalid_reasons": [],
            "direction_assigned": False,
            "direction_source": "order_request_missing",
            "executable_side_valid": False,
        }

    missing_fields: list[str] = []
    invalid_reasons: list[str] = []
    if order_request.get("symbol") != SYMBOL:
        missing_fields.append("symbol")
    if _number(order_request.get("lot")) != LOT:
        missing_fields.append("lot")
    if order_request.get("demo_only") is not True:
        missing_fields.append("demo_only")
    side = order_request.get("side")
    executable_side_valid = _is_executable_internal_side(side)
    if side in (None, "", REVIEW_ONLY_UNASSIGNED_SIDE):
        invalid_reasons.append(DIRECTION_UNASSIGNED_NON_EXECUTABLE)
    elif not executable_side_valid:
        invalid_reasons.append("side_not_allowed_internal_executable_side")
    if not executable_side_valid:
        missing_fields.append("side")
    for key in ("order_type", "action", "risk_reference", "candidate_id"):
        if order_request.get(key) in (None, ""):
            missing_fields.append(key)
    if "stop_loss" not in order_request and "stop_distance" not in order_request:
        missing_fields.append("stop_loss_or_stop_distance")
    if "take_profit" not in order_request and "exit_rule" not in order_request:
        missing_fields.append("take_profit_or_exit_rule")
    if order_request.get("candidate_id") != CANDIDATE_ID and "candidate_id" not in missing_fields:
        missing_fields.append("candidate_id")

    missing_fields = _dedupe(missing_fields)
    invalid_reasons = _dedupe(invalid_reasons)
    if invalid_reasons and DIRECTION_UNASSIGNED_NON_EXECUTABLE in invalid_reasons:
        status = DIRECTION_UNASSIGNED_NON_EXECUTABLE
    elif invalid_reasons:
        status = "invalid_side_non_executable"
    else:
        status = "complete" if not missing_fields else "incomplete"
    return {
        "present": True,
        "complete": not missing_fields and not invalid_reasons,
        "missing_fields": missing_fields,
        "status": status,
        "invalid_reasons": invalid_reasons,
        "direction_assigned": executable_side_valid,
        "direction_source": _direction_source(order_request),
        "executable_side_valid": executable_side_valid,
    }


def _builder_status(*, blockers: list[str], signal_qualified: bool, order_request_complete: bool) -> str:
    if any("readiness" in blocker or "risk" in blocker or "limited_demo_executor" in blocker for blocker in blockers):
        return BLOCKED_READINESS_OR_RISK_REPORT_MISSING
    if "macro_event_lock_active" in blockers:
        return BLOCKED_MACRO_EVENT_WINDOW
    if any("candidate" in blocker for blocker in blockers):
        return BLOCKED_CANDIDATE_SIGNAL_UNAVAILABLE
    if any(blocker in {"symbol_must_equal_XAUUSD", "lot_must_equal_0.01", "dry_run_must_remain_true"} for blocker in blockers):
        return BLOCKED_INCOMPLETE_ORDER_REQUEST
    if "order_request_incomplete" in blockers:
        return BLOCKED_INCOMPLETE_ORDER_REQUEST
    if not signal_qualified:
        return NO_QUALIFIED_SIGNAL_NOW
    if not order_request_complete:
        return BLOCKED_INCOMPLETE_ORDER_REQUEST
    return ORDER_REQUEST_BUILT_DRY_RUN_ONLY


def _source_candidate(path: Path, report: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "path": str(path),
        "candidate_id": report.get("candidate_id") if isinstance(report, dict) else None,
        "status": report.get("status") if isinstance(report, dict) else None,
        "source_family": report.get("source_family") if isinstance(report, dict) else None,
    }


def _explicit_non_actions() -> dict[str, bool]:
    return {
        "order_send_called_or_wrapped": False,
        "order_check_called_or_wrapped": False,
        "live_execution_created": False,
        "automatic_loop_created": False,
        "background_scheduler_created": False,
        "execution_queue_created": False,
        "candidate_rules_changed": False,
        "trade_recommendation_output_created": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "oos_review_repeated": False,
    }


def _next_recommended_step(status: str) -> str:
    if status == ORDER_REQUEST_BUILT_DRY_RUN_ONLY:
        return "human review of the dry-run-only internal order request before any separate explicit demo execution task"
    if status == NO_QUALIFIED_SIGNAL_NOW:
        return "keep dry-run monitoring only; no internal order request exists for review"
    if status == BLOCKED_MACRO_EVENT_WINDOW:
        return "wait until the configured macro event window clears before rebuilding dry-run request data"
    return "repair blocker and rerun v0_43 in dry-run mode only"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _is_executable_internal_side(side: Any) -> bool:
    return isinstance(side, str) and side in ALLOWED_EXECUTABLE_INTERNAL_SIDES


def _direction_source(order_request: dict[str, Any]) -> str:
    if isinstance(order_request.get("direction_source"), str) and order_request["direction_source"]:
        return str(order_request["direction_source"])
    if order_request.get("side") == REVIEW_ONLY_UNASSIGNED_SIDE:
        return "locked_candidate_no_deterministic_direction_rule"
    if _is_executable_internal_side(order_request.get("side")):
        return "signal_snapshot_side"
    return "order_request_side"


def _nested_flag(report: dict[str, Any], candidate: dict[str, Any], key: str) -> Any:
    return report[key] if key in report else candidate.get(key)
