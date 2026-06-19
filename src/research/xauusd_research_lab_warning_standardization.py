"""v0_59 research lab warning standardization for goldBotXAU.

This module standardizes the warnings surfaced by the v0_58 lab integrity
audit. It documents policy state only; it does not recompute metrics, tune
rules, run OOS, or create any executable candidate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STANDARDIZATION_VERSION = "v0_59"
SOURCE_INTEGRITY_AUDIT_VERSION = "v0_58"
DEFAULT_SOURCE_REPORT = Path("reports") / "xauusd_research_lab_integrity_audit_v0_58.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_research_lab_warning_standardization_v0_59.json"

COMPLETED = "lab_warning_standardization_completed"
BLOCKED_MISSING_V0_58 = "blocked_missing_v0_58_integrity_report"
FAILED = "standardization_failed"

POLICY_DOCUMENTS = {
    "cost_policy": Path("docs") / "research_lab_cost_policy.md",
    "timestamp_policy": Path("docs") / "research_lab_timestamp_and_session_policy.md",
    "gap_classification_policy": Path("docs") / "research_lab_gap_classification_policy.md",
    "gate_policy": Path("docs") / "research_lab_gate_policy.md",
}


def build_xauusd_research_lab_warning_standardization_v0_59(
    *,
    source_report_path: str | Path = DEFAULT_SOURCE_REPORT,
    root: str | Path = ".",
) -> dict[str, Any]:
    """Build the v0_59 warning-standardization report from v0_58 evidence."""
    root_path = Path(root)
    source_path = _resolve(root_path, Path(source_report_path))
    source = _read_json(source_path)
    if source is None:
        return _base_report(
            standardization_status=BLOCKED_MISSING_V0_58,
            source_integrity_decision=None,
            critical_findings_from_v0_58=[],
            warnings_addressed=[],
            policy_documents=_policy_document_status(root_path),
            cost_policy={},
            timestamp_session_policy={},
            gap_classification_policy={},
            gate_policy={},
            blockers=["missing_v0_58_integrity_report"],
            warnings=[],
            recommended_next_step="restore or generate v0_58 lab integrity report before standardization.",
        )

    warnings_addressed = _warnings_addressed(source)
    critical_findings = list(source.get("critical_findings", []))
    policy_documents = _policy_document_status(root_path)
    cost_policy = _cost_policy(source)
    timestamp_policy = _timestamp_policy(source)
    gap_policy = _gap_classification_policy(source)
    gate_policy = _gate_policy(source)

    documented = {
        "cost_policy_documented": bool(policy_documents["cost_policy"]["exists"]),
        "timestamp_policy_documented": bool(policy_documents["timestamp_policy"]["exists"]),
        "gap_classification_policy_documented": bool(policy_documents["gap_classification_policy"]["exists"]),
        "gate_policy_documented": bool(policy_documents["gate_policy"]["exists"]),
    }
    blockers = [
        key
        for key, value in documented.items()
        if value is not True
    ]
    status = COMPLETED if not blockers else FAILED

    return _base_report(
        standardization_status=status,
        source_integrity_decision=source.get("lab_integrity_decision"),
        critical_findings_from_v0_58=critical_findings,
        warnings_addressed=warnings_addressed,
        policy_documents=policy_documents,
        cost_policy=cost_policy,
        timestamp_session_policy=timestamp_policy,
        gap_classification_policy=gap_policy,
        gate_policy=gate_policy,
        blockers=blockers,
        warnings=_standardization_warnings(source),
        recommended_next_step="continue research with standardized lab policies.",
    )


def save_xauusd_research_lab_warning_standardization(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_report(
    *,
    standardization_status: str,
    source_integrity_decision: str | None,
    critical_findings_from_v0_58: list[Any],
    warnings_addressed: list[str],
    policy_documents: dict[str, Any],
    cost_policy: dict[str, Any],
    timestamp_session_policy: dict[str, Any],
    gap_classification_policy: dict[str, Any],
    gate_policy: dict[str, Any],
    blockers: list[str],
    warnings: list[str],
    recommended_next_step: str,
) -> dict[str, Any]:
    return {
        "standardization_version": STANDARDIZATION_VERSION,
        "standardization_status": standardization_status,
        "source_integrity_audit_version": SOURCE_INTEGRITY_AUDIT_VERSION,
        "source_integrity_decision": source_integrity_decision,
        "critical_findings_from_v0_58": critical_findings_from_v0_58,
        "warnings_addressed": warnings_addressed,
        "policy_documents": policy_documents,
        "cost_policy": cost_policy,
        "timestamp_session_policy": timestamp_session_policy,
        "gap_classification_policy": gap_classification_policy,
        "gate_policy": gate_policy,
        "cost_policy_documented": bool(policy_documents.get("cost_policy", {}).get("exists")),
        "timestamp_policy_documented": bool(policy_documents.get("timestamp_policy", {}).get("exists")),
        "gap_classification_policy_documented": bool(
            policy_documents.get("gap_classification_policy", {}).get("exists")
        ),
        "gate_policy_documented": bool(policy_documents.get("gate_policy", {}).get("exists")),
        "low_frequency_false_negative_risk_documented": bool(
            gate_policy.get("low_frequency_false_negative_risk_documented")
        ),
        "strategy_metrics_changed": False,
        "gates_lowered": False,
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
        "data_csv_added_to_git": False,
        "blockers": blockers,
        "warnings": warnings,
        "recommended_next_step": recommended_next_step,
        "safety": {
            "research_only": True,
            "policy_standardization_only": True,
            "strategy_metrics_changed": False,
            "gates_lowered": False,
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
            "execution_queue_created": False,
            "scheduler_created": False,
            "auto_execute_order": False,
            "trade_recommendation_output_present": False,
            "data_csv_added_to_git": False,
        },
    }


def _cost_policy(source: dict[str, Any]) -> dict[str, Any]:
    integrity = source.get("cost_slippage_integrity", {})
    warnings = list(integrity.get("warnings", [])) if isinstance(integrity, dict) else []
    return {
        "policy_id": "research_cost_slippage_policy_v0_59",
        "current_cost_application_state": "not_globally_consistent",
        "existing_tools_apply_costs_consistently": False,
        "application_locations_identified": list(integrity.get("application_locations", []))
        if isinstance(integrity, dict)
        else [],
        "globally_consistent_cost_model_detected": integrity.get("globally_consistent_cost_model_detected")
        if isinstance(integrity, dict)
        else None,
        "cost_fields_missing_or_inconsistent_warning": "costs_not_applied_consistently_across_all_train_validation_tools"
        in warnings,
        "future_report_requirement": "state whether cost, spread, and slippage are applied; warn when missing or inconsistent",
        "historical_metrics_recomputed": False,
        "retroactive_metric_change_allowed": False,
    }


def _timestamp_policy(source: dict[str, Any]) -> dict[str, Any]:
    integrity = source.get("session_timezone_integrity", {})
    basis = integrity.get("broker_timestamp_basis") if isinstance(integrity, dict) else None
    explicit_utc = basis in {"utc", "explicit_utc"}
    return {
        "policy_id": "research_timestamp_session_policy_v0_59",
        "source_v0_58_broker_timestamp_basis": basis,
        "timestamp_basis": "utc" if explicit_utc else "unknown_or_broker_server_time",
        "broker_timezone_provably_utc": explicit_utc,
        "future_session_research_must_state_timestamp_basis": True,
        "timestamp_shift_performed": False,
        "fixed_session_windows_from_v0_58": integrity.get("fixed_utc_session_windows", {})
        if isinstance(integrity, dict)
        else {},
    }


def _gap_classification_policy(source: dict[str, Any]) -> dict[str, Any]:
    data = source.get("data_integrity", {})
    timeframes = data.get("timeframes", {}) if isinstance(data, dict) else {}
    classifications: dict[str, Any] = {}
    critical: list[str] = []
    warnings: list[str] = []
    for timeframe, summary in sorted(timeframes.items()):
        if not isinstance(summary, dict):
            continue
        candle_count = int(summary.get("candle_count") or 0)
        missing = int(summary.get("missing_candle_gap_count") or 0)
        expected = int(summary.get("weekend_or_session_gap_count") or 0)
        zero_range = int(summary.get("zero_or_negative_range_count") or 0)
        duplicate = int(summary.get("duplicate_timestamp_count") or 0)
        monotonic = summary.get("timestamp_monotonic") is True
        unexpected = max(missing - expected, 0)
        zero_range_rate = zero_range / candle_count if candle_count else 0.0
        zero_range_excessive = zero_range_rate > 0.001
        if duplicate or not monotonic:
            critical.append(f"{timeframe.lower()}_duplicate_or_non_monotonic_error")
        if expected:
            warnings.append(f"{timeframe.lower()}_expected_weekend_or_market_closure_gap")
        if unexpected:
            warnings.append(f"{timeframe.lower()}_unexpected_intraday_gap")
        if zero_range:
            warnings.append(f"{timeframe.lower()}_zero_range_candle_warning")
        classifications[timeframe] = {
            "expected_weekend_or_market_closure_gap_count": expected,
            "unexpected_intraday_gap_count": unexpected,
            "zero_range_candle_warning_count": zero_range,
            "zero_range_frequency_excessive": zero_range_excessive,
            "duplicate_or_non_monotonic_error": bool(duplicate or not monotonic),
            "duplicate_timestamp_count": duplicate,
            "timestamp_monotonic": monotonic,
            "data_altered": False,
        }
    return {
        "policy_id": "research_gap_classification_policy_v0_59",
        "classification_enums": [
            "expected_weekend_or_market_closure_gap",
            "unexpected_intraday_gap",
            "zero_range_candle_warning",
            "duplicate_or_non_monotonic_error",
        ],
        "duplicate_or_non_monotonic_timestamps_are_critical": True,
        "expected_weekend_or_market_closure_gaps_are_warnings": True,
        "zero_range_candles_are_warnings_unless_excessive": True,
        "zero_range_excessive_frequency_threshold": 0.001,
        "data_deleted_or_altered": False,
        "classifications_by_timeframe": classifications,
        "critical_findings": critical,
        "warnings": warnings,
    }


def _gate_policy(source: dict[str, Any]) -> dict[str, Any]:
    gate_sanity = source.get("gate_sanity", {})
    fixed_gates = gate_sanity.get("fixed_gates_reviewed", {}) if isinstance(gate_sanity, dict) else {}
    return {
        "policy_id": "research_validation_gate_policy_v0_59",
        "fixed_gates_preserved": fixed_gates,
        "validation_trade_minimum": fixed_gates.get("validation_trades_min"),
        "validation_trade_minimum_lowered": False,
        "gates_lowered": False,
        "low_frequency_false_negative_risk_documented": True,
        "low_frequency_caveat": (
            "validation_trades >= 50 can reject low-frequency candidates as insufficient evidence; "
            "this is not necessarily evidence of negative edge"
        ),
        "future_report_requirement": "distinguish insufficient validation sample from negative edge without lowering gates",
    }


def _warnings_addressed(source: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys(str(warning) for warning in source.get("warnings", []) if warning))


def _standardization_warnings(source: dict[str, Any]) -> list[str]:
    warnings = _warnings_addressed(source)
    if not warnings:
        return []
    return [f"standardized_v0_58_warning:{warning}" for warning in warnings]


def _policy_document_status(root: Path) -> dict[str, Any]:
    return {
        key: {
            "path": path.as_posix(),
            "exists": _resolve(root, path).exists(),
        }
        for key, path in POLICY_DOCUMENTS.items()
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path
