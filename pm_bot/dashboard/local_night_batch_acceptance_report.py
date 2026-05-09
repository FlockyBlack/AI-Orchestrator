from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

TASK_ID = "PMBOT-OPERATOR-002-NIGHT-BATCH-ACCEPTANCE-REPORT-LOCAL-ONLY"
REQUEST_CONTRACT_VERSION = "pmbot_local_night_batch_acceptance_report_request.v1"
REPORT_CONTRACT_VERSION = "pmbot_local_night_batch_acceptance_report.v1"
LOCAL_RUN_MODE = "local_static_night_batch_acceptance_report"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
REPORT_ROW_STATE = "ready_for_operator_review"
SAMPLE_REPORT_PATH = "pm_bot/dashboard/samples/local_night_batch_acceptance_report.fixture.json"
CREATED_AT = "2026-05-09T00:00:00Z"
REQUIRED_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)

ALLOWED_LOCAL_REFERENCE_PREFIXES = (
    "docs/",
    "pm_bot/dashboard/",
    "pm_bot/tests/",
    "tests/",
)
FORBIDDEN_LOCAL_REFERENCE_PREFIXES = (
    ".codex/",
    ".env",
    ".env.",
    ".git/",
    "agent_tasks/running/",
    "dispatcher/",
    "pm_bot/llm/",
    "pm_bot/orders/",
    "pm_bot/trading/",
    "pm_bot/wallet/",
    "run_codex/",
    "runtime/",
)
BLOCKED_REVIEW_TERMS = {
    "advice",
    "bet",
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
    "recommendations",
    "score",
    "scoring",
    "selection",
    "sell",
    "side",
    "stake",
    "wager",
}
LOCAL_ONLY_SAFETY_BOUNDARIES = {
    "authenticated_endpoint_calls_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "local_static_samples_only": True,
    "network_calls_allowed": False,
    "operator_review_required": True,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


@dataclass(frozen=True)
class NightBatchAcceptanceReportValidationResult:
    valid: bool
    errors: tuple[str, ...]


class NightBatchAcceptanceReportValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_acceptance_report_request(path: str | Path) -> dict[str, Any]:
    normalized = _normalize_local_reference(str(path))
    if _is_network_like(normalized):
        raise NightBatchAcceptanceReportValidationError(("request path must be local",))
    if _contains_path_traversal(normalized):
        raise NightBatchAcceptanceReportValidationError(("request path must not use traversal",))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_acceptance_report(request: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_acceptance_report_request(request)
    if not validation.valid:
        raise NightBatchAcceptanceReportValidationError(validation.errors)

    report_sections = [_build_section_row(row) for row in request["section_records"]]
    acceptance_rows = [_build_acceptance_row(row) for row in request["acceptance_records"]]
    validation_rows = [_build_validation_row(row) for row in request["validation_records"]]
    local_references = _collect_local_references(report_sections, acceptance_rows, validation_rows)

    report = {
        "acceptance_report_id": request["report_id"],
        "acceptance_review": acceptance_rows,
        "build_id": f"{request['report_id']}-{_stable_digest(request)}",
        "contract_version": REPORT_CONTRACT_VERSION,
        "created_at": CREATED_AT,
        "errors": [],
        "local_only": True,
        "operator_acceptance": {
            "required": True,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": list(request["operator_review_steps"]),
        "report_sections": report_sections,
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "review_date": request["review_date"],
        "run_label": request["run_label"],
        "run_mode": LOCAL_RUN_MODE,
        "safety_boundaries": deepcopy(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "summary_counts": {
            "acceptance_records": len(acceptance_rows),
            "local_references": len(local_references),
            "operator_review_pending_records": _count_pending(report_sections, acceptance_rows, validation_rows),
            "report_sections": len(report_sections),
            "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
            "validation_records": len(validation_rows),
            "warnings": 0,
        },
        "task_id": TASK_ID,
        "validation_review": validation_rows,
        "warnings": [],
    }

    artifact_validation = validate_acceptance_report(report)
    if not artifact_validation.valid:
        raise NightBatchAcceptanceReportValidationError(artifact_validation.errors)
    return report


def validate_acceptance_report_request(request: Mapping[str, Any]) -> NightBatchAcceptanceReportValidationResult:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "report_id",
        "run_label",
        "review_date",
        "scope",
        "local_only",
        "operator_review_required",
        "section_records",
        "acceptance_records",
        "validation_records",
        "operator_review_steps",
    )
    errors.extend(_missing_fields(request, required_fields, "request"))

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "local_night_batch_acceptance_report":
        errors.append("scope must be local_night_batch_acceptance_report")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")

    for field_name in ("section_records", "acceptance_records", "validation_records", "operator_review_steps"):
        if field_name in request and not isinstance(request[field_name], list):
            errors.append(f"{field_name} must be a list")

    if isinstance(request.get("section_records"), list):
        errors.extend(_validate_rows("section_records", request["section_records"], _SECTION_REQUIRED_FIELDS))
    if isinstance(request.get("acceptance_records"), list):
        errors.extend(_validate_rows("acceptance_records", request["acceptance_records"], _ACCEPTANCE_REQUIRED_FIELDS))
    if isinstance(request.get("validation_records"), list):
        errors.extend(_validate_rows("validation_records", request["validation_records"], _VALIDATION_REQUIRED_FIELDS))

    errors.extend(_duplicate_id_errors("section_records", request.get("section_records"), "section_id"))
    errors.extend(_duplicate_id_errors("acceptance_records", request.get("acceptance_records"), "acceptance_id"))
    errors.extend(_duplicate_id_errors("validation_records", request.get("validation_records"), "validation_id"))
    errors.extend(_blocked_term_errors(request, "request"))
    return NightBatchAcceptanceReportValidationResult(valid=not errors, errors=tuple(errors))


def validate_acceptance_report(report: Mapping[str, Any]) -> NightBatchAcceptanceReportValidationResult:
    errors: list[str] = []
    required_fields = (
        "acceptance_report_id",
        "acceptance_review",
        "build_id",
        "contract_version",
        "created_at",
        "errors",
        "local_only",
        "operator_acceptance",
        "operator_review_required",
        "operator_review_steps",
        "report_sections",
        "required_validation_commands",
        "review_date",
        "run_label",
        "run_mode",
        "safety_boundaries",
        "summary_counts",
        "task_id",
        "validation_review",
        "warnings",
    )
    errors.extend(_missing_fields(report, required_fields, "report"))

    if report.get("contract_version") != REPORT_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REPORT_CONTRACT_VERSION}")
    if report.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if report.get("created_at") != CREATED_AT:
        errors.append(f"created_at must be {CREATED_AT}")
    if report.get("run_mode") != LOCAL_RUN_MODE:
        errors.append(f"run_mode must be {LOCAL_RUN_MODE}")
    if report.get("local_only") is not True:
        errors.append("local_only must be true")
    if report.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if report.get("operator_acceptance", {}).get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"operator_acceptance.status must be {OPERATOR_REVIEW_STATUS}")
    if report.get("operator_acceptance", {}).get("required") is not True:
        errors.append("operator_acceptance.required must be true")
    if report.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match the local validation command list")
    if report.get("safety_boundaries") != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only acceptance report boundary")

    report_sections = _list_or_error(report.get("report_sections"), "report_sections", errors)
    acceptance_rows = _list_or_error(report.get("acceptance_review"), "acceptance_review", errors)
    validation_rows = _list_or_error(report.get("validation_review"), "validation_review", errors)

    for collection_name, rows in (
        ("report_sections", report_sections),
        ("acceptance_review", acceptance_rows),
        ("validation_review", validation_rows),
    ):
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"{collection_name}[{index}] must be an object")
                continue
            if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
                errors.append(f"{collection_name}[{index}].operator_review_status must be {OPERATOR_REVIEW_STATUS}")
            if row.get("runner_state") != REPORT_ROW_STATE:
                errors.append(f"{collection_name}[{index}].runner_state must be {REPORT_ROW_STATE}")
            for field_name in ("local_reference", "source_fixture_reference", "evidence_reference"):
                if field_name in row:
                    errors.extend(_validate_local_reference(str(row[field_name]), f"{collection_name}[{index}].{field_name}"))

    summary_counts = report.get("summary_counts")
    if isinstance(summary_counts, Mapping):
        local_references = _collect_local_references(report_sections, acceptance_rows, validation_rows)
        expected_counts = {
            "acceptance_records": len(acceptance_rows),
            "local_references": len(local_references),
            "operator_review_pending_records": _count_pending(report_sections, acceptance_rows, validation_rows),
            "report_sections": len(report_sections),
            "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
            "validation_records": len(validation_rows),
            "warnings": len(report.get("warnings", [])) if isinstance(report.get("warnings"), list) else 0,
        }
        if dict(summary_counts) != expected_counts:
            errors.append("summary_counts must match acceptance report content")
    else:
        errors.append("summary_counts must be an object")

    errors.extend(_blocked_term_errors(report, "report"))
    return NightBatchAcceptanceReportValidationResult(valid=not errors, errors=tuple(errors))


