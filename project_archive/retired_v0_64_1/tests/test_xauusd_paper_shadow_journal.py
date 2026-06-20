from __future__ import annotations

import json
from pathlib import Path

from src.research.xauusd_paper_shadow_journal import (
    CANDIDATE_ID,
    build_neutral_journal_records,
    build_xauusd_paper_shadow_journal_protocol_v0_31,
    save_xauusd_paper_shadow_journal_protocol,
)

ROOT = Path(__file__).resolve().parents[1]


def _governance(
    *,
    execution_allowed: bool = False,
    demo_allowed: bool = False,
    live_allowed: bool = False,
    repeat_allowed: bool = False,
) -> dict[str, object]:
    return {
        "governance_version": "v0_30",
        "candidate_id": CANDIDATE_ID,
        "governance_status": "post_oos_governance_created_design_only",
        "one_time_oos_review_completed": True,
        "repeat_oos_review_allowed": repeat_allowed,
        "execution_allowed": execution_allowed,
        "demo_allowed": demo_allowed,
        "live_allowed": live_allowed,
        "candidate_rules_lock": {
            "candidate_rules_modified": False,
        },
    }


def _candidate() -> dict[str, object]:
    return {
        "candidate_id": CANDIDATE_ID,
        "fixed_rules": {
            "reference_blocks": ["block_00_06", "block_06_12", "block_12_18"],
            "response_blocks": ["block_06_12", "block_12_18", "block_18_24"],
            "threshold_search_used": False,
            "parameter_grid_used": False,
            "retuning_used": False,
        },
    }


def _write_fixture_inputs(
    tmp_path: Path,
    *,
    governance: dict[str, object] | None = None,
    candidate: dict[str, object] | None = None,
) -> tuple[Path, Path]:
    reports = tmp_path / "reports"
    reports.mkdir()
    governance_path = reports / "xauusd_post_oos_governance_v0_30.json"
    candidate_path = reports / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    if governance is not None:
        governance_path.write_text(json.dumps(governance), encoding="utf-8")
    if candidate is not None:
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    return governance_path, candidate_path


def test_journal_protocol_blocks_if_v0_30_governance_missing(tmp_path: Path) -> None:
    governance_path, candidate_path = _write_fixture_inputs(tmp_path, candidate=_candidate())

    report = build_xauusd_paper_shadow_journal_protocol_v0_31(
        governance_report_path=governance_path,
        candidate_report_path=candidate_path,
    )

    assert report["journal_status"] == "blocked_framework_prerequisites_not_met"
    assert any(blocker.startswith("post_oos_governance_missing") for blocker in report["blockers"])
    assert report["execution_allowed"] is False


def test_journal_protocol_blocks_if_execution_demo_or_live_allowed(tmp_path: Path) -> None:
    governance_path, candidate_path = _write_fixture_inputs(
        tmp_path,
        governance=_governance(execution_allowed=True, demo_allowed=True, live_allowed=True),
        candidate=_candidate(),
    )

    report = build_xauusd_paper_shadow_journal_protocol_v0_31(
        governance_report_path=governance_path,
        candidate_report_path=candidate_path,
    )

    assert "governance_execution_allowed_not_false" in report["blockers"]
    assert "governance_demo_allowed_not_false" in report["blockers"]
    assert "governance_live_allowed_not_false" in report["blockers"]
    assert report["journal_status"] == "blocked_framework_prerequisites_not_met"


def test_journal_protocol_blocks_if_repeat_oos_allowed(tmp_path: Path) -> None:
    governance_path, candidate_path = _write_fixture_inputs(
        tmp_path,
        governance=_governance(repeat_allowed=True),
        candidate=_candidate(),
    )

    report = build_xauusd_paper_shadow_journal_protocol_v0_31(
        governance_report_path=governance_path,
        candidate_report_path=candidate_path,
    )

    assert "governance_repeat_oos_review_allowed_not_false" in report["blockers"]
    assert report["repeated_oos_review"] is False


