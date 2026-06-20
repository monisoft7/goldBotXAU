from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.backtest.engine import run_backtest_from_events
from src.backtest.metrics import calculate_metrics
from src.data.xauusd_csv_loader import load_xauusd_m15_csvs

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: str) -> None:
    path.write_text(rows, encoding="utf-8")


def test_loader_normalizes_sorts_and_validates_local_csv(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_fixture.csv",
        "\n".join(
            [
                "datetime,open,high,low,close,tick_volume",
                "2026-01-01 00:15,2001,2005,1999,2003,12",
                "2026-01-01 00:00,2000,2002,1998,2001,10",
            ]
        ),
    )

    result = load_xauusd_m15_csvs(data_dir)

    assert len(result.files) == 1
    assert [row["timestamp"] for row in result.records] == [
        "2026-01-01T00:00:00",
        "2026-01-01T00:15:00",
    ]
    assert result.records[0]["volume"] == 10.0


def test_loader_rejects_invalid_candle_and_duplicate_timestamp(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_bad_candle.csv",
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-01-01 00:00,2000,1999,1998,2001,1",
            ]
        ),
    )
    with pytest.raises(ValueError, match="high"):
        load_xauusd_m15_csvs(data_dir)

    (data_dir / "xauusd_m15_bad_candle.csv").unlink()
    _write_csv(
        data_dir / "xauusd_m15_duplicate.csv",
        "\n".join(
            [
                "timestamp,open,high,low,close",
                "2026-01-01 00:00,2000,2002,1998,2001",
                "2026-01-01T00:00:00,2001,2003,1999,2002",
            ]
        ),
    )
    with pytest.raises(ValueError, match="Duplicate timestamp"):
        load_xauusd_m15_csvs(data_dir)


def test_metrics_known_synthetic_trade_outcomes() -> None:
    metrics = calculate_metrics([1.0, -0.5, -1.0, 2.0], out_of_sample_result="fixture_pass").to_dict()

    assert metrics["trade_count"] == 4
    assert metrics["wins"] == 2
    assert metrics["losses"] == 2
    assert metrics["win_rate"] == 0.5
    assert metrics["gross_profit"] == 3.0
    assert metrics["gross_loss"] == 1.5
    assert metrics["profit_factor"] == 2.0
    assert metrics["expectancy"] == 0.375
    assert metrics["equity_curve"] == [0.0, 1.0, 0.5, -0.5, 1.5]
    assert metrics["max_drawdown"] == 1.5
    assert metrics["max_consecutive_losses"] == 2
    assert metrics["out_of_sample_result"] == "fixture_pass"


def test_zero_trade_metrics_do_not_crash() -> None:
    metrics = calculate_metrics([]).to_dict()

    assert metrics["trade_count"] == 0
    assert metrics["win_rate"] == 0.0
    assert metrics["profit_factor"] == 0.0
    assert metrics["expectancy"] == 0.0
    assert metrics["equity_curve"] == [0.0]
    assert metrics["max_drawdown"] == 0.0
    assert metrics["max_consecutive_losses"] == 0


def test_engine_uses_only_explicit_synthetic_events() -> None:
    report = run_backtest_from_events(
        candles=[{"timestamp": "2026-01-01T00:00:00"}],
        signal_events=[{"outcome_r": 1.0}, {"outcome_r": -0.25}],
        fixed_risk_unit_r=2.0,
        file_count=1,
        out_of_sample_result="fixture_only",
    ).to_dict()

    assert report["lab_version"] == "v0_2"
    assert report["required_metrics_present"] is True
    assert report["metrics"]["expectancy"] == 0.75
    assert report["safety"] == {
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
    }


def test_cli_report_includes_safety_and_required_metrics(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_fixture.csv",
        "\n".join(
            [
                "date,open,high,low,close,volume",
                "2026-01-01 00:00,2000,2002,1998,2001,10",
            ]
        ),
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_backtest_lab.py"),
            "--data-dir",
            str(data_dir),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["lab_version"] == "v0_2"
    assert report["status"] == "local_data_loaded"
    assert report["candle_count"] == 1
    assert report["file_count"] == 1
    assert report["required_metrics_present"] is True
    assert report["safety"]["demo_enabled"] is False
    assert report["safety"]["live_enabled"] is False
    assert report["safety"]["order_send_allowed"] is False


def test_cli_no_local_data_exits_cleanly(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_backtest_lab.py"),
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

    assert report["status"] == "no_local_data_found"
    assert report["candle_count"] == 0
    assert report["file_count"] == 0


def test_no_demo_live_order_send_permission_exposed() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [*ROOT.joinpath("src").rglob("*.py"), ROOT / "scripts" / "run_xauusd_backtest_lab.py"]
    ).lower()

    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "order" + "_send(" not in source_text
