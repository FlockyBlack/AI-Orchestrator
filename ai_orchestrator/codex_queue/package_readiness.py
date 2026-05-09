from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .files import ensure_queue_directories, safe_queue_path, write_json_atomic, write_text_atomic
from .portability import REQUIRED_CLI_COMMANDS
from .schema import QUEUE_DIRECTORIES

PACKAGE_READINESS_SCHEMA_VERSION = "codex_queue_package_readiness.v1"

REQUIRED_MODULES = (
    "schema.py",
    "validator.py",
    "safety.py",
    "planner.py",
    "dry_run_runner.py",
    "result_schema.py",
    "result_validator.py",
    "result_ingestor.py",
    "operator_cli.py",
    "git_safety.py",
    "workspace_planner.py",
    "queue_health.py",
    "runbook.py",
    "morning_report.py",
    "night_runner.py",
    "scheduler_plan.py",
    "portability.py",
    "package_readiness.py",
)

REQUIRED_TESTS = (
    "test_codex_queue_schema.py",
    "test_codex_queue_validator.py",
    "test_codex_queue_safety.py",
    "test_codex_queue_planner.py",
    "test_codex_queue_dry_run_runner.py",
    "test_codex_queue_result_schema.py",
    "test_codex_queue_result_validator.py",
    "test_codex_queue_result_ingestor.py",
    "test_codex_queue_operator_cli.py",
    "test_codex_queue_git_safety.py",
    "test_codex_queue_workspace_planner.py",
    "test_codex_queue_queue_health.py",
    "test_codex_queue_runbook.py",
    "test_codex_queue_morning_report.py",
    "test_codex_queue_night_runner.py",
    "test_codex_queue_scheduler_plan.py",
)

LATEST_REPORTS = (
    "latest_dry_run_report.json",
    "latest_workspace_plan.json",
    "latest_result_ingestion_report.json",
    "latest_queue_status.json",
    "latest_operator_action.json",
    "latest_controlled_codex_runbook.json",
    "latest_morning_report.json",
    "latest_night_dry_run_plan.json",
    "latest_scheduler_plan.json",
    "latest_portability_report.json",
)


def generate_package_readiness_report(queue_root: str | Path) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    repo_root = Path.cwd().resolve(strict=False)
    modules = _modules_present(repo_root)
    tests = _tests_present(repo_root)
    reports = _latest_reports_present(root)
    pilot = _successful_pilot_evidence(repo_root, root)
    safety_gates = _safety_gates_present(modules, tests, reports)

    report: dict[str, Any] = {
        "schema_version": PACKAGE_READINESS_SCHEMA_VERSION,
        "status": "ready_for_operator_review",
        "run_id": _run_id(),
        "generated_at": _utc_iso(),
        "repo_root": str(repo_root),
        "queue_root": str(root),
        "modules_present": modules,
        "tests_present": tests,
        "cli_commands_available": _cli_commands(str(root)),
        "queue_dirs_present": {
            directory: safe_queue_path(root, directory).is_dir()
            for directory in QUEUE_DIRECTORIES
        },
        "latest_reports_present": reports,
        "successful_pilot_evidence_present": pilot,
        "safety_gates_present": safety_gates,
        "remaining_manual_steps": _remaining_manual_steps(),
        "blockers_before_real_unattended_scheduler": _scheduler_blockers(),
        "recommended_operator_commit_checklist": _commit_checklist(),
        "git_add_performed": False,
        "git_commit_performed": False,
        "git_push_performed": False,
        "branch_created": False,
        "worktree_created": False,
        "real_scheduler_registered": False,
        "background_worker_added": False,
        "codex_execution_added": False,
        "codex_app_server_used": False,
        "official_symphony_runtime_integrated": False,
        "linear_integration_added": False,
        "github_issues_integration_added": False,
        "network_calls_performed": 0,
        "credentials_accessed": False,
        "warnings": _readiness_warnings(modules, tests, reports, pilot, safety_gates),
    }

    reports_dir = safe_queue_path(root, "reports")
    json_path = reports_dir / "latest_package_readiness.json"
    md_path = reports_dir / "latest_package_readiness.md"
    report["report_paths"] = {
        "latest_package_readiness_json": str(json_path),
        "latest_package_readiness_md": str(md_path),
    }
    write_json_atomic(json_path, report)
    write_text_atomic(md_path, render_package_readiness_markdown(report))
    return report


