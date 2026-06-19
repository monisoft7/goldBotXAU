"""v0_51 fixed-rule expanded train/validation-equivalent retest."""

from __future__ import annotations

import importlib
import json
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

from src.research import xauusd_new_directional_strategy_discovery_board as board_v0_48
from src.research.xauusd_historical_data_expansion_feasibility_audit import (
    MT5_TIMEFRAME_NAMES,
)

RETEST_VERSION = "v0_51"
CANDIDATE_ID = "trend_pullback_continuation_directional"
SOURCE_CANDIDATE_BOARD_VERSION = "v0_48"
SOURCE_STABILITY_AUDIT_VERSION = "v0_49"
SOURCE_DATA_FEASIBILITY_VERSION = "v0_50"
DEFAULT_SOURCE_BOARD = Path("reports") / "xauusd_new_directional_discovery_v0_48.json"
DEFAULT_SOURCE_STABILITY_AUDIT = Path("reports") / "xauusd_trend_pullback_stability_audit_v0_49.json"
DEFAULT_SOURCE_DATA_FEASIBILITY = Path("reports") / "xauusd_historical_data_expansion_feasibility_v0_50.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_trend_pullback_expanded_retest_v0_51.json"
DEFAULT_TIMEFRAMES = ("M5", "M10")

EXPANDED_EVIDENCE_PASSED = "expanded_evidence_passed_pre_oos_locking_gate"
EXPANDED_EVIDENCE_FAILED = "expanded_evidence_failed"
BLOCKED_MISSING_EXPANSION_DATA = "blocked_missing_expansion_data"
RETEST_FAILED = "retest_failed"

VALIDATION_TRADE_MINIMUM = int(board_v0_48.GATE["validation_trades_min"])
EXPANDED_PROFIT_FACTOR_MINIMUM = 1.20
EXPANDED_TRADE_MINIMUM = 50
MIN_CALENDAR_YEARS_WITH_TRADES = 3
MAX_SINGLE_YEAR_TRADE_SHARE = 0.50
CATASTROPHIC_YEAR_LOSS_R = -10.0
CATASTROPHIC_YEAR_PROFIT_FACTOR = 0.50


