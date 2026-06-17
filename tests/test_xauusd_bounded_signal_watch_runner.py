from __future__ import annotations

from src.execution.xauusd_bounded_signal_watch_runner import (
    BLOCKED_INVALID_WATCH_PARAMETERS,
    COMPLETED_NO_QUALIFIED_SIGNAL,
    STOPPED_ORDER_REQUEST_READY_FOR_HUMAN_REVIEW,
    run_xauusd_bounded_signal_watch_v0_44,
)
from src.execution.xauusd_signal_to_order_request_builder import (
    BLOCKED_MACRO_EVENT_WINDOW,
    NO_QUALIFIED_SIGNAL_NOW,
    ORDER_REQUEST_BUILT_DRY_RUN_ONLY,
)

CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"


def _builder_report(
    *,
    builder_status: str = NO_QUALIFIED_SIGNAL_NOW,
    signal_qualified: bool = False,
    order_request_present: bool = False,
    order_request_complete: bool = False,
    macro_event_lock_status: str = "clear_static_manual_windows",
    order_request: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "builder_version": "v0_43",
        "builder_status": builder_status,
        "candidate_id": CANDIDATE_ID,
        "candidate_rules_preserved": True,
        "dry_run": True,
        "signal_qualified": signal_qualified,
        "order_request_present": order_request_present,
        "order_request_complete": order_request_complete,
        "order_request": order_request,
        "macro_event_lock_enabled": True,
        "macro_event_lock_status": macro_event_lock_status,
        "order_send_called": False,
        "order_check_called": False,
        "live_allowed": False,
        "retune_performed": False,
        "threshold_search_performed": False,
        "parameter_grid_performed": False,
        "repeated_oos_review": False,
    }


def test_default_bounded_watch_with_mocked_no_signal_completes() -> None:
    calls: list[dict[str, object]] = []

    def builder(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return _builder_report()

    report = run_xauusd_bounded_signal_watch_v0_44(builder=builder)

    assert report["watch_status"] == COMPLETED_NO_QUALIFIED_SIGNAL
    assert report["max_cycles"] == 6
    assert report["interval_seconds"] == 300
    assert report["cycles_completed"] == 6
    assert report["stopped_early"] is False
    assert report["latest_signal_qualified"] is False
    assert report["latest_order_request_complete"] is False
    assert len(calls) == 6
    assert all(call["dry_run"] is True for call in calls)


def test_mocked_qualified_signal_stops_early_for_human_review() -> None:
    request = {
        "symbol": "XAUUSD",
        "lot": 0.01,
        "demo_only": True,
        "candidate_id": CANDIDATE_ID,
        "side": "long",
        "order_type": "market",
        "action": "prepare_demo_order",
        "risk_reference": "fixed_v0_40_max_trade_risk_1R",
        "stop_distance": 1.25,
        "exit_rule": "fixed_v0_26_next_block_expansion_review",
    }

    def builder(**kwargs: object) -> dict[str, object]:
        return _builder_report(
            builder_status=ORDER_REQUEST_BUILT_DRY_RUN_ONLY,
            signal_qualified=True,
            order_request_present=True,
            order_request_complete=True,
            order_request=request,
        )

    report = run_xauusd_bounded_signal_watch_v0_44(builder=builder, max_cycles=6)

    assert report["watch_status"] == STOPPED_ORDER_REQUEST_READY_FOR_HUMAN_REVIEW
    assert report["cycles_completed"] == 1
    assert report["stopped_early"] is True
    assert report["latest_signal_qualified"] is True
    assert report["latest_order_request_present"] is True
    assert report["latest_order_request_complete"] is True
    assert report["latest_order_request"] == request
    assert report["order_send_called"] is False


def test_macro_event_window_blocks() -> None:
    def builder(**kwargs: object) -> dict[str, object]:
        return _builder_report(
            builder_status=BLOCKED_MACRO_EVENT_WINDOW,
            macro_event_lock_status=BLOCKED_MACRO_EVENT_WINDOW,
        )

    report = run_xauusd_bounded_signal_watch_v0_44(builder=builder, max_cycles=6)

    assert report["watch_status"] == BLOCKED_MACRO_EVENT_WINDOW
    assert report["cycles_completed"] == 1
    assert report["stopped_early"] is True
    assert report["macro_event_lock_status"] == BLOCKED_MACRO_EVENT_WINDOW
    assert "macro_event_lock_active" in report["blockers"]


def test_invalid_max_cycles_blocks() -> None:
    report = run_xauusd_bounded_signal_watch_v0_44(max_cycles=0)

    assert report["watch_status"] == BLOCKED_INVALID_WATCH_PARAMETERS
    assert report["cycles_completed"] == 0
    assert "max_cycles_must_be_at_least_1" in report["blockers"]


def test_invalid_interval_seconds_blocks() -> None:
    report = run_xauusd_bounded_signal_watch_v0_44(interval_seconds=0)

    assert report["watch_status"] == BLOCKED_INVALID_WATCH_PARAMETERS
    assert report["cycles_completed"] == 0
    assert "interval_seconds_must_be_at_least_1" in report["blockers"]


def test_order_send_is_never_called() -> None:
    report = run_xauusd_bounded_signal_watch_v0_44(builder=lambda **_: _builder_report())

    assert report["order_send_called"] is False
    assert all(record["order_send_called"] is False for record in report["cycle_records"])
    assert report["explicit_non_actions"]["order_send_called_or_wrapped"] is False


def test_order_check_is_never_called() -> None:
    report = run_xauusd_bounded_signal_watch_v0_44(builder=lambda **_: _builder_report())

    assert report["order_check_called"] is False
    assert all(record["order_check_called"] is False for record in report["cycle_records"])
    assert report["explicit_non_actions"]["order_check_called_or_wrapped"] is False


def test_live_remains_blocked() -> None:
    report = run_xauusd_bounded_signal_watch_v0_44(builder=lambda **_: _builder_report())

    assert report["dry_run"] is True
    assert report["live_allowed"] is False
    assert all(record["live_allowed"] is False for record in report["cycle_records"])
    assert report["explicit_non_actions"]["live_execution_created"] is False


def test_no_retune_threshold_search_parameter_grid_or_repeated_oos() -> None:
    report = run_xauusd_bounded_signal_watch_v0_44(builder=lambda **_: _builder_report())

    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["repeated_oos_review"] is False
    assert report["explicit_non_actions"]["candidate_rules_changed"] is False
    assert report["explicit_non_actions"]["oos_review_repeated"] is False


def test_sleep_is_opt_in_and_bounded() -> None:
    sleep_calls: list[float] = []

    report = run_xauusd_bounded_signal_watch_v0_44(
        builder=lambda **_: _builder_report(),
        max_cycles=3,
        interval_seconds=5,
        sleep_between_cycles=True,
        sleeper=sleep_calls.append,
    )

    assert report["watch_status"] == COMPLETED_NO_QUALIFIED_SIGNAL
    assert report["cycles_completed"] == 3
    assert sleep_calls == [5.0, 5.0]
