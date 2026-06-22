"""Oil proxy quality ranking and label design for XAUUSD research context.

This module is research infrastructure only. It ranks already-audited oil
proxy rows from v0_69 and defines descriptive regime labels without creating
signals, blockers, filters, strategy rules, aligned CSVs, or execution paths.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

DESIGN_VERSION = "v0_70"
SOURCE_OIL_AUDIT_VERSION = "v0_69"
DEFAULT_AUDIT_REPORT = Path("reports/xauusd_oil_proxy_context_audit_v0_69.json")
DEFAULT_OUTPUT_REPORT = Path("reports/xauusd_oil_proxy_quality_and_label_design_v0_70.json")
USABLE_SYMBOL_ORDER = ["BRN", "WTI"]
TIMEFRAME_ORDER = ["M5", "M10", "M15"]

SAFETY_FALSE_FIELDS = (
    "lookahead_risk_detected",
    "labels_used_as_trade_blockers",
    "labels_used_for_strategy_testing",
    "aligned_dataset_created",
    "data_csv_touched",
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
)


def load_audit_report(path: Path = DEFAULT_AUDIT_REPORT) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(report: dict[str, Any], path: Path = DEFAULT_OUTPUT_REPORT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def reject_invalid_ohlc_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for row in rows:
        try:
            open_price = float(row["open"])
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
        except (KeyError, TypeError, ValueError):
            rejected_rows.append({**row, "reject_reason": "missing_or_non_numeric_ohlc"})
            continue
        if min(open_price, high, low, close) <= 0:
            rejected_rows.append({**row, "reject_reason": "non_positive_ohlc"})
            continue
        if low > high or not (low <= open_price <= high) or not (low <= close <= high):
            rejected_rows.append({**row, "reject_reason": "inconsistent_ohlc_range"})
            continue
        valid_rows.append(row)
    return valid_rows, rejected_rows


def safe_asof_proxy_row(proxy_rows: list[dict[str, Any]], xauusd_timestamp: datetime) -> dict[str, Any] | None:
    """Return the latest proxy row known at or before the XAUUSD timestamp."""
    eligible_rows: list[tuple[datetime, dict[str, Any]]] = []
    for row in proxy_rows:
        timestamp = parse_timestamp(row.get("timestamp") or row.get("time") or row.get("timestamp_utc"))
        if timestamp is not None and timestamp <= xauusd_timestamp:
            eligible_rows.append((timestamp, row))
    if not eligible_rows:
        return None
    return max(eligible_rows, key=lambda item: item[0])[1]


def _best_timeframe(symbol_audits: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    candidates: list[tuple[int, int, int, str, dict[str, Any]]] = []
    for timeframe in TIMEFRAME_ORDER:
        audit = symbol_audits.get(timeframe)
        if not isinstance(audit, dict) or not audit.get("safe_asof_alignment_feasible"):
            continue
        overlap = audit.get("overlap_with_xauusd_summary", {})
        gap = audit.get("gap_summary", {})
        candidates.append(
            (
                int(overlap.get("overlap_row_floor") or 0),
                int(audit.get("parseable_row_count") or 0),
                -int(gap.get("gap_count") or 0),
                timeframe,
                audit,
            )
        )
    if not candidates:
        return None, None
    _, _, _, timeframe, audit = max(candidates)
    return timeframe, audit


def _quality_score(timeframe_audits: dict[str, Any], best_audit: dict[str, Any] | None) -> int:
    if best_audit is None:
        return 0

    supported_timeframes = [
        timeframe
        for timeframe in TIMEFRAME_ORDER
        if isinstance(timeframe_audits.get(timeframe), dict)
        and timeframe_audits[timeframe].get("safe_asof_alignment_feasible") is True
    ]
    copied_rows = sum(int(timeframe_audits[tf].get("copied_row_count") or 0) for tf in supported_timeframes)
    parseable_rows = sum(int(timeframe_audits[tf].get("parseable_row_count") or 0) for tf in supported_timeframes)
    overlap_rows = int(best_audit.get("overlap_with_xauusd_summary", {}).get("overlap_row_floor") or 0)
    gap_count = int(best_audit.get("gap_summary", {}).get("gap_count") or 0)
    max_gap_minutes = int(best_audit.get("gap_summary", {}).get("max_gap_minutes") or 0)

    score = 0
    score += 20 if supported_timeframes else 0
    score += min(20, len(supported_timeframes) * 6)
    score += min(20, copied_rows // 750)
    score += min(20, parseable_rows // 750)
    score += min(30, overlap_rows // 2000)
    score += 10 if best_audit.get("safe_asof_alignment_feasible") is True else 0
    score += 6 if best_audit.get("duplicate_timestamp_count") == 0 else -10
    score += 6 if best_audit.get("monotonic_timestamp_order") is True else -10
    score += 6 if best_audit.get("invalid_ohlc_count") == 0 else -20
    score -= min(12, gap_count // 250)
    score -= min(10, max_gap_minutes // 3000)
    return max(score, 0)


def _ranking_row(symbol: str, audit: dict[str, Any]) -> dict[str, Any]:
    symbol_audits = audit.get("symbol_timeframe_audits", {}).get(symbol, {})
    timeframe, best_audit = _best_timeframe(symbol_audits if isinstance(symbol_audits, dict) else {})
    safe_by_timeframe = {
        tf: bool(symbol_audits.get(tf, {}).get("safe_asof_alignment_feasible"))
        for tf in TIMEFRAME_ORDER
        if isinstance(symbol_audits.get(tf), dict)
    }
    copied_row_count = sum(int(symbol_audits.get(tf, {}).get("copied_row_count") or 0) for tf in TIMEFRAME_ORDER)
    parseable_row_count = sum(int(symbol_audits.get(tf, {}).get("parseable_row_count") or 0) for tf in TIMEFRAME_ORDER)
    duplicate_timestamps = sum(
        int(symbol_audits.get(tf, {}).get("duplicate_timestamp_count") or 0) for tf in TIMEFRAME_ORDER
    )
    invalid_ohlc = sum(int(symbol_audits.get(tf, {}).get("invalid_ohlc_count") or 0) for tf in TIMEFRAME_ORDER)
    gap_count = sum(
        int(symbol_audits.get(tf, {}).get("gap_summary", {}).get("gap_count") or 0) for tf in TIMEFRAME_ORDER
    )
    max_gap_minutes = max(
        [int(symbol_audits.get(tf, {}).get("gap_summary", {}).get("max_gap_minutes") or 0) for tf in TIMEFRAME_ORDER]
        or [0]
    )
    overlap = best_audit.get("overlap_with_xauusd_summary", {}) if isinstance(best_audit, dict) else {}

    return {
        "symbol": symbol,
        "supported_timeframes": [tf for tf, safe in safe_by_timeframe.items() if safe],
        "selected_timeframe": timeframe,
        "copied_row_count": copied_row_count,
        "parseable_row_count": parseable_row_count,
        "first_timestamp": best_audit.get("first_timestamp") if isinstance(best_audit, dict) else None,
        "last_timestamp": best_audit.get("last_timestamp") if isinstance(best_audit, dict) else None,
        "best_overlap_rows": int(overlap.get("overlap_row_floor") or 0),
        "gap_count": gap_count,
        "max_gap_minutes": max_gap_minutes,
        "duplicate_timestamp_count": duplicate_timestamps,
        "monotonic_timestamp_order": all(
            symbol_audits.get(tf, {}).get("monotonic_timestamp_order") is True
            for tf in TIMEFRAME_ORDER
            if isinstance(symbol_audits.get(tf), dict) and symbol_audits.get(tf, {}).get("symbol_found") is True
        ),
        "invalid_ohlc_count": invalid_ohlc,
        "safe_asof_alignment_feasible": any(safe_by_timeframe.values()),
        "quality_score": _quality_score(symbol_audits if isinstance(symbol_audits, dict) else {}, best_audit),
    }


def rank_oil_proxies(audit: dict[str, Any]) -> list[dict[str, Any]]:
    usable_symbols = [symbol for symbol in USABLE_SYMBOL_ORDER if symbol in set(audit.get("usable_proxy_symbols", []))]
    rows = [_ranking_row(symbol, audit) for symbol in usable_symbols]
    tie_order = {symbol: index for index, symbol in enumerate(USABLE_SYMBOL_ORDER)}
    return sorted(
        rows,
        key=lambda row: (
            -int(row["quality_score"]),
            -int(row["best_overlap_rows"]),
            tie_order.get(str(row["symbol"]), 999),
        ),
    )


def define_oil_regime_labels(selected_proxy_symbol: str | None) -> list[dict[str, Any]]:
    common_fields = ["proxy_timestamp", "proxy_open", "proxy_high", "proxy_low", "proxy_close"]
    warning = "Descriptive macro-context label only; not a trade signal, blocker, filter, entry rule, or exit rule."
    labels = [
        ("oil_strength", common_fields + ["proxy_return"], "Oil proxy shows positive directional pressure."),
        ("oil_weakness", common_fields + ["proxy_return"], "Oil proxy shows negative directional pressure."),
        ("oil_shock_up", common_fields + ["proxy_return", "proxy_range"], "Oil proxy shows an unusually sharp upward move."),
        ("oil_shock_down", common_fields + ["proxy_return", "proxy_range"], "Oil proxy shows an unusually sharp downward move."),
        (
            "gold_oil_inflation_pressure_aligned",
            common_fields + ["xauusd_timestamp", "xauusd_close", "proxy_return"],
            "Gold and oil context move in a way that may describe inflation-pressure alignment.",
        ),
        (
            "gold_oil_safe_haven_conflict",
            common_fields + ["xauusd_timestamp", "xauusd_close", "proxy_return"],
            "Gold and oil context diverge in a way that may describe safe-haven or growth conflict.",
        ),
        (
            "oil_supply_shock_context_candidate",
            common_fields + ["proxy_return", "proxy_range", "gap_minutes"],
            "Oil proxy move may deserve later human review as a supply-shock context candidate.",
        ),
    ]
    return [
        {
            "label_name": name,
            "required_input_fields": fields,
            "timeframe_applicability": ["M5", "M10", "M15"],
            "selected_proxy_symbol": selected_proxy_symbol,
            "safe_asof_requirement": "Use only proxy bars with timestamp less than or equal to the XAUUSD timestamp.",
            "no_lookahead_rule": "Never use a later proxy bar, forward join, or nearest-future join.",
            "intended_interpretation": interpretation,
            "not_a_trade_signal_warning": warning,
        }
        for name, fields, interpretation in labels
    ]


def build_oil_proxy_quality_and_label_design(audit: dict[str, Any]) -> dict[str, Any]:
    ranking_table = rank_oil_proxies(audit)
    safe_ranking_table = [row for row in ranking_table if row.get("safe_asof_alignment_feasible") is True]
    selected = safe_ranking_table[0] if safe_ranking_table else None
    fallback = safe_ranking_table[1] if len(safe_ranking_table) > 1 else None
    selected_symbol = selected["symbol"] if selected else None
    fallback_symbol = fallback["symbol"] if fallback else None

    if audit.get("audit_status") not in {"oil_proxy_context_feasibility_completed"}:
        design_status = "oil_proxy_quality_and_label_design_blocked_missing_data"
    elif selected is None or selected.get("safe_asof_alignment_feasible") is not True:
        design_status = "oil_proxy_quality_and_label_design_completed_no_safe_proxy"
    else:
        design_status = "oil_proxy_quality_and_label_design_completed"

    labels = define_oil_regime_labels(selected_symbol)
    safe_by_symbol = {row["symbol"]: row["safe_asof_alignment_feasible"] for row in ranking_table}
    quality_scores = {row["symbol"]: row["quality_score"] for row in ranking_table}
    rejected = {
        symbol: details
        for symbol, details in audit.get("rejected_proxy_symbols", {}).items()
        if symbol not in {row["symbol"] for row in ranking_table}
    }

    report: dict[str, Any] = {
        "design_version": DESIGN_VERSION,
        "design_status": design_status,
        "source_oil_audit_version": audit.get("audit_version", SOURCE_OIL_AUDIT_VERSION),
        "candidate_symbols_ranked": [row["symbol"] for row in ranking_table],
        "selected_proxy_symbol_or_null": selected_symbol,
        "fallback_proxy_symbol_or_null": fallback_symbol,
        "selection_reason": _selection_reason(selected, fallback),
        "quality_scores_by_symbol": quality_scores,
        "ranking_table": ranking_table,
        "rejected_proxy_symbols": rejected,
        "safe_asof_alignment_feasible_by_symbol": safe_by_symbol,
        "selected_proxy_safe_asof_alignment_feasible": selected.get("safe_asof_alignment_feasible") if selected else False,
        "labels_defined": labels,
        "label_count": len(labels),
        "train_validation_only": True,
        "recommended_next_step": "v0_71_gold_macro_context_board_no_strategy",
        "warnings": [
            "research_infrastructure_only_not_strategy",
            "labels_are_descriptive_context_only",
            "labels_not_approved_for_trade_filtering",
            "asof_alignment_must_use_proxy_values_known_at_or_before_xauusd_timestamp",
        ],
    }
    for field in SAFETY_FALSE_FIELDS:
        report[field] = False
    report["safety"] = {
        "research_only": True,
        "context_design_only": True,
        "strategy_rules_created": False,
        "strategy_rules_modified": False,
        "trade_signals_output": False,
        "auto_execute_order": False,
        "scheduler_created": False,
        "execution_queue_created": False,
        **{field: report[field] for field in SAFETY_FALSE_FIELDS},
        "train_validation_only": True,
    }
    return report


def _selection_reason(selected: dict[str, Any] | None, fallback: dict[str, Any] | None) -> str:
    if selected is None:
        return "No safe usable oil proxy was available from v0_69 evidence."
    reason = (
        f"{selected['symbol']} selected by highest deterministic quality score "
        f"{selected['quality_score']} using availability, timeframe support, overlap, gaps, timestamp integrity, "
        "OHLC validity, and safe as-of feasibility evidence."
    )
    if fallback is not None and fallback["quality_score"] == selected["quality_score"]:
        reason += f" Exact score tie resolved by fixed tie-breaker order; {fallback['symbol']} kept as fallback."
    elif fallback is not None:
        reason += f" {fallback['symbol']} kept as fallback with score {fallback['quality_score']}."
    return reason


def build_and_write_report(
    audit_path: Path = DEFAULT_AUDIT_REPORT, output_path: Path = DEFAULT_OUTPUT_REPORT
) -> dict[str, Any]:
    report = build_oil_proxy_quality_and_label_design(load_audit_report(audit_path))
    write_report(report, output_path)
    return report
