# Next Codex Handoff

- Current project: goldBotXAU
- Last completed checkpoint: v0_54 XAUUSD edge profiler
- OOS: evaluated once, marker locked, repeated review disallowed
- Current test baseline: 47 passed for v0_54 targeted tests; prior broad baseline 574 passed before v0_47
- Health status: warnings only due to documented safety mentions
- Rejected candidate count: 6
- Eligible for OOS review count: 0
- Strategy status: v0_26 compression/expansion closed as execution path; no retune
- Execution status: research only; v0_54 profiled XAUUSD train/validation event behavior, with demo/OOS blocked
- Locked candidate: `xauusd_compression_then_expansion_v0_26`
- Latest candidate report: `reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json`
- Latest final demo readiness gate: `reports/xauusd_final_demo_readiness_gate_v0_41.json`
- Latest fixed demo risk envelope: `reports/xauusd_demo_risk_envelope_v0_40.json`
- Latest limited demo execution scaffold: `reports/xauusd_limited_demo_execution_v0_42.json`
- Latest signal order request builder: `reports/xauusd_signal_order_request_v0_43.json`
- Latest bounded signal watch: `reports/xauusd_bounded_signal_watch_v0_44.json`
- Latest live signal snapshot: `reports/xauusd_live_signal_snapshot_v0_45.json`
- Latest direction provenance audit: `reports/xauusd_candidate_direction_provenance_v0_46.json`
- Latest direction research board: `reports/xauusd_direction_research_board_v0_47.json`
- Latest new directional discovery board: `reports/xauusd_new_directional_discovery_v0_48.json`
- Latest trend pullback stability audit: `reports/xauusd_trend_pullback_stability_audit_v0_49.json`
- Latest historical data expansion feasibility audit: `reports/xauusd_historical_data_expansion_feasibility_v0_50.json`
- Latest trend pullback expanded retest: `reports/xauusd_trend_pullback_expanded_retest_v0_51.json`
- Latest external strategy idea triage: `reports/xauusd_external_strategy_idea_triage_v0_52.json`
- Latest Kimi external idea addendum: `reports/xauusd_kimi_external_idea_addendum_v0_52_1.json`
- Latest external shortlist board: `reports/xauusd_external_shortlist_board_v0_53.json`
- Latest edge profiler: `reports/xauusd_edge_profiler_v0_54.json`
- Latest checkpoint: `docs/checkpoints/v0_54_xauusd_edge_profiler_result.md`
- Latest context pack: `reports/codex_context_v0_54.json`
- Latest health report: `reports/project_health_v0_54.json`
- Latest decision: `edge_profile_completed_with_research_leads`
- Next safe task: v0_55 fixed-rule candidate design for top 1-2 leads, no OOS; do not run OOS, retune, threshold search, parameter grid, create executable candidates, or demo/live execution

## v0_54 XAUUSD Edge Profiler Result

- Profiler module: `src/research/xauusd_edge_profiler.py`
- Profiler script: `scripts/run_xauusd_edge_profiler_v0_54.py`
- Profiler report: `reports/xauusd_edge_profiler_v0_54.json`
- Profiler status: `edge_profile_completed_with_research_leads`
- Source previous board version: `v0_53`
- Purpose: `empirical_edge_mapping_not_strategy_backtest`
- Event families profiled: `session_return_profile`, `prior_day_high_low_sweep_profile`, `asian_range_breakout_profile`, `london_opening_candle_profile`, `ny_first_hour_profile`, `failed_m15_swing_breakout_profile`, `sequential_m5_move_profile`, `volatility_regime_profile`
- Strongest empirical leads: `session_return_profile`, `volatility_regime_profile`
- Recommended v0_55 research plan: `v0_55 fixed-rule candidate design for session_return_profile using predeclared train/validation-only rules; no OOS`; `v0_55 fixed-rule candidate design for volatility_regime_profile using predeclared train/validation-only rules; no OOS`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `47 passed`
- Next recommended step: `v0_55 fixed-rule candidate design for top 1-2 leads, no OOS`

v0_54 is an empirical profiler only. It maps descriptive train/validation event-family behavior and does not create an executable strategy candidate, run OOS, retune, search thresholds, search parameter grids, make a profitability claim, or emit a user-facing trade recommendation.

No demo/live execution, order sending, order checking, scheduler, execution queue, or `data/*.csv` addition was introduced.

