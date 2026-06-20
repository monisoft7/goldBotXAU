"""Consolidate local read-only XAUUSD forward observation journal reports."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research.xauusd_forward_observation_runner import ALLOWED_TIMEFRAMES, CANDIDATE_ID

CONSOLIDATION_VERSION = "v0_34_2"
DEFAULT_ADAPTER_PROTOCOL = Path("reports") / "xauusd_forward_observation_schema_adapter_protocol_v0_34_1.json"
DEFAULT_RUNNER_PROTOCOL = Path("reports") / "xauusd_forward_observation_runner_protocol_v0_33.json"
DEFAULT_INPUT_REPORTS = [
    Path("reports") / "xauusd_forward_observation_m5_normalized_v0_34_2.json",
    Path("reports") / "xauusd_forward_observation_m10_normalized_v0_34_2.json",
]
DEFAULT_OUTPUT = Path("reports") / "xauusd_forward_observation_consolidated_v0_34_2.json"
NEXT_RECOMMENDED_STEP = "v0_35 collect more read-only forward observation samples over multiple sessions, no execution"
LOCAL_FORWARD_MODE = "local_read_only_forward_journal"
MISSING_REPORTS_BLOCKER = "blocked_missing_local_forward_journal_reports"

RAW_MARKET_FIELDS = {
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "source",
    "timestamp_utc",
    "symbol",
    "timeframe",
}
JOURNAL_RECORD_FIELDS = [
    "timestamp",
    "candidate_id",
    "observed_reference_block",
    "observed_response_block",
    "compression_label",
    "expansion_observed",
    "rule_match_status",
    "observation_status",
    "notes",
]


def build_xauusd_forward_observation_consolidation_v0_34_2(
    *,
    input_report_paths: list[str | Path] | None = None,
    adapter_protocol_path: str | Path = DEFAULT_ADAPTER_PROTOCOL,
    runner_protocol_path: str | Path = DEFAULT_RUNNER_PROTOCOL,
) -> dict[str, Any]:
    adapter_path = Path(adapter_protocol_path)
    runner_path = Path(runner_protocol_path)
    report_paths = [Path(path) for path in (input_report_paths or DEFAULT_INPUT_REPORTS)]

    adapter_protocol, adapter_errors = _read_json_object(adapter_path, "v0_34_1_adapter_protocol")
    runner_protocol, runner_errors = _read_json_object(runner_path, "v0_33_runner_protocol")
    blockers = [*adapter_errors, *runner_errors]
    missing_reports = [str(path) for path in report_paths if not path.exists()]
    if missing_reports:
        blockers.append(MISSING_REPORTS_BLOCKER)

    if adapter_protocol is not None:
        blockers.extend(_adapter_protocol_blockers(adapter_protocol))
    if runner_protocol is not None:
        blockers.extend(_runner_protocol_blockers(runner_protocol))

    input_reports: list[dict[str, Any]] = []
    input_report_errors: list[str] = []
    if not missing_reports:
        for path in report_paths:
            report, errors = _read_json_object(path, f"local_forward_journal_report:{path}")
            input_report_errors.extend(errors)
            if report is not None:
                input_reports.append(report)
        blockers.extend(input_report_errors)

    report_blockers: list[str] = []
    for report in input_reports:
        report_blockers.extend(_input_report_blockers(report))
    blockers.extend(report_blockers)

    neutral_records = [] if blockers else _neutral_records(input_reports)
    timeframes_observed = [] if blockers else _timeframes_observed(neutral_records, report_paths)
    counts_by_timeframe = (
        {timeframe: _count_records_for_timeframe(neutral_records, timeframe) for timeframe in timeframes_observed}
        if not blockers
        else {}
    )
    expansion_observed_count = sum(1 for record in neutral_records if record.get("expansion_observed") is True)
    no_expansion_observed_count = sum(1 for record in neutral_records if record.get("expansion_observed") is False)

    return {
        "consolidation_version": CONSOLIDATION_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "consolidation_status": "completed" if not blockers else MISSING_REPORTS_BLOCKER if missing_reports else "blocked",
        "observation_mode": LOCAL_FORWARD_MODE,
        "input_artifact_interpretation": "local_read_only_forward_observation_artifacts_not_synthetic_strategy_proof",
        "source_reports": {
            "adapter_protocol": str(adapter_path),
            "runner_protocol": str(runner_path),
            "local_forward_journal_reports": [str(path) for path in report_paths],
        },
        "total_input_reports": 0 if blockers else len(input_reports),
        "missing_input_reports": missing_reports,
        "timeframes_observed": timeframes_observed,
        "journal_record_count_by_timeframe": counts_by_timeframe,
        "total_journal_record_count": len(neutral_records),
        "expansion_observed_count": expansion_observed_count,
        "no_expansion_observed_count": no_expansion_observed_count,
        "neutral_journal_records": neutral_records,
        "blockers": _dedupe(blockers),
        "observation_quality_status": "insufficient_sample_for_quality_gate",
        "raw_market_data_embedded": False,
        "mt5_called": False,
        "market_data_exported": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
        "candidate_rules_lock": {
            "rule_change_allowed": False,
            "threshold_search_allowed": False,
            "parameter_grid_allowed": False,
            "parameter_optimization_allowed": False,
            "retune_allowed": False,
        },
        "non_actions_performed": {
            "mt5_called": False,
            "market_data_exported": False,
            "new_backtest_evaluated": False,
            "new_oos_run_performed": False,
            "repeated_oos_review": False,
            "candidate_rules_changed": False,
            "new_strategy_variant_created": False,
        },
        "safety_state": _safety_state(),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


def save_xauusd_forward_observation_consolidation(
    report: dict[str, Any],
    output_path: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json_object(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_missing: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{label}_invalid_json: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{label}_not_object: {path}"]
    return payload, []


def _adapter_protocol_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if report.get("adapter_version") != "v0_34_1":
        blockers.append("adapter_protocol_version_not_v0_34_1")
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("adapter_protocol_candidate_id_mismatch")
    if report.get("adapter_status") != "framework_ready":
        blockers.append("adapter_protocol_status_not_framework_ready")
    if report.get("expected_output_schema") is None:
        blockers.append("adapter_protocol_expected_output_schema_missing")
    for key in ("mt5_called", "data_exported_from_mt5", "execution_allowed", "demo_allowed", "live_allowed"):
        if report.get(key) is not False:
            blockers.append(f"adapter_protocol_{key}_not_false")
    if report.get("repeated_oos_review") is not False:
        blockers.append("adapter_protocol_repeated_oos_review_not_false")
    if report.get("candidate_rules_modified") is not False:
        blockers.append("adapter_protocol_candidate_rules_modified_not_false")
    return blockers


def _runner_protocol_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if report.get("runner_version") != "v0_33":
        blockers.append("runner_protocol_version_not_v0_33")
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("runner_protocol_candidate_id_mismatch")
    if report.get("future_mode") != "journal_only":
        blockers.append("runner_protocol_future_mode_not_journal_only")
    if report.get("allowed_timeframes") != ALLOWED_TIMEFRAMES:
        blockers.append("runner_protocol_allowed_timeframes_not_m5_m10")
    for key in ("execution_allowed", "demo_allowed", "live_allowed", "repeated_oos_review", "candidate_rules_modified"):
        if report.get(key) is not False:
            blockers.append(f"runner_protocol_{key}_not_false")
    return blockers


def _input_report_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("local_forward_journal_candidate_id_mismatch")
    if report.get("blockers") != []:
        blockers.append("local_forward_journal_report_has_blockers")
    if report.get("synthetic_fixture_journal_record_count") != len(report.get("synthetic_fixture_journal_records", [])):
        blockers.append("local_forward_journal_record_count_mismatch")
    for key in ("execution_allowed", "demo_allowed", "live_allowed", "repeated_oos_review", "candidate_rules_modified"):
        if report.get(key) is not False:
            blockers.append(f"local_forward_journal_{key}_not_false")
    safety = report.get("safety", {})
    if not isinstance(safety, dict):
        blockers.append("local_forward_journal_safety_not_object")
    else:
        for key in (
            "order_send_allowed",
            "order_check_allowed",
            "execution_queue_allowed",
            "new_oos_evaluation_allowed",
            "oos_repeat_allowed",
            "threshold_search_allowed",
            "parameter_grid_allowed",
            "parameter_optimization_allowed",
            "retune_allowed",
        ):
            if safety.get(key) is not False:
                blockers.append(f"local_forward_journal_safety_{key}_not_false")
    return blockers


def _neutral_records(input_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for report in input_reports:
        for record in report.get("synthetic_fixture_journal_records", []):
            if isinstance(record, dict):
                neutral_record = {field: record.get(field) for field in JOURNAL_RECORD_FIELDS if field in record}
                neutral_record["notes"] = _local_observation_notes(str(neutral_record.get("notes", "")))
                records.append(neutral_record)
    return records


def _timeframes_observed(records: list[dict[str, Any]], report_paths: list[Path]) -> list[str]:
    observed = {_record_timeframe(record) for record in records}
    observed.discard(None)
    if observed:
        return sorted(str(timeframe) for timeframe in observed)
    inferred = {_timeframe_from_path(path) for path in report_paths}
    inferred.discard(None)
    return sorted(str(timeframe) for timeframe in inferred)


def _count_records_for_timeframe(records: list[dict[str, Any]], timeframe: str) -> int:
    return sum(1 for record in records if _record_timeframe(record) == timeframe)


def _record_timeframe(record: dict[str, Any]) -> str | None:
    notes = str(record.get("notes", ""))
    match = re.search(r"(?:^|[;\s])timeframe=(M5|M10)(?:[;\s]|$)", notes)
    return match.group(1) if match else None


def _local_observation_notes(notes: str) -> str:
    timeframe = _record_timeframe({"notes": notes})
    parts = ["local read-only forward observation journal record"]
    if timeframe is not None:
        parts.append(f"timeframe={timeframe}")
    parts.append("data_quality=local normalized csv")
    parts.append("risk_note=observation only")
    return "; ".join(parts)


def _timeframe_from_path(path: Path) -> str | None:
    stem = path.stem.lower()
    if "_m5_" in f"_{stem}_":
        return "M5"
    if "_m10_" in f"_{stem}_":
        return "M10"
    return None


def _safety_state() -> dict[str, bool]:
    return {
        "local_read_only": True,
        "raw_market_data_embedded": False,
        "mt5_called": False,
        "market_data_exported": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "execution_queue_allowed": False,
        "recommendation_output_allowed": False,
        "directional_instruction_output_allowed": False,
        "trade_recommendation_output_allowed": False,
        "new_oos_evaluation_allowed": False,
        "oos_repeat_allowed": False,
        "candidate_rules_modified": False,
        "threshold_search_allowed": False,
        "parameter_grid_allowed": False,
        "parameter_optimization_allowed": False,
        "retune_allowed": False,
        "martingale_allowed": False,
        "averaging_into_loss_allowed": False,
    }


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
