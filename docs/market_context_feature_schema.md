# Market Context Feature Schema

v0_61 documents schemas only. No full external datasets are imported.

Holiday/reduced liquidity calendar schema:

- `date`
- `market`
- `country`
- `holiday_name`
- `closure_type`
- `liquidity_impact`
- `source`
- `timestamp_basis`

Economic calendar schema:

- `event_time_utc`
- `currency`
- `event_name`
- `impact`
- `actual`
- `forecast`
- `previous`
- `source`
- `revision_flag`

Required high-impact US events:

- `CPI`
- `PPI`
- `NFP`
- `Unemployment Rate`
- `FOMC Rate Decision`
- `FOMC Minutes`
- `Fed Chair Speech`
- `GDP`
- `Retail Sales`
- `ISM`
- `Jobless Claims`

Event-window labels:

- `pre_high_impact_us_event_window`
- `immediate_post_high_impact_us_event_window`
- `post_event_repricing_window`
- `fomc_day`
- `nfp_day`
- `cpi_day`

DXY/USD proxy and US yields/rates OHLC schema:

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `source_symbol`
- `timeframe`
- `timestamp_basis`
- `source`

Geopolitical and macro-risk label schema:

- `label`
- `window_start_utc`
- `window_end_utc`
- `risk_region`
- `source`
- `evidence_timestamp_utc`
- `evidence_url_or_reference`
- `confidence`
- `notes`

Allowed future geopolitical labels:

- `geopolitical_risk_bid`
- `risk_off_proxy_window`
- `middle_east_tension_window`
- `central_bank_headline_window`
- `unexpected_shock_window`

API key policy:

- API keys must not be stored in code, docs, reports, fixtures, or checked-in config.
- Future importer configuration must use local environment variables or ignored local config files.
- v0_61 does not require paid APIs.
