from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.research.xauusd_dxy_proxy_context_audit import (
    AUDIT_VERSION,
    BLOCKED_MISSING_DATA,
    COMPLETED,
    DEFAULT_CANDIDATE_SYMBOLS,
    NO_USABLE_PROXY,
    assert_safe_asof_join_direction,
    build_xauusd_dxy_proxy_context_audit_v0_65,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeSymbol:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeMt5:
    TIMEFRAME_M5 = "M5"
    TIMEFRAME_M15 = "M15"

    def __init__(self, *, names: list[str] | None = None, rows: dict[tuple[str, str], list[dict[str, int]]] | None = None):
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

    def copy_rates_from_pos(self, symbol: str, timeframe: str, start_pos: int, count: int) -> list[dict[str, int]]:
        assert start_pos == 0
        assert count == 5000
        return self.rows.get((symbol, timeframe), [])

    def order_send(self, *_args: object, **_kwargs: object) -> None:
        self.order_send_called = True

    def order_check(self, *_args: object, **_kwargs: object) -> None:
        self.order_check_called = True


def _epoch(text: str) -> int:
    return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp())


def _write_csv(path: Path, timestamps: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = ["timestamp,open,high,low,close,volume"]
    for index, timestamp in enumerate(timestamps, start=1):
        rows.append(f"{timestamp},{index},{index},{index},{index},1")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_missing_xauusd_data_is_blocked_safely(tmp_path: Path) -> None:
    report = build_xauusd_dxy_proxy_context_audit_v0_65(
        root=tmp_path,
        mt5_module=FakeMt5(),
    )

    assert report["audit_version"] == AUDIT_VERSION
    assert report["audit_status"] == BLOCKED_MISSING_DATA
    assert "missing_local_xauusd_csv_data" in report["blockers"]
    assert report["safe_asof_alignment_feasible"] is False
    assert report["approved_for_strategy_testing"] is False


def test_missing_proxy_data_is_reported_without_strategy_logic(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "data" / "xauusd_m5_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:05:00", "2026-01-01T00:10:00"],
    )

    report = build_xauusd_dxy_proxy_context_audit_v0_65(
        root=tmp_path,
        mt5_module=FakeMt5(),
    )

    assert report["audit_status"] == NO_USABLE_PROXY
    assert report["candidate_symbols_checked"] == DEFAULT_CANDIDATE_SYMBOLS
    assert report["usable_proxy_symbols"] == []
    assert report["selected_proxy_symbol_or_null"] is None
    assert report["strategy_rules_created"] is False
    assert report["trade_signals_output"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["recommended_next_step"] == "v0_66_dxy_asof_alignment_if_proxy_feasible"


def test_invalid_symbols_are_rejected_safely(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "data" / "xauusd_m15_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:15:00"],
    )

    report = build_xauusd_dxy_proxy_context_audit_v0_65(
        root=tmp_path,
        candidate_symbols=["NOT_DXY"],
        mt5_module=FakeMt5(names=["OTHER"]),
    )

    assert report["audit_status"] == NO_USABLE_PROXY
    assert report["candidate_symbols_checked"] == ["NOT_DXY"]
    assert report["rejected_proxy_symbols"]["NOT_DXY"]["status"] == "rejected_no_safe_overlap"
    assert "no_local_or_mt5_readonly_rows_for_candidate_symbol" in report["rejected_proxy_symbols"]["NOT_DXY"]["reasons"]
    assert report["executable_candidate_created"] is False


def test_usable_proxy_reports_feasibility_only_from_local_csv(tmp_path: Path) -> None:
    timestamps = ["2026-01-01T00:00:00", "2026-01-01T00:05:00", "2026-01-01T00:10:00"]
    _write_csv(tmp_path / "data" / "xauusd_m5_xauusd_2026-01-01_2026-01-01.csv", timestamps)
    _write_csv(tmp_path / "data" / "usdx_m5_usdx_2026-01-01_2026-01-01.csv", timestamps)

    report = build_xauusd_dxy_proxy_context_audit_v0_65(
        root=tmp_path,
        mt5_module=FakeMt5(),
    )

    assert report["audit_status"] == COMPLETED
    assert report["usable_proxy_symbols"] == ["USDX"]
    assert report["selected_proxy_symbol_or_null"] == "USDX"
    assert report["safe_asof_alignment_feasible"] is True
    assert report["lookahead_risk_detected"] is False
    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["future_label_candidates"] == [
        "dollar_strength",
        "dollar_weakness",
        "dollar_shock",
        "gold_dxy_decoupling",
        "dxy_trend_aligned",
        "dxy_trend_conflict",
    ]


def test_mt5_readonly_proxy_rows_are_audited_without_order_calls(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "data" / "xauusd_m15_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:15:00"],
    )
    mt5 = FakeMt5(
        names=["DXYN"],
        rows={
            ("DXYN", "M15"): [
                {"time": _epoch("2026-01-01T00:00:00")},
                {"time": _epoch("2026-01-01T00:15:00")},
            ]
        },
    )

    report = build_xauusd_dxy_proxy_context_audit_v0_65(root=tmp_path, mt5_module=mt5)

    assert report["audit_status"] == COMPLETED
    assert report["usable_proxy_symbols"] == ["DXYN"]
    assert report["mt5_readonly_discovery"]["status"] == "readonly_discovery_completed"
    assert report["mt5_readonly_discovery"]["order_send_called"] is False
    assert report["mt5_readonly_discovery"]["order_check_called"] is False
    assert mt5.order_send_called is False
    assert mt5.order_check_called is False


def test_lookahead_alignment_is_not_allowed() -> None:
    assert_safe_asof_join_direction("backward")
    with pytest.raises(ValueError, match="only backward/as-of joins"):
        assert_safe_asof_join_direction("forward")


def test_report_includes_all_required_safety_flags(tmp_path: Path) -> None:
    _write_csv(
        tmp_path / "data" / "xauusd_m5_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:05:00"],
    )
    report = build_xauusd_dxy_proxy_context_audit_v0_65(root=tmp_path, mt5_module=FakeMt5())

    for key in (
        "approved_for_strategy_testing",
        "approved_for_trade_filtering",
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
    ):
        assert report[key] is False
        assert report["safety"][key] is False
    assert report["train_validation_only"] is True
    assert report["safety"]["train_validation_only"] is True


def test_data_csv_not_staged_or_committed() -> None:
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
        tmp_path / "data" / "xauusd_m5_xauusd_2026-01-01_2026-01-01.csv",
        ["2026-01-01T00:00:00", "2026-01-01T00:05:00"],
    )
    output = tmp_path / "reports" / "audit.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_dxy_proxy_context_audit_v0_65.py"),
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
