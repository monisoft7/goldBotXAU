"""v0_44 bounded dry-run signal watch runner for locked XAUUSD candidate."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.execution.xauusd_signal_to_order_request_builder import (
    BLOCKED_MACRO_EVENT_WINDOW,
    ORDER_REQUEST_BUILT_DRY_RUN_ONLY,
    build_xauusd_signal_order_request_v0_43,
)
from src.research.xauusd_forward_observation_runner import CANDIDATE_ID

WATCH_VERSION = "v0_44"
DEFAULT_OUTPUT = Path("reports") / "xauusd_bounded_signal_watch_v0_44.json"

BLOCKED_INVALID_WATCH_PARAMETERS = "blocked_invalid_watch_parameters"
COMPLETED_NO_QUALIFIED_SIGNAL = "completed_no_qualified_signal"
STOPPED_ORDER_REQUEST_READY_FOR_HUMAN_REVIEW = "stopped_order_request_ready_for_human_review"
FAILED_BUILDER_ERROR = "failed_builder_error"

STATUS_OPTIONS = [
    BLOCKED_MACRO_EVENT_WINDOW,
    BLOCKED_INVALID_WATCH_PARAMETERS,
    COMPLETED_NO_QUALIFIED_SIGNAL,
    STOPPED_ORDER_REQUEST_READY_FOR_HUMAN_REVIEW,
    FAILED_BUILDER_ERROR,
]

BuilderCallable = Callable[..., dict[str, Any]]
SleepCallable = Callable[[float], None]


def run_xauusd_bounded_signal_watch_v0_44(
    *,
    symbol: str = "XAUUSD",
    lot: float = 0.01,
    max_cycles: int = 6,
    interval_seconds: int = 300,
    dry_run: bool = True,
    builder: BuilderCallable = build_xauusd_signal_order_request_v0_43,
    sleep_between_cycles: bool = False,
    sleeper: SleepCallable = time.sleep,
    builder_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the v0_43 builder for a bounded number of dry-run watch cycles."""

    blockers: list[str] = []
    warnings: list[str] = []
    cycle_records: list[dict[str, Any]] = []
    latest_report: dict[str, Any] | None = None

    if max_cycles < 1:
        blockers.append("max_cycles_must_be_at_least_1")
    if interval_seconds < 1:
        blockers.append("interval_seconds_must_be_at_least_1")
    if dry_run is not True:
        blockers.append("dry_run_must_remain_true")

    if blockers:
        return _watch_report(
            symbol=symbol,
            lot=lot,
            max_cycles=max_cycles,
            interval_seconds=interval_seconds,
            cycles_completed=0,
            stopped_early=False,
            stop_reason=BLOCKED_INVALID_WATCH_PARAMETERS,
            watch_status=BLOCKED_INVALID_WATCH_PARAMETERS,
            latest_report=None,
            cycle_records=cycle_records,
            blockers=blockers,
            warnings=warnings,
        )

    kwargs = dict(builder_kwargs or {})
    for cycle_number in range(1, max_cycles + 1):
        try:
            latest_report = builder(
                symbol=symbol,
                lot=lot,
                dry_run=True,
                **kwargs,
            )
        except Exception as exc:
            blockers.append(f"builder_error:{exc}")
            cycle_records.append(_failed_cycle_record(cycle_number, exc))
            return _watch_report(
                symbol=symbol,
                lot=lot,
                max_cycles=max_cycles,
                interval_seconds=interval_seconds,
                cycles_completed=len(cycle_records),
                stopped_early=True,
                stop_reason=FAILED_BUILDER_ERROR,
                watch_status=FAILED_BUILDER_ERROR,
                latest_report=None,
                cycle_records=cycle_records,
                blockers=blockers,
                warnings=warnings,
            )

        cycle_records.append(_cycle_record(cycle_number, latest_report))

        if latest_report.get("macro_event_lock_status") == BLOCKED_MACRO_EVENT_WINDOW:
            return _watch_report(
                symbol=symbol,
                lot=lot,
                max_cycles=max_cycles,
                interval_seconds=interval_seconds,
                cycles_completed=len(cycle_records),
                stopped_early=True,
                stop_reason=BLOCKED_MACRO_EVENT_WINDOW,
                watch_status=BLOCKED_MACRO_EVENT_WINDOW,
                latest_report=latest_report,
                cycle_records=cycle_records,
                blockers=_dedupe([*blockers, "macro_event_lock_active"]),
                warnings=warnings,
            )

        if latest_report.get("order_request_complete") is True:
            return _watch_report(
                symbol=symbol,
                lot=lot,
                max_cycles=max_cycles,
                interval_seconds=interval_seconds,
                cycles_completed=len(cycle_records),
                stopped_early=True,
                stop_reason=STOPPED_ORDER_REQUEST_READY_FOR_HUMAN_REVIEW,
                watch_status=STOPPED_ORDER_REQUEST_READY_FOR_HUMAN_REVIEW,
                latest_report=latest_report,
                cycle_records=cycle_records,
                blockers=blockers,
                warnings=warnings,
            )

        if sleep_between_cycles and cycle_number < max_cycles:
            sleeper(float(interval_seconds))

    return _watch_report(
        symbol=symbol,
        lot=lot,
        max_cycles=max_cycles,
        interval_seconds=interval_seconds,
        cycles_completed=len(cycle_records),
        stopped_early=False,
        stop_reason=COMPLETED_NO_QUALIFIED_SIGNAL,
        watch_status=COMPLETED_NO_QUALIFIED_SIGNAL,
        latest_report=latest_report,
        cycle_records=cycle_records,
        blockers=blockers,
        warnings=warnings,
    )


