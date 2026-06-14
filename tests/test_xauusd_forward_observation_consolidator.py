from __future__ import annotations

import json
from pathlib import Path

from scripts.project_health_check import build_project_health_report
from src.research.xauusd_forward_observation_consolidator import (
    CANDIDATE_ID,
    MISSING_REPORTS_BLOCKER,
    NEXT_RECOMMENDED_STEP,
    build_xauusd_forward_observation_consolidation_v0_34_2,
    save_xauusd_forward_observation_consolidation,
)

ROOT = Path(__file__).resolve().parents[1]


def _real_runner_report(name: str) -> dict[str, object]:
    return json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_consolidates_fixture_runner_json_reports_without_raw_market_rows(tmp_path: Path) -> None:
    m5_path = _write_json(
        tmp_path / "reports" / "xauusd_forward_observation_m5_normalized_v0_34_2.json",
        _real_runner_report("xauusd_forward_observation_m5_normalized_v0_34_2.json"),
    )
    m10_path = _write_json(
        tmp_path / "reports" / "xauusd_forward_observation_m10_normalized_v0_34_2.json",
        _real_runner_report("xauusd_forward_observation_m10_normalized_v0_34_2.json"),
    )

    report = build_xauusd_forward_observation_consolidation_v0_34_2(input_report_paths=[m5_path, m10_path])
    report_text = json.dumps(report)

    assert report["consolidation_status"] == "completed"
    assert report["observation_mode"] == "local_read_only_forward_journal"
    assert report["raw_market_data_embedded"] is False
    assert report["total_input_reports"] == 2
    assert report["timeframes_observed"] == ["M10", "M5"]
    assert report["journal_record_count_by_timeframe"] == {"M10": 1, "M5": 1}
    assert report["total_journal_record_count"] == 2
    assert report["expansion_observed_count"] == 0
    assert report["no_expansion_observed_count"] == 2
    assert report["observation_quality_status"] == "insufficient_sample_for_quality_gate"
    assert report["next_recommended_step"] == NEXT_RECOMMENDED_STEP
    assert '"open"' not in report_text
    assert '"high"' not in report_text
    assert '"low"' not in report_text
    assert '"close"' not in report_text
    assert '"tick_volume"' not in report_text
    assert '"spread"' not in report_text
    assert "synthetic fixture" not in report_text.lower()


def test_blocks_if_local_journal_reports_are_missing(tmp_path: Path) -> None:
    missing_m5 = tmp_path / "reports" / "missing_m5.json"
    missing_m10 = tmp_path / "reports" / "missing_m10.json"

    report = build_xauusd_forward_observation_consolidation_v0_34_2(
        input_report_paths=[missing_m5, missing_m10]
    )

    assert report["consolidation_status"] == MISSING_REPORTS_BLOCKER
    assert MISSING_REPORTS_BLOCKER in report["blockers"]
    assert report["total_input_reports"] == 0
    assert report["total_journal_record_count"] == 0
    assert report["raw_market_data_embedded"] is False


def test_keeps_candidate_rules_unchanged(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    output_path = tmp_path / "xauusd_forward_observation_consolidated_v0_34_2.json"

    report = build_xauusd_forward_observation_consolidation_v0_34_2()
    save_xauusd_forward_observation_consolidation(report, output_path)
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_id"] == CANDIDATE_ID
    assert report["candidate_rules_modified"] is False
    assert report["candidate_rules_lock"]["rule_change_allowed"] is False
    assert report["candidate_rules_lock"]["threshold_search_allowed"] is False
    assert report["candidate_rules_lock"]["parameter_grid_allowed"] is False
    assert report["candidate_rules_lock"]["parameter_optimization_allowed"] is False
    assert report["candidate_rules_lock"]["retune_allowed"] is False


def test_does_not_run_mt5() -> None:
    report = build_xauusd_forward_observation_consolidation_v0_34_2()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_consolidator.py").read_text(
        encoding="utf-8"
    )

    assert report["mt5_called"] is False
    assert report["safety_state"]["mt5_called"] is False
    assert "MetaTrader5" not in source_text
    assert "copy_rates" not in source_text
    assert "initialize(" not in source_text
    assert "shutdown(" not in source_text


def test_does_not_export_market_data() -> None:
    report = build_xauusd_forward_observation_consolidation_v0_34_2()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_consolidator.py").read_text(
        encoding="utf-8"
    )

    assert report["market_data_exported"] is False
    assert report["safety_state"]["market_data_exported"] is False
    assert "DictWriter" not in source_text
    assert "writerow" not in source_text


def test_does_not_repeat_oos() -> None:
    report = build_xauusd_forward_observation_consolidation_v0_34_2()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_consolidator.py").read_text(
        encoding="utf-8"
    )

    assert report["repeated_oos_review"] is False
    assert report["non_actions_performed"]["new_oos_run_performed"] is False
    assert report["safety_state"]["new_oos_evaluation_allowed"] is False
    assert "run_xauusd_oos_review_v0_29" not in source_text
    assert "load_oos_rows" not in source_text
    assert "evaluate_oos" not in source_text


def test_no_buy_sell_output_introduced() -> None:
    report_text = json.dumps(build_xauusd_forward_observation_consolidation_v0_34_2())
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_consolidator.py",
            ROOT / "scripts" / "consolidate_xauusd_forward_observation_v0_34_2.py",
        ]
    )

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text


def test_no_execution_order_demo_live_semantics_introduced() -> None:
    report = build_xauusd_forward_observation_consolidation_v0_34_2()
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_consolidator.py",
            ROOT / "scripts" / "consolidate_xauusd_forward_observation_v0_34_2.py",
        ]
    ).lower()

    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["order_send_allowed"] is False
    assert report["order_check_allowed"] is False
    assert report["safety_state"]["execution_queue_allowed"] is False
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
