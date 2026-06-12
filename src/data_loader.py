"""Local CSV loading utilities for XAUUSD OHLCV research data."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = ("time", "open", "high", "low", "close")


def load_ohlcv_csv(path: str | Path) -> Any:
    """Load local OHLCV CSV data and validate required columns.

    Returns a pandas DataFrame when pandas is available; otherwise returns a
    list of normalized dictionaries from the CSV file.
    """
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return _load_with_stdlib(csv_path)

    data = pd.read_csv(csv_path)
    _validate_columns(data.columns)
    return data


def _load_with_stdlib(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _validate_columns(reader.fieldnames or [])
        return [dict(row) for row in reader]


def _validate_columns(columns: Any) -> None:
    present = set(columns)
    missing = [column for column in REQUIRED_COLUMNS if column not in present]
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {', '.join(missing)}")
