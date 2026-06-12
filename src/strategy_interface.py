"""Strategy interface definitions for future research candidates."""

from __future__ import annotations

from typing import Protocol


class Strategy(Protocol):
    name: str

    def generate_signals(self, data: object) -> object:
        """Return strategy-specific research outputs for backtesting."""
        ...
