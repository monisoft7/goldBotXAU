# v0_11 Session Volatility Expansion Result

- candidate_id: xauusd_session_volatility_expansion_v0_11
- candidate_family: session_volatility_expansion
- source_profile: v0_10_train_only_market_profile
- status: rejected
- reason: validation_gate_failed
- oos_status: locked_not_evaluated
- tests: 110 passed

## Fixed Hypothesis

- Use only train/validation splits.
- Restrict signals to the high-activity 15-17 UTC window observed in v0_10.
- Test session-window expansion beyond the prior 16 M15 bars.
- Do not reuse generic impulse reversion or multi-bar exhaustion reversion.

## Train

- trade_count: 569
- win_rate: 0.4797891036906854
- profit_factor: 0.8696866061698781
- expectancy: -0.06132206910613204
- max_drawdown: 48.91438504522703
- max_consecutive_losses: 9

## Validation

- trade_count: 115
- win_rate: 0.5565217391304348
- profit_factor: 1.1911865275122382
- expectancy: 0.07434843954394188
- max_drawdown: 7.777076423107331
- max_consecutive_losses: 5

## Validation Gate

- passed: false
- reasons:
  - train_profit_factor_below_minimum

## Decision

- do_not_retune_this_candidate
- do_not_open_oos
- move_to_new_hypothesis_family

## Safety

- demo_enabled: false
- live_enabled: false
- order_send_allowed: false
- buy_sell_output_allowed: false
- oos_evaluated: false