def save_xauusd_bounded_signal_watch(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _watch_report(
    *,
    symbol: str,
    lot: float,
    max_cycles: int,
    interval_seconds: int,
    cycles_completed: int,
    stopped_early: bool,
    stop_reason: str,
    watch_status: str,
    latest_report: dict[str, Any] | None,
    cycle_records: list[dict[str, Any]],
    blockers: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    macro_status = _latest_value(latest_report, "macro_event_lock_status", "not_evaluated")
    return {
        "watch_version": WATCH_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "watch_status": watch_status,
        "status_options": STATUS_OPTIONS,
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": True,
        "dry_run": True,
        "symbol": symbol,
        "lot": lot,
        "max_cycles": max_cycles,
        "interval_seconds": interval_seconds,
        "cycles_completed": cycles_completed,
        "stopped_early": stopped_early,
        "stop_reason": stop_reason,
        "latest_builder_status": _latest_value(latest_report, "builder_status"),
        "latest_signal_qualified": bool(_latest_value(latest_report, "signal_qualified", False)),
        "latest_order_request_present": bool(_latest_value(latest_report, "order_request_present", False)),
        "latest_order_request_complete": bool(_latest_value(latest_report, "order_request_complete", False)),
        "latest_order_request": _latest_value(latest_report, "order_request"),
        "cycle_records": cycle_records,
        "macro_event_lock_enabled": bool(_latest_value(latest_report, "macro_event_lock_enabled", True)),
        "macro_event_lock_status": macro_status,
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
        "explicit_non_actions": _explicit_non_actions(),
        "next_recommended_step": _next_recommended_step(watch_status),
    }


def _cycle_record(cycle_number: int, builder_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "cycle_number": cycle_number,
        "builder_status": builder_report.get("builder_status"),
        "signal_qualified": bool(builder_report.get("signal_qualified", False)),
        "order_request_present": bool(builder_report.get("order_request_present", False)),
        "order_request_complete": bool(builder_report.get("order_request_complete", False)),
        "macro_event_lock_status": builder_report.get("macro_event_lock_status"),
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
    }


def _failed_cycle_record(cycle_number: int, exc: Exception) -> dict[str, Any]:
    return {
        "cycle_number": cycle_number,
        "builder_status": FAILED_BUILDER_ERROR,
        "error": str(exc),
        "signal_qualified": False,
        "order_request_present": False,
        "order_request_complete": False,
        "macro_event_lock_status": "not_evaluated",
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
    }


def _latest_value(report: dict[str, Any] | None, key: str, default: Any = None) -> Any:
    if not isinstance(report, dict):
        return default
    return report.get(key, default)


def _explicit_non_actions() -> dict[str, bool]:
    return {
        "order_send_called_or_wrapped": False,
        "order_check_called_or_wrapped": False,
        "live_execution_created": False,
        "background_scheduler_created": False,
        "unbounded_loop_created": False,
        "execution_queue_created": False,
        "auto_execute_order_created": False,
        "candidate_rules_changed": False,
        "new_strategy_added": False,
        "trade_recommendation_output_created": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "oos_review_repeated": False,
    }


def _next_recommended_step(status: str) -> str:
    if status == STOPPED_ORDER_REQUEST_READY_FOR_HUMAN_REVIEW:
        return "human review of the dry-run-only internal order request before any separate explicit demo execution task"
    if status == COMPLETED_NO_QUALIFIED_SIGNAL:
        return "keep bounded dry-run watch only; no internal order request exists for review"
    if status == BLOCKED_MACRO_EVENT_WINDOW:
        return "wait until the configured macro event window clears before another bounded dry-run watch"
    if status == BLOCKED_INVALID_WATCH_PARAMETERS:
        return "rerun with max_cycles >= 1, interval_seconds >= 1, and dry_run true"
    return "repair builder error and rerun bounded dry-run watch only"


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
