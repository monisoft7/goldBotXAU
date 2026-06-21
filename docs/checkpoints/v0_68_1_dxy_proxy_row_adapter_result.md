# v0_68_1 DXY Proxy Row Adapter Result

- Adapter module: `src/research/xauusd_dxy_proxy_quality_ranker.py`
- Diagnostic script: `scripts/diagnose_xauusd_dxy_proxy_rows_v0_68_1.py`
- Adapter report: `reports/xauusd_dxy_proxy_row_adapter_v0_68_1.json`
- Adapter status: `dxy_proxy_row_adapter_completed`
- Source quality ranker version: `v0_66`
- Source event study version: `v0_68`
- Symbols checked: `DXYN`, `DXYZ`, `GDXY`, `USDX`
- Selected parseable proxy symbol: `DXYN`
- Fallback proxy symbol: `null`
- v0_68 blocker root cause: `timestamp_conversion_mismatch`
- Shared adapter created or updated: `true`
- Event study updated to use shared adapter: `true`
- Safe as-of alignment possible after adapter: `true`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Lookahead risk detected: `false`
- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Next adapter-recommended step: `rerun_v0_68_dxy_conditioned_event_study_with_shared_adapter`

## Parseability

| Symbol | Copied rows | Parseable rows | First timestamp | Last timestamp | Reason if unparseable |
| --- | ---: | ---: | --- | --- | --- |
| `DXYN` | 10000 | 10000 | `2021-09-15T18:30:00` | `2024-10-02T23:00:00` | `null` |
| `DXYZ` | 10000 | 10000 | `2024-11-15T18:45:00` | `2026-06-18T22:45:00` | `null` |
| `GDXY` | 10000 | 10000 | `2024-10-24T20:15:00` | `2026-06-18T22:45:00` | `null` |
| `USDX` | 6885 | 6885 | `2024-02-29T17:45:00` | `2026-06-18T22:45:00` | `null` |

All four checked M15 proxy symbols were copied through read-only MT5 access and parsed by the shared in-memory adapter. Each symbol had required OHLC columns present, `invalid_ohlc_count=0`, `duplicate_timestamp_count=0`, and `monotonic_timestamp_order=true`.

The v0_68 handoff failure was not caused by missing MT5 rows, missing M15 availability, invalid OHLC, a symbol-specific lack of rows, or an attempted fallback failure. The repaired adapter can parse the current DXYN M15 proxy rows, so the root cause is recorded as `timestamp_conversion_mismatch` between the earlier v0_68 parser and MT5 copy-rates row timestamps.

## v0_68 Rerun After Adapter

- Event study report: `reports/xauusd_dxy_conditioned_event_study_v0_68.json`
- Event study status after adapter wiring: `dxy_conditioned_event_study_completed_no_clear_leads`
- Proxy adapter version used by v0_68: `v0_68_1`
- DXYN copied rows: `10000`
- DXYN parseable rows: `10000`
- Event count: `30`
- Clear lead count: `0`
- v0_68 next recommended step after rerun: `v0_69_yield_or_brent_context_feasibility_before_new_strategy`

The rerun remained diagnostic-only. Labels were descriptive context only, not trade blockers or trade filters, and no persistent aligned market CSV was created.
