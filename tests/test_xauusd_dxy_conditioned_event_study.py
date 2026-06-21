from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.xauusd_dxy_conditioned_event_study import (
    BLOCKED_MISSING_DATA,
    COMPLETED,
    COMPLETED_NO_CLEAR_LEADS,
    LABEL_NAMES,
    NO_CLEAR_LEAD_NEXT_STEP,
    STUDY_VERSION,
    assert_backward_asof_safe,
    build_xauusd_dxy_conditioned_event_study_v0_68,
)

ROOT = Path(__file__).resolve().parents[1]


def _events() -> list[dict[str, object]]:
    return [
        {
            "source_research_version": "v0_53",
            "candidate_id": "sample_candidate",
            "entry_timestamp": "2024-01-02T00:15:00",
            "split": "train",
            "return_r": 1.0,
        },
        {
            "source_research_version": "v0_53",
            "candidate_id": "sample_candidate",
            "entry_timestamp": "2024-01-02T00:30:00",
            "split": "train",
            "return_r": -1.0,
        },
        {
            "source_research_version": "v0_60",
            "candidate_id": "sample_candidate",
            "entry_timestamp": "2024-01-02T00:45:00",
            "split": "validation",
            "return_r": 0.5,
        },
    ]


def _proxy_rows() -> list[dict[str, object]]:
    return [
        {"time": "2024-01-02T00:00:00", "close": 100.0},
        {"time": "2024-01-02T00:15:00", "close": 101.0},
        {"time": "2024-01-02T00:30:00", "close": 100.5},
        {"time": "2024-01-02T00:45:00", "close": 102.0},
    ]


def _report() -> dict[str, object]:
    return build_xauusd_dxy_conditioned_event_study_v0_68(
        root=ROOT,
        event_records=_events(),
        proxy_rows=_proxy_rows(),
        attempt_mt5_readonly=False,
    )


def test_report_includes_required_diagnostic_fields_and_versions() -> None:
    report = _report()

    assert report["study_version"] == STUDY_VERSION
    assert report["study_status"] in {COMPLETED, COMPLETED_NO_CLEAR_LEADS}
    assert report["source_proxy_ranker_version"] == "v0_66"
    assert report["source_label_design_version"] == "v0_67"
    assert report["selected_proxy_symbol"] == "DXYN"
    assert report["labels_evaluated"] == LABEL_NAMES
    assert report["prior_research_versions_considered"] == ["v0_53", "v0_56", "v0_60", "v0_63"]
    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["event_count"] == 3
    assert isinstance(report["label_conditioned_summary"], dict)
    assert isinstance(report["strongest_diagnostic_observations"], list)
    assert isinstance(report["clear_lead_count"], int)
    assert isinstance(report["clear_leads"], list)


def test_no_strategy_rules_are_created_or_modified() -> None:
    report = _report()

    assert report["safety"]["strategy_rules_created"] is False
    assert report["safety"]["strategy_rules_modified"] is False
    assert report["executable_candidate_created"] is False
    assert report["approved_for_strategy_testing"] is False
    assert "fixed_rules" not in json.dumps(report)


def test_no_buy_sell_or_trade_recommendations_are_output() -> None:
    report = _report()
    text = json.dumps(report).lower()

    assert report["safety"]["trade_signals_output"] is False
    assert report["trade_recommendation_output"] is False
    assert "buy_signal" not in text
    assert "sell_signal" not in text
    assert "recommended_side" not in text


def test_labels_are_not_trade_blockers_or_filter_approvals() -> None:
    report = _report()

    assert report["labels_used_as_trade_blockers"] is False
    assert report["labels_used_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["approved_for_strategy_testing"] is False


def test_no_strategy_testing_oos_retune_threshold_search_or_grid() -> None:
    report = _report()

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False


def test_no_persistent_aligned_csv_or_data_csv_touch() -> None:
    before = {path.name: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}
    report = _report()
    after = {path.name: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}

    assert before == after
    assert report["aligned_dataset_created"] is False
    assert report["data_csv_touched"] is False
    assert report["proxy_readonly_summary"]["alignment_storage"] == "in_memory_only"
    assert report["proxy_readonly_summary"]["persistent_aligned_csv_created"] is False


def test_lookahead_safe_asof_rules_are_respected() -> None:
    report = _report()

    assert report["lookahead_risk_detected"] is False
    assert report["proxy_readonly_summary"]["allowed_join_direction"] == "backward"
    with pytest.raises(ValueError, match="future proxy timestamp"):
        assert_backward_asof_safe("2024-01-02T00:15:00", "2024-01-02T00:30:00")


def test_missing_proxy_data_blocks_without_fabricating_events() -> None:
    report = build_xauusd_dxy_conditioned_event_study_v0_68(
        root=ROOT,
        event_records=_events(),
        proxy_rows=[],
        attempt_mt5_readonly=False,
    )

    assert report["study_status"] == BLOCKED_MISSING_DATA
    assert report["event_count"] == 0
    assert report["recommended_next_step"] == NO_CLEAR_LEAD_NEXT_STEP
    assert "selected_proxy_rows_unavailable" in report["blockers"]


def test_cli_writes_required_report_without_mt5_dependency(tmp_path: Path) -> None:
    output = tmp_path / "reports" / "dxy_event_study.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_dxy_conditioned_event_study_v0_68.py"),
            "--json",
            "--skip-mt5-readonly",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["study_version"] == STUDY_VERSION
    assert output_report["study_status"] == BLOCKED_MISSING_DATA
    assert output_report["aligned_dataset_created"] is False
