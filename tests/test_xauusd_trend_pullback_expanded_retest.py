from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from src.research.xauusd_trend_pullback_expanded_retest import (
    BLOCKED_MISSING_EXPANSION_DATA,
    CANDIDATE_ID,
    EXPANDED_EVIDENCE_FAILED,
    EXPANDED_EVIDENCE_PASSED,
    RETEST_VERSION,
    build_xauusd_trend_pullback_expanded_retest_v0_51,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeMt5:
    TIMEFRAME_M5 = "M5"
    TIMEFRAME_M10 = "M10"

    def __init__(
        self,
        *,
        initialize_ok: bool = True,
        symbol_info_present: bool = True,
        rates_by_timeframe: dict[str, list[dict[str, float | int]]] | None = None,
    ) -> None:
        self.initialize_ok = initialize_ok
        self.symbol_info_present = symbol_info_present
        self.rates_by_timeframe = rates_by_timeframe or {}
        self.initialize_called = False
        self.shutdown_called = False

    def initialize(self) -> bool:
        self.initialize_called = True
        return self.initialize_ok

    def shutdown(self) -> None:
        self.shutdown_called = True

    def last_error(self) -> tuple[int, str]:
        return (1, "fake unavailable")

    def symbol_info(self, symbol: str) -> object | None:
        return object() if self.symbol_info_present and symbol == "XAUUSD" else None

    def symbol_select(self, symbol: str, selected: bool) -> bool:
        return symbol == "XAUUSD" and selected

    def copy_rates_range(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> list[dict[str, float | int]]:
        del symbol
        return [
            rate
            for rate in self.rates_by_timeframe.get(timeframe, [])
            if start <= datetime.fromtimestamp(int(rate["time"]), UTC).replace(tzinfo=None) <= end
        ]


def _source_artifacts(tmp_path: Path, *, data_expansion_feasible: bool = True) -> tuple[Path, Path, Path]:
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    board_path = reports / "board.json"
    stability_path = reports / "stability.json"
    feasibility_path = reports / "feasibility.json"
    board_path.write_text(
        json.dumps(
            {
                "board_version": "v0_48",
                "best_candidate_id": CANDIDATE_ID,
                "train_validation_only": True,
                "oos_used": False,
                "repeated_oos_review": False,
                "retune_performed": False,
                "threshold_search_performed": False,
                "parameter_grid_performed": False,
                "candidate_results": [
                    {
                        "candidate_id": CANDIDATE_ID,
                        "fixed_before_evaluation": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    stability_path.write_text(
        json.dumps(
            {
                "audit_version": "v0_49",
                "candidate_id": CANDIDATE_ID,
                "stability_decision": "promising_but_insufficient_validation_sample",
                "candidate_locking_allowed_pre_oos": False,
            }
        ),
        encoding="utf-8",
    )
    feasibility_path.write_text(
        json.dumps(
            {
                "audit_version": "v0_50",
                "candidate_to_retest_later": CANDIDATE_ID,
                "data_expansion_feasible": data_expansion_feasible,
            }
        ),
        encoding="utf-8",
    )
    return board_path, stability_path, feasibility_path


def _trend_day_rates(day: date, *, base: float, outcome_r: float) -> list[dict[str, float | int]]:
    reference_range = 1.3
    evaluation_open = base + 2.2
    evaluation_close = evaluation_open + outcome_r * reference_range
    specs = [
        (0, base, base + 2.2, base - 0.1, base + 2.0),
        (6, base + 2.0, base + 2.1, base + 0.8, base + 1.0),
        (12, base + 1.0, base + 2.4, base + 0.9, base + 2.2),
        (
            18,
            evaluation_open,
            max(evaluation_open, evaluation_close) + 0.1,
            min(evaluation_open, evaluation_close) - 0.1,
            evaluation_close,
        ),
    ]
    return [
        {
            "time": int(datetime.combine(day, datetime.min.time(), tzinfo=UTC).replace(hour=hour).timestamp()),
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": 1,
        }
        for hour, open_price, high, low, close in specs
    ]


def _rates(
    *,
    days_by_year: dict[int, int],
    outcome_r: float = 0.4,
) -> dict[str, list[dict[str, float | int]]]:
    m5_rates: list[dict[str, float | int]] = []
    m10_rates: list[dict[str, float | int]] = []
    sequence = 0
    for year, day_count in days_by_year.items():
        for index in range(day_count):
            day = date(year, 1, 2) + timedelta(days=index)
            m5_rates.extend(_trend_day_rates(day, base=1900.0 + sequence, outcome_r=outcome_r))
            m10_rates.extend(_trend_day_rates(day, base=2100.0 + sequence, outcome_r=outcome_r))
            sequence += 1
    return {"M5": m5_rates, "M10": m10_rates}


def _build_report(
    tmp_path: Path,
    *,
    rates_by_timeframe: dict[str, list[dict[str, float | int]]],
    data_expansion_feasible: bool = True,
) -> dict[str, object]:
    board_path, stability_path, feasibility_path = _source_artifacts(
        tmp_path,
        data_expansion_feasible=data_expansion_feasible,
    )
    return build_xauusd_trend_pullback_expanded_retest_v0_51(
        symbol="XAUUSD",
        from_date="2019-01-02",
        to_date="2022-12-30",
        mt5_module=FakeMt5(rates_by_timeframe=rates_by_timeframe),
        source_board_path=board_path,
        source_stability_audit_path=stability_path,
        source_data_feasibility_path=feasibility_path,
    )


def test_candidate_rules_preserved_and_expanded_range_is_train_validation_equivalent_only(tmp_path: Path) -> None:
    report = _build_report(tmp_path, rates_by_timeframe=_rates(days_by_year={2019: 12, 2020: 12, 2021: 12}))

    assert report["retest_version"] == RETEST_VERSION
    assert report["candidate_id"] == CANDIDATE_ID
    assert report["source_candidate_board_version"] == "v0_48"
    assert report["source_stability_audit_version"] == "v0_49"
    assert report["source_data_feasibility_version"] == "v0_50"
    assert report["candidate_rules_preserved"] is True
    assert report["train_validation_equivalent_only"] is True
    assert report["oos_used"] is False
    assert report["repeated_oos_review"] is False
    assert report["retune_performed"] is False
    assert report["threshold_search_performed"] is False
    assert report["parameter_grid_performed"] is False


def test_passing_fixture_allows_pre_oos_locking_only(tmp_path: Path) -> None:
    report = _build_report(tmp_path, rates_by_timeframe=_rates(days_by_year={2019: 12, 2020: 12, 2021: 12}))

    assert report["retest_status"] == EXPANDED_EVIDENCE_PASSED
    assert report["expanded_trade_count"] == 72
    assert report["expanded_metrics"]["profit_factor"] == "inf"
    assert report["expanded_metrics"]["expectancy_r"] > 0
    assert report["expanded_evidence_passed_gate"] is True
    assert report["candidate_locking_allowed_pre_oos"] is True
    assert report["demo_execution_allowed"] is False
    assert report["next_recommended_step"] == "create locked candidate artifact and one-time OOS protocol"


def test_failing_fixture_blocks_candidate_locking(tmp_path: Path) -> None:
    report = _build_report(tmp_path, rates_by_timeframe=_rates(days_by_year={2019: 12, 2020: 12, 2021: 12}, outcome_r=-0.2))

    assert report["retest_status"] == EXPANDED_EVIDENCE_FAILED
    assert report["expanded_evidence_passed_gate"] is False
    assert report["candidate_locking_allowed_pre_oos"] is False
    assert "expanded_expectancy_not_positive" in report["blockers"]
    assert "expanded_profit_factor_below_fixed_gate" in report["blockers"]


def test_concentration_risk_detected_if_trades_are_too_concentrated(tmp_path: Path) -> None:
    report = _build_report(tmp_path, rates_by_timeframe=_rates(days_by_year={2019: 26, 2020: 1, 2021: 1}))

    risk = report["sample_concentration_risk"]
    assert risk["risk_level"] == "high"
    assert "expanded_trades_concentrated_in_single_year" in risk["reasons"]
    assert "single_year_contains_more_than_50_percent_of_expanded_trades" in report["blockers"]
    assert report["expanded_evidence_passed_gate"] is False


def test_missing_expansion_data_blocks_without_oos_or_execution(tmp_path: Path) -> None:
    report = _build_report(tmp_path, rates_by_timeframe={"M5": [], "M10": []})

    assert report["retest_status"] == BLOCKED_MISSING_EXPANSION_DATA
    assert report["expanded_evidence_passed_gate"] is False
    assert report["candidate_locking_allowed_pre_oos"] is False
    assert report["oos_used"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False


def test_no_order_send_order_check_live_oos_retune_or_data_csv_added(tmp_path: Path) -> None:
    report = _build_report(tmp_path, rates_by_timeframe=_rates(days_by_year={2019: 12, 2020: 12, 2021: 12}))

    assert report["demo_execution_allowed"] is False
    assert report["order_send_called"] is False
    assert report["order_check_called"] is False
    assert report["live_allowed"] is False
    assert report["execution_queue_created"] is False
    assert report["scheduler_created"] is False
    assert report["trade_recommendation_output_present"] is False
    assert report["data_csv_added_to_git"] is False


def test_source_feasibility_must_allow_expansion(tmp_path: Path) -> None:
    report = _build_report(
        tmp_path,
        rates_by_timeframe=_rates(days_by_year={2019: 12, 2020: 12, 2021: 12}),
        data_expansion_feasible=False,
    )

    assert report["retest_status"] == BLOCKED_MISSING_EXPANSION_DATA
    assert "source_data_expansion_not_feasible" in report["blockers"]


def test_cli_writes_required_report(tmp_path: Path) -> None:
    output_path = tmp_path / "reports" / "retest.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_xauusd_trend_pullback_expanded_retest_v0_51.py"),
            "--symbol",
            "XAUUSD",
            "--from-date",
            "2019-01-02",
            "--to-date",
            "2022-12-30",
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["retest_version"] == RETEST_VERSION
    assert output_report["candidate_id"] == CANDIDATE_ID
    assert output_report["oos_used"] is False
