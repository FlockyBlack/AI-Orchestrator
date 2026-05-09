from __future__ import annotations

from typing import Any, Mapping

from .result_schema import (
    DANGEROUS_SAFETY_FLAGS,
    LIST_FIELDS,
    REQUIRED_SAFETY_FIELDS,
    REQUIRED_TOP_LEVEL_FIELDS,
    SAFETY_BOOLEAN_FIELDS,
    SAFETY_COUNT_FIELDS,
    SCHEMA_VERSION,
    STATUS_VALUES,
)
from .validator import ValidationResult


def validate_result(result: Mapping[str, Any] | Any) -> ValidationResult:
    errors: list[str] = []

    if not isinstance(result, Mapping):
        return ValidationResult(False, ("result must be a JSON object",))

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in result:
            errors.append(f"missing required field: {field}")

    if result.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")

    task_id = result.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        errors.append("task_id must be a non-empty string")

    status = result.get("status")
    if status not in STATUS_VALUES:
        errors.append(f"status must be one of: {', '.join(STATUS_VALUES)}")

    completed_by = result.get("completed_by")
    if not isinstance(completed_by, str) or not completed_by.strip():
        errors.append("completed_by must be a non-empty string")

    completed_at = result.get("completed_at")
    if completed_at is not None and not isinstance(completed_at, str):
        errors.append("completed_at must be a string or null")

    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary must be a non-empty string")

    for field in LIST_FIELDS:
        if not isinstance(result.get(field), list):
            errors.append(f"{field} must be a list")

    acceptance_checks_passed = result.get("acceptance_checks_passed")
    if not isinstance(acceptance_checks_passed, bool):
        errors.append("acceptance_checks_passed must be a boolean")

    operator_review_notes = result.get("operator_review_notes")
    if not isinstance(operator_review_notes, str):
        errors.append("operator_review_notes must be a string")

    next_recommended_action = result.get("next_recommended_action")
    if not isinstance(next_recommended_action, str):
        errors.append("next_recommended_action must be a string")

    _validate_files_deleted(result, status, errors)
    _validate_safety_confirmation(result.get("safety_confirmation"), errors)

    return ValidationResult(not errors, tuple(errors))


def _validate_files_deleted(result: Mapping[str, Any], status: Any, errors: list[str]) -> None:
    files_deleted = result.get("files_deleted")
    if not isinstance(files_deleted, list):
        return
    if files_deleted and status not in {"blocked", "failed"}:
        errors.append("files_deleted must be empty unless status is blocked or failed")


def _validate_safety_confirmation(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("safety_confirmation must be an object")
        return

    for field in REQUIRED_SAFETY_FIELDS:
        if field not in value:
            errors.append(f"safety_confirmation.{field} is required")

    for field in SAFETY_BOOLEAN_FIELDS:
        if field in value and not isinstance(value[field], bool):
            errors.append(f"safety_confirmation.{field} must be a boolean")

    for field in SAFETY_COUNT_FIELDS:
        count = value.get(field)
        if field in value and type(count) is not int:
            errors.append(f"safety_confirmation.{field} must be an integer")
        elif isinstance(count, int) and count < 0:
            errors.append(f"safety_confirmation.{field} must be a non-negative integer")

    for field in DANGEROUS_SAFETY_FLAGS:
        if value.get(field) is True:
            errors.append(f"safety_confirmation.{field} must be false")

    network_calls = value.get("network_calls_performed", 0)
    openrouter_calls = value.get("openrouter_calls_performed", 0)
    polymarket_calls = value.get("polymarket_api_calls_performed", 0)

    if type(network_calls) is int and network_calls > 0:
        errors.append("safety_confirmation.network_calls_performed must be 0")
    if type(openrouter_calls) is int and openrouter_calls > 0:
        errors.append("safety_confirmation.openrouter_calls_performed must be 0")
    if type(polymarket_calls) is int and polymarket_calls > 0:
        errors.append("safety_confirmation.polymarket_api_calls_performed must be 0")
