from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.xauusd_compression_expansion_promotion_gate import (
    BLOCKED_DECISION,
    PROMOTE_DECISION,
    PROMOTED_REGISTRY_STATUS,
    REJECT_DECISION,
    REJECTED_REGISTRY_STATUS,
    SOURCE_CANDIDATE_ID,
    decide_compression_expansion_promotion_gate_v0_27,
)

ROOT = Path(__file__).resolve().parents[1]
ACTUAL_CANDIDATE = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
ACTUAL_DECISION = ROOT / "reports" / "xauusd_compression_expansion_decision_v0_26.json"


def _actual_candidate_report() -> dict[str, object]:
    return json.loads(ACTUAL_CANDIDATE.read_text(encoding="utf-8"))


def _actual_decision_report() -> dict[str, object]:
    return json.loads(ACTUAL_DECISION.read_text(encoding="utf-8"))


def _write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report), encoding="utf-8")


def _write_pair(tmp_path: Path, candidate: dict[str, object]) -> tuple[Path, Path]:
    candidate_path = tmp_path / "candidate.json"
    decision_path = tmp_path / "decision.json"
    _write_report(candidate_path, candidate)
    _write_report(decision_path, _actual_decision_report())
    return candidate_path, decision_path


def _set_payload_rates(payload: dict[str, object], train_rate: float, validation_rate: float) -> None:
    train = payload["train_result"]
    validation = payload["validation_result"]
    assert isinstance(train, dict)
    assert isinstance(validation, dict)
    train["primary_metric_rate"] = train_rate
    train["edge_over_neutral"] = train_rate - 0.5
    train["label_rates"] = {
        "next_block_expansion": train_rate,
        "no_next_block_expansion": 1.0 - train_rate,
    }
    validation["primary_metric_rate"] = validation_rate
    validation["edge_over_neutral"] = validation_rate - 0.5
    validation["label_rates"] = {
        "next_block_expansion": validation_rate,
        "no_next_block_expansion": 1.0 - validation_rate,
    }
    degradation = payload["degradation_assessment"]
    assert isinstance(degradation, dict)
    degradation["primary_metric_train"] = train_rate
    degradation["primary_metric_validation"] = validation_rate
    degradation["validation_degradation"] = train_rate - validation_rate
    degradation["within_fixed_limit"] = train_rate - validation_rate <= 0.12


def test_missing_v0_26_report_blocks_cleanly(tmp_path: Path) -> None:
    result = decide_compression_expansion_promotion_gate_v0_27(
        tmp_path / "missing.json",
        ACTUAL_DECISION,
    )

    assert result["decision"] == BLOCKED_DECISION
    assert result["candidate_registry_update"] is None
    assert "v0_26_candidate_report_missing" in result["reasons"]
    assert result["safety"]["oos_evaluated"] is False