def build_xauusd_trend_pullback_expanded_retest_v0_51(
    *,
    symbol: str = "XAUUSD",
    from_date: str,
    to_date: str,
    mt5_module: Any | None = None,
    timeframes: tuple[str, ...] = DEFAULT_TIMEFRAMES,
    source_board_path: str | Path = DEFAULT_SOURCE_BOARD,
    source_stability_audit_path: str | Path = DEFAULT_SOURCE_STABILITY_AUDIT,
    source_data_feasibility_path: str | Path = DEFAULT_SOURCE_DATA_FEASIBILITY,
) -> dict[str, Any]:
    """Retest the fixed v0_48 trend-pullback rule on older read-only candles."""
    source_board = _read_json(Path(source_board_path))
    source_stability = _read_json(Path(source_stability_audit_path))
    source_feasibility = _read_json(Path(source_data_feasibility_path))
    source_blockers = _source_blockers(source_board, source_stability, source_feasibility)

    mt5_initialized = False
    mt5_shutdown_called = False
    try:
        rows_result = _load_mt5_rows(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            mt5_module=mt5_module,
            timeframes=timeframes,
        )
        rows = rows_result["rows"]
        mt5_initialized = rows_result["mt5_initialized"]
        mt5_shutdown_called = rows_result["mt5_shutdown_called"]
        candle_count_by_timeframe = rows_result["candle_count_by_timeframe"]
        expanded_range_from = rows_result["expanded_range_from"]
        expanded_range_to = rows_result["expanded_range_to"]
        blockers = [*source_blockers, *rows_result["blockers"]]
        warnings = [*rows_result["warnings"]]

        if blockers or not rows:
            return _base_report(
                retest_status=BLOCKED_MISSING_EXPANSION_DATA,
                symbol=symbol,
                expanded_range_from=expanded_range_from,
                expanded_range_to=expanded_range_to,
                candle_count_by_timeframe=candle_count_by_timeframe,
                mt5_initialized=mt5_initialized,
                mt5_shutdown_called=mt5_shutdown_called,
                trades=[],
                expanded_metrics={},
                metrics_by_year={},
                metrics_by_month={},
                metrics_by_timeframe={},
                metrics_by_side={},
                gate={},
                sample_concentration_risk=_empty_concentration_risk(),
                expanded_evidence_passed_gate=False,
                candidate_locking_allowed_pre_oos=False,
                blockers=blockers,
                warnings=warnings,
                next_recommended_step="repair source artifacts or read-only expansion data before rerunning v0_51",
            )

        profiles = board_v0_48._day_profiles(rows)
        trades = _trend_pullback_trades(profiles)
        expanded_metrics = board_v0_48._split_metrics(trades)
        metrics_by_year = _metrics_by_key(trades, "year")
        metrics_by_month = _metrics_by_key(trades, "month")
        metrics_by_timeframe = _metrics_by_key(trades, "source_timeframe")
        metrics_by_side = _metrics_by_key(trades, "side")
        concentration = _sample_concentration_risk(trades)
        gate = _expanded_gate(
            expanded_metrics=expanded_metrics,
            metrics_by_year=metrics_by_year,
            trade_distribution_by_year=_distribution(trades, "year"),
        )
        expanded_evidence_passed = gate["passed"]
        retest_status = EXPANDED_EVIDENCE_PASSED if expanded_evidence_passed else EXPANDED_EVIDENCE_FAILED
        next_step = (
            "create locked candidate artifact and one-time OOS protocol"
            if expanded_evidence_passed
            else "stop trend_pullback branch or broaden non-OOS research"
        )

        return _base_report(
            retest_status=retest_status,
            symbol=symbol,
            expanded_range_from=expanded_range_from,
            expanded_range_to=expanded_range_to,
            candle_count_by_timeframe=candle_count_by_timeframe,
            mt5_initialized=mt5_initialized,
            mt5_shutdown_called=mt5_shutdown_called,
            trades=trades,
            expanded_metrics=expanded_metrics,
            metrics_by_year=metrics_by_year,
            metrics_by_month=metrics_by_month,
            metrics_by_timeframe=metrics_by_timeframe,
            metrics_by_side=metrics_by_side,
            gate=gate,
            sample_concentration_risk=concentration,
            expanded_evidence_passed_gate=expanded_evidence_passed,
            candidate_locking_allowed_pre_oos=expanded_evidence_passed,
            blockers=gate["failures"],
            warnings=[
                "expanded_retest_only_no_oos_no_demo_promotion",
                "candidate_rules_reconstructed_from_v0_48_fixed_family_rule",
                *warnings,
                *concentration["warnings"],
            ],
            next_recommended_step=next_step,
        )
    except Exception as exc:
        return _base_report(
            retest_status=RETEST_FAILED,
            symbol=symbol,
            expanded_range_from=None,
            expanded_range_to=None,
            candle_count_by_timeframe={timeframe: 0 for timeframe in timeframes},
            mt5_initialized=mt5_initialized,
            mt5_shutdown_called=mt5_shutdown_called,
            trades=[],
            expanded_metrics={},
            metrics_by_year={},
            metrics_by_month={},
            metrics_by_timeframe={},
            metrics_by_side={},
            gate={},
            sample_concentration_risk=_empty_concentration_risk(),
            expanded_evidence_passed_gate=False,
            candidate_locking_allowed_pre_oos=False,
            blockers=[f"retest_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair retest implementation or input data before deciding",
        )


def save_xauusd_trend_pullback_expanded_retest(report: dict[str, Any], output: str | Path = DEFAULT_OUTPUT) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_mt5_rows(
    *,
    symbol: str,
    from_date: str,
    to_date: str,
    mt5_module: Any | None,
    timeframes: tuple[str, ...],
) -> dict[str, Any]:
    normalized_symbol = symbol.strip()
    requested_from = _date_start_utc(from_date)
    requested_to = _date_end_utc(to_date)
    blockers: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    mt5_initialized = False
    mt5_shutdown_called = False

    mt5 = mt5_module
    if mt5 is None:
        try:
            mt5 = importlib.import_module("MetaTrader5")
        except ImportError:
            blockers.append("metatrader5_package_unavailable")
            return _rows_result(rows, timeframes, mt5_initialized, mt5_shutdown_called, blockers, warnings)

    if not mt5.initialize():
        blockers.append(_last_error_text(mt5))
        return _rows_result(rows, timeframes, mt5_initialized, mt5_shutdown_called, blockers, warnings)
    mt5_initialized = True

    try:
        if mt5.symbol_info(normalized_symbol) is None:
            blockers.append(f"symbol_unavailable:{normalized_symbol}")
            return _rows_result(rows, timeframes, mt5_initialized, mt5_shutdown_called, blockers, warnings)
        if not mt5.symbol_select(normalized_symbol, True):
            blockers.append(f"symbol_select_failed:{normalized_symbol}")
            return _rows_result(rows, timeframes, mt5_initialized, mt5_shutdown_called, blockers, warnings)

        for timeframe in timeframes:
            mt5_timeframe = getattr(mt5, MT5_TIMEFRAME_NAMES[timeframe])
            rates = mt5.copy_rates_range(normalized_symbol, mt5_timeframe, requested_from, requested_to)
            timeframe_rows = [_rate_to_row(rate, timeframe=timeframe) for rate in ([] if rates is None else list(rates))]
            rows.extend(timeframe_rows)
            if not timeframe_rows:
                warnings.append(f"no_expanded_candles_loaded_for_{timeframe}")
    finally:
        mt5.shutdown()
        mt5_shutdown_called = True

    return _rows_result(rows, timeframes, mt5_initialized, mt5_shutdown_called, blockers, warnings)


def _rows_result(
    rows: list[dict[str, Any]],
    timeframes: tuple[str, ...],
    mt5_initialized: bool,
    mt5_shutdown_called: bool,
    blockers: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    sorted_rows = sorted(rows, key=lambda row: (str(row["source_timeframe"]), str(row["timestamp"])))
    timestamps = [str(row["timestamp"]) for row in sorted_rows]
    candle_count_by_timeframe = {
        timeframe: sum(1 for row in sorted_rows if row["source_timeframe"] == timeframe) for timeframe in timeframes
    }
    if not sorted_rows and "no_expanded_train_validation_equivalent_rows_loaded" not in blockers:
        blockers.append("no_expanded_train_validation_equivalent_rows_loaded")
    return {
        "rows": sorted_rows,
        "mt5_initialized": mt5_initialized,
        "mt5_shutdown_called": mt5_shutdown_called,
        "candle_count_by_timeframe": candle_count_by_timeframe,
        "expanded_range_from": min(timestamps) if timestamps else None,
        "expanded_range_to": max(timestamps) if timestamps else None,
        "blockers": blockers,
        "warnings": warnings,
    }


def _rate_to_row(rate: Any, *, timeframe: str) -> dict[str, Any]:
    timestamp = datetime.fromtimestamp(int(_rate_value(rate, "time")), UTC).replace(tzinfo=None)
    return {
        "timestamp": timestamp.isoformat(),
        "open": float(_rate_value(rate, "open")),
        "high": float(_rate_value(rate, "high")),
        "low": float(_rate_value(rate, "low")),
        "close": float(_rate_value(rate, "close")),
        "volume": float(_optional_rate_value(rate, "tick_volume", 0.0)),
        "source_timeframe": timeframe,
        "split": "expanded_train_validation",
    }


def _trend_pullback_trades(profiles: list[board_v0_48.DayProfile]) -> list[dict[str, Any]]:
    rule = board_v0_48._family_rules()[CANDIDATE_ID]
    trades: list[dict[str, Any]] = []
    for profile in profiles:
        for signal in rule(profile):
            trade = board_v0_48._trade_result(signal)
            trade["year"] = trade["date"][:4]
            trade["month"] = trade["date"][:7]
            trade["session_or_block"] = f"{trade['signal_window']}->{trade['evaluation_window']}"
            trades.append(trade)
    return sorted(trades, key=lambda trade: (trade["date"], trade["source_timeframe"], trade["side"]))


def _base_report(
    *,
    retest_status: str,
    symbol: str,
    expanded_range_from: str | None,
    expanded_range_to: str | None,
    candle_count_by_timeframe: dict[str, int],
    mt5_initialized: bool,
    mt5_shutdown_called: bool,
    trades: list[dict[str, Any]],
    expanded_metrics: dict[str, Any],
    metrics_by_year: dict[str, Any],
    metrics_by_month: dict[str, Any],
    metrics_by_timeframe: dict[str, Any],
    metrics_by_side: dict[str, Any],
    gate: dict[str, Any],
    sample_concentration_risk: dict[str, Any],
    expanded_evidence_passed_gate: bool,
    candidate_locking_allowed_pre_oos: bool,
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    return {
        "retest_version": RETEST_VERSION,
        "retest_status": retest_status,
        "symbol": symbol,
        "candidate_id": CANDIDATE_ID,
        "source_candidate_board_version": SOURCE_CANDIDATE_BOARD_VERSION,
        "source_stability_audit_version": SOURCE_STABILITY_AUDIT_VERSION,
        "source_data_feasibility_version": SOURCE_DATA_FEASIBILITY_VERSION,
        "candidate_rules_preserved": True,
        "expanded_range_from": expanded_range_from,
        "expanded_range_to": expanded_range_to,
        "train_validation_equivalent_only": True,
        "oos_used": False,
        "repeated_oos_review": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "mt5_read_only": True,
        "mt5_initialized": mt5_initialized,
        "mt5_shutdown_called": mt5_shutdown_called,
        "candle_count_by_timeframe": candle_count_by_timeframe,
        "expanded_metrics": expanded_metrics,
        "metrics_by_year": metrics_by_year,
        "metrics_by_month": metrics_by_month,
        "metrics_by_timeframe": metrics_by_timeframe,
        "metrics_by_side": metrics_by_side,
        "side_distribution": _distribution(trades, "side"),
        "trade_distribution_by_year": _distribution(trades, "year"),
        "trade_distribution_by_month": _distribution(trades, "month"),
        "sample_concentration_risk": sample_concentration_risk,
        "validation_trade_minimum": VALIDATION_TRADE_MINIMUM,
        "expanded_trade_count": int(expanded_metrics.get("trades", 0)),
        "expanded_evidence_gate": gate,
        "expanded_evidence_passed_gate": expanded_evidence_passed_gate,
        "candidate_locking_allowed_pre_oos": candidate_locking_allowed_pre_oos,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "trade_recommendation_output_present": False,
        "data_csv_added_to_git": False,
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def _source_blockers(
    source_board: dict[str, Any] | None,
    source_stability: dict[str, Any] | None,
    source_feasibility: dict[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    if source_board is None:
        blockers.append("source_v0_48_board_missing_or_invalid")
    else:
        if source_board.get("board_version") != SOURCE_CANDIDATE_BOARD_VERSION:
            blockers.append("source_candidate_board_version_mismatch")
        if source_board.get("best_candidate_id") != CANDIDATE_ID:
            blockers.append("source_board_best_candidate_not_trend_pullback")
        if _source_candidate(source_board) is None:
            blockers.append("source_trend_pullback_candidate_missing")
    if source_stability is None:
        blockers.append("source_v0_49_stability_audit_missing_or_invalid")
    elif source_stability.get("audit_version") != SOURCE_STABILITY_AUDIT_VERSION:
        blockers.append("source_stability_audit_version_mismatch")
    if source_feasibility is None:
        blockers.append("source_v0_50_data_feasibility_missing_or_invalid")
    else:
        if source_feasibility.get("audit_version") != SOURCE_DATA_FEASIBILITY_VERSION:
            blockers.append("source_data_feasibility_version_mismatch")
        if source_feasibility.get("data_expansion_feasible") is not True:
            blockers.append("source_data_expansion_not_feasible")
    return blockers


def _source_candidate(source_board: dict[str, Any]) -> dict[str, Any] | None:
    for candidate in source_board.get("candidate_results", []):
        if isinstance(candidate, dict) and candidate.get("candidate_id") == CANDIDATE_ID:
            if candidate.get("fixed_before_evaluation") is True:
                return candidate
    return None


def _expanded_gate(
    *,
    expanded_metrics: dict[str, Any],
    metrics_by_year: dict[str, Any],
    trade_distribution_by_year: dict[str, int],
) -> dict[str, Any]:
    failures: list[str] = []
    profit_factor = _pf_value(expanded_metrics.get("profit_factor"))
    expectancy = float(expanded_metrics.get("expectancy_r", 0.0))
    trade_count = int(expanded_metrics.get("trades", 0))
    years_with_trades = len([year for year, count in trade_distribution_by_year.items() if count > 0])
    max_year_share = max(trade_distribution_by_year.values()) / trade_count if trade_count else 0.0
    catastrophic_years = _catastrophic_negative_years(metrics_by_year)

    if profit_factor < EXPANDED_PROFIT_FACTOR_MINIMUM:
        failures.append("expanded_profit_factor_below_fixed_gate")
    if expectancy <= 0.0:
        failures.append("expanded_expectancy_not_positive")
    if trade_count < EXPANDED_TRADE_MINIMUM:
        failures.append("expanded_trade_count_below_fixed_gate")
    if years_with_trades < MIN_CALENDAR_YEARS_WITH_TRADES:
        failures.append("expanded_trades_cover_fewer_than_3_calendar_years")
    if max_year_share > MAX_SINGLE_YEAR_TRADE_SHARE:
        failures.append("single_year_contains_more_than_50_percent_of_expanded_trades")
    if catastrophic_years:
        failures.append("catastrophic_negative_year_present")

    return {
        "profit_factor_minimum": EXPANDED_PROFIT_FACTOR_MINIMUM,
        "expectancy_minimum_exclusive": 0.0,
        "expanded_trade_minimum": EXPANDED_TRADE_MINIMUM,
        "min_calendar_years_with_trades": MIN_CALENDAR_YEARS_WITH_TRADES,
        "max_single_year_trade_share": MAX_SINGLE_YEAR_TRADE_SHARE,
        "catastrophic_negative_years": catastrophic_years,
        "observed_profit_factor": expanded_metrics.get("profit_factor"),
        "observed_expectancy_r": expanded_metrics.get("expectancy_r"),
        "observed_trade_count": trade_count,
        "observed_calendar_years_with_trades": years_with_trades,
        "observed_max_single_year_trade_share": max_year_share,
        "oos_used": False,
        "failures": failures,
        "passed": not failures,
    }


def _catastrophic_negative_years(metrics_by_year: dict[str, Any]) -> list[str]:
    catastrophic: list[str] = []
    for year, metrics in metrics_by_year.items():
        if int(metrics.get("trades", 0)) < 5:
            continue
        total_return = float(metrics.get("total_return_r", 0.0))
        profit_factor = _pf_value(metrics.get("profit_factor"))
        if total_return <= CATASTROPHIC_YEAR_LOSS_R or profit_factor < CATASTROPHIC_YEAR_PROFIT_FACTOR:
            catastrophic.append(year)
    return catastrophic


def _metrics_by_key(trades: list[dict[str, Any]], key: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for trade in trades:
        grouped.setdefault(str(trade[key]), []).append(trade)
    return {value: _metrics_with_total(value_trades) for value, value_trades in sorted(grouped.items())}


def _metrics_with_total(trades: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = board_v0_48._split_metrics(trades)
    metrics["total_return_r"] = sum(float(trade["return_r"]) for trade in trades)
    return metrics


def _sample_concentration_risk(trades: list[dict[str, Any]]) -> dict[str, Any]:
    reasons: list[str] = []
    if len(trades) < EXPANDED_TRADE_MINIMUM:
        reasons.append("expanded_trade_count_below_fixed_gate")
    if len(_distribution(trades, "year")) < MIN_CALENDAR_YEARS_WITH_TRADES:
        reasons.append("expanded_trades_cover_fewer_than_3_calendar_years")
    for key, label, threshold in (
        ("year", "year", MAX_SINGLE_YEAR_TRADE_SHARE),
        ("month", "month", 0.50),
        ("side", "side", 0.75),
        ("source_timeframe", "timeframe", 0.75),
    ):
        share = _max_share(trades, key)
        if trades and share > threshold:
            reasons.append(f"expanded_trades_concentrated_in_single_{label}")
    risk_level = "high" if reasons else "low"
    return {
        "risk_level": risk_level,
        "risk_present": bool(reasons),
        "reasons": reasons,
        "expanded_trade_count": len(trades),
        "expanded_year_max_share": _max_share(trades, "year"),
        "expanded_month_max_share": _max_share(trades, "month"),
        "expanded_side_max_share": _max_share(trades, "side"),
        "expanded_timeframe_max_share": _max_share(trades, "source_timeframe"),
        "warnings": [f"sample_concentration_risk:{reason}" for reason in reasons],
    }


def _empty_concentration_risk() -> dict[str, Any]:
    return {
        "risk_level": "unknown",
        "risk_present": True,
        "reasons": ["expanded_retest_missing_required_data"],
        "expanded_trade_count": 0,
        "expanded_year_max_share": 0.0,
        "expanded_month_max_share": 0.0,
        "expanded_side_max_share": 0.0,
        "expanded_timeframe_max_share": 0.0,
        "warnings": [],
    }


def _distribution(trades: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for trade in trades:
        value = str(trade[key])
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _max_share(trades: list[dict[str, Any]], key: str) -> float:
    if not trades:
        return 0.0
    counts = _distribution(trades, key)
    return max(counts.values()) / len(trades)


def _pf_value(value: Any) -> float:
    if value == "inf":
        return float("inf")
    return float(value or 0.0)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _date_start_utc(value: str) -> datetime:
    return datetime.combine(date.fromisoformat(value), time.min, tzinfo=UTC).replace(tzinfo=None)


def _date_end_utc(value: str) -> datetime:
    return datetime.combine(date.fromisoformat(value), time.max, tzinfo=UTC).replace(tzinfo=None)


def _rate_value(rate: Any, key: str) -> Any:
    try:
        return rate[key]
    except (KeyError, IndexError, TypeError, ValueError):
        if hasattr(rate, key):
            return getattr(rate, key)
        raise


def _optional_rate_value(rate: Any, key: str, default: Any) -> Any:
    try:
        return _rate_value(rate, key)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return default


def _last_error_text(mt5: Any) -> str:
    last_error = getattr(mt5, "last_error", None)
    if callable(last_error):
        return f"mt5_initialize_failed:{last_error()}"
    return "mt5_initialize_failed"


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "mt5_read_only": True,
        "train_validation_equivalent_only": True,
        "demo_execution_allowed": False,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "execution_queue_created": False,
        "scheduler_created": False,
        "auto_execute_order": False,
        "trade_recommendation_output_present": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "oos_used": False,
        "repeated_oos_review": False,
        "data_csv_added_to_git": False,
    }
