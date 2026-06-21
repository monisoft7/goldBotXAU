"""v0_65 DXY / USD proxy context feasibility audit for XAUUSD."""

from __future__ import annotations

import csv
import importlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

AUDIT_VERSION = "v0_65"
DEFAULT_OUTPUT = Path("reports") / "xauusd_dxy_proxy_context_audit_v0_65.json"
DEFAULT_CANDIDATE_SYMBOLS = ["DXYN", "DXYZ", "GDXY", "USDX"]
RECOMMENDED_NEXT_STEP = "v0_66_dxy_asof_alignment_if_proxy_feasible"

COMPLETED = "dxy_proxy_context_feasibility_completed"
NO_USABLE_PROXY = "no_usable_dxy_proxy_found"
BLOCKED_MISSING_DATA = "dxy_proxy_audit_blocked_missing_data"

FUTURE_LABEL_CANDIDATES = [
    "dollar_strength",
    "dollar_weakness",
    "dollar_shock",
    "gold_dxy_decoupling",
    "dxy_trend_aligned",
    "dxy_trend_conflict",
]

TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M10": 10,
    "M15": 15,
}

SAFETY_FALSE_FLAGS = [
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
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
    "data_csv_added_to_git",
]


def build_xauusd_dxy_proxy_context_audit_v0_65(
    *,
    root: str | Path = ".",
    candidate_symbols: Iterable[str] = DEFAULT_CANDIDATE_SYMBOLS,
    mt5_module: Any | None = None,
    attempt_mt5_readonly_discovery: bool = True,
) -> dict[str, Any]:
    """Audit local/read-only DXY proxy availability without creating strategy logic."""
    root_path = Path(root)
    symbols = [_normalize_symbol(symbol) for symbol in candidate_symbols if _normalize_symbol(symbol)]
    local_series = _discover_local_csv_series(root_path)
    xauusd_series = [series for series in local_series if series["symbol"] == "XAUUSD"]
    proxy_local_series = [series for series in local_series if series["symbol"] in symbols]
    mt5_discovery = (
        _discover_mt5_series(symbols, mt5_module=mt5_module)
        if attempt_mt5_readonly_discovery
        else _empty_mt5_discovery(attempted=False)
    )
    all_proxy_series = proxy_local_series + mt5_discovery["series"]

    symbol_audits = {
        symbol: _audit_proxy_symbol(
            symbol=symbol,
            proxy_series=[series for series in all_proxy_series if series["symbol"] == symbol],
            xauusd_series=xauusd_series,
        )
        for symbol in symbols
    }
    usable_symbols = [symbol for symbol, audit in symbol_audits.items() if audit["usable"]]
    selected_symbol = usable_symbols[0] if usable_symbols else None
    rejected = {
        symbol: {
            "status": audit["status"],
            "reasons": audit["reasons"],
            "local_files": audit["local_files"],
            "mt5_readonly_rows": audit["mt5_readonly_rows"],
        }
        for symbol, audit in symbol_audits.items()
        if not audit["usable"]
    }

    xauusd_timeframes = _timeframe_availability(xauusd_series)
    proxy_timeframes = {
        symbol: _timeframe_availability([series for series in all_proxy_series if series["symbol"] == symbol])
        for symbol in symbols
    }
    overlap_summary = _overlap_summary(symbol_audits)
    gap_summary = _gap_summary(xauusd_series=xauusd_series, symbol_audits=symbol_audits)
    safe_asof_feasible = bool(selected_symbol)

    if not xauusd_series:
        status = BLOCKED_MISSING_DATA
    elif selected_symbol:
        status = COMPLETED
    else:
        status = NO_USABLE_PROXY

    report: dict[str, Any] = {
        "audit_version": AUDIT_VERSION,
        "audit_status": status,
        "purpose": "dxy_usd_proxy_context_feasibility_audit_only_not_strategy",
        "market_thesis": "gold_must_not_be_treated_as_normal_fx_pair_intraday_dxy_usd_pressure_first_context_layer",
        "candidate_symbols_checked": symbols,
        "usable_proxy_symbols": usable_symbols,
        "rejected_proxy_symbols": rejected,
        "selected_proxy_symbol_or_null": selected_symbol,
        "xauusd_timeframes_available": xauusd_timeframes,
        "proxy_timeframes_available": proxy_timeframes,
        "overlap_summary": overlap_summary,
        "gap_summary": gap_summary,
        "safe_asof_alignment_feasible": safe_asof_feasible,
        "lookahead_risk_detected": False,
        "asof_alignment_policy": {
            "allowed_join_direction": "backward",
            "feature_timestamp_must_be_less_than_or_equal_to_xauusd_timestamp": True,
            "disallowed_join_directions": ["forward", "nearest_future"],
            "alignment_evaluated_as_feasibility_only": True,
        },
        "future_label_candidates": list(FUTURE_LABEL_CANDIDATES),
        "local_csv_files_scanned_count": len(local_series),
        "mt5_readonly_discovery": mt5_discovery["summary"],
        "strategy_rules_created": False,
        "trade_signals_output": False,
        "train_validation_only": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "blockers": _blockers(status, xauusd_series, usable_symbols, mt5_discovery),
        "warnings": _warnings(status, mt5_discovery),
        "safety": _safety_flags(),
    }
    report.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return report


