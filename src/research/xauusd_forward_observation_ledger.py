"""Aggregate read-only XAUUSD forward observation summaries into a sample ledger."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research.xauusd_forward_observation_runner import ALLOWED_TIMEFRAMES, CANDIDATE_ID

LEDGER_VERSION = "v0_35"
DEFAULT_INPUT_REPORTS = [
    Path("reports") / "xauusd_forward_observation_consolidated_v0_34_2.json",
]
DEFAULT_OUTPUT = Path("reports") / "xauusd_forward_observation_ledger_v0_35.json"
NEXT_RECOMMENDED_STEP = "v0_36 collect additional read-only forward observation samples, no execution"

MIN_INDEPENDENT_OBSERVATION_SESSIONS = 3
MIN_UNIQUE_RECORDS_PER_TIMEFRAME = 3
QUALITY_GATE_STATUSES = [
    "insufficient_samples",
    "continue_forward_observation",
    "ready_for_demo_preflight_review",
    "forward_behavior_failed_review",
]

RAW_MARKET_FIELD_SET = {"open", "high", "low", "close"}
RAW_MARKET_CONTAINER_KEYS = {
    "raw_market_data",
    "raw_ohlc_rows",
    "ohlc_rows",
    "market_rows",
    "csv_rows",
    "normalized_csv_rows",
}
RECORD_FIELDS = [
    "timestamp",
    "candidate_id",
    "timeframe",
    "observed_reference_block",
    "observed_response_block",
    "compression_label",
    "expansion_observed",
    "rule_match_status",
    "observation_status",
    "notes",
]


def build_xauusd_forward_observation_ledger_v0_35(
    *,
    input_consolidated_report_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    report_paths = [Path(path) for path in (input_consolidated_report_paths or DEFAULT_INPUT_REPORTS)]
    blockers: list[str] = []
    loaded_reports: list[tuple[Path, dict[str, Any]]] = []

    missing_reports = [str(path) for path in report_paths if not path.exists()]
    if missing_reports:
        blockers.append("consolidated_forward_observation_reports_missing")

    if not missing_reports:
        for path in report_paths:
            report, errors = _read_json_object(path, f"consolidated_forward_observation_report:{path}")
            blockers.extend(errors)
            if report is not None:
                loaded_reports.append((path, report))

    for path, report in loaded_reports:
        blockers.extend(_consolidated_report_blockers(path, report))

    unique_records = [] if blockers else _deduped_ledger_records(loaded_reports)
    timeframes_observed = sorted({str(record["timeframe"]) for record in unique_records})
    counts_by_timeframe = {
        timeframe: sum(1 for record in unique_records if record["timeframe"] == timeframe)
        for timeframe in timeframes_observed
    }
    expansion_observed_count = sum(1 for record in unique_records if record.get("expansion_observed") is True)
    no_expansion_observed_count = sum(1 for record in unique_records if record.get("expansion_observed") is False)
    independent_observation_session_count = 0 if blockers else len(_dedupe([str(path) for path, _ in loaded_reports]))
    quality_gate_status = _quality_gate_status(
        blockers=blockers,
        unique_records=unique_records,
        counts_by_timeframe=counts_by_timeframe,
        independent_observation_session_count=independent_observation_session_count,
    )

    return {
        "ledger_version": LEDGER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "ledger_status": "completed" if not blockers else "blocked",
        "input_consolidated_reports": [str(path) for path in report_paths],
        "raw_market_data_embedded": False,
        "total_unique_journal_records": len(unique_records),
        "timeframes_observed": timeframes_observed,
        "journal_record_count_by_timeframe": counts_by_timeframe,
        "independent_observation_session_count": independent_observation_session_count,
        "expansion_observed_count": expansion_observed_count,
        "no_expansion_observed_count": no_expansion_observed_count,
        "ledger_records": unique_records,
        "quality_gate_status": quality_gate_status,
        "quality_gate_status_options": QUALITY_GATE_STATUSES,
        "minimum_demo_preflight_review_requirements": {
            "multiple_independent_observation_sessions": {
                "required": True,
                "minimum_count": MIN_INDEPENDENT_OBSERVATION_SESSIONS,
                "current_count": independent_observation_session_count,
            },
            "both_m5_and_m10_covered": {
                "required": True,
                "required_timeframes": ALLOWED_TIMEFRAMES,
                "current_timeframes": timeframes_observed,
            },
            "minimum_unique_records_per_timeframe": {
                "required": True,
                "minimum_count": MIN_UNIQUE_RECORDS_PER_TIMEFRAME,
                "current_counts": counts_by_timeframe,
            },
            "no_schema_or_data_blockers": not bool(blockers),
            "no_rule_changes": True,
            "no_oos_repeat": True,
            "no_execution_path_introduced": True,
        },
        "blockers": _dedupe(blockers),
        "demo_preflight_allowed": False,
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


def save_xauusd_forward_observation_ledger(
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


def _consolidated_report_blockers(path: Path, report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    label = _path_label(path)

    if report.get("candidate_id") != CANDIDATE_ID:
        blockers.append(f"{label}_candidate_id_mismatch")
    if report.get("consolidation_status") != "completed":
        blockers.append(f"{label}_consolidation_status_not_completed")
    if report.get("raw_market_data_embedded") is not False:
        blockers.append(f"{label}_raw_market_data_embedded_not_false")
    if _contains_embedded_raw_market_data(report):
        blockers.append(f"{label}_raw_market_data_payload_detected")
    if report.get("blockers") != []:
        blockers.append(f"{label}_has_blockers")

    for key in (
        "mt5_called",
        "market_data_exported",
        "execution_allowed",
        "demo_allowed",
        "live_allowed",
        "order_send_allowed",
        "order_check_allowed",
    ):
        if report.get(key) is not False:
            blockers.append(f"{label}_{key}_not_false")
    if report.get("repeated_oos_review") is not False:
        blockers.append(f"{label}_repeated_oos_review_not_false")
    if report.get("candidate_rules_modified") is not False:
        blockers.append(f"{label}_candidate_rules_modified_not_false")

    safety = report.get("safety_state", {})
    if not isinstance(safety, dict):
        blockers.append(f"{label}_safety_state_not_object")
    else:
        if safety.get("local_read_only") is not True:
            blockers.append(f"{label}_safety_state_local_read_only_not_true")
        for key in (
            "raw_market_data_embedded",
            "mt5_called",
            "market_data_exported",
            "execution_allowed",
            "demo_allowed",
            "live_allowed",
            "order_send_allowed",
            "order_check_allowed",
            "execution_queue_allowed",
            "recommendation_output_allowed",
            "directional_instruction_output_allowed",
            "trade_recommendation_output_allowed",
            "new_oos_evaluation_allowed",
            "oos_repeat_allowed",
            "candidate_rules_modified",
            "threshold_search_allowed",
            "parameter_grid_allowed",
            "parameter_optimization_allowed",
            "retune_allowed",
        ):
            if safety.get(key) is not False:
                blockers.append(f"{label}_safety_state_{key}_not_false")

    rules_lock = report.get("candidate_rules_lock", {})
    if not isinstance(rules_lock, dict):
        blockers.append(f"{label}_candidate_rules_lock_not_object")
    else:
        for key in (
            "rule_change_allowed",
            "threshold_search_allowed",
            "parameter_grid_allowed",
            "parameter_optimization_allowed",
            "retune_allowed",
        ):
            if rules_lock.get(key) is not False:
                blockers.append(f"{label}_candidate_rules_lock_{key}_not_false")

    for record in report.get("neutral_journal_records", []):
        if not isinstance(record, dict):
            blockers.append(f"{label}_neutral_journal_record_not_object")
            continue
        if record.get("candidate_id") != CANDIDATE_ID:
            blockers.append(f"{label}_journal_record_candidate_id_mismatch")
        if _record_timeframe(record) not in ALLOWED_TIMEFRAMES:
            blockers.append(f"{label}_journal_record_timeframe_missing_or_not_allowed")
    return blockers


def _deduped_ledger_records(loaded_reports: list[tuple[Path, dict[str, Any]]]) -> list[dict[str, Any]]:
    records_by_key: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for path, report in loaded_reports:
        for record in report.get("neutral_journal_records", []):
            if not isinstance(record, dict):
                continue
            timeframe = _record_timeframe(record)
            if timeframe is None:
                continue
            ledger_record = {field: record.get(field) for field in RECORD_FIELDS if field in record}
            ledger_record["timeframe"] = timeframe
            ledger_record["source_consolidated_report"] = str(path)
            key = (
                str(ledger_record.get("candidate_id")),
                str(ledger_record.get("timestamp")),
                str(ledger_record.get("timeframe")),
                str(ledger_record.get("observed_reference_block")),
                str(ledger_record.get("observed_response_block")),
            )
            records_by_key.setdefault(key, ledger_record)
    return [records_by_key[key] for key in sorted(records_by_key)]


def _quality_gate_status(
    *,
    blockers: list[str],
    unique_records: list[dict[str, Any]],
    counts_by_timeframe: dict[str, int],
    independent_observation_session_count: int,
) -> str:
    if blockers:
        return "forward_behavior_failed_review"
    if not unique_records:
        return "insufficient_samples"
    has_required_sessions = independent_observation_session_count >= MIN_INDEPENDENT_OBSERVATION_SESSIONS
    has_required_timeframes = all(timeframe in counts_by_timeframe for timeframe in ALLOWED_TIMEFRAMES)
    has_required_records = all(
        counts_by_timeframe.get(timeframe, 0) >= MIN_UNIQUE_RECORDS_PER_TIMEFRAME
        for timeframe in ALLOWED_TIMEFRAMES
    )
    if has_required_sessions and has_required_timeframes and has_required_records:
        return "ready_for_demo_preflight_review"
    if has_required_timeframes:
        return "insufficient_samples"
    return "continue_forward_observation"


def _contains_embedded_raw_market_data(value: Any) -> bool:
    if isinstance(value, dict):
        keys = set(value)
        if RAW_MARKET_FIELD_SET.issubset(keys):
            return True
        if keys.intersection(RAW_MARKET_CONTAINER_KEYS):
            return True
        return any(_contains_embedded_raw_market_data(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_embedded_raw_market_data(item) for item in value)
    return False


def _record_timeframe(record: dict[str, Any]) -> str | None:
    timeframe = record.get("timeframe")
    if timeframe in ALLOWED_TIMEFRAMES:
        return str(timeframe)
    notes = str(record.get("notes", ""))
    match = re.search(r"(?:^|[;\s])timeframe=(M5|M10)(?:[;\s]|$)", notes)
    return match.group(1) if match else None


def _path_label(path: Path) -> str:
    return path.stem.replace("-", "_")


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
