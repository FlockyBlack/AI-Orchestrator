from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pm_bot.paper_accounting.paper_accounting_ledger import (
    FORBIDDEN_DECISION_TOKENS,
    FORBIDDEN_LOCAL_REFERENCE_PREFIXES,
    LEDGER_CONTRACT_VERSION,
    OPERATOR_REVIEW_STATUS,
    SAMPLE_LEDGER_PATH,
    ValidationResult,
    validate_paper_accounting_ledger,
)
from pm_bot.paper_accounting.paper_accounting_session_summary import (
    SAMPLE_SESSION_SUMMARY_PATH,
    SESSION_SUMMARY_CONTRACT_VERSION,
    validate_paper_accounting_session_inputs,
    validate_paper_accounting_session_summary,
)
from pm_bot.paper_accounting.paper_accounting_validator import (
    SAMPLE_VALIDATION_PATH,
    VALIDATION_CONTRACT_VERSION,
    validate_paper_accounting_validation,
)

REQUEST_CONTRACT_VERSION = "pmbot_paperlive_accounting_reconciliation_request.v1"
RECONCILIATION_CONTRACT_VERSION = "pmbot_paperlive_accounting_reconciliation.v1"
RECONCILIATION_RUN_MODE = "local_static_paperlive_to_accounting_reconciliation"
RECONCILIATION_ROW_STATE = "descriptive_paperlive_accounting_reconciliation_record"
PAPERLIVE_CONTRACT_VERSION = "pmbot_crypto_paperlive_observation_ledger.v1"
SAMPLE_REQUEST_PATH = Path(
    "pm_bot/tests/fixtures/paper_accounting/paperlive_accounting_reconciliation_request.valid.json"
)
SAMPLE_RECONCILIATION_PATH = Path(
    "pm_bot/paper_accounting/samples/paperlive_accounting_reconciliation.fixture.json"
)
SAMPLE_OPERATOR_REPORT_PATH = Path(
    "pm_bot/paper_accounting/samples/paperlive_accounting_reconciliation.fixture.md"
)

ALLOWED_LOCAL_REFERENCE_PREFIXES = (
    "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/",
    "pm_bot/tests/fixtures/paper_accounting/",
    "pm_bot/paper_accounting/samples/",
)
LOCAL_ONLY_RECONCILIATION_SAFETY_BOUNDARIES = {
    "account_change_instruction_allowed": False,
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "external_market_api_allowed": False,
    "llm_calls_allowed": False,
    "network_calls_allowed": False,
    "offline_inputs_only": True,
    "operator_review_gate_required": True,
    "paperlive_execution_allowed": False,
    "real_money_or_signing_allowed": False,
    "runtime_wiring_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_allowed": False,
    "wallet_or_order_code_allowed": False,
}


class PaperliveAccountingReconciliationError(ValueError):
    def __init__(self, errors: tuple[str, ...]):
        super().__init__("; ".join(errors))
        self.errors = errors


def load_reconciliation_artifact(path: str | Path) -> dict[str, Any]:
    artifact_path = Path(path)
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PaperliveAccountingReconciliationError(("paperlive accounting artifact must be a JSON object",))
    return payload


def validate_reconciliation_request(request: Any) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(request, dict):
        return ValidationResult(False, ("request must be an object",))

    errors.extend(_find_forbidden_decision_terms(request, "request"))
    _validate_request_top_level(request, errors)
    if errors:
        return ValidationResult(False, tuple(errors))

    paperlive_payloads: dict[str, dict[str, Any]] = {}
    paperlive_records: dict[tuple[str, str], dict[str, Any]] = {}
    for artifact_index, artifact in enumerate(request["paperlive_artifacts"]):
        _validate_paperlive_artifact(artifact, artifact_index, paperlive_payloads, paperlive_records, errors)

    accounting_payloads: dict[str, dict[str, Any]] = {}
    accounting_by_role: dict[str, dict[str, Any]] = {}
    accounting_reference_by_role: dict[str, str] = {}
    for artifact_index, artifact in enumerate(request["accounting_artifacts"]):
        _validate_accounting_artifact(
            artifact,
            artifact_index,
            accounting_payloads,
            accounting_by_role,
            accounting_reference_by_role,
            errors,
        )

    _validate_accounting_artifact_consistency(accounting_by_role, accounting_reference_by_role, errors)

    ledger = accounting_by_role.get("paper_accounting_ledger", {})
    ledger_entries = {
        entry.get("entry_id"): entry
        for entry in ledger.get("accounting_entries", [])
        if isinstance(entry, dict) and entry.get("entry_id")
    }
    for link_index, link in enumerate(request["record_links"]):
        _validate_record_link(link, link_index, paperlive_records, ledger, ledger_entries, errors)
    _validate_record_link_coverage(request["record_links"], paperlive_records, errors)

    return ValidationResult(not errors, tuple(errors))


