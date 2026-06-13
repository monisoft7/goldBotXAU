"""Local project health gate for goldBotXAU repository safety."""

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

from src.research.candidate_registry import research_candidate_registry

HEALTH_CHECK_VERSION = "v0_20"
IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".json", ".txt", ".toml", ".ini", ".cfg"}
DANGEROUS_FILE_PATTERNS = (
    re.compile(r"(^|[\\/])credentials", re.IGNORECASE),
    re.compile(r"(^|[\\/])secrets", re.IGNORECASE),
    re.compile(r"mt5_login", re.IGNORECASE),
    re.compile(r"mt5_password", re.IGNORECASE),
    re.compile(r"\.(key|pem)$", re.IGNORECASE),
)


def _project_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _exists(root: Path, relative_path: str) -> bool:
    return (root / relative_path).exists()


def _issue_templates_exist(root: Path) -> bool:
    issue_template_dir = root / ".github" / "ISSUE_TEMPLATE"
    required = {
        "research_candidate.md",
        "bug_report.md",
        "research_diagnostic.md",
    }
    return issue_template_dir.exists() and required.issubset({path.name for path in issue_template_dir.glob("*.md")})


def _iter_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def _is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {".gitignore"}


def _is_safety_context(path: Path, root: Path) -> bool:
    relative = _project_path(path, root)
    return (
        relative.startswith("docs/")
        or relative.startswith("tests/")
        or relative.startswith("project_memory/")
        or relative == "README.md"
        or relative == "safety_rules.md"
        or relative == "scripts/project_health_check.py"
        or relative.startswith(".github/")
    )


def _find_paths_with_patterns(
    root: Path,
    patterns: tuple[re.Pattern[str], ...],
    fatal_patterns: tuple[re.Pattern[str], ...] = (),
    benign_patterns: tuple[re.Pattern[str], ...] = (),
) -> tuple[list[str], list[str]]:
    warnings: set[str] = set()
    failures: set[str] = set()

    for path in _iter_project_files(root):
        if not _is_text_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scan_text = "\n".join(
            line for line in text.splitlines() if not any(pattern.search(line) for pattern in benign_patterns)
        )
        if not any(pattern.search(scan_text) for pattern in patterns):
            continue
        relative = _project_path(path, root)
        fatal_match = any(pattern.search(scan_text) for pattern in fatal_patterns)
        if _is_safety_context(path, root):
            warnings.add(relative)
        elif fatal_match and (relative.startswith("src/") or relative.startswith("scripts/")):
            failures.add(relative)
        else:
            warnings.add(relative)

    return sorted(warnings), sorted(failures)


def _find_dangerous_files(root: Path) -> list[str]:
    dangerous: list[str] = []
    for path in _iter_project_files(root):
        relative = _project_path(path, root)
        if any(pattern.search(relative) for pattern in DANGEROUS_FILE_PATTERNS):
            dangerous.append(relative)
    return sorted(dangerous)


def _latest_checkpoint_docs_present(root: Path) -> bool:
    checkpoint_dir = root / "docs" / "checkpoints"
    if not checkpoint_dir.exists():
        return False
    return any(checkpoint_dir.glob("v0_*_result.md"))


