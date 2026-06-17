"""v0_40 fixed demo risk envelope design for locked XAUUSD candidate."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from src.research.xauusd_forward_observation_runner import CANDIDATE_ID

ENVELOPE_VERSION = "v0_40"
DEFAULT_BROKER_FACTS_REPORT = Path("reports") / "xauusd_broker_facts_audit_v0_39.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_demo_risk_envelope_v0_40.json"

BLOCKED_MISSING_BROKER_FACTS = "blocked_missing_broker_facts"
BLOCKED_INVALID_VOLUME_CONSTRAINTS = "blocked_invalid_volume_constraints"
BLOCKED_INVALID_TICK_OR_CONTRACT_VALUES = "blocked_invalid_tick_or_contract_values"
DEMO_RISK_ENVELOPE_DESIGN_READY = "demo_risk_envelope_design_ready"

REQUIRED_SYMBOL_FIELDS = [
    "digits",
    "point",
    "trade_contract_size",
    "trade_tick_size",
    "trade_tick_value",
    "volume_min",
    "volume_max",
    "volume_step",
    "spread",
    "spread_float",
    "trade_stops_level",
    "trade_freeze_level",
]


def build_xauusd_demo_risk_envelope_v0_40(
    *,
    broker_facts_report_path: str | Path = DEFAULT_BROKER_FACTS_REPORT,
) -> dict[str, Any]:
    source_path = Path(broker_facts_report_path)
    source_report, read_blockers = _read_json_object(source_path)

    warnings: list[str] = []
    blockers: list[str] = []
    blockers.extend(read_blockers)

    broker_facts = source_report.get("broker_facts") if isinstance(source_report, dict) else None
    symbol_facts = broker_facts.get("symbol") if isinstance(broker_facts, dict) else None
    broker_facts_used = _broker_facts_used(symbol_facts if isinstance(symbol_facts, dict) else {})

    missing_fields = _missing_symbol_fields(symbol_facts)
    blockers.extend(f"missing_broker_fact: symbol.{field}" for field in missing_fields)

    volume_blockers = _volume_blockers(symbol_facts)
    tick_blockers = _tick_or_contract_blockers(symbol_facts)
    blockers.extend(volume_blockers)
    blockers.extend(tick_blockers)

    derived_tick_value = _derived_tick_value(symbol_facts) if not tick_blockers else None
    reported_tick_value = _number(symbol_facts.get("trade_tick_value")) if isinstance(symbol_facts, dict) else None
    conservative_tick_value = None
    if derived_tick_value is not None and reported_tick_value is not None:
        if not math.isclose(derived_tick_value, reported_tick_value, rel_tol=1e-12, abs_tol=1e-12):
            warnings.append("tick_value_contract_size_mismatch")
        conservative_tick_value = max(reported_tick_value, derived_tick_value)

    blockers = _dedupe(blockers)
    warnings = _dedupe(warnings)
    decision = _decision(blockers)
    envelope_status = "completed" if decision == DEMO_RISK_ENVELOPE_DESIGN_READY else "blocked"

    volume_min = _number(symbol_facts.get("volume_min")) if isinstance(symbol_facts, dict) else None

    return {
        "envelope_version": ENVELOPE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "envelope_status": envelope_status,
        "decision": decision,
        "decision_options": [
            BLOCKED_MISSING_BROKER_FACTS,
            BLOCKED_INVALID_VOLUME_CONSTRAINTS,
            BLOCKED_INVALID_TICK_OR_CONTRACT_VALUES,
            DEMO_RISK_ENVELOPE_DESIGN_READY,
        ],
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": True,
        "source_broker_facts_report": str(source_path),
        "broker_facts_used": broker_facts_used,
        "derived_tick_value": derived_tick_value,
        "reported_tick_value": reported_tick_value,
        "conservative_tick_value": conservative_tick_value,
        "warnings": warnings,
        "blockers": blockers,
        "fixed_risk_envelope": _fixed_risk_envelope(volume_min),
        "explicit_non_actions": _explicit_non_actions(),
        "design_only": True,
        "demo_execution_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "broker_execution_path_created": False,
        "execution_queue_created": False,
        "buy_sell_output_allowed": False,
        "trade_recommendation_output_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
        "next_recommended_step": _next_recommended_step(decision),
    }


def save_xauusd_demo_risk_envelope(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json_object(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"broker_facts_report_missing: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"broker_facts_report_invalid_json: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"broker_facts_report_not_object: {path}"]
    return payload, []


def _broker_facts_used(symbol_facts: dict[str, Any]) -> dict[str, Any]:
    return {field: symbol_facts.get(field) for field in REQUIRED_SYMBOL_FIELDS}


def _missing_symbol_fields(symbol_facts: Any) -> list[str]:
    if not isinstance(symbol_facts, dict):
        return REQUIRED_SYMBOL_FIELDS.copy()
    return [field for field in REQUIRED_SYMBOL_FIELDS if symbol_facts.get(field) is None]


def _volume_blockers(symbol_facts: Any) -> list[str]:
    if not isinstance(symbol_facts, dict):
        return []
    if any(symbol_facts.get(field) is None for field in ("volume_min", "volume_max", "volume_step")):
        return []

    volume_min = _number(symbol_facts.get("volume_min"))
    volume_max = _number(symbol_facts.get("volume_max"))
    volume_step = _number(symbol_facts.get("volume_step"))
    blockers: list[str] = []
    if volume_min is None or volume_min <= 0:
        blockers.append("invalid_volume_min")
    if volume_max is None or volume_max <= 0:
        blockers.append("invalid_volume_max")
    if volume_step is None or volume_step <= 0:
        blockers.append("invalid_volume_step")
    if volume_min is not None and volume_max is not None and volume_min > volume_max:
        blockers.append("volume_min_exceeds_volume_max")
    if (
        volume_min is not None
        and volume_step is not None
        and volume_min > 0
        and volume_step > 0
        and not _decimal_multiple(volume_min, volume_step)
    ):
        blockers.append("volume_min_not_aligned_to_volume_step")
    return blockers


def _tick_or_contract_blockers(symbol_facts: Any) -> list[str]:
    if not isinstance(symbol_facts, dict):
        return []
    if any(symbol_facts.get(field) is None for field in ("trade_contract_size", "trade_tick_size", "trade_tick_value")):
        return []

    blockers: list[str] = []
    for field in ("trade_contract_size", "trade_tick_size", "trade_tick_value"):
        value = _number(symbol_facts.get(field))
        if value is None or value <= 0:
            blockers.append(f"invalid_{field}")
    return blockers


def _derived_tick_value(symbol_facts: Any) -> float | None:
    if not isinstance(symbol_facts, dict):
        return None
    contract_size = _number(symbol_facts.get("trade_contract_size"))
    tick_size = _number(symbol_facts.get("trade_tick_size"))
    if contract_size is None or tick_size is None:
        return None
    return contract_size * tick_size


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _decimal_multiple(value: float, step: float) -> bool:
    try:
        value_decimal = Decimal(str(value))
        step_decimal = Decimal(str(step))
    except InvalidOperation:
        return False
    if step_decimal <= 0:
        return False
    return value_decimal % step_decimal == 0


def _decision(blockers: list[str]) -> str:
    if any(blocker.startswith("missing_") or blocker.startswith("broker_facts_report_") for blocker in blockers):
        return BLOCKED_MISSING_BROKER_FACTS
    if any("volume" in blocker for blocker in blockers):
        return BLOCKED_INVALID_VOLUME_CONSTRAINTS
    if any(blocker.startswith("invalid_trade_") for blocker in blockers):
        return BLOCKED_INVALID_TICK_OR_CONTRACT_VALUES
    return DEMO_RISK_ENVELOPE_DESIGN_READY


def _fixed_risk_envelope(volume_min: float | None) -> dict[str, Any]:
    return {
        "max_positions": 1,
        "no_martingale": True,
        "no_averaging_into_loss": True,
        "no_position_scaling": True,
        "no_discretionary_lot_increase": True,
        "emergency_stop_required": True,
        "max_consecutive_losses_before_stop": 2,
        "max_daily_demo_loss_R": 2.0,
        "max_session_demo_loss_R": 1.0,
        "max_trade_risk_R": 1.0,
        "starting_demo_lot": volume_min,
        "max_demo_lot": volume_min,
        "lot_step_must_match": True,
        "symbol_must_match_v0_39": True,
        "broker_facts_must_match_v0_39": True,
    }


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
    if decision == DEMO_RISK_ENVELOPE_DESIGN_READY:
        return "human review of the fixed demo risk envelope before any separate future demo preflight decision"
    if decision == BLOCKED_INVALID_VOLUME_CONSTRAINTS:
        return "repair broker volume constraints in the read-only v0_39 facts before risk envelope approval"
    if decision == BLOCKED_INVALID_TICK_OR_CONTRACT_VALUES:
        return "repair tick value, tick size, or contract size facts before risk envelope approval"
    return "rerun or repair the read-only v0_39 broker facts audit before risk envelope design"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
