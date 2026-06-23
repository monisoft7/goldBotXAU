from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.print_codex_context import build_codex_context

ROOT = Path(__file__).resolve().parents[1]


def test_print_codex_context_returns_valid_json() -> None:
    context = build_codex_context(ROOT)

    assert context["context_version"] == "v0_84"
    json.dumps(context)


def test_context_includes_safety_rules() -> None:
    context = build_codex_context(ROOT)

    assert context["current_safety_rules"] == {
        "demo_only_scaffold": True,
        "no_live": True,
        "no_order_send_by_default": True,
        "no_order_check": True,
        "no_execution_queue": True,
        "no_buy_sell_output": True,
        "no_trade_recommendation_output": True,
        "oos_locked": True,
    }


def test_context_includes_rejected_candidates() -> None:
    context = build_codex_context(ROOT)

    assert context["rejected_do_not_retune_candidates"] == ["v0_7", "v0_8", "v0_11", "v0_14", "v0_17", "v0_23"]


def test_context_includes_oos_locked_true() -> None:
    context = build_codex_context(ROOT)

    assert context["health"]["oos_locked"] is True


def test_context_includes_eligible_for_oos_review_count() -> None:
    context = build_codex_context(ROOT)

    assert context["health"]["eligible_for_oos_review_count"] == 0


def test_context_does_not_include_huge_report_payloads_or_equity_curves() -> None:
    context_text = json.dumps(build_codex_context(ROOT), separators=(",", ":"))

    assert "equity_curve" not in context_text
    assert "train_metrics" not in context_text
    assert len(context_text) < 28500


def test_context_cli_json_works() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "print_codex_context.py"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    context = json.loads(completed.stdout)

    assert context["project"] == "goldBotXAU"
    assert context["context_version"] == "v0_84"


def test_context_cli_output_writes_report(tmp_path: Path) -> None:
    output_path = tmp_path / "codex_context_v0_84.json"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "print_codex_context.py"),
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    context = json.loads(output_path.read_text(encoding="utf-8"))
    assert context["context_version"] == "v0_84"


def test_context_includes_v0_29_1_repair_summary() -> None:
    context = build_codex_context(ROOT)

    assert context["latest_oos_repair"]["repair_version"] == "v0_29_1"
    assert context["latest_oos_repair"]["marker_decision_preserved"] == "oos_passed_research_validation"
    assert context["latest_oos_repair"]["detailed_oos_metrics_available"] is False
    assert context["latest_oos_repair"]["repeat_review_allowed"] is False


def test_context_includes_v0_30_post_oos_governance_summary() -> None:
    context = build_codex_context(ROOT)

    governance = context["latest_post_oos_governance"]
    assert governance is not None
    assert governance["governance_version"] == "v0_30"
    assert governance["source_oos_marker_decision"] == "oos_passed_research_validation"
    assert governance["detailed_oos_metrics_available"] is False
    assert governance["repeat_oos_review_allowed"] is False
    assert governance["paper_shadow_protocol_status"] == "design_only_not_started"
    assert governance["execution_allowed"] is False
    assert governance["demo_allowed"] is False
    assert governance["live_allowed"] is False


