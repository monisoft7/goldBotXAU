from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.xauusd_oil_proxy_context_audit import (
    AUDIT_VERSION,
    BLOCKED_MISSING_DATA,
    COMPLETED,
    DEFAULT_CANDIDATE_SYMBOLS,
    NEXT_IF_NO_USABLE,
    NEXT_IF_USABLE,
    NO_USABLE_PROXY,
    assert_no_future_proxy_bars,
    build_xauusd_oil_proxy_context_audit_v0_69,
    safe_backward_asof_alignment_pairs,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeSymbol:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeMt5:
    TIMEFRAME_M5 = "M5"
    TIMEFRAME_M10 = "M10"
    TIMEFRAME_M15 = "M15"

    def __init__(self, *, names: list[str] | None = None, rows: dict[tuple[str, str], list[dict[str, object]]] | None = None):
        self.names = names or []
        self.rows = rows or {}
        self.initialize_called = False
        self.shutdown_called = False
        self.order_send_called = False
        self.order_check_called = False

    def initialize(self) -> bool:
        self.initialize_called = True
        return True

    def shutdown(self) -> None:
        self.shutdown_called = True

    def symbols_get(self) -> list[FakeSymbol]:
        return [FakeSymbol(name) for name in self.names]

    def copy_rates_from_pos(self, symbol: str, timeframe: str, start_pos: int, count: int) -> list[dict[str, object]]:
        assert start_pos == 0
        assert count == 5000
        return self.rows.get((symbol, timeframe), [])

    def order_send(self, *_args: object, **_kwargs: object) -> None:
        self.order_send_called = True

    def order_check(self, *_args: object, **_kwargs: object) -> None:
        self.order_check_called = True


def _epoch(text: str) -> int:
    return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp())


def _bar(text: str, *, open_value: float = 80.0, high: float = 81.0, low: float = 79.0, close: float = 80.5) -> dict[str, object]:
    return {"time": _epoch(text), "open": open_value, "high": high, "low": low, "close": close}


def _write_csv(path: Path, timestamps: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = ["timestamp,open,high,low,close,volume"]
    for index, timestamp in enumerate(timestamps, start=1):
        rows.append(f"{timestamp},{index},{index + 1},{index - 0.5},{index + 0.5},1")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_missing_xauusd_data_is_blocked_safely(tmp_path: Path) -> None:
    report = build_xauusd_oil_proxy_context_audit_v0_69(root=tmp_path, mt5_module=FakeMt5())

    assert report["audit_version"] == AUDIT_VERSION
    assert report["audit_status"] == BLOCKED_MISSING_DATA
    assert "missing_local_xauusd_csv_data" in report["blockers"]
    assert report["safe_asof_alignment_feasible"] is False
    assert report["approved_for_strategy_testing"] is False
    assert report["recommended_next_step"] == NEXT_IF_NO_USABLE


def test_missing_oil_symbols_fail_safely(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "data" / "xauusd_m15_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:15:00"],
    )

    report = build_xauusd_oil_proxy_context_audit_v0_69(root=tmp_path, mt5_module=FakeMt5(names=["OTHER"]))

    assert report["audit_status"] == NO_USABLE_PROXY
    assert report["candidate_symbols_checked"] == DEFAULT_CANDIDATE_SYMBOLS
    assert report["usable_proxy_symbols"] == []
    assert report["selected_proxy_symbol_or_null"] is None
    assert report["rejected_proxy_symbols"]["UKOIL"]["reasons_by_timeframe"]["M15"] == "oil_proxy_symbol_or_timeframe_not_available"
    assert report["recommended_next_step"] == NEXT_IF_NO_USABLE


def test_invalid_ohlc_rows_are_rejected(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "data" / "xauusd_m15_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:15:00"],
    )
    mt5 = FakeMt5(
        names=["UKOIL"],
        rows={("UKOIL", "M15"): [_bar("2026-01-01T00:00:00", high=79.0, low=78.0)]},
    )

    report = build_xauusd_oil_proxy_context_audit_v0_69(root=tmp_path, mt5_module=mt5)
    detail = report["symbol_timeframe_audits"]["UKOIL"]["M15"]

    assert report["audit_status"] == NO_USABLE_PROXY
    assert detail["copied_row_count"] == 1
    assert detail["parseable_row_count"] == 0
    assert detail["invalid_ohlc_count"] == 1
    assert detail["reason_if_rejected"] == "no_parseable_oil_proxy_rows"


