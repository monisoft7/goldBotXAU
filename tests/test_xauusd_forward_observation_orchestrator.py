from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from scripts.project_health_check import build_project_health_report
from src.research.xauusd_forward_observation_orchestrator import (
    APPROVAL_TOKEN,
    build_xauusd_forward_observation_cycle_protocol_v0_36,
    run_xauusd_forward_observation_cycle_v0_36,
)
from src.research.xauusd_forward_observation_runner import ALLOWED_TIMEFRAMES, CANDIDATE_ID

ROOT = Path(__file__).resolve().parents[1]


def _write_m5_csv(path: Path, date_text: str = "2026-06-15") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    specs = [
        (0, 6, 3300.0, 3310.0),
        (6, 12, 3305.0, 3330.0),
        (12, 18, 3315.0, 3352.0),
        (18, 24, 3320.0, 3348.0),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for start_hour, end_hour, low, high in specs:
            cursor = _block_boundary_datetime(date_text, start_hour)
            end = _block_boundary_datetime(date_text, end_hour)
            while cursor < end:
                writer.writerow(
                    {
                        "timestamp": cursor.isoformat(),
                        "open": low + 1,
                        "high": high,
                        "low": low,
                        "close": high - 1,
                        "volume": 100,
                    }
                )
                cursor += timedelta(minutes=5)
    return path


def _block_boundary_datetime(date_text: str, hour: int) -> datetime:
    base = datetime.fromisoformat(f"{date_text}T00:00:00")
    return base + timedelta(hours=hour)


def test_m5_fixture_supports_block_range_ending_at_24(tmp_path: Path) -> None:
    m5_csv = _write_m5_csv(tmp_path / "data" / "xauusd_m5_xauusd_2026-06-15_2026-06-15.csv")
    with m5_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[-1]["timestamp"] == "2026-06-15T23:55:00"
    assert not any("T24:" in row["timestamp"] for row in rows)


def test_protocol_confirms_v0_35_gate_and_v0_36_safety() -> None:
    protocol = build_xauusd_forward_observation_cycle_protocol_v0_36()

    assert protocol["candidate_id"] == CANDIDATE_ID
    assert protocol["orchestrator_status"] == "ready_for_approved_read_only_cycle"
    assert protocol["approval_token_required"] is True
    assert protocol["read_only_forward_observation_allowed"] is True
    assert protocol["demo_preflight_allowed"] is False
    assert protocol["execution_allowed"] is False
    assert protocol["demo_allowed"] is False
    assert protocol["live_allowed"] is False
    assert protocol["order_send_allowed"] is False
    assert protocol["order_check_allowed"] is False
    assert protocol["repeated_oos_review"] is False
    assert protocol["candidate_rules_modified"] is False
    assert protocol["raw_market_data_embedded"] is False
    assert protocol["supported_timeframes"] == ["M5", "M10"]


def test_blocks_without_approval_token_and_does_not_call_mt5(tmp_path: Path) -> None:
    called = {"export": False}

    def fake_export(**kwargs: object) -> dict[str, object]:
        called["export"] = True
        return {}

    report = run_xauusd_forward_observation_cycle_v0_36(
        from_date="2026-06-15",
        to_date="2026-06-15",
        approval_token=None,
        project_root=ROOT,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        protocol_output_path=tmp_path / "reports" / "cycle.json",
        export_m5_func=fake_export,
    )

    assert report["orchestrator_status"] == "blocked"
    assert "approval_token_missing_or_invalid" in report["blockers"]
    assert called["export"] is False


def test_blocks_with_wrong_approval_token(tmp_path: Path) -> None:
    report = run_xauusd_forward_observation_cycle_v0_36(
        from_date="2026-06-15",
        to_date="2026-06-15",
        approval_token="wrong",
        project_root=ROOT,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        protocol_output_path=tmp_path / "reports" / "cycle.json",
    )

    assert report["orchestrator_status"] == "blocked"
    assert "approval_token_missing_or_invalid" in report["blockers"]


def test_requires_explicit_from_date_and_to_date(tmp_path: Path) -> None:
    report = run_xauusd_forward_observation_cycle_v0_36(
        from_date=None,
        to_date=None,
        approval_token=APPROVAL_TOKEN,
        project_root=ROOT,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        protocol_output_path=tmp_path / "reports" / "cycle.json",
    )

    assert report["orchestrator_status"] == "blocked"
    assert "from_date_required" in report["blockers"]
    assert "to_date_required" in report["blockers"]


def test_blocks_when_data_unavailable_with_no_synthetic_replacement(tmp_path: Path) -> None:
    report = run_xauusd_forward_observation_cycle_v0_36(
        from_date="2026-06-15",
        to_date="2026-06-15",
        approval_token=APPROVAL_TOKEN,
        project_root=ROOT,
        data_dir=tmp_path / "empty_data",
        reports_dir=tmp_path / "reports",
        protocol_output_path=tmp_path / "reports" / "cycle.json",
    )

    assert report["orchestrator_status"] == "blocked"
    assert "m5_forward_csv_missing_and_mt5_export_not_requested" in report["blockers"]
    assert report["safety_state"]["synthetic_replacement_allowed"] is False


def test_cycle_uses_local_m5_resamples_m10_and_updates_ledger_outputs(tmp_path: Path) -> None:
    m5_csv = _write_m5_csv(tmp_path / "data" / "xauusd_m5_xauusd_2026-06-15_2026-06-15.csv")
    output = tmp_path / "reports" / "xauusd_forward_observation_cycle_protocol_v0_36.json"
    ledger_output = tmp_path / "reports" / "xauusd_forward_observation_ledger_v0_35.json"

    report = run_xauusd_forward_observation_cycle_v0_36(
        from_date="2026-06-15",
        to_date="2026-06-15",
        approval_token=APPROVAL_TOKEN,
        project_root=ROOT,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        m5_csv=m5_csv,
        protocol_output_path=output,
        ledger_output_path=ledger_output,
    )

    assert report["orchestrator_status"] == "completed"
    assert report["supported_timeframes"] == ALLOWED_TIMEFRAMES
    assert report["raw_market_data_embedded"] is False
    assert output.exists()
    assert ledger_output.exists()

    ledger = json.loads(ledger_output.read_text(encoding="utf-8"))
    assert ledger["ledger_status"] == "completed"
    assert ledger["candidate_id"] == CANDIDATE_ID
    assert ledger["independent_observation_session_count"] == 2
    assert ledger["journal_record_count_by_timeframe"] == {"M10": 2, "M5": 2}
    assert ledger["demo_preflight_allowed"] is False


def test_explicit_export_flag_is_required_before_exporter_call(tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def fake_export(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"status": "mt5_not_available", "output_file": None, "errors": ["missing"], "warnings": []}

    report_without_flag = run_xauusd_forward_observation_cycle_v0_36(
        from_date="2026-06-15",
        to_date="2026-06-15",
        approval_token=APPROVAL_TOKEN,
        project_root=ROOT,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        protocol_output_path=tmp_path / "reports" / "cycle_without_flag.json",
        export_m5_func=fake_export,
    )
    report_with_flag = run_xauusd_forward_observation_cycle_v0_36(
        from_date="2026-06-15",
        to_date="2026-06-15",
        approval_token=APPROVAL_TOKEN,
        project_root=ROOT,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        protocol_output_path=tmp_path / "reports" / "cycle_with_flag.json",
        export_m5_from_mt5=True,
        export_m5_func=fake_export,
    )

    assert report_without_flag["orchestrator_status"] == "blocked"
    assert report_with_flag["orchestrator_status"] == "blocked"
    assert len(calls) == 1
    assert calls[0]["timeframe"] == "M5"


def test_does_not_embed_raw_market_rows(tmp_path: Path) -> None:
    m5_csv = _write_m5_csv(tmp_path / "data" / "xauusd_m5_xauusd_2026-06-15_2026-06-15.csv")
    report = run_xauusd_forward_observation_cycle_v0_36(
        from_date="2026-06-15",
        to_date="2026-06-15",
        approval_token=APPROVAL_TOKEN,
        project_root=ROOT,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        m5_csv=m5_csv,
        protocol_output_path=tmp_path / "reports" / "cycle.json",
        ledger_output_path=tmp_path / "reports" / "ledger.json",
    )
    report_text = json.dumps(report)

    assert report["raw_market_data_embedded"] is False
    assert '"open"' not in report_text
    assert '"high"' not in report_text
    assert '"low"' not in report_text
    assert '"close"' not in report_text
    assert '"tick_volume"' not in report_text


def test_keeps_candidate_rules_unchanged(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    m5_csv = _write_m5_csv(tmp_path / "data" / "xauusd_m5_xauusd_2026-06-15_2026-06-15.csv")

    report = run_xauusd_forward_observation_cycle_v0_36(
        from_date="2026-06-15",
        to_date="2026-06-15",
        approval_token=APPROVAL_TOKEN,
        project_root=ROOT,
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        m5_csv=m5_csv,
        protocol_output_path=tmp_path / "reports" / "cycle.json",
        ledger_output_path=tmp_path / "reports" / "ledger.json",
    )
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_rules_modified"] is False
    assert report["safety_state"]["candidate_rules_modified"] is False


def test_does_not_run_oos() -> None:
    report = build_xauusd_forward_observation_cycle_protocol_v0_36()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_orchestrator.py").read_text(
        encoding="utf-8"
    )

    assert report["repeated_oos_review"] is False
    assert report["safety_state"]["new_oos_evaluation_allowed"] is False
    assert "run_xauusd_oos_review_v0_29" not in source_text
    assert "load_oos_rows" not in source_text
    assert "evaluate_oos" not in source_text


def test_no_buy_sell_output_introduced() -> None:
    report_text = json.dumps(build_xauusd_forward_observation_cycle_protocol_v0_36())
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_orchestrator.py",
            ROOT / "scripts" / "run_xauusd_forward_observation_cycle_v0_36.py",
        ]
    )

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text


