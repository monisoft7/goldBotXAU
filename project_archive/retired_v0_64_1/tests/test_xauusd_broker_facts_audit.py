from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.research.xauusd_broker_facts_audit import (
    BLOCKED_MISSING_CRITICAL_BROKER_FACTS,
    BLOCKED_MT5_UNAVAILABLE,
    BLOCKED_SYMBOL_UNAVAILABLE,
    BROKER_FACTS_AUDIT_READY_FOR_RISK_ENVELOPE_DESIGN,
    build_xauusd_broker_facts_audit_v0_39,
)

ROOT = Path(__file__).resolve().parents[1]
_DEFAULT = object()


class FakeMt5:
    def __init__(
        self,
        *,
        initialize_result: bool = True,
        symbol_info_result: object | None = _DEFAULT,
        account_info_result: object | None = _DEFAULT,
    ) -> None:
        self.initialize_result = initialize_result
        self.symbol_info_result = _valid_symbol_info() if symbol_info_result is _DEFAULT else symbol_info_result
        self.account_info_result = _valid_account_info() if account_info_result is _DEFAULT else account_info_result
        self.shutdown_called = False
        self.symbol_info_calls: list[str] = []
        self.account_info_called = False

    def __getattribute__(self, name: str) -> Any:
        if name in {"order_send", "order_check"}:
            raise AssertionError(f"forbidden MT5 attribute accessed: {name}")
        return object.__getattribute__(self, name)

    def initialize(self) -> bool:
        return self.initialize_result

    def shutdown(self) -> None:
        self.shutdown_called = True

    def symbol_info(self, symbol: str) -> object | None:
        self.symbol_info_calls.append(symbol)
        return self.symbol_info_result

    def account_info(self) -> object | None:
        self.account_info_called = True
        return self.account_info_result

    def last_error(self) -> tuple[int, str]:
        return (1, "fake init failure")


