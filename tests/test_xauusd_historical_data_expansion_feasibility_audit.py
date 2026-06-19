from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.research.xauusd_historical_data_expansion_feasibility_audit import (
    AUDIT_VERSION,
    BLOCKED_MT5_UNAVAILABLE,
    CANDIDATE_ID,
    EXPANSION_AVAILABLE,
    EXPANSION_PARTIAL,
    EXPANSION_UNAVAILABLE,
    build_xauusd_historical_data_expansion_feasibility_audit_v0_50,
)


class FakeMt5:
    TIMEFRAME_M5 = "M5"
    TIMEFRAME_M10 = "M10"

    def __init__(
        self,
        *,
        initialize_ok: bool = True,
        symbol_info_present: bool = True,
        m5_times: list[datetime] | None = None,
        m10_times: list[datetime] | None = None,
    ) -> None:
        self.initialize_ok = initialize_ok
        self.symbol_info_present = symbol_info_present
        self.m5_times = m5_times or []
        self.m10_times = m10_times or []
        self.initialize_called = False
        self.shutdown_called = False

    def initialize(self) -> bool:
        self.initialize_called = True
        return self.initialize_ok

    def shutdown(self) -> None:
        self.shutdown_called = True

    def last_error(self) -> tuple[int, str]:
        return (1, "fake unavailable")

    def symbol_info(self, symbol: str) -> object | None:
        return object() if self.symbol_info_present and symbol == "XAUUSD" else None

    def symbol_select(self, symbol: str, selected: bool) -> bool:
        return symbol == "XAUUSD" and selected

    def copy_rates_range(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[dict[str, int]]:
        del symbol, start, end
        source = self.m5_times if timeframe == self.TIMEFRAME_M5 else self.m10_times
        return [{"time": int(value.timestamp())} for value in source]


def _times(start: str, *, count: int, minutes: int) -> list[datetime]:
    base = datetime.fromisoformat(start).replace(tzinfo=UTC)
    return [base + timedelta(minutes=minutes * index) for index in range(count)]


def test_mt5_unavailable_blocks() -> None:
    mt5 = FakeMt5(initialize_ok=False)

    report = build_xauusd_historical_data_expansion_feasibility_audit_v0_50(
        symbol="XAUUSD",
        from_date="2019-01-01",
        to_date="2022-12-31",
        mt5_module=mt5,
    )

    assert report["audit_version"] == AUDIT_VERSION
    assert report["audit_status"] == BLOCKED_MT5_UNAVAILABLE
    assert report["mt5_read_only"] is True
    assert report["mt5_initialized"] is False
    assert report["mt5_shutdown_called"] is False
    assert report["data_expansion_feasible"] is False


def test_old_data_available_passes_feasibility() -> None:
    mt5 = FakeMt5(
        m5_times=_times("2019-01-01T00:00:00", count=288, minutes=5),
        m10_times=_times("2019-01-01T00:00:00", count=144, minutes=10),
    )

    report = build_xauusd_historical_data_expansion_feasibility_audit_v0_50(
        symbol="XAUUSD",
        from_date="2019-01-01",
        to_date="2019-01-01",
        mt5_module=mt5,
    )

    assert report["audit_status"] == EXPANSION_AVAILABLE
    assert report["mt5_initialized"] is True
    assert report["mt5_shutdown_called"] is True
    assert mt5.shutdown_called is True
    assert report["available_oldest_candle_time"] == "2019-01-01T00:00:00"
    assert report["available_newest_candle_time"] == "2019-01-01T23:55:00"
    assert report["requested_range_available"] is True
    assert report["candle_count_by_timeframe"] == {"M5": 288, "M10": 144}
    assert report["missing_range_gaps"] == []
    assert report["data_expansion_feasible"] is True
    assert report["next_recommended_step"] == "v0_51 fixed-rule expanded train/validation retest, no OOS"


def test_partial_gaps_are_reported_and_may_remain_feasible() -> None:
    first_block = _times("2019-01-02T00:00:00", count=300, minutes=5)
    second_block = _times("2019-01-04T00:00:00", count=300, minutes=5)
    mt5 = FakeMt5(
        m5_times=first_block + second_block,
        m10_times=_times("2019-01-02T00:00:00", count=300, minutes=10),
    )

    report = build_xauusd_historical_data_expansion_feasibility_audit_v0_50(
        symbol="XAUUSD",
        from_date="2019-01-01",
        to_date="2019-01-05",
        mt5_module=mt5,
    )

    assert report["audit_status"] == EXPANSION_PARTIAL
    assert report["data_expansion_feasible"] is True
    assert report["candle_count_by_timeframe"]["M5"] == 600
    gap_types = {gap["gap_type"] for gap in report["missing_range_gaps"]}
    assert "missing_start_of_requested_range" in gap_types
    assert "missing_end_of_requested_range" in gap_types
    assert "internal_gap" in gap_types


def test_unavailable_old_data_blocks() -> None:
    mt5 = FakeMt5(m5_times=[], m10_times=[])

    report = build_xauusd_historical_data_expansion_feasibility_audit_v0_50(
        symbol="XAUUSD",
        from_date="2019-01-01",
        to_date="2022-12-31",
        mt5_module=mt5,
    )

    assert report["audit_status"] == EXPANSION_UNAVAILABLE
    assert report["data_expansion_feasible"] is False
    assert report["candle_count_by_timeframe"] == {"M5": 0, "M10": 0}
    assert "no_requested_older_low_timeframe_candles_available" in report["blockers"]


def test_safety_and_research_boundaries_are_preserved() -> None:
    mt5 = FakeMt5(
        m5_times=_times("2019-01-01T00:00:00", count=288, minutes=5),
        m10_times=_times("2019-01-01T00:00:00", count=144, minutes=10),
    )

    report = build_xauusd_historical_data_expansion_feasibility_audit_v0_50(
        symbol="XAUUSD",
        from_date="2019-01-01",
        to_date="2019-01-01",
        mt5_module=mt5,
    )

    assert report["candidate_to_retest_later"] == CANDIDATE_ID
    assert report["candidate_rules_preserved"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["execution_queue_created"] is False
    assert report["scheduler_created"] is False
    assert report["trade_recommendation_output_present"] is False
    assert report["data_csv_added_to_git"] is False
    assert report["proposed_expanded_train_validation_plan"]["oos_allowed"] is False
