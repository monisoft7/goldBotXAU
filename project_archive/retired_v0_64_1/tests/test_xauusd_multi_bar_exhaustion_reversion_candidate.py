from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.research.strategy_research_runner import run_strategy_research_harness
from src.strategies.xauusd_multi_bar_exhaustion_reversion import XauusdMultiBarExhaustionReversionCandidate

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "xauusd_multi_bar_exhaustion_reversion_v0_8"


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows), encoding="utf-8")


def _row(timestamp: datetime, open_price: float, high: float, low: float, close: float) -> str:
    return f"{timestamp:%Y-%m-%d %H:%M},{open_price},{high},{low},{close},1"


def _normal_rows(start: datetime, count: int, price: float = 2000.0) -> tuple[list[str], datetime]:
    rows: list[str] = []
    timestamp = start
    for _ in range(count):
        rows.append(_row(timestamp, price, price + 0.5, price - 0.5, price))
        timestamp += timedelta(minutes=15)
    return rows, timestamp


def _profitable_upper_exhaustion_rows(start: datetime, trade_count: int) -> tuple[list[str], datetime]:
    rows, timestamp = _normal_rows(start, 96)
    for _ in range(trade_count):
        rows.extend(
            [
                _row(timestamp, 2000.0, 2001.0, 1999.9, 2000.8),
                _row(timestamp + timedelta(minutes=15), 2000.8, 2001.6, 2000.7, 2001.4),
                _row(timestamp + timedelta(minutes=30), 2001.4, 2002.2, 2001.3, 2002.0),
                _row(timestamp + timedelta(minutes=45), 2002.0, 2003.0, 2001.9, 2002.9),
                _row(timestamp + timedelta(minutes=60), 2002.7, 2002.8, 1999.8, 2000.0),
            ]
        )
        timestamp += timedelta(minutes=75)
        filler, timestamp = _normal_rows(timestamp, 14)
        rows.extend(filler)
    return rows, timestamp


def _ready_dataset(data_dir: Path, train_trades: int = 0, validation_trades: int = 0) -> None:
    data_dir.mkdir()
    rows = ["timestamp,open,high,low,close,volume"]
    if train_trades:
        train_rows, _ = _profitable_upper_exhaustion_rows(datetime(2025, 1, 1), train_trades)
        rows.extend(train_rows)
    else:
        rows.append(_row(datetime(2025, 6, 30, 23, 45), 2000, 2002, 1999, 2001))
    if validation_trades:
        validation_rows, _ = _profitable_upper_exhaustion_rows(datetime(2025, 7, 1), validation_trades)
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
    assert params["sequence_bars"] == 4
    assert params["cumulative_move_atr_min"] == 1.35
    assert params["minimum_aligned_closes"] == 4
    assert params["final_close_extreme_fraction"] == 0.25
    assert params["max_hold_bars"] == 10
    assert params["stop_atr_buffer"] == 0.25
    assert params["target_r"] == 0.90
    assert params["cost_r_per_trade"] == 0.05
    assert params["cooldown_bars_after_trade"] == 14


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


def test_intrabar_ambiguity_uses_conservative_stop_first_rule() -> None:
    candidate = XauusdMultiBarExhaustionReversionCandidate()
    rows, timestamp = _normal_rows(datetime(2025, 1, 1), 96)
    rows.extend(
        [
            _row(timestamp, 2000.0, 2001.0, 1999.9, 2000.8),
            _row(timestamp + timedelta(minutes=15), 2000.8, 2001.6, 2000.7, 2001.4),
            _row(timestamp + timedelta(minutes=30), 2001.4, 2002.2, 2001.3, 2002.0),
            _row(timestamp + timedelta(minutes=45), 2002.0, 2003.0, 2001.9, 2002.9),
            _row(timestamp + timedelta(minutes=60), 2002.7, 2003.4, 2001.3, 2001.8),
        ]
    )

    outcomes = candidate.run_on_split(_candles(rows), "train")

    assert outcomes == [-1.05]


def test_cost_r_per_trade_is_deducted() -> None:
    candidate = XauusdMultiBarExhaustionReversionCandidate()
    rows, _ = _profitable_upper_exhaustion_rows(datetime(2025, 1, 1), 1)

    outcomes = candidate.run_on_split(_candles(rows), "train")

    assert outcomes == [0.85]


def test_cli_can_run_v0_8_candidate(tmp_path: Path) -> None:
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
