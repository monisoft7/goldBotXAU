from __future__ import annotations

from pathlib import Path

from src.research.xauusd_executable_fixed_rule_candidate_design import (
    CANDIDATE_ID,
    COMPLETED_STATUS,
    FUTURE_EVALUATION_STEP,
    build_executable_fixed_rule_candidate_design,
)

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_SAFETY_FIELDS = {
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
}


def test_candidate_design_identity_and_market_scope() -> None:
    report = build_executable_fixed_rule_candidate_design()

    assert report["design_version"] == "v0_82"
    assert report["design_status"] == COMPLETED_STATUS
    assert report["candidate_id"] == CANDIDATE_ID
    assert report["candidate_version"] == "v0_82"
    assert report["candidate_family"] == "ny_displacement_retest_continuation"
    assert report["source_reentry_board_version"] == "v0_81"
    assert report["symbol"] == "XAUUSD"
    assert report["intended_timeframes"] == ["M5", "M15"]
    assert report["context_layers_optional_only"] is True


def test_candidate_design_includes_explicit_buy_and_sell_side_mapping() -> None:
    report = build_executable_fixed_rule_candidate_design()
    side_mapping = report["side_mapping"]

    assert report["explicit_side_mapping"] is True
    assert report["direction_ambiguity_resolved"] is True
    assert report["buy_rule_defined"] is True
    assert report["sell_rule_defined"] is True
    assert side_mapping["long_side"]["internal_side"] == "long"
    assert side_mapping["short_side"]["internal_side"] == "short"
    assert "bullish_displacement_condition" in side_mapping["long_side"]["valid_only_after"]
    assert "bearish_displacement_condition" in side_mapping["short_side"]["valid_only_after"]
    assert "bearish_displacement_condition" in side_mapping["long_side"]["invalid_after"]
    assert "bullish_displacement_condition" in side_mapping["short_side"]["invalid_after"]


def test_candidate_design_defines_fixed_rule_components_without_backtest_logic() -> None:
    report = build_executable_fixed_rule_candidate_design()
    design = report["fixed_rule_design"]

    assert report["entry_condition_defined"] is True
    assert report["stop_invalidation_defined"] is True
    assert report["target_exit_defined"] is True
    assert report["time_stop_defined"] is True
    assert report["no_trade_conditions_defined"] is True
    assert "bullish_displacement_condition" in design
    assert "bearish_displacement_condition" in design
    assert "retest_hold_condition" in design
    assert "long_entry_condition" in design
    assert "short_entry_condition" in design
    assert "invalidation_stop_concept" in design
    assert "target_exit_concept" in design
    assert "time_stop_concept" in design
    assert "missing_data_behavior" in design
    assert isinstance(design["no_trade_conditions"], list)


def test_v0_26_is_not_recommended_for_trading_as_is() -> None:
    report = build_executable_fixed_rule_candidate_design()
    guard = report["anti_retune_guard"]

    assert guard["v0_26_not_traded_as_is"] is True
    assert guard["v0_26_direction_problem_acknowledged"] is True
    assert report["v0_26_not_traded_as_is"] is True
    assert report["v0_26_direction_problem_acknowledged"] is True


def test_rejected_candidates_are_not_modified_retuned_or_reused_as_same_rule() -> None:
    report = build_executable_fixed_rule_candidate_design()
    guard = report["anti_retune_guard"]

    assert guard["not_retune_of_rejected_candidates"] is True
    assert guard["rejected_candidates_not_modified"] is True
    assert guard["rejected_candidates_not_reused_as_same_rule"] is True
    assert report["retune_performed"] is False
    assert report["rejected_candidates_modified"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False


def test_no_train_validation_oos_demo_live_or_execution_path_is_created() -> None:
    report = build_executable_fixed_rule_candidate_design()

    assert report["strategy_testing_performed"] is False
    assert report["train_validation_performed"] is False
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["oos_allowed_now"] is False
    assert report["demo_allowed_now"] is False
    assert report["live_allowed_now"] is False
    assert report["order_request_ready"] is False
    assert report["execution_ready"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False


def test_no_trade_recommendation_output_or_data_side_effects() -> None:
    report = build_executable_fixed_rule_candidate_design()

    assert report["trade_recommendation_output"] is False
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["data_csv_touched"] is False


def test_report_includes_future_v0_83_train_validation_plan_and_gates() -> None:
    report = build_executable_fixed_rule_candidate_design()
    plan = report["future_evaluation_plan"]

    assert report["future_evaluation_plan_defined"] is True
    assert report["future_evaluation_step"] == FUTURE_EVALUATION_STEP
    assert report["recommended_next_step"] == FUTURE_EVALUATION_STEP
    assert plan["next_step"] == FUTURE_EVALUATION_STEP
    assert plan["train_validation_only"] is True
    assert plan["oos_allowed_in_v0_83"] is False
    assert plan["minimum_train_trade_count_gate"] == 60
    assert plan["minimum_validation_trade_count_gate"] == 25
    assert plan["validation_profit_factor_gate"] == 1.25
    assert plan["validation_expectancy_gate_R"] == 0.05
    assert plan["max_drawdown_gate_R"] == 8.0
    assert plan["max_consecutive_loss_gate"] == 5
    assert plan["cost_sensitivity_required"] is True
    assert plan["timestamp_policy_required"] is True
    assert plan["no_oos_until_train_validation_gates_pass"] is True


def test_report_includes_all_required_safety_fields() -> None:
    report = build_executable_fixed_rule_candidate_design()

    assert REQUIRED_SAFETY_FIELDS.issubset(report)
    for field in REQUIRED_SAFETY_FIELDS:
        assert report[field] is False
        assert report["safety_flags"][field] is False
