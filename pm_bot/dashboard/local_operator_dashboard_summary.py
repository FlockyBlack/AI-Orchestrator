from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REQUEST_CONTRACT_VERSION = "pmbot_local_operator_dashboard_request.v1"
DASHBOARD_CONTRACT_VERSION = "pmbot_local_operator_dashboard_summary.v1"
LOCAL_RUN_MODE = "local_static_dashboard_summary"
OPERATOR_REVIEW_STATUS = "pending_operator_review"
SUMMARY_ROW_STATE = "ready_for_operator_review"
SAMPLE_DASHBOARD_PATH = "pm_bot/dashboard/samples/local_operator_dashboard_summary.fixture.json"

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
    "browser_automation_allowed": False,
    "external_market_api_allowed": False,
    "llm_calls_allowed": False,
    "network_calls_allowed": False,
    "offline_inputs_only": True,
    "operator_review_gate_required": True,
    "outcome_resolution_allowed": False,
    "runtime_wiring_allowed": False,
    "scheduler_or_worker_allowed": False,
    "trade_instruction_output_allowed": False,
    "transaction_endpoint_allowed": False,
    "wallet_or_order_code_allowed": False,
}


@dataclass(frozen=True)
class DashboardValidationResult:
    valid: bool
    errors: tuple[str, ...]


class LocalOperatorDashboardValidationError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_dashboard_request(path: str | Path) -> dict[str, Any]:
    normalized = _normalize_local_reference(str(path))
    if _is_network_like(normalized):
        raise LocalOperatorDashboardValidationError(("request path must be local",))
    if _contains_path_traversal(normalized):
        raise LocalOperatorDashboardValidationError(("request path must not use traversal",))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_local_operator_dashboard_summary(request: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_dashboard_request(request)
    if not validation.valid:
        raise LocalOperatorDashboardValidationError(validation.errors)

    queue_records = [_build_queue_row(row) for row in request["queue_records"]]
    ledger_records = [_build_ledger_row(row) for row in request["ledger_records"]]
    validation_records = [_build_validation_row(row) for row in request["validation_records"]]
    pending_count = sum(
        1
        for row in (*queue_records, *ledger_records, *validation_records)
        if row["operator_review_status"] == OPERATOR_REVIEW_STATUS
    )

    dashboard = {
        "contract_version": DASHBOARD_CONTRACT_VERSION,
        "dashboard_id": request["dashboard_id"],
        "build_id": f"{request['dashboard_id']}-{_stable_digest(request)}",
        "run_mode": LOCAL_RUN_MODE,
        "local_only": True,
        "operator_review_required": True,
        "operator_review": {
            "required": True,
            "status": OPERATOR_REVIEW_STATUS,
        },
        "summary_counts": {
            "ledger_records": len(ledger_records),
            "operator_review_pending_records": pending_count,
            "queue_records": len(queue_records),
            "validation_records": len(validation_records),
            "warnings": 0,
        },
        "queue_summary": queue_records,
        "ledger_summary": ledger_records,
        "validation_status_summary": validation_records,
        "operator_review_steps": list(request["operator_review_steps"]),
        "safety_boundaries": deepcopy(LOCAL_ONLY_SAFETY_BOUNDARIES),
        "errors": [],
        "warnings": [],
    }

    artifact_validation = validate_local_operator_dashboard_summary(dashboard)
    if not artifact_validation.valid:
        raise LocalOperatorDashboardValidationError(artifact_validation.errors)
    return dashboard


def validate_dashboard_request(request: Mapping[str, Any]) -> DashboardValidationResult:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "dashboard_id",
        "scope",
        "local_only",
        "operator_review_required",
        "queue_records",
        "ledger_records",
        "validation_records",
        "operator_review_steps",
    )
    errors.extend(_missing_fields(request, required_fields, "request"))

    if request.get("contract_version") != REQUEST_CONTRACT_VERSION:
        errors.append(f"contract_version must be {REQUEST_CONTRACT_VERSION}")
    if request.get("scope") != "local_operator_dashboard_summary":
        errors.append("scope must be local_operator_dashboard_summary")
    if request.get("local_only") is not True:
        errors.append("local_only must be true")
    if request.get("operator_review_required") is not True:
        errors.append("operator_review_required must be true")

    for field_name in ("queue_records", "ledger_records", "validation_records", "operator_review_steps"):
        if field_name in request and not isinstance(request[field_name], list):
            errors.append(f"{field_name} must be a list")

    if isinstance(request.get("queue_records"), list):
        errors.extend(_validate_rows("queue_records", request["queue_records"], _QUEUE_REQUIRED_FIELDS))
    if isinstance(request.get("ledger_records"), list):
        errors.extend(_validate_rows("ledger_records", request["ledger_records"], _LEDGER_REQUIRED_FIELDS))
    if isinstance(request.get("validation_records"), list):
        errors.extend(_validate_rows("validation_records", request["validation_records"], _VALIDATION_REQUIRED_FIELDS))

    errors.extend(_duplicate_id_errors("queue_records", request.get("queue_records"), "task_id"))
    errors.extend(_duplicate_id_errors("ledger_records", request.get("ledger_records"), "ledger_id"))
    errors.extend(_duplicate_id_errors("validation_records", request.get("validation_records"), "validation_id"))

    errors.extend(_forbidden_term_errors(request, "request"))
    return DashboardValidationResult(valid=not errors, errors=tuple(errors))


