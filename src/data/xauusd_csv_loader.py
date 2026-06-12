"""Local XAUUSD M15 CSV loader.

This module only reads files already present on disk. It has no network,
broker, or platform connection behavior.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

DEFAULT_PATTERN = "xauusd_m15_*.csv"
TIME_COLUMNS = ("time", "date", "datetime", "timestamp")
REQUIRED_PRICE_COLUMNS = ("open", "high", "low", "close")
VOLUME_COLUMNS = ("volume", "tick_volume")


@dataclass(frozen=True)
class CandleLoadResult:
    records: list[dict[str, float | str]]
    files: list[Path]


def load_xauusd_m15_csvs(
    data_dir: str | Path = "data",
    pattern: str = DEFAULT_PATTERN,
) -> CandleLoadResult:
    """Load and normalize all matching local XAUUSD M15 CSV files."""
    root = Path(data_dir)
    files = sorted(root.glob(pattern)) if root.exists() else []
    records: list[dict[str, float | str]] = []

    for file_path in files:
        records.extend(load_xauusd_csv(file_path))

    records = sorted(records, key=lambda row: str(row["timestamp"]))
    _validate_no_duplicate_timestamps(records)
    return CandleLoadResult(records=records, files=files)


def load_xauusd_csv(path: str | Path) -> list[dict[str, float | str]]:
    """Load one local CSV and normalize rows to timestamp/OHLCV records."""
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {csv_path}")

        column_map = _build_column_map(reader.fieldnames)
        records = [_normalize_row(row, column_map) for row in reader]

    records = sorted(records, key=lambda row: str(row["timestamp"]))
    _validate_no_duplicate_timestamps(records)
    return records


def _build_column_map(fieldnames: Iterable[str]) -> dict[str, str | None]:
    normalized = {name.strip().lower(): name for name in fieldnames}

    time_column = next((normalized[name] for name in TIME_COLUMNS if name in normalized), None)
    if time_column is None:
        raise ValueError("CSV must contain one timestamp column.")

    missing = [name for name in REQUIRED_PRICE_COLUMNS if name not in normalized]
    if missing:
        raise ValueError(f"CSV missing required OHLC columns: {', '.join(missing)}")

    volume_column = next((normalized[name] for name in VOLUME_COLUMNS if name in normalized), None)
    return {
        "timestamp": time_column,
        "open": normalized["open"],
        "high": normalized["high"],
        "low": normalized["low"],
        "close": normalized["close"],
        "volume": volume_column,
    }


def _normalize_row(row: dict[str, str], column_map: dict[str, str | None]) -> dict[str, float | str]:
    timestamp = _normalize_timestamp(row[str(column_map["timestamp"])])
    open_price = _to_float(row[str(column_map["open"])], "open")
    high_price = _to_float(row[str(column_map["high"])], "high")
    low_price = _to_float(row[str(column_map["low"])], "low")
    close_price = _to_float(row[str(column_map["close"])], "close")

    if high_price < max(open_price, close_price):
        raise ValueError("Candle high must be greater than or equal to open and close.")
    if low_price > min(open_price, close_price):
        raise ValueError("Candle low must be less than or equal to open and close.")

    volume_column = column_map["volume"]
    volume = _to_float(row[volume_column], "volume") if volume_column else 0.0

    return {
        "timestamp": timestamp,
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "volume": volume,
    }


def _normalize_timestamp(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError("Timestamp cannot be empty.")

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).isoformat()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(raw).isoformat()
    except ValueError:
        return raw


def _to_float(value: str, column_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Column {column_name} must be numeric.") from exc


def _validate_no_duplicate_timestamps(records: list[dict[str, float | str]]) -> None:
    seen: set[str] = set()
    for record in records:
        timestamp = str(record["timestamp"])
        if timestamp in seen:
            raise ValueError(f"Duplicate timestamp after normalization: {timestamp}")
        seen.add(timestamp)
