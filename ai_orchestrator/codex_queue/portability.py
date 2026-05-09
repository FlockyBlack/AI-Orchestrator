from __future__ import annotations

import importlib
import os
import platform as platform_module
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .files import ensure_queue_directories, safe_queue_path, write_json_atomic, write_text_atomic
from .schema import QUEUE_DIRECTORIES

PORTABILITY_SCHEMA_VERSION = "codex_queue_portability_report.v1"

REQUIRED_CLI_COMMANDS = (
    "status",
    "runbook",
    "morning-report",
    "night-dry-run",
    "scheduler-plan",
)

TEXT_SUFFIXES = {".json", ".md", ".py", ".txt", ".yml", ".yaml", ".toml"}
WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"\b[A-Za-z]:[\\/][A-Za-z0-9_.-][^\s`'\"<>)]*")
HARDCODED_C_PATH_RE = re.compile(r"\bC:[\\/][A-Za-z0-9_.-][^\s`'\"<>)]*", re.IGNORECASE)
MAX_FINDINGS = 200


def collect_portability_report(repo_root: str, queue_root: str) -> dict[str, Any]:
    repo_path = Path(repo_root).resolve(strict=False)
    queue_path = _resolve_queue_root(repo_path, queue_root)
    package_import = _check_package_import()
    queue_dirs = {
        directory: (queue_path / directory).is_dir()
        for directory in QUEUE_DIRECTORIES
    }
    absolute_path_leaks = _scan_absolute_path_leaks(repo_path, queue_path)
    hardcoded_c_paths = _scan_hardcoded_c_paths(repo_path, queue_path)

    report: dict[str, Any] = {
        "schema_version": PORTABILITY_SCHEMA_VERSION,
        "run_id": _run_id(),
        "generated_at": _utc_iso(),
        "repo_root": str(repo_path),
        "queue_root": str(queue_path),
        "python_version": sys.version.split()[0],
        "platform": platform_module.platform(),
        "path_separator": os.sep,
        "package_import_ok": package_import["ok"],
        "package_import_error": package_import["error"],
        "queue_dirs_present": queue_dirs,
        "docs_dir_present": (repo_path / "docs").is_dir(),
        "tests_dir_present": (repo_path / "tests").is_dir(),
        "windows_path_risks": _windows_path_risks(absolute_path_leaks, hardcoded_c_paths),
        "absolute_path_leaks": absolute_path_leaks,
        "hardcoded_c_path_occurrences": hardcoded_c_paths,
        "commands_available": _commands_available(package_import["ok"], queue_root),
        "codex_execution_added": False,
        "codex_app_server_used": False,
        "automatic_execution_enabled": False,
        "branch_created": False,
        "worktree_created": False,
        "background_worker_added": False,
        "scheduler_registered": False,
        "network_calls_performed": 0,
        "credentials_accessed": False,
        "warnings": _portability_warnings(queue_dirs, absolute_path_leaks, hardcoded_c_paths, package_import),
    }
    return report


def generate_portability_report(repo_root: str | Path, queue_root: str | Path) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    report = collect_portability_report(str(repo_root), str(root))
    reports_dir = safe_queue_path(root, "reports")
    json_path = reports_dir / "latest_portability_report.json"
    md_path = reports_dir / "latest_portability_report.md"
    report["report_paths"] = {
        "latest_portability_report_json": str(json_path),
        "latest_portability_report_md": str(md_path),
    }
    write_json_atomic(json_path, report)
    write_text_atomic(md_path, render_portability_markdown(report))
    return report


def render_portability_markdown(report: Mapping[str, Any]) -> str:
    queue_dirs = _as_mapping(report.get("queue_dirs_present"))
    leaks = _as_mapping(report.get("absolute_path_leaks"))
    hardcoded = _as_mapping(report.get("hardcoded_c_path_occurrences"))
    commands = _as_mapping(report.get("commands_available"))
    lines = [
        "# Codex Queue Portability Report",
        "",
        f"- run_id: `{report['run_id']}`",
        f"- repo_root: `{report['repo_root']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- python_version: `{report['python_version']}`",
        f"- platform: `{report['platform']}`",
        f"- path_separator: `{report['path_separator']}`",
        f"- package_import_ok: `{report['package_import_ok']}`",
        f"- docs_dir_present: `{report['docs_dir_present']}`",
        f"- tests_dir_present: `{report['tests_dir_present']}`",
        "",
        "## Queue Directories",
        "",
    ]
    for directory, present in queue_dirs.items():
        lines.append(f"- {directory}: `{present}`")
    lines.extend(["", "## Commands", ""])
    for name, command in commands.items():
        if not isinstance(command, Mapping):
            continue
        lines.append(f"- {name}: available=`{command.get('available')}` command=`{command.get('command')}`")
    lines.extend(
        [
            "",
            "## Path Findings",
            "",
            f"- absolute_path_leaks_count: `{leaks.get('count', 0)}`",
            f"- hardcoded_c_path_occurrences_count: `{hardcoded.get('count', 0)}`",
            f"- findings_truncated: `{bool(leaks.get('truncated') or hardcoded.get('truncated'))}`",
            "",
        ]
    )
    if report.get("warnings"):
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.get("warnings", []))
        lines.append("")
    lines.extend(
        [
            "## Safety",
            "",
            "This check reads local source, test, queue, and ORCH documentation files and writes reports only. It does not execute Codex, call Codex app-server, create branches, create worktrees, register schedulers, start workers, call network services, or access credentials.",
            "",
        ]
    )
    return "\n".join(lines)


