"""v0_52 research-only external XAUUSD strategy idea intake and triage board."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TRIAGE_VERSION = "v0_52"
DEFAULT_OUTPUT = Path("reports") / "xauusd_external_strategy_idea_triage_v0_52.json"

SHORTLIST_READY = "shortlist_ready_for_v0_53_non_oos_board"
INSUFFICIENT_IDEAS = "insufficient_external_ideas_after_triage"

EXTERNAL_SOURCES_CONSIDERED = ["Claude", "DeepSeek", "Gemini", "GLM", "Perplexity", "Qwen/QwinMax"]

SCORING_DIMENSIONS = (
    "mechanical_rule_clarity",
    "expected_trade_frequency",
    "xauusd_structural_logic",
    "available_data_compatibility",
    "low_parameterization",
    "difference_from_failed_candidates",
    "oos_safety",
    "implementation_simplicity",
)

PRIOR_FAILED_BRANCHES_CONSIDERED = (
    {
        "branch_id": "xauusd_atr_impulse_reversion_v0_7",
        "status": "rejected_do_not_retune",
        "triage_note": "ATR impulse/exhaustion reversal ideas are penalized for resemblance and threshold risk.",
    },
    {
        "branch_id": "xauusd_multi_bar_exhaustion_reversion_v0_8",
        "status": "rejected_do_not_retune",
        "triage_note": "Exhaustion reversal variants are not treated as fresh evidence.",
    },
    {
        "branch_id": "session_volatility_expansion_v0_11",
        "status": "rejected_do_not_retune",
        "triage_note": "Session expansion concepts must avoid retuning this failed branch.",
    },
    {
        "branch_id": "low_atr_range_expansion_followthrough_v0_14",
        "status": "rejected_do_not_retune",
        "triage_note": "Range expansion ideas are penalized if they require threshold search.",
    },
    {
        "branch_id": "low_atr_x_hour_16_v0_17",
        "status": "rejected_do_not_retune",
        "triage_note": "Single-hour or low-ATR variants are not retuned.",
    },
    {
        "branch_id": "xauusd_spike_fixed_candidate_v0_23",
        "status": "rejected_do_not_retune",
        "triage_note": "Spike/exhaustion reversal concepts are treated cautiously.",
    },
    {
        "branch_id": "xauusd_compression_then_expansion_v0_26",
        "status": "closed_as_execution_path_do_not_retune",
        "triage_note": "Locked compression-expansion evidence remains historical and is not modified.",
    },
    {
        "branch_id": "trend_pullback_continuation_directional_v0_51",
        "status": "expanded_evidence_failed_do_not_promote",
        "triage_note": "Trend-pullback continuation is preserved as failed expanded evidence.",
    },
)


@dataclass(frozen=True)
class RawIdea:
    idea_id: str
    family_id: str
    description: str
    source_model_notes: tuple[str, ...]
    primary: bool = True
    duplicate_of: str | None = None
    duplicate_reason: str | None = None


RAW_IDEAS = (
    RawIdea(
        idea_id="prior_day_liquidity_sweep_reversal",
        family_id="liquidity_sweep_reversal",
        description="Sweep previous day high or low, close back inside the prior-day range, then study a fixed reversal response.",
        source_model_notes=("prior_day_reference", "close_back_inside_required", "mechanical_reversal_template"),
    ),
    RawIdea(
        idea_id="london_opening_range_breakout_or_first_candle_direction",
        family_id="london_opening_range_direction",
        description="Use the London 07:00 UTC first 15m/30m candle or opening range as a fixed directional setup.",
        source_model_notes=("london_open_reference", "fixed_time_window", "range_or_first_candle_variant"),
    ),
    RawIdea(
        idea_id="asian_range_london_breakout_confirmation",
        family_id="asian_range_london_breakout",
        description="Build the Asian high/low range, then require a London M15 close outside that range.",
        source_model_notes=("asian_range_reference", "london_close_confirmation", "mechanical_range_breakout"),
    ),
    RawIdea(
        idea_id="ny_liquidity_sweep_reversal",
        family_id="liquidity_sweep_reversal",
        description="Sweep the 00:00-12:00 range during the NY window and close back inside.",
        source_model_notes=("ny_window_reference", "close_back_inside_required"),
        primary=False,
        duplicate_of="prior_day_liquidity_sweep_reversal",
        duplicate_reason="same sweep-and-close-back-inside reversal family; time window can be a future variant after primary family testing",
    ),
    RawIdea(
        idea_id="m15_failed_swing_breakout_reversal",
        family_id="liquidity_sweep_reversal",
        description="Break a prior M15 swing high or low, then close back inside for a reversal study.",
        source_model_notes=("m15_swing_reference", "failed_breakout_reversal"),
        primary=False,
        duplicate_of="prior_day_liquidity_sweep_reversal",
        duplicate_reason="same failed breakout/liquidity sweep reversal family with a more discretionary swing definition",
    ),
    RawIdea(
        idea_id="vwap_mean_reversion",
        family_id="vwap_mean_reversion",
        description="Study stretch from session VWAP followed by a close back inside a fixed band.",
        source_model_notes=("session_vwap", "band_reentry", "volume_quality_dependency"),
    ),
    RawIdea(
        idea_id="atr_exhaustion_reversal",
        family_id="atr_exhaustion_reversal",
        description="Unusually large M15 candle followed by an opposite confirmation candle.",
        source_model_notes=("large_m15_candle", "opposite_confirmation", "threshold_sensitive"),
    ),
    RawIdea(
        idea_id="nr7_inside_day_expansion",
        family_id="nr7_inside_day_expansion",
        description="NR7 or inside-day breakout with fixed direction logic.",
        source_model_notes=("daily_compression", "fixed_breakout", "low_frequency"),
    ),
    RawIdea(
        idea_id="london_ny_range_extension",
        family_id="london_ny_range_extension",
        description="NY break of the London range with fixed range and confirmation definitions.",
        source_model_notes=("london_range_reference", "ny_extension_window"),
    ),
    RawIdea(
        idea_id="weekend_gap_fill",
        family_id="weekend_gap_fill",
        description="Weekend gap reversion toward the prior Friday close.",
        source_model_notes=("friday_close_reference", "monday_gap", "low_frequency"),
    ),
)

PRIMARY_IDEA_SCORES: dict[str, dict[str, int]] = {
    "prior_day_liquidity_sweep_reversal": {
        "mechanical_rule_clarity": 5,
        "expected_trade_frequency": 4,
        "xauusd_structural_logic": 5,
        "available_data_compatibility": 5,
        "low_parameterization": 5,
        "difference_from_failed_candidates": 4,
        "oos_safety": 5,
        "implementation_simplicity": 5,
    },
    "london_opening_range_breakout_or_first_candle_direction": {
        "mechanical_rule_clarity": 5,
        "expected_trade_frequency": 5,
        "xauusd_structural_logic": 4,
        "available_data_compatibility": 5,
        "low_parameterization": 5,
        "difference_from_failed_candidates": 4,
        "oos_safety": 5,
        "implementation_simplicity": 4,
    },
    "asian_range_london_breakout_confirmation": {
        "mechanical_rule_clarity": 5,
        "expected_trade_frequency": 4,
        "xauusd_structural_logic": 5,
        "available_data_compatibility": 5,
        "low_parameterization": 4,
        "difference_from_failed_candidates": 4,
        "oos_safety": 5,
        "implementation_simplicity": 4,
    },
    "vwap_mean_reversion": {
        "mechanical_rule_clarity": 4,
        "expected_trade_frequency": 4,
        "xauusd_structural_logic": 4,
        "available_data_compatibility": 2,
        "low_parameterization": 2,
        "difference_from_failed_candidates": 4,
        "oos_safety": 5,
        "implementation_simplicity": 2,
    },
    "atr_exhaustion_reversal": {
        "mechanical_rule_clarity": 3,
        "expected_trade_frequency": 3,
        "xauusd_structural_logic": 3,
        "available_data_compatibility": 5,
        "low_parameterization": 2,
        "difference_from_failed_candidates": 1,
        "oos_safety": 5,
        "implementation_simplicity": 4,
    },
    "nr7_inside_day_expansion": {
        "mechanical_rule_clarity": 4,
        "expected_trade_frequency": 2,
        "xauusd_structural_logic": 3,
        "available_data_compatibility": 4,
        "low_parameterization": 4,
        "difference_from_failed_candidates": 3,
        "oos_safety": 5,
        "implementation_simplicity": 3,
    },
    "london_ny_range_extension": {
        "mechanical_rule_clarity": 4,
        "expected_trade_frequency": 4,
        "xauusd_structural_logic": 4,
        "available_data_compatibility": 5,
        "low_parameterization": 4,
        "difference_from_failed_candidates": 3,
        "oos_safety": 5,
        "implementation_simplicity": 4,
    },
    "weekend_gap_fill": {
        "mechanical_rule_clarity": 5,
        "expected_trade_frequency": 1,
        "xauusd_structural_logic": 3,
        "available_data_compatibility": 3,
        "low_parameterization": 4,
        "difference_from_failed_candidates": 5,
        "oos_safety": 5,
        "implementation_simplicity": 3,
    },
}

PENALTY_NOTES: dict[str, list[str]] = {
    "vwap_mean_reversion": [
        "penalized_needs_vwap_and_volume_quality_validation",
        "penalized_band_definition_can_become_arbitrary_threshold",
    ],
    "atr_exhaustion_reversal": [
        "penalized_resembles_failed_exhaustion_reversal_branches",
        "penalized_large_candle_definition_requires_threshold_discipline",
    ],
    "nr7_inside_day_expansion": ["penalized_low_trade_frequency"],
    "weekend_gap_fill": ["penalized_too_low_trade_frequency"],
    "london_ny_range_extension": ["penalized_overlap_with_range_expansion_failed_branches"],
}


def build_xauusd_external_strategy_idea_triage_v0_52() -> dict[str, Any]:
    """Build a deterministic intake board for external ideas without evaluating performance."""
    raw_ideas = [_raw_idea_record(idea) for idea in RAW_IDEAS]
    idea_records = [_idea_record(idea) for idea in RAW_IDEAS if idea.primary]
    rejected_ideas = [_rejected_idea_record(idea) for idea in RAW_IDEAS if not idea.primary]
    ranked = sorted(idea_records, key=_idea_sort_key, reverse=True)
    shortlist = [record["idea_id"] for record in ranked if record["sufficiently_mechanical_for_v0_53"]][:3]
    status = SHORTLIST_READY if len(shortlist) >= 3 else INSUFFICIENT_IDEAS
    top = ranked[0]["idea_id"] if ranked else None

    return {
        "triage_version": TRIAGE_VERSION,
        "triage_status": status,
        "external_sources_considered": list(EXTERNAL_SOURCES_CONSIDERED),
        "total_raw_ideas": len(raw_ideas),
        "deduplicated_idea_count": len(idea_records),
        "raw_idea_ids": [idea["idea_id"] for idea in raw_ideas],
        "idea_records": idea_records,
        "rejected_ideas": rejected_ideas,
        "shortlist_for_v0_53": shortlist,
        "top_ranked_idea_id": top,
        "scoring_method": _scoring_method(),
        "prior_failed_branches_considered": [dict(item) for item in PRIOR_FAILED_BRANCHES_CONSIDERED],
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "data_csv_added_to_git": False,
        "blockers": [],
        "warnings": [
            "external_model_ideas_are_hypotheses_not_profitability_evidence",
            "shortlist_is_for_future_train_validation_board_design_only",
            "deduplicated_sweep_variants_require_one_primary_family_test_before_variants",
        ],
        "next_recommended_step": "design v0_53 fixed-rule train/validation-only board for the shortlisted ideas; no OOS, retune, threshold search, parameter grid, or execution",
        "safety": _safety_flags(),
    }


def save_xauusd_external_strategy_idea_triage(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _raw_idea_record(idea: RawIdea) -> dict[str, Any]:
    return {
        "idea_id": idea.idea_id,
        "family_id": idea.family_id,
        "description": idea.description,
        "source_model_notes": list(idea.source_model_notes),
        "primary_after_deduplication": idea.primary,
        "duplicate_of": idea.duplicate_of,
        "duplicate_reason": idea.duplicate_reason,
    }


def _idea_record(idea: RawIdea) -> dict[str, Any]:
    scores = PRIMARY_IDEA_SCORES[idea.idea_id]
    total_score = sum(scores[dimension] for dimension in SCORING_DIMENSIONS)
    sufficiently_mechanical = (
        scores["mechanical_rule_clarity"] >= 4
        and scores["available_data_compatibility"] >= 4
        and scores["low_parameterization"] >= 4
        and total_score >= 32
    )
    return {
        "idea_id": idea.idea_id,
        "family_id": idea.family_id,
        "description": idea.description,
        "deduplication_status": "primary_unique_strategy_family",
        "source_model_notes": list(idea.source_model_notes),
        "scorecard": dict(scores),
        "total_score": total_score,
        "rank_score": total_score,
        "sufficiently_mechanical_for_v0_53": sufficiently_mechanical,
        "profitability_claimed": False,
        "backtest_implemented": False,
        "candidate_created": False,
        "penalty_notes": PENALTY_NOTES.get(idea.idea_id, []),
    }


def _rejected_idea_record(idea: RawIdea) -> dict[str, Any]:
    return {
        "idea_id": idea.idea_id,
        "family_id": idea.family_id,
        "rejection_status": "deduplicated_variant_not_shortlisted",
        "duplicate_of": idea.duplicate_of,
        "reason": idea.duplicate_reason,
        "profitability_claimed": False,
        "backtest_implemented": False,
    }


def _idea_sort_key(record: dict[str, Any]) -> tuple[int, int, int, int, str]:
    scorecard = record["scorecard"]
    return (
        int(record["total_score"]),
        int(scorecard["mechanical_rule_clarity"]),
        int(scorecard["xauusd_structural_logic"]),
        int(scorecard["low_parameterization"]),
        str(record["idea_id"]),
    )


def _scoring_method() -> dict[str, Any]:
    return {
        "score_range": "0_to_5_each_dimension",
        "dimensions": list(SCORING_DIMENSIONS),
        "total_score_max": 40,
        "sufficiently_mechanical_rule": (
            "mechanical_rule_clarity>=4, available_data_compatibility>=4, "
            "low_parameterization>=4, and total_score>=32"
        ),
        "penalties_applied_for": [
            "needs_vwap_if_volume_quality_unreliable",
            "too_low_trade_frequency",
            "resembles_failed_branch_too_closely",
            "requires_arbitrary_thresholds",
            "requires_external_news_calendar",
            "relies_on_vague_discretionary_smc_language",
        ],
        "profitability_evidence_used": False,
        "backtests_run": False,
    }


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "strategy_evaluation": False,
        "backtest_implemented": False,
        "candidate_created": False,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
        "trade_recommendation_output_present": False,
        "data_csv_added_to_git": False,
    }
