"""Static research candidate registry for safe handoffs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

REGISTRY_VERSION = "v0_29"

_CANDIDATES: list[dict[str, Any]] = [
    {
        "candidate_id": "null_research_harness_test",
        "status": "harness_test_only",
        "eligible_for_oos_review": False,
    },
    {
        "candidate_id": "xauusd_atr_impulse_reversion_v0_7",
        "status": "rejected",
        "rejection_reason": "validation_gate_failed",
        "oos_status": "locked_not_evaluated",
        "eligible_for_oos_review": False,
        "do_not_retune": True,
    },
    {
        "candidate_id": "xauusd_multi_bar_exhaustion_reversion_v0_8",
        "status": "rejected",
        "rejection_reason": "validation_gate_failed",
        "oos_status": "locked_not_evaluated",
        "eligible_for_oos_review": False,
        "do_not_retune": True,
    },
    {
        "candidate_id": "xauusd_session_volatility_expansion_v0_11",
        "status": "rejected",
        "rejection_reason": "validation_gate_failed",
        "source_profile": "v0_10_train_only_market_profile",
        "oos_status": "locked_not_evaluated",
        "eligible_for_oos_review": False,
        "do_not_retune": True,
    },
    {
        "candidate_id": "xauusd_low_atr_range_expansion_followthrough_v0_14",
        "status": "rejected",
        "rejection_reason": "validation_gate_failed",
        "source_selection_board": "v0_13_strategy_family_selection_board",
        "oos_status": "locked_not_evaluated",
        "eligible_for_oos_review": False,
        "do_not_retune": True,
    },
    {
        "candidate_id": "xauusd_low_atr_x_hour_16_v0_17",
        "status": "rejected",
        "rejection_reason": "validation_gate_failed",
        "source_triage": "v0_16_advisor_idea_triage",
        "oos_status": "locked_not_evaluated",
        "eligible_for_oos_review": False,
        "do_not_retune": True,
    },
    {
        "candidate_id": "xauusd_low_tf_spike_m5_hour_11_fade_v0_23",
        "status": "rejected_train_validation_gate_failed",
        "rejection_reason": "v0_24_fixed_promotion_gate_failed_marginal_train_validation_evidence",
        "source_profile": "xauusd_low_tf_spike_profile_v0_22",
        "fixed_profile_group": {
            "source_timeframe": "M5",
            "spike_size_bucket": "range_to_atr_1_5_to_2_0",
            "session_bucket": "block_06_12",
            "hour_bucket": "11",
            "observed_behavior_label": "fade",
            "forward_horizon_bars": 3,
        },
        "oos_status": "locked_not_evaluated",
        "eligible_for_oos_review": False,
        "research_only": True,
        "do_not_retune": True,
        "threshold_search_used": False,
        "parameter_grid_used": False,
        "retuned_rejected_candidate": False,
        "spike_family_status": "abandoned",
    },
    {
        "candidate_id": "xauusd_compression_then_expansion_v0_26",
        "status": "oos_passed_research_validation_pending_post_oos_protocol",
        "source_atlas": "xauusd_session_structure_atlas_v0_25",
        "source_family": "compression_then_expansion",
        "fixed_rules": {
            "time_basis": "dataset_timestamp_hour_buckets_only",
            "reference_blocks": ["block_00_06", "block_06_12", "block_12_18"],
            "response_blocks": ["block_06_12", "block_12_18", "block_18_24"],
            "forward_behavior_label": "next_block_expansion",
        },
        "oos_status": "evaluated_passed",
        "eligible_for_oos_review": False,
        "human_approval_required_before_oos": False,
        "one_time_oos_review_completed": True,
        "repeat_oos_review_allowed": False,
        "research_only": True,
        "threshold_search_used": False,
        "parameter_grid_used": False,
        "retuned_rejected_candidate": False,
        "v0_27_gate_decision": "promote_to_oos_review_candidate_pending_human_approval",
        "v0_29_oos_decision": "oos_passed_research_validation",
    },
]


def _is_rejected_status(status: str) -> bool:
    return status == "rejected" or status.startswith("rejected_")


def research_candidate_registry() -> dict[str, Any]:
    candidates = deepcopy(_CANDIDATES)
    return {
        "registry_version": REGISTRY_VERSION,
        "candidate_count": len(candidates),
        "rejected_count": sum(1 for candidate in candidates if _is_rejected_status(str(candidate["status"]))),
        "eligible_for_oos_review_count": sum(
            1 for candidate in candidates if candidate["eligible_for_oos_review"] is True
        ),
        "oos_locked": True,
        "candidates": candidates,
        "safety": {
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
            "buy_sell_output_allowed": False,
            "execution_logic_present": False,
            "trade_recommendation_output_present": False,
            "oos_locked": True,
        },
    }


def candidate_registry_by_id() -> dict[str, dict[str, Any]]:
    return {
        candidate["candidate_id"]: candidate
        for candidate in research_candidate_registry()["candidates"]
    }
