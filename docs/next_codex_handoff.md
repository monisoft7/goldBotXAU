# Next Codex Handoff

- Current project: goldBotXAU
- Last completed checkpoint: v0_44 bounded signal watch runner
- OOS: evaluated once, marker locked, repeated review disallowed
- Current test baseline: 524 passed
- Health status: warnings only due to documented safety mentions
- Rejected candidate count: 6
- Eligible for OOS review count: 0
- Strategy status: locked candidate only, no retune
- Execution status: dry-run only; v0_44 bounded watch calls the v0_43 builder and stops before any execution path
- Locked candidate: `xauusd_compression_then_expansion_v0_26`
- Latest candidate report: `reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json`
- Latest final demo readiness gate: `reports/xauusd_final_demo_readiness_gate_v0_41.json`
- Latest fixed demo risk envelope: `reports/xauusd_demo_risk_envelope_v0_40.json`
- Latest limited demo execution scaffold: `reports/xauusd_limited_demo_execution_v0_42.json`
- Latest signal order request builder: `reports/xauusd_signal_order_request_v0_43.json`
- Latest bounded signal watch: `reports/xauusd_bounded_signal_watch_v0_44.json`
- Latest checkpoint: `docs/checkpoints/v0_44_bounded_signal_watch_runner_result.md`
- Latest context pack: `reports/codex_context_v0_44.json`
- Latest health report: `reports/project_health_v0_44.json`
- Latest decision: `blocked_macro_event_window`
- Next safe task: wait until the macro event window clears, then rerun the bounded dry-run watch if a fresh signal-to-order-request check is still desired

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
