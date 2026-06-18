# v0_45 Live Signal Snapshot Provider Result

- Snapshot module: `src/execution/xauusd_live_signal_snapshot_provider.py`
- Snapshot script: `scripts/build_xauusd_live_signal_snapshot_v0_45.py`
- Snapshot report: `reports/xauusd_live_signal_snapshot_v0_45.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Snapshot version: `v0_45`
- Snapshot status: `snapshot_ready_order_request_built_dry_run_only`
- Symbol: `XAUUSD`
- Timeframes requested: `M5`, `M10`
- Candles loaded: `M5=288`, `M10=144`
- Latest M5 candle: `2026-06-18T19:05:00+00:00`
- Latest M10 candle: `2026-06-18T19:00:00+00:00`
- MT5 read-only: `true`
- MT5 initialized: `true`
- MT5 shutdown called: `true`
- Current signal snapshot present: `true`
- Signal evaluated: `true`
- Signal qualified: `true`
- Signal reason: `locked_candidate_current_snapshot_expansion_confirmed_across_m5_m10`
- Order request present: `true`
- Order request complete: `true`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Candidate rules preserved: `true`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Repeated OOS review: `false`
- Targeted tests: `45 passed`

v0_45 adds a read-only MT5 live signal snapshot provider for the locked v0_26 candidate. It fetches M5/M10 candles, creates a structured `current_signal_snapshot`, and passes that snapshot into the v0_43 dry-run builder. It does not send orders, check orders, create a scheduler, create an execution queue, write `data/*.csv`, retune, search thresholds, run a parameter grid, or repeat OOS.

The latest read-only run found fixed six-hour block expansion diagnostics across M5 and M10 and produced a complete internal dry-run order request for human review only. This is not execution and is not a user-facing trade recommendation.

