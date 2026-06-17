# Next Codex Handoff

- Current project: goldBotXAU
- Last completed checkpoint: v0_39 read-only broker facts audit
- OOS: evaluated once, marker locked, repeated review disallowed
- Current test baseline: 467 passed
- Health status: warnings only due to documented safety mentions
- Rejected candidate count: 6
- Eligible for OOS review count: 0
- Strategy status: no promoted strategy
- Execution status: disabled
- Latest candidate report: `reports/xauusd_compression_expansion_candidate_v0_26_train_validation.json`
- Latest gate report: `reports/xauusd_compression_expansion_promotion_gate_v0_27.json`
- Latest OOS review protocol: `reports/xauusd_oos_review_protocol_v0_28.json`
- Latest OOS review result: `reports/xauusd_oos_review_v0_29.json`
- Latest OOS review marker: `reports/xauusd_oos_review_v0_29.marker.json`
- Latest OOS repair report: `reports/xauusd_oos_review_repair_v0_29_1.json`
- Latest post-OOS governance report: `reports/xauusd_post_oos_governance_v0_30.json`
- Latest paper-shadow journal protocol: `reports/xauusd_paper_shadow_journal_protocol_v0_31.json`
- Latest forward observation export plan: `reports/xauusd_forward_observation_export_plan_v0_32.json`
- Latest forward observation runner protocol: `reports/xauusd_forward_observation_runner_protocol_v0_33.json`
- Latest forward observation journal report: `reports/xauusd_forward_observation_journal_v0_34.json`
- Latest forward observation schema adapter protocol: `reports/xauusd_forward_observation_schema_adapter_protocol_v0_34_1.json`
- Latest forward observation consolidated report: `reports/xauusd_forward_observation_consolidated_v0_34_2.json`
- Latest forward observation ledger report: `reports/xauusd_forward_observation_ledger_v0_35.json`
- Latest ready forward observation ledger report: `reports/xauusd_forward_observation_ledger_v0_36_cycle_2026-06-16.json`
- Latest forward observation cycle protocol: `reports/xauusd_forward_observation_cycle_protocol_v0_36.json`
- Latest demo preflight review: `reports/xauusd_demo_preflight_review_v0_37.json`
- Latest demo broker safety preflight: `reports/xauusd_demo_broker_safety_preflight_v0_38.json`
- Latest broker facts audit: `reports/xauusd_broker_facts_audit_v0_39.json`
- Latest checkpoint: `docs/checkpoints/v0_39_broker_facts_audit_result.md`
- Latest context pack: `reports/codex_context_v0_38.json`
- Latest health report: `reports/project_health_v0_38.json`
- Latest decision: `broker_facts_audit_ready_for_risk_envelope_design`
- Next safe task: v0_39 risk envelope design

## v0_39 Broker Facts Audit Result

