from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .files import (
    ensure_queue_directories,
    read_json,
    safe_existing_path_under_queue,
    safe_queue_path,
    validate_task_id,
    write_json_atomic,
    write_text_atomic,
)
from .result_ingestor import ingest_result
from .result_schema import SCHEMA_VERSION as RESULT_SCHEMA_VERSION
from .result_schema import STATUS_VALUES, default_result
from .result_validator import validate_result

POSTPROCESS_REPORT_SCHEMA_VERSION = "codex_cli_batch_postprocess_report.v1"

IngestResultFunc = Callable[[str | Path, str | Path], dict[str, Any]]
ReviewResultFunc = Callable[[str | Path, str], dict[str, Any]]


def postprocess_codex_batch(
    queue_root: str | Path = "agent_tasks",
    *,
    batch_report_path: str | Path,
    bridge_results: bool = False,
    review_results: bool = False,
    overwrite_results: bool = False,
    ingest_result_func: IngestResultFunc = ingest_result,
    review_result_func: ReviewResultFunc | None = None,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    run_id = _run_id()
    report = _base_report(
        root=root,
        run_id=run_id,
        batch_report_path=batch_report_path,
        bridge_results=bridge_results,
        review_results=review_results,
        overwrite_results=overwrite_results,
    )

    if review_results and not bridge_results:
        report["warnings"].append("--review-results implies --bridge-results for post-batch processing")
        bridge_results = True
        report["bridge_results"] = True

    if not bridge_results:
        report["errors"].append("postprocess-codex-batch requires --bridge-results")
        report["next_operator_action"] = "Rerun with --bridge-results after inspecting the batch report."
        return _write_postprocess_report(root, report)

    batch_report, batch_path = _load_batch_report(root, batch_report_path, report)
    if batch_report is None or batch_path is None:
        report["next_operator_action"] = "Provide a readable batch report under the queue reports directory."
        return _write_postprocess_report(root, report)

    report["batch_report_path"] = str(batch_path)
    report["batch_run_id"] = batch_report.get("run_id")
    report["batch_execution_status"] = batch_report.get("execution_status")
    report["batch_status"] = batch_report.get("status")

    task_executions = batch_report.get("task_executions", [])
    if not isinstance(task_executions, list):
        report["errors"].append("batch report task_executions must be a list")
        report["next_operator_action"] = "Inspect the batch report schema before postprocessing."
        return _write_postprocess_report(root, report)

    for execution in task_executions:
        if not isinstance(execution, Mapping):
            report["warnings"].append("skipped non-object task execution entry")
            continue
        entry = _postprocess_execution(
            root,
            batch_report,
            execution,
            review_results=review_results,
            overwrite_results=overwrite_results,
            ingest_result_func=ingest_result_func,
            review_result_func=review_result_func,
        )
        report["task_results"].append(entry)

    _finalize_counts(report)
    report["status"] = "blocked" if report["blocked_count"] or report["errors"] else "ok"
    report["next_operator_action"] = (
        "Inspect the post-batch summary, task review reports, and git diff; run mark-done only for tasks "
        "whose review report recommends ready_for_operator_done."
        if report["status"] == "ok"
        else "Inspect blocked postprocess entries; fix missing or invalid result artifacts before review."
    )
    return _write_postprocess_report(root, report)


def render_postprocess_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Codex CLI Batch Postprocess",
        "",
        f"- status: `{report['status']}`",
        f"- run_id: `{report['run_id']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- batch_report: `{report.get('batch_report_path')}`",
        f"- batch_run_id: `{report.get('batch_run_id')}`",
        f"- bridge_results: `{report['bridge_results']}`",
        f"- review_results: `{report['review_results']}`",
        f"- overwrite_results: `{report['overwrite_results']}`",
        f"- completed_execution_count: `{report['completed_execution_count']}`",
        f"- bridged_count: `{report['bridged_count']}`",
        f"- ingested_count: `{report['ingested_count']}`",
        f"- reviewed_count: `{report['reviewed_count']}`",
        f"- blocked_count: `{report['blocked_count']}`",
        "",
        "## Task Results",
        "",
    ]
    task_results = list(report.get("task_results", []))
    if not task_results:
        lines.append("- No task executions were postprocessed.")
    for entry in task_results:
        lines.append(
            f"- `{entry.get('task_id')}`: `{entry.get('postprocess_status')}`"
            f", bridged `{entry.get('bridged')}`"
            f", ingested `{entry.get('ingested')}`"
            f", reviewed `{entry.get('reviewed')}`"
        )
        if entry.get("result_path"):
            lines.append(f"  - result: `{entry['result_path']}`")
        if entry.get("execution_report_json"):
            lines.append(f"  - execution_report: `{entry['execution_report_json']}`")
        if entry.get("last_message_path"):
            lines.append(f"  - last_message: `{entry['last_message_path']}`")
        if entry.get("errors"):
            for error in entry["errors"]:
                lines.append(f"  - error: {error}")
    if report.get("errors"):
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This command is a bounded, operator-invoked postprocess step. It reads an existing batch report "
            "and per-task execution artifacts, writes queue result JSON only when --bridge-results is set, "
            "and runs ingestion/review only when --review-results is set.",
            "",
            "It does not execute Codex, create tasks, approve tasks, mark tasks done, commit, push, create a "
            "scheduler, start a daemon, start a background worker, or run an infinite loop.",
            "",
            f"Next operator action: {report['next_operator_action']}",
            "",
        ]
    )
    return "\n".join(lines)


