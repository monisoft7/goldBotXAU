"""v0_57 viability audit for the v0_54 volatility-regime lead.

This module audits descriptive train/validation evidence only. It does not
create a backtest candidate, run OOS, tune thresholds, or touch execution APIs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_m15_csvs

AUDIT_VERSION = "v0_57"
SOURCE_PROFILER_VERSION = "v0_54"
SOURCE_DESIGN_VERSION = "v0_55"
SOURCE_REJECTED_EVAL_VERSION = "v0_56"
LEAD_ID = "volatility_regime_profile"

DEFAULT_OUTPUT = Path("reports") / "xauusd_volatility_regime_lead_viability_v0_57.json"
DEFAULT_SOURCE_PROFILER = Path("reports") / "xauusd_edge_profiler_v0_54.json"
DEFAULT_SOURCE_DESIGN = Path("reports") / "xauusd_session_volatility_design_v0_55.json"
DEFAULT_SOURCE_REJECTED_EVAL = Path("reports") / "xauusd_session_block_bias_eval_v0_56.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"

COMPLETED = "volatility_lead_viability_completed"
BLOCKED_MISSING_PROFILER = "blocked_missing_v0_54_profiler_report"
AUDIT_FAILED = "audit_failed"

DECISION_VIABLE = "volatility_lead_sample_viable_for_candidate_design"
DECISION_INSUFFICIENT = "volatility_lead_promising_but_insufficient_sample"
DECISION_REJECT = "volatility_lead_unstable_or_too_weak_reject"

VALIDATION_SAMPLE_MINIMUM = 50
CONCENTRATION_MONTH_MAX_SHARE = 0.35
CONCENTRATION_YEAR_MAX_SHARE = 0.75
ELEVATED_REGIME_LABELS = ("medium_high_volatility_quartile", "high_volatility_quartile")


@dataclass(frozen=True)
class DailyRegimeObservation:
    split: str
    day: str
    year: str
    month: str
    regime: str
    same_day_close_open_points: float


def build_xauusd_volatility_regime_lead_viability_audit_v0_57(
    *,
    data_dir: str | Path = "data",
    pattern: str = "xauusd_m15_*.csv",
    manifest_path: str | Path = DEFAULT_MANIFEST,
    source_profiler_path: str | Path = DEFAULT_SOURCE_PROFILER,
    source_design_path: str | Path = DEFAULT_SOURCE_DESIGN,
    source_rejected_eval_path: str | Path = DEFAULT_SOURCE_REJECTED_EVAL,
) -> dict[str, Any]:
    """Audit whether the v0_54 volatility-regime lead merits one v0_58 design."""
    try:
        profiler = _read_json(Path(source_profiler_path))
        profiler_blockers = _source_profiler_blockers(profiler)
        if profiler_blockers:
            return _base_report(
                audit_status=BLOCKED_MISSING_PROFILER,
                source_profiler=profiler,
                source_design=_read_json(Path(source_design_path)),
                source_rejected_eval=_read_json(Path(source_rejected_eval_path)),
                volatility_result=None,
                observations=[],
                data_files_used=[],
                split_candle_counts=_empty_counts(),
                decision=BLOCKED_MISSING_PROFILER,
                recommended_design={},
                blockers=profiler_blockers,
                warnings=[],
                next_recommended_step="restore reports/xauusd_edge_profiler_v0_54.json before rerunning v0_57",
            )

        source_design = _read_json(Path(source_design_path))
        source_rejected_eval = _read_json(Path(source_rejected_eval_path))
        source_blockers = [
            *_source_design_blockers(source_design),
            *_source_rejected_eval_blockers(source_rejected_eval),
        ]
        volatility_result = _volatility_result(profiler)
        if volatility_result is None:
            source_blockers.append("source_v0_54_volatility_regime_result_missing")
        if source_blockers:
            return _base_report(
                audit_status=AUDIT_FAILED,
                source_profiler=profiler,
                source_design=source_design,
                source_rejected_eval=source_rejected_eval,
                volatility_result=volatility_result,
                observations=[],
                data_files_used=[],
                split_candle_counts=_empty_counts(),
                decision=AUDIT_FAILED,
                recommended_design={},
                blockers=source_blockers,
                warnings=[],
                next_recommended_step="repair source v0_55/v0_56 evidence before deciding the volatility lead",
            )

        assert volatility_result is not None
        manifest = _read_json(Path(manifest_path))
        observations: list[DailyRegimeObservation] = []
        data_files_used: list[str] = []
        split_candle_counts = _empty_counts()
        data_warnings: list[str] = []
        manifest_blockers = _manifest_blockers(manifest)
        if manifest_blockers:
            data_warnings.extend(manifest_blockers)
        else:
            assert manifest is not None
            load_result = load_xauusd_m15_csvs(data_dir=data_dir, pattern=pattern)
            data_files_used = [path.as_posix() for path in load_result.files]
            observations, split_candle_counts = _daily_regime_observations(load_result.records, manifest)
            if not observations:
                data_warnings.append("daily_regime_distribution_unavailable_from_local_m15_data")

        profile = _fixed_elevated_profile(volatility_result)
        concentration = _sample_concentration_risk(observations, volatility_result)
        sufficiency = _validation_sample_sufficiency(profile, volatility_result)
        consistency = _train_validation_consistency(volatility_result, profile)
        feasibility = _candidate_design_feasibility(profile, sufficiency, consistency, concentration)
        decision = _viability_decision(sufficiency, consistency, feasibility)
        recommended_design = _recommended_design(decision, profile)
        warnings = _warnings(volatility_result, observations, concentration, sufficiency, consistency, data_warnings)
        next_step = _next_step(decision)

        return _base_report(
            audit_status=COMPLETED,
            source_profiler=profiler,
            source_design=source_design,
            source_rejected_eval=source_rejected_eval,
            volatility_result=volatility_result,
            observations=observations,
            data_files_used=data_files_used,
            split_candle_counts=split_candle_counts,
            decision=decision,
            recommended_design=recommended_design,
            blockers=[] if decision != DECISION_INSUFFICIENT else sufficiency["blockers"],
            warnings=warnings,
            next_recommended_step=next_step,
        )
    except Exception as exc:
        return _base_report(
            audit_status=AUDIT_FAILED,
            source_profiler=None,
            source_design=None,
            source_rejected_eval=None,
            volatility_result=None,
            observations=[],
            data_files_used=[],
            split_candle_counts=_empty_counts(),
            decision=AUDIT_FAILED,
            recommended_design={},
            blockers=[f"audit_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair v0_57 audit implementation or input artifacts before continuing",
        )


def save_xauusd_volatility_regime_lead_viability_audit(
    report: dict[str, Any],
    output: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_report(
    *,
    audit_status: str,
    source_profiler: dict[str, Any] | None,
    source_design: dict[str, Any] | None,
    source_rejected_eval: dict[str, Any] | None,
    volatility_result: dict[str, Any] | None,
    observations: list[DailyRegimeObservation],
    data_files_used: list[str],
    split_candle_counts: dict[str, int],
    decision: str,
    recommended_design: dict[str, Any],
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    counts = _volatility_regime_counts(volatility_result, observations)
    behavior = _volatility_regime_behavior_summary(volatility_result)
    profile = _fixed_elevated_profile(volatility_result)
    consistency = _train_validation_consistency(volatility_result, profile)
    concentration = _sample_concentration_risk(observations, volatility_result)
    sufficiency = _validation_sample_sufficiency(profile, volatility_result)
    feasibility = _candidate_design_feasibility(profile, sufficiency, consistency, concentration)
    return {
        "audit_version": AUDIT_VERSION,
        "audit_status": audit_status,
        "source_profiler_version": SOURCE_PROFILER_VERSION,
        "source_design_version": SOURCE_DESIGN_VERSION,
        "source_rejected_eval_version": SOURCE_REJECTED_EVAL_VERSION,
        "lead_id": LEAD_ID,
        "source_profiler_status": source_profiler.get("profiler_status") if isinstance(source_profiler, dict) else None,
        "source_design_status": source_design.get("design_status") if isinstance(source_design, dict) else None,
        "source_rejected_eval_status": source_rejected_eval.get("evaluation_status") if isinstance(source_rejected_eval, dict) else None,
        "session_block_branch_rejected": _session_block_rejected(source_rejected_eval),
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
        "data_csv_added_to_git": False,
        "data_files_used": data_files_used,
        "split_candle_counts": split_candle_counts,
        "volatility_regime_counts": counts,
        "volatility_regime_behavior_summary": behavior,
        "train_validation_consistency": consistency,
        "sample_concentration_risk": concentration,
        "validation_sample_sufficiency": sufficiency,
        "candidate_design_feasibility": feasibility,
        "volatility_lead_viability_decision": decision,
        "recommended_v0_58_candidate_design": recommended_design,
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def _volatility_regime_counts(
    volatility_result: dict[str, Any] | None,
    observations: list[DailyRegimeObservation],
) -> dict[str, Any]:
    train_summary = _behavior_summaries(volatility_result, "train")
    validation_summary = _behavior_summaries(volatility_result, "validation")
    labels = sorted(set(train_summary) | set(validation_summary) | {obs.regime for obs in observations})
    by_regime = {
        label: {
            "train": _event_count(train_summary.get(label)),
            "validation": _event_count(validation_summary.get(label)),
            "total": _event_count(train_summary.get(label)) + _event_count(validation_summary.get(label)),
        }
        for label in labels
    }
    return {
        "train_total": sum(item["train"] for item in by_regime.values()),
        "validation_total": sum(item["validation"] for item in by_regime.values()),
        "total": sum(item["total"] for item in by_regime.values()),
        "by_regime": by_regime,
        "by_year": _distribution(observations, "year"),
        "by_month": _distribution(observations, "month"),
        "distribution_source": "local_m15_reconstruction" if observations else "source_profiler_summary_only",
    }


def _volatility_regime_behavior_summary(volatility_result: dict[str, Any] | None) -> dict[str, Any]:
    train = _behavior_summaries(volatility_result, "train")
    validation = _behavior_summaries(volatility_result, "validation")
    labels = sorted(set(train) | set(validation))
    return {
        label: {
            "train": _behavior_metrics(train.get(label)),
            "validation": _behavior_metrics(validation.get(label)),
            "tendency": _behavior_tendency(train.get(label), validation.get(label)),
        }
        for label in labels
    }


def _fixed_elevated_profile(volatility_result: dict[str, Any] | None) -> dict[str, Any]:
    train = _behavior_summaries(volatility_result, "train")
    validation = _behavior_summaries(volatility_result, "validation")
    train_values = [_regime_points(train.get(label)) for label in ELEVATED_REGIME_LABELS]
    validation_values = [_regime_points(validation.get(label)) for label in ELEVATED_REGIME_LABELS]
    train_mean = _weighted_mean(train_values)
    validation_mean = _weighted_mean(validation_values)
    train_positive_rate = _weighted_rate(train_values)
    validation_positive_rate = _weighted_rate(validation_values)
    return {
        "fixed_label_group": list(ELEVATED_REGIME_LABELS),
        "train_count": sum(item["count"] for item in train_values),
        "validation_count": sum(item["count"] for item in validation_values),
        "train_mean_same_day_points": train_mean,
        "validation_mean_same_day_points": validation_mean,
        "train_positive_rate": train_positive_rate,
        "validation_positive_rate": validation_positive_rate,
        "train_sign": _sign_label(train_mean),
        "validation_sign": _sign_label(validation_mean),
        "mechanical_structure": "upper_half_existing_v0_54_volatility_quartile_labels",
    }


def _train_validation_consistency(
    volatility_result: dict[str, Any] | None,
    profile: dict[str, Any],
) -> dict[str, Any]:
    train_dominant = _split_summary(volatility_result, "train").get("dominant_behavior")
    validation_dominant = _split_summary(volatility_result, "validation").get("dominant_behavior")
    same_sign = profile["train_sign"] == profile["validation_sign"] and profile["train_sign"] != "flat"
    both_positive_rate_supportive = profile["train_positive_rate"] >= 0.50 and profile["validation_positive_rate"] >= 0.50
    return {
        "train_dominant_regime": train_dominant,
        "validation_dominant_regime": validation_dominant,
        "dominant_regime_matches": train_dominant == validation_dominant and train_dominant is not None,
        "fixed_elevated_group_same_sign": same_sign,
        "fixed_elevated_group_positive_rate_supportive": both_positive_rate_supportive,
        "fixed_elevated_group_train_sign": profile["train_sign"],
        "fixed_elevated_group_validation_sign": profile["validation_sign"],
        "consistency_status": "consistent" if same_sign and both_positive_rate_supportive else "unstable_or_weak",
        "notes": _consistency_notes(train_dominant, validation_dominant, same_sign),
    }


def _sample_concentration_risk(
    observations: list[DailyRegimeObservation],
    volatility_result: dict[str, Any] | None,
) -> dict[str, Any]:
    validation = [obs for obs in observations if obs.split == "validation" and obs.regime in ELEVATED_REGIME_LABELS]
    total_validation_count = len(validation) or int(_fixed_elevated_profile(volatility_result)["validation_count"])
    month_share = _max_share(validation, "month")
    year_share = _max_share(validation, "year")
    reasons: list[str] = []
    if observations and month_share > CONCENTRATION_MONTH_MAX_SHARE:
        reasons.append("validation_fixed_elevated_regime_observations_concentrated_in_single_month")
    if observations and year_share > CONCENTRATION_YEAR_MAX_SHARE:
        reasons.append("validation_fixed_elevated_regime_observations_concentrated_in_single_year")
    if not observations:
        reasons.append("distribution_unavailable_from_local_m15_data")
    return {
        "risk_level": "high" if reasons else "low",
        "risk_present": bool(reasons),
        "reasons": reasons,
        "validation_fixed_elevated_observations": total_validation_count,
        "validation_month_max_share": month_share,
        "validation_year_max_share": year_share,
        "month_share_limit": CONCENTRATION_MONTH_MAX_SHARE,
        "year_share_limit": CONCENTRATION_YEAR_MAX_SHARE,
    }


def _validation_sample_sufficiency(
    profile: dict[str, Any],
    volatility_result: dict[str, Any] | None,
) -> dict[str, Any]:
    validation_total = int((volatility_result or {}).get("event_count_validation", 0))
    fixed_validation = int(profile["validation_count"])
    blockers: list[str] = []
    if validation_total < VALIDATION_SAMPLE_MINIMUM:
        blockers.append("validation_total_regime_observations_below_50")
    if fixed_validation < VALIDATION_SAMPLE_MINIMUM:
        blockers.append("fixed_elevated_regime_validation_observations_below_50")
    return {
        "minimum_validation_observations": VALIDATION_SAMPLE_MINIMUM,
        "validation_total_regime_observations": validation_total,
        "fixed_elevated_regime_validation_observations": fixed_validation,
        "can_produce_at_least_50_validation_trades_under_fixed_rules": fixed_validation >= VALIDATION_SAMPLE_MINIMUM,
        "sufficiency_status": "sufficient" if not blockers else "insufficient",
        "blockers": blockers,
    }


def _candidate_design_feasibility(
    profile: dict[str, Any],
    sufficiency: dict[str, Any],
    consistency: dict[str, Any],
    concentration: dict[str, Any],
) -> dict[str, Any]:
    simple_mechanical = True
    enough_validation = sufficiency["can_produce_at_least_50_validation_trades_under_fixed_rules"] is True
    stable = consistency["consistency_status"] == "consistent"
    low_concentration = concentration["risk_level"] == "low"
    feasible = simple_mechanical and enough_validation and stable and low_concentration
    return {
        "simple_mechanical_candidate_possible": simple_mechanical,
        "uses_only_existing_v0_54_regime_labels": True,
        "arbitrary_threshold_required": False,
        "differs_materially_from_failed_session_block_candidate": True,
        "can_produce_at_least_50_validation_trades_under_fixed_rules": enough_validation,
        "candidate_design_feasible_for_v0_58": feasible,
        "fixed_structure_under_review": profile["mechanical_structure"],
        "reasons": _feasibility_reasons(enough_validation, stable, low_concentration),
    }


def _viability_decision(
    sufficiency: dict[str, Any],
    consistency: dict[str, Any],
    feasibility: dict[str, Any],
) -> str:
    if sufficiency["sufficiency_status"] == "insufficient":
        return DECISION_INSUFFICIENT
    if consistency["consistency_status"] != "consistent":
        return DECISION_REJECT
    if feasibility["candidate_design_feasible_for_v0_58"] is True:
        return DECISION_VIABLE
    return DECISION_REJECT


def _recommended_design(decision: str, profile: dict[str, Any]) -> dict[str, Any]:
    if decision != DECISION_VIABLE:
        return {}
    return {
        "candidate_design_id": "volatility_regime_elevated_same_day_bias_candidate",
        "source_lead": LEAD_ID,
        "design_intent": "fixed-rule train/validation evaluation only; no OOS and no execution",
        "fixed_regime_labels": list(ELEVATED_REGIME_LABELS),
        "exact_entry_rule": "On train/validation days labeled medium_high_volatility_quartile or high_volatility_quartile by the v0_54 daily-range quartile method, observe one fixed same-day open-to-close outcome.",
        "exact_behavior_rule": f"Use the train-derived same-day behavior sign for the fixed elevated-volatility label group: {profile['train_sign']}.",
        "exact_invalidation_rule": "Invalidate days outside the two fixed elevated v0_54 labels or days missing a complete daily open/close.",
        "stop_loss_logic": "No stop or target is designed in v0_57; v0_58 must predeclare any structural risk rule before evaluation.",
        "take_profit_or_exit_logic": "For viability design only, the measured behavior exits at the last available M15 close of the same UTC day.",
        "anti_curve_fit_argument": "Uses only the existing upper-half v0_54 volatility quartile labels; no threshold search, parameter grid, session window search, or validation-selected label switching.",
        "v0_58_test_scope": "Evaluate this one fixed train/validation candidate only, no OOS.",
    }


def _warnings(
    volatility_result: dict[str, Any],
    observations: list[DailyRegimeObservation],
    concentration: dict[str, Any],
    sufficiency: dict[str, Any],
    consistency: dict[str, Any],
    data_warnings: list[str],
) -> list[str]:
    warnings = [
        "viability_audit_only_not_backtest_candidate",
        "oos_rows_explicitly_excluded",
        "no_profitability_claim_made",
    ]
    if _split_summary(volatility_result, "train").get("dominant_behavior") != _split_summary(volatility_result, "validation").get("dominant_behavior"):
        warnings.append("volatility_regime_train_validation_dominant_bucket_differs")
    warnings.extend(data_warnings)
    warnings.extend(f"sample_concentration_risk:{reason}" for reason in concentration["reasons"])
    warnings.extend(sufficiency["blockers"])
    if consistency["consistency_status"] != "consistent":
        warnings.append("fixed_elevated_regime_behavior_unstable_or_weak")
    if not observations:
        warnings.append("year_month_distribution_limited_to_source_profiler_counts")
    return sorted(dict.fromkeys(warnings))


def _next_step(decision: str) -> str:
    if decision == DECISION_VIABLE:
        return "v0_58 fixed-rule train/validation evaluation for volatility_regime_elevated_same_day_bias_candidate only, no OOS."
    if decision == DECISION_INSUFFICIENT:
        return "broaden non-OOS research evidence or stop profiler-lead branch; do not run OOS."
    if decision == DECISION_REJECT:
        return "stop profiler-lead branch or broaden non-OOS research."
    return "repair v0_57 audit inputs before continuing."


def _daily_regime_observations(
    records: list[dict[str, float | str]],
    manifest: dict[str, Any],
) -> tuple[list[DailyRegimeObservation], dict[str, int]]:
    grouped: dict[str, list[dict[str, float | str]]] = {}
    counts = _empty_counts()
    for record in records:
        timestamp = _dt(str(record["timestamp"]))
        split = _split(timestamp, manifest)
        counts[split] += 1
        if split in {"train", "validation"}:
            grouped.setdefault(timestamp.date().isoformat(), []).append(record)
    day_ranges = {
        day: max(float(row["high"]) for row in rows) - min(float(row["low"]) for row in rows)
        for day, rows in grouped.items()
    }
    values = sorted(day_ranges.values())
    if len(values) < 4:
        return [], counts
    q1, q2, q3 = _quartiles(values)
    observations: list[DailyRegimeObservation] = []
    for day, rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: str(row["timestamp"]))
        timestamp = _dt(str(ordered[0]["timestamp"]))
        observations.append(
            DailyRegimeObservation(
                split=_split(timestamp, manifest),
                day=day,
                year=timestamp.strftime("%Y"),
                month=timestamp.strftime("%Y-%m"),
                regime=_vol_label(day_ranges[day], q1, q2, q3),
                same_day_close_open_points=float(ordered[-1]["close"]) - float(ordered[0]["open"]),
            )
        )
    return observations, counts


def _distribution(observations: list[DailyRegimeObservation], field: str) -> dict[str, dict[str, int]]:
    return {
        split: _counts([obs for obs in observations if obs.split == split], field)
        for split in ("train", "validation")
    }


def _counts(observations: list[DailyRegimeObservation], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for observation in observations:
        value = str(getattr(observation, field))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _max_share(observations: list[DailyRegimeObservation], field: str) -> float:
    if not observations:
        return 0.0
    counts = _counts(observations, field)
    return max(counts.values()) / len(observations)


def _source_profiler_blockers(profiler: dict[str, Any] | None) -> list[str]:
    if profiler is None:
        return ["source_v0_54_profiler_report_missing_or_invalid"]
    blockers: list[str] = []
    if profiler.get("profiler_version") != SOURCE_PROFILER_VERSION:
        blockers.append("source_profiler_version_mismatch")
    if profiler.get("train_validation_only") is not True:
        blockers.append("source_profiler_train_validation_only_not_true")
    if profiler.get("oos_used") is not False:
        blockers.append("source_profiler_oos_state_invalid")
    if _volatility_result(profiler) is None:
        blockers.append("source_v0_54_volatility_regime_result_missing")
    return blockers


def _source_design_blockers(design: dict[str, Any] | None) -> list[str]:
    if design is None:
        return ["source_v0_55_design_missing_or_invalid"]
    blockers: list[str] = []
    if design.get("design_version") != SOURCE_DESIGN_VERSION:
        blockers.append("source_design_version_mismatch")
    if design.get("source_profiler_version") != SOURCE_PROFILER_VERSION:
        blockers.append("source_design_profiler_version_mismatch")
    if LEAD_ID not in design.get("profiler_leads_used", []):
        blockers.append("source_design_volatility_lead_not_preserved")
    if design.get("oos_used") is not False:
        blockers.append("source_design_oos_state_invalid")
    return blockers


def _source_rejected_eval_blockers(evaluation: dict[str, Any] | None) -> list[str]:
    if evaluation is None:
        return ["source_v0_56_rejection_evidence_missing_or_invalid"]
    blockers: list[str] = []
    if evaluation.get("evaluation_version") != SOURCE_REJECTED_EVAL_VERSION:
        blockers.append("source_rejected_eval_version_mismatch")
    if evaluation.get("evaluation_status") != "session_block_candidate_rejected":
        blockers.append("session_block_branch_not_marked_rejected")
    if evaluation.get("candidate_passed_train_validation_gate") is not False:
        blockers.append("session_block_rejection_gate_state_invalid")
    if evaluation.get("candidate_locking_allowed_pre_oos") is not False:
        blockers.append("session_block_locking_state_invalid")
    if evaluation.get("oos_used") is not False:
        blockers.append("source_rejected_eval_oos_state_invalid")
    return blockers


def _manifest_blockers(manifest: dict[str, Any] | None) -> list[str]:
    if manifest is None:
        return ["dataset_manifest_missing_or_invalid"]
    policy = manifest.get("split_policy")
    if not isinstance(policy, dict):
        return ["dataset_manifest_split_policy_missing"]
    required = {"train_end", "validation_start", "validation_end", "oos_start"}
    missing = sorted(required.difference(policy))
    return [f"dataset_manifest_split_policy_missing:{','.join(missing)}"] if missing else []


def _volatility_result(profiler: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(profiler, dict):
        return None
    for result in profiler.get("event_family_results", []):
        if isinstance(result, dict) and result.get("event_family_id") == LEAD_ID:
            return result
    return None


def _behavior_summaries(volatility_result: dict[str, Any] | None, split: str) -> dict[str, Any]:
    summary = _split_summary(volatility_result, split)
    behavior_summaries = summary.get("behavior_summaries", {})
    return behavior_summaries if isinstance(behavior_summaries, dict) else {}


def _split_summary(volatility_result: dict[str, Any] | None, split: str) -> dict[str, Any]:
    if not isinstance(volatility_result, dict):
        return {}
    key = "train_summary" if split == "train" else "validation_summary"
    value = volatility_result.get(key, {})
    return value if isinstance(value, dict) else {}


def _behavior_metrics(summary: Any) -> dict[str, Any]:
    points = _regime_points(summary)
    return {
        "event_count": points["count"],
        "mean_same_day_close_open_points": points["mean"],
        "positive_rate": points["positive_rate"],
        "behavior_sign": _sign_label(points["mean"]),
    }


def _behavior_tendency(train_summary: Any, validation_summary: Any) -> str:
    train = _regime_points(train_summary)
    validation = _regime_points(validation_summary)
    if train["count"] == 0 or validation["count"] == 0:
        return "insufficient_observations"
    same_positive = train["mean"] > 0 and validation["mean"] > 0 and train["positive_rate"] >= 0.50 and validation["positive_rate"] >= 0.50
    same_negative = train["mean"] < 0 and validation["mean"] < 0 and train["positive_rate"] <= 0.50 and validation["positive_rate"] <= 0.50
    if same_positive:
        return "positive_same_day_bias_stable"
    if same_negative:
        return "negative_same_day_bias_stable"
    if _same_sign(train["mean"], validation["mean"]):
        return "same_sign_but_rate_mixed"
    return "unstable_between_train_validation"


def _regime_points(summary: Any) -> dict[str, Any]:
    if not isinstance(summary, dict):
        return {"count": 0, "mean": 0.0, "positive_rate": 0.0}
    mean_by_horizon = summary.get("mean_return_points_by_horizon", {})
    positive_by_horizon = summary.get("positive_rate_by_horizon", {})
    return {
        "count": int(summary.get("event_count", 0) or 0),
        "mean": float(mean_by_horizon.get("same_day_close_open_points", 0.0)) if isinstance(mean_by_horizon, dict) else 0.0,
        "positive_rate": float(positive_by_horizon.get("same_day_close_open_points", 0.0)) if isinstance(positive_by_horizon, dict) else 0.0,
    }


def _weighted_mean(values: list[dict[str, Any]]) -> float:
    total = sum(item["count"] for item in values)
    return sum(item["count"] * item["mean"] for item in values) / total if total else 0.0


def _weighted_rate(values: list[dict[str, Any]]) -> float:
    total = sum(item["count"] for item in values)
    return sum(item["count"] * item["positive_rate"] for item in values) / total if total else 0.0


def _event_count(summary: Any) -> int:
    return int(summary.get("event_count", 0) or 0) if isinstance(summary, dict) else 0


def _same_sign(first: float, second: float) -> bool:
    return (first > 0.0 and second > 0.0) or (first < 0.0 and second < 0.0)


def _sign_label(value: float) -> str:
    if value > 0.0:
        return "positive_same_day_bias"
    if value < 0.0:
        return "negative_same_day_bias"
    return "flat"


def _consistency_notes(train_dominant: Any, validation_dominant: Any, same_sign: bool) -> list[str]:
    notes: list[str] = []
    if train_dominant == validation_dominant and train_dominant is not None:
        notes.append("dominant_regime_consistent_train_validation")
    else:
        notes.append("dominant_regime_differs_train_validation")
    if same_sign:
        notes.append("fixed_elevated_group_mean_return_same_sign")
    else:
        notes.append("fixed_elevated_group_mean_return_sign_unstable")
    return notes


def _feasibility_reasons(enough_validation: bool, stable: bool, low_concentration: bool) -> list[str]:
    reasons: list[str] = []
    if not enough_validation:
        reasons.append("fixed_rule_validation_sample_below_50")
    if not stable:
        reasons.append("fixed_rule_behavior_not_stable")
    if not low_concentration:
        reasons.append("fixed_rule_sample_concentration_risk_high")
    if not reasons:
        reasons.append("fixed_existing_regime_labels_have_sufficient_train_validation_structure")
    return reasons


def _session_block_rejected(evaluation: dict[str, Any] | None) -> bool:
    return (
        isinstance(evaluation, dict)
        and evaluation.get("evaluation_status") == "session_block_candidate_rejected"
        and evaluation.get("candidate_passed_train_validation_gate") is False
        and evaluation.get("candidate_locking_allowed_pre_oos") is False
    )


def _quartiles(values: list[float]) -> tuple[float, float, float]:
    return values[len(values) // 4], values[len(values) // 2], values[(3 * len(values)) // 4]


def _vol_label(value: float, q1: float, q2: float, q3: float) -> str:
    if value <= q1:
        return "low_volatility_quartile"
    if value <= q2:
        return "medium_low_volatility_quartile"
    if value <= q3:
        return "medium_high_volatility_quartile"
    return "high_volatility_quartile"


def _split(timestamp: datetime, manifest: dict[str, Any]) -> str:
    policy = manifest["split_policy"]
    if timestamp <= _dt(str(policy["train_end"])):
        return "train"
    if _dt(str(policy["validation_start"])) <= timestamp <= _dt(str(policy["validation_end"])):
        return "validation"
    if timestamp >= _dt(str(policy["oos_start"])):
        return "excluded_oos"
    return "other"


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _empty_counts() -> dict[str, int]:
    return {"train": 0, "validation": 0, "excluded_oos": 0, "other": 0}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "viability_audit_only": True,
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
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
        "trade_recommendation_output_present": False,
        "data_csv_added_to_git": False,
    }
