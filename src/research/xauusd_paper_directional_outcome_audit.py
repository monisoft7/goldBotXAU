"""Paper-only directional outcome audit for v0_90 XAUUSD observations."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

from src.research.xauusd_paper_direction_annotator import (
    DEFAULT_FROM_DATE,
    DEFAULT_MARKET_CSV_DIR,
    DEFAULT_TIMEFRAMES,
    DIRECTION_ANNOTATION_METHOD,
    annotate_paper_direction,
    read_local_market_csv_rows,
)

AUDIT_VERSION = "v0_91"
SOURCE_WATCH_VERSION = "v0_90"
DEFAULT_REPORT_PATH = Path("reports") / "xauusd_paper_directional_outcome_audit_v0_91.json"
DEFAULT_HORIZON_BARS = 12
DEFAULT_LOOKBACK_BARS = 12
DEFAULT_MAX_SCAN_ROWS = 5000
DEFAULT_MAX_DIRECTIONAL_RECORDS = 300
FAVORABLE_MOVE_THRESHOLD_POINTS = 2.0
ADVERSE_MOVE_THRESHOLD_POINTS = 2.0

OUTCOME_STATUSES = (
    "favorable_move_observed",
    "adverse_move_observed",
    "both_favorable_and_adverse_observed",
    "neutral_or_insufficient_move",
    "blocked_missing_future_rows",
)

SAFETY_FLAGS = {
    "paper_observation_only": True,
    "execution_allowed": False,
    "demo_allowed": False,
    "live_allowed": False,
    "order_send_called": False,
    "order_check_called": False,
    "order_send_allowed": False,
    "order_check_allowed": False,
    "trade_recommendation_output": False,
    "user_facing_buy_sell_signal_output": False,
    "data_csv_touched": False,
    "external_api_called": False,
    "external_data_downloaded": False,
    "threshold_search_performed": False,
    "parameter_grid_performed": False,
    "optimization_performed": False,
}

NEXT_STEP_BY_DECISION = {
    "insufficient_directional_frequency": "v0_92_request_alternative_fixed_direction_rules_from_external_reviewer",
    "current_direction_rule_not_promising": "v0_92_kill_current_direction_rule_and_request_alternatives",
    "current_direction_rule_promising_for_more_forward_paper_only": "v0_92_forward_paper_directional_loop_live_observation_no_demo",
    "inconclusive_continue_paper_only": "v0_92_request_alternative_fixed_direction_rules_from_external_reviewer",
}


def build_xauusd_paper_directional_outcome_audit_v0_91(
    *,
    market_csv_dir: str | Path = DEFAULT_MARKET_CSV_DIR,
    from_date: str | None = DEFAULT_FROM_DATE,
    to_date: str | None = None,
    timeframes: list[str] | tuple[str, ...] | None = None,
    horizon_bars: int = DEFAULT_HORIZON_BARS,
    lookback_bars: int = DEFAULT_LOOKBACK_BARS,
    max_scan_rows: int = DEFAULT_MAX_SCAN_ROWS,
    max_directional_records: int = DEFAULT_MAX_DIRECTIONAL_RECORDS,
) -> dict[str, Any]:
    safe_horizon = max(1, int(horizon_bars))
    safe_lookback = max(1, int(lookback_bars))
    safe_max_scan_rows = max(0, int(max_scan_rows))
    safe_max_directional_records = max(0, int(max_directional_records))
    requested_timeframes = _normalize_timeframes(timeframes or DEFAULT_TIMEFRAMES)

    market_rows, source_files_used = read_local_market_csv_rows(Path(market_csv_dir), requested_timeframes)
    filtered_rows = _filter_market_rows(market_rows, from_date=from_date, to_date=to_date)
    scan_rows = filtered_rows[:safe_max_scan_rows] if safe_max_scan_rows else []
    observations = _build_observations(scan_rows, lookback_bars=safe_lookback)
    directional_observations = [
        record for record in observations if record.get("paper_observation_direction") is not None
    ][:safe_max_directional_records]
    null_count = len(observations) - len([record for record in observations if record.get("paper_observation_direction") is not None])

    market_index = _index_market_rows(filtered_rows if filtered_rows else market_rows)
    outcome_records = [
        _evaluate_directional_observation(index, record, market_index, safe_horizon)
        for index, record in enumerate(directional_observations)
    ]

    outcome_counts = {status: 0 for status in OUTCOME_STATUSES}
    outcome_counts.update(Counter(str(record["outcome_status"]) for record in outcome_records))
    records_blocked = outcome_counts["blocked_missing_future_rows"]
    records_evaluated = len(outcome_records) - records_blocked
    decision = _decision(len(directional_observations), outcome_counts, records_evaluated)
    audit_status = _audit_status(decision, market_rows, records_evaluated)

    report = {
        "audit_version": AUDIT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_status": audit_status,
        "source_watch_version": SOURCE_WATCH_VERSION,
        "run_mode": "local_readonly_directional_outcome_audit",
        "data_source_status": "local_readonly_market_csv" if market_rows else "blocked_missing_local_market_csv_rows",
        "direction_annotation_method": DIRECTION_ANNOTATION_METHOD,
        "from_date": from_date,
        "to_date": to_date,
        "timeframes_requested": requested_timeframes,
        "horizon_bars": safe_horizon,
        "lookback_bars": safe_lookback,
        "max_scan_rows": safe_max_scan_rows,
        "max_directional_records": safe_max_directional_records,
        "scanned_row_count": len(scan_rows),
        "directional_observation_count": len(directional_observations),
        "null_direction_observation_count": null_count,
        "records_evaluated": records_evaluated,
        "records_blocked": records_blocked,
        "outcome_counts": outcome_counts,
        "favorable_rate": _rate(outcome_counts["favorable_move_observed"] + outcome_counts["both_favorable_and_adverse_observed"], records_evaluated),
        "adverse_rate": _rate(outcome_counts["adverse_move_observed"] + outcome_counts["both_favorable_and_adverse_observed"], records_evaluated),
        "both_favorable_and_adverse_rate": _rate(outcome_counts["both_favorable_and_adverse_observed"], records_evaluated),
        "neutral_rate": _rate(outcome_counts["neutral_or_insufficient_move"], records_evaluated),
        "average_close_move_points": _average_metric(outcome_records, "close_move_points"),
        "median_close_move_points": _median_metric(outcome_records, "close_move_points"),
        "average_max_favorable_move_points": _average_metric(outcome_records, "max_favorable_move_points"),
        "average_max_adverse_move_points": _average_metric(outcome_records, "max_adverse_move_points"),
        "result_by_timeframe": _group_result(outcome_records, "timeframe"),
        "result_by_direction": _group_result(outcome_records, "paper_observation_direction"),
        "decision": decision,
        "recommended_next_step": NEXT_STEP_BY_DECISION[decision],
        "favorable_move_threshold_points": FAVORABLE_MOVE_THRESHOLD_POINTS,
        "adverse_move_threshold_points": ADVERSE_MOVE_THRESHOLD_POINTS,
        "source_files_used": source_files_used,
        "blockers": [] if market_rows else ["missing_local_market_csv_rows"],
        "outcome_records": outcome_records,
        **SAFETY_FLAGS,
    }
    return report


def save_xauusd_paper_directional_outcome_audit_report(
    report: dict[str, Any],
    output_path: str | Path = DEFAULT_REPORT_PATH,
) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_observations(rows: list[dict[str, Any]], *, lookback_bars: int) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["symbol"]).upper(), str(row["timeframe"]).upper(), str(row["source_file"]))
        by_key.setdefault(key, []).append(row)

    observations: list[dict[str, Any]] = []
    for key_rows in by_key.values():
        ordered_rows = sorted(key_rows, key=lambda row: row["timestamp_dt"])
        previous_rows: list[dict[str, Any]] = []
        for row in ordered_rows:
            annotation = annotate_paper_direction(row, previous_rows, lookback_bars=lookback_bars)
            observations.append(
                {
                    "timestamp": row["timestamp"],
                    "timestamp_dt": row["timestamp_dt"],
                    "symbol": row["symbol"],
                    "timeframe": row["timeframe"],
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "source_file": row["source_file"],
                    "source": row["source"],
                    "setup_label": annotation["setup_label"],
                    "paper_observation_direction": annotation["paper_observation_direction"],
                    "direction_assigned": annotation["direction_assigned"],
                    "lookback_bars": lookback_bars,
                    "paper_observation_only": True,
                    "trade_recommendation_output": False,
                    "user_facing_buy_sell_signal_output": False,
                    "order_send_called": False,
                    "order_check_called": False,
                }
            )
            previous_rows.append(row)
    return sorted(observations, key=lambda row: (row["timestamp_dt"], _timeframe_sort_key(str(row["timeframe"])), row["source_file"]))


def _evaluate_directional_observation(
    observation_index: int,
    record: dict[str, Any],
    market_index: dict[tuple[str, str, str], list[dict[str, Any]]],
    horizon_bars: int,
) -> dict[str, Any]:
    direction = str(record["paper_observation_direction"])
    rows = market_index.get((str(record["symbol"]).upper(), str(record["timeframe"]).upper(), str(record["source_file"])), [])
    future_rows = [row for row in rows if row["timestamp_dt"] > record["timestamp_dt"]][:horizon_bars]
    base = {
        "observation_index": observation_index,
        "timestamp": record["timestamp"],
        "symbol": record["symbol"],
        "timeframe": record["timeframe"],
        "setup_label": record["setup_label"],
        "paper_observation_direction": direction,
        "horizon_bars": horizon_bars,
        "source_file": record["source_file"],
        "future_rows_used": len(future_rows),
        "entry_close": round(float(record["close"]), 6),
        "max_favorable_move_points": None,
        "max_adverse_move_points": None,
        "close_move_points": None,
        "outcome_status": "blocked_missing_future_rows",
        "paper_observation_only": True,
        "trade_recommendation_output": False,
        "user_facing_buy_sell_signal_output": False,
        "order_send_called": False,
        "order_check_called": False,
    }
    if len(future_rows) < horizon_bars:
        return base

    entry_close = float(record["close"])
    if direction == "paper_long":
        max_favorable = max(float(row["high"]) - entry_close for row in future_rows)
        max_adverse = max(entry_close - float(row["low"]) for row in future_rows)
        close_move = float(future_rows[-1]["close"]) - entry_close
    elif direction == "paper_short":
        max_favorable = max(entry_close - float(row["low"]) for row in future_rows)
        max_adverse = max(float(row["high"]) - entry_close for row in future_rows)
        close_move = entry_close - float(future_rows[-1]["close"])
    else:
        return base

    favorable_observed = max_favorable >= FAVORABLE_MOVE_THRESHOLD_POINTS
    adverse_observed = max_adverse >= ADVERSE_MOVE_THRESHOLD_POINTS
    if favorable_observed and adverse_observed:
        status = "both_favorable_and_adverse_observed"
    elif favorable_observed:
        status = "favorable_move_observed"
    elif adverse_observed:
        status = "adverse_move_observed"
    else:
        status = "neutral_or_insufficient_move"

    return {
        **base,
        "future_window_start": future_rows[0]["timestamp"],
        "future_window_end": future_rows[-1]["timestamp"],
        "max_favorable_move_points": round(max_favorable, 6),
        "max_adverse_move_points": round(max_adverse, 6),
        "close_move_points": round(close_move, 6),
        "outcome_status": status,
    }


def _index_market_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    indexed: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["symbol"]).upper(), str(row["timeframe"]).upper(), str(row["source_file"]))
        indexed.setdefault(key, []).append(row)
    for key_rows in indexed.values():
        key_rows.sort(key=lambda row: row["timestamp_dt"])
    return indexed


def _decision(directional_count: int, outcome_counts: dict[str, int], records_evaluated: int) -> str:
    favorable_rate = _rate(outcome_counts["favorable_move_observed"] + outcome_counts["both_favorable_and_adverse_observed"], records_evaluated)
    adverse_rate = _rate(outcome_counts["adverse_move_observed"] + outcome_counts["both_favorable_and_adverse_observed"], records_evaluated)
    if directional_count < 20:
        return "insufficient_directional_frequency"
    if favorable_rate <= adverse_rate:
        return "current_direction_rule_not_promising"
    if favorable_rate >= 0.55 and adverse_rate <= 0.40:
        return "current_direction_rule_promising_for_more_forward_paper_only"
    return "inconclusive_continue_paper_only"


def _audit_status(decision: str, market_rows: list[dict[str, Any]], records_evaluated: int) -> str:
    if not market_rows:
        return "directional_outcome_audit_blocked"
    if decision == "insufficient_directional_frequency":
        return "directional_outcome_audit_completed_insufficient_directional_sample"
    if decision == "current_direction_rule_not_promising":
        return "directional_outcome_audit_completed_not_promising"
    return "directional_outcome_audit_completed" if records_evaluated else "directional_outcome_audit_blocked"


def _group_result(records: list[dict[str, Any]], group_field: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(str(record.get(group_field)), []).append(record)
    return {
        key: {
            "records": len(items),
            "records_evaluated": sum(1 for item in items if item["outcome_status"] != "blocked_missing_future_rows"),
            "records_blocked": sum(1 for item in items if item["outcome_status"] == "blocked_missing_future_rows"),
            "outcome_counts": {status: sum(1 for item in items if item["outcome_status"] == status) for status in OUTCOME_STATUSES},
            "average_close_move_points": _average_metric(items, "close_move_points"),
        }
        for key, items in sorted(grouped.items())
    }


def _average_metric(records: list[dict[str, Any]], field: str) -> float | None:
    values = [float(record[field]) for record in records if record.get(field) is not None]
    return round(mean(values), 6) if values else None


def _median_metric(records: list[dict[str, Any]], field: str) -> float | None:
    values = [float(record[field]) for record in records if record.get(field) is not None]
    return round(median(values), 6) if values else None


def _rate(count: int, denominator: int) -> float:
    return round(count / denominator, 6) if denominator else 0.0


def _filter_market_rows(rows: list[dict[str, Any]], *, from_date: str | None, to_date: str | None) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for row in rows:
        timestamp = str(row["timestamp"])
        if from_date and timestamp[:10] < from_date:
            continue
        if to_date and timestamp[:10] > to_date:
            continue
        filtered.append(row)
    return filtered


def _normalize_timeframes(timeframes: list[str] | tuple[str, ...]) -> list[str]:
    allowed = set(DEFAULT_TIMEFRAMES)
    normalized: list[str] = []
    for timeframe in timeframes:
        value = str(timeframe).strip().upper()
        if value in allowed and value not in normalized:
            normalized.append(value)
    return normalized or list(DEFAULT_TIMEFRAMES)


def _timeframe_sort_key(timeframe: str) -> int:
    order = {"M5": 0, "M10": 1, "M15": 2}
    return order.get(str(timeframe).upper(), 999)