def validate_local_operator_dashboard_summary(dashboard: Mapping[str, Any]) -> DashboardValidationResult:
    errors: list[str] = []
    required_fields = (
        "contract_version",
        "dashboard_id",
        "build_id",
        "run_mode",
        "local_only",
        "operator_review_required",
        "operator_review",
        "summary_counts",
        "queue_summary",
        "ledger_summary",
        "validation_status_summary",
        "safety_boundaries",
        "errors",
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
    if dashboard.get("safety_boundaries") != LOCAL_ONLY_SAFETY_BOUNDARIES:
        errors.append("safety_boundaries must match the local-only dashboard boundary")

    queue_summary = dashboard.get("queue_summary")
    ledger_summary = dashboard.get("ledger_summary")
    validation_summary = dashboard.get("validation_status_summary")
    if not isinstance(queue_summary, list):
        errors.append("queue_summary must be a list")
        queue_summary = []
    if not isinstance(ledger_summary, list):
        errors.append("ledger_summary must be a list")
        ledger_summary = []
    if not isinstance(validation_summary, list):
        errors.append("validation_status_summary must be a list")
        validation_summary = []

    for collection_name, rows in (
        ("queue_summary", queue_summary),
        ("ledger_summary", ledger_summary),
        ("validation_status_summary", validation_summary),
    ):
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"{collection_name}[{index}] must be an object")
                continue
            if row.get("operator_review_status") != OPERATOR_REVIEW_STATUS:
                errors.append(f"{collection_name}[{index}].operator_review_status must be {OPERATOR_REVIEW_STATUS}")
            if row.get("runner_state") != SUMMARY_ROW_STATE:
                errors.append(f"{collection_name}[{index}].runner_state must be {SUMMARY_ROW_STATE}")

    summary_counts = dashboard.get("summary_counts")
    if isinstance(summary_counts, Mapping):
        expected_counts = {
            "ledger_records": len(ledger_summary),
            "operator_review_pending_records": _count_pending(queue_summary, ledger_summary, validation_summary),
            "queue_records": len(queue_summary),
            "validation_records": len(validation_summary),
            "warnings": len(dashboard.get("warnings", [])) if isinstance(dashboard.get("warnings"), list) else 0,
        }
        if dict(summary_counts) != expected_counts:
            errors.append("summary_counts must match dashboard rows")
    else:
        errors.append("summary_counts must be an object")

    errors.extend(_forbidden_term_errors(dashboard, "dashboard"))
    return DashboardValidationResult(valid=not errors, errors=tuple(errors))


