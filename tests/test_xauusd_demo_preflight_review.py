from __future__ import annotations

import copy
import json
from pathlib import Path

from src.research.xauusd_demo_preflight_review import (
    BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE,
    BLOCKED_INSUFFICIENT_FORWARD_OBSERVATION,
    CANDIDATE_ID,
    READY_FOR_DEMO_PREFLIGHT_DESIGN,
    build_xauusd_demo_preflight_review_v0_37,
    save_xauusd_demo_preflight_review,
)

ROOT = Path(__file__).resolve().parents[1]


def _real_ledger() -> dict[str, object]:
    return json.loads(
        (ROOT / "reports" / "xauusd_forward_observation_ledger_v0_36_cycle_2026-06-16.json").read_text(
            encoding="utf-8"
        )
    )


def _real_candidate() -> dict[str, object]:
    return json.loads(
        (ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json").read_text(
            encoding="utf-8"
        )
    )


def _real_oos_repair() -> dict[str, object]:
    return json.loads((ROOT / "reports" / "xauusd_oos_review_repair_v0_29_1.json").read_text(encoding="utf-8"))


def _write_report(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _build_with_payloads(
    tmp_path: Path,
    *,
    ledger: dict[str, object] | None = None,
    candidate: dict[str, object] | None = None,
    oos_repair: dict[str, object] | None = None,
) -> dict[str, object]:
    ledger_path = _write_report(tmp_path / "reports" / "ledger.json", ledger or _real_ledger())
    candidate_path = _write_report(tmp_path / "reports" / "candidate.json", candidate or _real_candidate())
    oos_path = _write_report(tmp_path / "reports" / "oos_repair.json", oos_repair or _real_oos_repair())
    return build_xauusd_demo_preflight_review_v0_37(
        ledger_report_path=ledger_path,
        candidate_report_path=candidate_path,
        oos_repair_report_path=oos_path,
    )


def test_ready_review_from_latest_v0_36_ledger(tmp_path: Path) -> None:
    review = _build_with_payloads(tmp_path)

    assert review["decision"] == READY_FOR_DEMO_PREFLIGHT_DESIGN
    assert review["candidate_id"] == CANDIDATE_ID
    assert review["review_status"] == "completed"
    assert review["integrity_blockers"] == []
    assert review["insufficient_forward_observation_blockers"] == []
    assert review["input_confirmations"]["journal_record_count_by_timeframe"] == {"M10": 3, "M5": 3}
    assert review["input_confirmations"]["independent_observation_session_count"] == 4
    assert review["input_confirmations"]["ledger_blockers"] == []
    assert review["input_confirmations"]["raw_market_data_embedded"] is False
    assert review["candidate_rules_preserved"] is True
    assert review["safety_state"]["demo_allowed"] is False
    assert review["safety_state"]["execution_allowed"] is False
    assert review["safety_state"]["order_send_allowed"] is False
    assert review["safety_state"]["order_check_allowed"] is False
    assert [item["audit"] for item in review["future_audit_placeholders"]] == [
        "spread/slippage realism audit",
        "static macro blackout sensitivity audit",
        "broker connection safety audit",
    ]
    assert all(item["status"] == "future_design_placeholder_only" for item in review["future_audit_placeholders"])
    assert all(item["alters_v0_26_rules"] is False for item in review["future_audit_placeholders"])


def test_blocks_if_ledger_missing(tmp_path: Path) -> None:
    candidate_path = _write_report(tmp_path / "reports" / "candidate.json", _real_candidate())
    oos_path = _write_report(tmp_path / "reports" / "oos_repair.json", _real_oos_repair())

    review = build_xauusd_demo_preflight_review_v0_37(
        ledger_report_path=tmp_path / "reports" / "missing_ledger.json",
        candidate_report_path=candidate_path,
        oos_repair_report_path=oos_path,
    )

    assert review["decision"] == BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE
    assert any("forward_observation_ledger_missing" in blocker for blocker in review["integrity_blockers"])
    assert review["safety_state"]["demo_allowed"] is False


def test_blocks_if_candidate_mismatch(tmp_path: Path) -> None:
    ledger = _real_ledger()
    ledger["candidate_id"] = "wrong_candidate"

    review = _build_with_payloads(tmp_path, ledger=ledger)

    assert review["decision"] == BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE
    assert "ledger_candidate_id_mismatch" in review["integrity_blockers"]


def test_blocks_if_candidate_rules_modified(tmp_path: Path) -> None:
    ledger = _real_ledger()
    ledger["candidate_rules_modified"] = True

    review = _build_with_payloads(tmp_path, ledger=ledger)

    assert review["decision"] == BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE
    assert "ledger_candidate_rules_modified" in review["integrity_blockers"]
    assert review["safety_state"]["candidate_rules_modified"] is False


def test_blocks_if_oos_repeat_allowed(tmp_path: Path) -> None:
    oos_repair = _real_oos_repair()
    oos_repair["repeat_review_allowed"] = True
    safety = oos_repair["safety"]
    assert isinstance(safety, dict)
    safety["repeat_review_allowed"] = True

    review = _build_with_payloads(tmp_path, oos_repair=oos_repair)

    assert review["decision"] == BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE
    assert "repeat_oos_review_allowed" in review["integrity_blockers"]
    assert review["safety_state"]["oos_repeat_allowed"] is False


def test_blocks_if_m5_m10_record_count_below_requirement(tmp_path: Path) -> None:
    ledger = _real_ledger()
    ledger["journal_record_count_by_timeframe"] = {"M10": 3, "M5": 2}

    review = _build_with_payloads(tmp_path, ledger=ledger)

    assert review["decision"] == BLOCKED_INSUFFICIENT_FORWARD_OBSERVATION
    assert "M5_record_count_below_requirement" in review["insufficient_forward_observation_blockers"]


def test_blocks_if_independent_sessions_below_requirement(tmp_path: Path) -> None:
    ledger = _real_ledger()
    ledger["independent_observation_session_count"] = 2

    review = _build_with_payloads(tmp_path, ledger=ledger)

    assert review["decision"] == BLOCKED_INSUFFICIENT_FORWARD_OBSERVATION
    assert "independent_observation_sessions_below_requirement" in review[
        "insufficient_forward_observation_blockers"
    ]


def test_blocks_if_blockers_exist(tmp_path: Path) -> None:
    ledger = _real_ledger()
    ledger["blockers"] = ["schema_issue"]

    review = _build_with_payloads(tmp_path, ledger=ledger)

    assert review["decision"] == BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE
    assert "ledger_blockers_not_empty" in review["integrity_blockers"]


def test_blocks_if_raw_market_data_is_embedded(tmp_path: Path) -> None:
    ledger = _real_ledger()
    ledger["raw_market_data_embedded"] = True
    ledger["raw_ohlc_rows"] = [
        {
            "timestamp_utc": "2026-06-16T00:00:00+00:00",
            "open": 3300.0,
            "high": 3310.0,
            "low": 3295.0,
            "close": 3305.0,
        }
    ]

    review = _build_with_payloads(tmp_path, ledger=ledger)

    assert review["decision"] == BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE
    assert "ledger_raw_market_data_embedded_not_false" in review["integrity_blockers"]
    assert "ledger_raw_market_data_payload_detected" in review["integrity_blockers"]
    assert review["safety_state"]["raw_market_data_embedded"] is False


def test_confirms_no_demo_live_order_or_execution_path() -> None:
    review = build_xauusd_demo_preflight_review_v0_37()
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_demo_preflight_review.py",
            ROOT / "scripts" / "build_xauusd_demo_preflight_review_v0_37.py",
        ]
    ).lower()

    assert review["safety_state"]["demo_allowed"] is False
    assert review["safety_state"]["live_allowed"] is False
    assert review["safety_state"]["execution_allowed"] is False
    assert review["safety_state"]["execution_queue_allowed"] is False
    assert review["safety_state"]["order_send_allowed"] is False
    assert review["safety_state"]["order_check_allowed"] is False
    assert review["non_actions_performed"]["broker_execution_path_created"] is False
    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "metatrader5" not in source_text
    assert "copy_rates" not in source_text
    assert "initialize(" not in source_text
    assert "shutdown(" not in source_text


