# Next Codex Handoff

- Current project: goldBotXAU
- Last completed checkpoint: v0_42 limited demo execution scaffold
- OOS: evaluated once, marker locked, repeated review disallowed
- Current test baseline: 507 passed
- Health status: warnings only due to documented safety mentions
- Rejected candidate count: 6
- Eligible for OOS review count: 0
- Strategy status: locked candidate only, no retune
- Execution status: limited demo scaffold dry-run only by default
- Locked candidate: `xauusd_compression_then_expansion_v0_26`
- Latest candidate report: `reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json`
- Latest final demo readiness gate: `reports/xauusd_final_demo_readiness_gate_v0_41.json`
- Latest fixed demo risk envelope: `reports/xauusd_demo_risk_envelope_v0_40.json`
- Latest limited demo execution scaffold: `reports/xauusd_limited_demo_execution_v0_42.json`
- Latest checkpoint: `docs/checkpoints/v0_42_limited_demo_execution_scaffold_result.md`
- Latest context pack: `reports/codex_context_v0_42.json`
- Latest health report: `reports/project_health_v0_42.json`
- Latest decision: `dry_run_ready_no_order_sent`
- Next safe task: human review of the v0_42 dry-run scaffold report before any separate explicit demo action

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
