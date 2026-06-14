"""Local-only XAUUSD forward observation CSV schema adapter."""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.data.xauusd_timeframe_resampler import REQUIRED_COLUMNS as EXPORTER_RESAMPLER_COLUMNS
from src.research.xauusd_forward_observation_runner import (
    ALLOWED_SYMBOLS,
    ALLOWED_TIMEFRAMES,
    EXPECTED_CSV_SCHEMA,
)

ADAPTER_VERSION = "v0_34_1"
DEFAULT_SOURCE = "local_exporter_schema_adapter_v0_34_1"


@dataclass(frozen=True)
class XauusdForwardObservationSchemaAdapterReport:
    adapter_version: str
    adapter_status: str
    input_file: str
    output_file: str | None
    input_row_count: int
    output_row_count: int
    input_schema: list[str]
    exporter_resampler_schema_source: str
    exporter_resampler_schema: list[str]
    expected_output_schema: list[str]
    supported_timeframes: list[str]
    symbol: str | None
    timeframe: str | None
    spread_policy: str
    mt5_called: bool
    data_exported_from_mt5: bool
    execution_allowed: bool
    demo_allowed: bool
    live_allowed: bool
    repeated_oos_review: bool
    candidate_rules_modified: bool
    safety: dict[str, bool]
    errors: list[str]
    warnings: list[str]
    next_recommended_step: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_xauusd_forward_observation_csv(
    *,
    input_file: str | Path,
    output_file: str | Path | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    project_root: str | Path = ".",
) -> XauusdForwardObservationSchemaAdapterReport:
    input_path = Path(input_file)
    root = Path(project_root).resolve()
    output_path = Path(output_file) if output_file is not None else _default_output_path(input_path, root)
    normalized_symbol_arg = symbol.strip() if symbol else None
    normalized_timeframe_arg = timeframe.strip().upper() if timeframe else None

    if normalized_symbol_arg is not None and normalized_symbol_arg not in ALLOWED_SYMBOLS:
        return _report(
            adapter_status="blocked_invalid_metadata",
            input_file=input_path,
            output_file=None,
            symbol=normalized_symbol_arg,
            timeframe=normalized_timeframe_arg,
            errors=["symbol_not_allowed"],
        )

    if normalized_timeframe_arg is not None and normalized_timeframe_arg not in ALLOWED_TIMEFRAMES:
        return _report(
            adapter_status="blocked_unsupported_timeframe",
            input_file=input_path,
            output_file=None,
            symbol=normalized_symbol_arg,
            timeframe=normalized_timeframe_arg,
            errors=["timeframe_not_supported"],
        )

    if not input_path.exists():
        return _report(
            adapter_status="input_not_found",
            input_file=input_path,
            output_file=None,
            symbol=normalized_symbol_arg,
            timeframe=normalized_timeframe_arg,
            errors=[f"input_file_missing: {input_path}"],
        )

    if not _is_under_local_output_root(output_path, root):
        return _report(
            adapter_status="blocked_invalid_output_path",
            input_file=input_path,
            output_file=None,
            symbol=normalized_symbol_arg,
            timeframe=normalized_timeframe_arg,
            errors=["output_file_must_be_under_data_or_reports"],
        )

    try:
        raw_rows, input_schema = _read_csv_rows(input_path)
    except Exception as exc:
        return _report(
            adapter_status="adapter_failed",
            input_file=input_path,
            output_file=None,
            symbol=normalized_symbol_arg,
            timeframe=normalized_timeframe_arg,
            errors=[str(exc)],
        )

    if not raw_rows:
        return _report(
            adapter_status="blocked_empty_input",
            input_file=input_path,
            output_file=None,
            input_schema=input_schema,
            symbol=normalized_symbol_arg,
            timeframe=normalized_timeframe_arg,
            errors=["input_csv_rows_empty"],
        )

    warnings: list[str] = []
    normalized_rows: list[dict[str, Any]] = []
    try:
        for row in raw_rows:
            normalized_rows.append(
                _normalize_row(
                    row=row,
                    input_path=input_path,
                    symbol_arg=normalized_symbol_arg,
                    timeframe_arg=normalized_timeframe_arg,
                    warnings=warnings,
                )
            )
    except ValueError as exc:
        return _report(
            adapter_status="blocked_schema_mismatch",
            input_file=input_path,
            output_file=None,
            input_row_count=len(raw_rows),
            input_schema=input_schema,
            symbol=normalized_symbol_arg,
            timeframe=normalized_timeframe_arg,
            errors=[str(exc)],
            warnings=sorted(set(warnings)),
        )

    symbols = sorted({str(row["symbol"]) for row in normalized_rows})
    timeframes = sorted({str(row["timeframe"]) for row in normalized_rows})
    if len(symbols) != 1:
        return _report(
            adapter_status="blocked_inconsistent_metadata",
            input_file=input_path,
            output_file=None,
            input_row_count=len(raw_rows),
            input_schema=input_schema,
            errors=["input_csv_contains_multiple_symbols"],
            warnings=sorted(set(warnings)),
        )
    if len(timeframes) != 1:
        return _report(
            adapter_status="blocked_inconsistent_metadata",
            input_file=input_path,
            output_file=None,
            input_row_count=len(raw_rows),
            input_schema=input_schema,
            errors=["input_csv_contains_multiple_timeframes"],
            warnings=sorted(set(warnings)),
        )

    normalized_rows = sorted(normalized_rows, key=lambda row: str(row["timestamp_utc"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_normalized_csv(output_path, normalized_rows)

    return _report(
        adapter_status="framework_ready",
        input_file=input_path,
        output_file=output_path,
        input_row_count=len(raw_rows),
        output_row_count=len(normalized_rows),
        input_schema=input_schema,
        symbol=symbols[0],
        timeframe=timeframes[0],
        warnings=sorted(set(warnings)),
    )


def _normalize_row(
    *,
    row: dict[str, Any],
    input_path: Path,
    symbol_arg: str | None,
    timeframe_arg: str | None,
    warnings: list[str],
) -> dict[str, Any]:
    symbol = _metadata_value(row, "symbol", symbol_arg)
    timeframe = _metadata_value(row, "timeframe", timeframe_arg)
    if not symbol:
        raise ValueError("explicit_symbol_required_when_missing_from_csv")
    if not timeframe:
        raise ValueError("explicit_timeframe_required_when_missing_from_csv")
    timeframe = timeframe.upper()
    if symbol not in ALLOWED_SYMBOLS:
        raise ValueError("row_symbol_not_allowed")
    if timeframe not in ALLOWED_TIMEFRAMES:
        raise ValueError("row_timeframe_not_supported")

    timestamp = _timestamp_value(row)
    if timestamp is None:
        raise ValueError("timestamp_field_missing")
    timestamp_utc = _format_timestamp_utc(timestamp)

    spread = _field_value(row, "spread")
    spread_unavailable = False
    if spread in (None, ""):
        spread = "0"
        spread_unavailable = True
        warnings.append("spread_unavailable_from_exporter_set_to_0")

    return {
        "timestamp_utc": timestamp_utc,
        "symbol": symbol,
        "timeframe": timeframe,
        "open": _required_field(row, "open"),
        "high": _required_field(row, "high"),
        "low": _required_field(row, "low"),
        "close": _required_field(row, "close"),
        "tick_volume": _tick_volume_value(row),
        "spread": spread,
        "source": _source_value(row, input_path, spread_unavailable=spread_unavailable),
    }


def _metadata_value(row: dict[str, Any], field: str, explicit_value: str | None) -> str | None:
    csv_value = _field_value(row, field)
    if csv_value not in (None, ""):
        value = str(csv_value).strip()
        if explicit_value is not None and explicit_value != value:
            raise ValueError(f"explicit_{field}_does_not_match_csv")
        return value
    return explicit_value


def _timestamp_value(row: dict[str, Any]) -> str | None:
    timestamp = _field_value(row, "timestamp_utc") or _field_value(row, "timestamp")
    if timestamp not in (None, ""):
        return str(timestamp)
    date_value = _field_value(row, "date")
    time_value = _field_value(row, "time")
    if date_value not in (None, "") and time_value not in (None, ""):
        return f"{date_value}T{time_value}"
    return None


def _format_timestamp_utc(value: str) -> str:
    timestamp_text = value.replace("Z", "+00:00")
    timestamp_text = timestamp_text.replace(" ", "T")
    parsed = datetime.fromisoformat(timestamp_text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _tick_volume_value(row: dict[str, Any]) -> Any:
    tick_volume = _field_value(row, "tick_volume")
    if tick_volume not in (None, ""):
        return tick_volume
    volume = _field_value(row, "volume")
    if volume not in (None, ""):
        return volume
    raise ValueError("tick_volume_or_exporter_volume_field_missing")


def _source_value(row: dict[str, Any], input_path: Path, *, spread_unavailable: bool) -> str:
    source = _field_value(row, "source")
    if source not in (None, ""):
        return str(source)
    suffix = ";spread=unavailable_from_exporter" if spread_unavailable else ""
    return f"{DEFAULT_SOURCE}:{input_path.name}{suffix}"


def _required_field(row: dict[str, Any], field: str) -> Any:
    value = _field_value(row, field)
    if value in (None, ""):
        raise ValueError(f"{field}_field_missing")
    return value


def _field_value(row: dict[str, Any], field: str) -> Any:
    aliases = _aliases(field)
    for key, value in row.items():
        if _normalize_field_name(key) in aliases:
            return value
    return None


def _aliases(field: str) -> set[str]:
    base = _normalize_field_name(field)
    aliases = {base}
    if field == "timestamp_utc":
        aliases.update({"timestamp", "datetime"})
    if field == "tick_volume":
        aliases.update({"volume", "tickvol", "tick_volume"})
    return aliases


def _normalize_field_name(field: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", field.strip().lower()).strip("_")


def _read_csv_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        return list(reader), fieldnames


def _write_normalized_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_CSV_SCHEMA)
        writer.writeheader()
        writer.writerows(rows)


def _default_output_path(input_path: Path, root: Path) -> Path:
    clean_stem = re.sub(r"[^a-z0-9]+", "_", input_path.stem.lower()).strip("_")
    return root / "data" / f"{clean_stem}_forward_observation_v0_34_1.csv"


def _is_under_local_output_root(path: Path, root: Path) -> bool:
    resolved = path.resolve()
    allowed_roots = [(root / "data").resolve(), (root / "reports").resolve()]
    for allowed_root in allowed_roots:
        try:
            resolved.relative_to(allowed_root)
            return True
        except ValueError:
            continue
    return False


def _report(
    *,
    adapter_status: str,
    input_file: str | Path,
    output_file: str | Path | None,
    input_row_count: int = 0,
    output_row_count: int = 0,
    input_schema: list[str] | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> XauusdForwardObservationSchemaAdapterReport:
    return XauusdForwardObservationSchemaAdapterReport(
        adapter_version=ADAPTER_VERSION,
        adapter_status=adapter_status,
        input_file=str(input_file),
        output_file=str(output_file) if output_file is not None else None,
        input_row_count=input_row_count,
        output_row_count=output_row_count,
        input_schema=input_schema or [],
        exporter_resampler_schema_source="src.data.xauusd_timeframe_resampler.REQUIRED_COLUMNS",
        exporter_resampler_schema=list(EXPORTER_RESAMPLER_COLUMNS),
        expected_output_schema=list(EXPECTED_CSV_SCHEMA),
        supported_timeframes=list(ALLOWED_TIMEFRAMES),
        symbol=symbol,
        timeframe=timeframe,
        spread_policy="set_to_0_with_warning_when_unavailable_from_exporter",
        mt5_called=False,
        data_exported_from_mt5=False,
        execution_allowed=False,
        demo_allowed=False,
        live_allowed=False,
        repeated_oos_review=False,
        candidate_rules_modified=False,
        safety={
            "local_csv_read_only": True,
            "mt5_called": False,
            "data_exported_from_mt5": False,
            "execution_allowed": False,
            "demo_allowed": False,
            "live_allowed": False,
            "order_send_allowed": False,
            "order_check_allowed": False,
            "execution_queue_allowed": False,
            "recommendation_output_allowed": False,
            "directional_instruction_output_allowed": False,
            "new_oos_evaluation_allowed": False,
            "candidate_rules_modified": False,
        },
        errors=errors or [],
        warnings=warnings or [],
        next_recommended_step="v0_34_2 normalize local forward CSV files and rerun journal pass, no execution",
    )
