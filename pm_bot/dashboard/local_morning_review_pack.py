from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

TASK_ID = "PMBOT-OPERATOR-001-MORNING-REVIEW-PACK-LOCAL-ONLY"
REQUEST_CONTRACT_VERSION = "pmbot_local_morning_review_pack_request.v1"
PACK_CONTRACT_VERSION = "pmbot_local_morning_review_pack.v1"
LOCAL_RUN_MODE = "local_static_morning_review_pack"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
PACK_ROW_STATE = "ready_for_operator_review"
SAMPLE_PACK_PATH = "pm_bot/dashboard/samples/local_morning_review_pack.fixture.json"
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
class MorningReviewPackValidationResult:
    valid: bool
    errors: tuple[str, ...]


class MorningReviewPackValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_morning_review_request(path: str | Path) -> dict[str, Any]:
    normalized = _normalize_local_reference(str(path))
    if _is_network_like(normalized):
        raise MorningReviewPackValidationError(("request path must be local",))
    if _contains_path_traversal(normalized):
        raise MorningReviewPackValidationError(("request path must not use traversal",))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_morning_review_pack(request: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_morning_review_request(request)
    if not validation.valid:
        raise MorningReviewPackValidationError(validation.errors)

    queue_rows = [_build_queue_row(row) for row in request["queue_records"]]
    dashboard_rows = [_build_dashboard_row(row) for row in request["dashboard_records"]]
    safety_rows = [_build_safety_row(row) for row in request["safety_records"]]
    validation_rows = [_build_validation_row(row) for row in request["validation_records"]]
    local_references = _collect_local_references(queue_rows, dashboard_rows, safety_rows, validation_rows)

    pack = {
        "build_id": f"{request['pack_id']}-{_stable_digest(request)}",
        "contract_version": PACK_CONTRACT_VERSION,
        "created_at": CREATED_AT,
        "dashboard_review": dashboard_rows,
        "errors": [],
        "local_only": True,
        "operator_review": {
            "required": True,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": list(request["operator_review_steps"]),
        "pack_id": request["pack_id"],
        "queue_review": queue_rows,
        "required_validation_commands": list(REQUIRED_VALIDATION_COMMANDS),
        "review_date": request["review_date"],
        "run_label": request["run_label"],
        "run_mode": LOCAL_RUN_MODE,
        "safety_boundaries": deepcopy(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "safety_review": safety_rows,
        "summary_counts": {
            "dashboard_records": len(dashboard_rows),
            "local_references": len(local_references),
            "operator_review_pending_records": _count_pending(queue_rows, dashboard_rows, safety_rows, validation_rows),
            "queue_records": len(queue_rows),
            "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
            "safety_records": len(safety_rows),
            "validation_records": len(validation_rows),
            "warnings": 0,
        },
        "task_id": TASK_ID,
        "validation_review": validation_rows,
        "warnings": [],
    }

    artifact_validation = validate_morning_review_pack(pack)
    if not artifact_validation.valid:
        raise MorningReviewPackValidationError(artifact_validation.errors)
    return pack


def validate_morning_review_request(request: Mapping[str, Any]) -> MorningReviewPackValidationResult:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "pack_id",
        "run_label",
        "review_date",
        "scope",
        "local_only",
        "operator_review_required",
        "queue_records",
        "dashboard_records",
        "safety_records",
        "validation_records",
        "operator_review_steps",
    )
    errors.extend(_missing_fields(request, required_fields, "request"))

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "local_morning_review_pack":
        errors.append("scope must be local_morning_review_pack")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")

    for field_name in ("queue_records", "dashboard_records", "safety_records", "validation_records", "operator_review_steps"):
        if field_name in request and not isinstance(request[field_name], list):
            errors.append(f"{field_name} must be a list")

    if isinstance(request.get("queue_records"), list):
        errors.extend(_validate_rows("queue_records", request["queue_records"], _QUEUE_REQUIRED_FIELDS))
    if isinstance(request.get("dashboard_records"), list):
        errors.extend(_validate_rows("dashboard_records", request["dashboard_records"], _DASHBOARD_REQUIRED_FIELDS))
    if isinstance(request.get("safety_records"), list):
        errors.extend(_validate_rows("safety_records", request["safety_records"], _SAFETY_REQUIRED_FIELDS))
    if isinstance(request.get("validation_records"), list):
        errors.extend(_validate_rows("validation_records", request["validation_records"], _VALIDATION_REQUIRED_FIELDS))

    errors.extend(_duplicate_id_errors("queue_records", request.get("queue_records"), "task_id"))
    errors.extend(_duplicate_id_errors("dashboard_records", request.get("dashboard_records"), "artifact_id"))
    errors.extend(_duplicate_id_errors("safety_records", request.get("safety_records"), "boundary_id"))
    errors.extend(_duplicate_id_errors("validation_records", request.get("validation_records"), "validation_id"))
    errors.extend(_blocked_term_errors(request, "request"))
    return MorningReviewPackValidationResult(valid=not errors, errors=tuple(errors))


def validate_morning_review_pack(pack: Mapping[str, Any]) -> MorningReviewPackValidationResult:
    errors: list[str] = []
    required_fields = (
        "build_id",
        "contract_version",
        "created_at",
        "dashboard_review",
        "errors",
        "local_only",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "pack_id",
        "queue_review",
        "required_validation_commands",
        "review_date",
        "run_label",
        "run_mode",
        "safety_boundaries",
        "safety_review",
        "summary_counts",
        "task_id",
        "validation_review",
        "warnings",
    )
    errors.extend(_missing_fields(pack, required_fields, "pack"))

    if pack.get("contract_version") != PACK_CONTRACT_VERSION:
        errors.append(f"contract_version must be {PACK_CONTRACT_VERSION}")
    if pack.get("task_id") != TASK_ID:
        errors.append(f"task_id must be {TASK_ID}")
    if pack.get("created_at") != CREATED_AT:
        errors.append(f"created_at must be {CREATED_AT}")
    if pack.get("run_mode") != LOCAL_RUN_MODE:
        errors.append(f"run_mode must be {LOCAL_RUN_MODE}")
    if pack.get("local_only") is not True:
        errors.append("local_only must be true")
    if pack.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if pack.get("operator_review", {}).get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"operator_review.status must be {OPERATOR_REVIEW_STATUS}")
    if pack.get("required_validation_commands") != list(REQUIRED_VALIDATION_COMMANDS):
        errors.append("required_validation_commands must match the local validation command list")
    if pack.get("safety_boundaries") != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only morning review boundary")

    queue_rows = _list_or_error(pack.get("queue_review"), "queue_review", errors)
    dashboard_rows = _list_or_error(pack.get("dashboard_review"), "dashboard_review", errors)
    safety_rows = _list_or_error(pack.get("safety_review"), "safety_review", errors)
    validation_rows = _list_or_error(pack.get("validation_review"), "validation_review", errors)

    for collection_name, rows in (
        ("queue_review", queue_rows),
        ("dashboard_review", dashboard_rows),
        ("safety_review", safety_rows),
        ("validation_review", validation_rows),
    ):
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"{collection_name}[{index}] must be an object")
                continue
            if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
                errors.append(f"{collection_name}[{index}].operator_review_status must be {OPERATOR_REVIEW_STATUS}")
            if row.get("runner_state") != PACK_ROW_STATE:
                errors.append(f"{collection_name}[{index}].runner_state must be {PACK_ROW_STATE}")
            for field_name in ("local_reference", "source_fixture_reference"):
                if field_name in row:
                    errors.extend(_validate_local_reference(str(row[field_name]), f"{collection_name}[{index}].{field_name}"))

    summary_counts = pack.get("summary_counts")
    if isinstance(summary_counts, Mapping):
        local_references = _collect_local_references(queue_rows, dashboard_rows, safety_rows, validation_rows)
        expected_counts = {
            "dashboard_records": len(dashboard_rows),
            "local_references": len(local_references),
            "operator_review_pending_records": _count_pending(queue_rows, dashboard_rows, safety_rows, validation_rows),
            "queue_records": len(queue_rows),
            "required_validation_commands": len(REQUIRED_VALIDATION_COMMANDS),
            "safety_records": len(safety_rows),
            "validation_records": len(validation_rows),
            "warnings": len(pack.get("warnings", [])) if isinstance(pack.get("warnings"), list) else 0,
        }
        if dict(summary_counts) != expected_counts:
            errors.append("summary_counts must match morning review content")
    else:
        errors.append("summary_counts must be an object")

    errors.extend(_blocked_term_errors(pack, "pack"))
    return MorningReviewPackValidationResult(valid=not errors, errors=tuple(errors))


