from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.print_codex_context import build_codex_context

ROOT = Path(__file__).resolve().parents[1]


def test_print_codex_context_returns_valid_json() -> None:
    context = build_codex_context(ROOT)

    assert context["context_version"] == "v0_34"
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
    assert len(context_text) < 5000


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
    assert context["context_version"] == "v0_34"


def test_context_cli_output_writes_report(tmp_path: Path) -> None:
    output_path = tmp_path / "codex_context_v0_34.json"

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
    assert context["context_version"] == "v0_34"


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
