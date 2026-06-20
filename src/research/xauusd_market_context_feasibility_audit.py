"""v0_61 market context layer feasibility audit."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

AUDIT_VERSION = "v0_61"
SOURCE_PREVIOUS_BOARD_VERSION = "v0_60"
PURPOSE = "market_context_layer_feasibility_only"
DEFAULT_OUTPUT = Path("reports") / "xauusd_market_context_feasibility_v0_61.json"
DEFAULT_V0_60_REPORT = Path("reports") / "xauusd_second_tier_board_v0_60.json"

COMPLETED = "market_context_feasibility_completed"
BLOCKED_MISSING_V0_60_REPORT = "blocked_missing_v0_60_report"
FAILED = "market_context_feasibility_failed"

MARKET_CONTEXT_FAMILIES = [
    "market_open_closed_session_state",
    "holiday_reduced_liquidity_calendar",
    "economic_calendar_event_timestamps",
    "dxy_usd_proxy",
    "us_yields_rates_proxy",
    "geopolitical_macro_risk_labels",
    "technical_permission_gate",
]

MARKET_STATE_LABELS = [
    "market_closed_weekend",
    "market_closed_holiday",
    "thin_liquidity_session",
    "normal_liquidity_session",
    "london_active",
    "ny_active",
    "london_ny_overlap",
    "late_us_session",
]

EVENT_WINDOW_LABELS = [
    "pre_high_impact_us_event_window",
    "immediate_post_high_impact_us_event_window",
    "post_event_repricing_window",
    "fomc_day",
    "nfp_day",
    "cpi_day",
]

REQUIRED_US_EVENTS = [
    "CPI",
    "PPI",
    "NFP",
    "Unemployment Rate",
    "FOMC Rate Decision",
    "FOMC Minutes",
    "Fed Chair Speech",
    "GDP",
    "Retail Sales",
    "ISM",
    "Jobless Claims",
]

GEOPOLITICAL_LABELS = [
    "geopolitical_risk_bid",
    "risk_off_proxy_window",
    "middle_east_tension_window",
    "central_bank_headline_window",
    "unexpected_shock_window",
]

GATE_OUTPUTS = [
    "allow_technical_research",
    "block_due_to_closed_market",
    "block_due_to_thin_liquidity",
    "block_due_to_event_risk",
    "block_due_to_missing_context_data",
    "observe_only_due_to_macro_uncertainty",
]

DXY_SYMBOL_TOKENS = ("DXY", "USDX", "USDOLLAR", "USD_INDEX", "USDINDEX")
YIELD_SYMBOL_TOKENS = ("US10Y", "US02Y", "US2Y", "UST10Y", "UST02Y", "TREASURY", "YIELD")


def build_xauusd_market_context_feasibility_audit_v0_61(
    *,
    previous_board_path: str | Path = DEFAULT_V0_60_REPORT,
    policy_root: str | Path = ".",
    mt5_module: Any | None = None,
    attempt_mt5_symbol_discovery: bool = True,
) -> dict[str, Any]:
    """Define feasible market-context features without importing datasets or testing strategy rules."""
    try:
        previous_board = _read_json(Path(previous_board_path))
        if not _valid_v0_60_board(previous_board):
            return _base_report(
                audit_status=BLOCKED_MISSING_V0_60_REPORT,
                previous_board=previous_board,
                mt5_symbol_discovery=_empty_mt5_symbol_discovery(attempted=False),
                blockers=["missing_or_invalid_v0_60_second_tier_board_report"],
                warnings=[],
                next_recommended_step="restore reports/xauusd_second_tier_board_v0_60.json before v0_61 market-context feasibility audit",
            )

        mt5_symbol_discovery = (
            _discover_mt5_candidate_symbols(mt5_module=mt5_module)
            if attempt_mt5_symbol_discovery
            else _empty_mt5_symbol_discovery(attempted=False)
        )
        warnings = [
            "feasibility_audit_only_not_strategy_not_backtest_not_oos",
            "external_datasets_not_imported_in_v0_61",
            "mt5_symbol_discovery_is_candidate_metadata_only_not_approved_data",
            "manual_or_offline_sources_required_before_context_research",
        ]
        if mt5_symbol_discovery["status"] != "symbols_discovered":
            warnings.append(str(mt5_symbol_discovery["status"]))

        return _base_report(
            audit_status=COMPLETED,
            previous_board=previous_board,
            mt5_symbol_discovery=mt5_symbol_discovery,
            blockers=[],
            warnings=warnings,
            next_recommended_step="v0_62 controlled read-only market context data importer design, no strategy, no OOS",
        )
    except Exception as exc:
        return _base_report(
            audit_status=FAILED,
            previous_board=None,
            mt5_symbol_discovery=_empty_mt5_symbol_discovery(attempted=False),
            blockers=[f"audit_exception:{type(exc).__name__}:{exc}"],
            warnings=[],
            next_recommended_step="repair v0_61 audit implementation before any market-context feature import",
        )


def save_xauusd_market_context_feasibility_audit(
    report: dict[str, Any],
    output: str | Path = DEFAULT_OUTPUT,
) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_report(
    *,
    audit_status: str,
    previous_board: dict[str, Any] | None,
    mt5_symbol_discovery: dict[str, Any],
    blockers: list[str],
    warnings: list[str],
    next_recommended_step: str,
) -> dict[str, Any]:
    dxy_symbols = mt5_symbol_discovery.get("dxy_usd_proxy_candidate_symbols", [])
    yield_symbols = mt5_symbol_discovery.get("us_yields_rates_candidate_symbols", [])
    return {
        "audit_version": AUDIT_VERSION,
        "audit_status": audit_status,
        "purpose": PURPOSE,
        "source_previous_board_version": SOURCE_PREVIOUS_BOARD_VERSION,
        "pure_ohlc_branch_status": _pure_ohlc_branch_status(previous_board),
        "market_context_families_audited": list(MARKET_CONTEXT_FAMILIES),
        "market_open_closed_feasibility": _market_open_closed_feasibility(),
        "holiday_calendar_feasibility": _holiday_calendar_feasibility(),
        "economic_calendar_feasibility": _economic_calendar_feasibility(),
        "dxy_proxy_feasibility": _dxy_proxy_feasibility(dxy_symbols),
        "us_yields_proxy_feasibility": _us_yields_proxy_feasibility(yield_symbols),
        "geopolitical_label_feasibility": _geopolitical_label_feasibility(),
        "technical_permission_gate_defined": _technical_permission_gate(),
        "mt5_symbol_discovery_attempted": mt5_symbol_discovery["attempted"],
        "mt5_symbol_discovery": mt5_symbol_discovery,
        "discovered_candidate_symbols": {
            "dxy_usd_proxy": dxy_symbols,
            "us_yields_rates_proxy": yield_symbols,
        },
        "external_feature_schema_documented": True,
        "anti_lookahead_policy_documented": True,
        "data_alignment_policy_documented": True,
        "api_key_storage_policy_documented": True,
        "approved_for_v0_62_feature_import": False,
        "approved_for_strategy_testing": False,
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
        "recommended_v0_62_plan": _recommended_v0_62_plan(audit_status, mt5_symbol_discovery),
        "next_recommended_step": next_recommended_step,
        "safety": _safety_flags(),
    }


def _market_open_closed_feasibility() -> dict[str, Any]:
    return {
        "status": "feasible_for_weekend_and_session_labels_from_timestamps",
        "future_labels": list(MARKET_STATE_LABELS),
        "weekend_closure_inference": "timestamps_can_identify_saturday_sunday_closed_market_periods",
        "holiday_closure_inference": "requires_holiday_calendar_dataset_before_forward_or_research_gate",
        "session_liquidity_basis": "utc_time_windows_only_until_broker_timestamp_basis_is_confirmed",
        "online_forward_policy": "no_tradeable_signal_during_closed_market_periods",
        "can_infer_weekends_from_existing_timestamps": True,
        "closed_market_tradeable_signal_allowed": False,
    }


def _holiday_calendar_feasibility() -> dict[str, Any]:
    return {
        "status": "schema_defined_external_dataset_required",
        "required_future_dataset_category": "US_market_holidays_and_reduced_liquidity_days",
        "schema": [
            "date",
            "market",
            "country",
            "holiday_name",
            "closure_type",
            "liquidity_impact",
            "source",
            "timestamp_basis",
        ],
        "v0_61_dataset_downloaded": False,
        "acquisition_options": [
            "manual_offline_csv_from_exchange_or_government_sources",
            "broker_calendar_export_if_available",
            "free_public_calendar_download_reviewed_before_import",
        ],
    }


def _economic_calendar_feasibility() -> dict[str, Any]:
    return {
        "status": "schema_defined_external_dataset_required",
        "schema": [
            "event_time_utc",
            "currency",
            "event_name",
            "impact",
            "actual",
            "forecast",
            "previous",
            "source",
            "revision_flag",
        ],
        "required_events": list(REQUIRED_US_EVENTS),
        "event_window_labels": list(EVENT_WINDOW_LABELS),
        "anti_lookahead_rules": [
            "actual_forecast_surprise_unavailable_before_release_timestamp",
            "revised_values_must_set_revision_flag",
            "future_schedule_may_use_timestamps_and_names_only_not_outcomes",
        ],
        "v0_61_dataset_downloaded": False,
    }


def _dxy_proxy_feasibility(candidate_symbols: list[str]) -> dict[str, Any]:
    return {
        "status": "mt5_candidate_symbol_discovery_only_external_or_broker_data_required",
        "candidate_symbols": candidate_symbols,
        "approved_data": False,
        "future_ohlc_schema": [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "source_symbol",
            "timeframe",
            "timestamp_basis",
            "source",
        ],
        "alignment_rules": _alignment_rules(),
    }


def _us_yields_proxy_feasibility(candidate_symbols: list[str]) -> dict[str, Any]:
    return {
        "status": "mt5_candidate_symbol_discovery_only_external_offline_data_required_if_unavailable",
        "candidate_symbols": candidate_symbols,
        "approved_data": False,
        "external_offline_data_needed_if_no_broker_symbol": not bool(candidate_symbols),
        "future_ohlc_schema": [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "source_symbol",
            "timeframe",
            "timestamp_basis",
            "source",
        ],
        "alignment_rules": _alignment_rules(),
    }


def _geopolitical_label_feasibility() -> dict[str, Any]:
    return {
        "status": "schema_only_requires_timestamped_cited_sources_before_research_use",
        "future_labels": list(GEOPOLITICAL_LABELS),
        "live_scraping_allowed": False,
        "manual_subjective_labels_allowed_for_strategy_testing": False,
        "source_requirement": "timestamped_evidence_with_source_citation_required_before_any_research_dataset",
    }


def _technical_permission_gate() -> dict[str, Any]:
    return {
        "defined": True,
        "future_gate_outputs": list(GATE_OUTPUTS),
        "trading_logic_in_v0_61": False,
        "gate_position": "market_context_gate_before_technical_setup_before_risk_filter",
    }


def _alignment_rules() -> list[str]:
    return [
        "normalize_all_feature_timestamps_to_utc_before_joining_xauusd_candles",
        "join_context_features_asof_using_only_values_known_at_or_before_xauusd_candle_open",
        "never_forward_fill_actual_event_outcomes_before_release_timestamp",
        "record_source_symbol_timeframe_timestamp_basis_and_source_for_each_context_series",
        "treat missing_context_data as block_due_to_missing_context_data or observe_only_not_tradeable",
    ]


def _discover_mt5_candidate_symbols(*, mt5_module: Any | None) -> dict[str, Any]:
    mt5 = mt5_module
    if mt5 is None:
        try:
            mt5 = importlib.import_module("MetaTrader5")
        except ImportError:
            return _empty_mt5_symbol_discovery(
                attempted=True,
                status="metatrader5_package_unavailable",
                blockers=["metatrader5_package_unavailable"],
            )

    initialized = False
    shutdown_called = False
    try:
        if not mt5.initialize():
            return _empty_mt5_symbol_discovery(
                attempted=True,
                status="mt5_initialize_failed",
                blockers=[_last_error_text(mt5)],
            )
        initialized = True
        symbols = mt5.symbols_get()
        names = sorted({_symbol_name(symbol) for symbol in symbols or [] if _symbol_name(symbol)})
        dxy_symbols = _filter_symbols(names, DXY_SYMBOL_TOKENS)
        yield_symbols = _filter_symbols(names, YIELD_SYMBOL_TOKENS)
        mt5.shutdown()
        shutdown_called = True
        return {
            "attempted": True,
            "status": "symbols_discovered",
            "mt5_initialized": initialized,
            "mt5_shutdown_called": shutdown_called,
            "symbol_count_scanned": len(names),
            "dxy_usd_proxy_candidate_symbols": dxy_symbols,
            "us_yields_rates_candidate_symbols": yield_symbols,
            "approved_data": False,
            "blockers": [],
        }
    except Exception as exc:
        if initialized and not shutdown_called:
            mt5.shutdown()
            shutdown_called = True
        return _empty_mt5_symbol_discovery(
            attempted=True,
            status="mt5_symbol_discovery_failed",
            initialized=initialized,
            shutdown_called=shutdown_called,
            blockers=[f"mt5_symbol_discovery_exception:{type(exc).__name__}:{exc}"],
        )


def _empty_mt5_symbol_discovery(
    *,
    attempted: bool,
    status: str = "not_attempted",
    initialized: bool = False,
    shutdown_called: bool = False,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "attempted": attempted,
        "status": status,
        "mt5_initialized": initialized,
        "mt5_shutdown_called": shutdown_called,
        "symbol_count_scanned": 0,
        "dxy_usd_proxy_candidate_symbols": [],
        "us_yields_rates_candidate_symbols": [],
        "approved_data": False,
        "blockers": blockers or [],
    }


def _valid_v0_60_board(report: dict[str, Any] | None) -> bool:
    if not isinstance(report, dict):
        return False
    return report.get("board_version") == SOURCE_PREVIOUS_BOARD_VERSION


def _pure_ohlc_branch_status(report: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "source_report_present": _valid_v0_60_board(report),
        "source_board_status": report.get("board_status") if isinstance(report, dict) else None,
        "best_candidate_id": report.get("best_candidate_id") if isinstance(report, dict) else None,
        "best_candidate_passed_gate": report.get("best_candidate_passed_gate") if isinstance(report, dict) else None,
        "rejected_do_not_retune_candidates": report.get("rejected_do_not_retune_candidates")
        if isinstance(report, dict)
        else [],
        "pure_ohlc_branch_failure_recorded": (
            isinstance(report, dict) and report.get("board_status") == "no_second_tier_candidate_passed"
        ),
    }


def _recommended_v0_62_plan(audit_status: str, discovery: dict[str, Any]) -> str:
    if audit_status != COMPLETED:
        return "restore v0_60 source board before planning v0_62."
    if discovery.get("status") == "symbols_discovered":
        return "controlled read-only market context data importer, no strategy, no OOS."
    return "document manual/offline data acquisition requirements before context research."


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _symbol_name(symbol: Any) -> str:
    if isinstance(symbol, str):
        return symbol
    name = getattr(symbol, "name", "")
    return str(name or "")


def _filter_symbols(names: list[str], tokens: tuple[str, ...]) -> list[str]:
    matched = [name for name in names if any(token in name.upper().replace(" ", "_") for token in tokens)]
    return matched[:25]


def _last_error_text(mt5: Any) -> str:
    last_error = getattr(mt5, "last_error", None)
    if callable(last_error):
        return f"mt5_initialize_failed:{last_error()}"
    return "mt5_initialize_failed"


def _safety_flags() -> dict[str, bool]:
    return {
        "research_only": True,
        "feasibility_audit_only": True,
        "strategy_evaluation": False,
        "backtest_candidate_created": False,
        "approved_for_strategy_testing": False,
        "approved_for_v0_62_feature_import": False,
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
        "api_keys_in_code": False,
    }