def find_blocked_output_terms(value: object) -> list[str]:
    return _blocked_term_errors(value, "$")


def render_operator_report(report: Mapping[str, Any]) -> str:
    validation = validate_acceptance_report(report)
    if not validation.valid:
        raise NightBatchAcceptanceReportValidationError(validation.errors)

    lines = [
        "# PMBOT Night Batch Acceptance Report",
        "",
        f"Task: `{report['task_id']}`",
        f"Report: `{report['acceptance_report_id']}`",
        f"Build: `{report['build_id']}`",
        f"Contract: `{report['contract_version']}`",
        f"Run mode: `{report['run_mode']}`",
        f"Operator review: `{report['operator_acceptance']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Report sections: {report['summary_counts']['report_sections']}",
        f"- Acceptance records: {report['summary_counts']['acceptance_records']}",
        f"- Validation records: {report['summary_counts']['validation_records']}",
        f"- Pending operator review records: {report['summary_counts']['operator_review_pending_records']}",
        f"- Local references: {report['summary_counts']['local_references']}",
        f"- Warnings: {report['summary_counts']['warnings']}",
        "",
        "## Report Sections",
        "",
    ]
    for row in report["report_sections"]:
        lines.append(
            f"- `{row['section_id']}`: type `{row['section_type']}`, records {row['record_count']}, "
            f"state `{row['observed_state']}`, reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Acceptance Review", ""])
    for row in report["acceptance_review"]:
        lines.append(
            f"- `{row['acceptance_id']}`: basis `{row['review_basis']}`, state `{row['observed_state']}`, "
            f"evidence `{row['evidence_reference']}`"
        )

    lines.extend(["", "## Validation Review", ""])
    for row in report["validation_review"]:
        lines.append(
            f"- `{row['validation_id']}`: status `{row['status']}`, command `{row['command_label']}`, "
            f"reference `{row['local_reference']}`"
        )

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local files and static fixtures only.",
            "- Makes no network, LLM, external service, wallet, signing, endpoint, runtime, browser, scheduler, or worker calls.",
            "- Descriptive operator review material only.",
            "- Not execution approval and not runtime input.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT night batch acceptance report.")
    parser.add_argument("--request", required=True, help="Path to a local acceptance report request JSON file.")
    parser.add_argument("--output-report", required=True, help="Path for the output acceptance report JSON.")
    parser.add_argument("--output-markdown", required=True, help="Path for the output acceptance report Markdown.")
    args = parser.parse_args(argv)

    request = load_acceptance_report_request(args.request)
    report = build_acceptance_report(request)
    markdown = render_operator_report(report)

    report_path = Path(args.output_report)
    markdown_path = Path(args.output_markdown)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")
    return 0


