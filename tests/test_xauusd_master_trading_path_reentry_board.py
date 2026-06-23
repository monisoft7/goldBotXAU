from __future__ import annotations

from pathlib import Path

from src.research.xauusd_master_trading_path_reentry_board import (
    COMPLETED_STATUS,
    RECOMMENDED_NEXT_STEP,
    build_master_trading_path_reentry_board,
)

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_REPORT_FIELDS = {
    "board_version",
    "board_status",
    "context_infrastructure_status",
    "context_layers_summary",
    "rejected_paths",
    "prior_strategy_state_summary",
    "v0_26_tradeability_status",
    "current_executable_candidate_available",
    "current_executable_candidate_id_or_null",
    "oos_allowed_now",
    "demo_allowed_now",
    "live_allowed_now",
    "strategy_testing_allowed_now",
    "recommended_primary_path",
    "recommended_next_step",
    "reason_for_reentry",
    "reason_not_continue_context_expansion",
    "v0_82_requirements",
    "v0_82_forbidden_actions",
    "safety_flags",
    "external_api_called",
    "external_data_downloaded",
    "dataset_file_created",
    "market_csv_created",
    "data_csv_touched",
    "real_xauusd_data_used_for_new_test",
    "labels_used_as_trade_blockers",
    "labels_used_for_strategy_testing",
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
    "train_validation_only",
    "oos_used",
    "repeated_oos_review",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "executable_candidate_created",
    "strategy_rules_modified",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
}

FALSE_SAFETY_FIELDS = [
    "external_api_called",
    "external_data_downloaded",
    "dataset_file_created",
    "market_csv_created",
    "data_csv_touched",
    "real_xauusd_data_used_for_new_test",
    "labels_used_as_trade_blockers",
    "labels_used_for_strategy_testing",
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
    "oos_used",
    "repeated_oos_review",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "executable_candidate_created",
    "strategy_rules_modified",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
]


def test_board_recommends_v0_82_when_context_layers_complete_without_clear_leads() -> None:
    report = build_master_trading_path_reentry_board(ROOT)

    assert report["board_version"] == "v0_81"
    assert report["board_status"] == COMPLETED_STATUS
    assert report["recommended_next_step"] == RECOMMENDED_NEXT_STEP
    assert report["recommended_primary_path"] == "design_one_fixed_rule_executable_candidate_without_oos"
    assert report["context_layers_summary"]["dxy"]["clear_lead_count"] == 0
    assert report["context_layers_summary"]["oil"]["clear_lead_count"] == 0
    assert report["context_layers_summary"]["yield"]["ready_for_future_human_sample_preflight"] is True


def test_board_does_not_recommend_more_context_expansion_as_primary_path() -> None:
    report = build_master_trading_path_reentry_board(ROOT)

    assert "context_expansion" not in report["recommended_primary_path"]
    assert "continue_dxy_expansion_without_critical_blocker" in report["rejected_paths"]
    assert "continue_oil_expansion_without_critical_blocker" in report["rejected_paths"]
    assert "continue_yield_context_expansion_without_critical_blocker" in report["rejected_paths"]


def test_board_does_not_recommend_trading_v0_26() -> None:
    report = build_master_trading_path_reentry_board(ROOT)

    assert report["v0_26_tradeability_status"]["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert report["v0_26_tradeability_status"]["tradeable_as_is"] is False
    assert report["v0_26_tradeability_status"]["direction_side_mapping_resolved"] is False
    assert report["v0_26_tradeability_status"]["recommended_for_trading"] is False
    assert "trade_v0_26_as_is" in report["rejected_paths"]


def test_board_does_not_allow_oos_demo_live_or_strategy_testing_now() -> None:
    report = build_master_trading_path_reentry_board(ROOT)

    assert report["current_executable_candidate_available"] is False
    assert report["current_executable_candidate_id_or_null"] is None
    assert report["oos_allowed_now"] is False
    assert report["demo_allowed_now"] is False
    assert report["live_allowed_now"] is False
    assert report["strategy_testing_allowed_now"] is False


def test_board_does_not_create_or_modify_strategy_rules() -> None:
    report = build_master_trading_path_reentry_board(ROOT)

    assert report["executable_candidate_created"] is False
    assert report["strategy_rules_modified"] is False
    assert report["safety_flags"]["executable_candidate_created"] is False
    assert report["safety_flags"]["strategy_rules_modified"] is False


def test_board_does_not_perform_retune_threshold_search_or_parameter_grid() -> None:
    report = build_master_trading_path_reentry_board(ROOT)

    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False


def test_board_does_not_use_data_csv_create_datasets_or_download_external_data() -> None:
    report = build_master_trading_path_reentry_board(ROOT)

    assert report["data_csv_touched"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["real_xauusd_data_used_for_new_test"] is False


def test_board_includes_v0_82_requirements_and_forbidden_actions() -> None:
    report = build_master_trading_path_reentry_board(ROOT)

    assert report["v0_82_requirements"] == [
        "explicit_direction_side_mapping",
        "entry_condition",
        "invalidation_stop_concept",
        "target_exit_concept",
        "train_validation_evaluation_plan",
        "cost_spread_policy",
        "minimum_trade_count_gate",
        "no_oos_until_train_validation_passes",
        "no_demo_until_oos_passes",
    ]
    assert "oos_review" in report["v0_82_forbidden_actions"]
    assert "demo_live_execution" in report["v0_82_forbidden_actions"]
    assert "threshold_search" in report["v0_82_forbidden_actions"]
    assert "parameter_grid" in report["v0_82_forbidden_actions"]


def test_report_includes_all_required_decision_and_safety_fields() -> None:
    report = build_master_trading_path_reentry_board(ROOT)

    assert REQUIRED_REPORT_FIELDS.issubset(report)
    for field in FALSE_SAFETY_FIELDS:
        assert report[field] is False
        assert report["safety_flags"][field] is False
    assert report["train_validation_only"] is True
    assert report["safety_flags"]["train_validation_only"] is True
