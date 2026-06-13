from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.xauusd_compression_expansion_candidate import (
    BLOCKED_DECISION,
    CANDIDATE_ID,
    CREATE_DECISION,
    REJECT_DECISION,
    decide_compression_expansion_candidate_v0_26,
)
from src.research.xauusd_session_structure_atlas import profile_xauusd_session_structure_atlas

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


def _daily_rows(start: str, days: int, *, expands: bool = True) -> list[dict[str, float | str]]:
    current = date.fromisoformat(start)
    rows: list[dict[str, float | str]] = []
    for day_index in range(days):
        rows.extend(_one_day_rows(current + timedelta(days=day_index), base=2000.0 + day_index * 2.0, expands=expands))
    return rows


def _one_day_rows(day: date, *, base: float, expands: bool) -> list[dict[str, float | str]]:
    specs = [
        (0, 0.10, 0.15),
        (1, 0.10, 0.15),
        (6, 0.75 if expands else 0.03, 1.40 if expands else 0.10),
        (7, 0.75 if expands else 0.03, 1.40 if expands else 0.10),
        (12, 0.50, 1.00),
        (13, 0.50, 1.00),
        (18, -0.10, 0.50),
        (19, -0.10, 0.50),
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


def _manifest_and_data(tmp_path: Path) -> tuple[Path, Path]:
    manifest = tmp_path / "reports" / "manifest.json"
    data_dir = tmp_path / "data"
    _write_manifest(manifest)
    return manifest, data_dir


def _stable_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    manifest, data_dir = _manifest_and_data(tmp_path)
    rows = _daily_rows("2025-05-01", 55, expands=True) + _daily_rows("2025-07-01", 25, expands=True)
    _write_rows(data_dir / "xauusd_m5_fixture.csv", rows)
    _write_rows(data_dir / "xauusd_m10_fixture.csv", rows)
    atlas_path = tmp_path / "reports" / "atlas.json"
    atlas_path.write_text(
        json.dumps(profile_xauusd_session_structure_atlas(data_dir, manifest), indent=2),
        encoding="utf-8",
    )
    return manifest, data_dir, atlas_path


def _inconclusive_atlas() -> dict[str, object]:
    return {
        "profiler_version": "v0_25",
        "status": "profile_ready",
        "oos_rows_used": 0,
        "dataset": {"profiled_splits": ["train", "validation"], "oos_row_count_used": 0},
        "fixed_research_design": {"threshold_search_used": False, "parameter_grid_used": False},
        "family_results": {
            "compression_then_expansion": {
                "strong_enough_for_future_single_fixed_candidate": False,
                "stability_assessment": {"label": "inconclusive", "stable": False},
                "degradation_assessment": {"within_fixed_limit": False},
                "train_result": {
                    "sample_count": 10,
                    "dominant_behavior": "insufficient",
                    "edge_over_neutral": 0.0,
                },
                "validation_result": {
                    "sample_count": 2,
                    "dominant_behavior": "insufficient",
                    "edge_over_neutral": 0.0,
                },
            }
        },
    }


def test_missing_v0_25_atlas_blocks_cleanly(tmp_path: Path) -> None:
    result = decide_compression_expansion_candidate_v0_26(tmp_path / "missing.json")

    assert result.decision_report["decision"] == BLOCKED_DECISION
    assert result.decision_report["candidate_created"] is False
    assert result.candidate_report is None


def test_inconclusive_atlas_rejects_cleanly(tmp_path: Path) -> None:
    atlas_path = tmp_path / "reports" / "atlas.json"
    atlas_path.parent.mkdir(parents=True, exist_ok=True)
    atlas_path.write_text(json.dumps(_inconclusive_atlas()), encoding="utf-8")

    result = decide_compression_expansion_candidate_v0_26(atlas_path)

    assert result.decision_report["decision"] == REJECT_DECISION
    assert result.decision_report["candidate_created"] is False
    assert result.candidate_report is None


def test_creates_at_most_one_fixed_compression_expansion_candidate(tmp_path: Path) -> None:
    manifest, data_dir, atlas_path = _stable_fixture(tmp_path)

    result = decide_compression_expansion_candidate_v0_26(atlas_path, data_dir=data_dir, manifest_path=manifest)

    assert result.decision_report["decision"] == CREATE_DECISION
    assert result.decision_report["candidate_created"] is True
    assert result.decision_report["candidate_id"] == CANDIDATE_ID
    assert result.candidate_report is not None
    assert result.candidate_report["candidate_id"] == CANDIDATE_ID
    assert result.candidate_report["candidate"]["fixed_rules"]["threshold_search_used"] is False


def test_candidate_uses_train_validation_only_and_zero_oos_rows(tmp_path: Path) -> None:
    manifest, data_dir, atlas_path = _stable_fixture(tmp_path)

    result = decide_compression_expansion_candidate_v0_26(atlas_path, data_dir=data_dir, manifest_path=manifest)
    assert result.candidate_report is not None

    assert result.candidate_report["splits_used"] == ["train", "validation"]
    assert result.candidate_report["oos_rows_used"] == 0
    assert result.candidate_report["evaluation_scope"]["oos_evaluated"] is False


def test_no_eligible_for_oos_review_promotion_in_v0_26(tmp_path: Path) -> None:
    manifest, data_dir, atlas_path = _stable_fixture(tmp_path)

    result = decide_compression_expansion_candidate_v0_26(atlas_path, data_dir=data_dir, manifest_path=manifest)

    assert result.candidate_report is not None
    assert result.candidate_report["candidate"]["eligible_for_oos_review"] is False
    assert result.candidate_report["candidate"]["oos_status"] == "locked_not_evaluated"


def test_reports_m5_m10_and_combined_evidence_separately(tmp_path: Path) -> None:
    manifest, data_dir, atlas_path = _stable_fixture(tmp_path)

    result = decide_compression_expansion_candidate_v0_26(atlas_path, data_dir=data_dir, manifest_path=manifest)
    assert result.candidate_report is not None
    evidence = result.candidate_report["timeframe_evidence"]

    assert set(evidence["by_timeframe"]) == {"M5", "M10"}
    assert evidence["combined"]["stability_assessment"]["stable"] is True
    assert evidence["by_timeframe"]["M5"]["stability_assessment"]["stable"] is True
    assert evidence["by_timeframe"]["M10"]["stability_assessment"]["stable"] is True
    assert evidence["double_counting_assessment"]["combined_sample_count_not_treated_as_independent_event_count"] is True


def test_no_execution_order_demo_live_or_direction_words_are_introduced(tmp_path: Path) -> None:
    manifest, data_dir, atlas_path = _stable_fixture(tmp_path)

    result = decide_compression_expansion_candidate_v0_26(atlas_path, data_dir=data_dir, manifest_path=manifest)
    report_text = json.dumps(result.to_dict())
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_compression_expansion_candidate.py",
            ROOT / "scripts" / "decide_compression_expansion_candidate_v0_26.py",
        ]
    ).lower()

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "execution_queue_enabled\": true" not in source_text


