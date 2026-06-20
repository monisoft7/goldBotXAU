# v0_8 Multi-Bar Exhaustion Reversion Result

- candidate_id: xauusd_multi_bar_exhaustion_reversion_v0_8
- candidate_family: multi_bar_exhaustion_reversion
- status: rejected
- reason: validation_gate_failed
- oos_status: locked_not_evaluated
- tests: 76 passed

## Train

- trade_count: 1205
- win_rate: 0.41244813278008297
- profit_factor: 0.5690328663793104
- expectancy: -0.26551867219917014
- max_drawdown: 324.4500000000027
- max_consecutive_losses: 11

## Validation

- trade_count: 256
- win_rate: 0.40234375
- profit_factor: 0.5449735449735449
- expectancy: -0.28554687500000003
- max_drawdown: 74.89999999999974
- max_consecutive_losses: 9

## Validation Gate

- passed: false
- reasons:
  - train_profit_factor_below_minimum
  - validation_profit_factor_below_minimum
  - validation_expectancy_below_minimum
  - validation_max_consecutive_losses_too_high

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