def render_package_readiness_markdown(report: Mapping[str, Any]) -> str:
    modules = _as_mapping(report.get("modules_present"))
    tests = _as_mapping(report.get("tests_present"))
    reports = _as_mapping(report.get("latest_reports_present"))
    pilot = _as_mapping(report.get("successful_pilot_evidence_present"))
    gates = _as_mapping(report.get("safety_gates_present"))
    lines = [
        "# Codex Queue Package Readiness",
        "",
        f"- status: `{report['status']}`",
        f"- run_id: `{report['run_id']}`",
        f"- repo_root: `{report['repo_root']}`",
        f"- queue_root: `{report['queue_root']}`",
        f"- modules_present_count: `{_count_present(modules)}/{len(modules)}`",
        f"- tests_present_count: `{_count_present(tests)}/{len(tests)}`",
        f"- latest_reports_present_count: `{_count_present(reports)}/{len(reports)}`",
        f"- successful_pilot_core_evidence_present: `{pilot.get('core_evidence_present')}`",
        "",
        "## CLI Commands",
        "",
    ]
    for name, command in _as_mapping(report.get("cli_commands_available")).items():
        lines.append(f"- {name}: `{command}`")
    lines.extend(["", "## Safety Gates", ""])
    for gate, present in gates.items():
        lines.append(f"- {gate}: `{present}`")
    lines.extend(["", "## Remaining Manual Steps", ""])
    lines.extend(f"- {step}" for step in report.get("remaining_manual_steps", []))
    lines.extend(["", "## Blockers Before Real Unattended Scheduler", ""])
    lines.extend(f"- {blocker}" for blocker in report.get("blockers_before_real_unattended_scheduler", []))
    lines.extend(["", "## Recommended Commit Checklist", ""])
    lines.extend(f"- {item}" for item in report.get("recommended_operator_commit_checklist", []))
    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report.get("warnings", []))
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This readiness command reads local source, tests, queue artifacts, and reports and writes a readiness report only. It does not stage, commit, push, create branches, create worktrees, register schedulers, start workers, execute Codex, call Codex app-server, call network services, or access credentials.",
            "",
        ]
    )
    return "\n".join(lines)


def _modules_present(repo_root: Path) -> dict[str, bool]:
    module_root = repo_root / "ai_orchestrator" / "codex_queue"
    return {module: (module_root / module).is_file() for module in REQUIRED_MODULES}


def _tests_present(repo_root: Path) -> dict[str, bool]:
    tests_root = repo_root / "tests"
    return {test: (tests_root / test).is_file() for test in REQUIRED_TESTS}


def _latest_reports_present(queue_root: Path) -> dict[str, bool]:
    reports_dir = safe_queue_path(queue_root, "reports")
    return {report: (reports_dir / report).is_file() for report in LATEST_REPORTS}


def _successful_pilot_evidence(repo_root: Path, queue_root: Path) -> dict[str, Any]:
    evidence = {
        "done_task_packet": safe_queue_path(
            queue_root,
            "done",
            "ORCH-PILOT-001-REAL-DOCS-HANDOFF.task.json",
        ).is_file(),
        "review_result_packet": safe_queue_path(
            queue_root,
            "review",
            "ORCH-PILOT-001-REAL-DOCS-HANDOFF.result.json",
        ).is_file(),
        "review_report": safe_queue_path(
            queue_root,
            "reports",
            "ORCH-PILOT-001-REAL-DOCS-HANDOFF.review.json",
        ).is_file(),
        "pilot_output_doc": (repo_root / "docs" / "ORCH_PILOT_001_REAL_DOCS_HANDOFF_OUTPUT.md").is_file(),
        "orch_008_result": (
            repo_root / "docs" / "ORCH_SYMPHONY_008_REAL_MANUAL_CODEX_TASK_PILOT_NO_AUTONOMY_RESULT.json"
        ).is_file(),
    }
    evidence["core_evidence_present"] = all(evidence.values())
    return evidence


