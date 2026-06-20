# Reusable Assets

Only the assets below are worth carrying into `goldBotXAU`.

## Safety Rules
- Reuse `project_memory/safety_rules.md` as the starting safety contract.
- Keep demo/live/order_send/execution disabled until backtest and out-of-sample pass.

## XAUUSD Local CSV Data
- Local XAUUSD data is available under `data/`.
- Use only local files; do not fetch prices or scrape.
- Candidate files include existing `xauusd_m15_*` CSVs.

## MT5 Read-Only Exporter
- `mt5_readonly_candle_csv_exporter.py` is present.
- It is read-only export tooling only.
- Do not enable execution or order sending.

## Project Memory Summary
- Use project memory summary only as context.
- Do not import old project state as a strategy signal.

## v1_87 FOMC XAUUSD 4h Learning Summary
- Reusable as context only.
- Not a predictive rule.
- Not a trade signal.

## v1_88/v1_89/v1_90 Rate Decision Context Work
- Reusable as context only.
- Context append or ingestion requires explicit approval in the old project.
- Not a trade signal.

## v0_64 consolidation reusable assets
- `reports/repository_consolidation_plan_v0_64.json` is the source of truth for cleanup planning.
- `docs/active_project_map.md` is the human-readable active-context map.
- `docs/retired_experiments_archive.md` preserves failed experiment evidence before any cleanup.
- `project_memory/failed_strategy_registry.md` remains the do-not-retune registry.
- Reusable only for repository hygiene and context reduction; not reusable as strategy logic, trade filtering, or execution approval.
