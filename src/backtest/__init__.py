"""Backtest lab primitives for goldBotXAU."""

from .engine import BacktestLabReport, run_backtest_from_events
from .metrics import calculate_metrics

__all__ = ["BacktestLabReport", "calculate_metrics", "run_backtest_from_events"]