- Audit module: `src/research/xauusd_broker_facts_audit.py`
- Audit script: `scripts/build_xauusd_broker_facts_audit_v0_39.py`
- Audit checkpoint: `docs/checkpoints/v0_39_broker_facts_audit_result.md`
- Audit report: `reports/xauusd_broker_facts_audit_v0_39.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Decision: `broker_facts_audit_ready_for_risk_envelope_design`
- Audit status: `completed`
- Candidate rules preserved: `true`
- Design or read-only: `true`
- MT5 read-only metadata access: `true`
- MT5 initialized: `true`
- MT5 shutdown called: `true`
- Missing facts: none
- Broker fact blockers: none
- Order send created: `false`
- Order send called: `false`
- Order check created: `false`
- Order check called: `false`
- Execution queue created: `false`
- Broker execution path created: `false`
- Buy/sell output allowed: `false`
- Trade recommendation output allowed: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Repeated OOS review: `false`

v0_39 collected read-only symbol/account metadata only. It did not create demo or live execution, a broker execution adapter, a trade request, order sending, order checking, an execution queue, directional output, trade recommendations, a strategy variant, a retune, threshold search, parameter grid, repeated OOS review, or any `data/*.csv`.

Collected broker facts:

- XAUUSD exists and is visible.
- Digits `2`, point `0.01`, contract size `100.0`, tick size `0.01`, tick value `0.1`.
- Volume min `0.01`, max `100.0`, step `0.01`.
- Spread `15`, spread float `true`.
- Trade mode `4`, trade execution mode `2`, filling mode `3`, order mode `127`.
- Stops level `0`, freeze level `0`, swap long `-12.6`, swap short `-4.6`.
- Account server `MetaQuotes-Demo`, account currency `USD`, account trade mode `0`.

## v0_38 Demo Broker Safety Preflight Result

- Preflight module: `src/research/xauusd_demo_broker_safety_preflight.py`
- Preflight script: `scripts/build_xauusd_demo_broker_safety_preflight_v0_38.py`
- Preflight checkpoint: `docs/checkpoints/v0_38_demo_broker_safety_preflight_result.md`
- Preflight report: `reports/xauusd_demo_broker_safety_preflight_v0_38.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Decision: `demo_preflight_safety_design_ready`
- Preflight status: `completed`
- Candidate rules preserved: `true`
- Blocking conditions: none
- Design only: `true`
- Demo execution created: `false`
- Broker execution path created: `false`
- MT5 connection created: `false`
- Order send created: `false`
- Order check created: `false`
- Execution queue created: `false`
- Buy/sell output allowed: `false`
- Trade recommendation output allowed: `false`
- Retune performed: `false`
- Threshold search performed: `false`
- Parameter grid performed: `false`
- Repeated OOS review: `false`

v0_38 created only a safety checklist/report for future demo preflight. It defines required confirmations and blocking conditions before any future demo execution can even be considered. It did not connect to MT5, create broker adapters, call or wrap order sending, call or wrap order checking, create execution queues, output directional instructions, output trade recommendations, alter v0_26, retune, optimize, grid search, threshold search, repeat OOS, or add any `data/*.csv` to git.

Required future checks before any future demo consideration:

- candidate lock
- OOS lock
- execution absence
- output language
- broker facts design
- risk controls design
- operator approval

## v0_37 Demo Preflight Review Result

- Review module: `src/research/xauusd_demo_preflight_review.py`
- Review script: `scripts/build_xauusd_demo_preflight_review_v0_37.py`
- Review checkpoint: `docs/checkpoints/v0_37_demo_preflight_review_result.md`
- Review report: `reports/xauusd_demo_preflight_review_v0_37.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Decision: `ready_for_demo_preflight_design`
- Candidate rules preserved: `true`
- OOS completed once: `true`
- Repeat OOS review allowed: `false`
- Ledger quality gate: `ready_for_demo_preflight_review`
- Independent observation sessions: `4`
- Journal record count by timeframe: `M5=3`, `M10=3`
- Ledger blockers: none
- Raw market data embedded: `false`
- Demo allowed: `false`
- Execution allowed: `false`
- Live allowed: `false`
- Order send allowed: `false`
- Order check allowed: `false`

v0_37 reviewed the locked v0_26 candidate and accumulated read-only forward observation evidence only. It did not create demo execution, live trading, order sending, order checking, an execution queue, broker execution, directional output, recommendation output, a new strategy variant, a retune, threshold search, parameter grid, parameter optimization, repeated OOS, or raw market CSV embedding.

Future audit placeholders added for v0_38 design only:

- spread/slippage realism audit
- static macro blackout sensitivity audit
- broker connection safety audit

These placeholders must not alter v0_26 rules and must not create broker or order execution.

## v0_36_3 CI Promotion Gate Result

- Checkpoint: `docs/checkpoints/v0_36_3_ci_promotion_gate_result.md`
- Root cause: the v0_26 decision report stores `candidate_report_path` with Windows backslashes, and the promotion gate compared that metadata path as a raw string. Linux treated the backslash as a literal character and blocked otherwise valid v0_26 report content.
- Fix scope: compression-expansion promotion gate report loading and validation only.
- Path behavior: relative report and output paths resolve repo-relative; clean cwd shadow files are ignored.
- Validation behavior: temp reports are accepted or rejected based on report content and fixed evidence checks, not solely on whether the embedded candidate report path is the default reports path.
- Targeted tests: `16 passed`
- Full tests: `441 passed`
- Health: warnings only, no failures
- Safety: no strategy logic, candidate rules, thresholds, OOS decision, OOS repeat, forward observation logic, execution path, directional output, or raw market data embedding changed.

## v0_36_2 CI Parity Result

- Checkpoint: `docs/checkpoints/v0_36_2_ci_parity_result.md`
- Promotion gate root cause: v0_27 CLI defaults were cwd-relative, so clean Linux CI could block before loading the committed v0_26 candidate report.
- Orchestrator root cause: the test fixture constructed `T24:00:00` for the `block_18_24` end boundary, which is not a valid Python datetime hour.
- Fix scope: repo-rooted/default report path resolution and fixture-safe next-day-midnight block end handling.
- Targeted tests: `29 passed`
- Full tests: `439 passed`
- Health: warnings only, no failures
- Safety: no strategy logic, candidate rules, thresholds, OOS decision, OOS repeat, execution path, or raw market data embedding changed.

## v0_31 Journal Framework Result

- Journal module: `src/research/xauusd_paper_shadow_journal.py`
- Journal script: `scripts/build_xauusd_paper_shadow_journal_v0_31.py`
- Journal checkpoint: `docs/checkpoints/v0_31_paper_shadow_journal_result.md`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Journal status: `framework_ready_not_started`
- Data source status: `synthetic_fixtures_only`
- Real market observation started: `false`
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`
- Repeated OOS review: `false`
- Candidate rules modified: `false`

v0_31 built only a synthetic-fixture journal framework. It did not run OOS, did not evaluate real market data, did not start forward observation, did not retune, did not change candidate rules, and did not create a new strategy variant.

## Journal Record Schema

- timestamp
- candidate_id
- observed_reference_block
- observed_response_block
- compression_label
- expansion_observed
- rule_match_status
- observation_status
- notes

Records are neutral observations only. Allowed record language centers on observation, rule match, expansion observed, no expansion observed, and journal record.

## Source Governance State

- v0_30 governance report: `reports/xauusd_post_oos_governance_v0_30.json`
- governance status: `post_oos_governance_created_design_only`
- paper-shadow protocol status before v0_31: `design_only_not_started`
- source OOS marker decision: `oos_passed_research_validation`
- repeat OOS review allowed: `false`
- detailed OOS metrics available: `false`

The detailed v0_29 OOS metrics remain unavailable because the main OOS report was overwritten by an accidental invalid-token rerun before v0_29_1 restored the locked marker decision. Do not recreate those metrics by rerunning OOS.

## Registry State

- `xauusd_compression_then_expansion_v0_26` status: `oos_passed_research_validation_pending_post_oos_protocol`
- OOS status: `evaluated_passed`
- eligible_for_oos_review: `false`
- one_time_oos_review_completed: `true`
- repeat_oos_review_allowed: `false`
- research_only: `true`

## Safety Boundary

- no repeated OOS research review
- no demo or live trading
- no order sending or order checking
- no execution queue
- no recommendation output
- no directional output
- no threshold search or parameter grid
- no parameter optimization
- no retune of rejected candidates
- no retune of the v0_26 compression-expansion candidate
- no OOS result-driven rule modification
- no promotion to strategy or execution semantics from the v0_29 OOS pass alone

## v0_32 Boundary

v0_32 designed a read-only forward observation data export plan only. It did not create demo, live, order, execution, broker, account, queue, recommendation, or directional-instruction paths. It did not call MT5, export market data, run real observation, run a new backtest, repeat OOS, change candidate rules, or create a strategy variant.

## v0_32 Forward Observation Export Plan Result

- Plan module: `src/research/xauusd_forward_observation_plan.py`
- Plan script: `scripts/build_xauusd_forward_observation_export_plan_v0_32.py`
- Plan checkpoint: `docs/checkpoints/v0_32_forward_observation_export_plan_result.md`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Plan status: `export_plan_ready_not_started`
- Future observation mode: `journal_only`
- Allowed future timeframes: `M5`, `M10`
- MT5 called: `false`
- Data exported: `false`
- Observation run: `false`
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`
- Repeated OOS review: `false`
- Candidate rules modified: `false`

v0_33 built the read-only forward observation exporter wrapper and journal runner framework. It remains journal-only and validates synthetic/local fixture CSV rows only.

## v0_33 Forward Observation Runner Result

- Runner module: `src/research/xauusd_forward_observation_runner.py`
- Runner script: `scripts/run_xauusd_forward_observation_v0_33.py`
- Runner checkpoint: `docs/checkpoints/v0_33_forward_observation_runner_result.md`
- Runner protocol: `reports/xauusd_forward_observation_runner_protocol_v0_33.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Runner status: `framework_ready_not_started`
- Data source status: `synthetic_fixtures_only`
- Future mode: `journal_only`
- Allowed timeframes: `M5`, `M10`
- Real market observation started: `false`
- MT5 called in tests: `false`
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`
- Repeated OOS review: `false`
- Candidate rules modified: `false`

v0_33 did not call MT5, did not export real market data, did not start real observation, did not repeat OOS, did not retune, did not change candidate rules, did not create execution paths, and did not generate recommendations or directional instructions.

v0_34 ran one read-only local forward observation journal pass, still no execution. It remained journal-only and used only the locked candidate rules.

## v0_34 Forward Observation Journal Result

- Journal module: `src/research/xauusd_forward_observation_runner.py`
- Journal script: `scripts/run_xauusd_forward_observation_journal_v0_34.py`
- Journal checkpoint: `docs/checkpoints/v0_34_forward_observation_journal_result.md`
- Journal report: `reports/xauusd_forward_observation_journal_v0_34.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Observation status: `blocked_need_forward_observation_data`
- Journal record count: `0`
- Real market observation started: `false`
- MT5 export used: `false`
- Data files used: none
- Blocking reason: forward M5 data was unavailable; forward M10 was inspected but no journal pass was completed
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`
- Order send allowed: `false`
- Order check allowed: `false`
- Repeated OOS review: `false`
- Candidate rules modified: `false`

v0_34 ran exactly one local read-only pass and blocked cleanly before creating journal records because required forward observation data was incomplete. It did not call MT5, did not export market data, did not start real observation, did not repeat OOS, did not retune, did not change candidate rules, did not create execution paths, and did not generate recommendations or directional instructions.

## v0_34_1 Forward Observation Schema Adapter Result

- Adapter module: `src/research/xauusd_forward_observation_schema_adapter.py`
- Adapter script: `scripts/normalize_xauusd_forward_observation_csv_v0_34_1.py`
- Adapter checkpoint: `docs/checkpoints/v0_34_1_forward_observation_schema_adapter_result.md`
- Adapter protocol: `reports/xauusd_forward_observation_schema_adapter_protocol_v0_34_1.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Adapter status: `framework_ready`
- Supported timeframes: `M5`, `M10`
- Expected output schema: `timestamp_utc`, `symbol`, `timeframe`, `open`, `high`, `low`, `close`, `tick_volume`, `spread`, `source`
- Source schema inspected from project code: `src.data.xauusd_timeframe_resampler.REQUIRED_COLUMNS`
- MT5 called: `false`
- Market data exported from MT5: `false`
- Local real CSV files normalized in v0_34_1: `false`
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`
- Repeated OOS review: `false`
- Candidate rules modified: `false`

v0_34_1 built a local-only schema adapter that converts existing read-only exporter/resampler CSVs into the v0_33/v0_34 forward observation journal schema. If `symbol` or `timeframe` is absent from the input CSV, the adapter requires explicit arguments. If spread is unavailable from the exporter, the adapter writes `spread=0`, records `spread=unavailable_from_exporter` in `source`, and emits warning `spread_unavailable_from_exporter_set_to_0`.

The actual local market CSV files remain uncommitted and were not normalized during v0_34_1. The next safe step is to normalize them locally and rerun the journal pass without execution:

```powershell
py -3 scripts/normalize_xauusd_forward_observation_csv_v0_34_1.py --json --input-csv data/xauusd_m5_xauusd_2026-06-12_2026-06-14.csv --symbol XAUUSD --timeframe M5 --output data/xauusd_m5_xauusd_2026-06-12_2026-06-14_forward_observation_v0_34_1.csv
```

```powershell
py -3 scripts/normalize_xauusd_forward_observation_csv_v0_34_1.py --json --input-csv data/xauusd_m10_xauusd_m5_xauusd_2026_06_12_2026_06_14_2026-06-12_2026-06-12.csv --symbol XAUUSD --timeframe M10 --output data/xauusd_m10_xauusd_m5_xauusd_2026_06_12_2026_06_14_2026-06-12_2026-06-12_forward_observation_v0_34_1.csv
```

v0_34_1 did not call MT5, did not export market data, did not run the journal over real data, did not repeat OOS, did not retune, did not change candidate rules, did not create execution paths, and did not generate recommendations or directional instructions.

## v0_34_2 Forward Observation Consolidated Result

- Consolidator module: `src/research/xauusd_forward_observation_consolidator.py`
- Consolidator script: `scripts/consolidate_xauusd_forward_observation_v0_34_2.py`
- Consolidator checkpoint: `docs/checkpoints/v0_34_2_forward_observation_consolidated_result.md`
- Consolidated report: `reports/xauusd_forward_observation_consolidated_v0_34_2.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Consolidation status: `completed`
- Observation mode: `local_read_only_forward_journal`
- Raw market data embedded: `false`
- Total input reports: `2`
- Timeframes observed: `M10`, `M5`
- Journal record count by timeframe: `M10=1`, `M5=1`
- Total journal record count: `2`
- Expansion observed count: `0`
- No expansion observed count: `2`
- Blockers: none
- Observation quality status: `insufficient_sample_for_quality_gate`
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`
- Order send allowed: `false`
- Order check allowed: `false`
- Repeated OOS review: `false`
- Candidate rules modified: `false`

v0_34_2 consolidated the existing local M5/M10 journal runner JSON reports as read-only forward observation artifacts. It did not embed raw OHLC rows, did not call MT5, did not export market data, did not repeat OOS, did not retune, did not change candidate rules, did not create execution paths, and did not generate recommendations or directional instructions.

## v0_35 Forward Observation Ledger Result

- Ledger module: `src/research/xauusd_forward_observation_ledger.py`
- Ledger script: `scripts/build_xauusd_forward_observation_ledger_v0_35.py`
- Ledger checkpoint: `docs/checkpoints/v0_35_forward_observation_ledger_result.md`
- Ledger report: `reports/xauusd_forward_observation_ledger_v0_35.json`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Ledger status: `completed`
- Raw market data embedded: `false`
- Input consolidated reports: `reports/xauusd_forward_observation_consolidated_v0_34_2.json`
- Independent observation sessions: `1`
- Timeframes observed: `M10`, `M5`
- Total unique journal records: `2`
- Expansion observed count: `0`
- No expansion observed count: `2`
- Quality gate status: `insufficient_samples`
- Demo preflight allowed: `false`
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`
- Order send allowed: `false`
- Order check allowed: `false`
- Repeated OOS review: `false`
- Candidate rules modified: `false`

v0_35 aggregated only consolidated read-only forward observation summaries. It deduplicated records by candidate id, timestamp, timeframe, reference block, and response block. It did not embed raw OHLC rows, did not call MT5, did not export market data, did not repeat OOS, did not retune, did not change candidate rules, did not create execution paths, and did not generate recommendations or directional instructions.

The quality gate did not approve demo preflight. Minimum future requirements before demo preflight review include multiple independent observation sessions, both `M5` and `M10` covered, no schema/data blockers, no rule changes, no OOS repeat, and no execution path introduced.

Next safe step: run approved v0_36 read-only forward observation cycles for new date ranges, no execution.

## v0_36 Forward Observation Cycle Orchestrator Result

- Orchestrator module: `src/research/xauusd_forward_observation_orchestrator.py`
- Cycle script: `scripts/run_xauusd_forward_observation_cycle_v0_36.py`
- Cycle protocol: `reports/xauusd_forward_observation_cycle_protocol_v0_36.json`
- Cycle checkpoint: `docs/checkpoints/v0_36_forward_observation_cycle_result.md`
- Candidate id: `xauusd_compression_then_expansion_v0_26`
- Orchestrator status: `ready_for_approved_read_only_cycle`
- Approval token required: `true`
- Required token: `HUMAN_APPROVED_READONLY_FORWARD_OBSERVATION_V0_36`
- Required date arguments: `--from-date`, `--to-date`
- Supported timeframes: `M5`, `M10`
- Read-only forward observation allowed: `true`
- Demo preflight allowed: `false`
- Execution allowed: `false`
- Demo allowed: `false`
- Live allowed: `false`
- Order send allowed: `false`
- Order check allowed: `false`
- Repeated OOS review: `false`
- Candidate rules modified: `false`
- Raw market data embedded: `false`

v0_36 created a single approved local command that can collect one additional read-only forward observation cycle: use an existing local M5 CSV or explicitly request the read-only MT5 M5 export, resample to M10, normalize both timeframes, build neutral journal reports, consolidate the session, and rebuild the ledger from prior and new consolidated summaries.

The orchestrator blocks cleanly without the exact token, without explicit dates, or when local/exported data is unavailable. It does not synthesize replacement market data and keeps raw CSV files under `data/` as local-only artifacts.

Example approved command for a new date range:

```powershell
py -3 scripts/run_xauusd_forward_observation_cycle_v0_36.py --json --from-date 2026-06-16 --to-date 2026-06-16 --approval-token HUMAN_APPROVED_READONLY_FORWARD_OBSERVATION_V0_36 --export-m5-from-mt5
```

Use `--m5-csv data/<local_m5_file>.csv` instead of `--export-m5-from-mt5` when the M5 file already exists locally.

## v0_36_1 CI Path Normalization Result

- OOS review module: `src/research/xauusd_oos_review.py`
- OOS review tests: `tests/test_xauusd_oos_review.py`
- CI checkpoint: `docs/checkpoints/v0_36_1_ci_path_normalization_result.md`
- Health report: `reports/project_health_v0_36_1.json`
- Context pack: `reports/codex_context_v0_36_1.json`
- Decision: `ci_path_normalization_complete`
- Targeted OOS tests: `15 passed`
- Full tests: `436 passed`

v0_36_1 fixed Linux CI portability for OOS protocol/report path validation only. The root cause was Windows-style backslashes in locked protocol path strings being interpreted differently on Linux. Protocol path strings now normalize `\` and `/` as equivalent repo-relative separators for validation and source report loading, while report path strings are emitted in stable forward-slash form.

v0_36_1 did not rerun the real locked OOS review, did not change candidate rules, did not alter strategy logic, did not retune, did not change thresholds, did not modify market data, did not embed raw CSV data, did not change forward observation results, and did not add demo, live, order, or execution paths.
