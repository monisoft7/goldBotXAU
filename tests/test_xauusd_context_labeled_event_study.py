from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.research.xauusd_context_labeled_event_study import (
    BLOCKED_MISSING_V0_62_LABELS,
    COMPLETED_NO_CLEAR_LEADS,
    COMPLETED_WITH_LEADS,
    CONTEXT_STUDY_VERSION,
    CANDIDATES_TO_ANALYZE,
    CONTEXT_LABELS_TO_ATTACH,
    build_xauusd_context_labeled_event_study_v0_63,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _label_report(tmp_path: Path) -> Path:
    return _write_json(
        tmp_path / "reports" / "xauusd_market_context_labels_v0_62.json",
        {
            "labeler_version": "v0_62",
            "labeler_status": "market_context_labeler_completed",
            "labels_are_trade_blockers": False,
            "timestamp_only_labels": [
                "market_closed_weekend",
                "likely_market_open",
                "asian_session",
                "london_morning_session",
                "ny_core_session",
                "late_us_session",
                "off_session_or_low_activity",
                "session_transition_asian_to_london",
                "session_transition_london_to_ny",
                "friday_late_session",
                "monday_reopen_window",
            ],
        },
    )


def _source_reports(tmp_path: Path) -> tuple[Path, Path, Path]:
    v0_53 = _write_json(
        tmp_path / "reports" / "xauusd_external_shortlist_board_v0_53.json",
        {
            "board_version": "v0_53",
            "rejected_do_not_retune_candidates": [
                "prior_day_liquidity_sweep_reversal",
                "london_opening_range_breakout_or_first_candle_direction",
                "asian_range_london_breakout_confirmation",
            ],
        },
    )
    v0_56 = _write_json(
        tmp_path / "reports" / "xauusd_session_block_bias_eval_v0_56.json",
        {
            "evaluation_version": "v0_56",
            "rejected_do_not_retune": True,
        },
    )
    v0_60 = _write_json(
        tmp_path / "reports" / "xauusd_second_tier_board_v0_60.json",
        {
            "board_version": "v0_60",
            "rejected_do_not_retune_candidates": [
                "failed_m15_swing_breakout_reversal",
                "ny_liquidity_sweep_reversal",
                "sequential_m5_move_mean_reversion",
            ],
        },
    )
    return v0_53, v0_56, v0_60


def _event(candidate_id: str, split: str, timestamp: datetime, return_r: float) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "split": split,
        "entry_timestamp": timestamp.isoformat(),
        "exit_timestamp": timestamp.replace(hour=min(timestamp.hour + 1, 23)).isoformat(),
        "side": "long",
        "entry_price": 2000.0,
        "exit_price": 2001.0,
        "stop_price": 1999.0,
        "target_price": 2002.0,
        "return_r": return_r,
        "won": return_r > 0.0,
        "exit_reason": "fixture",
    }


def _lead_events() -> dict[str, list[dict[str, object]]]:
    records: list[dict[str, object]] = []
    for index in range(30):
        records.append(
            _event(
                "asian_range_london_breakout_confirmation",
                "train",
                datetime(2024, (index % 6) + 1, (index % 20) + 1, 8, 0),
                1.0 if index < 20 else -0.5,
            )
        )
    for index in range(30):
        year = 2025 if index % 2 == 0 else 2026
        records.append(
            _event(
                "asian_range_london_breakout_confirmation",
                "validation",
                datetime(year, (index % 6) + 1, (index % 20) + 1, 8, 0),
                1.0 if index < 20 else -0.5,
            )
        )
    return {"asian_range_london_breakout_confirmation": records}


def _weak_events() -> dict[str, list[dict[str, object]]]:
    records: list[dict[str, object]] = []
    for index in range(30):
        records.append(
            _event(
                "ny_liquidity_sweep_reversal",
                "train",
                datetime(2024, (index % 6) + 1, (index % 20) + 1, 13, 0),
                1.0,
            )
        )
    for index in range(10):
        records.append(
            _event(
                "ny_liquidity_sweep_reversal",
                "validation",
                datetime(2025, 7, (index % 20) + 1, 13, 0),
                -1.0,
            )
        )
    return {"ny_liquidity_sweep_reversal": records}


