from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_external_strategy_idea_triage import (
    RAW_IDEAS,
    SHORTLIST_READY,
    TRIAGE_VERSION,
    build_xauusd_external_strategy_idea_triage_v0_52,
)

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_RAW_IDEA_IDS = {
    "prior_day_liquidity_sweep_reversal",
    "london_opening_range_breakout_or_first_candle_direction",
    "asian_range_london_breakout_confirmation",
    "ny_liquidity_sweep_reversal",
    "m15_failed_swing_breakout_reversal",
    "vwap_mean_reversion",
    "atr_exhaustion_reversal",
    "nr7_inside_day_expansion",
    "london_ny_range_extension",
    "weekend_gap_fill",
}


def test_all_required_idea_ids_present_before_deduplication() -> None:
    report = build_xauusd_external_strategy_idea_triage_v0_52()

    assert report["triage_version"] == TRIAGE_VERSION
    assert set(report["raw_idea_ids"]) == REQUIRED_RAW_IDEA_IDS
    assert report["total_raw_ideas"] == 10
    assert len(RAW_IDEAS) == 10


def test_deduplication_keeps_unique_strategy_families() -> None:
    report = build_xauusd_external_strategy_idea_triage_v0_52()
    records = report["idea_records"]
    families = [record["family_id"] for record in records]

    assert report["deduplicated_idea_count"] == len(records)
    assert len(families) == len(set(families))
    assert report["deduplicated_idea_count"] == 8
    assert {item["idea_id"] for item in report["rejected_ideas"]} == {
        "ny_liquidity_sweep_reversal",
        "m15_failed_swing_breakout_reversal",
    }
    assert all(item["duplicate_of"] == "prior_day_liquidity_sweep_reversal" for item in report["rejected_ideas"])


def test_prior_failed_branches_are_considered() -> None:
    report = build_xauusd_external_strategy_idea_triage_v0_52()
    branches = {item["branch_id"]: item for item in report["prior_failed_branches_considered"]}

    assert "xauusd_compression_then_expansion_v0_26" in branches
    assert branches["xauusd_compression_then_expansion_v0_26"]["status"] == "closed_as_execution_path_do_not_retune"
    assert "trend_pullback_continuation_directional_v0_51" in branches
    assert branches["trend_pullback_continuation_directional_v0_51"]["status"] == "expanded_evidence_failed_do_not_promote"


def test_top_ideas_are_mechanical_and_train_validation_safe() -> None:
    report = build_xauusd_external_strategy_idea_triage_v0_52()
    by_id = {record["idea_id"]: record for record in report["idea_records"]}

    assert report["triage_status"] == SHORTLIST_READY
    assert report["top_ranked_idea_id"] == "prior_day_liquidity_sweep_reversal"
    assert report["shortlist_for_v0_53"] == [
        "prior_day_liquidity_sweep_reversal",
        "london_opening_range_breakout_or_first_candle_direction",
        "asian_range_london_breakout_confirmation",
    ]
    for idea_id in report["shortlist_for_v0_53"]:
        scorecard = by_id[idea_id]["scorecard"]
        assert by_id[idea_id]["sufficiently_mechanical_for_v0_53"] is True
        assert scorecard["mechanical_rule_clarity"] >= 4
        assert scorecard["available_data_compatibility"] >= 4
        assert by_id[idea_id]["profitability_claimed"] is False
        assert by_id[idea_id]["backtest_implemented"] is False


def test_scoring_method_has_required_dimensions_and_penalties() -> None:
    report = build_xauusd_external_strategy_idea_triage_v0_52()
    method = report["scoring_method"]

    assert method["dimensions"] == [
        "mechanical_rule_clarity",
        "expected_trade_frequency",
        "xauusd_structural_logic",
        "available_data_compatibility",
        "low_parameterization",
        "difference_from_failed_candidates",
        "oos_safety",
        "implementation_simplicity",
    ]
    assert method["profitability_evidence_used"] is False
    assert method["backtests_run"] is False
    assert "needs_vwap_if_volume_quality_unreliable" in method["penalties_applied_for"]
    assert "requires_arbitrary_thresholds" in method["penalties_applied_for"]


def test_no_oos_retune_threshold_search_parameter_grid_or_execution() -> None:
    report = build_xauusd_external_strategy_idea_triage_v0_52()

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["safety"]["execution_queue_created"] is False
    assert report["safety"]["scheduler_created"] is False
    assert report["safety"]["auto_execute_order"] is False


def test_data_csv_not_staged_or_committed() -> None:
    report = build_xauusd_external_strategy_idea_triage_v0_52()
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
    report_text = json.dumps(build_xauusd_external_strategy_idea_triage_v0_52())

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "profitability_claimed" in report_text


def test_cli_writes_required_report(tmp_path: Path) -> None:
    output_path = tmp_path / "triage.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_external_strategy_idea_triage_v0_52.py"),
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["triage_version"] == TRIAGE_VERSION
    assert output_report["triage_status"] == SHORTLIST_READY
    assert output_report["top_ranked_idea_id"] == "prior_day_liquidity_sweep_reversal"
