# Market Context Layer Policy

The market context layer is a pre-strategy research gate for XAUUSD. Its future position is:

`Market Context Gate -> Technical Setup -> Risk Filter -> No-trade or candidate evaluation`

The layer is not a strategy, not a signal generator, not an order builder, and not an execution surface. v0_61 only defines feasibility, labels, schemas, alignment rules, and safety policy.

Future gate outputs:

- `allow_technical_research`
- `block_due_to_closed_market`
- `block_due_to_thin_liquidity`
- `block_due_to_event_risk`
- `block_due_to_missing_context_data`
- `observe_only_due_to_macro_uncertainty`

Market/session labels:

- `market_closed_weekend`
- `market_closed_holiday`
- `thin_liquidity_session`
- `normal_liquidity_session`
- `london_active`
- `ny_active`
- `london_ny_overlap`
- `late_us_session`

Closed-market policy:

- Weekend closure can be inferred from timestamps.
- Holiday closure requires a documented holiday calendar dataset before any research or forward use.
- Online or forward evaluation must not produce a tradeable signal during closed market periods.
- Missing context data must block the context gate or force observe-only status.

Safety boundaries:

- No OOS.
- No retune.
- No threshold search.
- No parameter grid.
- No executable candidate.
- No demo or live execution.
- No order sending or order checking.
- No scheduler or execution queue.
- No user-facing trade recommendation or profitability claim.
