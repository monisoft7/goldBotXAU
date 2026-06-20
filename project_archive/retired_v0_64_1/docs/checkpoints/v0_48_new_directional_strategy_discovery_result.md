# v0_48 New Directional Strategy Discovery Result

- Board module: `src/research/xauusd_new_directional_strategy_discovery_board.py`
- Board script: `scripts/run_xauusd_new_directional_discovery_v0_48.py`
- Board report: `reports/xauusd_new_directional_discovery_v0_48.json`
- Prior path closed: `xauusd_compression_then_expansion_v0_26`
- Prior path closure reason: `no_executable_direction_rule_and_v0_47_direction_board_failed`
- Board status: `no_new_directional_candidate_passed`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Directional families evaluated: `session_open_range_breakout_directional`, `prior_block_breakout_continuation_directional`, `failed_breakout_reversal_directional`, `trend_pullback_continuation_directional`
- Best candidate id: `trend_pullback_continuation_directional`
- Best candidate passed gate: `false`
- Best train profit factor: `1.8816690460357557`
- Best train expectancy: `0.2045491371207446`
- Best validation profit factor: `4.1448723516886234`
- Best validation trades: `16`
- Best validation expectancy: `0.4564440182058163`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Targeted tests: `39 passed`
- Warnings: `research_only_new_directional_board_not_demo_execution`, `v0_26_path_closed_as_execution_path_preserved_as_historical_evidence`, `combined_m5_m10_counts_are_not_treated_as_independent_oos_evidence`
- Next recommended step: `stop current research branch or create a broader non-OOS research plan`

v0_48 started a fresh train/validation-only board for inherently directional XAUUSD strategy families. It did not revive v0_26 as an executable path; v0_26 is preserved only as historical research evidence and optional market-state context.

No family passed the fixed predeclared gate. The best failed candidate was `trend_pullback_continuation_directional`; it cleared train and validation profit factor/expectancy but failed the validation trade-count gate with only `16` validation trades versus the required `25`.

All rejected candidates are preserved as `rejected_do_not_retune`. No order sending, order checking, live trading, scheduler, execution queue, candidate-rule retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.
