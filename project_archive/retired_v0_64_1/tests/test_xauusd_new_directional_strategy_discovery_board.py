from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from src.research.xauusd_new_directional_strategy_discovery_board import (
    BOARD_VERSION,
    NO_CANDIDATE_PASSED,
    ONE_CANDIDATE_PASSED,
    PRIOR_PATH_CLOSED,
    PRIOR_PATH_CLOSURE_REASON,
    build_xauusd_new_directional_strategy_discovery_board_v0_48,
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


def _day_rows(day: date, *, base: float, favorable: bool = True) -> list[dict[str, float | str]]:
    evaluation_close = base + 4.0 if favorable else base - 1.0
    evaluation_low = min(base + 1.8, evaluation_close - 0.2)
    specs = [
        (0, base, base + 0.5, base - 0.5, base + 0.1),
        (6, base + 0.1, base + 2.2, base, base + 2.0),
        (12, base + 2.0, base + 4.2, evaluation_low, evaluation_close),
        (18, evaluation_close, evaluation_close + 0.3, evaluation_close - 0.3, evaluation_close + 0.1),
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


def _fixture(tmp_path: Path, *, train_days: int, validation_days: int, favorable: bool = True) -> tuple[Path, Path]:
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    _write_manifest(manifest)

    rows: list[dict[str, float | str]] = []
    for index in range(train_days):
        rows.extend(
            _day_rows(
                date.fromisoformat("2025-05-01") + timedelta(days=index),
                base=2000.0 + index,
                favorable=favorable,
            )
        )
    for index in range(validation_days):
        rows.extend(
            _day_rows(
                date.fromisoformat("2025-07-01") + timedelta(days=index),
                base=2100.0 + index,
                favorable=favorable,
            )
        )

    _write_rows(data_dir / "xauusd_m5_fixture.csv", rows)
    _write_rows(data_dir / "xauusd_m10_fixture.csv", rows)
    return manifest, data_dir


def test_v0_26_path_is_explicitly_closed_as_executable(tmp_path: Path) -> None:
    manifest, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=data_dir,
        manifest_path=manifest,
    )

    assert report["board_version"] == BOARD_VERSION
    assert report["prior_path_closed"] == PRIOR_PATH_CLOSED
    assert report["prior_path_closure_reason"] == PRIOR_PATH_CLOSURE_REASON
    assert report["prior_path_executable_status"] == "closed_as_execution_path"


def test_fixed_directional_families_are_present_and_named(tmp_path: Path) -> None:
    manifest, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=data_dir,
        manifest_path=manifest,
    )

    assert report["directional_families_evaluated"] == [
        "session_open_range_breakout_directional",
        "prior_block_breakout_continuation_directional",
        "failed_breakout_reversal_directional",
        "trend_pullback_continuation_directional",
    ]


def test_train_validation_only_and_oos_not_used(tmp_path: Path) -> None:
    manifest, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=data_dir,
        manifest_path=manifest,
    )

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False


def test_no_retune_threshold_search_parameter_grid_or_execution(tmp_path: Path) -> None:
    manifest, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=data_dir,
        manifest_path=manifest,
    )

    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["demo_execution_allowed"] is False
    assert report["safety"]["execution_queue_created"] is False
    assert report["safety"]["scheduler_created"] is False
    assert report["safety"]["auto_execute_order"] is False


def test_no_data_csv_additions(tmp_path: Path) -> None:
    before = sorted((ROOT / "data").glob("*.csv"))
    manifest, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)

    report = build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=data_dir,
        manifest_path=manifest,
    )

    assert sorted((ROOT / "data").glob("*.csv")) == before
    assert report["data_csv_added"] is False


def test_passing_fixture_selects_best_candidate(tmp_path: Path) -> None:
    manifest, data_dir = _fixture(tmp_path, train_days=30, validation_days=30, favorable=True)

    report = build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=data_dir,
        manifest_path=manifest,
    )

    assert report["board_status"] == ONE_CANDIDATE_PASSED
    assert report["best_candidate_id"] in {
        "session_open_range_breakout_directional",
        "prior_block_breakout_continuation_directional",
    }
    assert report["best_candidate_passed_gate"] is True
    assert report["best_candidate_metrics"]["validation"]["trades"] >= 25
    assert report["best_candidate_metrics"]["validation"]["expectancy_r"] > 0


def test_failing_fixture_blocks(tmp_path: Path) -> None:
    manifest, data_dir = _fixture(tmp_path, train_days=30, validation_days=30, favorable=False)

    report = build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=data_dir,
        manifest_path=manifest,
    )

    assert report["board_status"] == NO_CANDIDATE_PASSED
    assert report["best_candidate_passed_gate"] is False
    assert all(result["passed_gate"] is False for result in report["candidate_results"])
    assert all(result["do_not_retune"] is True for result in report["candidate_results"])


def test_missing_data_blocks(tmp_path: Path) -> None:
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    _write_manifest(manifest)

    report = build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=data_dir,
        manifest_path=manifest,
    )

    assert report["board_status"] == "blocked_missing_required_data"
    assert "train_validation_m5_m10_rows_missing" in report["blockers"]


def test_cli_writes_required_report(tmp_path: Path) -> None:
    manifest, data_dir = _fixture(tmp_path, train_days=30, validation_days=30)
    output_path = tmp_path / "reports" / "board.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_new_directional_discovery_v0_48.py"),
            "--json",
            "--output",
            str(output_path),
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
    output_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["board_version"] == BOARD_VERSION
    assert output_report["prior_path_closed"] == PRIOR_PATH_CLOSED
