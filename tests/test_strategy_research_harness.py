from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.oos_guard import LOCKED_MESSAGE, OOSGuard
from src.research.strategy_candidate import NullResearchCandidate, ResearchCandidate
from src.research.strategy_research_runner import run_strategy_research_harness

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows), encoding="utf-8")


def _write_ready_dataset(data_dir: Path) -> None:
    data_dir.mkdir()
    _write_csv(
        data_dir / "xauusd_m15_fixture.csv",
        [
            "timestamp,open,high,low,close,volume",
            "2025-06-30 23:45,2000,2002,1999,2001,1",
            "2025-07-01 00:00,2001,2003,2000,2002,1",
            "2026-01-01 00:00,2002,2004,2001,2003,1",
        ],
    )


def _manifest() -> dict[str, object]:
    return {
        "split_policy": {
            "train_end": "2025-06-30T23:59:59",
            "validation_start": "2025-07-01T00:00:00",
            "validation_end": "2025-12-31T23:59:59",
            "oos_start": "2026-01-01T00:00:00",
        }
    }


def test_oos_guard_locks_oos_by_default() -> None:
    guard = OOSGuard(_manifest())

    assert guard.report()["oos_locked"] is True
    assert guard.report()["oos_access_allowed"] is False


def test_oos_access_attempt_raises_clear_error() -> None:
    guard = OOSGuard(_manifest())

    with pytest.raises(PermissionError, match=LOCKED_MESSAGE):
        guard.filter_candles([{"timestamp": "2026-01-01T00:00:00"}], "out_of_sample")

    assert guard.report()["oos_access_attempted"] is True


def test_runner_uses_train_and_validation_only(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = run_strategy_research_harness(data_dir)

    assert report["status"] == "harness_ready"
    assert report["dataset"]["train_candle_count"] == 1
    assert report["dataset"]["validation_candle_count"] == 1
    assert report["dataset"]["oos_candle_count"] == 1
    assert report["oos_guard"]["oos_access_attempted"] is False


def test_runner_does_not_evaluate_oos(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = run_strategy_research_harness(data_dir)

    assert report["results"]["out_of_sample_result"] == "locked_not_evaluated"
    assert report["decision"]["eligible_for_oos_review"] is False


def test_null_candidate_returns_zero_trades_safely() -> None:
    candidate = NullResearchCandidate()
    outcomes = candidate.run_on_split([{"timestamp": "2025-06-30T23:45:00"}], "train")

    assert outcomes == []


def test_forbidden_family_is_rejected_before_run(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)
    candidate = ResearchCandidate(
        candidate_id="bad_family",
        candidate_name="Bad Family",
        candidate_version="v0",
        family_name="baseline_current_rules",
        description="Forbidden family fixture.",
    )

    report = run_strategy_research_harness(data_dir, candidate=candidate)

    assert report["status"] == "candidate_rejected"
    assert report["errors"]


def test_cli_json_includes_oos_locked_true(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_strategy_research_harness.py"),
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

    assert report["oos_guard"]["oos_locked"] is True
    assert report["oos_guard"]["oos_access_allowed"] is False


def test_cli_json_includes_safety_flags(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_strategy_research_harness.py"),
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

    assert report["safety"] == {
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
        "execution_queue_enabled": False,
        "buy_sell_output_allowed": False,
        "oos_evaluated": False,
        "research_candidate_logic_present": False,
        "execution_logic_present": False,
        "trade_recommendation_output_present": False,
    }


def test_no_demo_live_order_send_permission_exposed() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "oos_guard.py",
            ROOT / "src" / "research" / "strategy_candidate.py",
            ROOT / "src" / "research" / "strategy_research_runner.py",
            ROOT / "scripts" / "run_strategy_research_harness.py",
        ]
    ).lower()

    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "order" + "_send(" not in source_text


def test_no_trade_direction_output_exposed(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)
    report_text = json.dumps(run_strategy_research_harness(data_dir))

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text


def test_existing_metric_fields_are_present_for_train_and_validation(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)
    report = run_strategy_research_harness(data_dir)

    for split_key in ("train_metrics", "validation_metrics"):
        metrics = report["results"][split_key]
        for metric_key in (
            "trade_count",
            "win_rate",
            "profit_factor",
            "expectancy",
            "max_drawdown",
            "max_consecutive_losses",
            "out_of_sample_result",
        ):
            assert metric_key in metrics


def test_harness_returns_data_not_ready_when_manifest_is_not_ready(tmp_path: Path) -> None:
    report = run_strategy_research_harness(tmp_path / "empty")

    assert report["status"] == "data_not_ready"
    assert report["decision"]["eligible_for_oos_review"] is False
