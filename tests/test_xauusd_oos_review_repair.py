from __future__ import annotations

import json
from pathlib import Path

from scripts.repair_xauusd_oos_review_report_v0_29_1 import repair_xauusd_oos_review_report_v0_29_1

ROOT = Path(__file__).resolve().parents[1]


def _locked_marker(path: Path) -> dict[str, object]:
    return {
        "review_version": "v0_29",
        "candidate_id": "xauusd_compression_then_expansion_v0_26",
        "decision": "oos_passed_research_validation",
        "output_path": str(path),
        "repeat_review_allowed": False,
    }


def _blocked_report() -> dict[str, object]:
    return {
        "review_version": "v0_29",
        "candidate_id": "xauusd_compression_then_expansion_v0_26",
        "decision": "blocked_missing_or_invalid_approval",
        "blockers": ["approval_token_missing_or_invalid"],
        "oos_result": None,
        "safety": {
            "oos_evaluated": False,
            "one_time_oos_review_completed": False,
        },
    }


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    report_path = tmp_path / "reports" / "xauusd_oos_review_v0_29.json"
    marker_path = tmp_path / "reports" / "xauusd_oos_review_v0_29.marker.json"
    repair_path = tmp_path / "reports" / "xauusd_oos_review_repair_v0_29_1.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(_blocked_report()), encoding="utf-8")
    marker_path.write_text(json.dumps(_locked_marker(report_path)), encoding="utf-8")
    return marker_path, report_path, repair_path


def test_repair_detects_marker_report_mismatch(tmp_path: Path) -> None:
    marker_path, report_path, repair_path = _write_fixture(tmp_path)

    result = repair_xauusd_oos_review_report_v0_29_1(
        marker_path=marker_path,
        report_path=report_path,
        repair_output_path=repair_path,
    )

    assert result["marker_report_mismatch_detected"] is True
    assert "report_decision_mismatch" in result["mismatch_reasons"]
    assert result["overwritten_report_detected"] is True
    assert repair_path.exists()


def test_repair_preserves_marker_decision_and_repeat_lock(tmp_path: Path) -> None:
    marker_path, report_path, repair_path = _write_fixture(tmp_path)

    result = repair_xauusd_oos_review_report_v0_29_1(
        marker_path=marker_path,
        report_path=report_path,
        repair_output_path=repair_path,
    )
    repaired = json.loads(report_path.read_text(encoding="utf-8"))

    assert result["marker_decision_preserved"] == "oos_passed_research_validation"
    assert repaired["decision"] == "oos_passed_research_validation"
    assert repaired["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert repaired["one_time_review"]["repeat_review_allowed"] is False
    assert repaired["safety"]["repeat_review_allowed"] is False


def test_repair_does_not_invent_detailed_metrics(tmp_path: Path) -> None:
    marker_path, report_path, repair_path = _write_fixture(tmp_path)

    result = repair_xauusd_oos_review_report_v0_29_1(
        marker_path=marker_path,
        report_path=report_path,
        repair_output_path=repair_path,
    )
    repaired = json.loads(report_path.read_text(encoding="utf-8"))
    repaired_text = json.dumps(repaired)

    assert result["detailed_oos_metrics_available"] is False
    assert repaired["detailed_oos_metrics_available"] is False
    assert repaired["oos_result"] is None
    assert "primary_metric_rate" not in repaired_text
    assert "edge_over_neutral" not in repaired_text
    assert "sample_count" not in repaired_text


def test_repair_source_introduces_no_execution_or_direction_output() -> None:
    source_text_raw = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "scripts" / "repair_xauusd_oos_review_report_v0_29_1.py",
            ROOT / "scripts" / "run_xauusd_oos_review_v0_29.py",
            ROOT / "src" / "research" / "xauusd_oos_review.py",
        ]
    )
    source_text = source_text_raw.lower()

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "execution_queue_enabled\": true" not in source_text
    assert "B" + "UY" not in source_text_raw
    assert "S" + "ELL" not in source_text_raw
