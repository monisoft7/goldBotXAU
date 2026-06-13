"""v0_24 fixed train/validation promotion gate for the v0_23 spike candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GATE_VERSION = "v0_24"
SOURCE_REPORT_VERSION = "v0_23"
SOURCE_CANDIDATE_ID = "xauusd_low_tf_spike_m5_hour_11_fade_v0_23"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_spike_fixed_candidate_v0_23_train_validation.json"
DEFAULT_OUTPUT_REPORT = Path("reports") / "xauusd_spike_promotion_gate_v0_24.json"

PROMOTE_DECISION = "promote_to_oos_review_candidate"
REJECT_DECISION = "reject_train_validation_candidate"
BLOCKED_DECISION = "blocked_missing_or_invalid_v0_23_candidate_report"

PROMOTED_REGISTRY_STATUS = "eligible_for_oos_review_pending_human_approval"
REJECTED_REGISTRY_STATUS = "rejected_train_validation_gate_failed"

SAFETY_FLAGS = {
    "demo_enabled": False,
    "live_enabled": False,
    "order_send_allowed": False,
    "execution_queue_enabled": False,
    "buy_sell_output_allowed": False,
    "execution_logic_present": False,
    "trade_recommendation_output_present": False,
    "oos_evaluated": False,
    "threshold_search_used": False,
    "parameter_grid_used": False,
    "rejected_candidate_retuned": False,
}

FIXED_GATE = {
    "minimum_train_sample_count": 500,
    "minimum_validation_sample_count": 200,
    "minimum_train_target_rate_3bar": 0.55,
    "minimum_validation_target_rate_3bar": 0.56,
    "minimum_validation_edge_over_neutral_3bar": 0.06,
    "maximum_validation_degradation_vs_train_3bar": 0.03,
    "minimum_train_target_rate_all_horizons": 0.53,
    "minimum_validation_target_rate_all_horizons": 0.55,
    "required_forward_horizons": ["forward_1bar", "forward_3bar", "forward_6bar"],
}


def decide_spike_promotion_gate_v0_24(
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
) -> dict[str, Any]:
    path = Path(candidate_report_path)
    if not path.exists():
        return _blocked_report(path=path, reasons=["v0_23_candidate_report_missing"])

    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _blocked_report(path=path, reasons=[f"v0_23_candidate_report_invalid_json: {exc}"])

    blockers = _candidate_report_blockers(report)
    if blockers:
        return _blocked_report(path=path, reasons=blockers, candidate_report=report)

    evidence = _evidence_summary(report)
    checks = _gate_checks(evidence)
    failed_checks = [check["check"] for check in checks if check["status"] == "failed"]
    decision = PROMOTE_DECISION if not failed_checks else REJECT_DECISION
    registry_status = PROMOTED_REGISTRY_STATUS if decision == PROMOTE_DECISION else REJECTED_REGISTRY_STATUS

    reasons = (
        [
            "Fixed train/validation gate passed without OOS evaluation.",
            "Candidate may become eligible for future OOS review only after human approval.",
        ]
        if decision == PROMOTE_DECISION
        else [
            "Fixed train/validation gate failed before OOS evaluation.",
            "Spike family is abandoned unless a future non-retuned fixed hypothesis is separately justified.",
        ]
    )

    return {
        "gate_version": GATE_VERSION,
        "decision": decision,
        "candidate_id": SOURCE_CANDIDATE_ID,
        "candidate_report_path": str(path),
        "candidate_registry_update": {
            "candidate_id": SOURCE_CANDIDATE_ID,
            "status": registry_status,
            "eligible_for_oos_review": decision == PROMOTE_DECISION,
            "oos_status": "locked_not_evaluated",
            "human_approval_required_before_oos": decision == PROMOTE_DECISION,
        },
        "registry_count_effect_if_applied": {
            "eligible_for_oos_review_count_delta": 1 if decision == PROMOTE_DECISION else 0,
            "rejected_candidate_count_delta": 0 if decision == PROMOTE_DECISION else 1,
        },
        "spike_family_status": "eligible_for_future_oos_review" if decision == PROMOTE_DECISION else "abandoned",
        "fixed_gate": dict(FIXED_GATE),
        "evidence_summary": evidence,
        "gate_checks": checks,
        "failed_checks": failed_checks,
        "reasons": reasons,
        "safety": dict(SAFETY_FLAGS),
    }


def save_spike_promotion_gate_report(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT_REPORT) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _candidate_report_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if report.get("report_version") != SOURCE_REPORT_VERSION:
        blockers.append("unexpected_candidate_report_version")
    if report.get("candidate_id") != SOURCE_CANDIDATE_ID:
        blockers.append("unexpected_candidate_id")
    if report.get("status") != "train_validation_evaluation_only":
        blockers.append("candidate_report_not_train_validation_evaluation_only")

    candidate = report.get("candidate", {})
    if candidate.get("candidate_id") != SOURCE_CANDIDATE_ID:
        blockers.append("candidate_payload_id_mismatch")
    if candidate.get("rules_are_fixed_from_profile_group") is not True:
        blockers.append("candidate_rules_not_fixed")
    if candidate.get("threshold_search_used") is not False:
        blockers.append("candidate_threshold_search_flag_not_false")
    if candidate.get("parameter_grid_used") is not False:
        blockers.append("candidate_parameter_grid_flag_not_false")
    if candidate.get("oos_status") != "locked_not_evaluated":
        blockers.append("candidate_oos_status_not_locked")

    scope = report.get("evaluation_scope", {})
    if scope.get("splits") != ["train", "validation"]:
        blockers.append("candidate_report_not_train_validation_only")
    if scope.get("oos_evaluated") is not False:
        blockers.append("candidate_report_oos_evaluated")

    safety = report.get("safety", {})
    if safety.get("oos_evaluated") is not False:
        blockers.append("safety_oos_evaluated_not_false")
    if safety.get("threshold_search_used") is not False:
        blockers.append("safety_threshold_search_not_false")
    if safety.get("parameter_grid_used") is not False:
        blockers.append("safety_parameter_grid_not_false")
    if safety.get("rejected_candidate_retuned") is not False:
        blockers.append("safety_rejected_candidate_retuned_not_false")

    for split in ("train_result", "validation_result"):
        split_result = report.get(split)
        if not isinstance(split_result, dict):
            blockers.append(f"{split}_missing")
            continue
        if "sample_count" not in split_result:
            blockers.append(f"{split}_sample_count_missing")
        if split_result.get("fade_vs_continuation_tendency") not in {"fade", "continuation"}:
            blockers.append(f"{split}_tendency_missing_or_invalid")
        behavior = split_result.get("forward_behavior")
        if not isinstance(behavior, dict):
            blockers.append(f"{split}_forward_behavior_missing")
            continue
        for horizon in FIXED_GATE["required_forward_horizons"]:
            horizon_payload = behavior.get(horizon)
            if not isinstance(horizon_payload, dict):
                blockers.append(f"{split}_{horizon}_missing")

    if not blockers:
        try:
            _evidence_summary(report)
        except (KeyError, TypeError, ValueError) as exc:
            blockers.append(f"candidate_report_metric_payload_invalid: {exc}")

    return blockers


def _evidence_summary(report: dict[str, Any]) -> dict[str, Any]:
    train = report["train_result"]
    validation = report["validation_result"]
    train_tendency = str(train["fade_vs_continuation_tendency"])
    validation_tendency = str(validation["fade_vs_continuation_tendency"])
    candidate_label = str(report["candidate"]["observed_behavior_label"])
    metric_key = f"{candidate_label}_rate"

    train_rates = _rates_by_horizon(train, metric_key)
    validation_rates = _rates_by_horizon(validation, metric_key)
    train_3bar = train_rates["forward_3bar"]
    validation_3bar = validation_rates["forward_3bar"]

    return {
        "candidate_observed_behavior_label": candidate_label,
        "train_tendency": train_tendency,
        "validation_tendency": validation_tendency,
        "train_sample_count": int(train["sample_count"]),
        "validation_sample_count": int(validation["sample_count"]),
        "train_target_rates": train_rates,
        "validation_target_rates": validation_rates,
        "train_3bar_target_rate": train_3bar,
        "validation_3bar_target_rate": validation_3bar,
        "validation_3bar_edge_over_neutral": validation_3bar - 0.5,
        "validation_degradation_vs_train_3bar": train_3bar - validation_3bar,
        "train_validation_directionally_consistent": (
            train_tendency == validation_tendency == candidate_label
        ),
        "oos_rows_used": 0,
        "adverse_excursion_evidence_available": False,
        "year_month_concentration_evidence_available": False,
    }


def _rates_by_horizon(split_result: dict[str, Any], metric_key: str) -> dict[str, float]:
    rates: dict[str, float] = {}
    behavior = split_result["forward_behavior"]
    for horizon in FIXED_GATE["required_forward_horizons"]:
        payload = behavior[horizon]
        if metric_key not in payload:
            raise KeyError(f"{horizon}.{metric_key}")
        rates[horizon] = float(payload[metric_key])
    return rates


def _gate_checks(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        _check(
            "train_validation_directional_consistency",
            bool(evidence["train_validation_directionally_consistent"]),
            observed={
                "candidate_observed_behavior_label": evidence["candidate_observed_behavior_label"],
                "train_tendency": evidence["train_tendency"],
                "validation_tendency": evidence["validation_tendency"],
            },
        ),
        _check(
            "train_sample_size_sufficiency",
            evidence["train_sample_count"] >= FIXED_GATE["minimum_train_sample_count"],
            observed=evidence["train_sample_count"],
            required=FIXED_GATE["minimum_train_sample_count"],
        ),
        _check(
            "validation_sample_size_sufficiency",
            evidence["validation_sample_count"] >= FIXED_GATE["minimum_validation_sample_count"],
            observed=evidence["validation_sample_count"],
            required=FIXED_GATE["minimum_validation_sample_count"],
        ),
        _check(
            "material_train_3bar_edge",
            evidence["train_3bar_target_rate"] >= FIXED_GATE["minimum_train_target_rate_3bar"],
            observed=evidence["train_3bar_target_rate"],
            required=FIXED_GATE["minimum_train_target_rate_3bar"],
        ),
        _check(
            "material_validation_3bar_edge",
            evidence["validation_3bar_target_rate"] >= FIXED_GATE["minimum_validation_target_rate_3bar"],
            observed=evidence["validation_3bar_target_rate"],
            required=FIXED_GATE["minimum_validation_target_rate_3bar"],
        ),
        _check(
            "validation_edge_over_neutral_not_tiny",
            evidence["validation_3bar_edge_over_neutral"]
            >= FIXED_GATE["minimum_validation_edge_over_neutral_3bar"],
            observed=evidence["validation_3bar_edge_over_neutral"],
            required=FIXED_GATE["minimum_validation_edge_over_neutral_3bar"],
        ),
        _check(
            "limited_validation_degradation_vs_train",
            evidence["validation_degradation_vs_train_3bar"]
            <= FIXED_GATE["maximum_validation_degradation_vs_train_3bar"],
            observed=evidence["validation_degradation_vs_train_3bar"],
            required=FIXED_GATE["maximum_validation_degradation_vs_train_3bar"],
        ),
        _check(
            "train_forward_horizon_consistency",
            min(evidence["train_target_rates"].values()) >= FIXED_GATE["minimum_train_target_rate_all_horizons"],
            observed=evidence["train_target_rates"],
            required=FIXED_GATE["minimum_train_target_rate_all_horizons"],
        ),
        _check(
            "validation_forward_horizon_consistency",
            min(evidence["validation_target_rates"].values())
            >= FIXED_GATE["minimum_validation_target_rate_all_horizons"],
            observed=evidence["validation_target_rates"],
            required=FIXED_GATE["minimum_validation_target_rate_all_horizons"],
        ),
    ]
    return checks


def _check(
    name: str,
    passed: bool,
    *,
    observed: Any,
    required: Any | None = None,
) -> dict[str, Any]:
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
    path: Path,
    reasons: list[str],
    candidate_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "gate_version": GATE_VERSION,
        "decision": BLOCKED_DECISION,
        "candidate_id": candidate_report.get("candidate_id") if candidate_report else SOURCE_CANDIDATE_ID,
        "candidate_report_path": str(path),
        "candidate_registry_update": None,
        "registry_count_effect_if_applied": {
            "eligible_for_oos_review_count_delta": 0,
            "rejected_candidate_count_delta": 0,
        },
        "spike_family_status": "blocked",
        "fixed_gate": dict(FIXED_GATE),
        "evidence_summary": None,
        "gate_checks": [],
        "failed_checks": [],
        "reasons": reasons,
        "safety": dict(SAFETY_FLAGS),
    }
