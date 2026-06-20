from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_session_volatility_candidate_design_board import (
    BLOCKED_MISSING_PROFILER,
    COMPLETED_WITH_CANDIDATE,
    DESIGN_VERSION,
    build_xauusd_session_volatility_candidate_design_board_v0_55,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _family_result(
    family_id: str,
    *,
    train_behavior: str,
    validation_behavior: str,
    train_mean: float,
    validation_mean: float,
    total_score: int,
    stability_notes: list[str] | None = None,
) -> dict[str, object]:
    primary = "block_return_points" if family_id == "session_return_profile" else "same_day_close_open_points"
    return {
        "event_family_id": family_id,
        "event_count_train": 120,
        "event_count_validation": 60,
        "candidate_suitability_score": {"total_score": total_score},
        "train_summary": {
            "event_count": 120,
            "primary_horizon": primary,
            "dominant_behavior": train_behavior,
            "dominant_behavior_mean_return_points": train_mean,
            "behavior_summaries": {
                train_behavior: {
                    "event_count": 120,
                    "mean_return_points_by_horizon": {primary: train_mean},
                    "positive_rate_by_horizon": {primary: 0.56},
                }
            },
        },
        "validation_summary": {
            "event_count": 60,
            "primary_horizon": primary,
            "dominant_behavior": validation_behavior,
            "dominant_behavior_mean_return_points": validation_mean,
            "behavior_summaries": {
                validation_behavior: {
                    "event_count": 60,
                    "mean_return_points_by_horizon": {primary: validation_mean},
                    "positive_rate_by_horizon": {primary: 0.54},
                },
                train_behavior: {
                    "event_count": 60,
                    "mean_return_points_by_horizon": {primary: validation_mean},
                    "positive_rate_by_horizon": {primary: 0.54},
                },
            },
        },
        "stability_notes": stability_notes or ["dominant_behavior_mean_return_same_sign"],
    }


def _profiler_report() -> dict[str, object]:
    return {
        "profiler_version": "v0_54",
        "profiler_status": "edge_profile_completed_with_research_leads",
        "train_validation_only": True,
        "oos_used": False,
        "strongest_empirical_leads": [
            {"event_family_id": "session_return_profile"},
            {"event_family_id": "volatility_regime_profile"},
        ],
        "event_family_results": [
            _family_result(
                "session_return_profile",
                train_behavior="asian_00_06",
                validation_behavior="asian_00_06",
                train_mean=1.2,
                validation_mean=3.4,
                total_score=33,
                stability_notes=["dominant_behavior_consistent_train_validation", "dominant_behavior_mean_return_same_sign"],
            ),
            _family_result(
                "volatility_regime_profile",
                train_behavior="medium_high_volatility_quartile",
                validation_behavior="high_volatility_quartile",
                train_mean=6.8,
                validation_mean=9.1,
                total_score=30,
                stability_notes=["dominant_behavior_differs_between_train_validation", "dominant_behavior_mean_return_same_sign"],
            ),
            _family_result(
                "prior_day_high_low_sweep_profile",
                train_behavior="ignored",
                validation_behavior="ignored",
                train_mean=20.0,
                validation_mean=20.0,
                total_score=35,
            ),
        ],
    }


def test_v0_54_profiler_report_is_required(tmp_path: Path) -> None:
    report = build_xauusd_session_volatility_candidate_design_board_v0_55(
        source_profiler_path=tmp_path / "missing.json",
    )

    assert report["design_status"] == BLOCKED_MISSING_PROFILER
    assert report["blockers"] == ["source_v0_54_profiler_report_missing_or_invalid"]
    assert report["candidate_designs"] == []


def test_only_v0_54_top_session_and_volatility_leads_are_used(tmp_path: Path) -> None:
    source = tmp_path / "reports" / "profiler.json"
    _write_json(source, _profiler_report())

    report = build_xauusd_session_volatility_candidate_design_board_v0_55(source_profiler_path=source)

    assert report["design_version"] == DESIGN_VERSION
    assert report["design_status"] == COMPLETED_WITH_CANDIDATE
    assert report["source_profiler_version"] == "v0_54"
    assert report["source_profiler_status"] == "edge_profile_completed_with_research_leads"
    assert report["profiler_leads_used"] == ["session_return_profile", "volatility_regime_profile"]
    assert {design["source_lead"] for design in report["candidate_designs"]} == {
        "session_return_profile",
        "volatility_regime_profile",
    }
    assert "prior_day_high_low_sweep_profile" not in json.dumps(report)


def test_candidate_designs_have_exact_rules_and_rejection_metrics(tmp_path: Path) -> None:
    source = tmp_path / "reports" / "profiler.json"
    _write_json(source, _profiler_report())

    report = build_xauusd_session_volatility_candidate_design_board_v0_55(source_profiler_path=source)

    required = {
        "candidate_design_id",
        "source_lead",
        "market_logic",
        "exact_entry_rule",
        "exact_direction_rule",
        "exact_invalidation_rule",
        "stop_loss_logic",
        "take_profit_or_exit_logic",
        "time_session_filter",
        "volatility_filter",
        "expected_trade_frequency",
        "minimum_data_required",
        "main_failure_modes",
        "anti_curve_fit_argument",
        "train_validation_test_plan",
        "rejection_metrics",
        "candidate_design_suitability_score",
        "recommended_action",
    }
    assert 2 <= report["candidate_design_count"] <= 4
    for design in report["candidate_designs"]:
        assert set(design) == required
        assert str(design["exact_entry_rule"])
        assert str(design["exact_direction_rule"])
        assert str(design["exact_invalidation_rule"])
        assert str(design["stop_loss_logic"])
        assert str(design["take_profit_or_exit_logic"])
        assert design["rejection_metrics"]
        assert design["recommended_action"] in {
            "promote_to_v0_56_train_validation_test",
            "keep_for_observation_only",
            "reject_design",
        }


def test_final_recommended_v0_56_candidate_count_is_at_most_one(tmp_path: Path) -> None:
    source = tmp_path / "reports" / "profiler.json"
    _write_json(source, _profiler_report())

    report = build_xauusd_session_volatility_candidate_design_board_v0_55(source_profiler_path=source)
    promoted = [
        design
        for design in report["candidate_designs"]
        if design["recommended_action"] == "promote_to_v0_56_train_validation_test"
    ]

    assert len(promoted) <= 1
    assert report["recommended_candidate_for_v0_56"] == "session_block_directional_bias_candidate"
    assert report["next_recommended_step"] == (
        "v0_56 fixed-rule train/validation evaluation for session_block_directional_bias_candidate only, no OOS"
    )


def test_train_validation_only_no_oos_no_retune_or_execution(tmp_path: Path) -> None:
    source = tmp_path / "reports" / "profiler.json"
    _write_json(source, _profiler_report())

    report = build_xauusd_session_volatility_candidate_design_board_v0_55(source_profiler_path=source)

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["safety"]["execution_queue_created"] is False
    assert report["safety"]["scheduler_created"] is False


def test_data_csv_not_staged_or_committed(tmp_path: Path) -> None:
    source = tmp_path / "reports" / "profiler.json"
    _write_json(source, _profiler_report())
    report = build_xauusd_session_volatility_candidate_design_board_v0_55(source_profiler_path=source)
    completed = subprocess.run(
        ["git", "status", "--short", "--", "data/*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert report["data_csv_added_to_git"] is False
    assert completed.stdout.strip() == ""


def test_cli_writes_required_report(tmp_path: Path) -> None:
    source = tmp_path / "reports" / "profiler.json"
    output = tmp_path / "reports" / "design.json"
    _write_json(source, _profiler_report())

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_session_volatility_design_v0_55.py"),
            "--json",
            "--output",
            str(output),
            "--source-profiler",
            str(source),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["design_version"] == DESIGN_VERSION
    assert output_report["design_status"] == COMPLETED_WITH_CANDIDATE
    assert output_report["oos_used"] is False
