"""v0_50 read-only MT5 historical data expansion feasibility audit."""

from __future__ import annotations

import importlib
import json
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

AUDIT_VERSION = "v0_50"
CANDIDATE_ID = "trend_pullback_continuation_directional"
DEFAULT_OUTPUT = Path("reports") / "xauusd_historical_data_expansion_feasibility_v0_50.json"
DEFAULT_TIMEFRAMES = ("M5", "M10")
TIMEFRAME_SECONDS = {"M5": 5 * 60, "M10": 10 * 60}
MT5_TIMEFRAME_NAMES = {"M5": "TIMEFRAME_M5", "M10": "TIMEFRAME_M10"}
MIN_USABLE_M5_CANDLES = 500
MAX_REPORTED_GAPS = 100

EXPANSION_AVAILABLE = "expansion_data_available"
EXPANSION_PARTIAL = "expansion_data_partially_available"
EXPANSION_UNAVAILABLE = "expansion_data_unavailable"
BLOCKED_MT5_UNAVAILABLE = "blocked_mt5_unavailable"
AUDIT_FAILED = "audit_failed"


def build_xauusd_historical_data_expansion_feasibility_audit_v0_50(
    *,
    symbol: str = "XAUUSD",
    from_date: str,
    to_date: str,
    mt5_module: Any | None = None,
    timeframes: tuple[str, ...] = DEFAULT_TIMEFRAMES,
    min_usable_m5_candles: int = MIN_USABLE_M5_CANDLES,
) -> dict[str, Any]:
    """Check whether older low-timeframe XAUUSD data is feasible to collect."""
    normalized_symbol = symbol.strip()
    requested_from = _date_start_utc(from_date)
    requested_to = _date_end_utc(to_date)
    warnings: list[str] = ["feasibility_audit_only_no_strategy_evaluation_no_oos"]
    blockers: list[str] = []
    mt5_initialized = False
    mt5_shutdown_called = False

    mt5 = mt5_module
    if mt5 is None:
        try:
            mt5 = importlib.import_module("MetaTrader5")
        except ImportError:
            blockers.append("metatrader5_package_unavailable")
            return _base_report(
                audit_status=BLOCKED_MT5_UNAVAILABLE,
                symbol=normalized_symbol,
                requested_from_date=from_date,
                requested_to_date=to_date,
                mt5_initialized=False,
                mt5_shutdown_called=False,
                available_oldest_candle_time=None,
                available_newest_candle_time=None,
                requested_range_available=False,
                candle_count_by_timeframe={timeframe: 0 for timeframe in timeframes},
                missing_range_gaps=[],
                missing_range_gap_count=0,
                missing_range_gaps_truncated=False,
                data_expansion_feasible=False,
                blockers=blockers,
                warnings=warnings,
                next_recommended_step="install or connect MT5 read-only data access before rerunning v0_50",
            )

    try:
        if not mt5.initialize():
            blockers.append(_last_error_text(mt5))
            return _base_report(
                audit_status=BLOCKED_MT5_UNAVAILABLE,
                symbol=normalized_symbol,
                requested_from_date=from_date,
                requested_to_date=to_date,
                mt5_initialized=False,
                mt5_shutdown_called=False,
                available_oldest_candle_time=None,
                available_newest_candle_time=None,
                requested_range_available=False,
                candle_count_by_timeframe={timeframe: 0 for timeframe in timeframes},
                missing_range_gaps=[],
                missing_range_gap_count=0,
                missing_range_gaps_truncated=False,
                data_expansion_feasible=False,
                blockers=blockers,
                warnings=warnings,
                next_recommended_step="repair MT5 read-only initialization before rerunning v0_50",
            )
        mt5_initialized = True

        if mt5.symbol_info(normalized_symbol) is None:
            blockers.append(f"symbol_unavailable:{normalized_symbol}")
            mt5.shutdown()
            mt5_shutdown_called = True
            return _base_report(
                audit_status=EXPANSION_UNAVAILABLE,
                symbol=normalized_symbol,
                requested_from_date=from_date,
                requested_to_date=to_date,
                mt5_initialized=mt5_initialized,
                mt5_shutdown_called=mt5_shutdown_called,
                available_oldest_candle_time=None,
                available_newest_candle_time=None,
                requested_range_available=False,
                candle_count_by_timeframe={timeframe: 0 for timeframe in timeframes},
                missing_range_gaps=[],
                missing_range_gap_count=0,
                missing_range_gaps_truncated=False,
                data_expansion_feasible=False,
                blockers=blockers,
                warnings=warnings,
                next_recommended_step="stop this candidate branch or broaden non-OOS research",
            )
        if not mt5.symbol_select(normalized_symbol, True):
            blockers.append(f"symbol_select_failed:{normalized_symbol}")
            mt5.shutdown()
            mt5_shutdown_called = True
            return _base_report(
                audit_status=EXPANSION_UNAVAILABLE,
                symbol=normalized_symbol,
                requested_from_date=from_date,
                requested_to_date=to_date,
                mt5_initialized=mt5_initialized,
                mt5_shutdown_called=mt5_shutdown_called,
                available_oldest_candle_time=None,
                available_newest_candle_time=None,
                requested_range_available=False,
                candle_count_by_timeframe={timeframe: 0 for timeframe in timeframes},
                missing_range_gaps=[],
                missing_range_gap_count=0,
                missing_range_gaps_truncated=False,
                data_expansion_feasible=False,
                blockers=blockers,
                warnings=warnings,
                next_recommended_step="stop this candidate branch or broaden non-OOS research",
            )

        availability = _availability_by_timeframe(
            mt5=mt5,
            symbol=normalized_symbol,
            requested_from=requested_from,
            requested_to=requested_to,
            timeframes=timeframes,
        )
        candle_count_by_timeframe = {
            timeframe: details["candle_count"] for timeframe, details in availability.items()
        }
        all_times = [
            value
            for details in availability.values()
            for value in (details["oldest_candle_time"], details["newest_candle_time"])
            if value is not None
        ]
        oldest = min(all_times) if all_times else None
        newest = max(all_times) if all_times else None
        raw_gaps = [
            gap
            for details in availability.values()
            for gap in details["missing_range_gaps"]
        ]
        gaps = raw_gaps[:MAX_REPORTED_GAPS]
        if len(raw_gaps) > MAX_REPORTED_GAPS:
            warnings.append(f"missing_range_gaps_truncated_to_{MAX_REPORTED_GAPS}_examples")
        requested_range_available = _requested_range_available(
            availability=availability,
            requested_from=requested_from,
            requested_to=requested_to,
        )
        usable_m5_candles = int(candle_count_by_timeframe.get("M5", 0))
        enough_usable_candles = usable_m5_candles >= min_usable_m5_candles

        if requested_range_available:
            audit_status = EXPANSION_AVAILABLE
            data_expansion_feasible = True
            next_step = "v0_51 fixed-rule expanded train/validation retest, no OOS"
        elif enough_usable_candles:
            audit_status = EXPANSION_PARTIAL
            data_expansion_feasible = True
            warnings.append("requested_range_partially_available_with_enough_usable_m5_candles")
            next_step = "v0_51 fixed-rule expanded train/validation retest on available older range only, no OOS"
        elif any(count > 0 for count in candle_count_by_timeframe.values()):
            audit_status = EXPANSION_PARTIAL
            data_expansion_feasible = False
            blockers.append("partial_data_below_minimum_usable_m5_candles")
            next_step = "stop this candidate branch or broaden non-OOS research"
        else:
            audit_status = EXPANSION_UNAVAILABLE
            data_expansion_feasible = False
            blockers.append("no_requested_older_low_timeframe_candles_available")
            next_step = "stop this candidate branch or broaden non-OOS research"

        mt5.shutdown()
        mt5_shutdown_called = True
        return _base_report(
            audit_status=audit_status,
            symbol=normalized_symbol,
            requested_from_date=from_date,
            requested_to_date=to_date,
            mt5_initialized=mt5_initialized,
            mt5_shutdown_called=mt5_shutdown_called,
            available_oldest_candle_time=oldest,
            available_newest_candle_time=newest,
            requested_range_available=requested_range_available,
            candle_count_by_timeframe=candle_count_by_timeframe,
            missing_range_gaps=gaps,
            missing_range_gap_count=len(raw_gaps),
            missing_range_gaps_truncated=len(raw_gaps) > MAX_REPORTED_GAPS,
            data_expansion_feasible=data_expansion_feasible,
            blockers=blockers,
            warnings=warnings,
            next_recommended_step=next_step,
        )
    except Exception as exc:
        blockers.append(f"audit_exception:{type(exc).__name__}:{exc}")
        if mt5_initialized and not mt5_shutdown_called:
            mt5.shutdown()
            mt5_shutdown_called = True
        return _base_report(
            audit_status=AUDIT_FAILED,
            symbol=normalized_symbol,
            requested_from_date=from_date,
            requested_to_date=to_date,
            mt5_initialized=mt5_initialized,
            mt5_shutdown_called=mt5_shutdown_called,
            available_oldest_candle_time=None,
            available_newest_candle_time=None,
            requested_range_available=False,
            candle_count_by_timeframe={timeframe: 0 for timeframe in timeframes},
            missing_range_gaps=[],
            missing_range_gap_count=0,
            missing_range_gaps_truncated=False,
            data_expansion_feasible=False,
            blockers=blockers,
            warnings=warnings,
            next_recommended_step="repair audit error before deciding on data expansion",
        )


