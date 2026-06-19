# Research Lab Gap Classification Policy

Version: v0_59

This policy standardizes how research reports classify candle gaps and zero-range rows. It does not delete, alter, backfill, or synthesize market data.

## Classification Enums

- `expected_weekend_or_market_closure_gap`
- `unexpected_intraday_gap`
- `zero_range_candle_warning`
- `duplicate_or_non_monotonic_error`

## Standard

- Duplicate timestamps and non-monotonic timestamps are critical errors.
- Expected weekend or market-closure gaps are warnings only.
- Unexpected intraday gaps are warnings that must be counted and disclosed.
- Zero-range candles are warnings unless their frequency is excessive.
- The v0_59 excessive zero-range frequency threshold is `0.001` of candles in a timeframe.
- Data must not be deleted or altered by this classification step.

## Machine Policy

- `duplicate_or_non_monotonic_timestamps_are_critical = true`
- `expected_weekend_or_market_closure_gaps_are_warnings = true`
- `zero_range_candles_are_warnings_unless_excessive = true`
- `data_deleted_or_altered = false`
