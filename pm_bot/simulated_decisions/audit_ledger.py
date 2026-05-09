from __future__ import annotations

import argparse
import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pm_bot.simulated_decisions.schema import (
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    PACKET_STATE,
    SIMULATED_DECISION_PACKET_CONTRACT_VERSION,
    SIMULATED_DECISION_PACKET_SCHEMA,
    validate_simulated_decision_packet,
)

AUDIT_LEDGER_REQUEST_CONTRACT_VERSION = "pmbot_simulated_decision_audit_ledger_request.v1"
AUDIT_LEDGER_CONTRACT_VERSION = "pmbot_simulated_decision_audit_ledger.v1"
AUDIT_LEDGER_SCHEMA_ID = "pmbot_simulated_decision_audit_ledger_schema.v1"
AUDIT_LEDGER_STATE = "recorded_for_operator_review"

_PACKAGE_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _PACKAGE_DIR.parents[1]
AUDIT_LEDGER_SCHEMA_PATH = _PACKAGE_DIR / "schemas" / "simulated_decision_audit_ledger.schema.v1.json"
SAMPLE_AUDIT_LEDGER_PATH = _PACKAGE_DIR / "samples" / "simulated_decision_audit_ledger.fixture.json"
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

LOCAL_ONLY_SAFETY_BOUNDARIES = deepcopy(SIMULATED_DECISION_PACKET_SCHEMA["safety_boundaries"])


@dataclass(frozen=True)
class SimulatedDecisionAuditLedgerValidationResult:
    valid: bool
    errors: tuple[str, ...]


