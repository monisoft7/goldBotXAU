# Market Context Anti-Lookahead Policy

All market context features must be aligned so each XAUUSD candle can see only information known at or before the candle decision timestamp.

Economic-calendar rules:

- Future event schedules may use timestamps, currency, event name, and planned impact before release.
- `actual`, `forecast` surprise, and derived surprise fields cannot be used before the release timestamp.
- Revised values must be marked with `revision_flag`.
- A revised value cannot overwrite what was known at the original decision timestamp.

Cross-asset alignment rules:

- Normalize feature timestamps to UTC before joining to XAUUSD candles.
- Use an as-of join at or before the XAUUSD candle open or explicitly documented decision timestamp.
- Store `source_symbol`, `timeframe`, `timestamp_basis`, and `source` for DXY/USD proxy and US yields/rates proxy series.
- Missing aligned context data must produce `block_due_to_missing_context_data` or observe-only status, not silent forward fill.

Geopolitical and headline-label rules:

- Labels require timestamped source evidence before research use.
- No live scraping is allowed in v0_61.
- Subjective manual labels are not allowed for strategy testing until a future policy defines source citation, timestamp basis, reviewer process, and reproducibility checks.
