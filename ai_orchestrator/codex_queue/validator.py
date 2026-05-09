from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .schema import (
    PRIORITY_VALUES,
    REQUIRED_TOP_LEVEL_FIELDS,
    RISK_FLAG_FIELDS,
    SCHEMA_VERSION,
    STATUS_VALUES,
    TASK_ID_RE,
    TASK_TYPE_VALUES,
)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
        }


def validate_packet(packet: Mapping[str, Any] | Any) -> ValidationResult:
    errors: list[str] = []

    if not isinstance(packet, Mapping):
        return ValidationResult(False, ("packet must be a JSON object",))

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in packet:
            errors.append(f"missing required field: {field}")

    if packet.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")

    task_id = packet.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        errors.append("task_id must be a non-empty string")
    elif not TASK_ID_RE.match(task_id):
        errors.append("task_id must match safe uppercase identifier style")

    title = packet.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title must be a non-empty string")

    status = packet.get("status")
    if status not in STATUS_VALUES:
        errors.append(f"status must be one of: {', '.join(STATUS_VALUES)}")

    priority = packet.get("priority")
    if priority not in PRIORITY_VALUES:
        errors.append(f"priority must be one of: {', '.join(PRIORITY_VALUES)}")

    task_type = packet.get("task_type")
    if task_type not in TASK_TYPE_VALUES:
        errors.append(f"task_type must be one of: {', '.join(TASK_TYPE_VALUES)}")

    summary = packet.get("summary")
    if not isinstance(summary, str):
        errors.append("summary must be a string")

    operator_notes = packet.get("operator_notes")
    if not isinstance(operator_notes, str):
        errors.append("operator_notes must be a string")

    _validate_string_list(packet.get("instructions"), "instructions", errors, non_empty=True)
    _validate_string_list(packet.get("safety_boundaries"), "safety_boundaries", errors, non_empty=True)
    _validate_string_list(packet.get("acceptance_checks"), "acceptance_checks", errors, non_empty=False)

    expected_outputs = packet.get("expected_outputs")
    if not isinstance(expected_outputs, list):
        errors.append("expected_outputs must be a list")

    _validate_source(packet.get("source"), errors)
    _validate_repo(packet.get("repo"), errors)
    _validate_symphony_mapping(packet.get("symphony_mapping"), status, errors)
    _validate_risk_flags(packet.get("risk_flags"), errors)

    return ValidationResult(not errors, tuple(errors))


def _validate_string_list(value: Any, field_name: str, errors: list[str], *, non_empty: bool) -> None:
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list of strings")
        return
    if non_empty and not value:
        errors.append(f"{field_name} must be a non-empty list of strings")
    for index, item in enumerate(value):
        if not isinstance(item, str) or (non_empty and not item.strip()):
            errors.append(f"{field_name}[{index}] must be a non-empty string")


def _validate_source(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("source must be an object")
        return
    if not isinstance(value.get("origin"), str) or not value.get("origin", "").strip():
        errors.append("source.origin must be a non-empty string")
    if not isinstance(value.get("reference"), str):
        errors.append("source.reference must be a string")


def _validate_repo(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("repo must be an object")
        return
    if not isinstance(value.get("repo_root"), str) or not value.get("repo_root", "").strip():
        errors.append("repo.repo_root must be a non-empty string")
    if not isinstance(value.get("base_branch"), str) or not value.get("base_branch", "").strip():
        errors.append("repo.base_branch must be a non-empty string")
    target_branch = value.get("target_branch")
    if target_branch is not None and not isinstance(target_branch, str):
        errors.append("repo.target_branch must be a string or null")
    if not isinstance(value.get("allowed_paths"), list):
        errors.append("repo.allowed_paths must be a list")
    elif not all(isinstance(item, str) for item in value.get("allowed_paths", [])):
        errors.append("repo.allowed_paths must contain only strings")
    if not isinstance(value.get("forbidden_paths"), list):
        errors.append("repo.forbidden_paths must be a list")
    elif not all(isinstance(item, str) for item in value.get("forbidden_paths", [])):
        errors.append("repo.forbidden_paths must contain only strings")


def _validate_symphony_mapping(value: Any, status: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("symphony_mapping must be an object")
        return

    issue_id = value.get("issue_id")
    if issue_id is not None and not isinstance(issue_id, str):
        errors.append("symphony_mapping.issue_id must be a string or null")

    workspace_key = value.get("workspace_key")
    if workspace_key is not None and not isinstance(workspace_key, str):
        errors.append("symphony_mapping.workspace_key must be a string or null")

    proof_required = value.get("proof_of_work_required")
    human_required = value.get("human_review_required")
    if not isinstance(proof_required, bool):
        errors.append("symphony_mapping.proof_of_work_required must be a boolean")
    if not isinstance(human_required, bool):
        errors.append("symphony_mapping.human_review_required must be a boolean")
    if status in {"approved", "planned"} and proof_required is not True:
        errors.append("symphony_mapping.proof_of_work_required must be true for approved/planned tasks")
    if status in {"approved", "planned"} and human_required is not True:
        errors.append("symphony_mapping.human_review_required must be true for approved/planned tasks")


def _validate_risk_flags(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("risk_flags must be an object")
        return

    for field in RISK_FLAG_FIELDS:
        if field not in value:
            errors.append(f"risk_flags.{field} is required")
        elif not isinstance(value[field], bool):
            errors.append(f"risk_flags.{field} must be a boolean")

    for field, flag_value in value.items():
        if field not in RISK_FLAG_FIELDS:
            errors.append(f"risk_flags.{field} is not recognized")
        elif not isinstance(flag_value, bool):
            errors.append(f"risk_flags.{field} must be a boolean")