def build_project_health_report(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    registry = research_candidate_registry()

    order_send_warnings, order_send_failures = _find_paths_with_patterns(
        root,
        (re.compile(r"\border_send\b"),),
        (re.compile(r"\border_send\s*\("),),
        (
            re.compile(r"\border_send_allowed[\"']?\s*[:=]\s*False\b"),
            re.compile(r"^\s*[\"']order_send_enabled[\"'],?\s*$", re.MULTILINE),
        ),
    )
    order_check_warnings, order_check_failures = _find_paths_with_patterns(
        root,
        (re.compile(r"\border_check\b"),),
        (re.compile(r"\border_check\s*\("),),
    )
    demo_live_warnings, demo_live_failures = _find_paths_with_patterns(
        root,
        (
            re.compile(r"\bdemo[_\s-]*(enabled|trading|account|mode)\b", re.IGNORECASE),
            re.compile(r"\blive[_\s-]*(enabled|trading|account|mode)\b", re.IGNORECASE),
        ),
        (
            re.compile(r"\bdemo_enabled[\"']?\s*[:=]\s*True\b"),
            re.compile(r"\blive_enabled[\"']?\s*[:=]\s*True\b"),
            re.compile(r"\b(enable|start|connect).*?\b(demo|live)[_\s-]*(trading|account|mode)\b", re.IGNORECASE),
        ),
        (
            re.compile(r"\bdemo_enabled[\"']?\s*[:=]\s*False\b"),
            re.compile(r"\blive_enabled[\"']?\s*[:=]\s*False\b"),
            re.compile(r"^\s*[\"']demo_enabled[\"'],?\s*$", re.MULTILINE),
            re.compile(r"^\s*[\"']live_enabled[\"'],?\s*$", re.MULTILINE),
        ),
    )
    buy_sell_warnings, buy_sell_failures = _find_paths_with_patterns(
        root,
        (
            re.compile(r"\bBUY\b"),
            re.compile(r"\bSELL\b"),
        ),
        (
            re.compile(r"\bprint\s*\([^)]*\bBUY\b"),
            re.compile(r"\bprint\s*\([^)]*\bSELL\b"),
            re.compile(r"\b(signal|side|action)[\"']?\s*[:=]\s*[\"'](BUY|SELL)[\"']"),
        ),
        (
            re.compile(r"\bbuy_sell_output_allowed[\"']?\s*[:=]\s*False\b"),
            re.compile(r"\btrade_recommendation_output_present[\"']?\s*[:=]\s*False\b"),
        ),
    )
    queue_warnings, queue_failures = _find_paths_with_patterns(
        root,
        (
            re.compile(r"\bexecution[_\s-]*queue\b", re.IGNORECASE),
            re.compile(r"\bExecutionQueue\b"),
        ),
        (
            re.compile(r"\bexecution_queue_enabled[\"']?\s*[:=]\s*True\b"),
            re.compile(r"\bExecutionQueue\s*\("),
        ),
        (re.compile(r"\bexecution_queue_enabled[\"']?\s*[:=]\s*False\b"),),
    )
    dangerous_files = _find_dangerous_files(root)

    failure_files = sorted(
        set(order_send_failures + order_check_failures + demo_live_failures + buy_sell_failures + queue_failures)
    )
    warning_files = sorted(
        set(order_send_warnings + order_check_warnings + demo_live_warnings + buy_sell_warnings + queue_warnings)
    )

    repository_tooling = {
        "gitignore_exists": _exists(root, ".gitignore"),
        "github_actions_tests_exists": _exists(root, ".github/workflows/tests.yml"),
        "pull_request_template_exists": _exists(root, ".github/pull_request_template.md"),
        "issue_templates_exist": _issue_templates_exist(root),
        "codex_task_protocol_exists": _exists(root, "docs/codex_task_protocol.md"),
    }
    project_state = {
        "candidate_registry_exists": _exists(root, "src/research/candidate_registry.py"),
        "rejected_candidate_count": registry["rejected_count"],
        "eligible_for_oos_review_count": registry["eligible_for_oos_review_count"],
        "oos_locked": bool(registry["oos_locked"]),
        "one_time_oos_review_completed_count": sum(
            1 for candidate in registry["candidates"] if candidate.get("one_time_oos_review_completed") is True
        ),
        "repeat_oos_review_allowed_count": sum(
            1 for candidate in registry["candidates"] if candidate.get("repeat_oos_review_allowed") is True
        ),
    }
    required_docs = {
        "codex_operating_notes_exists": _exists(root, "docs/codex_operating_notes.md"),
        "next_codex_handoff_exists": _exists(root, "docs/next_codex_handoff.md"),
        "latest_checkpoint_docs_present": _latest_checkpoint_docs_present(root),
    }
    safety_scan = {
        "order_send_found": bool(order_send_warnings or order_send_failures),
        "order_check_found": bool(order_check_warnings or order_check_failures),
        "demo_live_execution_found": bool(demo_live_warnings or demo_live_failures),
        "buy_sell_output_found": bool(buy_sell_warnings or buy_sell_failures),
        "execution_queue_found": bool(queue_warnings or queue_failures),
        "dangerous_files_found": bool(dangerous_files),
        "warning_files": warning_files,
        "failure_files": failure_files,
        "dangerous_file_paths": dangerous_files,
    }

    missing_required = [
        f"repository_tooling.{key}" for key, value in repository_tooling.items() if value is not True
    ] + [f"required_docs.{key}" for key, value in required_docs.items() if value is not True]
    warnings: list[str] = []
    failures: list[str] = []
    if warning_files:
        warnings.append("documented_safety_mentions: forbidden terms appear only in docs, tests, templates, reports, or safety-check tooling.")
    if failure_files:
        failures.append("execution_like_code: forbidden execution-like code appears in src/ or scripts/ outside safety-check context.")
    if dangerous_files:
        failures.append("dangerous_files_found: local credential or secret-like files are present in the project tree.")
    for missing in missing_required:
        failures.append(f"missing_required_file: {missing}")

    failed = bool(failures)
    warned = bool(warnings)
    status = "failed" if failed else "warnings" if warned else "healthy"
    recommended_action = "fix_health_failures" if failed else "review_warnings" if warned else "continue_research"

    return {
        "health_check_version": HEALTH_CHECK_VERSION,
        "status": status,
        "warnings": warnings,
        "warning_files": warning_files,
        "failures": failures,
        "failure_files": failure_files,
        "repository_tooling": repository_tooling,
        "project_state": project_state,
        "safety_scan": safety_scan,
        "required_docs": required_docs,
        "recommended_action": recommended_action,
        "safety": {
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
            "execution_queue_enabled": False,
            "oos_evaluated": project_state["one_time_oos_review_completed_count"] > 0,
            "repeat_oos_review_allowed": project_state["repeat_oos_review_allowed_count"] > 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the goldBotXAU project health gate.")
    parser.add_argument("--json", action="store_true", help="Print the health report as JSON.")
    parser.add_argument("--output", type=Path, help="Optional path to write the JSON health report.")
    args = parser.parse_args()

    report = build_project_health_report(ROOT)
    report_text = json.dumps(report, indent=2, sort_keys=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_text + "\n", encoding="utf-8")

    if args.json:
        print(report_text)
    else:
        print(f"project health: {report['status']} ({report['recommended_action']})")

    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
