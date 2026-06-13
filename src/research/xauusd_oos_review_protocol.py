"""v0_28 OOS review protocol builder for the fixed compression-expansion candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.research.candidate_registry import research_candidate_registry
from src.research.xauusd_compression_expansion_promotion_gate import (
    FIXED_GATE,
    PROMOTE_DECISION,
    SOURCE_CANDIDATE_ID,
)

PROTOCOL_VERSION = "v0_28"
PROTOCOL_DECISION = "create_oos_review_protocol_pending_future_human_approval"
BLOCKED_DECISION = "blocked_oos_review_protocol_not_created"

DEFAULT_PROMOTION_GATE_REPORT = Path("reports") / "xauusd_compression_expansion_promotion_gate_v0_27.json"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_DATASET_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"
DEFAULT_OUTPUT_REPORT = Path("reports") / "xauusd_oos_review_protocol_v0_28.json"
DEFAULT_FUTURE_OOS_REPORT = Path("reports") / "xauusd_oos_review_v0_29.json"

ALLOWED_FUTURE_OOS_SCRIPT = "scripts/run_xauusd_oos_review_v0_29.py"
HUMAN_APPROVAL_TOKEN = "HUMAN_APPROVED_OOS_REVIEW_V0_29"
ALLOWED_FUTURE_OOS_COMMAND = (
    "py -3 scripts/run_xauusd_oos_review_v0_29.py "
    "--protocol reports/xauusd_oos_review_protocol_v0_28.json "
    "--approval-token HUMAN_APPROVED_OOS_REVIEW_V0_29 "
    "--json --output reports/xauusd_oos_review_v0_29.json"
)

SAFETY_FLAGS = {
    "demo_enabled": False,
    "live_enabled": False,
    "order_send_allowed": False,
    "order_check_allowed": False,
    "execution_queue_enabled": False,
    "execution_logic_present": False,
    "trade_recommendation_output_present": False,
    "trade_direction_output_allowed": False,
    "oos_evaluated": False,
    "oos_rows_read": 0,
    "oos_metrics_created": False,
    "threshold_search_used": False,
    "parameter_grid_used": False,
    "candidate_rules_modified": False,
    "rejected_candidate_retuned": False,
}


def build_xauusd_oos_review_protocol_v0_28(
    promotion_gate_report_path: str | Path = DEFAULT_PROMOTION_GATE_REPORT,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    dataset_manifest_path: str | Path = DEFAULT_DATASET_MANIFEST,
    future_oos_report_path: str | Path = DEFAULT_FUTURE_OOS_REPORT,
    *,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only protocol for a later one-time OOS review."""

    gate_path = Path(promotion_gate_report_path)
    candidate_path = Path(candidate_report_path)
    manifest_path = Path(dataset_manifest_path)
    future_result_path = Path(future_oos_report_path)
    registry_payload = registry if registry is not None else research_candidate_registry()

    gate_report, gate_errors = _load_json(gate_path, "promotion_gate_report")
    candidate_report, candidate_errors = _load_json(candidate_path, "candidate_report")
    manifest, manifest_errors = _load_json(manifest_path, "dataset_manifest")
    blockers = gate_errors + candidate_errors + manifest_errors

    blockers.extend(_registry_blockers(registry_payload))
    if gate_report is not None:
        blockers.extend(_promotion_gate_blockers(gate_report))
    if candidate_report is not None:
        blockers.extend(_candidate_report_blockers(candidate_report))
    if manifest is not None:
        blockers.extend(_manifest_blockers(manifest))
    if future_result_path.exists():
        blockers.append("future_oos_result_already_exists")

    if blockers:
        return _blocked_protocol(
            blockers=blockers,
            gate_path=gate_path,
            candidate_path=candidate_path,
            manifest_path=manifest_path,
            future_result_path=future_result_path,
        )

    assert gate_report is not None
    assert candidate_report is not None
    assert manifest is not None

    fixed_rules = candidate_report["fixed_rules"]
    split_policy = manifest["split_policy"]
    out_of_sample = manifest["splits"]["out_of_sample"]

    return {
        "protocol_version": PROTOCOL_VERSION,
        "decision": PROTOCOL_DECISION,
        "candidate_id": SOURCE_CANDIDATE_ID,
        "candidate_status_at_protocol_build": "eligible_for_oos_review_pending_human_approval",
        "source_reports": {
            "promotion_gate_report": str(gate_path),
            "candidate_report": str(candidate_path),
            "dataset_manifest": str(manifest_path),
        },
        "eligibility_confirmation": {
            "eligible_for_oos_review_count": registry_payload["eligible_for_oos_review_count"],
            "eligible_candidate_id": SOURCE_CANDIDATE_ID,
            "promotion_gate_decision": gate_report["decision"],
            "oos_status": "locked_not_evaluated",
            "human_approval_required_before_oos": True,
        },
        "fixed_rules_source": {
            "report": str(candidate_path),
            "candidate_id": SOURCE_CANDIDATE_ID,
            "source_atlas": candidate_report["source_atlas"],
            "source_family": candidate_report["source_family"],
            "rules_hash_sha256": _stable_hash(fixed_rules),
            "rules": fixed_rules,
        },
        "oos_split_boundaries": {
            "source_manifest": str(manifest_path),
            "split_policy": {
                "method": split_policy["method"],
                "leakage_prevention": split_policy["leakage_prevention"],
                "train_end": split_policy["train_end"],
                "validation_start": split_policy["validation_start"],
                "validation_end": split_policy["validation_end"],
                "oos_start": split_policy["oos_start"],
            },
            "out_of_sample": {
                "start": out_of_sample["start"],
                "end": out_of_sample["end"],
            },
        },
        "allowed_future_oos_review": {
            "script": ALLOWED_FUTURE_OOS_SCRIPT,
            "exact_command": ALLOWED_FUTURE_OOS_COMMAND,
            "approval_token_required": HUMAN_APPROVAL_TOKEN,
            "may_run_in_v0_28": False,
            "script_created_in_v0_28": False,
            "result_path": str(future_result_path),
        },
        "pass_fail_criteria": {
            "must_use_fixed_rules_hash_sha256": _stable_hash(fixed_rules),
            "minimum_combined_oos_primary_metric_rate": FIXED_GATE["minimum_combined_validation_primary_metric_rate"],
            "minimum_combined_oos_edge_over_neutral": FIXED_GATE["minimum_combined_validation_edge_over_neutral"],
            "maximum_combined_oos_degradation_vs_validation": FIXED_GATE[
                "maximum_combined_validation_degradation_vs_train"
            ],
            "minimum_timeframe_oos_primary_metric_rate": FIXED_GATE["minimum_timeframe_validation_primary_metric_rate"],
            "minimum_timeframe_oos_edge_over_neutral": FIXED_GATE["minimum_timeframe_validation_edge_over_neutral"],
            "maximum_timeframe_oos_degradation_vs_validation": FIXED_GATE[
                "maximum_timeframe_validation_degradation_vs_train"
            ],
            "required_timeframes": FIXED_GATE["required_timeframes"],
            "required_reference_windows": FIXED_GATE["required_reference_windows"],
            "required_response_windows": FIXED_GATE["required_response_windows"],
            "must_report_m5_and_m10_separately": True,
            "combined_timeframe_counts_must_not_be_treated_as_independent_confidence": True,
            "must_pass_all_leakage_controls": True,
            "must_preserve_all_safety_flags": True,
        },
        "leakage_controls": {
            "protocol_builder_reads_oos_rows": False,
            "future_review_may_read_only_oos_rows_after_approval": True,
            "chronological_only_no_shuffle": True,
            "no_oos_data_may_change_rules": True,
            "no_oos_data_may_change_thresholds": True,
            "no_train_validation_recalculation_during_oos_review": True,
            "future_review_must_abort_if_result_path_already_exists": True,
            "future_review_must_abort_if_rules_hash_mismatch": True,
        },
        "one_time_review_policy": {
            "one_time_only": True,
            "current_oos_result_exists": False,
            "rerun_allowed": False,
            "future_result_path": str(future_result_path),
        },
        "no_retune_policy_after_oos": {
            "candidate_rules_may_be_changed_after_oos": False,
            "threshold_search_after_oos_allowed": False,
            "parameter_grid_after_oos_allowed": False,
            "failed_oos_candidate_must_not_be_retuned": True,
        },
        "if_oos_passes": [
            "Create a post-OOS checkpoint and keep the candidate research-only pending human review.",
            "Do not add execution, order, demo, live, or trade-direction output.",
            "Require a separate future promotion protocol before any strategy status change.",
        ],
        "if_oos_fails": [
            "Mark the candidate rejected with do_not_retune true.",
            "Do not alter thresholds, parameters, or fixed rules to rescue the candidate.",
            "Move to a different non-blacklisted research family.",
        ],
        "created_metrics": {
            "oos_performance_results_created": False,
            "oos_rows_evaluated": 0,
            "oos_rows_read": 0,
        },
        "safety": dict(SAFETY_FLAGS),
        "recommended_next_step": (
            "v0_29 may run the one-time OOS review only after explicit human approval using the exact command."
        ),
    }


