"""Pure metric calculations for deterministic backtest fixtures."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isinf
from typing import Iterable

REQUIRED_METRICS = {
    "trade_count",
    "win_rate",
    "profit_factor",
    "expectancy",
    "max_drawdown",
    "max_consecutive_losses",
    "out_of_sample_result",
}


@dataclass(frozen=True)
class BacktestMetrics:
    trade_count: int
    wins: int
    losses: int
    win_rate: float
    gross_profit: float
    gross_loss: float
    profit_factor: float | str
    expectancy: float
    equity_curve: list[float]
    max_drawdown: float
    max_consecutive_losses: int
    out_of_sample_result: str

    def to_dict(self) -> dict[str, float | int | str | list[float]]:
        data = asdict(self)
        if isinstance(self.profit_factor, float) and isinf(self.profit_factor):
            data["profit_factor"] = "inf"
        return data


def calculate_metrics(outcomes: Iterable[float], out_of_sample_result: str = "not_evaluated") -> BacktestMetrics:
    values = [float(value) for value in outcomes]
    curve = equity_curve(values)

    return BacktestMetrics(
        trade_count=trade_count(values),
        wins=wins(values),
        losses=losses(values),
        win_rate=win_rate(values),
        gross_profit=gross_profit(values),
        gross_loss=gross_loss(values),
        profit_factor=profit_factor(values),
        expectancy=expectancy(values),
        equity_curve=curve,
        max_drawdown=max_drawdown(curve),
        max_consecutive_losses=max_consecutive_losses(values),
        out_of_sample_result=out_of_sample_result,
    )


def trade_count(outcomes: list[float]) -> int:
    return len(outcomes)


def wins(outcomes: list[float]) -> int:
    return sum(1 for value in outcomes if value > 0)


def losses(outcomes: list[float]) -> int:
    return sum(1 for value in outcomes if value < 0)


def win_rate(outcomes: list[float]) -> float:
    if not outcomes:
        return 0.0
    return wins(outcomes) / len(outcomes)


def gross_profit(outcomes: list[float]) -> float:
    return sum(value for value in outcomes if value > 0)


def gross_loss(outcomes: list[float]) -> float:
    return abs(sum(value for value in outcomes if value < 0))


def profit_factor(outcomes: list[float]) -> float:
    profit = gross_profit(outcomes)
    loss = gross_loss(outcomes)
    if loss == 0:
        return float("inf") if profit > 0 else 0.0
    return profit / loss


def expectancy(outcomes: list[float]) -> float:
    if not outcomes:
        return 0.0
    return sum(outcomes) / len(outcomes)


def equity_curve(outcomes: list[float], starting_equity: float = 0.0) -> list[float]:
    equity = starting_equity
    curve = [equity]
    for value in outcomes:
        equity += value
        curve.append(equity)
    return curve


def max_drawdown(curve: list[float]) -> float:
    peak: float | None = None
    worst = 0.0
    for equity in curve:
        peak = equity if peak is None else max(peak, equity)
        worst = min(worst, equity - peak)
    return abs(worst)


def max_consecutive_losses(outcomes: list[float]) -> int:
    longest = 0
    current = 0
    for value in outcomes:
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest
