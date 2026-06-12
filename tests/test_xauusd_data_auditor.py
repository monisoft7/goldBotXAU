from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.data.xauusd_data_auditor import audit_xauusd_data

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows), encoding="utf-8")


def test_no_files_returns_no_local_data_found(tmp_path: Path) -> None:
    report = audit_xauusd_data(tmp_path / "data").to_dict()

    assert report["status"] == "no_local_data_found"
    assert report["usable_for_backtest"] is False
    assert report["errors"] == []
    assert report["warnings"]


def test_valid_m15_synthetic_candles_are_ready(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_valid.csv",
        [
            "time,open,high,low,close,volume",
            "2026-01-01 00:00,2000,2002,1999,2001,10",
            "2026-01-01 00:15,2001,2004,2000,2003,11",
            "2026-01-01 00:30,2003,2005,2002,2004,12",
        ],
    )

    report = audit_xauusd_data(data_dir).to_dict()

    assert report["status"] == "data_ready"
    assert report["usable_for_backtest"] is True
    assert report["candle_count"] == 3
    assert report["detected_timeframe_minutes"] == 15


def test_duplicate_timestamps_are_invalid(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_duplicate.csv",
        [
            "timestamp,open,high,low,close",
            "2026-01-01 00:00,2000,2002,1999,2001",
            "2026-01-01T00:00:00,2001,2004,2000,2003",
        ],
    )

    report = audit_xauusd_data(data_dir).to_dict()

    assert report["status"] == "data_invalid"
    assert report["usable_for_backtest"] is False
    assert report["errors"]


def test_invalid_ohlc_is_invalid(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_invalid_ohlc.csv",
        [
            "time,open,high,low,close",
            "2026-01-01 00:00,2000,1999,1998,2001",
        ],
    )

    report = audit_xauusd_data(data_dir).to_dict()

    assert report["status"] == "data_invalid"
    assert report["usable_for_backtest"] is False
    assert report["errors"]


def test_non_positive_prices_are_invalid(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_non_positive.csv",
        [
            "datetime,open,high,low,close",
            "2026-01-01 00:00,0,2,-1,1",
        ],
    )

    report = audit_xauusd_data(data_dir).to_dict()

    assert report["status"] == "data_invalid"
    assert report["usable_for_backtest"] is False
    assert report["errors"]


def test_missing_non_weekend_bar_creates_warning(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_gap.csv",
        [
            "date,open,high,low,close",
            "2026-01-01 00:00,2000,2002,1999,2001",
            "2026-01-01 00:30,2001,2003,2000,2002",
        ],
    )

    report = audit_xauusd_data(data_dir).to_dict()

    assert report["status"] == "data_has_warnings"
    assert report["usable_for_backtest"] is True
    assert report["missing_bar_count"] == 1
    assert report["large_gap_count"] == 1


def test_weekend_gap_classified_and_not_fatal(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_weekend.csv",
        [
            "time,open,high,low,close",
            "2026-01-02 21:45,2000,2002,1999,2001",
            "2026-01-05 00:00,2001,2003,2000,2002",
        ],
    )

    report = audit_xauusd_data(data_dir).to_dict()

    assert report["status"] == "data_has_warnings"
    assert report["usable_for_backtest"] is True
    assert report["weekend_gap_count"] == 1
    assert report["missing_bar_count"] == 0


def test_cli_json_includes_safety_flags(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_xauusd_data.py"),
            "--data-dir",
            str(tmp_path / "empty"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["auditor_version"] == "v0_3"
    assert report["safety"] == {
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
    }


def test_no_demo_live_order_send_permission_exposed() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "data" / "xauusd_data_auditor.py",
            ROOT / "scripts" / "audit_xauusd_data.py",
        ]
    ).lower()

    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "order" + "_send(" not in source_text
