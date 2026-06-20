from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_market_context_feasibility_audit import (
    AUDIT_VERSION,
    BLOCKED_MISSING_V0_60_REPORT,
    COMPLETED,
    build_xauusd_market_context_feasibility_audit_v0_61,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeSymbol:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeMt5:
    def __init__(self, *, initialize_ok: bool = True) -> None:
        self.initialize_ok = initialize_ok
        self.initialize_called = False
        self.shutdown_called = False

    def initialize(self) -> bool:
        self.initialize_called = True
        return self.initialize_ok

    def shutdown(self) -> None:
        self.shutdown_called = True

    def last_error(self) -> tuple[int, str]:
        return (1, "fake unavailable")

    def symbols_get(self) -> list[FakeSymbol]:
        return [
            FakeSymbol("XAUUSD"),
            FakeSymbol("DXY"),
            FakeSymbol("USDOLLAR"),
            FakeSymbol("US10Y"),
            FakeSymbol("US02Y"),
        ]


def _write_v0_60(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "board_version": "v0_60",
                "board_status": "no_second_tier_candidate_passed",
                "best_candidate_id": "ny_liquidity_sweep_reversal",
                "best_candidate_passed_gate": False,
                "rejected_do_not_retune_candidates": [
                    "failed_m15_swing_breakout_reversal",
                    "ny_liquidity_sweep_reversal",
                    "sequential_m5_move_mean_reversion",
                ],
                "train_validation_only": True,
                "oos_used": False,
            }
        ),
        encoding="utf-8",
    )


def _build(tmp_path: Path, *, mt5: FakeMt5 | None = None) -> dict[str, object]:
    previous = tmp_path / "reports" / "xauusd_second_tier_board_v0_60.json"
    _write_v0_60(previous)
    return build_xauusd_market_context_feasibility_audit_v0_61(
        previous_board_path=previous,
        mt5_module=mt5,
    )


def test_v0_60_report_is_required(tmp_path: Path) -> None:
    report = build_xauusd_market_context_feasibility_audit_v0_61(
        previous_board_path=tmp_path / "missing.json",
        attempt_mt5_symbol_discovery=False,
    )

    assert report["audit_version"] == AUDIT_VERSION
    assert report["audit_status"] == BLOCKED_MISSING_V0_60_REPORT
    assert "missing_or_invalid_v0_60_second_tier_board_report" in report["blockers"]
    assert report["approved_for_strategy_testing"] is False


def test_pure_ohlc_branch_failure_is_recorded(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())

    assert report["audit_status"] == COMPLETED
    assert report["source_previous_board_version"] == "v0_60"
    status = report["pure_ohlc_branch_status"]
    assert status["source_board_status"] == "no_second_tier_candidate_passed"
    assert status["best_candidate_id"] == "ny_liquidity_sweep_reversal"
    assert status["best_candidate_passed_gate"] is False
    assert status["pure_ohlc_branch_failure_recorded"] is True


def test_market_open_closed_context_is_defined(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())
    feasibility = report["market_open_closed_feasibility"]

    assert "market_open_closed_session_state" in report["market_context_families_audited"]
    assert "market_closed_weekend" in feasibility["future_labels"]
    assert "market_closed_holiday" in feasibility["future_labels"]
    assert "london_ny_overlap" in feasibility["future_labels"]
    assert feasibility["can_infer_weekends_from_existing_timestamps"] is True
    assert feasibility["closed_market_tradeable_signal_allowed"] is False


def test_holiday_calendar_schema_is_documented(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())
    holiday = report["holiday_calendar_feasibility"]

    assert holiday["status"] == "schema_defined_external_dataset_required"
    assert holiday["required_future_dataset_category"] == "US_market_holidays_and_reduced_liquidity_days"
    assert holiday["schema"] == [
        "date",
        "market",
        "country",
        "holiday_name",
        "closure_type",
        "liquidity_impact",
        "source",
        "timestamp_basis",
    ]
    assert holiday["v0_61_dataset_downloaded"] is False


