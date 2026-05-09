from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

TASK_ID = "PMBOT-OPERATOR-003-SUPERVISED-LIVE-MORNING-REVIEW-CARD-LOCAL-ONLY"
REQUEST_CONTRACT_VERSION = "pmbot_local_supervised_live_morning_review_card_request.v1"
CARD_CONTRACT_VERSION = "pmbot_local_supervised_live_morning_review_card.v1"
LOCAL_RUN_MODE = "local_static_supervised_live_morning_review_card"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
CARD_ROW_STATE = "ready_for_operator_review"
SAMPLE_CARD_PATH = "pm_bot/dashboard/samples/local_supervised_live_morning_review_card.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/dashboard/samples/local_supervised_live_morning_review_card.fixture.md"
CREATED_AT = "2026-05-09T04:00:00Z"
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
    "live_data_refresh_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "supervised_live_transition_allowed": False,
    "timed_automation_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


@dataclass(frozen=True)
class SupervisedLiveMorningReviewCardValidationResult:
    valid: bool
    errors: tuple[str, ...]


class SupervisedLiveMorningReviewCardValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_card_request(path: str | Path) -> dict[str, Any]:
    normalized = _normalize_local_reference(str(path))
    if _is_network_like(normalized):
        raise SupervisedLiveMorningReviewCardValidationError(("request path must be local",))
    if _contains_path_traversal(normalized):
        raise SupervisedLiveMorningReviewCardValidationError(("request path must not use traversal",))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_supervised_live_morning_review_card(request: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_card_request(request)
    if not validation.valid:
        raise SupervisedLiveMorningReviewCardValidationError(validation.errors)

    card_sections = [_build_section_row(row) for row in request["card_sections"]]
    review_rows = [_build_review_row(row) for row in request["review_records"]]
    safety_rows = [_build_safety_row(row) for row in request["safety_records"]]
    validation_rows = [_build_validation_row(row) for row in request["validation_records"]]
    local_references = _collect_local_references(card_sections, review_rows, safety_rows, validation_rows)

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
            "required": True,
            "reviewed_at": None,
            "reviewed_by": None,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": list(request["operator_review_steps"]),
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "review_date": request["review_date"],
        "review_records": review_rows,
        "run_label": request["run_label"],
        "run_mode": LOCAL_RUN_MODE,
        "safety_boundaries": deepcopy(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "safety_records": safety_rows,
        "summary_counts": {
            "card_sections": len(card_sections),
            "local_references": len(local_references),
            "operator_review_pending_records": _count_pending(
                card_sections,
                review_rows,
                safety_rows,
                validation_rows,
            ),
            "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
            "review_records": len(review_rows),
            "safety_records": len(safety_rows),
            "validation_records": len(validation_rows),
            "warnings": 0,
        },
        "task_id": TASK_ID,
        "validation_records": validation_rows,
        "warnings": [],
    }

    artifact_validation = validate_supervised_live_morning_review_card(card)
    if not artifact_validation.valid:
        raise SupervisedLiveMorningReviewCardValidationError(artifact_validation.errors)
    return card


def validate_card_request(request: Mapping[str, Any]) -> SupervisedLiveMorningReviewCardValidationResult:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "card_id",
        "card_label",
        "run_label",
        "review_date",
        "scope",
        "local_only",
        "operator_review_required",
        "card_sections",
        "review_records",
        "safety_records",
        "validation_records",
        "operator_review_steps",
    )
    errors.extend(_missing_fields(request, required_fields, "request"))

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "local_supervised_live_morning_review_card":
        errors.append("scope must be local_supervised_live_morning_review_card")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if not _is_non_empty_string_list(request.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")

    for field_name in ("card_sections", "review_records", "safety_records", "validation_records"):
        if field_name in request and not isinstance(request[field_name], list):
            errors.append(f"{field_name} must be a list")

    if isinstance(request.get("card_sections"), list):
        errors.extend(_validate_rows("card_sections", request["card_sections"], _SECTION_REQUIRED_FIELDS))
    if isinstance(request.get("review_records"), list):
        errors.extend(_validate_rows("review_records", request["review_records"], _REVIEW_REQUIRED_FIELDS))
    if isinstance(request.get("safety_records"), list):
        errors.extend(_validate_rows("safety_records", request["safety_records"], _SAFETY_REQUIRED_FIELDS))
    if isinstance(request.get("validation_records"), list):
        errors.extend(_validate_rows("validation_records", request["validation_records"], _VALIDATION_REQUIRED_FIELDS))

    errors.extend(_duplicate_id_errors("card_sections", request.get("card_sections"), "section_id"))
    errors.extend(_duplicate_id_errors("review_records", request.get("review_records"), "artifact_id"))
    errors.extend(_duplicate_id_errors("safety_records", request.get("safety_records"), "boundary_id"))
    errors.extend(_duplicate_id_errors("validation_records", request.get("validation_records"), "validation_id"))
    errors.extend(_forbidden_card_term_errors(request, "request"))
    return SupervisedLiveMorningReviewCardValidationResult(valid=not errors, errors=tuple(errors))


def validate_supervised_live_morning_review_card(
    card: Mapping[str, Any],
) -> SupervisedLiveMorningReviewCardValidationResult:
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
        "required_validation_commands",
        "review_date",
        "review_records",
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

    if card.get("contract_version") != CARD_CONTRACT_VERSION:
        errors.append(f"contract_version must be {CARD_CONTRACT_VERSION}")
    if card.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if card.get("created_at") != CREATED_AT:
        errors.append(f"created_at must be {CREATED_AT}")
    if card.get("run_mode") != LOCAL_RUN_MODE:
        errors.append(f"run_mode must be {LOCAL_RUN_MODE}")
    if card.get("local_only") is not True:
        errors.append("local_only must be true")
    if card.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if card.get("operator_review", {}).get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"operator_review.status must be {OPERATOR_REVIEW_STATUS}")
    if card.get("operator_review", {}).get("required") is not True:
        errors.append("operator_review.required must be true")
    if not _is_non_empty_string_list(card.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")
    if card.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(card.get("warnings")):
        errors.append("warnings must be a list of strings")
    if card.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match the local validation command list")
    if card.get("safety_boundaries") != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only supervised-live morning review card boundary")

    card_sections = _list_or_error(card.get("card_sections"), "card_sections", errors)
    review_rows = _list_or_error(card.get("review_records"), "review_records", errors)
    safety_rows = _list_or_error(card.get("safety_records"), "safety_records", errors)
    validation_rows = _list_or_error(card.get("validation_records"), "validation_records", errors)

    for collection_name, rows in (
        ("card_sections", card_sections),
        ("review_records", review_rows),
        ("safety_records", safety_rows),
        ("validation_records", validation_rows),
    ):
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"{collection_name}[{index}] must be an object")
                continue
            if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
                errors.append(f"{collection_name}[{index}].operator_review_status must be {OPERATOR_REVIEW_STATUS}")
            if row.get("runner_state") != CARD_ROW_STATE:
                errors.append(f"{collection_name}[{index}].runner_state must be {CARD_ROW_STATE}")
            if "required_state" in row and row["required_state"] != OPERATOR_REVIEW_STATUS:
                errors.append(f"{collection_name}[{index}].required_state must be {OPERATOR_REVIEW_STATUS}")
            for field_name in ("fixture_reference", "local_reference", "source_reference"):
                if field_name in row:
                    errors.extend(_validate_local_reference(str(row[field_name]), f"{collection_name}[{index}].{field_name}"))
            if "record_count" in row:
                errors.extend(_validate_non_negative_integer(row["record_count"], f"{collection_name}[{index}].record_count"))

    summary_counts = card.get("summary_counts")
    if isinstance(summary_counts, Mapping):
        local_references = _collect_local_references(card_sections, review_rows, safety_rows, validation_rows)
        expected_counts = {
            "card_sections": len(card_sections),
            "local_references": len(local_references),
            "operator_review_pending_records": _count_pending(
                card_sections,
                review_rows,
                safety_rows,
                validation_rows,
            ),
            "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
            "review_records": len(review_rows),
            "safety_records": len(safety_rows),
            "validation_records": len(validation_rows),
            "warnings": len(card.get("warnings", [])) if isinstance(card.get("warnings"), list) else 0,
        }
        if dict(summary_counts) != expected_counts:
            errors.append("summary_counts must match supervised-live morning review card content")
    else:
        errors.append("summary_counts must be an object")

    errors.extend(_forbidden_card_term_errors(card, "card"))
    return SupervisedLiveMorningReviewCardValidationResult(valid=not errors, errors=tuple(errors))


