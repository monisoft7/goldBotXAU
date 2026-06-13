"""v0_26 fixed compression-then-expansion research candidate decision."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.data.xauusd_low_tf_dataset_catalog import (
    DEFAULT_MANIFEST_PATH,
    build_low_tf_dataset_catalog,
    load_profiler_rows_from_catalog,
)
from src.research import xauusd_session_structure_atlas as atlas

DECISION_VERSION = "v0_26"
SOURCE_ATLAS_ID = "xauusd_session_structure_atlas_v0_25"
DEFAULT_ATLAS_REPORT = Path("reports") / f"{SOURCE_ATLAS_ID}.json"
DEFAULT_DECISION_REPORT = Path("reports") / "xauusd_compression_expansion_decision_v0_26.json"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"
SOURCE_FAMILY = "compression_then_expansion"
CREATE_DECISION = "create_fixed_compression_expansion_candidate"
REJECT_DECISION = "reject_compression_expansion_not_strong_enough"
BLOCKED_DECISION = "blocked_missing_or_invalid_v0_25_atlas"
SAFETY_FLAGS = {
    "demo_enabled": False,
    "live_enabled": False,
    "order_send_allowed": False,
    "order_check_allowed": False,
    "execution_queue_enabled": False,
    "execution_logic_present": False,
    "trade_recommendation_output_present": False,
    "oos_evaluated": False,
    "threshold_search_used": False,
    "parameter_grid_used": False,
    "rejected_candidate_retuned": False,
}


@dataclass(frozen=True)
class CompressionExpansionDecisionResult:
    decision_report: dict[str, Any]
    candidate_report: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decide_compression_expansion_candidate_v0_26(
    atlas_report_path: str | Path = DEFAULT_ATLAS_REPORT,
    *,
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    pattern: str = "xauusd_m*.csv",
) -> CompressionExpansionDecisionResult:
    path = Path(atlas_report_path)
    if not path.exists():
        return CompressionExpansionDecisionResult(
            decision_report=_blocked_report(path, ["v0_25_atlas_report_missing"], None),
            candidate_report=None,
        )

    try:
        atlas_report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CompressionExpansionDecisionResult(
            decision_report=_blocked_report(path, [f"v0_25_atlas_report_invalid_json: {exc}"], None),
            candidate_report=None,
        )

    blockers = _atlas_blockers(atlas_report)
    if blockers:
        return CompressionExpansionDecisionResult(
            decision_report=_blocked_report(path, blockers, atlas_report),
            candidate_report=None,
        )

    family = atlas_report["family_results"][SOURCE_FAMILY]
    family_rejection_reasons = _family_rejection_reasons(family)
    if family_rejection_reasons:
        return CompressionExpansionDecisionResult(
            decision_report=_reject_report(path, atlas_report, family, family_rejection_reasons, None),
            candidate_report=None,
        )

    evidence = _compression_expansion_evidence_by_timeframe(data_dir, manifest_path, pattern)
    evidence_rejection_reasons = _evidence_rejection_reasons(evidence)
    if evidence_rejection_reasons:
        return CompressionExpansionDecisionResult(
            decision_report=_reject_report(path, atlas_report, family, evidence_rejection_reasons, evidence),
            candidate_report=None,
        )

    candidate = _candidate_definition(atlas_report, family, evidence)
    candidate_report = _candidate_report(path, atlas_report, family, evidence, candidate)
    decision_report = _create_report(path, atlas_report, family, evidence, candidate)
    return CompressionExpansionDecisionResult(decision_report=decision_report, candidate_report=candidate_report)


def save_compression_expansion_decision_reports(
    result: CompressionExpansionDecisionResult,
    decision_output: str | Path = DEFAULT_DECISION_REPORT,
    candidate_output: str | Path | None = DEFAULT_CANDIDATE_REPORT,
) -> None:
    decision_path = Path(decision_output)
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(result.decision_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if result.candidate_report is not None and candidate_output is not None:
        candidate_path = Path(candidate_output)
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(
            json.dumps(result.candidate_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _atlas_blockers(atlas_report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if atlas_report.get("profiler_version") != "v0_25":
        blockers.append("unexpected_atlas_version")
    if atlas_report.get("status") != "profile_ready":
        blockers.append("v0_25_atlas_not_profile_ready")
    if int(atlas_report.get("oos_rows_used", -1) or 0) != 0:
        blockers.append("v0_25_atlas_used_oos_rows")

    dataset = atlas_report.get("dataset", {})
    if dataset.get("profiled_splits") != ["train", "validation"]:
        blockers.append("v0_25_atlas_did_not_use_train_validation_only")
    if int(dataset.get("oos_row_count_used", -1) or 0) != 0:
        blockers.append("v0_25_atlas_dataset_used_oos_rows")

    design = atlas_report.get("fixed_research_design", {})
    if design.get("threshold_search_used") is not False:
        blockers.append("v0_25_atlas_threshold_search_not_false")
    if design.get("parameter_grid_used") is not False:
        blockers.append("v0_25_atlas_parameter_grid_not_false")
    if SOURCE_FAMILY not in atlas_report.get("family_results", {}):
        blockers.append("compression_then_expansion_family_missing")
    return blockers


def _family_rejection_reasons(family: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    stability = family.get("stability_assessment", {})
    degradation = family.get("degradation_assessment", {})
    train = family.get("train_result", {})
    validation = family.get("validation_result", {})
    if family.get("strong_enough_for_future_single_fixed_candidate") is not True:
        reasons.append("atlas_family_not_marked_strong_enough")
    if stability.get("stable") is not True or stability.get("label") != "stable":
        reasons.append("atlas_family_not_stable")
    if train.get("dominant_behavior") != "next_block_expansion":
        reasons.append("unexpected_train_forward_behavior_label")
    if validation.get("dominant_behavior") != "next_block_expansion":
        reasons.append("unexpected_validation_forward_behavior_label")
    if float(train.get("edge_over_neutral", 0.0) or 0.0) < atlas.MATERIAL_EDGE:
        reasons.append("train_edge_below_fixed_material_edge")
    if float(validation.get("edge_over_neutral", 0.0) or 0.0) < atlas.MATERIAL_EDGE:
        reasons.append("validation_edge_below_fixed_material_edge")
    if degradation.get("within_fixed_limit") is not True:
        reasons.append("validation_degradation_exceeds_fixed_limit")
    return reasons


def _compression_expansion_evidence_by_timeframe(
    data_dir: str | Path,
    manifest_path: str | Path,
    pattern: str,
) -> dict[str, Any]:
    catalog = build_low_tf_dataset_catalog(data_dir=data_dir, manifest_path=manifest_path, pattern=pattern)
    rows = [
        row
        for row in load_profiler_rows_from_catalog(catalog)
        if row.get("source_timeframe") in atlas.LOW_TF_ALLOWED and row.get("split") in {"train", "validation"}
    ]
    profiles = atlas._day_profiles(rows)
    events = [event for profile in profiles if (event := atlas._compression_expansion_event(profile)) is not None]
    combined = _evidence_for_events(events)
    by_timeframe = {
        timeframe: _evidence_for_events([event for event in events if event["source_timeframe"] == timeframe])
        for timeframe in sorted(atlas.LOW_TF_ALLOWED)
    }
    timeframe_counts = {
        split: {
            timeframe: by_timeframe[timeframe][f"{split}_result"]["sample_count"]
            for timeframe in sorted(atlas.LOW_TF_ALLOWED)
        }
        for split in ("train", "validation")
    }
    duplicated_like_counts = all(
        len(set(counts.values())) == 1 and all(count > 0 for count in counts.values())
        for counts in timeframe_counts.values()
    )
    all_timeframes_stable = all(
        by_timeframe[timeframe]["stability_assessment"]["stable"] is True
        for timeframe in sorted(atlas.LOW_TF_ALLOWED)
    )
    return {
        "data_files_used": _data_files_used(catalog),
        "catalog_split_policy": catalog.get("split_policy", {}),
        "combined": combined,
        "by_timeframe": by_timeframe,
        "double_counting_assessment": {
            "timeframe_counts": timeframe_counts,
            "duplicated_like_counts_across_timeframes": duplicated_like_counts,
            "independent_timeframe_evidence_required": True,
            "all_timeframes_individually_stable": all_timeframes_stable,
            "combined_sample_count_not_treated_as_independent_event_count": True,
            "confidence_inflation_blocked": duplicated_like_counts and not all_timeframes_stable,
        },
    }


def _evidence_for_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    train_result = atlas._split_result([event for event in events if event["split"] == "train"])
    validation_result = atlas._split_result([event for event in events if event["split"] == "validation"])
    return {
        "train_result": train_result,
        "validation_result": validation_result,
        "sample_size_assessment": {
            "train": train_result["sample_count"],
            "validation": validation_result["sample_count"],
            "minimum_train_samples": atlas.MIN_TRAIN_SAMPLES,
            "minimum_validation_samples": atlas.MIN_VALIDATION_SAMPLES,
            "meets_fixed_minimums": train_result["sample_count"] >= atlas.MIN_TRAIN_SAMPLES
            and validation_result["sample_count"] >= atlas.MIN_VALIDATION_SAMPLES,
        },
        "stability_assessment": atlas._stability_assessment(train_result, validation_result),
        "degradation_assessment": atlas._degradation_assessment(train_result, validation_result),
    }


def _evidence_rejection_reasons(evidence: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not evidence["data_files_used"]:
        reasons.append("train_validation_m5_m10_data_missing")
    if evidence["double_counting_assessment"]["confidence_inflation_blocked"] is True:
        reasons.append("combined_strength_depends_on_duplicated_like_timeframe_counts")
    for timeframe, result in evidence["by_timeframe"].items():
        if result["sample_size_assessment"]["meets_fixed_minimums"] is not True:
            reasons.append(f"{timeframe}_sample_size_below_fixed_minimum")
        if result["stability_assessment"]["stable"] is not True:
            reasons.append(f"{timeframe}_evidence_not_individually_stable")
    return reasons


def _create_report(
    path: Path,
    atlas_report: dict[str, Any],
    family: dict[str, Any],
    evidence: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    return _base_report(
        decision=CREATE_DECISION,
        atlas_report_path=path,
        atlas_report=atlas_report,
        family=family,
        evidence=evidence,
        candidate_created=True,
        candidate=candidate,
        reasons=[
            "v0_25 atlas marked compression_then_expansion stable on train/validation rows only.",
            "M5-only and M10-only fixed evidence are each stable, so combined counts are not used as inflated confidence.",
            "Exactly one fixed research candidate was copied from the v0_25 family definition.",
        ],
    )


def _reject_report(
    path: Path,
    atlas_report: dict[str, Any],
    family: dict[str, Any],
    reasons: list[str],
    evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    return _base_report(
        decision=REJECT_DECISION,
        atlas_report_path=path,
        atlas_report=atlas_report,
        family=family,
        evidence=evidence,
        candidate_created=False,
        candidate=None,
        reasons=reasons,
    )


def _blocked_report(
    path: Path,
    reasons: list[str],
    atlas_report: dict[str, Any] | None,
) -> dict[str, Any]:
    return _base_report(
        decision=BLOCKED_DECISION,
        atlas_report_path=path,
        atlas_report=atlas_report,
        family=None,
        evidence=None,
        candidate_created=False,
        candidate=None,
        reasons=reasons,
    )


def _base_report(
    *,
    decision: str,
    atlas_report_path: Path,
    atlas_report: dict[str, Any] | None,
    family: dict[str, Any] | None,
    evidence: dict[str, Any] | None,
    candidate_created: bool,
    candidate: dict[str, Any] | None,
    reasons: list[str],
) -> dict[str, Any]:
    dataset = atlas_report.get("dataset", {}) if atlas_report else {}
    next_step = (
        "future v0_27 fixed promotion gate"
        if decision == CREATE_DECISION
        else "reject and move to intermarket/news atlas"
        if decision == REJECT_DECISION
        else "repair_or_regenerate_v0_25_atlas_before_any_candidate_work"
    )
    return {
        "decision_version": DECISION_VERSION,
        "decision": decision,
        "candidate_created": candidate_created,
        "candidate_id": candidate["candidate_id"] if candidate else None,
        "candidate_report_path": str(DEFAULT_CANDIDATE_REPORT) if candidate else None,
        "source_family": SOURCE_FAMILY,
        "source_atlas": SOURCE_ATLAS_ID,
        "atlas_report_path": str(atlas_report_path),
        "input_summary": {
            "atlas_version": atlas_report.get("profiler_version") if atlas_report else None,
            "atlas_status": atlas_report.get("status") if atlas_report else None,
            "splits_used": dataset.get("profiled_splits", []),
            "oos_rows_used": int(dataset.get("oos_row_count_used", 0) or 0),
            "family_stability_label": family.get("stability_assessment", {}).get("label") if family else None,
        },
        "fixed_rules": _fixed_rules(),
        "candidate": candidate,
        "atlas_family_result": family,
        "timeframe_evidence": evidence,
        "selection_policy": {
            "source_family_only": SOURCE_FAMILY,
            "single_candidate_limit": 1,
            "threshold_search_used": False,
            "parameter_grid_used": False,
            "retuning_used": False,
            "combined_timeframe_counts_used_for_confidence": False,
        },
        "reasons": reasons,
        "recommended_next_step": next_step,
        "safety_block": _safety_block(),
        "safety": dict(SAFETY_FLAGS),
    }


def _candidate_definition(
    atlas_report: dict[str, Any],
    family: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_version": DECISION_VERSION,
        "status": "train_validation_research_candidate_only",
        "source_family": SOURCE_FAMILY,
        "source_atlas": SOURCE_ATLAS_ID,
        "fixed_rules": _fixed_rules(),
        "data_files_used": list(evidence["data_files_used"]),
        "splits_used": ["train", "validation"],
        "oos_rows_used": 0,
        "train_result": family["train_result"],
        "validation_result": family["validation_result"],
        "degradation_assessment": family["degradation_assessment"],
        "sample_size_assessment": evidence["combined"]["sample_size_assessment"],
        "stability_assessment": {
            "atlas": family["stability_assessment"],
            "timeframe_evidence": evidence["double_counting_assessment"],
        },
        "decision": CREATE_DECISION,
        "recommended_next_step": "future v0_27 fixed promotion gate",
        "eligible_for_oos_review": False,
        "oos_status": "locked_not_evaluated",
        "research_only": True,
        "rules_are_fixed_from_atlas_family": True,
        "threshold_search_used": False,
        "parameter_grid_used": False,
        "safety_block": _safety_block(),
    }


def _candidate_report(
    path: Path,
    atlas_report: dict[str, Any],
    family: dict[str, Any],
    evidence: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "report_version": DECISION_VERSION,
        "candidate_id": CANDIDATE_ID,
        "candidate_version": DECISION_VERSION,
        "status": "train_validation_research_candidate_only",
        "source_family": SOURCE_FAMILY,
        "source_atlas": SOURCE_ATLAS_ID,
        "source_atlas_report": str(path),
        "fixed_rules": _fixed_rules(),
        "data_files_used": list(evidence["data_files_used"]),
        "splits_used": ["train", "validation"],
        "oos_rows_used": 0,
        "candidate": candidate,
        "train_result": family["train_result"],
        "validation_result": family["validation_result"],
        "degradation_assessment": family["degradation_assessment"],
        "sample_size_assessment": evidence["combined"]["sample_size_assessment"],
        "stability_assessment": {
            "atlas": family["stability_assessment"],
            "combined": evidence["combined"]["stability_assessment"],
            "M5": evidence["by_timeframe"]["M5"]["stability_assessment"],
            "M10": evidence["by_timeframe"]["M10"]["stability_assessment"],
            "double_counting": evidence["double_counting_assessment"],
        },
        "timeframe_evidence": evidence,
        "decision": CREATE_DECISION,
        "recommended_next_step": "future v0_27 fixed promotion gate",
        "evaluation_scope": {
            "splits": ["train", "validation"],
            "oos_evaluated": False,
            "source": "v0_25_fixed_compression_then_expansion_family",
            "event_summary_only": True,
        },
        "safety_block": _safety_block(),
        "safety": dict(SAFETY_FLAGS),
        "notes": [
            "Research-only hypothetical event behavior summary.",
            "M5-only, M10-only, and combined evidence are reported separately.",
            "Combined timeframe counts are not treated as independent market-event confidence.",
        ],
    }


def _fixed_rules() -> dict[str, Any]:
    return {
        "time_basis": "dataset_timestamp_hour_buckets_only",
        "reference_blocks": ["block_00_06", "block_06_12", "block_12_18"],
        "response_blocks": ["block_06_12", "block_12_18", "block_18_24"],
        "compression_definition": "select the available fixed six-hour reference block with the lowest average bar range",
        "forward_behavior_label": "next_block_expansion",
        "hypothetical_event_outcome": "response block range is greater than selected compressed reference block range",
        "tie_break": "earliest fixed reference block",
        "threshold_search_used": False,
        "parameter_grid_used": False,
        "retuning_used": False,
    }


def _safety_block() -> dict[str, Any]:
    return {
        "research_only": True,
        "oos_locked": True,
        "oos_rows_used": 0,
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "execution_queue_enabled": False,
        "execution_logic_present": False,
        "trade_recommendation_output_present": False,
        "strategy_promotion_created": False,
        "eligible_for_oos_review": False,
        "threshold_search_used": False,
        "parameter_grid_used": False,
        "rejected_candidate_retuned": False,
    }


def _data_files_used(catalog: dict[str, Any]) -> list[str]:
    return sorted(
        str(entry["filename"])
        for entry in catalog.get("entries", [])
        if entry.get("usable_for_profiler") is True and entry.get("source_timeframe") in atlas.LOW_TF_ALLOWED
    )
