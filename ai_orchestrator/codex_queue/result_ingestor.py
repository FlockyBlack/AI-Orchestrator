from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping

from .report_writer import ensure_queue_directories, utc_run_id, write_json, write_text
from .result_schema import FILE_LIST_FIELDS, SCHEMA_VERSION as RESULT_SCHEMA_VERSION
from .result_validator import validate_result
from .schema import SCHEMA_VERSION as TASK_PACKET_SCHEMA_VERSION
from .validator import ValidationResult, validate_packet

TASK_PACKET_SEARCH_DIRECTORIES = (
    "approved",
    "planned",
    "review",
    "done",
    "blocked",
)

CONSERVATIVE_ALLOWED_PATHS = (
    "docs/",
    "agent_tasks/review/",
    "agent_tasks/reports/",
)

CONSERVATIVE_FORBIDDEN_PATHS = (
    "ai_orchestrator/",
    "pm_bot/",
    ".git/",
    ".openclaw/",
    "runtime/",
    "dispatcher/",
    "run_codex/",
)

RUNTIME_DISPATCHER_TOKENS = (
    "runtime",
    "dispatcher",
    "run_codex",
)


def ingest_result(queue_root: str | Path, result_path: str | Path) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    run_id = utc_run_id()
    result_file = Path(result_path)
    errors: list[str] = []

    result_payload, load_errors = _load_json(result_file)
    result_validation = validate_result(result_payload) if not load_errors else ValidationResult(False, tuple(load_errors))
    errors.extend(result_validation.errors)

    task_id = result_payload.get("task_id") if isinstance(result_payload, Mapping) else None
    task_match: dict[str, Any] = {
        "found": False,
        "task_id": task_id,
        "packet_path": None,
        "search_directories": [str(root / directory) for directory in TASK_PACKET_SEARCH_DIRECTORIES],
        "errors": [],
    }
    task_validation = ValidationResult(False, ("matching task packet was not validated",))
    path_validation = ValidationResult(False, ("changed file paths were not validated",))

    if result_validation.valid and isinstance(task_id, str):
        task_match = find_matching_task_packet(root, task_id)
        errors.extend(task_match["errors"])
        if task_match["found"]:
            task_packet = task_match["packet"]
            task_validation = validate_packet(task_packet)
            errors.extend(task_validation.errors)
            if task_validation.valid:
                path_validation = validate_changed_file_paths(result_payload, task_packet)
                errors.extend(path_validation.errors)
        else:
            errors.append(f"no matching task packet found for task_id: {task_id}")

    accepted = not errors
    report: dict[str, Any] = {
        "run_id": run_id,
        "queue_root": str(root),
        "result_path": str(result_file),
        "task_id": task_id,
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "ingestion_status": "accepted" if accepted else "blocked",
        "accepted": accepted,
        "errors": errors,
        "result_validation": result_validation.to_dict(),
        "task_match": _public_task_match(task_match),
        "task_validation": task_validation.to_dict(),
        "path_validation": path_validation.to_dict(),
        "commands_from_result_executed": False,
        "commands_run_recorded_only": True,
        "task_marked_done_automatically": False,
        "task_packets_moved": False,
        "codex_execution_added": False,
        "codex_app_server_used": False,
        "automatic_execution_enabled": False,
        "official_symphony_runtime_integrated": False,
        "linear_integration_added": False,
        "github_issues_integration_added": False,
        "background_worker_added": False,
        "scheduler_added": False,
        "telegram_added": False,
        "openclaw_added": False,
        "network_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "credentials_accessed": False,
        "wallet_or_trading_touched": False,
        "runtime_or_dispatcher_touched": False,
        "destructive_commands_used": False,
    }
    report["report_paths"] = write_result_ingestion_reports(root, report)
    return report


def find_matching_task_packet(queue_root: str | Path, task_id: str) -> dict[str, Any]:
    root = Path(queue_root)
    unreadable: list[str] = []

    for directory in TASK_PACKET_SEARCH_DIRECTORIES:
        search_dir = root / directory
        for packet_path in sorted(search_dir.glob("*.json")):
            try:
                payload = json.loads(packet_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                unreadable.append(f"{packet_path}: invalid JSON: {exc}")
                continue

            if not isinstance(payload, Mapping):
                continue
            if payload.get("task_id") != task_id:
                continue
            if payload.get("schema_version") != TASK_PACKET_SCHEMA_VERSION:
                continue
            return {
                "found": True,
                "task_id": task_id,
                "packet_path": str(packet_path),
                "packet": payload,
                "search_directories": [str(root / name) for name in TASK_PACKET_SEARCH_DIRECTORIES],
                "errors": unreadable,
            }

    return {
        "found": False,
        "task_id": task_id,
        "packet_path": None,
        "packet": None,
        "search_directories": [str(root / name) for name in TASK_PACKET_SEARCH_DIRECTORIES],
        "errors": unreadable,
    }


def validate_changed_file_paths(
    result: Mapping[str, Any],
    task_packet: Mapping[str, Any],
) -> ValidationResult:
    repo = task_packet.get("repo", {})
    allowed_paths = list(repo.get("allowed_paths") or []) if isinstance(repo, Mapping) else []
    forbidden_paths = list(repo.get("forbidden_paths") or []) if isinstance(repo, Mapping) else []
    using_conservative_defaults = not allowed_paths
    active_allowed_paths = allowed_paths or list(CONSERVATIVE_ALLOWED_PATHS)
    active_forbidden_paths = list(forbidden_paths)
    if using_conservative_defaults:
        active_forbidden_paths.extend(CONSERVATIVE_FORBIDDEN_PATHS)

    errors: list[str] = []
    for field in FILE_LIST_FIELDS:
        for index, value in enumerate(result.get(field, [])):
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field}[{index}] must be a non-empty repo-relative path string")
                continue

            normalized, path_errors = _normalize_result_path(value)
            for error in path_errors:
                errors.append(f"{field}[{index}] {error}")
            if path_errors or normalized is None:
                continue

            if _matches_any_rule(normalized, active_forbidden_paths):
                errors.append(f"{field}[{index}] path is under forbidden_paths: {value}")
                continue

            if using_conservative_defaults and _is_runtime_or_dispatcher_like(normalized):
                errors.append(f"{field}[{index}] path is runtime/dispatcher-like: {value}")
                continue

            if active_allowed_paths and not _matches_any_rule(normalized, active_allowed_paths):
                errors.append(f"{field}[{index}] path is outside allowed_paths: {value}")

    return ValidationResult(not errors, tuple(errors))


