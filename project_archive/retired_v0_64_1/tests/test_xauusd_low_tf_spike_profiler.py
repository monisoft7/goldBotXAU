from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.data.xauusd_low_tf_dataset_catalog import build_low_tf_dataset_catalog
from src.research.candidate_registry import research_candidate_registry
from src.research.xauusd_low_tf_spike_profiler import profile_low_tf_spike_behavior

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


def _rows(start: str, count: int, minutes: int = 5, spike_every: int | None = None) -> list[dict[str, float | str]]:
    timestamp = datetime.fromisoformat(start)
    price = 2000.0
    rows: list[dict[str, float | str]] = []
    for index in range(count):
        is_spike = spike_every is not None and index >= 100 and index % spike_every == 0
        body = 0.35 if is_spike else 0.05
        span = 1.8 if is_spike else 0.20
        open_price = price
        close = open_price + body
        rows.append(
            {
                "timestamp": (timestamp + timedelta(minutes=minutes * index)).isoformat(),
                "open": round(open_price, 3),
                "high": round(max(open_price, close) + span, 3),
                "low": round(min(open_price, close) - span, 3),
                "close": round(close, 3),
                "volume": 10.0 + index,
            }
        )
        price = close
    return rows


def _manifest_and_data(tmp_path: Path) -> tuple[Path, Path]:
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    _write_manifest(manifest)
    return manifest, data_dir


def test_oos_only_file_is_blocked(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    _write_rows(data_dir / "xauusd_m1_oos_fixture.csv", _rows("2026-01-01T00:00:00", 20, minutes=1))

    catalog = build_low_tf_dataset_catalog(data_dir, manifest)
    report = profile_low_tf_spike_behavior(data_dir, manifest)
    entry = catalog["entries"][0]

    assert entry["split_classification"] == "oos_only"
    assert entry["usable_for_profiler"] is False
    assert entry["quarantine_reason"] == "oos_only_file_blocked_from_profiler"
    assert report["status"] == "blocked_need_train_validation_low_tf_data"
    assert report["dataset"]["oos_row_count_used"] == 0


def test_mixed_file_containing_oos_is_quarantined(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    rows = _rows("2025-12-31T23:40:00", 3, minutes=5) + _rows("2026-01-01T00:00:00", 3, minutes=5)
    _write_rows(data_dir / "xauusd_m5_mixed_fixture.csv", rows)

    catalog = build_low_tf_dataset_catalog(data_dir, manifest)
    report = profile_low_tf_spike_behavior(data_dir, manifest)
    entry = catalog["entries"][0]

    assert entry["split_classification"] == "mixed_contains_oos"
    assert entry["usable_for_profiler"] is False
    assert entry["validation_row_count"] > 0
    assert entry["oos_row_count"] > 0
    assert report["dataset"]["train_row_count"] == 0
    assert report["dataset"]["validation_row_count"] == 0


def test_train_validation_file_can_be_profiled(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    rows = _rows("2025-06-01T00:00:00", 140, spike_every=5) + _rows("2025-07-01T00:00:00", 140, spike_every=5)
    _write_rows(data_dir / "xauusd_m5_train_validation_fixture.csv", rows)

    report = profile_low_tf_spike_behavior(data_dir, manifest)

    assert report["status"] == "profile_ready"
    assert report["dataset"]["profiled_splits"] == ["train", "validation"]
    assert report["dataset"]["oos_row_count_used"] == 0
    assert report["event_counts"]["train_spike_event_count"] > 0
    assert report["event_counts"]["validation_spike_event_count"] > 0
    assert report["grouped_behavior"]


def test_no_execution_order_demo_live_or_direction_semantics_are_introduced(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    _write_rows(data_dir / "xauusd_m10_train_fixture.csv", _rows("2025-06-01T00:00:00", 130, minutes=10, spike_every=7))

    report_text = json.dumps(profile_low_tf_spike_behavior(data_dir, manifest))
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "data" / "xauusd_low_tf_dataset_catalog.py",
            ROOT / "src" / "research" / "xauusd_low_tf_spike_profiler.py",
            ROOT / "scripts" / "profile_low_tf_spike_behavior.py",
        ]
    ).lower()

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "execution_queue_enabled\": true" not in source_text
    assert json.loads(report_text)["safety"]["strategy_candidate_created"] is False


def test_rejected_candidates_are_not_modified_or_retuned() -> None:
    registry = research_candidate_registry()
    rejected = [candidate for candidate in registry["candidates"] if candidate.get("status") == "rejected"]

    assert registry["candidate_count"] == 8
    assert registry["eligible_for_oos_review_count"] == 0
    assert len(rejected) == 5
    assert all(candidate.get("do_not_retune") is True for candidate in rejected)


def test_cli_writes_json_report(tmp_path: Path) -> None:
    manifest, data_dir = _manifest_and_data(tmp_path)
    output = tmp_path / "reports" / "spike_profile.json"
    rows = _rows("2025-06-01T00:00:00", 130, spike_every=5) + _rows("2025-07-01T00:00:00", 130, spike_every=5)
    _write_rows(data_dir / "xauusd_m5_train_validation_fixture.csv", rows)

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "profile_low_tf_spike_behavior.py"),
            "--data-dir",
            str(data_dir),
            "--manifest",
            str(manifest),
            "--json",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output.read_text(encoding="utf-8"))

    assert stdout_report["profiler_version"] == "v0_22"
    assert output_report["status"] == "profile_ready"
