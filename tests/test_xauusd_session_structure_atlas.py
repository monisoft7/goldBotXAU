from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.xauusd_session_structure_atlas import (
    FAMILIES,
    profile_xauusd_session_structure_atlas,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "manifest_version": "v0_5",
                "split_policy": {
                    "method": "fixed_chronological_split",
                    "train_end": "2025-06-30T23:59:59",
                    "validation_start": "2025-07-01T00:00:00",
                    "validation_end": "2025-12-31T23:59:59",
                    "oos_start": "2026-01-01T00:00:00",
                    "leakage_prevention": "chronological_only_no_shuffle",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_rows(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _manifest_and_data(tmp_path: Path) -> tuple[Path, Path]:
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    _write_manifest(manifest)
    return manifest, data_dir


def _daily_rows(start: str, days: int, *, later_expands: bool = True) -> list[dict[str, float | str]]:
    current = date.fromisoformat(start)
    rows: list[dict[str, float | str]] = []
    for day_index in range(days):
        day = current + timedelta(days=day_index)
        rows.extend(_one_day_rows(day, base=2000.0 + day_index * 3.0, later_expands=later_expands))
    return rows


def _one_day_rows(day: date, *, base: float, later_expands: bool) -> list[dict[str, float | str]]:
    specs = [
        (0, 0.2, 0.4),
        (1, 0.2, 0.4),
        (6, 0.7 if later_expands else 0.05, 1.4 if later_expands else 0.2),
        (7, 0.7 if later_expands else 0.05, 1.4 if later_expands else 0.2),
        (12, 0.6, 1.2),
        (13, 0.5, 1.0),
        (18, -0.2, 0.6),
        (19, -0.2, 0.6),
    ]
    rows: list[dict[str, float | str]] = []
    price = base
    for hour, body, span in specs:
        open_price = price
        close_price = open_price + body
        timestamp = datetime.combine(day, datetime.min.time()).replace(hour=hour).isoformat()
        rows.append(
            {
                "timestamp": timestamp,
                "open": round(open_price, 3),
                "high": round(max(open_price, close_price) + span, 3),
                "low": round(min(open_price, close_price) - span, 3),
                "close": round(close_price, 3),
                "volume": 1.0,
            }
        )
        price = close_price
    return rows


def test_profiler_blocks_if_only_oos_data_exists(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    _write_rows(data_dir / "xauusd_m5_oos_fixture.csv", _daily_rows("2026-01-01", 3))

    report = profile_xauusd_session_structure_atlas(data_dir, manifest)

    assert report["status"] == "blocked_need_train_validation_low_tf_data"
    assert report["oos_rows_used"] == 0
    assert report["recommended_next_step"] == "blocked_inconclusive"


def test_profiler_handles_missing_m5_m10_files_cleanly(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    _write_rows(data_dir / "xauusd_m1_train_validation_fixture.csv", _daily_rows("2025-06-01", 5))

    report = profile_xauusd_session_structure_atlas(data_dir, manifest)

    assert report["status"] == "blocked_need_train_validation_low_tf_data"
    assert report["data_files_used"] == []
    assert report["dataset"]["source_timeframes_used"] == []


def test_profiler_uses_train_validation_only_and_quarantines_mixed_oos(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    _write_rows(
        data_dir / "xauusd_m5_train_validation_fixture.csv",
        _daily_rows("2025-05-01", 55) + _daily_rows("2025-07-01", 25),
    )
    _write_rows(
        data_dir / "xauusd_m10_mixed_oos_fixture.csv",
        _daily_rows("2025-12-30", 2) + _daily_rows("2026-01-01", 2),
    )

    report = profile_xauusd_session_structure_atlas(data_dir, manifest)
    mixed_entry = next(
        entry for entry in report["low_tf_catalog"]["entries"] if entry["filename"] == "xauusd_m10_mixed_oos_fixture.csv"
    )

    assert report["status"] == "profile_ready"
    assert report["oos_rows_used"] == 0
    assert report["dataset"]["oos_row_count_used"] == 0
    assert report["data_files_used"] == ["xauusd_m5_train_validation_fixture.csv"]
    assert mixed_entry["usable_for_profiler"] is False
    assert mixed_entry["split_classification"] == "mixed_contains_oos"


def test_profiler_profiles_all_required_families(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    _write_rows(
        data_dir / "xauusd_m5_train_validation_fixture.csv",
        _daily_rows("2025-05-01", 55) + _daily_rows("2025-07-01", 25),
    )

    report = profile_xauusd_session_structure_atlas(data_dir, manifest)

    assert report["families_profiled"] == list(FAMILIES)
    assert set(report["family_results"]) == set(FAMILIES)
    assert all("train_result" in result for result in report["family_results"].values())
    assert all("validation_result" in result for result in report["family_results"].values())


def test_profiler_reports_stable_weak_and_inconclusive_deterministically(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    _write_rows(
        data_dir / "xauusd_m5_stable_fixture.csv",
        _daily_rows("2025-05-01", 55, later_expands=True) + _daily_rows("2025-07-01", 25, later_expands=True),
    )
    stable_report = profile_xauusd_session_structure_atlas(data_dir, manifest)

    _write_rows(
        data_dir / "xauusd_m5_stable_fixture.csv",
        _daily_rows("2025-05-01", 55, later_expands=True) + _daily_rows("2025-07-01", 25, later_expands=False),
    )
    weak_report = profile_xauusd_session_structure_atlas(data_dir, manifest)

    _write_rows(
        data_dir / "xauusd_m5_stable_fixture.csv",
        _daily_rows("2025-05-01", 4, later_expands=True) + _daily_rows("2025-07-01", 2, later_expands=True),
    )
    inconclusive_report = profile_xauusd_session_structure_atlas(data_dir, manifest)

    family = "asia_range_to_london_expansion"
    assert stable_report["family_results"][family]["stability_assessment"]["label"] == "stable"
    assert weak_report["family_results"][family]["stability_assessment"]["label"] == "weak"
    assert inconclusive_report["family_results"][family]["stability_assessment"]["label"] == "inconclusive"


def test_profiler_produces_no_candidate_registry_promotion_or_oos_evaluation(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    before = research_candidate_registry()
    _write_rows(
        data_dir / "xauusd_m5_train_validation_fixture.csv",
        _daily_rows("2025-05-01", 55) + _daily_rows("2025-07-01", 25),
    )

    report = profile_xauusd_session_structure_atlas(data_dir, manifest)
    after = research_candidate_registry()

    assert before == after
    assert report["safety"]["strategy_candidate_created"] is False
    assert report["safety"]["candidate_registry_promotion_created"] is False
    assert report["safety"]["oos_evaluated"] is False
    assert report["any_family_strong_enough_for_future_single_fixed_candidate"] is True


def test_no_execution_order_demo_live_or_direction_semantics_are_introduced(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    _write_rows(
        data_dir / "xauusd_m5_train_validation_fixture.csv",
        _daily_rows("2025-05-01", 55) + _daily_rows("2025-07-01", 25),
    )

    report_text = json.dumps(profile_xauusd_session_structure_atlas(data_dir, manifest))
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_session_structure_atlas.py",
            ROOT / "scripts" / "profile_session_structure_atlas_v0_25.py",
        ]
    ).lower()

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "execution_queue_enabled\": true" not in source_text


def test_rejected_candidates_are_not_modified_or_retuned() -> None:
    candidates = {
        candidate["candidate_id"]: candidate
        for candidate in research_candidate_registry()["candidates"]
    }

    assert candidates["xauusd_low_tf_spike_m5_hour_11_fade_v0_23"]["status"] == (
        "rejected_train_validation_gate_failed"
    )
    assert candidates["xauusd_low_tf_spike_m5_hour_11_fade_v0_23"]["retuned_rejected_candidate"] is False
    assert research_candidate_registry()["eligible_for_oos_review_count"] == 0


def test_cli_writes_v0_25_atlas_report(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    output = tmp_path / "reports" / "atlas.json"
    _write_rows(
        data_dir / "xauusd_m5_train_validation_fixture.csv",
        _daily_rows("2025-05-01", 55) + _daily_rows("2025-07-01", 25),
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "profile_session_structure_atlas_v0_25.py"),
            "--data-dir",
            str(data_dir),
            "--manifest",
            str(manifest),
            "--output",
            str(output),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout)["profiler_version"] == "v0_25"
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "profile_ready"