def save_xauusd_oos_review_protocol_report(
    report: dict[str, Any],
    output_path: str | Path = DEFAULT_OUTPUT_REPORT,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_missing"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{label}_invalid_json: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{label}_not_object"]
    return payload, []


def _registry_blockers(registry: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    eligible_count = registry.get("eligible_for_oos_review_count")
    if eligible_count != 1:
        blockers.append("eligible_candidate_count_not_exactly_1")
    if registry.get("oos_locked") is not True:
        blockers.append("registry_oos_not_locked")

    eligible_candidates = [
        candidate for candidate in registry.get("candidates", []) if candidate.get("eligible_for_oos_review") is True
    ]
    if len(eligible_candidates) == 1:
        candidate = eligible_candidates[0]
        if candidate.get("candidate_id") != SOURCE_CANDIDATE_ID:
            blockers.append("eligible_candidate_is_not_v0_26_compression_expansion")
        if candidate.get("oos_status") != "locked_not_evaluated":
            blockers.append("eligible_candidate_oos_status_not_locked")
        if candidate.get("human_approval_required_before_oos") is not True:
            blockers.append("eligible_candidate_missing_human_approval_requirement")
        for flag in ("threshold_search_used", "parameter_grid_used", "retuned_rejected_candidate"):
            if candidate.get(flag) is not False:
                blockers.append(f"eligible_candidate_{flag}_not_false")
    return blockers


def _promotion_gate_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if report.get("gate_version") != "v0_27":
        blockers.append("promotion_gate_version_not_v0_27")
    if report.get("candidate_id") != SOURCE_CANDIDATE_ID:
        blockers.append("promotion_gate_candidate_id_mismatch")
    if report.get("decision") != PROMOTE_DECISION:
        blockers.append("promotion_gate_did_not_promote_to_oos_review")
    update = report.get("candidate_registry_update", {})
    if update.get("eligible_for_oos_review") is not True:
        blockers.append("promotion_gate_candidate_not_marked_oos_eligible")
    if update.get("human_approval_required_before_oos") is not True:
        blockers.append("promotion_gate_missing_human_approval_requirement")
    if update.get("oos_status") != "locked_not_evaluated":
        blockers.append("promotion_gate_oos_status_not_locked")
    evidence = report.get("evidence_summary", {})
    if evidence.get("oos_evaluated") is not False:
        blockers.append("promotion_gate_oos_already_evaluated")
    if int(evidence.get("oos_rows_used", -1) or 0) != 0:
        blockers.append("promotion_gate_used_oos_rows")
    safety = report.get("safety", {})
    for flag in (
        "oos_evaluated",
        "threshold_search_used",
        "parameter_grid_used",
        "rejected_candidate_retuned",
        "trade_recommendation_output_present",
        "execution_logic_present",
    ):
        if safety.get(flag) is not False:
            blockers.append(f"promotion_gate_safety_{flag}_not_false")
    return blockers


def _candidate_report_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if report.get("candidate_id") != SOURCE_CANDIDATE_ID:
        blockers.append("candidate_report_candidate_id_mismatch")
    if report.get("status") != "train_validation_research_candidate_only":
        blockers.append("candidate_report_not_train_validation_research_only")
    if int(report.get("oos_rows_used", -1) or 0) != 0:
        blockers.append("candidate_report_used_oos_rows")
    if report.get("evaluation_scope", {}).get("oos_evaluated") is not False:
        blockers.append("candidate_report_oos_already_evaluated")
    if not isinstance(report.get("fixed_rules"), dict):
        blockers.append("candidate_report_fixed_rules_missing")
    fixed_rules = report.get("fixed_rules", {})
    for flag in ("threshold_search_used", "parameter_grid_used", "retuning_used"):
        if fixed_rules.get(flag) is not False:
            blockers.append(f"candidate_fixed_rules_{flag}_not_false")
    safety = report.get("safety", {})
    for flag in (
        "oos_evaluated",
        "threshold_search_used",
        "parameter_grid_used",
        "rejected_candidate_retuned",
        "trade_recommendation_output_present",
        "execution_logic_present",
    ):
        if safety.get(flag) is not False:
            blockers.append(f"candidate_safety_{flag}_not_false")
    return blockers


def _manifest_blockers(manifest: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    split_policy = manifest.get("split_policy", {})
    splits = manifest.get("splits", {})
    out_of_sample = splits.get("out_of_sample", {})
    for key in ("method", "leakage_prevention", "train_end", "validation_start", "validation_end", "oos_start"):
        if not split_policy.get(key):
            blockers.append(f"manifest_split_policy_{key}_missing")
    for key in ("start", "end"):
        if not out_of_sample.get(key):
            blockers.append(f"manifest_oos_split_{key}_missing")
    if split_policy.get("leakage_prevention") != "chronological_only_no_shuffle":
        blockers.append("manifest_leakage_prevention_not_chronological")
    return blockers


def _blocked_protocol(
    *,
    blockers: list[str],
    gate_path: Path,
    candidate_path: Path,
    manifest_path: Path,
    future_result_path: Path,
) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "decision": BLOCKED_DECISION,
        "candidate_id": SOURCE_CANDIDATE_ID,
        "source_reports": {
            "promotion_gate_report": str(gate_path),
            "candidate_report": str(candidate_path),
            "dataset_manifest": str(manifest_path),
        },
        "blockers": blockers,
        "allowed_future_oos_review": {
            "script": ALLOWED_FUTURE_OOS_SCRIPT,
            "exact_command": ALLOWED_FUTURE_OOS_COMMAND,
            "approval_token_required": HUMAN_APPROVAL_TOKEN,
            "may_run_in_v0_28": False,
            "script_created_in_v0_28": False,
            "result_path": str(future_result_path),
        },
        "created_metrics": {
            "oos_performance_results_created": False,
            "oos_rows_evaluated": 0,
            "oos_rows_read": 0,
        },
        "safety": dict(SAFETY_FLAGS),
        "recommended_next_step": "fix blockers before creating any OOS review protocol",
    }


def _stable_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