def test_synthetic_fixture_journal_generation_works() -> None:
    records = build_neutral_journal_records(
        [
            {
                "timestamp": "2026-06-13T00:00:00",
                "observed_reference_block": "block_00_06",
                "observed_response_block": "block_06_12",
                "compression_label": "lowest range reference block",
                "reference_range": 5,
                "response_range": 8,
                "notes": "synthetic fixture journal record",
            },
            {
                "timestamp": "2026-06-14T00:00:00",
                "observed_reference_block": "block_06_12",
                "observed_response_block": "block_12_18",
                "compression_label": "lowest range reference block",
                "reference_range": 8,
                "response_range": 5,
                "notes": "synthetic fixture journal record",
            },
        ]
    )

    assert len(records) == 2
    assert set(records[0]) == {
        "timestamp",
        "candidate_id",
        "observed_reference_block",
        "observed_response_block",
        "compression_label",
        "expansion_observed",
        "rule_match_status",
        "observation_status",
        "notes",
    }
    assert records[0]["expansion_observed"] is True
    assert records[0]["rule_match_status"] == "rule match"
    assert records[0]["observation_status"] == "expansion observed"
    assert records[1]["expansion_observed"] is False
    assert records[1]["observation_status"] == "no expansion observed"


def test_journal_records_use_neutral_observation_language() -> None:
    report = build_xauusd_paper_shadow_journal_protocol_v0_31()
    report_text = json.dumps(report)

    assert "observation" in report_text
    assert "rule match" in report_text
    assert "expansion observed" in report_text
    assert "journal record" in report_text
    assert "B" + "UY" not in report_text
    assert "S" + "ELL" not in report_text
    for record in report["synthetic_fixture_records"]:
        assert "recommendation" not in json.dumps(record).lower()
        assert "directional" not in json.dumps(record).lower()


def test_journal_protocol_report_has_required_v0_31_fields() -> None:
    report = build_xauusd_paper_shadow_journal_protocol_v0_31()

    assert report["candidate_id"] == CANDIDATE_ID
    assert report["journal_status"] == "framework_ready_not_started"
    assert report["data_source_status"] == "synthetic_fixtures_only"
    assert report["real_market_observation_started"] is False
    assert report["execution_allowed"] is False
    assert report["demo_allowed"] is False
    assert report["live_allowed"] is False
    assert report["repeated_oos_review"] is False
    assert report["candidate_rules_modified"] is False
    assert report["next_recommended_step"] == "v0_32 read-only forward observation data export plan, no execution"


def test_journal_protocol_does_not_modify_candidate_rules(tmp_path: Path) -> None:
    candidate_path = ROOT / "reports" / "xauusd_compression_expansion_candidate_v0_26_train_validation.json"
    before = candidate_path.read_text(encoding="utf-8")
    output_path = tmp_path / "xauusd_paper_shadow_journal_protocol_v0_31.json"

    report = build_xauusd_paper_shadow_journal_protocol_v0_31()
    save_xauusd_paper_shadow_journal_protocol(report, output_path)
    after = candidate_path.read_text(encoding="utf-8")

    assert before == after
    assert report["candidate_rules_modified"] is False
    assert report["candidate_rules_lock"]["rule_change_allowed"] is False


def test_journal_source_introduces_no_execution_order_demo_or_live_paths() -> None:
    source_text_raw = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "src" / "research" / "xauusd_paper_shadow_journal.py",
            ROOT / "scripts" / "build_xauusd_paper_shadow_journal_v0_31.py",
        ]
    )
    source_text = source_text_raw.lower()

    assert "order" + "_send(" not in source_text
    assert "order" + "_check(" not in source_text
    assert "executionqueue" not in source_text
    assert "broker" not in source_text
    assert "demo_allowed\": true" not in source_text
    assert "live_allowed\": true" not in source_text
    assert "execution_allowed\": true" not in source_text
    assert "B" + "UY" not in source_text_raw
    assert "S" + "ELL" not in source_text_raw


def test_journal_protocol_does_not_run_or_repeat_oos() -> None:
    source_text = (ROOT / "src" / "research" / "xauusd_paper_shadow_journal.py").read_text(encoding="utf-8")

    assert "run_xauusd_oos_review_v0_29" not in source_text
    assert "load_oos_rows" not in source_text
    assert "evaluate_oos" not in source_text
    assert "new_oos_run_performed" in source_text
