from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_paper_forward_watcher import (
    DEFAULT_CANDIDATE_REPORT,
    DEFAULT_OUTPUT,
    build_xauusd_paper_forward_watcher_v0_86,
    save_xauusd_paper_forward_watcher_report,
)

ROOT = Path(__file__).resolve().parents[1]


def test_paper_forward_watcher_builds_report() -> None:
    report = build_xauusd_paper_forward_watcher_v0_86()

    assert report["watch_version"] == "v0_86"
    assert report["candidate_id"] == "xauusd_compression_then_expansion_v0_26"
    assert report["watch_status"] == "watch_completed"
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["order_send_allowed"] is False
    assert report["order_check_allowed"] is False
    assert report["candidate_rules_preserved"] is True
    assert report["watch_record_count"] > 0
    assert isinstance(report["watch_records"], list)


def test_paper_forward_watcher_saves_report(tmp_path: Path) -> None:
    report = build_xauusd_paper_forward_watcher_v0_86()
    output_path = tmp_path / "xauusd_paper_forward_watcher_v0_86.json"

    save_xauusd_paper_forward_watcher_report(report, output_path)

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["watch_version"] == "v0_86"
    assert saved["watch_record_count"] == report["watch_record_count"]


def test_paper_forward_watcher_cli_json_works(tmp_path: Path) -> None:
    output_path = tmp_path / "xauusd_paper_forward_watcher_v0_86.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_paper_forward_watcher_v0_86.py"),
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    report = json.loads(completed.stdout)
    assert report["watch_version"] == "v0_86"
    assert report["watch_status"] == "watch_completed"
    assert output_path.exists()
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["watch_version"] == "v0_86"
