from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.research.advisor_idea_triage_profiler import profile_advisor_ideas
from src.research.candidate_registry import research_candidate_registry

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows), encoding="utf-8")


def _row(timestamp: datetime, open_price: float, high: float, low: float, close: float, volume: float = 1.0) -> str:
    return f"{timestamp:%Y-%m-%d %H:%M},{open_price},{high},{low},{close},{volume}"


def _write_ready_dataset(data_dir: Path, train_count: int = 220) -> None:
    data_dir.mkdir()
    rows = ["timestamp,open,high,low,close,volume"]
    timestamp = datetime(2025, 1, 1)
    price = 2000.0
    for index in range(train_count):
        hour_shape = 0.35 if timestamp.hour == 16 else 0.15
        body = hour_shape if index % 3 else -hour_shape
        open_price = price
        close = open_price + body
        span = 0.65 if timestamp.hour in {12, 13, 14, 15, 16, 17, 18} else 0.35
        high = max(open_price, close) + span
        low = min(open_price, close) - span
        rows.append(_row(timestamp, open_price, high, low, close, 10 + index))
        price = close
        timestamp += timedelta(minutes=15)
    rows.append(_row(datetime(2025, 7, 1), 2500, 2600, 2400, 2550, 999))
    rows.append(_row(datetime(2026, 1, 1), 2600, 2700, 2500, 2650, 999))
    _write_csv(data_dir / "xauusd_m15_fixture.csv", rows)


def test_profiler_uses_train_split_only(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir, train_count=220)

    report = profile_advisor_ideas(data_dir)

    assert report["status"] == "profile_ready"
    assert report["dataset"]["discovery_split"] == "train"
    assert report["dataset"]["train_candle_count"] == 220
    assert report["dataset"]["validation_candle_count"] == 1


