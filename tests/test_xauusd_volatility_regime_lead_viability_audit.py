from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

from src.research.xauusd_volatility_regime_lead_viability_audit import (
    AUDIT_VERSION,
    BLOCKED_MISSING_PROFILER,
    COMPLETED,
    DECISION_INSUFFICIENT,
    DECISION_REJECT,
    DECISION_VIABLE,
    build_xauusd_volatility_regime_lead_viability_audit_v0_57,
)

ROOT = Path(__file__).resolve().parents[1]


def _behavior(count: int, mean_points: float, positive_rate: float) -> dict[str, object]:
    return {
        "event_count": count,
        "mean_return_points_by_horizon": {"same_day_close_open_points": mean_points},
        "positive_rate_by_horizon": {"same_day_close_open_points": positive_rate},
    }


def _profiler_report(
    *,
    validation_medium_high_count: int = 60,
    validation_high_count: int = 70,
    train_high_mean: float = -2.0,
    validation_high_mean: float = 8.0,
    validation_medium_high_mean: float = 5.0,
) -> dict[str, object]:
    train_behaviors = {
        "low_volatility_quartile": _behavior(120, 0.2, 0.48),
        "medium_low_volatility_quartile": _behavior(140, 1.5, 0.55),
        "medium_high_volatility_quartile": _behavior(160, 6.0, 0.60),
        "high_volatility_quartile": _behavior(100, train_high_mean, 0.42 if train_high_mean < 0 else 0.58),
    }
    validation_behaviors = {
        "low_volatility_quartile": _behavior(8, 0.1, 0.50),
        "medium_low_volatility_quartile": _behavior(12, 0.4, 0.55),
        "medium_high_volatility_quartile": _behavior(validation_medium_high_count, validation_medium_high_mean, 0.58),
        "high_volatility_quartile": _behavior(validation_high_count, validation_high_mean, 0.59 if validation_high_mean > 0 else 0.40),
    }
    return {
        "profiler_version": "v0_54",
        "profiler_status": "edge_profile_completed_with_research_leads",
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "event_family_results": [
            {
                "event_family_id": "volatility_regime_profile",
                "event_count_train": sum(int(v["event_count"]) for v in train_behaviors.values()),
                "event_count_validation": sum(int(v["event_count"]) for v in validation_behaviors.values()),
                "total_event_count": sum(int(v["event_count"]) for v in train_behaviors.values())
                + sum(int(v["event_count"]) for v in validation_behaviors.values()),
                "train_summary": {
                    "event_count": sum(int(v["event_count"]) for v in train_behaviors.values()),
                    "primary_horizon": "same_day_close_open_points",
                    "dominant_behavior": "medium_high_volatility_quartile",
                    "dominant_behavior_mean_return_points": 6.0,
                    "behavior_summaries": train_behaviors,
                },
                "validation_summary": {
                    "event_count": sum(int(v["event_count"]) for v in validation_behaviors.values()),
                    "primary_horizon": "same_day_close_open_points",
                    "dominant_behavior": "high_volatility_quartile",
                    "dominant_behavior_mean_return_points": validation_high_mean,
                    "behavior_summaries": validation_behaviors,
                },
            }
        ],
    }


def _design_report() -> dict[str, object]:
    return {
        "design_version": "v0_55",
        "design_status": "session_volatility_design_completed_with_v0_56_candidate",
        "source_profiler_version": "v0_54",
        "profiler_leads_used": ["session_return_profile", "volatility_regime_profile"],
        "train_validation_only": True,
        "oos_used": False,
    }


def _rejected_eval_report() -> dict[str, object]:
    return {
        "evaluation_version": "v0_56",
        "evaluation_status": "session_block_candidate_rejected",
        "candidate_passed_train_validation_gate": False,
        "candidate_locking_allowed_pre_oos": False,
        "train_validation_only": True,
        "oos_used": False,
    }