class SimulatedDecisionAuditLedgerValidationError(ValueError):
    """Raised when a local simulated decision audit ledger request is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


SIMULATED_DECISION_AUDIT_LEDGER_SCHEMA = _load_json(AUDIT_LEDGER_SCHEMA_PATH)
SIMULATED_DECISION_AUDIT_LEDGER_FIXTURE = _load_json(SAMPLE_AUDIT_LEDGER_PATH)


def build_simulated_decision_audit_ledger_schema() -> dict[str, Any]:
    """Return a detached copy of the local audit ledger schema artifact."""

    return deepcopy(SIMULATED_DECISION_AUDIT_LEDGER_SCHEMA)


def example_simulated_decision_audit_ledger() -> dict[str, Any]:
    """Return a detached copy of the static local audit ledger fixture."""

    return deepcopy(SIMULATED_DECISION_AUDIT_LEDGER_FIXTURE)


def load_audit_request(path: Path | str) -> dict[str, Any]:
    return _load_json(Path(path))


def validate_audit_request(request: Any) -> SimulatedDecisionAuditLedgerValidationResult:
    errors: list[str] = []
    if not isinstance(request, dict):
        return SimulatedDecisionAuditLedgerValidationResult(False, ("request must be an object",))

    required = (
        "contract_version",
        "ledger_id",
        "created_at",
        "scope",
        "local_only",
        "operator_review_required",
        "source_packets",
        "audit_requirements",
        "operator_review_steps",
    )
    _require_exact_fields(request, required, "$", errors)
    _require_value(
        request,
        "contract_version",
        AUDIT_LEDGER_REQUEST_CONTRACT_VERSION,
        "$.contract_version",
        errors,
    )
    _require_value(request, "local_only", True, "$.local_only", errors)
    _require_value(request, "operator_review_required", True, "$.operator_review_required", errors)
    _require_local_id(request.get("ledger_id"), "$.ledger_id", errors)
    _require_utc_timestamp(request.get("created_at"), "$.created_at", errors)
    _require_non_empty_string(request.get("scope"), "$.scope", errors)
    _validate_source_packets(request.get("source_packets"), errors)
    _validate_audit_requirements(request.get("audit_requirements"), errors)
    _validate_string_array(request.get("operator_review_steps"), "$.operator_review_steps", errors)

    for path in _find_forbidden_output_terms(request):
        errors.append(f"forbidden scoring/action field detected in audit request at {path}")

    return SimulatedDecisionAuditLedgerValidationResult(not errors, tuple(errors))


def build_simulated_decision_audit_ledger(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_audit_request(request)
    if not validation.valid:
        raise SimulatedDecisionAuditLedgerValidationError("; ".join(validation.errors))

    source_packets = _load_source_packets(request)
    build_id = f"{request['ledger_id']}-{_stable_digest({'request': request, 'source_packets': source_packets})[:12]}"
    source_inventory = _build_source_inventory(request, source_packets)
    audit_rows = _build_audit_rows(source_packets)
    record_section_rows = _build_record_section_rows(source_packets)
    local_reference_rows = _build_local_reference_rows(source_packets)
    audit_requirement_rows = _build_audit_requirement_rows(request)
    warnings: list[str] = []
    errors: list[str] = []

    ledger = {
        "contract_version": AUDIT_LEDGER_CONTRACT_VERSION,
        "ledger_id": request["ledger_id"],
        "build_id": build_id,
        "created_at": request["created_at"],
        "scope": request["scope"],
        "run_mode": LOCAL_RUN_MODE,
        "local_only": True,
        "operator_review_required": True,
        "ledger_state": AUDIT_LEDGER_STATE,
        "source_inventory": source_inventory,
        "audit_rows": audit_rows,
        "record_section_rows": record_section_rows,
        "local_reference_rows": local_reference_rows,
        "audit_requirement_rows": audit_requirement_rows,
        "summary_counts": {
            "source_packets": len(source_inventory),
            "audit_rows": len(audit_rows),
            "record_section_rows": len(record_section_rows),
            "local_references": len(local_reference_rows),
            "audit_requirements": len(audit_requirement_rows),
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
    output_validation = validate_simulated_decision_audit_ledger(ledger)
    if not output_validation.valid:
        raise SimulatedDecisionAuditLedgerValidationError("; ".join(output_validation.errors))
    return ledger


def validate_simulated_decision_audit_ledger(ledger: Any) -> SimulatedDecisionAuditLedgerValidationResult:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return SimulatedDecisionAuditLedgerValidationResult(False, ("ledger must be an object",))

    required = tuple(SIMULATED_DECISION_AUDIT_LEDGER_SCHEMA["required_fields"])
    _require_exact_fields(ledger, required, "$", errors)
    _require_value(ledger, "contract_version", AUDIT_LEDGER_CONTRACT_VERSION, "$.contract_version", errors)
    _require_value(ledger, "run_mode", LOCAL_RUN_MODE, "$.run_mode", errors)
    _require_value(ledger, "local_only", True, "$.local_only", errors)
    _require_value(ledger, "operator_review_required", True, "$.operator_review_required", errors)
    _require_value(ledger, "ledger_state", AUDIT_LEDGER_STATE, "$.ledger_state", errors)
    _require_local_id(ledger.get("ledger_id"), "$.ledger_id", errors)
    _require_utc_timestamp(ledger.get("created_at"), "$.created_at", errors)
    _require_non_empty_string(ledger.get("scope"), "$.scope", errors)
    _require_non_empty_string(ledger.get("build_id"), "$.build_id", errors)

    _validate_source_inventory_rows(ledger.get("source_inventory"), errors)
    _validate_status_rows(ledger.get("audit_rows"), "$.audit_rows", errors)
    _validate_status_rows(ledger.get("record_section_rows"), "$.record_section_rows", errors)
    _validate_reference_rows(ledger.get("local_reference_rows"), errors)
    _validate_status_rows(ledger.get("audit_requirement_rows"), "$.audit_requirement_rows", errors)
    _validate_operator_review(ledger.get("operator_review"), errors)
    _validate_summary_counts(ledger, errors)
    _validate_safety_boundaries(ledger.get("safety_boundaries"), errors)
    _validate_string_array(ledger.get("warnings"), "$.warnings", errors)
    _validate_string_array(ledger.get("errors"), "$.errors", errors)

    for path in _find_forbidden_output_terms(ledger):
        errors.append(f"forbidden scoring/action field detected in audit ledger at {path}")

    return SimulatedDecisionAuditLedgerValidationResult(not errors, tuple(errors))


def build_operator_report(ledger: dict[str, Any]) -> str:
    validation = validate_simulated_decision_audit_ledger(ledger)
    if not validation.valid:
        raise SimulatedDecisionAuditLedgerValidationError("; ".join(validation.errors))

    lines = [
        "# PMBOT Simulated Decision Audit Ledger",
        "",
        f"Ledger: `{ledger['ledger_id']}`",
        f"Build: `{ledger['build_id']}`",
        f"Run mode: `{ledger['run_mode']}`",
        f"Operator review: `{ledger['operator_review']['status']}`",
        "",
        "## Summary Counts",
    ]
    for key, value in ledger["summary_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Source Packets",
        ]
    )
    for row in ledger["source_inventory"]:
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
    for row in ledger["local_reference_rows"]:
        lines.append(f"- {row['reference_role']}: `{row['local_reference']}` | exists: {row['reference_exists']}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, worker, scheduler, or browser calls.",
            "- Descriptive simulated record audit only; not runtime input or execution approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT simulated decision audit ledger.")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--output-ledger", required=True, type=Path)
    parser.add_argument("--output-report", required=True, type=Path)
    args = parser.parse_args(argv)

    request = load_audit_request(args.request)
    ledger = build_simulated_decision_audit_ledger(request)
    report = build_operator_report(ledger)

    args.output_ledger.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_ledger.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_report.write_text(report, encoding="utf-8")
    return 0


def _load_source_packets(request: dict[str, Any]) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for index, source in enumerate(request["source_packets"]):
        reference = source["local_reference"]
        packet_path = (_WORKSPACE_ROOT / reference).resolve()
        packet = _load_json(packet_path)
        validation = validate_simulated_decision_packet(packet)
        if not validation.valid:
            raise SimulatedDecisionAuditLedgerValidationError(
                f"source_packets[{index}] packet failed validation: {'; '.join(validation.errors)}"
            )
        if packet["packet_id"] != source["source_packet_id"]:
            raise SimulatedDecisionAuditLedgerValidationError(
                f"source_packets[{index}].source_packet_id must match the local packet id"
            )
        packets.append({"request_source": deepcopy(source), "packet": packet})
    return packets


def _build_source_inventory(
    request: dict[str, Any],
    source_packets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_packets:
        source = loaded["request_source"]
        packet = loaded["packet"]
        observation_count = sum(len(section["observations"]) for section in packet["record_sections"])
        rows.append(
            {
                "source_packet_id": source["source_packet_id"],
                "source_packet_label": source["source_packet_label"],
                "local_reference": source["local_reference"],
                "artifact_loaded": True,
                "contract_version": packet["contract_version"],
                "packet_state": packet["packet_state"],
                "record_section_count": len(packet["record_sections"]),
                "observation_count": observation_count,
                "warning_count": len(packet["warnings"]),
                "error_count": len(packet["errors"]),
                "operator_review_status": source["operator_review_status"],
                "row_state": AUDIT_LEDGER_STATE,
            }
        )
    return rows


def _build_audit_rows(source_packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_packets:
        source = loaded["request_source"]
        packet = loaded["packet"]
        rows.extend(
            [
                {
                    "row_id": f"{packet['packet_id']}.packet_contract",
                    "source_packet_id": packet["packet_id"],
                    "audit_area": "packet_contract",
                    "audit_label": "Packet contract and review gate",
                    "local_reference": source["local_reference"],
                    "observed_state": packet["packet_state"],
                    "observed_detail": f"contract={packet['contract_version']}; run_mode={packet['run_mode']}",
                    "operator_review_status": OPERATOR_REVIEW_STATUS,
                    "row_state": AUDIT_LEDGER_STATE,
                },
                {
                    "row_id": f"{packet['packet_id']}.summary_counts",
                    "source_packet_id": packet["packet_id"],
                    "audit_area": "summary_counts",
                    "audit_label": "Packet count fields",
                    "local_reference": source["local_reference"],
                    "observed_state": "counts_match_local_record",
                    "observed_detail": (
                        f"input_artifacts={packet['summary_counts']['input_artifacts']}; "
                        f"record_sections={packet['summary_counts']['record_sections']}; "
                        f"observations={packet['summary_counts']['observations']}; "
                        f"warnings={packet['summary_counts']['warnings']}"
                    ),
                    "operator_review_status": OPERATOR_REVIEW_STATUS,
                    "row_state": AUDIT_LEDGER_STATE,
                },
                {
                    "row_id": f"{packet['packet_id']}.safety_boundaries",
                    "source_packet_id": packet["packet_id"],
                    "audit_area": "safety_boundaries",
                    "audit_label": "Closed local-only safety flags",
                    "local_reference": source["local_reference"],
                    "observed_state": "closed_local_only",
                    "observed_detail": "network=false; llm=false; wallet=false; runtime=false",
                    "operator_review_status": OPERATOR_REVIEW_STATUS,
                    "row_state": AUDIT_LEDGER_STATE,
                },
            ]
        )
    return rows


def _build_record_section_rows(source_packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_packets:
        packet = loaded["packet"]
        local_reference = loaded["request_source"]["local_reference"]
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
                    "row_id": f"{packet['packet_id']}.{section['section_id']}",
                    "source_packet_id": packet["packet_id"],
                    "section_id": section["section_id"],
                    "section_label": section["section_label"],
                    "local_reference": local_reference,
                    "observation_count": len(section["observations"]),
                    "source_artifact_ids": source_artifact_ids,
                    "operator_review_status": section["operator_review_status"],
                    "row_state": AUDIT_LEDGER_STATE,
                }
            )
    return rows


def _build_local_reference_rows(source_packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for loaded in source_packets:
        packet = loaded["packet"]
        source = loaded["request_source"]
        references = [
            ("source_packet", source["local_reference"]),
            ("schema_reference", packet["schema_reference"]),
            ("market_snapshot", packet["market_snapshot"]["local_reference"]),
        ]
        references.extend(
            (f"input_artifact.{artifact['artifact_id']}", artifact["local_reference"])
            for artifact in packet["input_artifacts"]
        )
        for role, reference in references:
            rows.append(
                {
                    "row_id": f"{packet['packet_id']}.{role}",
                    "source_packet_id": packet["packet_id"],
                    "reference_role": role,
                    "local_reference": reference,
                    "reference_exists": (_WORKSPACE_ROOT / reference).resolve().exists(),
                    "operator_review_status": OPERATOR_REVIEW_STATUS,
                    "row_state": AUDIT_LEDGER_STATE,
                }
            )
    return rows


def _build_audit_requirement_rows(request: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": requirement["requirement_id"],
            "requirement_id": requirement["requirement_id"],
            "description": requirement["description"],
            "operator_review_status": requirement["operator_review_status"],
            "row_state": AUDIT_LEDGER_STATE,
        }
        for requirement in request["audit_requirements"]
    ]


def _validate_source_packets(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("$.source_packets must be a non-empty array")
        return
    required = ("source_packet_id", "source_packet_label", "local_reference", "operator_review_status")
    seen: set[str] = set()
    for index, source in enumerate(value):
        path = f"$.source_packets[{index}]"
        if not _require_object(source, path, errors):
            continue
        _require_exact_fields(source, required, path, errors)
        _require_local_id(source.get("source_packet_id"), f"{path}.source_packet_id", errors)
        _require_non_empty_string(source.get("source_packet_label"), f"{path}.source_packet_label", errors)
        _require_value(source, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _validate_local_reference(source.get("local_reference"), f"{path}.local_reference", errors)
        if isinstance(source.get("source_packet_id"), str):
            if source["source_packet_id"] in seen:
                errors.append(f"{path}.source_packet_id must be unique")
            seen.add(source["source_packet_id"])


def _validate_audit_requirements(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("$.audit_requirements must be a non-empty array")
        return
    required = ("requirement_id", "description", "operator_review_status")
    seen: set[str] = set()
    for index, requirement in enumerate(value):
        path = f"$.audit_requirements[{index}]"
        if not _require_object(requirement, path, errors):
            continue
        _require_exact_fields(requirement, required, path, errors)
        _require_local_id(requirement.get("requirement_id"), f"{path}.requirement_id", errors)
        _require_non_empty_string(requirement.get("description"), f"{path}.description", errors)
        _require_value(
            requirement,
            "operator_review_status",
            OPERATOR_REVIEW_STATUS,
            f"{path}.operator_review_status",
            errors,
        )
        if isinstance(requirement.get("requirement_id"), str):
            if requirement["requirement_id"] in seen:
                errors.append(f"{path}.requirement_id must be unique")
            seen.add(requirement["requirement_id"])


def _validate_source_inventory_rows(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("$.source_inventory must be an array")
        return
    for index, row in enumerate(value):
        path = f"$.source_inventory[{index}]"
        if not _require_object(row, path, errors):
            continue
        _require_value(row, "contract_version", SIMULATED_DECISION_PACKET_CONTRACT_VERSION, f"{path}.contract_version", errors)
        _require_value(row, "packet_state", PACKET_STATE, f"{path}.packet_state", errors)
        _require_value(row, "operator_review_status", OPERATOR_REVIEW_STATUS, f"{path}.operator_review_status", errors)
        _require_value(row, "row_state", AUDIT_LEDGER_STATE, f"{path}.row_state", errors)
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
        _require_value(row, "row_state", AUDIT_LEDGER_STATE, f"{row_path}.row_state", errors)
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
        _require_value(row, "row_state", AUDIT_LEDGER_STATE, f"{path}.row_state", errors)
        _validate_local_reference(row.get("local_reference"), f"{path}.local_reference", errors)


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


def _validate_summary_counts(ledger: dict[str, Any], errors: list[str]) -> None:
    value = ledger.get("summary_counts")
    if not _require_object(value, "$.summary_counts", errors):
        return
    expected = {
        "source_packets": len(ledger.get("source_inventory")) if isinstance(ledger.get("source_inventory"), list) else 0,
        "audit_rows": len(ledger.get("audit_rows")) if isinstance(ledger.get("audit_rows"), list) else 0,
        "record_section_rows": (
            len(ledger.get("record_section_rows")) if isinstance(ledger.get("record_section_rows"), list) else 0
        ),
        "local_references": (
            len(ledger.get("local_reference_rows")) if isinstance(ledger.get("local_reference_rows"), list) else 0
        ),
        "audit_requirements": (
            len(ledger.get("audit_requirement_rows")) if isinstance(ledger.get("audit_requirement_rows"), list) else 0
        ),
        "warnings": len(ledger.get("warnings")) if isinstance(ledger.get("warnings"), list) else 0,
        "errors": len(ledger.get("errors")) if isinstance(ledger.get("errors"), list) else 0,
    }
    _require_exact_fields(value, tuple(expected), "$.summary_counts", errors)
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            errors.append(f"$.summary_counts.{field} must match ledger content: {expected_value}")


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