def test_economic_calendar_schema_and_required_events_are_documented(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())
    calendar = report["economic_calendar_feasibility"]

    assert calendar["schema"] == [
        "event_time_utc",
        "currency",
        "event_name",
        "impact",
        "actual",
        "forecast",
        "previous",
        "source",
        "revision_flag",
    ]
    assert {"CPI", "PPI", "NFP", "FOMC Rate Decision", "Fed Chair Speech"}.issubset(
        set(calendar["required_events"])
    )
    assert "pre_high_impact_us_event_window" in calendar["event_window_labels"]
    assert "actual_forecast_surprise_unavailable_before_release_timestamp" in calendar["anti_lookahead_rules"]


def test_dxy_usd_proxy_feasibility_is_audited(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())
    dxy = report["dxy_proxy_feasibility"]

    assert report["mt5_symbol_discovery_attempted"] is True
    assert dxy["approved_data"] is False
    assert dxy["candidate_symbols"] == ["DXY", "USDOLLAR"]
    assert dxy["future_ohlc_schema"] == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "source_symbol",
        "timeframe",
        "timestamp_basis",
        "source",
    ]


def test_us_yields_rates_feasibility_is_audited(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())
    yields = report["us_yields_proxy_feasibility"]

    assert yields["approved_data"] is False
    assert yields["candidate_symbols"] == ["US02Y", "US10Y"]
    assert yields["external_offline_data_needed_if_no_broker_symbol"] is False


def test_geopolitical_label_schema_is_documented(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())
    geo = report["geopolitical_label_feasibility"]

    assert "geopolitical_risk_bid" in geo["future_labels"]
    assert "unexpected_shock_window" in geo["future_labels"]
    assert geo["live_scraping_allowed"] is False
    assert geo["manual_subjective_labels_allowed_for_strategy_testing"] is False


def test_technical_permission_gate_outputs_are_defined(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())
    gate = report["technical_permission_gate_defined"]

    assert gate["defined"] is True
    assert gate["future_gate_outputs"] == [
        "allow_technical_research",
        "block_due_to_closed_market",
        "block_due_to_thin_liquidity",
        "block_due_to_event_risk",
        "block_due_to_missing_context_data",
        "observe_only_due_to_macro_uncertainty",
    ]
    assert gate["trading_logic_in_v0_61"] is False


def test_policy_documentation_flags_are_true(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())

    assert report["external_feature_schema_documented"] is True
    assert report["anti_lookahead_policy_documented"] is True
    assert report["data_alignment_policy_documented"] is True
    assert report["api_key_storage_policy_documented"] is True


def test_approval_flags_remain_false(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())

    assert report["approved_for_v0_62_feature_import"] is False
    assert report["approved_for_strategy_testing"] is False


def test_no_strategy_backtest_oos_retune_search_or_execution(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())

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
    assert report["safety"]["backtest_candidate_created"] is False


def test_missing_mt5_keeps_audit_completed_with_manual_data_plan(tmp_path: Path) -> None:
    mt5 = FakeMt5(initialize_ok=False)
    report = _build(tmp_path, mt5=mt5)

    assert report["audit_status"] == COMPLETED
    assert report["mt5_symbol_discovery_attempted"] is True
    assert report["mt5_symbol_discovery"]["status"] == "mt5_initialize_failed"
    assert report["discovered_candidate_symbols"] == {
        "dxy_usd_proxy": [],
        "us_yields_rates_proxy": [],
    }
    assert report["recommended_v0_62_plan"] == "document manual/offline data acquisition requirements before context research."


def test_data_csv_not_staged_or_committed(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=FakeMt5())
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
    previous = tmp_path / "reports" / "xauusd_second_tier_board_v0_60.json"
    _write_v0_60(previous)
    output = tmp_path / "reports" / "audit.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_xauusd_market_context_feasibility_v0_61.py"),
            "--json",
            "--output",
            str(output),
            "--previous-board",
            str(previous),
            "--skip-mt5-symbol-discovery",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["audit_version"] == AUDIT_VERSION
    assert output_report["audit_status"] == COMPLETED
    assert output_report["mt5_symbol_discovery_attempted"] is False
    assert output_report["approved_for_strategy_testing"] is False
