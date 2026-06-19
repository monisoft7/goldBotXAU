from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from src.research.xauusd_edge_profiler import (
    COMPLETED_NO_CLEAR_LEADS,
    COMPLETED_WITH_LEADS,
    EVENT_FAMILIES,
    PROFILER_VERSION,
    build_xauusd_edge_profiler_v0_54,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _manifest(path: Path) -> None:
    _write_json(
        path,
        {
            "manifest_version": "v0_5",
            "split_policy": {
                "method": "fixed_chronological_split",
                "train_end": "2025-06-30T23:59:59",
                "validation_start": "2025-07-01T00:00:00",
                "validation_end": "2025-12-31T23:59:59",
                "oos_start": "2026-01-01T00:00:00",
            },
        },
    )


def _source_board(path: Path) -> None:
    _write_json(
        path,
        {
            "board_version": "v0_53",
            "board_status": "no_external_shortlist_candidate_passed",
            "oos_used": False,
        },
    )


def _m15_day(day: date, *, base: float, strong: bool) -> list[dict[str, float | str]]:
    london_close = base + 8.0 if strong else base
    ny_close = london_close + 1.0 if strong else base
    specs = [
        (0, 0, base, base + 0.4, base - 0.4, base),
        (6, 45, base, base + 0.4, base - 0.4, base),
        (7, 0, base, base + 0.6, base - 0.2, base + 0.5 if strong else base),
        (7, 15, base + 0.5 if strong else base, base + 4.0 if strong else base + 0.3, base, base + 3.5 if strong else base),
        (11, 45, base + 3.5 if strong else base, london_close + 0.3, base, london_close),
        (13, 0, london_close, london_close + 0.5, london_close - 0.2, london_close + 0.4 if strong else london_close),
        (13, 45, london_close + 0.4 if strong else london_close, london_close + 1.0, london_close - 0.2, london_close + 0.8 if strong else london_close),
        (14, 0, london_close + 0.8 if strong else london_close, london_close + 1.3, london_close - 0.2, london_close + 1.0 if strong else london_close),
        (16, 45, ny_close, ny_close + 0.3, ny_close - 0.3, ny_close),
        (20, 45, ny_close, ny_close + 0.2, ny_close - 0.2, ny_close),
    ]
    return [
        {
            "timestamp": datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute).isoformat(),
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1.0,
        }
        for hour, minute, open_price, high, low, close in specs
    ]


def _m5_day(day: date, *, base: float, strong: bool) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    price = base
    for index in range(24):
        timestamp = datetime.combine(day, datetime.min.time()).replace(hour=9, minute=0) + timedelta(minutes=5 * index)
        move = 0.2 if strong and index % 8 < 5 else 0.0
        open_price = price
        close = price + move
        rows.append(
            {
                "timestamp": timestamp.isoformat(),
                "open": open_price,
                "high": max(open_price, close) + 0.05,
                "low": min(open_price, close) - 0.05,
                "close": close,
                "volume": 1.0,
            }
        )
        price = close
    return rows


def _fixture(tmp_path: Path, *, strong: bool, day_count: int = 30) -> tuple[Path, Path, Path]:
    data_dir = tmp_path / "data"
    manifest = tmp_path / "reports" / "manifest.json"
    source = tmp_path / "reports" / "v0_53.json"
    _manifest(manifest)
    _source_board(source)
    m15_rows: list[dict[str, float | str]] = []
    m5_rows: list[dict[str, float | str]] = []
    sequence = 0
    for index in range(day_count):
        day = date(2025, 5, 1) + timedelta(days=index)
        m15_rows.extend(_m15_day(day, base=2000.0 + sequence, strong=strong))
        m5_rows.extend(_m5_day(day, base=2000.0 + sequence, strong=strong))
        sequence += 1
    for index in range(day_count):
        day = date(2025, 7, 1) + timedelta(days=index)
        m15_rows.extend(_m15_day(day, base=2100.0 + sequence, strong=strong))
        m5_rows.extend(_m5_day(day, base=2100.0 + sequence, strong=strong))
        sequence += 1
    for index in range(3):
        day = date(2026, 1, 2) + timedelta(days=index)
        m15_rows.extend(_m15_day(day, base=2200.0 + sequence, strong=True))
        m5_rows.extend(_m5_day(day, base=2200.0 + sequence, strong=True))
        sequence += 1
    _write_csv(data_dir / "xauusd_m15_fixture.csv", m15_rows)
    _write_csv(data_dir / "xauusd_m5_xauusd_fixture.csv", m5_rows)
    return data_dir, manifest, source


