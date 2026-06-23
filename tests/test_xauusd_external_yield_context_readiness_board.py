from __future__ import annotations

import json
from pathlib import Path

from src.research.xauusd_external_yield_context_readiness_board import (
    BLOCKED_STATUS,
    READY_DECISION,
    READY_NEXT_STEP,
    READY_STATUS,
    SOURCE_REPORTS,
    build_external_yield_context_readiness_board,
)

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_REPORT_FIELDS = {
    "board_version",
    "readiness_status",
    "source_versions_considered",
    "source_reports_present",
    "missing_source_reports",
    "source_status_summary",
    "local_yield_proxy_available",
    "external_dataset_required",
    "schema_ready",
    "validator_ready",
    "manual_fixture_ingestion_ready",
    "asof_alignment_design_ready",
    "label_design_ready",
    "fixture_label_application_ready",
    "not_applicable_labels_accepted",
    "readiness_decision",
    "readiness_reason",
    "required_preflight_inputs_for_v0_81",
    "rejected_next_steps",
    "external_api_called",
    "external_data_downloaded",
    "dataset_file_created",
    "market_csv_created",
    "data_csv_touched",
    "real_xauusd_data_used",
    "real_yield_data_used",
    "aligned_dataset_created",
    "label_dataset_exported",
    "no_lookahead_policy_confirmed",
    "backward_asof_policy_confirmed",
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
    "recommended_next_step",
}

FALSE_SAFETY_FIELDS = [
    "external_api_called",
    "external_data_downloaded",
    "dataset_file_created",
    "market_csv_created",
    "data_csv_touched",
    "real_xauusd_data_used",
    "real_yield_data_used",
    "aligned_dataset_created",
    "label_dataset_exported",
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
    "trade_signals_output",
    "strategy_rules_created",
    "strategy_rules_modified",
]


def _copy_source_reports(tmp_path: Path) -> Path:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True)
    for filename in SOURCE_REPORTS.values():
        source = ROOT / "reports" / filename
        (reports_dir / filename).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def _load_report(root: Path, version: str) -> dict:
    path = root / "reports" / SOURCE_REPORTS[version]
    return json.loads(path.read_text(encoding="utf-8"))


def _write_report(root: Path, version: str, report: dict) -> None:
    path = root / "reports" / SOURCE_REPORTS[version]
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_board_completes_when_all_source_reports_exist_and_are_safe() -> None:
    report = build_external_yield_context_readiness_board(ROOT)

    assert report["readiness_status"] == READY_STATUS
    assert report["readiness_decision"] == READY_DECISION
    assert report["recommended_next_step"] == READY_NEXT_STEP
    assert report["source_versions_considered"] == ["v0_73", "v0_74", "v0_75", "v0_76", "v0_77", "v0_78", "v0_79"]
    assert report["source_reports_present"] == ["v0_73", "v0_74", "v0_75", "v0_76", "v0_77", "v0_78", "v0_79"]
    assert report["missing_source_reports"] == []
    assert report["local_yield_proxy_available"] is False
    assert report["external_dataset_required"] is True
    assert report["schema_ready"] is True
    assert report["validator_ready"] is True
    assert report["manual_fixture_ingestion_ready"] is True
    assert report["asof_alignment_design_ready"] is True
    assert report["label_design_ready"] is True
    assert report["fixture_label_application_ready"] is True


def test_board_blocks_when_a_required_source_report_is_missing(tmp_path: Path) -> None:
    root = _copy_source_reports(tmp_path)
    (root / "reports" / SOURCE_REPORTS["v0_77"]).unlink()

    report = build_external_yield_context_readiness_board(root)

    assert report["readiness_status"] == BLOCKED_STATUS
    assert report["readiness_decision"] == "blocked_pending_repair"
    assert SOURCE_REPORTS["v0_77"] in report["missing_source_reports"]
    assert report["recommended_next_step"] == "repair_asof_alignment_design_ready"


def test_board_blocks_if_any_source_report_indicates_unsafe_usage(tmp_path: Path) -> None:
    unsafe_flags = [
        "external_api_called",
        "external_data_downloaded",
        "data_csv_touched",
        "approved_for_strategy_testing",
        "oos_used",
        "order_send_called",
    ]

    for flag in unsafe_flags:
        root = _copy_source_reports(tmp_path / flag)
        source_report = _load_report(root, "v0_79")
        source_report[flag] = True
        _write_report(root, "v0_79", source_report)

        report = build_external_yield_context_readiness_board(root)

        assert report["readiness_status"] == BLOCKED_STATUS
        assert f"v0_79:{flag}" in report["unsafe_source_reasons"]


def test_not_applicable_labels_from_v0_79_do_not_block_readiness() -> None:
    report = build_external_yield_context_readiness_board(ROOT)

    assert report["not_applicable_labels_accepted"] is True
    assert report["fixture_label_application_ready"] is True
    assert report["readiness_status"] == READY_STATUS


def test_board_does_not_use_real_or_external_data_surfaces() -> None:
    report = build_external_yield_context_readiness_board(ROOT)

    assert report["real_xauusd_data_used"] is False
    assert report["real_yield_data_used"] is False
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["data_csv_touched"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["aligned_dataset_created"] is False
    assert report["label_dataset_exported"] is False


def test_board_does_not_approve_labels_as_strategy_or_trade_filtering() -> None:
    report = build_external_yield_context_readiness_board(ROOT)

    assert report["labels_used_as_trade_blockers"] is False
    assert report["labels_used_for_strategy_testing"] is False
    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["strategy_rules_created"] is False
    assert report["strategy_rules_modified"] is False
    assert report["trade_signals_output"] is False


def test_board_does_not_perform_oos_retune_search_grid_or_execution() -> None:
    report = build_external_yield_context_readiness_board(ROOT)

    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False


def test_report_includes_all_required_readiness_and_safety_fields() -> None:
    report = build_external_yield_context_readiness_board(ROOT)

    assert REQUIRED_REPORT_FIELDS.issubset(report)
    for field in FALSE_SAFETY_FIELDS:
        assert report[field] is False
    assert report["train_validation_only"] is True
    assert report["no_lookahead_policy_confirmed"] is True
    assert report["backward_asof_policy_confirmed"] is True


def test_required_preflight_inputs_describe_future_manual_sample_only() -> None:
    report = build_external_yield_context_readiness_board(ROOT)
    preflight = report["required_preflight_inputs_for_v0_81"]

    assert preflight["sample_size"] == "small_manual_csv_or_jsonl_sample_only"
    assert preflight["allowed_series_ids"] == ["DGS10", "DGS2", "DFII10", "DFII5", "T10YIE", "DFF"]
    assert preflight["required_columns"] == ["series_id", "observation_date", "value", "source_name"]
    assert preflight["release_timestamp_required_with_timezone"] is True
    assert preflight["source_name_required"] is True
    assert preflight["api_key_required"] is False
    assert preflight["automated_download_allowed"] is False
    assert preflight["data_csv_allowed"] is False
    assert preflight["xauusd_alignment_allowed_in_v0_81"] is False
