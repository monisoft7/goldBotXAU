from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

from src.research.xauusd_oil_proxy_quality_and_label_design import (
    DEFAULT_AUDIT_REPORT,
    DEFAULT_OUTPUT_REPORT,
    build_and_write_report,
    build_oil_proxy_quality_and_label_design,
    reject_invalid_ohlc_rows,
    safe_asof_proxy_row,
)

ROOT = Path(__file__).resolve().parents[1]


def _audit() -> dict:
    return json.loads((ROOT / DEFAULT_AUDIT_REPORT).read_text(encoding="utf-8"))


def test_brn_selected_by_quality_evidence_not_prior_order() -> None:
    report = build_oil_proxy_quality_and_label_design(_audit())

    assert report["selected_proxy_symbol_or_null"] == "BRN"
    assert report["quality_scores_by_symbol"]["BRN"] > report["quality_scores_by_symbol"]["WTI"]
    brn_row = next(row for row in report["ranking_table"] if row["symbol"] == "BRN")
    assert brn_row["best_overlap_rows"] > next(row for row in report["ranking_table"] if row["symbol"] == "WTI")[
        "best_overlap_rows"
    ]
    assert "quality score" in report["selection_reason"]


def test_wti_can_be_selected_if_quality_evidence_is_better() -> None:
    audit = _audit()
    audit["symbol_timeframe_audits"]["WTI"]["M15"]["overlap_with_xauusd_summary"]["overlap_row_floor"] = 120000
    audit["symbol_timeframe_audits"]["WTI"]["M15"]["gap_summary"]["gap_count"] = 0
    audit["symbol_timeframe_audits"]["WTI"]["M15"]["gap_summary"]["max_gap_minutes"] = 0

    report = build_oil_proxy_quality_and_label_design(audit)

    assert report["selected_proxy_symbol_or_null"] == "WTI"
    assert report["fallback_proxy_symbol_or_null"] == "BRN"
    assert report["quality_scores_by_symbol"]["WTI"] > report["quality_scores_by_symbol"]["BRN"]


def test_invalid_or_missing_ohlc_rows_are_rejected_safely() -> None:
    rows = [
        {"timestamp": "2026-01-01T00:00:00", "open": 1, "high": 2, "low": 1, "close": 1.5},
        {"timestamp": "2026-01-01T00:05:00", "open": None, "high": 2, "low": 1, "close": 1.5},
        {"timestamp": "2026-01-01T00:10:00", "open": 3, "high": 2, "low": 1, "close": 1.5},
    ]

    valid, rejected = reject_invalid_ohlc_rows(rows)

    assert len(valid) == 1
    assert [row["reject_reason"] for row in rejected] == ["missing_or_non_numeric_ohlc", "inconsistent_ohlc_range"]


def test_safe_asof_alignment_never_uses_future_proxy_bars() -> None:
    rows = [
        {"timestamp": "2026-01-01T00:00:00", "close": 70},
        {"timestamp": "2026-01-01T00:15:00", "close": 71},
        {"timestamp": "2026-01-01T00:30:00", "close": 72},
    ]

    selected = safe_asof_proxy_row(rows, datetime.fromisoformat("2026-01-01T00:16:00"))

    assert selected is not None
    assert selected["timestamp"] == "2026-01-01T00:15:00"


def test_no_persistent_csv_or_data_csv_touch_flags() -> None:
    before = {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}

    report = build_and_write_report(ROOT / DEFAULT_AUDIT_REPORT, ROOT / DEFAULT_OUTPUT_REPORT)

    after = {path: path.stat().st_mtime_ns for path in (ROOT / "data").glob("*.csv")}
    assert before == after
    assert report["aligned_dataset_created"] is False
    assert report["data_csv_touched"] is False


def test_no_strategy_rules_trade_signals_or_trade_blockers_are_created() -> None:
    report = build_oil_proxy_quality_and_label_design(_audit())

    assert report["labels_used_as_trade_blockers"] is False
    assert report["labels_used_for_strategy_testing"] is False
    assert report["safety"]["strategy_rules_created"] is False
    assert report["safety"]["strategy_rules_modified"] is False
    assert report["safety"]["trade_signals_output"] is False
    assert report["approved_for_trade_filtering"] is False


def test_no_oos_retune_threshold_search_or_grid_is_performed() -> None:
    report = build_oil_proxy_quality_and_label_design(_audit())

    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False
    assert report["executable_candidate_created"] is False


def test_report_includes_required_ranking_label_and_safety_fields() -> None:
    report = build_oil_proxy_quality_and_label_design(_audit())

    required_fields = {
        "design_version",
        "design_status",
        "source_oil_audit_version",
        "candidate_symbols_ranked",
        "selected_proxy_symbol_or_null",
        "fallback_proxy_symbol_or_null",
        "selection_reason",
        "quality_scores_by_symbol",
        "ranking_table",
        "rejected_proxy_symbols",
        "safe_asof_alignment_feasible_by_symbol",
        "selected_proxy_safe_asof_alignment_feasible",
        "labels_defined",
        "label_count",
        "lookahead_risk_detected",
        "labels_used_as_trade_blockers",
        "labels_used_for_strategy_testing",
        "aligned_dataset_created",
        "data_csv_touched",
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
    assert required_fields <= set(report)
    assert report["design_version"] == "v0_70"
    assert report["source_oil_audit_version"] == "v0_69"
    assert report["candidate_symbols_ranked"] == ["BRN", "WTI"]
    assert report["label_count"] == 7
    for label in report["labels_defined"]:
        assert label["safe_asof_requirement"]
        assert "Never use a later proxy bar" in label["no_lookahead_rule"]
        assert "not a trade signal" in label["not_a_trade_signal_warning"]


def test_completed_no_safe_proxy_status_when_all_safe_asof_flags_are_false() -> None:
    audit = copy.deepcopy(_audit())
    for symbol in ("BRN", "WTI"):
        for timeframe_audit in audit["symbol_timeframe_audits"][symbol].values():
            timeframe_audit["safe_asof_alignment_feasible"] = False

    report = build_oil_proxy_quality_and_label_design(audit)

    assert report["design_status"] == "oil_proxy_quality_and_label_design_completed_no_safe_proxy"
    assert report["selected_proxy_symbol_or_null"] is None
