from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.xauusd_final_demo_readiness_gate import (
    BLOCKED_BROKER_FACTS_ISSUE,
    BLOCKED_CANDIDATE_INTEGRITY_ISSUE,
    BLOCKED_MISSING_REQUIRED_REPORT,
    BLOCKED_OOS_OR_RULE_LOCK_ISSUE,
    BLOCKED_RISK_ENVELOPE_ISSUE,
    FINAL_DEMO_READINESS_GATE_PASSED_PENDING_HUMAN_AUTHORIZATION,
    build_xauusd_final_demo_readiness_gate_v0_41,
)

ROOT = Path(__file__).resolve().parents[1]


def _valid_reports() -> dict[str, dict[str, object]]:
    return {
        "v0_37": {
            "review_version": "v0_37",
            "review_status": "completed",
            "decision": "ready_for_demo_preflight_design",
            "candidate_id": "xauusd_compression_then_expansion_v0_26",
            "candidate_rules_preserved": True,
            "input_confirmations": {
                "candidate_id_is_locked_v0_26": True,
                "candidate_rules_modified": False,
                "one_time_oos_review_completed": True,
                "repeat_oos_review_allowed": False,
            },
            "integrity_blockers": [],
            "insufficient_forward_observation_blockers": [],
            "safety_state": {
                "demo_allowed": False,
                "demo_preflight_execution_allowed": False,
                "execution_allowed": False,
                "execution_queue_allowed": False,
                "live_allowed": False,
                "order_send_allowed": False,
                "order_send_created": False,
                "order_check_allowed": False,
                "order_check_created": False,
                "broker_execution_path_allowed": False,
                "buy_sell_output_allowed": False,
                "trade_recommendation_output_allowed": False,
                "recommendation_output_allowed": False,
                "directional_instruction_output_allowed": False,
                "retune_allowed": False,
                "threshold_search_allowed": False,
                "parameter_grid_allowed": False,
                "oos_repeat_allowed": False,
            },
            "non_actions_performed": {
                "demo_execution_created": False,
                "execution_queue_created": False,
                "broker_execution_path_created": False,
                "order_send_created": False,
                "order_check_created": False,
                "repeated_oos_review": False,
                "retune_performed": False,
                "threshold_search_performed": False,
                "parameter_grid_performed": False,
            },
        },
        "v0_38": {
            "preflight_version": "v0_38",
            "preflight_status": "completed",
            "decision": "demo_preflight_safety_design_ready",
            "candidate_id": "xauusd_compression_then_expansion_v0_26",
            "candidate_rules_preserved": True,
            "design_only": True,
            "blocking_conditions": [],
            "demo_execution_created": False,
            "broker_execution_path_created": False,
            "mt5_connection_created": False,
            "order_send_created": False,
            "order_check_created": False,
            "execution_queue_created": False,
            "buy_sell_output_allowed": False,
            "trade_recommendation_output_allowed": False,
            "repeated_oos_review": False,
            "retune_performed": False,
            "threshold_search_performed": False,
            "parameter_grid_performed": False,
            "explicit_non_actions": {
                "demo_execution_created": False,
                "execution_queue_created": False,
                "order_send_called_or_wrapped": False,
                "order_check_called_or_wrapped": False,
                "oos_review_repeated": False,
            },
        },
        "v0_39": {
            "audit_version": "v0_39",
            "audit_status": "completed",
            "decision": "broker_facts_audit_ready_for_risk_envelope_design",
            "candidate_id": "xauusd_compression_then_expansion_v0_26",
            "candidate_rules_preserved": True,
            "design_or_read_only": True,
            "broker_fact_blockers": [],
            "missing_facts": [],
            "broker_execution_path_created": False,
            "order_send_created": False,
            "order_send_called": False,
            "order_check_created": False,
            "order_check_called": False,
            "execution_queue_created": False,
            "buy_sell_output_allowed": False,
            "trade_recommendation_output_allowed": False,
            "repeated_oos_review": False,
            "retune_performed": False,
            "threshold_search_performed": False,
            "parameter_grid_performed": False,
        },
        "v0_40": {
            "envelope_version": "v0_40",
            "envelope_status": "completed",
            "decision": "demo_risk_envelope_design_ready",
            "candidate_id": "xauusd_compression_then_expansion_v0_26",
            "candidate_rules_preserved": True,
            "blockers": [],
            "warnings": ["tick_value_contract_size_mismatch"],
            "reported_tick_value": 0.1,
            "derived_tick_value": 1.0,
            "conservative_tick_value": 1.0,
            "fixed_risk_envelope": {
                "starting_demo_lot": 0.01,
                "max_demo_lot": 0.01,
                "max_positions": 1,
                "max_consecutive_losses_before_stop": 2,
                "max_daily_demo_loss_R": 2.0,
                "max_session_demo_loss_R": 1.0,
                "no_martingale": True,
                "no_averaging_into_loss": True,
                "no_position_scaling": True,
            },
            "demo_execution_allowed": False,
            "broker_execution_path_created": False,
            "order_send_allowed": False,
            "order_check_allowed": False,
            "execution_queue_created": False,
            "buy_sell_output_allowed": False,
            "trade_recommendation_output_allowed": False,
            "repeated_oos_review": False,
            "retune_performed": False,
            "threshold_search_performed": False,
            "parameter_grid_performed": False,
            "explicit_non_actions": {
                "demo_execution_created": False,
                "execution_queue_created": False,
                "order_send_called_or_wrapped": False,
                "order_check_called_or_wrapped": False,
                "oos_review_repeated": False,
            },
        },
    }


