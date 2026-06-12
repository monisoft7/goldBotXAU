"""Fixed XAUUSD session volatility expansion research candidate."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.research.strategy_candidate import ResearchCandidate


@dataclass(frozen=True)
class XauusdSessionVolatilityExpansionCandidate(ResearchCandidate):
    candidate_id: str = "xauusd_session_volatility_expansion_v0_11"
    candidate_name: str = "XAUUSD Session Volatility Expansion"
    candidate_version: str = "v0_11"
    family_name: str = "session_volatility_expansion"
    description: str = "Fixed offline research test for 15-17 UTC session volatility expansion."
    allowed_splits: tuple[str, ...] = field(default=("train", "validation"))
    forbidden_families_check: bool = True
    is_null_candidate: bool = False

    timeframe: str = "M15"
    atr_period_bars: int = 96
    reference_lookback_bars: int = 16
    session_start_hour_utc: int = 15
    session_end_hour_utc: int = 17
    signal_range_atr_min: float = 0.75
    stop_atr_buffer: float = 0.55
    target_r: float = 1.00
    max_hold_bars: int = 8
    cost_r_per_trade: float = 0.05
    cooldown_bars_after_trade: int = 12

    def parameters(self) -> dict[str, float | int | str]:
        return {
            "timeframe": self.timeframe,
            "atr_period_bars": self.atr_period_bars,
            "reference_lookback_bars": self.reference_lookback_bars,
            "session_start_hour_utc": self.session_start_hour_utc,
            "session_end_hour_utc": self.session_end_hour_utc,
            "signal_range_atr_min": self.signal_range_atr_min,
            "stop_atr_buffer": self.stop_atr_buffer,
            "target_r": self.target_r,
            "max_hold_bars": self.max_hold_bars,
            "cost_r_per_trade": self.cost_r_per_trade,
            "cooldown_bars_after_trade": self.cooldown_bars_after_trade,
        }

    def run_on_split(self, candles: list[dict[str, float | str]], split_name: str) -> list[float]:
        self.validate()
        if split_name not in self.allowed_splits:
            raise ValueError(f"Split not allowed for candidate: {split_name}")
        rows = [_normal_row(candle) for candle in candles]
        minimum_rows = max(self.atr_period_bars, self.reference_lookback_bars) + 1
        if len(rows) < minimum_rows:
            return []

        true_ranges = _true_ranges(rows)
        outcomes: list[float] = []
        index = max(self.atr_period_bars, self.reference_lookback_bars)
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
        signal = rows[index]
        hour = int(signal["hour"])
        if hour < self.session_start_hour_utc or hour > self.session_end_hour_utc:
            return None

        signal_range = signal["high"] - signal["low"]
        if signal_range < self.signal_range_atr_min * atr:
            return None

        reference = rows[index - self.reference_lookback_bars : index]
        reference_high = max(row["high"] for row in reference)
        reference_low = min(row["low"] for row in reference)
        if signal["close"] > reference_high:
            return "upper_session_expansion"
        if signal["close"] < reference_low:
            return "lower_session_expansion"
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

        if scenario == "upper_session_expansion":
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
    timestamp = datetime.fromisoformat(str(candle["timestamp"]))
    return {
        "hour": float(timestamp.hour),
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
