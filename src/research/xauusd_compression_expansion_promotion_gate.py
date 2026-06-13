"""v0_27 fixed promotion gate for the v0_26 compression-expansion candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GATE_VERSION = "v0_27"
SOURCE_REPORT_VERSION = "v0_26"
SOURCE_CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"
SOURCE_DECISION = "create_fixed_compression_expansion_candidate"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_DECISION_REPORT = Path("reports") / "xauusd_compression_expansion_decision_v0_26.json"
DEFAULT_OUTPUT_REPORT = Path("reports") / "xauusd_compression_expansion_promotion_gate_v0_27.json"

PROMOTE_DECISION = "promote_to_oos_review_candidate_pending_human_approval"
REJECT_DECISION = "reject_train_validation_candidate"
BLOCKED_DECISION = "blocked_missing_or_invalid_v0_26_candidate_report"

PROMOTED_REGISTRY_STATUS = "eligible_for_oos_review_pending_human_approval"
REJECTED_REGISTRY_STATUS = "rejected_train_validation_gate_failed"

EXPECTED_REFERENCE_WINDOWS = ["block_00_06", "block_06_12", "block_12_18"]
EXPECTED_RESPONSE_WINDOWS = ["block_06_12", "block_12_18", "block_18_24"]
EXPECTED_TIMEFRAMES = ["M5", "M10"]

SAFETY_FLAGS = {
    "demo_enabled": False,
    "live_enabled": False,
    "order_send_allowed": False,
    "order_check_allowed": False,
    "execution_queue_enabled": False,
    "buy_sell_output_allowed": False,
    "execution_logic_present": False,
    "trade_recommendation_output_present": False,
    "oos_evaluated": False,
    "threshold_search_used": False,
    "parameter_grid_used": False,
    "rejected_candidate_retuned": False,
    "v0_26_candidate_retuned": False,
}

FIXED_GATE = {
    "minimum_independent_train_samples_per_timeframe": 500,
    "minimum_independent_validation_samples_per_timeframe": 100,
    "minimum_combined_train_primary_metric_rate": 0.74,
    "minimum_combined_validation_primary_metric_rate": 0.68,
    "minimum_combined_validation_edge_over_neutral": 0.18,
    "maximum_combined_validation_degradation_vs_train": 0.10,
    "minimum_timeframe_train_primary_metric_rate": 0.74,
    "minimum_timeframe_validation_primary_metric_rate": 0.68,
    "minimum_timeframe_validation_edge_over_neutral": 0.18,
    "maximum_timeframe_validation_degradation_vs_train": 0.10,
    "maximum_m5_m10_validation_primary_metric_gap": 0.03,
    "required_reference_windows": EXPECTED_REFERENCE_WINDOWS,
    "required_response_windows": EXPECTED_RESPONSE_WINDOWS,
    "required_timeframes": EXPECTED_TIMEFRAMES,
}


def decide_compression_expansion_promotion_gate_v0_27(
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    decision_report_path: str | Path = DEFAULT_DECISION_REPORT,
) -> dict[str, Any]:
    candidate_path = Path(candidate_report_path)
    decision_path = Path(decision_report_path)

    candidate_report, candidate_load_errors = _load_json(candidate_path, "v0_26_candidate_report")
    if candidate_load_errors:
        return _blocked_report(
            candidate_path=candidate_path,
            decision_path=decision_path,
            reasons=candidate_load_errors,
        )

    decision_report, decision_load_errors = _load_json(decision_path, "v0_26_decision_report")
    if decision_load_errors:
        return _blocked_report(
            candidate_path=candidate_path,
            decision_path=decision_path,
            reasons=decision_load_errors,
            candidate_report=candidate_report,
        )

    blockers = _candidate_report_blockers(candidate_report) + _decision_report_blockers(decision_report)
    blockers.extend(_cross_report_blockers(candidate_report, decision_report))
    if blockers:
        return _blocked_report(
            candidate_path=candidate_path,
            decision_path=decision_path,
            reasons=blockers,
            candidate_report=candidate_report,
        )

    evidence = _evidence_summary(candidate_report, decision_report)
    checks = _gate_checks(evidence)
    failed_checks = [check["check"] for check in checks if check["status"] == "failed"]
    decision = PROMOTE_DECISION if not failed_checks else REJECT_DECISION
    registry_status = PROMOTED_REGISTRY_STATUS if decision == PROMOTE_DECISION else REJECTED_REGISTRY_STATUS

    reasons = (
        [
            "Fixed train/validation gate passed without OOS evaluation.",
            "M5-only and M10-only evidence both passed the independent fixed checks.",
            "Duplicated-like M5/M10 counts were discounted; promotion does not rely on combined count inflation.",
            "Human approval is still required before any separate future OOS review protocol.",
        ]
        if decision == PROMOTE_DECISION
        else [
            "Fixed train/validation gate failed before OOS evaluation.",
            "Compression-expansion should be rejected rather than retuned under this candidate.",
        ]
    )

    return {
        "gate_version": GATE_VERSION,
        "decision": decision,
        "candidate_id": SOURCE_CANDIDATE_ID,
        "candidate_report_path": str(candidate_path),
        "decision_report_path": str(decision_path),
        "candidate_registry_update": {
            "candidate_id": SOURCE_CANDIDATE_ID,
            "status": registry_status,
            "eligible_for_oos_review": decision == PROMOTE_DECISION,
            "oos_status": "locked_not_evaluated",
            "human_approval_required_before_oos": decision == PROMOTE_DECISION,
            "research_only": True,
            "threshold_search_used": False,
            "parameter_grid_used": False,
            "retuned_rejected_candidate": False,
            "v0_26_candidate_retuned": False,
        },
        "registry_count_effect_if_applied": {
            "eligible_for_oos_review_count_delta": 1 if decision == PROMOTE_DECISION else 0,
            "rejected_candidate_count_delta": 0 if decision == PROMOTE_DECISION else 1,
        },
        "compression_expansion_family_status": (
            "eligible_for_future_oos_review_after_human_approval"
            if decision == PROMOTE_DECISION
            else "rejected_train_validation_gate_failed"
        ),
        "fixed_gate": dict(FIXED_GATE),
        "evidence_summary": evidence,
        "gate_checks": checks,
        "failed_checks": failed_checks,
        "reasons": reasons,
        "recommended_next_step": (
            "human approval followed by a separate v0_28 OOS review protocol"
            if decision == PROMOTE_DECISION
            else "move away from compression-expansion and choose a new non-retuned research family"
        ),
        "safety": dict(SAFETY_FLAGS),
    }


def save_compression_expansion_promotion_gate_report(
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


def _candidate_report_blockers(report: dict[str, Any] | None) -> list[str]:
    if report is None:
        return ["v0_26_candidate_report_missing"]

    blockers: list[str] = []
    if report.get("report_version") != SOURCE_REPORT_VERSION:
        blockers.append("unexpected_candidate_report_version")
    if report.get("candidate_id") != SOURCE_CANDIDATE_ID:
        blockers.append("unexpected_candidate_id")
    if report.get("status") != "train_validation_research_candidate_only":
        blockers.append("candidate_report_not_train_validation_research_only")
    if int(report.get("oos_rows_used", -1) or 0) != 0:
        blockers.append("candidate_report_used_oos_rows")
    if report.get("decision") != SOURCE_DECISION:
        blockers.append("candidate_report_unexpected_decision")

    candidate = report.get("candidate", {})
    if not isinstance(candidate, dict):
        blockers.append("candidate_payload_missing")
    else:
        if candidate.get("candidate_id") != SOURCE_CANDIDATE_ID:
            blockers.append("candidate_payload_id_mismatch")
        if candidate.get("rules_are_fixed_from_atlas_family") is not True:
            blockers.append("candidate_rules_not_fixed")
        if candidate.get("threshold_search_used") is not False:
            blockers.append("candidate_threshold_search_flag_not_false")
        if candidate.get("parameter_grid_used") is not False:
            blockers.append("candidate_parameter_grid_flag_not_false")
        if candidate.get("oos_status") != "locked_not_evaluated":
            blockers.append("candidate_oos_status_not_locked")
        if candidate.get("eligible_for_oos_review") is not False:
            blockers.append("candidate_already_oos_review_eligible_before_gate")

    scope = report.get("evaluation_scope", {})
    if scope.get("splits") != ["train", "validation"]:
        blockers.append("candidate_report_not_train_validation_only")
    if scope.get("oos_evaluated") is not False:
        blockers.append("candidate_report_oos_evaluated")

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
            blockers.append(f"safety_{flag}_not_false")

    for split in ("train_result", "validation_result"):
        blockers.extend(_split_result_blockers(report, split))

    evidence = report.get("timeframe_evidence")
    if not isinstance(evidence, dict):
        blockers.append("timeframe_evidence_missing")
    else:
        if not isinstance(evidence.get("combined"), dict):
            blockers.append("combined_timeframe_evidence_missing")
        by_timeframe = evidence.get("by_timeframe")
        if not isinstance(by_timeframe, dict):
            blockers.append("by_timeframe_evidence_missing")
        else:
            for timeframe in EXPECTED_TIMEFRAMES:
                if not isinstance(by_timeframe.get(timeframe), dict):
                    blockers.append(f"{timeframe}_evidence_missing")
                else:
                    blockers.extend(_timeframe_payload_blockers(by_timeframe[timeframe], timeframe))
        double_counting = evidence.get("double_counting_assessment", {})
        if double_counting.get("combined_sample_count_not_treated_as_independent_event_count") is not True:
            blockers.append("combined_sample_count_confidence_guard_missing")
        if double_counting.get("independent_timeframe_evidence_required") is not True:
            blockers.append("independent_timeframe_evidence_guard_missing")

    if not blockers:
        try:
            _evidence_summary(report, {"decision": SOURCE_DECISION, "candidate_id": SOURCE_CANDIDATE_ID})
        except (KeyError, TypeError, ValueError) as exc:
            blockers.append(f"candidate_report_metric_payload_invalid: {exc}")

    return blockers


def _decision_report_blockers(report: dict[str, Any] | None) -> list[str]:
    if report is None:
        return ["v0_26_decision_report_missing"]

    blockers: list[str] = []
    if report.get("decision_version") != SOURCE_REPORT_VERSION:
        blockers.append("unexpected_decision_report_version")
    if report.get("decision") != SOURCE_DECISION:
        blockers.append("unexpected_v0_26_decision")
    if report.get("candidate_id") != SOURCE_CANDIDATE_ID:
        blockers.append("decision_report_candidate_id_mismatch")
    if int(report.get("input_summary", {}).get("oos_rows_used", -1) or 0) != 0:
        blockers.append("decision_report_input_used_oos_rows")
    if report.get("selection_policy", {}).get("combined_timeframe_counts_used_for_confidence") is not False:
        blockers.append("decision_report_combined_confidence_guard_missing")

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
            blockers.append(f"decision_safety_{flag}_not_false")
    return blockers


def _cross_report_blockers(candidate_report: dict[str, Any] | None, decision_report: dict[str, Any] | None) -> list[str]:
    if candidate_report is None or decision_report is None:
        return []
    blockers: list[str] = []
    if decision_report.get("candidate_report_path") not in {None, str(DEFAULT_CANDIDATE_REPORT)}:
        blockers.append("decision_report_candidate_path_unexpected")
    if candidate_report.get("fixed_rules") != decision_report.get("fixed_rules"):
        blockers.append("candidate_and_decision_fixed_rules_mismatch")
    return blockers


def _split_result_blockers(report: dict[str, Any], split: str) -> list[str]:
    result = report.get(split)
    if not isinstance(result, dict):
        return [f"{split}_missing"]
    blockers: list[str] = []
    for key in (
        "sample_count",
        "primary_metric_rate",
        "edge_over_neutral",
        "dominant_behavior",
        "reference_windows",
        "response_windows",
    ):
        if key not in result:
            blockers.append(f"{split}_{key}_missing")
    if result.get("dominant_behavior") != "next_block_expansion":
        blockers.append(f"{split}_dominant_behavior_unexpected")
    return blockers


def _timeframe_payload_blockers(payload: dict[str, Any], timeframe: str) -> list[str]:
    blockers: list[str] = []
    for split in ("train_result", "validation_result"):
        if not isinstance(payload.get(split), dict):
            blockers.append(f"{timeframe}_{split}_missing")
    if not isinstance(payload.get("degradation_assessment"), dict):
        blockers.append(f"{timeframe}_degradation_assessment_missing")
    if not isinstance(payload.get("sample_size_assessment"), dict):
        blockers.append(f"{timeframe}_sample_size_assessment_missing")
    if not isinstance(payload.get("stability_assessment"), dict):
        blockers.append(f"{timeframe}_stability_assessment_missing")
    return blockers


def _evidence_summary(candidate_report: dict[str, Any], decision_report: dict[str, Any]) -> dict[str, Any]:
    evidence = candidate_report["timeframe_evidence"]
    combined = _metrics_for_payload(evidence["combined"])
    by_timeframe = {
        timeframe: _metrics_for_payload(evidence["by_timeframe"][timeframe])
        for timeframe in EXPECTED_TIMEFRAMES
    }
    validation_gap = abs(
        by_timeframe["M5"]["validation_primary_metric_rate"]
        - by_timeframe["M10"]["validation_primary_metric_rate"]
    )
    reference_windows = sorted(set(candidate_report["validation_result"]["reference_windows"]))
    response_windows = sorted(set(candidate_report["validation_result"]["response_windows"]))
    double_counting = evidence["double_counting_assessment"]

    return {
        "source_decision": decision_report.get("decision"),
        "candidate_status_before_gate": candidate_report.get("status"),
        "combined": combined,
        "by_timeframe": by_timeframe,
        "m5_m10_validation_primary_metric_gap": validation_gap,
        "timeframes_directionally_consistent": all(
            metrics["train_dominant_behavior"] == metrics["validation_dominant_behavior"] == "next_block_expansion"
            for metrics in by_timeframe.values()
        ),
        "all_timeframes_individually_stable": all(
            evidence["by_timeframe"][timeframe]["stability_assessment"].get("stable") is True
            for timeframe in EXPECTED_TIMEFRAMES
        ),
        "reference_windows_observed": reference_windows,
        "response_windows_observed": response_windows,
        "fixed_block_coverage_complete": (
            reference_windows == EXPECTED_REFERENCE_WINDOWS
            and response_windows == EXPECTED_RESPONSE_WINDOWS
        ),
        "double_counting_assessment": {
            **double_counting,
            "duplicated_timeframe_confidence_discount_applied": bool(
                double_counting.get("duplicated_like_counts_across_timeframes")
            ),
            "effective_train_sample_count_for_gate": min(
                by_timeframe[timeframe]["train_sample_count"] for timeframe in EXPECTED_TIMEFRAMES
            ),
            "effective_validation_sample_count_for_gate": min(
                by_timeframe[timeframe]["validation_sample_count"] for timeframe in EXPECTED_TIMEFRAMES
            ),
        },
        "oos_rows_used": 0,
        "oos_evaluated": False,
        "rules_retuned": False,
    }


def _metrics_for_payload(payload: dict[str, Any]) -> dict[str, Any]:
    train = payload["train_result"]
    validation = payload["validation_result"]
    degradation = payload["degradation_assessment"]
    return {
        "train_sample_count": int(train["sample_count"]),
        "validation_sample_count": int(validation["sample_count"]),
        "train_primary_metric_rate": float(train["primary_metric_rate"]),
        "validation_primary_metric_rate": float(validation["primary_metric_rate"]),
        "validation_edge_over_neutral": float(validation["edge_over_neutral"]),
        "validation_degradation_vs_train": float(degradation["validation_degradation"]),
        "train_dominant_behavior": train["dominant_behavior"],
        "validation_dominant_behavior": validation["dominant_behavior"],
        "reference_windows": list(validation["reference_windows"]),
        "response_windows": list(validation["response_windows"]),
    }


def _gate_checks(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        _check(
            "train_validation_scope_only",
            evidence["oos_rows_used"] == 0 and evidence["oos_evaluated"] is False,
            observed={"oos_rows_used": evidence["oos_rows_used"], "oos_evaluated": evidence["oos_evaluated"]},
        ),
        _check(
            "candidate_rules_fixed_without_search_or_retune",
            evidence["rules_retuned"] is False,
            observed={"rules_retuned": evidence["rules_retuned"]},
        ),
        _check(
            "combined_train_primary_metric_strength",
            evidence["combined"]["train_primary_metric_rate"] >= FIXED_GATE["minimum_combined_train_primary_metric_rate"],
            observed=evidence["combined"]["train_primary_metric_rate"],
            required=FIXED_GATE["minimum_combined_train_primary_metric_rate"],
        ),
        _check(
            "combined_validation_primary_metric_strength",
            evidence["combined"]["validation_primary_metric_rate"]
            >= FIXED_GATE["minimum_combined_validation_primary_metric_rate"],
            observed=evidence["combined"]["validation_primary_metric_rate"],
            required=FIXED_GATE["minimum_combined_validation_primary_metric_rate"],
        ),
        _check(
            "combined_validation_edge_material",
            evidence["combined"]["validation_edge_over_neutral"]
            >= FIXED_GATE["minimum_combined_validation_edge_over_neutral"],
            observed=evidence["combined"]["validation_edge_over_neutral"],
            required=FIXED_GATE["minimum_combined_validation_edge_over_neutral"],
        ),
        _check(
            "combined_validation_degradation_limited",
            evidence["combined"]["validation_degradation_vs_train"]
            <= FIXED_GATE["maximum_combined_validation_degradation_vs_train"],
            observed=evidence["combined"]["validation_degradation_vs_train"],
            required=FIXED_GATE["maximum_combined_validation_degradation_vs_train"],
        ),
        _check(
            "duplicate_timeframe_confidence_discounted",
            evidence["double_counting_assessment"]["combined_sample_count_not_treated_as_independent_event_count"] is True
            and evidence["double_counting_assessment"]["duplicated_timeframe_confidence_discount_applied"] is True,
            observed=evidence["double_counting_assessment"],
        ),
        _check(
            "independent_m5_m10_sample_size_sufficiency",
            evidence["double_counting_assessment"]["effective_train_sample_count_for_gate"]
            >= FIXED_GATE["minimum_independent_train_samples_per_timeframe"]
            and evidence["double_counting_assessment"]["effective_validation_sample_count_for_gate"]
            >= FIXED_GATE["minimum_independent_validation_samples_per_timeframe"],
            observed={
                "effective_train": evidence["double_counting_assessment"]["effective_train_sample_count_for_gate"],
                "effective_validation": evidence["double_counting_assessment"][
                    "effective_validation_sample_count_for_gate"
                ],
            },
            required={
                "train": FIXED_GATE["minimum_independent_train_samples_per_timeframe"],
                "validation": FIXED_GATE["minimum_independent_validation_samples_per_timeframe"],
            },
        ),
        _check(
            "m5_m10_directional_consistency",
            evidence["timeframes_directionally_consistent"] is True
            and evidence["all_timeframes_individually_stable"] is True,
            observed={
                "directionally_consistent": evidence["timeframes_directionally_consistent"],
                "all_timeframes_individually_stable": evidence["all_timeframes_individually_stable"],
            },
        ),
        _check(
            "m5_m10_validation_rate_consistency",
            evidence["m5_m10_validation_primary_metric_gap"]
            <= FIXED_GATE["maximum_m5_m10_validation_primary_metric_gap"],
            observed=evidence["m5_m10_validation_primary_metric_gap"],
            required=FIXED_GATE["maximum_m5_m10_validation_primary_metric_gap"],
        ),
        _check(
            "fixed_reference_response_block_coverage",
            evidence["fixed_block_coverage_complete"] is True,
            observed={
                "reference_windows": evidence["reference_windows_observed"],
                "response_windows": evidence["response_windows_observed"],
            },
            required={
                "reference_windows": EXPECTED_REFERENCE_WINDOWS,
                "response_windows": EXPECTED_RESPONSE_WINDOWS,
            },
        ),
    ]
    for timeframe, metrics in evidence["by_timeframe"].items():
        checks.extend(_timeframe_checks(timeframe, metrics))
    return checks


def _timeframe_checks(timeframe: str, metrics: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check(
            f"{timeframe}_train_primary_metric_strength",
            metrics["train_primary_metric_rate"] >= FIXED_GATE["minimum_timeframe_train_primary_metric_rate"],
            observed=metrics["train_primary_metric_rate"],
            required=FIXED_GATE["minimum_timeframe_train_primary_metric_rate"],
        ),
        _check(
            f"{timeframe}_validation_primary_metric_strength",
            metrics["validation_primary_metric_rate"] >= FIXED_GATE["minimum_timeframe_validation_primary_metric_rate"],
            observed=metrics["validation_primary_metric_rate"],
            required=FIXED_GATE["minimum_timeframe_validation_primary_metric_rate"],
        ),
        _check(
            f"{timeframe}_validation_edge_material",
            metrics["validation_edge_over_neutral"] >= FIXED_GATE["minimum_timeframe_validation_edge_over_neutral"],
            observed=metrics["validation_edge_over_neutral"],
            required=FIXED_GATE["minimum_timeframe_validation_edge_over_neutral"],
        ),
        _check(
            f"{timeframe}_validation_degradation_limited",
            metrics["validation_degradation_vs_train"]
            <= FIXED_GATE["maximum_timeframe_validation_degradation_vs_train"],
            observed=metrics["validation_degradation_vs_train"],
            required=FIXED_GATE["maximum_timeframe_validation_degradation_vs_train"],
        ),
    ]


def _check(name: str, passed: bool, *, observed: Any, required: Any | None = None) -> dict[str, Any]:
    check = {
        "check": name,
        "status": "passed" if passed else "failed",
        "observed": observed,
    }
    if required is not None:
        check["required"] = required
    return check


def _blocked_report(
    *,
    candidate_path: Path,
    decision_path: Path,
    reasons: list[str],
    candidate_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "gate_version": GATE_VERSION,
        "decision": BLOCKED_DECISION,
        "candidate_id": candidate_report.get("candidate_id") if candidate_report else SOURCE_CANDIDATE_ID,
        "candidate_report_path": str(candidate_path),
        "decision_report_path": str(decision_path),
        "candidate_registry_update": None,
        "registry_count_effect_if_applied": {
            "eligible_for_oos_review_count_delta": 0,
            "rejected_candidate_count_delta": 0,
        },
        "compression_expansion_family_status": "blocked",
        "fixed_gate": dict(FIXED_GATE),
        "evidence_summary": None,
        "gate_checks": [],
        "failed_checks": [],
        "reasons": reasons,
        "recommended_next_step": "repair or regenerate the v0_26 candidate report without OOS before any promotion decision",
        "safety": dict(SAFETY_FLAGS),
    }
