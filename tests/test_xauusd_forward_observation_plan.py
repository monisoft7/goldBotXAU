from __future__ import annotations

import json
from pathlib import Path

from scripts.project_health_check import build_project_health_report
from src.research.xauusd_forward_observation_plan import (
    ALLOWED_FUTURE_TIMEFRAMES,
    CANDIDATE_ID,
    EXPECTED_CSV_SCHEMA,
    build_xauusd_forward_observation_export_plan_v0_32,
    save_xauusd_forward_observation_export_plan,
)

ROOT = Path(__file__).resolve().parents[1]


def _journal_protocol(
    *,
    journal_status: str = "framework_ready_not_started",
    real_market_observation_started: bool = False,
    execution_allowed: bool = False,
    demo_allowed: bool = False,
    live_allowed: bool = False,
) -> dict[str, object]:
    return {
        "protocol_version": "v0_31",
        "candidate_id": CANDIDATE_ID,
        "journal_status": journal_status,
        "real_market_observation_started": real_market_observation_started,
        "execution_allowed": execution_allowed,
        "demo_allowed": demo_allowed,
        "live_allowed": live_allowed,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
        "safety": {
            "order_send_allowed": False,
            "order_check_allowed": False,
            "execution_queue_allowed": False,
        },
    }


def _candidate() -> dict[str, object]:
    return {
        "candidate_id": CANDIDATE_ID,
        "fixed_rules": {
            "reference_blocks": ["block_00_06", "block_06_12", "block_12_18"],
            "response_blocks": ["block_06_12", "block_12_18", "block_18_24"],
            "threshold_search_used": False,
            "parameter_grid_used": False,
            "retuning_used": False,
        },
    }


def _write_fixture_inputs(
    tmp_path: Path,
    *,
    journal_protocol: dict[str, object] | None = None,
    candidate: dict[str, object] | None = None,
) -> tuple[Path, Path]:
    reports = tmp_path / "reports"
    reports.mkdir()
    journal_path = reports / "xauusd_paper_shadow_journal_protocol_v0_31.json"
    candidate_path = reports / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    if journal_protocol is not None:
        journal_path.write_text(json.dumps(journal_protocol), encoding="utf-8")
    if candidate is not None:
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    return journal_path, candidate_path


def test_forward_observation_plan_blocks_if_v0_31_journal_protocol_missing(tmp_path: Path) -> None:
    journal_path, candidate_path = _write_fixture_inputs(tmp_path, candidate=_candidate())

    report = build_xauusd_forward_observation_export_plan_v0_32(
        journal_protocol_path=journal_path,
        candidate_report_path=candidate_path,
    )

    assert report["plan_status"] == "blocked_export_plan_prerequisites_not_met"
    assert any(blocker.startswith("v0_31_journal_protocol_missing") for blocker in report["blockers"])
    assert report["real_market_observation_started"] is False


def test_forward_observation_plan_blocks_if_real_market_observation_already_started(tmp_path: Path) -> None:
    journal_path, candidate_path = _write_fixture_inputs(
        tmp_path,
        journal_protocol=_journal_protocol(real_market_observation_started=True),
        candidate=_candidate(),
    )

    report = build_xauusd_forward_observation_export_plan_v0_32(
        journal_protocol_path=journal_path,
        candidate_report_path=candidate_path,
    )

    assert "real_market_observation_already_started" in report["blockers"]
    assert report["plan_status"] == "blocked_export_plan_prerequisites_not_met"
    assert report["real_market_observation_started"] is False


def test_forward_observation_plan_blocks_if_v0_31_journal_status_not_ready(tmp_path: Path) -> None:
    journal_path, candidate_path = _write_fixture_inputs(
        tmp_path,
        journal_protocol=_journal_protocol(journal_status="observation_started"),
        candidate=_candidate(),
    )

    report = build_xauusd_forward_observation_export_plan_v0_32(
        journal_protocol_path=journal_path,
        candidate_report_path=candidate_path,
    )

    assert "journal_status_not_framework_ready_not_started" in report["blockers"]
    assert report["plan_status"] == "blocked_export_plan_prerequisites_not_met"


def test_forward_observation_plan_blocks_if_execution_demo_or_live_allowed(tmp_path: Path) -> None:
    journal_path, candidate_path = _write_fixture_inputs(
        tmp_path,
        journal_protocol=_journal_protocol(execution_allowed=True, demo_allowed=True, live_allowed=True),
        candidate=_candidate(),
    )

    report = build_xauusd_forward_observation_export_plan_v0_32(
        journal_protocol_path=journal_path,
        candidate_report_path=candidate_path,
    )

    assert "journal_execution_allowed_not_false" in report["blockers"]
    assert "journal_demo_allowed_not_false" in report["blockers"]
    assert "journal_live_allowed_not_false" in report["blockers"]
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False


