"""Read-only paper-only forward watcher for local XAUUSD observation rows."""

from __future__ import annotations

import hashlib
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research.xauusd_forward_observation_runner import (
    ALLOWED_TIMEFRAMES,
    CANDIDATE_ID,
    DEFAULT_CANDIDATE_REPORT,
    csv_rows_to_journal_fixture_rows,
    default_synthetic_fixture_csv_rows,
    read_forward_observation_csv,
    validate_forward_observation_csv_rows,
)
from src.research.xauusd_paper_shadow_journal import build_neutral_journal_records

WATCHER_VERSION = "v0_86"
DEFAULT_OUTPUT = Path("reports") / "xauusd_paper_forward_watcher_v0_86.json"
NEXT_RECOMMENDED_STEP = "v0_87_review_paper_forward_watcher_or_stop"
WATCHER_VERSION_V0_87 = "v0_87"
DEFAULT_OUTPUT_V0_87 = Path("reports") / "xauusd_paper_forward_watcher_v0_87.json"
NEXT_RECOMMENDED_STEP_V0_87 = "v0_88_paper_forward_watcher_loop_journal"
DEFAULT_MARKET_CSV_DIR = Path("data")
DEFAULT_REAL_MARKET_TIMEFRAMES = ("M5", "M10", "M15")
DEFAULT_REAL_MARKET_FROM_DATE = "2026-01-01"