def test_oos_access_remains_locked(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_advisor_ideas(data_dir)

    assert report["oos_guard"] == {
        "oos_locked": True,
        "oos_access_attempted": False,
        "oos_access_allowed": False,
    }
    assert report["safety"]["oos_evaluated"] is False


def test_validation_is_not_used_for_discovery(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_advisor_ideas(data_dir)
    hour_16_samples = report["advisor_ideas"]["hour_16_isolated"]["contexts"]["all_dataset_hour_16_candles"][
        "next_1bar"
    ]["sample_count"]

    assert report["dataset"]["discovery_split"] == "train"
    assert hour_16_samples < report["dataset"]["train_candle_count"]


def test_all_six_advisor_ideas_are_present(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_advisor_ideas(data_dir)

    assert set(report["advisor_ideas"]) == {
        "hour_16_isolated",
        "low_atr_x_hour_16",
        "asia_range_pre_qualifier",
        "day_of_week_filter",
        "htf_trend_filter",
        "v0_11_rescue_train_fix",
    }


def test_v0_11_rescue_train_fix_is_rejected_not_allowed(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_advisor_ideas(data_dir)

    assert report["advisor_ideas"]["v0_11_rescue_train_fix"]["status"] == "rejected_not_allowed"
    assert report["advisor_ideas"]["v0_11_rescue_train_fix"]["eligible_for_ranking"] is False


def test_low_atr_x_hour_16_includes_fixed_and_rolling_contexts(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    contexts = profile_advisor_ideas(data_dir)["advisor_ideas"]["low_atr_x_hour_16"]["contexts"]

    assert "hour_16_fixed_low_atr_all" in contexts
    assert "hour_16_fixed_low_atr_after_compression" in contexts
    assert "hour_16_rolling_low_atr_all" in contexts
    assert "hour_16_rolling_low_atr_after_compression" in contexts


def test_hour_16_is_labelled_dataset_hour_16_not_guaranteed_utc(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    idea = profile_advisor_ideas(data_dir)["advisor_ideas"]["hour_16_isolated"]

    assert idea["timestamp_label"] == "dataset_hour_16"
    assert "project treats it as dataset hour" in idea["timestamp_note"]


def test_asia_range_pre_qualifier_has_no_range_break_boundary_logic(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    idea = profile_advisor_ideas(data_dir)["advisor_ideas"]["asia_range_pre_qualifier"]
    text = json.dumps(idea).lower()

    assert idea["range_boundary_logic_present"] is False
    assert "breakout" not in text
    assert "boundary" not in set(idea)


def test_htf_trend_filter_uses_m15_derived_proxy_only(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    idea = profile_advisor_ideas(data_dir)["advisor_ideas"]["htf_trend_filter"]

    assert idea["data_source"] == "M15_derived_proxy_only"
    assert idea["external_higher_timeframe_fetch_used"] is False
    assert set(idea["contexts"]) == {"positive_slope", "negative_slope", "flat_slope"}


def test_day_of_week_diagnostics_exist(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    idea = profile_advisor_ideas(data_dir)["advisor_ideas"]["day_of_week_filter"]

    assert set(idea["contexts"]) == {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
    assert "strongest_weekday_by_average_abs_forward_move_to_atr" in idea
    assert "strongest_weekday_by_directional_imbalance" in idea


def test_ranking_returns_one_recommended_next_research_direction(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    ranking = profile_advisor_ideas(data_dir)["ranking"]

    assert ranking["recommended_next_research_direction"] in {
        "no_edge_found",
        "investigate_hour_16_isolated",
        "investigate_low_atr_x_hour_16",
        "investigate_asia_pre_qualifier",
        "investigate_day_filter",
        "investigate_htf_proxy_filter",
        "needs_more_diagnostics",
    }
    assert ranking["recommended_v0_17_action"] in {
        "build_fixed_candidate",
        "run_more_diagnostics",
        "stop_strategy_search_temporarily",
    }


def test_no_strategy_candidate_is_registered() -> None:
    before = research_candidate_registry()
    after = research_candidate_registry()

    assert before == after
    assert after["candidate_count"] == 8
    assert all("v0_16" not in candidate["candidate_id"] for candidate in after["candidates"])


def test_no_trade_simulation_is_added(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report = profile_advisor_ideas(data_dir)

    assert report["safety"]["trade_simulation_added"] is False
    assert report["safety"]["research_candidate_logic_present"] is False


def test_report_contains_no_buy_or_sell_strings(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    report_text = json.dumps(profile_advisor_ideas(data_dir))

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text


def test_safety_flags_exist(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    safety = profile_advisor_ideas(data_dir)["safety"]

    assert safety["demo_enabled"] is False
    assert safety["live_enabled"] is False
    assert safety["order_send_allowed"] is False
    assert safety["execution_queue_enabled"] is False
    assert safety["buy_sell_output_allowed"] is False
    assert safety["execution_logic_present"] is False
    assert safety["trade_recommendation_output_present"] is False


def test_no_demo_live_order_send_execution_permission_exposed() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "advisor_idea_triage_profiler.py",
            ROOT / "scripts" / "triage_advisor_ideas.py",
        ]
    ).lower()

    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "execution_queue_enabled\": true" not in source_text


def test_cli_json_works(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_ready_dataset(data_dir)

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "triage_advisor_ideas.py"),
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

    assert report["profiler_version"] == "v0_16"
    assert report["status"] == "profile_ready"


def test_cli_output_file_works(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    output = tmp_path / "triage.json"
    _write_ready_dataset(data_dir)

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "triage_advisor_ideas.py"),
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

    assert json.loads(output.read_text(encoding="utf-8"))["profiler_version"] == "v0_16"


def test_no_data_case_handled_safely(tmp_path: Path) -> None:
    report = profile_advisor_ideas(tmp_path / "empty")

    assert report["status"] == "data_not_ready"
    assert report["dataset"]["discovery_split"] == "train"
    assert report["oos_guard"]["oos_locked"] is True
    assert report["advisor_ideas"]["v0_11_rescue_train_fix"]["status"] == "rejected_not_allowed"
