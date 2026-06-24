"""Paper-only outcome tracker for v0_88 forward observation journal records."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRACKER_VERSION = "v0_89"
SOURCE_LOOP_VERSION = "v0_88"
DEFAULT_JOURNAL_PATH = Path("reports") / "xauusd_paper_forward_journal_v0_88.jsonl"
DEFAULT_REPORT_PATH = Path("reports") / "xauusd_paper_forward_outcome_tracker_v0_89.json"
DEFAULT_MARKET_CSV_DIR = Path("data")
DEFAULT_HORIZON_BARS = 12
DEFAULT_MAX_RECORDS = 100
FAVORABLE_MOVE_THRESHOLD_POINTS = 2.0
ADVERSE_MOVE_THRESHOLD_POINTS = -2.0
RECOMMENDED_NEXT_STEP = "v0_90_paper_forward_performance_summary"

OUTCOME_STATUSES = (
    "favorable_move_observed",
    "adverse_move_observed",
    "neutral_or_insufficient_move",
    "blocked_missing_future_rows",
    "blocked_missing_direction",
)


def build_xauusd_paper_forward_outcome_tracker_v0_89(
    *,
    journal_path: str | Path = DEFAULT_JOURNAL_PATH,
    market_csv_dir: str | Path = DEFAULT_MARKET_CSV_DIR,
    horizon_bars: int = DEFAULT_HORIZON_BARS,
    max_records: int = DEFAULT_MAX_RECORDS,
) -> dict[str, Any]:
    safe_horizon = max(1, int(horizon_bars))
    safe_max_records = max(0, int(max_records))
    journal_file = Path(journal_path)
    market_dir = Path(market_csv_dir)

    journal_records, journal_blockers = read_paper_forward_journal_records(journal_file, max_records=safe_max_records)
    market_rows, source_files_used = read_local_market_csv_rows(market_dir)

    outcome_records: list[dict[str, Any]] = []
    blockers = [*journal_blockers]
    if not market_rows:
        blockers.append("missing_local_market_csv_rows")

    if journal_records and market_rows:
        market_index = _index_market_rows(market_rows)
        for index, record in enumerate(journal_records):
            outcome_records.append(_evaluate_observation_record(index, record, market_index, safe_horizon))

    outcome_counts = {status: 0 for status in OUTCOME_STATUSES}
    outcome_counts.update(Counter(str(record["outcome_status"]) for record in outcome_records))
    records_blocked = sum(1 for record in outcome_records if str(record["outcome_status"]).startswith("blocked_"))
    records_evaluated = len(outcome_records) - records_blocked

    if not journal_records or not market_rows:
        tracker_status = "outcome_tracker_blocked"
    elif records_blocked:
        tracker_status = "outcome_tracker_completed_with_blocked_records"
    else:
        tracker_status = "outcome_tracker_completed"

    return {
        "tracker_version": TRACKER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tracker_status": tracker_status,
        "source_loop_version": SOURCE_LOOP_VERSION,
        "journal_path": str(journal_file),
        "records_read": len(journal_records),
        "records_evaluated": records_evaluated,
        "records_blocked": records_blocked,
        "outcome_counts": outcome_counts,
        "horizon_bars": safe_horizon,
        "favorable_move_threshold_points": FAVORABLE_MOVE_THRESHOLD_POINTS,
        "adverse_move_threshold_points": ADVERSE_MOVE_THRESHOLD_POINTS,
        "paper_observation_only": True,
        "data_source_status": "local_readonly_market_csv" if market_rows else "blocked_missing_local_market_csv_rows",
        "real_market_observation_used": bool(market_rows),
        "source_files_used": source_files_used,
        "outcome_records": outcome_records,
        "blockers": sorted(set(blockers)),
        "order_send_called": False,
        "order_check_called": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "trade_recommendation_output": False,
        "user_facing_buy_sell_signal_output": False,
        "data_csv_touched": False,
        "market_csv_created": False,
        "external_api_called": False,
        "external_data_downloaded": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def save_xauusd_paper_forward_outcome_tracker_report(
    report: dict[str, Any],
    output_path: str | Path = DEFAULT_REPORT_PATH,
) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_paper_forward_journal_records(journal_path: Path, *, max_records: int) -> tuple[list[dict[str, Any]], list[str]]:
    if not journal_path.exists():
        return [], [f"journal_missing: {journal_path}"]
    records: list[dict[str, Any]] = []
    blockers: list[str] = []
    for line_number, line in enumerate(journal_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            blockers.append(f"journal_invalid_jsonl_line_{line_number}: {exc}")
            continue
        if isinstance(payload, dict):
            records.append(payload)
    if max_records:
        records = records[:max_records]
    else:
        records = []
    return records, blockers


def read_local_market_csv_rows(market_csv_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not market_csv_dir.exists() or not market_csv_dir.is_dir():
        return [], []
    rows: list[dict[str, Any]] = []
    source_files: set[str] = set()
    for csv_path in sorted(market_csv_dir.glob("*.csv")):
        if "xauusd" not in csv_path.name.lower():
            continue
        csv_rows = _read_one_market_csv(csv_path)
        if csv_rows:
            rows.extend(csv_rows)
            source_files.add(str(csv_path))
    rows.sort(key=lambda row: (row["timestamp_dt"], row["timeframe"], row["source_file"]))
    return rows, sorted(source_files)


def _read_one_market_csv(csv_path: Path) -> list[dict[str, Any]]:
    fallback_timeframe = _timeframe_from_market_csv_path(csv_path)
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            timestamp_text = _first_present(raw_row, ("timestamp_utc", "timestamp", "time", "datetime", "date"))
            if not timestamp_text:
                continue
            timeframe = str(raw_row.get("timeframe") or fallback_timeframe or "").upper()
            if not timeframe:
                continue
            try:
                timestamp_dt = _parse_timestamp(timestamp_text)
                open_price = float(raw_row.get("open", ""))
                high_price = float(raw_row.get("high", ""))
                low_price = float(raw_row.get("low", ""))
                close_price = float(raw_row.get("close", ""))
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "timestamp": _normalize_timestamp(timestamp_text),
                    "timestamp_dt": timestamp_dt,
                    "symbol": str(raw_row.get("symbol") or "XAUUSD").upper(),
                    "timeframe": timeframe,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "source_file": str(csv_path),
                }
            )
    return rows


def _evaluate_observation_record(
    observation_index: int,
    record: dict[str, Any],
    market_index: dict[tuple[str, str], list[dict[str, Any]]],
    horizon_bars: int,
) -> dict[str, Any]:
    timestamp_text = record.get("timestamp")
    timeframe = str(record.get("timeframe") or "").upper()
    direction = _paper_direction(record)
    base = {
        "observation_index": observation_index,
        "timestamp": timestamp_text,
        "symbol": record.get("symbol") or "XAUUSD",
        "timeframe": timeframe or None,
        "setup_label": record.get("setup_label"),
        "paper_observation_direction": direction,
        "horizon_bars": horizon_bars,
        "max_favorable_move_points": None,
        "max_adverse_move_points": None,
        "close_move_points": None,
        "outcome_status": None,
        "paper_observation_only": True,
        "trade_recommendation_output": False,
        "order_send_called": False,
        "order_check_called": False,
    }
    if direction is None:
        return {**base, "outcome_status": "blocked_missing_direction"}
    if not timestamp_text or not timeframe:
        return {**base, "outcome_status": "blocked_missing_future_rows"}

    try:
        timestamp_dt = _parse_timestamp(str(timestamp_text))
    except ValueError:
        return {**base, "outcome_status": "blocked_missing_future_rows"}

    rows = market_index.get((str(base["symbol"]).upper(), timeframe), [])
    anchor = _anchor_row(rows, timestamp_dt)
    future_rows = [row for row in rows if row["timestamp_dt"] > timestamp_dt][:horizon_bars]
    if anchor is None or not future_rows:
        return {**base, "outcome_status": "blocked_missing_future_rows"}

    entry_close = float(anchor["close"])
    if direction == "up":
        max_favorable = max(float(row["high"]) - entry_close for row in future_rows)
        max_adverse = min(float(row["low"]) - entry_close for row in future_rows)
        close_move = float(future_rows[-1]["close"]) - entry_close
    else:
        max_favorable = max(entry_close - float(row["low"]) for row in future_rows)
        max_adverse = min(entry_close - float(row["high"]) for row in future_rows)
        close_move = entry_close - float(future_rows[-1]["close"])

    if max_favorable >= FAVORABLE_MOVE_THRESHOLD_POINTS:
        outcome_status = "favorable_move_observed"
    elif max_adverse <= ADVERSE_MOVE_THRESHOLD_POINTS:
        outcome_status = "adverse_move_observed"
    else:
        outcome_status = "neutral_or_insufficient_move"

    return {
        **base,
        "future_rows_used": len(future_rows),
        "entry_close": entry_close,
        "future_window_start": future_rows[0]["timestamp"],
        "future_window_end": future_rows[-1]["timestamp"],
        "max_favorable_move_points": round(max_favorable, 6),
        "max_adverse_move_points": round(max_adverse, 6),
        "close_move_points": round(close_move, 6),
        "outcome_status": outcome_status,
    }


def _index_market_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    indexed: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        indexed.setdefault((str(row["symbol"]).upper(), str(row["timeframe"]).upper()), []).append(row)
    return indexed


def _anchor_row(rows: list[dict[str, Any]], timestamp_dt: datetime) -> dict[str, Any] | None:
    anchor = None
    for row in rows:
        if row["timestamp_dt"] <= timestamp_dt:
            anchor = row
        else:
            break
    return anchor


def _paper_direction(record: dict[str, Any]) -> str | None:
    raw_direction = record.get("paper_observation_direction")
    if raw_direction in (None, ""):
        raw_direction = record.get("direction_assigned")
    if raw_direction in (None, ""):
        return None
    value = str(raw_direction).strip().lower()
    if value in {"up", "upward", "bullish", "long", "positive"}:
        return "up"
    if value in {"down", "downward", "bearish", "short", "negative"}:
        return "down"
    return None


def _first_present(row: dict[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value)
    return None


def _timeframe_from_market_csv_path(csv_path: Path) -> str | None:
    match = re.search(r"(?<![A-Z0-9])M(1|5|10|15|30|60)(?![A-Z0-9])", csv_path.stem.upper())
    return f"M{match.group(1)}" if match else None


def _normalize_timestamp(value: Any) -> str:
    text = str(value).strip()
    if text.endswith("Z"):
        return text[:-1] + "+00:00"
    return text


def _parse_timestamp(value: Any) -> datetime:
    text = _normalize_timestamp(value)
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
