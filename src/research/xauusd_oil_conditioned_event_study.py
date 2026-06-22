"""v0_72 oil-conditioned diagnostic event study for prior XAUUSD research."""

from __future__ import annotations

import bisect
import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.research.xauusd_oil_proxy_context_audit import _adapt_row

STUDY_VERSION = "v0_72"
SOURCE_OIL_QUALITY_DESIGN_VERSION = "v0_70"
SOURCE_MACRO_CONTEXT_BOARD_VERSION = "v0_71"
SELECTED_PROXY_SYMBOL = "BRN"
FALLBACK_PROXY_SYMBOL = "WTI"
DEFAULT_OUTPUT = Path("reports") / "xauusd_oil_conditioned_event_study_v0_72.json"
DEFAULT_SOURCE_QUALITY_DESIGN = Path("reports") / "xauusd_oil_proxy_quality_and_label_design_v0_70.json"
DEFAULT_SOURCE_MACRO_BOARD = Path("reports") / "xauusd_gold_macro_context_board_v0_71.json"

COMPLETED = "oil_conditioned_event_study_completed"
COMPLETED_NO_CLEAR_LEADS = "oil_conditioned_event_study_completed_no_clear_leads"
BLOCKED_MISSING_DATA = "oil_conditioned_event_study_blocked_missing_data"

LABEL_NAMES = [
    "oil_strength",
    "oil_weakness",
    "oil_shock_up",
    "oil_shock_down",
    "gold_oil_inflation_pressure_aligned",
    "gold_oil_safe_haven_conflict",
    "oil_supply_shock_context_candidate",
]
PRIOR_RESEARCH_VERSIONS = ["v0_53", "v0_56", "v0_60", "v0_63", "v0_68", "v0_71"]
NO_CLEAR_LEAD_NEXT_STEP = "v0_73_yield_real_yield_context_feasibility_no_strategy"
CLEAR_LEAD_NEXT_STEP = "v0_73_oil_conditioned_research_board_no_oos_no_strategy_change"

SAFETY_FALSE_FLAGS = [
    "labels_used_as_trade_blockers",
    "labels_used_for_strategy_testing",
    "approved_for_strategy_testing",
    "approved_for_trade_filtering",
    "aligned_dataset_created",
    "data_csv_touched",
    "lookahead_risk_detected",
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
]


