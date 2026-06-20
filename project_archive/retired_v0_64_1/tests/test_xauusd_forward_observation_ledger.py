from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.project_health_check import build_project_health_report
from src.research.xauusd_forward_observation_ledger import (
    CANDIDATE_ID,
    NEXT_RECOMMENDED_STEP,
    build_xauusd_forward_observation_ledger_v0_35,
    save_xauusd_forward_observation_ledger,
)

ROOT = Path(__file__).resolve().parents[1]


def _real_consolidated_report() -> dict[str, object]:
    return json.loads(
        (ROOT / "reports" / "xauusd_forward_observation_consolidated_v0_34_2.json").read_text(encoding="utf-8")
    )


def _write_report(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_builds_ledger_from_v0_34_2_style_consolidated_report(tmp_path: Path) -> None:
    report_path = _write_report(tmp_path / "reports" / "consolidated.json", _real_consolidated_report())

    ledger = build_xauusd_forward_observation_ledger_v0_35(input_consolidated_report_paths=[report_path])
    ledger_text = json.dumps(ledger)

    assert ledger["ledger_status"] == "completed"
    assert ledger["candidate_id"] == CANDIDATE_ID
    assert ledger["input_consolidated_reports"] == [str(report_path)]
    assert ledger["raw_market_data_embedded"] is False
    assert ledger["total_unique_journal_records"] == 2
    assert ledger["timeframes_observed"] == ["M10", "M5"]
    assert ledger["expansion_observed_count"] == 0
    assert ledger["no_expansion_observed_count"] == 2
    assert ledger["quality_gate_status"] == "insufficient_samples"
    assert ledger["demo_preflight_allowed"] is False
    assert ledger["execution_allowed"] is False
    assert ledger["demo_allowed"] is False
    assert ledger["live_allowed"] is False
    assert ledger["order_send_allowed"] is False
    assert ledger["order_check_allowed"] is False
    assert ledger["repeated_oos_review"] is False
    assert ledger["candidate_rules_modified"] is False
    assert ledger["next_recommended_step"] == NEXT_RECOMMENDED_STEP
    assert '"open"' not in ledger_text
    assert '"high"' not in ledger_text
    assert '"low"' not in ledger_text
    assert '"close"' not in ledger_text
    assert '"tick_volume"' not in ledger_text
    assert '"spread"' not in ledger_text


def test_deduplicates_duplicate_observation_records(tmp_path: Path) -> None:
    consolidated = _real_consolidated_report()
    records = consolidated["neutral_journal_records"]
    assert isinstance(records, list)
    records.append(copy.deepcopy(records[0]))
    report_path = _write_report(tmp_path / "reports" / "duplicate_consolidated.json", consolidated)

    ledger = build_xauusd_forward_observation_ledger_v0_35(input_consolidated_report_paths=[report_path])

    assert ledger["ledger_status"] == "completed"
    assert ledger["total_unique_journal_records"] == 2
    assert ledger["journal_record_count_by_timeframe"] == {"M10": 1, "M5": 1}


def test_blocks_if_candidate_mismatch(tmp_path: Path) -> None:
    consolidated = _real_consolidated_report()
    consolidated["candidate_id"] = "wrong_candidate"
    report_path = _write_report(tmp_path / "reports" / "candidate_mismatch.json", consolidated)

    ledger = build_xauusd_forward_observation_ledger_v0_35(input_consolidated_report_paths=[report_path])

    assert ledger["ledger_status"] == "blocked"
    assert ledger["quality_gate_status"] == "forward_behavior_failed_review"
    assert any("candidate_id_mismatch" in blocker for blocker in ledger["blockers"])
    assert ledger["demo_preflight_allowed"] is False


def test_blocks_if_raw_market_data_appears_embedded(tmp_path: Path) -> None:
    consolidated = _real_consolidated_report()
    consolidated["raw_ohlc_rows"] = [
        {
            "timestamp_utc": "2026-06-12T00:00:00+00:00",
            "open": 3300.0,
            "high": 3310.0,
            "low": 3295.0,
            "close": 3305.0,
        }
    ]
    report_path = _write_report(tmp_path / "reports" / "raw_market_embedded.json", consolidated)

    ledger = build_xauusd_forward_observation_ledger_v0_35(input_consolidated_report_paths=[report_path])

    assert ledger["ledger_status"] == "blocked"
    assert ledger["raw_market_data_embedded"] is False
    assert any("raw_market_data_payload_detected" in blocker for blocker in ledger["blockers"])


def test_blocks_if_execution_demo_live_or_order_is_allowed(tmp_path: Path) -> None:
    consolidated = _real_consolidated_report()
    consolidated["execution_allowed"] = True
    consolidated["demo_allowed"] = True
    consolidated["live_allowed"] = True
    consolidated["order_send_allowed"] = True
    consolidated["order_check_allowed"] = True
    report_path = _write_report(tmp_path / "reports" / "unsafe_permissions.json", consolidated)

    ledger = build_xauusd_forward_observation_ledger_v0_35(input_consolidated_report_paths=[report_path])

    assert ledger["ledger_status"] == "blocked"
    assert ledger["quality_gate_status"] == "forward_behavior_failed_review"
    assert any("execution_allowed_not_false" in blocker for blocker in ledger["blockers"])
    assert any("demo_allowed_not_false" in blocker for blocker in ledger["blockers"])
    assert any("live_allowed_not_false" in blocker for blocker in ledger["blockers"])
    assert any("order_send_allowed_not_false" in blocker for blocker in ledger["blockers"])
    assert any("order_check_allowed_not_false" in blocker for blocker in ledger["blockers"])
    assert ledger["execution_allowed"] is False
    assert ledger["demo_allowed"] is False
    assert ledger["live_allowed"] is False
    assert ledger["order_send_allowed"] is False
    assert ledger["order_check_allowed"] is False


def test_keeps_candidate_rules_unchanged(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    output_path = tmp_path / "xauusd_forward_observation_ledger_v0_35.json"

    ledger = build_xauusd_forward_observation_ledger_v0_35()
    save_xauusd_forward_observation_ledger(ledger, output_path)
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert ledger["candidate_id"] == CANDIDATE_ID
    assert ledger["candidate_rules_modified"] is False
    assert ledger["candidate_rules_lock"]["rule_change_allowed"] is False
    assert ledger["candidate_rules_lock"]["threshold_search_allowed"] is False
    assert ledger["candidate_rules_lock"]["parameter_grid_allowed"] is False
    assert ledger["candidate_rules_lock"]["parameter_optimization_allowed"] is False
    assert ledger["candidate_rules_lock"]["retune_allowed"] is False


def test_does_not_run_mt5() -> None:
    ledger = build_xauusd_forward_observation_ledger_v0_35()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_ledger.py").read_text(encoding="utf-8")

    assert ledger["non_actions_performed"]["mt5_called"] is False
    assert ledger["safety_state"]["mt5_called"] is False
    assert "MetaTrader5" not in source_text
    assert "copy_rates" not in source_text
    assert "initialize(" not in source_text
    assert "shutdown(" not in source_text


def test_does_not_export_market_data() -> None:
    ledger = build_xauusd_forward_observation_ledger_v0_35()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_ledger.py").read_text(encoding="utf-8")

    assert ledger["non_actions_performed"]["market_data_exported"] is False
    assert ledger["safety_state"]["market_data_exported"] is False
    assert "DictWriter" not in source_text
    assert "writerow" not in source_text


def test_does_not_repeat_oos() -> None:
    ledger = build_xauusd_forward_observation_ledger_v0_35()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_ledger.py").read_text(encoding="utf-8")

    assert ledger["repeated_oos_review"] is False
    assert ledger["non_actions_performed"]["new_oos_run_performed"] is False
    assert ledger["safety_state"]["new_oos_evaluation_allowed"] is False
    assert "run_xauusd_oos_review_v0_29" not in source_text
    assert "load_oos_rows" not in source_text
    assert "evaluate_oos" not in source_text


def test_no_buy_sell_output_introduced() -> None:
    ledger_text = json.dumps(build_xauusd_forward_observation_ledger_v0_35())
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_ledger.py",
            ROOT / "scripts" / "build_xauusd_forward_observation_ledger_v0_35.py",
        ]
    )

    assert "B" + "UY" not in ledger_text
    assert "S" + "ELL" not in ledger_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text


def test_no_execution_order_demo_live_semantics_introduced() -> None:
    ledger = build_xauusd_forward_observation_ledger_v0_35()
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_ledger.py",
            ROOT / "scripts" / "build_xauusd_forward_observation_ledger_v0_35.py",
        ]
    ).lower()

    assert ledger["execution_allowed"] is False
    assert ledger["demo_allowed"] is False
    assert ledger["live_allowed"] is False
    assert ledger["order_send_allowed"] is False
    assert ledger["order_check_allowed"] is False
    assert ledger["safety_state"]["execution_queue_allowed"] is False
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "demo_allowed\": true" not in source_text
    assert "live_allowed\": true" not in source_text
    assert "execution_allowed\": true" not in source_text


def test_project_health_remains_safe() -> None:
    health = build_project_health_report(ROOT)

    assert health["status"] in {"healthy", "warnings"}
    assert health["failures"] == []
    assert health["failure_files"] == []
    assert health["project_state"]["oos_locked"] is True
