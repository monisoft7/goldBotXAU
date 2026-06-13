"""v0_31 read-only paper-shadow journal framework for synthetic fixtures."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "v0_31"
CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"
DEFAULT_GOVERNANCE_REPORT = Path("reports") / "xauusd_post_oos_governance_v0_30.json"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_paper_shadow_journal_protocol_v0_31.json"
NEXT_RECOMMENDED_STEP = "v0_32 read-only forward observation data export plan, no execution"

RECORD_FIELDS = [
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


def build_xauusd_paper_shadow_journal_protocol_v0_31(
    *,
    governance_report_path: str | Path = DEFAULT_GOVERNANCE_REPORT,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    fixture_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    governance_file = Path(governance_report_path)
    candidate_file = Path(candidate_report_path)

    governance, governance_errors = _read_json_object(governance_file, "post_oos_governance")
    candidate_report, candidate_errors = _read_json_object(candidate_file, "candidate_report")
    blockers = [*governance_errors, *candidate_errors]
    if governance is not None:
        blockers.extend(_governance_blockers(governance))
    if candidate_report is not None:
        blockers.extend(_candidate_blockers(candidate_report))

    fixed_rules = _fixed_rules(candidate_report)
    records = [] if blockers else build_neutral_journal_records(fixture_rows or _default_synthetic_fixture_rows(), fixed_rules)
    status = "framework_ready_not_started" if not blockers else "blocked_framework_prerequisites_not_met"

    return {
        "protocol_version": PROTOCOL_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "source_reports": {
            "post_oos_governance": str(governance_file),
            "candidate_report": str(candidate_file),
        },
        "journal_status": status,
        "data_source_status": "synthetic_fixtures_only",
        "real_market_observation_started": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
        "blockers": blockers,
        "journal_record_schema": RECORD_FIELDS,
        "synthetic_fixture_records": records,
        "synthetic_fixture_record_count": len(records),
        "neutral_language_policy": {
            "allowed_record_terms": [
                "observation",
                "rule match",
                "expansion observed",
                "no expansion observed",
                "journal record",
            ],
            "recommendation_language_allowed": False,
            "directional_instruction_language_allowed": False,
        },
        "candidate_rules_lock": {
            "fixed_rules_hash_sha256": _stable_hash(fixed_rules) if fixed_rules else None,
            "fixed_rules_source": str(candidate_file),
            "rule_change_allowed": False,
            "threshold_search_allowed": False,
            "parameter_grid_allowed": False,
            "parameter_optimization_allowed": False,
            "retune_allowed": False,
        },
        "non_actions_performed": {
            "new_oos_run_performed": False,
            "new_data_evaluated": False,
            "real_market_observation_started": False,
            "candidate_rules_changed": False,
            "new_variant_created": False,
        },
        "safety": _safety_summary(),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


def build_neutral_journal_records(
    fixture_rows: list[dict[str, Any]],
    fixed_rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rules = fixed_rules or _default_fixed_rules()
    records: list[dict[str, Any]] = []
    for row in fixture_rows:
        reference_block = str(row.get("observed_reference_block", ""))
        response_block = str(row.get("observed_response_block", ""))
        reference_range = _as_float(row.get("reference_range"))
        response_range = _as_float(row.get("response_range"))
        blocks_allowed = (
            reference_block in rules.get("reference_blocks", [])
            and response_block in rules.get("response_blocks", [])
        )
        ranges_available = reference_range is not None and response_range is not None
        expansion_observed = bool(ranges_available and response_range > reference_range)
        rule_match_status = "rule match" if blocks_allowed and ranges_available else "rule not matched"
        observation_status = "expansion observed" if expansion_observed else "no expansion observed"
        if not blocks_allowed:
            observation_status = "observation incomplete"

        records.append(
            {
                "timestamp": str(row.get("timestamp", "")),
                "candidate_id": CANDIDATE_ID,
                "observed_reference_block": reference_block,
                "observed_response_block": response_block,
                "compression_label": str(row.get("compression_label", "lowest range reference block")),
                "expansion_observed": expansion_observed,
                "rule_match_status": rule_match_status,
                "observation_status": observation_status,
                "notes": str(row.get("notes", "synthetic fixture journal record")),
            }
        )
    return records


def save_xauusd_paper_shadow_journal_protocol(
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


def _governance_blockers(governance: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if governance.get("candidate_id") != CANDIDATE_ID:
        blockers.append("governance_candidate_id_mismatch")
    if governance.get("governance_status") != "post_oos_governance_created_design_only":
        blockers.append("governance_status_not_ready")
    if governance.get("one_time_oos_review_completed") is not True:
        blockers.append("one_time_oos_review_not_completed")
    if governance.get("repeat_oos_review_allowed") is not False:
        blockers.append("governance_repeat_oos_review_allowed_not_false")
    if governance.get("execution_allowed") is not False:
        blockers.append("governance_execution_allowed_not_false")
    if governance.get("demo_allowed") is not False:
        blockers.append("governance_demo_allowed_not_false")
    if governance.get("live_allowed") is not False:
        blockers.append("governance_live_allowed_not_false")
    rules_lock = governance.get("candidate_rules_lock", {})
    if not isinstance(rules_lock, dict) or rules_lock.get("candidate_rules_modified") is not False:
        blockers.append("governance_candidate_rules_not_locked")
    return blockers


def _candidate_blockers(candidate_report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if candidate_report.get("candidate_id") != CANDIDATE_ID:
        blockers.append("candidate_report_candidate_id_mismatch")
    fixed_rules = _fixed_rules(candidate_report)
    if not fixed_rules:
        blockers.append("candidate_fixed_rules_missing")
        return blockers
    if fixed_rules.get("threshold_search_used") is not False:
        blockers.append("candidate_rules_threshold_search_not_false")
    if fixed_rules.get("parameter_grid_used") is not False:
        blockers.append("candidate_rules_parameter_grid_not_false")
    if fixed_rules.get("retuning_used") is not False:
        blockers.append("candidate_rules_retuning_not_false")
    return blockers


def _fixed_rules(candidate_report: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(candidate_report, dict):
        return {}
    fixed_rules = candidate_report.get("fixed_rules")
    return fixed_rules if isinstance(fixed_rules, dict) else {}


def _default_fixed_rules() -> dict[str, Any]:
    return {
        "reference_blocks": ["block_00_06", "block_06_12", "block_12_18"],
        "response_blocks": ["block_06_12", "block_12_18", "block_18_24"],
        "threshold_search_used": False,
        "parameter_grid_used": False,
        "retuning_used": False,
    }


def _default_synthetic_fixture_rows() -> list[dict[str, Any]]:
    return [
        {
            "timestamp": "2026-06-13T00:00:00",
            "observed_reference_block": "block_00_06",
            "observed_response_block": "block_06_12",
            "compression_label": "lowest range reference block",
            "reference_range": 12.0,
            "response_range": 18.0,
            "notes": "synthetic fixture journal record",
        },
        {
            "timestamp": "2026-06-14T00:00:00",
            "observed_reference_block": "block_06_12",
            "observed_response_block": "block_12_18",
            "compression_label": "lowest range reference block",
            "reference_range": 15.0,
            "response_range": 11.0,
            "notes": "synthetic fixture journal record",
        },
    ]


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safety_summary() -> dict[str, Any]:
    return {
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_path_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "execution_queue_allowed": False,
        "recommendation_output_allowed": False,
        "directional_instruction_output_allowed": False,
        "oos_repeat_allowed": False,
        "new_oos_evaluation_allowed": False,
        "candidate_rules_modified": False,
        "martingale_allowed": False,
        "averaging_into_loss_allowed": False,
    }


def _stable_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
