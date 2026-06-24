"""Deterministic paper-only direction annotations for local XAUUSD rows."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WATCH_VERSION = "v0_90"
JOURNAL_VERSION = "v0_90"
DEFAULT_MARKET_CSV_DIR = Path("data")
DEFAULT_REPORT_PATH = Path("reports") / "xauusd_paper_directional_watcher_v0_90.json"
DEFAULT_JOURNAL_PATH = Path("reports") / "xauusd_paper_directional_journal_v0_90.jsonl"
DEFAULT_MAX_RECORDS = 50
DEFAULT_FROM_DATE = "2026-01-01"
DEFAULT_TIMEFRAMES = ("M5", "M10", "M15")
DEFAULT_LOOKBACK_BARS = 12
RECOMMENDED_NEXT_STEP = "v0_91_directional_outcome_tracker"
DIRECTION_ANNOTATION_METHOD = "fixed_ohlc_structure_no_optimization"


def annotate_paper_direction(row: dict[str, Any], previous_rows: list[dict[str, Any]], *, lookback_bars: int) -> dict[str, Any]:
    safe_lookback = max(1, int(lookback_bars))
    base = {
        "paper_observation_direction": None,
        "direction_assigned": None,
        "setup_label": "insufficient_structure",
        "reason": f"fixed_ohlc_structure_lookback_{safe_lookback}",
        "invalidation_note": "paper_observation_only_not_trade_signal",
        "status": "paper_direction_observation_recorded",
    }
    if len(previous_rows) < safe_lookback:
        return base

    window = previous_rows[-safe_lookback:]
    previous_range_high = max(float(item["high"]) for item in window)
    previous_range_low = min(float(item["low"]) for item in window)
    open_price = float(row["open"])
    high_price = float(row["high"])
    low_price = float(row["low"])
    close_price = float(row["close"])
    body_positive = close_price > open_price
    body_negative = close_price < open_price

    if close_price > previous_range_high and body_positive:
        return {
            **base,
            "paper_observation_direction": "paper_long",
            "direction_assigned": "paper_long",
            "setup_label": "bullish_displacement_observation",
        }
    if close_price < previous_range_low and body_negative:
        return {
            **base,
            "paper_observation_direction": "paper_short",
            "direction_assigned": "paper_short",
            "setup_label": "bearish_displacement_observation",
        }
    if high_price > previous_range_high or low_price < previous_range_low:
        return {**base, "setup_label": "range_expansion_no_direction"}
    return base


def build_xauusd_paper_directional_watcher_v0_90(
    *,
    market_csv_dir: str | Path = DEFAULT_MARKET_CSV_DIR,
    max_records: int = DEFAULT_MAX_RECORDS,
    from_date: str | None = DEFAULT_FROM_DATE,
    to_date: str | None = None,
    timeframes: list[str] | tuple[str, ...] | None = None,
    lookback_bars: int = DEFAULT_LOOKBACK_BARS,
    journal_path: str | Path = DEFAULT_JOURNAL_PATH,
) -> dict[str, Any]:
    safe_max_records = max(0, int(max_records))
    safe_lookback = max(1, int(lookback_bars))
    requested_timeframes = _normalize_timeframes(timeframes or DEFAULT_TIMEFRAMES)
    journal_file = _validated_journal_path(Path(journal_path))

    market_rows, source_files_used = read_local_market_csv_rows(Path(market_csv_dir), requested_timeframes)
    filtered_rows = _filter_market_rows(market_rows, from_date=from_date, to_date=to_date)
    selected_source = filtered_rows if filtered_rows else market_rows
    observation_records = _annotate_rows(selected_source, lookback_bars=safe_lookback)
    selected_records = observation_records[-safe_max_records:] if safe_max_records else []
    directional_records = [record for record in selected_records if record["paper_observation_direction"] is not None]
    null_records = [record for record in selected_records if record["paper_observation_direction"] is None]
    journal_records = [_journal_record_from_observation(record) for record in directional_records]
    _append_jsonl_records(journal_file, journal_records)

    if not market_rows:
        watch_status = "directional_watch_blocked"
        blockers = ["missing_local_market_csv_rows"]
    elif directional_records:
        watch_status = "directional_watch_completed"
        blockers = []
    else:
        watch_status = "directional_watch_completed_no_directional_records"
        blockers = []

    return {
        "watch_version": WATCH_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "watch_status": watch_status,
        "run_mode": "local_readonly_directional_paper_observation",
        "data_source_status": "local_readonly_market_csv",
        "real_market_observation_started": bool(market_rows),
        "paper_observation_only": True,
        "directional_observation_count": len(directional_records),
        "null_direction_observation_count": len(null_records),
        "journal_path": str(journal_file),
        "journal_record_count": _count_valid_jsonl_records(journal_file),
        "source_files_used": sorted({str(record["source_file"]) for record in selected_records}) or source_files_used,
        "timeframes_used": sorted({str(record["timeframe"]) for record in selected_records}, key=_timeframe_sort_key),
        "lookback_bars": safe_lookback,
        "direction_annotation_method": DIRECTION_ANNOTATION_METHOD,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "optimization_performed": False,
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
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "blockers": blockers,
        "directional_records": directional_records,
        "null_direction_records": null_records,
    }


def save_xauusd_paper_directional_watcher_report(
    report: dict[str, Any],
    output_path: str | Path = DEFAULT_REPORT_PATH,
) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_local_market_csv_rows(market_csv_dir: Path, requested_timeframes: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    if not market_csv_dir.exists() or not market_csv_dir.is_dir():
        return [], []
    rows: list[dict[str, Any]] = []
    source_files: set[str] = set()
    for csv_path in sorted(market_csv_dir.glob("*.csv")):
        if "xauusd" not in csv_path.name.lower():
            continue
        fallback_timeframe = _timeframe_from_market_csv_path(csv_path)
        if fallback_timeframe not in requested_timeframes:
            continue
        csv_rows = _read_one_market_csv(csv_path, fallback_timeframe, requested_timeframes)
        if csv_rows:
            rows.extend(csv_rows)
            source_files.add(str(csv_path))
    rows.sort(key=lambda row: (row["timestamp_dt"], _timeframe_sort_key(row["timeframe"]), row["source_file"]))
    return rows, sorted(source_files)


def _read_one_market_csv(csv_path: Path, fallback_timeframe: str | None, requested_timeframes: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            timestamp_text = _first_present(raw_row, ("timestamp_utc", "timestamp", "time", "datetime", "date"))
            if not timestamp_text:
                continue
            timeframe = str(raw_row.get("timeframe") or fallback_timeframe or "").upper()
            if timeframe not in requested_timeframes:
                continue
            try:
                row = {
                    "timestamp": _normalize_timestamp(timestamp_text),
                    "timestamp_dt": _parse_timestamp(timestamp_text),
                    "symbol": str(raw_row.get("symbol") or "XAUUSD").upper(),
                    "timeframe": timeframe,
                    "open": float(raw_row.get("open", "")),
                    "high": float(raw_row.get("high", "")),
                    "low": float(raw_row.get("low", "")),
                    "close": float(raw_row.get("close", "")),
                    "source_file": str(csv_path),
                    "source": str(raw_row.get("source") or f"local_readonly_market_csv:{csv_path.name}"),
                }
            except (TypeError, ValueError):
                continue
            rows.append(row)
    return rows


def _annotate_rows(rows: list[dict[str, Any]], *, lookback_bars: int) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_key.setdefault((str(row["symbol"]).upper(), str(row["timeframe"]).upper()), []).append(row)

    records: list[dict[str, Any]] = []
    for key_rows in by_key.values():
        ordered_rows = sorted(key_rows, key=lambda row: row["timestamp_dt"])
        previous_rows: list[dict[str, Any]] = []
        for row in ordered_rows:
            annotation = annotate_paper_direction(row, previous_rows, lookback_bars=lookback_bars)
            records.append(_observation_record(row, annotation, lookback_bars))
            previous_rows.append(row)
    return sorted(records, key=lambda row: (row["timestamp"], _timeframe_sort_key(str(row["timeframe"])), row["source_file"]))


def _observation_record(row: dict[str, Any], annotation: dict[str, Any], lookback_bars: int) -> dict[str, Any]:
    return {
        "timestamp": row["timestamp"],
        "symbol": row["symbol"],
        "timeframe": row["timeframe"],
        "setup_label": annotation["setup_label"],
        "paper_observation_direction": annotation["paper_observation_direction"],
        "direction_assigned": annotation["direction_assigned"],
        "reason": annotation["reason"],
        "invalidation_note": annotation["invalidation_note"],
        "status": annotation["status"],
        "source": row["source"],
        "source_file": row["source_file"],
        "lookback_bars": lookback_bars,
        "direction_annotation_method": DIRECTION_ANNOTATION_METHOD,
        "paper_observation_only": True,
        "trade_recommendation_output": False,
        "user_facing_buy_sell_signal_output": False,
        "order_send_called": False,
        "order_check_called": False,
    }


def _journal_record_from_observation(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "journal_version": JOURNAL_VERSION,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": record["timestamp"],
        "symbol": record["symbol"],
        "timeframe": record["timeframe"],
        "setup_label": record["setup_label"],
        "paper_observation_direction": record["paper_observation_direction"],
        "direction_assigned": record["direction_assigned"],
        "reason": record["reason"],
        "invalidation_note": record["invalidation_note"],
        "status": record["status"],
        "source": record["source"],
        "paper_observation_only": True,
        "trade_recommendation_output": False,
        "user_facing_buy_sell_signal_output": False,
        "order_send_called": False,
        "order_check_called": False,
    }


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


def _validated_journal_path(journal_path: Path) -> Path:
    if journal_path.suffix.lower() != ".jsonl":
        raise ValueError("journal_path_must_be_jsonl")
    resolved = journal_path.resolve()
    data_root = Path("data").resolve()
    if resolved == data_root or data_root in resolved.parents:
        raise ValueError("journal_path_must_not_be_under_data")
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    return journal_path


def _append_jsonl_records(journal_path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        return
    with journal_path.open("a", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _count_valid_jsonl_records(journal_path: Path) -> int:
    if not journal_path.exists():
        return 0
    count = 0
    for line in journal_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        json.loads(line)
        count += 1
    return count


def _normalize_timeframes(timeframes: list[str] | tuple[str, ...]) -> list[str]:
    normalized: list[str] = []
    allowed = set(DEFAULT_TIMEFRAMES)
    for timeframe in timeframes:
        value = str(timeframe).strip().upper()
        if value in allowed and value not in normalized:
            normalized.append(value)
    return normalized or list(DEFAULT_TIMEFRAMES)


def _timeframe_from_market_csv_path(csv_path: Path) -> str | None:
    match = re.search(r"(?<![A-Z0-9])M(5|10|15)(?![A-Z0-9])", csv_path.stem.upper())
    return f"M{match.group(1)}" if match else None


def _timeframe_sort_key(timeframe: str) -> int:
    order = {"M5": 0, "M10": 1, "M15": 2}
    return order.get(str(timeframe).upper(), 999)


def _first_present(row: dict[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value)
    return None


def _normalize_timestamp(value: Any) -> str:
    text = str(value).strip()
    if text.endswith("Z"):
        return text[:-1] + "+00:00"
    return text


def _parse_timestamp(value: Any) -> datetime:
    parsed = datetime.fromisoformat(_normalize_timestamp(value))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