def test_confirms_no_buy_sell_or_trade_recommendation_output() -> None:
    review_text = json.dumps(build_xauusd_demo_preflight_review_v0_37())
    source_text = (ROOT / "src" / "research" / "xauusd_demo_preflight_review.py").read_text(encoding="utf-8")

    assert "B" + "UY" not in review_text
    assert "S" + "ELL" not in review_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text
    assert "trade recommendation" not in review_text.lower()
    assert "trade recommendation" not in source_text.lower()
    assert json.loads(review_text)["safety_state"]["trade_recommendation_output_allowed"] is False


def test_confirms_candidate_rules_are_preserved(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    output_path = tmp_path / "xauusd_demo_preflight_review_v0_37.json"

    review = build_xauusd_demo_preflight_review_v0_37()
    save_xauusd_demo_preflight_review(review, output_path)
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert review["candidate_id"] == CANDIDATE_ID
    assert review["candidate_rules_preserved"] is True
    assert review["candidate_rules_snapshot"] == _real_candidate()["fixed_rules"]
    assert review["safety_state"]["rule_change_allowed"] is False
    assert review["safety_state"]["threshold_search_allowed"] is False
    assert review["safety_state"]["parameter_grid_allowed"] is False
    assert review["safety_state"]["parameter_optimization_allowed"] is False
    assert review["safety_state"]["retune_allowed"] is False


def test_candidate_payload_mismatch_blocks_review(tmp_path: Path) -> None:
    candidate = copy.deepcopy(_real_candidate())
    nested = candidate["candidate"]
    assert isinstance(nested, dict)
    nested["fixed_rules"] = {"changed": True}

    review = _build_with_payloads(tmp_path, candidate=candidate)

    assert review["decision"] == BLOCKED_FORWARD_OBSERVATION_INTEGRITY_ISSUE
    assert "candidate_fixed_rules_mismatch" in review["integrity_blockers"]
