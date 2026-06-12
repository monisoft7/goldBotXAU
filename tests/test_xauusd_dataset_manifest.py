from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.data.xauusd_dataset_manifest import build_xauusd_dataset_manifest

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows), encoding="utf-8")


def _write_dataset(data_dir: Path, rows: list[str]) -> None:
    data_dir.mkdir()
    _write_csv(data_dir / "xauusd_m15_fixture.csv", rows)


def test_no_local_data_blocks_readiness(tmp_path: Path) -> None:
    manifest = build_xauusd_dataset_manifest(tmp_path / "data").to_dict()

    assert manifest["status"] == "no_local_data_found"
    assert manifest["readiness"]["ready_for_strategy_research"] is False
    assert "no_local_data_found" in manifest["readiness"]["blocker_reasons"]


def test_valid_dataset_covering_all_periods_is_ready(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_dataset(
        data_dir,
        [
            "timestamp,open,high,low,close,volume",
            "2025-06-30 23:45,2000,2002,1999,2001,1",
            "2025-07-01 00:00,2001,2003,2000,2002,1",
            "2026-01-01 00:00,2002,2004,2001,2003,1",
        ],
    )

    manifest = build_xauusd_dataset_manifest(data_dir).to_dict()

    assert manifest["status"] in {"manifest_ready", "manifest_has_warnings"}
    assert manifest["readiness"]["ready_for_strategy_research"] is True
    assert manifest["splits"]["train"]["candle_count"] == 1
    assert manifest["splits"]["validation"]["candle_count"] == 1
    assert manifest["splits"]["out_of_sample"]["candle_count"] == 1


def test_missing_oos_period_blocks_strategy_readiness(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_dataset(
        data_dir,
        [
            "time,open,high,low,close",
            "2025-06-30 23:45,2000,2002,1999,2001",
            "2025-07-01 00:00,2001,2003,2000,2002",
        ],
    )

    manifest = build_xauusd_dataset_manifest(data_dir).to_dict()

    assert manifest["readiness"]["ready_for_strategy_research"] is False
    assert "missing_out_of_sample_period" in manifest["readiness"]["blocker_reasons"]


def test_invalid_ohlc_blocks_readiness(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_dataset(
        data_dir,
        [
            "datetime,open,high,low,close",
            "2025-06-30 23:45,2000,1999,1998,2001",
        ],
    )

    manifest = build_xauusd_dataset_manifest(data_dir).to_dict()

    assert manifest["status"] == "manifest_invalid"
    assert manifest["readiness"]["ready_for_strategy_research"] is False


def test_duplicate_timestamps_block_readiness(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_dataset(
        data_dir,
        [
            "timestamp,open,high,low,close",
            "2025-06-30 23:45,2000,2002,1999,2001",
            "2025-06-30T23:45:00,2001,2003,2000,2002",
        ],
    )

    manifest = build_xauusd_dataset_manifest(data_dir).to_dict()

    assert manifest["status"] == "manifest_invalid"
    assert manifest["readiness"]["ready_for_strategy_research"] is False


def test_split_counts_are_chronological_and_exclusive(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_dataset(
        data_dir,
        [
            "date,open,high,low,close",
            "2025-01-01 00:00,2000,2002,1999,2001",
            "2025-06-30 23:45,2001,2003,2000,2002",
            "2025-07-01 00:00,2002,2004,2001,2003",
            "2025-12-31 23:45,2003,2005,2002,2004",
            "2026-01-01 00:00,2004,2006,2003,2005",
        ],
    )

    manifest = build_xauusd_dataset_manifest(data_dir).to_dict()
    splits = manifest["splits"]

    assert splits["train"]["end"] < splits["validation"]["start"]
    assert splits["validation"]["end"] < splits["out_of_sample"]["start"]
    assert sum(split["candle_count"] for split in splits.values()) == manifest["dataset"]["candle_count"]


def test_cli_json_includes_safety_flags_and_writes_output(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    output_path = tmp_path / "reports" / "manifest.json"
    _write_dataset(
        data_dir,
        [
            "time,open,high,low,close",
            "2025-06-30 23:45,2000,2002,1999,2001",
            "2025-07-01 00:00,2001,2003,2000,2002",
            "2026-01-01 00:00,2002,2004,2001,2003",
        ],
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_dataset_manifest.py"),
            "--data-dir",
            str(data_dir),
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    manifest = json.loads(completed.stdout)
    saved_manifest = json.loads(output_path.read_text(encoding="utf-8"))

    assert manifest == saved_manifest
    assert manifest["safety"] == {
        "demo_enabled": False,
        "live_enabled": False,
        "order_send_allowed": False,
        "strategy_logic_added": False,
    }


def test_no_demo_live_order_send_permission_exposed() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "data" / "xauusd_dataset_manifest.py",
            ROOT / "scripts" / "build_xauusd_dataset_manifest.py",
        ]
    ).lower()

    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "order" + "_send(" not in source_text


def test_manifest_includes_required_split_policy_fields(tmp_path: Path) -> None:
    manifest = build_xauusd_dataset_manifest(tmp_path / "data").to_dict()
    policy = manifest["split_policy"]

    assert policy["method"] == "fixed_chronological_split"
    assert policy["train_end"] == "2025-06-30T23:59:59"
    assert policy["validation_start"] == "2025-07-01T00:00:00"
    assert policy["validation_end"] == "2025-12-31T23:59:59"
    assert policy["oos_start"] == "2026-01-01T00:00:00"
    assert policy["leakage_prevention"] == "chronological_only_no_shuffle"
