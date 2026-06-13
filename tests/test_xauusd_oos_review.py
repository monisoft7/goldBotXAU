from __future__ import annotations

import copy
import csv
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from scripts.project_health_check import build_project_health_report
from src.research.xauusd_oos_review import (
    APPROVAL_TOKEN,
    BLOCKED_ALREADY_EVALUATED_DECISION,
    BLOCKED_APPROVAL_DECISION,
    BLOCKED_PROTOCOL_DECISION,
    run_xauusd_oos_review_v0_29,
    save_xauusd_oos_review_result,
)

ROOT = Path(__file__).resolve().parents[1]
ACTUAL_PROTOCOL = ROOT / "reports" / "xauusd_oos_review_protocol_v0_28.json"
ACTUAL_CANDIDATE = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"


def _write_rows(path: Path, rows: list[dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def _daily_m1_rows(start: str, days: int, *, expands: bool = True) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    first_day = date.fromisoformat(start)
    for day_index in range(days):
        day = first_day + timedelta(days=day_index)
        base = 2000.0 + day_index
        rows.extend(_one_day_m1_rows(day, base=base, expands=expands))
    return rows


def _one_day_m1_rows(day: date, *, base: float, expands: bool) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    price = base
    for minute_index in range(24 * 60):
        timestamp = datetime.combine(day, datetime.min.time()) + timedelta(minutes=minute_index)
        hour = timestamp.hour
        if hour < 6:
            body = 0.01
            span = 0.04
        elif hour < 12:
            body = 0.03 if expands else 0.001
            span = 0.25 if expands else 0.01
        elif hour < 18:
            body = 0.02
            span = 0.18
        else:
            body = -0.005
            span = 0.06
        open_price = price
        close_price = open_price + body
        rows.append(
            {
                "timestamp": timestamp.isoformat(),
                "open": round(open_price, 5),
                "high": round(max(open_price, close_price) + span, 5),
                "low": round(min(open_price, close_price) - span, 5),
                "close": round(close_price, 5),
                "volume": 1.0,
            }
        )
        price = close_price
    return rows


def _write_oos_m1_fixture(data_dir: Path, *, days: int = 30, expands: bool = True) -> None:
    _write_rows(
        data_dir / "xauusd_m1_fixture_2026-01-02_2026-02-01.csv",
        _daily_m1_rows("2026-01-02", days, expands=expands),
    )


def _protocol_copy(tmp_path: Path) -> Path:
    path = tmp_path / "reports" / "protocol.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ACTUAL_PROTOCOL.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def test_wrong_approval_token_blocks(tmp_path: Path) -> None:
    result = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token="wrong",
        output_path=tmp_path / "oos.json",
        data_dir=tmp_path / "data",
    )

    assert result["decision"] == BLOCKED_APPROVAL_DECISION
    assert result["safety"]["oos_evaluated"] is False


def test_missing_approval_token_blocks(tmp_path: Path) -> None:
    result = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token=None,
        output_path=tmp_path / "oos.json",
        data_dir=tmp_path / "data",
    )

    assert result["decision"] == BLOCKED_APPROVAL_DECISION
    assert "approval_token_missing_or_invalid" in result["blockers"]


def test_valid_approval_token_allows_one_time_oos_review(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_oos_m1_fixture(data_dir)

    result = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token=APPROVAL_TOKEN,
        output_path=tmp_path / "oos.json",
        data_dir=data_dir,
    )

    assert result["decision"] in {
        "oos_passed_research_validation",
        "oos_failed_research_validation",
        "oos_inconclusive_research_validation",
    }
    assert result["approval"]["approval_token_accepted"] is True
    assert result["fixed_rules_verification"]["hash_match"] is True
    assert result["safety"]["oos_evaluated"] is True


def test_repeated_oos_review_blocks(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    output_path = tmp_path / "oos.json"
    _write_oos_m1_fixture(data_dir)
    first = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token=APPROVAL_TOKEN,
        output_path=output_path,
        data_dir=data_dir,
    )
    save_xauusd_oos_review_result(first, output_path)

    second = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token=APPROVAL_TOKEN,
        output_path=output_path,
        data_dir=data_dir,
    )

    assert second["decision"] == BLOCKED_ALREADY_EVALUATED_DECISION
    assert second["safety"]["oos_evaluated"] is False


