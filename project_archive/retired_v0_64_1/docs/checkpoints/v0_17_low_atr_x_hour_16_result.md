# v0_17 Low ATR x Dataset Hour 16 Result

- candidate_id: xauusd_low_atr_x_hour_16_v0_17
- candidate_name: XAUUSD Low ATR x Dataset Hour 16 Response
- candidate_version: v0_17
- family_name: low_atr_x_dataset_hour_16_response
- status: rejected
- reason: validation_gate_failed
- oos_status: locked_not_evaluated
- source_triage: v0_16_advisor_idea_triage

## Fixed Hypothesis

- Use only train/validation splits.
- Treat hour 16 as dataset_hour_16, not proven UTC.
- Use fixed_low_atr only.
- Do not use rolling_low_atr.
- Do not retune v0_7, v0_8, v0_11, or v0_14.

## Train

- trade_count: 174
- win_rate: 0.5172413793103449
- profit_factor: 0.8775454581423584
- expectancy: -0.06095571155952807
- max_drawdown: 21.756293811357885
- max_consecutive_losses: 10
- final_equity_r: -10.606293811357892

## Validation

- trade_count: 54
- win_rate: 0.42592592592592593
- profit_factor: 0.5992337989192761
- expectancy: -0.23289334104757953
- max_drawdown: 13.426240416569298
- max_consecutive_losses: 8
- final_equity_r: -12.576240416569298

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
