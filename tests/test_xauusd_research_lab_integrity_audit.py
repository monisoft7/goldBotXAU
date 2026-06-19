from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.research.xauusd_research_lab_integrity_audit import (
    AUDIT_VERSION,
    Candle,
    SyntheticCandle,
    SyntheticTradeCase,
    build_xauusd_research_lab_integrity_audit_v0_58,
    detect_duplicate_timestamps,
    detect_missing_candle_gaps,
    synthetic_trade_outcome_r,
    validate_split_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, timestamps: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for index, timestamp in enumerate(timestamps):
            open_price = 1900.0 + index
            writer.writerow(
                {
                    "timestamp": timestamp,
                    "open": open_price,
                    "high": open_price + 1.0,
                    "low": open_price - 1.0,
                    "close": open_price + 0.25,
                    "volume": 1,
                }
            )


def _manifest() -> dict[str, object]:
    return {
        "manifest_version": "v0_5",
        "split_policy": {
            "train_end": "2025-01-01T00:10:00",
            "validation_start": "2025-01-01T00:15:00",
            "validation_end": "2025-01-01T00:30:00",
            "oos_start": "2025-01-01T00:35:00",
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_required_reports(root: Path) -> None:
    reports = root / "reports"
    _write_json(
        reports / "xauusd_external_shortlist_board_v0_53.json",
        {
            "board_status": "no_external_shortlist_candidate_passed",
            "best_candidate_passed_gate": False,
            "candidate_created": False,
            "oos_used": False,
            "retune_performed": False,
            "threshold_search_performed": False,
            "parameter_grid_performed": False,
            "demo_execution_allowed": False,
            "order_send_called": False,
            "order_check_called": False,
        },
    )
    _write_json(
        reports / "xauusd_session_block_bias_eval_v0_56.json",
        {
            "evaluation_status": "session_block_candidate_rejected",
            "candidate_passed_train_validation_gate": False,
            "candidate_locking_allowed_pre_oos": False,
            "oos_used": False,
            "retune_performed": False,
            "threshold_search_performed": False,
            "parameter_grid_performed": False,
            "demo_execution_allowed": False,
            "order_send_called": False,
            "order_check_called": False,
        },
    )
    _write_json(
        reports / "xauusd_volatility_regime_lead_viability_v0_57.json",
        {
            "audit_status": "volatility_lead_viability_completed",
            "volatility_lead_viability_decision": "volatility_lead_unstable_or_too_weak_reject",
            "oos_used": False,
            "retune_performed": False,
            "threshold_search_performed": False,
            "parameter_grid_performed": False,
            "demo_execution_allowed": False,
            "order_send_called": False,
            "order_check_called": False,
        },
    )


def _build_fixture_report(tmp_path: Path) -> dict[str, object]:
    timestamps = [
        "2025-01-01 00:00:00",
        "2025-01-01 00:05:00",
        "2025-01-01 00:10:00",
        "2025-01-01 00:15:00",
        "2025-01-01 00:20:00",
        "2025-01-01 00:25:00",
        "2025-01-01 00:30:00",
        "2025-01-01 00:35:00",
        "2025-01-01 00:40:00",
    ]
    data = tmp_path / "data"
    _write_csv(data / "xauusd_m5_xauusd_2023-01-01_2025-12-31.csv", timestamps)
    _write_csv(data / "xauusd_m10_xauusd_m5_xauusd_2023_01_01_2025_12_31_2023-01-03_2025-12-31.csv", timestamps[::2])
    _write_csv(data / "xauusd_m15_xauusd_2023-01-01_2026-06-11.csv", timestamps[::3])
    manifest = tmp_path / "reports" / "manifest.json"
    _write_json(manifest, _manifest())
    _write_required_reports(tmp_path)
    return build_xauusd_research_lab_integrity_audit_v0_58(
        data_dir=data,
        manifest_path=manifest,
        prior_report_paths={
            "v0_53_external_shortlist": tmp_path / "reports" / "xauusd_external_shortlist_board_v0_53.json",
            "v0_56_session_block": tmp_path / "reports" / "xauusd_session_block_bias_eval_v0_56.json",
            "v0_57_volatility_viability": tmp_path / "reports" / "xauusd_volatility_regime_lead_viability_v0_57.json",
        },
    )


def test_synthetic_target_hit_accounting_passes() -> None:
    outcome = synthetic_trade_outcome_r(
        SyntheticTradeCase(
            case_id="target",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=101.1, low=100.2, close=101.0),),
            expected_outcome_r=1.0,
        )
    )

    assert outcome == 1.0


def test_synthetic_stop_hit_accounting_passes() -> None:
    outcome = synthetic_trade_outcome_r(
        SyntheticTradeCase(
            case_id="stop",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=100.2, low=98.9, close=99.0),),
            expected_outcome_r=-1.0,
        )
    )

    assert outcome == -1.0