def test_forward_observation_plan_blocks_if_order_or_queue_paths_allowed(tmp_path: Path) -> None:
    journal = _journal_protocol()
    journal["safety"] = {
        "order_send_allowed": True,
        "order_check_allowed": True,
        "execution_queue_allowed": True,
    }
    journal_path, candidate_path = _write_fixture_inputs(
        tmp_path,
        journal_protocol=journal,
        candidate=_candidate(),
    )

    report = build_xauusd_forward_observation_export_plan_v0_32(
        journal_protocol_path=journal_path,
        candidate_report_path=candidate_path,
    )

    assert "journal_order_send_allowed_not_false" in report["blockers"]
    assert "journal_order_check_allowed_not_false" in report["blockers"]
    assert "journal_execution_queue_allowed_not_false" in report["blockers"]
    assert report["safety"]["order_path_allowed"] is False


def test_forward_observation_plan_report_has_required_v0_32_fields() -> None:
    report = build_xauusd_forward_observation_export_plan_v0_32()

    assert report["candidate_id"] == CANDIDATE_ID
    assert report["plan_status"] == "export_plan_ready_not_started"
    assert report["real_market_observation_started"] is False
    assert report["mt5_called"] is False
    assert report["data_exported"] is False
    assert report["observation_run"] is False
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["repeated_oos_review"] is False
    assert report["candidate_rules_modified"] is False
    assert report["allowed_future_timeframes"] == ["M5", "M10"]
    assert report["future_observation_mode"] == "journal_only"
    assert report["next_recommended_step"] == (
        "v0_33 build read-only forward observation exporter and journal runner, no execution"
    )


def test_forward_observation_plan_defines_future_inputs_without_exporting_data() -> None:
    report = build_xauusd_forward_observation_export_plan_v0_32()
    inputs = report["future_observation_inputs"]

    assert inputs["candidate_id"] == CANDIDATE_ID
    assert "XAUUSD" in inputs["allowed_symbol_names"]
    assert inputs["allowed_timeframes"] == ALLOWED_FUTURE_TIMEFRAMES
    assert inputs["allowed_read_only_exporter"]["status"] == "planned_not_built"
    assert inputs["observation_date_range_requirements"]["mode"] == "prospective_forward_only"
    assert inputs["expected_csv_schema"] == EXPECTED_CSV_SCHEMA
    assert inputs["no_execution_guarantee"]["csv_output_only"] is True
    assert report["data_exported"] is False


def test_forward_observation_plan_does_not_call_mt5_export_data_or_run_observation() -> None:
    report = build_xauusd_forward_observation_export_plan_v0_32()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_plan.py").read_text(encoding="utf-8")

    assert report["mt5_called"] is False
    assert report["data_exported"] is False
    assert report["observation_run"] is False
    assert "MetaTrader5" not in source_text
    assert "copy_rates" not in source_text
    assert "initialize(" not in source_text
    assert "shutdown(" not in source_text
    assert "to_csv(" not in source_text


def test_forward_observation_plan_does_not_run_backtest_or_repeat_oos() -> None:
    report = build_xauusd_forward_observation_export_plan_v0_32()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_plan.py").read_text(encoding="utf-8")

    assert report["non_actions_performed"]["new_backtest_evaluated"] is False
    assert report["non_actions_performed"]["new_oos_run_performed"] is False
    assert report["repeated_oos_review"] is False
    assert "run_xauusd_oos_review_v0_29" not in source_text
    assert "run_xauusd_backtest_lab" not in source_text
    assert "evaluate_oos" not in source_text


def test_forward_observation_plan_introduces_no_buy_sell_output() -> None:
    report_text = json.dumps(build_xauusd_forward_observation_export_plan_v0_32())
    source_text_raw = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_plan.py",
            ROOT / "scripts" / "build_xauusd_forward_observation_export_plan_v0_32.py",
        ]
    )

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text_raw
    assert "S" + "ELL" not in source_text_raw


def test_forward_observation_plan_introduces_no_execution_order_demo_or_live_code() -> None:
    source_text_raw = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_plan.py",
            ROOT / "scripts" / "build_xauusd_forward_observation_export_plan_v0_32.py",
        ]
    )
    source_text = source_text_raw.lower()

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "demo_allowed\": true" not in source_text
    assert "live_allowed\": true" not in source_text
    assert "execution_allowed\": true" not in source_text


def test_forward_observation_plan_does_not_modify_candidate_rules(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    output_path = tmp_path / "xauusd_forward_observation_export_plan_v0_32.json"

    report = build_xauusd_forward_observation_export_plan_v0_32()
    save_xauusd_forward_observation_export_plan(report, output_path)
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_rules_modified"] is False
    assert report["candidate_rules_lock"]["rule_change_allowed"] is False


def test_forward_observation_plan_keeps_project_health_safe() -> None:
    health = build_project_health_report(ROOT)

    assert health["status"] in {"healthy", "warnings"}
    assert health["failures"] == []
    assert health["failure_files"] == []
    assert health["project_state"]["oos_locked"] is True
