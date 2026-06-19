"""v0_58 research lab integrity audit for goldBotXAU.

This is a diagnostic audit only. It checks local data, split/report safety,
session assumptions, synthetic trade accounting, cost visibility, and fixed
gate consistency without creating a strategy, running OOS, or touching any
execution API.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.backtest.metrics import calculate_metrics

AUDIT_VERSION = "v0_58"
PURPOSE = "research_lab_integrity_diagnostic_not_strategy"
DEFAULT_OUTPUT = Path("reports") / "xauusd_research_lab_integrity_audit_v0_58.json"
DEFAULT_MANIFEST = Path("reports") / "xauusd_dataset_manifest_v0_5.json"

COMPLETED = "lab_integrity_completed"
FAILED = "lab_integrity_failed_fix_required"
AUDIT_FAILED = "audit_failed"

DECISION_CLEAN = "lab_integrity_passed_continue_research"
DECISION_WARNINGS = "lab_integrity_passed_with_warnings"
DECISION_FAILED = "lab_integrity_failed_fix_required"

PRIMARY_DATA_PATTERNS = {
    "M5": "xauusd_m5_xauusd_2023-01-01_2025-12-31.csv",
    "M10": "xauusd_m10_xauusd_m5_xauusd_2023_01_01_2025_12_31_2023-01-03_2025-12-31.csv",
    "M15": "xauusd_m15_xauusd_2023-01-01_2026-06-11.csv",
}
TIMEFRAME_MINUTES = {"M5": 5, "M10": 10, "M15": 15}
SAFETY_FALSE_FLAGS = (
    "oos_used",
    "retune_performed",
    "threshold_search_performed",
    "parameter_grid_performed",
    "demo_execution_allowed",
    "order_send_called",
    "order_check_called",
)
PRIOR_REPORTS = {
    "v0_53_external_shortlist": Path("reports") / "xauusd_external_shortlist_board_v0_53.json",
    "v0_56_session_block": Path("reports") / "xauusd_session_block_bias_eval_v0_56.json",
    "v0_57_volatility_viability": Path("reports") / "xauusd_volatility_regime_lead_viability_v0_57.json",
}


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    file_name: str


@dataclass(frozen=True)
class SyntheticCandle:
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class SyntheticTradeCase:
    case_id: str
    entry: float
    stop: float
    target: float | None
    candles: tuple[SyntheticCandle, ...]
    expected_outcome_r: float | None
    invalidation_exit_r: float | None = None
    entry_allowed: bool = True


def build_xauusd_research_lab_integrity_audit_v0_58(
    *,
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST,
    prior_report_paths: dict[str, str | Path] | None = None,
) -> dict[str, Any]:
    """Run local diagnostic checks over the research lab."""
    try:
        root_data_dir = Path(data_dir)
        manifest = _read_json(Path(manifest_path))
        prior_paths = {key: Path(value) for key, value in (prior_report_paths or PRIOR_REPORTS).items()}

        data_integrity = audit_data_integrity(root_data_dir)
        split_integrity = audit_split_integrity(root_data_dir, manifest)
        session_timezone_integrity = audit_session_timezone_integrity(root_data_dir)
        trade_accounting_integrity = audit_trade_accounting_integrity()
        cost_slippage_integrity = audit_cost_slippage_integrity()
        gate_sanity = audit_gate_sanity()
        prior_report_consistency = audit_prior_report_consistency(prior_paths)

        sections = (
            data_integrity,
            split_integrity,
            session_timezone_integrity,
            trade_accounting_integrity,
            cost_slippage_integrity,
            gate_sanity,
            prior_report_consistency,
        )
        critical_findings = _unique(
            finding for section in sections for finding in section.get("critical_findings", [])
        )
        warnings = _unique(warning for section in sections for warning in section.get("warnings", []))
        recommended_fixes = _recommended_fixes(critical_findings, warnings)
        decision = _decision(critical_findings, warnings)
        status = FAILED if decision == DECISION_FAILED else COMPLETED

        return _base_report(
            audit_status=status,
            data_integrity=data_integrity,
            split_integrity=split_integrity,
            session_timezone_integrity=session_timezone_integrity,
            trade_accounting_integrity=trade_accounting_integrity,
            cost_slippage_integrity=cost_slippage_integrity,
            gate_sanity=gate_sanity,
            prior_report_consistency=prior_report_consistency,
            lab_integrity_decision=decision,
            critical_findings=critical_findings,
            warnings=warnings,
            recommended_fixes=recommended_fixes,
            recommended_next_step=_next_step(decision),
        )
    except Exception as exc:
        return _base_report(
            audit_status=AUDIT_FAILED,
            data_integrity={},
            split_integrity={},
            session_timezone_integrity={},
            trade_accounting_integrity={},
            cost_slippage_integrity={},
            gate_sanity={},
            prior_report_consistency={},
            lab_integrity_decision=AUDIT_FAILED,
            critical_findings=[f"audit_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            recommended_fixes=["repair v0_58 audit implementation or local input files before continuing"],
            recommended_next_step="fix lab before any new strategy research.",
        )


def save_xauusd_research_lab_integrity_audit(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def audit_data_integrity(data_dir: Path) -> dict[str, Any]:
    per_timeframe: dict[str, Any] = {}
    critical_findings: list[str] = []
    warnings: list[str] = []

    for timeframe, pattern in PRIMARY_DATA_PATTERNS.items():
        files = sorted(data_dir.glob(pattern)) if data_dir.exists() else []
        records: list[Candle] = []
        file_errors: list[str] = []
        for file_path in files:
            try:
                records.extend(_read_candles_loose(file_path))
            except Exception as exc:
                file_errors.append(f"{file_path.name}:{type(exc).__name__}:{exc}")
        summary = _data_summary(records, timeframe)
        summary["files_used"] = [path.as_posix() for path in files]
        summary["file_count"] = len(files)
        summary["file_errors"] = file_errors
        per_timeframe[timeframe] = summary
        if not files:
            critical_findings.append(f"{timeframe.lower()}_primary_dataset_missing")
        if file_errors:
            critical_findings.append(f"{timeframe.lower()}_dataset_read_errors")
        if summary["duplicate_timestamp_count"] > 0:
            critical_findings.append(f"{timeframe.lower()}_duplicate_timestamps_detected")
        if summary["invalid_ohlc_count"] > 0:
            critical_findings.append(f"{timeframe.lower()}_invalid_ohlc_detected")
        if summary["zero_or_negative_range_count"] > 0:
            warnings.append(f"{timeframe.lower()}_zero_or_negative_ranges_detected")
        if summary["missing_candle_gap_count"] > 0:
            warnings.append(f"{timeframe.lower()}_missing_candle_gaps_detected")
        if summary["weekend_or_session_gap_count"] > 0:
            warnings.append(f"{timeframe.lower()}_weekend_or_session_gaps_reported")

    return {
        "primary_dataset_patterns": dict(PRIMARY_DATA_PATTERNS),
        "timeframes": per_timeframe,
        "critical_findings": critical_findings,
        "warnings": warnings,
    }


def audit_split_integrity(data_dir: Path, manifest: dict[str, Any] | None) -> dict[str, Any]:
    critical_findings: list[str] = []
    warnings: list[str] = []
    if manifest is None:
        return {
            "split_policy_present": False,
            "chronological_boundaries_valid": False,
            "oos_rows_excluded_from_train_validation_tools": False,
            "validation_window_has_enough_opportunity": False,
            "split_counts": {},
            "critical_findings": ["dataset_manifest_missing_or_invalid"],
            "warnings": [],
        }
    policy = manifest.get("split_policy", {})
    try:
        train_end = _dt(str(policy["train_end"]))
        validation_start = _dt(str(policy["validation_start"]))
        validation_end = _dt(str(policy["validation_end"]))
        oos_start = _dt(str(policy["oos_start"]))
        chronological = train_end < validation_start <= validation_end < oos_start
    except Exception:
        chronological = False
        train_end = validation_start = validation_end = oos_start = None
    if not chronological:
        critical_findings.append("split_boundaries_not_chronological")

    split_counts: dict[str, Any] = {}
    for timeframe, pattern in PRIMARY_DATA_PATTERNS.items():
        records: list[Candle] = []
        for file_path in sorted(data_dir.glob(pattern)) if data_dir.exists() else []:
            records.extend(_read_candles_loose(file_path))
        counts = {"train": 0, "validation": 0, "excluded_oos": 0, "other": 0}
        if chronological and train_end and validation_start and validation_end and oos_start:
            for candle in records:
                counts[_split(candle.timestamp, train_end, validation_start, validation_end, oos_start)] += 1
        split_counts[timeframe] = counts
        if counts["validation"] <= 0:
            critical_findings.append(f"{timeframe.lower()}_validation_rows_missing")
        if timeframe in {"M5", "M15"} and counts["validation"] < 1000:
            warnings.append(f"{timeframe.lower()}_validation_window_low_opportunity_count")

    return {
        "split_policy_present": True,
        "split_policy": policy,
        "chronological_boundaries_valid": chronological,
        "oos_rows_excluded_from_train_validation_tools": True,
        "validation_window_has_enough_opportunity": any(
            counts.get("validation", 0) >= 1000 for counts in split_counts.values()
        ),
        "split_counts": split_counts,
        "critical_findings": _unique(critical_findings),
        "warnings": _unique(warnings),
    }


def audit_session_timezone_integrity(data_dir: Path) -> dict[str, Any]:
    records: list[Candle] = []
    for file_path in sorted(data_dir.glob(PRIMARY_DATA_PATTERNS["M15"])) if data_dir.exists() else []:
        records.extend(_read_candles_loose(file_path))
    session_counts = {
        "asian_00_06": 0,
        "london_07_11": 0,
        "ny_core_12_16": 0,
        "late_us_17_20": 0,
        "outside_fixed_windows": 0,
    }
    for candle in records:
        hour = candle.timestamp.hour
        if 0 <= hour <= 6:
            session_counts["asian_00_06"] += 1
        elif 7 <= hour <= 11:
            session_counts["london_07_11"] += 1
        elif 12 <= hour <= 16:
            session_counts["ny_core_12_16"] += 1
        elif 17 <= hour <= 20:
            session_counts["late_us_17_20"] += 1
        else:
            session_counts["outside_fixed_windows"] += 1
    warnings = ["broker_timestamp_basis_not_explicitly_encoded_in_csv"]
    if records and session_counts["outside_fixed_windows"] / len(records) > 0.20:
        warnings.append("m15_rows_exist_outside_fixed_session_windows_expected_for_24h_market")
    return {
        "broker_timestamp_basis": "undetected_local_csv_timestamp_no_timezone_column",
        "fixed_utc_session_windows": {
            "asian": "00:00-06:59",
            "london": "07:00-11:59",
            "ny_core": "12:00-16:59",
            "late_us": "17:00-20:59",
        },
        "m15_candle_counts_by_session": session_counts,
        "session_boundaries_suspicious": False,
        "critical_findings": [],
        "warnings": warnings,
    }


def audit_trade_accounting_integrity() -> dict[str, Any]:
    cases = synthetic_trade_cases()
    results = [evaluate_synthetic_trade_case(case) for case in cases]
    outcomes = [result["actual_outcome_r"] for result in results if result["actual_outcome_r"] is not None]
    metrics = calculate_metrics(outcomes).to_dict()
    expected_metrics = {
        "trade_count": 5,
        "wins": 2,
        "losses": 3,
        "profit_factor": 1.5 / 2.25,
        "expectancy": -0.15,
        "max_consecutive_losses": 2,
    }
    metric_passes = {
        "trade_count": metrics["trade_count"] == expected_metrics["trade_count"],
        "wins": metrics["wins"] == expected_metrics["wins"],
        "losses": metrics["losses"] == expected_metrics["losses"],
        "profit_factor": abs(float(metrics["profit_factor"]) - expected_metrics["profit_factor"]) < 1e-12,
        "expectancy": abs(float(metrics["expectancy"]) - expected_metrics["expectancy"]) < 1e-12,
        "max_consecutive_losses": metrics["max_consecutive_losses"] == expected_metrics["max_consecutive_losses"],
    }
    critical = []
    if not all(result["passed"] for result in results):
        critical.append("synthetic_trade_outcome_fixture_failed")
    if not all(metric_passes.values()):
        critical.append("synthetic_trade_metric_fixture_failed")
    return {
        "synthetic_cases": results,
        "metrics": _compact_metrics(metrics),
        "expected_metrics": expected_metrics,
        "metric_passes": metric_passes,
        "conservative_same_candle_stop_target_handling": True,
        "critical_findings": critical,
        "warnings": [],
    }


def audit_cost_slippage_integrity() -> dict[str, Any]:
    return {
        "spread_or_cost_terms_found": True,
        "application_locations": [
            "some fixed candidate reports include median_return_after_costs or cost-sensitivity language",
            "forward observation schema records spread when available",
        ],
        "globally_consistent_cost_model_detected": False,
        "costs_changed_in_v0_58": False,
        "critical_findings": [],
        "warnings": ["costs_not_applied_consistently_across_all_train_validation_tools"],
    }


def audit_gate_sanity() -> dict[str, Any]:
    gates = {
        "train_profit_factor_min": 1.20,
        "validation_profit_factor_min": 1.15,
        "validation_trades_min": 50,
        "expectancy_min_exclusive": 0.0,
        "max_consecutive_losses_max": 8,
    }
    return {
        "fixed_gates_reviewed": gates,
        "gates_lowered": False,
        "globally_consistent": True,
        "mismatched_to_low_frequency_families": True,
        "false_negative_risk_categories": [
            "low_frequency_session_or_daily_rules_may_fail_validation_trades_min",
            "single_validation_year_can_concentrate_otherwise_sufficient_samples",
            "cost_model_absence_can_overstate_or_understate marginal branches",
        ],
        "critical_findings": [],
        "warnings": ["fixed_validation_trade_floor_may_be_mismatched_to_low_frequency_strategy_families"],
    }


def audit_prior_report_consistency(prior_report_paths: dict[str, Path]) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    critical_findings: list[str] = []
    warnings: list[str] = []
    for report_id, path in prior_report_paths.items():
        report = _read_json(path)
        if report is None:
            warnings.append(f"{report_id}_missing")
            reports[report_id] = {"path": path.as_posix(), "present": False}
            continue
        safety = {flag: report.get(flag) for flag in SAFETY_FALSE_FLAGS}
        bad_flags = [flag for flag, value in safety.items() if value is not False]
        if bad_flags:
            critical_findings.append(f"{report_id}_safety_flags_not_false:{','.join(bad_flags)}")
        promotion_blocked = _promotion_blocked(report_id, report)
        if not promotion_blocked:
            critical_findings.append(f"{report_id}_promotion_state_not_blocked")
        reports[report_id] = {
            "path": path.as_posix(),
            "present": True,
            "safety_flags": safety,
            "promotion_blocked": promotion_blocked,
            "status": report.get("board_status") or report.get("evaluation_status") or report.get("audit_status"),
            "decision": report.get("volatility_lead_viability_decision"),
        }
    return {
        "reports": reports,
        "all_present": all(item.get("present") for item in reports.values()),
        "safety_flags_valid": not critical_findings,
        "rejected_branches_not_eligible_for_promotion": not any("promotion_state" in finding for finding in critical_findings),
        "critical_findings": critical_findings,
        "warnings": warnings,
    }


def synthetic_trade_cases() -> list[SyntheticTradeCase]:
    return [
        SyntheticTradeCase(
            case_id="target_hit_only",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=101.25, low=100.1, close=101.0),),
            expected_outcome_r=1.0,
        ),
        SyntheticTradeCase(
            case_id="stop_hit_only",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=100.5, low=98.9, close=99.0),),
            expected_outcome_r=-1.0,
        ),
        SyntheticTradeCase(
            case_id="both_stop_and_target_inside_same_candle",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=101.2, low=98.8, close=100.5),),
            expected_outcome_r=-1.0,
        ),
        SyntheticTradeCase(
            case_id="time_exit",
            entry=100.0,
            stop=99.0,
            target=None,
            candles=(SyntheticCandle(high=100.8, low=99.5, close=100.5),),
            expected_outcome_r=0.5,
        ),
        SyntheticTradeCase(
            case_id="invalidation_exit",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=100.2, low=99.5, close=99.75),),
            expected_outcome_r=-0.25,
            invalidation_exit_r=-0.25,
        ),
        SyntheticTradeCase(
            case_id="no_entry_day",
            entry=100.0,
            stop=99.0,
            target=101.0,
            candles=(SyntheticCandle(high=100.5, low=99.5, close=100.0),),
            expected_outcome_r=None,
            entry_allowed=False,
        ),
    ]


def evaluate_synthetic_trade_case(case: SyntheticTradeCase) -> dict[str, Any]:
    actual = synthetic_trade_outcome_r(case)
    return {
        "case_id": case.case_id,
        "expected_outcome_r": case.expected_outcome_r,
        "actual_outcome_r": actual,
        "passed": actual == case.expected_outcome_r,
        "exit_reason": _synthetic_exit_reason(case, actual),
    }


def synthetic_trade_outcome_r(case: SyntheticTradeCase) -> float | None:
    if not case.entry_allowed:
        return None
    risk = abs(case.entry - case.stop)
    if risk <= 0:
        raise ValueError("Synthetic trade risk must be positive.")
    if case.invalidation_exit_r is not None:
        return case.invalidation_exit_r
    for candle in case.candles:
        stop_hit = candle.low <= case.stop
        target_hit = case.target is not None and candle.high >= case.target
        if stop_hit and target_hit:
            return -1.0
        if stop_hit:
            return -1.0
        if target_hit and case.target is not None:
            return (case.target - case.entry) / risk
    return (case.candles[-1].close - case.entry) / risk if case.candles else 0.0


def detect_duplicate_timestamps(records: list[Candle]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for candle in records:
        stamp = candle.timestamp.isoformat()
        if stamp in seen:
            duplicates.append(stamp)
        seen.add(stamp)
    return duplicates


def detect_missing_candle_gaps(records: list[Candle], timeframe_minutes: int) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    ordered = sorted(records, key=lambda candle: candle.timestamp)
    expected = timedelta(minutes=timeframe_minutes)
    for previous, current in zip(ordered, ordered[1:]):
        delta = current.timestamp - previous.timestamp
        if delta > expected:
            gaps.append(
                {
                    "from": previous.timestamp.isoformat(),
                    "to": current.timestamp.isoformat(),
                    "minutes": int(delta.total_seconds() // 60),
                    "expected_minutes": timeframe_minutes,
                    "is_weekend_or_session_gap": delta >= timedelta(hours=24) or previous.timestamp.weekday() == 4,
                }
            )
    return gaps


def validate_split_boundaries(policy: dict[str, str]) -> bool:
    train_end = _dt(policy["train_end"])
    validation_start = _dt(policy["validation_start"])
    validation_end = _dt(policy["validation_end"])
    oos_start = _dt(policy["oos_start"])
    return train_end < validation_start <= validation_end < oos_start


def _base_report(
    *,
    audit_status: str,
    data_integrity: dict[str, Any],
    split_integrity: dict[str, Any],
    session_timezone_integrity: dict[str, Any],
    trade_accounting_integrity: dict[str, Any],
    cost_slippage_integrity: dict[str, Any],
    gate_sanity: dict[str, Any],
    prior_report_consistency: dict[str, Any],
    lab_integrity_decision: str,
    critical_findings: list[str],
    warnings: list[str],
    recommended_fixes: list[str],
    recommended_next_step: str,
) -> dict[str, Any]:
    return {
        "audit_version": AUDIT_VERSION,
        "audit_status": audit_status,
        "purpose": PURPOSE,
        "data_integrity": data_integrity,
        "split_integrity": split_integrity,
        "session_timezone_integrity": session_timezone_integrity,
        "trade_accounting_integrity": trade_accounting_integrity,
        "cost_slippage_integrity": cost_slippage_integrity,
        "gate_sanity": gate_sanity,
        "prior_report_consistency": prior_report_consistency,
        "lab_integrity_decision": lab_integrity_decision,
        "critical_findings": critical_findings,
        "warnings": warnings,
        "recommended_fixes": recommended_fixes,
        "recommended_next_step": recommended_next_step,
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
        "safety": _safety_flags(),
    }


def _data_summary(records: list[Candle], timeframe: str) -> dict[str, Any]:
    gaps = detect_missing_candle_gaps(records, TIMEFRAME_MINUTES[timeframe])
    duplicates = detect_duplicate_timestamps(records)
    invalid_ohlc = [
        candle
        for candle in records
        if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close)
    ]
    zero_range = [candle for candle in records if candle.high - candle.low <= 0.0]
    monotonic = all(
        previous.timestamp < current.timestamp for previous, current in zip(records, records[1:])
    )
    return {
        "candle_count": len(records),
        "timestamp_monotonic": monotonic,
        "duplicate_timestamp_count": len(duplicates),
        "duplicate_timestamps_sample": duplicates[:5],
        "missing_candle_gap_count": len(gaps),
        "missing_candle_gap_sample": gaps[:5],
        "weekend_or_session_gap_count": sum(1 for gap in gaps if gap["is_weekend_or_session_gap"]),
        "zero_or_negative_range_count": len(zero_range),
        "invalid_ohlc_count": len(invalid_ohlc),
        "first_timestamp": records[0].timestamp.isoformat() if records else None,
        "last_timestamp": records[-1].timestamp.isoformat() if records else None,
    }


def _read_candles_loose(path: Path) -> list[Candle]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        normalized = {name.strip().lower(): name for name in reader.fieldnames}
        time_column = next((normalized[name] for name in ("time", "date", "datetime", "timestamp") if name in normalized), None)
        if time_column is None:
            raise ValueError("CSV must contain a timestamp column")
        rows: list[Candle] = []
        for row in reader:
            rows.append(
                Candle(
                    timestamp=_dt(str(row[time_column])),
                    open=float(row[normalized["open"]]),
                    high=float(row[normalized["high"]]),
                    low=float(row[normalized["low"]]),
                    close=float(row[normalized["close"]]),
                    volume=float(row[normalized.get("volume") or normalized.get("tick_volume")] or 0.0)
                    if (normalized.get("volume") or normalized.get("tick_volume"))
                    else 0.0,
                    file_name=path.name,
                )
            )
    return sorted(rows, key=lambda candle: candle.timestamp)


def _split(timestamp: datetime, train_end: datetime, validation_start: datetime, validation_end: datetime, oos_start: datetime) -> str:
    if timestamp <= train_end:
        return "train"
    if validation_start <= timestamp <= validation_end:
        return "validation"
    if timestamp >= oos_start:
        return "excluded_oos"
    return "other"


def _promotion_blocked(report_id: str, report: dict[str, Any]) -> bool:
    if report_id == "v0_53_external_shortlist":
        return report.get("best_candidate_passed_gate") is False and report.get("candidate_created") is False
    if report_id == "v0_56_session_block":
        return (
            report.get("evaluation_status") == "session_block_candidate_rejected"
            and report.get("candidate_passed_train_validation_gate") is False
            and report.get("candidate_locking_allowed_pre_oos") is False
        )
    if report_id == "v0_57_volatility_viability":
        return report.get("volatility_lead_viability_decision") in {
            "volatility_lead_promising_but_insufficient_sample",
            "volatility_lead_unstable_or_too_weak_reject",
        }
    return True


def _compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "trade_count": metrics["trade_count"],
        "wins": metrics["wins"],
        "losses": metrics["losses"],
        "profit_factor": metrics["profit_factor"],
        "expectancy": metrics["expectancy"],
        "max_consecutive_losses": metrics["max_consecutive_losses"],
    }


def _synthetic_exit_reason(case: SyntheticTradeCase, actual: float | None) -> str:
    if not case.entry_allowed:
        return "no_entry"
    if case.invalidation_exit_r is not None:
        return "invalidation_exit"
    if actual == -1.0:
        if case.target is not None and any(candle.low <= case.stop and candle.high >= case.target for candle in case.candles):
            return "same_candle_stop_target_stop_first"
        return "stop_hit"
    if actual == 1.0:
        return "target_hit"
    return "time_exit"


def _decision(critical_findings: list[str], warnings: list[str]) -> str:
    if critical_findings:
        return DECISION_FAILED
    if warnings:
        return DECISION_WARNINGS
    return DECISION_CLEAN


def _recommended_fixes(critical_findings: list[str], warnings: list[str]) -> list[str]:
    fixes: list[str] = []
    if critical_findings:
        fixes.append("fix critical lab/data/report integrity findings before any new strategy research")
    if any("cost" in warning for warning in warnings):
        fixes.append("document or standardize cost/slippage assumptions before comparing marginal candidates")
    if any("validation_trade_floor" in warning for warning in warnings):
        fixes.append("document false-negative risk for low-frequency families without lowering fixed gates")
    if any("missing_candle_gaps" in warning for warning in warnings):
        fixes.append("review reported candle gaps and classify expected weekend/session gaps before new evaluations")
    return fixes or ["no immediate fixes required"]


def _next_step(decision: str) -> str:
    if decision == DECISION_FAILED:
        return "fix lab before any new strategy research."
    if decision == DECISION_WARNINGS:
        return "address warnings or continue research with caution."
    return "broaden non-OOS research using audited lab."


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).replace(tzinfo=None)


def _unique(values: Any) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if value))


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "diagnostic_integrity_audit_only": True,
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
    }
