"""Fixed XAUUSD low ATR x dataset hour 16 response research candidate."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.research.strategy_candidate import ResearchCandidate


@dataclass(frozen=True)
class XauusdLowAtrXHour16ResponseCandidate(ResearchCandidate):
    candidate_id: str = "xauusd_low_atr_x_hour_16_v0_17"
    candidate_name: str = "XAUUSD Low ATR x Dataset Hour 16 Response"
    candidate_version: str = "v0_17"
    family_name: str = "low_atr_x_dataset_hour_16_response"
    description: str = "Fixed offline research test for low-ATR candles at dataset hour 16."
    allowed_splits: tuple[str, ...] = field(default=("train", "validation"))
    forbidden_families_check: bool = True
    is_null_candidate: bool = False

    timeframe: str = "M15"
    dataset_hour: int = 16
    atr_period_bars: int = 96
    fixed_low_atr_range_to_atr_max: float = 1.3230733892270252
    close_near_high_fraction: float = 0.75
    close_near_low_fraction: float = 0.25
    minimum_body_to_range: float = 0.35
    max_hold_bars: int = 8
    stop_atr_buffer: float = 0.25
    target_r: float = 0.90
    cost_r_per_trade: float = 0.05
    cooldown_bars_after_trade: int = 8

    def parameters(self) -> dict[str, float | int | str]:
        return {
            "timeframe": self.timeframe,
            "dataset_hour": self.dataset_hour,
            "dataset_hour_semantics": "dataset_hour_16_not_proven_utc",
            "atr_period_bars": self.atr_period_bars,
            "fixed_low_atr_range_to_atr_max": self.fixed_low_atr_range_to_atr_max,
            "close_near_high_fraction": self.close_near_high_fraction,
            "close_near_low_fraction": self.close_near_low_fraction,
            "minimum_body_to_range": self.minimum_body_to_range,
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
        if len(rows) < self.atr_period_bars + 1:
            return []

        true_ranges = _true_ranges(rows)
        outcomes: list[float] = []
        index = self.atr_period_bars
        while index < len(rows) - 1:
            atr = sum(true_ranges[index - self.atr_period_bars + 1 : index + 1]) / self.atr_period_bars
            if atr <= 0:
                index += 1
                continue

            scenario = self._scenario(rows[index], atr)
            if scenario is None:
                index += 1
                continue

            outcome, exit_index = self._simulate_outcome(rows, index, scenario, atr)
            outcomes.append(outcome)
            index = max(index + 1, exit_index + self.cooldown_bars_after_trade + 1)

        return outcomes

    def _scenario(self, signal: dict[str, float | int], atr: float) -> str | None:
        if int(signal["hour"]) != self.dataset_hour:
            return None

        signal_range = float(signal["high"]) - float(signal["low"])
        if signal_range <= 0:
            return None

        range_to_atr = signal_range / atr
        if range_to_atr >= self.fixed_low_atr_range_to_atr_max:
            return None

        body_to_range = abs(float(signal["close"]) - float(signal["open"])) / signal_range
        if body_to_range < self.minimum_body_to_range:
            return None

        close_location_fraction = (float(signal["close"]) - float(signal["low"])) / signal_range
        if close_location_fraction >= self.close_near_high_fraction:
            return "positive_response_test"
        if close_location_fraction <= self.close_near_low_fraction:
            return "negative_response_test"
        return None

    def _simulate_outcome(
        self,
        rows: list[dict[str, float | int]],
        signal_index: int,
        scenario: str,
        atr: float,
    ) -> tuple[float, int]:
        signal = rows[signal_index]
        entry_index = signal_index + 1
        entry = float(rows[entry_index]["open"])
        final_index = min(entry_index + self.max_hold_bars - 1, len(rows) - 1)

        if scenario == "positive_response_test":
            stop = float(signal["low"]) - self.stop_atr_buffer * atr
            risk = entry - stop
            if risk <= 0:
                return -self.cost_r_per_trade, entry_index
            target = entry + self.target_r * risk
            for index in range(entry_index, final_index + 1):
                row = rows[index]
                if float(row["low"]) <= stop:
                    return -1.0 - self.cost_r_per_trade, index
                if float(row["high"]) >= target:
                    return self.target_r - self.cost_r_per_trade, index
            timeout_r = (float(rows[final_index]["close"]) - entry) / risk
            return timeout_r - self.cost_r_per_trade, final_index

        stop = float(signal["high"]) + self.stop_atr_buffer * atr
        risk = stop - entry
        if risk <= 0:
            return -self.cost_r_per_trade, entry_index
        target = entry - self.target_r * risk
        for index in range(entry_index, final_index + 1):
            row = rows[index]
            if float(row["high"]) >= stop:
                return -1.0 - self.cost_r_per_trade, index
            if float(row["low"]) <= target:
                return self.target_r - self.cost_r_per_trade, index
        timeout_r = (entry - float(rows[final_index]["close"])) / risk
        return timeout_r - self.cost_r_per_trade, final_index


def _normal_row(candle: dict[str, float | str]) -> dict[str, float | int]:
    timestamp = datetime.fromisoformat(str(candle["timestamp"]))
    return {
        "hour": timestamp.hour,
        "open": float(candle["open"]),
        "high": float(candle["high"]),
        "low": float(candle["low"]),
        "close": float(candle["close"]),
    }


def _true_ranges(rows: list[dict[str, float | int]]) -> list[float]:
    ranges: list[float] = []
    previous_close: float | None = None
    for row in rows:
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        if previous_close is None:
            ranges.append(high - low)
        else:
            ranges.append(
                max(
                    high - low,
                    abs(high - previous_close),
                    abs(low - previous_close),
                )
            )
        previous_close = close
    return ranges