def build_paperlive_accounting_reconciliation(request: dict[str, Any]) -> dict[str, Any]:
    validation = validate_reconciliation_request(request)
    if not validation.valid:
        raise PaperliveAccountingReconciliationError(validation.errors)

    paperlive_payloads = {
        artifact["artifact_id"]: _load_local_json_object(artifact["local_reference"])
        for artifact in request["paperlive_artifacts"]
    }
    paperlive_records = {
        (artifact_id, record["record_id"]): record
        for artifact_id, payload in paperlive_payloads.items()
        for record in payload["observation_records"]
    }
    accounting_payloads = {
        artifact["artifact_role"]: _load_local_json_object(artifact["local_reference"])
        for artifact in request["accounting_artifacts"]
    }
    ledger = accounting_payloads["paper_accounting_ledger"]
    ledger_entries = {entry["entry_id"]: entry for entry in ledger["accounting_entries"]}

    reconciliation_rows = [
        _build_reconciliation_row(link, paperlive_records, ledger, ledger_entries)
        for link in request["record_links"]
    ]

    return {
        "account_context": deepcopy(ledger["account_context"]),
        "accounting_balance_summary": deepcopy(ledger["balance_summary"]),
        "build_id": f"{request['reconciliation_id']}-{_stable_digest(request)}",
        "contract_version": RECONCILIATION_CONTRACT_VERSION,
        "errors": [],
        "local_input_artifacts": [
            _build_input_artifact_row(artifact, paperlive_payloads, accounting_payloads)
            for artifact in [*request["paperlive_artifacts"], *request["accounting_artifacts"]]
        ],
        "local_only": True,
        "operator_review": {
            "required": True,
            "review_steps": list(request["operator_review_steps"]),
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "paperlive_reconciliation_rows": reconciliation_rows,
        "reconciliation_id": request["reconciliation_id"],
        "run_mode": RECONCILIATION_RUN_MODE,
        "safety_boundaries": dict(LOCAL_ONLY_RECONCILIATION_SAFETY_BOUNDARIES),
        "summary_counts": {
            "accounting_entries_linked": sum(row["accounting_entry_count"] for row in reconciliation_rows),
            "accounting_entries_total": len(ledger["accounting_entries"]),
            "input_artifacts": len(request["paperlive_artifacts"]) + len(request["accounting_artifacts"]),
            "paperlive_records": len(reconciliation_rows),
            "reconciliation_rows": len(reconciliation_rows),
            "warnings": 0,
        },
        "warnings": [],
    }


def validate_paperlive_accounting_reconciliation(reconciliation: Any) -> ValidationResult:
    errors: list[str] = []
    if not isinstance(reconciliation, dict):
        return ValidationResult(False, ("paperlive accounting reconciliation must be an object",))

    errors.extend(_find_forbidden_decision_terms(reconciliation, "paperlive_accounting_reconciliation"))
    required_fields = {
        "account_context",
        "accounting_balance_summary",
        "build_id",
        "contract_version",
        "errors",
        "local_input_artifacts",
        "local_only",
        "operator_review",
        "operator_review_required",
        "paperlive_reconciliation_rows",
        "reconciliation_id",
        "run_mode",
        "safety_boundaries",
        "summary_counts",
        "warnings",
    }
    _require_keys(reconciliation, required_fields, "paperlive_accounting_reconciliation", errors)
    if errors:
        return ValidationResult(False, tuple(errors))

    if reconciliation["contract_version"] != RECONCILIATION_CONTRACT_VERSION:
        errors.append(
            f"paperlive_accounting_reconciliation.contract_version must be {RECONCILIATION_CONTRACT_VERSION}"
        )
    if reconciliation["run_mode"] != RECONCILIATION_RUN_MODE:
        errors.append(f"paperlive_accounting_reconciliation.run_mode must be {RECONCILIATION_RUN_MODE}")
    if reconciliation["local_only"] is not True:
        errors.append("paperlive_accounting_reconciliation.local_only must be true")
    if reconciliation["operator_review_required"] is not True:
        errors.append("paperlive_accounting_reconciliation.operator_review_required must be true")
    if reconciliation["safety_boundaries"] != LOCAL_ONLY_RECONCILIATION_SAFETY_BOUNDARIES:
        errors.append("paperlive_accounting_reconciliation.safety_boundaries must match local-only boundaries")

    operator_review = reconciliation["operator_review"]
    if not isinstance(operator_review, dict):
        errors.append("paperlive_accounting_reconciliation.operator_review must be an object")
    elif operator_review.get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(
            f"paperlive_accounting_reconciliation.operator_review.status must be {OPERATOR_REVIEW_STATUS}"
        )

    input_artifacts = reconciliation["local_input_artifacts"]
    if not isinstance(input_artifacts, list):
        errors.append("paperlive_accounting_reconciliation.local_input_artifacts must be a list")
        input_artifacts = []
    for artifact_index, artifact in enumerate(input_artifacts):
        _validate_input_artifact_row(artifact, artifact_index, errors)

    rows = reconciliation["paperlive_reconciliation_rows"]
    if not isinstance(rows, list):
        errors.append("paperlive_accounting_reconciliation.paperlive_reconciliation_rows must be a list")
        rows = []
    linked_entry_count = 0
    observed_row_ids: set[str] = set()
    for row_index, row in enumerate(rows):
        linked_entry_count += _validate_reconciliation_row(row, row_index, observed_row_ids, errors)

    summary_counts = reconciliation["summary_counts"]
    if not isinstance(summary_counts, dict):
        errors.append("paperlive_accounting_reconciliation.summary_counts must be an object")
    else:
        paperlive_input_records = _count_paperlive_input_records(input_artifacts)
        expected_counts = {
            "accounting_entries_linked": linked_entry_count,
            "accounting_entries_total": _count_total_accounting_entries(input_artifacts),
            "input_artifacts": len(input_artifacts),
            "paperlive_records": paperlive_input_records,
            "reconciliation_rows": len(rows),
            "warnings": len(reconciliation["warnings"]) if isinstance(reconciliation["warnings"], list) else 0,
        }
        if summary_counts != expected_counts:
            errors.append("paperlive_accounting_reconciliation.summary_counts must match reconciliation rows")
        if paperlive_input_records != len(rows):
            errors.append(
                "paperlive_accounting_reconciliation.paperlive_records must match paperlive input artifact record_count"
            )

    if not isinstance(reconciliation["errors"], list):
        errors.append("paperlive_accounting_reconciliation.errors must be a list")
    if not isinstance(reconciliation["warnings"], list):
        errors.append("paperlive_accounting_reconciliation.warnings must be a list")

    return ValidationResult(not errors, tuple(errors))


def build_operator_report(reconciliation: dict[str, Any]) -> str:
    lines = [
        "# PMBOT Paperlive To Accounting Reconciliation",
        "",
        f"Reconciliation ID: `{reconciliation['reconciliation_id']}`",
        f"Build ID: `{reconciliation['build_id']}`",
        f"Run mode: `{reconciliation['run_mode']}`",
        f"Operator review: `{reconciliation['operator_review']['status']}`",
        "",
        "## Summary",
        "",
        f"- Paperlive records: {reconciliation['summary_counts']['paperlive_records']}",
        f"- Reconciliation rows: {reconciliation['summary_counts']['reconciliation_rows']}",
        f"- Accounting entries linked: {reconciliation['summary_counts']['accounting_entries_linked']}",
        f"- Accounting entries total: {reconciliation['summary_counts']['accounting_entries_total']}",
        f"- Input artifacts: {reconciliation['summary_counts']['input_artifacts']}",
        f"- Warnings: {reconciliation['summary_counts']['warnings']}",
        "",
        "## Input Artifacts",
        "",
    ]
    for artifact in reconciliation["local_input_artifacts"]:
        lines.append(
            f"- `{artifact['artifact_id']}`: `{artifact['artifact_role']}` from `{artifact['local_reference']}`."
        )
    lines.extend(["", "## Reconciliation Rows", ""])
    for row in reconciliation["paperlive_reconciliation_rows"]:
        lines.append(
            f"- `{row['paperlive_record_id']}`: `{row['accounting_handling']}` with "
            f"{row['accounting_entry_count']} linked accounting entries and quantity delta "
            f"`{row['accounting_quantity_delta_total']}`."
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static paperlive and paper accounting inputs only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, or runtime calls.",
            "- Descriptive paperlive to accounting reconciliation only; it is not execution approval.",
            "- Operator review remains required before using these records outside this local artifact.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a local-only PMBOT paperlive to accounting reconciliation artifact."
    )
    parser.add_argument(
        "--request",
        default=str(SAMPLE_REQUEST_PATH),
        help="Path to the local paperlive accounting reconciliation request JSON.",
    )
    parser.add_argument(
        "--output-reconciliation",
        required=True,
        help="Path where the JSON reconciliation artifact should be written.",
    )
    parser.add_argument("--output-report", required=True, help="Path where the Markdown report should be written.")
    args = parser.parse_args(argv)

    request = load_reconciliation_artifact(args.request)
    reconciliation = build_paperlive_accounting_reconciliation(request)
    artifact_validation = validate_paperlive_accounting_reconciliation(reconciliation)
    if not artifact_validation.valid:
        raise PaperliveAccountingReconciliationError(artifact_validation.errors)

    output_reconciliation = Path(args.output_reconciliation)
    output_report = Path(args.output_report)
    output_reconciliation.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_reconciliation.write_text(json.dumps(reconciliation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.write_text(build_operator_report(reconciliation), encoding="utf-8")
    return 0


def _validate_request_top_level(request: dict[str, Any], errors: list[str]) -> None:
    required_fields = {
        "accounting_artifacts",
        "contract_version",
        "local_only",
        "operator_review_required",
        "operator_review_steps",
        "paperlive_artifacts",
        "reconciliation_id",
        "record_links",
        "scope",
    }
    _require_keys(request, required_fields, "request", errors)
    if required_fields - set(request):
        return
    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"request.contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "paperlive_to_accounting_reconciliation":
        errors.append("request.scope must be paperlive_to_accounting_reconciliation")
    if request.get("local_only") is not True:
        errors.append("request.local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("request.operator_review_required must be true")
    if not isinstance(request.get("reconciliation_id"), str) or not request["reconciliation_id"]:
        errors.append("request.reconciliation_id must be a non-empty string")
    if not isinstance(request.get("paperlive_artifacts"), list) or not request["paperlive_artifacts"]:
        errors.append("request.paperlive_artifacts must be a non-empty list")
    if not isinstance(request.get("accounting_artifacts"), list) or not request["accounting_artifacts"]:
        errors.append("request.accounting_artifacts must be a non-empty list")
    if not isinstance(request.get("record_links"), list) or not request["record_links"]:
        errors.append("request.record_links must be a non-empty list")
    if not isinstance(request.get("operator_review_steps"), list) or not request["operator_review_steps"]:
        errors.append("request.operator_review_steps must be a non-empty list")


def _validate_paperlive_artifact(
    artifact: Any,
    artifact_index: int,
    paperlive_payloads: dict[str, dict[str, Any]],
    paperlive_records: dict[tuple[str, str], dict[str, Any]],
    errors: list[str],
) -> None:
    path = f"request.paperlive_artifacts[{artifact_index}]"
    if not isinstance(artifact, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = {"artifact_id", "artifact_role", "contract_version", "local_reference", "required_fields"}
    _require_keys(artifact, required_fields, path, errors)
    if required_fields - set(artifact):
        return
    artifact_id = artifact.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        errors.append(f"{path}.artifact_id must be a non-empty string")
        return
    if artifact_id in paperlive_payloads:
        errors.append(f"{path}.artifact_id duplicates {artifact_id}")
        return
    if artifact.get("artifact_role") != "crypto_paperlive_observation_ledger":
        errors.append(f"{path}.artifact_role must be crypto_paperlive_observation_ledger")
    if artifact.get("contract_version") != PAPERLIVE_CONTRACT_VERSION:
        errors.append(f"{path}.contract_version must be {PAPERLIVE_CONTRACT_VERSION}")
    if not _is_allowed_local_reference(artifact.get("local_reference")):
        errors.append(f"{path}.local_reference must stay under allowed local reconciliation paths")
        return
    try:
        payload = _load_local_json_object(artifact["local_reference"])
    except PaperliveAccountingReconciliationError as exc:
        errors.extend(f"{path}: {error}" for error in exc.errors)
        return
    paperlive_payloads[artifact_id] = payload
    if payload.get("contract_version") != artifact.get("contract_version"):
        errors.append(f"{path}.contract_version must match the local paperlive artifact")
    if payload.get("local_only") is not True:
        errors.append(f"{path}.local_reference local_only must be true")
    if payload.get("operator_review_required") is not True:
        errors.append(f"{path}.local_reference operator_review_required must be true")

    required_payload_fields = artifact.get("required_fields")
    if not isinstance(required_payload_fields, list) or not required_payload_fields:
        errors.append(f"{path}.required_fields must be a non-empty list")
        required_payload_fields = []
    missing_fields = [field for field in required_payload_fields if isinstance(field, str) and field not in payload]
    if missing_fields:
        errors.append(f"{path}.required_fields references missing local artifact fields: {', '.join(missing_fields)}")

    records = payload.get("observation_records")
    if not isinstance(records, list) or not records:
        errors.append(f"{path}.local_reference observation_records must be a non-empty list")
        return
    for record_index, record in enumerate(records):
        record_path = f"{path}.local_reference.observation_records[{record_index}]"
        _validate_paperlive_record(record, record_path, errors)
        if isinstance(record, dict) and isinstance(record.get("record_id"), str):
            paperlive_records[(artifact_id, record["record_id"])] = record


def _validate_paperlive_record(record: Any, path: str, errors: list[str]) -> None:
    if not isinstance(record, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = {
        "asset_symbol",
        "local_source_reference",
        "metric_type",
        "record_id",
        "reported_at_utc",
        "reported_reference_unit",
        "reported_reference_value",
        "review_status",
    }
    _require_keys(record, required_fields, path, errors)
    if required_fields - set(record):
        return
    for field in sorted(required_fields):
        if not isinstance(record.get(field), str) or not record[field]:
            errors.append(f"{path}.{field} must be a non-empty string")
    if record.get("review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.review_status must be {OPERATOR_REVIEW_STATUS}")
    if not _is_allowed_local_reference(record.get("local_source_reference")):
        errors.append(f"{path}.local_source_reference must stay under allowed local reconciliation paths")
    try:
        _decimal_from_string(record.get("reported_reference_value"))
    except PaperliveAccountingReconciliationError:
        errors.append(f"{path}.reported_reference_value must be a decimal string")


def _validate_accounting_artifact(
    artifact: Any,
    artifact_index: int,
    accounting_payloads: dict[str, dict[str, Any]],
    accounting_by_role: dict[str, dict[str, Any]],
    accounting_reference_by_role: dict[str, str],
    errors: list[str],
) -> None:
    path = f"request.accounting_artifacts[{artifact_index}]"
    if not isinstance(artifact, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = {"artifact_id", "artifact_role", "contract_version", "local_reference"}
    _require_keys(artifact, required_fields, path, errors)
    if required_fields - set(artifact):
        return
    artifact_id = artifact.get("artifact_id")
    artifact_role = artifact.get("artifact_role")
    if not isinstance(artifact_id, str) or not artifact_id:
        errors.append(f"{path}.artifact_id must be a non-empty string")
        return
    if artifact_id in accounting_payloads:
        errors.append(f"{path}.artifact_id duplicates {artifact_id}")
        return
    if artifact_role in accounting_by_role:
        errors.append(f"{path}.artifact_role duplicates {artifact_role}")
        return
    if not _is_allowed_local_reference(artifact.get("local_reference")):
        errors.append(f"{path}.local_reference must stay under allowed local reconciliation paths")
        return
    try:
        payload = _load_local_json_object(artifact["local_reference"])
    except PaperliveAccountingReconciliationError as exc:
        errors.extend(f"{path}: {error}" for error in exc.errors)
        return
    accounting_payloads[artifact_id] = payload
    accounting_by_role[str(artifact_role)] = payload
    accounting_reference_by_role[str(artifact_role)] = _normalize_local_reference(artifact["local_reference"])

    if artifact_role == "paper_accounting_ledger":
        _extend_validation_errors(validate_paper_accounting_ledger(payload), f"{path}.local_reference", errors)
        expected_contract = LEDGER_CONTRACT_VERSION
    elif artifact_role == "paper_accounting_validation":
        _extend_validation_errors(validate_paper_accounting_validation(payload), f"{path}.local_reference", errors)
        expected_contract = VALIDATION_CONTRACT_VERSION
    elif artifact_role == "paper_accounting_session_summary":
        _extend_validation_errors(validate_paper_accounting_session_summary(payload), f"{path}.local_reference", errors)
        expected_contract = SESSION_SUMMARY_CONTRACT_VERSION
    else:
        errors.append(f"{path}.artifact_role must be a supported paper accounting artifact role")
        return
    if artifact.get("contract_version") != expected_contract:
        errors.append(f"{path}.contract_version must be {expected_contract}")
    if payload.get("contract_version") != artifact.get("contract_version"):
        errors.append(f"{path}.contract_version must match the local accounting artifact")


def _validate_accounting_artifact_consistency(
    accounting_by_role: dict[str, dict[str, Any]],
    accounting_reference_by_role: dict[str, str],
    errors: list[str],
) -> None:
    required_roles = {
        "paper_accounting_ledger",
        "paper_accounting_validation",
        "paper_accounting_session_summary",
    }
    missing_roles = sorted(required_roles - set(accounting_by_role))
    if missing_roles:
        errors.append(f"request.accounting_artifacts missing required roles: {', '.join(missing_roles)}")
        return
    ledger = accounting_by_role["paper_accounting_ledger"]
    validation_artifact = accounting_by_role["paper_accounting_validation"]
    session_summary = accounting_by_role["paper_accounting_session_summary"]
    session_input_validation = validate_paper_accounting_session_inputs(
        ledger,
        validation_artifact,
        accounting_reference_by_role["paper_accounting_ledger"],
        accounting_reference_by_role["paper_accounting_validation"],
    )
    _extend_validation_errors(session_input_validation, "request.accounting_artifacts", errors)
    if session_summary.get("ledger_build_id") != ledger.get("build_id"):
        errors.append("request.accounting_artifacts session ledger_build_id must match ledger build_id")
    if session_summary.get("validation_build_id") != validation_artifact.get("build_id"):
        errors.append("request.accounting_artifacts session validation_build_id must match validation build_id")


def _validate_record_link(
    link: Any,
    link_index: int,
    paperlive_records: dict[tuple[str, str], dict[str, Any]],
    ledger: dict[str, Any],
    ledger_entries: dict[Any, dict[str, Any]],
    errors: list[str],
) -> None:
    path = f"request.record_links[{link_index}]"
    if not isinstance(link, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = {
        "accounting_entry_ids",
        "accounting_handling",
        "accounting_ledger_id",
        "link_id",
        "operator_review_label",
        "paperlive_artifact_id",
        "paperlive_record_id",
        "reconciliation_label",
    }
    _require_keys(link, required_fields, path, errors)
    if required_fields - set(link):
        return
    for field in sorted(required_fields - {"accounting_entry_ids"}):
        if not isinstance(link.get(field), str) or not link[field]:
            errors.append(f"{path}.{field} must be a non-empty string")
    if (link.get("paperlive_artifact_id"), link.get("paperlive_record_id")) not in paperlive_records:
        errors.append(f"{path}.paperlive_record_id must reference a loaded paperlive record")
    if link.get("accounting_ledger_id") != ledger.get("ledger_id"):
        errors.append(f"{path}.accounting_ledger_id must match the loaded paper accounting ledger")
    accounting_entry_ids = link.get("accounting_entry_ids")
    if not isinstance(accounting_entry_ids, list):
        errors.append(f"{path}.accounting_entry_ids must be a list")
        return
    for entry_index, entry_id in enumerate(accounting_entry_ids):
        if not isinstance(entry_id, str) or not entry_id:
            errors.append(f"{path}.accounting_entry_ids[{entry_index}] must be a non-empty string")
        elif entry_id not in ledger_entries:
            errors.append(f"{path}.accounting_entry_ids[{entry_index}] must reference a loaded accounting entry")


def _validate_record_link_coverage(
    record_links: list[Any],
    paperlive_records: dict[tuple[str, str], dict[str, Any]],
    errors: list[str],
) -> None:
    linked_records: list[tuple[Any, Any]] = [
        (link.get("paperlive_artifact_id"), link.get("paperlive_record_id"))
        for link in record_links
        if isinstance(link, dict)
    ]
    if len(set(linked_records)) != len(linked_records):
        errors.append("request.record_links must not duplicate paperlive record references")
    loaded_record_keys = set(paperlive_records)
    linked_record_keys = {
        (str(artifact_id), str(record_id))
        for artifact_id, record_id in linked_records
        if (artifact_id, record_id) in loaded_record_keys
    }
    if linked_record_keys != loaded_record_keys:
        errors.append("request.record_links must cover every loaded paperlive record exactly once")


def _build_input_artifact_row(
    artifact: dict[str, Any],
    paperlive_payloads: dict[str, dict[str, Any]],
    accounting_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    artifact_id = artifact["artifact_id"]
    artifact_role = artifact["artifact_role"]
    if artifact_id in paperlive_payloads:
        record_count = len(paperlive_payloads[artifact_id]["observation_records"])
    else:
        payload = accounting_payloads[artifact_role]
        record_count = len(payload.get("accounting_entries", payload.get("record_validation_rows", payload.get("session_review_rows", []))))
    return {
        "artifact_id": artifact_id,
        "artifact_role": artifact_role,
        "contract_version": artifact["contract_version"],
        "local_reference": _normalize_local_reference(artifact["local_reference"]),
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "record_count": record_count,
        "runner_state": RECONCILIATION_ROW_STATE,
    }


def _build_reconciliation_row(
    link: dict[str, Any],
    paperlive_records: dict[tuple[str, str], dict[str, Any]],
    ledger: dict[str, Any],
    ledger_entries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    paperlive_record = paperlive_records[(link["paperlive_artifact_id"], link["paperlive_record_id"])]
    linked_entries = [ledger_entries[entry_id] for entry_id in link["accounting_entry_ids"]]
    quantity_total = sum(
        (_decimal_from_string(entry["quantity_delta"]) for entry in linked_entries),
        Decimal("0"),
    )
    return {
        "accounting_entry_count": len(linked_entries),
        "accounting_entry_ids": list(link["accounting_entry_ids"]),
        "accounting_handling": link["accounting_handling"],
        "accounting_ledger_id": ledger["ledger_id"],
        "accounting_quantity_delta_total": _format_decimal(quantity_total),
        "accounting_review_status": OPERATOR_REVIEW_STATUS,
        "link_id": link["link_id"],
        "operator_review_label": link["operator_review_label"],
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "paperlive_artifact_id": link["paperlive_artifact_id"],
        "paperlive_asset_symbol": paperlive_record["asset_symbol"],
        "paperlive_metric_type": paperlive_record["metric_type"],
        "paperlive_record_id": paperlive_record["record_id"],
        "paperlive_reference_unit": paperlive_record["reported_reference_unit"],
        "paperlive_reference_value": _format_decimal(_decimal_from_string(paperlive_record["reported_reference_value"])),
        "paperlive_reported_at_utc": paperlive_record["reported_at_utc"],
        "paperlive_review_status": paperlive_record["review_status"],
        "reconciliation_label": link["reconciliation_label"],
        "reconciliation_status": "ready_for_operator_review",
        "row_id": f"{link['link_id']}.paperlive_accounting_reconciliation",
        "runner_state": RECONCILIATION_ROW_STATE,
        "source_fixture_reference": _normalize_local_reference(paperlive_record["local_source_reference"]),
    }


def _validate_input_artifact_row(artifact: Any, artifact_index: int, errors: list[str]) -> None:
    path = f"paperlive_accounting_reconciliation.local_input_artifacts[{artifact_index}]"
    if not isinstance(artifact, dict):
        errors.append(f"{path} must be an object")
        return
    required_fields = {
        "artifact_id",
        "artifact_role",
        "contract_version",
        "local_reference",
        "operator_review_status",
        "record_count",
        "runner_state",
    }
    _require_keys(artifact, required_fields, path, errors)
    if required_fields - set(artifact):
        return
    if not _is_allowed_local_reference(artifact.get("local_reference")):
        errors.append(f"{path}.local_reference must stay under allowed local reconciliation paths")
    if artifact.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if artifact.get("runner_state") != RECONCILIATION_ROW_STATE:
        errors.append(f"{path}.runner_state must be {RECONCILIATION_ROW_STATE}")
    if not isinstance(artifact.get("record_count"), int) or artifact["record_count"] < 0:
        errors.append(f"{path}.record_count must be a non-negative integer")


def _validate_reconciliation_row(
    row: Any,
    row_index: int,
    observed_row_ids: set[str],
    errors: list[str],
) -> int:
    path = f"paperlive_accounting_reconciliation.paperlive_reconciliation_rows[{row_index}]"
    if not isinstance(row, dict):
        errors.append(f"{path} must be an object")
        return 0
    required_fields = {
        "accounting_entry_count",
        "accounting_entry_ids",
        "accounting_handling",
        "accounting_ledger_id",
        "accounting_quantity_delta_total",
        "accounting_review_status",
        "link_id",
        "operator_review_label",
        "operator_review_status",
        "paperlive_artifact_id",
        "paperlive_asset_symbol",
        "paperlive_metric_type",
        "paperlive_record_id",
        "paperlive_reference_unit",
        "paperlive_reference_value",
        "paperlive_reported_at_utc",
        "paperlive_review_status",
        "reconciliation_label",
        "reconciliation_status",
        "row_id",
        "runner_state",
        "source_fixture_reference",
    }
    _require_keys(row, required_fields, path, errors)
    if required_fields - set(row):
        return 0
    for field in sorted(required_fields - {"accounting_entry_count", "accounting_entry_ids"}):
        if not isinstance(row.get(field), str) or not row[field]:
            errors.append(f"{path}.{field} must be a non-empty string")
    if row.get("row_id") in observed_row_ids:
        errors.append(f"{path}.row_id must be unique")
    observed_row_ids.add(str(row.get("row_id")))
    if row.get("row_id") != f"{row.get('link_id')}.paperlive_accounting_reconciliation":
        errors.append(f"{path}.row_id must be derived from link_id")
    if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("accounting_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.accounting_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("paperlive_review_status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"{path}.paperlive_review_status must be {OPERATOR_REVIEW_STATUS}")
    if row.get("runner_state") != RECONCILIATION_ROW_STATE:
        errors.append(f"{path}.runner_state must be {RECONCILIATION_ROW_STATE}")
    if row.get("reconciliation_status") != "ready_for_operator_review":
        errors.append(f"{path}.reconciliation_status must be ready_for_operator_review")
    if not _is_allowed_local_reference(row.get("source_fixture_reference")):
        errors.append(f"{path}.source_fixture_reference must stay under allowed local reconciliation paths")
    accounting_entry_ids = row.get("accounting_entry_ids")
    if not isinstance(accounting_entry_ids, list):
        errors.append(f"{path}.accounting_entry_ids must be a list")
        accounting_entry_ids = []
    elif not all(isinstance(entry_id, str) and entry_id for entry_id in accounting_entry_ids):
        errors.append(f"{path}.accounting_entry_ids must contain non-empty strings")
    if row.get("accounting_entry_count") != len(accounting_entry_ids):
        errors.append(f"{path}.accounting_entry_count must match accounting_entry_ids length")
    for quantity_field in ("accounting_quantity_delta_total", "paperlive_reference_value"):
        try:
            quantity = _decimal_from_string(row.get(quantity_field))
        except PaperliveAccountingReconciliationError:
            errors.append(f"{path}.{quantity_field} must be a decimal string")
        else:
            if _format_decimal(quantity) != row.get(quantity_field):
                errors.append(f"{path}.{quantity_field} must use canonical two-decimal formatting")
    return len(accounting_entry_ids)


def _count_total_accounting_entries(input_artifacts: list[Any]) -> int:
    for artifact in input_artifacts:
        if isinstance(artifact, dict) and artifact.get("artifact_role") == "paper_accounting_ledger":
            record_count = artifact.get("record_count")
            if isinstance(record_count, int):
                return record_count
    return 0


def _count_paperlive_input_records(input_artifacts: list[Any]) -> int:
    return sum(
        artifact["record_count"]
        for artifact in input_artifacts
        if (
            isinstance(artifact, dict)
            and artifact.get("artifact_role") == "crypto_paperlive_observation_ledger"
            and isinstance(artifact.get("record_count"), int)
        )
    )


def _load_local_json_object(local_reference: str) -> dict[str, Any]:
    path = Path(_normalize_local_reference(local_reference))
    if not path.exists():
        raise PaperliveAccountingReconciliationError((f"local_reference does not exist: {local_reference}",))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PaperliveAccountingReconciliationError((f"local_reference must contain a JSON object: {local_reference}",))
    return payload


def _is_allowed_local_reference(local_reference: Any) -> bool:
    if not isinstance(local_reference, str) or not local_reference:
        return False
    normalized = _normalize_local_reference(local_reference)
    if "://" in normalized or normalized.startswith("/") or Path(normalized).is_absolute():
        return False
    parts = [part for part in normalized.split("/") if part]
    if ".." in parts:
        return False
    if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in FORBIDDEN_LOCAL_REFERENCE_PREFIXES):
        return False
    return any(normalized.startswith(prefix) for prefix in ALLOWED_LOCAL_REFERENCE_PREFIXES)


def _normalize_local_reference(local_reference: str) -> str:
    return local_reference.replace("\\", "/")


def _decimal_from_string(value: Any) -> Decimal:
    if not isinstance(value, str) or not value:
        raise PaperliveAccountingReconciliationError(("value must be a decimal string",))
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise PaperliveAccountingReconciliationError(("value must be a decimal string",)) from exc


def _format_decimal(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def _stable_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def _extend_validation_errors(validation: ValidationResult, path: str, errors: list[str]) -> None:
    errors.extend(f"{path}: {error}" for error in validation.errors)


def _require_keys(value: dict[str, Any], required_fields: set[str], path: str, errors: list[str]) -> None:
    missing = sorted(required_fields - set(value))
    if missing:
        errors.append(f"{path} missing required fields: {', '.join(missing)}")


def _find_forbidden_decision_terms(value: Any, path: str) -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_token(str(key)):
                hits.append(f"forbidden scoring/action field detected at {key_path}")
            hits.extend(_find_forbidden_decision_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_forbidden_decision_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_token(value):
        hits.append(f"forbidden scoring/action text detected at {path}")
    return hits


def _has_forbidden_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_DECISION_TOKENS)


if __name__ == "__main__":
    raise SystemExit(main())
