from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.repository_cleanup_applier import build_repository_cleanup_report

ROOT = Path(__file__).resolve().parents[1]


def _write_fixture_plan(root: Path) -> Path:
    paths = [
        ("docs/checkpoints/v0_10_result.md", "historical_archive_document_only"),
        ("reports/codex_context_v0_20.json", "generated_report_archive_candidate"),
        ("src/strategies/retired_candidate.py", "retired_experiment_candidate"),
        ("manual/review.txt", "manual_review_required"),
        ("data/local.csv", "manual_review_required"),
        ("context_data/context.csv", "manual_review_required"),
        ("safety_rules.md", "active_safety_keep"),
        ("docs/checkpoints/v0_64_repository_consolidation_plan_result.md", "active_context_layer_keep"),
        ("reports/repository_consolidation_plan_v0_64.json", "active_context_layer_keep"),
        ("src/research/xauusd_forward_observation_runner.py", "retired_experiment_candidate"),
        ("__pycache__", "cache_delete_candidate"),
        ("__pycache__/cache.pyc", "cache_delete_candidate"),
        (".pytest_cache", "cache_delete_candidate"),
        (".pytest_cache/CACHEDIR.TAG", "cache_delete_candidate"),
    ]
    for rel_path, classification in paths:
        path = root / rel_path
        if rel_path.endswith((".pyc", ".json", ".md", ".txt", ".csv", ".py")):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{classification}\n", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)

    plan = {
        "files_scanned_count": 13,
        "active_keep_count": 3,
        "archive_candidate_count": 3,
        "delete_candidate_count": 4,
        "manual_review_count": 3,
        "classification_index": [{"path": path, "classification": classification} for path, classification in paths],
    }
    plan_path = root / "reports" / "repository_consolidation_plan_v0_64.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan_path


def test_build_repository_consolidation_plan_json_cli_works() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_repository_consolidation_plan_v0_64.py"), "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["consolidation_version"] == "v0_64"
    assert report["cleanup_actions_applied"] == []


def test_cleanup_applier_defaults_to_dry_run_and_changes_no_files(tmp_path: Path) -> None:
    plan_path = _write_fixture_plan(tmp_path)

    report = build_repository_cleanup_report(
        tmp_path,
        plan_path=plan_path,
        archive_root=tmp_path / "project_archive" / "retired_v0_64_1",
    )

    assert report["cleanup_status"] == "dry_run_completed"
    assert report["dry_run"] is True
    assert report["files_archived_count"] == 0
    assert report["files_deleted_count"] == 0
    assert (tmp_path / "docs/checkpoints/v0_10_result.md").exists()
    assert (tmp_path / "__pycache__/cache.pyc").exists()


def test_apply_deletes_only_cache_and_archives_only_approved_candidates(tmp_path: Path) -> None:
    plan_path = _write_fixture_plan(tmp_path)

    report = build_repository_cleanup_report(
        tmp_path,
        plan_path=plan_path,
        archive_root=tmp_path / "project_archive" / "retired_v0_64_1",
        apply=True,
    )

    assert report["cleanup_status"] == "cleanup_applied_completed"
    assert report["files_deleted_count"] >= 2
    assert report["files_archived_count"] == 3
    assert not (tmp_path / "__pycache__").exists()
    assert not (tmp_path / ".pytest_cache").exists()
    assert not (tmp_path / "docs/checkpoints/v0_10_result.md").exists()
    assert (tmp_path / "project_archive/retired_v0_64_1/docs/checkpoints/v0_10_result.md").exists()
    assert (tmp_path / "project_archive/retired_v0_64_1/reports/codex_context_v0_20.json").exists()
    assert (tmp_path / "project_archive/retired_v0_64_1/src/strategies/retired_candidate.py").exists()


def test_data_csv_safety_governance_latest_and_manual_review_are_never_touched(tmp_path: Path) -> None:
    plan_path = _write_fixture_plan(tmp_path)

    report = build_repository_cleanup_report(
        tmp_path,
        plan_path=plan_path,
        archive_root=tmp_path / "project_archive" / "retired_v0_64_1",
        apply=True,
    )

    assert report["data_csv_touched"] is False
    assert report["safety_files_touched"] is False
    assert report["latest_context_files_touched"] is False
    assert report["manual_review_skipped_count"] == 3
    assert (tmp_path / "data/local.csv").exists()
    assert (tmp_path / "context_data/context.csv").exists()
    assert (tmp_path / "safety_rules.md").exists()
    assert (tmp_path / "manual/review.txt").exists()
    assert (tmp_path / "docs/checkpoints/v0_64_repository_consolidation_plan_result.md").exists()
    assert (tmp_path / "reports/repository_consolidation_plan_v0_64.json").exists()


def test_archive_preserves_relative_paths_and_safety_flags_remain_locked(tmp_path: Path) -> None:
    plan_path = _write_fixture_plan(tmp_path)

    report = build_repository_cleanup_report(
        tmp_path,
        plan_path=plan_path,
        archive_root=tmp_path / "project_archive" / "retired_v0_64_1",
        apply=True,
    )

    assert "docs/checkpoints/v0_10_result.md" in report["archived_paths"]
    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["trade_recommendation_output"] is False
    assert report["recommended_next_step"] == "v0_65_dxy_proxy_context_audit_after_cleanup"


def test_cleanup_applier_does_not_rearchive_restored_active_dependencies(tmp_path: Path) -> None:
    plan_path = _write_fixture_plan(tmp_path)

    report = build_repository_cleanup_report(
        tmp_path,
        plan_path=plan_path,
        archive_root=tmp_path / "project_archive" / "retired_v0_64_1",
        apply=True,
    )

    restored_dependency = tmp_path / "src/research/xauusd_forward_observation_runner.py"
    archived_dependency = (
        tmp_path
        / "project_archive/retired_v0_64_1/src/research/xauusd_forward_observation_runner.py"
    )
    assert restored_dependency.exists()
    assert not archived_dependency.exists()
    assert "src/research/xauusd_forward_observation_runner.py" not in report["planned_archive_paths"]
