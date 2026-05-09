from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REQUEST_CONTRACT_VERSION = "pmbot_local_queue_paperlive_status_request.v1"
STATUS_SURFACE_CONTRACT_VERSION = "pmbot_local_queue_paperlive_status_surface.v1"
LOCAL_RUN_MODE = "local_static_queue_paperlive_status_surface"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
SURFACE_ROW_STATE = "ready_for_operator_review"
SAMPLE_STATUS_SURFACE_PATH = "pm_bot/dashboard/samples/local_queue_paperlive_status_surface.fixture.json"

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
FORBIDDEN_STATUS_TERMS = {
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
    "external_market_api_calls_allowed": False,
    "llm_calls_allowed": False,
    "local_fixture_inputs_only": True,
    "network_calls_allowed": False,
    "operator_review_gate_required": True,
    "outcome_resolution_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "trade_instruction_output_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_order_code_allowed": False,
}


@dataclass(frozen=True)
class StatusSurfaceValidationResult:
    valid: bool
    errors: tuple[str, ...]


class QueuePaperliveStatusSurfaceValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_status_request(path: str | Path) -> dict[str, Any]:
    normalized = _normalize_local_reference(str(path))
    if _is_network_like(normalized):
        raise QueuePaperliveStatusSurfaceValidationError(("request path must be local",))
    if _contains_path_traversal(normalized):
        raise QueuePaperliveStatusSurfaceValidationError(("request path must not use traversal",))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_local_queue_paperlive_status_surface(request: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_status_request(request)
    if not validation.valid:
        raise QueuePaperliveStatusSurfaceValidationError(validation.errors)

    queue_rows = [_build_queue_row(row) for row in request["queue_status_records"]]
    paperlive_rows = [_build_paperlive_row(row) for row in request["paperlive_status_records"]]
    validation_rows = [_build_validation_row(row) for row in request["validation_records"]]
    pending_count = _count_pending(queue_rows, paperlive_rows, validation_rows)

    surface = {
        "contract_version": STATUS_SURFACE_CONTRACT_VERSION,
        "surface_id": f"{request['surface_id']}-{_stable_digest(request)}",
        "surface_label": request["surface_label"],
        "run_mode": LOCAL_RUN_MODE,
        "local_only": True,
        "operator_review_required": True,
        "operator_review": {
            "required": True,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "summary_counts": {
            "operator_review_pending_records": pending_count,
            "paperlive_status_records": len(paperlive_rows),
            "queue_status_records": len(queue_rows),
            "validation_records": len(validation_rows),
            "warnings": 0,
        },
        "queue_status_summary": queue_rows,
        "paperlive_status_summary": paperlive_rows,
        "validation_status_summary": validation_rows,
        "operator_review_steps": list(request["operator_review_steps"]),
        "safety_boundaries": deepcopy(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "errors": [],
        "warnings": [],
    }

    artifact_validation = validate_local_queue_paperlive_status_surface(surface)
    if not artifact_validation.valid:
        raise QueuePaperliveStatusSurfaceValidationError(artifact_validation.errors)
    return surface


def validate_status_request(request: Mapping[str, Any]) -> StatusSurfaceValidationResult:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "surface_id",
        "surface_label",
        "scope",
        "local_only",
        "operator_review_required",
        "queue_status_records",
        "paperlive_status_records",
        "validation_records",
        "operator_review_steps",
    )
    errors.extend(_missing_fields(request, required_fields, "request"))

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "local_queue_paperlive_status_surface":
        errors.append("scope must be local_queue_paperlive_status_surface")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")

    for field_name in (
        "queue_status_records",
        "paperlive_status_records",
        "validation_records",
        "operator_review_steps",
    ):
        if field_name in request and not isinstance(request[field_name], list):
            errors.append(f"{field_name} must be a list")

    if isinstance(request.get("queue_status_records"), list):
        errors.extend(_validate_rows("queue_status_records", request["queue_status_records"], _QUEUE_REQUIRED_FIELDS))
    if isinstance(request.get("paperlive_status_records"), list):
        errors.extend(
            _validate_rows("paperlive_status_records", request["paperlive_status_records"], _PAPERLIVE_REQUIRED_FIELDS)
        )
    if isinstance(request.get("validation_records"), list):
        errors.extend(_validate_rows("validation_records", request["validation_records"], _VALIDATION_REQUIRED_FIELDS))

    errors.extend(_duplicate_id_errors("queue_status_records", request.get("queue_status_records"), "task_id"))
    errors.extend(_duplicate_id_errors("paperlive_status_records", request.get("paperlive_status_records"), "artifact_id"))
    errors.extend(_duplicate_id_errors("validation_records", request.get("validation_records"), "validation_id"))
    errors.extend(_forbidden_term_errors(request, "request"))
    return StatusSurfaceValidationResult(valid=not errors, errors=tuple(errors))


def validate_local_queue_paperlive_status_surface(surface: Mapping[str, Any]) -> StatusSurfaceValidationResult:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "surface_id",
        "surface_label",
        "run_mode",
        "local_only",
        "operator_review_required",
        "operator_review",
        "summary_counts",
        "queue_status_summary",
        "paperlive_status_summary",
        "validation_status_summary",
        "operator_review_steps",
        "safety_boundaries",
        "errors",
        "warnings",
    )
    errors.extend(_missing_fields(surface, required_fields, "surface"))

    if surface.get("contract_version") != STATUS_SURFACE_CONTRACT_VERSION:
        errors.append(f"contract_version must be {STATUS_SURFACE_CONTRACT_VERSION}")
    if surface.get("run_mode") != LOCAL_RUN_MODE:
        errors.append(f"run_mode must be {LOCAL_RUN_MODE}")
    if surface.get("local_only") is not True:
        errors.append("local_only must be true")
    if surface.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if surface.get("operator_review", {}).get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"operator_review.status must be {OPERATOR_REVIEW_STATUS}")
    if surface.get("safety_boundaries") != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only status boundary")

    queue_rows = surface.get("queue_status_summary")
    paperlive_rows = surface.get("paperlive_status_summary")
    validation_rows = surface.get("validation_status_summary")
    if not isinstance(queue_rows, list):
        errors.append("queue_status_summary must be a list")
        queue_rows = []
    if not isinstance(paperlive_rows, list):
        errors.append("paperlive_status_summary must be a list")
        paperlive_rows = []
    if not isinstance(validation_rows, list):
        errors.append("validation_status_summary must be a list")
        validation_rows = []

    for collection_name, rows in (
        ("queue_status_summary", queue_rows),
        ("paperlive_status_summary", paperlive_rows),
        ("validation_status_summary", validation_rows),
    ):
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"{collection_name}[{index}] must be an object")
                continue
            if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
                errors.append(f"{collection_name}[{index}].operator_review_status must be {OPERATOR_REVIEW_STATUS}")
            if row.get("runner_state") != SURFACE_ROW_STATE:
                errors.append(f"{collection_name}[{index}].runner_state must be {SURFACE_ROW_STATE}")
            for field_name in ("local_reference", "source_fixture_reference"):
                if field_name in row:
                    errors.extend(_validate_local_reference(str(row[field_name]), f"{collection_name}[{index}].{field_name}"))

    summary_counts = surface.get("summary_counts")
    if isinstance(summary_counts, Mapping):
        expected_counts = {
            "operator_review_pending_records": _count_pending(queue_rows, paperlive_rows, validation_rows),
            "paperlive_status_records": len(paperlive_rows),
            "queue_status_records": len(queue_rows),
            "validation_records": len(validation_rows),
            "warnings": len(surface.get("warnings", [])) if isinstance(surface.get("warnings"), list) else 0,
        }
        if dict(summary_counts) != expected_counts:
            errors.append("summary_counts must match status rows")
    else:
        errors.append("summary_counts must be an object")

    errors.extend(_forbidden_term_errors(surface, "surface"))
    return StatusSurfaceValidationResult(valid=not errors, errors=tuple(errors))