def _write_reports(tmp_path: Path, reports: dict[str, dict[str, object]]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for version, payload in reports.items():
        path = tmp_path / "reports" / f"{version}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths[version] = path
    return paths


def _build_with_reports(tmp_path: Path, reports: dict[str, dict[str, object]]) -> dict[str, object]:
    paths = _write_reports(tmp_path, reports)
    return build_xauusd_final_demo_readiness_gate_v0_41(
        v0_37_report_path=paths["v0_37"],
        v0_38_report_path=paths["v0_38"],
        v0_39_report_path=paths["v0_39"],
        v0_40_report_path=paths["v0_40"],
    )


def _blocker_names(report: dict[str, object]) -> list[str]:
    blockers = report["final_blockers"]
    assert isinstance(blockers, list)
    return [str(blocker["blocker"]) for blocker in blockers if isinstance(blocker, dict)]


def test_all_valid_fixture_reports_pass_final_gate(tmp_path: Path) -> None:
    report = _build_with_reports(tmp_path, _valid_reports())

    assert report["gate_version"] == "v0_41"
    assert report["gate_status"] == "completed"
    assert report["decision"] == FINAL_DEMO_READINESS_GATE_PASSED_PENDING_HUMAN_AUTHORIZATION
    assert report["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert report["candidate_rules_preserved"] is True
    assert report["final_blockers"] == []
    assert report["future_demo_execution_design_allowed_to_be_considered"] is True
    assert report["human_authorization_required"] is True

    accepted_warnings = report["accepted_warnings"]
    assert isinstance(accepted_warnings, list)
    assert accepted_warnings[0]["warning"] == "tick_value_contract_size_mismatch"
    assert accepted_warnings[0]["conservative_tick_value"] == 1.0


@pytest.mark.parametrize("missing_version", ["v0_37", "v0_38", "v0_39", "v0_40"])
def test_missing_required_report_blocks(tmp_path: Path, missing_version: str) -> None:
    reports = _valid_reports()
    paths = _write_reports(tmp_path, reports)
    paths[missing_version].unlink()

    report = build_xauusd_final_demo_readiness_gate_v0_41(
        v0_37_report_path=paths["v0_37"],
        v0_38_report_path=paths["v0_38"],
        v0_39_report_path=paths["v0_39"],
        v0_40_report_path=paths["v0_40"],
    )

    assert report["decision"] == BLOCKED_MISSING_REQUIRED_REPORT
    assert any(name.startswith(f"{missing_version}_report_missing:") for name in _blocker_names(report))


def test_candidate_mismatch_blocks(tmp_path: Path) -> None:
    reports = _valid_reports()
    reports["v0_38"]["candidate_id"] = "wrong_candidate"

    report = _build_with_reports(tmp_path, reports)

    assert report["decision"] == BLOCKED_CANDIDATE_INTEGRITY_ISSUE
    assert "v0_38_candidate_id_mismatch" in _blocker_names(report)


def test_broker_facts_blockers_block(tmp_path: Path) -> None:
    reports = _valid_reports()
    reports["v0_39"]["broker_fact_blockers"] = ["missing_symbol_digits"]

    report = _build_with_reports(tmp_path, reports)

    assert report["decision"] == BLOCKED_BROKER_FACTS_ISSUE
    assert "v0_39_broker_fact_blockers_not_empty" in _blocker_names(report)


def test_risk_envelope_blockers_block(tmp_path: Path) -> None:
    reports = _valid_reports()
    reports["v0_40"]["blockers"] = ["invalid_volume_step"]

    report = _build_with_reports(tmp_path, reports)

    assert report["decision"] == BLOCKED_RISK_ENVELOPE_ISSUE
    assert "v0_40_blockers_not_empty" in _blocker_names(report)


def test_wrong_lot_above_point_zero_one_blocks(tmp_path: Path) -> None:
    reports = _valid_reports()
    envelope = reports["v0_40"]["fixed_risk_envelope"]
    assert isinstance(envelope, dict)
    envelope["max_demo_lot"] = 0.02

    report = _build_with_reports(tmp_path, reports)

    assert report["decision"] == BLOCKED_RISK_ENVELOPE_ISSUE
    assert "v0_40_fixed_risk_envelope_max_demo_lot_invalid" in _blocker_names(report)


def test_missing_accepted_conservative_tick_handling_blocks(tmp_path: Path) -> None:
    reports = _valid_reports()
    reports["v0_40"]["conservative_tick_value"] = 0.1

    report = _build_with_reports(tmp_path, reports)

    assert report["decision"] == BLOCKED_RISK_ENVELOPE_ISSUE
    assert "v0_40_tick_value_contract_size_mismatch_not_conservatively_handled" in _blocker_names(report)
    assert report["accepted_warnings"] == []


def test_final_gate_still_keeps_demo_order_execution_false(tmp_path: Path) -> None:
    report = _build_with_reports(tmp_path, _valid_reports())

    for key in (
        "demo_allowed",
        "execution_allowed",
        "order_send_allowed",
        "order_check_allowed",
        "broker_execution_path_allowed",
        "buy_sell_output_allowed",
        "trade_recommendation_output_allowed",
        "retune_performed",
        "threshold_search_performed",
        "parameter_grid_performed",
        "repeated_oos_review",
    ):
        assert report[key] is False

    non_actions = report["explicit_non_actions"]
    assert isinstance(non_actions, dict)
    assert all(value is False for value in non_actions.values())


def test_v0_26_remains_locked_and_oos_is_not_repeated(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")

    report = _build_with_reports(tmp_path, _valid_reports())
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert report["candidate_rules_preserved"] is True
    assert report["repeated_oos_review"] is False


def test_repeated_oos_blocks(tmp_path: Path) -> None:
    reports = _valid_reports()
    confirmations = reports["v0_37"]["input_confirmations"]
    assert isinstance(confirmations, dict)
    confirmations["repeat_oos_review_allowed"] = True

    report = _build_with_reports(tmp_path, reports)

    assert report["decision"] == BLOCKED_OOS_OR_RULE_LOCK_ISSUE
    assert "v0_37_repeat_oos_review_not_disallowed" in _blocker_names(report)


def test_execution_surface_blocks_gate(tmp_path: Path) -> None:
    reports = _valid_reports()
    reports["v0_38"]["order_send_created"] = True

    report = _build_with_reports(tmp_path, reports)

    assert report["decision"] == "blocked_forward_or_preflight_issue"
    assert "v0_38_order_send_created_not_false" in _blocker_names(report)


def test_source_does_not_create_execution_order_or_mt5_path() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_final_demo_readiness_gate.py",
            ROOT / "scripts" / "build_xauusd_final_demo_readiness_gate_v0_41.py",
        ]
    ).lower()

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "trade" + "_request" not in source_text
    assert "metatrader5" not in source_text
    assert "copy_rates" not in source_text
    assert "initialize(" not in source_text
    assert "shutdown(" not in source_text


def test_report_does_not_emit_directional_or_recommendation_output(tmp_path: Path) -> None:
    report_text = json.dumps(_build_with_reports(tmp_path, _valid_reports()))
    source_text = (ROOT / "src" / "research" / "xauusd_final_demo_readiness_gate.py").read_text(encoding="utf-8")

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text
    assert "trade recommendation" not in report_text.lower()
    assert "trade recommendation" not in source_text.lower()


def test_cli_builds_v0_41_report(tmp_path: Path) -> None:
    paths = _write_reports(tmp_path, _valid_reports())
    output_path = tmp_path / "xauusd_final_demo_readiness_gate_v0_41.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_final_demo_readiness_gate_v0_41.py"),
            "--json",
            "--v0-37-report",
            str(paths["v0_37"]),
            "--v0-38-report",
            str(paths["v0_38"]),
            "--v0-39-report",
            str(paths["v0_39"]),
            "--v0-40-report",
            str(paths["v0_40"]),
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
    assert stdout_report["gate_version"] == "v0_41"
    assert output_report["decision"] == FINAL_DEMO_READINESS_GATE_PASSED_PENDING_HUMAN_AUTHORIZATION
