from __future__ import annotations

import copy
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from src.execution.xauusd_limited_demo_executor import (
    BLOCKED_INVALID_LOT,
    BLOCKED_INVALID_SYMBOL,
    BLOCKED_MACRO_EVENT_WINDOW,
    BLOCKED_MISSING_COMPLETE_ORDER_REQUEST,
    BLOCKED_MISSING_APPROVAL_TOKEN,
    BLOCKED_NOT_DEMO_ACCOUNT,
    BLOCKED_READINESS_GATE_MISSING_OR_FAILED,
    DRY_RUN_READY_NO_ORDER_SENT,
    REQUIRED_APPROVAL_TOKEN,
    build_xauusd_limited_demo_execution_v0_42,
)

ROOT = Path(__file__).resolve().parents[1]
SAFE_NOW = datetime(2026, 6, 17, 18, 0, tzinfo=ZoneInfo("Africa/Tripoli"))
MACRO_NOW = datetime(2026, 6, 17, 20, 0, tzinfo=ZoneInfo("Africa/Tripoli"))


class MockMT5:
    def __init__(self, *, server: str = "MetaQuotes-Demo", trade_mode: int = 0) -> None:
        self.account = SimpleNamespace(server=server, trade_mode=trade_mode, currency="USD")
        self.order_send_calls: list[dict[str, object] | None] = []
        self.order_check_calls: list[dict[str, object] | None] = []

    def account_info(self) -> SimpleNamespace:
        return self.account

    def order_send(self, request: dict[str, object] | None) -> dict[str, object]:
        self.order_send_calls.append(request)
        return {"retcode": 10009, "comment": "mocked"}

    def order_check(self, request: dict[str, object] | None) -> dict[str, object]:
        self.order_check_calls.append(request)
        return {"retcode": 0}


def _valid_reports() -> dict[str, dict[str, object]]:
    return {
        "readiness": {
            "gate_version": "v0_41",
            "decision": "final_demo_readiness_gate_passed_pending_human_authorization",
            "candidate_id": "xauusd_compression_then_expansion_v0_26",
            "candidate_rules_preserved": True,
            "human_authorization_required": True,
        },
        "risk": {
            "envelope_version": "v0_40",
            "decision": "demo_risk_envelope_design_ready",
            "candidate_id": "xauusd_compression_then_expansion_v0_26",
            "candidate_rules_preserved": True,
            "order_send_allowed": False,
            "order_check_allowed": False,
            "fixed_risk_envelope": {
                "starting_demo_lot": 0.01,
                "max_demo_lot": 0.01,
                "max_positions": 1,
                "no_martingale": True,
                "no_averaging_into_loss": True,
                "no_position_scaling": True,
            },
        },
        "broker": {
            "audit_version": "v0_39",
            "decision": "broker_facts_audit_ready_for_risk_envelope_design",
            "candidate_id": "xauusd_compression_then_expansion_v0_26",
            "candidate_rules_preserved": True,
            "broker_facts": {"account": {"server": "MetaQuotes-Demo", "trade_mode": 0, "currency": "USD"}},
        },
    }


def _write_reports(tmp_path: Path, reports: dict[str, dict[str, object]]) -> dict[str, Path]:
    paths = {
        "readiness": tmp_path / "reports" / "readiness.json",
        "risk": tmp_path / "reports" / "risk.json",
        "broker": tmp_path / "reports" / "broker.json",
    }
    for key, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(reports[key]), encoding="utf-8")
    return paths


def _build(
    tmp_path: Path,
    *,
    reports: dict[str, dict[str, object]] | None = None,
    mt5: MockMT5 | None = None,
    **kwargs: object,
) -> dict[str, object]:
    paths = _write_reports(tmp_path, reports or _valid_reports())
    return build_xauusd_limited_demo_execution_v0_42(
        readiness_gate_report_path=paths["readiness"],
        risk_envelope_report_path=paths["risk"],
        broker_facts_report_path=paths["broker"],
        mt5_client=mt5,
        current_time=SAFE_NOW,
        **kwargs,
    )


def test_default_dry_run_does_not_call_order_send(tmp_path: Path) -> None:
    mt5 = MockMT5()

    report = _build(tmp_path, mt5=mt5)

    assert report["executor_version"] == "v0_42"
    assert report["executor_status"] == DRY_RUN_READY_NO_ORDER_SENT
    assert report["dry_run"] is True
    assert report["order_send_attempted"] is False
    assert report["order_send_called"] is False
    assert report["order_request_present"] is False
    assert report["order_request_complete"] is False
    assert report["order_request_validation_status"] == "missing_order_request"
    assert mt5.order_send_calls == []