_SECTION_REQUIRED_FIELDS = (
    "section_id",
    "section_label",
    "section_type",
    "local_reference",
    "source_fixture_reference",
    "operator_review_status",
    "record_count",
    "observed_state",
)
_ACCEPTANCE_REQUIRED_FIELDS = (
    "acceptance_id",
    "acceptance_label",
    "evidence_reference",
    "local_reference",
    "observed_state",
    "operator_review_status",
    "review_basis",
)
_VALIDATION_REQUIRED_FIELDS = (
    "validation_id",
    "command_label",
    "status",
    "local_reference",
    "operator_review_status",
)


def _build_section_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "observed_state": row["observed_state"],
        "operator_review_status": row["operator_review_status"],
        "record_count": int(row["record_count"]),
        "record_id": f"section.{row['section_id']}",
        "runner_state": REPORT_ROW_STATE,
        "section_id": row["section_id"],
        "section_label": row["section_label"],
        "section_type": row["section_type"],
        "source_fixture_reference": _normalize_local_reference(row["source_fixture_reference"]),
    }


def _build_acceptance_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "acceptance_id": row["acceptance_id"],
        "acceptance_label": row["acceptance_label"],
        "evidence_reference": _normalize_local_reference(row["evidence_reference"]),
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "observed_state": row["observed_state"],
        "operator_review_status": row["operator_review_status"],
        "record_id": f"acceptance.{row['acceptance_id']}",
        "review_basis": row["review_basis"],
        "runner_state": REPORT_ROW_STATE,
    }