def test_no_execution_order_demo_live_semantics_introduced() -> None:
    report = build_xauusd_forward_observation_cycle_protocol_v0_36()
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_orchestrator.py",
            ROOT / "scripts" / "run_xauusd_forward_observation_cycle_v0_36.py",
        ]
    ).lower()

    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["order_send_allowed"] is False
    assert report["order_check_allowed"] is False
    assert report["safety_state"]["execution_queue_allowed"] is False
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "demo_allowed\": true" not in source_text
    assert "live_allowed\": true" not in source_text
    assert "execution_allowed\": true" not in source_text


def test_project_health_remains_safe() -> None:
    health = build_project_health_report(ROOT)

    assert health["status"] in {"healthy", "warnings"}
    assert health["failures"] == []
    assert health["failure_files"] == []
    assert health["project_state"]["oos_locked"] is True


def test_cli_blocks_cleanly_with_wrong_token(tmp_path: Path) -> None:
    output = tmp_path / "cycle.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_forward_observation_cycle_v0_36.py"),
            "--json",
            "--from-date",
            "2026-06-15",
            "--to-date",
            "2026-06-15",
            "--approval-token",
            "wrong",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    report = json.loads(completed.stdout)
    assert report["orchestrator_status"] == "blocked"
    assert output.exists()
