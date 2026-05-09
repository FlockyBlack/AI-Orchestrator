from __future__ import annotations

import argparse
import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pm_bot.simulated_decisions.audit_ledger import (
    AUDIT_LEDGER_CONTRACT_VERSION,
    AUDIT_LEDGER_STATE,
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    validate_simulated_decision_audit_ledger,
)
from pm_bot.simulated_decisions.schema import (
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    PACKET_STATE,
    SIMULATED_DECISION_PACKET_CONTRACT_VERSION,
    validate_simulated_decision_packet,
)

REPLAY_SUMMARY_REQUEST_CONTRACT_VERSION = "pmbot_simulated_decision_replay_summary_request.v1"
REPLAY_SUMMARY_CONTRACT_VERSION = "pmbot_simulated_decision_replay_summary.v1"
REPLAY_SUMMARY_SCHEMA_ID = "pmbot_simulated_decision_replay_summary_schema.v1"
REPLAY_SUMMARY_STATE = "recorded_for_operator_review"

_PACKAGE_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _PACKAGE_DIR.parents[1]
REPLAY_SUMMARY_SCHEMA_PATH = _PACKAGE_DIR / "schemas" / "simulated_decision_replay_summary.schema.v1.json"
SAMPLE_REPLAY_SUMMARY_PATH = _PACKAGE_DIR / "samples" / "simulated_decision_replay_summary.fixture.json"
_ALLOWED_LOCAL_REFERENCE_PREFIXES = ("pm_bot/simulated_decisions/", "pm_bot/tests/fixtures/")
_ID_RE = re.compile(r"^[a-z0-9_.-]+$")
_UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_FORBIDDEN_OUTPUT_TOKENS = frozenset(
    {
        "advice",
        "buy",
        "confidence",
        "edge",
        "enter",
        "ev",
        "exit",
        "forecast",
        "guidance",
        "hold",
        "odds",
        "pick",
        "probability",
        "recommendation",
        "score",
        "scoring",
        "selection",
        "sell",
        "side",
        "stake",
        "wager",
    }
)


@dataclass(frozen=True)
class SimulatedDecisionReplaySummaryValidationResult:
    valid: bool
    errors: tuple[str, ...]


