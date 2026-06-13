"""Local-only XAUUSD timeframe resampler."""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

RESAMPLER_VERSION = "v0_21"
TARGET_TIMEFRAME = "M10"
SUPPORTED_SOURCE_MINUTES = {"M1": 1, "M5": 5}
REQUIRED_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class XauusdResampleReport:
    resampler_version: str
    status: str
    input_file: str
    output_file: str | None
    source_timeframe: str | None
    target_timeframe: str
    input_row_count: int
    output_row_count: int
    duplicate_timestamp_count: int
    incomplete_bar_count: int
    safety: dict[str, bool]
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resample_xauusd_timeframe_csv(
    *,
    input_file: str | Path,
    target_timeframe: str = TARGET_TIMEFRAME,
    data_dir: str | Path = "data",
    source_timeframe: str | None = None,
) -> XauusdResampleReport:
    input_path = Path(input_file)
    normalized_target = target_timeframe.strip().upper()
    normalized_source = source_timeframe.strip().upper() if source_timeframe else _infer_source_timeframe(input_path)

    if not input_path.exists():
        return _report(status="input_not_found", input_file=input_path, target_timeframe=normalized_target)

    if normalized_target != TARGET_TIMEFRAME:
        return _report(
            status="invalid_input",
            input_file=input_path,
            source_timeframe=normalized_source,
            target_timeframe=normalized_target,
            errors=["Unsupported target timeframe. Supported target timeframe: M10."],
        )

    if normalized_source not in SUPPORTED_SOURCE_MINUTES:
        return _report(
            status="invalid_input",
            input_file=input_path,
            source_timeframe=normalized_source,
            target_timeframe=normalized_target,
            errors=["Unable to infer supported source timeframe M1 or M5."],
        )

    try:
        rows, duplicate_count, input_row_count = _read_normalized_rows(input_path)
        if not rows:
            return _report(
                status="invalid_input",
                input_file=input_path,
                source_timeframe=normalized_source,
                target_timeframe=normalized_target,
                input_row_count=input_row_count,
                duplicate_timestamp_count=duplicate_count,
                errors=["Input contains no usable normalized rows."],
            )

        output_rows, incomplete_count = _resample_rows(rows, SUPPORTED_SOURCE_MINUTES[normalized_source])
        if not output_rows:
            return _report(
                status="no_complete_bars",
                input_file=input_path,
                source_timeframe=normalized_source,
                target_timeframe=normalized_target,
                input_row_count=input_row_count,
                duplicate_timestamp_count=duplicate_count,
                incomplete_bar_count=incomplete_count,
                errors=["No complete M10 bars were available."],
            )

        output_path = _output_path(data_dir, input_path, output_rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _write_csv(output_path, output_rows)

        warnings: list[str] = []
        if duplicate_count:
            warnings.append("Duplicate timestamps were dropped before resampling.")
        if incomplete_count:
            warnings.append("Incomplete M10 bars were dropped.")

        return _report(
            status="resampled",
            input_file=input_path,
            output_file=output_path,
            source_timeframe=normalized_source,
            target_timeframe=normalized_target,
            input_row_count=input_row_count,
            output_row_count=len(output_rows),
            duplicate_timestamp_count=duplicate_count,
            incomplete_bar_count=incomplete_count,
            warnings=warnings,
        )
    except Exception as exc:
        return _report(
            status="resample_failed",
            input_file=input_path,
            source_timeframe=normalized_source,
            target_timeframe=normalized_target,
            errors=[str(exc)],
        )


def _read_normalized_rows(path: Path) -> tuple[list[dict[str, float | datetime | str]], int, int]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or any(column not in reader.fieldnames for column in REQUIRED_COLUMNS):
            raise ValueError("Input CSV must include timestamp, open, high, low, close, volume columns.")

        rows_by_timestamp: dict[datetime, dict[str, float | datetime | str]] = {}
        input_row_count = 0
        duplicate_count = 0
        for row in reader:
            input_row_count += 1
            timestamp = datetime.fromisoformat(str(row["timestamp"]))
            timestamp = timestamp.replace(tzinfo=None)
            if timestamp in rows_by_timestamp:
                duplicate_count += 1
                continue
            rows_by_timestamp[timestamp] = {
                "timestamp": timestamp,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }

    return [rows_by_timestamp[key] for key in sorted(rows_by_timestamp)], duplicate_count, input_row_count


def _resample_rows(rows: list[dict[str, float | datetime | str]], source_minutes: int) -> tuple[list[dict[str, float | str]], int]:
    target_minutes = 10
    expected_count = target_minutes // source_minutes
    grouped: dict[datetime, list[dict[str, float | datetime | str]]] = {}
    for row in rows:
        timestamp = row["timestamp"]
        if not isinstance(timestamp, datetime):
            raise ValueError("Internal timestamp normalization failed.")
        bucket = timestamp.replace(minute=(timestamp.minute // target_minutes) * target_minutes, second=0, microsecond=0)
        grouped.setdefault(bucket, []).append(row)

    output_rows: list[dict[str, float | str]] = []
    incomplete_count = 0
    for bucket in sorted(grouped):
        bucket_rows = sorted(grouped[bucket], key=lambda row: row["timestamp"])
        expected_timestamps = [bucket + timedelta(minutes=source_minutes * index) for index in range(expected_count)]
        actual_timestamps = [row["timestamp"] for row in bucket_rows]
        if actual_timestamps != expected_timestamps:
            incomplete_count += 1
            continue

        output_rows.append(
            {
                "timestamp": bucket.isoformat(),
                "open": float(bucket_rows[0]["open"]),
                "high": max(float(row["high"]) for row in bucket_rows),
                "low": min(float(row["low"]) for row in bucket_rows),
                "close": float(bucket_rows[-1]["close"]),
                "volume": sum(float(row["volume"]) for row in bucket_rows),
            }
        )

    return output_rows, incomplete_count


def _write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def _infer_source_timeframe(path: Path) -> str | None:
    stem = path.stem.lower()
    if re.search(r"(^|_)m1(_|$)", stem):
        return "M1"
    if re.search(r"(^|_)m5(_|$)", stem):
        return "M5"
    return None


def _output_path(data_dir: str | Path, input_path: Path, rows: list[dict[str, float | str]]) -> Path:
    clean_source = re.sub(r"[^a-z0-9]+", "_", input_path.stem.lower()).strip("_")
    from_date = str(rows[0]["timestamp"])[:10]
    to_date = str(rows[-1]["timestamp"])[:10]
    return Path(data_dir) / f"xauusd_m10_{clean_source}_{from_date}_{to_date}.csv"


def _report(
    *,
    status: str,
    input_file: str | Path,
    target_timeframe: str,
    output_file: str | Path | None = None,
    source_timeframe: str | None = None,
    input_row_count: int = 0,
    output_row_count: int = 0,
    duplicate_timestamp_count: int = 0,
    incomplete_bar_count: int = 0,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> XauusdResampleReport:
    return XauusdResampleReport(
        resampler_version=RESAMPLER_VERSION,
        status=status,
        input_file=str(input_file),
        output_file=str(output_file) if output_file is not None else None,
        source_timeframe=source_timeframe,
        target_timeframe=target_timeframe,
        input_row_count=input_row_count,
        output_row_count=output_row_count,
        duplicate_timestamp_count=duplicate_timestamp_count,
        incomplete_bar_count=incomplete_bar_count,
        safety={
            "local_only": True,
            "mt5_called": False,
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
            "execution_queue_enabled": False,
        },
        errors=errors or [],
        warnings=warnings or [],
    )
