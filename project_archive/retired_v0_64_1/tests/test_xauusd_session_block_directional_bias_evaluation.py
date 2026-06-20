from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

from src.research.xauusd_session_block_directional_bias_evaluation import (
    BLOCKED_MISSING_DESIGN,
    CANDIDATE_ID,
    EVALUATION_VERSION,
    PASSED,
    REJECTED,
    build_xauusd_session_block_directional_bias_evaluation_v0_56,
)

ROOT = Path(__file__).resolve().parents[1]


def _design_report() -> dict[str, object]:
    return {
        "design_version": "v0_55",
        "design_status": "session_volatility_design_completed_with_v0_56_candidate",
        "source_profiler_version": "v0_54",
        "source_profiler_status": "edge_profile_completed_with_research_leads",
        "profiler_leads_used": ["session_return_profile", "volatility_regime_profile"],
        "recommended_candidate_for_v0_56": CANDIDATE_ID,
        "candidate_design_count": 4,
        "candidate_designs": [
            {
                "candidate_design_id": CANDIDATE_ID,
                "source_lead": "session_return_profile",
                "market_logic": "fixed session block",
                "exact_entry_rule": "On each train/validation day with a complete asian_00_06 M15 block, enter once at the first M15 open inside that fixed UTC block.",
                "exact_direction_rule": "Derive direction from train only: if train mean block_return_points for asian_00_06 is positive use long; if negative use short; if zero, reject before testing. Current v0_54 train value implies long.",
                "exact_invalidation_rule": "Invalidate the day if the asian_00_06 block is incomplete, the first M15 open or final block close is missing, or the train-derived direction is zero.",
                "stop_loss_logic": "Use the opposite edge of the prior completed fixed session block range as the structural stop; for long use that prior block low, for short use that prior block high. Do not optimize distance.",
                "take_profit_or_exit_logic": "No optimized profit target; exit at the final M15 close inside the same fixed asian_00_06 block.",
                "time_session_filter": "Only the fixed UTC asian_00_06 block from v0_54.",
                "volatility_filter": "None in this design; volatility filters are reserved for separate v0_55 designs.",
                "expected_trade_frequency": "At most one completed fixed session-block observation per train/validation trading day.",
                "minimum_data_required": "At least 100 train observations and 50 validation observations for the selected fixed session block.",
                "main_failure_modes": [],
                "anti_curve_fit_argument": "No session-window optimization.",
                "train_validation_test_plan": "Compute fixed train and validation metrics only.",
                "rejection_metrics": [],
                "candidate_design_suitability_score": 35,
                "recommended_action": "promote_to_v0_56_train_validation_test",
            },
            {"candidate_design_id": "other_v0_55_candidate"},
        ],
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
    }


