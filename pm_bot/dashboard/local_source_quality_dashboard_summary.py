from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REQUEST_CONTRACT_VERSION = "pmbot_local_source_quality_dashboard_request.v1"
DASHBOARD_CONTRACT_VERSION = "pmbot_local_source_quality_dashboard_summary.v1"
LOCAL_RUN_MODE = "local_static_source_quality_dashboard_summary"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
DASHBOARD_ROW_STATE = "ready_for_operator_review"
SAMPLE_DASHBOARD_PATH = "pm_bot/dashboard/samples/local_source_quality_dashboard_summary.fixture.json"
SAMPLE_OPERATOR_REPORT_PATH = "pm_bot/dashboard/samples/local_source_quality_dashboard_summary.fixture.md"

ALLOWED_LOCAL_REFERENCE_PREFIXES = (
    "docs/",
    "pm_bot/dashboard/",
    "pm_bot/source_quality/",
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
FORBIDDEN_DASHBOARD_TERMS = {
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
class SourceQualityDashboardValidationResult:
    valid: bool
    errors: tuple[str, ...]


class SourceQualityDashboardValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_dashboard_request(path: str | Path) -> dict[str, Any]:
    normalized = _normalize_local_reference(str(path))
    if _is_network_like(normalized):
        raise SourceQualityDashboardValidationError(("request path must be local",))
    if _contains_path_traversal(normalized):
        raise SourceQualityDashboardValidationError(("request path must not use traversal",))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_local_source_quality_dashboard_summary(request: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_dashboard_request(request)
    if not validation.valid:
        raise SourceQualityDashboardValidationError(validation.errors)

    queue_rows = [_build_queue_row(row) for row in request["queue_records"]]
    source_quality_rows = [_build_source_quality_row(row) for row in request["source_quality_records"]]
    validation_rows = [_build_validation_row(row) for row in request["validation_records"]]

    dashboard = {
        "build_id": f"{request['dashboard_id']}-{_stable_digest(request)}",
        "contract_version": DASHBOARD_CONTRACT_VERSION,
        "dashboard_id": request["dashboard_id"],
        "dashboard_label": request["dashboard_label"],
        "errors": [],
        "local_only": True,
        "operator_review": {
            "required": True,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "operator_review_required": True,
        "operator_review_steps": list(request["operator_review_steps"]),
        "queue_summary": queue_rows,
        "run_mode": LOCAL_RUN_MODE,
        "safety_boundaries": deepcopy(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "source_quality_summary": source_quality_rows,
        "summary_counts": _summary_counts(queue_rows, source_quality_rows, validation_rows, []),
        "validation_status_summary": validation_rows,
        "warnings": [],
    }

    artifact_validation = validate_local_source_quality_dashboard_summary(dashboard)
    if not artifact_validation.valid:
        raise SourceQualityDashboardValidationError(artifact_validation.errors)
    return dashboard


def validate_dashboard_request(request: Mapping[str, Any]) -> SourceQualityDashboardValidationResult:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "dashboard_id",
        "dashboard_label",
        "scope",
        "local_only",
        "operator_review_required",
        "queue_records",
        "source_quality_records",
        "validation_records",
        "operator_review_steps",
    )
    errors.extend(_missing_fields(request, required_fields, "request"))

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "local_source_quality_dashboard_summary":
        errors.append("scope must be local_source_quality_dashboard_summary")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if not _is_non_empty_string_list(request.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")

    for field_name in ("queue_records", "source_quality_records", "validation_records"):
        if field_name in request and not isinstance(request[field_name], list):
            errors.append(f"{field_name} must be a list")

    if isinstance(request.get("queue_records"), list):
        errors.extend(_validate_rows("queue_records", request["queue_records"], _QUEUE_REQUIRED_FIELDS))
    if isinstance(request.get("source_quality_records"), list):
        errors.extend(
            _validate_rows("source_quality_records", request["source_quality_records"], _SOURCE_QUALITY_REQUIRED_FIELDS)
        )
    if isinstance(request.get("validation_records"), list):
        errors.extend(_validate_rows("validation_records", request["validation_records"], _VALIDATION_REQUIRED_FIELDS))

    errors.extend(_duplicate_id_errors("queue_records", request.get("queue_records"), "task_id"))
    errors.extend(_duplicate_id_errors("source_quality_records", request.get("source_quality_records"), "artifact_id"))
    errors.extend(_duplicate_id_errors("validation_records", request.get("validation_records"), "validation_id"))
    errors.extend(_forbidden_term_errors(request, "request"))
    return SourceQualityDashboardValidationResult(valid=not errors, errors=tuple(errors))


def validate_local_source_quality_dashboard_summary(
    dashboard: Mapping[str, Any],
) -> SourceQualityDashboardValidationResult:
    errors: list[str] = []
    required_fields = (
        "build_id",
        "contract_version",
        "dashboard_id",
        "dashboard_label",
        "errors",
        "local_only",
        "operator_review",
        "operator_review_required",
        "operator_review_steps",
        "queue_summary",
        "run_mode",
        "safety_boundaries",
        "source_quality_summary",
        "summary_counts",
        "validation_status_summary",
        "warnings",
    )
    errors.extend(_missing_fields(dashboard, required_fields, "dashboard"))

    if dashboard.get("contract_version") != DASHBOARD_CONTRACT_VERSION:
        errors.append(f"contract_version must be {DASHBOARD_CONTRACT_VERSION}")
    if dashboard.get("run_mode") != LOCAL_RUN_MODE:
        errors.append(f"run_mode must be {LOCAL_RUN_MODE}")
    if dashboard.get("local_only") is not True:
        errors.append("local_only must be true")
    if dashboard.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")
    if dashboard.get("operator_review", {}).get("status") != OPERATOR_REVIEW_STATUS:
        errors.append(f"operator_review.status must be {OPERATOR_REVIEW_STATUS}")
    if not _is_non_empty_string_list(dashboard.get("operator_review_steps")):
        errors.append("operator_review_steps must be a non-empty list of strings")
    if dashboard.get("errors") != []:
        errors.append("errors must be an empty list")
    if not _is_string_list(dashboard.get("warnings")):
        errors.append("warnings must be a list of strings")
    if dashboard.get("safety_boundaries") != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only source quality dashboard boundary")

    queue_rows = dashboard.get("queue_summary")
    source_quality_rows = dashboard.get("source_quality_summary")
    validation_rows = dashboard.get("validation_status_summary")
    if not isinstance(queue_rows, list):
        errors.append("queue_summary must be a list")
        queue_rows = []
    if not isinstance(source_quality_rows, list):
        errors.append("source_quality_summary must be a list")
        source_quality_rows = []
    if not isinstance(validation_rows, list):
        errors.append("validation_status_summary must be a list")
        validation_rows = []

    _validate_output_rows("queue_summary", queue_rows, errors)
    _validate_output_rows("source_quality_summary", source_quality_rows, errors)
    _validate_output_rows("validation_status_summary", validation_rows, errors)

    summary_counts = dashboard.get("summary_counts")
    if isinstance(summary_counts, Mapping):
        expected_counts = _summary_counts(
            queue_rows,
            source_quality_rows,
            validation_rows,
            dashboard.get("warnings", []),
        )
        if dict(summary_counts) != expected_counts:
            errors.append("summary_counts must match source quality dashboard rows")
    else:
        errors.append("summary_counts must be an object")

    errors.extend(_forbidden_term_errors(dashboard, "dashboard"))
    return SourceQualityDashboardValidationResult(valid=not errors, errors=tuple(errors))


def build_operator_report(dashboard: Mapping[str, Any]) -> str:
    validation = validate_local_source_quality_dashboard_summary(dashboard)
    if not validation.valid:
        raise SourceQualityDashboardValidationError(validation.errors)

    lines = [
        "# PMBOT Source Quality Dashboard Summary",
        "",
        f"Dashboard: `{dashboard['dashboard_id']}`",
        f"Build: `{dashboard['build_id']}`",
        f"Label: `{dashboard['dashboard_label']}`",
        f"Run mode: `{dashboard['run_mode']}`",
        f"Operator review: `{dashboard['operator_review']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Queue records: {dashboard['summary_counts']['queue_records']}",
        f"- Source quality artifacts: {dashboard['summary_counts']['source_quality_artifacts']}",
        f"- Source artifacts: {dashboard['summary_counts']['source_artifacts']}",
        f"- Source quality rows: {dashboard['summary_counts']['source_quality_rows']}",
        f"- Declared fields: {dashboard['summary_counts']['fields_declared']}",
        f"- Present fields: {dashboard['summary_counts']['fields_present']}",
        f"- Missing fields: {dashboard['summary_counts']['fields_missing']}",
        f"- Review checks: {dashboard['summary_counts']['review_checks']}",
        f"- Known limitations: {dashboard['summary_counts']['known_limitations']}",
        f"- Review assertions: {dashboard['summary_counts']['review_assertions']}",
        f"- Validation records: {dashboard['summary_counts']['validation_records']}",
        f"- Pending operator review records: {dashboard['summary_counts']['operator_review_pending_records']}",
        f"- Warnings: {dashboard['summary_counts']['warnings']}",
        "",
        "## Queue Records",
        "",
    ]
    for row in dashboard["queue_summary"]:
        lines.append(
            f"- `{row['task_id']}`: group `{row['queue_group']}`, template `{row['task_template']}`, "
            f"state `{row['status_label']}`, review `{row['operator_review_status']}`, "
            f"reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Source Quality Artifacts", ""])
    for row in dashboard["source_quality_summary"]:
        lines.append(
            f"- `{row['artifact_id']}`: type `{row['artifact_type']}`, rows {row['source_quality_rows']}, "
            f"fields {row['fields_present']}/{row['fields_declared']}, review `{row['operator_review_status']}`, "
            f"sample `{row['source_fixture_reference']}`"
        )

    lines.extend(["", "## Validation Status Records", ""])
    for row in dashboard["validation_status_summary"]:
        lines.append(
            f"- `{row['validation_id']}`: status `{row['status']}`, "
            f"command `{row['command_label']}`, reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Operator Review Steps", ""])
    for step in dashboard["operator_review_steps"]:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Local fixture/static input only.",
            "- Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls.",
            "- Descriptive source quality dashboard only; no outcome resolution or trade instruction output.",
            "- Not execution approval and not runtime input.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT source quality dashboard summary.")
    parser.add_argument("--request", required=True, help="Path to a local source quality dashboard request JSON file.")
    parser.add_argument("--output-dashboard", required=True, help="Path for the output dashboard summary JSON.")
    parser.add_argument("--output-report", required=True, help="Path for the output dashboard summary Markdown.")
    args = parser.parse_args(argv)

    request = load_dashboard_request(args.request)
    dashboard = build_local_source_quality_dashboard_summary(request)
    report = build_operator_report(dashboard)

    dashboard_path = Path(args.output_dashboard)
    report_path = Path(args.output_report)
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(json.dumps(dashboard, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
_SOURCE_QUALITY_REQUIRED_FIELDS = (
    "artifact_id",
    "artifact_label",
    "artifact_type",
    "contract_version",
    "run_mode",
    "scope",
    "local_reference",
    "source_fixture_reference",
    "source_artifacts",
    "source_quality_rows",
    "fields_declared",
    "fields_present",
    "fields_missing",
    "review_checks",
    "known_limitations",
    "review_assertions",
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
_NON_NEGATIVE_INTEGER_FIELDS = (
    "fields_declared",
    "fields_missing",
    "fields_present",
    "known_limitations",
    "review_assertions",
    "review_checks",
    "source_artifacts",
    "source_quality_rows",
)


def _build_queue_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "operator_review_status": row["operator_review_status"],
        "queue_group": row["queue_group"],
        "record_id": f"queue_source_quality.{row['task_id']}",
        "runner_state": DASHBOARD_ROW_STATE,
        "safety_class": row["safety_class"],
        "status_label": row["status_label"],
        "task_id": row["task_id"],
        "task_template": row["task_template"],
        "task_title": row["task_title"],
        "validation_profile": row["validation_profile"],
    }


def _build_source_quality_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": row["artifact_id"],
        "artifact_label": row["artifact_label"],
        "artifact_type": row["artifact_type"],
        "contract_version": row["contract_version"],
        "fields_declared": int(row["fields_declared"]),
        "fields_missing": int(row["fields_missing"]),
        "fields_present": int(row["fields_present"]),
        "known_limitations": int(row["known_limitations"]),
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "operator_review_status": row["operator_review_status"],
        "record_id": f"source_quality_dashboard.{row['artifact_id']}",
        "review_assertions": int(row["review_assertions"]),
        "review_checks": int(row["review_checks"]),
        "run_mode": row["run_mode"],
        "runner_state": DASHBOARD_ROW_STATE,
        "scope": row["scope"],
        "source_artifacts": int(row["source_artifacts"]),
        "source_fixture_reference": _normalize_local_reference(row["source_fixture_reference"]),
        "source_quality_rows": int(row["source_quality_rows"]),
        "status_label": row["status_label"],
    }


def _build_validation_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "command_label": row["command_label"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "notes": row.get("notes", ""),
        "operator_review_status": row["operator_review_status"],
        "record_id": f"validation.{row['validation_id']}",
        "runner_state": DASHBOARD_ROW_STATE,
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
        for field_name in _NON_NEGATIVE_INTEGER_FIELDS:
            if field_name in row:
                errors.extend(_validate_non_negative_integer(row[field_name], f"{collection_name}[{index}].{field_name}"))
    return errors


def _validate_output_rows(collection_name: str, rows: Sequence[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"{collection_name}[{index}] must be an object")
            continue
        if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"{collection_name}[{index}].operator_review_status must be {OPERATOR_REVIEW_STATUS}")
        if row.get("runner_state") != DASHBOARD_ROW_STATE:
            errors.append(f"{collection_name}[{index}].runner_state must be {DASHBOARD_ROW_STATE}")
        for field_name in ("local_reference", "source_fixture_reference"):
            if field_name in row:
                errors.extend(_validate_local_reference(str(row[field_name]), f"{collection_name}[{index}].{field_name}"))
        for field_name in _NON_NEGATIVE_INTEGER_FIELDS:
            if field_name in row:
                errors.extend(_validate_non_negative_integer(row[field_name], f"{collection_name}[{index}].{field_name}"))
        if collection_name == "source_quality_summary":
            declared = _as_non_bool_int(row.get("fields_declared"))
            present = _as_non_bool_int(row.get("fields_present"))
            missing = _as_non_bool_int(row.get("fields_missing"))
            if declared is not None and present is not None and missing is not None and declared != present + missing:
                errors.append(f"{collection_name}[{index}].fields_declared must equal present plus missing fields")


def _summary_counts(
    queue_rows: Sequence[Any],
    source_quality_rows: Sequence[Any],
    validation_rows: Sequence[Any],
    warnings: object,
) -> dict[str, int]:
    source_quality_objects = [row for row in source_quality_rows if isinstance(row, Mapping)]
    return {
        "fields_declared": _sum_integer_field(source_quality_objects, "fields_declared"),
        "fields_missing": _sum_integer_field(source_quality_objects, "fields_missing"),
        "fields_present": _sum_integer_field(source_quality_objects, "fields_present"),
        "known_limitations": _sum_integer_field(source_quality_objects, "known_limitations"),
        "operator_review_pending_records": _count_pending(queue_rows, source_quality_rows, validation_rows),
        "queue_records": len(queue_rows),
        "review_assertions": _sum_integer_field(source_quality_objects, "review_assertions"),
        "review_checks": _sum_integer_field(source_quality_objects, "review_checks"),
        "source_artifacts": _sum_integer_field(source_quality_objects, "source_artifacts"),
        "source_quality_artifacts": len(source_quality_rows),
        "source_quality_rows": _sum_integer_field(source_quality_objects, "source_quality_rows"),
        "validation_records": len(validation_rows),
        "warnings": len(warnings) if isinstance(warnings, list) else 0,
    }


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
        errors.append(f"{field_path} is outside the source quality dashboard boundary")
    if not normalized.startswith(ALLOWED_LOCAL_REFERENCE_PREFIXES):
        errors.append(f"{field_path} must stay under allowed local source quality dashboard paths")
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


def _sum_integer_field(rows: Sequence[Mapping[str, Any]], field_name: str) -> int:
    return sum(value for row in rows if (value := _as_non_bool_int(row.get(field_name))) is not None)


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
            if _has_forbidden_dashboard_term(str(key)):
                errors.append(f"forbidden source quality dashboard decision field detected at {key_path}")
            errors.extend(_forbidden_term_errors(nested_value, key_path))
        return errors
    if isinstance(value, list):
        errors = []
        for index, nested_value in enumerate(value):
            errors.extend(_forbidden_term_errors(nested_value, f"{path}[{index}]"))
        return errors
    if isinstance(value, str) and _has_forbidden_dashboard_term(value):
        return [f"forbidden source quality dashboard decision value detected at {path}"]
    return []


def _has_forbidden_dashboard_term(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_DASHBOARD_TERMS)


def _count_pending(*collections: Sequence[Any]) -> int:
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
