from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.xauusd_market_profiler import profile_xauusd_market

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows), encoding="utf-8")


def _row(timestamp: datetime, open_price: float, high: float, low: float, close: float, volume: float = 1.0) -> str:
    return f"{timestamp:%Y-%m-%d %H:%M},{open_price},{high},{low},{close},{volume}"


def _write_ready_dataset(data_dir: Path, train_count: int = 120) -> None:
    data_dir.mkdir()
    rows = ["timestamp,open,high,low,close,volume"]
    timestamp = datetime(2025, 1, 1)
    price = 2000.0
    for index in range(train_count):
        body = 0.2 if index % 2 == 0 else -0.2
        open_price = price
        close = open_price + body
        high = max(open_price, close) + 0.4
        low = min(open_price, close) - 0.4
        rows.append(_row(timestamp, open_price, high, low, close, 10 + index))
        price = close
        timestamp += timedelta(minutes=15)
    rows.append(_row(datetime(2025, 7, 1), 2500, 2600, 2400, 2550, 999))
    rows.append(_row(datetime(2026, 1, 1), 2600, 2700, 2500, 2650, 999))
    _write_csv(data_dir / "xauusd_m15_fixture.csv", rows)


def test_profiler_uses_train_split_only(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir, train_count=120)

    report = profile_xauusd_market(data_dir)

    assert report["status"] == "profile_ready"
    assert report["dataset"]["profiled_split"] == "train"
    assert report["train_profile"]["candle_count"] == 120
    assert report["train_profile"]["timestamp_end"].startswith("2025-01-02")


def test_profiler_does_not_access_oos(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_xauusd_market(data_dir)

    assert report["oos_guard"]["oos_locked"] is True
    assert report["oos_guard"]["oos_access_attempted"] is False
    assert report["oos_guard"]["oos_access_allowed"] is False


def test_profiler_does_not_evaluate_validation_as_discovery_data(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir, train_count=120)

    report = profile_xauusd_market(data_dir)
    hour_candle_count = sum(hour["candle_count"] for hour in report["hour_profile"].values())

    assert report["dataset"]["validation_candle_count"] == 1
    assert hour_candle_count == report["train_profile"]["candle_count"]
    assert report["train_profile"]["average_range"] < 2.0


def test_report_includes_required_profile_sections(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_xauusd_market(data_dir)

    assert "hour_profile" in report
    assert "block_profile" in report
    assert "atr_profile" in report
    assert "impulse_diagnostic" in report


def test_hour_profile_has_all_hours(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_xauusd_market(data_dir)

    assert set(report["hour_profile"]) == {f"{hour:02d}" for hour in range(24)}


def test_block_profile_has_fixed_blocks(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_xauusd_market(data_dir)

    assert set(report["block_profile"]) == {
        "block_00_06",
        "block_06_12",
        "block_12_18",
        "block_18_24",
    }


def test_atr_profile_and_impulse_bins_are_present(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_xauusd_market(data_dir)

    assert report["atr_profile"]["atr_period_bars"] == 96
    assert report["atr_profile"]["atr_available_count"] == 25
    assert set(report["impulse_diagnostic"]) == {
        "range_to_atr_gte_1.0",
        "range_to_atr_gte_1.5",
        "range_to_atr_gte_2.0",
    }


def test_no_trade_direction_words_appear(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report_text = json.dumps(profile_xauusd_market(data_dir))

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text


def test_no_demo_live_order_send_permission_exposed() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_market_profiler.py",
            ROOT / "scripts" / "profile_xauusd_market.py",
        ]
    ).lower()

    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text


def test_no_strategy_candidate_is_registered_by_profiler_task() -> None:
    registry = research_candidate_registry()

    assert registry["candidate_count"] == 6
    assert all("v0_10" not in candidate["candidate_id"] for candidate in registry["candidates"])


def test_cli_json_works(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "profile_xauusd_market.py"),
            "--data-dir",
            str(data_dir),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["profiler_version"] == "v0_10"
    assert report["status"] == "profile_ready"


def test_cli_output_file_works(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    output = tmp_path / "profile.json"
    _write_ready_dataset(data_dir)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "profile_xauusd_market.py"),
            "--data-dir",
            str(data_dir),
            "--json",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(output.read_text(encoding="utf-8"))["profiler_version"] == "v0_10"


def test_profile_handles_no_data_safely(tmp_path: Path) -> None:
    report = profile_xauusd_market(tmp_path / "empty")

    assert report["status"] == "data_not_ready"
    assert report["dataset"]["profiled_split"] == "train"
    assert report["oos_guard"]["oos_locked"] is True
    assert report["train_profile"]["candle_count"] == 0
