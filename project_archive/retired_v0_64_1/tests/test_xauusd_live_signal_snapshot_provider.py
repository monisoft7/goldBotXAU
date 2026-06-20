from __future__ import annotations

import importlib
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.execution.xauusd_live_signal_snapshot_provider import (
    BLOCKED_INSUFFICIENT_LIVE_CANDLES,
    BLOCKED_MT5_UNAVAILABLE,
    BLOCKED_SYMBOL_UNAVAILABLE,
    SNAPSHOT_READY_NO_QUALIFIED_SIGNAL,
    SNAPSHOT_READY_ORDER_REQUEST_BUILT_DRY_RUN_ONLY,
    SNAPSHOT_READY_SIGNAL_CONFIRMED_DIRECTION_UNASSIGNED,
    build_xauusd_live_signal_snapshot_v0_45,
)

ROOT = Path(__file__).resolve().parents[1]
SAFE_NOW = datetime(2026, 6, 18, 15, 0, tzinfo=UTC)
CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"


class FakeMt5:
    TIMEFRAME_M5 = 5
    TIMEFRAME_M10 = 10

    def __init__(
        self,
        *,
        initialize_result: bool = True,
        symbol_info_result: object | None = object(),
        symbol_select_result: bool = True,
        rates_by_timeframe: dict[int, list[dict[str, float]]] | None = None,
    ) -> None:
        self.initialize_result = initialize_result
        self.symbol_info_result = symbol_info_result
        self.symbol_select_result = symbol_select_result
        self.rates_by_timeframe = rates_by_timeframe or {}
        self.shutdown_called = False
        self.copy_calls: list[tuple[str, int, int, int]] = []
        self.order_send_called = False
        self.order_check_called = False

    def initialize(self) -> bool:
        return self.initialize_result

    def shutdown(self) -> None:
        self.shutdown_called = True

    def symbol_info(self, symbol: str) -> object | None:
        return self.symbol_info_result

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        return self.symbol_select_result

    def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int) -> list[dict[str, float]]:
        self.copy_calls.append((symbol, timeframe, start_pos, count))
        return self.rates_by_timeframe.get(timeframe, [])

    def order_send(self, request: object) -> None:
        self.order_send_called = True
        raise AssertionError("order_send must not be called")

    def order_check(self, request: object) -> None:
        self.order_check_called = True
        raise AssertionError("order_check must not be called")

    def last_error(self) -> tuple[int, str]:
        return (1, "fake init failure")


def _timestamp(value: datetime) -> int:
    return int(value.timestamp())


