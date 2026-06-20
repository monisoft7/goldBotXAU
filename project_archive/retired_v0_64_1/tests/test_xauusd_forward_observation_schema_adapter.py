from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.project_health_check import build_project_health_report
from src.research.xauusd_forward_observation_runner import EXPECTED_CSV_SCHEMA
from src.research.xauusd_forward_observation_schema_adapter import (
    normalize_xauusd_forward_observation_csv,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_rows(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = fieldnames or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _exporter_rows() -> list[dict[str, object]]:
    return [
        {
            "timestamp": "2026-06-12T00:00:00",
            "open": "3400.0",
            "high": "3402.0",
            "low": "3399.0",
            "close": "3401.0",
            "volume": "11.0",
        },
        {
            "timestamp": "2026-06-12T00:05:00",
            "open": "3401.0",
            "high": "3404.0",
            "low": "3400.0",
            "close": "3403.0",
            "volume": "12.0",
        },
    ]


def test_adapter_maps_exporter_csv_fixture_into_expected_journal_schema(tmp_path: Path) -> None:
    input_csv = tmp_path / "fixture_exporter.csv"
    output_csv = tmp_path / "data" / "fixture_forward.csv"
    _write_rows(input_csv, _exporter_rows())

    report = normalize_xauusd_forward_observation_csv(
        input_file=input_csv,
        output_file=output_csv,
        symbol="XAUUSD",
        timeframe="M5",
        project_root=tmp_path,
    ).to_dict()

    assert report["adapter_status"] == "framework_ready"
    assert report["expected_output_schema"] == EXPECTED_CSV_SCHEMA
    assert report["supported_timeframes"] == ["M5", "M10"]
    assert report["mt5_called"] is False
    assert report["data_exported_from_mt5"] is False

    with output_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert list(rows[0]) == EXPECTED_CSV_SCHEMA
    assert rows[0]["timestamp_utc"] == "2026-06-12T00:00:00+00:00"
    assert rows[0]["symbol"] == "XAUUSD"
    assert rows[0]["timeframe"] == "M5"
    assert rows[0]["tick_volume"] == "11.0"
    assert rows[0]["spread"] == "0"
    assert "unavailable_from_exporter" in rows[0]["source"]


def test_adapter_requires_explicit_symbol_and_timeframe_when_missing(tmp_path: Path) -> None:
    input_csv = tmp_path / "fixture_exporter.csv"
    _write_rows(input_csv, _exporter_rows())

    missing_symbol = normalize_xauusd_forward_observation_csv(
        input_file=input_csv,
        output_file=tmp_path / "data" / "missing_symbol.csv",
        timeframe="M5",
        project_root=tmp_path,
    ).to_dict()
    missing_timeframe = normalize_xauusd_forward_observation_csv(
        input_file=input_csv,
        output_file=tmp_path / "data" / "missing_timeframe.csv",
        symbol="XAUUSD",
        project_root=tmp_path,
    ).to_dict()

    assert missing_symbol["adapter_status"] == "blocked_schema_mismatch"
    assert "explicit_symbol_required_when_missing_from_csv" in missing_symbol["errors"]
    assert missing_timeframe["adapter_status"] == "blocked_schema_mismatch"
    assert "explicit_timeframe_required_when_missing_from_csv" in missing_timeframe["errors"]


def test_adapter_handles_missing_spread_safely_with_warning(tmp_path: Path) -> None:
    input_csv = tmp_path / "fixture_exporter.csv"
    output_csv = tmp_path / "data" / "fixture_forward.csv"
    _write_rows(input_csv, _exporter_rows())

    report = normalize_xauusd_forward_observation_csv(
        input_file=input_csv,
        output_file=output_csv,
        symbol="XAUUSD",
        timeframe="M10",
        project_root=tmp_path,
    ).to_dict()

    assert "spread_unavailable_from_exporter_set_to_0" in report["warnings"]
    assert report["spread_policy"] == "set_to_0_with_warning_when_unavailable_from_exporter"

    with output_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["spread"] for row in rows} == {"0"}
    assert all("spread=unavailable_from_exporter" in row["source"] for row in rows)


def test_adapter_blocks_unsupported_timeframe(tmp_path: Path) -> None:
    input_csv = tmp_path / "fixture_exporter.csv"
    _write_rows(input_csv, _exporter_rows())

    report = normalize_xauusd_forward_observation_csv(
        input_file=input_csv,
        output_file=tmp_path / "data" / "fixture_forward.csv",
        symbol="XAUUSD",
        timeframe="M15",
        project_root=tmp_path,
    ).to_dict()

    assert report["adapter_status"] == "blocked_unsupported_timeframe"
    assert "timeframe_not_supported" in report["errors"]
    assert report["output_file"] is None


def test_adapter_does_not_call_mt5() -> None:
    report = normalize_xauusd_forward_observation_csv(
        input_file=ROOT / "missing.csv",
        output_file=ROOT / "data" / "unused.csv",
        symbol="XAUUSD",
        timeframe="M5",
        project_root=ROOT,
    ).to_dict()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_schema_adapter.py").read_text(
        encoding="utf-8"
    )

    assert report["mt5_called"] is False
    assert "MetaTrader5" not in source_text
    assert "copy_rates" not in source_text
    assert "initialize(" not in source_text
    assert "shutdown(" not in source_text


