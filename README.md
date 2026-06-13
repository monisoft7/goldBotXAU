# goldBotXAU

Clean XAUUSD-only strategy research bot.

This project is backtest first. Demo and live trading remain disabled until numeric evidence passes review, including out-of-sample validation.

## Required Metrics

Every future strategy candidate must report:

- trade_count
- win_rate
- profit_factor
- expectancy
- max_drawdown
- max_consecutive_losses
- out_of_sample_result

## Current Scope

- Research only
- Local CSV data only
- No execution
- No price fetching
- No strategy implementation yet

## v0_2 Backtest Lab

- v0_2 backtest lab foundation created
- strategy status: none_yet
- execution status: disabled
- next task: plug one candidate strategy into lab only after lab tests pass

For Codex operating rules, see:
`docs/codex_operating_notes.md`

## Repository Workflow

- Use branches/checkpoints for scoped changes.
- Open PRs for repository changes.
- GitHub Actions runs tests on push and pull request.
- Codex task rules are in `docs/codex_task_protocol.md`.

## Project Health Check

Run after major Codex changes and before PR merge:

```powershell
py -3 scripts/project_health_check.py --json --output reports/project_health_v0_20.json
```

The health check is infrastructure-only. It does not trade, does not access out-of-sample data, and only scans the local project tree.

## Compact Codex Context

Use the compact context pack instead of pasting long handoffs into future Codex tasks:

```powershell
py -3 scripts/print_codex_context.py --json --output reports/codex_context_v0_20.json
```

Recommended workflow after every major task:

```powershell
py -3 -m pytest -q
py -3 scripts/project_health_check.py --json --output reports/project_health_v0_21.json
py -3 scripts/print_codex_context.py --json --output reports/codex_context_v0_21.json
```

## v0_3 Data Readiness Auditor

- v0_3 adds XAUUSD data readiness auditing
- strategy status: none_yet
- execution status: disabled
- next task: use read-only export tooling or place local XAUUSD M15 CSV files under `data/` and run the auditor

## v0_4 Read-Only MT5 Exporter

- v0_4 adds a read-only XAUUSD M15 CSV exporter for locally available MT5 market data
- strategy status: none_yet
- execution status: disabled
- export: `py -3 scripts/export_mt5_xauusd_m15.py --symbol XAUUSD --from-date 2023-01-01 --to-date 2026-06-11 --data-dir data --json`
- audit: `py -3 scripts/audit_xauusd_data.py --data-dir data --pattern "xauusd_m15_*.csv" --json`

## v0_5 Dataset Manifest

- v0_5 creates a fixed chronological dataset manifest and train/validation/out-of-sample split
- strategy status: none_yet
- execution status: disabled
- future candidate strategies must use this manifest
- next task: create first strategy hypothesis plug-in using train/validation only, with out-of-sample locked until candidate passes validation

## v0_6 Strategy Research Harness

- v0_6 creates a strategy research harness and locked out-of-sample guard
- strategy status: none_yet
- execution status: disabled
- out-of-sample remains locked until a candidate passes train/validation review
- next task: add first single strategy hypothesis as a candidate plugin, evaluated only on train and validation

## v0_7 ATR Impulse Reversion Candidate

- v0_7 adds the first fixed XAUUSD M15 offline research candidate
- strategy status: train_validation_research_only
- execution status: disabled
- out-of-sample remains locked until candidate promotion review

v0_7 result and next handoff:
`docs/checkpoints/v0_7_atr_impulse_reversion_result.md`
`docs/next_codex_handoff.md`

## v0_8 Multi-Bar Exhaustion Reversion Candidate

- v0_8 adds the second fixed XAUUSD M15 offline research candidate
- result: rejected
- execution status: disabled
- out-of-sample remains locked and was not evaluated

v0_8 result:
`docs/checkpoints/v0_8_multi_bar_exhaustion_reversion_result.md`

## v0_9 Research Registry And Compact Reports

- list known candidates: `py -3 scripts/list_research_candidates.py --json`
- compact harness output: `py -3 scripts/run_strategy_research_harness.py --data-dir data --pattern "xauusd_m15_*.csv" --candidate xauusd_multi_bar_exhaustion_reversion_v0_8 --compact --json`
- compact reports omit full `equity_curve` arrays

## v0_10 Train-Only Market Profiler

- descriptive train-split profile only; no strategy candidate or trade simulation
- run: `py -3 scripts/profile_xauusd_market.py --data-dir data --pattern "xauusd_m15_*.csv" --json`
- optional output: `--output reports/xauusd_market_profile_v0_10.json`

## v0_11 Session Volatility Expansion Candidate

- v0_11 adds a fixed train/validation-only session volatility expansion candidate
- source: v0_10 train-only market profile, especially the 15-17 UTC high-activity window
- result: rejected, validation gate failed because train profit factor was below minimum
- out-of-sample remains locked and was not evaluated

v0_11 result:
`docs/checkpoints/v0_11_session_volatility_expansion_result.md`

## v0_13 Strategy Family Selection Board

- v0_13 creates a train-only decision board for the next fixed hypothesis family
- recommendation: low_atr_range_expansion_followthrough for v0_14
- no strategy logic, trade simulation, or out-of-sample evaluation added

v0_13 report:
`reports/xauusd_strategy_family_selection_v0_13.json`

## v0_14 Low ATR Range Expansion Followthrough Candidate

- v0_14 adds a fixed train/validation-only low ATR range expansion followthrough candidate
- result: rejected, validation gate failed on train profit factor, validation profit factor, and validation expectancy
- out-of-sample remains locked and was not evaluated
- compact run: `py -3 scripts/run_strategy_research_harness.py --data-dir data --pattern "xauusd_m15_*.csv" --candidate xauusd_low_atr_range_expansion_followthrough_v0_14 --compact --json`

v0_14 result:
`docs/checkpoints/v0_14_low_atr_range_expansion_followthrough_result.md`

## v0_17 Low ATR x Dataset Hour 16 Candidate

- v0_17 adds a fixed train/validation-only low ATR x dataset hour 16 response candidate
- source: v0_16 advisor idea triage profiler
- result: rejected, validation gate failed on train profit factor, validation profit factor, and validation expectancy
- out-of-sample remains locked and was not evaluated
- compact run: `py -3 scripts/run_strategy_research_harness.py --data-dir data --pattern "xauusd_m15_*.csv" --candidate xauusd_low_atr_x_hour_16_v0_17 --compact --json`

v0_17 result:
`docs/checkpoints/v0_17_low_atr_x_hour_16_result.md`

## v0_21 Low-Timeframe Data Tooling

- v0_21 adds read-only local MT5 XAUUSD M1/M5 export tooling and local CSV M10 resampling
- strategy status: none added
- execution status: disabled
- out-of-sample remains locked and was not evaluated
- low-timeframe data export: `py -3 scripts/export_mt5_xauusd_low_tf.py --symbol XAUUSD --timeframe M1 --from-date 2026-01-01 --to-date 2026-06-11 --data-dir data --json`
- M10 resampling: `py -3 scripts/resample_xauusd_timeframe.py --input <m1_csv_file> --target-timeframe M10 --data-dir data --json`
