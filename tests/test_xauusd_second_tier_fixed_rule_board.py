from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from src.research.xauusd_second_tier_fixed_rule_board import (
    BLOCKED_MISSING_POLICY_DOCS,
    BOARD_VERSION,
    CANDIDATES,
    NONE_PASSED,
    PASSED,
    build_xauusd_second_tier_fixed_rule_board_v0_60,
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


def _write_v0_59(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "standardization_version": "v0_59",
                "standardization_status": "lab_warning_standardization_completed",
                "cost_policy_documented": True,
                "timestamp_policy_documented": True,
                "gap_classification_policy_documented": True,
                "gate_policy_documented": True,
                "timestamp_session_policy": {"timestamp_basis": "unknown_or_broker_server_time"},
            }
        ),
        encoding="utf-8",
    )


def _write_policy_docs(root: Path) -> None:
    for relative_path in (
        "docs/research_lab_cost_policy.md",
        "docs/research_lab_timestamp_and_session_policy.md",
        "docs/research_lab_gap_classification_policy.md",
        "docs/research_lab_gate_policy.md",
    ):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# policy\n", encoding="utf-8")


def _write_rows(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _m15_day_rows(day: date, *, base: float) -> list[dict[str, float | str]]:
    return [
        {
            "timestamp": datetime.combine(day, datetime.min.time()).replace(hour=10, minute=0).isoformat(),
            "open": base,
            "high": base + 1.0,
            "low": base - 1.0,
            "close": base,
            "volume": 1.0,
        }
    ]


def _m5_day_rows(day: date, *, base: float, favorable: bool) -> list[dict[str, float | str]]:
    values = [
        (7, 0, base, base + 0.1, base - 0.1, base),
        (7, 5, base - 0.2, base - 0.1, base - 0.4, base - 0.3),
        (7, 10, base - 0.3, base - 0.2, base - 0.7, base - 0.6),
        (7, 15, base - 0.6, base - 0.5, base - 1.0, base - 0.9),
        (7, 20, base - 0.9, base - 0.8, base - 1.3, base - 1.2),
        (7, 25, base - 1.2, base - 1.1, base - 1.6, base - 1.5),
        (
            7,
            30,
            base - 1.5,
            base - 0.1 if favorable else base - 1.4,
            base - 1.6 if favorable else base - 1.8,
            base - 0.2 if favorable else base - 1.7,
        ),
    ]
    rows: list[dict[str, float | str]] = []
    for hour, minute, open_price, high, low, close in values:
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


def _fixture(tmp_path: Path, *, favorable: bool, validation_days: int = 60) -> tuple[Path, Path, Path]:
    manifest = tmp_path / "reports" / "manifest.json"
    standardization = tmp_path / "reports" / "v0_59.json"
    data_dir = tmp_path / "data"
    _write_manifest(manifest)
    _write_v0_59(standardization)
    _write_policy_docs(tmp_path)
    m15_rows: list[dict[str, float | str]] = []
    m5_rows: list[dict[str, float | str]] = []
    sequence = 0
    for index in range(60):
        day = date(2025, 4, 1) + timedelta(days=index)
        m15_rows.extend(_m15_day_rows(day, base=2000.0 + sequence * 0.01))
        m5_rows.extend(_m5_day_rows(day, base=2000.0 + sequence * 0.01, favorable=favorable))
        sequence += 1
    for index in range(validation_days):
        day = date(2025, 7, 1) + timedelta(days=index)
        m15_rows.extend(_m15_day_rows(day, base=2100.0 + sequence * 0.01))
        m5_rows.extend(_m5_day_rows(day, base=2100.0 + sequence * 0.01, favorable=favorable))
        sequence += 1
    for index in range(3):
        day = date(2026, 1, 2) + timedelta(days=index)
        m15_rows.extend(_m15_day_rows(day, base=2200.0 + sequence * 0.01))
        m5_rows.extend(_m5_day_rows(day, base=2200.0 + sequence * 0.01, favorable=True))
        sequence += 1
    _write_rows(data_dir / "xauusd_m15_fixture.csv", m15_rows)
    _write_rows(data_dir / "xauusd_m5_fixture.csv", m5_rows)
    return manifest, standardization, data_dir


def _build(tmp_path: Path, *, favorable: bool, validation_days: int = 60) -> dict[str, object]:
    manifest, standardization, data_dir = _fixture(tmp_path, favorable=favorable, validation_days=validation_days)
    return build_xauusd_second_tier_fixed_rule_board_v0_60(
        data_dir=data_dir,
        m5_pattern="xauusd_m5_*.csv",
        manifest_path=manifest,
        source_standardization_path=standardization,
        policy_root=tmp_path,
    )


def test_v0_59_policy_docs_are_required(tmp_path: Path) -> None:
    manifest, standardization, data_dir = _fixture(tmp_path, favorable=True)
    (tmp_path / "docs" / "research_lab_cost_policy.md").unlink()

    report = build_xauusd_second_tier_fixed_rule_board_v0_60(
        data_dir=data_dir,
        m5_pattern="xauusd_m5_*.csv",
        manifest_path=manifest,
        source_standardization_path=standardization,
        policy_root=tmp_path,
    )

    assert report["board_status"] == BLOCKED_MISSING_POLICY_DOCS
    assert "cost_policy_document_missing:docs/research_lab_cost_policy.md" in report["blockers"]
    assert report["oos_used"] is False


def test_all_three_second_tier_candidate_ids_are_present(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)

    assert report["board_version"] == BOARD_VERSION
    assert report["source_standardization_version"] == "v0_59"
    assert report["tested_candidate_ids"] == list(CANDIDATES)
    assert [result["candidate_id"] for result in report["candidate_results"]] == list(CANDIDATES)


def test_fixed_rules_are_implemented_for_all_three_candidates(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)
    rules = {result["candidate_id"]: result["fixed_rules"] for result in report["candidate_results"]}

    assert rules["failed_m15_swing_breakout_reversal"]["swing_lookback_completed_m15_candles"] == 20
    assert rules["failed_m15_swing_breakout_reversal"]["time_exit"] == "after_8_m15_bars_or_20_00_utc"
    assert rules["ny_liquidity_sweep_reversal"]["reference_range_utc"] == "00:00-12:00"
    assert rules["ny_liquidity_sweep_reversal"]["timestamp_policy"] == "fixed_utc_windows_with_timestamp_basis_reported"
    assert rules["sequential_m5_move_mean_reversion"]["streak_length"] == 5
    assert rules["sequential_m5_move_mean_reversion"]["news_calendar_filter"] == "none_in_v0_60"
    assert all(result["fixed_before_evaluation"] is True for result in report["candidate_results"])


def test_train_validation_only_oos_not_used_and_no_retune_or_search(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["gates_lowered"] is False
    assert report["past_metrics_changed"] is False
    assert report["split_candle_counts"]["M15"]["excluded_oos"] > 0
    assert report["split_candle_counts"]["M5"]["excluded_oos"] > 0


def test_no_executable_candidate_creation_or_execution_surface(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)

    assert report["executable_candidate_created"] is False
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


def test_timestamp_basis_and_policy_references_are_present(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)

    assert report["timestamp_basis_reported"] is True
    assert report["timestamp_basis"] == "unknown_or_broker_server_time"
    assert report["cost_policy_reference"] == "docs/research_lab_cost_policy.md"
    assert report["gap_policy_reference"] == "docs/research_lab_gap_classification_policy.md"
    assert report["gate_policy_reference"] == "docs/research_lab_gate_policy.md"
    assert set(report["standardized_policy_references"]) == {
        "cost_policy",
        "timestamp_session_policy",
        "gap_classification_policy",
        "gate_policy",
    }


def test_passing_fixture_selects_best_candidate(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=True)

    assert report["board_status"] == PASSED
    assert report["best_candidate_id"] == "sequential_m5_move_mean_reversion"
    assert report["best_candidate_passed_gate"] is True
    assert report["best_candidate_metrics"]["validation"]["trades"] >= 50
    assert report["best_candidate_metrics"]["validation"]["profit_factor"] == "inf"
    assert report["best_candidate_metrics"]["validation"]["expectancy_r"] > 0
    assert report["next_recommended_step"] == "lock fixed candidate artifact and prepare one-time OOS protocol, no OOS yet."


def test_failing_fixture_rejects_all_as_do_not_retune(tmp_path: Path) -> None:
    report = _build(tmp_path, favorable=False)

    assert report["board_status"] == NONE_PASSED
    assert report["best_candidate_passed_gate"] is False
    assert report["rejected_do_not_retune_candidates"] == list(CANDIDATES)
    assert all(result["passed_gate"] is False for result in report["candidate_results"])
    assert all(result["do_not_retune"] is True for result in report["candidate_results"])
    assert (
        report["next_recommended_step"]
        == "broaden non-OOS research or consider adding external features such as DXY/yields/news calendar before further strategy tests."
    )


def test_cli_writes_required_report(tmp_path: Path) -> None:
    manifest, standardization, data_dir = _fixture(tmp_path, favorable=True)
    output = tmp_path / "reports" / "board.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_second_tier_board_v0_60.py"),
            "--json",
            "--output",
            str(output),
            "--data-dir",
            str(data_dir),
            "--manifest",
            str(manifest),
            "--source-standardization",
            str(standardization),
            "--m5-pattern",
            "xauusd_m5_*.csv",
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
