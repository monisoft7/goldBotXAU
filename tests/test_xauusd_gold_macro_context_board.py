from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.research.xauusd_gold_macro_context_board import build_gold_macro_context_board, write_gold_macro_context_board

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FIELDS = {
    "board_version",
    "board_status",
    "source_versions_considered",
    "dxy_context_summary",
    "oil_context_summary",
    "context_layers_ready_for_diagnostic_study",
    "context_layers_not_ready",
    "dxy_clear_lead_count",
    "oil_event_study_completed",
    "oil_ready_for_event_study",
    "macro_context_decision",
    "next_research_step",
    "decision_reason",
    "rejected_next_steps",
    "labels_used_as_trade_blockers",
    "labels_used_for_strategy_testing",
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
    "train_validation_only",
    "oos_used",
    "repeated_oos_review",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "executable_candidate_created",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
    "aligned_dataset_created",
    "data_csv_touched",
}

FALSE_SAFETY_FIELDS = [
    "labels_used_as_trade_blockers",
    "labels_used_for_strategy_testing",
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
    "oos_used",
    "repeated_oos_review",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "executable_candidate_created",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
    "live_allowed",
    "trade_recommendation_output",
    "aligned_dataset_created",
    "data_csv_touched",
    "strategy_rules_created",
    "strategy_rules_modified",
    "trade_signals_output",
]


def _copy_input_reports(tmp_path: Path, *, include_oil: bool = True) -> Path:
    reports = tmp_path / "reports"
    reports.mkdir(parents=True)
    shutil.copyfile(
        ROOT / "reports" / "xauusd_dxy_conditioned_event_study_v0_68.json",
        reports / "xauusd_dxy_conditioned_event_study_v0_68.json",
    )
    if include_oil:
        shutil.copyfile(
            ROOT / "reports" / "xauusd_oil_proxy_context_audit_v0_69.json",
            reports / "xauusd_oil_proxy_context_audit_v0_69.json",
        )
        shutil.copyfile(
            ROOT / "reports" / "xauusd_oil_proxy_quality_and_label_design_v0_70.json",
            reports / "xauusd_oil_proxy_quality_and_label_design_v0_70.json",
        )
    return tmp_path


def test_board_contains_required_decision_and_safety_fields() -> None:
    report = build_gold_macro_context_board(ROOT)

    assert REQUIRED_FIELDS <= set(report)
    assert report["board_version"] == "v0_71"
    assert report["board_status"] == "gold_macro_context_board_completed"
    assert report["source_versions_considered"] == ["v0_65", "v0_66", "v0_67", "v0_68", "v0_68_1", "v0_69", "v0_70"]
    assert report["train_validation_only"] is True
    for field in FALSE_SAFETY_FIELDS:
        assert report[field] is False


def test_board_does_not_create_or_modify_strategy_rules() -> None:
    report = build_gold_macro_context_board(ROOT)

    assert report["strategy_rules_created"] is False
    assert report["strategy_rules_modified"] is False
    assert report["executable_candidate_created"] is False
    assert report["macro_context_decision"] == "run_oil_conditioned_event_study_next"


def test_board_does_not_output_recommendation_or_signal_language() -> None:
    report = build_gold_macro_context_board(ROOT)
    text = json.dumps(report, sort_keys=True).lower()

    assert report["trade_recommendation_output"] is False
    assert report["trade_signals_output"] is False
    assert "buy" not in text
    assert "sell" not in text


def test_board_does_not_approve_labels_for_trade_filtering() -> None:
    report = build_gold_macro_context_board(ROOT)

    assert report["labels_used_as_trade_blockers"] is False
    assert report["labels_used_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["approved_for_strategy_testing"] is False


def test_board_does_not_use_oos_or_search_behaviors() -> None:
    report = build_gold_macro_context_board(ROOT)

    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False


def test_board_recommends_oil_event_study_only_when_v0_69_and_v0_70_inputs_present(tmp_path: Path) -> None:
    complete_root = _copy_input_reports(tmp_path / "complete", include_oil=True)
    report = build_gold_macro_context_board(complete_root)

    assert report["oil_ready_for_event_study"] is True
    assert report["next_research_step"] == "v0_72_oil_conditioned_event_study_no_strategy"

    missing_oil_root = _copy_input_reports(tmp_path / "missing_oil", include_oil=False)
    blocked = build_gold_macro_context_board(missing_oil_root)

    assert blocked["board_status"] == "gold_macro_context_board_blocked_missing_inputs"
    assert blocked["oil_ready_for_event_study"] is False
    assert blocked["next_research_step"] != "v0_72_oil_conditioned_event_study_no_strategy"


def test_board_rejects_immediate_new_strategy_creation() -> None:
    report = build_gold_macro_context_board(ROOT)
    rejected_steps = {item["step"]: item["reason"] for item in report["rejected_next_steps"]}

    assert "new_strategy_creation" in rejected_steps
    assert report["next_research_step"] != "new_strategy_creation"
    assert report["approved_for_strategy_testing"] is False


def test_write_report_round_trips_json(tmp_path: Path) -> None:
    output = tmp_path / "reports" / "xauusd_gold_macro_context_board_v0_71.json"

    report = write_gold_macro_context_board(ROOT, output)

    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == report
