"""Apply the reviewed v0_64_1 low-risk repository cleanup plan."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

CLEANUP_VERSION = "v0_64_1"
RECOMMENDED_NEXT_STEP = "v0_65_dxy_proxy_context_audit_after_cleanup"
APPROVED_ARCHIVE_CLASSIFICATIONS = {
    "historical_archive_document_only",
    "retired_experiment_candidate",
    "generated_report_archive_candidate",
}
LATEST_PRESERVED_VERSIONS = {"v0_58", "v0_59", "v0_60", "v0_61", "v0_62", "v0_63", "v0_64"}
PROTECTED_EXACT_PATHS = {
    "safety_rules.md",
    "README.md",
    "config/settings.example.json",
    "scripts/project_health_check.py",
    "scripts/print_codex_context.py",
    "scripts/build_repository_consolidation_plan_v0_64.py",
    "scripts/apply_repository_cleanup_v0_64_1.py",
    "docs/next_codex_handoff.md",
    "docs/codex_operating_notes.md",
    "docs/codex_task_protocol.md",
    "docs/market_context_layer_policy.md",
    "docs/active_project_map.md",
    "docs/retired_experiments_archive.md",
    "project_memory/failed_strategy_registry.md",
    "project_memory/reusable_assets.md",
    "project_memory/codex_usage_contract.md",
    "src/research/candidate_registry.py",
    "src/research/oos_guard.py",
    "src/research/repository_consolidation_plan.py",
    "src/research/repository_cleanup_applier.py",
    "src/research/strategy_candidate.py",
    "src/strategies/xauusd_atr_impulse_reversion.py",
    "src/strategies/xauusd_low_atr_range_expansion_followthrough.py",
    "src/strategies/xauusd_low_atr_x_hour_16_response.py",
    "src/strategies/xauusd_multi_bar_exhaustion_reversion.py",
    "src/strategies/xauusd_session_volatility_expansion.py",
    "tests/test_codex_context_pack.py",
    "tests/test_project_health_check.py",
    "tests/test_repository_consolidation_plan.py",
    "tests/test_repository_cleanup_applier.py",
    "tests/test_research_safety_semantics.py",
}
ACTIVE_DEPENDENCY_PATHS = {
    "src/research/candidate_registry.py",
    "src/research/candidate_stability_diagnostics.py",
    "src/research/oos_guard.py",
    "src/research/repository_cleanup_applier.py",
    "src/research/repository_consolidation_plan.py",
    "src/research/strategy_candidate.py",
    "src/research/strategy_family_selection_board.py",
    "src/research/strategy_research_runner.py",
    "src/research/xauusd_compression_expansion_promotion_gate.py",
    "src/research/xauusd_context_labeled_event_study.py",
    "src/research/xauusd_demo_broker_safety_preflight.py",
    "src/research/xauusd_demo_preflight_review.py",
    "src/research/xauusd_demo_risk_envelope.py",
    "src/research/xauusd_external_shortlist_train_validation_board.py",
    "src/research/xauusd_final_demo_readiness_gate.py",
    "src/research/xauusd_forward_observation_runner.py",
    "src/research/xauusd_historical_data_expansion_feasibility_audit.py",
    "src/research/xauusd_market_context_feasibility_audit.py",
    "src/research/xauusd_market_context_labeler.py",
    "src/research/xauusd_oos_review.py",
    "src/research/xauusd_oos_review_protocol.py",
    "src/research/xauusd_paper_shadow_journal.py",
    "src/research/xauusd_post_oos_governance.py",
    "src/research/xauusd_research_lab_integrity_audit.py",
    "src/research/xauusd_research_lab_warning_standardization.py",
    "src/research/xauusd_second_tier_fixed_rule_board.py",
    "src/research/xauusd_session_block_directional_bias_evaluation.py",
    "src/research/xauusd_session_structure_atlas.py",
    "src/strategies/xauusd_atr_impulse_reversion.py",
    "src/strategies/xauusd_low_atr_range_expansion_followthrough.py",
    "src/strategies/xauusd_low_atr_x_hour_16_response.py",
    "src/strategies/xauusd_multi_bar_exhaustion_reversion.py",
    "src/strategies/xauusd_session_volatility_expansion.py",
    "scripts/export_mt5_xauusd_low_tf.py",
    "scripts/resample_xauusd_timeframe.py",
    "reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json",
    "reports/xauusd_compression_expansion_decision_v0_26.json",
    "reports/xauusd_compression_expansion_promotion_gate_v0_27.json",
    "reports/xauusd_forward_observation_ledger_v0_36_cycle_2026-06-16.json",
}


def _as_posix(path: str | Path) -> str:
    return Path(path).as_posix()


def _is_cache_path(rel_path: str) -> bool:
    parts = rel_path.split("/")
    return "__pycache__" in parts or ".pytest_cache" in parts or rel_path.endswith(".pyc")


def _is_data_csv(rel_path: str) -> bool:
    lower = rel_path.lower()
    return (lower.startswith("data/") or lower.startswith("context_data/")) and lower.endswith(".csv")


def _is_latest_context_path(rel_path: str) -> bool:
    lower = rel_path.lower()
    if not lower.startswith(("reports/", "docs/checkpoints/")):
        return False
    return any(version in rel_path for version in LATEST_PRESERVED_VERSIONS)


def _is_protected(rel_path: str) -> bool:
    if rel_path in PROTECTED_EXACT_PATHS or rel_path in ACTIVE_DEPENDENCY_PATHS:
        return True
    if _is_data_csv(rel_path):
        return True
    if _is_latest_context_path(rel_path):
        return True
    return False


def _safe_target(root: Path, rel_path: str) -> Path:
    target = (root / rel_path).resolve()
    if root.resolve() not in (target, *target.parents):
        raise ValueError(f"path escapes repository root: {rel_path}")
    return target


def _load_plan(plan_path: Path) -> dict[str, Any]:
    return json.loads(plan_path.read_text(encoding="utf-8"))


def _classification_items(plan: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for item in plan.get("classification_index", []):
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        classification = item.get("classification")
        if isinstance(path, str) and isinstance(classification, str):
            items.append({"path": _as_posix(path), "classification": classification})
    return items


def _count_existing(root: Path, paths: list[str]) -> int:
    return sum(1 for rel_path in paths if (root / rel_path).exists())


def _cleanup_empty_cache_dirs(root: Path, deleted_paths: list[str]) -> None:
    cache_dirs = sorted(
        {
            parent
            for rel_path in deleted_paths
            for parent in Path(rel_path).parents
            if parent.as_posix() != "." and parent.name in {"__pycache__", ".pytest_cache"}
        },
        key=lambda item: len(item.parts),
        reverse=True,
    )
    for rel_dir in cache_dirs:
        target = _safe_target(root, rel_dir.as_posix())
        if target.exists() and target.is_dir():
            shutil.rmtree(target)


def build_repository_cleanup_report(
    root: Path,
    *,
    plan_path: Path,
    archive_root: Path,
    apply: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    plan_path = plan_path if plan_path.is_absolute() else root / plan_path
    archive_root = archive_root if archive_root.is_absolute() else root / archive_root
    plan = _load_plan(plan_path)
    items = _classification_items(plan)

    cache_candidates = [
        item["path"]
        for item in items
        if item["classification"] == "cache_delete_candidate" and _is_cache_path(item["path"]) and not _is_protected(item["path"])
    ]
    archive_candidates = [
        item["path"]
        for item in items
        if item["classification"] in APPROVED_ARCHIVE_CLASSIFICATIONS and not _is_protected(item["path"])
    ]
    preserved = [
        item["path"]
        for item in items
        if item["classification"] not in APPROVED_ARCHIVE_CLASSIFICATIONS | {"cache_delete_candidate"} or _is_protected(item["path"])
    ]
    manual_review_skipped = [item["path"] for item in items if item["classification"] == "manual_review_required"]

    archived_paths: list[str] = []
    deleted_paths: list[str] = []
    blocked_reasons: list[str] = []
    archive_root_resolved = archive_root.resolve()
    if root in (archive_root_resolved, *archive_root_resolved.parents):
        pass
    else:
        blocked_reasons.append("archive_root_outside_repository")

    if apply and not blocked_reasons:
        archive_root_resolved.mkdir(parents=True, exist_ok=True)
        for rel_path in archive_candidates:
            source = _safe_target(root, rel_path)
            destination = archive_root_resolved / rel_path
            if not source.exists():
                if destination.exists():
                    archived_paths.append(rel_path)
                continue
            if source.is_dir():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                blocked_reasons.append(f"archive_destination_exists:{rel_path}")
                continue
            shutil.move(str(source), str(destination))
            archived_paths.append(rel_path)

        for rel_path in cache_candidates:
            source = _safe_target(root, rel_path)
            if not source.exists():
                deleted_paths.append(rel_path)
                continue
            if source.is_dir():
                shutil.rmtree(source)
            else:
                source.unlink()
            deleted_paths.append(rel_path)
        _cleanup_empty_cache_dirs(root, deleted_paths)

    status = "cleanup_blocked" if blocked_reasons else ("cleanup_applied_completed" if apply else "dry_run_completed")
    after_archive_remaining = _count_existing(root, archive_candidates)
    after_cache_remaining = _count_existing(root, cache_candidates)

    return {
        "cleanup_version": CLEANUP_VERSION,
        "cleanup_status": status,
        "dry_run": not apply,
        "apply_requested": apply,
        "files_deleted_count": len(deleted_paths),
        "files_archived_count": len(archived_paths),
        "files_preserved_count": len(preserved),
        "manual_review_skipped_count": len(manual_review_skipped),
        "data_csv_touched": False,
        "safety_files_touched": False,
        "latest_context_files_touched": False,
        "archive_root": archive_root.relative_to(root).as_posix() if root in (archive_root.resolve(), *archive_root.resolve().parents) else str(archive_root),
        "before_counts": {
            "files_scanned_count": plan.get("files_scanned_count"),
            "active_keep_count": plan.get("active_keep_count"),
            "archive_candidate_count": plan.get("archive_candidate_count"),
            "delete_candidate_count": plan.get("delete_candidate_count"),
            "manual_review_count": plan.get("manual_review_count"),
            "planned_cache_delete_count": len(cache_candidates),
            "planned_archive_count": len(archive_candidates),
        },
        "after_counts": {
            "archive_candidates_remaining": after_archive_remaining,
            "cache_candidates_remaining": after_cache_remaining,
            "archive_files_present": _count_existing(archive_root_resolved, archived_paths) if archive_root_resolved.exists() else 0,
        },
        "approved_for_strategy_testing": False,
        "approved_for_trade_filtering": False,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "executable_candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "trade_recommendation_output": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "source_plan": plan_path.relative_to(root).as_posix() if root in (plan_path.resolve(), *plan_path.resolve().parents) else str(plan_path),
        "archive_classifications_applied": sorted(APPROVED_ARCHIVE_CLASSIFICATIONS),
        "planned_archive_paths": archive_candidates,
        "planned_delete_paths": cache_candidates,
        "archived_paths": archived_paths,
        "deleted_paths": deleted_paths,
        "manual_review_skipped_paths": manual_review_skipped,
        "preserved_classification_counts": dict(Counter(item["classification"] for item in items if item["path"] in preserved)),
        "blocked_reasons": blocked_reasons,
    }


def write_repository_cleanup_report(
    root: Path,
    *,
    plan_path: Path,
    archive_root: Path,
    output_path: Path,
    apply: bool = False,
) -> dict[str, Any]:
    report = build_repository_cleanup_report(root, plan_path=plan_path, archive_root=archive_root, apply=apply)
    output_path = output_path if output_path.is_absolute() else root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
