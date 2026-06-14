from __future__ import annotations

import json
from pathlib import Path

from scripts.project_health_check import build_project_health_report
from src.research.xauusd_forward_observation_runner import (
    ALLOWED_TIMEFRAMES,
    CANDIDATE_ID,
    build_xauusd_forward_observation_runner_protocol_v0_33,
    csv_rows_to_journal_fixture_rows,
    default_synthetic_fixture_csv_rows,
    save_xauusd_forward_observation_runner_protocol,
    validate_forward_observation_csv_rows,
    write_local_fixture_forward_observation_csv,
)

ROOT = Path(__file__).resolve().parents[1]


def _fixed_rules() -> dict[str, object]:
    return {
        "reference_blocks": ["block_00_06", "block_06_12", "block_12_18"],
        "response_blocks": ["block_06_12", "block_12_18", "block_18_24"],
        "threshold_search_used": False,
        "parameter_grid_used": False,
        "retuning_used": False,
    }


def _candidate() -> dict[str, object]:
    return {
        "candidate_id": CANDIDATE_ID,
        "fixed_rules": _fixed_rules(),
    }


def _plan(
    *,
    plan_status: str = "export_plan_ready_not_started",
    future_observation_mode: str = "journal_only",
    execution_allowed: bool = False,
    demo_allowed: bool = False,
    live_allowed: bool = False,
    allowed_timeframes: list[str] | None = None,
) -> dict[str, object]:
    real_plan = json.loads((ROOT / "reports" / "xauusd_forward_observation_export_plan_v0_32.json").read_text())
    real_plan["plan_status"] = plan_status
    real_plan["future_observation_mode"] = future_observation_mode
    real_plan["execution_allowed"] = execution_allowed
    real_plan["demo_allowed"] = demo_allowed
    real_plan["live_allowed"] = live_allowed
    real_plan["allowed_future_timeframes"] = allowed_timeframes or ["M5", "M10"]
    return real_plan


def _journal_protocol() -> dict[str, object]:
    return {
        "protocol_version": "v0_31",
        "candidate_id": CANDIDATE_ID,
        "journal_status": "framework_ready_not_started",
        "real_market_observation_started": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
    }


def _write_fixture_inputs(
    tmp_path: Path,
    *,
    plan: dict[str, object] | None = None,
    journal_protocol: dict[str, object] | None = None,
    candidate: dict[str, object] | None = None,
) -> tuple[Path, Path, Path]:
    reports = tmp_path / "reports"
    reports.mkdir()
    plan_path = reports / "xauusd_forward_observation_export_plan_v0_32.json"
    journal_path = reports / "xauusd_paper_shadow_journal_protocol_v0_31.json"
    candidate_path = reports / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    if plan is not None:
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
    if journal_protocol is not None:
        journal_path.write_text(json.dumps(journal_protocol), encoding="utf-8")
    if candidate is not None:
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    return plan_path, journal_path, candidate_path


def test_runner_blocks_if_v0_32_plan_missing(tmp_path: Path) -> None:
    plan_path, journal_path, candidate_path = _write_fixture_inputs(
        tmp_path,
        journal_protocol=_journal_protocol(),
        candidate=_candidate(),
    )

    report = build_xauusd_forward_observation_runner_protocol_v0_33(
        plan_path=plan_path,
        journal_protocol_path=journal_path,
        candidate_report_path=candidate_path,
    )

    assert report["runner_status"] == "blocked_runner_prerequisites_not_met"
    assert any(blocker.startswith("v0_32_forward_observation_plan_missing") for blocker in report["blockers"])
    assert report["real_market_observation_started"] is False


def test_runner_blocks_if_plan_status_not_ready(tmp_path: Path) -> None:
    plan_path, journal_path, candidate_path = _write_fixture_inputs(
        tmp_path,
        plan=_plan(plan_status="observation_started"),
        journal_protocol=_journal_protocol(),
        candidate=_candidate(),
    )

    report = build_xauusd_forward_observation_runner_protocol_v0_33(
        plan_path=plan_path,
        journal_protocol_path=journal_path,
        candidate_report_path=candidate_path,
    )

    assert "plan_status_not_export_plan_ready_not_started" in report["blockers"]
    assert report["runner_status"] == "blocked_runner_prerequisites_not_met"


def test_runner_blocks_if_execution_demo_or_live_allowed(tmp_path: Path) -> None:
    plan_path, journal_path, candidate_path = _write_fixture_inputs(
        tmp_path,
        plan=_plan(execution_allowed=True, demo_allowed=True, live_allowed=True),
        journal_protocol=_journal_protocol(),
        candidate=_candidate(),
    )

    report = build_xauusd_forward_observation_runner_protocol_v0_33(
        plan_path=plan_path,
        journal_protocol_path=journal_path,
        candidate_report_path=candidate_path,
    )

    assert "plan_execution_allowed_not_false" in report["blockers"]
    assert "plan_demo_allowed_not_false" in report["blockers"]
    assert "plan_live_allowed_not_false" in report["blockers"]
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False


