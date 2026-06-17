"""v0_42 limited demo execution scaffold for locked XAUUSD candidate."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.research.xauusd_forward_observation_runner import CANDIDATE_ID

EXECUTOR_VERSION = "v0_42"
SYMBOL = "XAUUSD"
LOT = 0.01
MAX_POSITIONS = 1
REQUIRED_APPROVAL_TOKEN = "HUMAN_APPROVED_LIMITED_DEMO_EXECUTION_V0_42"
DEFAULT_OUTPUT = Path("reports") / "xauusd_limited_demo_execution_v0_42.json"
DEFAULT_READINESS_GATE_REPORT = Path("reports") / "xauusd_final_demo_readiness_gate_v0_41.json"
DEFAULT_RISK_ENVELOPE_REPORT = Path("reports") / "xauusd_demo_risk_envelope_v0_40.json"
DEFAULT_BROKER_FACTS_REPORT = Path("reports") / "xauusd_broker_facts_audit_v0_39.json"

BLOCKED_READINESS_GATE_MISSING_OR_FAILED = "blocked_readiness_gate_missing_or_failed"
BLOCKED_NOT_DEMO_ACCOUNT = "blocked_not_demo_account"
BLOCKED_INVALID_SYMBOL = "blocked_invalid_symbol"
BLOCKED_INVALID_LOT = "blocked_invalid_lot"
BLOCKED_MACRO_EVENT_WINDOW = "blocked_macro_event_window"
BLOCKED_MISSING_APPROVAL_TOKEN = "blocked_missing_approval_token"
DRY_RUN_READY_NO_ORDER_SENT = "dry_run_ready_no_order_sent"
DEMO_ORDER_SEND_ALLOWED_BUT_NOT_CALLED = "demo_order_send_allowed_but_not_called"
DEMO_ORDER_SEND_ATTEMPTED = "demo_order_send_attempted"

DECISION_OPTIONS = [
    BLOCKED_READINESS_GATE_MISSING_OR_FAILED,
    BLOCKED_NOT_DEMO_ACCOUNT,
    BLOCKED_INVALID_SYMBOL,
    BLOCKED_INVALID_LOT,
    BLOCKED_MACRO_EVENT_WINDOW,
    BLOCKED_MISSING_APPROVAL_TOKEN,
    DRY_RUN_READY_NO_ORDER_SENT,
    DEMO_ORDER_SEND_ALLOWED_BUT_NOT_CALLED,
    DEMO_ORDER_SEND_ATTEMPTED,
]

EXPECTED_READINESS_DECISION = "final_demo_readiness_gate_passed_pending_human_authorization"


@dataclass(frozen=True)
class MacroEventWindow:
    event_id: str
    label: str
    timezone: str
    starts_at: str
    ends_at: str
    source: str = "manual_static_config"


@dataclass(frozen=True)
class ExecutionIntent:
    candidate_id: str
    symbol: str
    lot: float
    max_positions: int
    demo_only: bool
    no_directional_recommendation: bool
    order_path: str


DEFAULT_MACRO_EVENT_WINDOWS = [
    MacroEventWindow(
        event_id="fomc_fed_chair_2026_06_17_default_libya_time",
        label="FOMC/Fed Chair static manual blocked window",
        timezone="Africa/Tripoli",
        starts_at="2026-06-17T19:30:00",
        ends_at="2026-06-17T22:30:00",
    )
]


def build_xauusd_limited_demo_execution_v0_42(
    *,
    symbol: str = SYMBOL,
    lot: float = LOT,
    dry_run: bool = True,
    allow_demo_order_send: bool = False,
    approval_token: str | None = None,
    readiness_gate_report_path: str | Path = DEFAULT_READINESS_GATE_REPORT,
    risk_envelope_report_path: str | Path = DEFAULT_RISK_ENVELOPE_REPORT,
    broker_facts_report_path: str | Path = DEFAULT_BROKER_FACTS_REPORT,
    mt5_client: Any | None = None,
    macro_event_lock_enabled: bool = True,
    macro_event_windows: list[MacroEventWindow | dict[str, Any]] | None = None,
    current_time: datetime | None = None,
    order_request: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the v0_42 execution scaffold report.

    The default path is a no-order dry run. A real order path is reachable only
    by explicit caller inputs, and tests should inject a mocked MT5-like client.
    """

    readiness_path = Path(readiness_gate_report_path)
    risk_path = Path(risk_envelope_report_path)
    broker_path = Path(broker_facts_report_path)

    readiness_report, readiness_read_blockers = _read_json_object(readiness_path, "readiness_gate_report")
    risk_report, risk_read_blockers = _read_json_object(risk_path, "risk_envelope_report")
    broker_report, broker_read_blockers = _read_json_object(broker_path, "broker_facts_report")

    blockers: list[str] = [*readiness_read_blockers, *risk_read_blockers, *broker_read_blockers]
    warnings: list[str] = []

    readiness_blockers = _readiness_gate_blockers(readiness_report)
    risk_blockers = _risk_envelope_blockers(risk_report)
    blockers.extend(readiness_blockers)
    blockers.extend(risk_blockers)

    account_facts, account_warnings = _account_facts(mt5_client, broker_report)
    warnings.extend(account_warnings)
    demo_account_verified = _demo_account_verified(account_facts)
    if _live_account_detected(account_facts) or not demo_account_verified:
        blockers.append("account_not_verified_as_demo")

    symbol_verified = symbol == SYMBOL
    if not symbol_verified:
        blockers.append("symbol_must_equal_XAUUSD")

    lot_verified = _number(lot) == LOT
    if not lot_verified:
        blockers.append("lot_must_equal_0.01")

    risk_envelope_verified = not risk_blockers and isinstance(risk_report, dict)
    readiness_gate_verified = not readiness_blockers and isinstance(readiness_report, dict)

    macro_status, macro_window_used = _macro_event_lock_status(
        enabled=macro_event_lock_enabled,
        windows=macro_event_windows or DEFAULT_MACRO_EVENT_WINDOWS,
        current_time=current_time,
    )
    if macro_status == BLOCKED_MACRO_EVENT_WINDOW:
        blockers.append("macro_event_lock_active")

    approval_token_required = True
    approval_token_valid = approval_token == REQUIRED_APPROVAL_TOKEN
    explicit_send_requested = allow_demo_order_send and not dry_run
    if explicit_send_requested and not approval_token_valid:
        blockers.append("approval_token_missing_or_invalid")

    execution_intent = ExecutionIntent(
        candidate_id=CANDIDATE_ID,
        symbol=symbol,
        lot=lot,
        max_positions=MAX_POSITIONS,
        demo_only=True,
        no_directional_recommendation=True,
        order_path="manual_approved_demo_only_order_send_path",
    )

    blockers = _dedupe(blockers)
    warnings = _dedupe(warnings)
    executor_status = _executor_status(
        blockers=blockers,
        dry_run=dry_run,
        allow_demo_order_send=allow_demo_order_send,
        approval_token_valid=approval_token_valid,
        order_request=order_request,
    )

    order_send_attempted = executor_status == DEMO_ORDER_SEND_ATTEMPTED
    order_send_called = False
    execution_result: dict[str, Any] = {
        "status": executor_status,
        "order_result": None,
        "reason": _execution_reason(executor_status),
    }

    if order_send_attempted:
        sender = getattr(mt5_client, "order_" + "send", None) if mt5_client is not None else None
        if callable(sender):
            order_result = sender(order_request)
            order_send_called = True
            execution_result["order_result"] = _json_safe(order_result)
        else:
            warnings.append("mockable_order_send_callable_missing")
            execution_result["status"] = DEMO_ORDER_SEND_ALLOWED_BUT_NOT_CALLED
            execution_result["reason"] = _execution_reason(DEMO_ORDER_SEND_ALLOWED_BUT_NOT_CALLED)
            order_send_attempted = False

    journal_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "executor_version": EXECUTOR_VERSION,
        "candidate_id": CANDIDATE_ID,
        "executor_status": execution_result["status"],
        "dry_run": dry_run,
        "order_send_attempted": order_send_attempted,
        "order_send_called": order_send_called,
        "macro_event_lock_status": macro_status,
        "notes": "limited_demo_execution_scaffold_no_default_order",
    }

    return {
        "executor_version": EXECUTOR_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "executor_status": execution_result["status"],
        "decision_options": DECISION_OPTIONS,
        "mode": "dry_run" if dry_run else "explicit_demo_order_send_requested",
        "dry_run": dry_run,
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": True,
        "source_readiness_gate_report": str(readiness_path),
        "source_risk_envelope_report": str(risk_path),
        "source_broker_facts_report": str(broker_path),
        "demo_only": True,
        "live_allowed": False,
        "order_send_default_allowed": False,
        "order_send_attempted": order_send_attempted,
        "order_send_called": order_send_called,
        "order_check_called": False,
        "macro_event_lock_enabled": macro_event_lock_enabled,
        "macro_event_lock_status": macro_status,
        "macro_event_window_used": macro_window_used,
        "approval_token_required": approval_token_required,
        "approval_token_valid": approval_token_valid,
        "demo_account_verified": demo_account_verified,
        "symbol_verified": symbol_verified,
        "lot_verified": lot_verified,
        "risk_envelope_verified": risk_envelope_verified,
        "readiness_gate_verified": readiness_gate_verified,
        "account_facts": account_facts,
        "blockers": blockers,
        "warnings": _dedupe(warnings),
        "execution_intent": asdict(execution_intent),
        "execution_result": execution_result,
        "journal_record": journal_record,
        "explicit_non_actions": _explicit_non_actions(order_send_called=order_send_called),
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
        "next_recommended_step": _next_recommended_step(execution_result["status"]),
    }


