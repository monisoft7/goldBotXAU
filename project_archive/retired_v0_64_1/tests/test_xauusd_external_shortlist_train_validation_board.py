from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from src.research.xauusd_external_shortlist_train_validation_board import (
    BLOCKED_MISSING_DATA,
    BOARD_VERSION,
    NONE_PASSED,
    PASSED,
    SHORTLIST,
    build_xauusd_external_shortlist_train_validation_board_v0_53,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "manifest_version": "v0_5",
                "split_policy": {
                    "method": "fixed_chronological_split",
                    "train_end": "2025-06-30T23:59:59",
                    "validation_start": "2025-07-01T00:00:00",
                    "validation_end": "2025-12-31T23:59:59",
                    "oos_start": "2026-01-01T00:00:00",
                    "leakage_prevention": "chronological_only_no_shuffle",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_rows(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _day_rows(day: date, *, base: float, favorable: bool) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for hour, minute, open_price, high, low, close in (
        (0, 0, base, base + 10.0, base - 10.0, base),
        (6, 45, base, base + 9.0, base - 9.0, base),
        (7, 0, base, base + 1.0, base - 1.0, base + 0.6),
        (
            7,
            15,
            base + 0.6,
            base + 3.1 if favorable else base + 0.8,
            base + 0.5 if favorable else base - 1.1,
            base + 3.0 if favorable else base - 0.9,
        ),
        (11, 45, base + 3.0 if favorable else base - 0.9, base + 3.2, base - 1.2, base + 2.5),
        (19, 45, base + 2.5, base + 2.8, base + 2.2, base + 2.4),
    ):
        rows.append(
            {
                "timestamp": datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute).isoformat(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": 1.0,
            }
        )
    return rows


def _fixture(tmp_path: Path, *, favorable: bool, validation_days: int = 60) -> tuple[Path, Path]:
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    _write_manifest(manifest)
    rows: list[dict[str, float | str]] = []
    sequence = 0
    for index in range(60):
        rows.extend(_day_rows(date(2025, 4, 1) + timedelta(days=index), base=2000.0 + sequence * 0.01, favorable=favorable))
        sequence += 1
    for index in range(validation_days):
        rows.extend(_day_rows(date(2025, 7, 1) + timedelta(days=index), base=2100.0 + sequence * 0.01, favorable=favorable))
        sequence += 1
    for index in range(5):
        rows.extend(_day_rows(date(2026, 1, 2) + timedelta(days=index), base=2200.0 + sequence * 0.01, favorable=True))
        sequence += 1
    _write_rows(data_dir / "xauusd_m15_fixture.csv", rows)
    return manifest, data_dir


def _build(tmp_path: Path, *, favorable: bool, validation_days: int = 60) -> dict[str, object]:
    manifest, data_dir = _fixture(tmp_path, favorable=favorable, validation_days=validation_days)
    return build_xauusd_external_shortlist_train_validation_board_v0_53(
        data_dir=data_dir,
        manifest_path=manifest,
    )


def test_all_three_shortlisted_candidate_ids_are_present(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)

    assert report["board_version"] == BOARD_VERSION
    assert report["source_triage_versions"] == ["v0_52", "v0_52_1"]
    assert report["tested_candidate_ids"] == list(SHORTLIST)
    assert [result["candidate_id"] for result in report["candidate_results"]] == list(SHORTLIST)


def test_fixed_rules_are_implemented_for_all_three_candidates(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)
    rules = {result["candidate_id"]: result["fixed_rules"] for result in report["candidate_results"]}

    assert rules["prior_day_liquidity_sweep_reversal"]["reference"] == "previous_completed_trading_day_high_low"
    assert rules["prior_day_liquidity_sweep_reversal"]["session_filter_utc"] == "07:00-20:00"
    assert rules["london_opening_range_breakout_or_first_candle_direction"]["target"] == "1.5R"
    assert rules["london_opening_range_breakout_or_first_candle_direction"]["invalidation"] == "skip_zero_or_invalid_stop_distance"
    assert rules["asian_range_london_breakout_confirmation"]["asian_range_utc"] == "00:00-06:59"
    assert rules["asian_range_london_breakout_confirmation"]["stop"] == "asian_midpoint"
    assert all(result["fixed_before_evaluation"] is True for result in report["candidate_results"])


def test_train_validation_only_oos_not_used_and_no_retune_or_search(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["split_candle_counts"]["excluded_oos"] > 0
    assert "excluded_oos_candle_count:" in " ".join(report["warnings"])


def test_no_executable_candidate_creation_or_execution_surface(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)

    assert report["candidate_created"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["safety"]["execution_queue_created"] is False
    assert report["safety"]["scheduler_created"] is False
    assert report["safety"]["auto_execute_order"] is False


def test_data_csv_not_staged_or_committed(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)
    completed = subprocess.run(
        ["git", "status", "--short", "--", "data/*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert report["data_csv_added_to_git"] is False
    assert completed.stdout.strip() == ""


def test_passing_fixture_selects_best_candidate(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)

    assert report["board_status"] == PASSED
    assert report["best_candidate_id"] == "london_opening_range_breakout_or_first_candle_direction"
    assert report["best_candidate_passed_gate"] is True
    assert report["best_candidate_metrics"]["validation"]["trades"] >= 50
    assert report["best_candidate_metrics"]["validation"]["profit_factor"] == "inf"
    assert report["best_candidate_metrics"]["validation"]["expectancy_r"] > 0
    assert report["next_recommended_step"] == "lock fixed candidate artifact and prepare one-time OOS protocol"


def test_failing_fixture_rejects_all_as_do_not_retune(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=False)

    assert report["board_status"] == NONE_PASSED
    assert report["best_candidate_passed_gate"] is False
    assert report["rejected_do_not_retune_candidates"] == list(SHORTLIST)
    assert all(result["passed_gate"] is False for result in report["candidate_results"])
    assert all(result["do_not_retune"] is True for result in report["candidate_results"])
    assert report["next_recommended_step"] == "broaden non-OOS research or stop current branch"


def test_missing_data_blocks_cleanly(tmp_path: Path) -> None:
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    _write_manifest(manifest)

    report = build_xauusd_external_shortlist_train_validation_board_v0_53(
        data_dir=data_dir,
        manifest_path=manifest,
    )

    assert report["board_status"] == BLOCKED_MISSING_DATA
    assert "m15_data_files_missing" in report["blockers"]
    assert report["oos_used"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False


def test_cli_writes_required_report(tmp_path: Path) -> None:
    manifest, data_dir = _fixture(tmp_path, favorable=True)
    output = tmp_path / "reports" / "board.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_external_shortlist_board_v0_53.py"),
            "--json",
            "--output",
            str(output),
            "--data-dir",
            str(data_dir),
            "--manifest",
            str(manifest),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["board_version"] == BOARD_VERSION
    assert output_report["board_status"] == PASSED
    assert output_report["train_validation_only"] is True
    assert output_report["oos_used"] is False
