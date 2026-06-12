from __future__ import annotations

import csv
import importlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.data.mt5_readonly_xauusd_exporter import export_xauusd_m15_csv

ROOT = Path(__file__).resolve().parents[1]


class FakeMt5:
    TIMEFRAME_M15 = 15

    def __init__(
        self,
        *,
        initialize_result: bool = True,
        symbol_info_result: object | None = object(),
        symbol_select_result: bool = True,
        rates: list[dict[str, float]] | None = None,
    ) -> None:
        self.initialize_result = initialize_result
        self.symbol_info_result = symbol_info_result
        self.symbol_select_result = symbol_select_result
        self.rates = rates
        self.shutdown_called = False

    def initialize(self) -> bool:
        return self.initialize_result

    def shutdown(self) -> None:
        self.shutdown_called = True

    def symbol_info(self, symbol: str) -> object | None:
        return self.symbol_info_result

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        return self.symbol_select_result

    def copy_rates_range(self, symbol: str, timeframe: int, start: datetime, end: datetime) -> list[dict[str, float]] | None:
        return self.rates

    def last_error(self) -> tuple[int, str]:
        return (1, "fake init failure")


def _timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=UTC).timestamp())


def test_missing_metatrader5_package_returns_not_available(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = importlib.import_module

    def fake_import(name: str, package: str | None = None) -> object:
        if name == "MetaTrader5":
            raise ImportError(name)
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    report = export_xauusd_m15_csv(from_date="2023-01-01", to_date="2023-01-02").to_dict()

    assert report["status"] == "mt5_not_available"


def test_initialize_failure_returns_initialize_failed() -> None:
    report = export_xauusd_m15_csv(
        from_date="2023-01-01",
        to_date="2023-01-02",
        mt5_module=FakeMt5(initialize_result=False),
    ).to_dict()

    assert report["status"] == "mt5_initialize_failed"
    assert report["errors"]


def test_invalid_non_gold_symbol_is_rejected() -> None:
    report = export_xauusd_m15_csv(
        symbol="EURUSD",
        from_date="2023-01-01",
        to_date="2023-01-02",
        mt5_module=FakeMt5(),
    ).to_dict()

    assert report["status"] == "symbol_not_found"
    assert report["errors"]


def test_symbol_not_found_returns_symbol_not_found() -> None:
    report = export_xauusd_m15_csv(
        symbol="XAUUSDm",
        from_date="2023-01-01",
        to_date="2023-01-02",
        mt5_module=FakeMt5(symbol_info_result=None),
    ).to_dict()

    assert report["status"] == "symbol_not_found"


def test_symbol_select_failure_returns_symbol_select_failed() -> None:
    report = export_xauusd_m15_csv(
        from_date="2023-01-01",
        to_date="2023-01-02",
        mt5_module=FakeMt5(symbol_select_result=False),
    ).to_dict()

    assert report["status"] == "symbol_select_failed"


def test_no_rates_returned_returns_no_rates_returned() -> None:
    report = export_xauusd_m15_csv(
        from_date="2023-01-01",
        to_date="2023-01-02",
        mt5_module=FakeMt5(rates=[]),
    ).to_dict()

    assert report["status"] == "no_rates_returned"


def test_valid_fake_rates_export_normalized_csv(tmp_path: Path) -> None:
    mt5 = FakeMt5(
        rates=[
            {
                "time": _timestamp("2023-01-01T00:15:00"),
                "open": 2001.0,
                "high": 2003.0,
                "low": 2000.0,
                "close": 2002.0,
                "tick_volume": 11.0,
            },
            {
                "time": _timestamp("2023-01-01T00:00:00"),
                "open": 2000.0,
                "high": 2002.0,
                "low": 1999.0,
                "close": 2001.0,
                "tick_volume": 10.0,
            },
        ],
    )

    report = export_xauusd_m15_csv(
        from_date="2023-01-01",
        to_date="2023-01-02",
        data_dir=tmp_path,
        mt5_module=mt5,
    ).to_dict()

    assert report["status"] == "exported"
    assert report["row_count"] == 2
    output_file = Path(str(report["output_file"]))
    with output_file.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert list(rows[0].keys()) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert [row["timestamp"] for row in rows] == ["2023-01-01T00:00:00", "2023-01-01T00:15:00"]
    assert rows[0]["volume"] == "10.0"
    assert mt5.shutdown_called is True


def test_duplicate_timestamps_are_dropped_and_reported(tmp_path: Path) -> None:
    duplicated_time = _timestamp("2023-01-01T00:00:00")
    report = export_xauusd_m15_csv(
        from_date="2023-01-01",
        to_date="2023-01-02",
        data_dir=tmp_path,
        mt5_module=FakeMt5(
            rates=[
                {"time": duplicated_time, "open": 1.0, "high": 2.0, "low": 1.0, "close": 1.5, "tick_volume": 1.0},
                {"time": duplicated_time, "open": 1.1, "high": 2.1, "low": 1.1, "close": 1.6, "tick_volume": 2.0},
            ],
        ),
    ).to_dict()

    assert report["status"] == "exported"
    assert report["row_count"] == 1
    assert report["duplicate_timestamp_count"] == 1
    assert report["warnings"]


def test_report_contains_safety_flags() -> None:
    report = export_xauusd_m15_csv(
        from_date="2023-01-01",
        to_date="2023-01-02",
        mt5_module=FakeMt5(rates=[]),
    ).to_dict()

    assert report["safety"] == {
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
        "read_only": True,
    }


def test_cli_json_handles_missing_package() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_mt5_xauusd_m15.py"),
            "--symbol",
            "XAUUSD",
            "--from-date",
            "2023-01-01",
            "--to-date",
            "2023-01-02",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["exporter_version"] == "v0_4"
    assert report["status"] in {"mt5_not_available", "mt5_initialize_failed", "symbol_not_found", "no_rates_returned", "exported"}
    assert report["safety"]["read_only"] is True


def test_source_does_not_call_trading_functions() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "data" / "mt5_readonly_xauusd_exporter.py",
            ROOT / "scripts" / "export_mt5_xauusd_m15.py",
        ]
    )
    forbidden_calls = ["order" + "_send(", "order" + "_check("]

    assert all(call not in source_text for call in forbidden_calls)
