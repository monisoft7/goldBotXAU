# Codex Operating Notes For goldBotXAU

## Project Path

`C:\Users\THE BLU WALF\Desktop\goldBotXAU`

## Current Project State

* Project: `goldBotXAU`
* Scope: XAUUSD only
* Current lab version: `v0_11`
* Current status: third fixed train/validation research candidate rejected
* Latest targeted tests: 110 passed
* Strategy status: `none_yet`
* Execution status: `disabled`
* Current blocker: out-of-sample remains locked until candidate promotion review

## Codex Intelligence Policy

Use the lowest sufficient intelligence level:

| Task Type                                                                             | Intelligence |
| ------------------------------------------------------------------------------------- | ------------ |
| Documentation, README, project memory notes                                           | Low          |
| Small code modules, CSV loader, CLI, tests                                            | Medium       |
| Backtest engine changes, first candidate strategy integration, metrics validation     | High         |
| Complex debugging, out-of-sample analysis, walk-forward validation, risk logic review | Extra High   |

Default for documentation-only work: `Low`.

Default for data-loader or lab plumbing: `Medium`.

Do not use `Extra High` unless the task is genuinely complex.

## Window / Context Policy

Stay in the same Codex window during the same checkpoint to reduce context waste.

Open a new Codex window only when:

* A major checkpoint is completed.
* Context becomes polluted or too large.
* Repeated errors make a clean restart more efficient.

Do not resend the full historical handoff every time. Use this file plus a short current task prompt.

## Hard Safety Rules

* No demo trading.
* No live trading.
* No order sending.
* No execution queue.
* No BUY/SELL output.
* No trade-direction recommendation.
* No scraping or online price fetching.
* Use local files only.
* Use read-only export tooling only when needed.
* Do not scan or import the old multiGold archive.
* Do not reuse blacklisted failed strategy families.
* Do not tune thresholds blindly.
* Every future strategy candidate must report numeric metrics.

## Required Metrics For Any Future Strategy Candidate

Every strategy candidate must report:

* trade_count
* win_rate
* profit_factor
* expectancy
* max_drawdown
* max_consecutive_losses
* out_of_sample_result

## Failed / Forbidden Strategy Families

Do not restart these families:

* baseline_current_rules
* local threshold tinkering variants
* productivity/signal variants
* recent-only promotion variants
* old hypothesis lab outputs
* range-break drawdown-control family
* old regime-aware families
* broad scanner / pending-order scanner
* speaker tone as trade signal
* FOMC direction as trade signal

## Current Next Safe Direction

Before any strategy work:

1. Prepare or validate local XAUUSD M15 CSV data under `data/`.
2. Keep all tooling read-only.
3. Confirm the backtest lab can load candles.
4. Only after data is valid, plug one candidate strategy into the lab.

## Standard Targeted Test Command

```powershell
py -3 -m pytest -q tests/test_project_skeleton.py tests/test_xauusd_backtest_lab.py tests/test_xauusd_data_auditor.py tests/test_mt5_readonly_xauusd_exporter.py tests/test_xauusd_dataset_manifest.py tests/test_strategy_research_harness.py tests/test_xauusd_atr_impulse_reversion_candidate.py
```

## Standard Lab CLI Command

```powershell
py -3 scripts/run_xauusd_backtest_lab.py --data-dir data --pattern "xauusd_m15_*.csv" --json
```

## Standard Data Audit CLI Command

```powershell
py -3 scripts/audit_xauusd_data.py --data-dir data --pattern "xauusd_m15_*.csv" --json
```

## Standard Read-Only Export Command

```powershell
py -3 scripts/export_mt5_xauusd_m15.py --symbol XAUUSD --from-date 2023-01-01 --to-date 2026-06-11 --data-dir data --json
```

## Standard Dataset Manifest Command

```powershell
py -3 scripts/build_xauusd_dataset_manifest.py --data-dir data --pattern "xauusd_m15_*.csv" --json --output reports/xauusd_dataset_manifest_v0_5.json
```

## Standard Research Harness Command

```powershell
py -3 scripts/run_strategy_research_harness.py --data-dir data --pattern "xauusd_m15_*.csv" --json
```

## Standard v0_7 Candidate Command

```powershell
py -3 scripts/run_strategy_research_harness.py --data-dir data --pattern "xauusd_m15_*.csv" --candidate xauusd_atr_impulse_reversion_v0_7 --json
```

## Standard v0_8 Candidate Command

```powershell
py -3 scripts/run_strategy_research_harness.py --data-dir data --pattern "xauusd_m15_*.csv" --candidate xauusd_multi_bar_exhaustion_reversion_v0_8 --json
```

## Standard v0_11 Candidate Command

```powershell
py -3 scripts/run_strategy_research_harness.py --data-dir data --pattern "xauusd_m15_*.csv" --candidate xauusd_session_volatility_expansion_v0_11 --json
```
