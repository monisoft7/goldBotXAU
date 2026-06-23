from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_external_yield_asof_alignment_design import design_external_yield_asof_alignment

ROOT = Path(__file__).resolve().parents[1]


def _records() -> list[dict[str, object]]:
    return [
        {
            "series_id": "DGS10",
            "observation_date": "2026-06-17",
            "value": 4.10,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-18T20:15:00+00:00",
            "input_index": 0,
        },
        {
            "series_id": "DGS10",
            "observation_date": "2026-06-18",
            "value": 4.12,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00+00:00",
            "input_index": 1,
        },
        {
            "series_id": "DGS2",
            "observation_date": "2026-06-17",
            "value": 4.70,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-18T20:15:00+00:00",
            "input_index": 2,
        },
        {
            "series_id": "DFII10",
            "observation_date": "2026-06-18",
            "value": None,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00+00:00",
            "input_index": 3,
        },
        {
            "series_id": "DFF",
            "observation_date": "2026-06-18",
            "value": 4.33,
            "source_name": "FRED / Federal Reserve Economic Data",
            "input_index": 4,
        },
        {
            "series_id": "T10YIE",
            "observation_date": "2026-06-18",
            "value": 2.32,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00",
            "input_index": 5,
        },
        {
            "series_id": "DGS10",
            "observation_date": "2026-06-18",
            "value": 4.13,
            "source_name": "FRED / Federal Reserve Economic Data",
            "release_timestamp": "2026-06-19T20:15:00+00:00",
            "input_index": 6,
        },
    ]


def _targets() -> list[str]:
    return [
        "2026-06-18T19:00:00+00:00",
        "2026-06-18T21:00:00+00:00",
        "2026-06-19T19:00:00+00:00",
        "2026-06-19T21:00:00+00:00",
    ]


def test_valid_released_observations_align_backward_asof() -> None:
    report = design_external_yield_asof_alignment(_records(), _targets())

    after_first_release = report["alignment_summary"][1]["series_results"]
    assert after_first_release["DGS10"]["observation_date"] == "2026-06-17"
    assert after_first_release["DGS10"]["value"] == 4.10
    assert after_first_release["DGS2"]["value"] == 4.70


def test_target_before_release_timestamp_does_not_use_future_value() -> None:
    report = design_external_yield_asof_alignment(_records(), _targets())

    before_second_release = report["alignment_summary"][2]["series_results"]
    assert before_second_release["DGS10"]["observation_date"] == "2026-06-17"
    after_second_release = report["alignment_summary"][3]["series_results"]
    assert after_second_release["DGS10"]["observation_date"] == "2026-06-18"


def test_target_before_first_release_remains_unaligned() -> None:
    report = design_external_yield_asof_alignment(_records(), _targets())

    assert report["alignment_summary"][0]["aligned_series_count"] == 0
    assert report["unaligned_target_count"] == 1


def test_missing_and_timezone_less_release_timestamps_are_not_alignable() -> None:
    report = design_external_yield_asof_alignment(_records(), _targets())

    assert report["rejection_reasons"]["release_timestamp_missing"] == 1
    assert report["rejection_reasons"]["release_timestamp_missing_timezone"] == 1
    assert report["records_not_alignable"] == 4


def test_duplicate_series_date_is_flagged() -> None:
    report = design_external_yield_asof_alignment(_records(), _targets())

    assert report["duplicate_count"] == 1
    assert report["duplicate_keys"] == [{"series_id": "DGS10", "observation_date": "2026-06-18"}]
    assert report["rejection_reasons"]["duplicate_series_id_observation_date"] == 1


def test_multiple_yield_series_align_independently() -> None:
    report = design_external_yield_asof_alignment(_records(), _targets())

    after_first_release = report["alignment_summary"][1]["series_results"]
    assert after_first_release["DGS10"]["observation_date"] == "2026-06-17"
    assert after_first_release["DGS2"]["observation_date"] == "2026-06-17"
    assert after_first_release["DFII10"] is None


def test_no_data_csv_file_is_created_or_touched_by_alignment_design() -> None:
    data_dir = ROOT / "data"
    before = {path: path.stat().st_mtime_ns for path in data_dir.glob("*.csv")}

    design_external_yield_asof_alignment(_records(), _targets())

    after = {path: path.stat().st_mtime_ns for path in data_dir.glob("*.csv")}
    assert after == before


def test_no_external_or_strategy_surfaces_are_performed() -> None:
    report = design_external_yield_asof_alignment(_records(), _targets())

    for key in (
        "external_api_called",
        "external_data_downloaded",
        "dataset_file_created",
        "market_csv_created",
        "data_csv_touched",
        "real_xauusd_data_used",
        "forward_fill_applied",
        "intraday_timestamp_inferred",
        "aligned_dataset_created",
        "labels_used_as_trade_blockers",
        "labels_used_for_strategy_testing",
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
        "strategy_rules_created",
        "strategy_rules_modified",
        "trade_signals_output",
    ):
        assert report[key] is False
    assert report["synthetic_target_timestamps_used"] is True
    assert report["train_validation_only"] is True
    assert report["backward_asof_only"] is True
    assert report["no_lookahead_policy_confirmed"] is True


def test_report_includes_required_alignment_and_safety_fields() -> None:
    report = design_external_yield_asof_alignment(_records(), _targets())

    expected_fields = {
        "alignment_version",
        "alignment_status",
        "source_schema_version",
        "source_validator_version",
        "source_ingestion_version",
        "external_api_called",
        "external_data_downloaded",
        "dataset_file_created",
        "market_csv_created",
        "data_csv_touched",
        "real_xauusd_data_used",
        "synthetic_target_timestamps_used",
        "records_seen",
        "records_alignable",
        "records_not_alignable",
        "target_timestamp_count",
        "aligned_target_count",
        "unaligned_target_count",
        "alignment_cases_tested",
        "rejection_reasons",
        "duplicate_count",
        "timezone_policy_enforced",
        "release_timestamp_policy_enforced",
        "no_lookahead_policy_confirmed",
        "backward_asof_only",
        "forward_fill_applied",
        "intraday_timestamp_inferred",
        "aligned_dataset_created",
        "future_label_candidates_preserved",
        "labels_used_as_trade_blockers",
        "labels_used_for_strategy_testing",
        "approved_for_strategy_testing",
        "approved_for_trade_filtering",
        "train_validation_only",
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
        "recommended_next_step",
    }
    assert expected_fields <= set(report)
    assert report["alignment_version"] == "v0_77"
    assert report["alignment_status"] == "external_yield_asof_alignment_design_completed_with_expected_rejections"
    assert report["source_schema_version"] == "v0_74"
    assert report["source_validator_version"] == "v0_75"
    assert report["source_ingestion_version"] == "v0_76"
    assert report["recommended_next_step"] == "v0_78_external_yield_label_design_no_strategy"


def test_cli_writes_report_from_inline_synthetic_fixture_only() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "design_xauusd_external_yield_asof_alignment_v0_77.py"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(completed.stdout)
    assert report["alignment_version"] == "v0_77"
    assert report["external_api_called"] is False
    assert report["external_data_downloaded"] is False
    assert report["dataset_file_created"] is False
    assert report["market_csv_created"] is False
    assert report["data_csv_touched"] is False
    assert report["real_xauusd_data_used"] is False
    assert report["aligned_dataset_created"] is False