def build_xauusd_paper_forward_watcher_v0_86(
    *,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    fixture_csv_path: str | Path | None = None,
    fixture_csv_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    candidate_file = Path(candidate_report_path)
    candidate_report, candidate_errors = _read_json_object(candidate_file, "candidate_report")
    blockers = [*candidate_errors]
    if candidate_report is not None:
        blockers.extend(_candidate_blockers(candidate_report))

    rows: list[dict[str, Any]] = []
    source_files_used: list[str] = []
    source_files_inspected: list[str] = []
    data_source_status = "synthetic_fixtures_only"
    if not blockers:
        rows, rows_blockers = _load_observation_rows(fixture_csv_path, fixture_csv_rows)
        blockers.extend(rows_blockers)
        if fixture_csv_path is not None:
            source_files_used = [str(Path(fixture_csv_path))]
            source_files_inspected = source_files_used
            data_source_status = "fixture_csv"
        elif fixture_csv_rows is not None:
            source_files_used = ["in_memory_fixture_csv_rows"]
            source_files_inspected = source_files_used
            data_source_status = "fixture_csv"
        else:
            source_files_used = []
            source_files_inspected = []
            data_source_status = "synthetic_fixtures_only"

    fixed_rules = _fixed_rules(candidate_report)
    watch_records: list[dict[str, Any]] = []
    journal_record_count = 0
    timeframes_used: list[str] = []
    if not blockers:
        fixture_rows = csv_rows_to_journal_fixture_rows(rows, fixed_rules)
        if not fixture_rows:
            blockers.append("watch_records_empty_after_csv_conversion")
        else:
            journal_records = build_neutral_journal_records(fixture_rows, fixed_rules)
            watch_records = [_convert_journal_record_to_watch_record(rec) for rec in journal_records]
            journal_record_count = len(journal_records)
            timeframes_used = sorted({record["timeframe"] for record in watch_records if record.get("timeframe")})

    watch_status = "watch_completed" if not blockers else "blocked"

    return {
        "watch_version": WATCHER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "source_reports": {
            "candidate_report": str(candidate_file),
        },
        "watch_status": watch_status,
        "data_source_status": data_source_status,
        "real_market_observation_started": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
        "timeframes_used": timeframes_used,
        "allowed_timeframes": ALLOWED_TIMEFRAMES,
        "source_files_used": source_files_used,
        "source_files_inspected": source_files_inspected,
        "journal_record_count": journal_record_count,
        "watch_record_count": len(watch_records),
        "watch_records": watch_records,
        "candidate_rules_preserved": _candidate_rules_preserved(candidate_report),
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
            "mt5_called": False,
            "market_data_exported": False,
            "new_backtest_evaluated": False,
            "new_oos_run_performed": False,
            "repeated_oos_review": False,
            "candidate_rules_changed": False,
            "new_strategy_variant_created": False,
        },
        "safety": _safety_summary(),
        "blockers": blockers,
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


def build_xauusd_paper_forward_watcher_v0_87(
    *,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    market_csv_dir: str | Path = DEFAULT_MARKET_CSV_DIR,
    max_records: int = 30,
    from_date: str | None = DEFAULT_REAL_MARKET_FROM_DATE,
    to_date: str | None = None,
    timeframes: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    candidate_file = Path(candidate_report_path)
    candidate_report, candidate_errors = _read_json_object(candidate_file, "candidate_report")
    blockers = [*candidate_errors]
    if candidate_report is not None:
        blockers.extend(_candidate_blockers(candidate_report))

    requested_timeframes = _normalize_timeframes(timeframes or DEFAULT_REAL_MARKET_TIMEFRAMES)
    max_records = max(0, int(max_records))
    csv_dir = Path(market_csv_dir)
    discovered_files = _discover_market_csv_files(csv_dir, requested_timeframes)

    if not discovered_files:
        blockers.append("missing_local_market_csv")

    watch_records: list[dict[str, Any]] = []
    source_files_used: list[str] = []
    timeframes_used: list[str] = []
    if not blockers:
        watch_records, source_files_used, timeframes_used = _load_real_market_watch_records(
            discovered_files,
            max_records=max_records,
            from_date=from_date,
            to_date=to_date,
        )

    if blockers:
        watch_status = "blocked_missing_local_market_csv" if "missing_local_market_csv" in blockers else "blocked"
    elif watch_records:
        watch_status = "watch_completed"
    else:
        watch_status = "watch_completed_no_records"

    fixed_rules = _fixed_rules(candidate_report)
    return {
        "watch_version": WATCHER_VERSION_V0_87,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "source_reports": {
            "candidate_report": str(candidate_file),
        },
        "watch_status": watch_status,
        "run_mode": "real_read_only",
        "data_source_status": "local_readonly_market_csv",
        "real_market_observation_started": bool(watch_records),
        "paper_observation_only": True,
        "source_files_used": source_files_used,
        "timeframes_used": timeframes_used,
        "watch_record_count": len(watch_records),
        "watch_records": watch_records,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "order_send_allowed": False,
        "order_check_allowed": False,
        "trade_recommendation_output": False,
        "user_facing_buy_sell_signal_output": False,
        "data_csv_touched": False,
        "market_csv_created": False,
        "external_api_called": False,
        "external_data_downloaded": False,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
        "candidate_rules_preserved": _candidate_rules_preserved(candidate_report),
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
            "mt5_called": False,
            "market_data_exported": False,
            "new_backtest_evaluated": False,
            "new_oos_run_performed": False,
            "repeated_oos_review": False,
            "candidate_rules_changed": False,
            "new_strategy_variant_created": False,
            "external_api_called": False,
            "external_data_downloaded": False,
            "data_csv_touched": False,
            "market_csv_created": False,
        },
        "safety": _safety_summary(),
        "blockers": blockers,
        "recommended_next_step": NEXT_RECOMMENDED_STEP_V0_87,
        "next_recommended_step": NEXT_RECOMMENDED_STEP_V0_87,
    }


def save_xauusd_paper_forward_watcher_report(
    report: dict[str, Any],
    output_path: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _discover_market_csv_files(csv_dir: Path, requested_timeframes: list[str]) -> list[tuple[Path, str]]:
    if not csv_dir.exists() or not csv_dir.is_dir():
        return []
    discovered: list[tuple[Path, str]] = []
    for csv_path in sorted(csv_dir.glob("*.csv")):
        if "xauusd" not in csv_path.name.lower():
            continue
        timeframe = _timeframe_from_market_csv_path(csv_path)
        if timeframe in requested_timeframes:
            discovered.append((csv_path, timeframe))
    order = {timeframe: idx for idx, timeframe in enumerate(requested_timeframes)}
    return sorted(discovered, key=lambda item: (order.get(item[1], 999), item[0].name.lower()))


def _load_real_market_watch_records(
    discovered_files: list[tuple[Path, str]],
    *,
    max_records: int,
    from_date: str | None,
    to_date: str | None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    if max_records <= 0:
        return [], [], []
    all_rows: list[dict[str, Any]] = []
    fallback_rows: list[dict[str, Any]] = []
    for csv_path, fallback_timeframe in discovered_files:
        rows = _read_market_csv_rows(csv_path, fallback_timeframe)
        fallback_rows.extend(rows)
        all_rows.extend(_filter_market_rows(rows, from_date=from_date, to_date=to_date))

    selected_rows = all_rows if all_rows else fallback_rows
    selected_rows = sorted(selected_rows, key=lambda row: (str(row["timestamp"]), str(row["timeframe"]), str(row["source_file"])))
    selected_rows = selected_rows[-max_records:]
    watch_records = [_market_row_to_watch_record(row) for row in selected_rows]
    source_files_used = sorted({str(row["source_file"]) for row in selected_rows})
    timeframes_used = sorted({str(row["timeframe"]) for row in selected_rows}, key=_timeframe_sort_key)
    return watch_records, source_files_used, timeframes_used


def _read_market_csv_rows(csv_path: Path, fallback_timeframe: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            timestamp = _first_present(raw_row, ("timestamp_utc", "timestamp", "time", "datetime", "date"))
            if not timestamp:
                continue
            timeframe = str(raw_row.get("timeframe") or fallback_timeframe).upper()
            if timeframe not in DEFAULT_REAL_MARKET_TIMEFRAMES:
                continue
            rows.append(
                {
                    "timestamp": _normalize_timestamp(timestamp),
                    "symbol": str(raw_row.get("symbol") or "XAUUSD").upper(),
                    "timeframe": timeframe,
                    "source_file": csv_path,
                    "source": str(raw_row.get("source") or f"local_readonly_market_csv:{csv_path.name}"),
                }
            )
    return rows


def _market_row_to_watch_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": row["timestamp"],
        "symbol": "XAUUSD",
        "timeframe": row["timeframe"],
        "setup_label": "local_market_csv_candle_observation",
        "direction_assigned": None,
        "paper_observation_direction": None,
        "reason": "local_readonly_market_csv_row_observed",
        "invalidation_note": None,
        "status": "paper_observation_recorded",
        "source": row["source"],
        "paper_observation_only": True,
    }


def _filter_market_rows(
    rows: list[dict[str, Any]],
    *,
    from_date: str | None,
    to_date: str | None,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for row in rows:
        timestamp = str(row["timestamp"])
        if from_date and timestamp[:10] < from_date:
            continue
        if to_date and timestamp[:10] > to_date:
            continue
        filtered.append(row)
    return filtered


def _normalize_timeframes(timeframes: list[str] | tuple[str, ...]) -> list[str]:
    normalized: list[str] = []
    for timeframe in timeframes:
        value = str(timeframe).strip().upper()
        if value in DEFAULT_REAL_MARKET_TIMEFRAMES and value not in normalized:
            normalized.append(value)
    return normalized or list(DEFAULT_REAL_MARKET_TIMEFRAMES)


def _timeframe_from_market_csv_path(csv_path: Path) -> str | None:
    match = re.search(r"(?<![A-Z0-9])M(5|10|15)(?![A-Z0-9])", csv_path.stem.upper())
    return f"M{match.group(1)}" if match else None


def _timeframe_sort_key(timeframe: str) -> int:
    order = {"M5": 0, "M10": 1, "M15": 2}
    return order.get(timeframe, 999)


def _first_present(row: dict[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value)
    return None


def _normalize_timestamp(value: str) -> str:
    text = str(value).strip()
    if text.endswith("Z"):
        return text[:-1] + "+00:00"
    return text if "+" in text or text.endswith("00:00") else text


def _load_observation_rows(
    fixture_csv_path: str | Path | None,
    fixture_csv_rows: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    if fixture_csv_path is not None and fixture_csv_rows is not None:
        return [], ["fixture_csv_path_and_rows_both_supplied"]
    if fixture_csv_path is not None:
        csv_path = Path(fixture_csv_path)
        if not csv_path.exists():
            return [], [f"fixture_csv_missing: {csv_path}"]
        rows = read_forward_observation_csv(csv_path)
    else:
        rows = fixture_csv_rows if fixture_csv_rows is not None else default_synthetic_fixture_csv_rows()
    return rows, validate_forward_observation_csv_rows(rows)


def _convert_journal_record_to_watch_record(record: dict[str, Any]) -> dict[str, Any]:
    notes = str(record.get("notes", ""))
    return {
        "timestamp": str(record.get("timestamp", "")),
        "symbol": "XAUUSD",
        "timeframe": _timeframe_from_notes(notes),
        "setup_label": str(record.get("compression_label", "")),
        "direction_assigned": None,
        "reason": str(record.get("rule_match_status", "")),
        "invalidation_note": None if record.get("rule_match_status") == "rule match" else str(record.get("observation_status", "")),
        "status": str(record.get("observation_status", "")),
        "notes": notes,
    }


def _timeframe_from_notes(notes: str) -> str | None:
    match = re.search(r"timeframe=(M5|M10)", notes)
    return match.group(1) if match else None


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


def _candidate_rules_preserved(candidate_report: dict[str, Any] | None) -> bool:
    if not isinstance(candidate_report, dict):
        return False
    fixed_rules = _fixed_rules(candidate_report)
    if not fixed_rules:
        return False
    return (
        fixed_rules.get("threshold_search_used") is False
        and fixed_rules.get("parameter_grid_used") is False
        and fixed_rules.get("retuning_used") is False
    )


def _fixed_rules(candidate_report: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(candidate_report, dict):
        return {}
    fixed_rules = candidate_report.get("fixed_rules")
    return fixed_rules if isinstance(fixed_rules, dict) else {}


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
        "trade_recommendation_output_allowed": False,
        "new_backtest_allowed": False,
        "new_oos_evaluation_allowed": False,
        "oos_repeat_allowed": False,
        "threshold_search_allowed": False,
        "parameter_grid_allowed": False,
        "parameter_optimization_allowed": False,
        "retune_allowed": False,
        "martingale_allowed": False,
        "averaging_into_loss_allowed": False,
    }


def _stable_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
