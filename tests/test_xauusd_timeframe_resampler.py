from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.data.xauusd_timeframe_resampler import resample_xauusd_timeframe_csv

ROOT = Path(__file__).resolve().parents[1]


def _write_rows(path: Path, rows: list[dict[str, float | str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _m1_rows(start: str, count: int) -> list[dict[str, float | str]]:
    current = datetime.fromisoformat(start)
    rows: list[dict[str, float | str]] = []
    for index in range(count):
        rows.append(
            {
                "timestamp": (current + timedelta(minutes=index)).isoformat(),
                "open": 100.0 + index,
                "high": 101.0 + index,
                "low": 99.0 + index,
                "close": 100.5 + index,
                "volume": 1.0 + index,
            }
        )
    return rows


def _m5_rows() -> list[dict[str, float | str]]:
    return [
        {"timestamp": "2026-01-01T00:00:00", "open": 2000.0, "high": 2003.0, "low": 1999.0, "close": 2002.0, "volume": 5.0},
        {"timestamp": "2026-01-01T00:05:00", "open": 2002.0, "high": 2004.0, "low": 2001.0, "close": 2003.0, "volume": 7.0},
    ]


def _read_output(report: dict[str, object]) -> list[dict[str, str]]:
    with Path(str(report["output_file"])).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_resampler_converts_m1_to_m10_correctly(tmp_path: Path) -> None:
    input_file = tmp_path / "xauusd_m1_xauusd_2026-01-01_2026-01-01.csv"
    _write_rows(input_file, _m1_rows("2026-01-01T00:00:00", 10))

    report = resample_xauusd_timeframe_csv(input_file=input_file, data_dir=tmp_path).to_dict()

    assert report["status"] == "resampled"
    assert report["source_timeframe"] == "M1"
    assert report["target_timeframe"] == "M10"
    assert report["output_row_count"] == 1
    rows = _read_output(report)
    assert rows[0]["timestamp"] == "2026-01-01T00:00:00"
    assert rows[0]["open"] == "100.0"
    assert rows[0]["close"] == "109.5"


def test_resampler_converts_m5_to_m10_correctly(tmp_path: Path) -> None:
    input_file = tmp_path / "xauusd_m5_xauusd_2026-01-01_2026-01-01.csv"
    _write_rows(input_file, _m5_rows())

    report = resample_xauusd_timeframe_csv(input_file=input_file, data_dir=tmp_path).to_dict()

    assert report["status"] == "resampled"
    assert report["source_timeframe"] == "M5"
    rows = _read_output(report)
    assert rows[0]["open"] == "2000.0"
    assert rows[0]["close"] == "2003.0"


def test_resampler_drops_incomplete_bars(tmp_path: Path) -> None:
    input_file = tmp_path / "xauusd_m1_partial.csv"
    _write_rows(input_file, _m1_rows("2026-01-01T00:00:00", 11))

    report = resample_xauusd_timeframe_csv(input_file=input_file, data_dir=tmp_path).to_dict()

    assert report["status"] == "resampled"
    assert report["output_row_count"] == 1
    assert report["incomplete_bar_count"] == 1
    assert report["warnings"]


def test_resampler_preserves_ohlcv_rules(tmp_path: Path) -> None:
    input_file = tmp_path / "xauusd_m5_rules.csv"
    _write_rows(
        input_file,
        [
            {"timestamp": "2026-01-01T00:05:00", "open": 10.0, "high": 14.0, "low": 9.0, "close": 11.0, "volume": 3.0},
            {"timestamp": "2026-01-01T00:00:00", "open": 8.0, "high": 12.0, "low": 7.0, "close": 10.0, "volume": 2.0},
        ],
    )

    report = resample_xauusd_timeframe_csv(input_file=input_file, data_dir=tmp_path).to_dict()

    rows = _read_output(report)
    assert rows[0] == {
        "timestamp": "2026-01-01T00:00:00",
        "open": "8.0",
        "high": "14.0",
        "low": "7.0",
        "close": "11.0",
        "volume": "5.0",
    }


def test_resampler_reports_duplicates(tmp_path: Path) -> None:
    input_file = tmp_path / "xauusd_m5_duplicates.csv"
    rows = _m5_rows()
    rows.append({"timestamp": "2026-01-01T00:05:00", "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0})
    _write_rows(input_file, rows)

    report = resample_xauusd_timeframe_csv(input_file=input_file, data_dir=tmp_path).to_dict()

    assert report["status"] == "resampled"
    assert report["duplicate_timestamp_count"] == 1
    assert report["warnings"]


def test_resampler_no_complete_bars(tmp_path: Path) -> None:
    input_file = tmp_path / "xauusd_m5_incomplete.csv"
    _write_rows(input_file, [{"timestamp": "2026-01-01T00:05:00", "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}])

    report = resample_xauusd_timeframe_csv(input_file=input_file, data_dir=tmp_path).to_dict()

    assert report["status"] == "no_complete_bars"
    assert report["incomplete_bar_count"] == 1


def test_resampler_script_returns_json(tmp_path: Path) -> None:
    input_file = tmp_path / "xauusd_m1_script.csv"
    _write_rows(input_file, _m1_rows("2026-01-01T00:00:00", 10))

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "resample_xauusd_timeframe.py"),
            "--input",
            str(input_file),
            "--target-timeframe",
            "M10",
            "--data-dir",
            str(tmp_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["resampler_version"] == "v0_21"
    assert report["status"] == "resampled"


def test_resampler_safety_flags_exist_and_no_direction_words_in_report_output(tmp_path: Path) -> None:
    input_file = tmp_path / "xauusd_m1_safety.csv"
    _write_rows(input_file, _m1_rows("2026-01-01T00:00:00", 10))

    report = resample_xauusd_timeframe_csv(input_file=input_file, data_dir=tmp_path).to_dict()
    report_output = json.dumps(report)

    assert report["safety"] == {
        "local_only": True,
        "mt5_called": False,
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
        "execution_queue_enabled": False,
    }
    assert "BUY" not in report_output
    assert "SELL" not in report_output