def _rates_for_timeframe(timeframe: str, *, expanded: bool) -> list[dict[str, float]]:
    step = 5 if timeframe == "M5" else 10
    start = datetime(2026, 6, 18, 0, 0, tzinfo=UTC)
    rows: list[dict[str, float]] = []
    for index in range((24 * 60) // step):
        stamp = start + timedelta(minutes=index * step)
        if stamp.hour < 6:
            candle_range = 1.0 if expanded else 5.0
        elif stamp.hour < 12:
            candle_range = 3.0 if expanded else 1.0
        elif stamp.hour < 18:
            candle_range = 4.0 if expanded else 1.0
        else:
            candle_range = 4.0 if expanded else 1.0
        open_price = 3300.0 + index * 0.01
        rows.append(
            {
                "time": _timestamp(stamp),
                "open": open_price,
                "high": open_price + candle_range,
                "low": open_price,
                "close": open_price + candle_range / 2.0,
                "tick_volume": 100.0,
                "spread": 20.0,
            }
        )
    return rows


def _fake_mt5(*, expanded: bool = False) -> FakeMt5:
    return FakeMt5(
        rates_by_timeframe={
            FakeMt5.TIMEFRAME_M5: _rates_for_timeframe("M5", expanded=expanded),
            FakeMt5.TIMEFRAME_M10: _rates_for_timeframe("M10", expanded=expanded),
        }
    )


def _qualified_order_signal() -> dict[str, object]:
    return {
        "qualified": True,
        "reason": "mocked_locked_candidate_signal_qualified_with_direction",
        "side": "long",
        "order_type": "market",
        "action": "prepare_demo_order",
        "risk_reference": "fixed_v0_40_max_trade_risk_1R",
        "stop_distance": 1.25,
        "exit_rule": "fixed_v0_26_next_block_expansion_review",
    }


def test_mocked_mt5_unavailable_blocks(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = importlib.import_module

    def fake_import(name: str, package: str | None = None) -> object:
        if name == "MetaTrader5":
            raise ImportError(name)
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    report = build_xauusd_live_signal_snapshot_v0_45(current_time=SAFE_NOW)

    assert report["snapshot_status"] == BLOCKED_MT5_UNAVAILABLE
    assert report["mt5_initialized"] is False
    assert report["mt5_shutdown_called"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False


def test_mocked_missing_symbol_blocks() -> None:
    mt5 = FakeMt5(symbol_info_result=None)

    report = build_xauusd_live_signal_snapshot_v0_45(mt5_module=mt5, current_time=SAFE_NOW)

    assert report["snapshot_status"] == BLOCKED_SYMBOL_UNAVAILABLE
    assert report["mt5_initialized"] is True
    assert report["mt5_shutdown_called"] is True
    assert mt5.shutdown_called is True
    assert report["order_send_called"] is False


def test_insufficient_candles_blocks() -> None:
    mt5 = FakeMt5(
        rates_by_timeframe={
            FakeMt5.TIMEFRAME_M5: _rates_for_timeframe("M5", expanded=False)[:10],
            FakeMt5.TIMEFRAME_M10: _rates_for_timeframe("M10", expanded=False)[:10],
        }
    )

    report = build_xauusd_live_signal_snapshot_v0_45(mt5_module=mt5, current_time=SAFE_NOW)

    assert report["snapshot_status"] == BLOCKED_INSUFFICIENT_LIVE_CANDLES
    assert report["candles_loaded_by_timeframe"] == {"M5": 10, "M10": 10}
    assert report["current_signal_snapshot_present"] is False
    assert report["order_request_present"] is False


def test_valid_no_signal_snapshot_returns_diagnostics() -> None:
    report = build_xauusd_live_signal_snapshot_v0_45(mt5_module=_fake_mt5(expanded=False), current_time=SAFE_NOW)

    assert report["snapshot_version"] == "v0_45_1"
    assert report["snapshot_status"] == SNAPSHOT_READY_NO_QUALIFIED_SIGNAL
    assert report["candidate_id"] == CANDIDATE_ID
    assert report["candidate_rules_preserved"] is True
    assert report["dry_run"] is True
    assert report["timeframes_requested"] == ["M5", "M10"]
    assert report["mt5_read_only"] is True
    assert report["candles_loaded_by_timeframe"] == {"M5": 288, "M10": 144}
    assert report["current_signal_snapshot_present"] is True
    assert report["signal_evaluated"] is True
    assert report["signal_qualified"] is False
    assert report["signal_reason"].startswith("current_snapshot_not_qualified")
    assert report["signal_diagnostics"]["by_timeframe"]["M5"]["response_expanded_reference"] is False
    assert report["order_request_present"] is False
    assert report["order_request_complete"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False


def test_mocked_qualified_snapshot_blocks_when_direction_unassigned() -> None:
    mt5 = _fake_mt5(expanded=True)

    report = build_xauusd_live_signal_snapshot_v0_45(mt5_module=mt5, current_time=SAFE_NOW)

    assert report["snapshot_status"] == SNAPSHOT_READY_SIGNAL_CONFIRMED_DIRECTION_UNASSIGNED
    assert report["signal_qualified"] is True
    assert report["signal_reason"] == "locked_candidate_current_snapshot_expansion_confirmed_across_m5_m10"
    assert report["direction_assigned"] is False
    assert report["direction_source"] == "locked_candidate_no_deterministic_direction_rule"
    assert report["executable_side_valid"] is False
    assert report["order_request_present"] is False
    assert report["order_request_complete"] is False
    assert report["order_request_validation_status"] == "direction_unassigned_non_executable"
    assert report["invalid_order_request_reasons"] == ["direction_unassigned_non_executable"]
    assert report["order_request"] is None
    assert report["review_request_present"] is True
    assert report["review_request"]["side"] == "direction_unassigned_review_only"
    assert report["review_request"]["review_only"] is True
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert mt5.order_send_called is False
    assert mt5.order_check_called is False


def test_mocked_qualified_snapshot_with_valid_internal_side_can_still_be_complete() -> None:
    mt5 = _fake_mt5(expanded=True)

    report = build_xauusd_live_signal_snapshot_v0_45(
        mt5_module=mt5,
        current_time=SAFE_NOW,
        builder_kwargs={"signal_snapshot": _qualified_order_signal()},
    )

    assert report["snapshot_status"] == SNAPSHOT_READY_ORDER_REQUEST_BUILT_DRY_RUN_ONLY
    assert report["signal_qualified"] is True
    assert report["direction_assigned"] is True
    assert report["executable_side_valid"] is True
    assert report["order_request_present"] is True
    assert report["order_request_complete"] is True
    assert report["order_request_validation_status"] == "complete"
    assert report["invalid_order_request_reasons"] == []
    assert report["order_request"]["side"] == "long"
    assert report["review_request_present"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert mt5.order_send_called is False
    assert mt5.order_check_called is False


def test_live_remains_blocked_and_candidate_rules_preserved() -> None:
    report = build_xauusd_live_signal_snapshot_v0_45(mt5_module=_fake_mt5(expanded=True), current_time=SAFE_NOW)

    assert report["live_allowed"] is False
    assert report["candidate_rules_preserved"] is True
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["repeated_oos_review"] is False
    assert report["explicit_non_actions"]["candidate_rules_changed"] is False
    assert report["explicit_non_actions"]["data_csv_added"] is False


def test_order_send_and_order_check_are_never_called() -> None:
    mt5 = _fake_mt5(expanded=True)

    report = build_xauusd_live_signal_snapshot_v0_45(mt5_module=mt5, current_time=SAFE_NOW)

    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert mt5.order_send_called is False
    assert mt5.order_check_called is False


def test_cli_returns_required_json_shape(tmp_path: Path) -> None:
    output_path = tmp_path / "xauusd_live_signal_snapshot_v0_45.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_live_signal_snapshot_v0_45.py"),
            "--symbol",
            "XAUUSD",
            "--dry-run",
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    saved_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["snapshot_version"] == "v0_45_1"
    assert saved_report["snapshot_status"] in {
        BLOCKED_MT5_UNAVAILABLE,
        BLOCKED_SYMBOL_UNAVAILABLE,
        BLOCKED_INSUFFICIENT_LIVE_CANDLES,
        SNAPSHOT_READY_NO_QUALIFIED_SIGNAL,
        SNAPSHOT_READY_ORDER_REQUEST_BUILT_DRY_RUN_ONLY,
        SNAPSHOT_READY_SIGNAL_CONFIRMED_DIRECTION_UNASSIGNED,
        "blocked_macro_event_window",
    }
    assert saved_report["order_send_called"] is False
    assert saved_report["order_check_called"] is False


def test_provider_source_does_not_call_order_apis() -> None:
    source_text = (ROOT / "src" / "execution" / "xauusd_live_signal_snapshot_provider.py").read_text(encoding="utf-8")
    forbidden_terms = ["order" + "_send(", "order" + "_check("]

    assert all(term not in source_text for term in forbidden_terms)
