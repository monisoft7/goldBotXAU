# v0_34_1 Forward Observation Schema Adapter Result

## Decision

`framework_ready`

v0_34_1 created a local-only CSV schema adapter for `xauusd_compression_then_expansion_v0_26`.

## Adapter Output

- adapter module: `src/research/xauusd_forward_observation_schema_adapter.py`
- adapter script: `scripts/normalize_xauusd_forward_observation_csv_v0_34_1.py`
- protocol report: `reports/xauusd_forward_observation_schema_adapter_protocol_v0_34_1.json`
- supported timeframes: `M5`, `M10`
- expected output schema: `timestamp_utc`, `symbol`, `timeframe`, `open`, `high`, `low`, `close`, `tick_volume`, `spread`, `source`
- source schema inspected from project code: `src.data.xauusd_timeframe_resampler.REQUIRED_COLUMNS`

The adapter maps the local exporter/resampler schema `timestamp`, `open`, `high`, `low`, `close`, `volume` into the forward observation journal schema. If `symbol` or `timeframe` is absent from the input CSV, explicit CLI/function arguments are required.

## Spread Policy

The local exporter/resampler schema does not include spread. When spread is unavailable, the adapter writes `spread=0`, marks the row source with `spread=unavailable_from_exporter`, and emits warning `spread_unavailable_from_exporter_set_to_0`.

## Validation

- targeted adapter tests: `10 passed`
- targeted adapter + context tests: `25 passed`
- full tests: `396 passed`
- project health: `warnings` only, zero failures
- context pack: `reports/codex_context_v0_34_1.json`
- real local market CSV files required by tests: `false`
- MT5 called: `false`
- market data exported from MT5: `false`
- repeated OOS review: `false`
- candidate rules modified: `false`

## Local Normalization Commands

```powershell
py -3 scripts/normalize_xauusd_forward_observation_csv_v0_34_1.py --json --input-csv data/xauusd_m5_xauusd_2026-06-12_2026-06-14.csv --symbol XAUUSD --timeframe M5 --output data/xauusd_m5_xauusd_2026-06-12_2026-06-14_forward_observation_v0_34_1.csv
```

```powershell
py -3 scripts/normalize_xauusd_forward_observation_csv_v0_34_1.py --json --input-csv data/xauusd_m10_xauusd_m5_xauusd_2026_06_12_2026_06_14_2026-06-12_2026-06-12.csv --symbol XAUUSD --timeframe M10 --output data/xauusd_m10_xauusd_m5_xauusd_2026_06_12_2026_06_14_2026-06-12_2026-06-12_forward_observation_v0_34_1.csv
```

## Next Step

`v0_34_2 normalize local forward CSV files and rerun journal pass, no execution`

## Safety Confirmation

- Demo behavior added: `false`
- Live behavior added: `false`
- Order sending or checking added: `false`
- Execution queue added: `false`
- Recommendation output added: `false`
- Directional instruction output added: `false`
- Threshold search used: `false`
- Parameter grid used: `false`
- Parameter optimization used: `false`
- Retune used: `false`
- Candidate rules changed: `false`
- Repeated OOS research review: `false`
