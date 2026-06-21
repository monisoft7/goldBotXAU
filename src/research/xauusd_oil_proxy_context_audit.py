"""v0_69 Brent/Oil proxy context feasibility audit for XAUUSD."""

from __future__ import annotations

import csv
import importlib
import json
from collections import Counter
from datetime import datetime, timezone
from numbers import Real
from pathlib import Path
from typing import Any, Iterable

AUDIT_VERSION = "v0_69"
DEFAULT_OUTPUT = Path("reports") / "xauusd_oil_proxy_context_audit_v0_69.json"
DEFAULT_CANDIDATE_SYMBOLS = ["UKOIL", "XBRUSD", "BRENT", "BRENT.fs", "BRN", "USOIL", "WTI", "XTIUSD"]

COMPLETED = "oil_proxy_context_feasibility_completed"
NO_USABLE_PROXY = "no_usable_oil_proxy_found"
BLOCKED_MISSING_DATA = "oil_proxy_audit_blocked_missing_data"

NEXT_IF_USABLE = "v0_70_oil_proxy_quality_ranking_and_label_design"
NEXT_IF_NO_USABLE = "v0_70_yield_context_external_dataset_feasibility_no_strategy"

FUTURE_LABEL_CANDIDATES = [
    "oil_strength",
    "oil_weakness",
    "oil_shock_up",
    "oil_shock_down",
    "gold_oil_inflation_pressure_aligned",
    "gold_oil_safe_haven_conflict",
    "oil_supply_shock_context_candidate",
]

TIMEFRAME_MINUTES = {"M5": 5, "M10": 10, "M15": 15}
PREFERRED_TIMEFRAMES = ["M15", "M5", "M10"]
REQUIRED_COLUMNS = ["time", "open", "high", "low", "close"]
TIMESTAMP_COLUMNS = ["time", "timestamp", "timestamp_utc", "datetime", "date"]

SAFETY_FALSE_FLAGS = [
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
    "labels_used_as_trade_blockers",
    "oos_used",
    "repeated_oos_review",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "executable_candidate_created",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
    "aligned_dataset_created",
    "data_csv_touched",
]


