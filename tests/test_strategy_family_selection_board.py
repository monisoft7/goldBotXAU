from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.research.candidate_registry import research_candidate_registry
from src.research.strategy_family_selection_board import build_strategy_family_selection_board

ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _profile_fixture() -> dict[str, object]:
    return {
        "status": "profile_ready",
        "profiler_version": "v0_10",
        "candidate_direction_hints": {
            "continuation_bias_detected": False,
            "reversion_bias_detected": False,
        },
        "block_profile": {
            "block_00_06": {
                "average_range_to_atr": 0.82,
                "average_next_4bar_abs_return_to_atr": 0.81,
            },
            "block_12_18": {
                "average_range_to_atr": 1.35,
                "average_next_4bar_abs_return_to_atr": 1.43,
            },
        },
        "impulse_diagnostic": {
            "range_to_atr_gte_1.5": {
                "persistence_4bar_rate": 0.49,
                "reversal_4bar_rate": 0.51,
            }
        },
        "oos_guard": {
            "oos_locked": True,
            "oos_access_attempted": False,
            "oos_access_allowed": False,
        },
        "safety": {
            "strategy_logic_added": False,
            "trade_simulation_added": False,
        },
    }


def _diagnostic_fixture() -> dict[str, object]:
    return {
        "diagnostic_version": "v0_12",
        "status": "diagnostic_ready",
        "candidate": {
            "candidate_id": "xauusd_session_volatility_expansion_v0_11",
            "family_name": "session_volatility_expansion",
            "do_not_retune": True,
        },
        "breakdowns": {
            "by_atr_regime": [
                {
                    "bucket": "low_atr",
                    "trade_count": 91,
                    "profit_factor": 1.13,
                    "expectancy": 0.06,
                    "final_equity_r": 5.48,
                },
                {
                    "bucket": "high_atr",
                    "trade_count": 105,
                    "profit_factor": 0.69,
                    "expectancy": -0.16,
                    "final_equity_r": -17.37,
                },
                {
                    "bucket": "extreme_atr",
                    "trade_count": 268,
                    "profit_factor": 0.86,
                    "expectancy": -0.05,
                    "final_equity_r": -15.67,
                },
            ]
        },
        "stability_summary": {
            "best_bucket": {
                "bucket": "low_atr",
                "trade_count": 91,
                "profit_factor": 1.13,
                "final_equity_r": 5.48,
            },
            "worst_bucket": {
                "bucket": "block_12_18",
                "trade_count": 490,
                "profit_factor": 0.89,
                "final_equity_r": -24.23,
            },
            "train_failure_scope": "broad_failure",
        },
        "diagnostic_decision": {
            "next_action": "abandon_family",
            "retune_allowed": False,
            "oos_review_allowed": False,
        },
        "oos_guard": {
            "oos_locked": True,
            "oos_access_attempted": False,
            "oos_access_allowed": False,
        },
        "safety": {
            "strategy_logic_added": False,
            "parameter_tuning_added": False,
            "oos_evaluated": False,
        },
    }


def _fixture_board(tmp_path: Path) -> dict[str, object]:
    profile_path = tmp_path / "reports" / "profile.json"
    diagnostic_path = tmp_path / "reports" / "diagnostic.json"
    _write_json(profile_path, _profile_fixture())
    _write_json(diagnostic_path, _diagnostic_fixture())
    return build_strategy_family_selection_board(profile_path, diagnostic_path)


def test_board_runs_with_fixture_profile_and_diagnostic_inputs(tmp_path: Path) -> None:
    board = _fixture_board(tmp_path)

    assert board["board_version"] == "v0_13"
    assert board["status"] == "board_ready"
    assert len(board["candidate_family_options"]) == 3


def test_board_marks_rejected_candidates_as_forbidden_for_retune(tmp_path: Path) -> None:
    board = _fixture_board(tmp_path)
    rejected = {candidate["candidate_id"]: candidate for candidate in board["input_summary"]["rejected_candidates"]}

    assert rejected["xauusd_atr_impulse_reversion_v0_7"]["do_not_retune"] is True
    assert rejected["xauusd_multi_bar_exhaustion_reversion_v0_8"]["do_not_retune"] is True
    assert rejected["xauusd_session_volatility_expansion_v0_11"]["do_not_retune"] is True
    assert "atr_impulse_reversion" in board["forbidden_next_families"]
    assert "multi_bar_exhaustion_reversion" in board["forbidden_next_families"]


