from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from src.research.xauusd_demo_broker_safety_preflight import (
    BLOCKED_PREFLIGHT_INTEGRITY_ISSUE,
    CANDIDATE_ID,
    DEMO_PREFLIGHT_SAFETY_DESIGN_READY,
    build_xauusd_demo_broker_safety_preflight_v0_38,
    save_xauusd_demo_broker_safety_preflight,
)

ROOT = Path(__file__).resolve().parents[1]


def _real_candidate() -> dict[str, object]:
    return json.loads(
        (ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json").read_text(
            encoding="utf-8"
        )
    )


def _real_oos_repair() -> dict[str, object]:
    return json.loads((ROOT / "reports" / "xauusd_oos_review_repair_v0_29_1.json").read_text(encoding="utf-8"))


def _real_prior_review() -> dict[str, object]:
    return json.loads((ROOT / "reports" / "xauusd_demo_preflight_review_v0_37.json").read_text(encoding="utf-8"))


def _write_report(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _build_with_payloads(
    tmp_path: Path,
    *,
    candidate: dict[str, object] | None = None,
    oos_repair: dict[str, object] | None = None,
    prior_review: dict[str, object] | None = None,
) -> dict[str, object]:
    candidate_path = _write_report(tmp_path / "reports" / "candidate.json", candidate or _real_candidate())
    oos_path = _write_report(tmp_path / "reports" / "oos_repair.json", oos_repair or _real_oos_repair())
    review_path = _write_report(tmp_path / "reports" / "prior_review.json", prior_review or _real_prior_review())
    return build_xauusd_demo_broker_safety_preflight_v0_38(
        candidate_report_path=candidate_path,
        oos_repair_report_path=oos_path,
        demo_preflight_review_path=review_path,
    )


def test_v0_38_report_is_design_ready_with_required_fields(tmp_path: Path) -> None:
    report = _build_with_payloads(tmp_path)

    assert report["preflight_version"] == "v0_38"
    assert report["preflight_status"] == "completed"
    assert report["decision"] == DEMO_PREFLIGHT_SAFETY_DESIGN_READY
    assert report["decision_options"] == [
        BLOCKED_PREFLIGHT_INTEGRITY_ISSUE,
        DEMO_PREFLIGHT_SAFETY_DESIGN_READY,
    ]
    assert report["candidate_id"] == CANDIDATE_ID
    assert report["candidate_rules_preserved"] is True
    assert report["design_only"] is True
    assert report["blocking_conditions"] == []
    assert report["next_recommended_step"] == (
        "human review of v0_38 safety checklist, then design a separate read-only broker facts audit only"
    )


def test_v0_38_explicitly_keeps_all_execution_disabled(tmp_path: Path) -> None:
    report = _build_with_payloads(tmp_path)

    for key in (
        "demo_execution_created",
        "broker_execution_path_created",
        "mt5_connection_created",
        "order_send_created",
        "order_check_created",
        "execution_queue_created",
        "buy_sell_output_allowed",
        "trade_recommendation_output_allowed",
        "retune_performed",
        "threshold_search_performed",
        "parameter_grid_performed",
        "repeated_oos_review",
    ):
        assert report[key] is False

    non_actions = report["explicit_non_actions"]
    assert isinstance(non_actions, dict)
    assert all(value is False for value in non_actions.values())


def test_required_future_checks_define_confirmations_and_blockers(tmp_path: Path) -> None:
    report = _build_with_payloads(tmp_path)
    checks = report["required_future_demo_preflight_checks"]

    assert isinstance(checks, list)
    assert {check["check_id"] for check in checks} == {
        "candidate_lock",
        "oos_lock",
        "execution_absence",
        "output_language",
        "broker_facts_design",
        "risk_controls_design",
        "operator_approval",
    }
    assert all(check["required_confirmation"] for check in checks)
    assert all(check["blocking_condition"] for check in checks)
    assert all(check["required_before_demo_execution_can_be_considered"] is True for check in checks)
    assert all(check["creates_execution"] is False for check in checks)
    assert all(check["alters_candidate_rules"] is False for check in checks)


def test_blocks_if_prior_v0_37_review_is_not_ready(tmp_path: Path) -> None:
    prior_review = _real_prior_review()
    prior_review["decision"] = "blocked"

    report = _build_with_payloads(tmp_path, prior_review=prior_review)

    assert report["decision"] == BLOCKED_PREFLIGHT_INTEGRITY_ISSUE
    assert report["preflight_status"] == "blocked"
    assert "prior_review_not_ready_for_demo_preflight_design" in report["blocking_conditions"]
    assert report["demo_execution_created"] is False


def test_blocks_if_prior_review_allows_execution(tmp_path: Path) -> None:
    prior_review = _real_prior_review()
    safety = prior_review["safety_state"]
    assert isinstance(safety, dict)
    safety["execution_allowed"] = True

    report = _build_with_payloads(tmp_path, prior_review=prior_review)

    assert report["decision"] == BLOCKED_PREFLIGHT_INTEGRITY_ISSUE
    assert "prior_review_safety_execution_allowed_not_false" in report["blocking_conditions"]
    assert report["broker_execution_path_created"] is False


def test_blocks_if_candidate_rules_are_changed(tmp_path: Path) -> None:
    candidate = copy.deepcopy(_real_candidate())
    fixed_rules = candidate["fixed_rules"]
    assert isinstance(fixed_rules, dict)
    fixed_rules["threshold_search_used"] = True

    report = _build_with_payloads(tmp_path, candidate=candidate)

    assert report["decision"] == BLOCKED_PREFLIGHT_INTEGRITY_ISSUE
    assert "candidate_fixed_rules_threshold_search_used_not_false" in report["blocking_conditions"]
    assert report["candidate_rules_preserved"] is False
    assert report["threshold_search_performed"] is False


def test_blocks_if_oos_repeat_is_allowed(tmp_path: Path) -> None:
    oos_repair = _real_oos_repair()
    oos_repair["repeat_review_allowed"] = True
    safety = oos_repair["safety"]
    assert isinstance(safety, dict)
    safety["repeat_review_allowed"] = True

    report = _build_with_payloads(tmp_path, oos_repair=oos_repair)

    assert report["decision"] == BLOCKED_PREFLIGHT_INTEGRITY_ISSUE
    assert "repeat_oos_review_allowed" in report["blocking_conditions"]
    assert report["repeated_oos_review"] is False


def test_confirms_v0_26_report_is_not_modified(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    output_path = tmp_path / "xauusd_demo_broker_safety_preflight_v0_38.json"

    report = build_xauusd_demo_broker_safety_preflight_v0_38()
    save_xauusd_demo_broker_safety_preflight(report, output_path)
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_id"] == CANDIDATE_ID
    assert report["candidate_rules_preserved"] is True


def test_source_does_not_create_execution_order_or_mt5_path() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_demo_broker_safety_preflight.py",
            ROOT / "scripts" / "build_xauusd_demo_broker_safety_preflight_v0_38.py",
        ]
    ).lower()

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "metatrader5" not in source_text
    assert "copy_rates" not in source_text
    assert "initialize(" not in source_text
    assert "shutdown(" not in source_text


def test_report_does_not_emit_directional_or_recommendation_output(tmp_path: Path) -> None:
    report_text = json.dumps(_build_with_payloads(tmp_path))
    source_text = (ROOT / "src" / "research" / "xauusd_demo_broker_safety_preflight.py").read_text(
        encoding="utf-8"
    )

    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    assert "B" + "UY" not in source_text
    assert "S" + "ELL" not in source_text
    assert "trade recommendation" not in report_text.lower()
    assert "trade recommendation" not in source_text.lower()


def test_cli_builds_v0_38_report(tmp_path: Path) -> None:
    output_path = tmp_path / "xauusd_demo_broker_safety_preflight_v0_38.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_xauusd_demo_broker_safety_preflight_v0_38.py"),
            "--json",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_report = json.loads(completed.stdout)
    output_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_report["preflight_version"] == "v0_38"
    assert output_report["decision"] == DEMO_PREFLIGHT_SAFETY_DESIGN_READY
