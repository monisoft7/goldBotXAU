# Failed Strategy Registry

All families below are blacklisted for the clean `goldBotXAU` project.

## baseline_current_rules
- family_name: baseline_current_rules
- why_excluded: Existing baseline did not produce enough reliable evidence for active deployment and belongs to the old multiGold track.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: Reuse only neutral plumbing or validation ideas, not the rule family.

## local threshold tinkering variants
- family_name: local threshold tinkering variants
- why_excluded: Local parameter edits risk overfitting and did not establish a robust profitable edge.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: no
- notes: Do not restart threshold-tweaking loops in the new project.

## productivity/signal variants
- family_name: productivity/signal variants
- why_excluded: Attempts to increase signal count harmed quality or failed promotion gates.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: no
- notes: Signal frequency is not a substitute for edge.

## recent-only promotion variants
- family_name: recent-only promotion variants
- why_excluded: Recent-window promotion logic risks cherry-picking and did not prove durable out-of-sample behavior.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: no
- notes: New work must use explicit train/test and out-of-sample validation.

## old hypothesis lab outputs
- family_name: old hypothesis lab outputs
- why_excluded: The old hypothesis lab did not produce a promotable strategy family.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: Reuse only negative findings and metric discipline.

## range-break drawdown-control family
- family_name: range-break drawdown-control family
- why_excluded: Drawdown-control variants failed to create an acceptable active candidate.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: Risk concepts may be reused, but not the family.

## old regime-aware families
- family_name: old regime-aware families
- why_excluded: Regime-aware families failed promotion and did not become an active candidate.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: Regime labels may inform diagnostics only after a base strategy exists.

## broad scanner/pending-order scanner
- family_name: broad scanner/pending-order scanner
- why_excluded: Broad scanning expands scope and execution risk before a clean single-strategy backtest exists.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: no
- notes: Keep `goldBotXAU` focused on one XAUUSD strategy.

## speaker tone as trade signal
- family_name: speaker tone as trade signal
- why_excluded: Speaker tone is contextual intelligence only and is not validated as a trade signal.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: May be retained as non-signal research context only.

## FOMC direction as trade signal
- family_name: FOMC direction as trade signal
- why_excluded: FOMC direction summaries are descriptive context and not validated as predictive trade rules.
- retry_allowed: false
- retune_allowed: false
- can_reuse_components: yes
- notes: FOMC context must not produce trade-direction output.

## v0_64 failed/rejected experiment archive
- source_report: `reports/repository_consolidation_plan_v0_64.json`
- consolidation_status: `repository_consolidation_plan_completed`
- failed_experiments_indexed_count: `22`
- do_not_retune_default: true
- safe_to_apply_cleanup_now: false
- cleanup_requires_human_review: true

The v0_64 consolidation pass indexes failed and rejected candidates from the static registry plus existing reports/checkpoints. These entries are historical evidence, not active strategy invitations. Retired candidates must not be retuned or revived without a separate human-approved research contract.

Indexed candidate names are listed below. The evidence-entry count is higher than the unique-name count because `trend_pullback_continuation_directional` is represented by both the v0_48 initial rejection and the v0_51 expanded retest failure.

- `xauusd_atr_impulse_reversion_v0_7`
- `xauusd_multi_bar_exhaustion_reversion_v0_8`
- `xauusd_session_volatility_expansion_v0_11`
- `xauusd_low_atr_range_expansion_followthrough_v0_14`
- `xauusd_low_atr_x_hour_16_v0_17`
- `xauusd_low_tf_spike_m5_hour_11_fade_v0_23`
- `expansion_continuation_close_direction`
- `expansion_fade_direction`
- `first_breakout_m5_confirmed_by_m10`
- `response_block_body_direction`
- `session_open_range_breakout_directional`
- `prior_block_breakout_continuation_directional`
- `failed_breakout_reversal_directional`
- `trend_pullback_continuation_directional`
- `prior_day_liquidity_sweep_reversal`
- `london_opening_range_breakout_or_first_candle_direction`
- `asian_range_london_breakout_confirmation`
- `session_block_directional_bias_candidate`
- `failed_m15_swing_breakout_reversal`
- `ny_liquidity_sweep_reversal`
- `sequential_m5_move_mean_reversion`
