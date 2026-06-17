from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.print_codex_context import build_codex_context

ROOT = Path(__file__).resolve().parents[1]


def test_print_codex_context_returns_valid_json() -> None:
    context = build_codex_context(ROOT)

    assert context["context_version"] == "v0_38"
    json.dumps(context)


def test_context_includes_safety_rules() -> None:
    context = build_codex_context(ROOT)

    assert context["current_safety_rules"] == {
        "no_demo": True,
        "no_live": True,
        "no_order_send": True,
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
    context_text = json.dumps(build_codex_context(ROOT))

    assert "equity_curve" not in context_text
    assert "train_metrics" not in context_text
    assert len(context_text) < 8500


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
    assert context["context_version"] == "v0_38"


def test_context_cli_output_writes_report(tmp_path: Path) -> None:
    output_path = tmp_path / "codex_context_v0_38.json"

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
    assert context["context_version"] == "v0_38"


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
    assert ledger["input_consolidated_reports"] == [
        "reports\\xauusd_forward_observation_consolidated_v0_34_2.json",
        "reports\\xauusd_forward_observation_consolidated_cycle_2026_06_15_2026_06_16_v0_36.json",
        "reports\\xauusd_forward_observation_consolidated_cycle_2026_06_14_2026_06_15_v0_36.json",
        "C:\\Users\\THE BLU WALF\\Desktop\\goldBotXAU\\reports\\xauusd_forward_observation_consolidated_cycle_2026_06_16_2026_06_17_v0_36.json",
    ]
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