def build_operator_report(surface: Mapping[str, Any]) -> str:
    validation = validate_local_queue_paperlive_status_surface(surface)
    if not validation.valid:
        raise QueuePaperliveStatusSurfaceValidationError(validation.errors)

    lines = [
        "# PMBOT Queue And Paperlive Status Surface",
        "",
        f"Surface: `{surface['surface_id']}`",
        f"Label: `{surface['surface_label']}`",
        f"Run mode: `{surface['run_mode']}`",
        f"Operator review: `{surface['operator_review']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Queue status records: {surface['summary_counts']['queue_status_records']}",
        f"- Paperlive status records: {surface['summary_counts']['paperlive_status_records']}",
        f"- Validation records: {surface['summary_counts']['validation_records']}",
        f"- Pending operator review records: {surface['summary_counts']['operator_review_pending_records']}",
        f"- Warnings: {surface['summary_counts']['warnings']}",
        "",
        "## Queue Status Records",
        "",
    ]
    for row in surface["queue_status_summary"]:
        lines.append(
            f"- `{row['task_id']}`: group `{row['queue_group']}`, template `{row['task_template']}`, "
            f"state `{row['status_label']}`, review `{row['operator_review_status']}`, "
            f"reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Paperlive Status Records", ""])
    for row in surface["paperlive_status_summary"]:
        lines.append(
            f"- `{row['artifact_id']}`: area `{row['paperlive_area']}`, records {row['record_count']}, "
            f"state `{row['status_label']}`, review `{row['operator_review_status']}`, "
            f"reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Validation Status Records", ""])
    for row in surface["validation_status_summary"]:
        lines.append(
            f"- `{row['validation_id']}`: status `{row['status']}`, "
            f"command `{row['command_label']}`, reference `{row['local_reference']}`"
        )

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.",
            "- Descriptive status inventory only; no outcome resolution or trade instruction output.",
            "- Not execution approval and not runtime input.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT queue and paperlive status surface.")
    parser.add_argument("--request", required=True, help="Path to a local status request JSON file.")
    parser.add_argument("--output-surface", required=True, help="Path for the output status surface JSON.")
    parser.add_argument("--output-report", required=True, help="Path for the output status surface Markdown.")
    args = parser.parse_args(argv)

    request = load_status_request(args.request)
    surface = build_local_queue_paperlive_status_surface(request)
    report = build_operator_report(surface)

    surface_path = Path(args.output_surface)
    report_path = Path(args.output_report)
    surface_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    surface_path.write_text(json.dumps(surface, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    "status_label",
)
_PAPERLIVE_REQUIRED_FIELDS = (
    "artifact_id",
    "task_id",
    "paperlive_area",
    "contract_version",
    "run_mode",
    "record_state",
    "record_count",
    "source_fixture_reference",
    "local_reference",
    "operator_review_status",
    "status_label",
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
        "record_id": f"queue_status.{row['task_id']}",
        "task_id": row["task_id"],
        "task_title": row["task_title"],
        "queue_group": row["queue_group"],
        "task_template": row["task_template"],
        "validation_profile": row["validation_profile"],
        "safety_class": row["safety_class"],
        "status_label": row["status_label"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "operator_review_status": row["operator_review_status"],
        "runner_state": SURFACE_ROW_STATE,
        "notes": row.get("notes", ""),
    }


def _build_paperlive_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "record_id": f"paperlive_status.{row['artifact_id']}",
        "artifact_id": row["artifact_id"],
        "task_id": row["task_id"],
        "paperlive_area": row["paperlive_area"],
        "contract_version": row["contract_version"],
        "run_mode": row["run_mode"],
        "record_state": row["record_state"],
        "record_count": int(row["record_count"]),
        "source_fixture_reference": _normalize_local_reference(row["source_fixture_reference"]),
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "operator_review_status": row["operator_review_status"],
        "runner_state": SURFACE_ROW_STATE,
        "status_label": row["status_label"],
        "notes": row.get("notes", ""),
    }


def _build_validation_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "record_id": f"validation.{row['validation_id']}",
        "validation_id": row["validation_id"],
        "command_label": row["command_label"],
        "status": row["status"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "operator_review_status": row["operator_review_status"],
        "runner_state": SURFACE_ROW_STATE,
        "notes": row.get("notes", ""),
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
        errors.append(f"{field_path} must be a local reference")
    if Path(normalized).is_absolute():
        errors.append(f"{field_path} must be repository-relative")
    if _contains_path_traversal(normalized):
        errors.append(f"{field_path} must not use traversal")
    if _is_forbidden_reference(normalized):
        errors.append(f"{field_path} is outside the dashboard boundary")
    if not normalized.startswith(ALLOWED_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{field_path} must stay under allowed local dashboard paths")
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


def _forbidden_term_errors(value: object, path: str) -> list[str]:
    if isinstance(value, Mapping):
        errors: list[str] = []
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_forbidden_status_term(str(key)):
                errors.append(f"forbidden status decision field detected at {key_path}")
            errors.extend(_forbidden_term_errors(nested_value, key_path))
        return errors
    if isinstance(value, list):
        errors = []
        for index, nested_value in enumerate(value):
            errors.extend(_forbidden_term_errors(nested_value, f"{path}[{index}]"))
        return errors
    if isinstance(value, str) and _has_forbidden_status_term(value):
        return [f"forbidden status decision value detected at {path}"]
    return []


def _has_forbidden_status_term(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_STATUS_TERMS)


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
