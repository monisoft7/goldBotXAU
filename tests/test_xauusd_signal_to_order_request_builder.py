from __future__ import annotations

import copy
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.execution.xauusd_signal_to_order_request_builder import (
    BLOCKED_CANDIDATE_SIGNAL_UNAVAILABLE,
    BLOCKED_INCOMPLETE_ORDER_REQUEST,
    BLOCKED_MACRO_EVENT_WINDOW,
    NO_QUALIFIED_SIGNAL_NOW,
    ORDER_REQUEST_BUILT_DRY_RUN_ONLY,
    build_xauusd_signal_order_request_v0_43,
)

ROOT = Path(__file__).resolve().parents[1]
SAFE_NOW = datetime(2026, 6, 17, 18, 0, tzinfo=ZoneInfo("Africa/Tripoli"))
MACRO_NOW = datetime(2026, 6, 17, 20, 0, tzinfo=ZoneInfo("Africa/Tripoli"))
CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"


def _valid_reports() -> dict[str, dict[str, object]]:
    return {
        "candidate": {
            "report_version": "v0_26",
            "candidate_id": CANDIDATE_ID,
            "status": "train_validation_research_candidate_only",
            "source_family": "compression_then_expansion",
            "threshold_search_used": False,
            "parameter_grid_used": False,
            "candidate": {
                "candidate_id": CANDIDATE_ID,
                "rules_are_fixed_from_atlas_family": True,
            },
        },
        "readiness": {
            "gate_version": "v0_41",
            "decision": "final_demo_readiness_gate_passed_pending_human_authorization",
            "candidate_id": CANDIDATE_ID,
            "candidate_rules_preserved": True,
        },
        "risk": {
            "envelope_version": "v0_40",
            "decision": "demo_risk_envelope_design_ready",
            "candidate_id": CANDIDATE_ID,
            "candidate_rules_preserved": True,
            "fixed_risk_envelope": {
                "starting_demo_lot": 0.01,
                "max_demo_lot": 0.01,
                "max_positions": 1,
            },
        },
        "executor": {
            "executor_version": "v0_42",
            "executor_status": "dry_run_ready_no_order_sent",
            "candidate_id": CANDIDATE_ID,
            "candidate_rules_preserved": True,
            "order_send_called": False,
            "order_check_called": False,
        },
    }


def _write_reports(tmp_path: Path, reports: dict[str, dict[str, object]]) -> dict[str, Path]:
    paths = {
        "candidate": tmp_path / "reports" / "candidate.json",
        "readiness": tmp_path / "reports" / "readiness.json",
        "risk": tmp_path / "reports" / "risk.json",
        "executor": tmp_path / "reports" / "executor.json",
    }
    for key, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(reports[key]), encoding="utf-8")
    return paths


def _build(
    tmp_path: Path,
    *,
    reports: dict[str, dict[str, object]] | None = None,
    **kwargs: object,
) -> dict[str, object]:
    paths = _write_reports(tmp_path, reports or _valid_reports())
    return build_xauusd_signal_order_request_v0_43(
        candidate_report_path=paths["candidate"],
        readiness_gate_report_path=paths["readiness"],
        risk_envelope_report_path=paths["risk"],
        limited_demo_executor_report_path=paths["executor"],
        current_time=SAFE_NOW,
        **kwargs,
    )


def _qualified_signal() -> dict[str, object]:
    return {
        "qualified": True,
        "reason": "mocked_locked_candidate_signal_qualified",
        "side": "long",
        "order_type": "market",
        "action": "prepare_demo_order",
        "risk_reference": "fixed_v0_40_max_trade_risk_1R",
        "stop_distance": 1.25,
        "exit_rule": "fixed_v0_26_next_block_expansion_review",
    }


def test_no_qualified_signal_returns_no_request(tmp_path: Path) -> None:
    report = _build(tmp_path, signal_snapshot={"qualified": False, "reason": "mocked_no_signal"})

    assert report["builder_status"] == NO_QUALIFIED_SIGNAL_NOW
    assert report["signal_evaluated"] is True
    assert report["signal_qualified"] is False
    assert report["order_request_present"] is False
    assert report["order_request_complete"] is False
    assert report["order_send_called"] is False


def test_qualified_mocked_signal_builds_complete_internal_order_request(tmp_path: Path) -> None:
    report = _build(tmp_path, signal_snapshot=_qualified_signal())

    assert report["builder_status"] == ORDER_REQUEST_BUILT_DRY_RUN_ONLY
    assert report["signal_qualified"] is True
    assert report["order_request_present"] is True
    assert report["order_request_complete"] is True
    assert report["direction_assigned"] is True
    assert report["direction_source"] == "signal_snapshot_side"
    assert report["executable_side_valid"] is True
    assert report["order_request_missing_fields"] == []
    assert report["order_request_validation_status"] == "complete"
    request = report["order_request"]
    assert request["symbol"] == "XAUUSD"
    assert request["lot"] == 0.01
    assert request["demo_only"] is True
    assert request["candidate_id"] == CANDIDATE_ID
    assert request["side"] == "long"
    assert request["order_type"] == "market"
    assert request["action"] == "prepare_demo_order"
    assert request["risk_reference"] == "fixed_v0_40_max_trade_risk_1R"
    assert request["stop_distance"] == 1.25
    assert request["exit_rule"] == "fixed_v0_26_next_block_expansion_review"
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False