def test_runner_does_not_overwrite_main_report_when_locked_marker_exists(tmp_path: Path) -> None:
    output_path = tmp_path / "oos.json"
    marker_path = output_path.with_name(f"{output_path.stem}.marker.json")
    original_report = {
        "review_version": "v0_29",
        "decision": "oos_passed_research_validation",
        "candidate_id": "xauusd_compression_then_expansion_v0_26",
        "sentinel": "keep_existing_main_report",
    }
    output_path.write_text(json.dumps(original_report, indent=2), encoding="utf-8")
    marker_path.write_text(
        json.dumps(
            {
                "review_version": "v0_29",
                "candidate_id": "xauusd_compression_then_expansion_v0_26",
                "decision": "oos_passed_research_validation",
                "output_path": str(output_path),
                "repeat_review_allowed": False,
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_oos_review_v0_29.py"),
            "--protocol",
            str(ACTUAL_PROTOCOL),
            "--approval-token",
            "invalid-token",
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    blocked = json.loads(completed.stdout)
    assert blocked["decision"] == BLOCKED_ALREADY_EVALUATED_DECISION
    assert json.loads(output_path.read_text(encoding="utf-8")) == original_report


def test_protocol_hash_mismatch_blocks(tmp_path: Path) -> None:
    protocol = json.loads(ACTUAL_PROTOCOL.read_text(encoding="utf-8"))
    protocol["fixed_rules_source"]["rules_hash_sha256"] = "0" * 64
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    data_dir = tmp_path / "data"
    _write_oos_m1_fixture(data_dir)

    result = run_xauusd_oos_review_v0_29(
        protocol_path=protocol_path,
        approval_token=APPROVAL_TOKEN,
        output_path=tmp_path / "oos.json",
        data_dir=data_dir,
    )

    assert result["decision"] == BLOCKED_PROTOCOL_DECISION
    assert "candidate_rules_hash_mismatch" in result["blockers"]


def test_candidate_rules_are_not_modified(tmp_path: Path) -> None:
    before = json.loads(ACTUAL_CANDIDATE.read_text(encoding="utf-8"))["fixed_rules"]
    data_dir = tmp_path / "data"
    _write_oos_m1_fixture(data_dir)

    result = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token=APPROVAL_TOKEN,
        output_path=tmp_path / "oos.json",
        data_dir=data_dir,
    )

    after = json.loads(ACTUAL_CANDIDATE.read_text(encoding="utf-8"))["fixed_rules"]
    assert after == before
    assert result["safety"]["candidate_rules_modified"] is False


def test_oos_boundaries_come_only_from_manifest_and_protocol(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    rows = _daily_m1_rows("2025-12-20", 5, expands=False) + _daily_m1_rows("2026-01-02", 5, expands=True)
    _write_rows(data_dir / "xauusd_m1_boundary_fixture.csv", rows)

    result = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token=APPROVAL_TOKEN,
        output_path=tmp_path / "oos.json",
        data_dir=data_dir,
    )

    assert result["oos_boundaries"] == json.loads(ACTUAL_PROTOCOL.read_text(encoding="utf-8"))["oos_split_boundaries"]
    assert result["oos_data"]["oos_rows_evaluated"] == 10


def test_no_parameter_search_grid_or_retune_introduced(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_oos_m1_fixture(data_dir)

    result = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token=APPROVAL_TOKEN,
        output_path=tmp_path / "oos.json",
        data_dir=data_dir,
    )

    assert result["safety"]["threshold_search_used"] is False
    assert result["safety"]["parameter_grid_used"] is False
    assert result["safety"]["parameter_optimization_used"] is False
    assert result["safety"]["retune_used"] is False


def test_no_execution_order_demo_live_semantics_or_direction_output(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_oos_m1_fixture(data_dir)
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_oos_review.py",
            ROOT / "scripts" / "run_xauusd_oos_review_v0_29.py",
        ]
    ).lower()
    result_text = json.dumps(
        run_xauusd_oos_review_v0_29(
            protocol_path=ACTUAL_PROTOCOL,
            approval_token=APPROVAL_TOKEN,
            output_path=tmp_path / "oos.json",
            data_dir=data_dir,
        )
    )

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "demo_enabled\": true" not in source_text
    assert "live_enabled\": true" not in source_text
    assert "execution_queue_enabled\": true" not in source_text
    assert "B" + "UY" not in result_text
    assert "S" + "ELL" not in result_text


def test_pass_fail_inconclusive_decision_is_deterministic(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    _write_oos_m1_fixture(data_dir, expands=True)

    first = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token=APPROVAL_TOKEN,
        output_path=tmp_path / "first.json",
        data_dir=data_dir,
    )
    second = run_xauusd_oos_review_v0_29(
        protocol_path=ACTUAL_PROTOCOL,
        approval_token=APPROVAL_TOKEN,
        output_path=tmp_path / "second.json",
        data_dir=data_dir,
    )

    assert first["decision"] == second["decision"]
    assert first["decision_checks"] == second["decision_checks"]


def test_project_health_remains_safe_after_v0_29_sources_added() -> None:
    report = build_project_health_report(ROOT)

    assert report["status"] in {"healthy", "warnings"}
    assert report["failures"] == []


def test_cli_writes_oos_report_and_marker(tmp_path: Path) -> None:
    output_path = tmp_path / "oos.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_oos_review_v0_29.py"),
            "--protocol",
            str(ACTUAL_PROTOCOL),
            "--approval-token",
            APPROVAL_TOKEN,
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
    assert report["decision"] in {
        "oos_passed_research_validation",
        "oos_failed_research_validation",
        "oos_inconclusive_research_validation",
    }
    assert json.loads(output_path.read_text(encoding="utf-8"))["review_version"] == "v0_29"
    assert output_path.with_name(f"{output_path.stem}.marker.json").exists()
