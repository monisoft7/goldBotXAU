from __future__ import annotations

import csv
import importlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.data.mt5_readonly_low_tf_exporter import export_xauusd_low_tf_csv

ROOT = Path(__file__).resolve().parents[1]


class FakeMt5:
    TIMEFRAME_M1 = 1
    TIMEFRAME_M5 = 5

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
        self.copied_timeframe: int | None = None
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
        self.copied_timeframe = timeframe
        return self.rates

    def last_error(self) -> tuple[int, str]:
        return (1, "fake init failure")


def _timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=UTC).timestamp())


def _rates(first_timestamp: str) -> list[dict[str, float]]:
    return [
        {
            "time": _timestamp(first_timestamp),
            "open": 2000.0,
            "high": 2002.0,
            "low": 1999.0,
            "close": 2001.0,
            "tick_volume": 10.0,
        }
    ]


def test_missing_metatrader5_package_returns_not_available(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = importlib.import_module

    def fake_import(name: str, package: str | None = None) -> object:
        if name == "MetaTrader5":
            raise ImportError(name)
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    report = export_xauusd_low_tf_csv(from_date="2026-01-01", to_date="2026-01-02").to_dict()

    assert report["status"] == "mt5_not_available"


def test_initialize_failure_returns_initialize_failed() -> None:
    report = export_xauusd_low_tf_csv(
        from_date="2026-01-01",
        to_date="2026-01-02",
        mt5_module=FakeMt5(initialize_result=False),
    ).to_dict()

    assert report["status"] == "mt5_initialize_failed"
    assert report["errors"]


def test_invalid_non_gold_symbol_is_rejected() -> None:
    report = export_xauusd_low_tf_csv(
        symbol="EURUSD",
        from_date="2026-01-01",
        to_date="2026-01-02",
        mt5_module=FakeMt5(),
    ).to_dict()

    assert report["status"] == "symbol_not_found"


def test_unsupported_timeframe_rejected() -> None:
    report = export_xauusd_low_tf_csv(
        timeframe="M15",
        from_date="2026-01-01",
        to_date="2026-01-02",
        mt5_module=FakeMt5(),
    ).to_dict()

    assert report["status"] == "export_failed"
    assert report["errors"]


def test_fake_m1_rates_export_to_normalized_csv(tmp_path: Path) -> None:
    mt5 = FakeMt5(rates=_rates("2026-01-01T00:00:00"))

    report = export_xauusd_low_tf_csv(
        timeframe="M1",
        from_date="2026-01-01",
        to_date="2026-01-02",
        data_dir=tmp_path,
        mt5_module=mt5,
    ).to_dict()

    assert report["status"] == "exported"
    assert report["timeframe"] == "M1"
    assert mt5.copied_timeframe == FakeMt5.TIMEFRAME_M1
    assert Path(str(report["output_file"])).name == "xauusd_m1_xauusd_2026-01-01_2026-01-02.csv"
    with Path(str(report["output_file"])).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0].keys()) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert rows[0]["timestamp"] == "2026-01-01T00:00:00"
    assert rows[0]["volume"] == "10.0"
    assert mt5.shutdown_called is True


def test_fake_m5_rates_export_to_normalized_csv(tmp_path: Path) -> None:
    mt5 = FakeMt5(rates=_rates("2026-01-01T00:05:00"))

    report = export_xauusd_low_tf_csv(
        timeframe="M5",
        from_date="2026-01-01",
        to_date="2026-01-02",
        data_dir=tmp_path,
        mt5_module=mt5,
    ).to_dict()

    assert report["status"] == "exported"
    assert report["timeframe"] == "M5"
    assert mt5.copied_timeframe == FakeMt5.TIMEFRAME_M5
    assert Path(str(report["output_file"])).name == "xauusd_m5_xauusd_2026-01-01_2026-01-02.csv"


def test_duplicate_timestamps_handled_and_reported(tmp_path: Path) -> None:
    duplicated_time = _timestamp("2026-01-01T00:00:00")
    report = export_xauusd_low_tf_csv(
        from_date="2026-01-01",
        to_date="2026-01-02",
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


def test_exporter_does_not_expose_trading_behavior() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "data" / "mt5_readonly_low_tf_exporter.py",
            ROOT / "scripts" / "export_mt5_xauusd_low_tf.py",
        ]
    )
    forbidden_terms = ["order" + "_send(", "order" + "_check(", "positions" + "_get("]

    assert all(term not in source_text for term in forbidden_terms)


def test_low_tf_cli_returns_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_mt5_xauusd_low_tf.py"),
            "--symbol",
            "XAUUSD",
            "--timeframe",
            "M1",
            "--from-date",
            "2026-01-01",
            "--to-date",
            "2026-01-02",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["exporter_version"] == "v0_21"
    assert report["timeframe"] == "M1"
    assert "safety" in report


def test_safety_flags_exist_and_no_direction_words_in_report_output() -> None:
    report = export_xauusd_low_tf_csv(
        from_date="2026-01-01",
        to_date="2026-01-02",
        mt5_module=FakeMt5(rates=[]),
    ).to_dict()
    report_output = json.dumps(report)

    assert report["safety"] == {
        "read_only": True,
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "execution_queue_enabled": False,
        "buy_sell_output_allowed": False,
    }
    assert "BUY" not in report_output
    assert "SELL" not in report_output
    assert "demo_enabled" in report["safety"]
    assert "live_enabled" in report["safety"]
    assert "execution_queue_enabled" in report["safety"]
