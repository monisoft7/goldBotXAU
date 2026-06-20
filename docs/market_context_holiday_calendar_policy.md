# Market Context Holiday Calendar Policy

US market holidays and reduced-liquidity days are a required future dataset category for XAUUSD market context because US closures and partial sessions can materially affect liquidity.

v0_61 does not download holiday datasets. Future acquisition options:

- Manual offline CSV from exchange, government, or broker-published sources.
- Broker calendar export if available.
- Free public calendar download reviewed before import.

Required schema:

- `date`
- `market`
- `country`
- `holiday_name`
- `closure_type`
- `liquidity_impact`
- `source`
- `timestamp_basis`

Policy:

- Holiday rows must cite a source.
- `closure_type` must distinguish full closure, partial closure, settlement holiday, and normal trading with reduced liquidity.
- `liquidity_impact` must be explicit and conservative.
- Unknown holiday state should block or observe-only the market context gate until the dataset is documented.
