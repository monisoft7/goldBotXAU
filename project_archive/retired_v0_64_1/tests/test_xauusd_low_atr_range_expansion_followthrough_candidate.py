from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.research.strategy_candidate import ResearchCandidate
from src.research.strategy_research_runner import run_strategy_research_harness
from src.strategies.xauusd_low_atr_range_expansion_followthrough import (
    XauusdLowAtrRangeExpansionFollowthroughCandidate,
)

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "xauusd_low_atr_range_expansion_followthrough_v0_14"


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows), encoding="utf-8")


def _row(timestamp: datetime, open_price: float, high: float, low: float, close: float) -> str:
    return f"{timestamp:%Y-%m-%d %H:%M},{open_price},{high},{low},{close},1"


def _quiet_row(timestamp: datetime, price: float = 2000.0) -> str:
    return _row(timestamp, price, price + 0.25, price - 0.25, price)


def _warmup_row(timestamp: datetime, price: float = 2000.0) -> str:
    return _row(timestamp, price, price + 0.50, price - 0.50, price)


def _append_quiet_until(rows: list[str], timestamp: datetime, target: datetime) -> datetime:
    while timestamp < target:
        rows.append(_quiet_row(timestamp))
        timestamp += timedelta(minutes=15)
    return timestamp


def _profitable_positive_rows(start: datetime, trade_count: int) -> tuple[list[str], datetime]:
    rows: list[str] = []
    timestamp = start
    for _ in range(trade_count):
        for _ in range(96):
            rows.append(_warmup_row(timestamp))
            timestamp += timedelta(minutes=15)
        for _ in range(8):
            rows.append(_quiet_row(timestamp))
            timestamp += timedelta(minutes=15)
        signal_time = timestamp
        rows.extend(
            [
                _row(signal_time, 2000.00, 2000.95, 2000.00, 2000.90),
                _row(signal_time + timedelta(minutes=15), 2000.90, 2002.40, 2000.88, 2002.20),
            ]
        )
        timestamp = signal_time + timedelta(minutes=30)
    return rows, timestamp


def _ready_dataset(data_dir: Path, train_trades: int = 0, validation_trades: int = 0) -> None:
    data_dir.mkdir()
    rows = ["timestamp,open,high,low,close,volume"]
    if train_trades:
        train_rows, _ = _profitable_positive_rows(datetime(2025, 1, 1), train_trades)
        rows.extend(train_rows)
    else:
        rows.append(_row(datetime(2025, 6, 30, 23, 45), 2000, 2001, 1999.5, 2000.5))
    if validation_trades:
        validation_rows, _ = _profitable_positive_rows(datetime(2025, 7, 1), validation_trades)
        rows.extend(validation_rows)
    else:
        rows.append(_row(datetime(2025, 7, 1), 2001, 2002, 2000.5, 2001.5))
    rows.append(_row(datetime(2026, 1, 1), 2002, 2003, 2001.5, 2002.5))
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


def _one_signal_rows(
    *,
    compression: bool = True,
    trigger_range: float = 0.95,
    next_high: float = 2002.40,
    next_low: float = 2000.88,
) -> list[str]:
    rows: list[str] = []
    timestamp = datetime(2025, 1, 1)
    for _ in range(96):
        rows.append(_warmup_row(timestamp))
        timestamp += timedelta(minutes=15)
    for _ in range(8):
        if compression:
            rows.append(_quiet_row(timestamp))
        else:
            rows.append(_row(timestamp, 2000.0, 2001.3, 2000.0, 2000.8))
        timestamp += timedelta(minutes=15)
    rows.extend(
        [
            _row(timestamp, 2000.00, 2000.00 + trigger_range, 2000.00, 2000.00 + trigger_range * 0.95),
            _row(timestamp + timedelta(minutes=15), 2000.90, next_high, next_low, 2002.20),
        ]
    )
    return rows


