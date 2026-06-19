# v0_50 Historical Data Expansion Feasibility Result

- Audit module: `src/research/xauusd_historical_data_expansion_feasibility_audit.py`
- Audit script: `scripts/audit_xauusd_historical_data_expansion_v0_50.py`
- Audit report: `reports/xauusd_historical_data_expansion_feasibility_v0_50.json`
- Audit status: `expansion_data_partially_available`
- Symbol: `XAUUSD`
- Requested range: `2019-01-01` to `2022-12-31`
- MT5 read-only: `true`
- MT5 initialized: `true`
- MT5 shutdown called: `true`
- Available oldest candle time: `2019-01-02T06:00:00`
- Available newest candle time: `2022-12-30T23:55:00`
- Requested range available: `false`
- Candle count by timeframe: `M5=281176`, `M10=141476`
- Missing range gap count: `2086`
- Missing range gaps truncated in report: `true`
- Data expansion feasible: `true`
- Candidate to retest later: `trend_pullback_continuation_directional`
- Candidate rules preserved: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Blockers: none
- Warnings: `feasibility_audit_only_no_strategy_evaluation_no_oos`, `missing_range_gaps_truncated_to_100_examples`, `requested_range_partially_available_with_enough_usable_m5_candles`
- Targeted tests: `37 passed`
- Next recommended step: `v0_51 fixed-rule expanded train/validation retest on available older range only, no OOS`

v0_50 performed a read-only MT5 historical data availability audit only. It did not run strategy evaluation, did not run or repeat OOS, did not export or commit CSV data, and did not change the `trend_pullback_continuation_directional` candidate rules.

The requested full range is not completely available because returned candles begin at `2019-01-02T06:00:00` and end at `2022-12-30T23:55:00`, with reportable gaps. However, the available older low-timeframe sample is large enough for a fixed-rule expanded train/validation retest: `281176` M5 candles and `141476` M10 candles.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.
