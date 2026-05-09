from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

TASK_ID = "PMBOT-REHEARSAL-011-REHEARSAL-READINESS-DASHBOARD-CARD-LOCAL-ONLY"
REQUEST_CONTRACT_VERSION = "pmbot_rehearsal_readiness_dashboard_card_request.v1"
CARD_CONTRACT_VERSION = "pmbot_rehearsal_readiness_dashboard_card.v1"
LOCAL_RUN_MODE = "local_static_rehearsal_readiness_dashboard_card"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
CARD_ROW_STATE = "ready_for_operator_review"
CREATED_AT = "2026-05-09T07:00:00Z"
SAMPLE_CARD_PATH = "pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/dashboard/samples/pmbot_rehearsal_readiness_dashboard_card.fixture.md"
REQUIRED_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)

ALLOWED_LOCAL_REFERENCE_PREFIXES = (
    "docs/",
    "pm_bot/dashboard/",
    "pm_bot/readiness/",
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
FORBIDDEN_CARD_TERMS = {
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
    "llm_provider_calls_allowed": False,
    "local_fixtures_only": True,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_instruction_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "openrouter_calls_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "polymarket_api_calls_allowed": False,
    "run_codex_changes_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_path_access_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}

_SECTION_REQUIRED_FIELDS = (
    "local_reference",
    "notes",
    "operator_review_status",
    "section_id",
    "section_label",
    "section_role",
    "source_record_ids",
)
_READINESS_REQUIRED_FIELDS = (
    "artifact_id",
    "artifact_label",
    "artifact_type",
    "contract_version",
    "expected_state",
    "local_reference",
    "notes",
    "operator_review_status",
    "record_id",
    "record_role",
    "run_mode",
    "source_task_id",
)
_SAFETY_REQUIRED_FIELDS = (
    "boundary_id",
    "boundary_label",
    "local_reference",
    "operator_review_status",
    "required_state",
    "status_label",
)
_VALIDATION_REQUIRED_FIELDS = (
    "command_label",
    "local_reference",
    "notes",
    "operator_review_status",
    "status",
    "validation_id",
)


@dataclass(frozen=True)
class RehearsalReadinessDashboardCardValidationResult:
    valid: bool
    errors: tuple[str, ...]


class RehearsalReadinessDashboardCardValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_card_request(path: str | Path) -> dict[str, Any]:
    normalized = _normalize_local_reference(str(path))
    if _is_network_like(normalized):
        raise RehearsalReadinessDashboardCardValidationError(("request path must be local",))
    if _contains_path_traversal(normalized):
        raise RehearsalReadinessDashboardCardValidationError(("request path must not use traversal",))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_rehearsal_readiness_dashboard_card(request: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_card_request(request)
    if not validation.valid:
        raise RehearsalReadinessDashboardCardValidationError(validation.errors)

    card_sections = [_build_section_row(row) for row in request["card_sections"]]
    readiness_records = [_build_readiness_row(row) for row in request["readiness_records"]]
    safety_records = [_build_safety_row(row) for row in request["safety_records"]]
    validation_records = [_build_validation_row(row) for row in request["validation_records"]]
    local_references = _collect_local_references(
        card_sections,
        readiness_records,
        safety_records,
        validation_records,
    )

    card = {
        "build_id": f"{request['card_id']}-{_stable_digest(request)}",
        "card_id": request["card_id"],
        "card_label": request["card_label"],
        "card_sections": card_sections,
        "contract_version": CARD_CONTRACT_VERSION,
        "created_at": CREATED_AT,
        "errors": [],
        "local_only": True,
        "operator_review": {
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": list(request["operator_review_steps"]),
        "readiness_records": readiness_records,
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "review_date": request["review_date"],
        "run_label": request["run_label"],
        "run_mode": LOCAL_RUN_MODE,
        "safety_boundaries": deepcopy(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "safety_records": safety_records,
        "summary_counts": {
            "card_sections": len(card_sections),
            "local_references": len(local_references),
            "operator_review_pending_records": _count_pending(
                card_sections,
                readiness_records,
                safety_records,
                validation_records,
            ),
            "readiness_records": len(readiness_records),
            "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
            "safety_records": len(safety_records),
            "validation_records": len(validation_records),
            "warnings": 0,
        },
        "task_id": TASK_ID,
        "validation_records": validation_records,
        "warnings": [],
    }

    artifact_validation = validate_rehearsal_readiness_dashboard_card(card)
    if not artifact_validation.valid:
        raise RehearsalReadinessDashboardCardValidationError(artifact_validation.errors)
    return card


def validate_card_request(
    request: Mapping[str, Any],
) -> RehearsalReadinessDashboardCardValidationResult:
    errors: list[str] = []
    required_fields = (
        "card_id",
        "card_label",
        "card_sections",
        "contract_version",
        "local_only",
        "operator_review_required",
        "operator_review_steps",
        "readiness_records",
        "review_date",
        "run_label",
        "safety_records",
        "scope",
        "validation_records",
    )
    errors.extend(_missing_fields(request, required_fields, "request"))

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "rehearsal_readiness_dashboard_card":
        errors.append("scope must be rehearsal_readiness_dashboard_card")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if not _is_non_empty_string_list(request.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")

    for field_name in ("card_sections", "readiness_records", "safety_records", "validation_records"):
        if field_name in request and not isinstance(request[field_name], list):
            errors.append(f"{field_name} must be a list")

    if isinstance(request.get("card_sections"), list):
        errors.extend(_validate_rows("card_sections", request["card_sections"], _SECTION_REQUIRED_FIELDS))
    if isinstance(request.get("readiness_records"), list):
        errors.extend(_validate_rows("readiness_records", request["readiness_records"], _READINESS_REQUIRED_FIELDS))
    if isinstance(request.get("safety_records"), list):
        errors.extend(_validate_rows("safety_records", request["safety_records"], _SAFETY_REQUIRED_FIELDS))
    if isinstance(request.get("validation_records"), list):
        errors.extend(_validate_rows("validation_records", request["validation_records"], _VALIDATION_REQUIRED_FIELDS))

    errors.extend(_duplicate_id_errors("card_sections", request.get("card_sections"), "section_id"))
    errors.extend(_duplicate_id_errors("readiness_records", request.get("readiness_records"), "record_id"))
    errors.extend(_duplicate_id_errors("safety_records", request.get("safety_records"), "boundary_id"))
    errors.extend(_duplicate_id_errors("validation_records", request.get("validation_records"), "validation_id"))
    errors.extend(_forbidden_card_term_errors(request, "request"))
    return RehearsalReadinessDashboardCardValidationResult(valid=not errors, errors=tuple(errors))


def validate_rehearsal_readiness_dashboard_card(
    card: Mapping[str, Any],
) -> RehearsalReadinessDashboardCardValidationResult:
    errors: list[str] = []
    required_fields = (
        "build_id",
        "card_id",
        "card_label",
        "card_sections",
        "contract_version",
        "created_at",
        "errors",
        "local_only",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "readiness_records",
        "required_validation_commands",
        "review_date",
        "run_label",
        "run_mode",
        "safety_boundaries",
        "safety_records",
        "summary_counts",
        "task_id",
        "validation_records",
        "warnings",
    )
    errors.extend(_missing_fields(card, required_fields, "card"))

    if card.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if card.get("contract_version") != CARD_CONTRACT_VERSION:
        errors.append(f"contract_version must be {CARD_CONTRACT_VERSION}")
    if card.get("run_mode") != LOCAL_RUN_MODE:
        errors.append(f"run_mode must be {LOCAL_RUN_MODE}")
    if card.get("created_at") != CREATED_AT:
        errors.append(f"created_at must be {CREATED_AT}")
    if card.get("local_only") is not True:
        errors.append("local_only must be true")
    if card.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if card.get("operator_review") != {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }:
        errors.append("operator_review must remain pending")
    if card.get("errors") != []:
        errors.append("errors must be an empty list")
    if card.get("warnings") != []:
        errors.append("warnings must be an empty list")
    if card.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match the rehearsal readiness dashboard card commands")
    if card.get("safety_boundaries") != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only rehearsal readiness dashboard card boundary")
    if not _is_non_empty_string_list(card.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")

    card_sections = _list_or_empty(card.get("card_sections"), "card_sections", errors)
    readiness_records = _list_or_empty(card.get("readiness_records"), "readiness_records", errors)
    safety_records = _list_or_empty(card.get("safety_records"), "safety_records", errors)
    validation_records = _list_or_empty(card.get("validation_records"), "validation_records", errors)

    _validate_output_rows("card_sections", card_sections, errors)
    _validate_output_rows("readiness_records", readiness_records, errors)
    _validate_output_rows("safety_records", safety_records, errors)
    _validate_output_rows("validation_records", validation_records, errors)

    summary_counts = card.get("summary_counts")
    if isinstance(summary_counts, Mapping):
        expected_local_references = _collect_local_references(
            card_sections,
            readiness_records,
            safety_records,
            validation_records,
        )
        expected_counts = {
            "card_sections": len(card_sections),
            "local_references": len(expected_local_references),
            "operator_review_pending_records": _count_pending(
                card_sections,
                readiness_records,
                safety_records,
                validation_records,
            ),
            "readiness_records": len(readiness_records),
            "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
            "safety_records": len(safety_records),
            "validation_records": len(validation_records),
            "warnings": len(card.get("warnings", [])),
        }
        if summary_counts != expected_counts:
            errors.append("summary_counts must match rehearsal readiness dashboard card rows")
    else:
        errors.append("summary_counts must be an object")

    errors.extend(_forbidden_card_term_errors(card, "card"))
    return RehearsalReadinessDashboardCardValidationResult(valid=not errors, errors=tuple(errors))


def render_operator_card(card: Mapping[str, Any]) -> str:
    validation = validate_rehearsal_readiness_dashboard_card(card)
    if not validation.valid:
        raise RehearsalReadinessDashboardCardValidationError(validation.errors)

    lines = [
        "# PMBOT Rehearsal Readiness Dashboard Card",
        "",
        f"Task: `{card['task_id']}`",
        f"Card: `{card['card_id']}`",
        f"Build: `{card['build_id']}`",
        f"Contract: `{card['contract_version']}`",
        f"Run mode: `{card['run_mode']}`",
        f"Review date: `{card['review_date']}`",
        f"Operator review: `{card['operator_review']['status']}`",
        "",
        "## Sections",
    ]
    for section in card["card_sections"]:
        lines.append(
            "- "
            f"`{section['section_id']}`: role `{section['section_role']}`, "
            f"records {len(section['source_record_ids'])}, review `{section['operator_review_status']}`, "
            f"reference `{section['local_reference']}`"
        )

    lines.extend(["", "## Readiness Records"])
    for record in card["readiness_records"]:
        lines.append(
            "- "
            f"`{record['artifact_id']}`: type `{record['artifact_type']}`, "
            f"state `{record['expected_state']}`, review `{record['operator_review_status']}`, "
            f"reference `{record['local_reference']}`"
        )

    lines.extend(["", "## Safety Records"])
    for record in card["safety_records"]:
        lines.append(
            "- "
            f"`{record['boundary_id']}`: state `{record['required_state']}`, "
            f"review `{record['operator_review_status']}`, reference `{record['local_reference']}`"
        )

    lines.extend(["", "## Validation"])
    for record in card["validation_records"]:
        lines.append(
            "- "
            f"`{record['command_label']}`: status `{record['status']}`, "
            f"review `{record['operator_review_status']}`, reference `{record['local_reference']}`"
        )

    counts = card["summary_counts"]
    lines.extend(
        [
            "",
            "## Summary Counts",
            f"- Card sections: `{counts['card_sections']}`",
            f"- Readiness records: `{counts['readiness_records']}`",
            f"- Safety records: `{counts['safety_records']}`",
            f"- Validation records: `{counts['validation_records']}`",
            f"- Local references: `{counts['local_references']}`",
            f"- Pending operator review records: `{counts['operator_review_pending_records']}`",
            "",
            "## Operator Review Boundary",
            "- Descriptive readiness dashboard card only; no live data refresh, endpoint use, transaction output, or execution output.",
            "- Human review remains required before any later operational use.",
        ]
    )
    return "\n".join(lines) + "\n"


def find_forbidden_card_terms(value: object) -> list[str]:
    return _forbidden_card_term_errors(value, "$")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT rehearsal readiness dashboard card.")
    parser.add_argument("--request", required=True, help="Path to a local rehearsal dashboard card request JSON file.")
    parser.add_argument("--output-card", required=True, help="Path to write the local card JSON artifact.")
    parser.add_argument("--output-report", required=True, help="Path to write the local operator report markdown artifact.")
    args = parser.parse_args(argv)

    request = load_card_request(args.request)
    card = build_rehearsal_readiness_dashboard_card(request)
    report = render_operator_card(card)

    output_card = Path(args.output_card)
    output_report = Path(args.output_report)
    output_card.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_card.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_report.write_text(report, encoding="utf-8")
    return 0


def _build_section_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row["notes"],
        "operator_review_status": row["operator_review_status"],
        "runner_state": CARD_ROW_STATE,
        "section_id": row["section_id"],
        "section_label": row["section_label"],
        "section_role": row["section_role"],
        "source_record_ids": list(row["source_record_ids"]),
    }


def _build_readiness_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": row["artifact_id"],
        "artifact_label": row["artifact_label"],
        "artifact_type": row["artifact_type"],
        "contract_version": row["contract_version"],
        "expected_state": row["expected_state"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row["notes"],
        "operator_review_status": row["operator_review_status"],
        "record_id": row["record_id"],
        "record_role": row["record_role"],
        "run_mode": row["run_mode"],
        "runner_state": CARD_ROW_STATE,
        "source_task_id": row["source_task_id"],
    }


def _build_safety_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "boundary_id": row["boundary_id"],
        "boundary_label": row["boundary_label"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "operator_review_status": row["operator_review_status"],
        "required_state": row["required_state"],
        "runner_state": CARD_ROW_STATE,
        "status_label": row["status_label"],
    }


def _build_validation_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "command_label": row["command_label"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row["notes"],
        "operator_review_status": row["operator_review_status"],
        "record_id": row["validation_id"],
        "runner_state": CARD_ROW_STATE,
        "status": row["status"],
    }


def _validate_rows(field_name: str, rows: list[Any], required_fields: Sequence[str]) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows):
        row_path = f"{field_name}[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{row_path} must be an object")
            continue
        errors.extend(_missing_fields(row, required_fields, row_path))
        if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{row_path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if "source_record_ids" in row and not _is_non_empty_string_list(row.get("source_record_ids")):
            errors.append(f"{row_path}.source_record_ids must be a non-empty list of strings")
        for key, value in row.items():
            if key.endswith("reference"):
                errors.extend(_local_reference_errors(value, f"{row_path}.{key}"))
    return errors


def _validate_output_rows(field_name: str, rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        row_path = f"{field_name}[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{row_path} must be an object")
            continue
        if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{row_path}.operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if row.get("runner_state") != CARD_ROW_STATE:
            errors.append(f"{row_path}.runner_state must be {CARD_ROW_STATE}")
        for key, value in row.items():
            if key.endswith("reference"):
                errors.extend(_local_reference_errors(value, f"{row_path}.{key}"))


def _local_reference_errors(value: Any, field_path: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, str) or not value:
        return [f"{field_path} must be a non-empty local path"]
    normalized = _normalize_local_reference(value)
    if _is_network_like(normalized):
        errors.append(f"{field_path} must be a local path")
    if _contains_path_traversal(normalized):
        errors.append(f"{field_path} must not use traversal")
    if normalized.startswith(FORBIDDEN_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{field_path} is outside the rehearsal readiness dashboard card boundary")
    if not normalized.startswith(ALLOWED_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{field_path} must stay under allowed local rehearsal readiness dashboard card paths")
    if not Path(normalized).exists():
        errors.append(f"{field_path} must reference an existing local file")
    return errors


def _missing_fields(value: Mapping[str, Any], required_fields: Sequence[str], path: str) -> list[str]:
    return [f"{path}.{field} is required" for field in required_fields if field not in value]


def _duplicate_id_errors(field_name: str, rows: object, id_field: str) -> list[str]:
    if not isinstance(rows, list):
        return []
    seen: set[str] = set()
    errors: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        value = row.get(id_field)
        if not isinstance(value, str):
            continue
        if value in seen:
            errors.append(f"{field_name}.{id_field} must be unique: {value}")
        seen.add(value)
    return errors


def _collect_local_references(*row_groups: Iterable[Mapping[str, Any]]) -> set[str]:
    references: set[str] = set()
    for rows in row_groups:
        for row in rows:
            for key, value in row.items():
                if key.endswith("reference") and isinstance(value, str):
                    references.add(_normalize_local_reference(value))
    return references


def _count_pending(*row_groups: Iterable[Mapping[str, Any]]) -> int:
    return sum(
        1
        for rows in row_groups
        for row in rows
        if row.get("operator_review_status") == OPERATOR_REVIEW_STATUS
    )


def _list_or_empty(value: object, field_name: str, errors: list[str]) -> list[Any]:
    if isinstance(value, list):
        return value
    errors.append(f"{field_name} must be a list")
    return []


def _stable_digest(request: Mapping[str, Any]) -> str:
    payload = json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def _is_non_empty_string_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _is_network_like(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or lowered.startswith("//") or lowered.startswith(("http:", "https:"))


def _contains_path_traversal(value: str) -> bool:
    return any(part == ".." for part in value.replace("\\", "/").split("/"))


def _normalize_local_reference(value: str) -> str:
    normalized = value.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _forbidden_card_term_errors(value: object, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_token(str(key)):
                errors.append(f"forbidden rehearsal readiness dashboard card field detected at {key_path}")
            if key in {"local_reference", "required_validation_commands"}:
                continue
            errors.extend(_forbidden_card_term_errors(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            errors.extend(_forbidden_card_term_errors(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_forbidden_token(value):
        errors.append(f"forbidden rehearsal readiness dashboard card value detected at {path}")
    return errors


def _has_forbidden_token(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_CARD_TERMS)


if __name__ == "__main__":
    raise SystemExit(main())
