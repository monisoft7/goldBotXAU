# Next Codex Handoff

- Current project: goldBotXAU
- Last completed checkpoint: v0_72 Oil-conditioned event study
- OOS: no OOS used in v0_68_1; historical OOS lock state remains governed by checked-in reports and registry
- Current test baseline: 66 passed for v0_72 targeted oil-conditioned event study/context pack tests; prior 64 passed for v0_71 targeted gold macro context board/context pack tests; prior 64 passed for v0_70 targeted oil proxy quality/label design/context pack tests; prior 63 passed for v0_69 targeted oil proxy audit/context pack tests; prior 71 passed for v0_68_1 targeted DXY proxy row adapter/DXY-conditioned event study/context pack tests; prior 62 passed for v0_68 targeted DXY-conditioned event study/context pack tests; prior 61 passed for v0_67 targeted DXY regime label design/context pack tests; prior 60 passed for v0_66 targeted DXY proxy ranker/context pack tests; prior 59 passed for v0_65 targeted DXY proxy audit/context pack tests; prior 364 passed for v0_64_2 full pytest; prior v0_64_1 targeted baseline 61 passed before apply, prior v0_64 targeted baseline 55 passed, prior v0_63 targeted baseline 53 passed, prior v0_62 targeted baseline 53 passed, prior v0_61 targeted baseline 59 passed, prior v0_60 targeted baseline 53 passed, prior v0_59 targeted baseline 53 passed, prior v0_58 targeted baseline 54 passed, and prior broad baseline 574 passed before v0_47
- Health status: warnings only due to documented safety mentions
- Rejected candidate count: 6
- Eligible for OOS review count: 0
- Strategy status: v0_26 compression/expansion closed as execution path; no retune
- Execution status: research infrastructure only; v0_72 ran the oil-conditioned diagnostic event study on BRN with WTI as fallback metadata only, found `event_count=30` and `clear_lead_count=0`, selected next step `v0_73_yield_real_yield_context_feasibility_no_strategy`, and did not perform strategy testing, trade filtering approval, execution, order sending, order checking, or aligned CSV export
- Locked candidate: `xauusd_compression_then_expansion_v0_26`
- Latest candidate report: `reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json`
- Latest final demo readiness gate: `reports/xauusd_final_demo_readiness_gate_v0_41.json`
- Latest fixed demo risk envelope: `reports/xauusd_demo_risk_envelope_v0_40.json`
- Latest limited demo execution scaffold: `reports/xauusd_limited_demo_execution_v0_42.json`
- Latest signal order request builder: `reports/xauusd_signal_order_request_v0_43.json`
- Latest bounded signal watch: `reports/xauusd_bounded_signal_watch_v0_44.json`
- Latest live signal snapshot: `reports/xauusd_live_signal_snapshot_v0_45.json`
- Latest direction provenance audit: `reports/xauusd_candidate_direction_provenance_v0_46.json`
- Latest direction research board: `reports/xauusd_direction_research_board_v0_47.json`
- Latest new directional discovery board: `reports/xauusd_new_directional_discovery_v0_48.json`
- Latest trend pullback stability audit: `reports/xauusd_trend_pullback_stability_audit_v0_49.json`
- Latest historical data expansion feasibility audit: `reports/xauusd_historical_data_expansion_feasibility_v0_50.json`
- Latest trend pullback expanded retest: `reports/xauusd_trend_pullback_expanded_retest_v0_51.json`
- Latest external strategy idea triage: `reports/xauusd_external_strategy_idea_triage_v0_52.json`
- Latest Kimi external idea addendum: `reports/xauusd_kimi_external_idea_addendum_v0_52_1.json`
- Latest external shortlist board: `reports/xauusd_external_shortlist_board_v0_53.json`
- Latest edge profiler: `reports/xauusd_edge_profiler_v0_54.json`
- Latest session/volatility design board: `reports/xauusd_session_volatility_design_v0_55.json`
- Latest session block bias evaluation: `reports/xauusd_session_block_bias_eval_v0_56.json`
- Latest volatility regime lead viability audit: `reports/xauusd_volatility_regime_lead_viability_v0_57.json`
- Latest research lab integrity audit: `reports/xauusd_research_lab_integrity_audit_v0_58.json`
- Latest research lab warning standardization: `reports/xauusd_research_lab_warning_standardization_v0_59.json`
- Latest second-tier fixed-rule board: `reports/xauusd_second_tier_board_v0_60.json`
- Latest market context feasibility audit: `reports/xauusd_market_context_feasibility_v0_61.json`
- Latest market context labeler: `reports/xauusd_market_context_labels_v0_62.json`
- Latest context-labeled event study: `reports/xauusd_context_labeled_event_study_v0_63.json`
- Latest DXY proxy context audit: `reports/xauusd_dxy_proxy_context_audit_v0_65.json`
- Latest DXY proxy quality ranker: `reports/xauusd_dxy_proxy_quality_ranker_v0_66.json`
- Latest DXY regime label design: `reports/xauusd_dxy_regime_label_design_v0_67.json`
- Latest DXY proxy row adapter: `reports/xauusd_dxy_proxy_row_adapter_v0_68_1.json`
- Latest DXY-conditioned event study: `reports/xauusd_dxy_conditioned_event_study_v0_68.json`
- Latest oil proxy context audit: `reports/xauusd_oil_proxy_context_audit_v0_69.json`
- Latest oil proxy quality and label design: `reports/xauusd_oil_proxy_quality_and_label_design_v0_70.json`
- Latest gold macro context board: `reports/xauusd_gold_macro_context_board_v0_71.json`
- Latest oil-conditioned event study: `reports/xauusd_oil_conditioned_event_study_v0_72.json`
- Latest repository consolidation plan: `reports/repository_consolidation_plan_v0_64.json`
- Latest repository cleanup result: `reports/repository_cleanup_applied_v0_64_1.json`
- Latest repository cleanup repair: `reports/repository_cleanup_repair_v0_64_2.json`
- Latest active project map: `docs/active_project_map.md`
- Latest retired experiments archive: `docs/retired_experiments_archive.md`
- Latest checkpoint: `docs/checkpoints/v0_72_oil_conditioned_event_study_result.md`
- Latest context pack generator: `scripts/print_codex_context.py` (`context_version=v0_72`)
- Latest health report: `reports/project_health_v0_64_2.json`
- Latest decision: `yield_real_yield_context_feasibility_next`; DXY event study has `clear_lead_count=0`, oil-conditioned event study has `clear_lead_count=0`, and the next safest research branch is yield/real-yield context feasibility only
- Next safe task: v0_73_yield_real_yield_context_feasibility_no_strategy; keep yield/real-yield work as diagnostic research only, with no strategy testing unless explicitly approved, no trade filtering approval, no OOS, no retune, no threshold search, no parameter grid, no executable candidates for demo, no demo/live execution, no order_send/order_check, no trade recommendations, no aligned market CSV export, no safety/governance file removal, no `data/*.csv` staging, and no `git add .`

## v0_72 Oil-Conditioned Event Study Result

- Study module: `src/research/xauusd_oil_conditioned_event_study.py`
- Study script: `scripts/run_xauusd_oil_conditioned_event_study_v0_72.py`
- Study report: `reports/xauusd_oil_conditioned_event_study_v0_72.json`
- Study status: `oil_conditioned_event_study_completed_no_clear_leads`
- Source oil quality/design version: `v0_70`
- Source macro context board version: `v0_71`
- Selected proxy/fallback: `BRN` / `WTI`
- Labels evaluated: `oil_strength`, `oil_weakness`, `oil_shock_up`, `oil_shock_down`, `gold_oil_inflation_pressure_aligned`, `gold_oil_safe_haven_conflict`, `oil_supply_shock_context_candidate`
- Prior research versions considered: `v0_53`, `v0_56`, `v0_60`, `v0_63`, `v0_68`, `v0_71`
- Event count: `30`
- Clear lead count: `0`
- Strongest diagnostic observations: descriptive-only oil slices; no clear train/validation diagnostic lead
- Next recommended step: `v0_73_yield_real_yield_context_feasibility_no_strategy`
- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Lookahead risk detected: `false`

