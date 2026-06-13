"""v0_23 decision gate for the low-timeframe spike research family."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DECISION_VERSION = "v0_23"
DEFAULT_PROFILE_REPORT = Path("reports") / "xauusd_low_tf_spike_profile_v0_22.json"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_spike_fixed_candidate_v0_23_train_validation.json"
CANDIDATE_ID = "xauusd_low_tf_spike_m5_hour_11_fade_v0_23"
CREATE_DECISION = "create_fixed_candidate_from_stable_profile_group"
ABANDON_DECISION = "abandon_spike_family_no_stable_train_validation_behavior"
BLOCKED_DECISION = "blocked_profiler_report_missing_or_inconclusive"
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


@dataclass(frozen=True)
class SpikeFamilyDecisionResult:
    decision_report: dict[str, Any]
    candidate_report: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decide_spike_family_v0_23(
    profile_report_path: str | Path = DEFAULT_PROFILE_REPORT,
) -> SpikeFamilyDecisionResult:
    path = Path(profile_report_path)
    if not path.exists():
        return SpikeFamilyDecisionResult(
            decision_report=_blocked_report(
                profile_report_path=path,
                reasons=["profiler_report_missing"],
            ),
            candidate_report=None,
        )

    try:
        profile_report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return SpikeFamilyDecisionResult(
            decision_report=_blocked_report(
                profile_report_path=path,
                reasons=[f"profiler_report_invalid_json: {exc}"],
            ),
            candidate_report=None,
        )

    blockers = _profile_blockers(profile_report)
    if blockers:
        return SpikeFamilyDecisionResult(
            decision_report=_blocked_report(
                profile_report_path=path,
                reasons=blockers,
                profile_report=profile_report,
            ),
            candidate_report=None,
        )

    stable_groups = list(profile_report.get("stability_assessment", {}).get("stable_groups", []))
    if not stable_groups:
        return SpikeFamilyDecisionResult(
            decision_report=_abandon_report(profile_report_path=path, profile_report=profile_report),
            candidate_report=None,
        )

    selected = _select_strongest_group(stable_groups)
    candidate_report = _candidate_report(profile_report_path=path, selected_group=selected)
    decision_report = _create_report(
        profile_report_path=path,
        profile_report=profile_report,
        selected_group=selected,
        candidate_report_path=DEFAULT_CANDIDATE_REPORT,
    )
    return SpikeFamilyDecisionResult(decision_report=decision_report, candidate_report=candidate_report)


def save_spike_family_decision_reports(
    result: SpikeFamilyDecisionResult,
    decision_output: str | Path,
    candidate_output: str | Path | None = DEFAULT_CANDIDATE_REPORT,
) -> None:
    decision_path = Path(decision_output)
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(json.dumps(result.decision_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if result.candidate_report is not None and candidate_output is not None:
        candidate_path = Path(candidate_output)
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(
            json.dumps(result.candidate_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _profile_blockers(profile_report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if profile_report.get("status") != "profile_ready":
        blockers.append("profiler_report_not_profile_ready")
    if profile_report.get("profiler_version") != "v0_22":
        blockers.append("unexpected_profiler_version")
    dataset = profile_report.get("dataset", {})
    if int(dataset.get("oos_row_count_used", -1) or 0) != 0:
        blockers.append("profiler_report_used_oos_rows")
    if dataset.get("profiled_splits") != ["train", "validation"]:
        blockers.append("profiler_report_did_not_use_train_validation_only")
    stability = profile_report.get("stability_assessment", {})
    stable_count = int(stability.get("stable_group_count", 0) or 0)
    stable_groups = stability.get("stable_groups", [])
    if stable_count > 0 and not stable_groups:
        blockers.append("profiler_report_stable_group_payload_missing")
    return blockers


def _select_strongest_group(stable_groups: list[dict[str, Any]]) -> dict[str, Any]:
    return max(stable_groups, key=_stable_group_strength_key)


def _stable_group_strength_key(group: dict[str, Any]) -> tuple[float, float, float, str, str, str, str]:
    train = group["train_result"]
    validation = group["validation_result"]
    tendency = str(train["fade_vs_continuation_tendency"])
    metric = f"{tendency}_rate"
    train_rate = float(train["forward_behavior"]["forward_3bar"][metric])
    validation_rate = float(validation["forward_behavior"]["forward_3bar"][metric])
    rate_gap = abs(train_rate - validation_rate)
    return (
        float(validation["sample_count"]),
        float(train["sample_count"]),
        -rate_gap,
        str(group["source_timeframe"]),
        str(group["spike_size_bucket"]),
        str(group["session_bucket"]),
        str(group["hour_bucket"]),
    )


def _create_report(
    *,
    profile_report_path: Path,
    profile_report: dict[str, Any],
    selected_group: dict[str, Any],
    candidate_report_path: Path,
) -> dict[str, Any]:
    candidate = _candidate_definition(selected_group)
    return _base_report(
        decision=CREATE_DECISION,
        profile_report_path=profile_report_path,
        profile_report=profile_report,
        candidate_created=True,
        selected_group=selected_group,
        candidate=candidate,
        candidate_report_path=str(candidate_report_path),
        reasons=[
            "v0_22 reported at least one stable train/validation group.",
            "Selected one group by validation sample count, then train sample count, then smallest 3-bar tendency-rate gap.",
            "Candidate rules are copied from the selected profile group without search or retuning.",
        ],
    )


def _abandon_report(*, profile_report_path: Path, profile_report: dict[str, Any]) -> dict[str, Any]:
    return _base_report(
        decision=ABANDON_DECISION,
        profile_report_path=profile_report_path,
        profile_report=profile_report,
        candidate_created=False,
        selected_group=None,
        candidate=None,
        candidate_report_path=None,
        reasons=["No stable train/validation group was available in the v0_22 profile report."],
    )


def _blocked_report(
    *,
    profile_report_path: Path,
    reasons: list[str],
    profile_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _base_report(
        decision=BLOCKED_DECISION,
        profile_report_path=profile_report_path,
        profile_report=profile_report,
        candidate_created=False,
        selected_group=None,
        candidate=None,
        candidate_report_path=None,
        reasons=reasons,
    )


def _base_report(
    *,
    decision: str,
    profile_report_path: Path,
    profile_report: dict[str, Any] | None,
    candidate_created: bool,
    selected_group: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    candidate_report_path: str | None,
    reasons: list[str],
) -> dict[str, Any]:
    profile_dataset = profile_report.get("dataset", {}) if profile_report else {}
    return {
        "decision_version": DECISION_VERSION,
        "decision": decision,
        "profile_report_path": str(profile_report_path),
        "candidate_created": candidate_created,
        "candidate_id": candidate["candidate_id"] if candidate else None,
        "candidate_report_path": candidate_report_path,
        "selected_profile_group": selected_group,
        "candidate": candidate,
        "input_summary": {
            "profiler_version": profile_report.get("profiler_version") if profile_report else None,
            "profile_status": profile_report.get("status") if profile_report else None,
            "oos_row_count_used": int(profile_dataset.get("oos_row_count_used", 0) or 0),
            "profiled_splits": profile_dataset.get("profiled_splits", []),
            "stable_group_count": int(
                profile_report.get("stability_assessment", {}).get("stable_group_count", 0) or 0
            )
            if profile_report
            else 0,
        },
        "selection_policy": {
            "source": "v0_22_stable_groups_only",
            "sort_order": [
                "largest_validation_sample_count",
                "largest_train_sample_count",
                "smallest_forward_3bar_tendency_rate_gap",
                "deterministic_group_labels",
            ],
            "threshold_search_used": False,
            "parameter_grid_used": False,
        },
        "reasons": reasons,
        "safety": dict(SAFETY_FLAGS),
    }


def _candidate_definition(selected_group: dict[str, Any]) -> dict[str, Any]:
    tendency = str(selected_group["train_result"]["fade_vs_continuation_tendency"])
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_version": DECISION_VERSION,
        "status": "train_validation_research_candidate_only",
        "source_profile": "xauusd_low_tf_spike_profile_v0_22",
        "source_timeframe": selected_group["source_timeframe"],
        "fixed_profile_group": {
            "spike_size_bucket": selected_group["spike_size_bucket"],
            "session_bucket": selected_group["session_bucket"],
            "hour_bucket": selected_group["hour_bucket"],
        },
        "observed_behavior_label": tendency,
        "forward_horizon_bars": 3,
        "rules_are_fixed_from_profile_group": True,
        "threshold_search_used": False,
        "parameter_grid_used": False,
        "oos_status": "locked_not_evaluated",
        "eligible_for_oos_review": False,
        "research_only": True,
    }


def _candidate_report(*, profile_report_path: Path, selected_group: dict[str, Any]) -> dict[str, Any]:
    candidate = _candidate_definition(selected_group)
    return {
        "report_version": DECISION_VERSION,
        "candidate_id": CANDIDATE_ID,
        "status": "train_validation_evaluation_only",
        "source_profile_report": str(profile_report_path),
        "candidate": candidate,
        "train_result": selected_group["train_result"],
        "validation_result": selected_group["validation_result"],
        "evaluation_scope": {
            "splits": ["train", "validation"],
            "oos_evaluated": False,
            "source": "v0_22_selected_stable_profile_group",
        },
        "safety": dict(SAFETY_FLAGS),
        "notes": [
            "Research-only event behavior summary.",
            "No OOS data was evaluated.",
            "No search or retuning was performed.",
        ],
    }
