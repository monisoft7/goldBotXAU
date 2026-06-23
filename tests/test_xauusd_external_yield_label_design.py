from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_external_yield_label_design import build_label_design_report

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_LABELS = [
    "nominal_yield_rising",
    "nominal_yield_falling",
    "real_yield_rising",
    "real_yield_falling",
    "yield_shock_up",
    "yield_shock_down",
    "gold_yield_pressure_aligned",
    "gold_yield_decoupling",
    "breakeven_inflation_rising",
    "breakeven_inflation_falling",
    "fed_funds_pressure_tightening",
    "fed_funds_pressure_easing",
]

REQUIRED_LABEL_FIELDS = {
    "label_name",
    "required_series",
    "required_input_fields",
    "timeframe_applicability",
    "release_timestamp_requirement",
    "safe_backward_asof_requirement",
    "no_lookahead_rule",
    "intended_interpretation_for_xauusd_macro_context",
    "not_a_trade_signal_warning",
}


def test_label_definitions_include_all_required_fields() -> None:
    report = build_label_design_report()
    labels = report["labels_defined"]

    assert [label["label_name"] for label in labels] == EXPECTED_LABELS
    assert report["label_count"] == len(EXPECTED_LABELS)

    for label in labels:
        assert REQUIRED_LABEL_FIELDS <= set(label)
        assert label["required_series"]
        assert "release_timestamp" in label["required_input_fields"]
        assert label["release_timestamp_requirement"]
        assert label["safe_backward_asof_requirement"]
        assert label["no_lookahead_rule"]
        assert "not a buy/sell signal" in label["not_a_trade_signal_warning"]


def test_labels_require_release_timestamp_and_backward_asof_policy() -> None:
    report = build_label_design_report()

    assert report["release_timestamp_policy_required"] is True
    assert report["backward_asof_required"] is True
    assert report["no_lookahead_policy_confirmed"] is True
    for label in report["labels_defined"]:
        assert "release_timestamp" in label["required_input_fields"]
        assert "at or before the target timestamp" in label["safe_backward_asof_requirement"]
        assert "Observation dates alone are not availability proof" in label["no_lookahead_rule"]


def test_labels_do_not_create_trade_signals_or_blockers() -> None:
    report = build_label_design_report()

    assert report["labels_used_as_trade_blockers"] is False
    assert report["labels_used_for_strategy_testing"] is False
    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False
    assert report["trade_signals_output"] is False
    assert report["strategy_rules_created"] is False
    assert report["strategy_rules_modified"] is False


def test_no_external_or_persistent_data_side_effects_are_declared() -> None:
    report = build_label_design_report()

    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["data_csv_touched"] is False
    assert report["real_xauusd_data_used"] is False
    assert report["aligned_dataset_created"] is False


def test_no_oos_retune_search_grid_or_execution_surface() -> None:
    report = build_label_design_report()

    assert report["train_validation_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False
    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["trade_recommendation_output"] is False


def test_report_includes_required_label_and_safety_fields() -> None:
    report = build_label_design_report()

    assert report["label_design_version"] == "v0_78"
    assert report["label_design_status"] == "external_yield_label_design_completed"
    assert report["source_schema_version"] == "v0_74"
    assert report["source_validator_version"] == "v0_75"
    assert report["source_ingestion_version"] == "v0_76"
    assert report["source_alignment_version"] == "v0_77"
    assert sorted(report["required_series_by_label"]) == sorted(EXPECTED_LABELS)
    assert report["recommended_next_step"] == "v0_79_external_yield_label_fixture_application_no_strategy"


def test_script_writes_report_without_external_data_access() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_external_yield_label_design_v0_78.py"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["label_design_version"] == "v0_78"
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert (ROOT / "reports" / "xauusd_external_yield_label_design_v0_78.json").exists()
