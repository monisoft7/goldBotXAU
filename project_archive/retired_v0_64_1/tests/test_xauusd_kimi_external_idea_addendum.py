from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_kimi_external_idea_addendum import (
    ADDENDUM_VERSION,
    SHORTLIST_UNCHANGED,
    build_xauusd_kimi_external_idea_addendum_v0_52_1,
)

ROOT = Path(__file__).resolve().parents[1]

KIMI_IDS = {
    "opening_range_breakout_with_momentum_confirmation",
    "mean_reversion_after_extended_sequential_moves",
    "london_close_or_asian_liquidity_sweep",
    "range_contraction_expansion_with_close_bias",
    "ny_session_first_hour_continuation",
    "gap_fill_failure",
    "vwap_deviation_reversion",
    "three_candle_body_confirmation_reversal",
    "higher_timeframe_alignment_pullback",
    "friday_range_extension_reversal",
}

EXPECTED_SHORTLIST = [
    "prior_day_liquidity_sweep_reversal",
    "london_opening_range_breakout_or_first_candle_direction",
    "asian_range_london_breakout_confirmation",
]


def test_kimi_is_added_to_external_sources() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()

    assert report["addendum_version"] == ADDENDUM_VERSION
    assert report["source_triage_version"] == "v0_52"
    assert report["kimi_added_to_external_sources"] is True
    assert "kimi" in report["external_sources_considered"]


def test_all_ten_kimi_ideas_are_represented_before_deduplication() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()

    assert report["kimi_raw_idea_count"] == 10
    assert set(report["kimi_raw_idea_ids"]) == KIMI_IDS
    assert {record["idea_id"] for record in report["kimi_idea_records"]} == KIMI_IDS


def test_overlapping_ideas_are_deduplicated_or_penalized() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()
    records = {record["idea_id"]: record for record in report["kimi_idea_records"]}

    assert records["opening_range_breakout_with_momentum_confirmation"]["disposition"] == "deduplicated_overlap"
    assert "london_opening_range_breakout_or_first_candle_direction" in records[
        "opening_range_breakout_with_momentum_confirmation"
    ]["overlaps_with"]
    assert records["london_close_or_asian_liquidity_sweep"]["disposition"] == "deduplicated_overlap"
    assert records["ny_session_first_hour_continuation"]["disposition"] == "deduplicated_overlap"


def test_v0_26_like_compression_idea_is_penalized() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()
    idea = next(
        record for record in report["kimi_idea_records"] if record["idea_id"] == "range_contraction_expansion_with_close_bias"
    )

    assert idea["disposition"] == "penalized_scored_idea"
    assert "xauusd_compression_then_expansion_v0_26" in idea["overlaps_with"]
    assert "penalized_similarity_to_failed_v0_26_compression_expansion_branch" in idea["penalty_notes"]
    assert idea["scorecard"]["difference_from_failed_candidates"] == 2


def test_trend_pullback_like_idea_is_penalized() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()
    idea = next(
        record for record in report["kimi_idea_records"] if record["idea_id"] == "higher_timeframe_alignment_pullback"
    )

    assert idea["disposition"] == "penalized_scored_idea"
    assert "trend_pullback_continuation_directional_v0_51" in idea["overlaps_with"]
    assert "penalized_similarity_to_failed_v0_48_v0_51_trend_pullback_branch" in idea["penalty_notes"]
    assert idea["scorecard"]["difference_from_failed_candidates"] == 1


def test_vwap_idea_is_penalized_for_uncertain_volume_quality() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()
    idea = next(record for record in report["kimi_idea_records"] if record["idea_id"] == "vwap_deviation_reversion")

    assert idea["disposition"] == "penalized_overlap"
    assert "vwap_mean_reversion" in idea["overlaps_with"]
    assert "penalized_vwap_volume_quality_uncertain" in idea["penalty_notes"]


def test_final_shortlist_max_three_and_unchanged() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()

    assert report["addendum_status"] == SHORTLIST_UNCHANGED
    assert report["original_v0_52_shortlist"] == EXPECTED_SHORTLIST
    assert report["final_shortlist_for_v0_53"] == EXPECTED_SHORTLIST
    assert len(report["final_shortlist_for_v0_53"]) <= 3
    assert report["shortlist_changed"] is False
    assert "did_not_materially_beat" in report["shortlist_change_reason"]


def test_top_ranked_idea_remains_v0_52_leader() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()

    assert report["top_ranked_idea_id"] == "prior_day_liquidity_sweep_reversal"
    assert report["scoring_method_preserved"] is True


def test_no_backtest_oos_retune_threshold_grid_candidate_or_execution() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["backtest_implemented"] is False
    assert report["candidate_created"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["safety"]["execution_queue_created"] is False
    assert report["safety"]["scheduler_created"] is False
    assert report["safety"]["auto_execute_order"] is False


def test_data_csv_not_staged_or_committed() -> None:
    report = build_xauusd_kimi_external_idea_addendum_v0_52_1()
    completed = subprocess.run(
        ["git", "status", "--short", "--", "data/*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert report["data_csv_added_to_git"] is False
    assert completed.stdout.strip() == ""


def test_report_contains_no_user_facing_buy_or_sell_recommendations() -> None:
    text = json.dumps(build_xauusd_kimi_external_idea_addendum_v0_52_1())

    assert "B" + "UY" not in text
    assert "S" + "ELL" not in text


def test_missing_v0_52_report_blocks_cleanly(tmp_path: Path) -> None:
    missing = tmp_path / "missing_v0_52.json"

    report = build_xauusd_kimi_external_idea_addendum_v0_52_1(missing)

    assert report["addendum_status"] == "kimi_addendum_failed_missing_v0_52_report"
    assert report["blockers"] == [f"missing_v0_52_report:{missing.as_posix()}"]
    assert report["oos_used"] is False
    assert report["order_send_called"] is False


def test_cli_writes_required_report(tmp_path: Path) -> None:
    output = tmp_path / "kimi_addendum.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_kimi_idea_addendum_v0_52_1.py"),
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
    assert stdout_report["addendum_version"] == ADDENDUM_VERSION
    assert output_report["addendum_status"] == SHORTLIST_UNCHANGED
    assert output_report["final_shortlist_for_v0_53"] == EXPECTED_SHORTLIST
