from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.print_codex_context import build_codex_context

ROOT = Path(__file__).resolve().parents[1]


def test_print_codex_context_returns_valid_json() -> None:
    context = build_codex_context(ROOT)

    assert context["context_version"] == "v0_29_1"
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
    assert context["context_version"] == "v0_29_1"


def test_context_cli_output_writes_report(tmp_path: Path) -> None:
    output_path = tmp_path / "codex_context_v0_29_1.json"

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
    assert context["context_version"] == "v0_29_1"


def test_context_includes_v0_29_1_repair_summary() -> None:
    context = build_codex_context(ROOT)

    assert context["latest_oos_repair"]["repair_version"] == "v0_29_1"
    assert context["latest_oos_repair"]["marker_decision_preserved"] == "oos_passed_research_validation"
    assert context["latest_oos_repair"]["detailed_oos_metrics_available"] is False
    assert context["latest_oos_repair"]["repeat_review_allowed"] is False