def test_incomplete_order_request_blocks(tmp_path: Path) -> None:
    report = _build(
        tmp_path,
        signal_snapshot={
            "qualified": True,
            "reason": "mocked_incomplete_signal",
            "order_type": "market",
            "action": "prepare_demo_order",
        },
    )

    assert report["builder_status"] == BLOCKED_INCOMPLETE_ORDER_REQUEST
    assert report["order_request_present"] is True
    assert report["order_request_complete"] is False
    assert "side" in report["order_request_missing_fields"]
    assert "risk_reference" in report["order_request_missing_fields"]
    assert "stop_loss_or_stop_distance" in report["order_request_missing_fields"]
    assert "take_profit_or_exit_rule" in report["order_request_missing_fields"]
    assert report["order_send_called"] is False


def test_direction_unassigned_review_only_is_not_complete(tmp_path: Path) -> None:
    signal = _qualified_signal()
    signal["side"] = "direction_unassigned_review_only"
    signal["direction_source"] = "locked_candidate_no_deterministic_direction_rule"

    report = _build(tmp_path, signal_snapshot=signal)

    assert report["builder_status"] == BLOCKED_INCOMPLETE_ORDER_REQUEST
    assert report["signal_qualified"] is True
    assert report["direction_assigned"] is False
    assert report["direction_source"] == "locked_candidate_no_deterministic_direction_rule"
    assert report["executable_side_valid"] is False
    assert report["order_request_present"] is True
    assert report["order_request_complete"] is False
    assert report["order_request_validation_status"] == "direction_unassigned_non_executable"
    assert report["invalid_order_request_reasons"] == ["direction_unassigned_non_executable"]
    assert "side" in report["order_request_missing_fields"]
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False


def test_unknown_side_is_not_complete(tmp_path: Path) -> None:
    signal = _qualified_signal()
    signal["side"] = "review_later"

    report = _build(tmp_path, signal_snapshot=signal)

    assert report["builder_status"] == BLOCKED_INCOMPLETE_ORDER_REQUEST
    assert report["executable_side_valid"] is False
    assert report["order_request_complete"] is False
    assert report["order_request_validation_status"] == "invalid_side_non_executable"
    assert report["invalid_order_request_reasons"] == ["side_not_allowed_internal_executable_side"]


def test_macro_event_window_blocks_before_signal_request(tmp_path: Path) -> None:
    paths = _write_reports(tmp_path, _valid_reports())

    report = build_xauusd_signal_order_request_v0_43(
        candidate_report_path=paths["candidate"],
        readiness_gate_report_path=paths["readiness"],
        risk_envelope_report_path=paths["risk"],
        limited_demo_executor_report_path=paths["executor"],
        current_time=MACRO_NOW,
        signal_snapshot=_qualified_signal(),
    )

    assert report["builder_status"] == BLOCKED_MACRO_EVENT_WINDOW
    assert report["macro_event_lock_status"] == BLOCKED_MACRO_EVENT_WINDOW
    assert report["signal_evaluated"] is False
    assert report["order_request_present"] is False
    assert report["order_send_called"] is False


def test_order_send_and_order_check_are_never_called(tmp_path: Path) -> None:
    report = _build(tmp_path, signal_snapshot=_qualified_signal())

    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["explicit_non_actions"]["order_send_called_or_wrapped"] is False
    assert report["explicit_non_actions"]["order_check_called_or_wrapped"] is False


def test_live_remains_blocked(tmp_path: Path) -> None:
    report = _build(tmp_path, signal_snapshot=_qualified_signal())

    assert report["dry_run"] is True
    assert report["live_allowed"] is False
    assert report["explicit_non_actions"]["live_execution_created"] is False


def test_lot_above_point_zero_one_blocks(tmp_path: Path) -> None:
    report = _build(tmp_path, lot=0.02, signal_snapshot=_qualified_signal())

    assert report["builder_status"] == BLOCKED_INCOMPLETE_ORDER_REQUEST
    assert "lot_must_equal_0.01" in report["blockers"]
    assert report["order_request_complete"] is False
    assert report["order_send_called"] is False


def test_candidate_id_mismatch_blocks(tmp_path: Path) -> None:
    reports = _valid_reports()
    reports["candidate"] = copy.deepcopy(reports["candidate"])
    reports["candidate"]["candidate_id"] = "wrong_candidate"

    report = _build(tmp_path, reports=reports, signal_snapshot=_qualified_signal())

    assert report["builder_status"] == BLOCKED_CANDIDATE_SIGNAL_UNAVAILABLE
    assert "candidate_id_mismatch" in report["blockers"]
    assert report["signal_evaluated"] is False
    assert report["order_request_present"] is False


def test_no_retune_threshold_search_parameter_grid_or_repeated_oos(tmp_path: Path) -> None:
    report = _build(tmp_path, signal_snapshot=_qualified_signal())

    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["repeated_oos_review"] is False
    assert report["explicit_non_actions"]["candidate_rules_changed"] is False
    assert report["explicit_non_actions"]["oos_review_repeated"] is False


def test_cli_builds_default_no_signal_report_without_order(tmp_path: Path) -> None:
    output_path = tmp_path / "xauusd_signal_order_request_v0_43.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_signal_order_request_v0_43.py"),
            "--symbol",
            "XAUUSD",
            "--lot",
            "0.01",
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
    assert stdout_report["builder_version"] == "v0_43"
    assert output_report["builder_status"] in {NO_QUALIFIED_SIGNAL_NOW, BLOCKED_MACRO_EVENT_WINDOW}
    assert output_report["order_send_called"] is False
    assert output_report["order_check_called"] is False
