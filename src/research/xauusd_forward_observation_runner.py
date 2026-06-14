"""v0_33 read-only forward observation CSV runner for local fixtures."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research.xauusd_paper_shadow_journal import build_neutral_journal_records

RUNNER_VERSION = "v0_33"
CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"
DEFAULT_PLAN = Path("reports") / "xauusd_forward_observation_export_plan_v0_32.json"
DEFAULT_JOURNAL_PROTOCOL = Path("reports") / "xauusd_paper_shadow_journal_protocol_v0_31.json"
DEFAULT_CANDIDATE_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_forward_observation_runner_protocol_v0_33.json"
NEXT_RECOMMENDED_STEP = "v0_34 run one read-only local forward observation export and journal pass, no execution"

ALLOWED_TIMEFRAMES = ["M5", "M10"]
ALLOWED_SYMBOLS = ["XAUUSD", "XAUUSD.", "XAUUSDm"]
EXPECTED_CSV_SCHEMA = [
    "timestamp_utc",
    "symbol",
    "timeframe",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "source",
]
REFERENCE_RESPONSE_PAIRS = {
    "block_00_06": "block_06_12",
    "block_06_12": "block_12_18",
    "block_12_18": "block_18_24",
}


def build_xauusd_forward_observation_runner_protocol_v0_33(
    *,
    plan_path: str | Path = DEFAULT_PLAN,
    journal_protocol_path: str | Path = DEFAULT_JOURNAL_PROTOCOL,
    candidate_report_path: str | Path = DEFAULT_CANDIDATE_REPORT,
    fixture_csv_path: str | Path | None = None,
    fixture_csv_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    plan_file = Path(plan_path)
    journal_file = Path(journal_protocol_path)
    candidate_file = Path(candidate_report_path)

    plan, plan_errors = _read_json_object(plan_file, "v0_32_forward_observation_plan")
    journal_protocol, journal_errors = _read_json_object(journal_file, "v0_31_journal_protocol")
    candidate_report, candidate_errors = _read_json_object(candidate_file, "candidate_report")
    blockers = [*plan_errors, *journal_errors, *candidate_errors]

    if plan is not None:
        blockers.extend(_plan_blockers(plan))
    if journal_protocol is not None:
        blockers.extend(_journal_protocol_blockers(journal_protocol))
    if candidate_report is not None:
        blockers.extend(_candidate_blockers(candidate_report))
    if plan is not None and candidate_report is not None:
        blockers.extend(_candidate_rules_hash_blockers(plan, candidate_report))

    csv_rows, csv_blockers = _load_fixture_csv_rows(fixture_csv_path, fixture_csv_rows)
    blockers.extend(csv_blockers)

    fixed_rules = _fixed_rules(candidate_report)
    fixture_rows = [] if blockers else csv_rows_to_journal_fixture_rows(csv_rows, fixed_rules)
    journal_records = [] if blockers else build_neutral_journal_records(fixture_rows, fixed_rules)
    runner_status = "framework_ready_not_started" if not blockers else "blocked_runner_prerequisites_not_met"

    return {
        "runner_version": RUNNER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_id": CANDIDATE_ID,
        "source_reports": {
            "forward_observation_plan": str(plan_file),
            "paper_shadow_journal_protocol": str(journal_file),
            "candidate_report": str(candidate_file),
        },
        "runner_status": runner_status,
        "data_source_status": "synthetic_fixtures_only",
        "future_mode": "journal_only",
        "allowed_timeframes": ALLOWED_TIMEFRAMES,
        "expected_csv_schema": EXPECTED_CSV_SCHEMA,
        "real_market_observation_started": False,
        "mt5_called_in_tests": False,
        "execution_allowed": False,
        "demo_allowed": False,
        "live_allowed": False,
        "repeated_oos_review": False,
        "candidate_rules_modified": False,
        "blockers": blockers,
        "readonly_exporter_wrapper": {
            "name": "xauusd_forward_observation_readonly_csv_exporter_v0_33",
            "status": "framework_ready_not_started" if not blockers else "blocked",
            "input_mode": "local_csv_fixture_rows_only",
            "output_mode": "csv_rows_for_neutral_journal_records",
            "mt5_called": False,
            "real_market_observation_started": False,
            "requires_future_explicit_run_approval": True,
        },
        "journal_runner": {
            "name": "xauusd_forward_observation_journal_runner_v0_33",
            "journal_framework_source": "src/research/xauusd_paper_shadow_journal.py",
            "journal_protocol_source": str(journal_file),
            "record_schema_source": "reports/xauusd_paper_shadow_journal_protocol_v0_31.json",
            "generated_record_count": len(journal_records),
            "fixture_group_count": len(fixture_rows),
        },
        "synthetic_fixture_csv_row_count": len(csv_rows),
        "synthetic_fixture_journal_records": journal_records,
        "synthetic_fixture_journal_record_count": len(journal_records),
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
            "real_observation_run": False,
            "new_backtest_evaluated": False,
            "new_oos_run_performed": False,
            "repeated_oos_review": False,
            "candidate_rules_changed": False,
            "new_strategy_variant_created": False,
        },
        "safety": _safety_summary(),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
    }


def read_forward_observation_csv(csv_path: str | Path) -> list[dict[str, Any]]:
    csv_file = Path(csv_path)
    with csv_file.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_local_fixture_forward_observation_csv(
    rows: list[dict[str, Any]],
    output_path: str | Path,
) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_CSV_SCHEMA)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in EXPECTED_CSV_SCHEMA})


def csv_rows_to_journal_fixture_rows(
    csv_rows: list[dict[str, Any]],
    fixed_rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rules = fixed_rules or _default_fixed_rules()
    parsed_rows = [_parse_csv_row(row) for row in csv_rows]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in parsed_rows:
        key = (row["timeframe"], row["timestamp"].date().isoformat())
        grouped.setdefault(key, []).append(row)

    fixture_rows: list[dict[str, Any]] = []
    for (timeframe, date_text), rows in sorted(grouped.items()):
        block_ranges = _block_ranges(rows)
        selected_reference = _select_lowest_reference_block(block_ranges, rules)
        if selected_reference is None:
            continue
        response_block = REFERENCE_RESPONSE_PAIRS[selected_reference]
        fixture_rows.append(
            {
                "timestamp": f"{date_text}T00:00:00+00:00",
                "observed_reference_block": selected_reference,
                "observed_response_block": response_block,
                "compression_label": "lowest range reference block",
                "reference_range": block_ranges[selected_reference],
                "response_range": block_ranges[response_block],
                "notes": (
                    f"synthetic fixture journal record; timeframe={timeframe}; "
                    "data_quality=local fixture csv; risk_note=observation only"
                ),
            }
        )
    return fixture_rows


def save_xauusd_forward_observation_runner_protocol(
    report: dict[str, Any],
    output_path: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_synthetic_fixture_csv_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for timeframe, step_minutes in (("M5", 5), ("M10", 10)):
        rows.extend(_fixture_rows_for_timeframe("2026-06-14", timeframe, step_minutes))
    return rows


def _fixture_rows_for_timeframe(date_text: str, timeframe: str, step_minutes: int) -> list[dict[str, Any]]:
    specs = [
        (0, 6, 3300.0, 3310.0),
        (6, 12, 3305.0, 3330.0),
        (12, 18, 3315.0, 3352.0),
        (18, 24, 3320.0, 3348.0),
    ]
    rows: list[dict[str, Any]] = []
    for start_hour, end_hour, low, high in specs:
        cursor_minutes = start_hour * 60
        end_minutes = end_hour * 60
        while cursor_minutes < end_minutes:
            hour = cursor_minutes // 60
            minute = cursor_minutes % 60
            rows.append(
                {
                    "timestamp_utc": f"{date_text}T{hour:02d}:{minute:02d}:00+00:00",
                    "symbol": "XAUUSD",
                    "timeframe": timeframe,
                    "open": f"{low + 1:.2f}",
                    "high": f"{high:.2f}",
                    "low": f"{low:.2f}",
                    "close": f"{high - 1:.2f}",
                    "tick_volume": "100",
                    "spread": "20",
                    "source": "synthetic_fixture",
                }
            )
            cursor_minutes += step_minutes
    return rows


def _load_fixture_csv_rows(
    fixture_csv_path: str | Path | None,
    fixture_csv_rows: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    if fixture_csv_path is not None and fixture_csv_rows is not None:
        return [], ["fixture_csv_path_and_rows_both_supplied"]
    if fixture_csv_path is not None:
        csv_file = Path(fixture_csv_path)
        if not csv_file.exists():
            return [], [f"fixture_csv_missing: {csv_file}"]
        rows = read_forward_observation_csv(csv_file)
    else:
        rows = fixture_csv_rows if fixture_csv_rows is not None else default_synthetic_fixture_csv_rows()
    blockers = validate_forward_observation_csv_rows(rows)
    return rows, blockers


def validate_forward_observation_csv_rows(rows: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    if not rows:
        return ["fixture_csv_rows_empty"]

    first_row = rows[0]
    missing_fields = [field for field in EXPECTED_CSV_SCHEMA if field not in first_row]
    if missing_fields:
        blockers.append(f"fixture_csv_missing_fields: {','.join(missing_fields)}")
        return blockers

    previous_by_timeframe: dict[str, datetime] = {}
    for index, row in enumerate(rows):
        row_label = f"row_{index}"
        timeframe = str(row.get("timeframe", ""))
        symbol = str(row.get("symbol", ""))
        timestamp = _parse_timestamp(row.get("timestamp_utc"))
        if timestamp is None:
            blockers.append(f"{row_label}_timestamp_utc_invalid")
        if symbol not in ALLOWED_SYMBOLS:
            blockers.append(f"{row_label}_symbol_not_allowed")
        if timeframe not in ALLOWED_TIMEFRAMES:
            blockers.append(f"{row_label}_timeframe_not_allowed")
        for field in ("open", "high", "low", "close", "tick_volume", "spread"):
            if _as_float(row.get(field)) is None:
                blockers.append(f"{row_label}_{field}_not_numeric")
        if timestamp is not None and timeframe in ALLOWED_TIMEFRAMES:
            previous = previous_by_timeframe.get(timeframe)
            if previous is not None and timestamp < previous:
                blockers.append(f"{row_label}_timestamp_not_chronological_for_timeframe")
            previous_by_timeframe[timeframe] = timestamp
    return blockers


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


def _plan_blockers(plan: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if plan.get("plan_version") != "v0_32":
        blockers.append("plan_version_not_v0_32")
    if plan.get("candidate_id") != CANDIDATE_ID:
        blockers.append("plan_candidate_id_mismatch")
    if plan.get("plan_status") != "export_plan_ready_not_started":
        blockers.append("plan_status_not_export_plan_ready_not_started")
    if plan.get("future_observation_mode") != "journal_only":
        blockers.append("future_observation_mode_not_journal_only")
    if plan.get("allowed_future_timeframes") != ALLOWED_TIMEFRAMES:
        blockers.append("plan_allowed_timeframes_not_m5_m10")
    if plan.get("real_market_observation_started") is not False:
        blockers.append("plan_real_market_observation_started_not_false")
    if plan.get("mt5_called") is not False:
        blockers.append("plan_mt5_called_not_false")
    if plan.get("data_exported") is not False:
        blockers.append("plan_data_exported_not_false")
    if plan.get("observation_run") is not False:
        blockers.append("plan_observation_run_not_false")
    if plan.get("execution_allowed") is not False:
        blockers.append("plan_execution_allowed_not_false")
    if plan.get("demo_allowed") is not False:
        blockers.append("plan_demo_allowed_not_false")
    if plan.get("live_allowed") is not False:
        blockers.append("plan_live_allowed_not_false")
    if plan.get("repeated_oos_review") is not False:
        blockers.append("plan_repeated_oos_review_not_false")
    if plan.get("candidate_rules_modified") is not False:
        blockers.append("plan_candidate_rules_modified_not_false")

    safety = plan.get("safety", {})
    if not isinstance(safety, dict):
        blockers.append("plan_safety_not_object")
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
                blockers.append(f"plan_safety_{key}_not_false")
    return blockers


def _journal_protocol_blockers(journal_protocol: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if journal_protocol.get("protocol_version") != "v0_31":
        blockers.append("journal_protocol_version_not_v0_31")
    if journal_protocol.get("candidate_id") != CANDIDATE_ID:
        blockers.append("journal_protocol_candidate_id_mismatch")
    if journal_protocol.get("journal_status") != "framework_ready_not_started":
        blockers.append("journal_status_not_framework_ready_not_started")
    if journal_protocol.get("real_market_observation_started") is not False:
        blockers.append("journal_real_market_observation_started_not_false")
    if journal_protocol.get("execution_allowed") is not False:
        blockers.append("journal_execution_allowed_not_false")
    if journal_protocol.get("demo_allowed") is not False:
        blockers.append("journal_demo_allowed_not_false")
    if journal_protocol.get("live_allowed") is not False:
        blockers.append("journal_live_allowed_not_false")
    if journal_protocol.get("repeated_oos_review") is not False:
        blockers.append("journal_repeated_oos_review_not_false")
    if journal_protocol.get("candidate_rules_modified") is not False:
        blockers.append("journal_candidate_rules_modified_not_false")
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


def _candidate_rules_hash_blockers(plan: dict[str, Any], candidate_report: dict[str, Any]) -> list[str]:
    rules = _fixed_rules(candidate_report)
    plan_lock = plan.get("candidate_rules_lock", {})
    if not isinstance(plan_lock, dict):
        return ["plan_candidate_rules_lock_not_object"]
    expected_hash = plan_lock.get("fixed_rules_hash_sha256")
    actual_hash = _stable_hash(rules) if rules else None
    if expected_hash != actual_hash:
        return ["candidate_rules_hash_mismatch"]
    return []


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


def _parse_csv_row(row: dict[str, Any]) -> dict[str, Any]:
    timestamp = _parse_timestamp(row.get("timestamp_utc"))
    if timestamp is None:
        raise ValueError("validated csv row has invalid timestamp")
    return {
        "timestamp": timestamp,
        "symbol": str(row["symbol"]),
        "timeframe": str(row["timeframe"]),
        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"]),
        "tick_volume": float(row["tick_volume"]),
        "spread": float(row["spread"]),
        "source": str(row["source"]),
    }


def _block_ranges(rows: list[dict[str, Any]]) -> dict[str, float]:
    block_values: dict[str, list[dict[str, Any]]] = {
        "block_00_06": [],
        "block_06_12": [],
        "block_12_18": [],
        "block_18_24": [],
    }
    for row in rows:
        block = _block_for_hour(row["timestamp"].hour)
        if block is not None:
            block_values[block].append(row)
    ranges: dict[str, float] = {}
    for block, block_rows in block_values.items():
        if not block_rows:
            continue
        high = max(float(row["high"]) for row in block_rows)
        low = min(float(row["low"]) for row in block_rows)
        ranges[block] = high - low
    return ranges


def _block_for_hour(hour: int) -> str | None:
    if 0 <= hour < 6:
        return "block_00_06"
    if 6 <= hour < 12:
        return "block_06_12"
    if 12 <= hour < 18:
        return "block_12_18"
    if 18 <= hour < 24:
        return "block_18_24"
    return None


def _select_lowest_reference_block(
    block_ranges: dict[str, float],
    fixed_rules: dict[str, Any],
) -> str | None:
    reference_blocks = [block for block in fixed_rules.get("reference_blocks", []) if block in REFERENCE_RESPONSE_PAIRS]
    candidates = [
        block
        for block in reference_blocks
        if block in block_ranges and REFERENCE_RESPONSE_PAIRS[block] in block_ranges
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda block: (block_ranges[block], reference_blocks.index(block)))


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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
        "trade_recommendation_output_allowed": False,
        "new_backtest_allowed": False,
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


def _stable_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
