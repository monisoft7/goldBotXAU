"""Local XAUUSD M15 data readiness auditor."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_m15_csvs

AUDITOR_VERSION = "v0_3"


@dataclass(frozen=True)
class DataAuditReport:
    auditor_version: str
    status: str
    file_count: int
    candle_count: int
    start_timestamp: str | None
    end_timestamp: str | None
    expected_timeframe_minutes: int
    detected_timeframe_minutes: int | None
    duplicate_timestamp_count: int
    invalid_ohlc_count: int
    non_positive_price_count: int
    missing_bar_count: int
    large_gap_count: int
    weekend_gap_count: int
    flat_candle_count: int
    warnings: list[str]
    errors: list[str]
    usable_for_backtest: bool
    safety: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_xauusd_data(
    data_dir: str | Path = "data",
    pattern: str = "xauusd_m15_*.csv",
    expected_timeframe_minutes: int = 15,
) -> DataAuditReport:
    root = Path(data_dir)
    files = sorted(root.glob(pattern)) if root.exists() else []
    warnings: list[str] = []
    errors: list[str] = []

    if not files:
        warnings.append("No local XAUUSD M15 CSV data found.")
        return _report(
            status="no_local_data_found",
            file_count=0,
            candle_count=0,
            expected_timeframe_minutes=expected_timeframe_minutes,
            warnings=warnings,
            errors=errors,
            usable_for_backtest=False,
        )

    try:
        load_result = load_xauusd_m15_csvs(root, pattern)
        records = load_result.records
    except ValueError as exc:
        errors.append(str(exc))
        status = "data_invalid"
        return _report(
            status=status,
            file_count=len(files),
            candle_count=0,
            expected_timeframe_minutes=expected_timeframe_minutes,
            warnings=warnings,
            errors=errors,
            usable_for_backtest=False,
        )

    stats = _inspect_records(records, expected_timeframe_minutes)
    warnings.extend(stats["warnings"])
    errors.extend(stats["errors"])

    invalid = (
        stats["duplicate_timestamp_count"] > 0
        or stats["invalid_ohlc_count"] > 0
        or stats["non_positive_price_count"] > 0
    )
    if invalid:
        status = "data_invalid"
        usable = False
    elif warnings:
        status = "data_has_warnings"
        usable = True
    else:
        status = "data_ready"
        usable = True

    return _report(
        status=status,
        file_count=len(files),
        candle_count=len(records),
        start_timestamp=stats["start_timestamp"],
        end_timestamp=stats["end_timestamp"],
        expected_timeframe_minutes=expected_timeframe_minutes,
        detected_timeframe_minutes=stats["detected_timeframe_minutes"],
        duplicate_timestamp_count=stats["duplicate_timestamp_count"],
        invalid_ohlc_count=stats["invalid_ohlc_count"],
        non_positive_price_count=stats["non_positive_price_count"],
        missing_bar_count=stats["missing_bar_count"],
        large_gap_count=stats["large_gap_count"],
        weekend_gap_count=stats["weekend_gap_count"],
        flat_candle_count=stats["flat_candle_count"],
        warnings=warnings,
        errors=errors,
        usable_for_backtest=usable,
    )


def _inspect_records(records: list[dict[str, float | str]], expected_minutes: int) -> dict[str, Any]:
    timestamps = [_parse_timestamp(str(record["timestamp"])) for record in records]
    duplicate_count = len(timestamps) - len(set(timestamps))
    invalid_ohlc_count = 0
    non_positive_price_count = 0
    flat_candle_count = 0
    warnings: list[str] = []
    errors: list[str] = []

    for record in records:
        open_price = float(record["open"])
        high_price = float(record["high"])
        low_price = float(record["low"])
        close_price = float(record["close"])
        if high_price < max(open_price, close_price) or low_price > min(open_price, close_price):
            invalid_ohlc_count += 1
        if min(open_price, high_price, low_price, close_price) <= 0:
            non_positive_price_count += 1
        if open_price == high_price == low_price == close_price:
            flat_candle_count += 1

    sorted_timestamps = sorted(timestamps)
    gap_stats = _gap_stats(sorted_timestamps, expected_minutes)
    detected_timeframe = _detect_timeframe_minutes(sorted_timestamps)

    if duplicate_count:
        errors.append("Duplicate timestamps found after normalization.")
    if invalid_ohlc_count:
        errors.append("Invalid OHLC candles found.")
    if non_positive_price_count:
        errors.append("Non-positive prices found.")
    if gap_stats["missing_bar_count"]:
        warnings.append("Non-weekend timestamp gaps found.")
    if gap_stats["weekend_gap_count"]:
        warnings.append("Weekend market closure gaps classified separately.")
    if flat_candle_count:
        warnings.append("Flat candles found.")

    return {
        "start_timestamp": sorted_timestamps[0].isoformat() if sorted_timestamps else None,
        "end_timestamp": sorted_timestamps[-1].isoformat() if sorted_timestamps else None,
        "detected_timeframe_minutes": detected_timeframe,
        "duplicate_timestamp_count": duplicate_count,
        "invalid_ohlc_count": invalid_ohlc_count,
        "non_positive_price_count": non_positive_price_count,
        "missing_bar_count": gap_stats["missing_bar_count"],
        "large_gap_count": gap_stats["large_gap_count"],
        "weekend_gap_count": gap_stats["weekend_gap_count"],
        "flat_candle_count": flat_candle_count,
        "warnings": warnings,
        "errors": errors,
    }


def _gap_stats(timestamps: list[datetime], expected_minutes: int) -> dict[str, int]:
    expected_delta = timedelta(minutes=expected_minutes)
    missing_bar_count = 0
    large_gap_count = 0
    weekend_gap_count = 0

    for previous, current in zip(timestamps, timestamps[1:]):
        delta = current - previous
        if delta <= expected_delta:
            continue
        if _is_weekend_gap(previous, current):
            weekend_gap_count += 1
            continue
        missing_bar_count += max(1, int(delta / expected_delta) - 1)
        large_gap_count += 1

    return {
        "missing_bar_count": missing_bar_count,
        "large_gap_count": large_gap_count,
        "weekend_gap_count": weekend_gap_count,
    }


def _is_weekend_gap(previous: datetime, current: datetime) -> bool:
    cursor = previous
    while cursor <= current:
        if cursor.weekday() in {5, 6}:
            return True
        cursor += timedelta(days=1)
    return False


def _detect_timeframe_minutes(timestamps: list[datetime]) -> int | None:
    deltas = [
        int((current - previous).total_seconds() // 60)
        for previous, current in zip(timestamps, timestamps[1:])
        if current > previous
    ]
    if not deltas:
        return None
    return min(deltas)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _report(
    *,
    status: str,
    file_count: int,
    candle_count: int,
    expected_timeframe_minutes: int,
    warnings: list[str],
    errors: list[str],
    usable_for_backtest: bool,
    start_timestamp: str | None = None,
    end_timestamp: str | None = None,
    detected_timeframe_minutes: int | None = None,
    duplicate_timestamp_count: int = 0,
    invalid_ohlc_count: int = 0,
    non_positive_price_count: int = 0,
    missing_bar_count: int = 0,
    large_gap_count: int = 0,
    weekend_gap_count: int = 0,
    flat_candle_count: int = 0,
) -> DataAuditReport:
    return DataAuditReport(
        auditor_version=AUDITOR_VERSION,
        status=status,
        file_count=file_count,
        candle_count=candle_count,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        expected_timeframe_minutes=expected_timeframe_minutes,
        detected_timeframe_minutes=detected_timeframe_minutes,
        duplicate_timestamp_count=duplicate_timestamp_count,
        invalid_ohlc_count=invalid_ohlc_count,
        non_positive_price_count=non_positive_price_count,
        missing_bar_count=missing_bar_count,
        large_gap_count=large_gap_count,
        weekend_gap_count=weekend_gap_count,
        flat_candle_count=flat_candle_count,
        warnings=warnings,
        errors=errors,
        usable_for_backtest=usable_for_backtest,
        safety={
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
        },
    )
