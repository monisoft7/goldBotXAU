from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.research.xauusd_dxy_proxy_quality_ranker import (
    BLOCKED_MISSING_DATA,
    COMPLETED,
    COMPLETED_NO_SAFE_PROXY,
    DEFAULT_CANDIDATE_SYMBOLS,
    RANKER_VERSION,
    assert_no_future_proxy_bars,
    build_xauusd_dxy_proxy_quality_ranker_v0_66,
    safe_backward_asof_alignment_pairs,
)

ROOT = Path(__file__).resolve().parents[1]


def _write_source_audit(path: Path, *, proxy_timeframes: dict[str, object], overlaps: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "audit_version": "v0_65",
                "audit_status": "dxy_proxy_context_feasibility_completed",
                "candidate_symbols_checked": DEFAULT_CANDIDATE_SYMBOLS,
                "xauusd_timeframes_available": {
                    "M5": {"row_count": 100, "first_timestamp": "2026-01-01T00:00:00", "last_timestamp": "2026-01-02T00:00:00"},
                    "M15": {"row_count": 40, "first_timestamp": "2026-01-01T00:00:00", "last_timestamp": "2026-01-02T00:00:00"},
                },
                "proxy_timeframes_available": proxy_timeframes,
                "overlap_summary": overlaps,
                "rejected_proxy_symbols": {},
                "mt5_readonly_discovery": {
                    "attempted": True,
                    "status": "readonly_discovery_completed",
                    "candidate_symbols_available": DEFAULT_CANDIDATE_SYMBOLS,
                    "order_send_called": False,
                    "order_check_called": False,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _tf(row_count: int, first: str, last: str) -> dict[str, object]:
    return {
        "row_count": row_count,
        "first_timestamp": first,
        "last_timestamp": last,
        "series_count": 1,
        "sources": ["mt5_readonly"],
    }


def _overlap(best: int, timeframe: str = "M5") -> dict[str, object]:
    return {
        "usable": best > 0,
        "best_overlap_rows": best,
        "overlap_count": 1 if best > 0 else 0,
        "overlaps": [{"timeframe": timeframe, "overlap_row_floor": best}],
    }


def _rows(prefix: str, count: int) -> list[dict[str, object]]:
    rows = []
    for index in range(count):
        minute = index * 5
        rows.append(
            {
                "time": f"2026-01-01T{minute // 60:02d}:{minute % 60:02d}:00",
                "open": 100 + index,
                "high": 101 + index,
                "low": 99 + index,
                "close": 100.5 + index,
                "spread": 1,
                "tick_volume": 10,
                "symbol": prefix,
            }
        )
    return rows


def test_dxy_n_is_not_selected_when_another_symbol_scores_higher(tmp_path: Path) -> None:
    source = tmp_path / "reports" / "source.json"
    _write_source_audit(
        source,
        proxy_timeframes={
            "DXYN": {"M5": _tf(1000, "2026-01-01T00:00:00", "2026-01-03T00:00:00")},
            "DXYZ": {
                "M5": _tf(5000, "2026-01-01T00:00:00", "2026-02-01T00:00:00"),
                "M15": _tf(5000, "2026-01-01T00:00:00", "2026-02-01T00:00:00"),
            },
            "GDXY": {},
            "USDX": {},
        },
        overlaps={
            "DXYN": _overlap(1000),
            "DXYZ": _overlap(60000),
            "GDXY": _overlap(0),
            "USDX": _overlap(0),
        },
    )

    report = build_xauusd_dxy_proxy_quality_ranker_v0_66(
        root=tmp_path,
        source_audit_path=source,
        proxy_series_by_symbol={
            "DXYN": {"M5": _rows("DXYN", 4)},
            "DXYZ": {"M5": _rows("DXYZ", 4), "M15": _rows("DXYZ", 4)},
        },
    )

    assert report["ranker_status"] == COMPLETED
    assert report["selected_proxy_symbol_or_null"] == "DXYZ"
    assert report["ranking_table"][0]["symbol"] == "DXYZ"
    assert report["quality_scores_by_symbol"]["DXYZ"]["total_score"] > report["quality_scores_by_symbol"]["DXYN"]["total_score"]


def test_dxy_n_can_win_only_by_score_or_deterministic_tie_break(tmp_path: Path) -> None:
    source = tmp_path / "reports" / "source.json"
    equal_tf = {
        "DXYN": {"M5": _tf(5000, "2026-01-01T00:00:00", "2026-02-01T00:00:00")},
        "DXYZ": {"M5": _tf(5000, "2026-01-01T00:00:00", "2026-02-01T00:00:00")},
        "GDXY": {},
        "USDX": {},
    }
    _write_source_audit(
        source,
        proxy_timeframes=equal_tf,
        overlaps={"DXYN": _overlap(50000), "DXYZ": _overlap(50000), "GDXY": _overlap(0), "USDX": _overlap(0)},
    )

    report = build_xauusd_dxy_proxy_quality_ranker_v0_66(
        root=tmp_path,
        source_audit_path=source,
        proxy_series_by_symbol={"DXYN": {"M5": _rows("DXYN", 4)}, "DXYZ": {"M5": _rows("DXYZ", 4)}},
    )

    assert report["selected_proxy_symbol_or_null"] == "DXYN"
    assert "tie-break" in report["selection_reason"]
    assert report["quality_scores_by_symbol"]["DXYN"]["total_score"] == report["quality_scores_by_symbol"]["DXYZ"]["total_score"]


def test_invalid_missing_candidate_data_is_rejected_safely(tmp_path: Path) -> None:
    source = tmp_path / "reports" / "source.json"
    _write_source_audit(
        source,
        proxy_timeframes={"DXYN": {"M5": _tf(10, "2026-01-01T00:00:00", "2026-01-01T01:00:00")}},
        overlaps={"DXYN": _overlap(10)},
    )
    bad_rows = [
        {"time": "2026-01-01T00:00:00", "open": 100, "high": 101, "low": 99, "close": 100},
        {"time": "2026-01-01T00:00:00", "open": 100, "high": 101, "low": 99, "close": 100},
        {"time": "2026-01-01T00:10:00", "open": 0, "high": 0, "low": 0, "close": 0},
        {"time": "2026-01-01T00:15:00", "open": "", "high": 101, "low": 99, "close": 100},
    ]

    report = build_xauusd_dxy_proxy_quality_ranker_v0_66(
        root=tmp_path,
        source_audit_path=source,
        proxy_series_by_symbol={"DXYN": {"M5": bad_rows}},
    )

    assert report["ranker_status"] == COMPLETED_NO_SAFE_PROXY
    assert report["selected_proxy_symbol_or_null"] is None
    assert report["safe_asof_alignment_feasible_by_symbol"]["DXYN"] is False
    assert "duplicate_proxy_timestamps_detected" in report["rejected_proxy_symbols"]["DXYN"]["reasons"]
    assert "missing_proxy_ohlc_rows_detected" in report["rejected_proxy_symbols"]["DXYN"]["reasons"]
    assert "zero_or_invalid_proxy_ohlc_rows_detected" in report["rejected_proxy_symbols"]["DXYN"]["reasons"]


def test_missing_source_audit_blocks_without_strategy_logic(tmp_path: Path) -> None:
    report = build_xauusd_dxy_proxy_quality_ranker_v0_66(root=tmp_path)

    assert report["ranker_status"] == BLOCKED_MISSING_DATA
    assert report["selected_proxy_symbol_or_null"] is None
    assert report["approved_for_strategy_testing"] is False
    assert report["executable_candidate_created"] is False


def test_safe_asof_alignment_never_uses_future_proxy_bars() -> None:
    aligned = safe_backward_asof_alignment_pairs(
        ["2026-01-01T00:02:00", "2026-01-01T00:06:00", "2026-01-01T00:11:00"],
        ["2026-01-01T00:00:00", "2026-01-01T00:05:00", "2026-01-01T00:10:00"],
    )

    assert aligned == [
        {"xauusd_timestamp": "2026-01-01T00:02:00", "proxy_timestamp": "2026-01-01T00:00:00"},
        {"xauusd_timestamp": "2026-01-01T00:06:00", "proxy_timestamp": "2026-01-01T00:05:00"},
        {"xauusd_timestamp": "2026-01-01T00:11:00", "proxy_timestamp": "2026-01-01T00:10:00"},
    ]
    assert_no_future_proxy_bars(aligned)
    with pytest.raises(ValueError, match="future proxy bar"):
        assert_no_future_proxy_bars(
            [{"xauusd_timestamp": "2026-01-01T00:04:00", "proxy_timestamp": "2026-01-01T00:05:00"}]
        )


def test_report_contains_required_ranking_alignment_and_safety_fields() -> None:
    report = build_xauusd_dxy_proxy_quality_ranker_v0_66(root=ROOT)

    assert report["ranker_version"] == RANKER_VERSION
    assert report["source_audit_version"] == "v0_65"
    assert report["candidate_symbols_ranked"] == DEFAULT_CANDIDATE_SYMBOLS
    assert isinstance(report["quality_scores_by_symbol"], dict)
    assert isinstance(report["ranking_table"], list)
    assert set(report["safe_asof_alignment_feasible_by_symbol"]) == set(DEFAULT_CANDIDATE_SYMBOLS)
    assert report["lookahead_risk_detected"] is False
    assert report["aligned_dataset_created"] is False
    assert report["data_csv_touched"] is False
    assert report["future_label_candidates_preserved"] == [
        "dollar_strength",
        "dollar_weakness",
        "dollar_shock",
        "gold_dxy_decoupling",
        "dxy_trend_aligned",
        "dxy_trend_conflict",
    ]
    for key in (
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
    assert report["train_validation_only"] is True
    assert report["approved_for_trade_filtering"] is False


def test_no_aligned_csv_or_data_csv_is_created() -> None:
    before = {path.as_posix() for path in (ROOT / "data").glob("*.csv")}
    report = build_xauusd_dxy_proxy_quality_ranker_v0_66(root=ROOT)
    after = {path.as_posix() for path in (ROOT / "data").glob("*.csv")}

    assert before == after
    assert report["aligned_dataset_created"] is False
    assert report["data_csv_touched"] is False


def test_no_strategy_rules_or_trade_signals_are_created() -> None:
    report = build_xauusd_dxy_proxy_quality_ranker_v0_66(root=ROOT)

    assert report["safety"]["strategy_rules_created"] is False
    assert report["safety"]["trade_signals_output"] is False
    assert report["approved_for_strategy_testing"] is False
    assert report["approved_for_trade_filtering"] is False


def test_cli_writes_required_report(tmp_path: Path) -> None:
    output = tmp_path / "reports" / "ranker.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_dxy_proxy_quality_ranker_v0_66.py"),
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
    assert stdout_report["ranker_version"] == RANKER_VERSION
    assert output_report["ranker_status"] in {COMPLETED, COMPLETED_NO_SAFE_PROXY, BLOCKED_MISSING_DATA}
    assert output_report["aligned_dataset_created"] is False