def _valid_symbol_info(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "digits": 2,
        "point": 0.01,
        "trade_contract_size": 100.0,
        "trade_tick_size": 0.01,
        "trade_tick_value": 1.0,
        "volume_min": 0.01,
        "volume_max": 50.0,
        "volume_step": 0.01,
        "spread": 25,
        "spread_float": True,
        "trade_mode": 4,
        "trade_exemode": 2,
        "filling_mode": 3,
        "order_mode": 127,
        "trade_stops_level": 50,
        "trade_freeze_level": 0,
        "swap_long": -20.0,
        "swap_short": 10.0,
        "visible": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _valid_account_info(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "server": "Demo-Server",
        "currency": "USD",
        "trade_mode": 0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_valid_mocked_broker_facts_pass() -> None:
    mt5 = FakeMt5()

    report = build_xauusd_broker_facts_audit_v0_39(symbol="XAUUSD", mt5_module=mt5)

    assert report["audit_version"] == "v0_39"
    assert report["audit_status"] == "completed"
    assert report["decision"] == BROKER_FACTS_AUDIT_READY_FOR_RISK_ENVELOPE_DESIGN
    assert report["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert report["candidate_rules_preserved"] is True
    assert report["design_or_read_only"] is True
    assert report["mt5_read_only_metadata_access"] is True
    assert report["mt5_initialized"] is True
    assert report["mt5_shutdown_called"] is True
    assert report["missing_facts"] == []
    assert report["broker_fact_blockers"] == []
    assert report["broker_facts"]["symbol"]["exists"] is True
    assert report["broker_facts"]["symbol"]["digits"] == 2
    assert report["broker_facts"]["account"]["server"] == "Demo-Server"
    assert mt5.shutdown_called is True
    assert mt5.symbol_info_calls == ["XAUUSD"]
    assert mt5.account_info_called is True


def test_missing_critical_facts_block() -> None:
    mt5 = FakeMt5(symbol_info_result=_valid_symbol_info(trade_tick_value=None))

    report = build_xauusd_broker_facts_audit_v0_39(symbol="XAUUSD", mt5_module=mt5)

    assert report["audit_status"] == "blocked"
    assert report["decision"] == BLOCKED_MISSING_CRITICAL_BROKER_FACTS
    assert "symbol.trade_tick_value" in report["missing_facts"]
    assert "missing_critical_fact: symbol.trade_tick_value" in report["broker_fact_blockers"]
    assert report["mt5_shutdown_called"] is True


def test_symbol_unavailable_blocks() -> None:
    mt5 = FakeMt5(symbol_info_result=None)

    report = build_xauusd_broker_facts_audit_v0_39(symbol="XAUUSD", mt5_module=mt5)

    assert report["audit_status"] == "blocked"
    assert report["decision"] == BLOCKED_SYMBOL_UNAVAILABLE
    assert report["broker_facts"]["symbol"]["exists"] is False
    assert "symbol_unavailable: XAUUSD" in report["broker_fact_blockers"]
    assert report["mt5_shutdown_called"] is True


def test_missing_metatrader5_package_blocks_without_real_mt5(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = importlib.import_module

    def fake_import(name: str, package: str | None = None) -> object:
        if name == "MetaTrader5":
            raise ImportError(name)
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    report = build_xauusd_broker_facts_audit_v0_39(symbol="XAUUSD")

    assert report["audit_status"] == "blocked"
    assert report["decision"] == BLOCKED_MT5_UNAVAILABLE
    assert report["mt5_initialized"] is False
    assert report["mt5_shutdown_called"] is False
    assert "metatrader5_package_unavailable" in report["broker_fact_blockers"]


def test_execution_remains_disabled() -> None:
    report = build_xauusd_broker_facts_audit_v0_39(symbol="XAUUSD", mt5_module=FakeMt5())

    for key in (
        "order_send_created",
        "order_send_called",
        "order_check_created",
        "order_check_called",
        "execution_queue_created",
        "broker_execution_path_created",
        "buy_sell_output_allowed",
        "trade_recommendation_output_allowed",
        "retune_performed",
        "threshold_search_performed",
        "parameter_grid_performed",
        "repeated_oos_review",
    ):
        assert report[key] is False


def test_no_order_functions_are_accessed() -> None:
    mt5 = FakeMt5()

    report = build_xauusd_broker_facts_audit_v0_39(symbol="XAUUSD", mt5_module=mt5)

    assert report["decision"] == BROKER_FACTS_AUDIT_READY_FOR_RISK_ENVELOPE_DESIGN
    assert mt5.shutdown_called is True


def test_source_does_not_call_or_create_execution_paths() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_broker_facts_audit.py",
            ROOT / "scripts" / "build_xauusd_broker_facts_audit_v0_39.py",
        ]
    ).lower()

    assert ".order" + "_send" not in source_text
    assert ".order" + "_check" not in source_text
    assert "trade_request" not in source_text
    assert "request =" not in source_text
    assert "executionqueue" not in source_text
    assert "copy_rates" not in source_text
    assert "symbol_select" not in source_text


def test_report_does_not_emit_directional_or_recommendation_output() -> None:
    report_text = json.dumps(build_xauusd_broker_facts_audit_v0_39(symbol="XAUUSD", mt5_module=FakeMt5()))
    source_text = (ROOT / "src" / "research" / "xauusd_broker_facts_audit.py").read_text(encoding="utf-8")

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text
    assert "trade recommendation" not in report_text.lower()
    assert "trade recommendation" not in source_text.lower()


def test_cli_builds_v0_39_report(tmp_path: Path) -> None:
    output_path = tmp_path / "xauusd_broker_facts_audit_v0_39.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_broker_facts_audit_v0_39.py"),
            "--symbol",
            "XAUUSD",
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
    output_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["audit_version"] == "v0_39"
    assert output_report["audit_version"] == "v0_39"
    assert output_report["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
