"""Read-only MT5 XAUUSD low-timeframe CSV exporter."""

from __future__ import annotations

import csv
import importlib
import re
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

EXPORTER_VERSION = "v0_21"
SUPPORTED_TIMEFRAMES = {"M1": "TIMEFRAME_M1", "M5": "TIMEFRAME_M5"}


@dataclass(frozen=True)
class Mt5LowTfExportReport:
    exporter_version: str
    status: str
    symbol: str
    timeframe: str
    from_date: str
    to_date: str
    output_file: str | None
    row_count: int
    duplicate_timestamp_count: int
    safety: dict[str, bool]
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def export_xauusd_low_tf_csv(
    *,
    symbol: str = "XAUUSD",
    timeframe: str = "M1",
    from_date: str,
    to_date: str,
    data_dir: str | Path = "data",
    mt5_module: Any | None = None,
) -> Mt5LowTfExportReport:
    warnings: list[str] = []
    normalized_symbol = symbol.strip()
    normalized_timeframe = timeframe.strip().upper()

    if not _is_gold_symbol(normalized_symbol):
        return _report(
            status="symbol_not_found",
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            from_date=from_date,
            to_date=to_date,
            errors=["Symbol scope is limited to gold symbols containing XAU or GOLD."],
        )

    if normalized_timeframe not in SUPPORTED_TIMEFRAMES:
        return _report(
            status="export_failed",
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            from_date=from_date,
            to_date=to_date,
            errors=["Unsupported timeframe. Supported timeframes: M1, M5."],
        )

    mt5 = mt5_module
    if mt5 is None:
        try:
            mt5 = importlib.import_module("MetaTrader5")
        except ImportError:
            return _report(
                status="mt5_not_available",
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                from_date=from_date,
                to_date=to_date,
                errors=["MetaTrader5 package is not available."],
            )

    initialized = False
    try:
        if not mt5.initialize():
            return _report(
                status="mt5_initialize_failed",
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                from_date=from_date,
                to_date=to_date,
                errors=[_last_error_text(mt5)],
            )
        initialized = True

        if mt5.symbol_info(normalized_symbol) is None:
            return _report(
                status="symbol_not_found",
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                from_date=from_date,
                to_date=to_date,
                errors=[f"Symbol not found: {normalized_symbol}"],
            )

        if not mt5.symbol_select(normalized_symbol, True):
            return _report(
                status="symbol_select_failed",
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                from_date=from_date,
                to_date=to_date,
                errors=[f"Symbol select failed: {normalized_symbol}"],
            )

        mt5_timeframe = getattr(mt5, SUPPORTED_TIMEFRAMES[normalized_timeframe])
        rates = mt5.copy_rates_range(
            normalized_symbol,
            mt5_timeframe,
            _date_start_utc(from_date),
            _date_end_utc(to_date),
        )
        rows, duplicate_count = _normalize_rates(rates)
        if not rows:
            return _report(
                status="no_rates_returned",
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                from_date=from_date,
                to_date=to_date,
                duplicate_timestamp_count=duplicate_count,
                errors=[f"No {normalized_timeframe} rates returned for requested range."],
            )

        output_path = _output_path(data_dir, normalized_symbol, normalized_timeframe, from_date, to_date)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _write_csv(output_path, rows)

        if duplicate_count:
            warnings.append("Duplicate timestamps returned by MT5 were dropped.")

        return _report(
            status="exported",
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            from_date=from_date,
            to_date=to_date,
            output_file=str(output_path),
            row_count=len(rows),
            duplicate_timestamp_count=duplicate_count,
            warnings=warnings,
        )
    except Exception as exc:
        return _report(
            status="export_failed",
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            from_date=from_date,
            to_date=to_date,
            errors=[str(exc)],
        )
    finally:
        if initialized:
            mt5.shutdown()


def _normalize_rates(rates: Any) -> tuple[list[dict[str, float | str]], int]:
    if rates is None:
        return [], 0

    rows_by_timestamp: dict[str, dict[str, float | str]] = {}
    duplicate_count = 0
    for rate in list(rates):
        timestamp = _rate_value(rate, "time")
        timestamp_text = datetime.fromtimestamp(int(timestamp), UTC).replace(tzinfo=None).isoformat()
        if timestamp_text in rows_by_timestamp:
            duplicate_count += 1
            continue
        rows_by_timestamp[timestamp_text] = {
            "timestamp": timestamp_text,
            "open": float(_rate_value(rate, "open")),
            "high": float(_rate_value(rate, "high")),
            "low": float(_rate_value(rate, "low")),
            "close": float(_rate_value(rate, "close")),
            "volume": float(_rate_value(rate, "tick_volume", default=0.0)),
        }

    rows = sorted(rows_by_timestamp.values(), key=lambda row: str(row["timestamp"]))
    return rows, duplicate_count


def _rate_value(rate: Any, key: str, default: float | None = None) -> Any:
    try:
        return rate[key]
    except (KeyError, IndexError, TypeError, ValueError):
        if hasattr(rate, key):
            return getattr(rate, key)
        if default is not None:
            return default
        raise


def _write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _output_path(data_dir: str | Path, symbol: str, timeframe: str, from_date: str, to_date: str) -> Path:
    clean_symbol = re.sub(r"[^a-z0-9]+", "", symbol.lower())
    return Path(data_dir) / f"xauusd_{timeframe.lower()}_{clean_symbol}_{from_date}_{to_date}.csv"


def _date_start_utc(value: str) -> datetime:
    return datetime.combine(date.fromisoformat(value), time.min, tzinfo=UTC)


def _date_end_utc(value: str) -> datetime:
    return datetime.combine(date.fromisoformat(value), time.max, tzinfo=UTC)


def _is_gold_symbol(symbol: str) -> bool:
    upper = symbol.upper()
    return "XAU" in upper or "GOLD" in upper


def _last_error_text(mt5: Any) -> str:
    last_error = getattr(mt5, "last_error", None)
    if callable(last_error):
        return f"MT5 initialize failed: {last_error()}"
    return "MT5 initialize failed."


def _report(
    *,
    status: str,
    symbol: str,
    timeframe: str,
    from_date: str,
    to_date: str,
    output_file: str | None = None,
    row_count: int = 0,
    duplicate_timestamp_count: int = 0,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> Mt5LowTfExportReport:
    return Mt5LowTfExportReport(
        exporter_version=EXPORTER_VERSION,
        status=status,
        symbol=symbol,
        timeframe=timeframe,
        from_date=from_date,
        to_date=to_date,
        output_file=output_file,
        row_count=row_count,
        duplicate_timestamp_count=duplicate_timestamp_count,
        safety={
            "read_only": True,
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
            "order_check_allowed": False,
            "execution_queue_enabled": False,
            "buy_sell_output_allowed": False,
        },
        errors=errors or [],
        warnings=warnings or [],
    )
