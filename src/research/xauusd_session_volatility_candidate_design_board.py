"""v0_55 fixed-rule design board for session and volatility XAUUSD leads.

This board converts the v0_54 descriptive profiler leads into research
hypotheses only. It does not evaluate trades, run OOS, tune parameters, or
create an executable candidate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DESIGN_VERSION = "v0_55"
SOURCE_PROFILER_VERSION = "v0_54"
DEFAULT_OUTPUT = Path("reports") / "xauusd_session_volatility_design_v0_55.json"
DEFAULT_SOURCE_PROFILER = Path("reports") / "xauusd_edge_profiler_v0_54.json"

COMPLETED_WITH_CANDIDATE = "session_volatility_design_completed_with_v0_56_candidate"
COMPLETED_NO_CANDIDATE = "session_volatility_design_completed_no_candidate"
BLOCKED_MISSING_PROFILER = "blocked_missing_v0_54_profiler_report"
DESIGN_FAILED = "design_failed"

ALLOWED_LEADS = ("session_return_profile", "volatility_regime_profile")


def build_xauusd_session_volatility_candidate_design_board_v0_55(
    *,
    source_profiler_path: str | Path = DEFAULT_SOURCE_PROFILER,
) -> dict[str, Any]:
    """Build v0_55 fixed candidate designs from v0_54 top profiler leads."""
    try:
        profiler = _read_json(Path(source_profiler_path))
        blockers = _source_blockers(profiler)
        if blockers:
            return _base_report(
                design_status=BLOCKED_MISSING_PROFILER,
                source_profiler_status=profiler.get("profiler_status") if isinstance(profiler, dict) else None,
                profiler_leads_used=[],
                candidate_designs=[],
                recommended_candidate_for_v0_56=None,
                blockers=blockers,
                warnings=[],
                next_recommended_step="restore reports/xauusd_edge_profiler_v0_54.json before rerunning v0_55",
            )

        assert profiler is not None
        lead_ids = _allowed_top_lead_ids(profiler)
        family_results = {
            result.get("event_family_id"): result
            for result in profiler.get("event_family_results", [])
            if isinstance(result, dict) and result.get("event_family_id") in ALLOWED_LEADS
        }
        designs = _candidate_designs(family_results, lead_ids)
        recommended = _recommended_design(designs)
        status = COMPLETED_WITH_CANDIDATE if recommended is not None else COMPLETED_NO_CANDIDATE
        next_step = (
            f"v0_56 fixed-rule train/validation evaluation for {recommended['candidate_design_id']} only, no OOS"
            if recommended is not None
            else "stop current branch or broaden data/features without OOS"
        )

        return _base_report(
            design_status=status,
            source_profiler_status=profiler.get("profiler_status"),
            profiler_leads_used=lead_ids,
            candidate_designs=designs,
            recommended_candidate_for_v0_56=recommended["candidate_design_id"] if recommended is not None else None,
            blockers=[],
            warnings=_warnings(family_results, lead_ids, designs),
            next_recommended_step=next_step,
        )
    except Exception as exc:
        return _base_report(
            design_status=DESIGN_FAILED,
            source_profiler_status=None,
            profiler_leads_used=[],
            candidate_designs=[],
            recommended_candidate_for_v0_56=None,
            blockers=[f"design_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair v0_55 design-board implementation or source profiler report before continuing",
        )


def save_xauusd_session_volatility_candidate_design_board(
    report: dict[str, Any],
    output: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_report(
    *,
    design_status: str,
    source_profiler_status: str | None,
    profiler_leads_used: list[str],
    candidate_designs: list[dict[str, Any]],
    recommended_candidate_for_v0_56: str | None,
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    return {
        "design_version": DESIGN_VERSION,
        "design_status": design_status,
        "source_profiler_version": SOURCE_PROFILER_VERSION,
        "source_profiler_status": source_profiler_status,
        "profiler_leads_used": profiler_leads_used,
        "candidate_designs": candidate_designs,
        "recommended_candidate_for_v0_56": recommended_candidate_for_v0_56,
        "candidate_design_count": len(candidate_designs),
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "executable_candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "data_csv_added_to_git": False,
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def _candidate_designs(family_results: dict[str, dict[str, Any]], lead_ids: list[str]) -> list[dict[str, Any]]:
    designs: list[dict[str, Any]] = []
    session = family_results.get("session_return_profile")
    volatility = family_results.get("volatility_regime_profile")
    if session is not None and "session_return_profile" in lead_ids:
        designs.append(_session_block_directional_bias_design(session))
        designs.append(_session_transition_continuation_design(session))
    if volatility is not None and "volatility_regime_profile" in lead_ids:
        designs.append(_volatility_regime_session_filter_design(volatility))
        designs.append(_volatility_regime_momentum_design(volatility))
    return designs


def _session_block_directional_bias_design(result: dict[str, Any]) -> dict[str, Any]:
    train = result["train_summary"]
    validation = result["validation_summary"]
    block_id = str(train["dominant_behavior"])
    direction = _direction_from_mean(float(train["dominant_behavior_mean_return_points"]))
    validation_mean = _behavior_mean(validation, block_id, train["primary_horizon"])
    return _design(
        candidate_design_id="session_block_directional_bias_candidate",
        source_lead="session_return_profile",
        market_logic=(
            f"v0_54 found the fixed {block_id} session block had the clearest train session-return bias "
            f"and the same block remained positive in validation ({validation_mean} points)."
        ),
        exact_entry_rule=f"On each train/validation day with a complete {block_id} M15 block, enter once at the first M15 open inside that fixed UTC block.",
        exact_direction_rule=(
            f"Derive direction from train only: if train mean block_return_points for {block_id} is positive use {direction}; "
            f"if negative use short; if zero, reject before testing. Current v0_54 train value implies {direction}."
        ),
        exact_invalidation_rule=(
            f"Invalidate the day if the {block_id} block is incomplete, the first M15 open or final block close is missing, "
            "or the train-derived direction is zero."
        ),
        stop_loss_logic=(
            "Use the opposite edge of the prior completed fixed session block range as the structural stop; "
            "for long use that prior block low, for short use that prior block high. Do not optimize distance."
        ),
        take_profit_or_exit_logic=f"No optimized profit target; exit at the final M15 close inside the same fixed {block_id} block.",
        time_session_filter=f"Only the fixed UTC {block_id} block from v0_54.",
        volatility_filter="None in this design; volatility filters are reserved for separate v0_55 designs.",
        expected_trade_frequency="At most one completed fixed session-block observation per train/validation trading day.",
        minimum_data_required="At least 100 train observations and 50 validation observations for the selected fixed session block.",
        main_failure_modes=[
            "session bias disappears after transaction-cost modeling",
            "validation positive mean is driven by a small number of large days",
            "overnight liquidity or spread conditions make fixed-block entry unrealistic",
        ],
        anti_curve_fit_argument=(
            "The session block is selected from the v0_54 train dominant behavior and checked in validation; "
            "the entry and exit use fixed block boundaries with no session-window or threshold optimization."
        ),
        train_validation_test_plan=(
            "In v0_56, compute train and validation return distribution, adverse excursion to structural stop, "
            "trade count, positive rate, month concentration, and transaction-cost sensitivity using only this fixed design."
        ),
        rejection_metrics=[
            "validation_mean_return_points <= 0",
            "validation_positive_rate < 0.50",
            "validation_trade_count < 50",
            "single_month_trade_share > 0.35",
            "median_return_after_costs <= 0",
        ],
        candidate_design_suitability_score=_score(result, bonus=2),
        recommended_action="promote_to_v0_56_train_validation_test",
    )


def _volatility_regime_session_filter_design(result: dict[str, Any]) -> dict[str, Any]:
    train = result["train_summary"]
    validation = result["validation_summary"]
    train_regime = str(train["dominant_behavior"])
    validation_regime = str(validation["dominant_behavior"])
    direction = _direction_from_mean(float(train["dominant_behavior_mean_return_points"]))
    return _design(
        candidate_design_id="volatility_regime_session_filter_candidate",
        source_lead="volatility_regime_profile",
        market_logic=(
            f"v0_54 showed positive same-day behavior in descriptive volatility buckets, with train strongest in {train_regime} "
            f"and validation strongest in {validation_regime}; this design keeps the bucket definition fixed and descriptive."
        ),
        exact_entry_rule=(
            f"For each train/validation day labeled {train_regime} by the v0_54 daily-range quartile method, "
            "enter at the first available M15 open of the day."
        ),
        exact_direction_rule=(
            f"Use train only: if mean same_day_close_open_points for {train_regime} is positive use {direction}; "
            f"if negative use short; if zero, reject before testing. Do not switch to {validation_regime} after validation review."
        ),
        exact_invalidation_rule=(
            f"Invalidate the day if the fixed descriptive volatility label is not {train_regime}, if a full day open/close is missing, "
            "or if the train-derived direction is zero."
        ),
        stop_loss_logic=(
            "Use the prior completed day's high-low range as a non-optimized structural stop distance from entry; "
            "for long subtract the range, for short add the range."
        ),
        take_profit_or_exit_logic="No optimized target; exit at the last available M15 close of the same UTC day.",
        time_session_filter="Full UTC day; no intraday session chasing.",
        volatility_filter=f"Only the fixed descriptive {train_regime} bucket from v0_54 train dominance.",
        expected_trade_frequency=f"One observation on train/validation days labeled {train_regime}; fewer than daily.",
        minimum_data_required="At least 100 train labeled days and 50 validation labeled days after applying the fixed bucket.",
        main_failure_modes=[
            "train and validation dominant volatility buckets differ",
            "descriptive quartile labels leak if recomputed outside the intended split policy",
            "daily open-to-close behavior is too coarse for executable risk control",
        ],
        anti_curve_fit_argument=(
            "The bucket is the v0_54 train-dominant descriptive label, not an optimized volatility threshold; "
            "the design must keep that label fixed even though validation highlighted a different high-volatility bucket."
        ),
        train_validation_test_plan=(
            "In v0_56, recompute only the predeclared descriptive labels under the existing split policy, "
            "then measure train/validation same-day returns, bucket counts, month concentration, and structural-stop hit rate."
        ),
        rejection_metrics=[
            "validation_mean_return_points <= 0 for the train-selected bucket",
            "validation_labeled_day_count < 50",
            "validation_positive_rate < 0.50",
            "train_validation_bucket_dominance_conflict_remains_material",
            "median_return_after_costs <= 0",
        ],
        candidate_design_suitability_score=_score(result, penalty=4),
        recommended_action="keep_for_observation_only",
    )


def _session_transition_continuation_design(result: dict[str, Any]) -> dict[str, Any]:
    train = result["train_summary"]
    dominant = str(train["dominant_behavior"])
    direction = _direction_from_mean(float(train["dominant_behavior_mean_return_points"]))
    return _design(
        candidate_design_id="session_transition_continuation_candidate",
        source_lead="session_return_profile",
        market_logic=(
            f"v0_54 suggests fixed session behavior matters; this design tests whether the {dominant} bias continues "
            "into the next predeclared session block without using intraday signal chasing."
        ),
        exact_entry_rule=(
            f"When the fixed {dominant} block closes in the train-derived direction, enter at the first M15 open of the next fixed session block."
        ),
        exact_direction_rule=(
            f"Use the same train-derived direction as the {dominant} block: {direction} for current v0_54 evidence; "
            "if the selected session mean is zero, reject before testing."
        ),
        exact_invalidation_rule=(
            "Invalidate if either the source session block or the next fixed session block is incomplete, "
            "or if the source session block closes against the train-derived direction."
        ),
        stop_loss_logic=(
            "Use the completed source session block's opposite extreme as the structural stop; "
            "for long use the source block low, for short use the source block high."
        ),
        take_profit_or_exit_logic="No optimized target; exit at the final M15 close of the next fixed session block.",
        time_session_filter=f"Transition from fixed {dominant} to its next fixed UTC session block only.",
        volatility_filter="None in this design.",
        expected_trade_frequency="Less than daily; only days where the source block closes in the fixed train-derived direction.",
        minimum_data_required="At least 100 train transitions and 50 validation transitions after the fixed close-direction condition.",
        main_failure_modes=[
            "continuation is weaker than same-session return",
            "entry after the source block captures exhausted movement",
            "transition sample is smaller and more concentrated than the base session design",
        ],
        anti_curve_fit_argument=(
            "The source and destination blocks are fixed from the v0_54 session map; no transition pair, threshold, "
            "or stop/exit distance is searched."
        ),
        train_validation_test_plan=(
            "In v0_56 only if the primary session design is not selected, compute fixed transition counts, "
            "return distribution, stop interaction, month concentration, and validation consistency."
        ),
        rejection_metrics=[
            "validation_transition_count < 50",
            "validation_mean_return_points <= 0",
            "validation_positive_rate < 0.50",
            "single_month_trade_share > 0.35",
            "underperforms session_block_directional_bias_candidate",
        ],
        candidate_design_suitability_score=max(_score(result, penalty=3), 0),
        recommended_action="keep_for_observation_only",
    )


def _volatility_regime_momentum_design(result: dict[str, Any]) -> dict[str, Any]:
    train = result["train_summary"]
    regime = str(train["dominant_behavior"])
    direction = _direction_from_mean(float(train["dominant_behavior_mean_return_points"]))
    return _design(
        candidate_design_id="volatility_regime_momentum_candidate",
        source_lead="volatility_regime_profile",
        market_logic=(
            f"v0_54 observed same-day positive momentum in the train-dominant {regime} descriptive volatility regime; "
            "this design tests that single momentum interpretation only."
        ),
        exact_entry_rule=f"On days labeled {regime} by the fixed v0_54 daily-range quartile method, enter at the 12:00 UTC M15 open.",
        exact_direction_rule=(
            f"Momentum only: use {direction} because train same_day_close_open_points for {regime} is positive; "
            "do not switch to mean reversion or a different bucket after validation."
        ),
        exact_invalidation_rule=(
            f"Invalidate if the day is not labeled {regime}, if the 12:00 UTC M15 open is missing, "
            "or if the same-day close required for the fixed exit is missing."
        ),
        stop_loss_logic=(
            "Use half of the prior completed day's high-low range as a fixed descriptive stop distance; "
            "this fraction is predeclared for design review and must not be optimized in v0_56."
        ),
        take_profit_or_exit_logic="No optimized target; exit at the last available M15 close of the same UTC day.",
        time_session_filter="Entry fixed at 12:00 UTC only.",
        volatility_filter=f"Only the fixed descriptive {regime} bucket from v0_54 train dominance.",
        expected_trade_frequency=f"Only train/validation days with {regime} label and a 12:00 UTC M15 candle.",
        minimum_data_required="At least 100 train labeled midday observations and 50 validation labeled midday observations.",
        main_failure_modes=[
            "midday entry is not what the daily open-to-close profiler measured",
            "validation dominance shifted to a different volatility bucket",
            "fixed half-range stop is too coarse without optimization",
        ],
        anti_curve_fit_argument=(
            "Only the momentum interpretation is tested, based on the train sign from v0_54; "
            "mean reversion is not tested in the same candidate and no bucket threshold is searched."
        ),
        train_validation_test_plan=(
            "In v0_56 only after the recommended design, measure the fixed midday momentum rule on train/validation rows, "
            "including labeled-day counts, stop interaction, and validation sign consistency."
        ),
        rejection_metrics=[
            "validation_labeled_midday_count < 50",
            "validation_mean_return_points <= 0",
            "validation_positive_rate < 0.50",
            "train_validation_bucket_dominance_conflict_remains_material",
            "median_return_after_costs <= 0",
        ],
        candidate_design_suitability_score=max(_score(result, penalty=5), 0),
        recommended_action="keep_for_observation_only",
    )


def _design(**values: Any) -> dict[str, Any]:
    return values


def _recommended_design(designs: list[dict[str, Any]]) -> dict[str, Any] | None:
    promoted = [design for design in designs if design["recommended_action"] == "promote_to_v0_56_train_validation_test"]
    if not promoted:
        return None
    return max(promoted, key=lambda item: item["candidate_design_suitability_score"])


def _score(result: dict[str, Any], *, bonus: int = 0, penalty: int = 0) -> int:
    score = int(result.get("candidate_suitability_score", {}).get("total_score", 0)) + bonus - penalty
    return max(min(score, 35), 0)


def _behavior_mean(summary: dict[str, Any], behavior: str, horizon: str) -> float | None:
    behavior_summary = summary.get("behavior_summaries", {}).get(behavior, {})
    value = behavior_summary.get("mean_return_points_by_horizon", {}).get(horizon)
    return float(value) if value is not None else None


def _direction_from_mean(value: float) -> str:
    if value > 0.0:
        return "long"
    if value < 0.0:
        return "short"
    return "none"


def _allowed_top_lead_ids(profiler: dict[str, Any]) -> list[str]:
    lead_ids: list[str] = []
    for lead in profiler.get("strongest_empirical_leads", []):
        if not isinstance(lead, dict):
            continue
        lead_id = lead.get("event_family_id")
        if lead_id in ALLOWED_LEADS and lead_id not in lead_ids:
            lead_ids.append(str(lead_id))
    return lead_ids


def _warnings(family_results: dict[str, dict[str, Any]], lead_ids: list[str], designs: list[dict[str, Any]]) -> list[str]:
    warnings = [
        "design_board_only_no_train_validation_metrics_computed",
        "v0_56_must_evaluate_recommended_candidate_only_before_any_new_branch",
    ]
    if set(lead_ids) != set(ALLOWED_LEADS):
        warnings.append("not_all_allowed_v0_54_top_leads_available")
    volatility = family_results.get("volatility_regime_profile")
    if volatility is not None and "dominant_behavior_differs_between_train_validation" in volatility.get("stability_notes", []):
        warnings.append("volatility_regime_train_validation_dominant_bucket_differs")
    if len([d for d in designs if d["recommended_action"] == "promote_to_v0_56_train_validation_test"]) > 1:
        warnings.append("multiple_promoted_designs_present_review_required")
    return warnings


def _source_blockers(profiler: dict[str, Any] | None) -> list[str]:
    if profiler is None:
        return ["source_v0_54_profiler_report_missing_or_invalid"]
    blockers: list[str] = []
    if profiler.get("profiler_version") != SOURCE_PROFILER_VERSION:
        blockers.append("source_profiler_version_mismatch")
    if profiler.get("profiler_status") != "edge_profile_completed_with_research_leads":
        blockers.append("source_profiler_status_not_completed_with_research_leads")
    if profiler.get("train_validation_only") is not True:
        blockers.append("source_profiler_train_validation_only_not_true")
    if profiler.get("oos_used") is not False:
        blockers.append("source_profiler_oos_state_invalid")
    lead_ids = _allowed_top_lead_ids(profiler)
    if not lead_ids:
        blockers.append("source_profiler_allowed_top_leads_missing")
    return blockers


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "design_board_only": True,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "executable_candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "user_facing_trade_recommendation": False,
    }
