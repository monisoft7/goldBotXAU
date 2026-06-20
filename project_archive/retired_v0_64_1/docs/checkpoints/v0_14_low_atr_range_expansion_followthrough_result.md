# v0_14 Low ATR Range Expansion Followthrough Result

- candidate_id: xauusd_low_atr_range_expansion_followthrough_v0_14
- candidate_name: XAUUSD Low ATR Range Expansion Followthrough
- candidate_version: v0_14
- family_name: low_atr_range_expansion_followthrough
- status: rejected
- reason: validation_gate_failed
- oos_status: locked_not_evaluated
- source_selection_board: v0_13_strategy_family_selection_board
- tests: 153 passed

## Fixed Hypothesis

- Use only train/validation splits.
- Test controlled expansion after low-ATR compression.
- Do not use classic range-break logic.
- Do not retune v0_7, v0_8, or v0_11.

## Train

- trade_count: 902
- win_rate: 0.4911308203991131
- profit_factor: 0.8378602892407452
- expectancy: -0.0728660807411693
- max_drawdown: 85.37351730303274
- max_consecutive_losses: 8
- final_equity_r: -65.72520482853388

## Validation

- trade_count: 185
- win_rate: 0.4864864864864865
- profit_factor: 0.7900902139165014
- expectancy: -0.09910269270440307
- max_drawdown: 22.365933464000886
- max_consecutive_losses: 7
- final_equity_r: -18.333998150314596

## Validation Gate

- passed: false
- reasons:
  - train_profit_factor_below_minimum
  - validation_profit_factor_below_minimum
  - validation_expectancy_below_minimum
- minimum_train_trades: 100
- minimum_validation_trades: 30
- minimum_train_profit_factor: 1.05
- minimum_validation_profit_factor: 1.10
- minimum_validation_expectancy: 0.0
- maximum_validation_max_consecutive_losses: 8

## Decision

- eligible_for_oos_review: false
- do_not_retune_this_candidate
- do_not_open_oos
- no_candidate_eligible_for_oos_review
- move_to_new_hypothesis_family

## OOS

- locked_not_evaluated
- no OOS evaluation performed

## Safety

- demo_enabled: false
- live_enabled: false
- order_send_allowed: false
- execution_queue_enabled: false
- buy_sell_output_allowed: false
- oos_evaluated: false
- research_candidate_logic_present: true
- execution_logic_present: false
- trade_recommendation_output_present: false
