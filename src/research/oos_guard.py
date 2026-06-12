"""Locked out-of-sample split guard for XAUUSD research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

LOCKED_MESSAGE = "OOS data is locked until candidate promotion review."


@dataclass
class OOSGuard:
    manifest: dict[str, Any]
    oos_locked: bool = True
    oos_access_attempted: bool = False

    def filter_candles(self, candles: list[dict[str, float | str]], split_name: str) -> list[dict[str, float | str]]:
        if split_name == "out_of_sample":
            self.oos_access_attempted = True
            raise PermissionError(LOCKED_MESSAGE)
        if split_name not in {"train", "validation"}:
            raise ValueError(f"Unknown or unavailable split: {split_name}")

        policy = self.manifest["split_policy"]
        return [candle for candle in candles if self._in_split(str(candle["timestamp"]), split_name, policy)]

    def report(self) -> dict[str, bool]:
        return {
            "oos_locked": True,
            "oos_access_attempted": self.oos_access_attempted,
            "oos_access_allowed": False,
        }

    @staticmethod
    def _in_split(timestamp: str, split_name: str, policy: dict[str, str]) -> bool:
        candle_time = datetime.fromisoformat(timestamp)
        if split_name == "train":
            return candle_time <= datetime.fromisoformat(policy["train_end"])
        return (
            datetime.fromisoformat(policy["validation_start"])
            <= candle_time
            <= datetime.fromisoformat(policy["validation_end"])
        )