def build_xauusd_oil_conditioned_event_study_v0_72(
    *,
    root: str | Path = ".",
    source_quality_design_path: str | Path = DEFAULT_SOURCE_QUALITY_DESIGN,
    source_macro_board_path: str | Path = DEFAULT_SOURCE_MACRO_BOARD,
    event_records: list[dict[str, Any]] | None = None,
    proxy_rows: Iterable[Any] | None = None,
    attempt_mt5_readonly: bool = True,
    mt5_module: Any | None = None,
) -> dict[str, Any]:
    """Build an aggregate oil-conditioned diagnostic report without rule changes."""
    root_path = Path(root)
    quality_design = _read_json(_resolve(root_path, source_quality_design_path))
    macro_board = _read_json(_resolve(root_path, source_macro_board_path))
    source_blockers = _source_blockers(quality_design, macro_board)
    source_reports = _source_report_summaries(root_path)
    events = event_records if event_records is not None else _load_prior_event_records(root_path)
    proxy_detail = (
        _proxy_detail_from_rows(proxy_rows, attempted=False)
        if proxy_rows is not None
        else (
            _discover_mt5_proxy_rows(SELECTED_PROXY_SYMBOL, mt5_module=mt5_module)
            if attempt_mt5_readonly
            else _empty_proxy_detail(attempted=False)
        )
    )

    if source_blockers or not events or not proxy_detail["rows"]:
        blockers = list(source_blockers)
        if not events:
            blockers.append("no_prior_train_validation_event_samples_available")
        if not proxy_detail["rows"]:
            blockers.extend(proxy_detail["summary"].get("blockers") or ["selected_proxy_rows_unavailable"])
        return _base_report(
            study_status=BLOCKED_MISSING_DATA,
            event_count=0,
            source_reports=source_reports,
            label_conditioned_summary=_empty_label_summary(),
            strongest_diagnostic_observations=[],
            clear_leads=[],
            proxy_summary=proxy_detail["summary"],
            blockers=sorted(set(blockers)),
        )

    label_context = _proxy_label_context(proxy_detail["rows"])
    labeled_events = []
    lookahead_detected = False
    for event in events:
        timestamp = _parse_timestamp(event.get("entry_timestamp") or event.get("timestamp"))
        if timestamp is None:
            continue
        context = _asof_context(timestamp, label_context)
        if context is None:
            continue
        if context["proxy_timestamp"] > timestamp:
            lookahead_detected = True
            continue
        labeled_events.append({**event, "oil_labels": context["labels"], "proxy_timestamp": _format_ts(context["proxy_timestamp"])})

    summary = _label_conditioned_summary(labeled_events)
    observations = _strongest_observations(summary)
    clear_leads = [item for item in observations if item["diagnostic_strength"] == "clear_train_validation_pattern"]
    status = COMPLETED if clear_leads else COMPLETED_NO_CLEAR_LEADS
    if lookahead_detected:
        status = BLOCKED_MISSING_DATA

    report = _base_report(
        study_status=status,
        event_count=len(labeled_events),
        source_reports=source_reports,
        label_conditioned_summary=summary,
        strongest_diagnostic_observations=observations,
        clear_leads=clear_leads,
        proxy_summary=proxy_detail["summary"],
        blockers=["lookahead_risk_detected"] if lookahead_detected else [],
    )
    report["lookahead_risk_detected"] = lookahead_detected
    report["safety"]["lookahead_risk_detected"] = lookahead_detected
    report["recommended_next_step"] = CLEAR_LEAD_NEXT_STEP if clear_leads else NO_CLEAR_LEAD_NEXT_STEP
    return report


