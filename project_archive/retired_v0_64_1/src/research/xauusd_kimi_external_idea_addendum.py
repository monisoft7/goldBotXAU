"""v0_52_1 Kimi external idea addendum for the v0_52 XAUUSD triage board."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.research.xauusd_external_strategy_idea_triage import (
    DEFAULT_OUTPUT as V0_52_OUTPUT,
    SCORING_DIMENSIONS,
)

ADDENDUM_VERSION = "v0_52_1"
DEFAULT_OUTPUT = Path("reports") / "xauusd_kimi_external_idea_addendum_v0_52_1.json"

SHORTLIST_UNCHANGED = "kimi_addendum_completed_shortlist_unchanged"
SHORTLIST_UPDATED = "kimi_addendum_completed_shortlist_updated"
FAILED_MISSING_V0_52 = "kimi_addendum_failed_missing_v0_52_report"
FAILED = "kimi_addendum_failed"


@dataclass(frozen=True)
class KimiIdea:
    idea_id: str
    family_id: str
    description: str
    disposition: str
    overlaps_with: tuple[str, ...] = ()
    penalty_notes: tuple[str, ...] = ()
    scores: dict[str, int] | None = None


KIMI_IDEAS = (
    KimiIdea(
        idea_id="opening_range_breakout_with_momentum_confirmation",
        family_id="london_opening_range_direction",
        description="Opening range breakout with fixed momentum confirmation.",
        disposition="deduplicated_overlap",
        overlaps_with=("london_opening_range_breakout_or_first_candle_direction",),
        penalty_notes=("overlaps_with_existing_v0_52_london_opening_range_family",),
    ),
    KimiIdea(
        idea_id="mean_reversion_after_extended_sequential_moves",
        family_id="sequential_move_mean_reversion",
        description="Fixed sequence of same-direction M5 closes followed by a reversal response.",
        disposition="new_scored_idea",
        penalty_notes=("penalized_for_sequence_length_threshold_sensitivity",),
        scores={
            "mechanical_rule_clarity": 4,
            "expected_trade_frequency": 4,
            "xauusd_structural_logic": 3,
            "available_data_compatibility": 5,
            "low_parameterization": 3,
            "difference_from_failed_candidates": 4,
            "oos_safety": 5,
            "implementation_simplicity": 4,
        },
    ),
    KimiIdea(
        idea_id="london_close_or_asian_liquidity_sweep",
        family_id="asian_range_london_breakout",
        description="London close or Asian liquidity sweep variant.",
        disposition="deduplicated_overlap",
        overlaps_with=("asian_range_london_breakout_confirmation", "prior_day_liquidity_sweep_reversal"),
        penalty_notes=("overlaps_with_existing_asian_range_and_liquidity_sweep_families",),
    ),
    KimiIdea(
        idea_id="range_contraction_expansion_with_close_bias",
        family_id="compression_expansion_close_bias",
        description="Range contraction/expansion with explicit close-location directional bias.",
        disposition="penalized_scored_idea",
        overlaps_with=("xauusd_compression_then_expansion_v0_26",),
        penalty_notes=(
            "penalized_similarity_to_failed_v0_26_compression_expansion_branch",
            "explicit_close_location_direction_is_distinct_but_not_enough_to_displace_v0_52_top_three",
        ),
        scores={
            "mechanical_rule_clarity": 4,
            "expected_trade_frequency": 4,
            "xauusd_structural_logic": 4,
            "available_data_compatibility": 5,
            "low_parameterization": 3,
            "difference_from_failed_candidates": 2,
            "oos_safety": 5,
            "implementation_simplicity": 4,
        },
    ),
    KimiIdea(
        idea_id="ny_session_first_hour_continuation",
        family_id="london_ny_range_extension",
        description="NY session first-hour continuation idea.",
        disposition="deduplicated_overlap",
        overlaps_with=("london_ny_range_extension",),
        penalty_notes=("overlaps_with_existing_range_extension_and_first_hour_family",),
    ),
    KimiIdea(
        idea_id="gap_fill_failure",
        family_id="weekend_gap_fill",
        description="Weekend gap fill failure variant.",
        disposition="penalized_overlap",
        overlaps_with=("weekend_gap_fill",),
        penalty_notes=("related_to_weekend_gap_family", "penalized_low_sample_frequency"),
    ),
    KimiIdea(
        idea_id="vwap_deviation_reversion",
        family_id="vwap_mean_reversion",
        description="VWAP deviation reversion variant.",
        disposition="penalized_overlap",
        overlaps_with=("vwap_mean_reversion",),
        penalty_notes=("penalized_vwap_volume_quality_uncertain", "overlaps_with_existing_vwap_mean_reversion_family"),
    ),
    KimiIdea(
        idea_id="three_candle_body_confirmation_reversal",
        family_id="generic_candle_pattern_reversal",
        description="Three-candle body confirmation reversal.",
        disposition="penalized_scored_idea",
        penalty_notes=("penalized_generic_candle_pattern_mining_risk", "penalized_noisy_high_frequency_pattern"),
        scores={
            "mechanical_rule_clarity": 3,
            "expected_trade_frequency": 4,
            "xauusd_structural_logic": 2,
            "available_data_compatibility": 5,
            "low_parameterization": 2,
            "difference_from_failed_candidates": 3,
            "oos_safety": 5,
            "implementation_simplicity": 4,
        },
    ),
    KimiIdea(
        idea_id="higher_timeframe_alignment_pullback",
        family_id="trend_pullback_alignment",
        description="Higher-timeframe alignment with pullback continuation.",
        disposition="penalized_scored_idea",
        overlaps_with=("trend_pullback_continuation_directional_v0_51",),
        penalty_notes=(
            "penalized_similarity_to_failed_v0_48_v0_51_trend_pullback_branch",
            "requires_materially_different_fixed_rule_before_future_consideration",
        ),
        scores={
            "mechanical_rule_clarity": 3,
            "expected_trade_frequency": 3,
            "xauusd_structural_logic": 4,
            "available_data_compatibility": 4,
            "low_parameterization": 2,
            "difference_from_failed_candidates": 1,
            "oos_safety": 5,
            "implementation_simplicity": 2,
        },
    ),
    KimiIdea(
        idea_id="friday_range_extension_reversal",
        family_id="friday_range_extension_reversal",
        description="Friday range extension reversal.",
        disposition="penalized_scored_idea",
        penalty_notes=("penalized_low_frequency", "penalized_friday_concentration_risk"),
        scores={
            "mechanical_rule_clarity": 4,
            "expected_trade_frequency": 1,
            "xauusd_structural_logic": 3,
            "available_data_compatibility": 5,
            "low_parameterization": 4,
            "difference_from_failed_candidates": 4,
            "oos_safety": 5,
            "implementation_simplicity": 4,
        },
    ),
)


def build_xauusd_kimi_external_idea_addendum_v0_52_1(
    source_report_path: str | Path = V0_52_OUTPUT,
) -> dict[str, Any]:
    """Build the Kimi addendum without changing the completed v0_52 report."""
    source_path = Path(source_report_path)
    if not source_path.exists():
        return _failed_missing_source_report(source_path)

    try:
        source = json.loads(source_path.read_text(encoding="utf-8"))
        original_shortlist = list(source.get("shortlist_for_v0_53", []))
        source_records = list(source.get("idea_records", []))
        source_by_id = {str(record.get("idea_id")): record for record in source_records}
        sources = _sources_with_kimi(source.get("external_sources_considered", []))

        kimi_records = [_kimi_record(idea) for idea in KIMI_IDEAS]
        scored_kimi = [record for record in kimi_records if record["scorecard"]]
        candidate_pool = _combined_candidate_pool(source_records, scored_kimi)
        updated_shortlist = [record["idea_id"] for record in candidate_pool if record["sufficiently_mechanical_for_v0_53"]][:3]
        changed = updated_shortlist != original_shortlist
        final_shortlist = updated_shortlist if changed else original_shortlist
        status = SHORTLIST_UPDATED if changed else SHORTLIST_UNCHANGED
        top_ranked = candidate_pool[0]["idea_id"] if candidate_pool else source.get("top_ranked_idea_id")

        return {
            "addendum_version": ADDENDUM_VERSION,
            "addendum_status": status,
            "source_triage_version": source.get("triage_version"),
            "external_sources_considered": sources,
            "kimi_added_to_external_sources": "kimi" in sources,
            "kimi_raw_idea_count": len(KIMI_IDEAS),
            "kimi_deduplicated_idea_count": sum(1 for idea in KIMI_IDEAS if not idea.disposition.endswith("overlap")),
            "kimi_raw_idea_ids": [idea.idea_id for idea in KIMI_IDEAS],
            "kimi_idea_records": kimi_records,
            "kimi_rejected_or_penalized_ideas": [
                record for record in kimi_records if record["disposition"] != "new_scored_idea"
            ],
            "original_v0_52_shortlist": original_shortlist,
            "final_shortlist_for_v0_53": final_shortlist[:3],
            "shortlist_changed": changed,
            "shortlist_change_reason": _shortlist_change_reason(changed, final_shortlist, source_by_id, scored_kimi),
            "top_ranked_idea_id": top_ranked,
            "scoring_method": source.get("scoring_method"),
            "scoring_method_preserved": True,
            "train_validation_only": True,
            "oos_used": False,
            "repeated_oos_review": False,
            "retune_performed": False,
            "threshold_search_performed": False,
            "parameter_grid_performed": False,
            "backtest_implemented": False,
            "candidate_created": False,
            "demo_execution_allowed": False,
            "order_send_called": False,
            "order_check_called": False,
            "live_allowed": False,
            "data_csv_added_to_git": False,
            "blockers": [],
            "warnings": [
                "kimi_ideas_are_external_hypotheses_not_profitability_evidence",
                "v0_52_report_left_unchanged_by_addendum",
                "final_shortlist_remains_capped_at_three",
            ],
            "next_recommended_step": "use the unchanged v0_52 shortlist for v0_53 fixed-rule train/validation-only board design; keep Kimi addendum ideas as supplemental do-not-retune-aware notes",
            "safety": _safety_flags(),
        }
    except Exception as exc:
        report = _failed_missing_source_report(source_path)
        report["addendum_status"] = FAILED
        report["blockers"] = [f"addendum_exception:{type(exc).__name__}:{exc}"]
        report["warnings"] = []
        report["next_recommended_step"] = "repair v0_52_1 addendum implementation before using Kimi ideas"
        return report


def save_xauusd_kimi_external_idea_addendum(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _kimi_record(idea: KimiIdea) -> dict[str, Any]:
    scores = dict(idea.scores or {})
    total_score = sum(scores.get(dimension, 0) for dimension in SCORING_DIMENSIONS)
    sufficiently_mechanical = bool(
        scores
        and scores["mechanical_rule_clarity"] >= 4
        and scores["available_data_compatibility"] >= 4
        and scores["low_parameterization"] >= 4
        and total_score >= 32
    )
    return {
        "idea_id": idea.idea_id,
        "source": "kimi",
        "family_id": idea.family_id,
        "description": idea.description,
        "disposition": idea.disposition,
        "overlaps_with": list(idea.overlaps_with),
        "scorecard": scores,
        "total_score": total_score if scores else None,
        "rank_score": total_score if scores else None,
        "sufficiently_mechanical_for_v0_53": sufficiently_mechanical,
        "penalty_notes": list(idea.penalty_notes),
        "profitability_claimed": False,
        "backtest_implemented": False,
        "candidate_created": False,
    }


def _combined_candidate_pool(
    source_records: list[dict[str, Any]],
    scored_kimi: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = [
        {
            "idea_id": record["idea_id"],
            "total_score": int(record["total_score"]),
            "scorecard": record["scorecard"],
            "sufficiently_mechanical_for_v0_53": bool(record["sufficiently_mechanical_for_v0_53"]),
            "source": "v0_52",
        }
        for record in source_records
    ] + [
        {
            "idea_id": record["idea_id"],
            "total_score": int(record["total_score"]),
            "scorecard": record["scorecard"],
            "sufficiently_mechanical_for_v0_53": bool(record["sufficiently_mechanical_for_v0_53"]),
            "source": "kimi",
        }
        for record in scored_kimi
        if record["total_score"] is not None
    ]
    return sorted(combined, key=_sort_key, reverse=True)


def _sort_key(record: dict[str, Any]) -> tuple[int, int, int, int, str]:
    scorecard = record["scorecard"]
    return (
        int(record["total_score"]),
        int(scorecard["mechanical_rule_clarity"]),
        int(scorecard["xauusd_structural_logic"]),
        int(scorecard["low_parameterization"]),
        str(record["idea_id"]),
    )


def _shortlist_change_reason(
    changed: bool,
    final_shortlist: list[str],
    source_by_id: dict[str, dict[str, Any]],
    scored_kimi: list[dict[str, Any]],
) -> str:
    if changed:
        return f"kimi_idea_materially_ranked_into_top_three:{final_shortlist}"
    best_kimi = max((record for record in scored_kimi if record["total_score"] is not None), key=_sort_key)
    weakest_original = min((source_by_id[item] for item in final_shortlist), key=_sort_key)
    return (
        f"unchanged: best_kimi={best_kimi['idea_id']} score={best_kimi['total_score']} "
        f"did_not_materially_beat_weakest_v0_52_shortlist={weakest_original['idea_id']} "
        f"score={weakest_original['total_score']}"
    )


def _sources_with_kimi(sources: Any) -> list[str]:
    values = [str(source) for source in sources] if isinstance(sources, list) else []
    if "kimi" not in values:
        values.append("kimi")
    return values


def _failed_missing_source_report(source_path: Path) -> dict[str, Any]:
    return {
        "addendum_version": ADDENDUM_VERSION,
        "addendum_status": FAILED_MISSING_V0_52,
        "source_triage_version": None,
        "external_sources_considered": ["kimi"],
        "kimi_added_to_external_sources": True,
        "kimi_raw_idea_count": len(KIMI_IDEAS),
        "kimi_deduplicated_idea_count": 0,
        "kimi_idea_records": [],
        "kimi_rejected_or_penalized_ideas": [],
        "original_v0_52_shortlist": [],
        "final_shortlist_for_v0_53": [],
        "shortlist_changed": False,
        "shortlist_change_reason": "missing_v0_52_report",
        "top_ranked_idea_id": None,
        "scoring_method_preserved": True,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "backtest_implemented": False,
        "candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "data_csv_added_to_git": False,
        "blockers": [f"missing_v0_52_report:{source_path.as_posix()}"],
        "warnings": [],
        "next_recommended_step": "restore reports/xauusd_external_strategy_idea_triage_v0_52.json before running v0_52_1",
        "safety": _safety_flags(),
    }


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "triage_supplement_only": True,
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
