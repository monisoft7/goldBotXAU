# v0_10 Train-Only Market Profile Result

- checkpoint: v0_10
- status: profile_ready
- tests: 99 passed
- profiled_split: train
- OOS: locked_not_evaluated
- strategy_logic_added: false
- trade_simulation_added: false

## Key Train-Only Observations

- ATR p80: 1.3230733892270252
- ATR p90: 1.7216007380924383
- ATR p95: 2.1671266144165635
- Highest activity block: block_12_18
- block_12_18 average_range_to_atr: 1.3516199632010066
- block_12_18 average_next_4bar_abs_return_to_atr: 1.428709955317565
- Hour 15 average_range_to_atr: 1.7438375069948429
- Hour 16 average_range_to_atr: 1.8379065636084606
- Hour 17 average_range_to_atr: 1.7587324313445742
- No clear fixed-bin reversion or continuation bias detected.
- Impulse >= 1.5 ATR sample_count: 8477
- Impulse >= 1.5 ATR persistence_4bar_rate: 0.49013585351447136
- Impulse >= 1.5 ATR reversal_4bar_rate: 0.5098641464855287

## Decision

- Do not build another generic reversion candidate.
- Do not build impulse-only continuation/reversion based on fixed bins.
- v0_11 should use time/session volatility structure, especially 12_18 and hours 15-17, not generic impulse reversal.
- Keep validation reserved for testing only.
- Keep OOS locked.

## Safety

- demo_enabled: false
- live_enabled: false
- order_send_allowed: false
- order_check_allowed: false
- execution_queue_enabled: false
- buy_sell_output_allowed: false
