from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_paper_direction_annotator import (
    annotate_paper_direction,
    build_xauusd_paper_directional_watcher_v0_90,
)

ROOT = Path(__file__).resolve().parents[1]


def _row(open_price: float, high: float, low: float, close: float) -> dict[str, float]:
    return {"open": open_price, "high": high, "low": low, "close": close}


def _previous_rows(count: int = 12) -> list[dict[str, float]]:
    return [_row(100.0, 101.0, 99.0, 100.0) for _ in range(count)]


def _write_market_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "timestamp,symbol,timeframe,open,high,low,close,volume",
        *[
            f"2026-01-02T00:{idx:02d}:00,XAUUSD,M5,100.0,101.0,99.0,100.0,10"
            for idx in range(12)
        ],
        "2026-01-02T00:12:00,XAUUSD,M5,100.0,104.0,100.0,103.0,11",
        "2026-01-02T00:13:00,XAUUSD,M5,103.0,103.2,98.0,98.5,12",
    ]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_annotator_returns_paper_long_for_bullish_breakout_fixture() -> None:
    annotation = annotate_paper_direction(_row(100.0, 104.0, 100.0, 103.0), _previous_rows(), lookback_bars=12)

    assert annotation["paper_observation_direction"] == "paper_long"
    assert annotation["direction_assigned"] == "paper_long"
    assert annotation["setup_label"] == "bullish_displacement_observation"


def test_annotator_returns_paper_short_for_bearish_breakout_fixture() -> None:
    annotation = annotate_paper_direction(_row(100.0, 100.5, 96.0, 97.0), _previous_rows(), lookback_bars=12)

    assert annotation["paper_observation_direction"] == "paper_short"
    assert annotation["direction_assigned"] == "paper_short"
    assert annotation["setup_label"] == "bearish_displacement_observation"


def test_annotator_returns_null_for_insufficient_or_no_structure() -> None:
    insufficient = annotate_paper_direction(_row(100.0, 104.0, 100.0, 103.0), _previous_rows(3), lookback_bars=12)
    neutral = annotate_paper_direction(_row(100.0, 100.5, 99.5, 100.2), _previous_rows(), lookback_bars=12)

    assert insufficient["paper_observation_direction"] is None
    assert insufficient["setup_label"] == "insufficient_structure"
    assert neutral["paper_observation_direction"] is None
    assert neutral["setup_label"] == "insufficient_structure"


def test_directional_watcher_reads_csv_read_only_and_writes_valid_jsonl(tmp_path: Path) -> None:
    csv_path = tmp_path / "data" / "xauusd_m5_fixture.csv"
    journal_path = tmp_path / "reports" / "directional.jsonl"
    _write_market_csv(csv_path)
    before = csv_path.stat()

    report = build_xauusd_paper_directional_watcher_v0_90(
        market_csv_dir=csv_path.parent,
        max_records=20,
        from_date="2026-01-01",
        timeframes=["M5"],
        lookback_bars=12,
        journal_path=journal_path,
    )

    after = csv_path.stat()
    assert after.st_mtime_ns == before.st_mtime_ns
    assert after.st_size == before.st_size
    assert report["watch_version"] == "v0_90"
    assert report["watch_status"] == "directional_watch_completed"
    assert report["directional_observation_count"] == 2
    assert report["data_csv_touched"] is False
    assert report["market_csv_created"] is False
    journal_records = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(journal_records) == 2
    assert {record["paper_observation_direction"] for record in journal_records} == {"paper_long", "paper_short"}
    for record in journal_records:
        assert record["journal_version"] == "v0_90"
        assert record["paper_observation_only"] is True
        assert record["trade_recommendation_output"] is False
        assert record["user_facing_buy_sell_signal_output"] is False
        assert record["order_send_called"] is False
        assert record["order_check_called"] is False


def test_directional_watcher_safety_flags_disable_execution_and_search(tmp_path: Path) -> None:
    csv_path = tmp_path / "data" / "xauusd_m5_fixture.csv"
    _write_market_csv(csv_path)

    report = build_xauusd_paper_directional_watcher_v0_90(
        market_csv_dir=csv_path.parent,
        max_records=20,
        timeframes=["M5"],
        journal_path=tmp_path / "reports" / "directional.jsonl",
    )

    assert report["paper_observation_only"] is True
    assert report["direction_annotation_method"] == "fixed_ohlc_structure_no_optimization"
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["optimization_performed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["trade_recommendation_output"] is False
    assert report["user_facing_buy_sell_signal_output"] is False
    assert report["recommended_next_step"] == "v0_91_directional_outcome_tracker"


def test_directional_watcher_is_safe_when_no_directional_observations(tmp_path: Path) -> None:
    csv_path = tmp_path / "data" / "xauusd_m5_fixture.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text(
        "timestamp,symbol,timeframe,open,high,low,close,volume\n"
        + "\n".join(
            f"2026-01-02T00:{idx:02d}:00,XAUUSD,M5,100.0,101.0,99.0,100.0,10"
            for idx in range(15)
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_xauusd_paper_directional_watcher_v0_90(
        market_csv_dir=csv_path.parent,
        max_records=15,
        timeframes=["M5"],
        journal_path=tmp_path / "reports" / "directional.jsonl",
    )

    assert report["watch_status"] == "directional_watch_completed_no_directional_records"
    assert report["directional_observation_count"] == 0
    assert report["null_direction_observation_count"] == 15
    assert report["journal_record_count"] == 0


def test_v0_90_cli_json_supports_required_options(tmp_path: Path) -> None:
    csv_path = tmp_path / "data" / "xauusd_m5_fixture.csv"
    output_path = tmp_path / "reports" / "directional_report.json"
    journal_path = tmp_path / "reports" / "directional.jsonl"
    _write_market_csv(csv_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_paper_directional_watcher_v0_90.py"),
            "--json",
            "--max-records",
            "20",
            "--from-date",
            "2026-01-01",
            "--timeframes",
            "M5",
            "--lookback-bars",
            "12",
            "--market-csv-dir",
            str(csv_path.parent),
            "--journal-path",
            str(journal_path),
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
    assert report["watch_version"] == "v0_90"
    assert report["lookback_bars"] == 12
    assert journal_path.exists()
    assert output_path.exists()
