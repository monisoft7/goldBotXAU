# Next Codex Handoff

- Current project: goldBotXAU
- Last completed checkpoint: v0_48 new directional strategy discovery board
- OOS: evaluated once, marker locked, repeated review disallowed
- Current test baseline: 574 passed before v0_47; v0_48 targeted tests: 39 passed
- Health status: warnings only due to documented safety mentions
- Rejected candidate count: 6
- Eligible for OOS review count: 0
- Strategy status: v0_26 compression/expansion closed as execution path; no retune
- Execution status: research only; v0_48 found no new train/validation directional candidate that passed the fixed gate
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
- Latest checkpoint: `docs/checkpoints/v0_48_new_directional_strategy_discovery_result.md`
- Latest context pack: `reports/codex_context_v0_48.json`
- Latest health report: `reports/project_health_v0_48.json`
- Latest decision: `no_new_directional_candidate_passed`
- Next safe task: stop current research branch or create a broader non-OOS research plan; do not promote to demo

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
