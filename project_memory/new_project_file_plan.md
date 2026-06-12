# New Project File Plan

Create a clean project outside the heavy old `multiGold` tree:

```text
goldBotXAU/
  README.md
  safety_rules.md
  config/
  data/
  reports/
  src/
    data_loader.py
    indicators.py
    backtest_engine.py
    risk_manager.py
    strategy_interface.py
    strategies/
    metrics.py
  tests/
  project_memory/
    new_project_handoff.md
    failed_strategy_registry.md
    codex_usage_contract.md
```

## Project Rules
- Keep the project compact.
- Build one XAUUSD strategy path at a time.
- Make strategy metrics numeric and reproducible.
- Keep execution disabled until explicit demo-phase approval.
