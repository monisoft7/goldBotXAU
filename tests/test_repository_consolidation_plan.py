from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from src.research.repository_consolidation_plan import (
    build_repository_consolidation_plan,
    classify_path,
    failed_experiments_index,
)

ROOT = Path(__file__).resolve().parents[1]


def test_cache_files_are_delete_candidates(tmp_path: Path) -> None:
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "example.cpython-314.pyc").write_bytes(b"cache")

    report = build_repository_consolidation_plan(tmp_path)

    cache_paths = {item["path"]: item["classification"] for item in report["classification_index"]}
    assert cache_paths[".pytest_cache"] == "cache_delete_candidate"
    assert cache_paths["__pycache__"] == "cache_delete_candidate"
    assert cache_paths["__pycache__/example.cpython-314.pyc"] == "cache_delete_candidate"
    assert report["delete_candidate_count"] >= 3


def test_data_csv_files_are_never_active_core_keep() -> None:
    report = build_repository_consolidation_plan(ROOT)
    data_csv_classifications = {
        item["path"]: item["classification"]
        for item in report["classification_index"]
        if item["path"].startswith("data/") and item["path"].endswith(".csv")
    }

    assert data_csv_classifications
    assert all(
        classification in {"local_data_only", "manual_review_required"}
        for classification in data_csv_classifications.values()
    )
    assert "active_core_keep" not in set(data_csv_classifications.values())


def test_failed_candidates_are_indexed_from_existing_evidence() -> None:
    failures = failed_experiments_index(ROOT)
    names = {entry["candidate_name"] for entry in failures}

    assert "xauusd_atr_impulse_reversion_v0_7" in names
    assert "xauusd_low_tf_spike_m5_hour_11_fade_v0_23" in names
    assert "trend_pullback_continuation_directional" in names
    assert "session_block_directional_bias_candidate" in names
    assert "ny_liquidity_sweep_reversal" in names
    assert any(entry["source_report_or_checkpoint"].endswith("xauusd_second_tier_board_v0_60.json") for entry in failures)


def test_safety_files_are_preserved() -> None:
    report = build_repository_consolidation_plan(ROOT)
    classifications = {item["path"]: item["classification"] for item in report["classification_index"]}

    assert classifications["safety_rules.md"] == "active_safety_keep"
    assert classifications["docs/research_lab_gate_policy.md"] == "active_safety_keep"
    assert classifications["src/research/oos_guard.py"] == "active_safety_keep"


def test_latest_v0_58_to_v0_63_reports_and_checkpoints_are_preserved() -> None:
    report = build_repository_consolidation_plan(ROOT)
    classifications = {item["path"]: item["classification"] for item in report["classification_index"]}

    for version in ("v0_58", "v0_59", "v0_60", "v0_61", "v0_62", "v0_63"):
        matching = [
            path
            for path in classifications
            if path.startswith(("reports/", "docs/checkpoints/")) and version in path
        ]
        assert matching, version
        assert all(classifications[path].startswith("active_") for path in matching), version


def test_no_cleanup_is_applied_in_v0_64() -> None:
    report = build_repository_consolidation_plan(ROOT)

    assert report["safe_to_apply_cleanup_now"] is False
    assert report["cleanup_requires_human_review"] is True
    assert report["cleanup_actions_applied"] == []
    assert report["recommended_next_step"] == "v0_64_1_apply_reviewed_cleanup_plan_no_strategy_changes"


def test_safety_flags_remain_false_or_locked() -> None:
    report = build_repository_consolidation_plan(ROOT)

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


def test_classify_tracked_data_csv_as_manual_review() -> None:
    classification = classify_path(
        "data/xauusd_m15_xauusd_2023-01-01_2026-06-11.csv",
        failed_tokens=set(),
        tracked_data_csv={"data/xauusd_m15_xauusd_2023-01-01_2026-06-11.csv"},
    )

    assert classification == "manual_review_required"


def test_project_archive_is_excluded_from_default_pytest_collection() -> None:
    pytest_config = (ROOT / "pytest.ini").read_text(encoding="utf-8")

    assert "testpaths = tests" in pytest_config
    assert "project_archive" in pytest_config

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "project_archive/retired_v0_64_1/tests" not in completed.stdout.replace("\\", "/")


def test_project_archive_is_ignored_by_repository_scanner() -> None:
    report = build_repository_consolidation_plan(ROOT)

    assert all(
        not item["path"].startswith("project_archive/")
        for item in report["classification_index"]
    )


def test_active_import_dependencies_are_not_archive_candidates() -> None:
    report = build_repository_consolidation_plan(ROOT)
    classifications = {item["path"]: item["classification"] for item in report["classification_index"]}

    active_dependencies = {
        "src/research/xauusd_forward_observation_runner.py",
        "src/research/xauusd_external_shortlist_train_validation_board.py",
        "src/research/xauusd_session_structure_atlas.py",
        "src/research/xauusd_compression_expansion_promotion_gate.py",
        "src/research/xauusd_paper_shadow_journal.py",
        "scripts/export_mt5_xauusd_low_tf.py",
        "scripts/resample_xauusd_timeframe.py",
        "reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json",
        "reports/xauusd_compression_expansion_promotion_gate_v0_27.json",
        "reports/xauusd_forward_observation_ledger_v0_36_cycle_2026-06-16.json",
    }

    for path in active_dependencies:
        assert classifications[path] == "active_dependency_keep"