## v0_53 External Shortlist Train/Validation Board Result

- Board module: `src/research/xauusd_external_shortlist_train_validation_board.py`
- Board script: `scripts/run_xauusd_external_shortlist_board_v0_53.py`
- Board report: `reports/xauusd_external_shortlist_board_v0_53.json`
- Board status: `no_external_shortlist_candidate_passed`
- Source triage versions: `v0_52`, `v0_52_1`
- Tested candidate ids: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Best candidate id: `asian_range_london_breakout_confirmation`
- Best candidate passed gate: `false`
- Best train profit factor: `1.0107152929889043`
- Best train expectancy: `0.005028872470589754`
- Best train trades: `497`
- Best validation profit factor: `1.1330238648738264`
- Best validation expectancy: `0.053786897553678714`
- Best validation trades: `94`
- Rejected do-not-retune candidates: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `45 passed`
- Next recommended step: `broaden non-OOS research or stop current branch`

v0_53 implemented fixed M15 train/validation-only tests for the finalized external shortlist. The strongest fixed result was `asian_range_london_breakout_confirmation`, but no candidate passed the full fixed gate.

No OOS run, repeated OOS review, retune, threshold search, parameter grid, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_52_1 Kimi External Idea Addendum Result

- Addendum module: `src/research/xauusd_kimi_external_idea_addendum.py`
- Addendum script: `scripts/run_xauusd_kimi_idea_addendum_v0_52_1.py`
- Addendum report: `reports/xauusd_kimi_external_idea_addendum_v0_52_1.json`
- Addendum status: `kimi_addendum_completed_shortlist_unchanged`
- Source triage version: `v0_52`
- Kimi added to external sources: `true`
- Kimi raw idea count: `10`
- Kimi deduplicated idea count: `5`
- Original v0_52 shortlist: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Final shortlist for v0_53: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Shortlist changed: `false`
- Top ranked idea id: `prior_day_liquidity_sweep_reversal`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Backtest implemented: `false`
- Candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `48 passed`
- Next recommended step: `use the unchanged v0_52 shortlist for v0_53 fixed-rule train/validation-only board design; keep Kimi addendum ideas as supplemental do-not-retune-aware notes`

v0_52_1 adds Kimi as an external idea source without changing the finalized v0_52 report. Kimi ideas were deduplicated or penalized where they overlapped opening-range, Asian/liquidity-sweep, v0_26 compression/expansion, VWAP, weekend gap, trend-pullback, or generic candle-pattern families.

The v0_52 shortlist remains unchanged because no Kimi idea materially beat the top three. No profitability claim was made.

No order sending, order checking, live trading, scheduler, execution queue, backtest implementation, candidate creation, retune, threshold search, parameter grid, OOS run, repeated OOS review, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_52 External Strategy Idea Intake Triage Result

- Triage module: `src/research/xauusd_external_strategy_idea_triage.py`
- Triage script: `scripts/run_xauusd_external_strategy_idea_triage_v0_52.py`
- Triage report: `reports/xauusd_external_strategy_idea_triage_v0_52.json`
- Triage status: `shortlist_ready_for_v0_53_non_oos_board`
- Total raw ideas: `10`
- Deduplicated idea count: `8`
- Top ranked idea id: `prior_day_liquidity_sweep_reversal`
- Shortlist for v0_53: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `43 passed`
- Next recommended step: `design v0_53 fixed-rule train/validation-only board for the shortlisted ideas; no OOS, retune, threshold search, parameter grid, or execution`

v0_52 is intake and triage only. It did not evaluate profitability, did not create a strategy candidate, did not implement a backtest, and did not promote any branch.

No order sending, order checking, live trading, scheduler, execution queue, strategy evaluation, backtest implementation, candidate creation, retune, threshold search, parameter grid, OOS run, repeated OOS review, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_51 Trend Pullback Expanded Retest Result

