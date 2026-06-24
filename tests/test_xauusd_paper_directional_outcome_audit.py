from __future__ import annotations

import csv
from pathlib import Path

from src.research.xauusd_paper_directional_outcome_audit import (
    OUTCOME_STATUSES,
    build_xauusd_paper_directional_outcome_audit_v0_91,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp_utc", "symbol", "timeframe", "open", "high", "low", "close", "source"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _base_row(index: int, *, close: float = 100.0) -> dict[str, object]:
    return {
        "timestamp_utc": f"2026-01-01T00:{index:02d}:00+00:00",
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "open": close,
        "high": close + 0.5,
        "low": close - 0.5,
        "close": close,
        "source": "synthetic_fixture",
    }


def _build_fixture_rows(direction: str, future_closes: list[float], *, adverse_first: bool = False) -> list[dict[str, object]]:
    rows = [_base_row(index) for index in range(12)]
    if direction == "long":
        rows.append({**_base_row(12), "open": 100.0, "high": 103.2, "low": 99.7, "close": 102.5})
    else:
        rows.append({**_base_row(12), "open": 100.0, "high": 100.3, "low": 96.8, "close": 97.5})

    for offset, close in enumerate(future_closes, start=13):
        row = _base_row(offset, close=close)
        if direction == "long":
            row.update({"open": close - 0.1, "high": close + 0.4, "low": close - (2.4 if adverse_first and offset == 13 else 0.4)})
        else:
            row.update({"open": close + 0.1, "high": close + (2.4 if adverse_first and offset == 13 else 0.4), "low": close - 0.4})
        rows.append(row)
    return rows


def test_bullish_fixture_produces_favorable_long_outcome(tmp_path: Path) -> None:
    _write_rows(tmp_path / "xauusd_m5_fixture.csv", _build_fixture_rows("long", [103.0, 104.8]))

    report = build_xauusd_paper_directional_outcome_audit_v0_91(
        market_csv_dir=tmp_path,
        horizon_bars=2,
        max_scan_rows=20,
        max_directional_records=10,
    )

    record = report["outcome_records"][0]
    assert record["paper_observation_direction"] == "paper_long"
    assert record["outcome_status"] == "favorable_move_observed"
    assert record["max_favorable_move_points"] >= 2.0


def test_bearish_fixture_produces_favorable_short_outcome(tmp_path: Path) -> None:
    _write_rows(tmp_path / "xauusd_m5_fixture.csv", _build_fixture_rows("short", [96.8, 95.1]))

    report = build_xauusd_paper_directional_outcome_audit_v0_91(
        market_csv_dir=tmp_path,
        horizon_bars=2,
        max_scan_rows=20,
        max_directional_records=10,
    )

    record = report["outcome_records"][0]
    assert record["paper_observation_direction"] == "paper_short"
    assert record["outcome_status"] == "favorable_move_observed"
    assert record["max_favorable_move_points"] >= 2.0


def test_adverse_outcomes_are_detected(tmp_path: Path) -> None:
    _write_rows(tmp_path / "xauusd_m5_fixture.csv", _build_fixture_rows("long", [100.6, 100.8], adverse_first=True))

    report = build_xauusd_paper_directional_outcome_audit_v0_91(
        market_csv_dir=tmp_path,
        horizon_bars=2,
        max_scan_rows=20,
        max_directional_records=10,
    )

    assert report["outcome_records"][0]["outcome_status"] == "adverse_move_observed"
    assert report["outcome_counts"]["adverse_move_observed"] == 1


def test_insufficient_future_rows_are_blocked(tmp_path: Path) -> None:
    _write_rows(tmp_path / "xauusd_m5_fixture.csv", _build_fixture_rows("long", [103.0]))

    report = build_xauusd_paper_directional_outcome_audit_v0_91(
        market_csv_dir=tmp_path,
        horizon_bars=2,
        max_scan_rows=20,
        max_directional_records=10,
    )

    assert report["outcome_records"][0]["outcome_status"] == "blocked_missing_future_rows"
    assert report["records_blocked"] == 1


def test_missing_or_low_directional_sample_returns_insufficient_directional_frequency(tmp_path: Path) -> None:
    _write_rows(tmp_path / "xauusd_m5_fixture.csv", [_base_row(index) for index in range(30)])

    report = build_xauusd_paper_directional_outcome_audit_v0_91(
        market_csv_dir=tmp_path,
        horizon_bars=2,
        max_scan_rows=30,
        max_directional_records=10,
    )

    assert report["directional_observation_count"] == 0
    assert report["decision"] == "insufficient_directional_frequency"
    assert report["audit_status"] == "directional_outcome_audit_completed_insufficient_directional_sample"


def test_no_data_csv_file_is_modified() -> None:
    before = {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}

    build_xauusd_paper_directional_outcome_audit_v0_91(
        market_csv_dir=ROOT / "data",
        horizon_bars=1,
        max_scan_rows=20,
        max_directional_records=5,
    )

    after = {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}
    assert after == before


def test_no_order_send_order_check_demo_live_path_is_enabled(tmp_path: Path) -> None:
    _write_rows(tmp_path / "xauusd_m5_fixture.csv", _build_fixture_rows("long", [103.0, 104.8]))

    report = build_xauusd_paper_directional_outcome_audit_v0_91(market_csv_dir=tmp_path, horizon_bars=2)

    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["order_send_allowed"] is False
    assert report["order_check_allowed"] is False


def test_no_trade_recommendation_output_is_produced(tmp_path: Path) -> None:
    _write_rows(tmp_path / "xauusd_m5_fixture.csv", _build_fixture_rows("long", [103.0, 104.8]))

    report = build_xauusd_paper_directional_outcome_audit_v0_91(market_csv_dir=tmp_path, horizon_bars=2)

    assert report["paper_observation_only"] is True
    assert report["trade_recommendation_output"] is False
    assert report["user_facing_buy_sell_signal_output"] is False
    assert all(record["trade_recommendation_output"] is False for record in report["outcome_records"])


def test_no_optimization_grid_or_search_flags_are_true(tmp_path: Path) -> None:
    _write_rows(tmp_path / "xauusd_m5_fixture.csv", _build_fixture_rows("long", [103.0, 104.8]))

    report = build_xauusd_paper_directional_outcome_audit_v0_91(market_csv_dir=tmp_path, horizon_bars=2)

    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["optimization_performed"] is False
    assert set(report["outcome_counts"]) == set(OUTCOME_STATUSES)
