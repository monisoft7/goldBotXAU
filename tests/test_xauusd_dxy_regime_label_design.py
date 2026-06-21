from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.xauusd_dxy_regime_label_design import (
    COMPLETED,
    LABEL_DESIGN_VERSION,
    LABEL_NAMES,
    aggregate_sample_label_counts,
    build_xauusd_dxy_regime_label_design_v0_67,
)

ROOT = Path(__file__).resolve().parents[1]


def test_report_contains_required_label_definitions() -> None:
    report = build_xauusd_dxy_regime_label_design_v0_67(root=ROOT)

    assert report["label_design_version"] == LABEL_DESIGN_VERSION
    assert report["label_design_status"] == COMPLETED
    assert report["source_proxy_ranker_version"] == "v0_66"
    assert report["selected_proxy_symbol"] == "DXYN"
    assert report["secondary_proxy_symbol"] == "USDX"
    assert report["label_count"] == 8
    assert [item["label_name"] for item in report["labels_defined"]] == LABEL_NAMES
    for definition in report["labels_defined"]:
        assert definition["required_input_fields"]
        assert definition["timeframe_applicability"] == ["M5", "M10", "M15"]
        assert "less than or equal to the XAUUSD timestamp" in definition["safe_asof_requirement"]
        assert "at or before" in definition["no_lookahead_rule"]
        assert definition["intended_interpretation"]
        assert "Descriptive research context only" in definition["not_a_trade_signal_warning"]


def test_labels_are_definitions_context_only() -> None:
    report = build_xauusd_dxy_regime_label_design_v0_67(root=ROOT)

    assert report["safety"]["research_only"] is True
    assert report["safety"]["definitions_only"] is True
    assert report["labels_used_as_trade_blockers"] is False
    assert report["labels_used_for_strategy_testing"] is False
    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False


def test_labels_do_not_create_trade_signals_or_trade_blockers() -> None:
    report = build_xauusd_dxy_regime_label_design_v0_67(root=ROOT)
    text = json.dumps(report).lower()

    assert report["safety"]["trade_signals_output"] is False
    assert report["safety"]["strategy_rules_created"] is False
    assert report["trade_recommendation_output"] is False
    assert report["labels_used_as_trade_blockers"] is False
    assert "buy_signal" not in text
    assert "sell_signal" not in text


def test_no_strategy_testing_oos_or_retune_is_performed() -> None:
    report = build_xauusd_dxy_regime_label_design_v0_67(root=ROOT)

    assert report["train_validation_only"] is True
    assert report["labels_used_for_strategy_testing"] is False
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False


def test_no_persistent_aligned_csv_or_data_csv_is_created() -> None:
    before = {path.as_posix() for path in (ROOT / "data").glob("*.csv")}
    report = build_xauusd_dxy_regime_label_design_v0_67(root=ROOT)
    after = {path.as_posix() for path in (ROOT / "data").glob("*.csv")}

    assert before == after
    assert report["aligned_dataset_created"] is False
    assert report["data_csv_touched"] is False
    assert report["safety"]["persistent_market_dataset_created"] is False


def test_no_lookahead_is_allowed_for_sample_counts() -> None:
    with pytest.raises(ValueError, match="future proxy timestamp"):
        aggregate_sample_label_counts(
            [
                {
                    "xauusd_timestamp": "2026-01-01T00:00:00",
                    "proxy_timestamp": "2026-01-01T00:05:00",
                    "dxy_strength": True,
                }
            ]
        )


def test_sample_counts_are_aggregate_only_when_sample_is_supplied() -> None:
    counts = aggregate_sample_label_counts(
        [
            {
                "xauusd_timestamp": "2026-01-01T00:05:00",
                "proxy_timestamp": "2026-01-01T00:00:00",
                "dxy_strength": True,
                "gold_dxy_decoupling": True,
            },
            {
                "xauusd_timestamp": "2026-01-01T00:10:00",
                "proxy_timestamp": "2026-01-01T00:05:00",
                "dxy_strength": True,
            },
        ]
    )

    assert counts == {"dxy_strength": 2, "gold_dxy_decoupling": 1}


def test_all_safety_flags_remain_false_or_locked() -> None:
    report = build_xauusd_dxy_regime_label_design_v0_67(root=ROOT)

    for key in (
        "lookahead_risk_detected",
        "labels_used_as_trade_blockers",
        "labels_used_for_strategy_testing",
        "aligned_dataset_created",
        "data_csv_touched",
        "approved_for_strategy_testing",
        "approved_for_trade_filtering",
        "oos_used",
        "repeated_oos_review",
        "retune_performed",
        "threshold_search_performed",
        "parameter_grid_performed",
        "executable_candidate_created",
        "demo_execution_allowed",
        "order_send_called",
        "order_check_called",
        "live_allowed",
        "trade_recommendation_output",
    ):
        assert report[key] is False
        assert report["safety"][key] is False
    assert report["safe_asof_alignment_required"] is True


def test_cli_writes_required_report(tmp_path: Path) -> None:
    output = tmp_path / "reports" / "label_design.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_dxy_regime_label_design_v0_67.py"),
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
    assert stdout_report["label_design_version"] == LABEL_DESIGN_VERSION
    assert output_report["label_design_status"] == COMPLETED
    assert output_report["aligned_dataset_created"] is False