def find_blocked_output_terms(value: object) -> list[str]:
    return _blocked_term_errors(value, "$")


def render_operator_report(pack: Mapping[str, Any]) -> str:
    validation = validate_morning_review_pack(pack)
    if not validation.valid:
        raise MorningReviewPackValidationError(validation.errors)

    lines = [
        "# PMBOT Morning Review Pack",
        "",
        f"Task: `{pack['task_id']}`",
        f"Pack: `{pack['pack_id']}`",
        f"Build: `{pack['build_id']}`",
        f"Contract: `{pack['contract_version']}`",
        f"Run mode: `{pack['run_mode']}`",
        f"Operator review: `{pack['operator_review']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Queue records: {pack['summary_counts']['queue_records']}",
        f"- Dashboard records: {pack['summary_counts']['dashboard_records']}",
        f"- Safety records: {pack['summary_counts']['safety_records']}",
        f"- Validation records: {pack['summary_counts']['validation_records']}",
        f"- Pending operator review records: {pack['summary_counts']['operator_review_pending_records']}",
        f"- Local references: {pack['summary_counts']['local_references']}",
        f"- Warnings: {pack['summary_counts']['warnings']}",
        "",
        "## Queue Review",
        "",
    ]
    for row in pack["queue_review"]:
        lines.append(
            f"- `{row['task_id']}`: group `{row['queue_group']}`, template `{row['task_template']}`, "
            f"state `{row['record_state']}`, reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Dashboard Review", ""])
    for row in pack["dashboard_review"]:
        lines.append(
            f"- `{row['artifact_id']}`: type `{row['artifact_type']}`, records {row['record_count']}, "
            f"reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Safety Review", ""])
    for row in pack["safety_review"]:
        lines.append(
            f"- `{row['boundary_id']}`: state `{row['observed_state']}`, reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Validation Review", ""])
    for row in pack["validation_review"]:
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
    parser = argparse.ArgumentParser(description="Build a local PMBOT morning review pack.")
    parser.add_argument("--request", required=True, help="Path to a local morning review request JSON file.")
    parser.add_argument("--output-pack", required=True, help="Path for the output morning review pack JSON.")
    parser.add_argument("--output-report", required=True, help="Path for the output morning review pack Markdown.")
    args = parser.parse_args(argv)

    request = load_morning_review_request(args.request)
    pack = build_morning_review_pack(request)
    report = render_operator_report(pack)

    pack_path = Path(args.output_pack)
    report_path = Path(args.output_report)
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    pack_path.write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(report, encoding="utf-8")
    return 0