def test_invalid_or_inconclusive_v0_26_report_blocks_cleanly(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidate.json"
    _write_report(candidate_path, {"report_version": "v0_26", "candidate_id": SOURCE_CANDIDATE_ID})

    result = decide_compression_expansion_promotion_gate_v0_27(candidate_path, ACTUAL_DECISION)

    assert result["decision"] == BLOCKED_DECISION
    assert "candidate_report_not_train_validation_research_only" in result["reasons"]
    assert result["registry_count_effect_if_applied"]["eligible_for_oos_review_count_delta"] == 0
    assert result["registry_count_effect_if_applied"]["rejected_candidate_count_delta"] == 0


def test_actual_candidate_can_be_promoted_only_without_oos_evaluation() -> None:
    result = decide_compression_expansion_promotion_gate_v0_27(ACTUAL_CANDIDATE, ACTUAL_DECISION)

    assert result["decision"] == PROMOTE_DECISION
    assert result["candidate_registry_update"]["status"] == PROMOTED_REGISTRY_STATUS
    assert result["candidate_registry_update"]["eligible_for_oos_review"] is True
    assert result["candidate_registry_update"]["oos_status"] == "locked_not_evaluated"
    assert result["registry_count_effect_if_applied"]["eligible_for_oos_review_count_delta"] == 1
    assert result["registry_count_effect_if_applied"]["rejected_candidate_count_delta"] == 0
    assert result["evidence_summary"]["oos_rows_used"] == 0
    assert result["safety"]["oos_evaluated"] is False


def test_candidate_with_oos_evaluation_blocks_instead_of_promoting(tmp_path: Path) -> None:
    report = _actual_candidate_report()
    report["evaluation_scope"]["oos_evaluated"] = True
    report["safety"]["oos_evaluated"] = True
    candidate_path, decision_path = _write_pair(tmp_path, report)

    result = decide_compression_expansion_promotion_gate_v0_27(candidate_path, decision_path)

    assert result["decision"] == BLOCKED_DECISION
    assert "candidate_report_oos_evaluated" in result["reasons"]
    assert result["candidate_registry_update"] is None


def test_weak_marginal_candidate_is_rejected_without_oos_evaluation(tmp_path: Path) -> None:
    report = _actual_candidate_report()
    weak = copy.deepcopy(report["timeframe_evidence"])
    _set_payload_rates(weak["combined"], train_rate=0.70, validation_rate=0.60)
    _set_payload_rates(weak["by_timeframe"]["M5"], train_rate=0.70, validation_rate=0.60)
    _set_payload_rates(weak["by_timeframe"]["M10"], train_rate=0.70, validation_rate=0.60)
    report["timeframe_evidence"] = weak
    _set_payload_rates(report, train_rate=0.70, validation_rate=0.60)
    candidate_path, decision_path = _write_pair(tmp_path, report)

    result = decide_compression_expansion_promotion_gate_v0_27(candidate_path, decision_path)

    assert result["decision"] == REJECT_DECISION
    assert result["candidate_registry_update"]["status"] == REJECTED_REGISTRY_STATUS
    assert result["candidate_registry_update"]["eligible_for_oos_review"] is False
    assert result["evidence_summary"]["oos_rows_used"] == 0
    assert "combined_validation_primary_metric_strength" in result["failed_checks"]
    assert "M5_validation_edge_material" in result["failed_checks"]


def test_duplicate_timeframe_confidence_risk_is_handled_conservatively(tmp_path: Path) -> None:
    report = _actual_candidate_report()
    risky = copy.deepcopy(report["timeframe_evidence"])
    _set_payload_rates(risky["combined"], train_rate=0.79, validation_rate=0.72)
    _set_payload_rates(risky["by_timeframe"]["M5"], train_rate=0.62, validation_rate=0.55)
    _set_payload_rates(risky["by_timeframe"]["M10"], train_rate=0.79, validation_rate=0.72)
    report["timeframe_evidence"] = risky
    candidate_path, decision_path = _write_pair(tmp_path, report)

    result = decide_compression_expansion_promotion_gate_v0_27(candidate_path, decision_path)

    assert result["decision"] == REJECT_DECISION
    assert result["evidence_summary"]["double_counting_assessment"]["duplicated_timeframe_confidence_discount_applied"] is True
    assert "M5_validation_primary_metric_strength" in result["failed_checks"]
    assert "m5_m10_validation_rate_consistency" in result["failed_checks"]


def test_m5_m10_inconsistency_prevents_promotion(tmp_path: Path) -> None:
    report = _actual_candidate_report()
    inconsistent = copy.deepcopy(report["timeframe_evidence"])
    m10_validation = inconsistent["by_timeframe"]["M10"]["validation_result"]
    m10_validation["dominant_behavior"] = "no_next_block_expansion"
    inconsistent["by_timeframe"]["M10"]["stability_assessment"] = {
        "label": "weak",
        "stable": False,
        "reason": "fixture inconsistency",
    }
    report["timeframe_evidence"] = inconsistent
    candidate_path, decision_path = _write_pair(tmp_path, report)

    result = decide_compression_expansion_promotion_gate_v0_27(candidate_path, decision_path)

    assert result["decision"] == REJECT_DECISION
    assert "m5_m10_directional_consistency" in result["failed_checks"]


def test_registry_counter_behavior_after_v0_27_promotion() -> None:
    registry = research_candidate_registry()

    assert registry["candidate_count"] == 8
    assert registry["rejected_count"] == 6
    assert registry["eligible_for_oos_review_count"] == 0


def test_no_execution_order_demo_live_or_direction_semantics_are_introduced() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_compression_expansion_promotion_gate.py",
            ROOT / "scripts" / "decide_compression_expansion_promotion_gate_v0_27.py",
        ]
    ).lower()
    report_text = json.dumps(decide_compression_expansion_promotion_gate_v0_27(ACTUAL_CANDIDATE, ACTUAL_DECISION))

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "execution_queue_enabled\": true" not in source_text
    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text


def test_old_rejected_candidates_are_not_modified_or_retuned() -> None:
    candidates = {
        candidate["candidate_id"]: candidate
        for candidate in research_candidate_registry()["candidates"]
    }
    old_ids = [
        "xauusd_atr_impulse_reversion_v0_7",
        "xauusd_multi_bar_exhaustion_reversion_v0_8",
        "xauusd_session_volatility_expansion_v0_11",
        "xauusd_low_atr_range_expansion_followthrough_v0_14",
        "xauusd_low_atr_x_hour_16_v0_17",
    ]

    for candidate_id in old_ids:
        assert candidates[candidate_id]["status"] == "rejected"
        assert candidates[candidate_id]["do_not_retune"] is True
    assert candidates["xauusd_low_tf_spike_m5_hour_11_fade_v0_23"]["status"] == (
        "rejected_train_validation_gate_failed"
    )
    assert candidates["xauusd_low_tf_spike_m5_hour_11_fade_v0_23"]["retuned_rejected_candidate"] is False


def test_v0_26_candidate_is_not_retuned_by_gate() -> None:
    result = decide_compression_expansion_promotion_gate_v0_27(ACTUAL_CANDIDATE, ACTUAL_DECISION)
    registry_candidate = {
        candidate["candidate_id"]: candidate
        for candidate in research_candidate_registry()["candidates"]
    }[SOURCE_CANDIDATE_ID]

    assert result["candidate_registry_update"]["v0_26_candidate_retuned"] is False
    assert registry_candidate["threshold_search_used"] is False
    assert registry_candidate["parameter_grid_used"] is False
    assert registry_candidate["retuned_rejected_candidate"] is False


def test_cli_writes_v0_27_gate_report(tmp_path: Path) -> None:
    output_path = tmp_path / "gate.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "decide_compression_expansion_promotion_gate_v0_27.py"),
            "--candidate-report",
            str(ACTUAL_CANDIDATE),
            "--decision-report",
            str(ACTUAL_DECISION),
            "--output",
            str(output_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout)["decision"] == PROMOTE_DECISION
    assert json.loads(output_path.read_text(encoding="utf-8"))["gate_version"] == "v0_27"
