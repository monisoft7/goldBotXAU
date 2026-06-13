from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.xauusd_spike_family_decision import (
    ABANDON_DECISION,
    BLOCKED_DECISION,
    CREATE_DECISION,
    CANDIDATE_ID,
    decide_spike_family_v0_23,
)

ROOT = Path(__file__).resolve().parents[1]


def _stable_group(
    *,
    timeframe: str = "M5",
    hour: str = "11",
    train_count: int = 902,
    validation_count: int = 142,
    train_rate: float = 0.5283,
    validation_rate: float = 0.5319,
) -> dict[str, object]:
    return {
        "source_timeframe": timeframe,
        "spike_size_bucket": "range_to_atr_1_5_to_2_0",
        "session_bucket": "block_06_12",
        "hour_bucket": hour,
        "stable_enough_for_future_fixed_candidate": True,
        "train_result": {
            "sample_count": train_count,
            "median_range_to_atr": 1.7,
            "fade_vs_continuation_tendency": "fade",
            "forward_behavior": {
                "forward_1bar": {"usable_count": train_count, "fade_rate": 0.51, "continuation_rate": 0.49},
                "forward_3bar": {"usable_count": train_count, "fade_rate": train_rate, "continuation_rate": 1.0 - train_rate},
                "forward_6bar": {"usable_count": train_count, "fade_rate": 0.50, "continuation_rate": 0.50},
            },
        },
        "validation_result": {
            "sample_count": validation_count,
            "median_range_to_atr": 1.72,
            "fade_vs_continuation_tendency": "fade",
            "forward_behavior": {
                "forward_1bar": {"usable_count": validation_count, "fade_rate": 0.52, "continuation_rate": 0.48},
                "forward_3bar": {
                    "usable_count": validation_count,
                    "fade_rate": validation_rate,
                    "continuation_rate": 1.0 - validation_rate,
                },
                "forward_6bar": {"usable_count": validation_count, "fade_rate": 0.50, "continuation_rate": 0.50},
            },
        },
    }


def _profile_report(stable_groups: list[dict[str, object]], *, oos_rows: int = 0) -> dict[str, object]:
    return {
        "profiler_version": "v0_22",
        "status": "profile_ready",
        "dataset": {
            "profiled_splits": ["train", "validation"],
            "oos_row_count_used": oos_rows,
            "source_timeframes": ["M5"],
        },
        "stability_assessment": {
            "stable_group_count": len(stable_groups),
            "stable_groups": stable_groups,
        },
    }


def _write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report), encoding="utf-8")


def test_v0_23_refuses_missing_profiler_report(tmp_path: Path) -> None:
    result = decide_spike_family_v0_23(tmp_path / "missing.json")

    assert result.decision_report["decision"] == BLOCKED_DECISION
    assert result.decision_report["candidate_created"] is False
    assert result.candidate_report is None
    assert "profiler_report_missing" in result.decision_report["reasons"]


def test_v0_23_abandons_inconclusive_profiler_results(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "profile.json"
    _write_report(report_path, _profile_report([]))

    result = decide_spike_family_v0_23(report_path)

    assert result.decision_report["decision"] == ABANDON_DECISION
    assert result.decision_report["candidate_created"] is False
    assert result.candidate_report is None


def test_v0_23_creates_at_most_one_fixed_candidate_from_stable_profile_results(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "profile.json"
    weaker = _stable_group(timeframe="M10", hour="08", train_count=184, validation_count=42)
    stronger = _stable_group()
    _write_report(report_path, _profile_report([weaker, stronger]))

    result = decide_spike_family_v0_23(report_path)
    decision = result.decision_report

    assert decision["decision"] == CREATE_DECISION
    assert decision["candidate_created"] is True
    assert decision["candidate_id"] == CANDIDATE_ID
    assert decision["candidate"]["fixed_profile_group"] == {
        "spike_size_bucket": "range_to_atr_1_5_to_2_0",
        "session_bucket": "block_06_12",
        "hour_bucket": "11",
    }
    assert result.candidate_report is not None
    assert result.candidate_report["candidate_id"] == CANDIDATE_ID
    assert result.candidate_report["candidate"]["rules_are_fixed_from_profile_group"] is True


def test_v0_23_does_not_use_oos_rows(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "profile.json"
    _write_report(report_path, _profile_report([_stable_group()], oos_rows=1))

    result = decide_spike_family_v0_23(report_path)

    assert result.decision_report["decision"] == BLOCKED_DECISION
    assert result.decision_report["candidate_created"] is False
    assert "profiler_report_used_oos_rows" in result.decision_report["reasons"]


def test_no_execution_order_demo_live_or_direction_semantics_are_introduced(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "profile.json"
    _write_report(report_path, _profile_report([_stable_group()]))

    result = decide_spike_family_v0_23(report_path)
    report_text = json.dumps(result.to_dict())
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_spike_family_decision.py",
            ROOT / "scripts" / "decide_spike_family_v0_23.py",
        ]
    ).lower()

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "execution_queue_enabled\": true" not in source_text
    assert result.decision_report["safety"]["threshold_search_used"] is False
    assert result.decision_report["safety"]["parameter_grid_used"] is False


def test_rejected_candidate_registry_tracks_v0_24_without_retuning_old_rejections() -> None:
    registry = research_candidate_registry()
    rejected = [
        candidate
        for candidate in registry["candidates"]
        if str(candidate.get("status")) == "rejected" or str(candidate.get("status", "")).startswith("rejected_")
    ]
    old_rejected = [candidate for candidate in registry["candidates"] if candidate.get("status") == "rejected"]
    v0_23 = [candidate for candidate in registry["candidates"] if candidate["candidate_id"] == CANDIDATE_ID]

    assert registry["candidate_count"] == 8
    assert registry["rejected_count"] == 6
    assert registry["eligible_for_oos_review_count"] == 0
    assert len(rejected) == 6
    assert len(old_rejected) == 5
    assert all(candidate.get("do_not_retune") is True for candidate in old_rejected)
    assert len(v0_23) == 1
    assert v0_23[0]["status"] == "rejected_train_validation_gate_failed"


def test_cli_writes_decision_and_candidate_reports(tmp_path: Path) -> None:
    profile = tmp_path / "reports" / "profile.json"
    decision_output = tmp_path / "reports" / "decision.json"
    candidate_output = tmp_path / "reports" / "candidate.json"
    _write_report(profile, _profile_report([_stable_group()]))

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "decide_spike_family_v0_23.py"),
            "--profile-report",
            str(profile),
            "--output",
            str(decision_output),
            "--candidate-output",
            str(candidate_output),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout)["decision"] == CREATE_DECISION
    assert json.loads(decision_output.read_text(encoding="utf-8"))["candidate_id"] == CANDIDATE_ID
    assert json.loads(candidate_output.read_text(encoding="utf-8"))["status"] == "train_validation_evaluation_only"
