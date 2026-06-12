"""Backtest metric helpers for future strategy evaluation."""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def trade_count(results: Sequence[float]) -> int:
    return len(results)


def win_rate(results: Sequence[float]) -> float:
    if not results:
        return 0.0
    wins = sum(1 for value in results if value > 0)
    return wins / len(results)


def profit_factor(results: Sequence[float]) -> float:
    gross_profit = sum(value for value in results if value > 0)
    gross_loss = abs(sum(value for value in results if value < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def expectancy(results: Sequence[float]) -> float:
    if not results:
        return 0.0
    return sum(results) / len(results)


def max_drawdown(equity_curve: Iterable[float]) -> float:
    peak: float | None = None
    worst = 0.0
    for equity in equity_curve:
        peak = equity if peak is None else max(peak, equity)
        worst = min(worst, equity - peak)
    return abs(worst)


def max_consecutive_losses(results: Sequence[float]) -> int:
    longest = 0
    current = 0
    for value in results:
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest
