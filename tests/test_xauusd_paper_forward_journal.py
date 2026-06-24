from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.xauusd_paper_forward_journal import run_paper_forward_watcher_loop_v0_88

ROOT = Path(__file__).resolve().parents[1]


def _watch_report(record_count: int = 2) -> dict[str, object]:
    return {
        "watch_version": "v0_87",
        "watch_status": "watch_completed" if record_count else "watch_completed_no_records",
        "data_source_status": "local_readonly_market_csv",
        "real_market_observation_started": bool(record_count),
        "watch_records": [
            {
                "timestamp": f"2026-01-02T01:{idx:02d}:00",
                "symbol": "XAUUSD",
                "timeframe": "M5",
                "setup_label": "local_market_csv_candle_observation",
                "direction_assigned": None,
                "reason": "local_readonly_market_csv_row_observed",
                "invalidation_note": None,
                "status": "paper_observation_recorded",
                "source": "local_readonly_market_csv:test.csv",
                "paper_observation_only": True,
            }
            for idx in range(record_count)
        ],
        "blockers": [],
    }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_loop_calls_watcher_for_requested_cycle_count_and_writes_valid_jsonl(tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def fake_builder(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return _watch_report(record_count=2)

    journal_path = tmp_path / "reports" / "xauusd_paper_forward_journal_v0_88.jsonl"
    report = run_paper_forward_watcher_loop_v0_88(
        cycles=3,
        interval_seconds=0,
        max_records_per_cycle=2,
        journal_path=journal_path,
        watcher_builder=fake_builder,
    )

    records = _read_jsonl(journal_path)
    assert len(calls) == 3
    assert [call["max_records"] for call in calls] == [2, 2, 2]
    assert report["loop_version"] == "v0_88"
    assert report["loop_status"] == "loop_completed"
    assert report["cycle_count"] == 3
    assert report["observation_count"] == 6
    assert report["journal_record_count"] == 6
    assert str(journal_path) == report["journal_path"]
    assert len(records) == 6
    assert {record["cycle_index"] for record in records} == {0, 1, 2}
    for record in records:
        assert record["journal_version"] == "v0_88"
        assert record["source_watch_version"] == "v0_87"
        assert record["paper_observation_only"] is True
        assert record["trade_recommendation_output"] is False
        assert record["order_send_called"] is False
        assert record["order_check_called"] is False
        assert record["direction_assigned"] is None


def test_repeated_runs_append_safely(tmp_path: Path) -> None:
    journal_path = tmp_path / "reports" / "xauusd_paper_forward_journal_v0_88.jsonl"

    run_paper_forward_watcher_loop_v0_88(
        cycles=1,
        interval_seconds=0,
        max_records_per_cycle=1,
        journal_path=journal_path,
        watcher_builder=lambda **_: _watch_report(record_count=1),
    )
    second = run_paper_forward_watcher_loop_v0_88(
        cycles=2,
        interval_seconds=0,
        max_records_per_cycle=1,
        journal_path=journal_path,
        watcher_builder=lambda **_: _watch_report(record_count=1),
    )

    records = _read_jsonl(journal_path)
    assert len(records) == 3
    assert second["journal_record_count"] == 3
    for line in journal_path.read_text(encoding="utf-8").splitlines():
        assert isinstance(json.loads(line), dict)


def test_no_observation_cycle_writes_safe_summary_record(tmp_path: Path) -> None:
    journal_path = tmp_path / "reports" / "xauusd_paper_forward_journal_v0_88.jsonl"

    report = run_paper_forward_watcher_loop_v0_88(
        cycles=1,
        interval_seconds=0,
        max_records_per_cycle=0,
        journal_path=journal_path,
        watcher_builder=lambda **_: _watch_report(record_count=0),
    )

    records = _read_jsonl(journal_path)
    assert report["loop_status"] == "loop_completed_no_observations"
    assert report["observation_count"] == 0
    assert records[0]["status"] == "no_observation"
    assert records[0]["paper_observation_only"] is True
    assert records[0]["trade_recommendation_output"] is False


def test_loop_safety_flags_disable_execution_demo_live_and_recommendations(tmp_path: Path) -> None:
    journal_path = tmp_path / "reports" / "xauusd_paper_forward_journal_v0_88.jsonl"

    report = run_paper_forward_watcher_loop_v0_88(
        cycles=1,
        interval_seconds=0,
        max_records_per_cycle=1,
        journal_path=journal_path,
        watcher_builder=lambda **_: _watch_report(record_count=1),
    )

    assert report["paper_observation_only"] is True
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["order_send_allowed"] is False
    assert report["order_check_allowed"] is False
    assert report["trade_recommendation_output"] is False
    assert report["user_facing_buy_sell_signal_output"] is False
    assert report["recommended_next_step"] == "v0_89_paper_forward_outcome_tracker"


def test_loop_rejects_journal_path_under_data(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="journal_path_must_not_be_under_data"):
        run_paper_forward_watcher_loop_v0_88(
            cycles=1,
            interval_seconds=0,
            journal_path=ROOT / "data" / "xauusd_paper_forward_journal_v0_88.jsonl",
            watcher_builder=lambda **_: _watch_report(record_count=1),
        )


def test_real_watcher_loop_does_not_touch_data_csv(tmp_path: Path) -> None:
    market_dir = tmp_path / "data"
    market_dir.mkdir()
    csv_path = market_dir / "xauusd_m5_xauusd_2026-01-01_2026-01-02.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-02T01:00:00,4300,4301,4299,4300.5,100\n"
        "2026-01-02T01:05:00,4301,4302,4300,4301.5,101\n",
        encoding="utf-8",
    )
    before_stat = csv_path.stat()

    report = run_paper_forward_watcher_loop_v0_88(
        cycles=2,
        interval_seconds=0,
        max_records_per_cycle=1,
        journal_path=tmp_path / "reports" / "xauusd_paper_forward_journal_v0_88.jsonl",
        market_csv_dir=market_dir,
    )

    after_stat = csv_path.stat()
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns
    assert after_stat.st_size == before_stat.st_size
    assert report["data_csv_touched"] is False
    assert report["market_csv_created"] is False


def test_v0_88_cli_json_supports_loop_options(tmp_path: Path) -> None:
    journal_path = tmp_path / "reports" / "xauusd_paper_forward_journal_v0_88.jsonl"
    output_path = tmp_path / "reports" / "xauusd_paper_forward_watcher_loop_v0_88.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_paper_forward_watcher_loop_v0_88.py"),
            "--json",
            "--cycles",
            "1",
            "--interval-seconds",
            "0",
            "--max-records-per-cycle",
            "1",
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
    assert report["loop_version"] == "v0_88"
    assert report["cycle_count"] == 1
    assert report["paper_observation_only"] is True
    assert journal_path.exists()
    assert output_path.exists()
