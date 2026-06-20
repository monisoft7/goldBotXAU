# Retired Experiments Archive

Sources:

- `reports/repository_consolidation_plan_v0_64.json`
- `reports/repository_cleanup_applied_v0_64_1.json`

v0_64 documents failed and retired experiments before any repository cleanup. This file is historical evidence only. It does not authorize strategy testing, OOS, retune, threshold search, parameter grids, executable candidates, demo/live execution, order sending, order checking, or trade recommendation output.

## Archive Status

- consolidation_version: `v0_64`
- consolidation_status: `repository_consolidation_plan_completed`
- failed_experiments_indexed_count: `22`
- retired_experiment_candidate_path_count: `109`
- safe_to_apply_cleanup_now: `false`
- cleanup_requires_human_review: `true`
- cleanup_version: `v0_64_1`
- cleanup_status: `cleanup_applied_completed`
- archive_root: `project_archive/retired_v0_64_1`
- files_archived_count: `298`
- files_deleted_count: `172`
- manual_review_skipped_count: `11`
- data_csv_touched: `false`
- safety_files_touched: `false`
- latest_context_files_touched: `false`
- repair_version: `v0_64_2`
- repair_status: `cleanup_boundary_repair_completed`
- restored_active_dependency_count: `14`
- project_archive_test_collection_blocked: `true`
- full_pytest_result: `364 passed`

## Indexed Failed Experiments

| Candidate | Version | Status | Evidence |
| --- | --- | --- | --- |
| `xauusd_atr_impulse_reversion_v0_7` | `v0_7` | `rejected` | `src/research/candidate_registry.py` |
| `xauusd_multi_bar_exhaustion_reversion_v0_8` | `v0_8` | `rejected` | `src/research/candidate_registry.py` |
| `xauusd_session_volatility_expansion_v0_11` | `v0_11` | `rejected` | `src/research/candidate_registry.py` |
| `xauusd_low_atr_range_expansion_followthrough_v0_14` | `v0_14` | `rejected` | `src/research/candidate_registry.py` |
| `xauusd_low_atr_x_hour_16_v0_17` | `v0_17` | `rejected` | `src/research/candidate_registry.py` |
| `xauusd_low_tf_spike_m5_hour_11_fade_v0_23` | `v0_23` | `rejected_train_validation_gate_failed` | `src/research/candidate_registry.py` |
| `expansion_continuation_close_direction` | `v0_47` | `rejected_do_not_retune` | `reports/xauusd_direction_research_board_v0_47.json` |
| `expansion_fade_direction` | `v0_47` | `rejected_do_not_retune` | `reports/xauusd_direction_research_board_v0_47.json` |
| `first_breakout_m5_confirmed_by_m10` | `v0_47` | `rejected_do_not_retune` | `reports/xauusd_direction_research_board_v0_47.json` |
| `response_block_body_direction` | `v0_47` | `rejected_do_not_retune` | `reports/xauusd_direction_research_board_v0_47.json` |
| `session_open_range_breakout_directional` | `v0_48` | `rejected_do_not_retune` | `reports/xauusd_new_directional_discovery_v0_48.json` |
| `prior_block_breakout_continuation_directional` | `v0_48` | `rejected_do_not_retune` | `reports/xauusd_new_directional_discovery_v0_48.json` |
| `failed_breakout_reversal_directional` | `v0_48` | `rejected_do_not_retune` | `reports/xauusd_new_directional_discovery_v0_48.json` |
| `trend_pullback_continuation_directional` | `v0_48` | `rejected_do_not_retune` | `reports/xauusd_new_directional_discovery_v0_48.json` |
| `trend_pullback_continuation_directional` | `v0_51` | `expanded_evidence_failed` | `reports/xauusd_trend_pullback_expanded_retest_v0_51.json` |
| `prior_day_liquidity_sweep_reversal` | `v0_53` | `rejected_do_not_retune` | `reports/xauusd_external_shortlist_board_v0_53.json` |
| `london_opening_range_breakout_or_first_candle_direction` | `v0_53` | `rejected_do_not_retune` | `reports/xauusd_external_shortlist_board_v0_53.json` |
| `asian_range_london_breakout_confirmation` | `v0_53` | `rejected_do_not_retune` | `reports/xauusd_external_shortlist_board_v0_53.json` |
| `session_block_directional_bias_candidate` | `v0_56` | `session_block_candidate_rejected` | `reports/xauusd_session_block_bias_eval_v0_56.json` |
| `failed_m15_swing_breakout_reversal` | `v0_60` | `rejected_do_not_retune` | `reports/xauusd_second_tier_board_v0_60.json` |
| `ny_liquidity_sweep_reversal` | `v0_60` | `rejected_do_not_retune` | `reports/xauusd_second_tier_board_v0_60.json` |
| `sequential_m5_move_mean_reversion` | `v0_60` | `rejected_do_not_retune` | `reports/xauusd_second_tier_board_v0_60.json` |

For full rejection reasons, `do_not_retune`, OOS usage, and demo/live approval flags, use the machine-readable `failed_experiments` array in `reports/repository_consolidation_plan_v0_64.json`.

## Cleanup Rule

Retired experiment files and generated historical artifacts were moved under `project_archive/retired_v0_64_1` with their relative paths preserved. v0_64_2 restored active modules, scripts, and fixture reports that root tests or active safety/context modules still depend on. Failed experiment evidence remains documented here and in `reports/repository_consolidation_plan_v0_64.json`. Manual-review paths and CSV data were skipped.