def test_live_account_blocks(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=MockMT5(server="Broker-Live", trade_mode=2))

    assert report["executor_status"] == BLOCKED_NOT_DEMO_ACCOUNT
    assert report["demo_account_verified"] is False
    assert report["live_allowed"] is False
    assert report["order_send_called"] is False


def test_non_demo_server_blocks(tmp_path: Path) -> None:
    report = _build(tmp_path, mt5=MockMT5(server="Broker-Contest", trade_mode=1))

    assert report["executor_status"] == BLOCKED_NOT_DEMO_ACCOUNT
    assert "account_not_verified_as_demo" in report["blockers"]
    assert report["order_send_called"] is False


def test_invalid_symbol_blocks(tmp_path: Path) -> None:
    report = _build(tmp_path, symbol="EURUSD")

    assert report["executor_status"] == BLOCKED_INVALID_SYMBOL
    assert report["symbol_verified"] is False
    assert report["order_send_called"] is False


def test_lot_above_point_zero_one_blocks(tmp_path: Path) -> None:
    report = _build(tmp_path, lot=0.02)

    assert report["executor_status"] == BLOCKED_INVALID_LOT
    assert report["lot_verified"] is False
    assert report["order_send_called"] is False


def test_missing_approval_token_blocks_when_allow_order_send_is_used(tmp_path: Path) -> None:
    mt5 = MockMT5()

    report = _build(tmp_path, mt5=mt5, dry_run=False, allow_demo_order_send=True)

    assert report["executor_status"] == BLOCKED_MISSING_APPROVAL_TOKEN
    assert report["approval_token_required"] is True
    assert report["approval_token_valid"] is False
    assert report["order_send_called"] is False
    assert mt5.order_send_calls == []


