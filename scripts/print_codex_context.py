"""Print a compact local Codex context pack for goldBotXAU."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.project_health_check import build_project_health_report
from src.research.candidate_registry import research_candidate_registry

CONTEXT_VERSION = "v0_31"


def _latest_known_test_count(root: Path) -> int | None:
    handoff_path = root / "docs" / "next_codex_handoff.md"
    if not handoff_path.exists():
        return None
    text = handoff_path.read_text(encoding="utf-8")
    match = re.search(r"Current test baseline:\s*(\d+)\s+passed", text)
    return int(match.group(1)) if match else None


def _recommended_next_step(root: Path) -> str:
    handoff_path = root / "docs" / "next_codex_handoff.md"
    if not handoff_path.exists():
        return "ask_director"
    for line in handoff_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Next safe task:"):
            return line.split(":", 1)[1].strip() or "ask_director"
    return "ask_director"


def _rejected_candidate_versions(registry: dict[str, Any]) -> list[str]:
    versions: list[str] = []
    for candidate in registry["candidates"]:
        status = str(candidate.get("status"))
        if not (status == "rejected" or status.startswith("rejected_")) or candidate.get("do_not_retune") is not True:
            continue
        match = re.search(r"_(v\d+_\d+)(?:_|$)", str(candidate["candidate_id"]))
        if match:
            versions.append(match.group(1))
    return sorted(versions, key=lambda version: tuple(int(part) for part in version[1:].split("_")))


def _oos_repair_summary(root: Path) -> dict[str, Any] | None:
    repair_path = root / "reports" / "xauusd_oos_review_repair_v0_29_1.json"
    if not repair_path.exists():
        return None
    report = json.loads(repair_path.read_text(encoding="utf-8"))
    return {
        "repair_version": report.get("repair_version"),
        "marker_report_mismatch_detected": report.get("marker_report_mismatch_detected"),
        "overwritten_report_detected": report.get("overwritten_report_detected"),
        "marker_decision_preserved": report.get("marker_decision_preserved"),
        "detailed_oos_metrics_available": report.get("detailed_oos_metrics_available"),
        "repeat_review_allowed": report.get("repeat_review_allowed"),
    }


def _post_oos_governance_summary(root: Path) -> dict[str, Any] | None:
    governance_path = root / "reports" / "xauusd_post_oos_governance_v0_30.json"
    if not governance_path.exists():
        return None
    report = json.loads(governance_path.read_text(encoding="utf-8"))
    return {
        "governance_version": report.get("governance_version"),
        "candidate_id": report.get("candidate_id"),
        "source_oos_marker_decision": report.get("source_oos_marker_decision"),
        "detailed_oos_metrics_available": report.get("detailed_oos_metrics_available"),
        "repeat_oos_review_allowed": report.get("repeat_oos_review_allowed"),
        "governance_status": report.get("governance_status"),
        "paper_shadow_protocol_status": report.get("paper_shadow_protocol_status"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "next_recommended_step": report.get("next_recommended_step"),
    }


def _paper_shadow_journal_summary(root: Path) -> dict[str, Any] | None:
    journal_path = root / "reports" / "xauusd_paper_shadow_journal_protocol_v0_31.json"
    if not journal_path.exists():
        return None
    report = json.loads(journal_path.read_text(encoding="utf-8"))
    return {
        "protocol_version": report.get("protocol_version"),
        "candidate_id": report.get("candidate_id"),
        "journal_status": report.get("journal_status"),
        "data_source_status": report.get("data_source_status"),
        "real_market_observation_started": report.get("real_market_observation_started"),
        "execution_allowed": report.get("execution_allowed"),
        "demo_allowed": report.get("demo_allowed"),
        "live_allowed": report.get("live_allowed"),
        "repeated_oos_review": report.get("repeated_oos_review"),
        "candidate_rules_modified": report.get("candidate_rules_modified"),
        "next_recommended_step": report.get("next_recommended_step"),
    }


def build_codex_context(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    health = build_project_health_report(root)
    registry = research_candidate_registry()

    return {
        "context_version": CONTEXT_VERSION,
        "project": "goldBotXAU",
        "path": str(root),
        "current_tests": _latest_known_test_count(root),
        "health": {
            "status": health["status"],
            "recommended_action": health["recommended_action"],
            "oos_locked": health["project_state"]["oos_locked"],
            "eligible_for_oos_review_count": health["project_state"]["eligible_for_oos_review_count"],
            "rejected_candidate_count": health["project_state"]["rejected_candidate_count"],
        },
        "latest_oos_repair": _oos_repair_summary(root),
        "latest_post_oos_governance": _post_oos_governance_summary(root),
        "latest_paper_shadow_journal": _paper_shadow_journal_summary(root),
        "rejected_do_not_retune_candidates": _rejected_candidate_versions(registry),
        "current_safety_rules": {
            "no_demo": True,
            "no_live": True,
            "no_order_send": True,
            "no_order_check": True,
            "no_execution_queue": True,
            "no_buy_sell_output": True,
            "oos_locked": True,
        },
        "next_task_protocol": [
            "read docs/codex_operating_notes.md",
            "read docs/codex_task_protocol.md",
            "run targeted tests",
            "run project health check",
            "return files changed, tests, safety confirmation",
        ],
        "recommended_next_step": _recommended_next_step(root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Print compact Codex context for goldBotXAU.")
    parser.add_argument("--json", action="store_true", help="Print the context as JSON.")
    parser.add_argument("--output", type=Path, help="Optional path to write the JSON context.")
    args = parser.parse_args()

    context = build_codex_context(ROOT)
    context_text = json.dumps(context, indent=2, sort_keys=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(context_text + "\n", encoding="utf-8")

    if args.json:
        print(context_text)
    else:
        print(f"Codex context {context['context_version']} for {context['project']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