- Retest module: `src/research/xauusd_trend_pullback_expanded_retest.py`
- Retest script: `scripts/run_xauusd_trend_pullback_expanded_retest_v0_51.py`
- Retest report: `reports/xauusd_trend_pullback_expanded_retest_v0_51.json`
- Retest status: `expanded_evidence_failed`
- Candidate id: `trend_pullback_continuation_directional`
- Source candidate board version: `v0_48`
- Source stability audit version: `v0_49`
- Source data feasibility version: `v0_50`
- Candidate rules preserved: `true`
- Expanded range: `2019-01-02T06:00:00` to `2022-12-30T21:55:00`
- Train/validation-equivalent only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Candle count by timeframe: `M5=281152`, `M10=141464`
- Expanded trade count: `230`
- Expanded profit factor: `1.1861259380980205`
- Expanded expectancy: `0.0574451807402551`
- Sample concentration risk: `low`
- Expanded evidence passed gate: `false`
- Candidate locking allowed pre-OOS: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `41 passed`
- Next recommended step: `stop trend_pullback branch or broaden non-OOS research`

v0_51 retested the exact fixed v0_48 `trend_pullback_continuation_directional` rule on the older range made feasible by v0_50. This was expanded train/validation-equivalent evidence only, not OOS, not a retune, and not a parameter or threshold search.

The expanded sample reached `230` trades across `4` calendar years and reduced concentration risk to `low`, but the expanded profit factor was `1.1861259380980205`, below the fixed `1.20` gate. Candidate locking, OOS, demo execution, and live execution remain blocked.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_50 Historical Data Expansion Feasibility Result

- Audit module: `src/research/xauusd_historical_data_expansion_feasibility_audit.py`
- Audit script: `scripts/audit_xauusd_historical_data_expansion_v0_50.py`
- Audit report: `reports/xauusd_historical_data_expansion_feasibility_v0_50.json`
- Audit status: `expansion_data_partially_available`
- Symbol: `XAUUSD`
- Requested range: `2019-01-01` to `2022-12-31`
- MT5 read-only: `true`
- MT5 initialized: `true`
- MT5 shutdown called: `true`
- Available oldest candle time: `2019-01-02T06:00:00`
- Available newest candle time: `2022-12-30T23:55:00`
- Requested range available: `false`
- Candle count by timeframe: `M5=281176`, `M10=141476`
- Missing range gap count: `2086`
- Missing range gaps truncated in report: `true`
- Data expansion feasible: `true`
- Candidate to retest later: `trend_pullback_continuation_directional`
- Candidate rules preserved: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `37 passed`
- Next recommended step: `v0_51 fixed-rule expanded train/validation retest on available older range only, no OOS`

v0_50 used MT5 read-only data availability checks only. The full requested range is not complete, but there is enough available older low-timeframe data to justify a fixed-rule expanded train/validation retest. No CSV files were exported or added to git.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_49 Trend Pullback Sample Stability Audit Result

- Audit module: `src/research/xauusd_trend_pullback_sample_stability_audit.py`
- Audit script: `scripts/audit_xauusd_trend_pullback_stability_v0_49.py`
- Audit report: `reports/xauusd_trend_pullback_stability_audit_v0_49.json`
- Source board version: `v0_48`
- Candidate id: `trend_pullback_continuation_directional`
- Candidate rules preserved: `true`
- Audit status: `completed`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Train profit factor: `1.8816690460357557`
- Train expectancy: `0.2045491371207446`
- Train trades: `164`
- Validation profit factor: `4.1448723516886234`
- Validation expectancy: `0.4564440182058163`
- Validation trades: `16`
- Validation trade minimum: `25`
- Validation trade count passed: `false`
- Sample concentration risk: `high`
- Fixed 0.05R cost edge broken: `false`
- Stability decision: `promising_but_insufficient_validation_sample`
- Candidate locking allowed pre-OOS: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `38 passed`
- Next recommended step: `collect more train/validation-equivalent evidence or stop; do not lock candidate or run OOS`

v0_49 reconstructed the v0_48 fixed trend-pullback candidate on existing train/validation data only. It matched the v0_48 source metrics and did not modify candidate rules.

The candidate remains promising but insufficient: validation PF and expectancy are strong, and fixed cost sensitivity does not break the edge, but validation has only `16` trades versus the fixed `25` minimum. Candidate locking, OOS, demo execution, and live execution remain blocked.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_48 New Directional Strategy Discovery Result

- Board module: `src/research/xauusd_new_directional_strategy_discovery_board.py`
- Board script: `scripts/run_xauusd_new_directional_discovery_v0_48.py`
- Board report: `reports/xauusd_new_directional_discovery_v0_48.json`
- Prior path closed: `xauusd_compression_then_expansion_v0_26`
- Prior path closure reason: `no_executable_direction_rule_and_v0_47_direction_board_failed`
- Board status: `no_new_directional_candidate_passed`
- Train/validation only: `true`
- OOS used: `false`
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
- Targeted tests: `39 passed`
- Next recommended step: `stop current research branch or create a broader non-OOS research plan`

