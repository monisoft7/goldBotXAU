"""Indicator placeholder module for future research-only calculations."""

from __future__ import annotations


def ensure_series_ready(values: object) -> object:
    """Return values unchanged after a minimal presence check."""
    if values is None:
        raise ValueError("Indicator input cannot be None.")
    return values
