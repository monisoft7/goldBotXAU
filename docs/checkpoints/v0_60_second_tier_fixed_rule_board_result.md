# v0_60 Second-Tier Fixed-Rule Board Result

- Board module: `src/research/xauusd_second_tier_fixed_rule_board.py`
- Board script: `scripts/run_xauusd_second_tier_board_v0_60.py`
- Board report: `reports/xauusd_second_tier_board_v0_60.json`
- Board status: `no_second_tier_candidate_passed`
- Source standardization version: `v0_59`
- Tested candidate ids: `failed_m15_swing_breakout_reversal`, `ny_liquidity_sweep_reversal`, `sequential_m5_move_mean_reversion`
- Best candidate id: `ny_liquidity_sweep_reversal`
- Best candidate passed gate: `false`
- Best train profit factor: `0.7656489689036846`
- Best train expectancy: `-0.21007613604144268`
- Best train trades: `270`
- Best validation profit factor: `1.7101588243682602`
- Best validation expectancy: `0.5567402891905258`
- Best validation trades: `43`
- Rejected do-not-retune candidates: `failed_m15_swing_breakout_reversal`, `ny_liquidity_sweep_reversal`, `sequential_m5_move_mean_reversion`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Gates lowered: `false`
- Past metrics changed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Timestamp basis reported: `true`
- Timestamp basis: `unknown_or_broker_server_time`
- Policy references: `docs/research_lab_cost_policy.md`, `docs/research_lab_timestamp_and_session_policy.md`, `docs/research_lab_gap_classification_policy.md`, `docs/research_lab_gate_policy.md`
- Blockers: none
- Warnings: research-only board, fixed rules only, OOS candles excluded from evaluation, v0_59 cost policy referenced with raw R metrics and no retroactive cost recompute, timestamp basis inherited from v0_59, conservative stop-first same-candle handling, M15 excluded OOS candle count `10180`
- Targeted tests: `53 passed`
- Next recommended step: `broaden non-OOS research or consider adding external features such as DXY/yields/news calendar before further strategy tests.`

v0_60 evaluated exactly the three requested second-tier fixed-rule ideas under the v0_59 standardized lab policies. No candidate passed the fixed train/validation gate. The strongest result by the board sort was `ny_liquidity_sweep_reversal`, but it failed because train PF and train expectancy were below the fixed gate, validation trades were below `50`, and train max consecutive losses exceeded `8`.

No OOS run, repeated OOS review, retune, threshold search, parameter grid, gate lowering, past metric change, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, profitability claim, or `data/*.csv` addition was introduced.
