"""US yield / real-yield context feasibility audit for XAUUSD.

This module is research infrastructure only. It inspects local read-only MT5
market data when available and documents external dataset requirements without
calling external APIs or creating persistent aligned market datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


AUDIT_VERSION = "v0_73"
CANDIDATE_YIELD_SYMBOLS = [
    "US10Y",
    "US02Y",
    "US05Y",
    "US30Y",
    "UST10Y",
    "UST02Y",
    "TNX",
    "TYX",
    "FVX",
    "IRX",
    "US10YT",
    "10YUS",
    "2YUS",
    "USGG10YR",
    "TNOTE",
    "US10Y.BOND",
    "US10Y.cash",
]
TIMEFRAMES_TO_CHECK = ["D1", "H1", "M15"]
EXTERNAL_DATASET_CANDIDATES = ["DGS10", "DGS2", "DFII10", "DFII5", "T10YIE", "DFF"]
EXTERNAL_SCHEMA_REQUIREMENTS = [
    "timestamp/date",
    "value",
    "series_id",
    "release/source metadata",
]
FUTURE_LABEL_CANDIDATES = [
    "nominal_yield_rising",
    "nominal_yield_falling",
    "real_yield_rising",
    "real_yield_falling",
    "yield_shock_up",
    "yield_shock_down",
    "gold_yield_pressure_aligned",
    "gold_yield_decoupling",
]
REQUIRED_COLUMNS = ["time", "open", "high", "low", "close"]


@dataclass(frozen=True)
class ParsedBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


def _iso_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(tzinfo=None).isoformat()


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(tzinfo=None)
    if isinstance(value, str):
        try:
            cleaned = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(cleaned)
            return parsed.astimezone(timezone.utc).replace(tzinfo=None) if parsed.tzinfo else parsed
        except ValueError:
            return None
    return None


def _row_value(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    if hasattr(row, "dtype") and getattr(row.dtype, "names", None):
        if key in row.dtype.names:
            return row[key]
        return None
    try:
        return getattr(row, key)
    except AttributeError:
        return None


def _row_has_key(row: Any, key: str) -> bool:
    if isinstance(row, dict):
        return key in row
    if hasattr(row, "dtype") and getattr(row.dtype, "names", None):
        return key in row.dtype.names
    return hasattr(row, key)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def _parse_bars(rows: Iterable[Any]) -> tuple[list[ParsedBar], int, bool]:
    parsed: list[ParsedBar] = []
    invalid_ohlc_count = 0
    required_columns_present = True
    for row in rows:
        row_required = all(_row_has_key(row, column) for column in REQUIRED_COLUMNS)
        required_columns_present = required_columns_present and row_required
        if not row_required:
            invalid_ohlc_count += 1
            continue

        timestamp = _parse_timestamp(_row_value(row, "time"))
        open_value = _to_float(_row_value(row, "open"))
        high_value = _to_float(_row_value(row, "high"))
        low_value = _to_float(_row_value(row, "low"))
        close_value = _to_float(_row_value(row, "close"))
        values = [open_value, high_value, low_value, close_value]
        if timestamp is None or any(value is None for value in values):
            invalid_ohlc_count += 1
            continue
        assert open_value is not None
        assert high_value is not None
        assert low_value is not None
        assert close_value is not None
        if high_value < max(open_value, close_value, low_value) or low_value > min(open_value, close_value, high_value):
            invalid_ohlc_count += 1
            continue
        parsed.append(ParsedBar(timestamp, open_value, high_value, low_value, close_value))
    return parsed, invalid_ohlc_count, required_columns_present


def _duplicate_timestamp_count(bars: list[ParsedBar]) -> int:
    seen: set[datetime] = set()
    duplicates = 0
    for bar in bars:
        if bar.timestamp in seen:
            duplicates += 1
        seen.add(bar.timestamp)
    return duplicates


def _monotonic_timestamp_order(bars: list[ParsedBar]) -> bool | None:
    if len(bars) < 2:
        return True if bars else None
    return all(left.timestamp < right.timestamp for left, right in zip(bars, bars[1:]))


def _gap_summary(bars: list[ParsedBar]) -> dict[str, Any]:
    if len(bars) < 2:
        return {
            "bar_count": len(bars),
            "largest_gap_seconds": None,
            "gap_count_gt_3x_median": 0,
        }
    sorted_bars = sorted(bars, key=lambda bar: bar.timestamp)
    gaps = [
        int((right.timestamp - left.timestamp).total_seconds())
        for left, right in zip(sorted_bars, sorted_bars[1:])
        if right.timestamp > left.timestamp
    ]
    if not gaps:
        return {
            "bar_count": len(bars),
            "largest_gap_seconds": None,
            "gap_count_gt_3x_median": 0,
        }
    median_gap = sorted(gaps)[len(gaps) // 2]
    return {
        "bar_count": len(bars),
        "largest_gap_seconds": max(gaps),
        "median_gap_seconds": median_gap,
        "gap_count_gt_3x_median": sum(1 for gap in gaps if gap > median_gap * 3),
    }


def _overlap_summary(xauusd_bars: list[ParsedBar], proxy_bars: list[ParsedBar]) -> dict[str, Any]:
    if not xauusd_bars or not proxy_bars:
        return {
            "overlap_available": False,
            "first_overlap_timestamp": None,
            "last_overlap_timestamp": None,
            "xauusd_first_timestamp": _iso_or_none(min((bar.timestamp for bar in xauusd_bars), default=None)),
            "xauusd_last_timestamp": _iso_or_none(max((bar.timestamp for bar in xauusd_bars), default=None)),
            "proxy_first_timestamp": _iso_or_none(min((bar.timestamp for bar in proxy_bars), default=None)),
            "proxy_last_timestamp": _iso_or_none(max((bar.timestamp for bar in proxy_bars), default=None)),
        }
    xauusd_first = min(bar.timestamp for bar in xauusd_bars)
    xauusd_last = max(bar.timestamp for bar in xauusd_bars)
    proxy_first = min(bar.timestamp for bar in proxy_bars)
    proxy_last = max(bar.timestamp for bar in proxy_bars)
    overlap_first = max(xauusd_first, proxy_first)
    overlap_last = min(xauusd_last, proxy_last)
    overlap_available = overlap_first <= overlap_last
    return {
        "overlap_available": overlap_available,
        "first_overlap_timestamp": _iso_or_none(overlap_first) if overlap_available else None,
        "last_overlap_timestamp": _iso_or_none(overlap_last) if overlap_available else None,
        "xauusd_first_timestamp": _iso_or_none(xauusd_first),
        "xauusd_last_timestamp": _iso_or_none(xauusd_last),
        "proxy_first_timestamp": _iso_or_none(proxy_first),
        "proxy_last_timestamp": _iso_or_none(proxy_last),
    }


def assert_safe_backward_asof_alignment(xauusd_timestamp: Any, proxy_timestamp: Any) -> None:
    xauusd_time = _parse_timestamp(xauusd_timestamp)
    proxy_time = _parse_timestamp(proxy_timestamp)
    if xauusd_time is None or proxy_time is None:
        raise ValueError("as-of alignment requires parseable timestamps")
    if proxy_time > xauusd_time:
        raise ValueError("future proxy timestamp is not allowed for yield context alignment")


def safe_backward_asof_proxy_bar(xauusd_timestamp: Any, proxy_bars: Iterable[ParsedBar]) -> ParsedBar | None:
    xauusd_time = _parse_timestamp(xauusd_timestamp)
    if xauusd_time is None:
        raise ValueError("as-of alignment requires a parseable XAUUSD timestamp")
    eligible = [bar for bar in proxy_bars if bar.timestamp <= xauusd_time]
    if not eligible:
        return None
    selected = max(eligible, key=lambda bar: bar.timestamp)
    assert_safe_backward_asof_alignment(xauusd_time, selected.timestamp)
    return selected


def _mt5_timeframe_value(mt5: Any, timeframe: str) -> Any:
    fallback = {"M15": 15, "H1": 16385, "D1": 16408}
    return getattr(mt5, f"TIMEFRAME_{timeframe}", fallback[timeframe])


def _copy_rates(mt5: Any, symbol: str, timeframe: str, row_limit: int) -> list[Any]:
    raw_rows = mt5.copy_rates_from_pos(symbol, _mt5_timeframe_value(mt5, timeframe), 0, row_limit)
    if raw_rows is None:
        return []
    return list(raw_rows)


def _symbol_found(mt5: Any, symbol: str) -> bool:
    try:
        selected = mt5.symbol_select(symbol, True)
    except Exception:
        return False
    return bool(selected)


def _load_default_mt5() -> Any | None:
    try:
        import MetaTrader5 as mt5  # type: ignore[import-not-found]
    except Exception:
        return None
    return mt5


def _empty_candidate_audit(symbol: str, reason: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "symbol_found": False,
        "symbol_selected": False,
        "timeframe": None,
        "copied_row_count": 0,
        "parseable_row_count": 0,
        "first_timestamp": None,
        "last_timestamp": None,
        "required_columns_present": False,
        "invalid_ohlc_count": 0,
        "duplicate_timestamp_count": 0,
        "monotonic_timestamp_order": None,
        "gap_summary": _gap_summary([]),
        "overlap_with_xauusd_summary": _overlap_summary([], []),
        "safe_asof_alignment_feasible": False,
        "reason_if_rejected": reason,
    }


def _audit_symbol(
    mt5: Any,
    symbol: str,
    xauusd_bars_by_timeframe: dict[str, list[ParsedBar]],
    row_limit: int,
) -> dict[str, Any]:
    if not _symbol_found(mt5, symbol):
        return _empty_candidate_audit(symbol, "symbol_not_found_in_local_mt5")

    best: dict[str, Any] | None = None
    for timeframe in TIMEFRAMES_TO_CHECK:
        rows = _copy_rates(mt5, symbol, timeframe, row_limit)
        bars, invalid_ohlc_count, required_columns_present = _parse_bars(rows)
        duplicate_count = _duplicate_timestamp_count(bars)
        monotonic_order = _monotonic_timestamp_order(bars)
        sorted_bars = sorted(bars, key=lambda bar: bar.timestamp)
        xauusd_bars = xauusd_bars_by_timeframe.get(timeframe, [])
        overlap = _overlap_summary(xauusd_bars, sorted_bars)
        safe_asof = (
            bool(sorted_bars)
            and bool(xauusd_bars)
            and required_columns_present
            and invalid_ohlc_count == 0
            and duplicate_count == 0
            and bool(overlap["overlap_available"])
        )
        reason = None
        if not rows:
            reason = "no_rows_copied"
        elif not required_columns_present:
            reason = "missing_required_ohlc_columns"
        elif invalid_ohlc_count:
            reason = "invalid_ohlc_rows"
        elif duplicate_count:
            reason = "duplicate_timestamps"
        elif not sorted_bars:
            reason = "no_parseable_rows"
        elif not xauusd_bars:
            reason = "missing_xauusd_reference_rows"
        elif not overlap["overlap_available"]:
            reason = "no_overlap_with_xauusd"
        audit = {
            "symbol": symbol,
            "symbol_found": True,
            "symbol_selected": False,
            "timeframe": timeframe,
            "copied_row_count": len(rows),
            "parseable_row_count": len(sorted_bars),
            "first_timestamp": _iso_or_none(sorted_bars[0].timestamp) if sorted_bars else None,
            "last_timestamp": _iso_or_none(sorted_bars[-1].timestamp) if sorted_bars else None,
            "required_columns_present": required_columns_present,
            "invalid_ohlc_count": invalid_ohlc_count,
            "duplicate_timestamp_count": duplicate_count,
            "monotonic_timestamp_order": monotonic_order,
            "gap_summary": _gap_summary(sorted_bars),
            "overlap_with_xauusd_summary": overlap,
            "safe_asof_alignment_feasible": safe_asof,
            "reason_if_rejected": reason,
        }
        if best is None or (audit["safe_asof_alignment_feasible"] and not best["safe_asof_alignment_feasible"]):
            best = audit
        if safe_asof:
            break
    return best if best is not None else _empty_candidate_audit(symbol, "no_timeframes_checked")


def _load_xauusd_bars_by_timeframe(mt5: Any, row_limit: int) -> dict[str, list[ParsedBar]]:
    if not _symbol_found(mt5, "XAUUSD"):
        return {}
    bars_by_timeframe: dict[str, list[ParsedBar]] = {}
    for timeframe in TIMEFRAMES_TO_CHECK:
        rows = _copy_rates(mt5, "XAUUSD", timeframe, row_limit)
        bars, invalid_ohlc_count, required_columns_present = _parse_bars(rows)
        if rows and bars and invalid_ohlc_count == 0 and required_columns_present:
            bars_by_timeframe[timeframe] = sorted(bars, key=lambda bar: bar.timestamp)
    return bars_by_timeframe


def _external_dataset_policy(external_required: bool) -> dict[str, Any]:
    return {
        "required": external_required,
        "series_candidates": EXTERNAL_DATASET_CANDIDATES,
        "required_fields": EXTERNAL_SCHEMA_REQUIREMENTS,
        "alignment_policy": {
            "safe_backward_asof_only": True,
            "daily_yield_data_applied_by_backward_asof": True,
            "intraday_forward_fill_allowed_before_official_timestamp_policy": False,
            "lookahead_allowed": False,
            "official_timestamp_assumption_required_before_intraday_use": True,
        },
        "download_performed": False,
        "external_api_called": False,
    }


def build_yield_context_feasibility_report(
    root: Path,
    mt5: Any | None = None,
    row_limit: int = 10000,
) -> dict[str, Any]:
    mt5_module = mt5 if mt5 is not None else _load_default_mt5()
    mt5_initialized = False
    mt5_shutdown_called = False
    candidate_audits: list[dict[str, Any]]
    xauusd_bars_by_timeframe: dict[str, list[ParsedBar]] = {}
    warnings: list[str] = [
        "yield_context_research_infrastructure_only_not_strategy",
        "future_yield_labels_are_not_trade_blockers",
        "external_dataset_schema_documented_without_download",
        "persistent_aligned_market_csv_not_created",
    ]

    if mt5_module is None:
        candidate_audits = [
            _empty_candidate_audit(symbol, "mt5_module_unavailable_readonly_local_check_blocked")
            for symbol in CANDIDATE_YIELD_SYMBOLS
        ]
        warnings.append("mt5_module_unavailable")
    else:
        try:
            mt5_initialized = bool(mt5_module.initialize())
        except Exception:
            mt5_initialized = False
        if mt5_initialized:
            try:
                xauusd_bars_by_timeframe = _load_xauusd_bars_by_timeframe(mt5_module, row_limit)
                candidate_audits = [
                    _audit_symbol(mt5_module, symbol, xauusd_bars_by_timeframe, row_limit)
                    for symbol in CANDIDATE_YIELD_SYMBOLS
                ]
            finally:
                if hasattr(mt5_module, "shutdown"):
                    mt5_module.shutdown()
                    mt5_shutdown_called = True
        else:
            candidate_audits = [
                _empty_candidate_audit(symbol, "mt5_initialize_failed_readonly_local_check_blocked")
                for symbol in CANDIDATE_YIELD_SYMBOLS
            ]
            warnings.append("mt5_initialize_failed")

    usable_symbols = [audit["symbol"] for audit in candidate_audits if audit["safe_asof_alignment_feasible"]]
    selected_symbol = usable_symbols[0] if usable_symbols else None
    for audit in candidate_audits:
        audit["symbol_selected"] = audit["symbol"] == selected_symbol
    selected_audit = next((audit for audit in candidate_audits if audit["symbol"] == selected_symbol), None)
    local_proxy_available = selected_symbol is not None
    external_required = not local_proxy_available
    audit_status = (
        "yield_context_feasibility_completed"
        if local_proxy_available
        else "no_usable_local_yield_proxy_found"
    )
    if not mt5_initialized and mt5_module is not None:
        audit_status = "yield_context_audit_blocked_missing_data"

    rejected_symbols = [
        {
            "symbol": audit["symbol"],
            "reason_if_rejected": audit["reason_if_rejected"],
        }
        for audit in candidate_audits
        if audit["symbol"] != selected_symbol
    ]

    return {
        "audit_version": AUDIT_VERSION,
        "audit_status": audit_status,
        "candidate_symbols_checked": candidate_audits,
        "usable_local_proxy_symbols": usable_symbols,
        "rejected_local_proxy_symbols": rejected_symbols,
        "selected_local_proxy_symbol_or_null": selected_symbol,
        "local_yield_proxy_available": local_proxy_available,
        "external_dataset_required": external_required,
        "external_dataset_candidates": EXTERNAL_DATASET_CANDIDATES,
        "external_schema_requirements": EXTERNAL_SCHEMA_REQUIREMENTS,
        "external_dataset_feasibility": _external_dataset_policy(external_required),
        "xauusd_timeframes_available": sorted(xauusd_bars_by_timeframe),
        "proxy_timeframes_available": sorted(
            {
                audit["timeframe"]
                for audit in candidate_audits
                if audit["symbol_found"] and audit["parseable_row_count"] and audit["timeframe"] is not None
            }
        ),
        "overlap_summary": selected_audit["overlap_with_xauusd_summary"] if selected_audit else _overlap_summary([], []),
        "gap_summary": selected_audit["gap_summary"] if selected_audit else _gap_summary([]),
        "safe_asof_alignment_feasible": bool(selected_audit and selected_audit["safe_asof_alignment_feasible"]),
        "lookahead_risk_detected": False,
        "future_label_candidates": FUTURE_LABEL_CANDIDATES,
        "approved_for_strategy_testing": False,
        "approved_for_trade_filtering": False,
        "labels_used_as_trade_blockers": False,
        "labels_used_for_strategy_testing": False,
        "strategy_rules_created": False,
        "strategy_rules_modified": False,
        "trade_signals_output": False,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "executable_candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "trade_recommendation_output": False,
        "aligned_dataset_created": False,
        "data_csv_touched": False,
        "persistent_aligned_csv_created": False,
        "external_api_called": False,
        "mt5_initialized": mt5_initialized,
        "mt5_shutdown_called": mt5_shutdown_called,
        "warnings": warnings,
        "recommended_next_step": (
            "v0_74_yield_proxy_quality_and_label_design"
            if local_proxy_available
            else "v0_74_external_yield_dataset_schema_design_no_strategy"
        ),
    }


def write_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import json

    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
