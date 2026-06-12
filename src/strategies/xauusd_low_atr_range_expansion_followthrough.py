"""Fixed XAUUSD low ATR range expansion followthrough research candidate."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.research.strategy_candidate import ResearchCandidate


@dataclass(frozen=True)
class XauusdLowAtrRangeExpansionFollowthroughCandidate(ResearchCandidate):
    candidate_id: str = "xauusd_low_atr_range_expansion_followthrough_v0_14"
    candidate_name: str = "XAUUSD Low ATR Range Expansion Followthrough"
    candidate_version: str = "v0_14"
    family_name: str = "low_atr_range_expansion_followthrough"
    description: str = "Fixed offline research test for controlled expansion after low-ATR compression."
    allowed_splits: tuple[str, ...] = field(default=("train", "validation"))
    forbidden_families_check: bool = True
    is_null_candidate: bool = False

    timeframe: str = "M15"
    atr_period_bars: int = 96
    compression_lookback_bars: int = 8
    compression_avg_range_to_atr_max: float = 0.85
    compression_max_single_range_to_atr_max: float = 1.3230733892270252
    trigger_range_to_atr_min: float = 0.90
    trigger_range_to_atr_max: float = 1.3230733892270252
    trigger_body_to_range_min: float = 0.55
    trigger_close_extreme_fraction: float = 0.25
    max_hold_bars: int = 8
    stop_atr_buffer: float = 0.25
    target_r: float = 0.90
    cost_r_per_trade: float = 0.05
    cooldown_bars_after_trade: int = 12

    def parameters(self) -> dict[str, float | int | str]:
        return {
            "timeframe": self.timeframe,
            "atr_period_bars": self.atr_period_bars,
            "compression_lookback_bars": self.compression_lookback_bars,
            "compression_avg_range_to_atr_max": self.compression_avg_range_to_atr_max,
            "compression_max_single_range_to_atr_max": self.compression_max_single_range_to_atr_max,
            "trigger_range_to_atr_min": self.trigger_range_to_atr_min,
            "trigger_range_to_atr_max": self.trigger_range_to_atr_max,
            "trigger_body_to_range_min": self.trigger_body_to_range_min,
            "trigger_close_extreme_fraction": self.trigger_close_extreme_fraction,
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
        minimum_rows = self.atr_period_bars + self.compression_lookback_bars + 1
        if len(rows) < minimum_rows:
            return []

        true_ranges = _true_ranges(rows)
        outcomes: list[float] = []
        index = self.atr_period_bars + self.compression_lookback_bars
        while index < len(rows) - 1:
            atr = sum(true_ranges[index - self.atr_period_bars + 1 : index + 1]) / self.atr_period_bars
            if atr <= 0:
                index += 1
                continue

            scenario = self._scenario(rows, true_ranges, index, atr)
            if scenario is None:
                index += 1
                continue

            outcome, exit_index = self._simulate_outcome(rows, index, scenario, atr)
            outcomes.append(outcome)
            index = max(index + 1, exit_index + self.cooldown_bars_after_trade + 1)

        return outcomes

    def _scenario(
        self,
        rows: list[dict[str, float]],
        true_ranges: list[float],
        index: int,
        atr: float,
    ) -> str | None:
        compression_ranges = [
            true_ranges[range_index] / atr
            for range_index in range(index - self.compression_lookback_bars, index)
        ]
        if sum(compression_ranges) / len(compression_ranges) > self.compression_avg_range_to_atr_max:
            return None
        if max(compression_ranges) > self.compression_max_single_range_to_atr_max:
            return None

        signal = rows[index]
        signal_range = signal["high"] - signal["low"]
        if signal_range <= 0:
            return None
        range_to_atr = signal_range / atr
        if range_to_atr < self.trigger_range_to_atr_min:
            return None
        if range_to_atr > self.trigger_range_to_atr_max:
            return None

        body_to_range = abs(signal["close"] - signal["open"]) / signal_range
        if body_to_range < self.trigger_body_to_range_min:
            return None

        extreme_limit = self.trigger_close_extreme_fraction * signal_range
        if signal["high"] - signal["close"] <= extreme_limit:
            return "positive_followthrough"
        if signal["close"] - signal["low"] <= extreme_limit:
            return "negative_followthrough"
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

        if scenario == "positive_followthrough":
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
