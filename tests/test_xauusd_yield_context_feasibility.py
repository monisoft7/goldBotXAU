from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.research.xauusd_yield_context_feasibility import (
    CANDIDATE_YIELD_SYMBOLS,
    EXTERNAL_DATASET_CANDIDATES,
    build_yield_context_feasibility_report,
    safe_backward_asof_proxy_bar,
)


class FakeMT5:
    TIMEFRAME_D1 = "D1"
    TIMEFRAME_H1 = "H1"
    TIMEFRAME_M15 = "M15"

    def __init__(self, rows_by_symbol_timeframe: dict[tuple[str, str], list[dict[str, object]]]) -> None:
        self.rows_by_symbol_timeframe = rows_by_symbol_timeframe
        self.selected_symbols: list[str] = []
        self.shutdown_called = False

    def initialize(self) -> bool:
        return True

    def shutdown(self) -> None:
        self.shutdown_called = True

    def symbol_select(self, symbol: str, enabled: bool) -> bool:
        self.selected_symbols.append(symbol)
        if symbol == "XAUUSD":
            return any(key[0] == symbol for key in self.rows_by_symbol_timeframe)
        return any(key[0] == symbol for key in self.rows_by_symbol_timeframe)

    def copy_rates_from_pos(self, symbol: str, timeframe: str, start_pos: int, count: int) -> list[dict[str, object]]:
        assert start_pos == 0
        return self.rows_by_symbol_timeframe.get((symbol, timeframe), [])[:count]


def _bar(timestamp: datetime, value: float = 1.0) -> dict[str, object]:
    return {
        "time": timestamp,
        "open": value,
        "high": value + 0.1,
        "low": value - 0.1,
        "close": value,
    }


def _xauusd_rows() -> list[dict[str, object]]:
    start = datetime(2024, 1, 1)
    return [_bar(start + timedelta(days=offset), 2000.0 + offset) for offset in range(3)]


def test_missing_yield_symbols_fail_safely(tmp_path: Path) -> None:
    fake_mt5 = FakeMT5({("XAUUSD", "D1"): _xauusd_rows()})

    report = build_yield_context_feasibility_report(tmp_path, mt5=fake_mt5)

    assert report["audit_status"] == "no_usable_local_yield_proxy_found"
    assert report["selected_local_proxy_symbol_or_null"] is None
    assert report["local_yield_proxy_available"] is False
    assert report["external_dataset_required"] is True
    assert [entry["symbol"] for entry in report["candidate_symbols_checked"]] == CANDIDATE_YIELD_SYMBOLS
    assert all(entry["symbol_found"] is False for entry in report["candidate_symbols_checked"])
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert fake_mt5.shutdown_called is True


def test_invalid_or_missing_ohlc_rows_are_rejected(tmp_path: Path) -> None:
    bad_rows = [
        {"time": datetime(2024, 1, 1), "open": 4.0, "high": 3.0, "low": 3.5, "close": 4.0},
        {"time": datetime(2024, 1, 2), "open": 4.0, "high": 4.1, "low": 3.9},
    ]
    fake_mt5 = FakeMT5({("XAUUSD", "D1"): _xauusd_rows(), ("US10Y", "D1"): bad_rows})

    report = build_yield_context_feasibility_report(tmp_path, mt5=fake_mt5)
    us10y = report["candidate_symbols_checked"][0]

    assert us10y["symbol"] == "US10Y"
    assert us10y["symbol_found"] is True
    assert us10y["required_columns_present"] is False
    assert us10y["invalid_ohlc_count"] == 2
    assert us10y["safe_asof_alignment_feasible"] is False
    assert us10y["reason_if_rejected"] == "missing_required_ohlc_columns"
    assert report["usable_local_proxy_symbols"] == []