def find_forbidden_card_terms(value: object) -> list[str]:
    return _forbidden_card_term_errors(value, "$")


def render_operator_card(card: Mapping[str, Any]) -> str:
    validation = validate_supervised_live_morning_review_card(card)
    if not validation.valid:
        raise SupervisedLiveMorningReviewCardValidationError(validation.errors)

    lines = [
        "# PMBOT Supervised Live Morning Review Card",
        "",
        f"Task: `{card['task_id']}`",
        f"Card: `{card['card_id']}`",
        f"Build: `{card['build_id']}`",
        f"Contract: `{card['contract_version']}`",
        f"Run mode: `{card['run_mode']}`",
        f"Operator review: `{card['operator_review']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Card sections: {card['summary_counts']['card_sections']}",
        f"- Review records: {card['summary_counts']['review_records']}",
        f"- Safety records: {card['summary_counts']['safety_records']}",
        f"- Validation records: {card['summary_counts']['validation_records']}",
        f"- Pending operator review records: {card['summary_counts']['operator_review_pending_records']}",
        f"- Local references: {card['summary_counts']['local_references']}",
        f"- Warnings: {card['summary_counts']['warnings']}",
        "",
        "## Card Sections",
        "",
    ]
    for row in card["card_sections"]:
        lines.append(
            f"- `{row['section_id']}`: role `{row['section_role']}`, records {row['record_count']}, "
            f"state `{row['observed_state']}`, reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Review Records", ""])
    for row in card["review_records"]:
        lines.append(
            f"- `{row['artifact_id']}`: type `{row['artifact_type']}`, state `{row['observed_state']}`, "
            f"review `{row['operator_review_status']}`, fixture `{row['fixture_reference']}`"
        )

    lines.extend(["", "## Safety Records", ""])
    for row in card["safety_records"]:
        lines.append(
            f"- `{row['boundary_id']}`: state `{row['observed_state']}`, reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Validation Records", ""])
    for row in card["validation_records"]:
        lines.append(
            f"- `{row['validation_id']}`: status `{row['status']}`, command `{row['command_label']}`, "
            f"reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in card["operator_review_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local static samples only.",
            "- Makes no network, LLM provider, external service, wallet, order, transaction endpoint, runtime, browser, scheduler, worker, timed automation, or resident process calls.",
            "- Descriptive operator review card only; no live transition, data refresh, endpoint, or execution output.",
            "- Not execution approval and not runtime input.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT supervised-live morning review card.")
    parser.add_argument("--request", required=True, help="Path to a local supervised-live morning review card request JSON file.")
    parser.add_argument("--output-card", required=True, help="Path for the output card JSON.")
    parser.add_argument("--output-report", required=True, help="Path for the output card Markdown.")
    args = parser.parse_args(argv)

    request = load_card_request(args.request)
    card = build_supervised_live_morning_review_card(request)
    report = render_operator_card(card)

    card_path = Path(args.output_card)
    report_path = Path(args.output_report)
    card_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(report, encoding="utf-8")
    return 0


_SECTION_REQUIRED_FIELDS = (
    "section_id",
    "section_label",
    "section_role",
    "local_reference",
    "source_reference",
    "operator_review_status",
    "observed_state",
    "record_count",
)
_REVIEW_REQUIRED_FIELDS = (
    "artifact_id",
    "artifact_label",
    "artifact_type",
    "contract_version",
    "fixture_reference",
    "local_reference",
    "observed_state",
    "operator_review_status",
    "required_state",
)
_SAFETY_REQUIRED_FIELDS = (
    "boundary_id",
    "boundary_label",
    "local_reference",
    "observed_state",
    "operator_review_status",
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
        "runner_state": CARD_ROW_STATE,
        "section_id": row["section_id"],
        "section_label": row["section_label"],
        "section_role": row["section_role"],
        "source_reference": _normalize_local_reference(row["source_reference"]),
    }


def _build_review_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": row["artifact_id"],
        "artifact_label": row["artifact_label"],
        "artifact_type": row["artifact_type"],
        "contract_version": row["contract_version"],
        "fixture_reference": _normalize_local_reference(row["fixture_reference"]),
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "observed_state": row["observed_state"],
        "operator_review_status": row["operator_review_status"],
        "record_id": f"review.{row['artifact_id']}",
        "required_state": row["required_state"],
        "runner_state": CARD_ROW_STATE,
    }


