from __future__ import annotations

import json
from pathlib import Path

from src.research.xauusd_post_oos_governance import (
    CANDIDATE_ID,
    SOURCE_OOS_DECISION,
    build_xauusd_post_oos_governance_v0_30,
    save_xauusd_post_oos_governance_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _marker(*, repeat_allowed: bool = False, decision: str = SOURCE_OOS_DECISION) -> dict[str, object]:
    return {
        "review_version": "v0_29",
        "candidate_id": CANDIDATE_ID,
        "decision": decision,
        "output_path": "reports/xauusd_oos_review_v0_29.json",
        "repeat_review_allowed": repeat_allowed,
    }


def _repair(*, completed: bool = True, detailed_metrics_available: bool = False) -> dict[str, object]:
    return {
        "repair_version": "v0_29_1",
        "marker_decision_preserved": SOURCE_OOS_DECISION,
        "repeat_review_allowed": False,
        "detailed_oos_metrics_available": detailed_metrics_available,
        "restored_main_report": {"oos_result": None},
        "safety": {
            "one_time_oos_review_completed": completed,
            "repeat_review_allowed": False,
        },
    }


def _candidate() -> dict[str, object]:
    return {
        "candidate_id": CANDIDATE_ID,
        "research_only": True,
        "fixed_rules": {
            "time_basis": "dataset_timestamp_hour_buckets_only",
            "reference_blocks": ["block_00_06", "block_06_12", "block_12_18"],
            "response_blocks": ["block_06_12", "block_12_18", "block_18_24"],
            "forward_behavior_label": "next_block_expansion",
            "threshold_search_used": False,
            "parameter_grid_used": False,
            "retuning_used": False,
        },
    }


def _write_inputs(
    tmp_path: Path,
    *,
    marker: dict[str, object] | None = None,
    repair: dict[str, object] | None = None,
    candidate: dict[str, object] | None = None,
) -> tuple[Path, Path, Path]:
    reports = tmp_path / "reports"
    reports.mkdir()
    marker_path = reports / "xauusd_oos_review_v0_29.marker.json"
    repair_path = reports / "xauusd_oos_review_repair_v0_29_1.json"
    candidate_path = reports / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    if marker is not None:
        marker_path.write_text(json.dumps(marker), encoding="utf-8")
    if repair is not None:
        repair_path.write_text(json.dumps(repair), encoding="utf-8")
    if candidate is not None:
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    return marker_path, repair_path, candidate_path


def test_governance_blocks_if_oos_marker_missing(tmp_path: Path) -> None:
    marker_path, repair_path, candidate_path = _write_inputs(tmp_path, repair=_repair(), candidate=_candidate())

    report = build_xauusd_post_oos_governance_v0_30(
        marker_path=marker_path,
        repair_report_path=repair_path,
        candidate_report_path=candidate_path,
    )

    assert report["governance_status"] == "blocked_post_oos_governance_prerequisites_not_met"
    assert any(blocker.startswith("oos_marker_missing") for blocker in report["blockers"])
    assert report["execution_allowed"] is False


def test_governance_blocks_if_repeat_review_allowed_true(tmp_path: Path) -> None:
    marker_path, repair_path, candidate_path = _write_inputs(
        tmp_path,
        marker=_marker(repeat_allowed=True),
        repair=_repair(),
        candidate=_candidate(),
    )

    report = build_xauusd_post_oos_governance_v0_30(
        marker_path=marker_path,
        repair_report_path=repair_path,
        candidate_report_path=candidate_path,
    )

    assert "oos_marker_repeat_review_allowed_not_false" in report["blockers"]
    assert report["repeat_oos_review_allowed"] is False


def test_governance_blocks_if_oos_not_completed(tmp_path: Path) -> None:
    marker_path, repair_path, candidate_path = _write_inputs(
        tmp_path,
        marker=_marker(),
        repair=_repair(completed=False),
        candidate=_candidate(),
    )

    report = build_xauusd_post_oos_governance_v0_30(
        marker_path=marker_path,
        repair_report_path=repair_path,
        candidate_report_path=candidate_path,
    )

    assert "one_time_oos_review_not_completed" in report["blockers"]
    assert report["one_time_oos_review_completed"] is False


def test_governance_creates_paper_shadow_design_only() -> None:
    report = build_xauusd_post_oos_governance_v0_30(
        marker_path=ROOT / "reports" / "xauusd_oos_review_v0_29.marker.json",
        repair_report_path=ROOT / "reports" / "xauusd_oos_review_repair_v0_29_1.json",
        candidate_report_path=ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json",
    )

    assert report["candidate_id"] == CANDIDATE_ID
    assert report["source_oos_marker_decision"] == SOURCE_OOS_DECISION
    assert report["detailed_oos_metrics_available"] is False
    assert report["detailed_oos_metrics_confirmed_unavailable"] is True
    assert report["repeat_oos_review_allowed"] is False
    assert report["governance_status"] == "post_oos_governance_created_design_only"
    assert report["paper_shadow_protocol_status"] == "design_only_not_started"
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["non_actions_performed"]["paper_shadow_observation_started"] is False
    assert report["next_recommended_step"] == "v0_31 build read-only paper-shadow journal simulator, no execution"


def test_governance_does_not_run_or_repeat_oos() -> None:
    source_text = (ROOT / "src" / "research" / "xauusd_post_oos_governance.py").read_text(encoding="utf-8")

    assert "run_xauusd_oos_review_v0_29" not in source_text
    assert "load_oos_rows" not in source_text
    assert "evaluate_oos" not in source_text
    assert "new_oos_run_performed" in source_text


def test_governance_does_not_modify_candidate_rules(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    output_path = tmp_path / "xauusd_post_oos_governance_v0_30.json"

    report = build_xauusd_post_oos_governance_v0_30()
    save_xauusd_post_oos_governance_report(report, output_path)
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_rules_lock"]["candidate_rules_modified"] is False
    assert report["candidate_rules_lock"]["rule_change_allowed"] is False


def test_governance_source_introduces_no_execution_or_direction_output() -> None:
    source_text_raw = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_post_oos_governance.py",
            ROOT / "scripts" / "build_xauusd_post_oos_governance_v0_30.py",
        ]
    )
    source_text = source_text_raw.lower()

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_allowed\": true" not in source_text
    assert "live_allowed\": true" not in source_text
    assert "execution_allowed\": true" not in source_text
    assert "B" + "UY" not in source_text_raw
    assert "S" + "ELL" not in source_text_raw


def test_governance_report_contains_no_directional_output(tmp_path: Path) -> None:
    output_path = tmp_path / "report.json"
    report = build_xauusd_post_oos_governance_v0_30()
    save_xauusd_post_oos_governance_report(report, output_path)
    report_text = output_path.read_text(encoding="utf-8")

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert report["future_paper_shadow_prerequisites"]["journal_only_observations"] is True
    assert report["future_paper_shadow_prerequisites"]["risk_notes_only"] is True