def test_no_external_api_or_persistent_csv_is_created(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_csv = data_dir / "local.csv"
    data_csv.write_text("timestamp,close\n2024-01-01,1\n", encoding="utf-8")
    before = data_csv.read_text(encoding="utf-8")
    fake_mt5 = FakeMT5({("XAUUSD", "D1"): _xauusd_rows()})

    report = build_yield_context_feasibility_report(tmp_path, mt5=fake_mt5)

    assert report["external_api_called"] is False
    assert report["aligned_dataset_created"] is False
    assert report["persistent_aligned_csv_created"] is False
    assert report["data_csv_touched"] is False
    assert data_csv.read_text(encoding="utf-8") == before
    assert list(data_dir.glob("*.csv")) == [data_csv]


def test_safety_flags_prevent_strategy_rules_trade_signals_and_trade_blockers(tmp_path: Path) -> None:
    fake_mt5 = FakeMT5({("XAUUSD", "D1"): _xauusd_rows()})

    report = build_yield_context_feasibility_report(tmp_path, mt5=fake_mt5)

    assert report["strategy_rules_created"] is False
    assert report["strategy_rules_modified"] is False
    assert report["trade_signals_output"] is False
    assert report["labels_used_as_trade_blockers"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["approved_for_strategy_testing"] is False


def test_no_oos_retune_threshold_search_or_parameter_grid_is_performed(tmp_path: Path) -> None:
    fake_mt5 = FakeMT5({("XAUUSD", "D1"): _xauusd_rows()})

    report = build_yield_context_feasibility_report(tmp_path, mt5=fake_mt5)

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False


def test_safe_asof_alignment_never_uses_future_proxy_bars(tmp_path: Path) -> None:
    xauusd_time = datetime(2024, 1, 2, 12)
    fake_mt5 = FakeMT5(
        {
            ("XAUUSD", "D1"): _xauusd_rows(),
            ("US10Y", "D1"): [
                _bar(datetime(2024, 1, 1), 4.0),
                _bar(datetime(2024, 1, 3), 4.2),
            ],
        }
    )
    report = build_yield_context_feasibility_report(tmp_path, mt5=fake_mt5)
    parsed_bars = [
        type("Bar", (), {"timestamp": datetime(2024, 1, 1)})(),
        type("Bar", (), {"timestamp": datetime(2024, 1, 3)})(),
    ]

    selected = safe_backward_asof_proxy_bar(xauusd_time, parsed_bars)

    assert selected is not None
    assert selected.timestamp == datetime(2024, 1, 1)
    assert report["lookahead_risk_detected"] is False
    with pytest.raises(ValueError, match="future proxy timestamp"):
        from src.research.xauusd_yield_context_feasibility import assert_safe_backward_asof_alignment

        assert_safe_backward_asof_alignment(datetime(2024, 1, 2), datetime(2024, 1, 3))


def test_report_includes_external_dataset_schema_when_local_proxy_unavailable(tmp_path: Path) -> None:
    fake_mt5 = FakeMT5({("XAUUSD", "D1"): _xauusd_rows()})

    report = build_yield_context_feasibility_report(tmp_path, mt5=fake_mt5)

    assert report["external_dataset_required"] is True
    assert report["external_dataset_candidates"] == EXTERNAL_DATASET_CANDIDATES
    assert report["external_schema_requirements"] == [
        "timestamp/date",
        "value",
        "series_id",
        "release/source metadata",
    ]
    assert report["external_dataset_feasibility"]["alignment_policy"]["safe_backward_asof_only"] is True
    assert report["external_dataset_feasibility"]["external_api_called"] is False


def test_report_json_is_serializable_when_local_proxy_is_found(tmp_path: Path) -> None:
    rows = [_bar(datetime(2024, 1, 1), 4.0), _bar(datetime(2024, 1, 2), 4.1), _bar(datetime(2024, 1, 3), 4.2)]
    fake_mt5 = FakeMT5({("XAUUSD", "D1"): _xauusd_rows(), ("US10Y", "D1"): rows})

    report = build_yield_context_feasibility_report(tmp_path, mt5=fake_mt5)

    assert report["audit_status"] == "yield_context_feasibility_completed"
    assert report["selected_local_proxy_symbol_or_null"] == "US10Y"
    assert report["recommended_next_step"] == "v0_74_yield_proxy_quality_and_label_design"
    json.dumps(report)
