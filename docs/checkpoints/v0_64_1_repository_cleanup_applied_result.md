# v0_64_1 Repository Cleanup Applied Result

Source report: `reports/repository_cleanup_applied_v0_64_1.json`

v0_64_1 applies the reviewed low-risk cleanup path from the v0_64 repository consolidation plan. It is repository hygiene only. It does not authorize strategy testing, trade filtering, OOS, retune, threshold search, parameter grids, executable candidates, demo/live execution, order sending, order checking, or trade recommendation output.

## Result

- cleanup_version: `v0_64_1`
- cleanup_status: `cleanup_applied_completed`
- dry_run: `false`
- apply_requested: `true`
- files_archived_count: `298`
- files_deleted_count: `172`
- files_preserved_count: `232`
- manual_review_skipped_count: `11`
- data_csv_touched: `false`
- safety_files_touched: `false`
- latest_context_files_touched: `false`
- archive_root: `project_archive/retired_v0_64_1`
- archive_candidates_remaining: `0`
- cache_candidates_remaining: `0`
- archive_files_present: `298`

## Safety State

- approved_for_strategy_testing: `false`
- approved_for_trade_filtering: `false`
- train_validation_only: `true`
- oos_used: `false`
- repeated_oos_review: `false`
- retune_performed: `false`
- threshold_search_performed: `false`
- parameter_grid_performed: `false`
- executable_candidate_created: `false`
- demo_execution_allowed: `false`
- order_send_called: `false`
- order_check_called: `false`
- live_allowed: `false`
- trade_recommendation_output: `false`

The cleanup used `reports/repository_consolidation_plan_v0_64.json` as its source plan, archived only approved historical/generated/retired classes after active dependency protections, deleted only cache paths, skipped manual-review paths, and preserved `data/*.csv` and `context_data/*.csv`.

Next recommended step: `v0_65_dxy_proxy_context_audit_after_cleanup`.
