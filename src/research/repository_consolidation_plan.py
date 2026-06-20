"""Repository consolidation planning for v0_64.

This module is intentionally read-only. It inventories files, classifies cleanup
review candidates, and indexes failed experiments without deleting anything.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from src.research.candidate_registry import research_candidate_registry

CONSOLIDATION_VERSION = "v0_64"
RECOMMENDED_NEXT_STEP = "v0_64_1_apply_reviewed_cleanup_plan_no_strategy_changes"

ACTIVE_VERSIONS = {"v0_58", "v0_59", "v0_60", "v0_61", "v0_62", "v0_63", "v0_64"}
SAFETY_KEYWORDS = {
    "safety",
    "governance",
    "oos",
    "demo",
    "execution",
    "executor",
    "order",
    "risk",
    "preflight",
    "readiness",
    "macro",
    "gate_policy",
}
DATA_CONTRACT_KEYWORDS = {
    "data",
    "dataset",
    "csv_loader",
    "resampler",
    "manifest",
    "timestamp",
    "gap_classification",
    "cost_policy",
    "gate_policy",
}
CONTEXT_KEYWORDS = {
    "market_context",
    "context_labeled",
    "research_lab",
    "second_tier",
    "codex_context",
    "active_project_map",
    "retired_experiments_archive",
    "repository_consolidation",
}
RETIRED_EXPERIMENT_HINTS = {
    "atr_impulse",
    "multi_bar_exhaustion",
    "session_volatility",
    "low_atr",
    "spike",
    "direction_research",
    "new_directional",
    "trend_pullback",
    "external_shortlist",
    "session_block",
    "second_tier",
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


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _version_key(version: str) -> tuple[int, ...]:
    if not version.startswith("v"):
        return (9999,)
    return tuple(int(part) for part in version[1:].split("_") if part.isdigit())


def _versions_in_text(text: str) -> list[str]:
    return re.findall(r"v\d+_\d+(?:_\d+)?", text)


def _first_version(text: str) -> str | None:
    versions = _versions_in_text(text)
    return versions[-1] if versions else None


def _is_cache_path(rel_path: str) -> bool:
    parts = rel_path.split("/")
    return "__pycache__" in parts or ".pytest_cache" in parts or rel_path.endswith(".pyc")


def _path_entries(root: Path) -> list[Path]:
    entries: list[Path] = []
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if ".git" in rel_parts or "project_archive" in rel_parts:
            continue
        entries.append(path)
    return sorted(entries, key=lambda item: _rel(item, root))


def _tracked_data_csv_files(root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "ls-files", "data/*.csv"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return sorted(line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip())


def _reason_from_result(result: dict[str, Any], fallback_status: str) -> str:
    for key in ("gate_failures", "blockers", "failed_checks"):
        value = result.get(key)
        if isinstance(value, list) and value:
            return ",".join(str(item) for item in value)
    if result.get("passed_gate") is False:
        return "passed_gate_false"
    if result.get("candidate_passed_train_validation_gate") is False:
        return "candidate_passed_train_validation_gate_false"
    return fallback_status


def _failed_entry(
    *,
    candidate_name: str,
    version: str | None,
    status: str,
    reason: str,
    do_not_retune: bool,
    oos_used: bool,
    approved_for_demo_or_live: bool,
    source: str,
) -> dict[str, Any]:
    return {
        "candidate_name": candidate_name,
        "version": version or "unknown",
        "status": status,
        "reason_for_rejection": reason,
        "do_not_retune": do_not_retune,
        "oos_used": oos_used,
        "approved_for_demo_or_live": approved_for_demo_or_live,
        "source_report_or_checkpoint": source,
    }


def _index_registry_failures() -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    registry = research_candidate_registry()
    for candidate in registry["candidates"]:
        status = str(candidate.get("status", ""))
        if not (status == "rejected" or status.startswith("rejected_")):
            continue
        candidate_id = str(candidate["candidate_id"])
        failures.append(
            _failed_entry(
                candidate_name=candidate_id,
                version=_first_version(candidate_id),
                status=status,
                reason=str(candidate.get("rejection_reason", "registry_rejected")),
                do_not_retune=candidate.get("do_not_retune") is True,
                oos_used=candidate.get("oos_status") == "evaluated_passed",
                approved_for_demo_or_live=False,
                source="src/research/candidate_registry.py",
            )
        )
    return failures


def _index_json_failures(root: Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    report_paths = []
    if (root / "reports").exists():
        report_paths.extend(sorted((root / "reports").glob("*.json")))
    archive_reports = root / "project_archive" / "retired_v0_64_1" / "reports"
    if archive_reports.exists():
        report_paths.extend(sorted(archive_reports.glob("*.json")))
    for path in report_paths:
        rel_path = _rel(path, root)
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        version = (
            report.get("board_version")
            or report.get("evaluation_version")
            or report.get("retest_version")
            or report.get("context_study_version")
            or _first_version(path.name)
        )

        for result in report.get("candidate_results", []) if isinstance(report.get("candidate_results"), list) else []:
            if not isinstance(result, dict) or not result.get("candidate_id"):
                continue
            status = str(result.get("candidate_disposition") or ("rejected_do_not_retune" if result.get("passed_gate") is False else ""))
            if "rejected" not in status and result.get("passed_gate") is not False:
                continue
            safety = result.get("safety", {}) if isinstance(result.get("safety"), dict) else {}
            failures.append(
                _failed_entry(
                    candidate_name=str(result["candidate_id"]),
                    version=str(version),
                    status=status or "failed_train_validation_gate",
                    reason=_reason_from_result(result, status or str(report.get("board_status", "failed"))),
                    do_not_retune=result.get("do_not_retune") is True or "do_not_retune" in status,
                    oos_used=safety.get("oos_used") is True or result.get("oos_used") is True,
                    approved_for_demo_or_live=safety.get("demo_execution_allowed") is True
                    or safety.get("live_allowed") is True
                    or result.get("demo_execution_allowed") is True
                    or result.get("live_allowed") is True,
                    source=rel_path,
                )
            )

        top_candidate = report.get("candidate_id")
        top_status = str(
            report.get("evaluation_status")
            or report.get("retest_status")
            or report.get("gate_status")
            or report.get("board_status")
            or ""
        )
        top_failed = (
            isinstance(top_candidate, str)
            and top_candidate != "xauusd_compression_then_expansion_v0_26"
            and (
                "rejected" in top_status
                or "failed" in top_status
                or report.get("candidate_passed_train_validation_gate") is False
                or report.get("expanded_evidence_passed_gate") is False
            )
        )
        if top_failed:
            failures.append(
                _failed_entry(
                    candidate_name=top_candidate,
                    version=str(version),
                    status=top_status or "failed_train_validation_gate",
                    reason=_reason_from_result(report, top_status or "failed"),
                    do_not_retune=report.get("rejected_do_not_retune") is True
                    or report.get("candidate_locking_allowed_pre_oos") is False,
                    oos_used=report.get("oos_used") is True,
                    approved_for_demo_or_live=report.get("demo_execution_allowed") is True
                    or report.get("live_allowed") is True,
                    source=rel_path,
                )
            )

    return failures


def failed_experiments_index(root: Path) -> list[dict[str, Any]]:
    indexed: dict[tuple[str, str, str], dict[str, Any]] = {}
    for entry in [*_index_registry_failures(), *_index_json_failures(root)]:
        key = (entry["candidate_name"], entry["version"], entry["source_report_or_checkpoint"])
        indexed[key] = entry
    return sorted(indexed.values(), key=lambda entry: (_version_key(entry["version"]), entry["candidate_name"]))


def _retired_candidate_names(failures: list[dict[str, Any]]) -> set[str]:
    names = {str(entry["candidate_name"]) for entry in failures}
    tokens: set[str] = set()
    for name in names:
        tokens.add(name)
        tokens.update(part for part in name.split("_") if len(part) >= 5)
    tokens.update(RETIRED_EXPERIMENT_HINTS)
    return tokens


def classify_path(rel_path: str, *, failed_tokens: set[str], tracked_data_csv: set[str]) -> str:
    lower = rel_path.lower()
    name = Path(rel_path).name.lower()

    if _is_cache_path(rel_path):
        return "cache_delete_candidate"
    if lower.startswith("data/") and lower.endswith(".csv"):
        return "manual_review_required" if rel_path in tracked_data_csv else "local_data_only"
    if lower in {"safety_rules.md", "project_memory/codex_usage_contract.md"}:
        return "active_safety_keep"
    if any(keyword in lower for keyword in SAFETY_KEYWORDS):
        return "active_safety_keep"
    if rel_path in ACTIVE_DEPENDENCY_PATHS:
        return "active_dependency_keep"
    if any(keyword in lower for keyword in CONTEXT_KEYWORDS):
        version = _first_version(rel_path)
        if version is None or version in ACTIVE_VERSIONS:
            return "active_context_layer_keep"
    if any(keyword in lower for keyword in DATA_CONTRACT_KEYWORDS):
        return "active_data_contract_keep"
    if lower.startswith(("docs/checkpoints/", "reports/")) and any(version in rel_path for version in ACTIVE_VERSIONS):
        return "active_context_layer_keep"
    if lower.startswith(("src/", "scripts/", "tests/")) and any(token in lower for token in failed_tokens):
        return "retired_experiment_candidate"
    if lower.startswith("reports/"):
        if name.startswith(("codex_context_", "project_health_")):
            return "generated_report_archive_candidate"
        return "historical_archive_document_only"
    if lower.startswith("docs/checkpoints/"):
        return "historical_archive_document_only"
    if lower.startswith(("src/", "scripts/", "tests/", "config/", ".github/")):
        return "active_core_keep"
    if lower.startswith(("docs/", "project_memory/")):
        return "active_context_layer_keep"
    if lower in {".gitignore", ".gitattributes", "readme.md"}:
        return "active_data_contract_keep"
    return "manual_review_required"


def _count_by_version(paths: list[str], prefix: str | None = None) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for rel_path in paths:
        if prefix and not rel_path.startswith(prefix):
            continue
        version = _first_version(rel_path)
        if version:
            counts[version] += 1
    return dict(sorted(counts.items(), key=lambda item: _version_key(item[0])))


def build_repository_consolidation_plan(root: Path) -> dict[str, Any]:
    root = root.resolve()
    entries = _path_entries(root)
    rel_entries = [_rel(path, root) for path in entries]
    file_paths = [path for path in entries if path.is_file()]
    rel_files = [_rel(path, root) for path in file_paths]
    tracked_csv = _tracked_data_csv_files(root)
    failures = failed_experiments_index(root)
    failed_tokens = _retired_candidate_names(failures)

    classifications = [
        {
            "path": rel_path,
            "classification": classify_path(rel_path, failed_tokens=failed_tokens, tracked_data_csv=set(tracked_csv)),
        }
        for rel_path in rel_entries
    ]
    classification_counts = Counter(item["classification"] for item in classifications)
    active_keep_count = sum(
        classification_counts[label]
        for label in (
            "active_core_keep",
            "active_safety_keep",
            "active_context_layer_keep",
            "active_data_contract_keep",
            "active_dependency_keep",
        )
    )
    archive_candidate_count = sum(
        classification_counts[label]
        for label in (
            "historical_archive_document_only",
            "retired_experiment_candidate",
            "generated_report_archive_candidate",
        )
    )
    delete_candidate_count = classification_counts["cache_delete_candidate"]

    directory_counts = Counter(rel_file.split("/", 1)[0] if "/" in rel_file else "." for rel_file in rel_files)
    cache_files = [rel_path for rel_path in rel_entries if _is_cache_path(rel_path)]
    retired_paths = [
        item["path"]
        for item in classifications
        if item["classification"] == "retired_experiment_candidate"
    ]

    return {
        "consolidation_version": CONSOLIDATION_VERSION,
        "consolidation_status": "repository_consolidation_plan_completed",
        "files_scanned_count": len(rel_files),
        "active_keep_count": active_keep_count,
        "archive_candidate_count": archive_candidate_count,
        "delete_candidate_count": delete_candidate_count,
        "manual_review_count": classification_counts["manual_review_required"],
        "tracked_data_csv_files": tracked_csv,
        "cache_files_detected": cache_files,
        "failed_experiments_indexed_count": len(failures),
        "safe_to_apply_cleanup_now": False,
        "cleanup_requires_human_review": True,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
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
        "directory_file_counts": dict(sorted(directory_counts.items())),
        "report_counts_by_version": _count_by_version(rel_files, "reports/"),
        "script_counts_by_version": _count_by_version(rel_files, "scripts/"),
        "test_counts_by_version": _count_by_version(rel_files, "tests/"),
        "classification_counts": dict(sorted(classification_counts.items())),
        "classification_index": classifications,
        "retired_experiment_candidate_paths": retired_paths,
        "failed_experiments": failures,
        "latest_preserved_versions": sorted(ACTIVE_VERSIONS, key=_version_key),
        "cleanup_actions_applied": [],
    }


def write_repository_consolidation_plan(root: Path, output_path: Path) -> dict[str, Any]:
    report = build_repository_consolidation_plan(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