def test_board_marks_session_volatility_expansion_as_abandoned(tmp_path: Path) -> None:
    board = _fixture_board(tmp_path)

    assert board["evidence_summary"]["session_volatility_family_status"] == "abandoned"
    assert "session_volatility_expansion" in board["input_summary"]["abandoned_families"]
    assert "session_volatility_expansion" in board["forbidden_next_families"]


def test_board_returns_exactly_one_recommended_next_family(tmp_path: Path) -> None:
    board = _fixture_board(tmp_path)

    assert board["recommended_next_family"] == "low_atr_range_expansion_followthrough"
    assert board["recommended_v0_14_candidate_id"] == "xauusd_low_atr_range_expansion_followthrough_v0_14"


def test_board_does_not_recommend_a_blacklisted_family(tmp_path: Path) -> None:
    board = _fixture_board(tmp_path)

    assert board["recommended_next_family"] not in board["forbidden_next_families"]
    assert all(option["blacklisted"] is False for option in board["candidate_family_options"])


def test_board_does_not_use_oos_or_validation_for_discovery(tmp_path: Path) -> None:
    board = _fixture_board(tmp_path)

    assert board["oos_policy"] == {
        "oos_locked": True,
        "oos_review_allowed": False,
    }
    assert board["input_summary"]["oos_locked"] is True
    assert board["input_summary"]["eligible_for_oos_review_count"] == 0
    assert board["input_summary"]["discovery_split"] == "train"
    assert board["input_summary"]["validation_used_for_discovery"] is False
    assert board["safety"]["oos_evaluated"] is False


def test_board_does_not_create_a_new_strategy_candidate(tmp_path: Path) -> None:
    before = research_candidate_registry()

    _fixture_board(tmp_path)

    assert research_candidate_registry() == before


def test_board_does_not_simulate_trades(tmp_path: Path) -> None:
    board = _fixture_board(tmp_path)

    assert board["safety"]["strategy_logic_added"] is False
    assert board["safety"]["trade_simulation_added"] is False
    assert "train_metrics" not in json.dumps(board)


def test_board_output_contains_no_trade_instruction_words(tmp_path: Path) -> None:
    board_text = json.dumps(_fixture_board(tmp_path))

    assert "B" + "UY" not in board_text
    assert "S" + "ELL" not in board_text


def test_safety_flags_exist(tmp_path: Path) -> None:
    board = _fixture_board(tmp_path)

    assert set(board["safety"]) == {
        "demo_enabled",
        "live_enabled",
        "order_send_allowed",
        "execution_queue_enabled",
        "buy_sell_output_allowed",
        "strategy_logic_added",
        "trade_simulation_added",
        "oos_evaluated",
    }


def test_no_demo_live_order_send_permission_exposed(tmp_path: Path) -> None:
    safety = _fixture_board(tmp_path)["safety"]

    assert safety["demo_enabled"] is False
    assert safety["live_enabled"] is False
    assert safety["order_send_allowed"] is False
    assert safety["execution_queue_enabled"] is False


def test_cli_json_works(tmp_path: Path) -> None:
    profile_path = tmp_path / "reports" / "profile.json"
    diagnostic_path = tmp_path / "reports" / "diagnostic.json"
    output_path = tmp_path / "reports" / "board.json"
    _write_json(profile_path, _profile_fixture())
    _write_json(diagnostic_path, _diagnostic_fixture())

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "select_next_strategy_family.py"),
            "--profile",
            str(profile_path),
            "--diagnostic",
            str(diagnostic_path),
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(completed.stdout)
    assert report["board_version"] == "v0_13"
    assert report["status"] == "board_ready"
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == report


def test_missing_inputs_are_handled_safely(tmp_path: Path) -> None:
    board = build_strategy_family_selection_board(
        tmp_path / "missing_profile.json",
        tmp_path / "missing_diagnostic.json",
    )

    assert board["status"] == "inputs_missing"
    assert board["input_summary"]["missing_inputs"] == ["market_profile", "stability_diagnostic"]
    assert board["oos_policy"]["oos_locked"] is True
    assert board["safety"]["trade_simulation_added"] is False
