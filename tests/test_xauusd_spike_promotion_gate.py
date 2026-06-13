from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.xauusd_spike_promotion_gate import (
    BLOCKED_DECISION,
    PROMOTE_DECISION,
    REJECT_DECISION,
    REJECTED_REGISTRY_STATUS,
    SOURCE_CANDIDATE_ID,
    decide_spike_promotion_gate_v0_24,
)

ROOT = Path(__file__).resolve().parents[1]


def _candidate_report(
    *,
    train_count: int = 902,
    validation_count: int = 142,
    train_rates: dict[str, float] | None = None,
    validation_rates: dict[str, float] | None = None,
    oos_evaluated: bool = False,
) -> dict[str, object]:
    train_rates = train_rates or {
        "forward_1bar": 0.54,
        "forward_3bar": 0.5283,
        "forward_6bar": 0.5211,
    }
    validation_rates = validation_rates or {
        "forward_1bar": 0.5319,
        "forward_3bar": 0.5319,
        "forward_6bar": 0.5319,
    }
    return {
        "report_version": "v0_23",
        "candidate_id": SOURCE_CANDIDATE_ID,
        "status": "train_validation_evaluation_only",
        "candidate": {
            "candidate_id": SOURCE_CANDIDATE_ID,
            "candidate_version": "v0_23",
            "status": "train_validation_research_candidate_only",
            "source_profile": "xauusd_low_tf_spike_profile_v0_22",
            "source_timeframe": "M5",
            "fixed_profile_group": {
                "spike_size_bucket": "range_to_atr_1_5_to_2_0",
                "session_bucket": "block_06_12",
                "hour_bucket": "11",
            },
            "observed_behavior_label": "fade",
            "forward_horizon_bars": 3,
            "rules_are_fixed_from_profile_group": True,
            "threshold_search_used": False,
            "parameter_grid_used": False,
            "oos_status": "locked_not_evaluated",
            "eligible_for_oos_review": False,
            "research_only": True,
        },
        "train_result": _split_result(train_count, train_rates),
        "validation_result": _split_result(validation_count, validation_rates),
        "evaluation_scope": {
            "splits": ["train", "validation"],
            "oos_evaluated": oos_evaluated,
            "source": "fixture_train_validation_only",
        },
        "safety": {
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
            "execution_queue_enabled": False,
            "buy_sell_output_allowed": False,
            "execution_logic_present": False,
            "trade_recommendation_output_present": False,
            "oos_evaluated": oos_evaluated,
            "threshold_search_used": False,
            "parameter_grid_used": False,
            "rejected_candidate_retuned": False,
        },
    }


def _split_result(sample_count: int, rates: dict[str, float]) -> dict[str, object]:
    return {
        "fade_vs_continuation_tendency": "fade",
        "sample_count": sample_count,
        "forward_behavior": {
            horizon: {
                "usable_count": sample_count,
                "fade_rate": rate,
                "continuation_rate": 1.0 - rate,
            }
            for horizon, rate in rates.items()
        },
    }


def _write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report), encoding="utf-8")


def test_missing_v0_23_report_blocks_cleanly(tmp_path: Path) -> None:
    result = decide_spike_promotion_gate_v0_24(tmp_path / "missing.json")

    assert result["decision"] == BLOCKED_DECISION
    assert result["candidate_registry_update"] is None
    assert "v0_23_candidate_report_missing" in result["reasons"]
    assert result["safety"]["oos_evaluated"] is False


def test_invalid_or_inconclusive_v0_23_report_blocks_cleanly(tmp_path: Path) -> None:
    report_path = tmp_path / "candidate.json"
    _write_report(report_path, {"report_version": "v0_23", "candidate_id": SOURCE_CANDIDATE_ID})

    result = decide_spike_promotion_gate_v0_24(report_path)

    assert result["decision"] == BLOCKED_DECISION
    assert "candidate_report_not_train_validation_evaluation_only" in result["reasons"]
    assert result["registry_count_effect_if_applied"]["eligible_for_oos_review_count_delta"] == 0
    assert result["registry_count_effect_if_applied"]["rejected_candidate_count_delta"] == 0