def write_result_ingestion_reports(queue_root: str | Path, report: Mapping[str, Any]) -> dict[str, str]:
    root = ensure_queue_directories(queue_root)
    reports_dir = root / "reports"
    run_json = reports_dir / f"result_ingestion_report_{report['run_id']}.json"
    latest_json = reports_dir / "latest_result_ingestion_report.json"
    latest_md = reports_dir / "latest_result_ingestion_report.md"
    report_paths = {
        "run_report_json": str(run_json),
        "latest_report_json": str(latest_json),
        "latest_report_md": str(latest_md),
    }
    payload = dict(report)
    payload["report_paths"] = report_paths
    write_json(run_json, payload)
    write_json(latest_json, payload)
    write_text(latest_md, render_result_ingestion_markdown(payload))
    return report_paths


def render_result_ingestion_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Latest Codex Result Ingestion Report",
        "",
        f"- run_id: `{report['run_id']}`",
        f"- ingestion_status: `{report['ingestion_status']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- result_path: `{report['result_path']}`",
        f"- task_id: `{report.get('task_id')}`",
        f"- matching_task_packet: `{report['task_match'].get('packet_path')}`",
        f"- commands_from_result_executed: `{report['commands_from_result_executed']}`",
        f"- task_marked_done_automatically: `{report['task_marked_done_automatically']}`",
        "",
        "## Validation",
        "",
        f"- result_schema_valid: `{report['result_validation']['valid']}`",
        f"- task_packet_found: `{report['task_match']['found']}`",
        f"- task_packet_valid: `{report['task_validation']['valid']}`",
        f"- path_validation_valid: `{report['path_validation']['valid']}`",
        "",
    ]

    if report["errors"]:
        lines.extend(["## Blocking Errors", ""])
        for error in report["errors"]:
            lines.append(f"- {error}")
        lines.append("")

    lines.extend(
        [
            "## Safety",
            "",
            "This ingestor is local-only. It loads a manually supplied result packet, checks that it matches an existing task packet, validates declared safety confirmations, validates declared changed paths against the task packet path rules, and writes review reports.",
            "",
            "It does not execute Codex, use Codex app-server, run commands listed in the result, inspect git diffs deeply, move task packets, mark tasks done, start background workers, add schedulers, call network services, or integrate with external trackers.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json(path: Path) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [f"result file not found: {path}"]
    except json.JSONDecodeError as exc:
        return None, [f"invalid result JSON: {exc}"]


def _public_task_match(task_match: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "found": bool(task_match.get("found")),
        "task_id": task_match.get("task_id"),
        "packet_path": task_match.get("packet_path"),
        "search_directories": list(task_match.get("search_directories", [])),
        "errors": list(task_match.get("errors", [])),
    }


def _normalize_result_path(value: str) -> tuple[str | None, list[str]]:
    raw = value.strip()
    errors: list[str] = []

    if PureWindowsPath(raw).drive:
        errors.append("must not contain an absolute drive path")
    if PureWindowsPath(raw).is_absolute() or PurePosixPath(raw).is_absolute() or raw.startswith("\\"):
        errors.append("must be repo-relative")

    normalized = raw.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    path = PurePosixPath(normalized)
    parts = path.parts
    if not parts or normalized in {"", "."}:
        errors.append("must be a non-empty repo-relative path")
    if ".." in parts:
        errors.append("must not contain path traversal")
    if any(part == "" for part in parts):
        errors.append("must not contain empty path segments")

    if errors:
        return None, errors
    return "/".join(parts), []


def _matches_any_rule(path: str, rules: list[str] | tuple[str, ...]) -> bool:
    return any(_matches_rule(path, rule) for rule in rules)


def _matches_rule(path: str, rule: str) -> bool:
    normalized_rule = _normalize_rule(rule)
    if not normalized_rule:
        return False
    return path == normalized_rule or path.startswith(f"{normalized_rule}/")


def _normalize_rule(rule: str) -> str:
    normalized = str(rule).strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def _is_runtime_or_dispatcher_like(path: str) -> bool:
    parts = [part.lower() for part in PurePosixPath(path).parts]
    return any(token in part for token in RUNTIME_DISPATCHER_TOKENS for part in parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest a manual Codex handoff result packet.")
    parser.add_argument("--queue-root", default="agent_tasks", help="Local queue root directory.")
    parser.add_argument("--result", required=True, help="Result packet JSON path to ingest.")
    args = parser.parse_args(argv)

    report = ingest_result(args.queue_root, args.result)
    print(
        json.dumps(
            {
                "status": report["ingestion_status"],
                "accepted": report["accepted"],
                "report_paths": report["report_paths"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
