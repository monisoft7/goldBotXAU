from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_demo_risk_envelope import (
    BLOCKED_INVALID_TICK_OR_CONTRACT_VALUES,
    BLOCKED_INVALID_VOLUME_CONSTRAINTS,
    BLOCKED_MISSING_BROKER_FACTS,
    DEMO_RISK_ENVELOPE_DESIGN_READY,
    build_xauusd_demo_risk_envelope_v0_40,
)

ROOT = Path(__file__).resolve().parents[1]


def _valid_broker_facts_report() -> dict[str, object]:
    return {
        "audit_version": "v0_39",
        "decision": "broker_facts_audit_ready_for_risk_envelope_design",
        "candidate_id": "xauusd_compression_then_expansion_v0_26",
        "candidate_rules_preserved": True,
        "broker_facts": {
            "symbol": {
                "digits": 2,
                "point": 0.01,
                "trade_contract_size": 100.0,
                "trade_tick_size": 0.01,
                "trade_tick_value": 1.0,
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01,
                "spread": 13,
                "spread_float": True,
                "trade_stops_level": 0,
                "trade_freeze_level": 0,
            }
        },
    }


def _write_report(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _build_with_report(tmp_path: Path, payload: dict[str, object]) -> dict[str, object]:
    report_path = _write_report(tmp_path / "reports" / "broker_facts.json", payload)
    return build_xauusd_demo_risk_envelope_v0_40(broker_facts_report_path=report_path)


def test_valid_v0_39_facts_produce_design_ready(tmp_path: Path) -> None:
    report = _build_with_report(tmp_path, _valid_broker_facts_report())

    assert report["envelope_version"] == "v0_40"
    assert report["envelope_status"] == "completed"
    assert report["decision"] == DEMO_RISK_ENVELOPE_DESIGN_READY
    assert report["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert report["candidate_rules_preserved"] is True
    assert report["source_broker_facts_report"].endswith("broker_facts.json")
    assert report["reported_tick_value"] == 1.0
    assert report["derived_tick_value"] == 1.0
    assert report["conservative_tick_value"] == 1.0
    assert report["warnings"] == []
    assert report["blockers"] == []

    envelope = report["fixed_risk_envelope"]
    assert isinstance(envelope, dict)
    assert envelope["max_positions"] == 1
    assert envelope["starting_demo_lot"] == 0.01
    assert envelope["max_demo_lot"] == 0.01
    assert envelope["max_consecutive_losses_before_stop"] == 2
    assert envelope["max_daily_demo_loss_R"] == 2.0
    assert envelope["max_session_demo_loss_R"] == 1.0
    assert envelope["max_trade_risk_R"] == 1.0


def test_missing_volume_min_blocks(tmp_path: Path) -> None:
    payload = _valid_broker_facts_report()
    symbol = payload["broker_facts"]["symbol"]
    assert isinstance(symbol, dict)
    symbol["volume_min"] = None

    report = _build_with_report(tmp_path, payload)

    assert report["decision"] == BLOCKED_MISSING_BROKER_FACTS
    assert "missing_broker_fact: symbol.volume_min" in report["blockers"]
    assert report["fixed_risk_envelope"]["starting_demo_lot"] is None


def test_invalid_volume_step_blocks(tmp_path: Path) -> None:
    payload = _valid_broker_facts_report()
    symbol = payload["broker_facts"]["symbol"]
    assert isinstance(symbol, dict)
    symbol["volume_step"] = 0

    report = _build_with_report(tmp_path, payload)

    assert report["decision"] == BLOCKED_INVALID_VOLUME_CONSTRAINTS
    assert "invalid_volume_step" in report["blockers"]


def test_invalid_tick_or_contract_values_block(tmp_path: Path) -> None:
    payload = _valid_broker_facts_report()
    symbol = payload["broker_facts"]["symbol"]
    assert isinstance(symbol, dict)
    symbol["trade_contract_size"] = 0

    report = _build_with_report(tmp_path, payload)

    assert report["decision"] == BLOCKED_INVALID_TICK_OR_CONTRACT_VALUES
    assert "invalid_trade_contract_size" in report["blockers"]
    assert report["conservative_tick_value"] is None


def test_tick_value_mismatch_warns_and_uses_conservative_max(tmp_path: Path) -> None:
    payload = _valid_broker_facts_report()
    symbol = payload["broker_facts"]["symbol"]
    assert isinstance(symbol, dict)
    symbol["trade_tick_value"] = 0.1

    report = _build_with_report(tmp_path, payload)

    assert report["decision"] == DEMO_RISK_ENVELOPE_DESIGN_READY
    assert report["warnings"] == ["tick_value_contract_size_mismatch"]
    assert report["reported_tick_value"] == 0.1
    assert report["derived_tick_value"] == 1.0
    assert report["conservative_tick_value"] == 1.0


def test_all_execution_order_and_demo_outputs_remain_false(tmp_path: Path) -> None:
    report = _build_with_report(tmp_path, _valid_broker_facts_report())

    for key in (
        "design_only",
        "demo_execution_allowed",
        "order_send_allowed",
        "order_check_allowed",
        "broker_execution_path_created",
        "execution_queue_created",
        "buy_sell_output_allowed",
        "trade_recommendation_output_allowed",
        "retune_performed",
        "threshold_search_performed",
        "parameter_grid_performed",
        "repeated_oos_review",
    ):
        assert report[key] is (True if key == "design_only" else False)

    non_actions = report["explicit_non_actions"]
    assert isinstance(non_actions, dict)
    assert all(value is False for value in non_actions.values())


def test_v0_26_remains_locked_and_oos_is_not_repeated(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")

    report = _build_with_report(tmp_path, _valid_broker_facts_report())
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert report["candidate_rules_preserved"] is True
    assert report["repeated_oos_review"] is False


def test_missing_broker_facts_report_blocks(tmp_path: Path) -> None:
    report = build_xauusd_demo_risk_envelope_v0_40(
        broker_facts_report_path=tmp_path / "reports" / "missing.json"
    )

    assert report["decision"] == BLOCKED_MISSING_BROKER_FACTS
    assert report["envelope_status"] == "blocked"
    assert report["blockers"][0].startswith("broker_facts_report_missing:")


def test_source_does_not_create_execution_order_or_mt5_path() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_demo_risk_envelope.py",
            ROOT / "scripts" / "build_xauusd_demo_risk_envelope_v0_40.py",
        ]
    ).lower()

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "trade_request" not in source_text
    assert "metatrader5" not in source_text
    assert "copy_rates" not in source_text
    assert "initialize(" not in source_text
    assert "shutdown(" not in source_text


def test_report_does_not_emit_directional_or_recommendation_output(tmp_path: Path) -> None:
    report_text = json.dumps(_build_with_report(tmp_path, _valid_broker_facts_report()))
    source_text = (ROOT / "src" / "research" / "xauusd_demo_risk_envelope.py").read_text(encoding="utf-8")

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text
    assert "trade recommendation" not in report_text.lower()
    assert "trade recommendation" not in source_text.lower()


def test_cli_builds_v0_40_report(tmp_path: Path) -> None:
    broker_facts_path = _write_report(tmp_path / "broker_facts.json", _valid_broker_facts_report())
    output_path = tmp_path / "xauusd_demo_risk_envelope_v0_40.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_demo_risk_envelope_v0_40.py"),
            "--json",
            "--broker-facts-report",
            str(broker_facts_path),
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
    assert stdout_report["envelope_version"] == "v0_40"
    assert output_report["decision"] == DEMO_RISK_ENVELOPE_DESIGN_READY
