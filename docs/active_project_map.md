# Active Project Map

Sources:

- `reports/repository_consolidation_plan_v0_64.json`
- `reports/repository_cleanup_applied_v0_64_1.json`

## v0_64_1 Active Context Boundary

- cleanup_version: `v0_64_1`
- cleanup_status: `cleanup_applied_completed`
- files_scanned_count: `672`
- active_keep_count: `193`
- archive_candidate_count: `305`
- delete_candidate_count: `172`
- manual_review_count: `11`
- planned_archive_count: `298`
- planned_cache_delete_count: `172`
- files_archived_count: `298`
- files_deleted_count: `172`
- files_preserved_count: `232`
- manual_review_skipped_count: `11`
- archive_root: `project_archive/retired_v0_64_1`
- archive_candidates_remaining: `0`
- cache_candidates_remaining: `0`
- data_csv_touched: `false`
- safety_files_touched: `false`
- latest_context_files_touched: `false`

## Active Keep Classes

- `active_core_keep`: current source, scripts, tests, config, and CI files that remain part of the working project.
- `active_safety_keep`: safety, governance, OOS, demo, execution, order, risk, preflight, and readiness files. These must not be removed by cleanup.
- `active_context_layer_keep`: v0_58 through v0_64 research-lab and market-context artifacts plus current project-map and archive docs.
- `active_data_contract_keep`: data loaders, dataset manifests, CSV loader/resampler contracts, timestamp/gap/cost policies, README, and git metadata.

## Latest Preserved Checkpoint Chain

- v0_58: research lab integrity audit
- v0_59: research lab warning standardization
- v0_60: second-tier fixed-rule board
- v0_61: market context feasibility audit
- v0_62: market context labeler
- v0_63: context-labeled event study
- v0_64: repository consolidation plan and failed experiment archive
- v0_64_1: reviewed low-risk cleanup applied to archive historical/generated artifacts and delete cache paths
- v0_64_2: cleanup boundary repair, pytest archive exclusion, and active dependency restore

## Data Boundary

- `data/*.csv` files are `local_data_only` or `manual_review_required`, never `active_core_keep`.
- Tracked data CSV files detected: `data/xauusd_m15_xauusd_2023-01-01_2026-06-11.csv`
- No `data/*.csv` files should be staged or committed during v0_64 cleanup planning.

## Cleanup Boundary

- Cache artifacts were deleted only from `cache_delete_candidate` paths.
- Generated historical report payloads were archived from `generated_report_archive_candidate` paths.
- Retired historical artifacts were archived from `retired_experiment_candidate` and `historical_archive_document_only` paths after active dependency protections.
- v0_64_1 applied cleanup to `project_archive/retired_v0_64_1` without touching safety files, latest v0_58-v0_64 context files, or CSV data.
- v0_64_2 excludes `project_archive` from pytest collection and marks active import dependencies as `active_dependency_keep`.
- v0_64_2 restored 14 active dependency files from the archive and verified `364 passed`.
- The next safe task is `commit_v0_63_to_v0_64_2_then_v0_65_dxy_proxy_context_audit`.
