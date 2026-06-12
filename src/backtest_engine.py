"""Minimal placeholder backtest runner for research-only strategy work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class BacktestStrategy(Protocol):
    name: str

    def generate_signals(self, data: object) -> object:
        ...


@dataclass(frozen=True)
class BacktestResult:
    strategy_name: str
    rows_processed: int | None
    status: str


def run_backtest(data: object, strategy: BacktestStrategy) -> BacktestResult:
    """Accept data and a strategy object, but leave execution details unbuilt."""
    if not getattr(strategy, "name", None):
        raise ValueError("Strategy must define a name.")
    if data is None:
        raise ValueError("Backtest data cannot be None.")

    raise NotImplementedError("Backtest execution details are not implemented yet.")
