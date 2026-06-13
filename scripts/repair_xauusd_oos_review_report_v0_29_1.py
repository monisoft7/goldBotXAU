from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research.xauusd_oos_review import (
    CANDIDATE_ID,
    DEFAULT_OUTPUT,
    PASSED_DECISION,
    REVIEW_VERSION,
    SAFETY_FLAGS,
)

REPAIR_VERSION = "v0_29_1"
DEFAULT_MARKER = Path("reports") / "xauusd_oos_review_v0_29.marker.json"
DEFAULT_REPAIR_OUTPUT = Path("reports") / "xauusd_oos_review_repair_v0_29_1.json"
RECOVERY_NOTE = (
    "Original detailed OOS metrics may have been overwritten by the accidental invalid-token rerun. "
    "No detailed OOS metrics were recovered from the current main report, so the repaired report does not invent metrics."
)
NEXT_STEP = (
    "v0_30 post-OOS robustness and paper-shadow protocol design only; caution: detailed OOS metrics were overwritten "
    "unless recovered from an external backup."
)


def repair_xauusd_oos_review_report_v0_29_1(
    *,
    marker_path: str | Path = DEFAULT_MARKER,
    report_path: str | Path = DEFAULT_OUTPUT,
    repair_output_path: str | Path = DEFAULT_REPAIR_OUTPUT,
) -> dict[str, Any]:
    marker_file = Path(marker_path)
    report_file = Path(report_path)
    repair_file = Path(repair_output_path)

    marker = _read_json_object(marker_file, "marker")
    current_report = _read_json_object(report_file, "current_report")
    mismatch_reasons = _mismatch_reasons(marker, current_report)
    overwritten_report_detected = _looks_like_accidental_invalid_token_overwrite(marker, current_report)
    detailed_metrics_available = _detailed_metrics_available(marker, current_report)

    repaired_report = _locked_report_from_marker(
        marker=marker,
        marker_file=marker_file,
        report_file=report_file,
        detailed_metrics_available=detailed_metrics_available,
        overwritten_report_detected=overwritten_report_detected,
    )

    repair_summary = {
        "repair_version": REPAIR_VERSION,
        "repair_decision": "repaired_oos_report_from_locked_marker",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "marker_path": str(marker_file),
        "report_path": str(report_file),
        "repair_output_path": str(repair_file),
        "marker_report_mismatch_detected": bool(mismatch_reasons),
        "mismatch_reasons": mismatch_reasons,
        "overwritten_report_detected": overwritten_report_detected,
        "detailed_oos_metrics_available": detailed_metrics_available,
        "recovery_status": repaired_report["recovery_status"],
        "recovery_note": RECOVERY_NOTE,
        "marker_decision_preserved": marker["decision"],
        "repeat_review_allowed": False,
        "recommended_next_step": NEXT_STEP,
        "restored_main_report": repaired_report,
        "safety": {
            **SAFETY_FLAGS,
            "oos_evaluated": True,
            "one_time_oos_review_completed": True,
            "repeat_review_allowed": False,
        },
    }

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(repaired_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    repair_file.parent.mkdir(parents=True, exist_ok=True)
    repair_file.write_text(json.dumps(repair_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return repair_summary


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label}_missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label}_not_object: {path}")
    return payload


def _mismatch_reasons(marker: dict[str, Any], current_report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if marker.get("review_version") != REVIEW_VERSION:
        reasons.append("marker_review_version_unexpected")
    if marker.get("candidate_id") != CANDIDATE_ID:
        reasons.append("marker_candidate_id_unexpected")
    if marker.get("repeat_review_allowed") is not False:
        reasons.append("marker_repeat_review_allowed_not_false")
    if current_report.get("review_version") != marker.get("review_version"):
        reasons.append("report_review_version_mismatch")
    if current_report.get("candidate_id") != marker.get("candidate_id"):
        reasons.append("report_candidate_id_mismatch")
    if current_report.get("decision") != marker.get("decision"):
        reasons.append("report_decision_mismatch")
    one_time_review = current_report.get("one_time_review")
    if not isinstance(one_time_review, dict):
        reasons.append("report_one_time_review_missing")
    elif one_time_review.get("repeat_review_allowed") is not False:
        reasons.append("report_repeat_review_allowed_not_false")
    if current_report.get("safety", {}).get("one_time_oos_review_completed") is not True:
        reasons.append("report_one_time_completion_not_true")
    return reasons


def _looks_like_accidental_invalid_token_overwrite(
    marker: dict[str, Any],
    current_report: dict[str, Any],
) -> bool:
    return (
        marker.get("repeat_review_allowed") is False
        and marker.get("decision") == PASSED_DECISION
        and current_report.get("decision") == "blocked_missing_or_invalid_approval"
        and "approval_token_missing_or_invalid" in current_report.get("blockers", [])
    )


def _detailed_metrics_available(marker: dict[str, Any], current_report: dict[str, Any]) -> bool:
    if current_report.get("decision") != marker.get("decision"):
        return False
    return isinstance(current_report.get("oos_result"), dict)


def _locked_report_from_marker(
    *,
    marker: dict[str, Any],
    marker_file: Path,
    report_file: Path,
    detailed_metrics_available: bool,
    overwritten_report_detected: bool,
) -> dict[str, Any]:
    return {
        "review_version": marker["review_version"],
        "report_repair_version": REPAIR_VERSION,
        "decision": marker["decision"],
        "candidate_id": marker["candidate_id"],
        "output_path": str(report_file),
        "recovery_status": "locked_report_restored_from_marker_without_detailed_metrics",
        "overwritten_report_detected": overwritten_report_detected,
        "detailed_oos_metrics_available": detailed_metrics_available,
        "detailed_oos_metrics_note": RECOVERY_NOTE,
        "oos_result": None,
        "decision_checks": None,
        "one_time_review": {
            "marker_path": str(marker_file),
            "output_path": str(report_file),
            "repeat_review_allowed": False,
        },
        "candidate_registry_update": {
            "candidate_id": marker["candidate_id"],
            "status": "oos_passed_research_validation_pending_post_oos_protocol",
            "eligible_for_oos_review": False,
            "oos_status": "evaluated_passed",
            "research_only": True,
        },
        "recommended_next_step": NEXT_STEP,
        "safety": {
            **SAFETY_FLAGS,
            "oos_evaluated": True,
            "one_time_oos_review_completed": True,
            "repeat_review_allowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair v0_29 OOS report consistency from the locked marker.")
    parser.add_argument("--marker", type=Path, default=DEFAULT_MARKER)
    parser.add_argument("--report", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json", action="store_true", required=True, dest="as_json")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPAIR_OUTPUT)
    args = parser.parse_args()

    result = repair_xauusd_oos_review_report_v0_29_1(
        marker_path=args.marker,
        report_path=args.report,
        repair_output_path=args.output,
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.as_json:
        print(text)
    else:
        print(f"repair_version={result['repair_version']} repair_decision={result['repair_decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