def save_xauusd_oil_conditioned_event_study(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_backward_asof_safe(event_timestamp: Any, proxy_timestamp: Any) -> None:
    event_time = _parse_timestamp(event_timestamp)
    proxy_time = _parse_timestamp(proxy_timestamp)
    if event_time and proxy_time and proxy_time > event_time:
        raise ValueError("future proxy timestamp is not allowed in v0_72 oil-conditioned event study")


def _load_prior_event_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for version, filename in (
        ("v0_53", "xauusd_external_shortlist_board_v0_53.json"),
        ("v0_60", "xauusd_second_tier_board_v0_60.json"),
    ):
        report = _read_json(_report_path(root, filename))
        if not isinstance(report, dict):
            continue
        for candidate in report.get("candidate_results", []):
            if not isinstance(candidate, dict):
                continue
            candidate_id = str(candidate.get("candidate_id") or "unknown_candidate")
            for sample in candidate.get("trade_sample", []):
                if isinstance(sample, dict) and sample.get("split") in {"train", "validation"}:
                    records.append({**sample, "source_research_version": version, "candidate_id": candidate_id})
    return records


def _source_report_summaries(root: Path) -> dict[str, Any]:
    paths = {
        "v0_53": "xauusd_external_shortlist_board_v0_53.json",
        "v0_56": "xauusd_session_block_bias_eval_v0_56.json",
        "v0_60": "xauusd_second_tier_board_v0_60.json",
        "v0_63": "xauusd_context_labeled_event_study_v0_63.json",
        "v0_68": "xauusd_dxy_conditioned_event_study_v0_68.json",
        "v0_71": "xauusd_gold_macro_context_board_v0_71.json",
    }
    summaries: dict[str, Any] = {}
    for version, filename in paths.items():
        path = _report_path(root, filename)
        report = _read_json(path)
        summaries[version] = {
            "report": str(path.as_posix()) if path.exists() else None,
            "available": isinstance(report, dict),
            "status": _first_present(report or {}, "board_status", "evaluation_status", "context_study_status", "study_status"),
            "train_validation_only": (report or {}).get("train_validation_only"),
            "oos_used": (report or {}).get("oos_used"),
            "event_samples_available": version in {"v0_53", "v0_60"} and isinstance(report, dict),
        }
    return summaries


def _proxy_label_context(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parsed = sorted(rows, key=lambda row: row["timestamp"])
    returns = []
    ranges = []
    for index in range(1, len(parsed)):
        previous = parsed[index - 1]
        current = parsed[index]
        if previous["close"] > 0:
            returns.append((current["close"] - previous["close"]) / previous["close"])
        if current["close"] > 0:
            ranges.append((current["high"] - current["low"]) / current["close"])
    nonzero_abs = sorted(abs(value) for value in returns if value != 0.0)
    shock_cutoff = (nonzero_abs[len(nonzero_abs) // 2] * 2.0) if nonzero_abs else float("inf")
    range_cutoff = (sorted(ranges)[len(ranges) // 2] * 1.5) if ranges else float("inf")

    contexts = []
    for index, row in enumerate(parsed):
        labels = []
        oil_return = 0.0
        proxy_range = (row["high"] - row["low"]) / row["close"] if row["close"] > 0 else 0.0
        if index > 0:
            previous = parsed[index - 1]
            oil_return = (row["close"] - previous["close"]) / previous["close"] if previous["close"] > 0 else 0.0
            if oil_return > 0:
                labels.append("oil_strength")
            elif oil_return < 0:
                labels.append("oil_weakness")
            if oil_return >= shock_cutoff:
                labels.append("oil_shock_up")
            elif oil_return <= -shock_cutoff:
                labels.append("oil_shock_down")
            if abs(oil_return) >= shock_cutoff and proxy_range >= range_cutoff:
                labels.append("oil_supply_shock_context_candidate")
        contexts.append({"proxy_timestamp": row["timestamp"], "labels": labels, "oil_return": oil_return})
    return contexts


def _asof_context(event_timestamp: datetime, contexts: list[dict[str, Any]]) -> dict[str, Any] | None:
    timestamps = [item["proxy_timestamp"] for item in contexts]
    index = bisect.bisect_right(timestamps, event_timestamp) - 1
    if index < 0:
        return None
    context = contexts[index]
    assert_backward_asof_safe(event_timestamp, context["proxy_timestamp"])
    return context


def _label_conditioned_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_label: dict[str, list[dict[str, Any]]] = {label: [] for label in LABEL_NAMES}
    for event in events:
        for label in event.get("oil_labels", []):
            if label in by_label:
                by_label[label].append(event)
    return {label: _label_summary(label, label_events) for label, label_events in by_label.items()}


def _label_summary(label: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    train = [event for event in events if event.get("split") == "train"]
    validation = [event for event in events if event.get("split") == "validation"]
    return {
        "label": label,
        "event_count": len(events),
        "train_event_count": len(train),
        "validation_event_count": len(validation),
        "candidate_count": len({event.get("candidate_id") for event in events if event.get("candidate_id")}),
        "source_versions": sorted({str(event.get("source_research_version")) for event in events if event.get("source_research_version")}),
        "train_average_return_r": _average_return(train),
        "validation_average_return_r": _average_return(validation),
        "positive_outcome_share_train": _positive_share(train),
        "positive_outcome_share_validation": _positive_share(validation),
        "diagnostic_note": _diagnostic_note(train, validation),
    }


def _strongest_observations(summary: dict[str, Any]) -> list[dict[str, Any]]:
    observations = []
    for label, item in summary.items():
        if item["event_count"] <= 0:
            continue
        train_count = item["train_event_count"]
        validation_count = item["validation_event_count"]
        train_avg = float(item["train_average_return_r"] or 0.0)
        validation_avg = float(item["validation_average_return_r"] or 0.0)
        strength = "descriptive_only"
        if train_count >= 3 and validation_count >= 3 and train_avg > 0.0 and validation_avg > 0.0:
            strength = "clear_train_validation_pattern"
        elif train_count > 0 and validation_count > 0 and (train_avg > 0.0 or validation_avg > 0.0):
            strength = "weak_or_mixed_pattern"
        observations.append(
            {
                "label": label,
                "event_count": item["event_count"],
                "train_event_count": train_count,
                "validation_event_count": validation_count,
                "candidate_count": item["candidate_count"],
                "train_average_return_r": item["train_average_return_r"],
                "validation_average_return_r": item["validation_average_return_r"],
                "diagnostic_strength": strength,
                "observation_scope": "aggregate_train_validation_diagnostic_only_not_strategy",
            }
        )
    return sorted(
        observations,
        key=lambda item: (
            item["diagnostic_strength"] == "clear_train_validation_pattern",
            item["event_count"],
            float(item["validation_average_return_r"] or 0.0),
        ),
        reverse=True,
    )[:10]


def _base_report(
    *,
    study_status: str,
    event_count: int,
    source_reports: dict[str, Any],
    label_conditioned_summary: dict[str, Any],
    strongest_diagnostic_observations: list[dict[str, Any]],
    clear_leads: list[dict[str, Any]],
    proxy_summary: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "study_version": STUDY_VERSION,
        "study_status": study_status,
        "source_oil_quality_design_version": SOURCE_OIL_QUALITY_DESIGN_VERSION,
        "source_macro_context_board_version": SOURCE_MACRO_CONTEXT_BOARD_VERSION,
        "selected_proxy_symbol": SELECTED_PROXY_SYMBOL,
        "fallback_proxy_symbol": FALLBACK_PROXY_SYMBOL,
        "labels_evaluated": list(LABEL_NAMES),
        "prior_research_versions_considered": list(PRIOR_RESEARCH_VERSIONS),
        "prior_research_source_reports": source_reports,
        "proxy_readonly_summary": proxy_summary,
        "train_validation_only": True,
        "oos_used": False,
        "event_count": event_count,
        "label_conditioned_summary": label_conditioned_summary,
        "strongest_diagnostic_observations": strongest_diagnostic_observations,
        "clear_lead_count": len(clear_leads),
        "clear_leads": clear_leads,
        "aligned_dataset_created": False,
        "data_csv_touched": False,
        "recommended_next_step": CLEAR_LEAD_NEXT_STEP if clear_leads else NO_CLEAR_LEAD_NEXT_STEP,
        "blockers": blockers,
        "warnings": [
            "diagnostic_research_only_not_strategy",
            "oil_labels_are_not_trade_blockers",
            "prior_outcomes_are_train_validation_only_where_available",
            "persistent_aligned_market_csv_not_created",
        ],
        "safety": _safety_flags(),
    }
    report.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return report


def _empty_label_summary() -> dict[str, Any]:
    return {label: _label_summary(label, []) for label in LABEL_NAMES}


def _safety_flags() -> dict[str, bool]:
    flags = {
        "research_only": True,
        "diagnostic_event_study_only": True,
        "strategy_rules_created": False,
        "strategy_rules_modified": False,
        "trade_signals_output": False,
        "persistent_market_dataset_created": False,
        "train_validation_only": True,
        "oos_used": False,
    }
    flags.update({flag: False for flag in SAFETY_FALSE_FLAGS})
    return flags


def _source_blockers(quality_design: Any, macro_board: Any) -> list[str]:
    blockers = []
    if not isinstance(quality_design, dict) or quality_design.get("design_version") != SOURCE_OIL_QUALITY_DESIGN_VERSION:
        blockers.append("missing_or_invalid_v0_70_oil_quality_design")
    else:
        if quality_design.get("selected_proxy_symbol_or_null") != SELECTED_PROXY_SYMBOL:
            blockers.append("v0_70_selected_proxy_not_BRN")
        defined = [item.get("label_name") for item in quality_design.get("labels_defined", []) if isinstance(item, dict)]
        missing = sorted(set(LABEL_NAMES).difference(defined))
        if missing:
            blockers.append(f"v0_70_missing_oil_labels:{','.join(missing)}")
    if not isinstance(macro_board, dict) or macro_board.get("board_version") != SOURCE_MACRO_CONTEXT_BOARD_VERSION:
        blockers.append("missing_or_invalid_v0_71_macro_context_board")
    elif macro_board.get("next_research_step") != "v0_72_oil_conditioned_event_study_no_strategy":
        blockers.append("v0_71_did_not_select_oil_event_study")
    return blockers


def _discover_mt5_proxy_rows(symbol: str, *, mt5_module: Any | None) -> dict[str, Any]:
    mt5 = mt5_module
    if mt5 is None:
        try:
            mt5 = importlib.import_module("MetaTrader5")
        except ImportError:
            return _empty_proxy_detail(attempted=True, status="metatrader5_package_unavailable", blockers=["metatrader5_package_unavailable"])
    initialized = False
    shutdown_called = False
    try:
        if not mt5.initialize():
            return _empty_proxy_detail(attempted=True, status="mt5_initialize_failed", blockers=["mt5_initialize_failed"])
        initialized = True
        mt5_timeframe = getattr(mt5, "TIMEFRAME_M15", None)
        copy_rates = getattr(mt5, "copy_rates_from_pos", None)
        available = sorted({_symbol_name(item) for item in (mt5.symbols_get() or []) if _symbol_name(item)})
        rows = []
        if symbol in available and mt5_timeframe is not None and callable(copy_rates):
            copied = copy_rates(symbol, mt5_timeframe, 0, 10000)
            rows = list(copied) if copied is not None else []
        mt5.shutdown()
        shutdown_called = True
        detail = _proxy_detail_from_rows(rows, attempted=True)
        has_rows = bool(detail["rows"])
        detail["summary"].update(
            {
                "status": "readonly_proxy_rows_loaded" if has_rows else "selected_proxy_rows_unavailable",
                "mt5_initialized": initialized,
                "mt5_shutdown_called": shutdown_called,
                "candidate_symbols_available": [item for item in (SELECTED_PROXY_SYMBOL, FALLBACK_PROXY_SYMBOL) if item in available],
                "fallback_proxy_symbol": FALLBACK_PROXY_SYMBOL,
                "fallback_metadata_only": True,
                "fallback_attempted": False,
                "order_send_called": False,
                "order_check_called": False,
                "blockers": [] if has_rows else ["selected_proxy_rows_unavailable"],
            }
        )
        return detail
    except Exception as exc:
        if initialized and not shutdown_called:
            mt5.shutdown()
            shutdown_called = True
        return _empty_proxy_detail(
            attempted=True,
            status="mt5_readonly_proxy_rows_failed",
            initialized=initialized,
            shutdown_called=shutdown_called,
            blockers=[f"mt5_readonly_proxy_rows_exception:{type(exc).__name__}:{exc}"],
        )


def _proxy_detail_from_rows(rows: Iterable[Any], *, attempted: bool) -> dict[str, Any]:
    raw_rows = list(rows)
    parsed = []
    timestamps = []
    seen = set()
    duplicates = 0
    invalid_ohlc = 0
    required_present = 0
    for row in raw_rows:
        if _has_required_row_fields(row):
            required_present += 1
        adapted = _adapt_row(row, symbol=SELECTED_PROXY_SYMBOL, timeframe="M15", source="injected_proxy_rows")
        timestamp = _parse_timestamp(_row_value(row, "time") or _row_value(row, "timestamp") or _row_value(row, "timestamp_utc"))
        if timestamp is not None:
            timestamps.append(timestamp)
            if timestamp in seen:
                duplicates += 1
            seen.add(timestamp)
        if adapted is None:
            if timestamp is not None or _has_required_row_fields(row):
                invalid_ohlc += 1
            continue
        parsed.append(adapted)
    parsed = sorted(parsed, key=lambda item: item["timestamp"])
    monotonic = all(current >= previous for previous, current in zip(timestamps, timestamps[1:])) if timestamps else None
    return {
        "rows": parsed,
        "summary": {
            "attempted": attempted,
            "status": "injected_proxy_rows_loaded" if parsed else "selected_proxy_rows_unavailable",
            "selected_proxy_symbol": SELECTED_PROXY_SYMBOL,
            "fallback_proxy_symbol": FALLBACK_PROXY_SYMBOL,
            "fallback_metadata_only": True,
            "timeframe": "M15",
            "row_count": len(parsed),
            "alignment_storage": "in_memory_only",
            "allowed_join_direction": "backward",
            "persistent_aligned_csv_created": False,
            "order_send_called": False,
            "order_check_called": False,
            "adapter_version": "v0_72_oil_proxy_row_adapter_in_memory",
            "copied_row_count": len(raw_rows),
            "parseable_row_count": len(parsed),
            "first_timestamp": _format_ts(parsed[0]["timestamp"]) if parsed else None,
            "last_timestamp": _format_ts(parsed[-1]["timestamp"]) if parsed else None,
            "required_columns_present": bool(raw_rows) and required_present == len(raw_rows),
            "invalid_ohlc_count": invalid_ohlc,
            "duplicate_timestamp_count": duplicates,
            "monotonic_timestamp_order": monotonic,
            "reason_if_unparseable": None if parsed else "selected_proxy_rows_unavailable",
            "fallback_attempted": False,
            "blockers": [] if parsed else ["selected_proxy_rows_unavailable"],
        },
    }


def _empty_proxy_detail(
    *,
    attempted: bool,
    status: str = "not_attempted",
    initialized: bool = False,
    shutdown_called: bool = False,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "rows": [],
        "summary": {
            "attempted": attempted,
            "status": status,
            "selected_proxy_symbol": SELECTED_PROXY_SYMBOL,
            "fallback_proxy_symbol": FALLBACK_PROXY_SYMBOL,
            "fallback_metadata_only": True,
            "timeframe": "M15",
            "row_count": 0,
            "alignment_storage": "in_memory_only",
            "allowed_join_direction": "backward",
            "persistent_aligned_csv_created": False,
            "mt5_initialized": initialized,
            "mt5_shutdown_called": shutdown_called,
            "order_send_called": False,
            "order_check_called": False,
            "fallback_attempted": False,
            "blockers": blockers or [],
        },
    }


def _average_return(events: list[dict[str, Any]]) -> float:
    values = [_number_or_none(event.get("return_r")) for event in events]
    clean = [float(value) for value in values if value is not None]
    return sum(clean) / len(clean) if clean else 0.0


def _positive_share(events: list[dict[str, Any]]) -> float:
    values = [_number_or_none(event.get("return_r")) for event in events]
    clean = [float(value) for value in values if value is not None]
    return sum(1 for value in clean if value > 0.0) / len(clean) if clean else 0.0


def _diagnostic_note(train: list[dict[str, Any]], validation: list[dict[str, Any]]) -> str:
    if not train and not validation:
        return "label did not occur in the available event sample"
    if len(train) < 3 or len(validation) < 3:
        return "aggregate label slice is descriptive only because train/validation sample is small"
    if _average_return(train) > 0.0 and _average_return(validation) > 0.0:
        return "aggregate label slice has a train/validation diagnostic pattern only, not an approval gate"
    return "aggregate label slice does not show a clear train/validation diagnostic pattern"


def _report_path(root: Path, filename: str) -> Path:
    active = root / "reports" / filename
    if active.exists():
        return active
    return root / "project_archive" / "retired_v0_64_1" / "reports" / filename


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _row_value(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    try:
        return row[key]
    except (KeyError, TypeError, IndexError, ValueError):
        return getattr(row, key, None)


def _has_required_row_fields(row: Any) -> bool:
    return any(_row_value(row, key) not in (None, "") for key in ("time", "timestamp", "timestamp_utc")) and all(
        _row_value(row, key) not in (None, "") for key in ("open", "high", "low", "close")
    )


def _number_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(tzinfo=None)
        except (OSError, OverflowError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _format_ts(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _symbol_name(item: Any) -> str | None:
    name = getattr(item, "name", None)
    return str(name) if name else None
