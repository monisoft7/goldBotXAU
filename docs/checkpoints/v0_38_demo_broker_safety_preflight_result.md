# v0_38 Demo Broker Safety Preflight Result

- Preflight module: `src/research/xauusd_demo_broker_safety_preflight.py`
- Preflight script: `scripts/build_xauusd_demo_broker_safety_preflight_v0_38.py`
- Preflight report: `reports/xauusd_demo_broker_safety_preflight_v0_38.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Decision: `demo_preflight_safety_design_ready`
- Preflight status: `completed`
- Candidate rules preserved: `true`
- Blocking conditions: none
- OOS: completed once, repeat review disallowed
- Prior v0_37 review: `ready_for_demo_preflight_design`
- Design only: `true`
- Demo execution created: `false`
- Broker execution path created: `false`
- MT5 connection created: `false`
- Order send created: `false`
- Order check created: `false`
- Execution queue created: `false`
- Buy/sell output allowed: `false`
- Trade recommendation output allowed: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Repeated OOS review: `false`

v0_38 creates only a design checklist/report for future demo preflight safety. It defines required confirmations and blockers before any future demo execution can even be considered. It does not connect to MT5, create a broker adapter, call or wrap order sending, call or wrap order checking, create an execution queue, output directional instructions, output trade recommendations, alter the locked v0_26 candidate, retune, optimize, grid search, threshold search, repeat OOS, or add market CSV files to git.

## Required Future Checks

- Candidate lock: v0_26 candidate id and fixed rules must match the committed v0_26 report exactly.
- OOS lock: OOS must remain reviewed once only, with repeat review disallowed.
- Execution absence: no demo/live execution surface, broker path, account connection, order function wrapper, or queue may exist.
- Output language: outputs must remain non-directional and contain no trading instructions or recommendations.
- Broker facts design: future read-only broker facts audit must cover contract, digits, tick size, lot step, min/max lot, margin mode, session hours, swaps, commission, spread source, and slippage assumptions.
- Risk controls design: future human-approved constraints must define account type, max loss, max lots, one-position cap, emergency stop, and no averaging into loss.
- Operator approval: explicit human approval must cite reviewed artifacts before any future demo consideration.

## Verification

- Targeted tests: `31 passed`
- Full tests: `467 passed`
- Health: `warnings`, no failures
- Safety: all execution creation flags remain `false`; candidate rules remain preserved; OOS was not repeated.

## Next Safe Step

Human review of v0_38 safety checklist, then design a separate read-only broker facts audit only. Keep demo execution, broker connection, order sending/checking, execution queues, directional output, and trade recommendations disabled.
