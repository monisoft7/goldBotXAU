"""v0_45 read-only live signal snapshot provider for locked XAUUSD candidate."""

from __future__ import annotations

import importlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.execution.xauusd_limited_demo_executor import DEFAULT_MACRO_EVENT_WINDOWS, MacroEventWindow, _macro_event_lock_status
from src.execution.xauusd_signal_to_order_request_builder import (
    ALLOWED_EXECUTABLE_INTERNAL_SIDES,
    BLOCKED_MACRO_EVENT_WINDOW,
    DIRECTION_UNASSIGNED_NON_EXECUTABLE,
    ORDER_REQUEST_BUILT_DRY_RUN_ONLY,
    build_xauusd_signal_order_request_v0_43,
)
from src.research.xauusd_forward_observation_runner import CANDIDATE_ID

SNAPSHOT_VERSION = "v0_45_1"
DEFAULT_OUTPUT = Path("reports") / "xauusd_live_signal_snapshot_v0_45.json"
TIMEFRAMES_REQUESTED = ["M5", "M10"]
TIMEFRAME_CONSTANTS = {"M5": "TIMEFRAME_M5", "M10": "TIMEFRAME_M10"}
DEFAULT_CANDLE_COUNTS = {"M5": 288, "M10": 144}
MIN_CANDLES_BY_TIMEFRAME = {"M5": 144, "M10": 72}
REFERENCE_BLOCKS = ["block_00_06", "block_06_12", "block_12_18"]
RESPONSE_PAIRS = {
    "block_00_06": "block_06_12",
    "block_06_12": "block_12_18",
    "block_12_18": "block_18_24",
}

BLOCKED_MT5_UNAVAILABLE = "blocked_mt5_unavailable"
BLOCKED_SYMBOL_UNAVAILABLE = "blocked_symbol_unavailable"
BLOCKED_INSUFFICIENT_LIVE_CANDLES = "blocked_insufficient_live_candles"
SNAPSHOT_READY_NO_QUALIFIED_SIGNAL = "snapshot_ready_no_qualified_signal"
SNAPSHOT_READY_ORDER_REQUEST_BUILT_DRY_RUN_ONLY = "snapshot_ready_order_request_built_dry_run_only"
SNAPSHOT_READY_SIGNAL_CONFIRMED_DIRECTION_UNASSIGNED = "snapshot_ready_signal_confirmed_direction_unassigned"

STATUS_OPTIONS = [
    BLOCKED_MT5_UNAVAILABLE,
    BLOCKED_SYMBOL_UNAVAILABLE,
    BLOCKED_INSUFFICIENT_LIVE_CANDLES,
    SNAPSHOT_READY_NO_QUALIFIED_SIGNAL,
    SNAPSHOT_READY_ORDER_REQUEST_BUILT_DRY_RUN_ONLY,
    SNAPSHOT_READY_SIGNAL_CONFIRMED_DIRECTION_UNASSIGNED,
    BLOCKED_MACRO_EVENT_WINDOW,
]


