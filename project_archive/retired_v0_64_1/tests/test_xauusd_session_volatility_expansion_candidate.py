from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.research.strategy_research_runner import run_strategy_research_harness
from src.strategies.xauusd_session_volatility_expansion import XauusdSessionVolatilityExpansionCandidate

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "xauusd_session_volatility_expansion_v0_11"


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows), encoding="utf-8")


def _row(timestamp: datetime, open_price: float, high: float, low: float, close: float) -> str:
    return f"{timestamp:%Y-%m-%d %H:%M},{open_price},{high},{low},{close},1"


def _normal_row(timestamp: datetime, price: float = 2000.0) -> str:
    return _row(timestamp, price, price + 0.5, price - 0.5, price)


def _append_normal_until(rows: list[str], timestamp: datetime, target: datetime) -> datetime:
    while timestamp < target:
        rows.append(_normal_row(timestamp))
        timestamp += timedelta(minutes=15)
    return timestamp


def _profitable_upper_session_rows(start: datetime, trade_count: int) -> tuple[list[str], datetime]:
    rows: list[str] = []
    timestamp = _append_normal_until(rows, start, start + timedelta(days=1))
    for trade_number in range(trade_count):
        signal_time = start + timedelta(days=1 + trade_number, hours=15)
        timestamp = _append_normal_until(rows, timestamp, signal_time)
        rows.extend(
            [
                _row(signal_time, 2000.0, 2001.3, 1999.8, 2001.2),
                _row(signal_time + timedelta(minutes=15), 2001.25, 2003.4, 2001.0, 2003.2),
            ]
        )
        timestamp = signal_time + timedelta(minutes=30)
        timestamp = _append_normal_until(rows, timestamp, start + timedelta(days=2 + trade_number))
    return rows, timestamp


def _ready_dataset(data_dir: Path, train_trades: int = 0, validation_trades: int = 0) -> None:
    data_dir.mkdir()
    rows = ["timestamp,open,high,low,close,volume"]
    if train_trades:
        train_rows, _ = _profitable_upper_session_rows(datetime(2025, 1, 1), train_trades)
        rows.extend(train_rows)
    else:
        rows.append(_row(datetime(2025, 6, 30, 23, 45), 2000, 2002, 1999, 2001))
    if validation_trades:
        validation_rows, _ = _profitable_upper_session_rows(datetime(2025, 7, 1), validation_trades)
        rows.extend(validation_rows)
    else:
        rows.append(_row(datetime(2025, 7, 1), 2001, 2003, 2000, 2002))
    rows.append(_row(datetime(2026, 1, 1), 2002, 2004, 2001, 2003))
    _write_csv(data_dir / "xauusd_m15_fixture.csv", rows)


def _candles(rows: list[str]) -> list[dict[str, str]]:
    return [
        {
            "timestamp": line.split(",")[0],
            "open": line.split(",")[1],
            "high": line.split(",")[2],
            "low": line.split(",")[3],
            "close": line.split(",")[4],
        }
        for line in rows
    ]


def test_candidate_parameters_are_fixed_and_returned_in_report(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)
    params = report["candidate"]["parameters"]

    assert params["atr_period_bars"] == 96
    assert params["reference_lookback_bars"] == 16
    assert params["session_start_hour_utc"] == 15
    assert params["session_end_hour_utc"] == 17
    assert params["signal_range_atr_min"] == 0.75
    assert params["stop_atr_buffer"] == 0.55
    assert params["target_r"] == 1.00
    assert params["max_hold_bars"] == 8
    assert params["cost_r_per_trade"] == 0.05
    assert params["cooldown_bars_after_trade"] == 12


def test_candidate_runs_on_synthetic_train_validation_data(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=2, validation_trades=1)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)

    assert report["status"] == "candidate_evaluated"
    assert report["results"]["train_metrics"]["trade_count"] == 2
    assert report["results"]["validation_metrics"]["trade_count"] == 1


def test_candidate_does_not_access_oos(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=2, validation_trades=1)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)

    assert report["oos_guard"]["oos_locked"] is True
    assert report["oos_guard"]["oos_access_attempted"] is False
    assert report["results"]["out_of_sample_result"] == "locked_not_evaluated"


def test_candidate_report_contains_no_individual_trade_instructions(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=1, validation_trades=1)

    report_text = json.dumps(run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)).lower()

    assert "entry_price" not in report_text
    assert "exit_price" not in report_text
    assert "trade_id" not in report_text
    assert "direction" not in report_text


def test_candidate_report_does_not_contain_trade_direction_words(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=1, validation_trades=1)

    report_text = json.dumps(run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID))

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text


def test_validation_gate_can_pass_on_controlled_profitable_fixture(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=100, validation_trades=30)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)

    assert report["validation_gate"]["passed"] is True
    assert report["decision"]["eligible_for_oos_review"] is True
    assert report["results"]["train_metrics"]["profit_factor"] == "inf"
    assert report["results"]["validation_metrics"]["expectancy"] > 0


def test_candidate_ignores_same_breakout_outside_session_window() -> None:
    candidate = XauusdSessionVolatilityExpansionCandidate()
    rows: list[str] = []
    timestamp = _append_normal_until(rows, datetime(2025, 1, 1), datetime(2025, 1, 2, 10))
    rows.extend(
        [
            _row(timestamp, 2000.0, 2001.3, 1999.8, 2001.2),
            _row(timestamp + timedelta(minutes=15), 2001.25, 2003.4, 2001.0, 2003.2),
        ]
    )

    outcomes = candidate.run_on_split(_candles(rows), "train")

    assert outcomes == []


def test_intrabar_ambiguity_uses_conservative_stop_first_rule() -> None:
    candidate = XauusdSessionVolatilityExpansionCandidate()
    rows: list[str] = []
    timestamp = _append_normal_until(rows, datetime(2025, 1, 1), datetime(2025, 1, 2, 15))
    rows.extend(
        [
            _row(timestamp, 2000.0, 2001.3, 1999.8, 2001.2),
            _row(timestamp + timedelta(minutes=15), 2001.25, 2003.4, 1999.0, 2001.5),
        ]
    )

    outcomes = candidate.run_on_split(_candles(rows), "train")

    assert outcomes == [-1.05]


def test_cost_r_per_trade_is_deducted() -> None:
    candidate = XauusdSessionVolatilityExpansionCandidate()
    rows, _ = _profitable_upper_session_rows(datetime(2025, 1, 1), 1)

    outcomes = candidate.run_on_split(_candles(rows), "train")

    assert outcomes == [0.95]


def test_cli_can_run_v0_11_candidate(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=1, validation_trades=1)

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_strategy_research_harness.py"),
            "--data-dir",
            str(data_dir),
            "--candidate",
            CANDIDATE_ID,
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout)["candidate"]["candidate_id"] == CANDIDATE_ID
