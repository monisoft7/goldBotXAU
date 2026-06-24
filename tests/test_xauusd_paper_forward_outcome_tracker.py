from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_paper_forward_outcome_tracker import (
    build_xauusd_paper_forward_outcome_tracker_v0_89,
    save_xauusd_paper_forward_outcome_tracker_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")


def _write_market_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "timestamp,symbol,timeframe,open,high,low,close,volume\n"
        "2026-01-02T00:00:00,XAUUSD,M5,100.0,100.4,99.8,100.0,10\n"
        "2026-01-02T00:05:00,XAUUSD,M5,100.0,102.5,99.7,101.8,11\n"
        "2026-01-02T00:10:00,XAUUSD,M5,101.8,102.0,101.0,101.2,12\n"
        "2026-01-02T01:00:00,XAUUSD,M5,200.0,200.2,199.8,200.0,20\n"
        "2026-01-02T01:05:00,XAUUSD,M5,200.0,200.2,197.5,198.0,21\n"
        "2026-01-02T01:10:00,XAUUSD,M5,198.0,198.5,197.8,198.3,22\n"
        "2026-01-02T02:00:00,XAUUSD,M5,300.0,300.2,299.8,300.0,30\n"
        "2026-01-02T02:05:00,XAUUSD,M5,300.0,300.7,299.5,300.3,31\n"
        "2026-01-02T02:10:00,XAUUSD,M5,300.3,300.8,299.6,300.1,32\n",
        encoding="utf-8",
    )


def _journal_record(timestamp: str, direction: str | None) -> dict[str, object]:
    return {
        "journal_version": "v0_88",
        "timestamp": timestamp,
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "setup_label": "local_market_csv_candle_observation",
        "direction_assigned": direction,
        "paper_observation_direction": direction,
        "status": "paper_observation_recorded",
        "paper_observation_only": True,
        "trade_recommendation_output": False,
        "order_send_called": False,
        "order_check_called": False,
    }


def test_tracker_reads_jsonl_and_local_csv_and_evaluates_outcomes(tmp_path: Path) -> None:
    journal_path = tmp_path / "reports" / "journal.jsonl"
    market_csv = tmp_path / "data" / "xauusd_m5_fixture.csv"
    _write_jsonl(
        journal_path,
        [
            _journal_record("2026-01-02T00:00:00", "up"),
            _journal_record("2026-01-02T01:00:00", "up"),
            _journal_record("2026-01-02T02:00:00", "up"),
        ],
    )
    _write_market_csv(market_csv)

    report = build_xauusd_paper_forward_outcome_tracker_v0_89(
        journal_path=journal_path,
        market_csv_dir=market_csv.parent,
        horizon_bars=2,
        max_records=10,
    )

    assert report["tracker_version"] == "v0_89"
    assert report["tracker_status"] == "outcome_tracker_completed"
    assert report["records_read"] == 3
    assert report["records_evaluated"] == 3
    assert report["records_blocked"] == 0
    assert [record["outcome_status"] for record in report["outcome_records"]] == [
        "favorable_move_observed",
        "adverse_move_observed",
        "neutral_or_insufficient_move",
    ]
    assert report["outcome_counts"]["favorable_move_observed"] == 1
    assert report["outcome_counts"]["adverse_move_observed"] == 1
    assert report["outcome_counts"]["neutral_or_insufficient_move"] == 1


def test_missing_direction_is_blocked_not_guessed(tmp_path: Path) -> None:
    journal_path = tmp_path / "reports" / "journal.jsonl"
    market_csv = tmp_path / "data" / "xauusd_m5_fixture.csv"
    _write_jsonl(journal_path, [_journal_record("2026-01-02T00:00:00", None)])
    _write_market_csv(market_csv)

    report = build_xauusd_paper_forward_outcome_tracker_v0_89(
        journal_path=journal_path,
        market_csv_dir=market_csv.parent,
    )

    assert report["tracker_status"] == "outcome_tracker_completed_with_blocked_records"
    assert report["records_read"] == 1
    assert report["records_evaluated"] == 0
    assert report["records_blocked"] == 1
    assert report["outcome_records"][0]["outcome_status"] == "blocked_missing_direction"
    assert report["outcome_records"][0]["paper_observation_direction"] is None


def test_missing_future_rows_are_blocked(tmp_path: Path) -> None:
    journal_path = tmp_path / "reports" / "journal.jsonl"
    market_csv = tmp_path / "data" / "xauusd_m5_fixture.csv"
    _write_jsonl(journal_path, [_journal_record("2026-01-02T02:10:00", "up")])
    _write_market_csv(market_csv)

    report = build_xauusd_paper_forward_outcome_tracker_v0_89(
        journal_path=journal_path,
        market_csv_dir=market_csv.parent,
        horizon_bars=2,
    )

    assert report["tracker_status"] == "outcome_tracker_completed_with_blocked_records"
    assert report["outcome_records"][0]["outcome_status"] == "blocked_missing_future_rows"


def test_tracker_reads_csv_read_only_and_does_not_touch_data_csv(tmp_path: Path) -> None:
    journal_path = tmp_path / "reports" / "journal.jsonl"
    market_csv = tmp_path / "data" / "xauusd_m5_fixture.csv"
    _write_jsonl(journal_path, [_journal_record("2026-01-02T00:00:00", "up")])
    _write_market_csv(market_csv)
    before = market_csv.stat()

    report = build_xauusd_paper_forward_outcome_tracker_v0_89(
        journal_path=journal_path,
        market_csv_dir=market_csv.parent,
    )

    after = market_csv.stat()
    assert after.st_mtime_ns == before.st_mtime_ns
    assert after.st_size == before.st_size
    assert report["data_csv_touched"] is False
    assert report["market_csv_created"] is False


def test_tracker_safety_flags_and_no_search_paths() -> None:
    report = build_xauusd_paper_forward_outcome_tracker_v0_89(
        journal_path=ROOT / "reports" / "xauusd_paper_forward_journal_v0_88.jsonl",
        market_csv_dir=ROOT / "data",
        max_records=1,
    )
    text = json.dumps(report, sort_keys=True)

    assert report["paper_observation_only"] is True
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["trade_recommendation_output"] is False
    assert report["user_facing_buy_sell_signal_output"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert "order_send_allowed" not in text
    assert "order_check_allowed" not in text
    assert "trade recommendation" not in text.lower()


def test_report_save_and_cli_json(tmp_path: Path) -> None:
    journal_path = tmp_path / "reports" / "journal.jsonl"
    market_csv = tmp_path / "data" / "xauusd_m5_fixture.csv"
    output_path = tmp_path / "reports" / "tracker.json"
    _write_jsonl(journal_path, [_journal_record("2026-01-02T00:00:00", "up")])
    _write_market_csv(market_csv)

    report = build_xauusd_paper_forward_outcome_tracker_v0_89(
        journal_path=journal_path,
        market_csv_dir=market_csv.parent,
    )
    save_xauusd_paper_forward_outcome_tracker_report(report, output_path)
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["tracker_version"] == "v0_89"
    assert saved["outcome_counts"]["favorable_move_observed"] == 1

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_paper_forward_outcome_tracker_v0_89.py"),
            "--json",
            "--journal-path",
            str(journal_path),
            "--market-csv-dir",
            str(market_csv.parent),
            "--horizon-bars",
            "2",
            "--max-records",
            "10",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    cli_report = json.loads(completed.stdout)
    assert cli_report["tracker_version"] == "v0_89"
    assert cli_report["horizon_bars"] == 2
    assert output_path.exists()
