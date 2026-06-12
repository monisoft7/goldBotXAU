from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_key_modules_import() -> None:
    modules = [
        "src.data_loader",
        "src.indicators",
        "src.metrics",
        "src.risk_manager",
        "src.strategy_interface",
        "src.backtest_engine",
        "src.strategies",
    ]
    for module in modules:
        importlib.import_module(module)


def test_settings_disable_all_execution_modes() -> None:
    settings = json.loads((ROOT / "config" / "settings.example.json").read_text(encoding="utf-8"))

    assert settings["symbol"] == "XAUUSD"
    assert settings["execution_enabled"] is False
    assert settings["demo_enabled"] is False
    assert settings["live_enabled"] is False
    assert settings["order_send_enabled"] is False


def test_safety_text_denies_live_and_demo() -> None:
    safety_text = (ROOT / "safety_rules.md").read_text(encoding="utf-8").lower()

    assert "no live trading" in safety_text
    assert "no demo trading" in safety_text


def test_source_has_no_trade_direction_output_or_execution_call() -> None:
    forbidden_terms = ("B" + "UY", "S" + "ELL")

    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert all(term not in text for term in forbidden_terms), path
        assert "order" + "_send(" not in text, path


def test_failed_strategy_registry_exists() -> None:
    assert (ROOT / "project_memory" / "failed_strategy_registry.md").exists()