_QUEUE_REQUIRED_FIELDS = (
    "task_id",
    "task_title",
    "queue_group",
    "task_template",
    "local_reference",
    "operator_review_status",
    "validation_profile",
    "safety_class",
    "record_state",
)
_DASHBOARD_REQUIRED_FIELDS = (
    "artifact_id",
    "artifact_label",
    "artifact_type",
    "contract_version",
    "record_count",
    "source_fixture_reference",
    "local_reference",
    "operator_review_status",
    "record_state",
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


def _build_queue_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "operator_review_status": row["operator_review_status"],
        "queue_group": row["queue_group"],
        "record_id": f"queue.{row['task_id']}",
        "record_state": row["record_state"],
        "runner_state": PACK_ROW_STATE,
        "safety_class": row["safety_class"],
        "task_id": row["task_id"],
        "task_template": row["task_template"],
        "task_title": row["task_title"],
        "validation_profile": row["validation_profile"],
    }


def _build_dashboard_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": row["artifact_id"],
        "artifact_label": row["artifact_label"],
        "artifact_type": row["artifact_type"],
        "contract_version": row["contract_version"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "operator_review_status": row["operator_review_status"],
        "record_count": int(row["record_count"]),
        "record_id": f"dashboard.{row['artifact_id']}",
        "record_state": row["record_state"],
        "runner_state": PACK_ROW_STATE,
        "source_fixture_reference": _normalize_local_reference(row["source_fixture_reference"]),
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
        "runner_state": PACK_ROW_STATE,
    }


def _build_validation_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "command_label": row["command_label"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "operator_review_status": row["operator_review_status"],
        "record_id": f"validation.{row['validation_id']}",
        "runner_state": PACK_ROW_STATE,
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
        for field_name in ("local_reference", "source_fixture_reference"):
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
        errors.append(f"{field_path} is outside the local morning review boundary")
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
            for field_name in ("local_reference", "source_fixture_reference"):
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
