"""v0_47 train/validation-only executable direction research board."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from math import isinf
from pathlib import Path
from typing import Any, Callable

from src.data.xauusd_low_tf_dataset_catalog import (
    DEFAULT_MANIFEST_PATH,
    build_low_tf_dataset_catalog,
    load_profiler_rows_from_catalog,
)
from src.research import xauusd_session_structure_atlas as atlas

BOARD_VERSION = "v0_47"
SOURCE_FILTER_CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"
DEFAULT_SOURCE_FILTER_REPORT = Path("reports") / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_direction_research_board_v0_47.json"

NO_CANDIDATE_PASSED = "no_direction_candidate_passed"
ONE_CANDIDATE_PASSED = "direction_candidate_passed_train_validation"
BLOCKED_MISSING_DATA = "blocked_missing_required_data"
BOARD_FAILED = "board_failed"

GATE = {
    "train_profit_factor_min": 1.15,
    "validation_profit_factor_min": 1.10,
    "validation_trades_min": 25,
    "train_expectancy_min_exclusive": 0.0,
    "validation_expectancy_min_exclusive": 0.0,
    "max_consecutive_losses_max": 8,
    "oos_used": False,
}

HYPOTHESES = (
    {
        "candidate_id": "expansion_continuation_close_direction",
        "description": "Internal long if the response block closes above the compression high; internal short if it closes below the compression low.",
    },
    {
        "candidate_id": "first_breakout_m5_confirmed_by_m10",
        "description": "Internal long if the first M5 break is above the compression high and the paired M10 response closes above its compression high; internal short on the mirrored downside condition.",
    },
    {
        "candidate_id": "response_block_body_direction",
        "description": "Internal long if the response block closes above its open; internal short if it closes below its open.",
    },
    {
        "candidate_id": "expansion_fade_direction",
        "description": "Internal short after an upside response expansion; internal long after a downside response expansion.",
    },
)


@dataclass(frozen=True)
class DirectionEvent:
    source_timeframe: str
    split: str
    date: str
    reference_window: str
    response_window: str
    next_window: str
    reference_block: dict[str, Any]
    response_block: dict[str, Any]
    next_block: dict[str, Any]
    response_rows: tuple[dict[str, Any], ...]


SideRule = Callable[[DirectionEvent, dict[tuple[str, str, str], DirectionEvent]], str | None]


def build_xauusd_direction_research_board_v0_47(
    *,
    data_dir: str | Path = "data",
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    source_filter_report_path: str | Path = DEFAULT_SOURCE_FILTER_REPORT,
    pattern: str = "xauusd_m*.csv",
) -> dict[str, Any]:
    """Evaluate fixed direction hypotheses on train/validation rows only."""
    source_filter_report, source_blockers = _load_source_filter_report(source_filter_report_path)
    if source_blockers:
        return _blocked_report(source_filter_report_path, source_blockers, source_filter_report)

    catalog = build_low_tf_dataset_catalog(data_dir=data_dir, manifest_path=manifest_path, pattern=pattern)
    rows = [
        row
        for row in load_profiler_rows_from_catalog(catalog)
        if row.get("source_timeframe") in atlas.LOW_TF_ALLOWED and row.get("split") in {"train", "validation"}
    ]
    events = _direction_events(rows)
    blockers: list[str] = []
    if not rows:
        blockers.append("train_validation_m5_m10_rows_missing")
    if not events:
        blockers.append("source_filter_events_with_next_window_missing")
    if blockers:
        return _blocked_report(source_filter_report_path, blockers, source_filter_report, catalog=catalog)

    event_lookup = {
        (event.source_timeframe, event.split, event.date): event
        for event in events
    }
    candidate_results = [
        _evaluate_hypothesis(hypothesis["candidate_id"], events, event_lookup)
        for hypothesis in HYPOTHESES
    ]
    passed = [result for result in candidate_results if result["passed_gate"] is True]
    best = max(candidate_results, key=_candidate_sort_key)

    if len(passed) == 1:
        status = ONE_CANDIDATE_PASSED
        next_step = "create locked directional candidate artifact and then one-time OOS protocol"
    elif len(passed) > 1:
        status = ONE_CANDIDATE_PASSED
        next_step = "select one fixed passing direction candidate for a locked artifact before any one-time OOS protocol"
    else:
        status = NO_CANDIDATE_PASSED
        next_step = "stop this path or design a new non-OOS research candidate"

    return _base_report(
        board_status=status,
        source_filter_report_path=source_filter_report_path,
        source_filter_report=source_filter_report,
        catalog=catalog,
        candidate_results=candidate_results,
        best_candidate=best,
        blockers=[],
        warnings=_warnings(candidate_results),
        next_recommended_step=next_step,
    )


def save_xauusd_direction_research_board(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_source_filter_report(path: str | Path) -> tuple[dict[str, Any] | None, list[str]]:
    report_path = Path(path)
    if not report_path.exists():
        return None, ["source_filter_candidate_report_missing"]
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"source_filter_candidate_report_invalid_json:{exc}"]

    blockers: list[str] = []
    if report.get("candidate_id") != SOURCE_FILTER_CANDIDATE_ID:
        blockers.append("unexpected_source_filter_candidate_id")
    if report.get("splits_used") != ["train", "validation"]:
        blockers.append("source_filter_not_train_validation_only")
    if int(report.get("oos_rows_used", -1) or 0) != 0:
        blockers.append("source_filter_used_oos_rows")
    fixed_rules = report.get("fixed_rules", {})
    if fixed_rules.get("threshold_search_used") is not False:
        blockers.append("source_filter_threshold_search_not_false")
    if fixed_rules.get("parameter_grid_used") is not False:
        blockers.append("source_filter_parameter_grid_not_false")
    if fixed_rules.get("retuning_used") is not False:
        blockers.append("source_filter_retuning_not_false")
    return report, blockers


def _blocked_report(
    source_filter_report_path: str | Path,
    blockers: list[str],
    source_filter_report: dict[str, Any] | None,
    *,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _base_report(
        board_status=BLOCKED_MISSING_DATA,
        source_filter_report_path=source_filter_report_path,
        source_filter_report=source_filter_report,
        catalog=catalog,
        candidate_results=[],
        best_candidate=None,
        blockers=blockers,
        warnings=[],
        next_recommended_step="repair required source filter/data artifacts before direction research board evaluation",
    )


def _direction_events(rows: list[dict[str, Any]]) -> list[DirectionEvent]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        timestamp = datetime.fromisoformat(str(row["timestamp"]))
        key = (str(row["source_timeframe"]), str(row["split"]), timestamp.date().isoformat())
        grouped.setdefault(key, []).append(row)

    ordered_blocks = list(atlas.SESSION_BLOCKS)
    events: list[DirectionEvent] = []
    for source_timeframe, split, day in sorted(grouped):
        day_rows = sorted(grouped[(source_timeframe, split, day)], key=lambda row: str(row["timestamp"]))
        block_rows = {
            name: [
                row
                for row in day_rows
                if datetime.fromisoformat(str(row["timestamp"])).hour in hours
            ]
            for name, hours in atlas.SESSION_BLOCKS.items()
        }
        blocks = {
            name: atlas._window_metrics(block_rows[name])
            for name in ordered_blocks
        }
        available = [
            (index, name, blocks[name])
            for index, name in enumerate(ordered_blocks[:-1])
            if blocks[name]["row_count"] > 0 and blocks[ordered_blocks[index + 1]]["row_count"] > 0
        ]
        if not available:
            continue
        index, reference_name, reference = min(
            available,
            key=lambda item: (float(item[2]["average_bar_range"]), item[0]),
        )
        response_name = ordered_blocks[index + 1]
        next_index = index + 2
        if next_index >= len(ordered_blocks):
            continue
        response = blocks[response_name]
        if response["range"] <= reference["range"]:
            continue
        next_name = ordered_blocks[next_index]
        next_block = blocks[next_name]
        if next_block["row_count"] <= 0 or reference["range"] <= 0:
            continue
        events.append(
            DirectionEvent(
                source_timeframe=source_timeframe,
                split=split,
                date=day,
                reference_window=reference_name,
                response_window=response_name,
                next_window=next_name,
                reference_block=reference,
                response_block=response,
                next_block=next_block,
                response_rows=tuple(block_rows[response_name]),
            )
        )
    return events


def _evaluate_hypothesis(
    candidate_id: str,
    events: list[DirectionEvent],
    event_lookup: dict[tuple[str, str, str], DirectionEvent],
) -> dict[str, Any]:
    side_rule = _side_rules()[candidate_id]
    trades: list[dict[str, Any]] = []
    skipped = 0
    for event in events:
        side = side_rule(event, event_lookup)
        if side is None:
            skipped += 1
            continue
        trades.append(_trade_result(event, side))

    train_metrics = _split_metrics([trade for trade in trades if trade["split"] == "train"])
    validation_metrics = _split_metrics([trade for trade in trades if trade["split"] == "validation"])
    gate_failures = _gate_failures(train_metrics, validation_metrics)
    hypothesis = next(item for item in HYPOTHESES if item["candidate_id"] == candidate_id)
    return {
        "candidate_id": candidate_id,
        "hypothesis_name": candidate_id,
        "hypothesis_description": hypothesis["description"],
        "fixed_before_evaluation": True,
        "source_filter_candidate_id": SOURCE_FILTER_CANDIDATE_ID,
        "metric_horizon": "next_fixed_six_hour_block_after_response_close",
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "combined_trade_count": len(trades),
        "skipped_event_count": skipped,
        "passed_gate": not gate_failures,
        "gate_failures": gate_failures,
        "safety": _safety_flags(),
    }


def _side_rules() -> dict[str, SideRule]:
    return {
        "expansion_continuation_close_direction": _continuation_close_side,
        "first_breakout_m5_confirmed_by_m10": _first_breakout_confirmed_side,
        "response_block_body_direction": _body_side,
        "expansion_fade_direction": _fade_side,
    }


def _continuation_close_side(event: DirectionEvent, _: dict[tuple[str, str, str], DirectionEvent]) -> str | None:
    close = float(event.response_block["close"])
    if close > float(event.reference_block["high"]):
        return "long"
    if close < float(event.reference_block["low"]):
        return "short"
    return None


def _first_breakout_confirmed_side(
    event: DirectionEvent,
    event_lookup: dict[tuple[str, str, str], DirectionEvent],
) -> str | None:
    if event.source_timeframe != "M5":
        return None
    first_break = _first_m5_break(event)
    if first_break is None:
        return None
    m10_event = event_lookup.get(("M10", event.split, event.date))
    if m10_event is None:
        return None
    m10_close = float(m10_event.response_block["close"])
    if first_break == "up" and m10_close > float(m10_event.reference_block["high"]):
        return "long"
    if first_break == "down" and m10_close < float(m10_event.reference_block["low"]):
        return "short"
    return None


def _body_side(event: DirectionEvent, _: dict[tuple[str, str, str], DirectionEvent]) -> str | None:
    close = float(event.response_block["close"])
    open_price = float(event.response_block["open"])
    if close > open_price:
        return "long"
    if close < open_price:
        return "short"
    return None


def _fade_side(event: DirectionEvent, _: dict[tuple[str, str, str], DirectionEvent]) -> str | None:
    close = float(event.response_block["close"])
    if close > float(event.reference_block["high"]):
        return "short"
    if close < float(event.reference_block["low"]):
        return "long"
    return None


def _first_m5_break(event: DirectionEvent) -> str | None:
    reference_high = float(event.reference_block["high"])
    reference_low = float(event.reference_block["low"])
    for row in sorted(event.response_rows, key=lambda item: str(item["timestamp"])):
        broke_up = float(row["high"]) > reference_high
        broke_down = float(row["low"]) < reference_low
        if broke_up and not broke_down:
            return "up"
        if broke_down and not broke_up:
            return "down"
        if broke_up and broke_down:
            return "up" if float(row["close"]) >= float(row["open"]) else "down"
    return None


def _trade_result(event: DirectionEvent, side: str) -> dict[str, Any]:
    direction = 1.0 if side == "long" else -1.0
    raw_move = float(event.next_block["close"]) - float(event.next_block["open"])
    reference_range = max(float(event.reference_block["range"]), 0.0000001)
    return_r = direction * raw_move / reference_range
    return {
        "source_timeframe": event.source_timeframe,
        "split": event.split,
        "date": event.date,
        "side": side,
        "reference_window": event.reference_window,
        "response_window": event.response_window,
        "evaluation_window": event.next_window,
        "return_r": return_r,
        "won": return_r > 0,
    }


def _split_metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(trade["return_r"]) for trade in trades]
    gross_profit = sum(value for value in returns if value > 0)
    gross_loss = abs(sum(value for value in returns if value < 0))
    if not returns:
        profit_factor = 0.0
    elif gross_loss == 0 and gross_profit > 0:
        profit_factor = "inf"
    else:
        profit_factor = gross_profit / gross_loss if gross_loss else 0.0
    return {
        "trades": len(returns),
        "wins": sum(1 for value in returns if value > 0),
        "losses": sum(1 for value in returns if value < 0),
        "win_rate": _rate(sum(1 for value in returns if value > 0), len(returns)),
        "gross_profit_r": gross_profit,
        "gross_loss_r": gross_loss,
        "profit_factor": profit_factor,
        "expectancy_r": sum(returns) / len(returns) if returns else 0.0,
        "max_consecutive_losses": _max_consecutive_losses(returns),
        "timeframe_counts": _counts(trades, "source_timeframe"),
    }


def _gate_failures(train: dict[str, Any], validation: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if _pf_value(train["profit_factor"]) < GATE["train_profit_factor_min"]:
        failures.append("train_profit_factor_below_fixed_gate")
    if _pf_value(validation["profit_factor"]) < GATE["validation_profit_factor_min"]:
        failures.append("validation_profit_factor_below_fixed_gate")
    if int(validation["trades"]) < GATE["validation_trades_min"]:
        failures.append("validation_trades_below_fixed_gate")
    if float(train["expectancy_r"]) <= GATE["train_expectancy_min_exclusive"]:
        failures.append("train_expectancy_not_positive")
    if float(validation["expectancy_r"]) <= GATE["validation_expectancy_min_exclusive"]:
        failures.append("validation_expectancy_not_positive")
    if int(train["max_consecutive_losses"]) > GATE["max_consecutive_losses_max"]:
        failures.append("train_max_consecutive_losses_above_fixed_gate")
    if int(validation["max_consecutive_losses"]) > GATE["max_consecutive_losses_max"]:
        failures.append("validation_max_consecutive_losses_above_fixed_gate")
    return failures


def _base_report(
    *,
    board_status: str,
    source_filter_report_path: str | Path,
    source_filter_report: dict[str, Any] | None,
    catalog: dict[str, Any] | None,
    candidate_results: list[dict[str, Any]],
    best_candidate: dict[str, Any] | None,
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    best_metrics = best_candidate_metrics(best_candidate)
    return {
        "board_version": BOARD_VERSION,
        "board_status": board_status,
        "source_filter_candidate_id": SOURCE_FILTER_CANDIDATE_ID,
        "source_filter_report_path": str(Path(source_filter_report_path)),
        "source_filter_preserved": source_filter_report is not None and not blockers,
        "source_filter_rules_modified": False,
        "train_validation_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "direction_hypotheses_evaluated": [hypothesis["candidate_id"] for hypothesis in HYPOTHESES],
        "fixed_gate": dict(GATE),
        "candidate_results": candidate_results,
        "best_candidate_id": best_candidate.get("candidate_id") if best_candidate else None,
        "best_candidate_metrics": best_metrics,
        "best_candidate_passed_gate": best_candidate.get("passed_gate") if best_candidate else False,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "data_csv_added": False,
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "data_files_used": _data_files_used(catalog) if catalog else [],
        "source_filter_summary": _source_filter_summary(source_filter_report),
        "safety": _safety_flags(),
    }


def best_candidate_metrics(best_candidate: dict[str, Any] | None) -> dict[str, Any] | None:
    if best_candidate is None:
        return None
    return {
        "train": best_candidate["train_metrics"],
        "validation": best_candidate["validation_metrics"],
    }


def _candidate_sort_key(result: dict[str, Any]) -> tuple[bool, float, float, int, float]:
    validation = result["validation_metrics"]
    train = result["train_metrics"]
    return (
        bool(result["passed_gate"]),
        _pf_value(validation["profit_factor"]),
        float(validation["expectancy_r"]),
        int(validation["trades"]),
        _pf_value(train["profit_factor"]),
    )


def _warnings(candidate_results: list[dict[str, Any]]) -> list[str]:
    warnings = [
        "research_only_direction_board_not_demo_execution",
        "combined_m5_m10_counts_are_not_treated_as_independent_oos_evidence",
    ]
    if sum(1 for result in candidate_results if result["passed_gate"] is True) > 1:
        warnings.append("multiple_direction_hypotheses_passed_fixed_train_validation_gate")
    return warnings


def _source_filter_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if report is None:
        return None
    return {
        "candidate_id": report.get("candidate_id"),
        "status": report.get("status"),
        "splits_used": report.get("splits_used"),
        "oos_rows_used": report.get("oos_rows_used"),
        "fixed_rules": report.get("fixed_rules"),
    }


def _safety_flags() -> dict[str, Any]:
    return {
        "research_only": True,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "oos_used": False,
        "repeated_oos_review": False,
        "trade_recommendation_output_present": False,
        "execution_queue_created": False,
    }


def _data_files_used(catalog: dict[str, Any]) -> list[str]:
    return sorted(
        str(entry["filename"])
        for entry in catalog.get("entries", [])
        if entry.get("usable_for_profiler") is True and entry.get("source_timeframe") in atlas.LOW_TF_ALLOWED
    )


def _pf_value(value: Any) -> float:
    if value == "inf":
        return float("inf")
    return float(value or 0.0)


def _json_safe_float(value: float) -> float | str:
    return "inf" if isinf(value) else value


def _max_consecutive_losses(returns: list[float]) -> int:
    max_losses = 0
    current = 0
    for value in returns:
        if value < 0:
            current += 1
            max_losses = max(max_losses, current)
        else:
            current = 0
    return max_losses


def _counts(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item[key])
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0
