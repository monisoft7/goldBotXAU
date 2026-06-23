"""Design-only fixed-rule XAUUSD executable candidate for v0_82."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DESIGN_VERSION = "v0_82"
CANDIDATE_ID = "xauusd_ny_displacement_retest_executable_v0_82"
CANDIDATE_VERSION = "v0_82"
CANDIDATE_FAMILY = "ny_displacement_retest_continuation"
SOURCE_REENTRY_BOARD_VERSION = "v0_81"
COMPLETED_STATUS = "executable_fixed_rule_candidate_design_completed"
BLOCKED_STATUS = "executable_fixed_rule_candidate_design_blocked"
FUTURE_EVALUATION_STEP = "v0_83_executable_candidate_train_validation_evaluation_no_oos"

FALSE_SAFETY_FIELDS = (
    "oos_allowed_now",
    "demo_allowed_now",
    "live_allowed_now",
    "order_request_ready",
    "execution_ready",
    "strategy_testing_performed",
    "train_validation_performed",
    "oos_used",
    "repeated_oos_review",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "existing_strategy_rules_modified",
    "rejected_candidates_modified",
    "external_api_called",
    "external_data_downloaded",
    "dataset_file_created",
    "market_csv_created",
    "data_csv_touched",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
    "approved_for_strategy_testing",
    "approved_for_oos",
    "approved_for_demo",
)


def _fixed_rule_design() -> dict[str, Any]:
    return {
        "setup_preconditions": [
            "Evaluate only XAUUSD during the NY core high-liquidity session when future v0_83 data is supplied.",
            "Use M15 to define the displacement context and M5 to define the controlled retest/hold behavior.",
            "Require complete OHLCV bars, valid chronological timestamps, and explicit spread/cost assumptions.",
            "Do not use DXY, oil, or yield labels as trade filters; they remain optional diagnostics only.",
        ],
        "bullish_displacement_condition": {
            "side_context": "long_only",
            "structured_rule": (
                "A bullish displacement exists when an M15 close breaks above the prior completed M15 swing or range "
                "high with an expansion body and closes in the upper portion of its range."
            ),
            "direction_result": "long_context_valid",
        },
        "bearish_displacement_condition": {
            "side_context": "short_only",
            "structured_rule": (
                "A bearish displacement exists when an M15 close breaks below the prior completed M15 swing or range "
                "low with an expansion body and closes in the lower portion of its range."
            ),
            "direction_result": "short_context_valid",
        },
        "retest_hold_condition": {
            "structured_rule": (
                "After displacement, wait for M5 price to retest the displaced level or displacement-origin zone, "
                "then require a hold candle that rejects the level without closing back through the invalidation side."
            ),
            "long_hold": "M5 retest holds above the broken resistance/zone and closes back upward.",
            "short_hold": "M5 retest holds below the broken support/zone and closes back downward.",
        },
        "long_entry_condition": (
            "Internal long side is valid only after bullish displacement plus a controlled M5 retest/hold above the "
            "broken level. No long side is available after bearish displacement."
        ),
        "short_entry_condition": (
            "Internal short side is valid only after bearish displacement plus a controlled M5 retest/hold below the "
            "broken level. No short side is available after bullish displacement."
        ),
        "entry_condition_defined": True,
        "invalidation_stop_concept": (
            "Invalidate a long on an M5 close below the held retest zone or displacement origin; invalidate a short "
            "on an M5 close above the held retest zone or displacement origin. Future v0_83 must translate this into "
            "a fixed R stop definition before evaluation."
        ),
        "target_exit_concept": (
            "Use fixed R-based continuation targets and/or next-session liquidity objective definitions declared "
            "before v0_83 evaluation; no target is optimized in v0_82."
        ),
        "time_stop_concept": (
            "Exit or mark invalid if continuation does not develop within a fixed number of completed M5 bars after "
            "entry; the exact bar count is a future fixed evaluation constant, not a v0_82 search parameter."
        ),
        "max_one_position_concept": "At most one candidate position may be open at a time.",
        "no_overlapping_trade_concept": "Do not open a new setup while a prior setup remains active or unresolved.",
        "spread_cost_policy_placeholder": (
            "Future v0_83 evaluation must apply a documented spread/cost policy and sensitivity check before any "
            "candidate promotion."
        ),
        "missing_data_behavior": (
            "Fail closed when required M5/M15 bars, timestamps, OHLC fields, session classification, or cost inputs "
            "are missing or non-chronological."
        ),
        "no_trade_conditions": [
            "No bullish or bearish displacement condition is present.",
            "Both bullish and bearish contexts appear simultaneously or side mapping is ambiguous.",
            "Retest/hold condition fails or closes through invalidation.",
            "Outside NY core/high-liquidity session context.",
            "Required M5/M15 data, timestamps, or cost assumptions are missing.",
            "Spread/cost policy cannot be applied in future evaluation.",
            "A prior candidate position is already active.",
            "Any safety boundary would require OOS, demo/live execution, order_send, order_check, or recommendation output.",
        ],
    }


def _future_evaluation_plan() -> dict[str, Any]:
    return {
        "next_step": FUTURE_EVALUATION_STEP,
        "train_validation_only": True,
        "oos_allowed_in_v0_83": False,
        "minimum_train_trade_count_gate": 60,
        "minimum_validation_trade_count_gate": 25,
        "validation_profit_factor_gate": 1.25,
        "validation_expectancy_gate_R": 0.05,
        "max_drawdown_gate_R": 8.0,
        "max_consecutive_loss_gate": 5,
        "cost_sensitivity_required": True,
        "timestamp_policy_required": True,
        "no_oos_until_train_validation_gates_pass": True,
        "gate_definitions_only_not_optimization_parameters": True,
    }


def build_executable_fixed_rule_candidate_design() -> dict[str, Any]:
    fixed_rule_design = _fixed_rule_design()
    future_plan = _future_evaluation_plan()
    safety = {field: False for field in FALSE_SAFETY_FIELDS}
    report: dict[str, Any] = {
        "design_version": DESIGN_VERSION,
        "design_status": COMPLETED_STATUS,
        "candidate_id": CANDIDATE_ID,
        "candidate_version": CANDIDATE_VERSION,
        "candidate_family": CANDIDATE_FAMILY,
        "source_board_version": SOURCE_REENTRY_BOARD_VERSION,
        "source_reentry_board_version": SOURCE_REENTRY_BOARD_VERSION,
        "symbol": "XAUUSD",
        "intended_timeframes": ["M5", "M15"],
        "intended_session_context": (
            "NY core / high-liquidity session context only, using existing timestamp/session policy if later evaluated"
        ),
        "context_layers_optional_only": True,
        "context_layers_policy": (
            "DXY/Oil/Yield context layers remain diagnostic only and must not be used as trade filters in v0_82."
        ),
        "explicit_side_mapping": True,
        "direction_ambiguity_resolved": True,
        "buy_rule_defined": True,
        "sell_rule_defined": True,
        "entry_condition_defined": fixed_rule_design["entry_condition_defined"],
        "stop_invalidation_defined": True,
        "target_exit_defined": True,
        "time_stop_defined": True,
        "no_trade_conditions_defined": True,
        "fixed_rule_design": fixed_rule_design,
        "side_mapping": {
            "long_side": {
                "valid_only_after": [
                    "bullish_displacement_condition",
                    "controlled_retest_hold_condition",
                ],
                "invalid_after": ["bearish_displacement_condition", "ambiguous_or_missing_direction_context"],
                "internal_side": "long",
            },
            "short_side": {
                "valid_only_after": [
                    "bearish_displacement_condition",
                    "controlled_retest_hold_condition",
                ],
                "invalid_after": ["bullish_displacement_condition", "ambiguous_or_missing_direction_context"],
                "internal_side": "short",
            },
        },
        "anti_retune_guard": {
            "not_retune_of_rejected_candidates": True,
            "rejected_candidates_not_modified": True,
            "rejected_candidates_not_reused_as_same_rule": True,
            "v0_26_not_traded_as_is": True,
            "v0_26_direction_problem_acknowledged": True,
        },
        "not_retune_of_rejected_candidates": True,
        "rejected_candidates_not_modified": True,
        "rejected_candidates_not_reused_as_same_rule": True,
        "v0_26_not_traded_as_is": True,
        "v0_26_direction_problem_acknowledged": True,
        "future_evaluation_plan": future_plan,
        "future_evaluation_plan_defined": True,
        "future_evaluation_step": FUTURE_EVALUATION_STEP,
        "recommended_next_step": FUTURE_EVALUATION_STEP,
        "safety_flags": safety,
        **safety,
    }
    return report


def write_executable_fixed_rule_candidate_design(root: Path) -> dict[str, Any]:
    report = build_executable_fixed_rule_candidate_design()
    output_path = root / "reports" / "xauusd_executable_fixed_rule_candidate_design_v0_82.json"
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