def test_both_stop_target_uses_conservative_stop_first() -> None:
    outcome = synthetic_trade_outcome_r(
        SyntheticTradeCase(
            case_id="both",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=101.1, low=98.9, close=100.5),),
            expected_outcome_r=-1.0,
        )
    )

    assert outcome == -1.0


def test_time_exit_accounting_passes() -> None:
    outcome = synthetic_trade_outcome_r(
        SyntheticTradeCase(
            case_id="time",
            entry=100.0,
            stop=99.0,
            target=None,
            candles=(SyntheticCandle(high=100.7, low=99.5, close=100.5),),
            expected_outcome_r=0.5,
        )
    )

    assert outcome == 0.5


def test_invalidation_exit_accounting_passes() -> None:
    outcome = synthetic_trade_outcome_r(
        SyntheticTradeCase(
            case_id="invalidation",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=100.3, low=99.3, close=99.75),),
            expected_outcome_r=-0.25,
            invalidation_exit_r=-0.25,
        )
    )

    assert outcome == -0.25


def test_no_entry_day_returns_no_trade() -> None:
    outcome = synthetic_trade_outcome_r(
        SyntheticTradeCase(
            case_id="no_entry",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=101.0, low=99.0, close=100.0),),
            expected_outcome_r=None,
            entry_allowed=False,
        )
    )

    assert outcome is None


def test_duplicate_timestamp_detection_works() -> None:
    records = [
        Candle(datetime(2025, 1, 1, 0, 0), 1, 2, 0, 1, 1, "fixture"),
        Candle(datetime(2025, 1, 1, 0, 0), 1, 2, 0, 1, 1, "fixture"),
    ]

    assert detect_duplicate_timestamps(records) == ["2025-01-01T00:00:00"]


def test_missing_candle_gap_detection_works() -> None:
    records = [
        Candle(datetime(2025, 1, 1, 0, 0), 1, 2, 0, 1, 1, "fixture"),
        Candle(datetime(2025, 1, 1, 0, 15), 1, 2, 0, 1, 1, "fixture"),
    ]

    gaps = detect_missing_candle_gaps(records, 5)
    assert len(gaps) == 1
    assert gaps[0]["minutes"] == 15


def test_split_boundary_validation_works() -> None:
    assert validate_split_boundaries(_manifest()["split_policy"]) is True
    assert validate_split_boundaries(
        {
            "train_end": "2025-01-02T00:00:00",
            "validation_start": "2025-01-01T00:00:00",
            "validation_end": "2025-01-03T00:00:00",
            "oos_start": "2025-01-04T00:00:00",
        }
    ) is False


def test_oos_exclusion_validation_works(tmp_path: Path) -> None:
    report = _build_fixture_report(tmp_path)

    assert report["split_integrity"]["oos_rows_excluded_from_train_validation_tools"] is True
    assert report["split_integrity"]["split_counts"]["M5"]["excluded_oos"] == 2


def test_safety_flags_remain_false(tmp_path: Path) -> None:
    report = _build_fixture_report(tmp_path)

    assert report["audit_version"] == AUDIT_VERSION
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


def test_no_order_send_order_check_live_or_data_csv_staged(tmp_path: Path) -> None:
    report = _build_fixture_report(tmp_path)
    completed = subprocess.run(
        ["git", "status", "--short", "--", "data/*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["data_csv_added_to_git"] is False
    assert completed.stdout.strip() == ""


def test_cli_writes_required_report(tmp_path: Path) -> None:
    data = tmp_path / "data"
    timestamps = [
        "2025-01-01 00:00:00",
        "2025-01-01 00:05:00",
        "2025-01-01 00:10:00",
        "2025-01-01 00:15:00",
        "2025-01-01 00:20:00",
        "2025-01-01 00:25:00",
        "2025-01-01 00:30:00",
        "2025-01-01 00:35:00",
    ]
    _write_csv(data / "xauusd_m5_xauusd_2023-01-01_2025-12-31.csv", timestamps)
    _write_csv(data / "xauusd_m10_xauusd_m5_xauusd_2023_01_01_2025_12_31_2023-01-03_2025-12-31.csv", timestamps[::2])
    _write_csv(data / "xauusd_m15_xauusd_2023-01-01_2026-06-11.csv", timestamps[::3])
    manifest = tmp_path / "reports" / "manifest.json"
    output = tmp_path / "reports" / "audit.json"
    _write_json(manifest, _manifest())

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_xauusd_research_lab_integrity_v0_58.py"),
            "--json",
            "--output",
            str(output),
            "--data-dir",
            str(data),
            "--manifest",
            str(manifest),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["audit_version"] == AUDIT_VERSION
    assert output_report["purpose"] == "research_lab_integrity_diagnostic_not_strategy"