def test_usable_proxy_prefers_m15_then_remains_feasibility_only(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "data" / "xauusd_m15_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:15:00", "2026-01-01T00:30:00"],
    )
    mt5 = FakeMt5(
        names=["UKOIL"],
        rows={
            ("UKOIL", "M15"): [
                _bar("2026-01-01T00:00:00"),
                _bar("2026-01-01T00:15:00"),
                _bar("2026-01-01T00:30:00"),
            ]
        },
    )

    report = build_xauusd_oil_proxy_context_audit_v0_69(root=tmp_path, mt5_module=mt5)

    assert report["audit_status"] == COMPLETED
    assert report["selected_proxy_symbol_or_null"] == "UKOIL"
    assert report["selected_proxy_timeframe_or_null"] == "M15"
    assert report["safe_asof_alignment_feasible"] is True
    assert report["lookahead_risk_detected"] is False
    assert report["future_label_candidates"] == [
        "oil_strength",
        "oil_weakness",
        "oil_shock_up",
        "oil_shock_down",
        "gold_oil_inflation_pressure_aligned",
        "gold_oil_safe_haven_conflict",
        "oil_supply_shock_context_candidate",
    ]
    assert report["labels_used_as_trade_blockers"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["trade_signals_output"] is False
    assert report["recommended_next_step"] == NEXT_IF_USABLE
    assert mt5.order_send_called is False
    assert mt5.order_check_called is False


def test_safe_asof_alignment_never_uses_future_proxy_bars() -> None:
    pairs = safe_backward_asof_alignment_pairs(
        ["2026-01-01T00:07:00", "2026-01-01T00:16:00"],
        ["2026-01-01T00:00:00", "2026-01-01T00:15:00", "2026-01-01T00:30:00"],
    )

    assert pairs == [
        {"xauusd_timestamp": "2026-01-01T00:07:00", "proxy_timestamp": "2026-01-01T00:00:00"},
        {"xauusd_timestamp": "2026-01-01T00:16:00", "proxy_timestamp": "2026-01-01T00:15:00"},
    ]
    with pytest.raises(ValueError, match="future oil proxy bar"):
        assert_no_future_proxy_bars(
            [{"xauusd_timestamp": "2026-01-01T00:07:00", "proxy_timestamp": "2026-01-01T00:15:00"}]
        )


def test_report_includes_required_diagnostic_and_safety_fields(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "data" / "xauusd_m15_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:15:00"],
    )
    report = build_xauusd_oil_proxy_context_audit_v0_69(root=tmp_path, mt5_module=FakeMt5())

    for key in (
        "candidate_symbols_checked",
        "usable_proxy_symbols",
        "rejected_proxy_symbols",
        "selected_proxy_symbol_or_null",
        "xauusd_timeframes_available",
        "proxy_timeframes_available",
        "overlap_summary",
        "gap_summary",
        "safe_asof_alignment_feasible",
        "future_label_candidates",
    ):
        assert key in report
    for key in (
        "approved_for_strategy_testing",
        "approved_for_trade_filtering",
        "labels_used_as_trade_blockers",
        "oos_used",
        "repeated_oos_review",
        "retune_performed",
        "threshold_search_performed",
        "parameter_grid_performed",
        "executable_candidate_created",
        "demo_execution_allowed",
        "order_send_called",
        "order_check_called",
        "live_allowed",
        "trade_recommendation_output",
        "aligned_dataset_created",
        "data_csv_touched",
    ):
        assert report[key] is False
        assert report["safety"][key] is False
    assert report["train_validation_only"] is True


def test_no_persistent_csv_is_created_and_data_csv_status_is_clean(tmp_path: Path) -> None:
    report = build_xauusd_oil_proxy_context_audit_v0_69(root=tmp_path, mt5_module=FakeMt5())

    assert list(tmp_path.rglob("*.csv")) == []
    assert report["aligned_dataset_created"] is False
    assert report["data_csv_touched"] is False

    completed = subprocess.run(
        ["git", "status", "--short", "--", "data/*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == ""


def test_cli_writes_required_report(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "data" / "xauusd_m15_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:15:00"],
    )
    output = tmp_path / "reports" / "audit.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_oil_proxy_context_audit_v0_69.py"),
            "--json",
            "--root",
            str(tmp_path),
            "--output",
            str(output),
            "--skip-mt5-readonly-discovery",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["audit_version"] == AUDIT_VERSION
    assert output_report["audit_status"] == NO_USABLE_PROXY
    assert output_report["oos_used"] is False