def _postprocess_execution(
    root: Path,
    batch_report: Mapping[str, Any],
    execution: Mapping[str, Any],
    *,
    review_results: bool,
    overwrite_results: bool,
    ingest_result_func: IngestResultFunc,
    review_result_func: ReviewResultFunc | None,
) -> dict[str, Any]:
    entry = _entry_from_execution(execution)
    task_id = entry["task_id"]
    try:
        safe_task_id = validate_task_id(task_id)
    except ValueError as exc:
        return _block_entry(entry, f"invalid task_id {task_id!r}: {exc}")
    entry["task_id"] = safe_task_id

    if not _is_completed_execution(execution):
        return _skip_entry(entry, "task execution did not complete successfully")
    entry["completed_execution"] = True

    execution_report = _load_execution_report(root, execution, entry)
    if entry["errors"]:
        return _block_entry(entry)

    last_message_path = _locate_last_message(root, execution, execution_report, entry)
    if last_message_path is None:
        return _block_entry(entry)
    entry["last_message_path"] = str(last_message_path)

    try:
        source_payload = _extract_result_payload(last_message_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return _block_entry(entry, f"could not extract result JSON from last_message.md: {exc}")

    result_payload, bridge_warnings, bridge_errors = _queue_result_from_source(
        source_payload,
        task_id=safe_task_id,
        batch_report=batch_report,
        execution_report=execution_report,
        last_message_path=last_message_path,
    )
    entry["warnings"].extend(bridge_warnings)
    if bridge_errors:
        return _block_entry(entry, *bridge_errors)

    validation = validate_result(result_payload)
    entry["result_validation"] = validation.to_dict()
    if not validation.valid:
        return _block_entry(entry, *validation.errors)

    result_path = safe_queue_path(root, "review", f"{safe_task_id}.result.json")
    if result_path.exists() and not overwrite_results:
        return _block_entry(entry, f"result packet already exists: {result_path}")

    write_json_atomic(result_path, result_payload, overwrite=overwrite_results)
    entry["result_path"] = str(result_path)
    entry["bridged"] = True

    if review_results:
        ingestion_report = ingest_result_func(root, result_path)
        entry["ingestion_status"] = ingestion_report.get("ingestion_status")
        entry["ingestion_report_paths"] = ingestion_report.get("report_paths", {})
        entry["ingested"] = bool(ingestion_report.get("accepted"))
        if not entry["ingested"]:
            entry["errors"].extend(str(error) for error in ingestion_report.get("errors", []))
            return _block_entry(entry)

        review_func = review_result_func or _default_review_result_func
        review_report = review_func(root, safe_task_id)
        entry["review_report_paths"] = review_report.get("report_paths", {})
        entry["review_recommendation"] = review_report.get("recommendation")
        entry["reviewed"] = True

    entry["postprocess_status"] = "ok"
    return entry


def _queue_result_from_source(
    source: Mapping[str, Any],
    *,
    task_id: str,
    batch_report: Mapping[str, Any],
    execution_report: Mapping[str, Any],
    last_message_path: Path,
) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    if source.get("schema_version") == RESULT_SCHEMA_VERSION:
        result = dict(source)
        if result.get("task_id") != task_id:
            errors.append(f"result task_id does not match execution task_id: {result.get('task_id')}")
        return result, warnings, errors

    result = default_result()
    source_task_id = source.get("task_id")
    if isinstance(source_task_id, str) and source_task_id:
        if source_task_id != task_id:
            errors.append(f"last_message task_id does not match execution task_id: {source_task_id}")
        result["task_id"] = source_task_id
    else:
        result["task_id"] = task_id

    status = source.get("status")
    if status in STATUS_VALUES:
        result["status"] = status
    else:
        errors.append(f"last_message status must be one of {', '.join(STATUS_VALUES)}")

    summary = source.get("summary")
    if isinstance(summary, str) and summary.strip():
        result["summary"] = summary
    else:
        errors.append("last_message summary must be a non-empty string")

    completed_by = source.get("completed_by")
    result["completed_by"] = (
        completed_by.strip() if isinstance(completed_by, str) and completed_by.strip() else "codex_cli_last_message_bridge"
    )
    result["completed_at"] = _completed_at(source, execution_report, batch_report)

    result["files_created"] = _optional_string_list(source, "files_created", errors)
    result["files_deleted"] = _optional_string_list(source, "files_deleted", errors)
    files_modified = _optional_string_list(source, "files_modified", errors)
    if not files_modified and "files_changed" in source:
        files_modified = _optional_string_list(source, "files_changed", errors)
        if files_modified:
            warnings.append("last_message used files_changed; bridged those paths as files_modified")
    result["files_modified"] = files_modified

    commands_run = _optional_string_list(source, "commands_run", errors)
    if not commands_run and "validation_commands_run" in source:
        commands_run = _optional_string_list(source, "validation_commands_run", errors)
    result["commands_run"] = commands_run

    validation_results = _optional_string_list(source, "validation_results", errors)
    if not validation_results and "validation_commands_run" in source:
        validation_results = _optional_string_list(source, "validation_commands_run", errors)
    result["validation_results"] = validation_results

    acceptance_checks_passed = source.get("acceptance_checks_passed")
    if isinstance(acceptance_checks_passed, bool):
        result["acceptance_checks_passed"] = acceptance_checks_passed
    elif isinstance(source.get("tests_passed"), bool):
        result["acceptance_checks_passed"] = bool(source["tests_passed"])
    else:
        result["acceptance_checks_passed"] = False
        warnings.append("last_message did not include acceptance_checks_passed or tests_passed; bridged as false")

    result["safety_confirmation"] = _safety_confirmation(source, execution_report)
    result["operator_review_notes"] = _operator_review_notes(source, last_message_path, warnings)
    result["next_recommended_action"] = _next_recommended_action(source)
    return result, warnings, errors


def _safety_confirmation(source: Mapping[str, Any], execution_report: Mapping[str, Any]) -> dict[str, Any]:
    structured = source.get("safety_confirmation")
    if isinstance(structured, Mapping):
        return dict(structured)

    return {
        "network_calls_performed": _int_fact(source, execution_report, "network_calls_performed"),
        "credentials_accessed": _bool_fact(source, execution_report, "credentials_accessed"),
        "wallet_or_trading_touched": _bool_fact(
            source,
            execution_report,
            "wallet_or_trading_touched",
            "wallet_or_private_key_access",
            "orders_or_trading_actions",
        ),
        "runtime_or_dispatcher_touched": _bool_fact(
            source,
            execution_report,
            "runtime_or_dispatcher_touched",
            "runtime_or_dispatcher_changes",
        ),
        "background_worker_added": _bool_fact(
            source,
            execution_report,
            "background_worker_added",
            "background_worker_created",
        ),
        "scheduler_added": _bool_fact(source, execution_report, "scheduler_added", "scheduler_created"),
        "telegram_or_openclaw_added": _bool_fact(source, execution_report, "telegram_or_openclaw_added"),
        "openrouter_calls_performed": _int_fact(source, execution_report, "openrouter_calls_performed"),
        "polymarket_api_calls_performed": _int_fact(source, execution_report, "polymarket_api_calls_performed"),
        "codex_app_server_used": _bool_fact(source, execution_report, "codex_app_server_used"),
        "destructive_commands_used": _bool_fact(source, execution_report, "destructive_commands_used"),
    }


def _load_batch_report(
    root: Path,
    batch_report_path: str | Path,
    report: dict[str, Any],
) -> tuple[dict[str, Any] | None, Path | None]:
    try:
        path = safe_existing_path_under_queue(root, batch_report_path)
    except ValueError as exc:
        report["errors"].append(str(exc))
        return None, None
    if not path.exists():
        report["errors"].append(f"batch report not found: {path}")
        return None, path
    try:
        payload = read_json(path)
    except json.JSONDecodeError as exc:
        report["errors"].append(f"invalid batch report JSON: {exc}")
        return None, path
    if not isinstance(payload, Mapping):
        report["errors"].append("batch report must be a JSON object")
        return None, path
    return dict(payload), path


def _load_execution_report(
    root: Path,
    execution: Mapping[str, Any],
    entry: dict[str, Any],
) -> dict[str, Any]:
    raw_path = execution.get("execution_report_json")
    if not isinstance(raw_path, str) or not raw_path.strip():
        entry["warnings"].append("completed execution is missing execution_report_json; using last_message path if present")
        return {}
    try:
        path = safe_existing_path_under_queue(root, raw_path)
    except ValueError as exc:
        entry["errors"].append(str(exc))
        return {}
    entry["execution_report_json"] = str(path)
    if not path.exists():
        entry["errors"].append(f"execution report not found: {path}")
        return {}
    try:
        payload = read_json(path)
    except json.JSONDecodeError as exc:
        entry["errors"].append(f"invalid execution report JSON: {exc}")
        return {}
    if not isinstance(payload, Mapping):
        entry["errors"].append(f"execution report must be a JSON object: {path}")
        return {}
    return dict(payload)


def _locate_last_message(
    root: Path,
    execution: Mapping[str, Any],
    execution_report: Mapping[str, Any],
    entry: dict[str, Any],
) -> Path | None:
    candidates: list[Any] = [
        _mapping_value(execution_report.get("report_paths"), "last_message"),
        _mapping_value(execution_report.get("paths"), "last_message"),
        execution.get("last_message"),
        execution.get("last_message_path"),
    ]
    execution_report_path = entry.get("execution_report_json")
    if execution_report_path:
        candidates.append(Path(str(execution_report_path)).with_name("last_message.md"))

    for candidate in candidates:
        if not isinstance(candidate, (str, Path)) or not str(candidate).strip():
            continue
        try:
            path = safe_existing_path_under_queue(root, candidate)
        except ValueError as exc:
            entry["warnings"].append(str(exc))
            continue
        if path.exists():
            return path

    entry["errors"].append("last_message.md was not found for completed execution")
    return None


def _extract_result_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    candidates = [stripped]
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            candidates.append("\n".join(lines[1:-1]).strip())

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            return dict(payload)

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            return dict(payload)
    raise ValueError("no JSON object found")


def _entry_from_execution(execution: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_id": str(execution.get("task_id") or ""),
        "completed_execution": False,
        "postprocess_status": "blocked",
        "bridged": False,
        "ingested": False,
        "reviewed": False,
        "result_path": None,
        "execution_report_json": execution.get("execution_report_json"),
        "last_message_path": None,
        "result_validation": None,
        "ingestion_status": None,
        "ingestion_report_paths": {},
        "review_report_paths": {},
        "review_recommendation": None,
        "errors": [],
        "warnings": [],
    }


def _is_completed_execution(execution: Mapping[str, Any]) -> bool:
    return (
        execution.get("status") == "ok"
        and execution.get("execution_status") == "completed"
        and execution.get("exit_code") == 0
    )


def _skip_entry(entry: dict[str, Any], reason: str) -> dict[str, Any]:
    entry["postprocess_status"] = "skipped"
    entry["warnings"].append(reason)
    return entry


def _block_entry(entry: dict[str, Any], *errors: str) -> dict[str, Any]:
    entry["postprocess_status"] = "blocked"
    entry["errors"].extend(error for error in errors if error)
    return entry


def _optional_string_list(source: Mapping[str, Any], field: str, errors: list[str]) -> list[str]:
    value = source.get(field)
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"last_message {field} must be a list when present")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"last_message {field}[{index}] must be a non-empty string")
            continue
        result.append(item)
    return result


