"""v0_39 read-only broker facts audit for locked XAUUSD candidate."""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research.xauusd_forward_observation_runner import CANDIDATE_ID

AUDIT_VERSION = "v0_39"
DEFAULT_OUTPUT = Path("reports") / "xauusd_broker_facts_audit_v0_39.json"

BLOCKED_MT5_UNAVAILABLE = "blocked_mt5_unavailable"
BLOCKED_SYMBOL_UNAVAILABLE = "blocked_symbol_unavailable"
BLOCKED_MISSING_CRITICAL_BROKER_FACTS = "blocked_missing_critical_broker_facts"
BROKER_FACTS_AUDIT_READY_FOR_RISK_ENVELOPE_DESIGN = "broker_facts_audit_ready_for_risk_envelope_design"

SYMBOL_FACT_FIELDS = [
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
    "trade_mode",
    "trade_exemode",
    "filling_mode",
    "order_mode",
    "trade_stops_level",
    "trade_freeze_level",
    "swap_long",
    "swap_short",
    "visible",
]

ACCOUNT_FACT_FIELDS = [
    "server",
    "currency",
    "trade_mode",
]

CRITICAL_FACT_PATHS = [
    "symbol.exists",
    "symbol.digits",
    "symbol.point",
    "symbol.trade_contract_size",
    "symbol.trade_tick_size",
    "symbol.trade_tick_value",
    "symbol.volume_min",
    "symbol.volume_max",
    "symbol.volume_step",
    "symbol.trade_mode",
    "symbol.trade_exemode",
    "symbol.filling_mode",
    "symbol.order_mode",
    "symbol.trade_stops_level",
    "symbol.trade_freeze_level",
    "account.server",
    "account.currency",
    "account.trade_mode",
]


def build_xauusd_broker_facts_audit_v0_39(
    *,
    symbol: str = "XAUUSD",
    mt5_module: Any | None = None,
) -> dict[str, Any]:
    normalized_symbol = symbol.strip()
    warnings: list[str] = []
    broker_fact_blockers: list[str] = []
    mt5_initialized = False
    mt5_shutdown_called = False
    broker_facts = _empty_broker_facts(normalized_symbol)

    mt5 = mt5_module
    if mt5 is None:
        try:
            mt5 = importlib.import_module("MetaTrader5")
        except ImportError:
            broker_fact_blockers.append("metatrader5_package_unavailable")
            return _report(
                symbol=normalized_symbol,
                audit_status="blocked",
                decision=BLOCKED_MT5_UNAVAILABLE,
                mt5_initialized=False,
                mt5_shutdown_called=False,
                broker_facts=broker_facts,
                broker_fact_blockers=broker_fact_blockers,
                warnings=warnings,
            )

    try:
        if not mt5.initialize():
            broker_fact_blockers.append(f"mt5_initialize_failed: {_last_error_text(mt5)}")
            return _report(
                symbol=normalized_symbol,
                audit_status="blocked",
                decision=BLOCKED_MT5_UNAVAILABLE,
                mt5_initialized=False,
                mt5_shutdown_called=False,
                broker_facts=broker_facts,
                broker_fact_blockers=broker_fact_blockers,
                warnings=warnings,
            )
        mt5_initialized = True

        symbol_info = mt5.symbol_info(normalized_symbol)
        account_info = mt5.account_info()

        broker_facts = _broker_facts_from_metadata(normalized_symbol, symbol_info, account_info)
        if symbol_info is None:
            broker_fact_blockers.append(f"symbol_unavailable: {normalized_symbol}")
            decision = BLOCKED_SYMBOL_UNAVAILABLE
        else:
            missing_facts = _missing_critical_facts(broker_facts)
            if missing_facts:
                broker_fact_blockers.extend(f"missing_critical_fact: {fact}" for fact in missing_facts)
                decision = BLOCKED_MISSING_CRITICAL_BROKER_FACTS
            else:
                decision = BROKER_FACTS_AUDIT_READY_FOR_RISK_ENVELOPE_DESIGN

        if account_info is None:
            warnings.append("account_info_unavailable")
    except Exception as exc:
        broker_fact_blockers.append(f"mt5_metadata_audit_failed: {exc}")
        decision = BLOCKED_MT5_UNAVAILABLE
    finally:
        if mt5_initialized:
            mt5.shutdown()
            mt5_shutdown_called = True

    return _report(
        symbol=normalized_symbol,
        audit_status="completed" if decision == BROKER_FACTS_AUDIT_READY_FOR_RISK_ENVELOPE_DESIGN else "blocked",
        decision=decision,
        mt5_initialized=mt5_initialized,
        mt5_shutdown_called=mt5_shutdown_called,
        broker_facts=broker_facts,
        broker_fact_blockers=broker_fact_blockers,
        warnings=warnings,
    )


