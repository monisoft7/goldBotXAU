from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.candidate_stability_diagnostics import diagnose_candidate_stability
from src.strategies.xauusd_session_volatility_expansion import XauusdSessionVolatilityExpansionCandidate

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "xauusd_session_volatility_expansion_v0_11"
COMPACT_FIELDS = {
    "trade_count",
    "win_rate",
    "profit_factor",
    "expectancy",
    "final_equity_r",
    "max_consecutive_losses",
    "gross_profit",
    "gross_loss",
    "wins",
    "losses",
}


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


def _ready_dataset(data_dir: Path, train_trades: int = 3, validation_trades: int = 2) -> None:
    data_dir.mkdir()
    rows = ["timestamp,open,high,low,close,volume"]
    train_rows, _ = _profitable_upper_session_rows(datetime(2025, 1, 1), train_trades)
    rows.extend(train_rows)
    validation_rows, _ = _profitable_upper_session_rows(datetime(2025, 7, 1), validation_trades)
    rows.extend(validation_rows)
    rows.append(_row(datetime(2026, 1, 1), 2002, 2004, 2001, 2003))
    _write_csv(data_dir / "xauusd_m15_fixture.csv", rows)


def test_diagnostic_uses_train_split_only(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=2, validation_trades=5)

    report = diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    assert report["status"] == "diagnostic_ready"
    assert report["dataset"]["diagnostic_split"] == "train"
    assert report["train_overall_metrics"]["trade_count"] == 2
    assert report["dataset"]["validation_candle_count"] > 0


def test_oos_access_remains_locked(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report = diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    assert report["oos_guard"] == {
        "oos_locked": True,
        "oos_access_attempted": False,
        "oos_access_allowed": False,
    }
    assert report["safety"]["oos_evaluated"] is False


def test_validation_is_not_used_for_discovery_breakdowns(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir, train_trades=1, validation_trades=8)

    report = diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    assert report["train_overall_metrics"]["trade_count"] == 1
    assert report["breakdowns"]["by_year"][0]["bucket"] == "2025"
    assert sum(bucket["trade_count"] for bucket in report["breakdowns"]["by_year"]) == 1


def test_report_includes_all_required_breakdowns(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report = diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    assert set(report["breakdowns"]) == {
        "by_year",
        "by_quarter",
        "by_month",
        "by_hour",
        "by_session_block",
        "by_atr_regime",
    }


def test_report_includes_compact_metrics_per_bucket(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report = diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    for buckets in report["breakdowns"].values():
        for bucket in buckets:
            assert COMPACT_FIELDS.issubset(bucket)


def test_report_includes_stability_summary(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report = diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    assert set(report["stability_summary"]) == {
        "positive_bucket_count",
        "negative_bucket_count",
        "flat_bucket_count",
        "best_bucket",
        "worst_bucket",
        "consistency_score",
        "train_failure_scope",
    }
    assert report["stability_summary"]["train_failure_scope"] in {
        "broad_failure",
        "concentrated_failure",
        "inconclusive",
    }


def test_diagnostic_does_not_change_v0_11_parameters(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)
    before = XauusdSessionVolatilityExpansionCandidate().parameters()

    diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    assert XauusdSessionVolatilityExpansionCandidate().parameters() == before


def test_diagnostic_does_not_register_a_new_candidate(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)
    before = research_candidate_registry()

    diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    assert research_candidate_registry() == before


def test_diagnostic_does_not_output_buy_or_sell_strings(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report_text = json.dumps(diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID))

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text


def test_report_does_not_expose_individual_trade_instructions(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report_text = json.dumps(diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)).lower()

    assert "entry_price" not in report_text
    assert "stop_price" not in report_text
    assert "target_price" not in report_text
    assert "direction" not in report_text
    assert "trade_id" not in report_text


def test_safety_flags_exist(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    report = diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    assert set(report["safety"]) == {
        "demo_enabled",
        "live_enabled",
        "order_send_allowed",
        "execution_queue_enabled",
        "buy_sell_output_allowed",
        "strategy_logic_added",
        "parameter_tuning_added",
        "oos_evaluated",
    }


def test_no_demo_live_order_send_or_execution_permission_exposed(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _ready_dataset(data_dir)

    safety = diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)["safety"]

    assert safety["demo_enabled"] is False
    assert safety["live_enabled"] is False
    assert safety["order_send_allowed"] is False
    assert safety["execution_queue_enabled"] is False


def test_cli_json_works(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    output_path = tmp_path / "reports" / "diagnostic.json"
    _ready_dataset(data_dir)

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "diagnose_candidate_stability.py"),
            "--data-dir",
            str(data_dir),
            "--candidate",
            CANDIDATE_ID,
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(completed.stdout)
    assert report["diagnostic_version"] == "v0_12"
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == report


def test_no_data_case_handled_safely(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    report = diagnose_candidate_stability(data_dir, candidate_id=CANDIDATE_ID)

    assert report["status"] == "data_not_ready"
    assert report["oos_guard"]["oos_locked"] is True
    assert report["diagnostic_decision"]["retune_allowed"] is False
