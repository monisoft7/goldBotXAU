from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from src.research import xauusd_new_directional_strategy_discovery_board as board_v0_48
from src.research.xauusd_trend_pullback_sample_stability_audit import (
    AUDIT_VERSION,
    CANDIDATE_ID,
    PROMISING_INSUFFICIENT_SAMPLE,
    UNSTABLE_REJECT,
    build_xauusd_trend_pullback_stability_audit_v0_49,
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


def _trend_day_rows(day: date, *, base: float, outcome_r: float) -> list[dict[str, float | str]]:
    reference_range = 1.3
    evaluation_open = base + 2.2
    evaluation_close = evaluation_open + outcome_r * reference_range
    specs = [
        (0, base, base + 2.2, base - 0.1, base + 2.0),
        (6, base + 2.0, base + 2.1, base + 0.8, base + 1.0),
        (12, base + 1.0, base + 2.4, base + 0.9, base + 2.2),
        (18, evaluation_open, max(evaluation_open, evaluation_close) + 0.1, min(evaluation_open, evaluation_close) - 0.1, evaluation_close),
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


def _fixture(
    tmp_path: Path,
    *,
    train_days: int,
    validation_days: int,
    outcome_r: float = 0.4,
) -> tuple[Path, Path, Path]:
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    source_board = tmp_path / "reports" / "source_board.json"
    _write_manifest(manifest)

    rows: list[dict[str, float | str]] = []
    for index in range(train_days):
        rows.extend(_trend_day_rows(date.fromisoformat("2025-05-01") + timedelta(days=index), base=2000.0 + index, outcome_r=outcome_r))
    for index in range(validation_days):
        rows.extend(_trend_day_rows(date.fromisoformat("2025-07-01") + timedelta(days=index), base=2100.0 + index, outcome_r=outcome_r))

    _write_rows(data_dir / "xauusd_m5_fixture.csv", rows)
    _write_rows(data_dir / "xauusd_m10_fixture.csv", rows)

    board = board_v0_48.build_xauusd_new_directional_strategy_discovery_board_v0_48(
        data_dir=data_dir,
        manifest_path=manifest,
    )
    trend = next(candidate for candidate in board["candidate_results"] if candidate["candidate_id"] == CANDIDATE_ID)
    source_board.write_text(
        json.dumps(
            {
                **board,
                "best_candidate_id": CANDIDATE_ID,
                "best_candidate_metrics": {
                    "train": trend["train_metrics"],
                    "validation": trend["validation_metrics"],
                },
                "best_candidate_passed_gate": trend["passed_gate"],
                "candidate_results": [trend],
            }
        ),
        encoding="utf-8",
    )
    return manifest, data_dir, source_board


def test_candidate_rules_are_preserved_and_train_validation_only(tmp_path: Path) -> None:
    manifest, data_dir, source_board = _fixture(tmp_path, train_days=30, validation_days=8)

    report = build_xauusd_trend_pullback_stability_audit_v0_49(
        data_dir=data_dir,
        manifest_path=manifest,
        source_board_path=source_board,
    )

    assert report["audit_version"] == AUDIT_VERSION
    assert report["candidate_id"] == CANDIDATE_ID
    assert report["candidate_rules_preserved"] is True
    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False


def test_validation_below_25_blocks_candidate_locking(tmp_path: Path) -> None:
    manifest, data_dir, source_board = _fixture(tmp_path, train_days=30, validation_days=8)

    report = build_xauusd_trend_pullback_stability_audit_v0_49(
        data_dir=data_dir,
        manifest_path=manifest,
        source_board_path=source_board,
    )

    assert report["validation_trade_count"] == 16
    assert report["validation_trade_minimum"] == 25
    assert report["validation_trade_count_passed"] is False
    assert report["candidate_locking_allowed_pre_oos"] is False
    assert report["stability_decision"] == PROMISING_INSUFFICIENT_SAMPLE
    assert "validation_trade_count_below_fixed_minimum_blocks_candidate_locking" in report["blockers"]


def test_concentrated_validation_sample_flags_risk(tmp_path: Path) -> None:
    manifest, data_dir, source_board = _fixture(tmp_path, train_days=30, validation_days=8)

    report = build_xauusd_trend_pullback_stability_audit_v0_49(
        data_dir=data_dir,
        manifest_path=manifest,
        source_board_path=source_board,
    )

    risk = report["sample_concentration_risk"]
    assert risk["risk_level"] == "high"
    assert "validation_trades_concentrated_in_single_month" in risk["reasons"]
    assert "validation_trades_concentrated_in_single_side" in risk["reasons"]
    assert "validation_trades_concentrated_in_single_session_or_block" in risk["reasons"]


def test_fixed_cost_sensitivity_can_reject_fixture(tmp_path: Path) -> None:
    manifest, data_dir, source_board = _fixture(tmp_path, train_days=30, validation_days=15, outcome_r=0.02)

    report = build_xauusd_trend_pullback_stability_audit_v0_49(
        data_dir=data_dir,
        manifest_path=manifest,
        source_board_path=source_board,
    )

    assert report["validation_trade_count"] == 30
    assert report["cost_sensitivity_if_available"]["edge_broken_by_fixed_cost"] is True
    assert report["stability_decision"] == UNSTABLE_REJECT
    assert report["candidate_locking_allowed_pre_oos"] is False


def test_no_order_send_order_check_or_live_allowed(tmp_path: Path) -> None:
    manifest, data_dir, source_board = _fixture(tmp_path, train_days=30, validation_days=8)

    report = build_xauusd_trend_pullback_stability_audit_v0_49(
        data_dir=data_dir,
        manifest_path=manifest,
        source_board_path=source_board,
    )

    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["execution_queue_created"] is False
    assert report["scheduler_created"] is False
    assert report["trade_recommendation_output_present"] is False


def test_missing_source_board_fails_without_oos_or_execution(tmp_path: Path) -> None:
    manifest, data_dir, _source_board = _fixture(tmp_path, train_days=30, validation_days=8)

    report = build_xauusd_trend_pullback_stability_audit_v0_49(
        data_dir=data_dir,
        manifest_path=manifest,
        source_board_path=tmp_path / "missing.json",
    )

    assert report["stability_decision"] == "audit_failed_missing_required_data"
    assert report["candidate_locking_allowed_pre_oos"] is False
    assert report["oos_used"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False


def test_cli_writes_required_report(tmp_path: Path) -> None:
    manifest, data_dir, source_board = _fixture(tmp_path, train_days=30, validation_days=8)
    output_path = tmp_path / "reports" / "audit.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_xauusd_trend_pullback_stability_v0_49.py"),
            "--json",
            "--output",
            str(output_path),
            "--data-dir",
            str(data_dir),
            "--manifest",
            str(manifest),
            "--source-board",
            str(source_board),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["audit_version"] == AUDIT_VERSION
    assert output_report["candidate_id"] == CANDIDATE_ID