v0_48 evaluated four fixed inherently directional families on existing train/validation data only. No OOS rows were used, no thresholds or parameter grids were searched, and no retune was performed.

No new family passed the fixed board gate. The strongest failed family, `trend_pullback_continuation_directional`, failed only on validation trade count: `16` trades versus the required `25`. All rejected candidates remain `rejected_do_not_retune`.

No order sending, order checking, live trading, scheduler, execution queue, v0_26 candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_47 Executable Direction Research Board Result

- Board module: `src/research/xauusd_executable_direction_research_board.py`
- Board script: `scripts/run_xauusd_direction_research_board_v0_47.py`
- Board report: `reports/xauusd_direction_research_board_v0_47.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Board status: `no_direction_candidate_passed`
- Source filter preserved: `true`
- Train/validation only: `true`
- OOS used: `false`
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
- Targeted tests: `37 passed`
- Next recommended step: `stop this path or design a new non-OOS research candidate`

v0_47 treated the locked v0_26 candidate as a non-executable market-state filter and evaluated only four fixed direction hypotheses on train/validation rows. No hypothesis passed the predeclared gate, so no locked directional candidate was created and demo execution remains blocked.

No order sending, order checking, live trading, scheduler, execution queue, v0_26 candidate-rule change, retune, threshold search, parameter grid, repeated OOS, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_46 Candidate Direction Provenance Audit Result

- Audit module: `src/research/xauusd_candidate_direction_provenance_audit.py`
- Audit script: `scripts/audit_xauusd_candidate_direction_v0_46.py`
- Audit report: `reports/xauusd_candidate_direction_provenance_v0_46.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Audit status: `no_direction_rule_found_execution_blocked`
- Direction rule found: `false`
- Executable side mapping found: `false`
- Direction provenance confidence: `none`
- Demo execution direction ready: `false`
- Blockers: `locked_candidate_has_no_executable_side_mapping`, `locked_candidate_has_no_explicit_direction_rule`
- Warning: `next_block_expansion_behavior_found_but_not_executable_direction_rule`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Candidate rules preserved: `true`

v0_46 audited the existing locked v0_26 candidate artifacts and registry record. The artifacts contain fixed compression-then-expansion behavior provenance, but no deterministic executable internal side rule or side mapping. Demo execution direction readiness remains blocked.

No side was invented or inferred. No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, repeated OOS, or `data/*.csv` addition was introduced.

## v0_45_1 Direction Validity Guard Result

- Snapshot module: `src/execution/xauusd_live_signal_snapshot_provider.py`
- Builder module: `src/execution/xauusd_signal_to_order_request_builder.py`
- Executor module: `src/execution/xauusd_limited_demo_executor.py`
- Snapshot report: `reports/xauusd_live_signal_snapshot_v0_45.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Snapshot version: `v0_45_1`
- Snapshot status: `snapshot_ready_signal_confirmed_direction_unassigned`
- Signal qualified: `true`
- Signal reason: `locked_candidate_current_snapshot_expansion_confirmed_across_m5_m10`
- Direction assigned: `false`
- Direction source: `locked_candidate_no_deterministic_direction_rule`
- Executable side valid: `false`
- Order request present: `false`
- Order request complete: `false`
- Order request validation status: `direction_unassigned_non_executable`
- Invalid order request reasons: `direction_unassigned_non_executable`
- Review request present: `true`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`

v0_45_1 makes `direction_unassigned_review_only`, missing side values, empty side values, and unknown side values non-executable. The latest live snapshot still qualifies the locked v0_26 compression-expansion signal, but it does not report a complete order request because no deterministic executable internal side is assigned.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, repeated OOS, or `data/*.csv` addition was introduced.

## v0_45 Live Signal Snapshot Provider Result

