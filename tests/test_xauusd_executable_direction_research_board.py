from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from src.research.xauusd_executable_direction_research_board import (
    BOARD_VERSION,
    NO_CANDIDATE_PASSED,
    ONE_CANDIDATE_PASSED,
    SOURCE_FILTER_CANDIDATE_ID,
    build_xauusd_direction_research_board_v0_47,
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


def _write_source_filter_report(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "candidate_id": SOURCE_FILTER_CANDIDATE_ID,
                "status": "train_validation_research_candidate_only",
                "splits_used": ["train", "validation"],
                "oos_rows_used": 0,
                "fixed_rules": {
                    "threshold_search_used": False,
                    "parameter_grid_used": False,
                    "retuning_used": False,
                    "reference_blocks": ["block_00_06", "block_06_12", "block_12_18"],
                    "response_blocks": ["block_06_12", "block_12_18", "block_18_24"],
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


def _day_rows(day: date, *, base: float, next_block_up: bool = True) -> list[dict[str, float | str]]:
    next_close = base + 3.0 if next_block_up else base + 1.0
    specs = [
        (0, base, base + 0.05, base - 0.05, base + 0.02),
        (6, base + 0.02, base + 2.00, base - 0.10, base + 1.50),
        (12, base + 1.50, base + 3.20, base + 1.30, next_close),
        (18, next_close, next_close + 0.20, next_close - 0.20, next_close + 0.01),
    ]
    return [
        {
            "timestamp": datetime.combine(day, datetime.min.time()).replace(hour=hour).isoformat(),
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1.0,
        }
        for hour, open_price, high, low, close in specs
    ]


def _fixture(tmp_path: Path, *, train_days: int, validation_days: int, next_block_up: bool = True) -> tuple[Path, Path, Path]:
    manifest = tmp_path / "reports" / "manifest.json"
    source_filter = tmp_path / "reports" / "source_filter.json"
    data_dir = tmp_path / "data"
    _write_manifest(manifest)
    _write_source_filter_report(source_filter)

    rows: list[dict[str, float | str]] = []
    for index in range(train_days):
        rows.extend(_day_rows(date.fromisoformat("2025-05-01") + timedelta(days=index), base=2000.0 + index, next_block_up=next_block_up))
    for index in range(validation_days):
        rows.extend(_day_rows(date.fromisoformat("2025-07-01") + timedelta(days=index), base=2100.0 + index, next_block_up=next_block_up))

    _write_rows(data_dir / "xauusd_m5_fixture.csv", rows)
    _write_rows(data_dir / "xauusd_m10_fixture.csv", rows)
    return manifest, source_filter, data_dir


def test_fixed_hypotheses_are_present_and_named(tmp_path: Path) -> None:
    manifest, source_filter, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_direction_research_board_v0_47(
        data_dir=data_dir,
        manifest_path=manifest,
        source_filter_report_path=source_filter,
    )

    assert report["board_version"] == BOARD_VERSION
    assert report["direction_hypotheses_evaluated"] == [
        "expansion_continuation_close_direction",
        "first_breakout_m5_confirmed_by_m10",
        "response_block_body_direction",
        "expansion_fade_direction",
    ]


def test_v0_26_source_filter_is_preserved(tmp_path: Path) -> None:
    manifest, source_filter, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_direction_research_board_v0_47(
        data_dir=data_dir,
        manifest_path=manifest,
        source_filter_report_path=source_filter,
    )

    assert report["source_filter_candidate_id"] == SOURCE_FILTER_CANDIDATE_ID
    assert report["source_filter_preserved"] is True
    assert report["source_filter_rules_modified"] is False


def test_train_validation_only_and_oos_not_used(tmp_path: Path) -> None:
    manifest, source_filter, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_direction_research_board_v0_47(
        data_dir=data_dir,
        manifest_path=manifest,
        source_filter_report_path=source_filter,
    )

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False


def test_no_retune_threshold_search_parameter_grid_or_execution(tmp_path: Path) -> None:
    manifest, source_filter, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_direction_research_board_v0_47(
        data_dir=data_dir,
        manifest_path=manifest,
        source_filter_report_path=source_filter,
    )

    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["demo_execution_allowed"] is False


def test_no_data_csv_additions(tmp_path: Path) -> None:
    before = sorted((ROOT / "data").glob("*.csv"))
    manifest, source_filter, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_direction_research_board_v0_47(
        data_dir=data_dir,
        manifest_path=manifest,
        source_filter_report_path=source_filter,
    )

    assert sorted((ROOT / "data").glob("*.csv")) == before
    assert report["data_csv_added"] is False


def test_passing_fixture_selects_best_candidate(tmp_path: Path) -> None:
    manifest, source_filter, data_dir = _fixture(tmp_path, train_days=30, validation_days=30, next_block_up=True)

    report = build_xauusd_direction_research_board_v0_47(
        data_dir=data_dir,
        manifest_path=manifest,
        source_filter_report_path=source_filter,
    )

    assert report["board_status"] == ONE_CANDIDATE_PASSED
    assert report["best_candidate_id"] == "expansion_continuation_close_direction"
    assert report["best_candidate_passed_gate"] is True
    assert report["best_candidate_metrics"]["validation"]["trades"] == 60
    assert report["best_candidate_metrics"]["validation"]["expectancy_r"] > 0


def test_failing_fixture_blocks(tmp_path: Path) -> None:
    manifest, source_filter, data_dir = _fixture(tmp_path, train_days=10, validation_days=5, next_block_up=True)

    report = build_xauusd_direction_research_board_v0_47(
        data_dir=data_dir,
        manifest_path=manifest,
        source_filter_report_path=source_filter,
    )

    assert report["board_status"] == NO_CANDIDATE_PASSED
    assert report["best_candidate_passed_gate"] is False
    assert all(result["passed_gate"] is False for result in report["candidate_results"])


def test_cli_writes_required_report(tmp_path: Path) -> None:
    manifest, source_filter, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)
    output_path = tmp_path / "reports" / "board.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_direction_research_board_v0_47.py"),
            "--json",
            "--output",
            str(output_path),
            "--data-dir",
            str(data_dir),
            "--manifest",
            str(manifest),
            "--source-filter-report",
            str(source_filter),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["board_version"] == BOARD_VERSION
    assert output_report["source_filter_candidate_id"] == SOURCE_FILTER_CANDIDATE_ID
