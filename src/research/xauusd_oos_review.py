"""v0_29 one-time OOS review for the fixed compression-expansion candidate."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.data.xauusd_csv_loader import load_xauusd_csv
from src.research import xauusd_session_structure_atlas as atlas

REVIEW_VERSION = "v0_29"
CANDIDATE_ID = "xauusd_compression_then_expansion_v0_26"
APPROVAL_TOKEN = "HUMAN_APPROVED_OOS_REVIEW_V0_29"
DEFAULT_PROTOCOL = Path("reports") / "xauusd_oos_review_protocol_v0_28.json"
DEFAULT_OUTPUT = Path("reports") / "xauusd_oos_review_v0_29.json"
DEFAULT_DATA_DIR = Path("data")

PASSED_DECISION = "oos_passed_research_validation"
FAILED_DECISION = "oos_failed_research_validation"
INCONCLUSIVE_DECISION = "oos_inconclusive_research_validation"
BLOCKED_APPROVAL_DECISION = "blocked_missing_or_invalid_approval"
BLOCKED_ALREADY_EVALUATED_DECISION = "blocked_oos_already_evaluated"
BLOCKED_PROTOCOL_DECISION = "blocked_protocol_invalid_or_hash_mismatch"

SAFETY_FLAGS = {
    "demo_enabled": False,
    "live_enabled": False,
    "order_send_allowed": False,
    "order_check_allowed": False,
    "execution_queue_enabled": False,
    "execution_logic_present": False,
    "trade_recommendation_output_present": False,
    "trade_direction_output_present": False,
    "threshold_search_used": False,
    "parameter_grid_used": False,
    "parameter_optimization_used": False,
    "retune_used": False,
    "candidate_rules_modified": False,
    "rejected_candidate_retuned": False,
}


def run_xauusd_oos_review_v0_29(
    *,
    protocol_path: str | Path = DEFAULT_PROTOCOL,
    approval_token: str | None,
    output_path: str | Path = DEFAULT_OUTPUT,
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> dict[str, Any]:
    protocol_file = Path(protocol_path)
    output_file = Path(output_path)
    marker_file = _marker_path(output_file)

    if _marker_locks_repeat_review(marker_file):
        return _blocked_report(
            decision=BLOCKED_ALREADY_EVALUATED_DECISION,
            blockers=["one_time_oos_review_marker_already_exists"],
            protocol_path=protocol_file,
            output_path=output_file,
        )

    if approval_token != APPROVAL_TOKEN:
        return _blocked_report(
            decision=BLOCKED_APPROVAL_DECISION,
            blockers=["approval_token_missing_or_invalid"],
            protocol_path=protocol_file,
            output_path=output_file,
        )

    if output_file.exists() or marker_file.exists():
        blockers = []
        if output_file.exists():
            blockers.append("oos_output_report_already_exists")
        if marker_file.exists():
            blockers.append("one_time_oos_review_marker_already_exists")
        return _blocked_report(
            decision=BLOCKED_ALREADY_EVALUATED_DECISION,
            blockers=blockers,
            protocol_path=protocol_file,
            output_path=output_file,
        )

    protocol, protocol_errors = _load_json(protocol_file, "protocol")
    if protocol_errors:
        return _blocked_report(
            decision=BLOCKED_PROTOCOL_DECISION,
            blockers=protocol_errors,
            protocol_path=protocol_file,
            output_path=output_file,
        )

    blockers = _protocol_blockers(protocol, protocol_file, output_file)
    if blockers:
        return _blocked_report(
            decision=BLOCKED_PROTOCOL_DECISION,
            blockers=blockers,
            protocol_path=protocol_file,
            output_path=output_file,
            protocol=protocol,
        )

    candidate_path = _protocol_path(protocol["source_reports"]["candidate_report"])
    candidate_report, candidate_errors = _load_json(candidate_path, "candidate_report")
    if candidate_errors:
        return _blocked_report(
            decision=BLOCKED_PROTOCOL_DECISION,
            blockers=candidate_errors,
            protocol_path=protocol_file,
            output_path=output_file,
            protocol=protocol,
        )

    manifest_path = _protocol_path(protocol["source_reports"]["dataset_manifest"])
    manifest, manifest_errors = _load_json(manifest_path, "dataset_manifest")
    if manifest_errors:
        return _blocked_report(
            decision=BLOCKED_PROTOCOL_DECISION,
            blockers=manifest_errors,
            protocol_path=protocol_file,
            output_path=output_file,
            protocol=protocol,
        )

    blockers = _source_payload_blockers(protocol, candidate_report, manifest)
    if blockers:
        return _blocked_report(
            decision=BLOCKED_PROTOCOL_DECISION,
            blockers=blockers,
            protocol_path=protocol_file,
            output_path=output_file,
            protocol=protocol,
        )

    oos_rows = _load_oos_rows_from_m1(
        data_dir=Path(data_dir),
        start=protocol["oos_split_boundaries"]["out_of_sample"]["start"],
        end=protocol["oos_split_boundaries"]["out_of_sample"]["end"],
    )
    evidence = _evaluate_oos_rows(oos_rows["rows"])
    checks = _decision_checks(protocol, candidate_report, evidence)
    decision, reasons = _decision_from_checks(checks)
    result = {
        "review_version": REVIEW_VERSION,
        "decision": decision,
        "candidate_id": CANDIDATE_ID,
        "protocol_path": _report_path(protocol_file),
        "approval": {
            "approval_token_required": APPROVAL_TOKEN,
            "approval_token_accepted": True,
        },
        "one_time_review": {
            "marker_path": _report_path(marker_file),
            "output_path": _report_path(output_file),
            "repeat_review_allowed": False,
        },
        "fixed_rules_verification": {
            "rules_hash_sha256": _stable_hash(candidate_report["fixed_rules"]),
            "protocol_rules_hash_sha256": protocol["fixed_rules_source"]["rules_hash_sha256"],
            "hash_match": True,
            "candidate_rules_modified": False,
        },
        "oos_boundaries": protocol["oos_split_boundaries"],
        "oos_data": {
            "source_timeframe": "M1",
            "derived_timeframes": ["M5", "M10"],
            "source_files_used": oos_rows["source_files_used"],
            "source_m1_rows_read": oos_rows["row_count"],
            "oos_rows_evaluated": evidence["combined"]["sample_count"],
            "boundaries_source": "protocol_and_manifest_only",
        },
        "oos_result": evidence,
        "pass_fail_criteria": protocol["pass_fail_criteria"],
        "decision_checks": checks,
        "reasons": reasons,
        "candidate_registry_update": _candidate_registry_update(decision),
        "recommended_next_step": _recommended_next_step(decision),
        "safety": {
            **SAFETY_FLAGS,
            "oos_evaluated": True,
            "one_time_oos_review_completed": True,
        },
    }
    return result


def save_xauusd_oos_review_result(report: dict[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    marker_file = _marker_path(output_file)
    if (
        _marker_locks_repeat_review(marker_file)
        and output_file.exists()
        and report.get("decision") not in {PASSED_DECISION, FAILED_DECISION, INCONCLUSIVE_DECISION}
    ):
        return
    output_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if report.get("decision") in {PASSED_DECISION, FAILED_DECISION, INCONCLUSIVE_DECISION}:
        marker = {
            "review_version": REVIEW_VERSION,
            "candidate_id": CANDIDATE_ID,
            "decision": report["decision"],
            "output_path": _report_path(output_file),
            "repeat_review_allowed": False,
        }
        _marker_path(output_file).write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _marker_locks_repeat_review(marker_file: Path) -> bool:
    marker, errors = _load_json(marker_file, "marker")
    if errors:
        return False
    return marker.get("repeat_review_allowed") is False


def _load_json(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{label}_missing"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{label}_invalid_json: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{label}_not_object"]
    return payload, []


def _protocol_blockers(protocol: dict[str, Any], protocol_path: Path, output_path: Path) -> list[str]:
    blockers: list[str] = []
    if protocol.get("protocol_version") != "v0_28":
        blockers.append("protocol_version_not_v0_28")
    if protocol.get("candidate_id") != CANDIDATE_ID:
        blockers.append("protocol_candidate_id_mismatch")
    allowed = protocol.get("allowed_future_oos_review", {})
    if allowed.get("approval_token_required") != APPROVAL_TOKEN:
        blockers.append("protocol_approval_token_mismatch")
    if _logical_path(allowed.get("script", "")) != "scripts/run_xauusd_oos_review_v0_29.py":
        blockers.append("protocol_future_script_unexpected")
    if _logical_path(allowed.get("result_path", "")) != "reports/xauusd_oos_review_v0_29.json":
        blockers.append("protocol_future_result_path_unexpected")
    if protocol_path != DEFAULT_PROTOCOL:
        expected_command = (
            "py -3 scripts/run_xauusd_oos_review_v0_29.py "
            f"--protocol {protocol_path} --approval-token {APPROVAL_TOKEN} --json --output {output_path}"
        )
    else:
        expected_command = allowed.get("exact_command")
    if protocol_path == DEFAULT_PROTOCOL and allowed.get("exact_command") != (
        "py -3 scripts/run_xauusd_oos_review_v0_29.py "
        "--protocol reports/xauusd_oos_review_protocol_v0_28.json "
        "--approval-token HUMAN_APPROVED_OOS_REVIEW_V0_29 "
        "--json --output reports/xauusd_oos_review_v0_29.json"
    ):
        blockers.append("protocol_exact_command_mismatch")
    if not expected_command:
        blockers.append("protocol_exact_command_missing")
    if protocol.get("one_time_review_policy", {}).get("one_time_only") is not True:
        blockers.append("protocol_one_time_policy_missing")
    if protocol.get("no_retune_policy_after_oos", {}).get("failed_oos_candidate_must_not_be_retuned") is not True:
        blockers.append("protocol_no_retune_policy_missing")
    return blockers


def _source_payload_blockers(
    protocol: dict[str, Any],
    candidate_report: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    fixed_rules = candidate_report.get("fixed_rules", {})
    protocol_rules = protocol.get("fixed_rules_source", {}).get("rules", {})
    if fixed_rules != protocol_rules:
        blockers.append("candidate_rules_do_not_match_protocol_rules")
    expected_hash = protocol.get("fixed_rules_source", {}).get("rules_hash_sha256")
    if _stable_hash(fixed_rules) != expected_hash:
        blockers.append("candidate_rules_hash_mismatch")
    if fixed_rules.get("threshold_search_used") is not False:
        blockers.append("candidate_rules_threshold_search_not_false")
    if fixed_rules.get("parameter_grid_used") is not False:
        blockers.append("candidate_rules_parameter_grid_not_false")
    if fixed_rules.get("retuning_used") is not False:
        blockers.append("candidate_rules_retuning_not_false")

    manifest_policy = manifest.get("split_policy", {})
    protocol_policy = protocol.get("oos_split_boundaries", {}).get("split_policy", {})
    if manifest_policy != protocol_policy:
        blockers.append("manifest_split_policy_mismatch")
    manifest_oos = {
        "start": manifest.get("splits", {}).get("out_of_sample", {}).get("start"),
        "end": manifest.get("splits", {}).get("out_of_sample", {}).get("end"),
    }
    if manifest_oos != protocol.get("oos_split_boundaries", {}).get("out_of_sample"):
        blockers.append("manifest_oos_boundaries_mismatch")
    return blockers


def _load_oos_rows_from_m1(*, data_dir: Path, start: str, end: str) -> dict[str, Any]:
    start_time = datetime.fromisoformat(start)
    end_time = datetime.fromisoformat(end)
    rows_by_timestamp: dict[str, dict[str, Any]] = {}
    source_files: set[str] = set()
    for path in sorted(data_dir.glob("xauusd_m1_*.csv")):
        for row in load_xauusd_csv(path):
            timestamp = datetime.fromisoformat(str(row["timestamp"]))
            if start_time <= timestamp <= end_time:
                rows_by_timestamp[timestamp.isoformat()] = {
                    "timestamp": timestamp.isoformat(),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0.0)),
                }
                source_files.add(path.name)
    rows = [rows_by_timestamp[key] for key in sorted(rows_by_timestamp)]
    return {
        "rows": rows,
        "row_count": len(rows),
        "source_files_used": sorted(source_files),
    }


def _evaluate_oos_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    timeframe_rows = {
        "M5": _aggregate_rows(rows, 5),
        "M10": _aggregate_rows(rows, 10),
    }
    profiler_rows = []
    for timeframe, derived_rows in timeframe_rows.items():
        for row in derived_rows:
            profiler_rows.append(
                {
                    **row,
                    "source_file": "in_memory_oos_m1_derived",
                    "source_timeframe": timeframe,
                    "split": "out_of_sample",
                }
            )
    profiles = atlas._day_profiles(profiler_rows)
    events = [event for profile in profiles if (event := atlas._compression_expansion_event(profile)) is not None]
    combined = atlas._split_result(events)
    by_timeframe = {
        timeframe: atlas._split_result([event for event in events if event["source_timeframe"] == timeframe])
        for timeframe in ["M5", "M10"]
    }
    return {
        "combined": combined,
        "by_timeframe": by_timeframe,
        "derived_bar_counts": {timeframe: len(derived_rows) for timeframe, derived_rows in timeframe_rows.items()},
        "double_counting_assessment": {
            "combined_sample_count_not_treated_as_independent_event_count": True,
            "independent_timeframe_evidence_required": True,
            "timeframe_counts": {
                timeframe: by_timeframe[timeframe]["sample_count"]
                for timeframe in ["M5", "M10"]
            },
        },
    }


def _aggregate_rows(rows: list[dict[str, Any]], minutes: int) -> list[dict[str, Any]]:
    grouped: dict[datetime, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        timestamp = datetime.fromisoformat(str(row["timestamp"]))
        bucket = timestamp.replace(minute=(timestamp.minute // minutes) * minutes, second=0, microsecond=0)
        grouped[bucket].append(row)

    output: list[dict[str, Any]] = []
    for bucket in sorted(grouped):
        bucket_rows = sorted(grouped[bucket], key=lambda row: str(row["timestamp"]))
        expected = [bucket + timedelta(minutes=index) for index in range(minutes)]
        actual = [datetime.fromisoformat(str(row["timestamp"])) for row in bucket_rows]
        if actual != expected:
            continue
        output.append(
            {
                "timestamp": bucket.isoformat(),
                "open": float(bucket_rows[0]["open"]),
                "high": max(float(row["high"]) for row in bucket_rows),
                "low": min(float(row["low"]) for row in bucket_rows),
                "close": float(bucket_rows[-1]["close"]),
                "volume": sum(float(row["volume"]) for row in bucket_rows),
            }
        )
    return output


def _decision_checks(
    protocol: dict[str, Any],
    candidate_report: dict[str, Any],
    evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    criteria = protocol["pass_fail_criteria"]
    validation = candidate_report["validation_result"]
    checks = [
        _check(
            "combined_oos_primary_metric_rate",
            evidence["combined"]["primary_metric_rate"] >= criteria["minimum_combined_oos_primary_metric_rate"],
            observed=evidence["combined"]["primary_metric_rate"],
            required=criteria["minimum_combined_oos_primary_metric_rate"],
        ),
        _check(
            "combined_oos_edge_over_neutral",
            evidence["combined"]["edge_over_neutral"] >= criteria["minimum_combined_oos_edge_over_neutral"],
            observed=evidence["combined"]["edge_over_neutral"],
            required=criteria["minimum_combined_oos_edge_over_neutral"],
        ),
        _check(
            "combined_oos_degradation_vs_validation",
            validation["primary_metric_rate"] - evidence["combined"]["primary_metric_rate"]
            <= criteria["maximum_combined_oos_degradation_vs_validation"],
            observed=validation["primary_metric_rate"] - evidence["combined"]["primary_metric_rate"],
            required=criteria["maximum_combined_oos_degradation_vs_validation"],
        ),
        _check(
            "fixed_reference_response_block_coverage",
            evidence["combined"]["reference_windows"] == criteria["required_reference_windows"]
            and evidence["combined"]["response_windows"] == criteria["required_response_windows"],
            observed={
                "reference_windows": evidence["combined"]["reference_windows"],
                "response_windows": evidence["combined"]["response_windows"],
            },
            required={
                "reference_windows": criteria["required_reference_windows"],
                "response_windows": criteria["required_response_windows"],
            },
        ),
        _check(
            "required_timeframes_present",
            sorted(evidence["by_timeframe"]) == sorted(criteria["required_timeframes"])
            and all(evidence["by_timeframe"][timeframe]["sample_count"] > 0 for timeframe in criteria["required_timeframes"]),
            observed={
                timeframe: evidence["by_timeframe"][timeframe]["sample_count"]
                for timeframe in sorted(evidence["by_timeframe"])
            },
            required=criteria["required_timeframes"],
        ),
    ]
    for timeframe in criteria["required_timeframes"]:
        timeframe_result = evidence["by_timeframe"][timeframe]
        validation_result = candidate_report["timeframe_evidence"]["by_timeframe"][timeframe]["validation_result"]
        checks.extend(
            [
                _check(
                    f"{timeframe}_oos_primary_metric_rate",
                    timeframe_result["primary_metric_rate"] >= criteria["minimum_timeframe_oos_primary_metric_rate"],
                    observed=timeframe_result["primary_metric_rate"],
                    required=criteria["minimum_timeframe_oos_primary_metric_rate"],
                ),
                _check(
                    f"{timeframe}_oos_edge_over_neutral",
                    timeframe_result["edge_over_neutral"] >= criteria["minimum_timeframe_oos_edge_over_neutral"],
                    observed=timeframe_result["edge_over_neutral"],
                    required=criteria["minimum_timeframe_oos_edge_over_neutral"],
                ),
                _check(
                    f"{timeframe}_oos_degradation_vs_validation",
                    validation_result["primary_metric_rate"] - timeframe_result["primary_metric_rate"]
                    <= criteria["maximum_timeframe_oos_degradation_vs_validation"],
                    observed=validation_result["primary_metric_rate"] - timeframe_result["primary_metric_rate"],
                    required=criteria["maximum_timeframe_oos_degradation_vs_validation"],
                ),
            ]
        )
    return checks


def _decision_from_checks(checks: list[dict[str, Any]]) -> tuple[str, list[str]]:
    failed = [check["check"] for check in checks if check["status"] == "failed"]
    inconclusive_failures = {
        "required_timeframes_present",
        "fixed_reference_response_block_coverage",
    }
    if not failed:
        return PASSED_DECISION, ["All fixed OOS pass/fail criteria were met."]
    if any(name in inconclusive_failures for name in failed):
        return INCONCLUSIVE_DECISION, [
            "OOS evidence quality or fixed block coverage was insufficient for a clean pass/fail decision.",
            f"Failed checks: {', '.join(failed)}",
        ]
    return FAILED_DECISION, [
        "One or more fixed OOS performance criteria failed.",
        f"Failed checks: {', '.join(failed)}",
    ]


def _candidate_registry_update(decision: str) -> dict[str, Any]:
    if decision == FAILED_DECISION:
        return {
            "candidate_id": CANDIDATE_ID,
            "status": "rejected_oos_failed",
            "eligible_for_oos_review": False,
            "oos_status": "evaluated_failed",
            "do_not_retune": True,
            "threshold_search_used": False,
            "parameter_grid_used": False,
            "retuned_rejected_candidate": False,
        }
    if decision == PASSED_DECISION:
        return {
            "candidate_id": CANDIDATE_ID,
            "status": "oos_passed_research_validation_pending_post_oos_protocol",
            "eligible_for_oos_review": False,
            "oos_status": "evaluated_passed",
            "research_only": True,
        }
    return {
        "candidate_id": CANDIDATE_ID,
        "status": "oos_inconclusive_research_validation",
        "eligible_for_oos_review": False,
        "oos_status": "evaluated_inconclusive",
        "do_not_retune": True,
    }


def _recommended_next_step(decision: str) -> str:
    if decision == PASSED_DECISION:
        return "v0_30 post-OOS robustness and paper-shadow protocol design only"
    if decision == FAILED_DECISION:
        return "move to a new research family such as intermarket or news/event atlas"
    return "governance review or abandon depending on evidence quality"


def _blocked_report(
    *,
    decision: str,
    blockers: list[str],
    protocol_path: Path,
    output_path: Path,
    protocol: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "review_version": REVIEW_VERSION,
        "decision": decision,
        "candidate_id": CANDIDATE_ID,
        "protocol_path": _report_path(protocol_path),
        "output_path": _report_path(output_path),
        "blockers": blockers,
        "protocol_version": protocol.get("protocol_version") if protocol else None,
        "oos_result": None,
        "candidate_registry_update": None,
        "recommended_next_step": "resolve blocker before any OOS evaluation",
        "safety": {
            **SAFETY_FLAGS,
            "oos_evaluated": False,
            "one_time_oos_review_completed": False,
        },
    }


def _check(name: str, passed: bool, *, observed: Any, required: Any | None = None) -> dict[str, Any]:
    check = {
        "check": name,
        "status": "passed" if passed else "failed",
        "observed": observed,
    }
    if required is not None:
        check["required"] = required
    return check


def _marker_path(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.stem}.marker.json")


def _logical_path(value: object) -> str:
    return str(value).replace("\\", "/")


def _protocol_path(value: object) -> Path:
    return Path(_logical_path(value))


def _report_path(path: Path) -> str:
    return path.as_posix()


def _stable_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