def build_operator_report(dashboard: Mapping[str, Any]) -> str:
    validation = validate_local_operator_dashboard_summary(dashboard)
    if not validation.valid:
        raise LocalOperatorDashboardValidationError(validation.errors)

    lines = [
        "# PMBOT Local Operator Dashboard Summary",
        "",
        f"Dashboard: `{dashboard['dashboard_id']}`",
        f"Build: `{dashboard['build_id']}`",
        f"Run mode: `{dashboard['run_mode']}`",
        f"Operator review: `{dashboard['operator_review']['status']}`",
        "",
        "## Summary Counts",
        "",
        f"- Queue records: {dashboard['summary_counts']['queue_records']}",
        f"- Ledger records: {dashboard['summary_counts']['ledger_records']}",
        f"- Validation records: {dashboard['summary_counts']['validation_records']}",
        f"- Pending operator review records: {dashboard['summary_counts']['operator_review_pending_records']}",
        f"- Warnings: {dashboard['summary_counts']['warnings']}",
        "",
        "## Queue Records",
        "",
    ]
    for row in dashboard["queue_summary"]:
        lines.append(
            f"- `{row['task_id']}`: bucket `{row['queue_bucket']}`, "
            f"template `{row['task_template']}`, review `{row['operator_review_status']}`, "
            f"reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Ledger Records", ""])
    for row in dashboard["ledger_summary"]:
        lines.append(
            f"- `{row['ledger_id']}`: type `{row['ledger_type']}`, records {row['record_count']}, "
            f"review `{row['operator_review_status']}`, reference `{row['local_reference']}`"
        )

    lines.extend(["", "## Validation Status Records", ""])
    for row in dashboard["validation_status_summary"]:
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
            "- Descriptive dashboard status only; no outcome resolution or trade instruction output.",
            "- Not execution approval and not runtime input.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local PMBOT operator dashboard summary.")
    parser.add_argument("--request", required=True, help="Path to a local dashboard request JSON file.")
    parser.add_argument("--output-dashboard", required=True, help="Path for the output dashboard summary JSON.")
    parser.add_argument("--output-report", required=True, help="Path for the output dashboard summary Markdown.")
    args = parser.parse_args(argv)

    request = load_dashboard_request(args.request)
    dashboard = build_local_operator_dashboard_summary(request)
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
    "queue_bucket",
    "task_template",
    "local_reference",
    "operator_review_status",
    "validation_profile",
    "safety_class",
)
_LEDGER_REQUIRED_FIELDS = (
    "ledger_id",
    "ledger_type",
    "contract_version",
    "record_count",
    "local_reference",
    "operator_review_status",
    "summary_label",
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
        "record_id": f"queue.{row['task_id']}",
        "task_id": row["task_id"],
        "task_title": row["task_title"],
        "queue_bucket": row["queue_bucket"],
        "task_template": row["task_template"],
        "validation_profile": row["validation_profile"],
        "safety_class": row["safety_class"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "operator_review_status": row["operator_review_status"],
        "runner_state": SUMMARY_ROW_STATE,
        "notes": row.get("notes", ""),
    }


def _build_ledger_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "record_id": f"ledger.{row['ledger_id']}",
        "ledger_id": row["ledger_id"],
        "ledger_type": row["ledger_type"],
        "contract_version": row["contract_version"],
        "record_count": int(row["record_count"]),
        "summary_label": row["summary_label"],
        "local_reference": _normalize_local_reference(row["local_reference"]),
        "operator_review_status": row["operator_review_status"],
        "runner_state": SUMMARY_ROW_STATE,
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
        "runner_state": SUMMARY_ROW_STATE,
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
        if "local_reference" in row:
            errors.extend(_validate_local_reference(str(row["local_reference"]), f"{collection_name}[{index}].local_reference"))
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
            if _has_forbidden_dashboard_term(str(key)):
                errors.append(f"forbidden dashboard decision field detected at {key_path}")
            errors.extend(_forbidden_term_errors(nested_value, key_path))
        return errors
    if isinstance(value, list):
        errors = []
        for index, nested_value in enumerate(value):
            errors.extend(_forbidden_term_errors(nested_value, f"{path}[{index}]"))
        return errors
    if isinstance(value, str) and _has_forbidden_dashboard_term(value):
        return [f"forbidden dashboard decision value detected at {path}"]
    return []


def _has_forbidden_dashboard_term(value: str) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & FORBIDDEN_DASHBOARD_TERMS)


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