def _resolve_queue_root(repo_root: Path, queue_root: str | Path) -> Path:
    candidate = Path(queue_root)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve(strict=False)


def _check_package_import() -> dict[str, Any]:
    try:
        importlib.import_module("ai_orchestrator.codex_queue")
    except Exception as exc:  # pragma: no cover - defensive environment report
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "error": ""}


def _commands_available(package_import_ok: bool, queue_root: str | Path) -> dict[str, dict[str, Any]]:
    base = "python -m ai_orchestrator.codex_queue.operator_cli"
    commands: dict[str, dict[str, Any]] = {}
    for command in REQUIRED_CLI_COMMANDS:
        suffix = f"{command} --queue-root {queue_root}"
        if command == "night-dry-run":
            suffix = f"{suffix} --max-tasks 5"
        commands[command] = {
            "available": bool(package_import_ok),
            "command": f"{base} {suffix}",
        }
    return commands


def _scan_absolute_path_leaks(repo_root: Path, queue_root: Path) -> dict[str, Any]:
    scan_roots = [
        queue_root / "reports",
        queue_root / "templates",
    ]
    return _scan_paths(repo_root, scan_roots, WINDOWS_ABSOLUTE_PATH_RE)


def _scan_hardcoded_c_paths(repo_root: Path, queue_root: Path) -> dict[str, Any]:
    scan_roots: list[Path] = [
        repo_root / "ai_orchestrator" / "codex_queue",
        repo_root / "tests",
        queue_root / "templates",
    ]
    scan_roots.extend((queue_root).glob("*.md"))
    docs_dir = repo_root / "docs"
    scan_roots.extend(docs_dir.glob("ORCH*.md"))
    scan_roots.extend(docs_dir.glob("ORCH*.json"))
    return _scan_paths(repo_root, scan_roots, HARDCODED_C_PATH_RE)


def _scan_paths(repo_root: Path, roots: Iterable[Path], pattern: re.Pattern[str]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    total = 0
    for path in _iter_text_files(roots):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not pattern.search(line):
                continue
            total += 1
            if len(findings) < MAX_FINDINGS:
                findings.append(
                    {
                        "file": _relative_to(repo_root, path),
                        "line": line_number,
                        "snippet": line.strip()[:180],
                    }
                )
    return {
        "count": total,
        "truncated": total > len(findings),
        "occurrences": findings,
    }


def _iter_text_files(roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            resolved = path.resolve(strict=False)
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path


def _windows_path_risks(
    absolute_path_leaks: Mapping[str, Any],
    hardcoded_c_paths: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "running_on_windows": os.sep == "\\",
        "uses_backslash_separator": os.sep == "\\",
        "absolute_path_leaks_detected": int(absolute_path_leaks.get("count", 0)) > 0,
        "hardcoded_c_paths_detected": int(hardcoded_c_paths.get("count", 0)) > 0,
        "absolute_path_leaks_count": int(absolute_path_leaks.get("count", 0)),
        "hardcoded_c_path_occurrences_count": int(hardcoded_c_paths.get("count", 0)),
    }


def _portability_warnings(
    queue_dirs: Mapping[str, bool],
    absolute_path_leaks: Mapping[str, Any],
    hardcoded_c_paths: Mapping[str, Any],
    package_import: Mapping[str, Any],
) -> list[str]:
    warnings: list[str] = []
    missing_dirs = [directory for directory, present in queue_dirs.items() if not present]
    if missing_dirs:
        warnings.append("missing queue directories: " + ", ".join(missing_dirs))
    if not package_import.get("ok"):
        warnings.append(f"package import failed: {package_import.get('error')}")
    if absolute_path_leaks.get("count"):
        warnings.append("absolute local paths were detected in generated reports/templates; review before packaging")
    if hardcoded_c_paths.get("count"):
        warnings.append("hardcoded C:/ or C:\\ paths were detected; review for portability before packaging")
    return warnings


def _relative_to(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(repo_root))
    except ValueError:
        return str(path)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