def save_xauusd_broker_facts_audit(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _report(
    *,
    symbol: str,
    audit_status: str,
    decision: str,
    mt5_initialized: bool,
    mt5_shutdown_called: bool,
    broker_facts: dict[str, Any],
    broker_fact_blockers: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    missing_facts = _missing_critical_facts(broker_facts)

    return {
        "audit_version": AUDIT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_status": audit_status,
        "decision": decision,
        "decision_options": [
            BLOCKED_MT5_UNAVAILABLE,
            BLOCKED_SYMBOL_UNAVAILABLE,
            BLOCKED_MISSING_CRITICAL_BROKER_FACTS,
            BROKER_FACTS_AUDIT_READY_FOR_RISK_ENVELOPE_DESIGN,
        ],
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": True,
        "design_or_read_only": True,
        "symbol": symbol,
        "mt5_read_only_metadata_access": True,
        "mt5_initialized": mt5_initialized,
        "mt5_shutdown_called": mt5_shutdown_called,
        "order_send_created": False,
        "order_send_called": False,
        "order_check_created": False,
        "order_check_called": False,
        "execution_queue_created": False,
        "broker_execution_path_created": False,
        "buy_sell_output_allowed": False,
        "trade_recommendation_output_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
        "broker_facts": broker_facts,
        "missing_facts": missing_facts,
        "broker_fact_blockers": _dedupe(broker_fact_blockers),
        "warnings": _dedupe(warnings),
        "next_recommended_step": _next_recommended_step(decision),
    }


def _broker_facts_from_metadata(symbol: str, symbol_info: Any | None, account_info: Any | None) -> dict[str, Any]:
    facts = _empty_broker_facts(symbol)
    symbol_facts = facts["symbol"]
    account_facts = facts["account"]

    symbol_facts["exists"] = symbol_info is not None
    if symbol_info is not None:
        for field in SYMBOL_FACT_FIELDS:
            symbol_facts[field] = _metadata_value(symbol_info, field)

    if account_info is not None:
        for field in ACCOUNT_FACT_FIELDS:
            account_facts[field] = _metadata_value(account_info, field)

    return facts


def _empty_broker_facts(symbol: str) -> dict[str, Any]:
    return {
        "symbol": {
            "name": symbol,
            "exists": False,
            **{field: None for field in SYMBOL_FACT_FIELDS},
        },
        "account": {
            field: None for field in ACCOUNT_FACT_FIELDS
        },
    }


def _metadata_value(metadata: Any, field: str) -> Any:
    if isinstance(metadata, dict):
        return metadata.get(field)
    if hasattr(metadata, "_asdict"):
        values = metadata._asdict()
        if isinstance(values, dict):
            return values.get(field)
    return getattr(metadata, field, None)


def _missing_critical_facts(broker_facts: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for path in CRITICAL_FACT_PATHS:
        section, key = path.split(".", 1)
        section_values = broker_facts.get(section)
        value = section_values.get(key) if isinstance(section_values, dict) else None
        if value is None or value is False:
            missing.append(path)
    return missing


def _last_error_text(mt5: Any) -> str:
    last_error = getattr(mt5, "last_error", None)
    if callable(last_error):
        return str(last_error())
    return "unknown_error"


def _next_recommended_step(decision: str) -> str:
    if decision == BROKER_FACTS_AUDIT_READY_FOR_RISK_ENVELOPE_DESIGN:
        return "design a separate human-approved risk envelope using the read-only broker facts only"
    if decision == BLOCKED_SYMBOL_UNAVAILABLE:
        return "verify the broker symbol name manually and rerun the read-only broker facts audit only"
    if decision == BLOCKED_MISSING_CRITICAL_BROKER_FACTS:
        return "repair missing broker metadata coverage before any risk envelope design"
    return "install or open MT5 for read-only metadata access, then rerun the broker facts audit only"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
