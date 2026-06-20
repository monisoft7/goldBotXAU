from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.research.strategy_candidate import ResearchCandidate
from src.research.strategy_research_runner import run_strategy_research_harness
from src.strategies.xauusd_atr_impulse_reversion import XauusdAtrImpulseReversionCandidate

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "xauusd_atr_impulse_reversion_v0_7"


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


def _profitable_reversion_rows(start: datetime, trade_count: int) -> tuple[list[str], datetime]:
    rows, timestamp = _normal_rows(start, 96)
    for _ in range(trade_count):
        rows.append(_row(timestamp, 2000.2, 2002.0, 2000.0, 2001.9))
        timestamp += timedelta(minutes=15)
        rows.append(_row(timestamp, 2001.5, 2001.6, 2000.6, 2001.0))
        timestamp += timedelta(minutes=15)
        filler, timestamp = _normal_rows(timestamp, 16)
        rows.extend(filler)
    return rows, timestamp


def _ready_dataset(data_dir: Path, train_trades: int = 0, validation_trades: int = 0) -> None:
    data_dir.mkdir()
    rows = ["timestamp,open,high,low,close,volume"]
    if train_trades:
        train_rows, _ = _profitable_reversion_rows(datetime(2025, 1, 1), train_trades)
        rows.extend(train_rows)
    else:
        rows.append(_row(datetime(2025, 6, 30, 23, 45), 2000, 2002, 1999, 2001))
    if validation_trades:
        validation_rows, _ = _profitable_reversion_rows(datetime(2025, 7, 1), validation_trades)
        rows.extend(validation_rows)
    else:
        rows.append(_row(datetime(2025, 7, 1), 2001, 2003, 2000, 2002))
    rows.append(_row(datetime(2026, 1, 1), 2002, 2004, 2001, 2003))
    _write_csv(data_dir / "xauusd_m15_fixture.csv", rows)


def test_candidate_parameters_are_fixed_and_returned_in_report(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)
    params = report["candidate"]["parameters"]

    assert params["atr_period_bars"] == 96
    assert params["impulse_range_atr_min"] == 1.8
    assert params["body_to_range_min"] == 0.60
    assert params["close_extreme_fraction"] == 0.20
    assert params["max_hold_bars"] == 12
    assert params["stop_atr_buffer"] == 0.30
    assert params["target_r"] == 1.00
    assert params["cost_r_per_trade"] == 0.05
    assert params["cooldown_bars_after_trade"] == 16


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


def test_validation_gate_fails_when_not_enough_trades(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=2, validation_trades=1)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)

    assert report["validation_gate"]["passed"] is False
    assert report["decision"]["eligible_for_oos_review"] is False


def test_validation_gate_can_pass_on_controlled_profitable_fixture(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=100, validation_trades=30)

    report = run_strategy_research_harness(data_dir, candidate_id=CANDIDATE_ID)

    assert report["validation_gate"]["passed"] is True
    assert report["decision"]["eligible_for_oos_review"] is True
    assert report["results"]["train_metrics"]["profit_factor"] == "inf"
    assert report["results"]["validation_metrics"]["expectancy"] > 0


def test_intrabar_ambiguity_uses_conservative_stop_first_rule() -> None:
    candidate = XauusdAtrImpulseReversionCandidate()
    rows, timestamp = _normal_rows(datetime(2025, 1, 1), 96)
    rows.append(_row(timestamp, 2000.2, 2002.0, 2000.0, 2001.9))
    timestamp += timedelta(minutes=15)
    rows.append(_row(timestamp, 2001.5, 2002.5, 2000.5, 2001.0))
    candles = [
        {
            "timestamp": line.split(",")[0],
            "open": line.split(",")[1],
            "high": line.split(",")[2],
            "low": line.split(",")[3],
            "close": line.split(",")[4],
        }
        for line in rows
    ]

    outcomes = candidate.run_on_split(candles, "train")

    assert outcomes == [-1.05]


def test_cost_r_per_trade_is_deducted() -> None:
    candidate = XauusdAtrImpulseReversionCandidate()
    rows, timestamp = _profitable_reversion_rows(datetime(2025, 1, 1), 1)
    candles = [
        {
            "timestamp": line.split(",")[0],
            "open": line.split(",")[1],
            "high": line.split(",")[2],
            "low": line.split(",")[3],
            "close": line.split(",")[4],
        }
        for line in rows
    ]

    outcomes = candidate.run_on_split(candles, "train")

    assert outcomes == [0.95]


def test_forbidden_family_checks_still_work(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)
    candidate = ResearchCandidate(
        candidate_id="bad",
        candidate_name="Bad",
        candidate_version="v0",
        family_name="baseline_current_rules",
        description="Rejected fixture.",
    )

    report = run_strategy_research_harness(data_dir, candidate=candidate)

    assert report["status"] == "candidate_rejected"


def test_cli_can_run_null_candidate_and_v0_7_candidate(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=1, validation_trades=1)

    null_completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_strategy_research_harness.py"),
            "--data-dir",
            str(data_dir),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    candidate_completed = subprocess.run(
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

    assert json.loads(null_completed.stdout)["candidate"]["is_null_candidate"] is True
    assert json.loads(candidate_completed.stdout)["candidate"]["candidate_id"] == CANDIDATE_ID


def test_cli_json_contains_safety_flags(tmp_path: Path) -> None:
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
    report = json.loads(completed.stdout)

    assert report["safety"] == {
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
        "execution_queue_enabled": False,
        "buy_sell_output_allowed": False,
        "oos_evaluated": False,
        "research_candidate_logic_present": True,
        "execution_logic_present": False,
        "trade_recommendation_output_present": False,
    }


def test_no_demo_live_order_send_execution_queue_exposed() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "strategies" / "xauusd_atr_impulse_reversion.py",
            ROOT / "src" / "research" / "strategy_research_runner.py",
            ROOT / "scripts" / "run_strategy_research_harness.py",
        ]
    ).lower()

    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