def build_xauusd_live_signal_snapshot_v0_45(
    *,
    symbol: str = "XAUUSD",
    dry_run: bool = True,
    mt5_module: Any | None = None,
    current_time: datetime | None = None,
    macro_event_lock_enabled: bool = True,
    macro_event_windows: list[MacroEventWindow | dict[str, Any]] | None = None,
    builder_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fetch read-only M5/M10 candles and build a structured v0_26 signal snapshot."""

    normalized_symbol = symbol.strip()
    blockers: list[str] = []
    warnings: list[str] = []
    mt5_initialized = False
    candles_by_timeframe: dict[str, list[dict[str, Any]]] = {timeframe: [] for timeframe in TIMEFRAMES_REQUESTED}

    macro_status, macro_window_used = _macro_event_lock_status(
        enabled=macro_event_lock_enabled,
        windows=macro_event_windows or DEFAULT_MACRO_EVENT_WINDOWS,
        current_time=current_time,
    )
    if macro_status == BLOCKED_MACRO_EVENT_WINDOW:
        blockers.append("macro_event_lock_active")
        return _report(
            symbol=normalized_symbol,
            dry_run=dry_run,
            snapshot_status=BLOCKED_MACRO_EVENT_WINDOW,
            mt5_initialized=False,
            mt5_shutdown_called=False,
            candles_by_timeframe=candles_by_timeframe,
            current_signal_snapshot=None,
            signal_evaluated=False,
            signal_qualified=False,
            signal_reason="blocked_before_snapshot_fetch:blocked_macro_event_window",
            signal_diagnostics={"macro_event_lock_status": macro_status},
            order_request=None,
            review_request=None,
            direction_assigned=False,
            direction_source="snapshot_blocked_before_signal",
            executable_side_valid=False,
            order_request_present=False,
            order_request_complete=False,
            order_request_validation_status="missing_order_request",
            invalid_order_request_reasons=[],
            blockers=blockers,
            warnings=warnings,
            macro_event_lock_status=macro_status,
            macro_event_window_used=macro_window_used,
        )

    if dry_run is not True:
        blockers.append("dry_run_must_remain_true")

    mt5 = mt5_module
    if mt5 is None:
        try:
            mt5 = importlib.import_module("MetaTrader5")
        except ImportError:
            blockers.append("metatrader5_package_unavailable")
            return _blocked_report(
                symbol=normalized_symbol,
                dry_run=dry_run,
                snapshot_status=BLOCKED_MT5_UNAVAILABLE,
                mt5_initialized=False,
                mt5_shutdown_called=False,
                candles_by_timeframe=candles_by_timeframe,
                blockers=blockers,
                warnings=warnings,
                macro_event_lock_status=macro_status,
                macro_event_window_used=macro_window_used,
                signal_reason="MetaTrader5 package is unavailable",
            )

    try:
        if not mt5.initialize():
            blockers.append(f"mt5_initialize_failed: {_last_error_text(mt5)}")
            return _blocked_report(
                symbol=normalized_symbol,
                dry_run=dry_run,
                snapshot_status=BLOCKED_MT5_UNAVAILABLE,
                mt5_initialized=False,
                mt5_shutdown_called=False,
                candles_by_timeframe=candles_by_timeframe,
                blockers=blockers,
                warnings=warnings,
                macro_event_lock_status=macro_status,
                macro_event_window_used=macro_window_used,
                signal_reason="MT5 initialize failed",
            )
        mt5_initialized = True

        if not _is_gold_symbol(normalized_symbol):
            blockers.append(f"symbol_not_in_gold_scope: {normalized_symbol}")
            return _blocked_report(
                symbol=normalized_symbol,
                dry_run=dry_run,
                snapshot_status=BLOCKED_SYMBOL_UNAVAILABLE,
                mt5_initialized=mt5_initialized,
                mt5_shutdown_called=mt5_initialized,
                candles_by_timeframe=candles_by_timeframe,
                blockers=blockers,
                warnings=warnings,
                macro_event_lock_status=macro_status,
                macro_event_window_used=macro_window_used,
                signal_reason="symbol scope is limited to XAU/GOLD instruments",
            )

        if mt5.symbol_info(normalized_symbol) is None:
            blockers.append(f"symbol_unavailable: {normalized_symbol}")
            return _blocked_report(
                symbol=normalized_symbol,
                dry_run=dry_run,
                snapshot_status=BLOCKED_SYMBOL_UNAVAILABLE,
                mt5_initialized=mt5_initialized,
                mt5_shutdown_called=mt5_initialized,
                candles_by_timeframe=candles_by_timeframe,
                blockers=blockers,
                warnings=warnings,
                macro_event_lock_status=macro_status,
                macro_event_window_used=macro_window_used,
                signal_reason="MT5 symbol_info returned no symbol",
            )

        if not mt5.symbol_select(normalized_symbol, True):
            blockers.append(f"symbol_select_failed: {normalized_symbol}")
            return _blocked_report(
                symbol=normalized_symbol,
                dry_run=dry_run,
                snapshot_status=BLOCKED_SYMBOL_UNAVAILABLE,
                mt5_initialized=mt5_initialized,
                mt5_shutdown_called=mt5_initialized,
                candles_by_timeframe=candles_by_timeframe,
                blockers=blockers,
                warnings=warnings,
                macro_event_lock_status=macro_status,
                macro_event_window_used=macro_window_used,
                signal_reason="MT5 symbol_select failed",
            )

        for timeframe in TIMEFRAMES_REQUESTED:
            mt5_timeframe = getattr(mt5, TIMEFRAME_CONSTANTS[timeframe])
            rates = mt5.copy_rates_from_pos(normalized_symbol, mt5_timeframe, 0, DEFAULT_CANDLE_COUNTS[timeframe])
            candles_by_timeframe[timeframe] = _normalize_rates(rates)

        insufficient = [
            timeframe
            for timeframe in TIMEFRAMES_REQUESTED
            if len(candles_by_timeframe[timeframe]) < MIN_CANDLES_BY_TIMEFRAME[timeframe]
        ]
        if insufficient:
            blockers.append(f"insufficient_live_candles: {','.join(insufficient)}")
            return _blocked_report(
                symbol=normalized_symbol,
                dry_run=dry_run,
                snapshot_status=BLOCKED_INSUFFICIENT_LIVE_CANDLES,
                mt5_initialized=mt5_initialized,
                mt5_shutdown_called=mt5_initialized,
                candles_by_timeframe=candles_by_timeframe,
                blockers=blockers,
                warnings=warnings,
                macro_event_lock_status=macro_status,
                macro_event_window_used=macro_window_used,
                signal_reason=f"insufficient live candles for {', '.join(insufficient)}",
            )

        current_signal_snapshot = _build_current_signal_snapshot(
            symbol=normalized_symbol,
            candles_by_timeframe=candles_by_timeframe,
        )
        builder_report = build_xauusd_signal_order_request_v0_43(
            symbol=normalized_symbol,
            dry_run=True,
            current_signal_snapshot=current_signal_snapshot,
            current_time=current_time,
            macro_event_lock_enabled=macro_event_lock_enabled,
            macro_event_windows=macro_event_windows,
            **(builder_kwargs or {}),
        )
        if builder_report.get("builder_status") == BLOCKED_MACRO_EVENT_WINDOW:
            snapshot_status = BLOCKED_MACRO_EVENT_WINDOW
        elif (
            builder_report.get("signal_qualified") is True
            and builder_report.get("order_request_validation_status") == DIRECTION_UNASSIGNED_NON_EXECUTABLE
        ):
            snapshot_status = SNAPSHOT_READY_SIGNAL_CONFIRMED_DIRECTION_UNASSIGNED
        elif builder_report.get("builder_status") == ORDER_REQUEST_BUILT_DRY_RUN_ONLY:
            snapshot_status = SNAPSHOT_READY_ORDER_REQUEST_BUILT_DRY_RUN_ONLY
        else:
            snapshot_status = SNAPSHOT_READY_NO_QUALIFIED_SIGNAL

        review_request = None
        order_request = builder_report.get("order_request")
        order_request_present = bool(builder_report.get("order_request_present"))
        order_request_complete = bool(builder_report.get("order_request_complete"))
        if snapshot_status == SNAPSHOT_READY_SIGNAL_CONFIRMED_DIRECTION_UNASSIGNED:
            review_request = _review_request_from_builder(builder_report)
            order_request = None
            order_request_present = False
            order_request_complete = False

        return _report(
            symbol=normalized_symbol,
            dry_run=dry_run,
            snapshot_status=snapshot_status,
            mt5_initialized=mt5_initialized,
            mt5_shutdown_called=mt5_initialized,
            candles_by_timeframe=candles_by_timeframe,
            current_signal_snapshot=current_signal_snapshot,
            signal_evaluated=bool(builder_report.get("signal_evaluated")),
            signal_qualified=bool(builder_report.get("signal_qualified")),
            signal_reason=str(builder_report.get("signal_reason")),
            signal_diagnostics=current_signal_snapshot.get("diagnostics", {}),
            order_request=order_request,
            review_request=review_request,
            direction_assigned=bool(builder_report.get("direction_assigned")),
            direction_source=str(builder_report.get("direction_source") or "unknown"),
            executable_side_valid=bool(builder_report.get("executable_side_valid")),
            order_request_present=order_request_present,
            order_request_complete=order_request_complete,
            order_request_validation_status=str(builder_report.get("order_request_validation_status")),
            invalid_order_request_reasons=list(builder_report.get("invalid_order_request_reasons", [])),
            blockers=[*blockers, *builder_report.get("blockers", [])],
            warnings=[*warnings, *builder_report.get("warnings", [])],
            macro_event_lock_status=builder_report.get("macro_event_lock_status", macro_status),
            macro_event_window_used=builder_report.get("macro_event_window_used", macro_window_used),
        )
    except Exception as exc:
        blockers.append(f"snapshot_provider_failed: {exc}")
        return _blocked_report(
            symbol=normalized_symbol,
            dry_run=dry_run,
            snapshot_status=BLOCKED_MT5_UNAVAILABLE,
            mt5_initialized=mt5_initialized,
            mt5_shutdown_called=mt5_initialized,
            candles_by_timeframe=candles_by_timeframe,
            blockers=blockers,
            warnings=warnings,
            macro_event_lock_status=macro_status,
            macro_event_window_used=macro_window_used,
            signal_reason=f"snapshot provider failed: {exc}",
        )
    finally:
        if mt5_initialized:
            mt5.shutdown()


def save_xauusd_live_signal_snapshot(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _blocked_report(
    *,
    symbol: str,
    dry_run: bool,
    snapshot_status: str,
    mt5_initialized: bool,
    mt5_shutdown_called: bool,
    candles_by_timeframe: dict[str, list[dict[str, Any]]],
    blockers: list[str],
    warnings: list[str],
    macro_event_lock_status: str,
    macro_event_window_used: dict[str, Any] | None,
    signal_reason: str,
) -> dict[str, Any]:
    return _report(
        symbol=symbol,
        dry_run=dry_run,
        snapshot_status=snapshot_status,
        mt5_initialized=mt5_initialized,
        mt5_shutdown_called=mt5_shutdown_called,
        candles_by_timeframe=candles_by_timeframe,
        current_signal_snapshot=None,
        signal_evaluated=False,
        signal_qualified=False,
        signal_reason=signal_reason,
        signal_diagnostics={},
        order_request=None,
        review_request=None,
        direction_assigned=False,
        direction_source="snapshot_blocked_before_signal",
        executable_side_valid=False,
        order_request_present=False,
        order_request_complete=False,
        order_request_validation_status="missing_order_request",
        invalid_order_request_reasons=[],
        blockers=blockers,
        warnings=warnings,
        macro_event_lock_status=macro_event_lock_status,
        macro_event_window_used=macro_event_window_used,
    )


def _report(
    *,
    symbol: str,
    dry_run: bool,
    snapshot_status: str,
    mt5_initialized: bool,
    mt5_shutdown_called: bool,
    candles_by_timeframe: dict[str, list[dict[str, Any]]],
    current_signal_snapshot: dict[str, Any] | None,
    signal_evaluated: bool,
    signal_qualified: bool,
    signal_reason: str,
    signal_diagnostics: dict[str, Any],
    order_request: dict[str, Any] | None,
    review_request: dict[str, Any] | None,
    direction_assigned: bool,
    direction_source: str,
    executable_side_valid: bool,
    order_request_present: bool,
    order_request_complete: bool,
    order_request_validation_status: str,
    invalid_order_request_reasons: list[str],
    blockers: list[str],
    warnings: list[str],
    macro_event_lock_status: str,
    macro_event_window_used: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "snapshot_status": snapshot_status,
        "status_options": STATUS_OPTIONS,
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": True,
        "dry_run": dry_run is True,
        "symbol": symbol,
        "timeframes_requested": TIMEFRAMES_REQUESTED,
        "mt5_read_only": True,
        "mt5_initialized": mt5_initialized,
        "mt5_shutdown_called": mt5_shutdown_called,
        "candles_loaded_by_timeframe": {
            timeframe: len(candles_by_timeframe.get(timeframe, [])) for timeframe in TIMEFRAMES_REQUESTED
        },
        "latest_candle_time_by_timeframe": {
            timeframe: _latest_candle_time(candles_by_timeframe.get(timeframe, [])) for timeframe in TIMEFRAMES_REQUESTED
        },
        "current_signal_snapshot_present": current_signal_snapshot is not None,
        "current_signal_snapshot": current_signal_snapshot,
        "signal_evaluated": signal_evaluated,
        "signal_qualified": signal_qualified,
        "signal_reason": signal_reason,
        "signal_diagnostics": signal_diagnostics,
        "direction_assigned": direction_assigned,
        "direction_source": direction_source,
        "executable_side_valid": executable_side_valid,
        "order_request_present": order_request_present,
        "order_request_complete": order_request_complete,
        "order_request_validation_status": order_request_validation_status,
        "invalid_order_request_reasons": invalid_order_request_reasons,
        "order_request": order_request,
        "review_request_present": review_request is not None,
        "review_request": review_request,
        "macro_event_lock_status": macro_event_lock_status,
        "macro_event_window_used": macro_event_window_used,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
        "explicit_non_actions": _explicit_non_actions(),
        "next_recommended_step": _next_recommended_step(snapshot_status),
    }


def _build_current_signal_snapshot(
    *,
    symbol: str,
    candles_by_timeframe: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    diagnostics_by_timeframe = {
        timeframe: _timeframe_diagnostics(candles_by_timeframe[timeframe]) for timeframe in TIMEFRAMES_REQUESTED
    }
    ready_timeframes = [
        timeframe
        for timeframe, diagnostics in diagnostics_by_timeframe.items()
        if diagnostics.get("response_expanded_reference") is True
    ]
    blocked_reasons = [
        f"{timeframe}:{diagnostics.get('reason')}"
        for timeframe, diagnostics in diagnostics_by_timeframe.items()
        if diagnostics.get("response_expanded_reference") is not True
    ]
    qualified = len(ready_timeframes) == len(TIMEFRAMES_REQUESTED)
    reason = (
        "locked_candidate_current_snapshot_expansion_confirmed_across_m5_m10"
        if qualified
        else "current_snapshot_not_qualified:" + ";".join(blocked_reasons)
    )
    latest_ranges = [
        float(candles_by_timeframe[timeframe][-1]["range"])
        for timeframe in TIMEFRAMES_REQUESTED
        if candles_by_timeframe.get(timeframe)
    ]
    stop_distance = max(latest_ranges) if latest_ranges else None

    signal: dict[str, Any] = {
        "qualified": qualified,
        "reason": reason,
        "candidate_id": CANDIDATE_ID,
        "symbol": symbol,
        "side": "direction_unassigned_review_only",
        "direction_source": "locked_candidate_no_deterministic_direction_rule",
        "order_type": "market",
        "action": "prepare_demo_order",
        "risk_reference": "fixed_v0_40_max_trade_risk_1R",
        "exit_rule": "fixed_v0_26_next_block_expansion_review",
        "diagnostics": {
            "candidate_rule_basis": "fixed six-hour block compression then next-block expansion",
            "timeframes_confirmed": ready_timeframes,
            "timeframes_requested": TIMEFRAMES_REQUESTED,
            "by_timeframe": diagnostics_by_timeframe,
            "no_threshold_search": True,
            "no_parameter_grid": True,
            "no_retune": True,
        },
    }
    if stop_distance is not None:
        signal["stop_distance"] = round(stop_distance, 5)
    return signal


def _review_request_from_builder(builder_report: dict[str, Any]) -> dict[str, Any]:
    order_request = builder_report.get("order_request")
    request = dict(order_request) if isinstance(order_request, dict) else {}
    request["review_only"] = True
    request["non_executable_reason"] = DIRECTION_UNASSIGNED_NON_EXECUTABLE
    request["allowed_executable_internal_sides"] = sorted(ALLOWED_EXECUTABLE_INTERNAL_SIDES)
    return request


def _timeframe_diagnostics(candles: list[dict[str, Any]]) -> dict[str, Any]:
    latest_date = str(candles[-1]["timestamp"])[:10] if candles else None
    same_day = [candle for candle in candles if str(candle["timestamp"]).startswith(str(latest_date))]
    average_ranges = _average_ranges_by_block(same_day)
    candidates = [
        block
        for block in REFERENCE_BLOCKS
        if block in average_ranges and RESPONSE_PAIRS[block] in average_ranges
    ]
    if not candidates:
        return {
            "latest_date": latest_date,
            "average_range_by_block": average_ranges,
            "selected_reference_block": None,
            "response_block": None,
            "response_expanded_reference": False,
            "reason": "no_reference_response_block_pair_available",
        }

    selected = min(candidates, key=lambda block: (average_ranges[block], REFERENCE_BLOCKS.index(block)))
    response = RESPONSE_PAIRS[selected]
    reference_range = average_ranges[selected]
    response_range = average_ranges[response]
    expanded = response_range > reference_range
    return {
        "latest_date": latest_date,
        "average_range_by_block": average_ranges,
        "selected_reference_block": selected,
        "response_block": response,
        "reference_average_range": reference_range,
        "response_average_range": response_range,
        "response_expanded_reference": expanded,
        "reason": "next_block_expansion_observed" if expanded else "response_block_did_not_expand_reference",
    }


def _average_ranges_by_block(candles: list[dict[str, Any]]) -> dict[str, float]:
    ranges_by_block: dict[str, list[float]] = {}
    for candle in candles:
        timestamp = datetime.fromisoformat(str(candle["timestamp"]).replace("Z", "+00:00"))
        block = _block_for_hour(timestamp.hour)
        if block is None:
            continue
        ranges_by_block.setdefault(block, []).append(float(candle["range"]))
    return {
        block: round(sum(values) / len(values), 5)
        for block, values in sorted(ranges_by_block.items())
        if values
    }


def _block_for_hour(hour: int) -> str | None:
    if 0 <= hour < 6:
        return "block_00_06"
    if 6 <= hour < 12:
        return "block_06_12"
    if 12 <= hour < 18:
        return "block_12_18"
    if 18 <= hour < 24:
        return "block_18_24"
    return None


def _normalize_rates(rates: Any) -> list[dict[str, Any]]:
    if rates is None:
        return []
    rows_by_timestamp: dict[str, dict[str, Any]] = {}
    for rate in list(rates):
        timestamp = datetime.fromtimestamp(int(_rate_value(rate, "time")), UTC).isoformat()
        high = float(_rate_value(rate, "high"))
        low = float(_rate_value(rate, "low"))
        rows_by_timestamp[timestamp] = {
            "timestamp": timestamp,
            "open": float(_rate_value(rate, "open")),
            "high": high,
            "low": low,
            "close": float(_rate_value(rate, "close")),
            "tick_volume": float(_rate_value(rate, "tick_volume", default=0.0)),
            "spread": float(_rate_value(rate, "spread", default=0.0)),
            "range": round(high - low, 5),
        }
    return sorted(rows_by_timestamp.values(), key=lambda row: str(row["timestamp"]))


def _rate_value(rate: Any, key: str, default: float | None = None) -> Any:
    try:
        return rate[key]
    except (KeyError, IndexError, TypeError, ValueError):
        if hasattr(rate, key):
            return getattr(rate, key)
        if default is not None:
            return default
        raise


def _latest_candle_time(candles: list[dict[str, Any]]) -> str | None:
    if not candles:
        return None
    return str(candles[-1]["timestamp"])


def _is_gold_symbol(symbol: str) -> bool:
    upper = symbol.upper()
    return "XAU" in upper or "GOLD" in upper


def _last_error_text(mt5: Any) -> str:
    last_error = getattr(mt5, "last_error", None)
    if callable(last_error):
        return str(last_error())
    return "unknown_error"


def _explicit_non_actions() -> dict[str, bool]:
    return {
        "order_send_called_or_wrapped": False,
        "order_check_called_or_wrapped": False,
        "live_execution_created": False,
        "background_scheduler_created": False,
        "execution_queue_created": False,
        "auto_execute_order_created": False,
        "candidate_rules_changed": False,
        "new_strategy_added": False,
        "trade_recommendation_output_created": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "oos_review_repeated": False,
        "data_csv_added": False,
    }


def _next_recommended_step(status: str) -> str:
    if status == SNAPSHOT_READY_ORDER_REQUEST_BUILT_DRY_RUN_ONLY:
        return "human review of the dry-run-only internal order request before any separate explicit demo execution task"
    if status == SNAPSHOT_READY_SIGNAL_CONFIRMED_DIRECTION_UNASSIGNED:
        return "define/verify locked candidate direction logic before demo execution"
    if status == SNAPSHOT_READY_NO_QUALIFIED_SIGNAL:
        return "keep dry-run monitoring only; no internal order request exists for review"
    if status == BLOCKED_MACRO_EVENT_WINDOW:
        return "wait until the configured macro event window clears before rebuilding the read-only live signal snapshot"
    if status == BLOCKED_SYMBOL_UNAVAILABLE:
        return "verify the broker symbol name manually and rerun the read-only snapshot provider only"
    if status == BLOCKED_INSUFFICIENT_LIVE_CANDLES:
        return "rerun after enough read-only M5/M10 candles are available"
    return "install or open MT5 for read-only market data access, then rerun the snapshot provider only"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
