"""v0_62 read-only XAUUSD market context labeler.

This module creates descriptive timestamp labels only. It does not test,
filter, approve, or execute any strategy behavior.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

LABELER_VERSION = "v0_62"
SOURCE_FEASIBILITY_VERSION = "v0_61"
PURPOSE = "observational_market_context_labels_only"
DEFAULT_OUTPUT = Path("reports") / "xauusd_market_context_labels_v0_62.json"
DEFAULT_V0_61_REPORT = Path("reports") / "xauusd_market_context_feasibility_v0_61.json"

COMPLETED = "market_context_labeler_completed"
BLOCKED_MISSING_V0_61_REPORT = "blocked_missing_v0_61_report"
FAILED = "labeler_failed"

PRIMARY_DATA_PATTERNS = {
    "M5": "xauusd_m5_xauusd_2023-01-01_2025-12-31.csv",
    "M10": "xauusd_m10_xauusd_m5_xauusd_2023_01_01_2025_12_31_2023-01-03_2025-12-31.csv",
    "M15": "xauusd_m15_xauusd_2023-01-01_2026-06-11.csv",
}

TIMESTAMP_ONLY_LABELS = [
    "market_closed_weekend",
    "likely_market_open",
    "asian_session",
    "london_morning_session",
    "ny_core_session",
    "late_us_session",
    "off_session_or_low_activity",
    "session_transition_asian_to_london",
    "session_transition_london_to_ny",
    "friday_late_session",
    "monday_reopen_window",
]

PLACEHOLDER_EXTERNAL_LABELS = [
    "holiday_us_reduced_liquidity",
    "high_impact_us_event_window",
    "pre_event_window",
    "post_event_repricing_window",
    "fomc_day",
    "nfp_day",
    "cpi_day",
    "dxy_available",
    "dxy_unavailable",
    "yields_available",
    "yields_unavailable",
    "geopolitical_risk_label_available",
    "geopolitical_risk_label_missing",
]

HARD_CONTEXT_OUTPUTS = [
    "hard_block_market_closed",
    "hard_block_missing_required_context_data",
]

SOFT_CONTEXT_OUTPUTS = [
    "observe_holiday_context",
    "observe_event_context",
    "observe_dxy_context",
    "observe_session_context",
    "observe_geopolitical_context",
]


@dataclass(frozen=True)
class TimestampRecord:
    timestamp: datetime
    timeframe: str
    file_name: str


def build_xauusd_market_context_labels_v0_62(
    *,
    data_dir: str | Path = "data",
    source_feasibility_path: str | Path = DEFAULT_V0_61_REPORT,
) -> dict[str, Any]:
    """Build descriptive market-context labels from local XAUUSD timestamps only."""
    try:
        source_feasibility = _read_json(Path(source_feasibility_path))
        if not _valid_v0_61_report(source_feasibility):
            return _base_report(
                labeler_status=BLOCKED_MISSING_V0_61_REPORT,
                source_feasibility=source_feasibility,
                timestamp_basis=_timestamp_basis(None),
                timeframes_used=[],
                context_label_groups=_context_label_groups(),
                timestamp_only_counts=_empty_label_counts(),
                session_distribution=_empty_session_distribution(),
                weekend_closed_distribution={"market_closed_weekend": 0, "likely_market_open": 0},
                missing_context_data_summary={
                    "v0_61_report_present": False,
                    "timestamp_source_present": False,
                    "required_timestamp_rows_present": False,
                    "read_error_count": 0,
                    "external_placeholder_data_required_in_v0_62": False,
                    "hard_block_missing_required_context_data": True,
                },
                dxy_placeholder_status=_dxy_placeholder_status(source_feasibility),
                yields_placeholder_status=_yields_placeholder_status(source_feasibility),
                calendar_placeholder_status=_calendar_placeholder_status(),
                holiday_placeholder_status=_holiday_placeholder_status(),
                blockers=["missing_or_invalid_v0_61_market_context_feasibility_report"],
                warnings=[],
                source_files=[],
                total_timestamp_rows=0,
                next_recommended_step="restore reports/xauusd_market_context_feasibility_v0_61.json before v0_62 context labeling",
            )

        records_by_timeframe, source_files, read_errors = _read_timestamp_records(Path(data_dir))
        records = [record for items in records_by_timeframe.values() for record in items]
        timestamp_only_counts, session_distribution, weekend_distribution = _count_timestamp_labels(records)
        missing_required = not bool(records) or bool(read_errors)
        blockers = ["missing_required_timestamp_context_data"] if missing_required else []
        warnings = [
            "observational_labels_only_not_trade_blockers",
            "broker_timestamp_basis_not_explicitly_encoded_in_csv",
            "external_context_labels_placeholder_only_not_filters",
            "holiday_news_dxy_yields_geopolitical_labels_not_used_to_block_trades_in_v0_62",
        ]
        if read_errors:
            warnings.append("timestamp_csv_read_errors_detected")

        return _base_report(
            labeler_status=COMPLETED,
            source_feasibility=source_feasibility,
            timestamp_basis=_timestamp_basis(source_feasibility),
            timeframes_used=sorted(records_by_timeframe),
            context_label_groups=_context_label_groups(),
            timestamp_only_counts=timestamp_only_counts,
            session_distribution=session_distribution,
            weekend_closed_distribution=weekend_distribution,
            missing_context_data_summary={
                "v0_61_report_present": True,
                "timestamp_source_present": bool(source_files),
                "required_timestamp_rows_present": bool(records),
                "read_error_count": len(read_errors),
                "read_errors": read_errors,
                "external_placeholder_data_required_in_v0_62": False,
                "external_placeholder_labels_trade_blockers": False,
                "hard_block_missing_required_context_data": missing_required,
            },
            dxy_placeholder_status=_dxy_placeholder_status(source_feasibility),
            yields_placeholder_status=_yields_placeholder_status(source_feasibility),
            calendar_placeholder_status=_calendar_placeholder_status(),
            holiday_placeholder_status=_holiday_placeholder_status(),
            blockers=blockers,
            warnings=warnings,
            source_files=source_files,
            total_timestamp_rows=len(records),
            next_recommended_step="v0_63 context-labeled event study, no strategy, no OOS",
        )
    except Exception as exc:
        return _base_report(
            labeler_status=FAILED,
            source_feasibility=None,
            timestamp_basis=_timestamp_basis(None),
            timeframes_used=[],
            context_label_groups=_context_label_groups(),
            timestamp_only_counts=_empty_label_counts(),
            session_distribution=_empty_session_distribution(),
            weekend_closed_distribution={"market_closed_weekend": 0, "likely_market_open": 0},
            missing_context_data_summary={
                "v0_61_report_present": False,
                "timestamp_source_present": False,
                "required_timestamp_rows_present": False,
                "read_error_count": 0,
                "hard_block_missing_required_context_data": True,
            },
            dxy_placeholder_status=_dxy_placeholder_status(None),
            yields_placeholder_status=_yields_placeholder_status(None),
            calendar_placeholder_status=_calendar_placeholder_status(),
            holiday_placeholder_status=_holiday_placeholder_status(),
            blockers=[f"labeler_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            source_files=[],
            total_timestamp_rows=0,
            next_recommended_step="repair v0_62 market context labeler before any context event study",
        )


def save_xauusd_market_context_labels(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_report(
    *,
    labeler_status: str,
    source_feasibility: dict[str, Any] | None,
    timestamp_basis: dict[str, Any],
    timeframes_used: list[str],
    context_label_groups: dict[str, list[str]],
    timestamp_only_counts: dict[str, int],
    session_distribution: dict[str, int],
    weekend_closed_distribution: dict[str, int],
    missing_context_data_summary: dict[str, Any],
    dxy_placeholder_status: dict[str, Any],
    yields_placeholder_status: dict[str, Any],
    calendar_placeholder_status: dict[str, Any],
    holiday_placeholder_status: dict[str, Any],
    blockers: list[str],
    warnings: list[str],
    source_files: list[str],
    total_timestamp_rows: int,
    next_recommended_step: str,
) -> dict[str, Any]:
    return {
        "labeler_version": LABELER_VERSION,
        "labeler_status": labeler_status,
        "source_feasibility_version": SOURCE_FEASIBILITY_VERSION,
        "source_feasibility_status": source_feasibility.get("audit_status") if isinstance(source_feasibility, dict) else None,
        "purpose": PURPOSE,
        "labels_are_trade_blockers": False,
        "hard_blockers_limited_to_market_closed_and_missing_data": True,
        "timestamp_basis": timestamp_basis,
        "timeframes_used": timeframes_used,
        "source_files": source_files,
        "total_timestamp_rows": total_timestamp_rows,
        "context_label_groups": context_label_groups,
        "timestamp_only_labels": list(TIMESTAMP_ONLY_LABELS),
        "placeholder_external_labels": list(PLACEHOLDER_EXTERNAL_LABELS),
        "hard_context_outputs": list(HARD_CONTEXT_OUTPUTS),
        "soft_context_outputs": list(SOFT_CONTEXT_OUTPUTS),
        "label_counts": timestamp_only_counts,
        "session_distribution": session_distribution,
        "weekend_closed_distribution": weekend_closed_distribution,
        "missing_context_data_summary": missing_context_data_summary,
        "dxy_placeholder_status": dxy_placeholder_status,
        "yields_placeholder_status": yields_placeholder_status,
        "calendar_placeholder_status": calendar_placeholder_status,
        "holiday_placeholder_status": holiday_placeholder_status,
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
        "data_csv_added_to_git": False,
        "blockers": blockers,
        "warnings": warnings,
        "recommended_v0_63_plan": "context-labeled event study, no strategy, no OOS.",
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def _read_timestamp_records(data_dir: Path) -> tuple[dict[str, list[TimestampRecord]], list[str], list[str]]:
    records_by_timeframe: dict[str, list[TimestampRecord]] = {}
    source_files: list[str] = []
    read_errors: list[str] = []
    for timeframe, pattern in PRIMARY_DATA_PATTERNS.items():
        files = sorted(data_dir.glob(pattern)) if data_dir.exists() else []
        timeframe_records: list[TimestampRecord] = []
        for file_path in files:
            try:
                records = _read_timestamps(file_path, timeframe)
                timeframe_records.extend(records)
                source_files.append(file_path.as_posix())
            except Exception as exc:
                read_errors.append(f"{file_path.name}:{type(exc).__name__}:{exc}")
        if timeframe_records:
            records_by_timeframe[timeframe] = sorted(timeframe_records, key=lambda record: record.timestamp)
    return records_by_timeframe, source_files, read_errors


def _read_timestamps(path: Path, timeframe: str) -> list[TimestampRecord]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        normalized = {name.strip().lower(): name for name in reader.fieldnames}
        time_column = next((normalized[name] for name in ("time", "date", "datetime", "timestamp") if name in normalized), None)
        if time_column is None:
            raise ValueError("CSV must contain a timestamp column")
        return [
            TimestampRecord(timestamp=_parse_timestamp(str(row[time_column])), timeframe=timeframe, file_name=path.name)
            for row in reader
            if str(row.get(time_column, "")).strip()
        ]


def _count_timestamp_labels(records: list[TimestampRecord]) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    label_counts = _empty_label_counts()
    for record in records:
        for label in _labels_for_timestamp(record.timestamp):
            label_counts[label] += 1
    session_distribution = {label: label_counts[label] for label in _session_distribution_labels()}
    weekend_distribution = {
        "market_closed_weekend": label_counts["market_closed_weekend"],
        "likely_market_open": label_counts["likely_market_open"],
    }
    return label_counts, session_distribution, weekend_distribution


def _labels_for_timestamp(timestamp: datetime) -> list[str]:
    labels: list[str] = []
    weekday = timestamp.weekday()
    hour = timestamp.hour
    minute_of_day = timestamp.hour * 60 + timestamp.minute

    if weekday >= 5:
        labels.append("market_closed_weekend")
    else:
        labels.append("likely_market_open")

    if 0 <= hour <= 6:
        labels.append("asian_session")
    elif 7 <= hour <= 11:
        labels.append("london_morning_session")
    elif 12 <= hour <= 16:
        labels.append("ny_core_session")
    elif 17 <= hour <= 20:
        labels.append("late_us_session")
    else:
        labels.append("off_session_or_low_activity")

    if 390 <= minute_of_day <= 450:
        labels.append("session_transition_asian_to_london")
    if 690 <= minute_of_day <= 750:
        labels.append("session_transition_london_to_ny")
    if weekday == 4 and hour >= 17:
        labels.append("friday_late_session")
    if weekday == 0 and hour <= 2:
        labels.append("monday_reopen_window")
    return labels


def _context_label_groups() -> dict[str, list[str]]:
    return {
        "timestamp_only": list(TIMESTAMP_ONLY_LABELS),
        "future_placeholder_external": list(PLACEHOLDER_EXTERNAL_LABELS),
        "hard_context_outputs": list(HARD_CONTEXT_OUTPUTS),
        "soft_context_outputs": list(SOFT_CONTEXT_OUTPUTS),
    }


def _empty_label_counts() -> dict[str, int]:
    return {label: 0 for label in TIMESTAMP_ONLY_LABELS}


def _empty_session_distribution() -> dict[str, int]:
    return {label: 0 for label in _session_distribution_labels()}


def _session_distribution_labels() -> list[str]:
    return [
        "asian_session",
        "london_morning_session",
        "ny_core_session",
        "late_us_session",
        "off_session_or_low_activity",
        "session_transition_asian_to_london",
        "session_transition_london_to_ny",
        "friday_late_session",
        "monday_reopen_window",
    ]


def _dxy_placeholder_status(source_feasibility: dict[str, Any] | None) -> dict[str, Any]:
    symbols = []
    if isinstance(source_feasibility, dict):
        discovered = source_feasibility.get("discovered_candidate_symbols")
        if isinstance(discovered, dict) and isinstance(discovered.get("dxy_usd_proxy"), list):
            symbols = discovered["dxy_usd_proxy"]
    return {
        "status": "placeholder_schema_defined_no_dxy_series_imported",
        "candidate_symbols_from_v0_61": symbols,
        "labels_defined": ["dxy_available", "dxy_unavailable"],
        "dxy_available": False,
        "dxy_unavailable": True,
        "trade_filter_allowed": False,
        "hard_blocker": False,
    }


def _yields_placeholder_status(source_feasibility: dict[str, Any] | None) -> dict[str, Any]:
    symbols = []
    if isinstance(source_feasibility, dict):
        discovered = source_feasibility.get("discovered_candidate_symbols")
        if isinstance(discovered, dict) and isinstance(discovered.get("us_yields_rates_proxy"), list):
            symbols = discovered["us_yields_rates_proxy"]
    return {
        "status": "placeholder_schema_defined_no_yields_series_imported",
        "candidate_symbols_from_v0_61": symbols,
        "labels_defined": ["yields_available", "yields_unavailable"],
        "yields_available": False,
        "yields_unavailable": True,
        "trade_filter_allowed": False,
        "hard_blocker": False,
    }


def _calendar_placeholder_status() -> dict[str, Any]:
    return {
        "status": "placeholder_schema_defined_no_economic_calendar_imported",
        "labels_defined": [
            "high_impact_us_event_window",
            "pre_event_window",
            "post_event_repricing_window",
            "fomc_day",
            "nfp_day",
            "cpi_day",
        ],
        "trade_filter_allowed": False,
        "hard_blocker": False,
    }


def _holiday_placeholder_status() -> dict[str, Any]:
    return {
        "status": "placeholder_schema_defined_no_holiday_calendar_imported",
        "labels_defined": ["holiday_us_reduced_liquidity"],
        "trade_filter_allowed": False,
        "hard_blocker": False,
    }


def _timestamp_basis(source_feasibility: dict[str, Any] | None) -> dict[str, Any]:
    session_basis = None
    if isinstance(source_feasibility, dict):
        market = source_feasibility.get("market_open_closed_feasibility", {})
        if isinstance(market, dict):
            session_basis = market.get("session_liquidity_basis")
    return {
        "basis": "local_csv_timestamp_no_timezone_column",
        "v0_61_session_basis": session_basis or "utc_time_windows_only_until_broker_timestamp_basis_is_confirmed",
        "timezone_conversion_performed": False,
        "timestamp_source": "existing_local_xauusd_csv_timestamps",
        "observation_only": True,
    }


def _valid_v0_61_report(report: dict[str, Any] | None) -> bool:
    return (
        isinstance(report, dict)
        and report.get("audit_version") == SOURCE_FEASIBILITY_VERSION
        and report.get("audit_status") == "market_context_feasibility_completed"
    )


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _parse_timestamp(value: str) -> datetime:
    raw = value.strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass
    parsed = datetime.fromisoformat(raw)
    return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "observational_context_only": True,
        "labels_are_trade_blockers": False,
        "holiday_news_dxy_session_labels_block_trades": False,
        "strategy_evaluation": False,
        "backtest_candidate_created": False,
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
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
        "trade_recommendation_output_present": False,
        "profitability_claimed": False,
        "external_dataset_imported": False,
        "data_csv_added_to_git": False,
    }