def _operator_review_notes(source: Mapping[str, Any], last_message_path: Path, warnings: list[str]) -> str:
    existing = source.get("operator_review_notes")
    if isinstance(existing, str) and existing.strip():
        return existing

    notes = [f"Bridged from {last_message_path}."]
    safety_notes = _optional_notes(source.get("safety_notes"))
    remaining_risks = _optional_notes(source.get("remaining_risks"))
    if safety_notes:
        notes.append("Safety notes: " + "; ".join(safety_notes))
    if remaining_risks:
        notes.append("Remaining risks: " + "; ".join(remaining_risks))
    if warnings:
        notes.append("Bridge warnings: " + "; ".join(warnings))
    return " ".join(notes)


def _optional_notes(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _next_recommended_action(source: Mapping[str, Any]) -> str:
    value = source.get("next_recommended_action")
    if isinstance(value, str) and value.strip():
        return value
    return "Inspect the bridged result, ingestion report, review report, and git diff before mark-done."


def _completed_at(
    source: Mapping[str, Any],
    execution_report: Mapping[str, Any],
    batch_report: Mapping[str, Any],
) -> str | None:
    value = source.get("completed_at")
    if isinstance(value, str) or value is None:
        return value or _string_or_none(execution_report.get("execution_ended_at")) or _string_or_none(batch_report.get("ended_at"))
    return _string_or_none(execution_report.get("execution_ended_at")) or _string_or_none(batch_report.get("ended_at"))


def _int_fact(source: Mapping[str, Any], execution_report: Mapping[str, Any], *keys: str) -> int:
    for key in keys:
        value = source.get(key)
        if type(value) is int:
            return value
    for key in keys:
        value = execution_report.get(key)
        if type(value) is int:
            return value
    return 0


def _bool_fact(source: Mapping[str, Any], execution_report: Mapping[str, Any], *keys: str) -> bool:
    for key in keys:
        value = source.get(key)
        if isinstance(value, bool):
            return value
    for key in keys:
        value = execution_report.get(key)
        if isinstance(value, bool):
            return value
    return False


def _mapping_value(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return None


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _default_review_result_func(queue_root: str | Path, task_id: str) -> dict[str, Any]:
    from .operator_cli import build_review_report

    return build_review_report(queue_root, task_id)


def _base_report(
    *,
    root: Path,
    run_id: str,
    batch_report_path: str | Path,
    bridge_results: bool,
    review_results: bool,
    overwrite_results: bool,
) -> dict[str, Any]:
    return {
        "schema_version": POSTPROCESS_REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "queue_root": str(root),
        "batch_report_path": str(batch_report_path),
        "batch_run_id": None,
        "batch_status": None,
        "batch_execution_status": None,
        "status": "blocked",
        "bridge_results": bridge_results,
        "review_results": review_results,
        "overwrite_results": overwrite_results,
        "policy": "continue through completed task executions; block individual tasks that cannot be bridged safely",
        "task_results": [],
        "completed_execution_count": 0,
        "bridged_count": 0,
        "ingested_count": 0,
        "reviewed_count": 0,
        "blocked_count": 0,
        "skipped_count": 0,
        "result_json_written_count": 0,
        "task_marked_done_automatically": False,
        "review_approved_automatically": False,
        "git_commit_performed": False,
        "git_push_performed": False,
        "scheduler_created": False,
        "daemon_created": False,
        "background_worker_created": False,
        "infinite_loop_created": False,
        "codex_exec_invoked": False,
        "codex_invocation_count": 0,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "wallet_or_private_key_access": False,
        "orders_or_trading_actions": False,
        "runtime_or_dispatcher_changes": False,
        "errors": [],
        "warnings": [],
        "next_operator_action": "",
        "report_paths": {},
    }


def _finalize_counts(report: dict[str, Any]) -> None:
    entries = list(report.get("task_results", []))
    report["completed_execution_count"] = sum(1 for entry in entries if entry.get("completed_execution"))
    report["bridged_count"] = sum(1 for entry in entries if entry.get("bridged"))
    report["ingested_count"] = sum(1 for entry in entries if entry.get("ingested"))
    report["reviewed_count"] = sum(1 for entry in entries if entry.get("reviewed"))
    report["blocked_count"] = sum(1 for entry in entries if entry.get("postprocess_status") == "blocked")
    report["skipped_count"] = sum(1 for entry in entries if entry.get("postprocess_status") == "skipped")
    report["result_json_written_count"] = report["bridged_count"]


def _write_postprocess_report(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    payload = dict(report)
    reports_dir = safe_queue_path(root, "reports")
    json_path = reports_dir / f"post_batch_review_summary_{payload['run_id']}.json"
    md_path = reports_dir / f"post_batch_review_summary_{payload['run_id']}.md"
    latest_json_path = reports_dir / "latest_post_batch_review_summary.json"
    latest_md_path = reports_dir / "latest_post_batch_review_summary.md"
    payload["report_paths"] = {
        "post_batch_summary_json": str(json_path),
        "post_batch_summary_md": str(md_path),
        "latest_post_batch_summary_json": str(latest_json_path),
        "latest_post_batch_summary_md": str(latest_md_path),
    }
    write_json_atomic(json_path, payload)
    write_text_atomic(md_path, render_postprocess_markdown(payload))
    write_json_atomic(latest_json_path, payload)
    write_text_atomic(latest_md_path, render_postprocess_markdown(payload))
    return payload


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