def save_xauusd_dxy_proxy_context_audit(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_safe_asof_join_direction(join_direction: str) -> None:
    """Guard future callers from accidental lookahead joins."""
    if join_direction != "backward":
        raise ValueError("v0_65 allows only backward/as-of joins using known proxy values at or before XAUUSD time")


def _discover_local_csv_series(root: Path) -> list[dict[str, Any]]:
    data_dir = root / "data"
    if not data_dir.exists():
        return []
    series = []
    for path in sorted(data_dir.glob("*.csv")):
        symbol = _symbol_from_filename(path.name)
        if symbol is None:
            continue
        summary = _csv_series_summary(path)
        if summary["row_count"] <= 0:
            continue
        series.append(
            {
                "source": "local_csv",
                "symbol": symbol,
                "timeframe": _infer_timeframe_from_name(path.name) or summary["inferred_timeframe"],
                "path": str(path.as_posix()),
                **summary,
            }
        )
    return series


def _csv_series_summary(path: Path) -> dict[str, Any]:
    row_count = 0
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    previous_ts: datetime | None = None
    deltas: Counter[int] = Counter()
    gap_count = 0
    max_gap_minutes = 0
    timestamp_column: str | None = None
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            timestamp_column = _timestamp_column(reader.fieldnames or [])
            if timestamp_column is None:
                return _empty_series_summary("missing_timestamp_column")
            for row in reader:
                timestamp = _parse_timestamp(row.get(timestamp_column))
                if timestamp is None:
                    continue
                row_count += 1
                first_ts = timestamp if first_ts is None else min(first_ts, timestamp)
                last_ts = timestamp if last_ts is None else max(last_ts, timestamp)
                if previous_ts is not None:
                    delta_minutes = int((timestamp - previous_ts).total_seconds() // 60)
                    if delta_minutes > 0:
                        deltas[delta_minutes] += 1
                        expected = _expected_delta_minutes(deltas)
                        if expected and delta_minutes > expected:
                            gap_count += 1
                            max_gap_minutes = max(max_gap_minutes, delta_minutes)
                previous_ts = timestamp
    except OSError:
        return _empty_series_summary("csv_read_failed")

    inferred = f"M{_expected_delta_minutes(deltas)}" if _expected_delta_minutes(deltas) else None
    return {
        "row_count": row_count,
        "first_timestamp": _format_ts(first_ts),
        "last_timestamp": _format_ts(last_ts),
        "timestamp_column": timestamp_column,
        "inferred_timeframe": inferred,
        "gap_count": gap_count,
        "max_gap_minutes": max_gap_minutes,
        "read_status": "readable" if row_count else "no_valid_timestamp_rows",
    }


def _empty_series_summary(status: str) -> dict[str, Any]:
    return {
        "row_count": 0,
        "first_timestamp": None,
        "last_timestamp": None,
        "timestamp_column": None,
        "inferred_timeframe": None,
        "gap_count": 0,
        "max_gap_minutes": 0,
        "read_status": status,
    }


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
            return _empty_mt5_discovery(
                attempted=True,
                status="mt5_initialize_failed",
                blockers=[_last_error_text(mt5)],
            )
        initialized = True
        available_names = sorted({_symbol_name(symbol) for symbol in (mt5.symbols_get() or []) if _symbol_name(symbol)})
        series: list[dict[str, Any]] = []
        for symbol in symbols:
            if symbol not in available_names:
                continue
            for timeframe in ("M5", "M15"):
                rows = _mt5_copy_rates_from_pos(mt5, symbol, timeframe, 5000)
                summary = _mt5_rows_summary(rows)
                series.append(
                    {
                        "source": "mt5_readonly",
                        "symbol": symbol,
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
                "candidate_symbols_available": [symbol for symbol in symbols if symbol in available_names],
                "copy_rates_rows_total": sum(int(item["row_count"]) for item in series),
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
    if not callable(copy_rates):
        return []
    mt5_timeframe = getattr(mt5, f"TIMEFRAME_{timeframe}", None)
    if mt5_timeframe is None:
        return []
    rows = copy_rates(symbol, mt5_timeframe, 0, count)
    if rows is None:
        return []
    return list(rows)


def _mt5_rows_summary(rows: list[Any]) -> dict[str, Any]:
    timestamps = [_parse_mt5_time(row) for row in rows]
    valid = [timestamp for timestamp in timestamps if timestamp is not None]
    if not valid:
        return _empty_series_summary("mt5_no_rows")
    valid.sort()
    deltas = Counter(
        int((valid[index] - valid[index - 1]).total_seconds() // 60)
        for index in range(1, len(valid))
        if valid[index] > valid[index - 1]
    )
    expected = _expected_delta_minutes(deltas)
    gaps = [
        int((valid[index] - valid[index - 1]).total_seconds() // 60)
        for index in range(1, len(valid))
        if expected and int((valid[index] - valid[index - 1]).total_seconds() // 60) > expected
    ]
    return {
        "row_count": len(valid),
        "first_timestamp": _format_ts(valid[0]),
        "last_timestamp": _format_ts(valid[-1]),
        "timestamp_column": "time",
        "inferred_timeframe": f"M{expected}" if expected else None,
        "gap_count": len(gaps),
        "max_gap_minutes": max(gaps) if gaps else 0,
        "read_status": "readable",
    }


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


def _audit_proxy_symbol(
    *,
    symbol: str,
    proxy_series: list[dict[str, Any]],
    xauusd_series: list[dict[str, Any]],
) -> dict[str, Any]:
    overlaps = []
    for proxy in proxy_series:
        for xauusd in xauusd_series:
            if proxy.get("timeframe") != xauusd.get("timeframe"):
                continue
            overlap = _series_overlap(proxy, xauusd)
            if overlap["overlap_row_floor"] > 0:
                overlaps.append(overlap)
    usable = bool(overlaps)
    reasons = []
    if not proxy_series:
        reasons.append("no_local_or_mt5_readonly_rows_for_candidate_symbol")
    if proxy_series and not overlaps:
        reasons.append("no_timestamp_overlap_with_xauusd_same_timeframe")
    return {
        "usable": usable,
        "status": "usable_for_future_asof_context_alignment" if usable else "rejected_no_safe_overlap",
        "reasons": reasons,
        "overlaps": overlaps,
        "local_files": [series["path"] for series in proxy_series if series.get("source") == "local_csv" and series.get("path")],
        "mt5_readonly_rows": sum(int(series.get("row_count", 0)) for series in proxy_series if series.get("source") == "mt5_readonly"),
        "series_count": len(proxy_series),
    }


def _series_overlap(proxy: dict[str, Any], xauusd: dict[str, Any]) -> dict[str, Any]:
    proxy_start = _parse_timestamp(proxy.get("first_timestamp"))
    proxy_end = _parse_timestamp(proxy.get("last_timestamp"))
    xau_start = _parse_timestamp(xauusd.get("first_timestamp"))
    xau_end = _parse_timestamp(xauusd.get("last_timestamp"))
    if None in (proxy_start, proxy_end, xau_start, xau_end):
        overlap_start = None
        overlap_end = None
        overlap_minutes = 0
    else:
        overlap_start = max(proxy_start, xau_start)  # type: ignore[arg-type]
        overlap_end = min(proxy_end, xau_end)  # type: ignore[arg-type]
        overlap_minutes = max(0, int((overlap_end - overlap_start).total_seconds() // 60))
    timeframe_minutes = TIMEFRAME_MINUTES.get(str(proxy.get("timeframe")), 1)
    return {
        "symbol": proxy["symbol"],
        "timeframe": proxy.get("timeframe"),
        "proxy_source": proxy.get("source"),
        "xauusd_source": xauusd.get("source"),
        "overlap_start": _format_ts(overlap_start),
        "overlap_end": _format_ts(overlap_end),
        "overlap_minutes": overlap_minutes,
        "overlap_row_floor": overlap_minutes // timeframe_minutes if timeframe_minutes else 0,
    }


def _timeframe_availability(series: list[dict[str, Any]]) -> dict[str, Any]:
    by_timeframe: dict[str, dict[str, Any]] = {}
    for item in series:
        timeframe = item.get("timeframe") or "UNKNOWN"
        bucket = by_timeframe.setdefault(
            str(timeframe),
            {
                "series_count": 0,
                "row_count": 0,
                "first_timestamp": None,
                "last_timestamp": None,
                "sources": [],
            },
        )
        bucket["series_count"] += 1
        bucket["row_count"] += int(item.get("row_count", 0))
        bucket["sources"].append(item.get("source"))
        first = _parse_timestamp(item.get("first_timestamp"))
        last = _parse_timestamp(item.get("last_timestamp"))
        current_first = _parse_timestamp(bucket["first_timestamp"])
        current_last = _parse_timestamp(bucket["last_timestamp"])
        if first and (current_first is None or first < current_first):
            bucket["first_timestamp"] = _format_ts(first)
        if last and (current_last is None or last > current_last):
            bucket["last_timestamp"] = _format_ts(last)
    return dict(sorted(by_timeframe.items()))


def _overlap_summary(symbol_audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        symbol: {
            "usable": audit["usable"],
            "overlap_count": len(audit["overlaps"]),
            "best_overlap_rows": max([item["overlap_row_floor"] for item in audit["overlaps"]] or [0]),
            "overlaps": audit["overlaps"],
        }
        for symbol, audit in symbol_audits.items()
    }


def _gap_summary(*, xauusd_series: list[dict[str, Any]], symbol_audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "xauusd": _aggregate_gap_summary(xauusd_series),
        "proxy_symbols": {
            symbol: {
                "usable": audit["usable"],
                "series_count": audit["series_count"],
            }
            for symbol, audit in symbol_audits.items()
        },
    }


def _aggregate_gap_summary(series: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "series_count": len(series),
        "total_gap_count": sum(int(item.get("gap_count", 0)) for item in series),
        "max_gap_minutes": max([int(item.get("max_gap_minutes", 0)) for item in series] or [0]),
    }


def _symbol_from_filename(name: str) -> str | None:
    lower = name.lower()
    for symbol in ["xauusd", *[item.lower() for item in DEFAULT_CANDIDATE_SYMBOLS]]:
        if symbol in lower:
            return symbol.upper()
    return None


def _infer_timeframe_from_name(name: str) -> str | None:
    lower = name.lower()
    for timeframe in ("m15", "m10", "m5", "m1"):
        token = f"_{timeframe}_"
        if token in lower or lower.startswith(f"{timeframe}_") or lower.endswith(f"_{timeframe}.csv"):
            return timeframe.upper()
    return None


def _timestamp_column(fieldnames: list[str]) -> str | None:
    for candidate in ("timestamp_utc", "timestamp", "time", "datetime", "date"):
        if candidate in fieldnames:
            return candidate
    return None


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
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


def _parse_mt5_time(row: Any) -> datetime | None:
    value: Any
    if isinstance(row, dict):
        value = row.get("time")
    else:
        try:
            value = row["time"]
        except (TypeError, KeyError, IndexError, ValueError):
            value = getattr(row, "time", None)
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).replace(tzinfo=None)
    except (TypeError, ValueError, OSError):
        return _parse_timestamp(value)


def _format_ts(value: datetime | None) -> str | None:
    return value.isoformat(timespec="seconds") if value else None


def _expected_delta_minutes(deltas: Counter[int]) -> int | None:
    positive = {delta: count for delta, count in deltas.items() if delta > 0}
    if not positive:
        return None
    return min(positive.items(), key=lambda item: (-item[1], item[0]))[0]


def _normalize_symbol(symbol: Any) -> str:
    return str(symbol or "").strip().upper()


def _symbol_name(symbol: Any) -> str:
    if isinstance(symbol, str):
        return symbol
    name = getattr(symbol, "name", "")
    return str(name or "")


def _last_error_text(mt5: Any) -> str:
    last_error = getattr(mt5, "last_error", None)
    if callable(last_error):
        return f"mt5_initialize_failed:{last_error()}"
    return "mt5_initialize_failed"


def _blockers(
    status: str,
    xauusd_series: list[dict[str, Any]],
    usable_symbols: list[str],
    mt5_discovery: dict[str, Any],
) -> list[str]:
    blockers = []
    if not xauusd_series:
        blockers.append("missing_local_xauusd_csv_data")
    if not usable_symbols:
        blockers.append("no_usable_dxy_proxy_symbol_with_safe_timestamp_overlap")
    blockers.extend(mt5_discovery["summary"].get("blockers", []))
    if status == NO_USABLE_PROXY and not blockers:
        blockers.append("proxy_data_unavailable_or_unaligned")
    return blockers


def _warnings(status: str, mt5_discovery: dict[str, Any]) -> list[str]:
    warnings = [
        "research_infrastructure_only_not_strategy",
        "no_trade_filtering_approval_in_v0_65",
        "future_labels_are_schema_candidates_only",
        "asof_alignment_must_use_proxy_values_known_at_or_before_xauusd_timestamp",
    ]
    mt5_status = mt5_discovery["summary"].get("status")
    if mt5_status not in {"not_attempted", "readonly_discovery_completed"}:
        warnings.append(str(mt5_status))
    if status == NO_USABLE_PROXY:
        warnings.append("dxy_proxy_unusable_until_local_or_broker_series_overlap_is_available")
    return warnings


def _safety_flags() -> dict[str, bool]:
    flags = {
        "research_only": True,
        "context_feasibility_only": True,
        "strategy_rules_created": False,
        "strategy_evaluation": False,
        "trade_signals_output": False,
        "backtest_candidate_created": False,
        "train_validation_only": True,
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
        "data_csv_added_to_git": False,
    }
    flags.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return flags