def build_xauusd_oil_proxy_context_audit_v0_69(
    *,
    root: str | Path = ".",
    candidate_symbols: Iterable[str] = DEFAULT_CANDIDATE_SYMBOLS,
    mt5_module: Any | None = None,
    attempt_mt5_readonly_discovery: bool = True,
) -> dict[str, Any]:
    """Audit read-only oil proxy availability without strategy logic or CSV export."""
    root_path = Path(root)
    symbols = [_clean_symbol(symbol) for symbol in candidate_symbols if _clean_symbol(symbol)]
    local_series = _discover_local_csv_series(root_path, symbols)
    xauusd_series = [series for series in local_series if series["symbol_key"] == "xauusd"]
    proxy_local_series = [series for series in local_series if series["symbol_key"] != "xauusd"]
    mt5_discovery = (
        _discover_mt5_series(symbols, mt5_module=mt5_module)
        if attempt_mt5_readonly_discovery
        else _empty_mt5_discovery(attempted=False)
    )
    proxy_series = proxy_local_series + mt5_discovery["series"]

    xauusd_timeframes = _timeframe_availability(xauusd_series)
    symbol_timeframe_audits = {
        symbol: {
            timeframe: _audit_symbol_timeframe(
                requested_symbol=symbol,
                timeframe=timeframe,
                proxy_series=[
                    item
                    for item in proxy_series
                    if item["symbol_key"] == _symbol_key(symbol) and item["timeframe"] == timeframe
                ],
                xauusd_series=[item for item in xauusd_series if item["timeframe"] == timeframe],
            )
            for timeframe in PREFERRED_TIMEFRAMES
        }
        for symbol in symbols
    }
    usable_symbols = [
        symbol
        for symbol in symbols
        if any(detail["safe_asof_alignment_feasible"] for detail in symbol_timeframe_audits[symbol].values())
    ]
    selected_symbol = usable_symbols[0] if usable_symbols else None
    selected_timeframe = _selected_timeframe(symbol_timeframe_audits.get(selected_symbol or "", {}))
    status = BLOCKED_MISSING_DATA if not xauusd_series else COMPLETED if selected_symbol else NO_USABLE_PROXY
    recommended_next_step = NEXT_IF_USABLE if selected_symbol else NEXT_IF_NO_USABLE

    report: dict[str, Any] = {
        "audit_version": AUDIT_VERSION,
        "audit_status": status,
        "purpose": "brent_oil_proxy_context_feasibility_audit_only_not_strategy",
        "candidate_symbols_checked": symbols,
        "usable_proxy_symbols": usable_symbols,
        "rejected_proxy_symbols": _rejected_symbols(symbols, symbol_timeframe_audits),
        "selected_proxy_symbol_or_null": selected_symbol,
        "selected_proxy_timeframe_or_null": selected_timeframe,
        "selection_reason": _selection_reason(status, selected_symbol, selected_timeframe),
        "xauusd_timeframes_available": xauusd_timeframes,
        "proxy_timeframes_available": _proxy_timeframes_available(symbols, proxy_series),
        "symbol_timeframe_audits": symbol_timeframe_audits,
        "overlap_summary": _overlap_summary(symbol_timeframe_audits),
        "gap_summary": _gap_summary(xauusd_series=xauusd_series, symbol_timeframe_audits=symbol_timeframe_audits),
        "safe_asof_alignment_feasible": bool(selected_symbol),
        "lookahead_risk_detected": False,
        "asof_alignment_policy": {
            "allowed_join_direction": "backward",
            "proxy_timestamp_must_be_less_than_or_equal_to_xauusd_timestamp": True,
            "alignment_storage": "in_memory_only",
            "persistent_aligned_csv_created": False,
            "disallowed_join_directions": ["forward", "nearest_future"],
        },
        "future_label_candidates": list(FUTURE_LABEL_CANDIDATES),
        "local_csv_files_scanned_count": len(local_series),
        "mt5_readonly_discovery": mt5_discovery["summary"],
        "strategy_rules_created": False,
        "trade_signals_output": False,
        "train_validation_only": True,
        "recommended_next_step": recommended_next_step,
        "blockers": _blockers(status, xauusd_series, usable_symbols, mt5_discovery),
        "warnings": _warnings(status),
        "safety": _safety_flags(),
    }
    report.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return report