def test_adapter_does_not_repeat_oos(tmp_path: Path) -> None:
    input_csv = tmp_path / "fixture_exporter.csv"
    _write_rows(input_csv, _exporter_rows())
    report = normalize_xauusd_forward_observation_csv(
        input_file=input_csv,
        output_file=tmp_path / "data" / "fixture_forward.csv",
        symbol="XAUUSD",
        timeframe="M5",
        project_root=tmp_path,
    ).to_dict()
    source_text = (ROOT / "src" / "research" / "xauusd_forward_observation_schema_adapter.py").read_text(
        encoding="utf-8"
    )

    assert report["repeated_oos_review"] is False
    assert report["safety"]["new_oos_evaluation_allowed"] is False
    assert "run_xauusd_oos_review_v0_29" not in source_text
    assert "load_oos_rows" not in source_text
    assert "evaluate_oos" not in source_text


def test_adapter_introduces_no_buy_sell_output(tmp_path: Path) -> None:
    input_csv = tmp_path / "fixture_exporter.csv"
    _write_rows(input_csv, _exporter_rows())
    report_text = json.dumps(
        normalize_xauusd_forward_observation_csv(
            input_file=input_csv,
            output_file=tmp_path / "data" / "fixture_forward.csv",
            symbol="XAUUSD",
            timeframe="M5",
            project_root=tmp_path,
        ).to_dict()
    )
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_schema_adapter.py",
            ROOT / "scripts" / "normalize_xauusd_forward_observation_csv_v0_34_1.py",
        ]
    )

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text


def test_adapter_introduces_no_execution_order_demo_or_live_semantics(tmp_path: Path) -> None:
    input_csv = tmp_path / "fixture_exporter.csv"
    _write_rows(input_csv, _exporter_rows())
    report = normalize_xauusd_forward_observation_csv(
        input_file=input_csv,
        output_file=tmp_path / "data" / "fixture_forward.csv",
        symbol="XAUUSD",
        timeframe="M5",
        project_root=tmp_path,
    ).to_dict()
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_forward_observation_schema_adapter.py",
            ROOT / "scripts" / "normalize_xauusd_forward_observation_csv_v0_34_1.py",
        ]
    ).lower()

    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["safety"]["order_send_allowed"] is False
    assert report["safety"]["order_check_allowed"] is False
    assert report["safety"]["execution_queue_allowed"] is False
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "broker" not in source_text


def test_adapter_does_not_modify_candidate_rules(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    input_csv = tmp_path / "fixture_exporter.csv"
    _write_rows(input_csv, _exporter_rows())

    report = normalize_xauusd_forward_observation_csv(
        input_file=input_csv,
        output_file=tmp_path / "data" / "fixture_forward.csv",
        symbol="XAUUSD",
        timeframe="M5",
        project_root=tmp_path,
    ).to_dict()
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_rules_modified"] is False
    assert report["safety"]["candidate_rules_modified"] is False


def test_adapter_keeps_project_health_safe() -> None:
    health = build_project_health_report(ROOT)

    assert health["status"] in {"healthy", "warnings"}
    assert health["failures"] == []
    assert health["failure_files"] == []
    assert health["project_state"]["oos_locked"] is True
