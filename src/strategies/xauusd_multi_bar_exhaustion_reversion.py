"""Fixed XAUUSD multi-bar exhaustion reversion research candidate."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.research.strategy_candidate import ResearchCandidate


@dataclass(frozen=True)
class XauusdMultiBarExhaustionReversionCandidate(ResearchCandidate):
    candidate_id: str = "xauusd_multi_bar_exhaustion_reversion_v0_8"
    candidate_name: str = "XAUUSD Multi-Bar Exhaustion Reversion"
    candidate_version: str = "v0_8"
    family_name: str = "multi_bar_exhaustion_reversion"
    description: str = "Fixed offline research test for multi-bar exhaustion partial reversion."
    allowed_splits: tuple[str, ...] = field(default=("train", "validation"))
    forbidden_families_check: bool = True
    is_null_candidate: bool = False

    timeframe: str = "M15"
    atr_period_bars: int = 96
    sequence_bars: int = 4
    cumulative_move_atr_min: float = 1.35
    minimum_aligned_closes: int = 4
    final_close_extreme_fraction: float = 0.25
    max_hold_bars: int = 10
    stop_atr_buffer: float = 0.25
    target_r: float = 0.90
    cost_r_per_trade: float = 0.05
    cooldown_bars_after_trade: int = 14

    def parameters(self) -> dict[str, float | int | str]:
        return {
            "timeframe": self.timeframe,
            "atr_period_bars": self.atr_period_bars,
            "sequence_bars": self.sequence_bars,
            "cumulative_move_atr_min": self.cumulative_move_atr_min,
            "minimum_aligned_closes": self.minimum_aligned_closes,
            "final_close_extreme_fraction": self.final_close_extreme_fraction,
            "max_hold_bars": self.max_hold_bars,
            "stop_atr_buffer": self.stop_atr_buffer,
            "target_r": self.target_r,
            "cost_r_per_trade": self.cost_r_per_trade,
            "cooldown_bars_after_trade": self.cooldown_bars_after_trade,
        }

    def run_on_split(self, candles: list[dict[str, float | str]], split_name: str) -> list[float]:
        self.validate()
        if split_name not in self.allowed_splits:
            raise ValueError(f"Split not allowed for candidate: {split_name}")
        rows = [_normal_row(candle) for candle in candles]
        minimum_rows = self.atr_period_bars + self.sequence_bars + 1
        if len(rows) < minimum_rows:
            return []

        true_ranges = _true_ranges(rows)
        outcomes: list[float] = []
        index = self.atr_period_bars + self.sequence_bars - 1
        while index < len(rows) - 1:
            atr = sum(true_ranges[index - self.atr_period_bars + 1 : index + 1]) / self.atr_period_bars
            if atr <= 0:
                index += 1
                continue

            scenario = self._scenario(rows, index, atr)
            if scenario is None:
                index += 1
                continue

            outcome, exit_index = self._simulate_outcome(rows, index, scenario, atr)
            outcomes.append(outcome)
            index = max(index + 1, exit_index + self.cooldown_bars_after_trade + 1)

        return outcomes

    def _scenario(self, rows: list[dict[str, float]], index: int, atr: float) -> str | None:
        start_index = index - self.sequence_bars + 1
        window = rows[start_index : index + 1]
        first_open = window[0]["open"]
        final_close = window[-1]["close"]
        cumulative_move = final_close - first_open
        if abs(cumulative_move) < self.cumulative_move_atr_min * atr:
            return None

        aligned_up = sum(1 for row in window if row["close"] > row["open"])
        aligned_down = sum(1 for row in window if row["close"] < row["open"])
        final = window[-1]
        final_range = final["high"] - final["low"]
        if final_range <= 0:
            return None

        extreme_limit = self.final_close_extreme_fraction * final_range
        near_upper = final["high"] - final["close"] <= extreme_limit
        near_lower = final["close"] - final["low"] <= extreme_limit
        if cumulative_move > 0 and aligned_up >= self.minimum_aligned_closes and near_upper:
            return "upper_exhaustion_reversion"
        if cumulative_move < 0 and aligned_down >= self.minimum_aligned_closes and near_lower:
            return "lower_exhaustion_reversion"
        return None

    def _simulate_outcome(
        self,
        rows: list[dict[str, float]],
        signal_index: int,
        scenario: str,
        atr: float,
    ) -> tuple[float, int]:
        signal = rows[signal_index]
        entry_index = signal_index + 1
        entry = rows[entry_index]["open"]
        final_index = min(entry_index + self.max_hold_bars - 1, len(rows) - 1)

        if scenario == "upper_exhaustion_reversion":
            stop = signal["high"] + self.stop_atr_buffer * atr
            risk = stop - entry
            if risk <= 0:
                return -self.cost_r_per_trade, entry_index
            target = entry - self.target_r * risk
            for index in range(entry_index, final_index + 1):
                row = rows[index]
                if row["high"] >= stop:
                    return -1.0 - self.cost_r_per_trade, index
                if row["low"] <= target:
                    return self.target_r - self.cost_r_per_trade, index
            timeout_r = (entry - rows[final_index]["close"]) / risk
            return timeout_r - self.cost_r_per_trade, final_index

        stop = signal["low"] - self.stop_atr_buffer * atr
        risk = entry - stop
        if risk <= 0:
            return -self.cost_r_per_trade, entry_index
        target = entry + self.target_r * risk
        for index in range(entry_index, final_index + 1):
            row = rows[index]
            if row["low"] <= stop:
                return -1.0 - self.cost_r_per_trade, index
            if row["high"] >= target:
                return self.target_r - self.cost_r_per_trade, index
        timeout_r = (rows[final_index]["close"] - entry) / risk
        return timeout_r - self.cost_r_per_trade, final_index


def _normal_row(candle: dict[str, float | str]) -> dict[str, float]:
    return {
        "open": float(candle["open"]),
        "high": float(candle["high"]),
        "low": float(candle["low"]),
        "close": float(candle["close"]),
    }


def _true_ranges(rows: list[dict[str, float]]) -> list[float]:
    ranges: list[float] = []
    previous_close: float | None = None
    for row in rows:
        if previous_close is None:
            ranges.append(row["high"] - row["low"])
        else:
            ranges.append(
                max(
                    row["high"] - row["low"],
                    abs(row["high"] - previous_close),
                    abs(row["low"] - previous_close),
                )
            )
        previous_close = row["close"]
    return ranges
