from __future__ import annotations

import json
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.strategy_research_runner import run_strategy_research_harness

V0_14_ID = "xauusd_low_atr_range_expansion_followthrough_v0_14"


def _write_ready_dataset(data_dir: Path) -> None:
    data_dir.mkdir()
    (data_dir / "xauusd_m15_fixture.csv").write_text(
        "\n".join(
            [
                "timestamp,open,high,low,close,volume",
                "2025-06-30 23:45,2000,2002,1999,2001,1",
                "2025-07-01 00:00,2001,2003,2000,2002,1",
                "2026-01-01 00:00,2002,2004,2001,2003,1",
            ]
        ),
        encoding="utf-8",
    )


def _candidate_by_id(candidate_id: str) -> dict[str, object]:
    return {
        candidate["candidate_id"]: candidate
        for candidate in research_candidate_registry()["candidates"]
    }[candidate_id]


def test_null_candidate_report_has_no_research_candidate_logic(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    safety = run_strategy_research_harness(data_dir)["safety"]

    assert safety["research_candidate_logic_present"] is False


def test_real_candidate_report_has_research_candidate_logic(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    safety = run_strategy_research_harness(data_dir, candidate_id=V0_14_ID)["safety"]

    assert safety["research_candidate_logic_present"] is True


def test_execution_and_recommendation_output_are_absent_for_all_reports(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)
    reports = [
        run_strategy_research_harness(data_dir),
        run_strategy_research_harness(data_dir, candidate_id=V0_14_ID),
    ]

    for report in reports:
        safety = report["safety"]
        assert safety["execution_logic_present"] is False
        assert safety["trade_recommendation_output_present"] is False
        assert safety["demo_enabled"] is False
        assert safety["live_enabled"] is False
        assert safety["order_send_allowed"] is False
        assert safety["execution_queue_enabled"] is False


def test_oos_remains_locked_and_not_evaluated(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = run_strategy_research_harness(data_dir, candidate_id=V0_14_ID)

    assert report["oos_guard"] == {
        "oos_locked": True,
        "oos_access_attempted": False,
        "oos_access_allowed": False,
    }
    assert report["results"]["out_of_sample_result"] == "locked_not_evaluated"
    assert report["safety"]["oos_evaluated"] is False


def test_compact_report_includes_new_safety_fields(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    safety = run_strategy_research_harness(data_dir, candidate_id=V0_14_ID, compact=True)["safety"]

    assert set(safety) == {
        "demo_enabled",
        "live_enabled",
        "order_send_allowed",
        "execution_queue_enabled",
        "buy_sell_output_allowed",
        "oos_evaluated",
        "research_candidate_logic_present",
        "execution_logic_present",
        "trade_recommendation_output_present",
    }


def test_registry_safety_includes_clear_non_execution_fields() -> None:
    safety = research_candidate_registry()["safety"]

    assert safety["execution_logic_present"] is False
    assert safety["trade_recommendation_output_present"] is False
    assert safety["oos_locked"] is True


def test_no_trade_direction_words_appear_in_json_outputs(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)
    report_text = json.dumps(
        {
            "null_report": run_strategy_research_harness(data_dir),
            "v0_14_report": run_strategy_research_harness(data_dir, candidate_id=V0_14_ID, compact=True),
            "registry": research_candidate_registry(),
        }
    )

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text


def test_v0_14_remains_rejected_and_do_not_retune() -> None:
    candidate = _candidate_by_id(V0_14_ID)

    assert candidate["status"] == "rejected"
    assert candidate["rejection_reason"] == "validation_gate_failed"
    assert candidate["do_not_retune"] is True


def test_no_candidate_is_eligible_for_oos_review() -> None:
    registry = research_candidate_registry()

    assert registry["eligible_for_oos_review_count"] == 0
    assert all(candidate["eligible_for_oos_review"] is False for candidate in registry["candidates"])