class SimulatedDecisionReplaySummaryValidationError(ValueError):
    """Raised when a local simulated decision replay summary request is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


SIMULATED_DECISION_REPLAY_SUMMARY_SCHEMA = _load_json(REPLAY_SUMMARY_SCHEMA_PATH)
SIMULATED_DECISION_REPLAY_SUMMARY_FIXTURE = _load_json(SAMPLE_REPLAY_SUMMARY_PATH)


def build_simulated_decision_replay_summary_schema() -> dict[str, Any]:
    """Return a detached copy of the local replay summary schema artifact."""

    return deepcopy(SIMULATED_DECISION_REPLAY_SUMMARY_SCHEMA)


def example_simulated_decision_replay_summary() -> dict[str, Any]:
    """Return a detached copy of the static local replay summary fixture."""

    return deepcopy(SIMULATED_DECISION_REPLAY_SUMMARY_FIXTURE)


def load_replay_summary_request(path: Path | str) -> dict[str, Any]:
    return _load_json(Path(path))


def validate_replay_summary_request(request: Any) -> SimulatedDecisionReplaySummaryValidationResult:
    errors: list[str] = []
    if not isinstance(request, dict):
        return SimulatedDecisionReplaySummaryValidationResult(False, ("request must be an object",))

    required = (
        "contract_version",
        "summary_id",
        "created_at",
        "replay_scope",
        "local_only",
        "operator_review_required",
        "source_audit_ledgers",
        "replay_checks",
        "operator_review_steps",
    )
    _require_exact_fields(request, required, "$", errors)
    _require_value(
        request,
        "contract_version",
        REPLAY_SUMMARY_REQUEST_CONTRACT_VERSION,
        "$.contract_version",
        errors,
    )
    _require_local_id(request.get("summary_id"), "$.summary_id", errors)
    _require_utc_timestamp(request.get("created_at"), "$.created_at", errors)
    _require_non_empty_string(request.get("replay_scope"), "$.replay_scope", errors)
    _require_value(request, "local_only", True, "$.local_only", errors)
    _require_value(request, "operator_review_required", True, "$.operator_review_required", errors)
    _validate_source_audit_ledgers(request.get("source_audit_ledgers"), errors)
    _validate_replay_checks(request.get("replay_checks"), errors)
    _validate_string_array(request.get("operator_review_steps"), "$.operator_review_steps", errors)

    for path in _find_forbidden_output_terms(request):
        errors.append(f"forbidden output field detected in replay request at {path}")

    return SimulatedDecisionReplaySummaryValidationResult(not errors, tuple(errors))


def build_simulated_decision_replay_summary(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_replay_summary_request(request)
    if not validation.valid:
        raise SimulatedDecisionReplaySummaryValidationError("; ".join(validation.errors))

    source_ledgers = _load_source_ledgers(request)
    build_id = f"{request['summary_id']}-{_stable_digest({'request': request, 'source_ledgers': source_ledgers})[:12]}"
    source_ledger_rows = _build_source_ledger_rows(source_ledgers)
    source_packet_rows = _build_source_packet_rows(source_ledgers)
    record_section_rows = _build_record_section_rows(source_ledgers)
    local_reference_rows = _build_local_reference_rows(source_ledgers)
    replay_check_rows = _build_replay_check_rows(request)
    warnings: list[str] = []
    errors: list[str] = []

    summary = {
        "contract_version": REPLAY_SUMMARY_CONTRACT_VERSION,
        "summary_id": request["summary_id"],
        "build_id": build_id,
        "created_at": request["created_at"],
        "replay_scope": request["replay_scope"],
        "run_mode": LOCAL_RUN_MODE,
        "local_only": True,
        "operator_review_required": True,
        "summary_state": REPLAY_SUMMARY_STATE,
        "source_ledger_rows": source_ledger_rows,
        "source_packet_rows": source_packet_rows,
        "record_section_rows": record_section_rows,
        "local_reference_rows": local_reference_rows,
        "replay_check_rows": replay_check_rows,
        "summary_counts": {
            "source_ledgers": len(source_ledger_rows),
            "source_packets": len(source_packet_rows),
            "record_section_rows": len(record_section_rows),
            "local_references": len(local_reference_rows),
            "replay_checks": len(replay_check_rows),
            "warnings": len(warnings),
            "errors": len(errors),
        },
        "operator_review": {
            "status": OPERATOR_REVIEW_STATUS,
            "reviewed_by": None,
            "reviewed_at": None,
            "notes": [],
        },
        "safety_boundaries": deepcopy(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "warnings": warnings,
        "errors": errors,
    }
    output_validation = validate_simulated_decision_replay_summary(summary)
    if not output_validation.valid:
        raise SimulatedDecisionReplaySummaryValidationError("; ".join(output_validation.errors))
    return summary


def validate_simulated_decision_replay_summary(summary: Any) -> SimulatedDecisionReplaySummaryValidationResult:
    errors: list[str] = []
    if not isinstance(summary, dict):
        return SimulatedDecisionReplaySummaryValidationResult(False, ("summary must be an object",))

    required = tuple(SIMULATED_DECISION_REPLAY_SUMMARY_SCHEMA["required_fields"])
    _require_exact_fields(summary, required, "$", errors)
    _require_value(summary, "contract_version", REPLAY_SUMMARY_CONTRACT_VERSION, "$.contract_version", errors)
    _require_local_id(summary.get("summary_id"), "$.summary_id", errors)
    _require_non_empty_string(summary.get("build_id"), "$.build_id", errors)
    _require_utc_timestamp(summary.get("created_at"), "$.created_at", errors)
    _require_non_empty_string(summary.get("replay_scope"), "$.replay_scope", errors)
    _require_value(summary, "run_mode", LOCAL_RUN_MODE, "$.run_mode", errors)
    _require_value(summary, "local_only", True, "$.local_only", errors)
    _require_value(summary, "operator_review_required", True, "$.operator_review_required", errors)
    _require_value(summary, "summary_state", REPLAY_SUMMARY_STATE, "$.summary_state", errors)

    _validate_source_ledger_rows(summary.get("source_ledger_rows"), errors)
    _validate_source_packet_rows(summary.get("source_packet_rows"), errors)
    _validate_status_rows(summary.get("record_section_rows"), "$.record_section_rows", errors)
    _validate_reference_rows(summary.get("local_reference_rows"), errors)
    _validate_status_rows(summary.get("replay_check_rows"), "$.replay_check_rows", errors)
    _validate_summary_counts(summary, errors)
    _validate_operator_review(summary.get("operator_review"), errors)
    _validate_safety_boundaries(summary.get("safety_boundaries"), errors)
    _validate_string_array(summary.get("warnings"), "$.warnings", errors)
    _validate_string_array(summary.get("errors"), "$.errors", errors)

    for path in _find_forbidden_output_terms(summary):
        errors.append(f"forbidden output field detected in replay summary at {path}")

    return SimulatedDecisionReplaySummaryValidationResult(not errors, tuple(errors))


def build_operator_report(summary: dict[str, Any]) -> str:
    validation = validate_simulated_decision_replay_summary(summary)
    if not validation.valid:
        raise SimulatedDecisionReplaySummaryValidationError("; ".join(validation.errors))

    lines = [
        "# PMBOT Simulated Decision Replay Summary",
        "",
        f"Summary: `{summary['summary_id']}`",
        f"Build: `{summary['build_id']}`",
        f"Run mode: `{summary['run_mode']}`",
        f"Operator review: `{summary['operator_review']['status']}`",
        "",
        "## Summary Counts",
    ]
    for key, value in summary["summary_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Source Audit Ledgers",
        ]
    )
    for row in summary["source_ledger_rows"]:
        lines.append(
            "- "
            f"{row['source_ledger_id']} | packets: {row['source_packet_count']} | "
            f"sections: {row['record_section_row_count']} | review: {row['operator_review_status']}"
        )
    lines.extend(
        [
            "",
            "## Source Packets",
        ]
    )
    for row in summary["source_packet_rows"]:
        lines.append(
            "- "
            f"{row['source_packet_id']} | sections: {row['record_section_count']} | "
            f"observations: {row['observation_count']} | review: {row['operator_review_status']}"
        )
    lines.extend(
        [
            "",
            "## Local References",
        ]
    )
    for row in summary["local_reference_rows"]:
        lines.append(f"- {row['reference_role']}: `{row['local_reference']}` | exists: {row['reference_exists']}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, worker, scheduler, or browser calls.",
            "- Descriptive simulated record replay only; not runtime input or execution approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT simulated decision replay summary.")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--output-summary", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    args = parser.parse_args(argv)

    request = load_replay_summary_request(args.request)
    summary = build_simulated_decision_replay_summary(request)
    report = build_operator_report(summary)

    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_report.write_text(report, encoding="utf-8")
    return 0


def _load_source_ledgers(request: dict[str, Any]) -> list[dict[str, Any]]:
    ledgers: list[dict[str, Any]] = []
    for index, source in enumerate(request["source_audit_ledgers"]):
        reference = source["local_reference"]
        ledger_path = (_WORKSPACE_ROOT / reference).resolve()
        ledger = _load_json(ledger_path)
        validation = validate_simulated_decision_audit_ledger(ledger)
        if not validation.valid:
            raise SimulatedDecisionReplaySummaryValidationError(
                f"source_audit_ledgers[{index}] ledger failed validation: {'; '.join(validation.errors)}"
            )
        if ledger["ledger_id"] != source["source_ledger_id"]:
            raise SimulatedDecisionReplaySummaryValidationError(
                f"source_audit_ledgers[{index}].source_ledger_id must match the local ledger id"
            )
        ledgers.append(
            {
                "request_source": deepcopy(source),
                "ledger": ledger,
                "source_packets": _load_source_packets(ledger),
            }
        )
    return ledgers


def _load_source_packets(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for index, inventory_row in enumerate(ledger["source_inventory"]):
        packet_path = (_WORKSPACE_ROOT / inventory_row["local_reference"]).resolve()
        packet = _load_json(packet_path)
        validation = validate_simulated_decision_packet(packet)
        if not validation.valid:
            raise SimulatedDecisionReplaySummaryValidationError(
                f"source_inventory[{index}] packet failed validation: {'; '.join(validation.errors)}"
            )
        if packet["packet_id"] != inventory_row["source_packet_id"]:
            raise SimulatedDecisionReplaySummaryValidationError(
                f"source_inventory[{index}].source_packet_id must match the local packet id"
            )
        packets.append({"inventory_row": deepcopy(inventory_row), "packet": packet})
    return packets


def _build_source_ledger_rows(source_ledgers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_ledgers:
        source = loaded["request_source"]
        ledger = loaded["ledger"]
        rows.append(
            {
                "row_id": f"{ledger['ledger_id']}.source_audit_ledger",
                "source_ledger_id": source["source_ledger_id"],
                "source_ledger_label": source["source_ledger_label"],
                "local_reference": source["local_reference"],
                "artifact_loaded": True,
                "contract_version": ledger["contract_version"],
                "ledger_state": ledger["ledger_state"],
                "source_packet_count": ledger["summary_counts"]["source_packets"],
                "audit_row_count": ledger["summary_counts"]["audit_rows"],
                "record_section_row_count": ledger["summary_counts"]["record_section_rows"],
                "warning_count": len(ledger["warnings"]),
                "error_count": len(ledger["errors"]),
                "operator_review_status": source["operator_review_status"],
                "row_state": REPLAY_SUMMARY_STATE,
            }
        )
    return rows


def _build_source_packet_rows(source_ledgers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_ledgers:
        ledger = loaded["ledger"]
        for source_packet in loaded["source_packets"]:
            inventory_row = source_packet["inventory_row"]
            packet = source_packet["packet"]
            rows.append(
                {
                    "row_id": f"{ledger['ledger_id']}.{packet['packet_id']}.source_packet",
                    "source_ledger_id": ledger["ledger_id"],
                    "source_packet_id": packet["packet_id"],
                    "source_packet_label": inventory_row["source_packet_label"],
                    "local_reference": inventory_row["local_reference"],
                    "artifact_loaded": True,
                    "contract_version": packet["contract_version"],
                    "packet_state": packet["packet_state"],
                    "record_section_count": len(packet["record_sections"]),
                    "observation_count": sum(len(section["observations"]) for section in packet["record_sections"]),
                    "warning_count": len(packet["warnings"]),
                    "error_count": len(packet["errors"]),
                    "operator_review_status": inventory_row["operator_review_status"],
                    "row_state": REPLAY_SUMMARY_STATE,
                }
            )
    return rows


def _build_record_section_rows(source_ledgers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_ledgers:
        ledger = loaded["ledger"]
        for source_packet in loaded["source_packets"]:
            packet = source_packet["packet"]
            local_reference = source_packet["inventory_row"]["local_reference"]
            for section in packet["record_sections"]:
                source_artifact_ids = sorted(
                    {
                        artifact_id
                        for observation in section["observations"]
                        for artifact_id in observation["source_artifact_ids"]
                    }
                )
                rows.append(
                    {
                        "row_id": f"{ledger['ledger_id']}.{packet['packet_id']}.{section['section_id']}",
                        "source_ledger_id": ledger["ledger_id"],
                        "source_packet_id": packet["packet_id"],
                        "section_id": section["section_id"],
                        "section_label": section["section_label"],
                        "local_reference": local_reference,
                        "observation_count": len(section["observations"]),
                        "source_artifact_ids": source_artifact_ids,
                        "operator_review_status": section["operator_review_status"],
                        "row_state": REPLAY_SUMMARY_STATE,
                    }
                )
    return rows


def _build_local_reference_rows(source_ledgers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_ledgers:
        source = loaded["request_source"]
        ledger = loaded["ledger"]
        rows.append(
            {
                "row_id": f"{ledger['ledger_id']}.source_audit_ledger",
                "source_ledger_id": ledger["ledger_id"],
                "reference_role": "source_audit_ledger",
                "local_reference": source["local_reference"],
                "reference_exists": (_WORKSPACE_ROOT / source["local_reference"]).resolve().exists(),
                "operator_review_status": OPERATOR_REVIEW_STATUS,
                "row_state": REPLAY_SUMMARY_STATE,
            }
        )
        for reference_row in ledger["local_reference_rows"]:
            row = {
                "row_id": f"{ledger['ledger_id']}.{reference_row['row_id']}",
                "source_ledger_id": ledger["ledger_id"],
                "reference_role": reference_row["reference_role"],
                "local_reference": reference_row["local_reference"],
                "reference_exists": (_WORKSPACE_ROOT / reference_row["local_reference"]).resolve().exists(),
                "operator_review_status": reference_row["operator_review_status"],
                "row_state": REPLAY_SUMMARY_STATE,
            }
            if "source_packet_id" in reference_row:
                row["source_packet_id"] = reference_row["source_packet_id"]
            rows.append(row)
    return rows


def _build_replay_check_rows(request: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": check["check_id"],
            "check_id": check["check_id"],
            "description": check["description"],
            "operator_review_status": check["operator_review_status"],
            "row_state": REPLAY_SUMMARY_STATE,
        }
        for check in request["replay_checks"]
    ]


def _validate_source_audit_ledgers(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("$.source_audit_ledgers must be a non-empty array")
        return
    required = ("source_ledger_id", "source_ledger_label", "local_reference", "operator_review_status")
    seen: set[str] = set()
    for index, source in enumerate(value):
        path = f"$.source_audit_ledgers[{index}]"
        if not _require_object(source, path, errors):
            continue
        _require_exact_fields(source, required, path, errors)
        _require_local_id(source.get("source_ledger_id"), f"{path}.source_ledger_id", errors)
        _require_non_empty_string(source.get("source_ledger_label"), f"{path}.source_ledger_label", errors)
        _require_value(source, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _validate_local_reference(source.get("local_reference"), f"{path}.local_reference", errors)
        if isinstance(source.get("source_ledger_id"), str):
            if source["source_ledger_id"] in seen:
                errors.append(f"{path}.source_ledger_id must be unique")
            seen.add(source["source_ledger_id"])


def _validate_replay_checks(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("$.replay_checks must be a non-empty array")
        return
    required = ("check_id", "description", "operator_review_status")
    seen: set[str] = set()
    for index, check in enumerate(value):
        path = f"$.replay_checks[{index}]"
        if not _require_object(check, path, errors):
            continue
        _require_exact_fields(check, required, path, errors)
        _require_local_id(check.get("check_id"), f"{path}.check_id", errors)
        _require_non_empty_string(check.get("description"), f"{path}.description", errors)
        _require_value(check, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        if isinstance(check.get("check_id"), str):
            if check["check_id"] in seen:
                errors.append(f"{path}.check_id must be unique")
            seen.add(check["check_id"])


def _validate_source_ledger_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.source_ledger_rows must be an array")
        return
    for index, row in enumerate(value):
        path = f"$.source_ledger_rows[{index}]"
        if not _require_object(row, path, errors):
            continue
        _require_value(row, "contract_version", AUDIT_LEDGER_CONTRACT_VERSION, f"{path}.contract_version", errors)
        _require_value(row, "ledger_state", AUDIT_LEDGER_STATE, f"{path}.ledger_state", errors)
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(row, "row_state", REPLAY_SUMMARY_STATE, f"{path}.row_state", errors)
        _validate_local_reference(row.get("local_reference"), f"{path}.local_reference", errors)


def _validate_source_packet_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.source_packet_rows must be an array")
        return
    for index, row in enumerate(value):
        path = f"$.source_packet_rows[{index}]"
        if not _require_object(row, path, errors):
            continue
        _require_value(row, "contract_version", SIMULATED_DECISION_PACKET_CONTRACT_VERSION, f"{path}.contract_version", errors)
        _require_value(row, "packet_state", PACKET_STATE, f"{path}.packet_state", errors)
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(row, "row_state", REPLAY_SUMMARY_STATE, f"{path}.row_state", errors)
        _validate_local_reference(row.get("local_reference"), f"{path}.local_reference", errors)


def _validate_status_rows(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return
    for index, row in enumerate(value):
        row_path = f"{path}[{index}]"
        if not _require_object(row, row_path, errors):
            continue
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{row_path}.operator_review_status", errors)
        _require_value(row, "row_state", REPLAY_SUMMARY_STATE, f"{row_path}.row_state", errors)
        if "local_reference" in row:
            _validate_local_reference(row.get("local_reference"), f"{row_path}.local_reference", errors)


def _validate_reference_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.local_reference_rows must be an array")
        return
    for index, row in enumerate(value):
        path = f"$.local_reference_rows[{index}]"
        if not _require_object(row, path, errors):
            continue
        _require_value(row, "reference_exists", True, f"{path}.reference_exists", errors)
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(row, "row_state", REPLAY_SUMMARY_STATE, f"{path}.row_state", errors)
        _validate_local_reference(row.get("local_reference"), f"{path}.local_reference", errors)


def _validate_summary_counts(summary: dict[str, Any], errors: list[str]) -> None:
    value = summary.get("summary_counts")
    if not _require_object(value, "$.summary_counts", errors):
        return
    expected = {
        "source_ledgers": (
            len(summary.get("source_ledger_rows")) if isinstance(summary.get("source_ledger_rows"), list) else 0
        ),
        "source_packets": (
            len(summary.get("source_packet_rows")) if isinstance(summary.get("source_packet_rows"), list) else 0
        ),
        "record_section_rows": (
            len(summary.get("record_section_rows")) if isinstance(summary.get("record_section_rows"), list) else 0
        ),
        "local_references": (
            len(summary.get("local_reference_rows")) if isinstance(summary.get("local_reference_rows"), list) else 0
        ),
        "replay_checks": (
            len(summary.get("replay_check_rows")) if isinstance(summary.get("replay_check_rows"), list) else 0
        ),
        "warnings": len(summary.get("warnings")) if isinstance(summary.get("warnings"), list) else 0,
        "errors": len(summary.get("errors")) if isinstance(summary.get("errors"), list) else 0,
    }
    _require_exact_fields(value, tuple(expected), "$.summary_counts", errors)
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            errors.append(f"$.summary_counts.{field} must match replay summary content: {expected_value}")


def _validate_operator_review(value: Any, errors: list[str]) -> None:
    if not _require_object(value, "$.operator_review", errors):
        return
    required = ("status", "reviewed_by", "reviewed_at", "notes")
    _require_exact_fields(value, required, "$.operator_review", errors)
    _require_value(value, "status", OPERATOR_REVIEW_STATUS, "$.operator_review.status", errors)
    if value.get("reviewed_by") is not None:
        errors.append("$.operator_review.reviewed_by must be null before operator review")
    if value.get("reviewed_at") is not None:
        errors.append("$.operator_review.reviewed_at must be null before operator review")
    _validate_string_array(value.get("notes"), "$.operator_review.notes", errors)


def _validate_safety_boundaries(value: Any, errors: list[str]) -> None:
    if value != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("$.safety_boundaries must match the closed local-only safety boundary contract")


def _require_object(value: Any, path: str, errors: list[str]) -> bool:
    if isinstance(value, dict):
        return True
    errors.append(f"{path} must be an object")
    return False


def _require_exact_fields(value: dict[str, Any], required_fields: tuple[str, ...], path: str, errors: list[str]) -> None:
    required = set(required_fields)
    present = set(value)
    missing = sorted(required - present)
    unexpected = sorted(present - required)
    if missing:
        errors.append(f"{path} missing required fields: {', '.join(missing)}")
    if unexpected:
        errors.append(f"{path} has unexpected fields: {', '.join(unexpected)}")


def _require_value(value: dict[str, Any], field: str, expected: Any, path: str, errors: list[str]) -> None:
    if value.get(field) != expected:
        errors.append(f"{path} must be {expected!r}")


def _require_non_empty_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{path} must be a non-empty string")


def _require_local_id(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        errors.append(f"{path} must be a lowercase local identifier")


def _require_utc_timestamp(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not _UTC_TIMESTAMP_RE.fullmatch(value):
        errors.append(f"{path} must be a UTC timestamp formatted as YYYY-MM-DDTHH:MM:SSZ")


def _validate_string_array(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(f"{path}[{index}] must be a string")


def _validate_local_reference(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{path} must be a non-empty local reference")
        return
    if "://" in value or Path(value).is_absolute() or ".." in Path(value).parts:
        errors.append(f"{path} must be a local repository-relative reference")
        return
    if not value.startswith(_ALLOWED_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{path} must stay under simulated decision allowed local paths")
        return

    resolved = (_WORKSPACE_ROOT / value).resolve()
    try:
        resolved.relative_to(_WORKSPACE_ROOT)
    except ValueError:
        errors.append(f"{path} must stay inside the local workspace")
        return
    if not resolved.exists():
        errors.append(f"{path} must point to an existing local artifact")


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _find_forbidden_output_terms(value: Any, path: str = "$") -> tuple[str, ...]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_token(str(key)):
                hits.append(key_path)
            hits.extend(_find_forbidden_output_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_output_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_token(value):
        hits.append(path)
    return tuple(hits)


def _has_forbidden_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & _FORBIDDEN_OUTPUT_TOKENS)


if __name__ == "__main__":
    raise SystemExit(main())
