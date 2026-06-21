"""v0_66 DXY / USD proxy quality ranker for XAUUSD research context."""

from __future__ import annotations

import bisect
import importlib
import json
from numbers import Real
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

RANKER_VERSION = "v0_66"
SOURCE_AUDIT_VERSION = "v0_65"
DEFAULT_SOURCE_AUDIT = Path("reports") / "xauusd_dxy_proxy_context_audit_v0_65.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_dxy_proxy_quality_ranker_v0_66.json"
DEFAULT_CANDIDATE_SYMBOLS = ["DXYN", "DXYZ", "GDXY", "USDX"]
RECOMMENDED_NEXT_STEP = "v0_67_dxy_regime_label_design_if_proxy_quality_passes"

COMPLETED = "dxy_proxy_quality_ranking_completed"
COMPLETED_NO_SAFE_PROXY = "dxy_proxy_quality_ranking_completed_no_safe_proxy"
BLOCKED_MISSING_DATA = "dxy_proxy_quality_ranking_blocked_missing_data"

FUTURE_LABEL_CANDIDATES = [
    "dollar_strength",
    "dollar_weakness",
    "dollar_shock",
    "gold_dxy_decoupling",
    "dxy_trend_aligned",
    "dxy_trend_conflict",
]

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
    "aligned_dataset_created",
    "data_csv_touched",
]

TIMEFRAME_MINUTES = {
    "M5": 5,
    "M10": 10,
    "M15": 15,
}


def build_xauusd_dxy_proxy_quality_ranker_v0_66(
    *,
    root: str | Path = ".",
    source_audit_path: str | Path = DEFAULT_SOURCE_AUDIT,
    candidate_symbols: Iterable[str] = DEFAULT_CANDIDATE_SYMBOLS,
    proxy_series_by_symbol: dict[str, dict[str, list[Any]]] | None = None,
    attempt_mt5_readonly_detail: bool = False,
    mt5_module: Any | None = None,
) -> dict[str, Any]:
    """Rank DXY proxy candidates without strategy testing or dataset export."""
    root_path = Path(root)
    symbols = [_normalize_symbol(symbol) for symbol in candidate_symbols if _normalize_symbol(symbol)]
    source_path = _resolve(root_path, source_audit_path)
    source_audit = _read_json(source_path)
    if not isinstance(source_audit, dict) or source_audit.get("audit_version") != SOURCE_AUDIT_VERSION:
        return _blocked_report(symbols, "missing_or_invalid_v0_65_source_audit")

    injected_series = proxy_series_by_symbol or {}
    mt5_detail = (
        _discover_mt5_detail(symbols=symbols, mt5_module=mt5_module)
        if attempt_mt5_readonly_detail
        else _empty_mt5_detail(attempted=False)
    )
    merged_series = _merge_series(injected_series, mt5_detail["series_by_symbol"])

    xauusd_timeframes = source_audit.get("xauusd_timeframes_available", {})
    if not isinstance(xauusd_timeframes, dict) or not xauusd_timeframes:
        return _blocked_report(symbols, "missing_xauusd_timeframe_availability", source_audit=source_audit)

    rows = []
    scores: dict[str, dict[str, Any]] = {}
    safe_feasible: dict[str, bool] = {}
    rejected: dict[str, Any] = {}
    for order, symbol in enumerate(symbols):
        assessment = _assess_symbol(
            symbol=symbol,
            candidate_order=order,
            source_audit=source_audit,
            row_series_by_timeframe=merged_series.get(symbol, {}),
        )
        row = assessment["ranking_row"]
        rows.append(row)
        scores[symbol] = assessment["score_detail"]
        safe_feasible[symbol] = assessment["safe_asof_alignment_feasible"]
        if not assessment["safe_asof_alignment_feasible"]:
            rejected[symbol] = {
                "status": "rejected_for_safe_asof_alignment",
                "reasons": assessment["rejection_reasons"],
                "quality_score": row["quality_score"],
            }

    ranked_rows = sorted(rows, key=lambda item: (-item["quality_score"], item["candidate_order"]))
    selected = ranked_rows[0]["symbol"] if ranked_rows and ranked_rows[0]["safe_asof_alignment_feasible"] else None
    if selected:
        status = COMPLETED
        selected_row = next(row for row in ranked_rows if row["symbol"] == selected)
        tied = [
            row["symbol"]
            for row in ranked_rows
            if row["safe_asof_alignment_feasible"] and row["quality_score"] == selected_row["quality_score"]
        ]
        if len(tied) > 1:
            reason = (
                f"{selected} selected by deterministic candidate-order tie-break after equal "
                f"quality score {selected_row['quality_score']}"
            )
        else:
            reason = f"{selected} selected because it has the highest safe proxy quality score"
    else:
        status = COMPLETED_NO_SAFE_PROXY
        reason = "no candidate satisfied safe backward as-of alignment quality requirements"

    report: dict[str, Any] = {
        "ranker_version": RANKER_VERSION,
        "ranker_status": status,
        "source_audit_version": SOURCE_AUDIT_VERSION,
        "candidate_symbols_ranked": symbols,
        "selected_proxy_symbol_or_null": selected,
        "selection_reason": reason,
        "quality_scores_by_symbol": scores,
        "ranking_table": ranked_rows,
        "rejected_proxy_symbols": rejected,
        "safe_asof_alignment_feasible_by_symbol": safe_feasible,
        "selected_proxy_safe_asof_alignment_feasible": bool(selected and safe_feasible.get(selected)),
        "lookahead_risk_detected": False,
        "aligned_dataset_created": False,
        "data_csv_touched": False,
        "future_label_candidates_preserved": list(FUTURE_LABEL_CANDIDATES),
        "train_validation_only": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "source_audit_report": str(source_path.as_posix()),
        "ranking_rules": _ranking_rules(),
        "safe_asof_alignment_design": _safe_asof_alignment_design(),
        "mt5_readonly_detail": mt5_detail["summary"],
        "safety": _safety_flags(),
    }
    report.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return report