def _manifest() -> dict[str, object]:
    return {
        "manifest_version": "v0_5",
        "split_policy": {
            "train_end": "2024-04-30T23:59:59",
            "validation_start": "2024-05-01T00:00:00",
            "validation_end": "2025-09-30T23:59:59",
            "oos_start": "2025-10-01T00:00:00",
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_m15_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    current = date(2024, 1, 1)
    end = date(2025, 9, 30)
    index = 0
    while current <= end:
        range_points = 1.0 + (index % 8)
        open_price = 1900.0 + index * 0.1
        close = open_price + (2.0 if index % 3 else -0.5)
        rows.append(
            {
                "timestamp": datetime.combine(current, time.min).isoformat(sep=" "),
                "open": open_price,
                "high": max(open_price, close) + range_points,
                "low": min(open_price, close) - range_points,
                "close": close,
                "volume": 1,
            }
        )
        current += timedelta(days=1)
        index += 1
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _build_report(tmp_path: Path, profiler: dict[str, object] | None = None) -> dict[str, object]:
    reports_dir = tmp_path / "reports"
    data_dir = tmp_path / "data"
    profiler_path = reports_dir / "profiler.json"
    design_path = reports_dir / "design.json"
    rejected_eval_path = reports_dir / "rejected_eval.json"
    manifest_path = reports_dir / "manifest.json"
    if profiler is not None:
        _write_json(profiler_path, profiler)
    _write_json(design_path, _design_report())
    _write_json(rejected_eval_path, _rejected_eval_report())
    _write_json(manifest_path, _manifest())
    _write_m15_csv(data_dir / "xauusd_m15_fixture.csv")
    return build_xauusd_volatility_regime_lead_viability_audit_v0_57(
        data_dir=data_dir,
        pattern="xauusd_m15_*.csv",
        manifest_path=manifest_path,
        source_profiler_path=profiler_path,
        source_design_path=design_path,
        source_rejected_eval_path=rejected_eval_path,
    )


def test_v0_54_profiler_report_is_required(tmp_path: Path) -> None:
    report = _build_report(tmp_path, profiler=None)

    assert report["audit_status"] == BLOCKED_MISSING_PROFILER
    assert report["volatility_lead_viability_decision"] == BLOCKED_MISSING_PROFILER
    assert "source_v0_54_profiler_report_missing_or_invalid" in report["blockers"]


def test_preserves_v0_56_rejection_evidence_and_session_block_rejection(tmp_path: Path) -> None:
    report = _build_report(tmp_path, _profiler_report())

    assert report["source_rejected_eval_version"] == "v0_56"
    assert report["session_block_branch_rejected"] is True
    assert report["source_rejected_eval_status"] == "session_block_candidate_rejected"


def test_train_validation_only_without_oos_retune_grid_or_execution(tmp_path: Path) -> None:
    report = _build_report(tmp_path, _profiler_report())

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["data_csv_added_to_git"] is False


def test_viable_fixture_produces_exactly_one_recommended_v0_58_design(tmp_path: Path) -> None:
    report = _build_report(tmp_path, _profiler_report())

    assert report["audit_version"] == AUDIT_VERSION
    assert report["audit_status"] == COMPLETED
    assert report["volatility_lead_viability_decision"] == DECISION_VIABLE
    design = report["recommended_v0_58_candidate_design"]
    assert design["candidate_design_id"] == "volatility_regime_elevated_same_day_bias_candidate"
    assert len([design]) == 1
    assert report["validation_sample_sufficiency"]["can_produce_at_least_50_validation_trades_under_fixed_rules"] is True
    assert report["candidate_design_feasibility"]["candidate_design_feasible_for_v0_58"] is True


def test_insufficient_sample_fixture_blocks_promotion(tmp_path: Path) -> None:
    profiler = _profiler_report(validation_medium_high_count=20, validation_high_count=10)
    report = _build_report(tmp_path, profiler)

    assert report["audit_status"] == COMPLETED
    assert report["volatility_lead_viability_decision"] == DECISION_INSUFFICIENT
    assert report["recommended_v0_58_candidate_design"] == {}
    assert "fixed_elevated_regime_validation_observations_below_50" in report["blockers"]


def test_unstable_fixture_rejects_lead(tmp_path: Path) -> None:
    profiler = _profiler_report(
        validation_medium_high_count=60,
        validation_high_count=70,
        validation_high_mean=-8.0,
        validation_medium_high_mean=-5.0,
    )
    report = _build_report(tmp_path, profiler)

    assert report["audit_status"] == COMPLETED
    assert report["volatility_lead_viability_decision"] == DECISION_REJECT
    assert report["recommended_v0_58_candidate_design"] == {}
    assert report["train_validation_consistency"]["consistency_status"] == "unstable_or_weak"


def test_data_csv_not_staged_or_committed(tmp_path: Path) -> None:
    report = _build_report(tmp_path, _profiler_report())
    completed = subprocess.run(
        ["git", "status", "--short", "--", "data/*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert report["data_csv_added_to_git"] is False
    assert completed.stdout.strip() == ""


def test_cli_writes_required_report(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    data_dir = tmp_path / "data"
    profiler_path = reports_dir / "profiler.json"
    design_path = reports_dir / "design.json"
    rejected_eval_path = reports_dir / "rejected_eval.json"
    manifest_path = reports_dir / "manifest.json"
    output = reports_dir / "audit.json"
    _write_json(profiler_path, _profiler_report())
    _write_json(design_path, _design_report())
    _write_json(rejected_eval_path, _rejected_eval_report())
    _write_json(manifest_path, _manifest())
    _write_m15_csv(data_dir / "xauusd_m15_fixture.csv")

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_xauusd_volatility_regime_lead_v0_57.py"),
            "--json",
            "--output",
            str(output),
            "--source-profiler",
            str(profiler_path),
            "--source-design",
            str(design_path),
            "--source-rejected-eval",
            str(rejected_eval_path),
            "--manifest",
            str(manifest_path),
            "--data-dir",
            str(data_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["audit_version"] == AUDIT_VERSION
    assert output_report["lead_id"] == "volatility_regime_profile"
    assert output_report["oos_used"] is False