def test_context_includes_v0_31_paper_shadow_journal_summary() -> None:
    context = build_codex_context(ROOT)

    journal = context["latest_paper_shadow_journal"]
    assert journal is not None
    assert journal["protocol_version"] == "v0_31"
    assert journal["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert journal["journal_status"] == "framework_ready_not_started"
    assert journal["data_source_status"] == "synthetic_fixtures_only"
    assert journal["real_market_observation_started"] is False
    assert journal["execution_allowed"] is False
    assert journal["demo_allowed"] is False
    assert journal["live_allowed"] is False
    assert journal["repeated_oos_review"] is False
    assert journal["candidate_rules_modified"] is False


def test_context_includes_v0_32_forward_observation_plan_summary() -> None:
    context = build_codex_context(ROOT)

    plan = context["latest_forward_observation_plan"]
    assert plan is not None
    assert plan["plan_version"] == "v0_32"
    assert plan["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert plan["plan_status"] == "export_plan_ready_not_started"
    assert plan["real_market_observation_started"] is False
    assert plan["mt5_called"] is False
    assert plan["data_exported"] is False
    assert plan["observation_run"] is False
    assert plan["execution_allowed"] is False
    assert plan["demo_allowed"] is False
    assert plan["live_allowed"] is False
    assert plan["repeated_oos_review"] is False
    assert plan["candidate_rules_modified"] is False
    assert plan["allowed_future_timeframes"] == ["M5", "M10"]
    assert plan["future_observation_mode"] == "journal_only"


def test_context_includes_v0_33_forward_observation_runner_summary() -> None:
    context = build_codex_context(ROOT)

    runner = context["latest_forward_observation_runner"]
    assert runner is not None
    assert runner["runner_version"] == "v0_33"
    assert runner["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert runner["runner_status"] == "framework_ready_not_started"
    assert runner["data_source_status"] == "synthetic_fixtures_only"
    assert runner["real_market_observation_started"] is False
    assert runner["mt5_called_in_tests"] is False
    assert runner["execution_allowed"] is False
    assert runner["demo_allowed"] is False
    assert runner["live_allowed"] is False
    assert runner["repeated_oos_review"] is False
    assert runner["candidate_rules_modified"] is False
    assert runner["allowed_timeframes"] == ["M5", "M10"]
    assert runner["future_mode"] == "journal_only"


def test_context_includes_v0_34_forward_observation_journal_summary() -> None:
    context = build_codex_context(ROOT)

    journal = context["latest_forward_observation_journal"]
    assert journal is not None
    assert journal["observation_version"] == "v0_34"
    assert journal["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert journal["observation_status"] in {"journal_pass_completed", "blocked_need_forward_observation_data"}
    assert journal["real_market_observation_started"] is False
    assert journal["execution_allowed"] is False
    assert journal["demo_allowed"] is False
    assert journal["live_allowed"] is False
    assert journal["order_send_allowed"] is False
    assert journal["order_check_allowed"] is False
    assert journal["repeated_oos_review"] is False
    assert journal["candidate_rules_modified"] is False


def test_context_includes_v0_34_1_forward_observation_schema_adapter_summary() -> None:
    context = build_codex_context(ROOT)

    adapter = context["latest_forward_observation_schema_adapter"]
    assert adapter is not None
    assert adapter["adapter_version"] == "v0_34_1"
    assert adapter["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert adapter["adapter_status"] == "framework_ready"
    assert adapter["mt5_called"] is False
    assert adapter["data_exported_from_mt5"] is False
    assert adapter["execution_allowed"] is False
    assert adapter["demo_allowed"] is False
    assert adapter["live_allowed"] is False
    assert adapter["repeated_oos_review"] is False
    assert adapter["candidate_rules_modified"] is False
    assert adapter["supported_timeframes"] == ["M5", "M10"]
    assert adapter["expected_output_schema"] == [
        "timestamp_utc",
        "symbol",
        "timeframe",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
        "source",
    ]
    assert adapter["spread_warning"] == "spread_unavailable_from_exporter_set_to_0"


def test_context_includes_v0_34_2_forward_observation_consolidated_summary() -> None:
    context = build_codex_context(ROOT)

    consolidated = context["latest_forward_observation_consolidated"]
    assert consolidated is not None
    assert consolidated["consolidation_version"] == "v0_34_2"
    assert consolidated["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert consolidated["consolidation_status"] == "completed"
    assert consolidated["observation_mode"] == "local_read_only_forward_journal"
    assert consolidated["raw_market_data_embedded"] is False
    assert consolidated["timeframes_observed"] == ["M10", "M5"]
    assert consolidated["journal_record_count_by_timeframe"] == {"M10": 1, "M5": 1}
    assert consolidated["total_journal_record_count"] == 2
    assert consolidated["expansion_observed_count"] == 0
    assert consolidated["no_expansion_observed_count"] == 2
    assert consolidated["observation_quality_status"] == "insufficient_sample_for_quality_gate"
    assert consolidated["execution_allowed"] is False
    assert consolidated["demo_allowed"] is False
    assert consolidated["live_allowed"] is False
    assert consolidated["order_send_allowed"] is False
    assert consolidated["order_check_allowed"] is False
    assert consolidated["repeated_oos_review"] is False
    assert consolidated["candidate_rules_modified"] is False


def test_context_includes_latest_forward_observation_ledger_summary() -> None:
    context = build_codex_context(ROOT)

    ledger = context["latest_forward_observation_ledger"]
    assert ledger is not None
    assert ledger["ledger_version"] == "v0_35"
    assert ledger["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert ledger["ledger_status"] == "completed"
    assert ledger["raw_market_data_embedded"] is False
    assert ledger["input_consolidated_report_count"] == 4
    assert ledger["total_unique_journal_records"] == 6
    assert ledger["timeframes_observed"] == ["M10", "M5"]
    assert ledger["journal_record_count_by_timeframe"] == {"M10": 3, "M5": 3}
    assert ledger["independent_observation_session_count"] == 4
    assert ledger["expansion_observed_count"] == 4
    assert ledger["no_expansion_observed_count"] == 2
    assert ledger["quality_gate_status"] == "ready_for_demo_preflight_review"
    assert ledger["demo_preflight_allowed"] is False
    assert ledger["execution_allowed"] is False
    assert ledger["demo_allowed"] is False
    assert ledger["live_allowed"] is False
    assert ledger["order_send_allowed"] is False
    assert ledger["order_check_allowed"] is False
    assert ledger["repeated_oos_review"] is False
    assert ledger["candidate_rules_modified"] is False


def test_context_includes_v0_36_forward_observation_cycle_protocol_summary() -> None:
    context = build_codex_context(ROOT)

    protocol = context["latest_forward_observation_cycle_protocol"]
    assert protocol is not None
    assert protocol["cycle_protocol_version"] == "v0_36"
    assert protocol["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert protocol["orchestrator_status"] == "ready_for_approved_read_only_cycle"
    assert protocol["approval_token_required"] is True
    assert protocol["read_only_forward_observation_allowed"] is True
    assert protocol["demo_preflight_allowed"] is False
    assert protocol["execution_allowed"] is False
    assert protocol["demo_allowed"] is False
    assert protocol["live_allowed"] is False
    assert protocol["order_send_allowed"] is False
    assert protocol["order_check_allowed"] is False
    assert protocol["repeated_oos_review"] is False
    assert protocol["candidate_rules_modified"] is False
    assert protocol["raw_market_data_embedded"] is False
    assert protocol["supported_timeframes"] == ["M5", "M10"]


def test_context_includes_v0_37_demo_preflight_review_summary() -> None:
    context = build_codex_context(ROOT)

    review = context["latest_demo_preflight_review"]
    assert review is not None
    assert review["review_version"] == "v0_37"
    assert review["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert review["review_status"] == "completed"
    assert review["decision"] == "ready_for_demo_preflight_design"
    assert review["candidate_rules_preserved"] is True
    assert review["journal_record_count_by_timeframe"] == {"M10": 3, "M5": 3}
    assert review["independent_observation_session_count"] == 4
    assert review["integrity_blockers"] == []
    assert review["insufficient_forward_observation_blockers"] == []
    assert review["demo_allowed"] is False
    assert review["execution_allowed"] is False
    assert review["order_send_allowed"] is False
    assert review["order_check_allowed"] is False


def test_context_includes_v0_38_demo_broker_safety_preflight_summary() -> None:
    context = build_codex_context(ROOT)

    preflight = context["latest_demo_broker_safety_preflight"]
    assert preflight is not None
    assert preflight["preflight_version"] == "v0_38"
    assert preflight["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert preflight["preflight_status"] == "completed"
    assert preflight["decision"] == "demo_preflight_safety_design_ready"
    assert preflight["candidate_rules_preserved"] is True
    assert preflight["design_only"] is True
    assert preflight["blocking_conditions"] == []
    assert preflight["demo_execution_created"] is False
    assert preflight["broker_execution_path_created"] is False
    assert preflight["mt5_connection_created"] is False
    assert preflight["order_send_created"] is False
    assert preflight["order_check_created"] is False
    assert preflight["execution_queue_created"] is False
    assert preflight["buy_sell_output_allowed"] is False
    assert preflight["trade_recommendation_output_allowed"] is False
    assert preflight["repeated_oos_review"] is False
    assert preflight["retune_performed"] is False
    assert preflight["threshold_search_performed"] is False
    assert preflight["parameter_grid_performed"] is False


def test_context_includes_v0_39_broker_facts_audit_summary() -> None:
    context = build_codex_context(ROOT)

    audit = context["latest_broker_facts_audit"]
    assert audit is not None
    assert audit["audit_version"] == "v0_39"
    assert audit["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert audit["decision"] in {
        "blocked_mt5_unavailable",
        "blocked_symbol_unavailable",
        "blocked_missing_critical_broker_facts",
        "broker_facts_audit_ready_for_risk_envelope_design",
    }
    assert audit["candidate_rules_preserved"] is True
    assert audit["design_or_read_only"] is True
    assert audit["mt5_read_only_metadata_access"] is True
    assert audit["order_send_created"] is False
    assert audit["order_send_called"] is False
    assert audit["order_check_created"] is False
    assert audit["order_check_called"] is False
    assert audit["execution_queue_created"] is False
    assert audit["broker_execution_path_created"] is False
    assert audit["buy_sell_output_allowed"] is False
    assert audit["trade_recommendation_output_allowed"] is False
    assert audit["repeated_oos_review"] is False
    assert audit["retune_performed"] is False
    assert audit["threshold_search_performed"] is False
    assert audit["parameter_grid_performed"] is False


def test_context_includes_v0_40_demo_risk_envelope_summary() -> None:
    context = build_codex_context(ROOT)

    envelope = context["latest_demo_risk_envelope"]
    assert envelope is not None
    assert envelope["version"] == "v0_40"
    assert envelope["decision"] == "demo_risk_envelope_design_ready"
    assert envelope["safety_locked"] is True
    assert envelope["lot"] == 0.01
    assert envelope["warnings"] == 1
    assert envelope["blockers"] == 0


def test_context_includes_v0_41_final_demo_readiness_gate_summary() -> None:
    context = build_codex_context(ROOT)

    gate = context["latest_final_demo_readiness_gate"]
    assert gate is not None
    assert gate["gate_version"] == "v0_41"
    assert gate["decision"] == "final_demo_readiness_gate_passed_pending_human_authorization"
    assert gate["gate_status"] == "completed"
    assert gate["final_blockers"] == 0
    assert gate["accepted_warnings"] == 1
    assert gate["human_auth_required"] is True
    assert gate["future_design_consideration"] is True
    assert gate["safety_locked"] is True


def test_context_includes_v0_42_limited_demo_execution_summary() -> None:
    context = build_codex_context(ROOT)

    execution = context["latest_limited_demo_execution"]
    assert execution is not None
    assert execution["executor_version"] == "v0_42"
    assert execution["executor_status"] in {
        "dry_run_ready_no_order_sent",
        "blocked_macro_event_window",
        "blocked_missing_complete_order_request",
    }
    assert execution["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert execution["candidate_rules_preserved"] is True
    assert execution["demo_only"] is True
    assert execution["live_allowed"] is False
    assert execution["order_send_default_allowed"] is False
    assert execution["order_send_called"] is False
    assert execution["order_check_called"] is False
    assert execution["order_request_present"] is False
    assert execution["order_request_complete"] is False
    assert execution["order_request_validation_status"] == "missing_order_request"
    assert execution["macro_event_lock_enabled"] is True
    assert execution["approval_token_required"] is True


def test_context_includes_v0_43_signal_order_request_summary() -> None:
    context = build_codex_context(ROOT)

    builder = context["latest_signal_order_request"]
    assert builder is not None
    assert builder["builder_version"] == "v0_43"
    assert builder["builder_status"] in {
        "no_qualified_signal_now",
        "blocked_macro_event_window",
        "order_request_built_dry_run_only",
    }
    assert builder["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert builder["candidate_rules_preserved"] is True
    assert builder["dry_run"] is True
    assert builder["order_send_called"] is False
    assert builder["order_check_called"] is False
    assert builder["live_allowed"] is False


def test_context_includes_v0_44_1_bounded_signal_watch_summary() -> None:
    context = build_codex_context(ROOT)

    watch = context["latest_bounded_signal_watch"]
    assert watch is not None
    assert watch["watch_version"] == "v0_44_1"
    assert watch["watch_status"] in {
        "completed_no_qualified_signal",
        "blocked_macro_event_window",
        "stopped_order_request_ready_for_human_review",
    }
    assert watch["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert watch["candidate_rules_preserved"] is True
    assert watch["dry_run"] is True
    assert isinstance(watch["max_cycles"], int)
    assert watch["max_cycles"] >= 1
    assert isinstance(watch["interval_seconds"], int)
    assert watch["interval_seconds"] >= 1
    assert watch["sleep_enabled"] is True
    assert isinstance(watch["sleep_calls"], int)
    assert isinstance(watch["total_planned_sleep_seconds"], int)
    assert watch["interval_seconds_honored"] is True
    assert watch["order_send_called"] is False
    assert watch["order_check_called"] is False
    assert watch["live_allowed"] is False


def test_context_includes_v0_45_live_signal_snapshot_summary() -> None:
    context = build_codex_context(ROOT)

    snapshot = context["latest_live_signal_snapshot"]
    assert snapshot is not None
    assert snapshot["snapshot_version"] == "v0_45_1"
    assert snapshot["snapshot_status"] in {
        "blocked_mt5_unavailable",
        "blocked_symbol_unavailable",
        "blocked_insufficient_live_candles",
        "snapshot_ready_no_qualified_signal",
        "snapshot_ready_order_request_built_dry_run_only",
        "snapshot_ready_signal_confirmed_direction_unassigned",
        "blocked_macro_event_window",
    }
    assert snapshot["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert snapshot["candidate_rules_preserved"] is True
    assert snapshot["dry_run"] is True
    assert snapshot["timeframes_requested"] == ["M5", "M10"]
    assert snapshot["mt5_read_only"] is True
    assert snapshot["direction_assigned"] in {True, False}
    assert snapshot["executable_side_valid"] in {True, False}
    assert snapshot["order_request_validation_status"] in {
        "missing_order_request",
        "incomplete",
        "complete",
        "direction_unassigned_non_executable",
        "invalid_side_non_executable",
    }
    assert isinstance(snapshot["invalid_order_request_reasons"], list)
    assert snapshot["order_send_called"] is False
    assert snapshot["order_check_called"] is False
    assert snapshot["live_allowed"] is False
    assert snapshot["retune_performed"] is False
    assert snapshot["threshold_search_performed"] is False
    assert snapshot["parameter_grid_performed"] is False
    assert snapshot["repeated_oos_review"] is False


def test_context_includes_v0_46_candidate_direction_provenance_summary() -> None:
    context = build_codex_context(ROOT)

    audit = context["latest_candidate_direction_provenance_audit"]
    assert audit is not None
    assert audit["audit_version"] == "v0_46"
    assert audit["audit_status"] in {
        "direction_rule_verified_from_locked_candidate",
        "no_direction_rule_found_execution_blocked",
        "ambiguous_direction_rule_execution_blocked",
        "audit_failed_missing_candidate_artifacts",
    }
    assert audit["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert audit["candidate_rules_preserved"] is True
    assert audit["direction_rule_found"] in {True, False}
    assert audit["executable_side_mapping_found"] in {True, False}
    assert audit["demo_execution_direction_ready"] in {True, False}
    assert isinstance(audit["blockers"], int)
    assert isinstance(audit["warnings"], int)
    assert audit["order_send_called"] is False
    assert audit["order_check_called"] is False
    assert audit["live_allowed"] is False
    assert audit["retune_performed"] is False
    assert audit["threshold_search_performed"] is False
    assert audit["parameter_grid_performed"] is False
    assert audit["repeated_oos_review"] is False


def test_context_includes_v0_47_direction_research_board_summary() -> None:
    context = build_codex_context(ROOT)

    board = context["latest_direction_research_board"]
    assert board is not None
    assert board["board_version"] == "v0_47"
    assert board["board_status"] in {
        "no_direction_candidate_passed",
        "direction_candidate_passed_train_validation",
        "blocked_missing_required_data",
        "board_failed",
    }
    assert board["source_filter_candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert board["source_filter_preserved"] is True
    assert board["train_validation_only"] is True
    assert board["oos_used"] is False
    assert board["direction_hypotheses_evaluated"] == [
        "expansion_continuation_close_direction",
        "first_breakout_m5_confirmed_by_m10",
        "response_block_body_direction",
        "expansion_fade_direction",
    ]
    assert board["best_candidate_id"] in {
        "expansion_continuation_close_direction",
        "first_breakout_m5_confirmed_by_m10",
        "response_block_body_direction",
        "expansion_fade_direction",
        None,
    }
    assert board["best_candidate_passed_gate"] in {True, False}
    assert board["demo_execution_allowed"] is False
    assert board["order_send_called"] is False
    assert board["order_check_called"] is False
    assert board["live_allowed"] is False
    assert board["retune_performed"] is False
    assert board["threshold_search_performed"] is False
    assert board["parameter_grid_performed"] is False


def test_context_includes_v0_48_new_directional_discovery_board_summary() -> None:
    context = build_codex_context(ROOT)

    board = context["latest_new_directional_discovery_board"]
    assert board is not None
    assert board["board_version"] == "v0_48"
    assert board["board_status"] in {
        "no_new_directional_candidate_passed",
        "new_directional_candidate_passed_train_validation",
        "blocked_missing_required_data",
        "board_failed",
    }
    assert board["prior_path_closed"] == "xauusd_compression_then_expansion_v0_26"
    assert board["prior_path_closure_reason"] == "no_executable_direction_rule_and_v0_47_direction_board_failed"
    assert board["train_validation_only"] is True
    assert board["oos_used"] is False
    assert board["repeated_oos_review"] is False
    assert board["directional_families_evaluated"] == [
        "session_open_range_breakout_directional",
        "prior_block_breakout_continuation_directional",
        "failed_breakout_reversal_directional",
        "trend_pullback_continuation_directional",
    ]
    assert board["best_candidate_id"] in {
        "session_open_range_breakout_directional",
        "prior_block_breakout_continuation_directional",
        "failed_breakout_reversal_directional",
        "trend_pullback_continuation_directional",
        None,
    }
    assert board["best_candidate_passed_gate"] in {True, False}
    assert board["demo_execution_allowed"] is False
    assert board["order_send_called"] is False
    assert board["order_check_called"] is False
    assert board["live_allowed"] is False
    assert board["retune_performed"] is False
    assert board["threshold_search_performed"] is False
    assert board["parameter_grid_performed"] is False


def test_context_includes_v0_49_trend_pullback_stability_audit_summary() -> None:
    context = build_codex_context(ROOT)

    audit = context["latest_trend_pullback_stability_audit"]
    assert audit is not None
    assert audit["audit_version"] == "v0_49"
    assert audit["audit_status"] in {"completed", "audit_failed_missing_required_data"}
    assert audit["source_board_version"] == "v0_48"
    assert audit["candidate_id"] == "trend_pullback_continuation_directional"
    assert audit["candidate_rules_preserved"] in {True, False}
    assert audit["train_validation_only"] is True
    assert audit["oos_used"] is False
    assert audit["repeated_oos_review"] is False
    assert isinstance(audit["validation_trade_count"], int)
    assert audit["validation_trade_minimum"] == 25
    assert audit["validation_trade_count_passed"] in {True, False}
    assert audit["sample_concentration_risk"] in {"low", "high", "unknown"}
    assert audit["stability_decision"] in {
        "promising_but_insufficient_validation_sample",
        "unstable_reject",
        "stable_enough_for_candidate_locking_pre_oos_review",
        "audit_failed_missing_required_data",
    }
    assert audit["candidate_locking_allowed_pre_oos"] in {True, False}
    assert audit["demo_execution_allowed"] is False
    assert audit["order_send_called"] is False
    assert audit["order_check_called"] is False
    assert audit["live_allowed"] is False
    assert audit["retune_performed"] is False
    assert audit["threshold_search_performed"] is False
    assert audit["parameter_grid_performed"] is False


def test_context_includes_v0_50_historical_data_expansion_feasibility_summary() -> None:
    context = build_codex_context(ROOT)

    audit = context["latest_historical_data_expansion_feasibility"]
    assert audit is not None
    assert audit["audit_version"] == "v0_50"
    assert audit["audit_status"] in {
        "expansion_data_available",
        "expansion_data_partially_available",
        "expansion_data_unavailable",
        "blocked_mt5_unavailable",
        "audit_failed",
    }
    assert audit["symbol"] == "XAUUSD"
    assert audit["requested_from_date"] == "2019-01-01"
    assert audit["requested_to_date"] == "2022-12-31"
    assert audit["mt5_read_only"] is True
    assert audit["mt5_initialized"] in {True, False}
    assert audit["mt5_shutdown_called"] in {True, False}
    assert audit["requested_range_available"] in {True, False}
    assert isinstance(audit["candle_count_by_timeframe"], dict)
    assert isinstance(audit["missing_range_gap_count"], int)
    assert audit["data_expansion_feasible"] in {True, False}
    assert audit["candidate_to_retest_later"] == "trend_pullback_continuation_directional"
    assert audit["candidate_rules_preserved"] is True
    assert audit["oos_used"] is False
    assert audit["repeated_oos_review"] is False
    assert audit["demo_execution_allowed"] is False
    assert audit["order_send_called"] is False
    assert audit["order_check_called"] is False
    assert audit["live_allowed"] is False
    assert audit["data_csv_added_to_git"] is False
    assert audit["retune_performed"] is False
    assert audit["threshold_search_performed"] is False
    assert audit["parameter_grid_performed"] is False


def test_context_includes_v0_51_trend_pullback_expanded_retest_summary() -> None:
    context = build_codex_context(ROOT)

    retest = context["latest_trend_pullback_expanded_retest"]
    assert retest is not None
    assert retest["retest_version"] == "v0_51"
    assert retest["retest_status"] in {
        "expanded_evidence_passed_pre_oos_locking_gate",
        "expanded_evidence_failed",
        "blocked_missing_expansion_data",
        "retest_failed",
    }
    assert retest["candidate_id"] == "trend_pullback_continuation_directional"
    assert retest["source_candidate_board_version"] == "v0_48"
    assert retest["source_stability_audit_version"] == "v0_49"
    assert retest["source_data_feasibility_version"] == "v0_50"
    assert retest["candidate_rules_preserved"] is True
    assert retest["train_validation_equivalent_only"] is True
    assert retest["oos_used"] is False
    assert retest["repeated_oos_review"] is False
    assert retest["retune_performed"] is False
    assert retest["threshold_search_performed"] is False
    assert retest["parameter_grid_performed"] is False
    assert isinstance(retest["candle_count_by_timeframe"], dict)
    assert isinstance(retest["expanded_trade_count"], int)
    assert retest["sample_concentration_risk"] in {"low", "high", "unknown"}
    assert retest["expanded_evidence_passed_gate"] in {True, False}
    assert retest["candidate_locking_allowed_pre_oos"] in {True, False}
    assert retest["demo_execution_allowed"] is False
    assert retest["order_send_called"] is False
    assert retest["order_check_called"] is False
    assert retest["live_allowed"] is False
    assert retest["data_csv_added_to_git"] is False


def test_context_includes_v0_52_external_strategy_idea_triage_summary() -> None:
    context = build_codex_context(ROOT)

    triage = context["latest_external_strategy_idea_triage"]
    assert triage is not None
    assert triage["triage_version"] == "v0_52"
    assert triage["triage_status"] in {
        "shortlist_ready_for_v0_53_non_oos_board",
        "insufficient_external_ideas_after_triage",
    }
    assert triage["shortlist_for_v0_53"] == [
        "prior_day_liquidity_sweep_reversal",
        "london_opening_range_breakout_or_first_candle_direction",
        "asian_range_london_breakout_confirmation",
    ]
    assert triage["oos_used"] is False


def test_context_includes_v0_52_1_kimi_external_idea_addendum_summary() -> None:
    context = build_codex_context(ROOT)

    addendum = context["latest_kimi_external_idea_addendum"]
    assert addendum is not None
    assert addendum["addendum_version"] == "v0_52_1"
    assert addendum["addendum_status"] in {
        "kimi_addendum_completed_shortlist_unchanged",
        "kimi_addendum_completed_shortlist_updated",
        "kimi_addendum_failed_missing_v0_52_report",
        "kimi_addendum_failed",
    }
    assert addendum["source_triage_version"] == "v0_52"
    assert addendum["final_shortlist_for_v0_53"] == [
        "prior_day_liquidity_sweep_reversal",
        "london_opening_range_breakout_or_first_candle_direction",
        "asian_range_london_breakout_confirmation",
    ]
    assert addendum["shortlist_changed"] is False
    assert addendum["oos_used"] is False
    assert addendum["candidate_created"] is False


def test_context_includes_v0_53_external_shortlist_board_summary() -> None:
    context = build_codex_context(ROOT)

    board = context["latest_external_shortlist_board"]
    assert board is not None
    assert board["board_version"] == "v0_53"
    assert board["board_status"] in {
        "external_shortlist_candidate_passed_train_validation",
        "no_external_shortlist_candidate_passed",
        "blocked_missing_required_data",
        "board_failed",
    }
    assert board["source_triage_versions"] == ["v0_52", "v0_52_1"]
    assert board["tested_candidate_ids"] == [
        "prior_day_liquidity_sweep_reversal",
        "london_opening_range_breakout_or_first_candle_direction",
        "asian_range_london_breakout_confirmation",
    ]
    assert board["best_candidate_id"] in {
        "prior_day_liquidity_sweep_reversal",
        "london_opening_range_breakout_or_first_candle_direction",
        "asian_range_london_breakout_confirmation",
        None,
    }
    assert board["best_candidate_passed_gate"] in {True, False}
    assert board["train_validation_only"] is True
    assert board["oos_used"] is False
    assert board["repeated_oos_review"] is False
    assert board["retune_performed"] is False
    assert board["threshold_search_performed"] is False
    assert board["parameter_grid_performed"] is False
    assert board["candidate_created"] is False
    assert board["demo_execution_allowed"] is False
    assert board["order_send_called"] is False
    assert board["order_check_called"] is False
    assert board["live_allowed"] is False
    assert board["data_csv_added_to_git"] is False


def test_context_includes_v0_54_edge_profiler_summary() -> None:
    context = build_codex_context(ROOT)

    profiler = context["latest_edge_profiler"]
    assert profiler is not None
    assert profiler["profiler_version"] == "v0_54"
    assert profiler["profiler_status"] in {
        "edge_profile_completed_with_research_leads",
        "edge_profile_completed_no_clear_leads",
        "blocked_missing_required_data",
        "profiler_failed",
    }
    assert profiler["source_previous_board_version"] == "v0_53"
    assert profiler["purpose"] == "empirical_edge_mapping_not_strategy_backtest"
    assert profiler["train_validation_only"] is True
    assert profiler["oos_used"] is False
    assert isinstance(profiler["strongest_empirical_leads"], list)
    assert profiler["candidate_created"] is False
    assert profiler["demo_execution_allowed"] is False
    assert profiler["order_send_called"] is False
    assert profiler["order_check_called"] is False
    assert profiler["live_allowed"] is False
    assert profiler["data_csv_added_to_git"] is False


def test_context_includes_v0_55_session_volatility_design_summary() -> None:
    context = build_codex_context(ROOT)

    design = context["latest_session_volatility_design"]
    assert design is not None
    assert design["design_version"] == "v0_55"
    assert design["design_status"] in {
        "session_volatility_design_completed_with_v0_56_candidate",
        "session_volatility_design_completed_no_candidate",
        "blocked_missing_v0_54_profiler_report",
        "design_failed",
    }
    assert design["source_profiler_version"] == "v0_54"
    assert design["profiler_leads_used"] == ["session_return_profile", "volatility_regime_profile"]
    assert 2 <= design["candidate_design_count"] <= 4
    assert design["recommended_candidate_for_v0_56"] in {
        None,
        "session_block_directional_bias_candidate",
        "volatility_regime_session_filter_candidate",
        "session_transition_continuation_candidate",
        "volatility_regime_momentum_candidate",
    }
    assert design["train_validation_only"] is True
    assert design["oos_used"] is False
    assert design["demo_execution_allowed"] is False
    assert design["order_send_called"] is False
    assert design["order_check_called"] is False


def test_context_includes_v0_56_session_block_bias_eval_summary() -> None:
    context = build_codex_context(ROOT)

    evaluation = context["latest_session_block_bias_eval"]
    assert evaluation is not None
    assert evaluation["evaluation_version"] == "v0_56"
    assert evaluation["evaluation_status"] in {
        "session_block_candidate_passed_train_validation",
        "session_block_candidate_rejected",
        "blocked_missing_v0_55_design",
        "blocked_missing_required_data",
        "evaluation_failed",
    }
    assert evaluation["source_design_version"] == "v0_55"
    assert evaluation["source_profiler_version"] == "v0_54"
    assert evaluation["candidate_id"] == "session_block_directional_bias_candidate"
    assert evaluation["candidate_rules_preserved"] is True
    assert evaluation["evaluated_candidate_count"] == 1
    assert evaluation["other_v0_55_candidates_evaluated"] is False
    assert evaluation["train_validation_only"] is True
    assert evaluation["oos_used"] is False
    assert evaluation["repeated_oos_review"] is False
    assert evaluation["retune_performed"] is False
    assert evaluation["threshold_search_performed"] is False
    assert evaluation["parameter_grid_performed"] is False
    assert isinstance(evaluation["train_trades"], int)
    assert isinstance(evaluation["validation_trades"], int)
    assert evaluation["candidate_passed_train_validation_gate"] in {True, False}
    assert evaluation["candidate_locking_allowed_pre_oos"] in {True, False}
    assert evaluation["demo_execution_allowed"] is False
    assert evaluation["order_send_called"] is False
    assert evaluation["order_check_called"] is False
    assert evaluation["live_allowed"] is False
    assert evaluation["data_csv_added_to_git"] is False


def test_context_includes_v0_57_volatility_regime_lead_viability_summary() -> None:
    context = build_codex_context(ROOT)

    audit = context["latest_volatility_regime_lead_viability"]
    assert audit is not None
    assert audit["audit_version"] == "v0_57"
    assert audit["audit_status"] in {
        "volatility_lead_viability_completed",
        "blocked_missing_v0_54_profiler_report",
        "audit_failed",
    }
    assert audit["lead_id"] == "volatility_regime_profile"
    assert audit["session_block_branch_rejected"] is True
    assert audit["volatility_lead_viability_decision"] in {
        "volatility_lead_sample_viable_for_candidate_design",
        "volatility_lead_promising_but_insufficient_sample",
        "volatility_lead_unstable_or_too_weak_reject",
        "blocked_missing_v0_54_profiler_report",
        "audit_failed",
    }
    assert audit["candidate_design_feasible_for_v0_58"] in {True, False}
    assert audit["demo_execution_allowed"] is False
    assert audit["order_send_called"] is False
    assert audit["order_check_called"] is False
    assert audit["live_allowed"] is False
    assert audit["data_csv_added_to_git"] is False


def test_context_includes_v0_58_research_lab_integrity_summary() -> None:
    context = build_codex_context(ROOT)

    audit = context["latest_research_lab_integrity_audit"]
    assert audit is not None
    assert audit["audit_version"] == "v0_58"
    assert audit["audit_status"] in {
        "lab_integrity_completed",
        "lab_integrity_failed_fix_required",
        "audit_failed",
    }
    assert audit["purpose"] == "research_lab_integrity_diagnostic_not_strategy"
    assert audit["lab_integrity_decision"] in {
        "lab_integrity_passed_continue_research",
        "lab_integrity_passed_with_warnings",
        "lab_integrity_failed_fix_required",
        "audit_failed",
    }
    assert isinstance(audit["critical_findings"], int)
    assert isinstance(audit["warnings"], int)
    assert audit["data_timeframes"] == ["M10", "M15", "M5"]
    assert audit["split_boundaries_valid"] in {True, False}
    assert audit["oos_rows_excluded"] is True
    assert audit["trade_accounting_passed"] is True
    assert audit["prior_reports_consistent"] is True
    assert audit["train_validation_only"] is True
    assert audit["oos_used"] is False
    assert audit["repeated_oos_review"] is False
    assert audit["retune_performed"] is False
    assert audit["threshold_search_performed"] is False
    assert audit["parameter_grid_performed"] is False
    assert audit["executable_candidate_created"] is False
    assert audit["demo_execution_allowed"] is False
    assert audit["order_send_called"] is False
    assert audit["order_check_called"] is False
    assert audit["live_allowed"] is False
    assert audit["data_csv_added_to_git"] is False


def test_context_includes_v0_59_research_lab_warning_standardization_summary() -> None:
    context = build_codex_context(ROOT)

    standardization = context["latest_research_lab_warning_standardization"]
    assert standardization is not None
    assert standardization["standardization_version"] == "v0_59"
    assert standardization["standardization_status"] in {
        "lab_warning_standardization_completed",
        "blocked_missing_v0_58_integrity_report",
        "standardization_failed",
    }
    assert standardization["source_integrity_audit_version"] == "v0_58"
    assert isinstance(standardization["warnings_addressed"], int)
    assert standardization["cost_policy_documented"] is True
    assert standardization["timestamp_policy_documented"] is True
    assert standardization["gap_classification_policy_documented"] is True
    assert standardization["gate_policy_documented"] is True
    assert standardization["low_frequency_false_negative_risk_documented"] is True
    assert standardization["strategy_metrics_changed"] is False
    assert standardization["gates_lowered"] is False
    assert standardization["oos_used"] is False
    assert standardization["repeated_oos_review"] is False
    assert standardization["retune_performed"] is False
    assert standardization["threshold_search_performed"] is False
    assert standardization["parameter_grid_performed"] is False
    assert standardization["executable_candidate_created"] is False
    assert standardization["demo_execution_allowed"] is False
    assert standardization["order_send_called"] is False
    assert standardization["order_check_called"] is False
    assert standardization["live_allowed"] is False


def test_context_includes_v0_60_second_tier_fixed_rule_board_summary() -> None:
    context = build_codex_context(ROOT)

    board = context["latest_second_tier_fixed_rule_board"]
    assert board is not None
    assert board["board_version"] == "v0_60"
    assert board["board_status"] in {
        "second_tier_candidate_passed_train_validation",
        "no_second_tier_candidate_passed",
        "blocked_missing_v0_59_policy_docs",
        "blocked_missing_required_data",
        "board_failed",
    }
    assert board["source_standardization_version"] == "v0_59"
    assert board["tested_candidate_ids"] == [
        "failed_m15_swing_breakout_reversal",
        "ny_liquidity_sweep_reversal",
        "sequential_m5_move_mean_reversion",
    ]
    assert board["best_candidate_id"] in {
        "failed_m15_swing_breakout_reversal",
        "ny_liquidity_sweep_reversal",
        "sequential_m5_move_mean_reversion",
        None,
    }
    assert board["best_candidate_passed_gate"] in {True, False}
    assert isinstance(board["rejected_do_not_retune_candidates"], list)
    assert board["train_validation_only"] is True
    assert board["oos_used"] is False
    assert board["repeated_oos_review"] is False
    assert board["retune_performed"] is False
    assert board["threshold_search_performed"] is False
    assert board["parameter_grid_performed"] is False
    assert board["gates_lowered"] is False
    assert board["past_metrics_changed"] is False
    assert board["executable_candidate_created"] is False
    assert board["demo_execution_allowed"] is False
    assert board["order_send_called"] is False
    assert board["order_check_called"] is False
    assert board["live_allowed"] is False
    assert board["data_csv_added_to_git"] is False
    assert board["timestamp_basis_reported"] is True


def test_context_includes_v0_61_market_context_feasibility_summary() -> None:
    context = build_codex_context(ROOT)

    audit = context["latest_market_context_feasibility"]
    assert audit is not None
    assert audit["audit_version"] == "v0_61"
    assert audit["audit_status"] in {
        "market_context_feasibility_completed",
        "blocked_missing_v0_60_report",
        "market_context_feasibility_failed",
    }
    assert audit["purpose"] == "market_context_layer_feasibility_only"
    assert audit["source_previous_board_version"] == "v0_60"
    assert audit["pure_ohlc_branch_status"] == "no_second_tier_candidate_passed"
    assert audit["market_context_family_count"] == 7
    assert isinstance(audit["discovered_candidate_symbols"], dict)
    assert audit["external_feature_schema_documented"] is True
    assert audit["anti_lookahead_policy_documented"] is True
    assert audit["data_alignment_policy_documented"] is True
    assert audit["api_key_storage_policy_documented"] is True
    assert audit["approved_for_v0_62_feature_import"] is False
    assert audit["approved_for_strategy_testing"] is False
    assert audit["safety_locked"] is True


def test_context_includes_v0_62_market_context_labeler_summary() -> None:
    context = build_codex_context(ROOT)

    labels = context["latest_market_context_labels"]
    assert labels is not None
    assert labels["labeler_version"] == "v0_62"
    assert labels["labeler_status"] in {
        "market_context_labeler_completed",
        "blocked_missing_v0_61_report",
        "labeler_failed",
    }
    assert labels["source_feasibility_version"] == "v0_61"
    assert labels["labels_are_trade_blockers"] is False
    assert labels["hard_blockers_limited_to_market_closed_and_missing_data"] is True
    assert labels["timeframes_used"] == ["M10", "M15", "M5"]
    assert isinstance(labels["total_timestamp_rows"], int)
    assert isinstance(labels["label_counts"], dict)
    assert "market_closed_weekend" in labels["label_counts"]
    assert "likely_market_open" in labels["label_counts"]
    assert labels["approved_for_strategy_testing"] is False
    assert labels["approved_for_trade_filtering"] is False
    assert labels["safety_locked"] is True


def test_context_includes_v0_65_dxy_proxy_context_audit_summary() -> None:
    context = build_codex_context(ROOT)

    audit = context["latest_dxy_proxy_context_audit"]
    assert audit is not None
    assert audit["version"] == "v0_65"
    assert audit["status"] in {
        "dxy_proxy_context_feasibility_completed",
        "no_usable_dxy_proxy_found",
        "dxy_proxy_audit_blocked_missing_data",
    }
    assert audit["safety_locked"] is True


def test_context_includes_v0_66_dxy_proxy_quality_ranker_summary() -> None:
    context = build_codex_context(ROOT)

    ranker = context["latest_dxy_proxy_quality_ranker"]
    assert ranker is not None
    assert ranker["ranker_version"] == "v0_66"
    assert ranker["ranker_status"] in {
        "dxy_proxy_quality_ranking_completed",
        "dxy_proxy_quality_ranking_completed_no_safe_proxy",
        "dxy_proxy_quality_ranking_blocked_missing_data",
    }
    assert ranker["source_audit_version"] == "v0_65"
    assert ranker["candidate_symbols_ranked"] == ["DXYN", "DXYZ", "GDXY", "USDX"]
    assert ranker["selected_proxy_symbol_or_null"] in {"DXYN", "DXYZ", "GDXY", "USDX", None}
    assert ranker["lookahead_risk_detected"] is False
    assert ranker["aligned_dataset_created"] is False
    assert ranker["data_csv_touched"] is False
    assert ranker["approved_for_strategy_testing"] is False
    assert ranker["approved_for_trade_filtering"] is False
    assert ranker["recommended_next_step"] == "v0_67_dxy_regime_label_design_if_proxy_quality_passes"
    assert ranker["safety_locked"] is True


def test_context_includes_v0_67_dxy_regime_label_design_summary() -> None:
    context = build_codex_context(ROOT)

    design = context["latest_dxy_regime_label_design"]
    assert design is not None
    assert design["label_design_version"] == "v0_67"
    assert design["label_design_status"] == "dxy_regime_label_design_completed"
    assert design["source_proxy_ranker_version"] == "v0_66"
    assert design["selected_proxy_symbol"] == "DXYN"
    assert design["secondary_proxy_symbol"] == "USDX"
    assert design["label_count"] == 8
    assert design["safe_asof_alignment_required"] is True
    assert design["recommended_next_step"] == "v0_68_dxy_conditioned_event_study_no_strategy_if_labels_pass"
    assert design["safety_locked"] is True


def test_context_includes_v0_68_dxy_conditioned_event_study_summary() -> None:
    context = build_codex_context(ROOT)

    study = context["latest_dxy_conditioned_event_study"]
    assert study is not None
    assert study["study_version"] == "v0_68"
    assert study["study_status"] in {
        "dxy_conditioned_event_study_completed",
        "dxy_conditioned_event_study_completed_no_clear_leads",
        "dxy_conditioned_event_study_blocked_missing_data",
    }
    assert study["selected_proxy_symbol"] == "DXYN"
    assert isinstance(study["event_count"], int)
    assert isinstance(study["clear_lead_count"], int)
    assert study["train_validation_only"] is True
    assert study["oos_used"] is False
    assert study["safety_locked"] is True


def test_context_includes_v0_68_1_dxy_proxy_row_adapter_summary() -> None:
    context = build_codex_context(ROOT)

    adapter = context["latest_dxy_proxy_row_adapter"]
    assert adapter is not None
    assert adapter["adapter_version"] == "v0_68_1"
    assert adapter["adapter_status"] in {
        "dxy_proxy_row_adapter_completed",
        "dxy_proxy_row_adapter_completed_with_fallback_recommended",
        "dxy_proxy_row_adapter_blocked_no_parseable_proxy_rows",
    }
    assert adapter["source_quality_ranker_version"] == "v0_66"
    assert adapter["source_event_study_version"] == "v0_68"
    assert adapter["symbols_checked"] == ["DXYN", "DXYZ", "GDXY", "USDX"]
    assert adapter["shared_adapter_created_or_updated"] is True
    assert adapter["event_study_updated_to_use_shared_adapter"] is True
    assert adapter["aligned_dataset_created"] is False
    assert adapter["data_csv_touched"] is False
    assert adapter["lookahead_risk_detected"] is False
    assert adapter["recommended_next_step"] in {
        "rerun_v0_68_dxy_conditioned_event_study_with_shared_adapter",
        "v0_69_yield_or_brent_context_feasibility_before_new_strategy",
    }
    assert adapter["safety_locked"] is True


def test_context_includes_v0_70_oil_proxy_quality_and_label_design_summary() -> None:
    context = build_codex_context(ROOT)

    design = context["latest_oil_v0_70"]
    assert design is not None
    assert design["version"] == "v0_70"
    assert design["status"] in {
        "oil_proxy_quality_and_label_design_completed",
        "oil_proxy_quality_and_label_design_completed_no_safe_proxy",
        "oil_proxy_quality_and_label_design_blocked_missing_data",
    }
    assert design["selected"] in {"BRN", "WTI", None}
    assert design["labels"] == 7
    assert design["next"] == "v0_71_gold_macro_context_board_no_strategy"
    assert design["safety_locked"] is True


def test_context_includes_v0_71_gold_macro_context_board_summary() -> None:
    context = build_codex_context(ROOT)

    board = context["latest_gold_macro_context_board"]
    assert board is not None
    assert board["version"] == "v0_71"
    assert board["status"] == "gold_macro_context_board_completed"
    assert board["next"] == "v0_72_oil_conditioned_event_study_no_strategy"
    assert board["safety_locked"] is True


def test_context_includes_v0_72_oil_conditioned_event_study_summary() -> None:
    context = build_codex_context(ROOT)

    study = context["latest_oil_conditioned_event_study"]
    assert study is not None
    assert study["study_version"] == "v0_72"
    assert study["study_status"] in {
        "oil_conditioned_event_study_completed",
        "oil_conditioned_event_study_completed_no_clear_leads",
        "oil_conditioned_event_study_blocked_missing_data",
    }
    assert study["selected_proxy_symbol"] == "BRN"
    assert study["fallback_proxy_symbol"] == "WTI"
    assert isinstance(study["event_count"], int)
    assert isinstance(study["clear_lead_count"], int)
    assert study["train_validation_only"] is True
    assert study["oos_used"] is False
    assert study["safety_locked"] is True


def test_context_includes_v0_73_yield_context_feasibility_summary() -> None:
    context = build_codex_context(ROOT)

    audit = context["latest_yield_context_feasibility"]
    assert audit is not None
    assert audit["audit_version"] == "v0_73"
    assert audit["audit_status"] in {
        "yield_context_feasibility_completed",
        "no_usable_local_yield_proxy_found",
        "yield_context_audit_blocked_missing_data",
    }
    assert audit["selected_local_proxy_symbol_or_null"] is None or isinstance(
        audit["selected_local_proxy_symbol_or_null"], str
    )
    assert audit["local_yield_proxy_available"] in {True, False}
    assert audit["external_dataset_required"] in {True, False}
    assert audit["safe_asof_alignment_feasible"] in {True, False}
    assert audit["recommended_next_step"] in {
        "v0_74_yield_proxy_quality_and_label_design",
        "v0_74_external_yield_dataset_schema_design_no_strategy",
    }
    assert audit["safety_locked"] is True


def test_context_includes_v0_74_external_yield_dataset_schema_summary() -> None:
    context = build_codex_context(ROOT)

    schema = context["latest_external_yield_dataset_schema"]
    assert schema is not None
    assert schema["version"] == "v0_74"
    assert schema["status"] == "external_yield_dataset_schema_completed"
    assert schema["series_count"] == 6
    assert schema["next"] == "v0_75_external_yield_sample_fixture_validator_no_strategy"
    assert schema["safe"] is True


def test_context_includes_v0_75_external_yield_sample_validator_summary() -> None:
    context = build_codex_context(ROOT)

    validator = context["latest_external_yield_sample_validator"]
    assert validator is not None
    assert validator["version"] == "v0_75"
    assert validator["status"] == "external_yield_sample_validator_completed_with_expected_fixture_rejections"
    assert validator["valid"] == 2
    assert validator["rejected"] == 2
    assert validator["dupes"] == 1
    assert validator["next"] == "v0_76_external_yield_manual_fixture_ingestion_design_no_strategy"
    assert validator["safe"] is True


def test_context_includes_v0_76_external_yield_manual_fixture_ingestion_summary() -> None:
    context = build_codex_context(ROOT)

    ingestion = context["latest_external_yield_manual_fixture_ingestion"]
    assert ingestion is not None
    assert ingestion["version"] == "v0_76"
    assert ingestion["status"] == "external_yield_manual_fixture_ingestion_completed_with_expected_rejections"
    assert ingestion["safe"] is True


def test_context_includes_v0_77_external_yield_asof_alignment_design_summary() -> None:
    context = build_codex_context(ROOT)

    alignment = context["latest_external_yield_asof_alignment_design"]
    assert alignment is not None
    assert alignment["v"] == "v0_77"
    assert alignment["status"] == "external_yield_asof_alignment_design_completed_with_expected_rejections"
    assert alignment["n"] == [7, 3, 4, 4, 3, 1, 1]
    assert alignment["next"] == "v0_78_external_yield_label_design_no_strategy"
    assert alignment["safe"] is True


def test_context_includes_v0_78_external_yield_label_design_summary() -> None:
    context = build_codex_context(ROOT)

    design = context["latest_yield_labels"]
    assert design is not None
    assert design["v"] == "v0_78"
    assert design["status"] == "external_yield_label_design_completed"
    assert design["count"] == 12
    assert design["next"] == "v0_79_external_yield_label_fixture_application_no_strategy"
    assert design["safe"] is True


def test_context_includes_v0_79_external_yield_label_fixture_application_summary() -> None:
    context = build_codex_context(ROOT)

    application = context["ylf"]
    assert application is not None
    assert application["v"] == "v0_79"
    assert application["n"] == [12, 12, 12, 18, 2]
    assert application["safe"] is True


def test_context_includes_v0_80_external_yield_context_readiness_board_summary() -> None:
    context = build_codex_context(ROOT)

    board = context["yr"]
    assert board is not None
    assert board["v"] == "v0_80"
    assert board["m"] == 0
    assert board["safe"] is True


def test_context_includes_v0_81_master_trading_path_reentry_board_summary() -> None:
    context = build_codex_context(ROOT)

    assert context["context_version"] == "v0_84"
    assert context["m"] is True


def test_context_includes_v0_82_executable_fixed_rule_candidate_design_summary() -> None:
    context = build_codex_context(ROOT)

    assert context["x82"] == [
        "v0_82",
        "xauusd_ny_displacement_retest_executable_v0_82",
        "executable_fixed_rule_candidate_design_completed",
        True,
        "v0_83_executable_candidate_train_validation_evaluation_no_oos",
        True,
    ]


def test_context_includes_v0_83_executable_candidate_train_validation_summary() -> None:
    context = build_codex_context(ROOT)

    summary = context["x83"]
    assert summary is not None
    assert summary[0] == "v0_83"
    assert summary[1] == "xauusd_ny_displacement_retest_executable_v0_82"
    assert summary[2] in {
        "executable_candidate_train_validation_passed",
        "executable_candidate_train_validation_failed",
        "executable_candidate_train_validation_blocked",
    }
    assert isinstance(summary[3], int)
    assert isinstance(summary[4], int)
    assert summary[5] in {True, False}
    assert summary[6] in {
        "v0_84_single_oos_review_for_executable_candidate",
        "v0_84_candidate_failure_postmortem_no_retune",
    }
    assert summary[7] is True


def test_context_includes_v0_84_trading_decision_sprint_summary() -> None:
    context = build_codex_context(ROOT)

    summary = context["x84"]
    assert summary is not None
    assert summary[0] == "v0_84"
    assert summary[1] == "xauusd_ny_displacement_retest_executable_v0_82"
    assert summary[2] in {
        "trading_decision_sprint_passed_ready_for_single_oos",
        "trading_decision_sprint_failed_close_candidate",
        "trading_decision_sprint_blocked_missing_diagnostics",
    }
    assert summary[3] in {
        "long_only_variant",
        "short_only_variant",
        "ny_core_only_variant",
        "reduce_overtrading_time_filter_variant",
        "close_candidate_no_variant",
    }
    assert summary[4] in {True, False}
    assert summary[5] in {True, False}
    assert summary[6] in {True, False}
    assert summary[7] in {
        "v0_85_single_oos_review_for_rescued_executable_candidate",
        "v0_85_fresh_executable_candidate_family_selection_sprint",
        "v0_85_repair_trade_diagnostics_then_decide",
    }
    assert summary[8] is True


def test_context_includes_v0_63_context_labeled_event_study_summary() -> None:
    context = build_codex_context(ROOT)

    study = context["latest_context_labeled_event_study"]
    assert study is not None
    assert study["context_study_version"] == "v0_63"
    assert study["context_study_status"] in {
        "context_labeled_event_study_completed_with_leads",
        "context_labeled_event_study_completed_no_clear_leads",
        "blocked_missing_v0_62_labels",
        "context_study_failed",
    }
    assert study["source_labeler_version"] == "v0_62"
    assert study["source_prior_versions_considered"] == ["v0_53", "v0_56", "v0_60"]
    assert study["labels_used_as_trade_blockers"] is False
    assert study["strategy_rules_changed"] is False
    assert isinstance(study["lead_count"], int)
    assert study["train_validation_only"] is True
    assert study["oos_used"] is False
    assert study["demo_execution_allowed"] is False
    assert study["order_send_called"] is False
    assert study["safety_locked"] is True


def test_context_includes_v0_64_repository_consolidation_summary() -> None:
    context = build_codex_context(ROOT)

    plan = context["latest_repository_consolidation_plan"]
    assert plan is not None
    assert plan["consolidation_version"] == "v0_64"
    assert plan["consolidation_status"] == "repository_consolidation_plan_completed"
    assert isinstance(plan["files_scanned_count"], int)
    assert plan["files_scanned_count"] > 0
    assert plan["active_keep_count"] > 0
    assert plan["archive_candidate_count"] > 0
    assert plan["delete_candidate_count"] > 0
    assert plan["manual_review_count"] > 0
    assert plan["tracked_data_csv_count"] >= 1
    assert plan["cache_files_detected_count"] > 0
    assert plan["failed_experiments_indexed_count"] >= 10
    assert plan["safe_to_apply_cleanup_now"] is False
    assert plan["cleanup_requires_human_review"] is True
    assert plan["recommended_next_step"] == "v0_64_1_apply_reviewed_cleanup_plan_no_strategy_changes"
    assert plan["safety_locked"] is True


def test_context_includes_v0_64_1_repository_cleanup_summary() -> None:
    context = build_codex_context(ROOT)

    cleanup = context["latest_repository_cleanup"]
    assert cleanup is not None
    assert cleanup["cleanup_version"] == "v0_64_1"
    assert cleanup["cleanup_status"] in {
        "dry_run_completed",
        "cleanup_applied_completed",
        "cleanup_blocked",
    }
    assert cleanup["data_csv_touched"] is False
    assert cleanup["safety_files_touched"] is False
    assert cleanup["latest_context_files_touched"] is False
    assert cleanup["archive_root"] == "project_archive/retired_v0_64_1"
    assert cleanup["recommended_next_step"] == "v0_65_dxy_proxy_context_audit_after_cleanup"
    assert cleanup["safety_locked"] is True


def test_context_includes_v0_64_2_repository_cleanup_repair_summary() -> None:
    context = build_codex_context(ROOT)

    repair = context["latest_repository_cleanup_repair"]
    assert repair is not None
    assert repair["repair_version"] == "v0_64_2"
    assert repair["repair_status"] == "cleanup_boundary_repair_completed"
    assert repair["pytest_archive_excluded"] is True
    assert repair["restored_active_dependency_count"] >= 4
    assert repair["active_tests_import_check_passed"] is True
    assert repair["full_pytest_passed"] is True
    assert repair["data_csv_touched"] is False
    assert repair["safety_files_touched"] is False
    assert repair["latest_context_files_touched"] is False
    assert repair["recommended_next_step"] == "commit_v0_63_to_v0_64_2_then_v0_65_dxy_proxy_context_audit"
    assert repair["safety_locked"] is True