def _build_with_events(tmp_path: Path, events: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    v0_53, v0_56, v0_60 = _source_reports(tmp_path)
    return build_xauusd_context_labeled_event_study_v0_63(
        label_report_path=_label_report(tmp_path),
        source_v0_53_path=v0_53,
        source_v0_56_path=v0_56,
        source_v0_60_path=v0_60,
        candidate_event_records=events,
    )


def test_v0_62_labels_are_required(tmp_path: Path) -> None:
    v0_53, v0_56, v0_60 = _source_reports(tmp_path)

    report = build_xauusd_context_labeled_event_study_v0_63(
        label_report_path=tmp_path / "missing.json",
        source_v0_53_path=v0_53,
        source_v0_56_path=v0_56,
        source_v0_60_path=v0_60,
        candidate_event_records={},
    )

    assert report["context_study_status"] == BLOCKED_MISSING_V0_62_LABELS
    assert report["blockers"] == ["source_v0_62_label_report_missing_or_invalid"]
    assert report["labels_used_as_trade_blockers"] is False


def test_strong_fixture_reports_context_conditioned_lead(tmp_path: Path) -> None:
    report = _build_with_events(tmp_path, _lead_events())

    assert report["context_study_version"] == CONTEXT_STUDY_VERSION
    assert report["context_study_status"] == COMPLETED_WITH_LEADS
    assert report["strongest_context_conditioned_leads"] == [
        {
            "candidate_id": "asian_range_london_breakout_confirmation",
            "context_label": "london_morning_session",
            "lead_scope": "retrospective_context_conditioned_research_lead_only",
            "trade_count_train": 30,
            "trade_count_validation": 30,
            "train_expectancy": 0.5,
            "train_profit_factor": 4.0,
            "validation_expectancy": 0.5,
            "validation_profit_factor": 4.0,
        }
    ]
    result = report["candidate_results_by_context"]["asian_range_london_breakout_confirmation"]["london_morning_session"]
    assert result["sample_sufficiency"] == "sufficient_for_context_lead_screen"
    assert result["train_validation_consistency"] == "consistent_positive_train_validation"
    assert result["context_concentration_risk"]["risk_present"] is False


def test_weak_fixture_reports_no_clear_lead(tmp_path: Path) -> None:
    report = _build_with_events(tmp_path, _weak_events())

    assert report["context_study_status"] == COMPLETED_NO_CLEAR_LEADS
    assert report["strongest_context_conditioned_leads"] == []
    assert report["recommended_v0_64_plan"] == (
        "add external datasets such as holiday/economic calendar/DXY before further context testing."
    )


def test_all_required_candidate_context_pairs_are_reported(tmp_path: Path) -> None:
    report = _build_with_events(tmp_path, _weak_events())

    assert list(report["candidate_results_by_context"]) == CANDIDATES_TO_ANALYZE
    for candidate_id in CANDIDATES_TO_ANALYZE:
        assert list(report["candidate_results_by_context"][candidate_id]) == CONTEXT_LABELS_TO_ATTACH
        context_result = report["candidate_results_by_context"][candidate_id]["likely_market_open"]
        assert {
            "trade_count_train",
            "trade_count_validation",
            "train_profit_factor",
            "validation_profit_factor",
            "train_expectancy",
            "validation_expectancy",
            "max_consecutive_losses",
            "sample_sufficiency",
            "train_validation_consistency",
            "context_concentration_risk",
            "interpretive_note",
        }.issubset(context_result)


def test_safety_flags_remain_locked(tmp_path: Path) -> None:
    report = _build_with_events(tmp_path, _lead_events())

    assert report["labels_used_as_trade_blockers"] is False
    assert report["strategy_rules_changed"] is False
    assert report["gates_lowered"] is False
    assert report["source_rejection_state"]["all_requested_prior_branches_remain_rejected_do_not_retune"] is True
    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False
    assert report["revived_candidate_allowed"] is False
    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False


def test_data_csv_not_staged_or_committed(tmp_path: Path) -> None:
    report = _build_with_events(tmp_path, _lead_events())
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
    output = tmp_path / "reports" / "xauusd_context_labeled_event_study_v0_63.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_context_labeled_event_study_v0_63.py"),
            "--json",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["context_study_version"] == CONTEXT_STUDY_VERSION
    assert output_report["source_labeler_version"] == "v0_62"
    assert output_report["labels_used_as_trade_blockers"] is False
    assert output_report["oos_used"] is False
