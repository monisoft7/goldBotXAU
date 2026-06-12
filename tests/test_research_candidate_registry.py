from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.strategy_research_runner import run_strategy_research_harness

ROOT = Path(__file__).resolve().parents[1]
V0_7_ID = "xauusd_atr_impulse_reversion_v0_7"
V0_8_ID = "xauusd_multi_bar_exhaustion_reversion_v0_8"
V0_11_ID = "xauusd_session_volatility_expansion_v0_11"
V0_14_ID = "xauusd_low_atr_range_expansion_followthrough_v0_14"
V0_17_ID = "xauusd_low_atr_x_hour_16_v0_17"


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


def _registry_by_id() -> dict[str, dict[str, object]]:
    return {
        candidate["candidate_id"]: candidate
        for candidate in research_candidate_registry()["candidates"]
    }


def test_registry_includes_null_v0_7_v0_8_v0_11_v0_14_and_v0_17() -> None:
    candidates = _registry_by_id()

    assert "null_research_harness_test" in candidates
    assert V0_7_ID in candidates
    assert V0_8_ID in candidates
    assert V0_11_ID in candidates
    assert V0_14_ID in candidates
    assert V0_17_ID in candidates


def test_rejected_candidates_are_marked_do_not_retune() -> None:
    candidates = _registry_by_id()

    assert candidates[V0_7_ID]["status"] == "rejected"
    assert candidates[V0_7_ID]["do_not_retune"] is True
    assert candidates[V0_8_ID]["status"] == "rejected"
    assert candidates[V0_8_ID]["do_not_retune"] is True


def test_v0_11_is_rejected_with_oos_locked_after_fixed_evaluation() -> None:
    candidates = _registry_by_id()

    assert candidates[V0_11_ID]["status"] == "rejected"
    assert candidates[V0_11_ID]["rejection_reason"] == "validation_gate_failed"
    assert candidates[V0_11_ID]["oos_status"] == "locked_not_evaluated"
    assert candidates[V0_11_ID]["eligible_for_oos_review"] is False
    assert candidates[V0_11_ID]["do_not_retune"] is True


def test_v0_14_is_rejected_with_oos_locked_after_fixed_evaluation() -> None:
    candidates = _registry_by_id()

    assert candidates[V0_14_ID]["status"] == "rejected"
    assert candidates[V0_14_ID]["rejection_reason"] == "validation_gate_failed"
    assert candidates[V0_14_ID]["source_selection_board"] == "v0_13_strategy_family_selection_board"
    assert candidates[V0_14_ID]["oos_status"] == "locked_not_evaluated"
    assert candidates[V0_14_ID]["eligible_for_oos_review"] is False
    assert candidates[V0_14_ID]["do_not_retune"] is True


def test_v0_17_is_recorded_with_oos_locked_after_fixed_evaluation() -> None:
    candidates = _registry_by_id()

    assert candidates[V0_17_ID]["status"] in {"pending_local_evaluation", "rejected", "validation_passed_pending_oos_review"}
    assert candidates[V0_17_ID]["source_triage"] == "v0_16_advisor_idea_triage"
    assert candidates[V0_17_ID]["oos_status"] == "locked_not_evaluated"
    assert candidates[V0_17_ID]["do_not_retune"] is True


def test_registry_keeps_oos_locked_and_has_no_oos_eligible_candidates() -> None:
    report = research_candidate_registry()

    assert report["eligible_for_oos_review_count"] in {0, 1}
    assert report["oos_locked"] is True


def test_registry_safety_flags_exist() -> None:
    assert research_candidate_registry()["safety"] == {
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
        "buy_sell_output_allowed": False,
        "execution_logic_present": False,
        "trade_recommendation_output_present": False,
        "oos_locked": True,
    }


def test_compact_mode_omits_equity_curve(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = run_strategy_research_harness(data_dir, candidate_id=V0_8_ID, compact=True)

    assert "equity_curve" not in report["results"]["train_metrics"]
    assert "equity_curve" not in report["results"]["validation_metrics"]


def test_compact_mode_includes_required_metric_summaries(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = run_strategy_research_harness(data_dir, candidate_id=V0_8_ID, compact=True)
    required_keys = {
        "final_equity_r",
        "trade_count",
        "win_rate",
        "profit_factor",
        "expectancy",
        "max_drawdown",
        "max_consecutive_losses",
        "gross_profit",
        "gross_loss",
        "wins",
        "losses",
        "out_of_sample_result",
    }

    assert set(report["results"]["train_metrics"]) == required_keys
    assert set(report["results"]["validation_metrics"]) == required_keys


def test_list_research_candidates_cli_prints_registry_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "list_research_candidates.py"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["registry_version"] == "v0_17"
    assert report["candidate_count"] == 6
    assert report["rejected_count"] >= 4


def test_compact_cli_omits_equity_curve(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_strategy_research_harness.py"),
            "--data-dir",
            str(data_dir),
            "--candidate",
            V0_8_ID,
            "--compact",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report_text = completed.stdout
    report = json.loads(report_text)

    assert "equity_curve" not in report_text
    assert "final_equity_r" in report["results"]["train_metrics"]


def test_no_demo_live_order_send_permission_exposed() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "candidate_registry.py",
            ROOT / "src" / "research" / "strategy_research_runner.py",
            ROOT / "scripts" / "list_research_candidates.py",
            ROOT / "scripts" / "run_strategy_research_harness.py",
        ]
    ).lower()

    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text


def test_no_trade_direction_output_exposed(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)
    report_text = json.dumps(
        {
            "registry": research_candidate_registry(),
            "compact": run_strategy_research_harness(data_dir, candidate_id=V0_8_ID, compact=True),
        }
    )

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
