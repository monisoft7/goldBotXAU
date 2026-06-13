from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.project_health_check import build_project_health_report

ROOT = Path(__file__).resolve().parents[1]


def test_health_check_runs_and_returns_json() -> None:
    report = build_project_health_report(ROOT)

    assert report["health_check_version"] == "v0_20"
    assert report["status"] in {"healthy", "warnings", "failed"}
    json.dumps(report)


def test_detects_repository_tooling_files() -> None:
    report = build_project_health_report(ROOT)

    assert report["repository_tooling"] == {
        "gitignore_exists": True,
        "github_actions_tests_exists": True,
        "pull_request_template_exists": True,
        "issue_templates_exist": True,
        "codex_task_protocol_exists": True,
    }


def test_detects_candidate_registry() -> None:
    report = build_project_health_report(ROOT)

    assert report["project_state"]["candidate_registry_exists"] is True
    assert report["project_state"]["rejected_candidate_count"] >= 5


def test_confirms_oos_locked_when_registry_says_no_eligible_candidate() -> None:
    report = build_project_health_report(ROOT)

    assert report["project_state"]["eligible_for_oos_review_count"] == 0
    assert report["project_state"]["oos_locked"] is True
    assert report["project_state"]["one_time_oos_review_completed_count"] == 1
    assert report["project_state"]["repeat_oos_review_allowed_count"] == 0
    assert report["safety"]["oos_evaluated"] is True
    assert report["safety"]["repeat_oos_review_allowed"] is False


def test_safety_fields_exist() -> None:
    report = build_project_health_report(ROOT)

    assert set(report["safety_scan"]) == {
        "order_send_found",
        "order_check_found",
        "demo_live_execution_found",
        "buy_sell_output_found",
        "execution_queue_found",
        "dangerous_files_found",
        "warning_files",
        "failure_files",
        "dangerous_file_paths",
    }
    assert set(report) >= {"warnings", "warning_files", "failures", "failure_files"}
    assert report["safety"] == {
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
        "execution_queue_enabled": False,
        "oos_evaluated": True,
        "repeat_oos_review_allowed": False,
    }


