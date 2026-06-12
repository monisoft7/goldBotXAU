"""Deterministic event-driven accounting engine for the v0_2 lab."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .metrics import REQUIRED_METRICS, BacktestMetrics, calculate_metrics


@dataclass(frozen=True)
class BacktestLabReport:
    lab_version: str
    status: str
    candle_count: int
    file_count: int
    required_metrics_present: bool
    metrics: dict[str, float | int | str | list[float]]
    safety: dict[str, bool]

    def to_dict(self) -> dict[str, object]:
        return {
            "lab_version": self.lab_version,
            "status": self.status,
            "candle_count": self.candle_count,
            "file_count": self.file_count,
            "required_metrics_present": self.required_metrics_present,
            "metrics": self.metrics,
            "safety": self.safety,
        }


def run_backtest_from_events(
    candles: Iterable[Mapping[str, object]],
    signal_events: Iterable[Mapping[str, float]],
    fixed_risk_unit_r: float = 1.0,
    file_count: int = 0,
    out_of_sample_result: str = "not_evaluated",
) -> BacktestLabReport:
    """Calculate fixture-driven outcomes from explicit synthetic events only."""
    candle_rows = list(candles)
    outcomes = [_event_outcome(event, fixed_risk_unit_r) for event in signal_events]
    metrics = calculate_metrics(outcomes, out_of_sample_result=out_of_sample_result).to_dict()
    return build_lab_report(
        status="backtest_fixture_complete",
        candle_count=len(candle_rows),
        file_count=file_count,
        metrics=metrics,
    )


def build_lab_report(
    status: str,
    candle_count: int,
    file_count: int,
    metrics: dict[str, float | int | str | list[float]] | None = None,
) -> BacktestLabReport:
    metric_payload = metrics or calculate_metrics([]).to_dict()
    return BacktestLabReport(
        lab_version="v0_2",
        status=status,
        candle_count=candle_count,
        file_count=file_count,
        required_metrics_present=REQUIRED_METRICS.issubset(metric_payload.keys()),
        metrics=metric_payload,
        safety={
            "demo_enabled": False,
            "live_enabled": False,
            "order_send_allowed": False,
        },
    )


def _event_outcome(event: Mapping[str, float], fixed_risk_unit_r: float) -> float:
    if "outcome_r" not in event:
        raise ValueError("Synthetic event must include outcome_r.")
    return float(event["outcome_r"]) * fixed_risk_unit_r