def test_candidate_can_be_promoted_only_without_oos_evaluation(tmp_path: Path) -> None:
    report_path = tmp_path / "candidate.json"
    _write_report(
        report_path,
        _candidate_report(
            train_count=900,
            validation_count=260,
            train_rates={"forward_1bar": 0.57, "forward_3bar": 0.58, "forward_6bar": 0.56},
            validation_rates={"forward_1bar": 0.56, "forward_3bar": 0.57, "forward_6bar": 0.55},
            oos_evaluated=False,
        ),
    )

    result = decide_spike_promotion_gate_v0_24(report_path)

    assert result["decision"] == PROMOTE_DECISION
    assert result["candidate_registry_update"]["eligible_for_oos_review"] is True
    assert result["candidate_registry_update"]["oos_status"] == "locked_not_evaluated"
    assert result["registry_count_effect_if_applied"]["eligible_for_oos_review_count_delta"] == 1
    assert result["safety"]["oos_evaluated"] is False


def test_candidate_with_oos_evaluation_blocks_instead_of_promoting(tmp_path: Path) -> None:
    report_path = tmp_path / "candidate.json"
    _write_report(
        report_path,
        _candidate_report(
            train_count=900,
            validation_count=260,
            train_rates={"forward_1bar": 0.57, "forward_3bar": 0.58, "forward_6bar": 0.56},
            validation_rates={"forward_1bar": 0.56, "forward_3bar": 0.57, "forward_6bar": 0.55},
            oos_evaluated=True,
        ),
    )

    result = decide_spike_promotion_gate_v0_24(report_path)

    assert result["decision"] == BLOCKED_DECISION
    assert "candidate_report_oos_evaluated" in result["reasons"]
    assert result["candidate_registry_update"] is None


def test_weak_candidate_is_rejected_without_oos_evaluation(tmp_path: Path) -> None:
    report_path = tmp_path / "candidate.json"
    _write_report(report_path, _candidate_report())

    result = decide_spike_promotion_gate_v0_24(report_path)

    assert result["decision"] == REJECT_DECISION
    assert result["candidate_registry_update"]["status"] == REJECTED_REGISTRY_STATUS
    assert result["candidate_registry_update"]["eligible_for_oos_review"] is False
    assert result["evidence_summary"]["oos_rows_used"] == 0
    assert {"validation_sample_size_sufficiency", "material_validation_3bar_edge"}.issubset(
        set(result["failed_checks"])
    )


def test_actual_v0_23_candidate_is_rejected_by_fixed_gate() -> None:
    result = decide_spike_promotion_gate_v0_24(ROOT / "reports" / "xauusd_spike_fixed_candidate_v0_23_train_validation.json")

    assert result["decision"] == REJECT_DECISION
    assert result["candidate_registry_update"]["status"] == REJECTED_REGISTRY_STATUS
    assert result["evidence_summary"]["validation_sample_count"] == 142
    assert result["evidence_summary"]["validation_3bar_target_rate"] < 0.56


def test_rejected_and_eligible_counter_behavior_is_correct() -> None:
    registry = research_candidate_registry()

    assert registry["candidate_count"] == 8
    assert registry["rejected_count"] == 6
    assert registry["eligible_for_oos_review_count"] == 0


def test_no_execution_order_demo_live_or_direction_semantics_are_introduced() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_spike_promotion_gate.py",
            ROOT / "scripts" / "decide_spike_promotion_gate_v0_24.py",
        ]
    ).lower()
    report_text = json.dumps(decide_spike_promotion_gate_v0_24(ROOT / "reports" / "xauusd_spike_fixed_candidate_v0_23_train_validation.json"))

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "execution_queue_enabled\": true" not in source_text
    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text


def test_rejected_old_candidates_are_not_modified_or_retuned() -> None:
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


def test_cli_writes_v0_24_gate_report(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidate.json"
    output_path = tmp_path / "gate.json"
    _write_report(candidate_path, _candidate_report())

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "decide_spike_promotion_gate_v0_24.py"),
            "--candidate-report",
            str(candidate_path),
            "--output",
            str(output_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout)["decision"] == REJECT_DECISION
    assert json.loads(output_path.read_text(encoding="utf-8"))["gate_version"] == "v0_24"