def _build(tmp_path: Path, *, strong: bool, day_count: int = 30) -> dict[str, object]:
    data_dir, manifest, source = _fixture(tmp_path, strong=strong, day_count=day_count)
    return build_xauusd_edge_profiler_v0_54(
        data_dir=data_dir,
        manifest_path=manifest,
        source_board_path=source,
    )


def test_all_required_event_families_are_present(tmp_path: Path) -> None:
    report = _build(tmp_path, strong=True)

    assert report["profiler_version"] == PROFILER_VERSION
    assert report["event_families_profiled"] == list(EVENT_FAMILIES)
    assert [result["event_family_id"] for result in report["event_family_results"]] == list(EVENT_FAMILIES)


def test_profiler_is_descriptive_not_execution_or_candidate_creation(tmp_path: Path) -> None:
    report = _build(tmp_path, strong=True)

    assert report["purpose"] == "empirical_edge_mapping_not_strategy_backtest"
    assert report["candidate_created"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["safety"]["strategy_backtest"] is False
    assert report["safety"]["execution_queue_created"] is False
    assert report["safety"]["scheduler_created"] is False


def test_train_validation_only_oos_not_used_and_no_retune_or_search(tmp_path: Path) -> None:
    report = _build(tmp_path, strong=True)

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["split_candle_counts"]["M15"]["excluded_oos"] > 0
    assert report["split_candle_counts"]["M5"]["excluded_oos"] > 0


def test_data_csv_not_staged_or_committed(tmp_path: Path) -> None:
    report = _build(tmp_path, strong=True)
    completed = subprocess.run(
        ["git", "status", "--short", "--", "data/*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert report["data_csv_added_to_git"] is False
    assert completed.stdout.strip() == ""


def test_sample_size_warnings_work(tmp_path: Path) -> None:
    report = _build(tmp_path, strong=True, day_count=3)

    assert report["sample_size_warnings"]
    assert any("validation_event_count_below_clear_lead_floor" in warning for warning in report["sample_size_warnings"])


def test_concentration_warnings_work(tmp_path: Path) -> None:
    report = _build(tmp_path, strong=True, day_count=30)

    assert report["concentration_warnings"]
    assert any("events_concentrated_in_single_month" in warning for warning in report["concentration_warnings"])


def test_strong_fixture_creates_research_lead(tmp_path: Path) -> None:
    report = _build(tmp_path, strong=True)

    assert report["profiler_status"] == COMPLETED_WITH_LEADS
    assert report["strongest_empirical_leads"]
    assert report["strongest_empirical_leads"][0]["event_family_id"] in set(EVENT_FAMILIES)
    assert report["recommended_v0_55_research_plan"][0].startswith("v0_55 fixed-rule candidate design")
    assert report["next_recommended_step"] == "v0_55 fixed-rule candidate design for top 1-2 leads, no OOS"


def test_weak_fixture_produces_no_clear_lead(tmp_path: Path) -> None:
    report = _build(tmp_path, strong=False)

    assert report["profiler_status"] == COMPLETED_NO_CLEAR_LEADS
    assert report["strongest_empirical_leads"] == []
    assert report["next_recommended_step"] == "stop current branch or broaden data/features"


def test_each_family_result_has_required_fields(tmp_path: Path) -> None:
    report = _build(tmp_path, strong=True)

    for result in report["event_family_results"]:
        assert set(result).issuperset(
            {
                "event_family_id",
                "event_count_train",
                "event_count_validation",
                "total_event_count",
                "direction_or_behavior_measured",
                "forward_horizons_measured",
                "train_summary",
                "validation_summary",
                "stability_notes",
                "sample_concentration_notes",
                "candidate_suitability_score",
                "recommended_action",
            }
        )
        assert set(result["candidate_suitability_score"]["dimensions"]) == {
            "sample_size",
            "train_validation_consistency",
            "directional_asymmetry",
            "structural_market_logic",
            "implementation_clarity",
            "difference_from_failed_candidates",
            "oos_safety",
        }
        assert result["recommended_action"] in {
            "promote_to_fixed_rule_candidate_design",
            "keep_for_observation_only",
            "reject_as_weak_or_unstable",
        }


def test_cli_writes_required_report(tmp_path: Path) -> None:
    data_dir, manifest, source = _fixture(tmp_path, strong=True)
    output = tmp_path / "reports" / "edge_profiler.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_edge_profiler_v0_54.py"),
            "--json",
            "--output",
            str(output),
            "--data-dir",
            str(data_dir),
            "--manifest",
            str(manifest),
            "--source-board",
            str(source),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report["profiler_version"] == PROFILER_VERSION
    assert output_report["source_previous_board_version"] == "v0_53"
    assert output_report["oos_used"] is False