def _manifest() -> dict[str, object]:
    return {
        "manifest_version": "v0_5",
        "split_policy": {
            "method": "fixed_chronological_split",
            "train_end": "2025-02-28T23:59:59",
            "validation_start": "2025-03-01T00:00:00",
            "validation_end": "2025-05-31T23:59:59",
            "oos_start": "2025-06-01T00:00:00",
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_m15_csv(path: Path, *, validation_losses: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    current = date(2025, 1, 1)
    end = date(2025, 5, 10)
    sequence = 0
    while current <= end:
        is_validation = current >= date(2025, 3, 1)
        loss_day = validation_losses and is_validation
        if not loss_day:
            loss_day = sequence % 5 == 0
        base = 1900.0 + sequence * 0.2
        final_close = base - 1.0 if loss_day else base + 2.0
        for index in range(28):
            stamp = datetime.combine(current, time.min) + timedelta(minutes=15 * index)
            open_price = base if index == 0 else base + 0.1
            close = final_close if index == 27 else open_price + 0.05
            rows.append(
                {
                    "timestamp": stamp.isoformat(sep=" "),
                    "open": open_price,
                    "high": max(open_price, close) + 0.25,
                    "low": min(open_price, close, base - 10.0),
                    "close": close,
                    "volume": 1,
                }
            )
        current += timedelta(days=1)
        sequence += 1
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _build_report(tmp_path: Path, *, validation_losses: bool = False) -> dict[str, object]:
    design = tmp_path / "reports" / "design.json"
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    _write_json(design, _design_report())
    _write_json(manifest, _manifest())
    _write_m15_csv(data_dir / "xauusd_m15_fixture.csv", validation_losses=validation_losses)
    return build_xauusd_session_block_directional_bias_evaluation_v0_56(
        data_dir=data_dir,
        pattern="xauusd_m15_*.csv",
        manifest_path=manifest,
        source_design_path=design,
    )


def test_v0_55_report_is_required(tmp_path: Path) -> None:
    report = build_xauusd_session_block_directional_bias_evaluation_v0_56(
        data_dir=tmp_path / "data",
        manifest_path=tmp_path / "manifest.json",
        source_design_path=tmp_path / "missing.json",
    )

    assert report["evaluation_status"] == BLOCKED_MISSING_DESIGN
    assert report["blockers"] == ["source_v0_55_design_missing_or_invalid"]


def test_exactly_one_candidate_is_evaluated_and_rules_are_preserved(tmp_path: Path) -> None:
    report = _build_report(tmp_path)

    assert report["evaluation_version"] == EVALUATION_VERSION
    assert report["candidate_id"] == CANDIDATE_ID
    assert report["candidate_rules_preserved"] is True
    assert report["evaluated_candidate_count"] == 1
    assert report["other_v0_55_candidates_evaluated"] is False
    assert report["selected_candidate_rules"]["candidate_design_id"] == CANDIDATE_ID


def test_train_validation_only_without_oos_retune_grid_or_execution(tmp_path: Path) -> None:
    report = _build_report(tmp_path)

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


def test_passing_fixture_allows_candidate_locking_pre_oos_only(tmp_path: Path) -> None:
    report = _build_report(tmp_path)

    assert report["evaluation_status"] == PASSED
    assert report["train_metrics"]["profit_factor"] >= 1.20
    assert report["validation_metrics"]["profit_factor"] >= 1.15
    assert report["validation_metrics"]["trades"] >= 50
    assert report["candidate_passed_train_validation_gate"] is True
    assert report["candidate_locking_allowed_pre_oos"] is True
    assert report["demo_execution_allowed"] is False
    assert report["next_recommended_step"] == "v0_57 lock fixed candidate artifact and prepare one-time OOS protocol, no OOS yet."


def test_failing_fixture_rejects_do_not_retune(tmp_path: Path) -> None:
    report = _build_report(tmp_path, validation_losses=True)

    assert report["evaluation_status"] == REJECTED
    assert report["candidate_passed_train_validation_gate"] is False
    assert report["candidate_locking_allowed_pre_oos"] is False
    assert report["rejected_do_not_retune"] is True
    assert "validation_profit_factor_below_fixed_gate" in report["blockers"]
    assert "validation_expectancy_not_positive" in report["blockers"]


def test_report_includes_required_distributions(tmp_path: Path) -> None:
    report = _build_report(tmp_path)

    assert report["metrics_by_session_block"]["asian_00_06"]["validation"]["trades"] >= 50
    assert isinstance(report["metrics_by_volatility_regime_if_available"], dict)
    assert report["trade_distribution_by_year"]["validation"]
    assert report["trade_distribution_by_month"]["validation"]
    assert report["side_distribution"]["combined"] == {"long": report["train_metrics"]["trades"] + report["validation_metrics"]["trades"]}
    assert report["sample_concentration_risk"]["risk_level"] in {"low", "high"}


def test_data_csv_not_staged_or_committed(tmp_path: Path) -> None:
    report = _build_report(tmp_path)
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
    design = tmp_path / "reports" / "design.json"
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    output = tmp_path / "reports" / "eval.json"
    _write_json(design, _design_report())
    _write_json(manifest, _manifest())
    _write_m15_csv(data_dir / "xauusd_m15_fixture.csv")

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_session_block_bias_eval_v0_56.py"),
            "--json",
            "--output",
            str(output),
            "--source-design",
            str(design),
            "--manifest",
            str(manifest),
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
    assert stdout_report["evaluation_version"] == EVALUATION_VERSION
    assert output_report["candidate_id"] == CANDIDATE_ID
    assert output_report["oos_used"] is False