- Snapshot module: `src/execution/xauusd_live_signal_snapshot_provider.py`
- Snapshot script: `scripts/build_xauusd_live_signal_snapshot_v0_45.py`
- Snapshot report: `reports/xauusd_live_signal_snapshot_v0_45.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Snapshot status: `snapshot_ready_order_request_built_dry_run_only`
- Timeframes requested: `M5`, `M10`
- Candles loaded: `M5=288`, `M10=144`
- Current signal snapshot present: `true`
- Signal evaluated: `true`
- Signal qualified: `true`
- Signal reason: `locked_candidate_current_snapshot_expansion_confirmed_across_m5_m10`
- Order request present: `true`
- Order request complete: `true`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- MT5 read-only: `true`
- MT5 initialized: `true`
- MT5 shutdown called: `true`
- Targeted tests: `45 passed`

v0_45 is read-only market data access only. It fetches the latest required M5/M10 candles, builds a structured `current_signal_snapshot`, and wires that snapshot into the v0_43 dry-run builder.

The latest report contains a complete internal dry-run order request for human review only. It did not call order sending, did not call order checking, did not enable live trading, did not create a scheduler, did not create an execution queue, did not change v0_26 candidate rules, did not retune, did not search thresholds, did not run a parameter grid, did not repeat OOS, did not output a user-facing trade recommendation, and did not add `data/*.csv`.

## v0_44_1 Real Interval Enforcement Result

- Watch module: `src/execution/xauusd_bounded_signal_watch_runner.py`
- Watch script: `scripts/run_xauusd_bounded_signal_watch_v0_44.py`
- Watch report: `reports/xauusd_bounded_signal_watch_v0_44.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Watch version: `v0_44_1`
- Watch status: `blocked_macro_event_window`
- Max cycles: `6`
- Interval seconds: `300`
- Cycles completed: `1`
- Stopped early: `true`
- Stop reason: `blocked_macro_event_window`
- Sleep enabled: `true`
- Sleep calls: `0`
- Total planned sleep seconds: `0`
- Interval seconds honored: `true`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `39 passed`

v0_44_1 enforces real foreground intervals by default. Normal CLI runs sleep for `--interval-seconds` between non-final cycles; `--no-sleep` is now the explicit test/dev bypass and reports `no_sleep_reason=explicit_no_sleep_flag`.

The latest report stopped on the active macro event window before any inter-cycle wait point, so `sleep_calls` is `0` while `sleep_enabled` and `interval_seconds_honored` remain `true`.

## v0_44 Bounded Signal Watch Runner Result

- Watch module: `src/execution/xauusd_bounded_signal_watch_runner.py`
- Watch script: `scripts/run_xauusd_bounded_signal_watch_v0_44.py`
- Watch report: `reports/xauusd_bounded_signal_watch_v0_44.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Watch status: `blocked_macro_event_window`
- Max cycles: `6`
- Interval seconds: `300`
- Cycles completed: `1`
- Stopped early: `true`
- Stop reason: `blocked_macro_event_window`
- Latest signal qualified: `false`
- Latest order request present: `false`
- Latest order request complete: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `36 passed`

v0_44 is a foreground, bounded, dry-run-only watch runner. It calls the v0_43 builder for at most the configured cycle count and stops early when the macro lock is active or a complete internal order request is ready for human review.

The default v0_44 report stopped on the active macro event window. No order request was built, and no execution path was called.

## v0_43 Signal-to-Order-Request Builder Result

- Builder module: `src/execution/xauusd_signal_to_order_request_builder.py`
- Builder script: `scripts/build_xauusd_signal_order_request_v0_43.py`
- Builder report: `reports/xauusd_signal_order_request_v0_43.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Builder status: `no_qualified_signal_now`
- Signal evaluated: `true`
- Signal qualified: `false`
- Signal reason: `no_current_signal_snapshot_supplied`
- Order request present: `false`
- Order request complete: `false`
- Order request validation status: `missing_order_request`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Macro event lock status: `clear_static_manual_windows`
- Targeted tests: `35 passed`

v0_43 is a dry-run-only internal builder. It converts a qualified locked v0_26 signal snapshot into a complete demo-only order request for review, or returns `no_qualified_signal_now`. The default report has no qualified signal and no order request.

The internal order request contract requires `symbol=XAUUSD`, `lot=0.01`, `demo_only=true`, side, order type, action, risk reference, stop loss or stop distance, take profit or exit rule, and candidate id `xauusd_compression_then_expansion_v0_26`.

## v0_42_1 Order Request Completeness Guard Result

- Executor module: `src/execution/xauusd_limited_demo_executor.py`
- Executor report: `reports/xauusd_limited_demo_execution_v0_42.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Executor status in regenerated default report: `dry_run_ready_no_order_sent`
- Explicit-send missing-request status: `blocked_missing_complete_order_request`
- Candidate rules preserved: `true`
- Demo only: `true`
- Live allowed: `false`
- Order request present in default report: `false`
- Order request complete in default report: `false`
- Order request validation status: `missing_order_request`
- Missing order request fields: `order_request`, `symbol`, `lot`, `demo_only`, `side`, `order_type`, `action`
- Order send attempted: `false`
- Order send called: `false`
- Order check called: `false`
- Targeted tests: `40 passed`

v0_42_1 hard-blocks the protected explicit demo order send path when `--allow-demo-order-send`, `--no-dry-run`, and the exact approval token are supplied without a complete explicit demo-only order request. Missing or incomplete request status is now `blocked_missing_complete_order_request`, not `demo_order_send_allowed_but_not_called`.

Required complete order request fields are symbol `XAUUSD`, fixed lot `0.01`, `demo_only=true`, explicit side field, explicit order type field, and explicit action field.

## v0_42 Limited Demo Execution Scaffold Result

- Executor module: `src/execution/xauusd_limited_demo_executor.py`
- Executor script: `scripts/run_xauusd_limited_demo_execution_v0_42.py`
- Executor report: `reports/xauusd_limited_demo_execution_v0_42.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Executor status: `dry_run_ready_no_order_sent`
- Mode: `dry_run`
- Candidate rules preserved: `true`
- Demo only: `true`
- Live allowed: `false`
- Default order send allowed: `false`
- Order send attempted: `false`
- Order send called: `false`
- Order check called: `false`
- Demo account verified: `true`
- Symbol verified: `true`
- Lot verified: `true`
- Risk envelope verified: `true`
- Readiness gate verified: `true`
- Macro event lock enabled: `true`
- Macro event lock status: `clear_static_manual_windows`
- Static macro window included: `2026-06-17 19:30` to `2026-06-17 22:30` `Africa/Tripoli`
- Approval token required: `true`
- Approval token valid in default run: `false`
- Blockers: none
- Warnings: none

v0_42 creates the first limited demo execution scaffold only. The default CLI path is dry-run and does not call order sending. Explicit future demo order sending requires the `--allow-demo-order-send` flag, a non-dry-run invocation, the exact human approval token, demo account verification, the locked v0_41 readiness decision, the fixed v0_40 risk envelope, symbol `XAUUSD`, lot `0.01`, and a clear static macro event lock.

The static macro event lock uses manual configured windows only. It includes FOMC/Fed Chair support and the default Libya-time blocked window for `2026-06-17 19:30` to `2026-06-17 22:30` `Africa/Tripoli`.

v0_42 did not execute an order, did not call order checking, did not permit live trading, did not create an automatic loop, did not create a background scheduler, did not use martingale, did not average into loss, did not scale positions, did not increase lots above `0.01`, did not retune, did not search thresholds, did not run a parameter grid, did not repeat OOS, did not create a new strategy, did not emit directional instructions, did not emit trade recommendations, and did not add any `data/*.csv`.

## v0_41 Final Demo Readiness Gate Result

- Gate report: `reports/xauusd_final_demo_readiness_gate_v0_41.json`
- Decision: `final_demo_readiness_gate_passed_pending_human_authorization`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Candidate rules preserved: `true`
- Final blockers: none
- Accepted warnings: `tick_value_contract_size_mismatch`
- Human authorization required: `true`
- Demo allowed: `false`
- Execution allowed: `false`
- Order send allowed: `false`
- Order check allowed: `false`

Fixed demo risk summary:

- Starting demo lot `0.01`
- Max demo lot `0.01`
- Max positions `1`
- Stop after `2` consecutive losses
- Max daily demo loss `2.0R`
- Max session demo loss `1.0R`
- No martingale, no averaging into loss, no position scaling

## Safety Boundary

- no live trading
- no real account trading
- no order sending by default
- no order checking in v0_42
- no automatic loop
- no background scheduler
- no execution queue
- no martingale
- no averaging into loss
- no position scaling
- no lot increase above `0.01`
- no recommendation output
- no directional output
- no threshold search or parameter grid
- no retune of rejected candidates
- no retune of the v0_26 compression-expansion candidate
- no repeated OOS review
- no OOS result-driven rule modification
