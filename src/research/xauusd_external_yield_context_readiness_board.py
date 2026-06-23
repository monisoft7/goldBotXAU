"""External yield context readiness board for XAUUSD research infrastructure."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BOARD_VERSION = "v0_80"
READY_STATUS = "external_yield_context_readiness_completed"
BLOCKED_STATUS = "external_yield_context_readiness_blocked"
READY_DECISION = "ready_for_human_supplied_external_yield_sample_preflight"
BLOCKED_DECISION = "blocked_pending_repair"
READY_NEXT_STEP = "v0_81_human_supplied_external_yield_sample_preflight_no_strategy"

SOURCE_REPORTS: dict[str, str] = {
    "v0_73": "xauusd_yield_context_feasibility_v0_73.json",
    "v0_74": "xauusd_external_yield_dataset_schema_v0_74.json",
    "v0_75": "xauusd_external_yield_sample_validator_v0_75.json",
    "v0_76": "xauusd_external_yield_manual_fixture_ingestion_v0_76.json",
    "v0_77": "xauusd_external_yield_asof_alignment_design_v0_77.json",
    "v0_78": "xauusd_external_yield_label_design_v0_78.json",
    "v0_79": "xauusd_external_yield_label_fixture_application_v0_79.json",
}

STATUS_FIELDS = (
    "audit_status",
    "schema_status",
    "validator_status",
    "ingestion_status",
    "alignment_status",
    "label_design_status",
    "application_status",
)

UNSAFE_TRUE_FLAGS = (
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
    "synthetic_gold_context_real_xauusd_data_used",
)


def _read_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _status_for(report: dict[str, Any]) -> str | None:
    for field in STATUS_FIELDS:
        value = report.get(field)
        if isinstance(value, str):
            return value
    return None


def _source_status_summary(reports: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for version, report in reports.items():
        summary[version] = {
            "status": _status_for(report),
            "recommended_next_step": report.get("recommended_next_step"),
            "safety_flags_closed": _source_safety_closed(report),
        }
    return summary


def _source_safety_closed(report: dict[str, Any]) -> bool:
    unsafe_true = any(report.get(flag) is True for flag in UNSAFE_TRUE_FLAGS)
    train_validation_safe = report.get("train_validation_only", True) is True
    return not unsafe_true and train_validation_safe


def _unsafe_reasons(reports: dict[str, dict[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for version, report in reports.items():
        for flag in UNSAFE_TRUE_FLAGS:
            if report.get(flag) is True:
                reasons.append(f"{version}:{flag}")
        if report.get("train_validation_only", True) is not True:
            reasons.append(f"{version}:train_validation_only_not_true")
    return reasons


def _schema_ready(report: dict[str, Any] | None) -> bool:
    if report is None:
        return False
    return (
        report.get("schema_status") == "external_yield_dataset_schema_completed"
        and bool(report.get("candidate_series"))
        and bool(report.get("required_future_columns"))
        and bool(report.get("required_schema_fields"))
    )


def _validator_ready(report: dict[str, Any] | None) -> bool:
    if report is None:
        return False
    return (
        report.get("validator_status") == "external_yield_sample_validator_completed_with_expected_fixture_rejections"
        and report.get("rejected_record_count", 0) > 0
        and bool(report.get("rejection_reasons"))
    )


def _manual_fixture_ingestion_ready(report: dict[str, Any] | None) -> bool:
    if report is None:
        return False
    return (
        report.get("ingestion_status") == "external_yield_manual_fixture_ingestion_completed_with_expected_rejections"
        and report.get("fixture_source") == "inline_or_test_fixture_only"
        and report.get("dataset_file_created") is False
        and report.get("market_csv_created") is False
        and report.get("data_csv_touched") is False
    )


def _asof_alignment_design_ready(report: dict[str, Any] | None) -> bool:
    if report is None:
        return False
    return (
        report.get("alignment_status") == "external_yield_asof_alignment_design_completed_with_expected_rejections"
        and report.get("no_lookahead_policy_confirmed") is True
        and report.get("backward_asof_only") is True
        and report.get("aligned_dataset_created") is False
    )


def _label_design_ready(report: dict[str, Any] | None) -> bool:
    if report is None:
        return False
    return (
        report.get("label_design_status") == "external_yield_label_design_completed"
        and report.get("label_count") == 12
        and report.get("release_timestamp_policy_required") is True
        and report.get("backward_asof_required") is True
        and report.get("no_lookahead_policy_confirmed") is True
    )


def _fixture_label_application_ready(report: dict[str, Any] | None) -> bool:
    if report is None:
        return False
    labels_requested = report.get("labels_requested", [])
    labels_applied = report.get("labels_applied", [])
    return (
        report.get("application_status") == "external_yield_label_fixture_application_completed_with_not_applicable_labels"
        and isinstance(labels_requested, list)
        and isinstance(labels_applied, list)
        and len(labels_requested) == 12
        and len(labels_applied) == 12
        and report.get("no_lookahead_policy_confirmed") is True
        and report.get("backward_asof_only") is True
        and report.get("aligned_dataset_created") is False
        and report.get("label_dataset_exported") is False
    )


def _not_applicable_labels_accepted(report: dict[str, Any] | None) -> bool:
    if report is None:
        return False
    labels_requested = report.get("labels_requested", [])
    labels_not_applicable = report.get("labels_not_applicable", [])
    return (
        isinstance(labels_requested, list)
        and isinstance(labels_not_applicable, list)
        and set(labels_not_applicable).issubset(set(labels_requested))
        and len(labels_not_applicable) > 0
    )


def _required_preflight_inputs(schema_report: dict[str, Any] | None, label_report: dict[str, Any] | None) -> dict[str, Any]:
    allowed_series = schema_report.get("candidate_series", []) if isinstance(schema_report, dict) else []
    if allowed_series and isinstance(allowed_series[0], dict):
        allowed_series_ids = [item.get("series_id") for item in allowed_series]
    else:
        allowed_series_ids = schema_report.get("allowed_series_ids", []) if isinstance(schema_report, dict) else []

    required_series_by_label = label_report.get("required_series_by_label", {}) if isinstance(label_report, dict) else {}
    return {
        "sample_size": "small_manual_csv_or_jsonl_sample_only",
        "allowed_series_ids": [series for series in allowed_series_ids if series],
        "required_series_by_label": required_series_by_label,
        "required_columns": schema_report.get("required_future_columns", []) if isinstance(schema_report, dict) else [],
        "release_timestamp_required_with_timezone": True,
        "source_name_required": True,
        "api_key_required": False,
        "automated_download_allowed": False,
        "data_csv_allowed": False,
        "xauusd_alignment_allowed_in_v0_81": False,
    }


def build_external_yield_context_readiness_board(root: Path) -> dict[str, Any]:
    reports_dir = root / "reports"
    reports: dict[str, dict[str, Any]] = {}
    missing: list[str] = []

    for version, filename in SOURCE_REPORTS.items():
        path = reports_dir / filename
        if path.exists():
            reports[version] = _read_report(path)
        else:
            missing.append(filename)

    v73 = reports.get("v0_73")
    v74 = reports.get("v0_74")
    v75 = reports.get("v0_75")
    v76 = reports.get("v0_76")
    v77 = reports.get("v0_77")
    v78 = reports.get("v0_78")
    v79 = reports.get("v0_79")

    local_yield_proxy_available = v73.get("local_yield_proxy_available") if isinstance(v73, dict) else None
    external_dataset_required = v73.get("external_dataset_required") if isinstance(v73, dict) else None
    schema_ready = _schema_ready(v74)
    validator_ready = _validator_ready(v75)
    manual_fixture_ingestion_ready = _manual_fixture_ingestion_ready(v76)
    asof_alignment_design_ready = _asof_alignment_design_ready(v77)
    label_design_ready = _label_design_ready(v78)
    fixture_label_application_ready = _fixture_label_application_ready(v79)
    not_applicable_labels_accepted = _not_applicable_labels_accepted(v79)
    unsafe_reasons = _unsafe_reasons(reports)

    readiness_checks = {
        "local_yield_proxy_unavailable": local_yield_proxy_available is False,
        "external_dataset_required": external_dataset_required is True,
        "schema_ready": schema_ready,
        "validator_ready": validator_ready,
        "manual_fixture_ingestion_ready": manual_fixture_ingestion_ready,
        "asof_alignment_design_ready": asof_alignment_design_ready,
        "label_design_ready": label_design_ready,
        "fixture_label_application_ready": fixture_label_application_ready,
        "not_applicable_labels_accepted": not_applicable_labels_accepted,
        "source_reports_present": not missing,
        "source_safety_flags_closed": not unsafe_reasons,
    }
    ready = all(readiness_checks.values())

    if ready:
        readiness_status = READY_STATUS
        readiness_decision = READY_DECISION
        readiness_reason = (
            "v0_73 through v0_79 are present, external yield context infrastructure is complete, "
            "not-applicable fixture labels are expected, and all safety flags remain closed."
        )
        recommended_next_step = READY_NEXT_STEP
    else:
        blockers = [name for name, passed in readiness_checks.items() if not passed]
        readiness_status = BLOCKED_STATUS
        readiness_decision = BLOCKED_DECISION
        readiness_reason = "Readiness blocked by: " + ", ".join(blockers + unsafe_reasons)
        recommended_next_step = "repair_" + (blockers[0] if blockers else unsafe_reasons[0].replace(":", "_"))

    return {
        "board_version": BOARD_VERSION,
        "readiness_status": readiness_status,
        "source_versions_considered": list(SOURCE_REPORTS),
        "source_reports_present": sorted(reports),
        "missing_source_reports": missing,
        "source_status_summary": _source_status_summary(reports),
        "local_yield_proxy_available": local_yield_proxy_available,
        "external_dataset_required": external_dataset_required,
        "schema_ready": schema_ready,
        "validator_ready": validator_ready,
        "manual_fixture_ingestion_ready": manual_fixture_ingestion_ready,
        "asof_alignment_design_ready": asof_alignment_design_ready,
        "label_design_ready": label_design_ready,
        "fixture_label_application_ready": fixture_label_application_ready,
        "not_applicable_labels_accepted": not_applicable_labels_accepted,
        "readiness_decision": readiness_decision,
        "readiness_reason": readiness_reason,
        "required_preflight_inputs_for_v0_81": _required_preflight_inputs(v74, v78),
        "rejected_next_steps": [
            "strategy_testing",
            "oos_review",
            "retune",
            "threshold_search",
            "parameter_grid",
            "trade_filtering_approval",
            "xauusd_alignment_in_v0_81_without_later_board",
            "external_api_download",
            "persistent_market_csv_creation",
            "demo_or_live_execution",
        ],
        "external_api_called": False,
        "external_data_downloaded": False,
        "dataset_file_created": False,
        "market_csv_created": False,
        "data_csv_touched": False,
        "real_xauusd_data_used": False,
        "real_yield_data_used": False,
        "aligned_dataset_created": False,
        "label_dataset_exported": False,
        "no_lookahead_policy_confirmed": True,
        "backward_asof_policy_confirmed": True,
        "labels_used_as_trade_blockers": False,
        "labels_used_for_strategy_testing": False,
        "approved_for_strategy_testing": False,
        "approved_for_trade_filtering": False,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "executable_candidate_created": False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "trade_recommendation_output": False,
        "trade_signals_output": False,
        "strategy_rules_created": False,
        "strategy_rules_modified": False,
        "unsafe_source_reasons": unsafe_reasons,
        "recommended_next_step": recommended_next_step,
    }


def write_external_yield_context_readiness_board(root: Path) -> dict[str, Any]:
    report = build_external_yield_context_readiness_board(root)
    output_path = root / "reports" / "xauusd_external_yield_context_readiness_board_v0_80.json"
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
