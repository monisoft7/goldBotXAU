from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_market_context_labeler import (
    BLOCKED_MISSING_V0_61_REPORT,
    COMPLETED,
    LABELER_VERSION,
    build_xauusd_market_context_labels_v0_62,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_v0_61(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "audit_version": "v0_61",
                "audit_status": "market_context_feasibility_completed",
                "purpose": "market_context_layer_feasibility_only",
                "market_open_closed_feasibility": {
                    "session_liquidity_basis": "utc_time_windows_only_until_broker_timestamp_basis_is_confirmed",
                },
                "discovered_candidate_symbols": {
                    "dxy_usd_proxy": ["DXYN", "DXYZ", "GDXY", "USDX"],
                    "us_yields_rates_proxy": [],
                },
                "approved_for_strategy_testing": False,
            }
        ),
        encoding="utf-8",
    )


def _write_primary_csvs(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        [
            "timestamp,open,high,low,close,volume",
            "2026-01-05 01:00,2000,2001,1999,2000.5,1",
            "2026-01-05 07:00,2000,2001,1999,2000.5,1",
            "2026-01-06 12:00,2000,2001,1999,2000.5,1",
            "2026-01-09 18:00,2000,2001,1999,2000.5,1",
            "2026-01-10 11:45,2000,2001,1999,2000.5,1",
            "2026-01-07 22:00,2000,2001,1999,2000.5,1",
        ]
    )
    for filename in (
        "xauusd_m5_xauusd_2023-01-01_2025-12-31.csv",
        "xauusd_m10_xauusd_m5_xauusd_2023_01_01_2025_12_31_2023-01-03_2025-12-31.csv",
        "xauusd_m15_xauusd_2023-01-01_2026-06-11.csv",
    ):
        (data_dir / filename).write_text(rows + "\n", encoding="utf-8")


def _build(tmp_path: Path) -> dict[str, object]:
    data_dir = tmp_path / "data"
    source = tmp_path / "reports" / "xauusd_market_context_feasibility_v0_61.json"
    _write_primary_csvs(data_dir)
    _write_v0_61(source)
    return build_xauusd_market_context_labels_v0_62(data_dir=data_dir, source_feasibility_path=source)


def test_v0_61_report_is_required(tmp_path: Path) -> None:
    report = build_xauusd_market_context_labels_v0_62(
        data_dir=tmp_path / "data",
        source_feasibility_path=tmp_path / "missing.json",
    )

    assert report["labeler_version"] == LABELER_VERSION
    assert report["labeler_status"] == BLOCKED_MISSING_V0_61_REPORT
    assert report["missing_context_data_summary"]["hard_block_missing_required_context_data"] is True
    assert report["approved_for_strategy_testing"] is False


def test_timestamp_only_labels_are_created(tmp_path: Path) -> None:
    report = _build(tmp_path)

    assert report["labeler_status"] == COMPLETED
    assert report["timestamp_only_labels"] == [
        "market_closed_weekend",
        "likely_market_open",
        "asian_session",
        "london_morning_session",
        "ny_core_session",
        "late_us_session",
        "off_session_or_low_activity",
        "session_transition_asian_to_london",
        "session_transition_london_to_ny",
        "friday_late_session",
        "monday_reopen_window",
    ]
    counts = report["label_counts"]
    assert counts["market_closed_weekend"] == 3
    assert counts["likely_market_open"] == 15
    assert counts["asian_session"] == 3
    assert counts["london_morning_session"] == 6
    assert counts["ny_core_session"] == 3
    assert counts["late_us_session"] == 3
    assert counts["off_session_or_low_activity"] == 3
    assert counts["session_transition_asian_to_london"] == 3
    assert counts["session_transition_london_to_ny"] == 6
    assert counts["friday_late_session"] == 3
    assert counts["monday_reopen_window"] == 3


def test_placeholder_external_labels_are_defined_but_not_blockers(tmp_path: Path) -> None:
    report = _build(tmp_path)

    assert set(report["placeholder_external_labels"]) == {
        "holiday_us_reduced_liquidity",
        "high_impact_us_event_window",
        "pre_event_window",
        "post_event_repricing_window",
        "fomc_day",
        "nfp_day",
        "cpi_day",
        "dxy_available",
        "dxy_unavailable",
        "yields_available",
        "yields_unavailable",
        "geopolitical_risk_label_available",
        "geopolitical_risk_label_missing",
    }
    assert report["dxy_placeholder_status"]["trade_filter_allowed"] is False
    assert report["yields_placeholder_status"]["trade_filter_allowed"] is False
    assert report["calendar_placeholder_status"]["hard_blocker"] is False
    assert report["holiday_placeholder_status"]["hard_blocker"] is False


def test_labels_are_observational_not_trade_blockers(tmp_path: Path) -> None:
    report = _build(tmp_path)

    assert report["labels_are_trade_blockers"] is False
    assert report["hard_blockers_limited_to_market_closed_and_missing_data"] is True
    assert report["hard_context_outputs"] == [
        "hard_block_market_closed",
        "hard_block_missing_required_context_data",
    ]
    assert report["soft_context_outputs"] == [
        "observe_holiday_context",
        "observe_event_context",
        "observe_dxy_context",
        "observe_session_context",
        "observe_geopolitical_context",
    ]


def test_approval_and_execution_safety_flags_remain_locked(tmp_path: Path) -> None:
    report = _build(tmp_path)

    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False
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
    assert report["safety"]["strategy_evaluation"] is False
    assert report["safety"]["holiday_news_dxy_session_labels_block_trades"] is False


def test_session_and_weekend_distributions_are_reported(tmp_path: Path) -> None:
    report = _build(tmp_path)

    assert report["timeframes_used"] == ["M10", "M15", "M5"]
    assert report["session_distribution"]["asian_session"] == 3
    assert report["weekend_closed_distribution"] == {
        "market_closed_weekend": 3,
        "likely_market_open": 15,
    }
    assert report["missing_context_data_summary"]["hard_block_missing_required_context_data"] is False


def test_data_csv_not_staged_or_committed(tmp_path: Path) -> None:
    report = _build(tmp_path)
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
    data_dir = tmp_path / "data"
    source = tmp_path / "reports" / "xauusd_market_context_feasibility_v0_61.json"
    output = tmp_path / "reports" / "labels.json"
    _write_primary_csvs(data_dir)
    _write_v0_61(source)

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_market_context_labels_v0_62.py"),
            "--json",
            "--output",
            str(output),
            "--data-dir",
            str(data_dir),
            "--source-feasibility",
            str(source),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["labeler_version"] == LABELER_VERSION
    assert output_report["labeler_status"] == COMPLETED
    assert output_report["labels_are_trade_blockers"] is False
