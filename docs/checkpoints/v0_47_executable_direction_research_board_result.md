# v0_47 Executable Direction Research Board Result

- Board module: `src/research/xauusd_executable_direction_research_board.py`
- Board script: `scripts/run_xauusd_direction_research_board_v0_47.py`
- Board report: `reports/xauusd_direction_research_board_v0_47.json`
- Candidate id used as fixed source filter: `xauusd_compression_then_expansion_v0_26`
- Board status: `no_direction_candidate_passed`
- Source filter preserved: `true`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Direction hypotheses evaluated: `expansion_continuation_close_direction`, `first_breakout_m5_confirmed_by_m10`, `response_block_body_direction`, `expansion_fade_direction`
- Best candidate id: `expansion_fade_direction`
- Best candidate passed gate: `false`
- Best train profit factor: `0.95235467842927`
- Best train expectancy: `-0.02935974061341059`
- Best validation profit factor: `1.1857423708051282`
- Best validation trades: `139`
- Best validation expectancy: `0.0739936548925565`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Targeted tests: `37 passed`
- Warnings: `research_only_direction_board_not_demo_execution`, `combined_m5_m10_counts_are_not_treated_as_independent_oos_evidence`
- Next recommended step: `stop this path or design a new non-OOS research candidate`

v0_47 evaluated a small fixed board of explicit direction hypotheses around the locked v0_26 compression/expansion market-state filter. The source filter candidate rules were not modified, no OOS rows were used, and no threshold search, parameter grid, or retune was performed.

No board candidate passed the predeclared train/validation gate. The strongest failed candidate was the expansion fade direction, but it failed because train profit factor and train expectancy did not clear the fixed gate. Demo execution remains blocked.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, repeated OOS, or `data/*.csv` addition was introduced.