def _build_validation_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "command_label": row["command_label"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "operator_review_status": row["operator_review_status"],
        "record_id": f"validation.{row['validation_id']}",
        "runner_state": REPORT_ROW_STATE,
        "status": row["status"],
        "validation_id": row["validation_id"],
    }


def _validate_rows(collection_name: str, rows: Sequence[Any], required_fields: Sequence[str]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"{collection_name}[{index}] must be an object")
            continue
        errors.extend(_missing_fields(row, required_fields, f"{collection_name}[{index}]"))
        if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{collection_name}[{index}].operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        for field_name in ("local_reference", "source_fixture_reference", "evidence_reference"):
            if field_name in row:
                errors.extend(_validate_local_reference(str(row[field_name]), f"{collection_name}[{index}].{field_name}"))
        if "record_count" in row:
            try:
                record_count = int(row["record_count"])
            except (TypeError, ValueError):
                errors.append(f"{collection_name}[{index}].record_count must be an integer")
            else:
                if record_count < 0:
                    errors.append(f"{collection_name}[{index}].record_count must not be negative")
    return errors


def _validate_local_reference(reference: str, field_path: str) -> list[str]:
    normalized = _normalize_local_reference(reference)
    errors: list[str] = []
    if _is_network_like(normalized):
        errors.append(f"{field_path} must be a local path")
    if Path(normalized).is_absolute():
        errors.append(f"{field_path} must be repository-relative")
    if _contains_path_traversal(normalized):
        errors.append(f"{field_path} must not use traversal")
    if _is_forbidden_reference(normalized):
        errors.append(f"{field_path} is outside the local acceptance report boundary")
    if not normalized.startswith(ALLOWED_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{field_path} must stay under allowed local PMBOT paths")
    return errors


def _is_forbidden_reference(reference: str) -> bool:
    if reference.startswith(FORBIDDEN_LOCAL_REFERENCE_PREFIXES):
        return True
    return any(f"/{prefix}" in reference for prefix in FORBIDDEN_LOCAL_REFERENCE_PREFIXES)


def _normalize_local_reference(reference: str) -> str:
    return reference.replace("\\", "/").strip()


def _is_network_like(reference: str) -> bool:
    lowered = reference.lower()
    return "://" in lowered or lowered.startswith(("http:", "https:"))


def _contains_path_traversal(reference: str) -> bool:
    return any(part == ".." for part in reference.split("/"))


def _missing_fields(value: Mapping[str, Any], required_fields: Iterable[str], label: str) -> list[str]:
    return [f"{label}.{field_name} is required" for field_name in required_fields if field_name not in value]


def _duplicate_id_errors(collection_name: str, rows: object, id_field: str) -> list[str]:
    if not isinstance(rows, list):
        return []
    seen: set[str] = set()
    duplicates: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping) or id_field not in row:
            continue
        value = str(row[id_field])
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        return [f"{collection_name}.{id_field} contains duplicate values: {', '.join(sorted(duplicates))}"]
    return []


def _list_or_error(value: object, field_name: str, errors: list[str]) -> list[Any]:
    if isinstance(value, list):
        return value
    errors.append(f"{field_name} must be a list")
    return []


def _collect_local_references(*collections: Sequence[Mapping[str, Any]]) -> set[str]:
    references: set[str] = set()
    for collection in collections:
        for row in collection:
            if not isinstance(row, Mapping):
                continue
            for field_name in ("local_reference", "source_fixture_reference", "evidence_reference"):
                if field_name in row:
                    references.add(_normalize_local_reference(str(row[field_name])))
    return references


def _blocked_term_errors(value: object, path: str) -> list[str]:
    if isinstance(value, Mapping):
        errors: list[str] = []
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_blocked_review_term(str(key)):
                errors.append(f"blocked review term detected at {key_path}")
            errors.extend(_blocked_term_errors(nested_value, key_path))
        return errors
    if isinstance(value, list):
        errors = []
        for index, nested_value in enumerate(value):
            errors.extend(_blocked_term_errors(nested_value, f"{path}[{index}]"))
        return errors
    if isinstance(value, str) and _has_blocked_review_term(value):
        return [f"blocked review term detected at {path}"]
    return []


def _has_blocked_review_term(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & BLOCKED_REVIEW_TERMS)


def _count_pending(*collections: Sequence[Mapping[str, Any]]) -> int:
    return sum(
        1
        for collection in collections
        for row in collection
        if isinstance(row, Mapping) and row.get("operator_review_status") == OPERATOR_REVIEW_STATUS
    )


def _stable_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


if __name__ == "__main__":
    raise SystemExit(main())
