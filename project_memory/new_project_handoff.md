# Final Handoff For goldBotXAU

## Current Old Project Status
- old_project: multiGold
- old_project_status: archived_reference_only
- intelligence_track_status: frozen
- frozen_version: v1_90
- active_new_project: goldBotXAU
- active_next_track: gold_strategy_backtest_lab
- permanent_delete_performed: false

The multiGold folder has become too large for active strategy work. It contains old intelligence layers, failed strategy experiments, dynamic watchlist work, FOMC memory, context fixtures, and broad test coverage. Preserve it as context and audit history, but do not treat it as the active bot project.

## New Project Goal
Build one clean XAUUSD bot in `goldBotXAU` with one testable profitable strategy and smart risk management. The first phase is research and backtesting only.

## Context Boundaries
- Old intelligence/FOMC work is context only, not a signal.
- v1_87 FOMC XAUUSD 4h learning is descriptive context only.
- v1_88/v1_89/v1_90 rate decision context work is context only.
- Speaker tone and FOMC direction must not be used as trade signals.
- Demo/live/order_send/execution must remain disabled until backtest and out-of-sample pass.
- No trade-direction output is allowed until explicitly approved for a future demo phase.

## Required Strategy Metrics
Every strategy candidate must report:
- trade_count
- win_rate
- profit_factor
- expectancy
- max_drawdown
- max_consecutive_losses
- out_of_sample_result

## Codex Usage Rules
- Start from this handoff file.
- Read only handoff files unless explicitly told otherwise.
- Do small tasks.
- Use targeted tests first.
- Run full tests only at checkpoints.
- Do not scan the entire old archive unless needed.
- Modify only requested files.

## Next Safe Task
`create_clean_goldBotXAU_project_skeleton`
