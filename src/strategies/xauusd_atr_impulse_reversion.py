"""Fixed XAUUSD ATR impulse reversion research candidate."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.research.strategy_candidate import ResearchCandidate


@dataclass(frozen=True)
class XauusdAtrImpulseReversionCandidate(ResearchCandidate):
    candidate_id: str = "xauusd_atr_impulse_reversion_v0_7"
    candidate_name: str = "XAUUSD ATR Impulse Reversion"
    candidate_version: str = "v0_7"
    family_name: str = "atr_impulse_reversion"
    description: str = "Fixed offline research test for ATR-normalized impulse partial reversion."
    allowed_splits: tuple[str, ...] = field(default=("train", "validation"))
    forbidden_families_check: bool = True
    is_null_candidate: bool = False

    timeframe: str = "M15"
    atr_period_bars: int = 96
    impulse_range_atr_min: float = 1.8
    body_to_range_min: float = 0.60
    close_extreme_fraction: float = 0.20
    max_hold_bars: int = 12
    stop_atr_buffer: float = 0.30
    target_r: float = 1.00
    cost_r_per_trade: float = 0.05
    cooldown_bars_after_trade: int = 16

    def parameters(self) -> dict[str, float | int | str]:
        return {
            "timeframe": self.timeframe,
            "atr_period_bars": self.atr_period_bars,
            "impulse_range_atr_min": self.impulse_range_atr_min,
            "body_to_range_min": self.body_to_range_min,
            "close_extreme_fraction": self.close_extreme_fraction,
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
        if len(rows) <= self.atr_period_bars + 1:
            return []

        true_ranges = _true_ranges(rows)
        outcomes: list[float] = []
        index = self.atr_period_bars
        while index < len(rows) - 1:
            atr = sum(true_ranges[index - self.atr_period_bars + 1 : index + 1]) / self.atr_period_bars
            if atr <= 0:
                index += 1
                continue

            candle = rows[index]
            candle_range = candle["high"] - candle["low"]
            if not self._is_impulse(candle, candle_range, atr):
                index += 1
                continue

            scenario = self._scenario(candle, candle_range)
            if scenario is None:
                index += 1
                continue

            outcome, exit_index = self._simulate_outcome(rows, index, scenario, atr)
            outcomes.append(outcome)
            index = max(index + 1, exit_index + self.cooldown_bars_after_trade + 1)

        return outcomes

    def _is_impulse(self, candle: dict[str, float], candle_range: float, atr: float) -> bool:
        if candle_range <= 0:
            return False
        body_fraction = abs(candle["close"] - candle["open"]) / candle_range
        return candle_range >= self.impulse_range_atr_min * atr and body_fraction >= self.body_to_range_min

    def _scenario(self, candle: dict[str, float], candle_range: float) -> str | None:
        upper_distance = candle["high"] - candle["close"]
        lower_distance = candle["close"] - candle["low"]
        extreme_limit = self.close_extreme_fraction * candle_range
        if upper_distance <= extreme_limit:
            return "upper_extreme_reversion"
        if lower_distance <= extreme_limit:
            return "lower_extreme_reversion"
        return None

    def _simulate_outcome(
        self,
        rows: list[dict[str, float]],
        impulse_index: int,
        scenario: str,
        atr: float,
    ) -> tuple[float, int]:
        impulse = rows[impulse_index]
        entry_index = impulse_index + 1
        entry = rows[entry_index]["open"]
        final_index = min(entry_index + self.max_hold_bars - 1, len(rows) - 1)

        if scenario == "upper_extreme_reversion":
            stop = impulse["high"] + self.stop_atr_buffer * atr
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

        stop = impulse["low"] - self.stop_atr_buffer * atr
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
