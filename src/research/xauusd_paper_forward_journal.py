"""Append-only paper forward watcher loop journal for v0_88."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.research.xauusd_forward_observation_runner import DEFAULT_CANDIDATE_REPORT
from src.research.xauusd_paper_forward_watcher import (
    DEFAULT_REAL_MARKET_FROM_DATE,
    DEFAULT_REAL_MARKET_TIMEFRAMES,
    WATCHER_VERSION_V0_87,
    build_xauusd_paper_forward_watcher_v0_87,
)

LOOP_VERSION = "v0_88"
DEFAULT_JOURNAL_PATH = Path("reports") / "xauusd_paper_forward_journal_v0_88.jsonl"
DEFAULT_LOOP_REPORT_PATH = Path("reports") / "xauusd_paper_forward_watcher_loop_v0_88.json"
RECOMMENDED_NEXT_STEP = "v0_89_paper_forward_outcome_tracker"

WatcherBuilder = Callable[..., dict[str, Any]]


def run_paper_forward_watcher_loop_v0_88(
    *,
    cycles: int = 3,
    interval_seconds: float = 1,
    max_records_per_cycle: int = 10,
    journal_path: str | Path = DEFAULT_JOURNAL_PATH,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    market_csv_dir: str | Path = Path("data"),
    from_date: str | None = DEFAULT_REAL_MARKET_FROM_DATE,
    to_date: str | None = None,
    timeframes: list[str] | tuple[str, ...] | None = None,
    watcher_builder: WatcherBuilder = build_xauusd_paper_forward_watcher_v0_87,
    sleep_func: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    safe_cycles = max(0, int(cycles))
    safe_interval_seconds = max(0.0, float(interval_seconds))
    safe_max_records = max(0, int(max_records_per_cycle))
    journal_file = _validated_journal_path(Path(journal_path))

    appended_records: list[dict[str, Any]] = []
    cycle_reports: list[dict[str, Any]] = []
    loop_blockers: list[str] = []
    observations_started = False
    data_source_status = "local_readonly_market_csv"

    for cycle_index in range(safe_cycles):
        watch_report = watcher_builder(
            candidate_report_path=candidate_report_path,
            market_csv_dir=market_csv_dir,
            max_records=safe_max_records,
            from_date=from_date,
            to_date=to_date,
            timeframes=timeframes or DEFAULT_REAL_MARKET_TIMEFRAMES,
        )
        cycle_reports.append(watch_report)
        data_source_status = str(watch_report.get("data_source_status") or data_source_status)
        observations_started = observations_started or bool(watch_report.get("real_market_observation_started"))

        watch_status = str(watch_report.get("watch_status", "blocked"))
        if watch_status not in {"watch_completed", "watch_completed_no_records"}:
            loop_blockers.extend(str(item) for item in watch_report.get("blockers", []) if item)

        records = _journal_records_from_watch_report(cycle_index, watch_report)
        if not records and watch_status in {"watch_completed", "watch_completed_no_records"}:
            records = [_no_observation_record(cycle_index, watch_report)]
        appended_records.extend(records)
        _append_jsonl_records(journal_file, records)

        if cycle_index < safe_cycles - 1 and safe_interval_seconds > 0:
            sleep_func(safe_interval_seconds)

    observation_count = sum(1 for record in appended_records if record.get("status") != "no_observation")
    if loop_blockers:
        loop_status = "loop_blocked"
    elif observation_count == 0:
        loop_status = "loop_completed_no_observations"
    else:
        loop_status = "loop_completed"

    return {
        "loop_version": LOOP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "loop_status": loop_status,
        "cycle_count": safe_cycles,
        "observation_count": observation_count,
        "journal_path": str(journal_file),
        "journal_record_count": _count_valid_jsonl_records(journal_file),
        "journal_append_mode": True,
        "data_source_status": data_source_status,
        "real_market_observation_started": observations_started,
        "paper_observation_only": True,
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
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "source_watch_version": WATCHER_VERSION_V0_87,
        "max_records_per_cycle": safe_max_records,
        "interval_seconds": safe_interval_seconds,
        "cycle_statuses": [report.get("watch_status") for report in cycle_reports],
        "blockers": sorted(set(loop_blockers)),
    }


def save_paper_forward_watcher_loop_report(report: dict[str, Any], output_path: str | Path = DEFAULT_LOOP_REPORT_PATH) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _journal_records_from_watch_report(cycle_index: int, watch_report: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for watch_record in watch_report.get("watch_records", []):
        if not isinstance(watch_record, dict):
            continue
        records.append(
            {
                "journal_version": LOOP_VERSION,
                "cycle_index": cycle_index,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "source_watch_version": str(watch_report.get("watch_version") or WATCHER_VERSION_V0_87),
                "timestamp": watch_record.get("timestamp"),
                "symbol": watch_record.get("symbol"),
                "timeframe": watch_record.get("timeframe"),
                "setup_label": watch_record.get("setup_label"),
                "direction_assigned": watch_record.get("direction_assigned"),
                "reason": watch_record.get("reason"),
                "invalidation_note": watch_record.get("invalidation_note"),
                "status": watch_record.get("status"),
                "source": watch_record.get("source"),
                "paper_observation_only": True,
                "trade_recommendation_output": False,
                "order_send_called": False,
                "order_check_called": False,
            }
        )
    return records


def _no_observation_record(cycle_index: int, watch_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "journal_version": LOOP_VERSION,
        "cycle_index": cycle_index,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source_watch_version": str(watch_report.get("watch_version") or WATCHER_VERSION_V0_87),
        "timestamp": None,
        "symbol": "XAUUSD",
        "timeframe": None,
        "setup_label": "no_observation",
        "direction_assigned": None,
        "reason": "no_observation",
        "invalidation_note": None,
        "status": "no_observation",
        "source": str(watch_report.get("data_source_status") or "local_readonly_market_csv"),
        "paper_observation_only": True,
        "trade_recommendation_output": False,
        "order_send_called": False,
        "order_check_called": False,
    }


def _validated_journal_path(journal_path: Path) -> Path:
    path = journal_path
    if path.suffix.lower() != ".jsonl":
        raise ValueError("journal_path_must_be_jsonl")
    resolved = path.resolve()
    data_root = Path("data").resolve()
    if resolved == data_root or data_root in resolved.parents:
        raise ValueError("journal_path_must_not_be_under_data")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _append_jsonl_records(journal_path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        return
    with journal_path.open("a", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _count_valid_jsonl_records(journal_path: Path) -> int:
    if not journal_path.exists():
        return 0
    count = 0
    for line in journal_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        json.loads(line)
        count += 1
    return count