def save_xauusd_historical_data_expansion_feasibility_audit(
    report: dict[str, Any],
    output: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _availability_by_timeframe(
    *,
    mt5: Any,
    symbol: str,
    requested_from: datetime,
    requested_to: datetime,
    timeframes: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    availability: dict[str, dict[str, Any]] = {}
    for timeframe in timeframes:
        mt5_timeframe = getattr(mt5, MT5_TIMEFRAME_NAMES[timeframe])
        rates = mt5.copy_rates_range(symbol, mt5_timeframe, requested_from, requested_to)
        timestamps = _rate_timestamps(rates)
        availability[timeframe] = {
            "candle_count": len(timestamps),
            "oldest_candle_time": _format_time(timestamps[0]) if timestamps else None,
            "newest_candle_time": _format_time(timestamps[-1]) if timestamps else None,
            "missing_range_gaps": _missing_gaps(
                timeframe=timeframe,
                timestamps=timestamps,
                requested_from=requested_from,
                requested_to=requested_to,
            ),
        }
    return availability


def _requested_range_available(
    *,
    availability: dict[str, dict[str, Any]],
    requested_from: datetime,
    requested_to: datetime,
) -> bool:
    m5 = availability.get("M5", {})
    oldest = _parse_report_time(m5.get("oldest_candle_time"))
    newest = _parse_report_time(m5.get("newest_candle_time"))
    if oldest is None or newest is None:
        return False
    return oldest <= requested_from and newest.date() >= requested_to.date() and not m5.get("missing_range_gaps")


def _missing_gaps(
    *,
    timeframe: str,
    timestamps: list[datetime],
    requested_from: datetime,
    requested_to: datetime,
) -> list[dict[str, Any]]:
    if not timestamps:
        return [
            {
                "timeframe": timeframe,
                "gap_type": "entire_requested_range_missing",
                "gap_start": _format_time(requested_from),
                "gap_end": _format_time(requested_to),
            }
        ]

    gaps: list[dict[str, Any]] = []
    expected_seconds = TIMEFRAME_SECONDS[timeframe]
    if timestamps[0] > requested_from:
        gaps.append(
            {
                "timeframe": timeframe,
                "gap_type": "missing_start_of_requested_range",
                "gap_start": _format_time(requested_from),
                "gap_end": _format_time(timestamps[0]),
            }
        )
    if timestamps[-1].date() < requested_to.date():
        gaps.append(
            {
                "timeframe": timeframe,
                "gap_type": "missing_end_of_requested_range",
                "gap_start": _format_time(timestamps[-1]),
                "gap_end": _format_time(requested_to),
            }
        )
    for previous, current in zip(timestamps, timestamps[1:]):
        delta_seconds = int((current - previous).total_seconds())
        if delta_seconds > expected_seconds * 3:
            gaps.append(
                {
                    "timeframe": timeframe,
                    "gap_type": "internal_gap",
                    "gap_start": _format_time(previous),
                    "gap_end": _format_time(current),
                    "observed_gap_seconds": delta_seconds,
                    "expected_seconds": expected_seconds,
                }
            )
    return gaps


def _base_report(
    *,
    audit_status: str,
    symbol: str,
    requested_from_date: str,
    requested_to_date: str,
    mt5_initialized: bool,
    mt5_shutdown_called: bool,
    available_oldest_candle_time: str | None,
    available_newest_candle_time: str | None,
    requested_range_available: bool,
    candle_count_by_timeframe: dict[str, int],
    missing_range_gaps: list[dict[str, Any]],
    missing_range_gap_count: int,
    missing_range_gaps_truncated: bool,
    data_expansion_feasible: bool,
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    return {
        "audit_version": AUDIT_VERSION,
        "audit_status": audit_status,
        "symbol": symbol,
        "requested_from_date": requested_from_date,
        "requested_to_date": requested_to_date,
        "mt5_read_only": True,
        "mt5_initialized": mt5_initialized,
        "mt5_shutdown_called": mt5_shutdown_called,
        "available_oldest_candle_time": available_oldest_candle_time,
        "available_newest_candle_time": available_newest_candle_time,
        "requested_range_available": requested_range_available,
        "candle_count_by_timeframe": candle_count_by_timeframe,
        "missing_range_gaps": missing_range_gaps,
        "missing_range_gap_count": missing_range_gap_count,
        "missing_range_gaps_truncated": missing_range_gaps_truncated,
        "data_expansion_feasible": data_expansion_feasible,
        "proposed_expanded_train_validation_plan": _expanded_plan(
            requested_from_date=requested_from_date,
            requested_to_date=requested_to_date,
            data_expansion_feasible=data_expansion_feasible,
            candle_count_by_timeframe=candle_count_by_timeframe,
        ),
        "candidate_to_retest_later": CANDIDATE_ID,
        "candidate_rules_preserved": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "trade_recommendation_output_present": False,
        "data_csv_added_to_git": False,
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def _expanded_plan(
    *,
    requested_from_date: str,
    requested_to_date: str,
    data_expansion_feasible: bool,
    candle_count_by_timeframe: dict[str, int],
) -> dict[str, Any]:
    return {
        "plan_status": "ready_for_v0_51_fixed_rule_retest" if data_expansion_feasible else "not_ready",
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": True,
        "expanded_evidence_range": {
            "from_date": requested_from_date,
            "to_date": requested_to_date,
        },
        "timeframes": sorted(candle_count_by_timeframe),
        "available_candles_by_timeframe": candle_count_by_timeframe,
        "next_audit": "v0_51_fixed_rule_expanded_train_validation_retest_no_oos"
        if data_expansion_feasible
        else None,
        "oos_allowed": False,
        "retune_allowed": False,
        "threshold_search_allowed": False,
        "parameter_grid_allowed": False,
        "demo_execution_allowed": False,
    }


def _rate_timestamps(rates: Any) -> list[datetime]:
    if rates is None:
        return []
    timestamps: list[datetime] = []
    for rate in list(rates):
        timestamp = _rate_value(rate, "time")
        timestamps.append(datetime.fromtimestamp(int(timestamp), UTC).replace(tzinfo=None))
    return sorted(set(timestamps))


def _rate_value(rate: Any, key: str) -> Any:
    try:
        return rate[key]
    except (KeyError, IndexError, TypeError, ValueError):
        if hasattr(rate, key):
            return getattr(rate, key)
        raise


def _date_start_utc(value: str) -> datetime:
    return datetime.combine(date.fromisoformat(value), time.min, tzinfo=UTC).replace(tzinfo=None)


def _date_end_utc(value: str) -> datetime:
    return datetime.combine(date.fromisoformat(value), time.max, tzinfo=UTC).replace(tzinfo=None)


def _format_time(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def _parse_report_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    return datetime.fromisoformat(value)


def _last_error_text(mt5: Any) -> str:
    last_error = getattr(mt5, "last_error", None)
    if callable(last_error):
        return f"mt5_initialize_failed:{last_error()}"
    return "mt5_initialize_failed"


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "mt5_read_only": True,
        "strategy_evaluation": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
        "trade_recommendation_output_present": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "oos_used": False,
        "repeated_oos_review": False,
        "data_csv_added_to_git": False,
    }
