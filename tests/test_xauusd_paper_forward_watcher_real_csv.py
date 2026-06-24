from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_paper_forward_watcher import build_xauusd_paper_forward_watcher_v0_87

ROOT = Path(__file__).resolve().parents[1]


def _write_market_csv(path: Path, *, timeframe_minutes: int = 5, rows: int = 12) -> None:
    lines = ["timestamp,open,high,low,close,volume"]
    for idx in range(rows):
        minute = idx * timeframe_minutes
        hour = 1 + minute // 60
        rem_minute = minute % 60
        lines.append(
            f"2026-01-02T{hour:02d}:{rem_minute:02d}:00,"
            f"{4300 + idx:.2f},{4301 + idx:.2f},{4299 + idx:.2f},{4300.50 + idx:.2f},{100 + idx}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_v0_87_local_csv_mode_reads_temp_fixture_without_modifying_it(tmp_path: Path) -> None:
    market_dir = tmp_path / "data"
    market_dir.mkdir()
    csv_path = market_dir / "xauusd_m5_xauusd_2026-01-01_2026-01-02.csv"
    _write_market_csv(csv_path, rows=12)
    before_stat = csv_path.stat()

    report = build_xauusd_paper_forward_watcher_v0_87(market_csv_dir=market_dir, max_records=10)

    after_stat = csv_path.stat()
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns
    assert after_stat.st_size == before_stat.st_size
    assert report["watch_version"] == "v0_87"
    assert report["watch_status"] == "watch_completed"
    assert report["run_mode"] == "real_read_only"
    assert report["data_source_status"] == "local_readonly_market_csv"
    assert report["real_market_observation_started"] is True
    assert report["paper_observation_only"] is True
    assert report["source_files_used"] == [str(csv_path)]
    assert report["timeframes_used"] == ["M5"]
    assert report["watch_record_count"] == 10
    assert len(report["watch_records"]) == 10


def test_v0_87_records_are_paper_observations_not_trade_recommendations(tmp_path: Path) -> None:
    market_dir = tmp_path / "data"
    market_dir.mkdir()
    _write_market_csv(market_dir / "xauusd_m5_xauusd_2026-01-01_2026-01-02.csv", rows=12)

    report = build_xauusd_paper_forward_watcher_v0_87(market_csv_dir=market_dir, max_records=10)

    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["order_send_allowed"] is False
    assert report["order_check_allowed"] is False
    assert report["trade_recommendation_output"] is False
    assert report["user_facing_buy_sell_signal_output"] is False
    assert report["data_csv_touched"] is False
    assert report["market_csv_created"] is False
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    for record in report["watch_records"]:
        assert record == {
            "timestamp": record["timestamp"],
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "setup_label": "local_market_csv_candle_observation",
            "direction_assigned": None,
            "paper_observation_direction": None,
            "reason": "local_readonly_market_csv_row_observed",
            "invalidation_note": None,
            "status": "paper_observation_recorded",
            "source": record["source"],
            "paper_observation_only": True,
        }


def test_v0_87_missing_csv_fails_safely(tmp_path: Path) -> None:
    report = build_xauusd_paper_forward_watcher_v0_87(market_csv_dir=tmp_path / "data")

    assert report["watch_status"] == "blocked_missing_local_market_csv"
    assert report["data_source_status"] == "local_readonly_market_csv"
    assert report["real_market_observation_started"] is False
    assert report["paper_observation_only"] is True
    assert report["source_files_used"] == []
    assert report["timeframes_used"] == []
    assert report["watch_record_count"] == 0
    assert report["watch_records"] == []
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["trade_recommendation_output"] is False


def test_v0_87_cli_json_supports_required_options(tmp_path: Path) -> None:
    market_dir = tmp_path / "data"
    market_dir.mkdir()
    _write_market_csv(market_dir / "xauusd_m5_xauusd_2026-01-01_2026-01-02.csv", rows=12)
    output_path = tmp_path / "xauusd_paper_forward_watcher_v0_87.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_paper_forward_watcher_v0_87.py"),
            "--json",
            "--market-csv-dir",
            str(market_dir),
            "--max-records",
            "10",
            "--from-date",
            "2026-01-01",
            "--to-date",
            "2026-01-03",
            "--timeframes",
            "M5,M10,M15",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    report = json.loads(completed.stdout)
    assert report["watch_version"] == "v0_87"
    assert report["watch_record_count"] == 10
    assert output_path.exists()