def test_candidate_parameters_are_fixed_and_returned_in_report(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)
    params = report["candidate"]["parameters"]

    assert params == {
        "timeframe": "M15",
        "atr_period_bars": 96,
        "compression_lookback_bars": 8,
        "compression_avg_range_to_atr_max": 0.85,
        "compression_max_single_range_to_atr_max": 1.3230733892270252,
        "trigger_range_to_atr_min": 0.90,
        "trigger_range_to_atr_max": 1.3230733892270252,
        "trigger_body_to_range_min": 0.55,
        "trigger_close_extreme_fraction": 0.25,
        "max_hold_bars": 8,
        "stop_atr_buffer": 0.25,
        "target_r": 0.90,
        "cost_r_per_trade": 0.05,
        "cooldown_bars_after_trade": 12,
    }


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

    assert report["oos_guard"] == {
        "oos_locked": True,
        "oos_access_attempted": False,
        "oos_access_allowed": False,
    }
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


def test_validation_gate_fails_when_not_enough_trades(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=2, validation_trades=1)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)

    assert report["validation_gate"]["passed"] is False
    assert "not_enough_train_trades" in report["validation_gate"]["reasons"]
    assert "not_enough_validation_trades" in report["validation_gate"]["reasons"]


def test_validation_gate_can_pass_on_controlled_profitable_fixture(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=100, validation_trades=30)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)

    assert report["validation_gate"]["passed"] is True
    assert report["decision"]["eligible_for_oos_review"] is True
    assert report["results"]["train_metrics"]["profit_factor"] == "inf"
    assert report["results"]["validation_metrics"]["expectancy"] > 0


def test_intrabar_ambiguity_uses_conservative_stop_first_rule() -> None:
    candidate = XauusdLowAtrRangeExpansionFollowthroughCandidate()

    outcomes = candidate.run_on_split(
        _candles(_one_signal_rows(next_high=2002.40, next_low=1999.70)),
        "train",
    )

    assert outcomes == [-1.05]


def test_cost_r_per_trade_is_deducted() -> None:
    candidate = XauusdLowAtrRangeExpansionFollowthroughCandidate()

    outcomes = candidate.run_on_split(_candles(_one_signal_rows()), "train")

    assert outcomes == [0.85]


def test_compression_condition_is_required_before_trigger() -> None:
    candidate = XauusdLowAtrRangeExpansionFollowthroughCandidate()

    outcomes = candidate.run_on_split(_candles(_one_signal_rows(compression=False)), "train")

    assert outcomes == []


def test_trigger_range_to_atr_must_stay_inside_low_atr_upper_bound() -> None:
    candidate = XauusdLowAtrRangeExpansionFollowthroughCandidate()

    outcomes = candidate.run_on_split(_candles(_one_signal_rows(trigger_range=1.60)), "train")

    assert outcomes == []


def test_forbidden_family_checks_still_work() -> None:
    candidate = ResearchCandidate(
        candidate_id="bad_family",
        candidate_name="Bad Family",
        candidate_version="test",
        family_name="range-break drawdown-control family",
        description="Forbidden family fixture.",
    )

    try:
        candidate.validate()
    except ValueError as exc:
        assert "Forbidden strategy family rejected" in str(exc)
    else:
        raise AssertionError("forbidden family validation did not fail")


def test_cli_can_run_v0_14_candidate(tmp_path: Path) -> None:
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
            "--compact",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(completed.stdout)
    assert report["candidate"]["candidate_id"] == CANDIDATE_ID
    assert "equity_curve" not in completed.stdout


def test_compact_json_contains_safety_flags(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=1, validation_trades=1)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID, compact=True)

    assert set(report["safety"]) == {
        "demo_enabled",
        "live_enabled",
        "order_send_allowed",
        "execution_queue_enabled",
        "buy_sell_output_allowed",
        "oos_evaluated",
        "research_candidate_logic_present",
        "execution_logic_present",
        "trade_recommendation_output_present",
    }


def test_no_demo_live_order_send_or_execution_queue_exposed(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=1, validation_trades=1)

    safety = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)["safety"]

    assert safety["demo_enabled"] is False
    assert safety["live_enabled"] is False
    assert safety["order_send_allowed"] is False
    assert safety["execution_queue_enabled"] is False
    assert safety["research_candidate_logic_present"] is True
    assert safety["execution_logic_present"] is False
    assert safety["trade_recommendation_output_present"] is False
