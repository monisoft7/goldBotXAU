# v0_63 Context-Labeled Event Study Result

- Study module: `src/research/xauusd_context_labeled_event_study.py`
- Study script: `scripts/run_xauusd_context_labeled_event_study_v0_63.py`
- Study report: `reports/xauusd_context_labeled_event_study_v0_63.json`
- Study status: `context_labeled_event_study_completed_no_clear_leads`
- Source labeler version: `v0_62`
- Source prior versions considered: `v0_53`, `v0_56`, `v0_60`
- Labels used as trade blockers: `false`
- Strategy rules changed: `false`
- Gates lowered: `false`
- Strongest context-conditioned leads: none
- Revived candidate allowed: `false`
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
- Data CSV added to git: `false`
- Targeted tests: `53 passed`
- Next recommended step: `add external datasets such as holiday/economic calendar/DXY before further context testing.`

Recomputed train/validation historical outcome counts:

- `asian_range_london_breakout_confirmation`: train `497`, validation `94`
- `ny_liquidity_sweep_reversal`: train `270`, validation `43`
- `prior_day_liquidity_sweep_reversal`: train `431`, validation `88`
- `failed_m15_swing_breakout_reversal`: train `4341`, validation `896`
- `sequential_m5_move_mean_reversion`: train `2913`, validation `614`
- `session_block_directional_bias_candidate`: train `34`, validation `3`

v0_63 attached fixed v0_62 timestamp-only labels to historical train/validation events from the prior rejected fixed-rule branches. It did not use labels as blockers, did not optimize labels, did not change strategy rules, did not create an executable candidate, and did not run OOS.

No context slice satisfied the lead criteria after validation sample, train/validation consistency, validation PF, expectancy, and concentration checks. Several slices were descriptive or locally stronger, but they remained weak, inconsistent, too small, or concentration-risk blocked.