def test_explicit_send_with_valid_token_blocks_without_order_request(tmp_path: Path) -> None:
    mt5 = MockMT5()

    report = _build(
        tmp_path,
        mt5=mt5,
        dry_run=False,
        allow_demo_order_send=True,
        approval_token=REQUIRED_APPROVAL_TOKEN,
    )

    assert report["executor_status"] == BLOCKED_MISSING_COMPLETE_ORDER_REQUEST
    assert report["order_request_present"] is False
    assert report["order_request_complete"] is False
    assert report["order_request_validation_status"] == "missing_order_request"
    assert "order_request" in report["order_request_missing_fields"]
    assert "order_request_missing_complete_fields" in report["blockers"]
    assert report["order_send_attempted"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert mt5.order_send_calls == []
    assert mt5.order_check_calls == []


def test_explicit_send_with_missing_side_type_action_blocks_as_incomplete(tmp_path: Path) -> None:
    mt5 = MockMT5()

    report = _build(
        tmp_path,
        mt5=mt5,
        dry_run=False,
        allow_demo_order_send=True,
        approval_token=REQUIRED_APPROVAL_TOKEN,
        order_request={"symbol": "XAUUSD", "lot": 0.01, "demo_only": True},
    )

    assert report["executor_status"] == BLOCKED_MISSING_COMPLETE_ORDER_REQUEST
    assert report["order_request_present"] is True
    assert report["order_request_complete"] is False
    assert report["order_request_validation_status"] == "direction_unassigned_non_executable"
    assert report["invalid_order_request_reasons"] == ["direction_unassigned_non_executable"]
    assert report["order_request_missing_fields"] == ["side", "order_type", "action"]
    assert report["order_send_attempted"] is False
    assert report["order_send_called"] is False
    assert mt5.order_send_calls == []


def test_direction_unassigned_review_only_order_request_blocks_as_non_executable(tmp_path: Path) -> None:
    mt5 = MockMT5()

    report = _build(
        tmp_path,
        mt5=mt5,
        dry_run=False,
        allow_demo_order_send=True,
        approval_token=REQUIRED_APPROVAL_TOKEN,
        order_request={
            "symbol": "XAUUSD",
            "lot": 0.01,
            "demo_only": True,
            "side": "direction_unassigned_review_only",
            "order_type": "market",
            "action": "prepare_demo_order",
        },
    )

    assert report["executor_status"] == BLOCKED_MISSING_COMPLETE_ORDER_REQUEST
    assert report["direction_assigned"] is False
    assert report["executable_side_valid"] is False
    assert report["order_request_present"] is True
    assert report["order_request_complete"] is False
    assert report["order_request_validation_status"] == "direction_unassigned_non_executable"
    assert report["invalid_order_request_reasons"] == ["direction_unassigned_non_executable"]
    assert "side" in report["order_request_missing_fields"]
    assert report["order_send_attempted"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert mt5.order_send_calls == []
    assert mt5.order_check_calls == []


def test_valid_internal_side_order_request_can_be_complete_without_sending(tmp_path: Path) -> None:
    mt5 = MockMT5()

    report = _build(
        tmp_path,
        mt5=mt5,
        order_request={
            "symbol": "XAUUSD",
            "lot": 0.01,
            "demo_only": True,
            "side": "long",
            "order_type": "market",
            "action": "prepare_demo_order",
        },
    )

    assert report["executor_status"] == DRY_RUN_READY_NO_ORDER_SENT
    assert report["direction_assigned"] is True
    assert report["executable_side_valid"] is True
    assert report["order_request_present"] is True
    assert report["order_request_complete"] is True
    assert report["order_request_validation_status"] == "complete"
    assert report["invalid_order_request_reasons"] == []
    assert report["order_send_attempted"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert mt5.order_send_calls == []
    assert mt5.order_check_calls == []


def test_macro_event_window_blocks_order_send(tmp_path: Path) -> None:
    mt5 = MockMT5()
    paths = _write_reports(tmp_path, _valid_reports())

    report = build_xauusd_limited_demo_execution_v0_42(
        readiness_gate_report_path=paths["readiness"],
        risk_envelope_report_path=paths["risk"],
        broker_facts_report_path=paths["broker"],
        mt5_client=mt5,
        current_time=MACRO_NOW,
        dry_run=False,
        allow_demo_order_send=True,
        approval_token=REQUIRED_APPROVAL_TOKEN,
        order_request={"symbol": "XAUUSD", "volume": 0.01},
    )

    assert report["executor_status"] == BLOCKED_MACRO_EVENT_WINDOW
    assert report["macro_event_lock_status"] == BLOCKED_MACRO_EVENT_WINDOW
    assert report["macro_event_window_used"]["event_id"] == "fomc_fed_chair_2026_06_17_default_libya_time"
    assert report["order_send_called"] is False
    assert mt5.order_send_calls == []


def test_valid_dry_run_returns_ready_no_order_sent(tmp_path: Path) -> None:
    report = _build(tmp_path)

    assert report["executor_status"] == DRY_RUN_READY_NO_ORDER_SENT
    assert report["macro_event_lock_status"] == "clear_static_manual_windows"
    assert report["demo_account_verified"] is True
    assert report["readiness_gate_verified"] is True
    assert report["risk_envelope_verified"] is True


def test_v0_41_missing_or_failed_blocks(tmp_path: Path) -> None:
    reports = _valid_reports()
    reports["readiness"] = copy.deepcopy(reports["readiness"])
    reports["readiness"]["decision"] = "blocked_missing_required_report"

    report = _build(tmp_path, reports=reports)

    assert report["executor_status"] == BLOCKED_READINESS_GATE_MISSING_OR_FAILED
    assert report["readiness_gate_verified"] is False
    assert report["order_send_called"] is False


def test_no_order_check_is_called(tmp_path: Path) -> None:
    mt5 = MockMT5()

    report = _build(
        tmp_path,
        mt5=mt5,
        dry_run=False,
        allow_demo_order_send=True,
        approval_token=REQUIRED_APPROVAL_TOKEN,
    )

    assert report["order_check_called"] is False
    assert mt5.order_check_calls == []


def test_no_retune_threshold_search_parameter_grid_or_repeated_oos(tmp_path: Path) -> None:
    report = _build(tmp_path)

    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["repeated_oos_review"] is False
    assert report["explicit_non_actions"]["candidate_rules_changed"] is False
    assert report["explicit_non_actions"]["oos_review_repeated"] is False


def test_candidate_remains_locked_v0_26(tmp_path: Path) -> None:
    report = _build(tmp_path)

    assert report["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert report["candidate_rules_preserved"] is True
    assert report["execution_intent"]["candidate_id"] == "xauusd_compression_then_expansion_v0_26"


def test_cli_builds_default_report_without_order(tmp_path: Path) -> None:
    output_path = tmp_path / "xauusd_limited_demo_execution_v0_42.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_limited_demo_execution_v0_42.py"),
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
    output_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["executor_version"] == "v0_42"
    assert output_report["order_send_called"] is False
    assert output_report["order_check_called"] is False


def test_report_does_not_emit_directional_or_recommendation_output(tmp_path: Path) -> None:
    report_text = json.dumps(_build(tmp_path))
    source_text = (ROOT / "src" / "execution" / "xauusd_limited_demo_executor.py").read_text(encoding="utf-8")

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text
    assert "trade recommendation" not in report_text.lower()
    assert "trade recommendation" not in source_text.lower()