v0_72 is a diagnostic event study only. It does not approve oil labels as trade filters, blockers, entry rules, exit rules, signals, or recommendations.

## v0_71 Gold Macro Context Board Result

- Board module: `src/research/xauusd_gold_macro_context_board.py`
- Board script: `scripts/run_xauusd_gold_macro_context_board_v0_71.py`
- Board report: `reports/xauusd_gold_macro_context_board_v0_71.json`
- Board status: `gold_macro_context_board_completed`
- Source versions considered: `v0_65`, `v0_66`, `v0_67`, `v0_68`, `v0_68_1`, `v0_69`, `v0_70`
- DXY event-study result: `dxy_conditioned_event_study_completed_no_clear_leads`
- DXY selected proxy/fallback: `DXYN` / `USDX`
- DXY event count: `30`
- DXY clear lead count: `0`
- Oil selected proxy/fallback: `BRN` / `WTI`
- Oil quality scores: `BRN=121`, `WTI=118`
- Oil labels defined: `7`
- Oil event study completed: `false`
- Oil ready for diagnostic event study: `true`
- Macro context decision: `run_oil_conditioned_event_study_next`
- Next research step: `v0_72_oil_conditioned_event_study_no_strategy`
- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`

v0_71 is a macro-context decision board only. It does not create strategy rules, trade filters, blockers, signals, execution logic, OOS review, retune work, threshold search, parameter grids, or persistent aligned market CSV datasets.

## v0_70 Oil Proxy Quality and Label Design Result

- Design module: `src/research/xauusd_oil_proxy_quality_and_label_design.py`
- Design script: `scripts/run_xauusd_oil_proxy_quality_and_label_design_v0_70.py`
- Design report: `reports/xauusd_oil_proxy_quality_and_label_design_v0_70.json`
- Design status: `oil_proxy_quality_and_label_design_completed`
- Source oil audit version: `v0_69`
- Candidate symbols ranked: `BRN`, `WTI`
- Selected proxy symbol: `BRN`
- Fallback proxy symbol: `WTI`
- Selection reason: `BRN selected by highest deterministic quality score 121 using availability, timeframe support, overlap, gaps, timestamp integrity, OHLC validity, and safe as-of feasibility evidence. WTI kept as fallback with score 118.`
- Quality scores: `BRN=121`, `WTI=118`
- Safe as-of alignment feasible by symbol: `BRN=true`, `WTI=true`
- Selected proxy safe as-of alignment feasible: `true`
- Labels defined: `oil_strength`, `oil_weakness`, `oil_shock_up`, `oil_shock_down`, `gold_oil_inflation_pressure_aligned`, `gold_oil_safe_haven_conflict`, `oil_supply_shock_context_candidate`
- Label count: `7`
- Lookahead risk detected: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Next recommended step: `v0_71_gold_macro_context_board_no_strategy`

v0_70 is macro-context research infrastructure only. The labels are descriptive context definitions only and are not approved as strategy filters, blockers, entry rules, exit rules, signals, or recommendations.

## v0_69 Oil Proxy Context Audit Result

- Audit module: `src/research/xauusd_oil_proxy_context_audit.py`
- Audit script: `scripts/run_xauusd_oil_proxy_context_audit_v0_69.py`
- Audit report: `reports/xauusd_oil_proxy_context_audit_v0_69.json`
- Audit status: `oil_proxy_context_feasibility_completed`
- Candidate symbols checked: `UKOIL`, `XBRUSD`, `BRENT`, `BRENT.fs`, `BRN`, `USOIL`, `WTI`, `XTIUSD`
- Usable proxy symbols: `BRN`, `WTI`
- Selected proxy symbol: `BRN`
- Selected proxy timeframe: `M15`
- Selection reason: `BRN M15 selected by fixed candidate/timeframe order with parseable overlapping rows`
- MT5 read-only candidate symbols available: `BRN`, `WTI`
- MT5 copied rows total: `30000`
- Safe as-of alignment feasible: `true`
- Lookahead risk detected: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Labels used as trade blockers: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Targeted tests: `63 passed`
- Next recommended step: `v0_70_oil_proxy_quality_ranking_and_label_design`

v0_69 is a macro-context research infrastructure audit only. Future oil labels are schema candidates only and are not approved as strategy filters, blockers, entry rules, exit rules, or recommendations.

## v0_68_1 DXY Proxy Row Adapter Result

- Adapter module: `src/research/xauusd_dxy_proxy_quality_ranker.py`
- Diagnostic script: `scripts/diagnose_xauusd_dxy_proxy_rows_v0_68_1.py`
- Adapter report: `reports/xauusd_dxy_proxy_row_adapter_v0_68_1.json`
- Adapter status: `dxy_proxy_row_adapter_completed`
- Source quality ranker version: `v0_66`
- Source event study version: `v0_68`
- Symbols checked: `DXYN`, `DXYZ`, `GDXY`, `USDX`
- Selected parseable proxy symbol: `DXYN`
- Fallback proxy symbol: `null`
- v0_68 blocker root cause: `timestamp_conversion_mismatch`
- Shared adapter created or updated: `true`
- Event study updated to use shared adapter: `true`
- Safe as-of alignment possible after adapter: `true`
- DXYN M15 copied rows: `10000`
- DXYN M15 parseable rows: `10000`
- DXYN first timestamp: `2021-09-15T18:30:00`
- DXYN last timestamp: `2024-10-02T23:00:00`
- All checked M15 symbols parseable: `true`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Lookahead risk detected: `false`
- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Targeted tests: `71 passed`
- Adapter next recommended step: `rerun_v0_68_dxy_conditioned_event_study_with_shared_adapter`

v0_68_1 diagnoses the handoff failure between v0_66 and v0_68 as `timestamp_conversion_mismatch`. The current read-only MT5 M15 rows for `DXYN`, `DXYZ`, `GDXY`, and `USDX` are present and parseable through the shared adapter, with no invalid OHLC, duplicate timestamps, or non-monotonic timestamp ordering.

After wiring v0_68 to the shared adapter, `reports/xauusd_dxy_conditioned_event_study_v0_68.json` reran with `study_status=dxy_conditioned_event_study_completed_no_clear_leads`, `event_count=30`, and `clear_lead_count=0`. This remains diagnostic-only context work and does not approve labels as trade blockers or filters.

## v0_68 DXY-Conditioned Event Study Result

- Study module: `src/research/xauusd_dxy_conditioned_event_study.py`
- Study script: `scripts/run_xauusd_dxy_conditioned_event_study_v0_68.py`
- Study report: `reports/xauusd_dxy_conditioned_event_study_v0_68.json`
- Study status: `dxy_conditioned_event_study_completed_no_clear_leads`
- Source proxy ranker version: `v0_66`
- Source label design version: `v0_67`
- Selected proxy symbol: `DXYN`
- Secondary proxy symbol: `USDX`
- Prior research versions considered: `v0_53`, `v0_56`, `v0_60`, `v0_63`
- Labels evaluated: `dxy_strength`, `dxy_weakness`, `dxy_shock_up`, `dxy_shock_down`, `gold_dxy_normal_inverse_behavior`, `gold_dxy_decoupling`, `dxy_gold_pressure_aligned`, `dxy_gold_pressure_conflict`
- Event count: `30`
- Clear lead count: `0`
- Blocker: none
- Proxy adapter version: `v0_68_1`
- DXYN M15 copied rows: `10000`
- DXYN M15 parseable rows: `10000`
- Lookahead risk detected: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Targeted tests: `71 passed` in the v0_68_1 combined targeted run
- Next recommended step: `v0_69_yield_or_brent_context_feasibility_before_new_strategy`

v0_68 considers the requested prior train/validation research versions and uses DXYN from v0_66 plus the v0_67 label definitions. After v0_68_1, the event study uses the shared proxy row adapter and no longer fails closed on DXYN M15 row parsing. It completed as a diagnostic-only no-clear-leads study with no aligned dataset export.

## v0_67 DXY Regime Label Design Result

- Label design module: `src/research/xauusd_dxy_regime_label_design.py`
- Label design script: `scripts/run_xauusd_dxy_regime_label_design_v0_67.py`
- Label design report: `reports/xauusd_dxy_regime_label_design_v0_67.json`
- Label design status: `dxy_regime_label_design_completed`
- Source proxy ranker version: `v0_66`
- Selected proxy symbol: `DXYN`
- Secondary proxy symbol: `USDX`
- Labels defined: `dxy_strength`, `dxy_weakness`, `dxy_shock_up`, `dxy_shock_down`, `gold_dxy_normal_inverse_behavior`, `gold_dxy_decoupling`, `dxy_gold_pressure_aligned`, `dxy_gold_pressure_conflict`
- Label count: `8`
- Sample label counts if available: `{}`
- Safe as-of alignment required: `true`
- Lookahead risk detected: `false`
- Labels used as trade blockers: `false`
- Labels used for strategy testing: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Targeted tests: `61 passed`
- Next recommended step: `v0_68_dxy_conditioned_event_study_no_strategy_if_labels_pass`

v0_67 defines labels only. It records required input fields, timeframe applicability, safe backward as-of alignment, no-lookahead requirements, intended interpretation, and the warning that labels are descriptive context only, not an entry, exit, sizing rule, filter, blocker, or recommendation.

No persistent aligned market CSV was created, no `data/*.csv` file was touched, and optional sample counts remain aggregate-only and in memory.

## v0_66 DXY Proxy Quality Ranker Result

- Ranker module: `src/research/xauusd_dxy_proxy_quality_ranker.py`
- Ranker script: `scripts/run_xauusd_dxy_proxy_quality_ranker_v0_66.py`
- Ranker report: `reports/xauusd_dxy_proxy_quality_ranker_v0_66.json`
- Ranker status: `dxy_proxy_quality_ranking_completed`
- Source audit version: `v0_65`
- Candidate symbols ranked: `DXYN`, `DXYZ`, `GDXY`, `USDX`
- Selected proxy symbol: `DXYN`
- Selection reason: `DXYN selected because it has the highest safe proxy quality score`
- Ranking order: `DXYN` score `84`, `USDX` score `78`, `DXYZ` score `66`, `GDXY` score `66`
- Safe as-of alignment feasible by symbol: `DXYN=true`, `DXYZ=true`, `GDXY=true`, `USDX=true`
- Selected proxy safe as-of alignment feasible: `true`
- Lookahead risk detected: `false`
- Aligned dataset created: `false`
- Data CSV touched: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Targeted tests: `60 passed`
- Next recommended step: `v0_67_dxy_regime_label_design_if_proxy_quality_passes`

v0_66 ranks the v0_65 DXY/USD proxy candidates using fixed deterministic quality scoring. It does not assume the v0_65 selected proxy remains best: `DXYN` remains selected because it won the score, while fixed candidate order is reserved only for exact score ties.

The as-of alignment design is in-memory only and requires backward joins where proxy timestamps are less than or equal to XAUUSD timestamps. No aligned CSV was exported, no trade labels became blockers, and no strategy/trade/execution path was created.

## v0_65 DXY Proxy Context Audit Result

- Audit module: `src/research/xauusd_dxy_proxy_context_audit.py`
- Audit script: `scripts/run_xauusd_dxy_proxy_context_audit_v0_65.py`
- Audit report: `reports/xauusd_dxy_proxy_context_audit_v0_65.json`
- Audit status: `dxy_proxy_context_feasibility_completed`
- Candidate symbols checked: `DXYN`, `DXYZ`, `GDXY`, `USDX`
- Usable proxy symbols: `DXYN`, `DXYZ`, `GDXY`, `USDX`
- Selected proxy symbol: `DXYN`
- XAUUSD timeframes available: `M1`, `M5`, `M10`, `M15`
- Proxy timeframes available: `M5`, `M15` for each usable candidate via MT5 read-only discovery
- Safe as-of alignment feasible: `true`
- Lookahead risk detected: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Data CSV added to git: `false`
- Targeted tests: `59 passed`
- Next recommended step: `v0_66_dxy_asof_alignment_if_proxy_feasible`

v0_65 audits whether the prior v0_61 candidate DXY/USD proxy symbols can be observed through local files or MT5 read-only market data and safely aligned with XAUUSD without lookahead. The current environment exposed all four candidates through read-only MT5 copy-rates access with overlapping M5/M15 windows. This is not a trading rule, not a trade filter, not a strategy test, and not approval to proceed to OOS or execution.

## v0_64_2 Repository Cleanup Boundary Repair Result

- Pytest config: `pytest.ini`
- Repair report: `reports/repository_cleanup_repair_v0_64_2.json`
- Repair status: `cleanup_boundary_repair_completed`
- Project archive excluded from pytest collection: `true`
- Restored active dependency count: `14`
- Active tests import check passed: `true`
- Full pytest: `364 passed`
- Data CSV touched: `false`
- Safety files touched: `false`
- Latest context files touched: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Next recommended step: `commit_v0_63_to_v0_64_2_then_v0_65_dxy_proxy_context_audit`

v0_64_2 treats `project_archive/retired_v0_64_1` as archived historical evidence, not an active pytest surface. It also protects active dependency files through `active_dependency_keep` so the cleanup applier does not re-archive modules, active CLI scripts, or fixture reports still required by root tests and safety/context tooling.

## v0_64_1 Repository Cleanup Applied Result

- Cleanup module: `src/research/repository_cleanup_applier.py`
- Cleanup script: `scripts/apply_repository_cleanup_v0_64_1.py`
- Cleanup report: `reports/repository_cleanup_applied_v0_64_1.json`
- Cleanup status: `cleanup_applied_completed`
- Archive root: `project_archive/retired_v0_64_1`
- Files archived: `298`
- Cache paths deleted: `172`
- Files preserved: `232`
- Manual-review paths skipped: `11`
- Archive candidates remaining: `0`
- Cache candidates remaining: `0`
- Data CSV touched: `false`
- Safety files touched: `false`
- Latest context files touched: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Targeted tests before apply: `61 passed`
- Post-apply CLIs: `scripts/print_codex_context.py --json` passed; `scripts/project_health_check.py --json` passed
- Next recommended step: `v0_65_dxy_proxy_context_audit_after_cleanup`

v0_64_1 used the v0_64 plan as its source, then applied active dependency protections for current health/context tooling before archiving. It moved historical/generated artifacts under `project_archive/retired_v0_64_1` with relative paths preserved, deleted cache paths only, skipped manual-review paths, and did not touch CSV data.

## v0_64 Repository Consolidation Plan Result

- Planner module: `src/research/repository_consolidation_plan.py`
- Planner script: `scripts/build_repository_consolidation_plan_v0_64.py`
- Planner report: `reports/repository_consolidation_plan_v0_64.json`
- Consolidation status: `repository_consolidation_plan_completed`
- Files scanned: `666`
- Active keep count: `189`
- Archive candidate count: `305`
- Delete candidate count: `170`
- Manual review count: `11`
- Tracked data CSV files: `data/xauusd_m15_xauusd_2023-01-01_2026-06-11.csv`
- Cache files detected: `170`
- Failed experiments indexed: `22`
- Safe to apply cleanup now: `false`
- Cleanup requires human review: `true`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Trade recommendation output: `false`
- Targeted tests: `55 passed`
- Next recommended step: `v0_64_1_apply_reviewed_cleanup_plan_no_strategy_changes`

v0_64 is a cleanup planning checkpoint only. It documents active keep surfaces, historical archive candidates, retired experiment candidates, generated report archive candidates, local data files, cache delete candidates, and manual-review paths. It applies no cleanup and preserves failed experiment evidence in `docs/retired_experiments_archive.md` and `project_memory/failed_strategy_registry.md`.

## v0_63 Context-Labeled Event Study Result

- Study module: `src/research/xauusd_context_labeled_event_study.py`
- Study script: `scripts/run_xauusd_context_labeled_event_study_v0_63.py`
- Study report: `reports/xauusd_context_labeled_event_study_v0_63.json`
- Study status: `context_labeled_event_study_completed_no_clear_leads`
- Source labeler version: `v0_62`
- Source prior versions considered: `v0_53`, `v0_56`, `v0_60`
- Labels used as trade blockers: `false`
- Strategy rules changed: `false`
- Gates lowered: `false`
- Strongest context-conditioned leads: none
- Revived candidate allowed: `false`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `53 passed`
- Next recommended step: `add external datasets such as holiday/economic calendar/DXY before further context testing.`

v0_63 is retrospective analysis only. It recomputes the previously tested fixed-rule train/validation outcomes, attaches v0_62 timestamp-only labels, and summarizes context-conditioned behavior without changing rules or turning labels into blockers.

No context-conditioned lead satisfied the required validation sample, train/validation consistency, PF, expectancy, and concentration checks. Prior rejected branches remain rejected do-not-retune.

## v0_62 Market Context Labeler Result

- Labeler module: `src/research/xauusd_market_context_labeler.py`
- Labeler script: `scripts/build_xauusd_market_context_labels_v0_62.py`
- Labeler report: `reports/xauusd_market_context_labels_v0_62.json`
- Labeler status: `market_context_labeler_completed`
- Source feasibility version: `v0_61`
- Purpose: `observational_market_context_labels_only`
- Labels are trade blockers: `false`
- Hard blockers limited to market closed and missing data: `true`
- Timestamp basis: `local_csv_timestamp_no_timezone_column`
- Timeframes used: `M10`, `M15`, `M5`
- Total timestamp rows labeled: `399509`
- Market closed weekend count: `0`
- Likely market open count: `399509`
- Asian session count: `105668`
- London morning session count: `87208`
- NY core session count: `87344`
- Late US session count: `69849`
- Off-session or low-activity count: `49440`
- DXY placeholder status: `placeholder_schema_defined_no_dxy_series_imported`
- Yields placeholder status: `placeholder_schema_defined_no_yields_series_imported`
- Calendar placeholder status: `placeholder_schema_defined_no_economic_calendar_imported`
- Holiday placeholder status: `placeholder_schema_defined_no_holiday_calendar_imported`
- Approved for strategy testing: `false`
- Approved for trade filtering: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `53 passed`
- Next recommended step: `v0_63 context-labeled event study, no strategy, no OOS`

v0_62 is an observational labeler skeleton only. It reads existing local XAUUSD timestamps and creates descriptive market/session/time labels plus placeholder external label schemas. Holiday, news/event, DXY, yields, geopolitical, and session labels are not trade blockers in v0_62.

## v0_61 Market Context Layer Feasibility Result

- Audit module: `src/research/xauusd_market_context_feasibility_audit.py`
- Audit script: `scripts/audit_xauusd_market_context_feasibility_v0_61.py`
- Audit report: `reports/xauusd_market_context_feasibility_v0_61.json`
- Audit status: `market_context_feasibility_completed`
- Purpose: `market_context_layer_feasibility_only`
- Source previous board version: `v0_60`
- Pure OHLC branch status: `no_second_tier_candidate_passed`
- Market context families audited: `market_open_closed_session_state`, `holiday_reduced_liquidity_calendar`, `economic_calendar_event_timestamps`, `dxy_usd_proxy`, `us_yields_rates_proxy`, `geopolitical_macro_risk_labels`, `technical_permission_gate`
- Market open/closed feasibility: `feasible_for_weekend_and_session_labels_from_timestamps`
- Holiday calendar feasibility: `schema_defined_external_dataset_required`
- Economic calendar feasibility: `schema_defined_external_dataset_required`
- DXY/USD proxy feasibility: `mt5_candidate_symbol_discovery_only_external_or_broker_data_required`
- DXY/USD proxy candidate symbols discovered: `DXYN`, `DXYZ`, `GDXY`, `USDX`
- US yields/rates proxy feasibility: `mt5_candidate_symbol_discovery_only_external_offline_data_required_if_unavailable`
- US yields/rates proxy candidate symbols discovered: none
- Approved for v0_62 feature import: `false`
- Approved for strategy testing: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Targeted tests: `59 passed`
- Next recommended step: `v0_62 controlled read-only market context data importer design, no strategy, no OOS`

v0_61 is a feasibility audit only. It defines the future Market Context Gate before technical setup work and documents schemas, source requirements, anti-lookahead rules, and alignment policy. No external datasets were imported, and MT5 symbol discovery was read-only candidate metadata only.

## v0_60 Second-Tier Fixed-Rule Board Result

- Board module: `src/research/xauusd_second_tier_fixed_rule_board.py`
- Board script: `scripts/run_xauusd_second_tier_board_v0_60.py`
- Board report: `reports/xauusd_second_tier_board_v0_60.json`
- Board status: `no_second_tier_candidate_passed`
- Source standardization version: `v0_59`
- Tested candidate ids: `failed_m15_swing_breakout_reversal`, `ny_liquidity_sweep_reversal`, `sequential_m5_move_mean_reversion`
- Best candidate id: `ny_liquidity_sweep_reversal`
- Best candidate passed gate: `false`
- Best train profit factor: `0.7656489689036846`
- Best train expectancy: `-0.21007613604144268`
- Best train trades: `270`
- Best validation profit factor: `1.7101588243682602`
- Best validation expectancy: `0.5567402891905258`
- Best validation trades: `43`
- Rejected do-not-retune candidates: `failed_m15_swing_breakout_reversal`, `ny_liquidity_sweep_reversal`, `sequential_m5_move_mean_reversion`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Gates lowered: `false`
- Past metrics changed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Timestamp basis reported: `true`
- Targeted tests: `53 passed`
- Next recommended step: `broaden non-OOS research or consider adding external features such as DXY/yields/news calendar before further strategy tests.`

v0_60 evaluated exactly the three requested second-tier fixed-rule ideas under the v0_59 standardized lab policies. No candidate passed the fixed train/validation gate. No OOS run, repeated OOS review, retune, threshold search, parameter grid, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, profitability claim, or `data/*.csv` addition was introduced.

## v0_59 Research Lab Warning Standardization Result

- Standardization module: `src/research/xauusd_research_lab_warning_standardization.py`
- Standardization script: `scripts/standardize_xauusd_research_lab_warnings_v0_59.py`
- Standardization report: `reports/xauusd_research_lab_warning_standardization_v0_59.json`
- Standardization status: `lab_warning_standardization_completed`
- Source integrity audit version: `v0_58`
- Source integrity decision: `lab_integrity_passed_with_warnings`
- Critical findings from v0_58: none
- Warnings addressed: M5/M10/M15 gap and zero-range warnings, timestamp-basis warning, cost/slippage consistency warning, and low-frequency validation-floor caveat
- Cost policy documented: `true`
- Timestamp/session policy documented: `true`
- Gap classification policy documented: `true`
- Gate policy documented: `true`
- Low-frequency false-negative risk documented: `true`
- Strategy metrics changed: `false`
- Gates lowered: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Policy docs: `docs/research_lab_cost_policy.md`, `docs/research_lab_timestamp_and_session_policy.md`, `docs/research_lab_gap_classification_policy.md`, `docs/research_lab_gate_policy.md`
- Targeted tests: `53 passed`
- Next recommended step: `continue research with standardized lab policies.`

v0_59 standardizes lab warning policy only. It does not change strategy results, lower gates, retune, search thresholds, run a parameter grid, run OOS, create an executable candidate, enable demo/live execution, send orders, check orders, create a scheduler, create an execution queue, output a user-facing trade recommendation, claim profitability, or add `data/*.csv`.

## v0_58 Research Lab Integrity Audit Result

- Audit module: `src/research/xauusd_research_lab_integrity_audit.py`
- Audit script: `scripts/audit_xauusd_research_lab_integrity_v0_58.py`
- Audit report: `reports/xauusd_research_lab_integrity_audit_v0_58.json`
- Audit status: `lab_integrity_completed`
- Purpose: `research_lab_integrity_diagnostic_not_strategy`
- Lab integrity decision: `lab_integrity_passed_with_warnings`
- Critical findings: none
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Primary data counts: `M5=212368`, `M10=106117`, `M15=81024`
- Duplicate timestamps: `0` on all primary datasets
- Invalid OHLC rows: `0` on all primary datasets
- Split boundaries chronological: `true`
- OOS rows excluded from train/validation tools: `true`
- Trade accounting synthetic fixtures: all passed
- Same-candle stop/target handling: conservative stop-first
- Prior report safety flags: valid for v0_53, v0_56, and v0_57
- Targeted tests: `54 passed`
- Next recommended step: `address warnings or continue research with caution.`

Warnings remain for reported M5/M10/M15 candle gaps and zero/negative ranges, missing explicit broker timestamp basis, inconsistent cost/slippage application across tools, and potential false-negative risk from applying the fixed validation trade-count floor to low-frequency families.

No OOS run, repeated OOS review, retune, threshold search, parameter grid, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, profitability claim, or `data/*.csv` addition was introduced.

## v0_57 Volatility Regime Lead Viability Result

- Audit module: `src/research/xauusd_volatility_regime_lead_viability_audit.py`
- Audit script: `scripts/audit_xauusd_volatility_regime_lead_v0_57.py`
- Audit report: `reports/xauusd_volatility_regime_lead_viability_v0_57.json`
- Audit status: `volatility_lead_viability_completed`
- Source profiler version: `v0_54`
- Source design version: `v0_55`
- Source rejected eval version: `v0_56`
- Lead id: `volatility_regime_profile`
- Session block branch rejected: `true`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Validation sample sufficiency: `sufficient`
- Fixed elevated-regime validation observations: `116`
- Can produce at least 50 validation trades under fixed rules: `true`
- Candidate design feasibility: `false`
- Volatility lead viability decision: `volatility_lead_unstable_or_too_weak_reject`
- Recommended v0_58 candidate design: `{}`
- Sample concentration risk: `high`
- Concentration warning: `validation_fixed_elevated_regime_observations_concentrated_in_single_year`
- Targeted tests: `48 passed`
- Next recommended step: `stop profiler-lead branch or broaden non-OOS research.`

v0_57 is a viability audit only. The v0_54 volatility-regime lead had enough fixed elevated-regime validation observations and same-sign train/validation behavior, but the validation sample is concentrated in a single year and train/validation dominant regimes differ. No v0_58 fixed-rule candidate was recommended.

No OOS run, repeated OOS review, retune, threshold search, parameter grid, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, profitability claim, or `data/*.csv` addition was introduced.

## v0_56 Session Block Directional Bias Evaluation Result

- Evaluation module: `src/research/xauusd_session_block_directional_bias_evaluation.py`
- Evaluation script: `scripts/run_xauusd_session_block_bias_eval_v0_56.py`
- Evaluation report: `reports/xauusd_session_block_bias_eval_v0_56.json`
- Evaluation status: `session_block_candidate_rejected`
- Source design version: `v0_55`
- Source profiler version: `v0_54`
- Candidate id: `session_block_directional_bias_candidate`
- Candidate rules preserved: `true`
- Evaluated candidate count: `1`
- Other v0_55 candidates evaluated: `false`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Train profit factor: `1.944079700461015`
- Train expectancy: `0.12169806372142332`
- Train trades: `34`
- Validation profit factor: `0.0`
- Validation expectancy: `-0.38490466623989666`
- Validation trades: `3`
- Candidate passed train/validation gate: `false`
- Candidate locking allowed pre-OOS: `false`
- Rejected do not retune: `true`
- Gate blockers: `validation_profit_factor_below_fixed_gate`, `validation_trades_below_fixed_gate`, `validation_expectancy_not_positive`, `validation_profit_factor_less_than_0_75_train_profit_factor`
- Sample concentration risk: `high`
- Targeted tests: `47 passed`
- Next recommended step: `stop session_block branch or return to profiler leads.`

v0_56 evaluated exactly one fixed-rule candidate from v0_55: `session_block_directional_bias_candidate`. The candidate failed the required validation gates and remains non-executable. No OOS run, repeated OOS review, retune, threshold search, parameter grid, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_55 Session/Volatility Candidate Design Result

- Design module: `src/research/xauusd_session_volatility_candidate_design_board.py`
- Design script: `scripts/run_xauusd_session_volatility_design_v0_55.py`
- Design report: `reports/xauusd_session_volatility_design_v0_55.json`
- Design status: `session_volatility_design_completed_with_v0_56_candidate`
- Source profiler version: `v0_54`
- Source profiler status: `edge_profile_completed_with_research_leads`
- Profiler leads used: `session_return_profile`, `volatility_regime_profile`
- Candidate design count: `4`
- Recommended candidate for v0_56: `session_block_directional_bias_candidate`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Executable candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `45 passed`
- Next recommended step: `v0_56 fixed-rule train/validation evaluation for session_block_directional_bias_candidate only, no OOS`

v0_55 is a design board only. It converts the two strongest v0_54 leads into fixed hypotheses and recommends exactly one train/validation-only evaluation candidate for v0_56.

No OOS run, repeated OOS review, retune, threshold search, parameter grid, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_54 XAUUSD Edge Profiler Result

- Profiler module: `src/research/xauusd_edge_profiler.py`
- Profiler script: `scripts/run_xauusd_edge_profiler_v0_54.py`
- Profiler report: `reports/xauusd_edge_profiler_v0_54.json`
- Profiler status: `edge_profile_completed_with_research_leads`
- Source previous board version: `v0_53`
- Purpose: `empirical_edge_mapping_not_strategy_backtest`
- Event families profiled: `session_return_profile`, `prior_day_high_low_sweep_profile`, `asian_range_breakout_profile`, `london_opening_candle_profile`, `ny_first_hour_profile`, `failed_m15_swing_breakout_profile`, `sequential_m5_move_profile`, `volatility_regime_profile`
- Strongest empirical leads: `session_return_profile`, `volatility_regime_profile`
- Recommended v0_55 research plan: `v0_55 fixed-rule candidate design for session_return_profile using predeclared train/validation-only rules; no OOS`; `v0_55 fixed-rule candidate design for volatility_regime_profile using predeclared train/validation-only rules; no OOS`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `47 passed`
- Next recommended step: `v0_55 fixed-rule candidate design for top 1-2 leads, no OOS`

v0_54 is an empirical profiler only. It maps descriptive train/validation event-family behavior and does not create an executable strategy candidate, run OOS, retune, search thresholds, search parameter grids, make a profitability claim, or emit a user-facing trade recommendation.

No demo/live execution, order sending, order checking, scheduler, execution queue, or `data/*.csv` addition was introduced.

## v0_53 External Shortlist Train/Validation Board Result

- Board module: `src/research/xauusd_external_shortlist_train_validation_board.py`
- Board script: `scripts/run_xauusd_external_shortlist_board_v0_53.py`
- Board report: `reports/xauusd_external_shortlist_board_v0_53.json`
- Board status: `no_external_shortlist_candidate_passed`
- Source triage versions: `v0_52`, `v0_52_1`
- Tested candidate ids: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Best candidate id: `asian_range_london_breakout_confirmation`
- Best candidate passed gate: `false`
- Best train profit factor: `1.0107152929889043`
- Best train expectancy: `0.005028872470589754`
- Best train trades: `497`
- Best validation profit factor: `1.1330238648738264`
- Best validation expectancy: `0.053786897553678714`
- Best validation trades: `94`
- Rejected do-not-retune candidates: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `45 passed`
- Next recommended step: `broaden non-OOS research or stop current branch`

v0_53 implemented fixed M15 train/validation-only tests for the finalized external shortlist. The strongest fixed result was `asian_range_london_breakout_confirmation`, but no candidate passed the full fixed gate.

No OOS run, repeated OOS review, retune, threshold search, parameter grid, executable candidate creation, demo/live execution, order sending, order checking, scheduler, execution queue, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_52_1 Kimi External Idea Addendum Result

- Addendum module: `src/research/xauusd_kimi_external_idea_addendum.py`
- Addendum script: `scripts/run_xauusd_kimi_idea_addendum_v0_52_1.py`
- Addendum report: `reports/xauusd_kimi_external_idea_addendum_v0_52_1.json`
- Addendum status: `kimi_addendum_completed_shortlist_unchanged`
- Source triage version: `v0_52`
- Kimi added to external sources: `true`
- Kimi raw idea count: `10`
- Kimi deduplicated idea count: `5`
- Original v0_52 shortlist: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Final shortlist for v0_53: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Shortlist changed: `false`
- Top ranked idea id: `prior_day_liquidity_sweep_reversal`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Backtest implemented: `false`
- Candidate created: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `48 passed`
- Next recommended step: `use the unchanged v0_52 shortlist for v0_53 fixed-rule train/validation-only board design; keep Kimi addendum ideas as supplemental do-not-retune-aware notes`

v0_52_1 adds Kimi as an external idea source without changing the finalized v0_52 report. Kimi ideas were deduplicated or penalized where they overlapped opening-range, Asian/liquidity-sweep, v0_26 compression/expansion, VWAP, weekend gap, trend-pullback, or generic candle-pattern families.

The v0_52 shortlist remains unchanged because no Kimi idea materially beat the top three. No profitability claim was made.

No order sending, order checking, live trading, scheduler, execution queue, backtest implementation, candidate creation, retune, threshold search, parameter grid, OOS run, repeated OOS review, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_52 External Strategy Idea Intake Triage Result

- Triage module: `src/research/xauusd_external_strategy_idea_triage.py`
- Triage script: `scripts/run_xauusd_external_strategy_idea_triage_v0_52.py`
- Triage report: `reports/xauusd_external_strategy_idea_triage_v0_52.json`
- Triage status: `shortlist_ready_for_v0_53_non_oos_board`
- Total raw ideas: `10`
- Deduplicated idea count: `8`
- Top ranked idea id: `prior_day_liquidity_sweep_reversal`
- Shortlist for v0_53: `prior_day_liquidity_sweep_reversal`, `london_opening_range_breakout_or_first_candle_direction`, `asian_range_london_breakout_confirmation`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `43 passed`
- Next recommended step: `design v0_53 fixed-rule train/validation-only board for the shortlisted ideas; no OOS, retune, threshold search, parameter grid, or execution`

v0_52 is intake and triage only. It did not evaluate profitability, did not create a strategy candidate, did not implement a backtest, and did not promote any branch.

No order sending, order checking, live trading, scheduler, execution queue, strategy evaluation, backtest implementation, candidate creation, retune, threshold search, parameter grid, OOS run, repeated OOS review, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_51 Trend Pullback Expanded Retest Result

- Retest module: `src/research/xauusd_trend_pullback_expanded_retest.py`
- Retest script: `scripts/run_xauusd_trend_pullback_expanded_retest_v0_51.py`
- Retest report: `reports/xauusd_trend_pullback_expanded_retest_v0_51.json`
- Retest status: `expanded_evidence_failed`
- Candidate id: `trend_pullback_continuation_directional`
- Source candidate board version: `v0_48`
- Source stability audit version: `v0_49`
- Source data feasibility version: `v0_50`
- Candidate rules preserved: `true`
- Expanded range: `2019-01-02T06:00:00` to `2022-12-30T21:55:00`
- Train/validation-equivalent only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Candle count by timeframe: `M5=281152`, `M10=141464`
- Expanded trade count: `230`
- Expanded profit factor: `1.1861259380980205`
- Expanded expectancy: `0.0574451807402551`
- Sample concentration risk: `low`
- Expanded evidence passed gate: `false`
- Candidate locking allowed pre-OOS: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `41 passed`
- Next recommended step: `stop trend_pullback branch or broaden non-OOS research`

v0_51 retested the exact fixed v0_48 `trend_pullback_continuation_directional` rule on the older range made feasible by v0_50. This was expanded train/validation-equivalent evidence only, not OOS, not a retune, and not a parameter or threshold search.

The expanded sample reached `230` trades across `4` calendar years and reduced concentration risk to `low`, but the expanded profit factor was `1.1861259380980205`, below the fixed `1.20` gate. Candidate locking, OOS, demo execution, and live execution remain blocked.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_50 Historical Data Expansion Feasibility Result

- Audit module: `src/research/xauusd_historical_data_expansion_feasibility_audit.py`
- Audit script: `scripts/audit_xauusd_historical_data_expansion_v0_50.py`
- Audit report: `reports/xauusd_historical_data_expansion_feasibility_v0_50.json`
- Audit status: `expansion_data_partially_available`
- Symbol: `XAUUSD`
- Requested range: `2019-01-01` to `2022-12-31`
- MT5 read-only: `true`
- MT5 initialized: `true`
- MT5 shutdown called: `true`
- Available oldest candle time: `2019-01-02T06:00:00`
- Available newest candle time: `2022-12-30T23:55:00`
- Requested range available: `false`
- Candle count by timeframe: `M5=281176`, `M10=141476`
- Missing range gap count: `2086`
- Missing range gaps truncated in report: `true`
- Data expansion feasible: `true`
- Candidate to retest later: `trend_pullback_continuation_directional`
- Candidate rules preserved: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Data CSV added to git: `false`
- Targeted tests: `37 passed`
- Next recommended step: `v0_51 fixed-rule expanded train/validation retest on available older range only, no OOS`

v0_50 used MT5 read-only data availability checks only. The full requested range is not complete, but there is enough available older low-timeframe data to justify a fixed-rule expanded train/validation retest. No CSV files were exported or added to git.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_49 Trend Pullback Sample Stability Audit Result

- Audit module: `src/research/xauusd_trend_pullback_sample_stability_audit.py`
- Audit script: `scripts/audit_xauusd_trend_pullback_stability_v0_49.py`
- Audit report: `reports/xauusd_trend_pullback_stability_audit_v0_49.json`
- Source board version: `v0_48`
- Candidate id: `trend_pullback_continuation_directional`
- Candidate rules preserved: `true`
- Audit status: `completed`
- Train/validation only: `true`
- OOS used: `false`
- Repeated OOS review: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Train profit factor: `1.8816690460357557`
- Train expectancy: `0.2045491371207446`
- Train trades: `164`
- Validation profit factor: `4.1448723516886234`
- Validation expectancy: `0.4564440182058163`
- Validation trades: `16`
- Validation trade minimum: `25`
- Validation trade count passed: `false`
- Sample concentration risk: `high`
- Fixed 0.05R cost edge broken: `false`
- Stability decision: `promising_but_insufficient_validation_sample`
- Candidate locking allowed pre-OOS: `false`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `38 passed`
- Next recommended step: `collect more train/validation-equivalent evidence or stop; do not lock candidate or run OOS`

v0_49 reconstructed the v0_48 fixed trend-pullback candidate on existing train/validation data only. It matched the v0_48 source metrics and did not modify candidate rules.

The candidate remains promising but insufficient: validation PF and expectancy are strong, and fixed cost sensitivity does not break the edge, but validation has only `16` trades versus the fixed `25` minimum. Candidate locking, OOS, demo execution, and live execution remain blocked.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_48 New Directional Strategy Discovery Result

- Board module: `src/research/xauusd_new_directional_strategy_discovery_board.py`
- Board script: `scripts/run_xauusd_new_directional_discovery_v0_48.py`
- Board report: `reports/xauusd_new_directional_discovery_v0_48.json`
- Prior path closed: `xauusd_compression_then_expansion_v0_26`
- Prior path closure reason: `no_executable_direction_rule_and_v0_47_direction_board_failed`
- Board status: `no_new_directional_candidate_passed`
- Train/validation only: `true`
- OOS used: `false`
- Directional families evaluated: `session_open_range_breakout_directional`, `prior_block_breakout_continuation_directional`, `failed_breakout_reversal_directional`, `trend_pullback_continuation_directional`
- Best candidate id: `trend_pullback_continuation_directional`
- Best candidate passed gate: `false`
- Best train profit factor: `1.8816690460357557`
- Best train expectancy: `0.2045491371207446`
- Best validation profit factor: `4.1448723516886234`
- Best validation trades: `16`
- Best validation expectancy: `0.4564440182058163`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `39 passed`
- Next recommended step: `stop current research branch or create a broader non-OOS research plan`

v0_48 evaluated four fixed inherently directional families on existing train/validation data only. No OOS rows were used, no thresholds or parameter grids were searched, and no retune was performed.

No new family passed the fixed board gate. The strongest failed family, `trend_pullback_continuation_directional`, failed only on validation trade count: `16` trades versus the required `25`. All rejected candidates remain `rejected_do_not_retune`.

No order sending, order checking, live trading, scheduler, execution queue, v0_26 candidate-rule change, retune, threshold search, parameter grid, OOS run, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_47 Executable Direction Research Board Result

- Board module: `src/research/xauusd_executable_direction_research_board.py`
- Board script: `scripts/run_xauusd_direction_research_board_v0_47.py`
- Board report: `reports/xauusd_direction_research_board_v0_47.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Board status: `no_direction_candidate_passed`
- Source filter preserved: `true`
- Train/validation only: `true`
- OOS used: `false`
- Direction hypotheses evaluated: `expansion_continuation_close_direction`, `first_breakout_m5_confirmed_by_m10`, `response_block_body_direction`, `expansion_fade_direction`
- Best candidate id: `expansion_fade_direction`
- Best candidate passed gate: `false`
- Best train profit factor: `0.95235467842927`
- Best train expectancy: `-0.02935974061341059`
- Best validation profit factor: `1.1857423708051282`
- Best validation trades: `139`
- Best validation expectancy: `0.0739936548925565`
- Demo execution allowed: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `37 passed`
- Next recommended step: `stop this path or design a new non-OOS research candidate`

v0_47 treated the locked v0_26 candidate as a non-executable market-state filter and evaluated only four fixed direction hypotheses on train/validation rows. No hypothesis passed the predeclared gate, so no locked directional candidate was created and demo execution remains blocked.

No order sending, order checking, live trading, scheduler, execution queue, v0_26 candidate-rule change, retune, threshold search, parameter grid, repeated OOS, user-facing trade recommendation, or `data/*.csv` addition was introduced.

## v0_46 Candidate Direction Provenance Audit Result

- Audit module: `src/research/xauusd_candidate_direction_provenance_audit.py`
- Audit script: `scripts/audit_xauusd_candidate_direction_v0_46.py`
- Audit report: `reports/xauusd_candidate_direction_provenance_v0_46.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Audit status: `no_direction_rule_found_execution_blocked`
- Direction rule found: `false`
- Executable side mapping found: `false`
- Direction provenance confidence: `none`
- Demo execution direction ready: `false`
- Blockers: `locked_candidate_has_no_executable_side_mapping`, `locked_candidate_has_no_explicit_direction_rule`
- Warning: `next_block_expansion_behavior_found_but_not_executable_direction_rule`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Candidate rules preserved: `true`

v0_46 audited the existing locked v0_26 candidate artifacts and registry record. The artifacts contain fixed compression-then-expansion behavior provenance, but no deterministic executable internal side rule or side mapping. Demo execution direction readiness remains blocked.

No side was invented or inferred. No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, repeated OOS, or `data/*.csv` addition was introduced.

## v0_45_1 Direction Validity Guard Result

- Snapshot module: `src/execution/xauusd_live_signal_snapshot_provider.py`
- Builder module: `src/execution/xauusd_signal_to_order_request_builder.py`
- Executor module: `src/execution/xauusd_limited_demo_executor.py`
- Snapshot report: `reports/xauusd_live_signal_snapshot_v0_45.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Snapshot version: `v0_45_1`
- Snapshot status: `snapshot_ready_signal_confirmed_direction_unassigned`
- Signal qualified: `true`
- Signal reason: `locked_candidate_current_snapshot_expansion_confirmed_across_m5_m10`
- Direction assigned: `false`
- Direction source: `locked_candidate_no_deterministic_direction_rule`
- Executable side valid: `false`
- Order request present: `false`
- Order request complete: `false`
- Order request validation status: `direction_unassigned_non_executable`
- Invalid order request reasons: `direction_unassigned_non_executable`
- Review request present: `true`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`

v0_45_1 makes `direction_unassigned_review_only`, missing side values, empty side values, and unknown side values non-executable. The latest live snapshot still qualifies the locked v0_26 compression-expansion signal, but it does not report a complete order request because no deterministic executable internal side is assigned.

No order sending, order checking, live trading, scheduler, execution queue, candidate-rule change, retune, threshold search, parameter grid, repeated OOS, or `data/*.csv` addition was introduced.

## v0_45 Live Signal Snapshot Provider Result

- Snapshot module: `src/execution/xauusd_live_signal_snapshot_provider.py`
- Snapshot script: `scripts/build_xauusd_live_signal_snapshot_v0_45.py`
- Snapshot report: `reports/xauusd_live_signal_snapshot_v0_45.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Snapshot status: `snapshot_ready_order_request_built_dry_run_only`
- Timeframes requested: `M5`, `M10`
- Candles loaded: `M5=288`, `M10=144`
- Current signal snapshot present: `true`
- Signal evaluated: `true`
- Signal qualified: `true`
- Signal reason: `locked_candidate_current_snapshot_expansion_confirmed_across_m5_m10`
- Order request present: `true`
- Order request complete: `true`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- MT5 read-only: `true`
- MT5 initialized: `true`
- MT5 shutdown called: `true`
- Targeted tests: `45 passed`

v0_45 is read-only market data access only. It fetches the latest required M5/M10 candles, builds a structured `current_signal_snapshot`, and wires that snapshot into the v0_43 dry-run builder.

The latest report contains a complete internal dry-run order request for human review only. It did not call order sending, did not call order checking, did not enable live trading, did not create a scheduler, did not create an execution queue, did not change v0_26 candidate rules, did not retune, did not search thresholds, did not run a parameter grid, did not repeat OOS, did not output a user-facing trade recommendation, and did not add `data/*.csv`.

## v0_44_1 Real Interval Enforcement Result

- Watch module: `src/execution/xauusd_bounded_signal_watch_runner.py`
- Watch script: `scripts/run_xauusd_bounded_signal_watch_v0_44.py`
- Watch report: `reports/xauusd_bounded_signal_watch_v0_44.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Watch version: `v0_44_1`
- Watch status: `blocked_macro_event_window`
- Max cycles: `6`
- Interval seconds: `300`
- Cycles completed: `1`
- Stopped early: `true`
- Stop reason: `blocked_macro_event_window`
- Sleep enabled: `true`
- Sleep calls: `0`
- Total planned sleep seconds: `0`
- Interval seconds honored: `true`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `39 passed`

v0_44_1 enforces real foreground intervals by default. Normal CLI runs sleep for `--interval-seconds` between non-final cycles; `--no-sleep` is now the explicit test/dev bypass and reports `no_sleep_reason=explicit_no_sleep_flag`.

The latest report stopped on the active macro event window before any inter-cycle wait point, so `sleep_calls` is `0` while `sleep_enabled` and `interval_seconds_honored` remain `true`.

## v0_44 Bounded Signal Watch Runner Result

- Watch module: `src/execution/xauusd_bounded_signal_watch_runner.py`
- Watch script: `scripts/run_xauusd_bounded_signal_watch_v0_44.py`
- Watch report: `reports/xauusd_bounded_signal_watch_v0_44.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Watch status: `blocked_macro_event_window`
- Max cycles: `6`
- Interval seconds: `300`
- Cycles completed: `1`
- Stopped early: `true`
- Stop reason: `blocked_macro_event_window`
- Latest signal qualified: `false`
- Latest order request present: `false`
- Latest order request complete: `false`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Targeted tests: `36 passed`

v0_44 is a foreground, bounded, dry-run-only watch runner. It calls the v0_43 builder for at most the configured cycle count and stops early when the macro lock is active or a complete internal order request is ready for human review.

The default v0_44 report stopped on the active macro event window. No order request was built, and no execution path was called.

## v0_43 Signal-to-Order-Request Builder Result

- Builder module: `src/execution/xauusd_signal_to_order_request_builder.py`
- Builder script: `scripts/build_xauusd_signal_order_request_v0_43.py`
- Builder report: `reports/xauusd_signal_order_request_v0_43.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Builder status: `no_qualified_signal_now`
- Signal evaluated: `true`
- Signal qualified: `false`
- Signal reason: `no_current_signal_snapshot_supplied`
- Order request present: `false`
- Order request complete: `false`
- Order request validation status: `missing_order_request`
- Order send called: `false`
- Order check called: `false`
- Live allowed: `false`
- Macro event lock status: `clear_static_manual_windows`
- Targeted tests: `35 passed`

v0_43 is a dry-run-only internal builder. It converts a qualified locked v0_26 signal snapshot into a complete demo-only order request for review, or returns `no_qualified_signal_now`. The default report has no qualified signal and no order request.

The internal order request contract requires `symbol=XAUUSD`, `lot=0.01`, `demo_only=true`, side, order type, action, risk reference, stop loss or stop distance, take profit or exit rule, and candidate id `xauusd_compression_then_expansion_v0_26`.

## v0_42_1 Order Request Completeness Guard Result

- Executor module: `src/execution/xauusd_limited_demo_executor.py`
- Executor report: `reports/xauusd_limited_demo_execution_v0_42.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Executor status in regenerated default report: `dry_run_ready_no_order_sent`
- Explicit-send missing-request status: `blocked_missing_complete_order_request`
- Candidate rules preserved: `true`
- Demo only: `true`
- Live allowed: `false`
- Order request present in default report: `false`
- Order request complete in default report: `false`
- Order request validation status: `missing_order_request`
- Missing order request fields: `order_request`, `symbol`, `lot`, `demo_only`, `side`, `order_type`, `action`
- Order send attempted: `false`
- Order send called: `false`
- Order check called: `false`
- Targeted tests: `40 passed`

v0_42_1 hard-blocks the protected explicit demo order send path when `--allow-demo-order-send`, `--no-dry-run`, and the exact approval token are supplied without a complete explicit demo-only order request. Missing or incomplete request status is now `blocked_missing_complete_order_request`, not `demo_order_send_allowed_but_not_called`.

Required complete order request fields are symbol `XAUUSD`, fixed lot `0.01`, `demo_only=true`, explicit side field, explicit order type field, and explicit action field.

## v0_42 Limited Demo Execution Scaffold Result

- Executor module: `src/execution/xauusd_limited_demo_executor.py`
- Executor script: `scripts/run_xauusd_limited_demo_execution_v0_42.py`
- Executor report: `reports/xauusd_limited_demo_execution_v0_42.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Executor status: `dry_run_ready_no_order_sent`
- Mode: `dry_run`
- Candidate rules preserved: `true`
- Demo only: `true`
- Live allowed: `false`
- Default order send allowed: `false`
- Order send attempted: `false`
- Order send called: `false`
- Order check called: `false`
- Demo account verified: `true`
- Symbol verified: `true`
- Lot verified: `true`
- Risk envelope verified: `true`
- Readiness gate verified: `true`
- Macro event lock enabled: `true`
- Macro event lock status: `clear_static_manual_windows`
- Static macro window included: `2026-06-17 19:30` to `2026-06-17 22:30` `Africa/Tripoli`
- Approval token required: `true`
- Approval token valid in default run: `false`
- Blockers: none
- Warnings: none

v0_42 creates the first limited demo execution scaffold only. The default CLI path is dry-run and does not call order sending. Explicit future demo order sending requires the `--allow-demo-order-send` flag, a non-dry-run invocation, the exact human approval token, demo account verification, the locked v0_41 readiness decision, the fixed v0_40 risk envelope, symbol `XAUUSD`, lot `0.01`, and a clear static macro event lock.

The static macro event lock uses manual configured windows only. It includes FOMC/Fed Chair support and the default Libya-time blocked window for `2026-06-17 19:30` to `2026-06-17 22:30` `Africa/Tripoli`.

v0_42 did not execute an order, did not call order checking, did not permit live trading, did not create an automatic loop, did not create a background scheduler, did not use martingale, did not average into loss, did not scale positions, did not increase lots above `0.01`, did not retune, did not search thresholds, did not run a parameter grid, did not repeat OOS, did not create a new strategy, did not emit directional instructions, did not emit trade recommendations, and did not add any `data/*.csv`.

## v0_41 Final Demo Readiness Gate Result

- Gate report: `reports/xauusd_final_demo_readiness_gate_v0_41.json`
- Decision: `final_demo_readiness_gate_passed_pending_human_authorization`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Candidate rules preserved: `true`
- Final blockers: none
- Accepted warnings: `tick_value_contract_size_mismatch`
- Human authorization required: `true`
- Demo allowed: `false`
- Execution allowed: `false`
- Order send allowed: `false`
- Order check allowed: `false`

Fixed demo risk summary:

- Starting demo lot `0.01`
- Max demo lot `0.01`
- Max positions `1`
- Stop after `2` consecutive losses
- Max daily demo loss `2.0R`
- Max session demo loss `1.0R`
- No martingale, no averaging into loss, no position scaling

## Safety Boundary

- no live trading
- no real account trading
- no order sending by default
- no order checking in v0_42
- no automatic loop
- no background scheduler
- no execution queue
- no martingale
- no averaging into loss
- no position scaling
- no lot increase above `0.01`
- no recommendation output
- no directional output
- no threshold search or parameter grid
- no retune of rejected candidates
- no retune of the v0_26 compression-expansion candidate
- no repeated OOS review
- no OOS result-driven rule modification