def _build_safety_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "boundary_id": row["boundary_id"],
        "boundary_label": row["boundary_label"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "observed_state": row["observed_state"],
        "operator_review_status": row["operator_review_status"],
        "record_id": f"safety.{row['boundary_id']}",
        "runner_state": CARD_ROW_STATE,
    }


def _build_validation_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "command_label": row["command_label"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "operator_review_status": row["operator_review_status"],
        "record_id": f"validation.{row['validation_id']}",
        "runner_state": CARD_ROW_STATE,
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
        if "required_state" in row and row["required_state"] != OPERATOR_REVIEW_STATUS:
            errors.append(f"{collection_name}[{index}].required_state must be {OPERATOR_REVIEW_STATUS}")
        for field_name in ("fixture_reference", "local_reference", "source_reference"):
            if field_name in row:
                errors.extend(_validate_local_reference(str(row[field_name]), f"{collection_name}[{index}].{field_name}"))
        if "record_count" in row:
            errors.extend(_validate_non_negative_integer(row["record_count"], f"{collection_name}[{index}].record_count"))
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
        errors.append(f"{field_path} is outside the supervised-live morning review card boundary")
    if not normalized.startswith(ALLOWED_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{field_path} must stay under allowed local PMBOT paths")
    return errors


def _validate_non_negative_integer(value: object, field_path: str) -> list[str]:
    converted = _as_non_bool_int(value)
    if converted is None:
        return [f"{field_path} must be an integer"]
    if converted < 0:
        return [f"{field_path} must not be negative"]
    return []


def _as_non_bool_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


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
            for field_name in ("fixture_reference", "local_reference", "source_reference"):
                if field_name in row:
                    references.add(_normalize_local_reference(str(row[field_name])))
    return references


def _forbidden_card_term_errors(value: object, path: str) -> list[str]:
    if isinstance(value, Mapping):
        errors: list[str] = []
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_card_term(str(key)):
                errors.append(f"forbidden supervised-live morning review card field detected at {key_path}")
            errors.extend(_forbidden_card_term_errors(nested_value, key_path))
        return errors
    if isinstance(value, list):
        errors = []
        for index, nested_value in enumerate(value):
            errors.extend(_forbidden_card_term_errors(nested_value, f"{path}[{index}]"))
        return errors
    if isinstance(value, str) and _has_forbidden_card_term(value):
        return [f"forbidden supervised-live morning review card value detected at {path}"]
    return []


def _has_forbidden_card_term(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_CARD_TERMS)


def _count_pending(*collections: Sequence[Mapping[str, Any]]) -> int:
    return sum(
        1
        for collection in collections
        for row in collection
        if isinstance(row, Mapping) and row.get("operator_review_status") == OPERATOR_REVIEW_STATUS
    )


def _is_non_empty_string_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _stable_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


if __name__ == "__main__":
    raise SystemExit(main())
