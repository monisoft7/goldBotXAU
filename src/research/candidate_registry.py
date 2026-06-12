"""Static research candidate registry for safe handoffs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

REGISTRY_VERSION = "v0_17"

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
]


def research_candidate_registry() -> dict[str, Any]:
    candidates = deepcopy(_CANDIDATES)
    return {
        "registry_version": REGISTRY_VERSION,
        "candidate_count": len(candidates),
        "rejected_count": sum(1 for candidate in candidates if candidate["status"] == "rejected"),
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
