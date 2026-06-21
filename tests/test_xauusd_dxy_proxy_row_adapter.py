from __future__ import annotations

import json
from pathlib import Path

from src.research.xauusd_dxy_conditioned_event_study import build_xauusd_dxy_conditioned_event_study_v0_68
from src.research.xauusd_dxy_proxy_quality_ranker import (
    ADAPTER_BLOCKED_NO_PARSEABLE_PROXY,
    ADAPTER_COMPLETED,
    ADAPTER_COMPLETED_WITH_FALLBACK,
    PROXY_ROW_ADAPTER_VERSION,
    adapt_dxy_proxy_rows,
    build_xauusd_dxy_proxy_row_adapter_report_v0_68_1,
)

ROOT = Path(__file__).resolve().parents[1]


def _valid_rows(symbol: str = "DXYN") -> list[dict[str, object]]:
    return [
        {
            "time": 1_704_067_200 + index * 900,
            "open": 100.0 + index,
            "high": 101.0 + index,
            "low": 99.0 + index,
            "close": 100.5 + index,
            "spread": 1,
            "tick_volume": 10,
            "symbol": symbol,
        }
        for index in range(4)
    ]


def _events() -> list[dict[str, object]]:
    return [
        {
            "source_research_version": "v0_53",
            "candidate_id": "sample_candidate",
            "entry_timestamp": "2024-01-01T00:15:00",
            "split": "train",
            "return_r": 1.0,
        }
    ]


def test_adapter_parses_valid_mt5_copy_rates_rows() -> None:
    detail = adapt_dxy_proxy_rows(_valid_rows(), symbol="DXYN", timeframe="M15", copy_rates_attempted=True)

    assert detail["adapter_version"] == PROXY_ROW_ADAPTER_VERSION
    assert detail["symbol_selected"] == "DXYN"
    assert detail["copy_rates_attempted"] is True
    assert detail["copied_row_count"] == 4
    assert detail["parseable_row_count"] == 4
    assert detail["required_columns_present"] is True
    assert detail["invalid_ohlc_count"] == 0
    assert detail["duplicate_timestamp_count"] == 0
    assert detail["monotonic_timestamp_order"] is True
    assert detail["reason_if_unparseable"] is None
    assert detail["rows"][0]["timestamp_utc"] == "2024-01-01T00:00:00"


def test_adapter_rejects_invalid_or_missing_ohlc_safely() -> None:
    rows = [
        {"time": "2024-01-01T00:00:00", "open": 100, "high": 101, "low": 99, "close": 100},
        {"time": "2024-01-01T00:15:00", "open": 0, "high": 0, "low": 0, "close": 0},
        {"time": "2024-01-01T00:30:00", "open": 100, "high": 101, "low": 99},
    ]

    detail = adapt_dxy_proxy_rows(rows, symbol="DXYN", timeframe="M15", copy_rates_attempted=True)

    assert detail["parseable_row_count"] == 1
    assert detail["invalid_ohlc_count"] == 2
    assert detail["required_columns_present"] is False


def test_adapter_preserves_duplicate_and_monotonic_timestamp_checks() -> None:
    rows = [
        {"time": "2024-01-01T00:30:00", "open": 100, "high": 101, "low": 99, "close": 100},
        {"time": "2024-01-01T00:15:00", "open": 100, "high": 101, "low": 99, "close": 100},
        {"time": "2024-01-01T00:15:00", "open": 100, "high": 101, "low": 99, "close": 100},
    ]

    detail = adapt_dxy_proxy_rows(rows, symbol="DXYN", timeframe="M15", copy_rates_attempted=True)

    assert detail["parseable_row_count"] == 3
    assert detail["duplicate_timestamp_count"] == 1
    assert detail["monotonic_timestamp_order"] is False


def test_adapter_does_not_create_persistent_csv_files() -> None:
    before = {path.as_posix() for path in (ROOT / "data").glob("*.csv")}
    report = build_xauusd_dxy_proxy_row_adapter_report_v0_68_1(
        root=ROOT,
        proxy_rows_by_symbol={"DXYN": _valid_rows("DXYN")},
        attempt_mt5_readonly=False,
    )
    after = {path.as_posix() for path in (ROOT / "data").glob("*.csv")}

    assert before == after
    assert report["aligned_dataset_created"] is False
    assert report["data_csv_touched"] is False


def test_adapter_supports_fallback_ranking_without_trading_output() -> None:
    report = build_xauusd_dxy_proxy_row_adapter_report_v0_68_1(
        root=ROOT,
        proxy_rows_by_symbol={
            "DXYN": [{"time": "2024-01-01T00:00:00", "open": 0, "high": 0, "low": 0, "close": 0}],
            "USDX": _valid_rows("USDX"),
        },
        attempt_mt5_readonly=False,
    )

    assert report["adapter_status"] == ADAPTER_COMPLETED_WITH_FALLBACK
    assert report["selected_parseable_proxy_symbol_or_null"] == "USDX"
    assert report["fallback_proxy_symbol_or_null"] == "USDX"
    assert report["trade_recommendation_output"] is False
    assert report["labels_used_as_trade_blockers"] is False
    assert report["approved_for_trade_filtering"] is False


def test_v0_68_event_study_uses_shared_adapter_without_strategy_rules() -> None:
    report = build_xauusd_dxy_conditioned_event_study_v0_68(
        root=ROOT,
        event_records=_events(),
        proxy_rows=_valid_rows("DXYN"),
        attempt_mt5_readonly=False,
    )

    assert report["proxy_readonly_summary"]["adapter_version"] == PROXY_ROW_ADAPTER_VERSION
    assert report["proxy_readonly_summary"]["parseable_row_count"] == 4
    assert report["safety"]["strategy_rules_created"] is False
    assert report["safety"]["strategy_rules_modified"] is False
    assert report["labels_used_as_trade_blockers"] is False


def test_no_oos_retune_threshold_search_or_parameter_grid_is_performed() -> None:
    report = build_xauusd_dxy_proxy_row_adapter_report_v0_68_1(
        root=ROOT,
        proxy_rows_by_symbol={"DXYN": _valid_rows("DXYN")},
        attempt_mt5_readonly=False,
    )

    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False


def test_report_contains_required_diagnostic_and_safety_fields() -> None:
    report = build_xauusd_dxy_proxy_row_adapter_report_v0_68_1(
        root=ROOT,
        proxy_rows_by_symbol={"DXYN": _valid_rows("DXYN")},
        attempt_mt5_readonly=False,
    )

    assert report["adapter_version"] == "v0_68_1"
    assert report["adapter_status"] in {
        ADAPTER_COMPLETED,
        ADAPTER_COMPLETED_WITH_FALLBACK,
        ADAPTER_BLOCKED_NO_PARSEABLE_PROXY,
    }
    assert report["source_quality_ranker_version"] == "v0_66"
    assert report["source_event_study_version"] == "v0_68"
    assert report["symbols_checked"] == ["DXYN", "DXYZ", "GDXY", "USDX"]
    assert set(report["parseability_by_symbol"]) == {"DXYN", "DXYZ", "GDXY", "USDX"}
    assert report["shared_adapter_created_or_updated"] is True
    assert report["event_study_updated_to_use_shared_adapter"] is True
    assert report["safe_asof_alignment_possible_after_adapter"] is True
    assert report["lookahead_risk_detected"] is False
    assert report["recommended_next_step"] == "rerun_v0_68_dxy_conditioned_event_study_with_shared_adapter"
    json.dumps(report)