def _safety_gates_present(
    modules: Mapping[str, bool],
    tests: Mapping[str, bool],
    reports: Mapping[str, bool],
) -> dict[str, bool]:
    return {
        "schema_validation": bool(modules.get("schema.py") and modules.get("validator.py")),
        "safety_classifier": bool(modules.get("safety.py") and tests.get("test_codex_queue_safety.py")),
        "dry_run_planner": bool(modules.get("planner.py") and modules.get("dry_run_runner.py")),
        "manual_handoff_prompt_generation": bool(modules.get("planner.py")),
        "manual_result_ingestion": bool(modules.get("result_ingestor.py")),
        "review_gate": bool(modules.get("operator_cli.py")),
        "workspace_planning_dry_run_only": bool(modules.get("workspace_planner.py")),
        "runbook_reporting": bool(modules.get("runbook.py") and reports.get("latest_controlled_codex_runbook.json")),
        "morning_reporting": bool(modules.get("morning_report.py") and reports.get("latest_morning_report.json")),
        "night_dry_run_reporting": bool(modules.get("night_runner.py") and reports.get("latest_night_dry_run_plan.json")),
        "scheduler_plan_report_only": bool(modules.get("scheduler_plan.py") and reports.get("latest_scheduler_plan.json")),
        "portability_reporting": bool(modules.get("portability.py")),
        "package_readiness_reporting": bool(modules.get("package_readiness.py")),
    }


def _cli_commands(queue_root: str) -> dict[str, str]:
    base = "python -m ai_orchestrator.codex_queue.operator_cli"
    commands = {command: f"{base} {command} --queue-root {queue_root}" for command in REQUIRED_CLI_COMMANDS}
    commands["night-dry-run"] = f"{commands['night-dry-run']} --max-tasks 5"
    commands["portability-check"] = f"{base} portability-check --queue-root {queue_root}"
    commands["package-readiness"] = f"{base} package-readiness --queue-root {queue_root}"
    return commands


def _remaining_manual_steps() -> list[str]:
    return [
        "Operator creates or approves task packets explicitly.",
        "Operator runs dry-run planning and workspace planning explicitly.",
        "Operator reviews handoff prompts before manually running Codex.",
        "Operator places manual result JSON under agent_tasks/review/.",
        "Operator runs ingest-result, review, and mark-done explicitly.",
        "Operator selectively stages files for commit after reviewing the dirty worktree.",
    ]


def _scheduler_blockers() -> list[str]:
    return [
        "No explicit approval task exists for scheduler registration.",
        "No background worker has been designed or approved.",
        "No autonomous Codex execution gate has been approved.",
        "No unattended credential/network policy has been approved.",
        "Git packaging still needs selective staging and final review.",
        "Historical generated reports may contain local absolute paths that should not be packaged blindly.",
    ]


def _commit_checklist() -> list[str]:
    return [
        "Run git status --short and review the large pre-existing untracked set.",
        "Avoid git add .",
        "Selectively add only ai_orchestrator/codex_queue, focused tests, agent_tasks documentation/reports, and ORCH-009 docs intended for the package.",
        "Review latest_portability_report.json and latest_package_readiness.json before staging.",
        "Use commit message: Add local Symphony-style Codex automation queue",
    ]


def _readiness_warnings(
    modules: Mapping[str, bool],
    tests: Mapping[str, bool],
    reports: Mapping[str, bool],
    pilot: Mapping[str, Any],
    gates: Mapping[str, bool],
) -> list[str]:
    warnings: list[str] = []
    missing_modules = [name for name, present in modules.items() if not present]
    missing_tests = [name for name, present in tests.items() if not present]
    missing_reports = [name for name, present in reports.items() if not present]
    missing_gates = [name for name, present in gates.items() if not present]
    if missing_modules:
        warnings.append("missing modules: " + ", ".join(missing_modules))
    if missing_tests:
        warnings.append("missing tests: " + ", ".join(missing_tests))
    if missing_reports:
        warnings.append("missing latest reports: " + ", ".join(missing_reports))
    if not pilot.get("core_evidence_present"):
        warnings.append("successful pilot evidence is incomplete")
    if missing_gates:
        warnings.append("some safety gates are not fully evidenced: " + ", ".join(missing_gates))
    warnings.append("real unattended scheduler activation remains intentionally blocked")
    return warnings


def _count_present(values: Mapping[str, Any]) -> int:
    return sum(1 for value in values.values() if value is True)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