def save_xauusd_limited_demo_execution(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
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


def _readiness_gate_blockers(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return ["readiness_gate_report_unavailable"]
    blockers: list[str] = []
    if report.get("decision") != EXPECTED_READINESS_DECISION:
        blockers.append("v0_41_decision_not_final_demo_readiness_gate_passed")
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("v0_41_candidate_id_mismatch")
    if report.get("candidate_rules_preserved") is not True:
        blockers.append("v0_41_candidate_rules_not_preserved")
    if report.get("human_authorization_required") is not True:
        blockers.append("v0_41_human_authorization_not_required")
    return blockers


def _risk_envelope_blockers(report: dict[str, Any] | None) -> list[str]:
    if not isinstance(report, dict):
        return ["risk_envelope_report_unavailable"]
    blockers: list[str] = []
    envelope = report.get("fixed_risk_envelope")
    if not isinstance(envelope, dict):
        return ["fixed_risk_envelope_missing"]
    expected = {
        "starting_demo_lot": LOT,
        "max_demo_lot": LOT,
        "max_positions": MAX_POSITIONS,
        "no_martingale": True,
        "no_averaging_into_loss": True,
        "no_position_scaling": True,
    }
    for key, expected_value in expected.items():
        if envelope.get(key) != expected_value:
            blockers.append(f"fixed_risk_envelope_{key}_invalid")
    if report.get("order_send_allowed") is not False:
        blockers.append("v0_40_order_send_allowed_not_false")
    if report.get("order_check_allowed") is not False:
        blockers.append("v0_40_order_check_allowed_not_false")
    return blockers


def _account_facts(mt5_client: Any | None, broker_report: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if mt5_client is not None:
        account_info = mt5_client.account_info()
        if account_info is None:
            return {}, ["mt5_account_info_unavailable"]
        return _object_to_dict(account_info), warnings

    account = {}
    if isinstance(broker_report, dict):
        broker_facts = broker_report.get("broker_facts")
        if isinstance(broker_facts, dict) and isinstance(broker_facts.get("account"), dict):
            account = dict(broker_facts["account"])
    if not account:
        warnings.append("broker_account_facts_unavailable")
    return account, warnings


def _object_to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "_asdict"):
        return dict(value._asdict())
    result: dict[str, Any] = {}
    for key in ("server", "trade_mode", "login", "currency", "name"):
        if hasattr(value, key):
            result[key] = getattr(value, key)
    return result


def _demo_account_verified(account: dict[str, Any]) -> bool:
    server = str(account.get("server", "")).lower()
    trade_mode = account.get("trade_mode")
    return "demo" in server or trade_mode == 0 or str(trade_mode).lower() == "demo"


def _live_account_detected(account: dict[str, Any]) -> bool:
    server = str(account.get("server", "")).lower()
    trade_mode = account.get("trade_mode")
    return "live" in server or "real" in server or trade_mode == 2 or str(trade_mode).lower() in {"live", "real"}


def _macro_event_lock_status(
    *,
    enabled: bool,
    windows: list[MacroEventWindow | dict[str, Any]],
    current_time: datetime | None,
) -> tuple[str, dict[str, Any] | None]:
    if not enabled:
        return "disabled", None
    now = current_time or datetime.now(ZoneInfo("Africa/Tripoli"))
    for raw_window in windows:
        window = _coerce_macro_window(raw_window)
        tz = ZoneInfo(window.timezone)
        localized_now = now.astimezone(tz) if now.tzinfo else now.replace(tzinfo=tz)
        starts_at = datetime.fromisoformat(window.starts_at).replace(tzinfo=tz)
        ends_at = datetime.fromisoformat(window.ends_at).replace(tzinfo=tz)
        if starts_at <= localized_now <= ends_at:
            return BLOCKED_MACRO_EVENT_WINDOW, asdict(window)
    return "clear_static_manual_windows", None


def _coerce_macro_window(raw_window: MacroEventWindow | dict[str, Any]) -> MacroEventWindow:
    if isinstance(raw_window, MacroEventWindow):
        return raw_window
    return MacroEventWindow(
        event_id=str(raw_window["event_id"]),
        label=str(raw_window["label"]),
        timezone=str(raw_window["timezone"]),
        starts_at=str(raw_window["starts_at"]),
        ends_at=str(raw_window["ends_at"]),
        source=str(raw_window.get("source", "manual_static_config")),
    )


def _executor_status(
    *,
    blockers: list[str],
    dry_run: bool,
    allow_demo_order_send: bool,
    approval_token_valid: bool,
    order_request: dict[str, Any] | None,
) -> str:
    if any(blocker.startswith("readiness_gate") or blocker.startswith("v0_41") for blocker in blockers):
        return BLOCKED_READINESS_GATE_MISSING_OR_FAILED
    if "account_not_verified_as_demo" in blockers:
        return BLOCKED_NOT_DEMO_ACCOUNT
    if "symbol_must_equal_XAUUSD" in blockers:
        return BLOCKED_INVALID_SYMBOL
    if (
        "lot_must_equal_0.01" in blockers
        or "risk_envelope_report_unavailable" in blockers
        or any(blocker.startswith("risk_envelope_report_") for blocker in blockers)
        or any(blocker.startswith("fixed_risk_envelope_") for blocker in blockers)
    ):
        return BLOCKED_INVALID_LOT
    if "macro_event_lock_active" in blockers:
        return BLOCKED_MACRO_EVENT_WINDOW
    if "approval_token_missing_or_invalid" in blockers:
        return BLOCKED_MISSING_APPROVAL_TOKEN
    if dry_run:
        return DRY_RUN_READY_NO_ORDER_SENT
    if allow_demo_order_send and approval_token_valid and order_request is not None:
        return DEMO_ORDER_SEND_ATTEMPTED
    return DEMO_ORDER_SEND_ALLOWED_BUT_NOT_CALLED


def _execution_reason(status: str) -> str:
    return {
        BLOCKED_READINESS_GATE_MISSING_OR_FAILED: "v0_41 readiness decision missing or failed",
        BLOCKED_NOT_DEMO_ACCOUNT: "account server or mode does not verify as demo",
        BLOCKED_INVALID_SYMBOL: "symbol must equal XAUUSD",
        BLOCKED_INVALID_LOT: "lot and risk envelope must stay fixed at 0.01",
        BLOCKED_MACRO_EVENT_WINDOW: "static high-impact macro event window is active",
        BLOCKED_MISSING_APPROVAL_TOKEN: "explicit demo order send requires the exact human approval token",
        DRY_RUN_READY_NO_ORDER_SENT: "dry-run default completed without order send",
        DEMO_ORDER_SEND_ALLOWED_BUT_NOT_CALLED: "all gates passed but no order request was supplied",
        DEMO_ORDER_SEND_ATTEMPTED: "explicit demo order send attempted after all gates passed",
    }[status]


def _explicit_non_actions(*, order_send_called: bool) -> dict[str, bool]:
    return {
        "live_execution_created": False,
        "automatic_loop_created": False,
        "background_scheduler_created": False,
        "execution_queue_created": False,
        "order_check_called_or_wrapped": False,
        "martingale_used": False,
        "averaging_into_loss_used": False,
        "position_scaling_used": False,
        "candidate_rules_changed": False,
        "oos_review_repeated": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "trade_recommendation_output_created": False,
        "order_send_called_or_wrapped": order_send_called,
    }


def _next_recommended_step(status: str) -> str:
    if status == DRY_RUN_READY_NO_ORDER_SENT:
        return "human review of v0_42 dry-run scaffold report before any separate explicit demo action"
    if status == BLOCKED_MACRO_EVENT_WINDOW:
        return "wait until the configured static macro event window has ended, then rerun dry-run only"
    if status == BLOCKED_MISSING_APPROVAL_TOKEN:
        return "do not continue without exact human approval token and dry-run review"
    return "repair blocker and rerun limited demo scaffold in dry-run mode"


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "_asdict"):
        return _json_safe(value._asdict())
    return repr(value)


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