def test_ignores_historical_safety_mentions_of_order_send(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "codex_operating_notes.md").write_text("Never add order_send.\n", encoding="utf-8")
    (tmp_path / "docs" / "next_codex_handoff.md").write_text("OOS remains locked.\n", encoding="utf-8")
    (tmp_path / "docs" / "checkpoints").mkdir()
    (tmp_path / "docs" / "checkpoints" / "v0_1_result.md").write_text("Rejected.\n", encoding="utf-8")
    (tmp_path / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / ".github" / "workflows" / "tests.yml").write_text("name: tests\n", encoding="utf-8")
    (tmp_path / ".github" / "pull_request_template.md").write_text("Checklist\n", encoding="utf-8")
    for name in ["research_candidate.md", "bug_report.md", "research_diagnostic.md"]:
        (tmp_path / ".github" / "ISSUE_TEMPLATE" / name).write_text("template\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (tmp_path / "src" / "research").mkdir(parents=True)
    (tmp_path / "src" / "research" / "candidate_registry.py").write_text("# registry\n", encoding="utf-8")
    (tmp_path / "docs" / "codex_task_protocol.md").write_text("No order_send.\n", encoding="utf-8")

    report = build_project_health_report(tmp_path)

    assert report["safety_scan"]["order_send_found"] is True
    assert "docs/codex_operating_notes.md" in report["safety_scan"]["warning_files"]
    assert report["safety_scan"]["failure_files"] == []
    assert report["warnings"] == [
        "documented_safety_mentions: forbidden terms appear only in docs, tests, templates, reports, or safety-check tooling."
    ]
    assert report["failures"] == []


def test_flags_suspicious_execution_like_source_code_in_temp_fixture(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "broker.py").write_text("client.order_send(request)\n", encoding="utf-8")

    report = build_project_health_report(tmp_path)

    assert report["status"] == "failed"
    assert "src/broker.py" in report["safety_scan"]["failure_files"]
    assert report["failures"]
    assert report["recommended_action"] == "fix_health_failures"


def test_no_data_no_reports_case_handled_safely(tmp_path: Path) -> None:
    (tmp_path / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / ".github" / "workflows" / "tests.yml").write_text("name: tests\n", encoding="utf-8")
    (tmp_path / ".github" / "pull_request_template.md").write_text("Checklist\n", encoding="utf-8")
    for name in ["research_candidate.md", "bug_report.md", "research_diagnostic.md"]:
        (tmp_path / ".github" / "ISSUE_TEMPLATE" / name).write_text("template\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "codex_operating_notes.md").write_text("notes\n", encoding="utf-8")
    (tmp_path / "docs" / "codex_task_protocol.md").write_text("protocol\n", encoding="utf-8")
    (tmp_path / "docs" / "next_codex_handoff.md").write_text("handoff\n", encoding="utf-8")
    (tmp_path / "src" / "research").mkdir(parents=True)
    (tmp_path / "src" / "research" / "candidate_registry.py").write_text("# registry\n", encoding="utf-8")

    report = build_project_health_report(tmp_path)

    assert report["safety_scan"]["dangerous_files_found"] is False
    assert report["required_docs"]["latest_checkpoint_docs_present"] is False


def test_cli_json_works() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "project_health_check.py"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["health_check_version"] == "v0_20"
    assert "repository_tooling" in report


def test_status_warnings_requires_non_empty_warnings() -> None:
    report = build_project_health_report(ROOT)

    if report["status"] == "warnings":
        assert report["warnings"]


def test_status_failed_requires_non_empty_failures(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "broker.py").write_text("client.order_send(request)\n", encoding="utf-8")

    report = build_project_health_report(tmp_path)

    assert report["status"] == "failed"
    assert report["failures"]


def test_healthy_has_empty_warnings_and_failures(tmp_path: Path) -> None:
    (tmp_path / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / ".github" / "workflows" / "tests.yml").write_text("name: tests\n", encoding="utf-8")
    (tmp_path / ".github" / "pull_request_template.md").write_text("Checklist\n", encoding="utf-8")
    for name in ["research_candidate.md", "bug_report.md", "research_diagnostic.md"]:
        (tmp_path / ".github" / "ISSUE_TEMPLATE" / name).write_text("template\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (tmp_path / "docs" / "checkpoints").mkdir(parents=True)
    (tmp_path / "docs" / "codex_operating_notes.md").write_text("notes\n", encoding="utf-8")
    (tmp_path / "docs" / "codex_task_protocol.md").write_text("protocol\n", encoding="utf-8")
    (tmp_path / "docs" / "next_codex_handoff.md").write_text("handoff\n", encoding="utf-8")
    (tmp_path / "docs" / "checkpoints" / "v0_1_result.md").write_text("checkpoint\n", encoding="utf-8")
    (tmp_path / "src" / "research").mkdir(parents=True)
    (tmp_path / "src" / "research" / "candidate_registry.py").write_text("# registry\n", encoding="utf-8")

    report = build_project_health_report(tmp_path)

    assert report["status"] == "healthy"
    assert report["warnings"] == []
    assert report["warning_files"] == []
    assert report["failures"] == []
    assert report["failure_files"] == []


def test_warning_files_and_failure_files_exist() -> None:
    report = build_project_health_report(ROOT)

    assert isinstance(report["warning_files"], list)
    assert isinstance(report["failure_files"], list)


def test_documented_safety_mentions_are_not_fatal(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_safety.py").write_text("assert 'order_send' not in text\n", encoding="utf-8")

    report = build_project_health_report(tmp_path)

    assert report["safety_scan"]["order_send_found"] is True
    assert report["failure_files"] == []