def save_xauusd_oil_proxy_context_audit(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_backward_asof_alignment_pairs(
    xauusd_timestamps: Iterable[Any],
    proxy_timestamps: Iterable[Any],
) -> list[dict[str, str | None]]:
    """Return in-memory as-of pairs using only proxy bars known at or before XAUUSD time."""
    xau_times = sorted(timestamp for timestamp in (_parse_timestamp(item) for item in xauusd_timestamps) if timestamp)
    proxy_times = sorted(timestamp for timestamp in (_parse_timestamp(item) for item in proxy_timestamps) if timestamp)
    aligned = []
    for xau_time in xau_times:
        proxy_time = None
        for candidate in proxy_times:
            if candidate <= xau_time:
                proxy_time = candidate
            else:
                break
        if proxy_time and proxy_time > xau_time:
            raise ValueError("safe as-of alignment cannot use future oil proxy bars")
        aligned.append({"xauusd_timestamp": _format_ts(xau_time), "proxy_timestamp": _format_ts(proxy_time)})
    return aligned


def assert_no_future_proxy_bars(aligned_pairs: Iterable[dict[str, Any]]) -> None:
    for pair in aligned_pairs:
        xau_time = _parse_timestamp(pair.get("xauusd_timestamp"))
        proxy_time = _parse_timestamp(pair.get("proxy_timestamp"))
        if xau_time and proxy_time and proxy_time > xau_time:
            raise ValueError("future oil proxy bar detected in as-of alignment")


def _discover_local_csv_series(root: Path, candidate_symbols: list[str]) -> list[dict[str, Any]]:
    data_dir = root / "data"
    if not data_dir.exists():
        return []
    series = []
    for path in sorted(data_dir.glob("*.csv")):
        symbol = _symbol_from_filename(path.name, candidate_symbols)
        if symbol is None:
            continue
        timeframe = _infer_timeframe_from_name(path.name)
        if timeframe not in TIMEFRAME_MINUTES:
            continue
        summary = _rows_summary(_read_csv_rows(path), timeframe=timeframe, source="local_csv", symbol=symbol)
        if summary["copied_row_count"] <= 0:
            continue
        series.append({"source": "local_csv", "symbol": symbol, "symbol_key": _symbol_key(symbol), "timeframe": timeframe, "path": str(path.as_posix()), **summary})
    return series


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def _discover_mt5_series(symbols: list[str], *, mt5_module: Any | None) -> dict[str, Any]:
    mt5 = mt5_module
    if mt5 is None:
        try:
            mt5 = importlib.import_module("MetaTrader5")
        except ImportError:
            return _empty_mt5_discovery(
                attempted=True,
                status="metatrader5_package_unavailable",
                blockers=["metatrader5_package_unavailable"],
            )
    initialized = False
    shutdown_called = False
    try:
        if not mt5.initialize():
            return _empty_mt5_discovery(attempted=True, status="mt5_initialize_failed", blockers=[_last_error_text(mt5)])
        initialized = True
        available_names = sorted({_symbol_name(symbol) for symbol in (mt5.symbols_get() or []) if _symbol_name(symbol)})
        available_by_key = {_symbol_key(name): name for name in available_names}
        series = []
        for requested_symbol in symbols:
            actual_symbol = available_by_key.get(_symbol_key(requested_symbol))
            if actual_symbol is None:
                continue
            for timeframe in PREFERRED_TIMEFRAMES:
                rows = _mt5_copy_rates_from_pos(mt5, actual_symbol, timeframe, 5000)
                summary = _rows_summary(rows, timeframe=timeframe, source="mt5_readonly", symbol=requested_symbol)
                series.append(
                    {
                        "source": "mt5_readonly",
                        "symbol": requested_symbol,
                        "actual_symbol": actual_symbol,
                        "symbol_key": _symbol_key(requested_symbol),
                        "timeframe": timeframe,
                        "path": None,
                        **summary,
                    }
                )
        mt5.shutdown()
        shutdown_called = True
        return {
            "series": series,
            "summary": {
                "attempted": True,
                "status": "readonly_discovery_completed",
                "mt5_initialized": initialized,
                "mt5_shutdown_called": shutdown_called,
                "candidate_symbols_available": [symbol for symbol in symbols if _symbol_key(symbol) in available_by_key],
                "copy_rates_rows_total": sum(int(item["copied_row_count"]) for item in series),
                "order_send_called": False,
                "order_check_called": False,
                "blockers": [],
            },
        }
    except Exception as exc:
        if initialized and not shutdown_called:
            mt5.shutdown()
            shutdown_called = True
        return _empty_mt5_discovery(
            attempted=True,
            status="mt5_readonly_discovery_failed",
            initialized=initialized,
            shutdown_called=shutdown_called,
            blockers=[f"mt5_readonly_discovery_exception:{type(exc).__name__}:{exc}"],
        )


def _mt5_copy_rates_from_pos(mt5: Any, symbol: str, timeframe: str, count: int) -> list[Any]:
    copy_rates = getattr(mt5, "copy_rates_from_pos", None)
    mt5_timeframe = getattr(mt5, f"TIMEFRAME_{timeframe}", None)
    if not callable(copy_rates) or mt5_timeframe is None:
        return []
    rows = copy_rates(symbol, mt5_timeframe, 0, count)
    return list(rows) if rows is not None else []


def _rows_summary(rows: Iterable[Any], *, timeframe: str, source: str, symbol: str) -> dict[str, Any]:
    raw_rows = list(rows)
    parsed_rows = []
    timestamps_in_input_order = []
    seen_timestamps = set()
    duplicate_timestamp_count = 0
    invalid_ohlc_count = 0
    rows_with_required_columns = 0
    for row in raw_rows:
        required_present = _required_columns_present(row)
        rows_with_required_columns += 1 if required_present else 0
        parsed = _adapt_row(row, symbol=symbol, timeframe=timeframe, source=source)
        timestamp = _parse_timestamp(_first_row_value(row, TIMESTAMP_COLUMNS))
        if timestamp is not None:
            timestamps_in_input_order.append(timestamp)
            if timestamp in seen_timestamps:
                duplicate_timestamp_count += 1
            seen_timestamps.add(timestamp)
        if parsed is None:
            if timestamp is not None or required_present:
                invalid_ohlc_count += 1
            continue
        parsed_rows.append(parsed)
    monotonic = _monotonic_non_decreasing(timestamps_in_input_order) if timestamps_in_input_order else None
    first_timestamp = min((row["timestamp"] for row in parsed_rows), default=None)
    last_timestamp = max((row["timestamp"] for row in parsed_rows), default=None)
    gaps = _gap_details([row["timestamp"] for row in sorted(parsed_rows, key=lambda item: item["timestamp"])], timeframe)
    required_columns_present = bool(raw_rows) and rows_with_required_columns == len(raw_rows)
    return {
        "symbol_found": bool(raw_rows),
        "symbol_selected": _clean_symbol(symbol),
        "copied_row_count": len(raw_rows),
        "parseable_row_count": len(parsed_rows),
        "first_timestamp": _format_ts(first_timestamp),
        "last_timestamp": _format_ts(last_timestamp),
        "required_columns_present": required_columns_present,
        "invalid_ohlc_count": invalid_ohlc_count,
        "duplicate_timestamp_count": duplicate_timestamp_count,
        "monotonic_timestamp_order": monotonic,
        "gap_summary": gaps,
        "rows": parsed_rows,
    }


def _adapt_row(row: Any, *, symbol: str, timeframe: str, source: str) -> dict[str, Any] | None:
    timestamp = _parse_timestamp(_first_row_value(row, TIMESTAMP_COLUMNS))
    values = {key: _number_or_none(_row_value(row, key)) for key in ("open", "high", "low", "close")}
    if timestamp is None or any(value is None for value in values.values()):
        return None
    open_value = float(values["open"])
    high_value = float(values["high"])
    low_value = float(values["low"])
    close_value = float(values["close"])
    if min(open_value, high_value, low_value, close_value) <= 0:
        return None
    if high_value < max(open_value, close_value) or low_value > min(open_value, close_value):
        return None
    return {
        "timestamp": timestamp,
        "timestamp_utc": _format_ts(timestamp),
        "symbol": _clean_symbol(symbol),
        "timeframe": timeframe,
        "open": open_value,
        "high": high_value,
        "low": low_value,
        "close": close_value,
        "source": source,
    }


def _audit_symbol_timeframe(
    *,
    requested_symbol: str,
    timeframe: str,
    proxy_series: list[dict[str, Any]],
    xauusd_series: list[dict[str, Any]],
) -> dict[str, Any]:
    aggregate = _aggregate_series_rows(proxy_series, requested_symbol=requested_symbol, timeframe=timeframe)
    overlap = _overlap_with_xauusd_summary(aggregate, xauusd_series, timeframe=timeframe)
    safe_feasible = (
        aggregate["parseable_row_count"] > 0
        and aggregate["required_columns_present"] is True
        and aggregate["invalid_ohlc_count"] == 0
        and aggregate["duplicate_timestamp_count"] == 0
        and aggregate["monotonic_timestamp_order"] is not False
        and overlap["overlap_row_floor"] > 0
    )
    reason = _reason_if_rejected(aggregate=aggregate, overlap=overlap, xauusd_series=xauusd_series)
    return {
        **{key: value for key, value in aggregate.items() if key != "rows"},
        "overlap_with_xauusd_summary": overlap,
        "safe_asof_alignment_feasible": safe_feasible,
        "reason_if_rejected": None if safe_feasible else reason,
    }


def _aggregate_series_rows(series: list[dict[str, Any]], *, requested_symbol: str, timeframe: str) -> dict[str, Any]:
    rows = [row for item in series for row in item.get("rows", [])]
    copied = sum(int(item.get("copied_row_count", 0)) for item in series)
    parseable = len(rows)
    first_timestamp = min((row["timestamp"] for row in rows), default=None)
    last_timestamp = max((row["timestamp"] for row in rows), default=None)
    monotonic_values = [item.get("monotonic_timestamp_order") for item in series if item.get("copied_row_count", 0)]
    required_values = [item.get("required_columns_present") for item in series if item.get("copied_row_count", 0)]
    sorted_rows = sorted(rows, key=lambda row: row["timestamp"])
    return {
        "symbol_found": copied > 0,
        "symbol_selected": _clean_symbol(requested_symbol),
        "copied_row_count": copied,
        "parseable_row_count": parseable,
        "first_timestamp": _format_ts(first_timestamp),
        "last_timestamp": _format_ts(last_timestamp),
        "required_columns_present": bool(required_values) and all(value is True for value in required_values),
        "invalid_ohlc_count": sum(int(item.get("invalid_ohlc_count", 0)) for item in series),
        "duplicate_timestamp_count": sum(int(item.get("duplicate_timestamp_count", 0)) for item in series),
        "monotonic_timestamp_order": all(value is not False for value in monotonic_values) if monotonic_values else None,
        "gap_summary": _gap_details([row["timestamp"] for row in sorted_rows], timeframe),
        "rows": sorted_rows,
    }


def _overlap_with_xauusd_summary(proxy: dict[str, Any], xauusd_series: list[dict[str, Any]], *, timeframe: str) -> dict[str, Any]:
    proxy_start = _parse_timestamp(proxy.get("first_timestamp"))
    proxy_end = _parse_timestamp(proxy.get("last_timestamp"))
    best = {
        "timeframe": timeframe,
        "overlap_start": None,
        "overlap_end": None,
        "overlap_minutes": 0,
        "overlap_row_floor": 0,
    }
    if proxy_start is None or proxy_end is None:
        return best
    for xauusd in xauusd_series:
        xau_start = _parse_timestamp(xauusd.get("first_timestamp"))
        xau_end = _parse_timestamp(xauusd.get("last_timestamp"))
        if xau_start is None or xau_end is None:
            continue
        overlap_start = max(proxy_start, xau_start)
        overlap_end = min(proxy_end, xau_end)
        overlap_minutes = max(0, int((overlap_end - overlap_start).total_seconds() // 60))
        if overlap_minutes > int(best["overlap_minutes"]):
            timeframe_minutes = TIMEFRAME_MINUTES.get(timeframe, 1)
            best = {
                "timeframe": timeframe,
                "overlap_start": _format_ts(overlap_start),
                "overlap_end": _format_ts(overlap_end),
                "overlap_minutes": overlap_minutes,
                "overlap_row_floor": overlap_minutes // timeframe_minutes if timeframe_minutes else 0,
            }
    return best


def _timeframe_availability(series: list[dict[str, Any]]) -> dict[str, Any]:
    availability: dict[str, dict[str, Any]] = {}
    for item in series:
        timeframe = str(item.get("timeframe") or "UNKNOWN")
        bucket = availability.setdefault(timeframe, {"series_count": 0, "row_count": 0, "first_timestamp": None, "last_timestamp": None, "sources": []})
        bucket["series_count"] += 1
        bucket["row_count"] += int(item.get("parseable_row_count", 0))
        bucket["sources"].append(item.get("source"))
        first = _parse_timestamp(item.get("first_timestamp"))
        last = _parse_timestamp(item.get("last_timestamp"))
        current_first = _parse_timestamp(bucket["first_timestamp"])
        current_last = _parse_timestamp(bucket["last_timestamp"])
        if first and (current_first is None or first < current_first):
            bucket["first_timestamp"] = _format_ts(first)
        if last and (current_last is None or last > current_last):
            bucket["last_timestamp"] = _format_ts(last)
    return dict(sorted(availability.items()))


def _proxy_timeframes_available(symbols: list[str], proxy_series: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        symbol: _timeframe_availability([item for item in proxy_series if item["symbol_key"] == _symbol_key(symbol)])
        for symbol in symbols
    }


def _overlap_summary(symbol_timeframe_audits: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    return {
        symbol: {
            "usable": any(detail["safe_asof_alignment_feasible"] for detail in by_timeframe.values()),
            "best_overlap_rows": max([detail["overlap_with_xauusd_summary"]["overlap_row_floor"] for detail in by_timeframe.values()] or [0]),
            "timeframes": {
                timeframe: detail["overlap_with_xauusd_summary"]
                for timeframe, detail in by_timeframe.items()
                if detail["overlap_with_xauusd_summary"]["overlap_row_floor"] > 0
            },
        }
        for symbol, by_timeframe in symbol_timeframe_audits.items()
    }


def _gap_summary(*, xauusd_series: list[dict[str, Any]], symbol_timeframe_audits: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    return {
        "xauusd": {
            "series_count": len(xauusd_series),
            "total_gap_count": sum(int(item.get("gap_summary", {}).get("gap_count", 0)) for item in xauusd_series),
            "max_gap_minutes": max([int(item.get("gap_summary", {}).get("max_gap_minutes", 0)) for item in xauusd_series] or [0]),
        },
        "proxy_symbols": {
            symbol: {
                "usable": any(detail["safe_asof_alignment_feasible"] for detail in by_timeframe.values()),
                "total_gap_count": sum(int(detail["gap_summary"]["gap_count"]) for detail in by_timeframe.values()),
                "max_gap_minutes": max([int(detail["gap_summary"]["max_gap_minutes"]) for detail in by_timeframe.values()] or [0]),
            }
            for symbol, by_timeframe in symbol_timeframe_audits.items()
        },
    }


def _gap_details(timestamps: list[datetime], timeframe: str) -> dict[str, Any]:
    expected = TIMEFRAME_MINUTES.get(timeframe)
    gaps = []
    duplicate_count = 0
    previous = None
    seen = set()
    for timestamp in timestamps:
        if timestamp in seen:
            duplicate_count += 1
        seen.add(timestamp)
        if previous is not None and expected:
            delta = int((timestamp - previous).total_seconds() // 60)
            if delta > expected:
                gaps.append(delta)
        previous = timestamp
    return {
        "expected_minutes": expected,
        "gap_count": len(gaps),
        "max_gap_minutes": max(gaps) if gaps else 0,
        "duplicate_timestamp_count": duplicate_count,
    }


def _selected_timeframe(by_timeframe: dict[str, dict[str, Any]]) -> str | None:
    for timeframe in PREFERRED_TIMEFRAMES:
        if by_timeframe.get(timeframe, {}).get("safe_asof_alignment_feasible") is True:
            return timeframe
    return None


def _rejected_symbols(symbols: list[str], audits: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    rejected = {}
    for symbol in symbols:
        if any(detail["safe_asof_alignment_feasible"] for detail in audits[symbol].values()):
            continue
        rejected[symbol] = {
            "status": "rejected_no_safe_oil_proxy_overlap",
            "reasons_by_timeframe": {
                timeframe: detail["reason_if_rejected"] for timeframe, detail in audits[symbol].items()
            },
        }
    return rejected


def _reason_if_rejected(*, aggregate: dict[str, Any], overlap: dict[str, Any], xauusd_series: list[dict[str, Any]]) -> str:
    if not xauusd_series:
        return "missing_xauusd_same_timeframe_data"
    if aggregate["copied_row_count"] <= 0:
        return "oil_proxy_symbol_or_timeframe_not_available"
    if aggregate["parseable_row_count"] <= 0:
        return "no_parseable_oil_proxy_rows"
    if aggregate["required_columns_present"] is not True:
        return "missing_required_ohlc_columns"
    if aggregate["invalid_ohlc_count"] > 0:
        return "invalid_or_missing_ohlc_rows"
    if aggregate["duplicate_timestamp_count"] > 0:
        return "duplicate_timestamps_detected"
    if aggregate["monotonic_timestamp_order"] is False:
        return "non_monotonic_timestamps_detected"
    if overlap["overlap_row_floor"] <= 0:
        return "no_timestamp_overlap_with_xauusd_same_timeframe"
    return "safe_asof_alignment_not_feasible"


def _selection_reason(status: str, selected_symbol: str | None, selected_timeframe: str | None) -> str:
    if selected_symbol and selected_timeframe:
        return f"{selected_symbol} {selected_timeframe} selected by fixed candidate/timeframe order with parseable overlapping rows"
    if status == BLOCKED_MISSING_DATA:
        return "missing_local_xauusd_csv_data"
    return "no candidate oil proxy had parseable overlapping rows for safe backward as-of alignment"


def _blockers(status: str, xauusd_series: list[dict[str, Any]], usable_symbols: list[str], mt5_discovery: dict[str, Any]) -> list[str]:
    blockers = []
    if not xauusd_series:
        blockers.append("missing_local_xauusd_csv_data")
    if not usable_symbols:
        blockers.append("no_usable_oil_proxy_symbol_with_safe_timestamp_overlap")
    blockers.extend(mt5_discovery["summary"].get("blockers", []))
    if status == NO_USABLE_PROXY and not blockers:
        blockers.append("oil_proxy_data_unavailable_or_unaligned")
    return blockers


def _warnings(status: str) -> list[str]:
    warnings = [
        "research_infrastructure_only_not_strategy",
        "no_trade_filtering_approval_in_v0_69",
        "future_oil_labels_are_schema_candidates_only",
        "asof_alignment_must_use_proxy_values_known_at_or_before_xauusd_timestamp",
    ]
    if status == NO_USABLE_PROXY:
        warnings.append("oil_proxy_unusable_until_local_or_broker_series_overlap_is_available")
    return warnings


def _safety_flags() -> dict[str, bool]:
    flags = {
        "research_only": True,
        "context_feasibility_only": True,
        "strategy_rules_created": False,
        "strategy_rules_modified": False,
        "trade_signals_output": False,
        "train_validation_only": True,
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
    }
    flags.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return flags


def _empty_mt5_discovery(
    *,
    attempted: bool,
    status: str = "not_attempted",
    initialized: bool = False,
    shutdown_called: bool = False,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "series": [],
        "summary": {
            "attempted": attempted,
            "status": status,
            "mt5_initialized": initialized,
            "mt5_shutdown_called": shutdown_called,
            "candidate_symbols_available": [],
            "copy_rates_rows_total": 0,
            "order_send_called": False,
            "order_check_called": False,
            "blockers": blockers or [],
        },
    }


def _symbol_from_filename(name: str, candidate_symbols: list[str]) -> str | None:
    lower = name.lower()
    if "xauusd" in lower:
        return "XAUUSD"
    for symbol in candidate_symbols:
        if _symbol_key(symbol) in _symbol_key(lower):
            return symbol
    return None


def _infer_timeframe_from_name(name: str) -> str | None:
    lower = name.lower()
    for timeframe in ("m15", "m10", "m5"):
        token = f"_{timeframe}_"
        if token in lower or lower.startswith(f"{timeframe}_") or lower.endswith(f"_{timeframe}.csv"):
            return timeframe.upper()
    return None


def _required_columns_present(row: Any) -> bool:
    return any(_has_row_key(row, key) for key in TIMESTAMP_COLUMNS) and all(
        _has_row_key(row, key) for key in ("open", "high", "low", "close")
    )


def _first_row_value(row: Any, keys: Iterable[str]) -> Any:
    for key in keys:
        value = _row_value(row, key)
        if value not in (None, ""):
            return value
    return None


def _row_value(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return _coerce_scalar(row.get(key))
    try:
        return _coerce_scalar(row[key])
    except (TypeError, KeyError, IndexError, ValueError):
        return _coerce_scalar(getattr(row, key, None))


def _has_row_key(row: Any, key: str) -> bool:
    if isinstance(row, dict):
        return key in row
    names = getattr(getattr(row, "dtype", None), "names", None)
    if names and key in names:
        return True
    try:
        row[key]
        return True
    except (TypeError, KeyError, IndexError, ValueError):
        return hasattr(row, key)


def _coerce_scalar(value: Any) -> Any:
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return item()
        except (TypeError, ValueError):
            return value
    return value


def _number_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, Real):
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc).replace(tzinfo=None)
        except (OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _format_ts(value: datetime | None) -> str | None:
    return value.isoformat(timespec="seconds") if value else None


def _monotonic_non_decreasing(values: list[datetime]) -> bool:
    return all(current >= previous for previous, current in zip(values, values[1:]))


def _clean_symbol(symbol: Any) -> str:
    return str(symbol or "").strip()


def _symbol_key(symbol: Any) -> str:
    return "".join(char for char in str(symbol or "").lower() if char.isalnum())


def _symbol_name(symbol: Any) -> str:
    if isinstance(symbol, str):
        return symbol
    return str(getattr(symbol, "name", "") or "")


def _last_error_text(mt5: Any) -> str:
    last_error = getattr(mt5, "last_error", None)
    if callable(last_error):
        return f"mt5_initialize_failed:{last_error()}"
    return "mt5_initialize_failed"