def save_xauusd_dxy_proxy_quality_ranker(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_backward_asof_alignment_pairs(
    xauusd_timestamps: Iterable[Any],
    proxy_timestamps: Iterable[Any],
) -> list[dict[str, str | None]]:
    """Return in-memory timestamp pairs using proxy bars known at or before XAUUSD time."""
    xau_times = sorted(timestamp for timestamp in (_parse_timestamp(item) for item in xauusd_timestamps) if timestamp)
    proxy_times = sorted(timestamp for timestamp in (_parse_timestamp(item) for item in proxy_timestamps) if timestamp)
    aligned = []
    for xau_time in xau_times:
        index = bisect.bisect_right(proxy_times, xau_time) - 1
        proxy_time = proxy_times[index] if index >= 0 else None
        if proxy_time and proxy_time > xau_time:
            raise ValueError("safe as-of alignment cannot use future proxy timestamps")
        aligned.append(
            {
                "xauusd_timestamp": _format_ts(xau_time),
                "proxy_timestamp": _format_ts(proxy_time),
            }
        )
    return aligned


def assert_no_future_proxy_bars(aligned_pairs: Iterable[dict[str, Any]]) -> None:
    for pair in aligned_pairs:
        xau_time = _parse_timestamp(pair.get("xauusd_timestamp"))
        proxy_time = _parse_timestamp(pair.get("proxy_timestamp"))
        if xau_time and proxy_time and proxy_time > xau_time:
            raise ValueError("future proxy bar detected in as-of alignment")


def _assess_symbol(
    *,
    symbol: str,
    candidate_order: int,
    source_audit: dict[str, Any],
    row_series_by_timeframe: dict[str, list[Any]],
) -> dict[str, Any]:
    proxy_timeframes = _dict_at(source_audit, "proxy_timeframes_available", symbol)
    overlap = _dict_at(source_audit, "overlap_summary", symbol)
    source_rejection = _dict_at(source_audit, "rejected_proxy_symbols", symbol)
    symbol_mt5_available = symbol in _dict_at(source_audit, "mt5_readonly_discovery").get(
        "candidate_symbols_available", []
    )
    row_quality = _row_quality(row_series_by_timeframe)
    availability = _availability_metrics(proxy_timeframes)
    overlap_metrics = _overlap_metrics(overlap)
    gap_metrics = _gap_metrics(proxy_timeframes, row_quality)

    rejection_reasons = []
    if source_rejection:
        rejection_reasons.extend(source_rejection.get("reasons", []))
    if availability["total_rows"] <= 0:
        rejection_reasons.append("no_proxy_rows_available")
    if overlap_metrics["best_overlap_rows"] <= 0:
        rejection_reasons.append("no_overlap_with_xauusd_m5_m10_m15_available_data")
    if row_quality["duplicate_timestamp_count"] > 0:
        rejection_reasons.append("duplicate_proxy_timestamps_detected")
    if row_quality["monotonic_timestamp_order"] is False:
        rejection_reasons.append("non_monotonic_proxy_timestamps_detected")
    if row_quality["missing_ohlc_rows"] > 0:
        rejection_reasons.append("missing_proxy_ohlc_rows_detected")
    if row_quality["zero_or_invalid_ohlc_rows"] > 0:
        rejection_reasons.append("zero_or_invalid_proxy_ohlc_rows_detected")

    score_detail = _score_symbol(
        availability=availability,
        overlap_metrics=overlap_metrics,
        gap_metrics=gap_metrics,
        row_quality=row_quality,
        symbol_selection_stable=symbol_mt5_available,
    )
    safe_feasible = (
        availability["total_rows"] > 0
        and overlap_metrics["best_overlap_rows"] > 0
        and row_quality["duplicate_timestamp_count"] == 0
        and row_quality["monotonic_timestamp_order"] is not False
        and row_quality["missing_ohlc_rows"] == 0
        and row_quality["zero_or_invalid_ohlc_rows"] == 0
    )
    return {
        "safe_asof_alignment_feasible": safe_feasible,
        "rejection_reasons": sorted(set(rejection_reasons)),
        "score_detail": score_detail,
        "ranking_row": {
            "symbol": symbol,
            "ranker_version": RANKER_VERSION,
            "candidate_order": candidate_order,
            "quality_score": score_detail["total_score"],
            "safe_asof_alignment_feasible": safe_feasible,
            "data_available": availability["total_rows"] > 0,
            "supported_timeframes": availability["supported_timeframes"],
            "row_count": availability["total_rows"],
            "timestamp_coverage": availability["timestamp_coverage"],
            "best_overlap_rows": overlap_metrics["best_overlap_rows"],
            "overlap_timeframes": overlap_metrics["overlap_timeframes"],
            "gap_count": gap_metrics["gap_count"],
            "max_gap_minutes": gap_metrics["max_gap_minutes"],
            "duplicate_timestamp_count": row_quality["duplicate_timestamp_count"],
            "monotonic_timestamp_order": row_quality["monotonic_timestamp_order"],
            "missing_ohlc_rows": row_quality["missing_ohlc_rows"],
            "zero_or_invalid_ohlc_rows": row_quality["zero_or_invalid_ohlc_rows"],
            "spread_available": row_quality["spread_available"],
            "tick_volume_available": row_quality["tick_volume_available"],
            "symbol_selection_stable": symbol_mt5_available,
        },
    }


def _score_symbol(
    *,
    availability: dict[str, Any],
    overlap_metrics: dict[str, Any],
    gap_metrics: dict[str, Any],
    row_quality: dict[str, Any],
    symbol_selection_stable: bool,
) -> dict[str, Any]:
    availability_score = 25 if availability["total_rows"] > 0 else 0
    timeframe_score = min(20, 8 * len(set(availability["supported_timeframes"]) & {"M5", "M10", "M15"}))
    overlap_score = min(30, int(overlap_metrics["best_overlap_rows"] / 2000))
    coverage_score = min(10, int(availability["coverage_minutes"] / (60 * 24 * 30)))
    stability_score = 5 if symbol_selection_stable else 0
    row_quality_bonus = 10 if row_quality["row_quality_observed"] and row_quality["row_quality_clean"] else 0
    gap_penalty = min(12, gap_metrics["gap_count"] + int(gap_metrics["max_gap_minutes"] / 720))
    duplicate_penalty = min(15, row_quality["duplicate_timestamp_count"] * 3)
    monotonic_penalty = 15 if row_quality["monotonic_timestamp_order"] is False else 0
    ohlc_penalty = min(20, row_quality["missing_ohlc_rows"] * 5 + row_quality["zero_or_invalid_ohlc_rows"] * 5)
    total = (
        availability_score
        + timeframe_score
        + overlap_score
        + coverage_score
        + stability_score
        + row_quality_bonus
        - gap_penalty
        - duplicate_penalty
        - monotonic_penalty
        - ohlc_penalty
    )
    return {
        "total_score": max(0, total),
        "availability_score": availability_score,
        "timeframe_score": timeframe_score,
        "overlap_score": overlap_score,
        "coverage_score": coverage_score,
        "symbol_selection_stability_score": stability_score,
        "row_quality_bonus": row_quality_bonus,
        "gap_penalty": gap_penalty,
        "duplicate_timestamp_penalty": duplicate_penalty,
        "monotonic_timestamp_penalty": monotonic_penalty,
        "ohlc_quality_penalty": ohlc_penalty,
        "scoring_note": "fixed deterministic scoring; candidate order is used only after equal total_score",
    }


def _availability_metrics(proxy_timeframes: dict[str, Any]) -> dict[str, Any]:
    total_rows = 0
    supported: list[str] = []
    starts = []
    ends = []
    for timeframe, info in sorted(proxy_timeframes.items()):
        if not isinstance(info, dict):
            continue
        rows = int(info.get("row_count") or 0)
        if rows > 0:
            supported.append(str(timeframe))
            total_rows += rows
        start = _parse_timestamp(info.get("first_timestamp"))
        end = _parse_timestamp(info.get("last_timestamp"))
        if start:
            starts.append(start)
        if end:
            ends.append(end)
    first = min(starts) if starts else None
    last = max(ends) if ends else None
    coverage_minutes = max(0, int((last - first).total_seconds() // 60)) if first and last else 0
    return {
        "total_rows": total_rows,
        "supported_timeframes": supported,
        "coverage_minutes": coverage_minutes,
        "timestamp_coverage": {
            "first_timestamp": _format_ts(first),
            "last_timestamp": _format_ts(last),
            "coverage_minutes": coverage_minutes,
        },
    }


def _overlap_metrics(overlap: dict[str, Any]) -> dict[str, Any]:
    overlaps = overlap.get("overlaps", []) if isinstance(overlap, dict) else []
    if not isinstance(overlaps, list):
        overlaps = []
    return {
        "best_overlap_rows": int(overlap.get("best_overlap_rows") or 0) if isinstance(overlap, dict) else 0,
        "overlap_timeframes": sorted({str(item.get("timeframe")) for item in overlaps if isinstance(item, dict)}),
    }


def _gap_metrics(proxy_timeframes: dict[str, Any], row_quality: dict[str, Any]) -> dict[str, int]:
    summary_gap_count = 0
    summary_max_gap = 0
    for info in proxy_timeframes.values():
        if not isinstance(info, dict):
            continue
        summary_gap_count += int(info.get("gap_count") or 0)
        summary_max_gap = max(summary_max_gap, int(info.get("max_gap_minutes") or 0))
    return {
        "gap_count": max(summary_gap_count, row_quality["gap_count"]),
        "max_gap_minutes": max(summary_max_gap, row_quality["max_gap_minutes"]),
    }


def _row_quality(series_by_timeframe: dict[str, list[Any]]) -> dict[str, Any]:
    duplicate_count = 0
    missing_ohlc = 0
    invalid_ohlc = 0
    spreads = []
    volumes = []
    gaps = []
    observed = False
    monotonic = True
    for timeframe, rows in series_by_timeframe.items():
        previous = None
        seen = set()
        expected = TIMEFRAME_MINUTES.get(str(timeframe))
        for row in rows:
            observed = True
            timestamp = _parse_timestamp(_row_value(row, "time") or _row_value(row, "timestamp"))
            if timestamp is None:
                missing_ohlc += 1
                continue
            if timestamp in seen:
                duplicate_count += 1
            seen.add(timestamp)
            if previous is not None:
                delta = int((timestamp - previous).total_seconds() // 60)
                if delta < 0:
                    monotonic = False
                if expected and delta > expected:
                    gaps.append(delta)
            previous = timestamp
            ohlc = [_number_or_none(_row_value(row, key)) for key in ("open", "high", "low", "close")]
            if any(value is None for value in ohlc):
                missing_ohlc += 1
            elif any(value <= 0 for value in ohlc if value is not None) or not (ohlc[1] >= ohlc[0] >= ohlc[2]):
                invalid_ohlc += 1
            spread = _number_or_none(_row_value(row, "spread"))
            volume = _number_or_none(_row_value(row, "tick_volume") or _row_value(row, "volume"))
            if spread is not None:
                spreads.append(spread)
            if volume is not None:
                volumes.append(volume)
    clean = duplicate_count == 0 and monotonic and missing_ohlc == 0 and invalid_ohlc == 0
    return {
        "row_quality_observed": observed,
        "row_quality_clean": clean,
        "duplicate_timestamp_count": duplicate_count,
        "monotonic_timestamp_order": monotonic if observed else None,
        "missing_ohlc_rows": missing_ohlc,
        "zero_or_invalid_ohlc_rows": invalid_ohlc,
        "spread_available": bool(spreads) if observed else None,
        "tick_volume_available": bool(volumes) if observed else None,
        "gap_count": len(gaps),
        "max_gap_minutes": max(gaps) if gaps else 0,
    }


def _discover_mt5_detail(*, symbols: list[str], mt5_module: Any | None) -> dict[str, Any]:
    mt5 = mt5_module
    if mt5 is None:
        try:
            mt5 = importlib.import_module("MetaTrader5")
        except ImportError:
            return _empty_mt5_detail(
                attempted=True,
                status="metatrader5_package_unavailable",
                blockers=["metatrader5_package_unavailable"],
            )
    initialized = False
    shutdown_called = False
    try:
        if not mt5.initialize():
            return _empty_mt5_detail(attempted=True, status="mt5_initialize_failed", blockers=["mt5_initialize_failed"])
        initialized = True
        available = sorted({_symbol_name(item) for item in (mt5.symbols_get() or []) if _symbol_name(item)})
        series_by_symbol: dict[str, dict[str, list[Any]]] = {}
        for symbol in symbols:
            if symbol not in available:
                continue
            for timeframe in ("M5", "M15"):
                mt5_timeframe = getattr(mt5, f"TIMEFRAME_{timeframe}", None)
                copy_rates = getattr(mt5, "copy_rates_from_pos", None)
                if mt5_timeframe is None or not callable(copy_rates):
                    continue
                rows = copy_rates(symbol, mt5_timeframe, 0, 5000)
                if rows is None:
                    rows = []
                series_by_symbol.setdefault(symbol, {})[timeframe] = list(rows)
        mt5.shutdown()
        shutdown_called = True
        return {
            "series_by_symbol": series_by_symbol,
            "summary": {
                "attempted": True,
                "status": "readonly_detail_completed",
                "mt5_initialized": initialized,
                "mt5_shutdown_called": shutdown_called,
                "candidate_symbols_available": [symbol for symbol in symbols if symbol in available],
                "copy_rates_rows_total": sum(
                    len(rows) for by_timeframe in series_by_symbol.values() for rows in by_timeframe.values()
                ),
                "order_send_called": False,
                "order_check_called": False,
                "blockers": [],
            },
        }
    except Exception as exc:
        if initialized and not shutdown_called:
            mt5.shutdown()
            shutdown_called = True
        return _empty_mt5_detail(
            attempted=True,
            status="mt5_readonly_detail_failed",
            initialized=initialized,
            shutdown_called=shutdown_called,
            blockers=[f"mt5_readonly_detail_exception:{type(exc).__name__}:{exc}"],
        )


def _empty_mt5_detail(
    *,
    attempted: bool,
    status: str = "not_attempted",
    initialized: bool = False,
    shutdown_called: bool = False,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "series_by_symbol": {},
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


def _merge_series(
    primary: dict[str, dict[str, list[Any]]],
    secondary: dict[str, dict[str, list[Any]]],
) -> dict[str, dict[str, list[Any]]]:
    merged = {symbol: {tf: list(rows) for tf, rows in by_tf.items()} for symbol, by_tf in secondary.items()}
    for symbol, by_tf in primary.items():
        merged.setdefault(_normalize_symbol(symbol), {}).update({str(tf): list(rows) for tf, rows in by_tf.items()})
    return merged


def _blocked_report(
    symbols: list[str],
    reason: str,
    *,
    source_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ranker_version": RANKER_VERSION,
        "ranker_status": BLOCKED_MISSING_DATA,
        "source_audit_version": source_audit.get("audit_version") if isinstance(source_audit, dict) else SOURCE_AUDIT_VERSION,
        "candidate_symbols_ranked": symbols,
        "selected_proxy_symbol_or_null": None,
        "selection_reason": reason,
        "quality_scores_by_symbol": {},
        "ranking_table": [],
        "rejected_proxy_symbols": {symbol: {"status": "blocked", "reasons": [reason]} for symbol in symbols},
        "safe_asof_alignment_feasible_by_symbol": {symbol: False for symbol in symbols},
        "selected_proxy_safe_asof_alignment_feasible": False,
        "lookahead_risk_detected": False,
        "aligned_dataset_created": False,
        "data_csv_touched": False,
        "future_label_candidates_preserved": list(FUTURE_LABEL_CANDIDATES),
        "train_validation_only": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "safety": _safety_flags(),
    }
    report.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return report


def _ranking_rules() -> dict[str, Any]:
    return {
        "fixed_candidate_order_for_ties_only": list(DEFAULT_CANDIDATE_SYMBOLS),
        "higher_score_wins": True,
        "score_inputs": [
            "data_availability",
            "supported_timeframes",
            "row_count",
            "timestamp_coverage",
            "overlap_with_xauusd_m5_m10_m15",
            "gap_count_and_gap_severity",
            "duplicate_timestamps",
            "monotonic_timestamp_order",
            "missing_or_invalid_ohlc",
            "spread_tick_volume_availability",
            "symbol_selection_stability",
        ],
    }


def _safe_asof_alignment_design() -> dict[str, Any]:
    return {
        "design_only": True,
        "alignment_storage": "in_memory_only",
        "persistent_aligned_csv_created": False,
        "allowed_join_direction": "backward",
        "proxy_timestamp_rule": "proxy_timestamp_must_be_less_than_or_equal_to_xauusd_timestamp",
        "disallowed_join_directions": ["forward", "nearest_future"],
        "lookahead_guard_function": "assert_no_future_proxy_bars",
    }


def _safety_flags() -> dict[str, bool]:
    flags = {
        "research_only": True,
        "strategy_rules_created": False,
        "trade_signals_output": False,
        "train_validation_only": True,
    }
    flags.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return flags


def _dict_at(mapping: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key, {})
    return current if isinstance(current, dict) else {}


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _row_value(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    try:
        return row[key]
    except (TypeError, KeyError, IndexError, ValueError):
        return getattr(row, key, None)


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


def _normalize_symbol(symbol: Any) -> str:
    return str(symbol or "").strip().upper()


def _symbol_name(symbol: Any) -> str:
    if isinstance(symbol, str):
        return symbol
    return str(getattr(symbol, "name", "") or "")