def test_runner_confirms_candidate_and_journal_only_mode() -> None:
    report = build_xauusd_forward_observation_runner_protocol_v0_33()

    assert report["candidate_id"] == CANDIDATE_ID
    assert report["runner_status"] == "framework_ready_not_started"
    assert report["future_mode"] == "journal_only"
    assert report["allowed_timeframes"] == ["M5", "M10"]


def test_runner_supports_m5_and_m10_only() -> None:
    rows = default_synthetic_fixture_csv_rows()

    assert validate_forward_observation_csv_rows(rows) == []
    assert {row["timeframe"] for row in rows} == set(ALLOWED_TIMEFRAMES)

    bad_rows = [dict(rows[0], timeframe="M15")]
    assert "row_0_timeframe_not_allowed" in validate_forward_observation_csv_rows(bad_rows)


def test_fixture_csv_journal_generation_works(tmp_path: Path) -> None:
    csv_path = tmp_path / "fixture_forward_rows.csv"
    write_local_fixture_forward_observation_csv(default_synthetic_fixture_csv_rows(), csv_path)

    report = build_xauusd_forward_observation_runner_protocol_v0_33(fixture_csv_path=csv_path)

    assert report["runner_status"] == "framework_ready_not_started"
    assert report["synthetic_fixture_csv_row_count"] > 0
    assert report["synthetic_fixture_journal_record_count"] == 2
    assert {record["candidate_id"] for record in report["synthetic_fixture_journal_records"]} == {CANDIDATE_ID}
    assert {record["rule_match_status"] for record in report["synthetic_fixture_journal_records"]} == {"rule match"}


def test_csv_conversion_selects_lowest_reference_block_without_modifying_rules() -> None:
    fixed_rules = _fixed_rules()
    before = json.dumps(fixed_rules, sort_keys=True)

    fixture_rows = csv_rows_to_journal_fixture_rows(default_synthetic_fixture_csv_rows(), fixed_rules)
    after = json.dumps(fixed_rules, sort_keys=True)

    assert before == after
    assert len(fixture_rows) == 2
    assert {row["observed_reference_block"] for row in fixture_rows} == {"block_00_06"}
    assert {row["observed_response_block"] for row in fixture_rows} == {"block_06_12"}


def test_runner_does_not_call_mt5_in_tests() -> None:
    report = build_xauusd_forward_observation_runner_protocol_v0_33()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_runner.py").read_text(encoding="utf-8")

    assert report["mt5_called_in_tests"] is False
    assert report["readonly_exporter_wrapper"]["mt5_called"] is False
    assert "MetaTrader5" not in source_text
    assert "copy_rates" not in source_text
    assert "initialize(" not in source_text
    assert "shutdown(" not in source_text


def test_runner_does_not_run_real_observation_in_v0_33() -> None:
    report = build_xauusd_forward_observation_runner_protocol_v0_33()

    assert report["real_market_observation_started"] is False
    assert report["readonly_exporter_wrapper"]["real_market_observation_started"] is False
    assert report["non_actions_performed"]["real_observation_run"] is False
    assert report["data_source_status"] == "synthetic_fixtures_only"


def test_runner_does_not_repeat_oos() -> None:
    report = build_xauusd_forward_observation_runner_protocol_v0_33()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_runner.py").read_text(encoding="utf-8")

    assert report["repeated_oos_review"] is False
    assert report["non_actions_performed"]["new_oos_run_performed"] is False
    assert "run_xauusd_oos_review_v0_29" not in source_text
    assert "load_oos_rows" not in source_text
    assert "evaluate_oos" not in source_text


def test_runner_introduces_no_buy_sell_output() -> None:
    report_text = json.dumps(build_xauusd_forward_observation_runner_protocol_v0_33())
    source_text_raw = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_runner.py",
            ROOT / "scripts" / "run_xauusd_forward_observation_v0_33.py",
        ]
    )

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text_raw
    assert "S" + "ELL" not in source_text_raw


def test_runner_introduces_no_execution_order_demo_or_live_semantics() -> None:
    source_text_raw = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_runner.py",
            ROOT / "scripts" / "run_xauusd_forward_observation_v0_33.py",
        ]
    )
    source_text = source_text_raw.lower()

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "broker" not in source_text
    assert "demo_allowed\": true" not in source_text
    assert "live_allowed\": true" not in source_text
    assert "execution_allowed\": true" not in source_text


def test_runner_does_not_modify_candidate_rules(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    output_path = tmp_path / "xauusd_forward_observation_runner_protocol_v0_33.json"

    report = build_xauusd_forward_observation_runner_protocol_v0_33()
    save_xauusd_forward_observation_runner_protocol(report, output_path)
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_rules_modified"] is False
    assert report["candidate_rules_lock"]["rule_change_allowed"] is False


def test_runner_keeps_project_health_safe() -> None:
    health = build_project_health_report(ROOT)

    assert health["status"] in {"healthy", "warnings"}
    assert health["failures"] == []
    assert health["failure_files"] == []
    assert health["project_state"]["oos_locked"] is True