def test_rejected_old_candidates_and_spike_candidate_are_not_retuned() -> None:
    candidates = {
        candidate["candidate_id"]: candidate
        for candidate in research_candidate_registry()["candidates"]
    }
    old_ids = {
        "xauusd_atr_impulse_reversion_v0_7",
        "xauusd_multi_bar_exhaustion_reversion_v0_8",
        "xauusd_session_volatility_expansion_v0_11",
        "xauusd_low_atr_range_expansion_followthrough_v0_14",
        "xauusd_low_atr_x_hour_16_v0_17",
    }

    for candidate_id in old_ids:
        assert candidates[candidate_id]["status"] == "rejected"
        assert candidates[candidate_id]["do_not_retune"] is True
    assert candidates["xauusd_low_tf_spike_m5_hour_11_fade_v0_23"]["retuned_rejected_candidate"] is False
    assert candidates["xauusd_low_tf_spike_m5_hour_11_fade_v0_23"]["status"] == (
        "rejected_train_validation_gate_failed"
    )


def test_cli_writes_v0_26_decision_and_candidate_reports(tmp_path: Path) -> None:
    manifest, data_dir, atlas_path = _stable_fixture(tmp_path)
    decision_output = tmp_path / "reports" / "decision.json"
    candidate_output = tmp_path / "reports" / "candidate.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "decide_compression_expansion_candidate_v0_26.py"),
            "--atlas-report",
            str(atlas_path),
            "--data-dir",
            str(data_dir),
            "--manifest",
            str(manifest),
            "--output",
            str(decision_output),
            "--candidate-output",
            str(candidate_output),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout)["decision"] == CREATE_DECISION
    assert json.loads(decision_output.read_text(encoding="utf-8"))["candidate_id"] == CANDIDATE_ID
    assert json.loads(candidate_output.read_text(encoding="utf-8"))["status"] == "train_validation_research_candidate_only"
