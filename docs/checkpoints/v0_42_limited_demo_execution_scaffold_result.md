# v0_42 Limited Demo Execution Scaffold Result

- Executor module: `src/execution/xauusd_limited_demo_executor.py`
- Executor script: `scripts/run_xauusd_limited_demo_execution_v0_42.py`
- Executor report: `reports/xauusd_limited_demo_execution_v0_42.json`
- Checkpoint: `docs/checkpoints/v0_42_limited_demo_execution_scaffold_result.md`
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

The scaffold uses static/manual macro event windows only. It does not scrape news, fetch events automatically, start an execution loop, create a background scheduler, use martingale, average into loss, scale positions, raise lots above `0.01`, retune, search thresholds, run a parameter grid, repeat OOS, create a new strategy, emit directional instructions, emit trade recommendations, or add `data/*.csv`.

Targeted tests: `38 passed`

Next safe step: human review of the v0_42 dry-run scaffold report before any separate explicit demo action.
