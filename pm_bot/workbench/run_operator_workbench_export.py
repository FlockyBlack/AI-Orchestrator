import argparse
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-WORKBENCH-003-SINGLE-COMMAND-LOCAL-EXPORT"
SCHEMA_VERSION = "operator_workbench_export_run.v1"
GENERATED_BY = "pm_bot/workbench/run_operator_workbench_export.py"
RUN_MODE = "manual_local_export"

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "pm_bot" / "workbench"
DOCS_DIR = ROOT / "docs"

DEFAULT_RUN_JSON = WORKBENCH_DIR / "operator_workbench_export_run.v1.json"
DEFAULT_RUN_MD = WORKBENCH_DIR / "operator_workbench_export_run.v1.md"
DEFAULT_EXPECTED_RUN_JSON = WORKBENCH_DIR / "expected_operator_workbench_export_run.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_WORKBENCH_003_RESULT.json"

SUMMARY_OUTPUT_ARTIFACTS = [
    "pm_bot/workbench/operator_workbench_export_run.v1.json",
    "pm_bot/workbench/operator_workbench_export_run.v1.md",
    "pm_bot/workbench/expected_operator_workbench_export_run.v1.json",
    "docs/PMBOT_WORKBENCH_003_RESULT.json",
]

SAFETY_FLAGS = {
    "manual_cli_only": True,
    "offline_only": True,
    "deterministic": True,
    "local_file_operations_only": True,
    "runtime_wiring": False,
    "network_api": False,
    "wallet": False,
    "trading": False,
    "autonomous_paper_orders": False,
    "scoring_probability_ev_edge": False,
    "market_decisions": False,
    "command_execution": False,
    "automation_daemon": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run deterministic local PMBOT operator workbench exporters in safe order."
    )
    parser.add_argument("--markdown", action="store_true", help="Print Markdown summary instead of JSON.")
    return parser.parse_args(argv)


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        value = resolved.relative_to(Path(root).resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_export_steps(root=ROOT):
    return [
        {
            "step_id": "portfolio_audit_state",
            "script_path": "pm_bot/dashboard/export_portfolio_audit_state.py",
            "required": False,
            "runner": "module_function",
            "function_name": "write_portfolio_audit_state_artifacts",
            "output_artifacts": [
                "pm_bot/dashboard/portfolio_audit_state_contract.v1.json",
                "pm_bot/dashboard/portfolio_audit_state_preview.v1.json",
                "pm_bot/dashboard/portfolio_audit_state_preview.v1.md",
                "pm_bot/dashboard/expected_portfolio_audit_state_preview.v1.json",
            ],
        },
        {
            "step_id": "manual_command_inbox_review",
            "script_path": "pm_bot/operator/review_manual_command_inbox.py",
            "required": False,
            "runner": "manual_command_inbox_review",
            "output_artifacts": [
                "pm_bot/operator/manual_command_inbox_review.v1.json",
                "pm_bot/operator/manual_command_inbox_review.v1.md",
                "pm_bot/operator/expected_manual_command_inbox_review.v1.json",
            ],
        },
        {
            "step_id": "artifact_health_report",
            "script_path": "pm_bot/quality/export_artifact_health_report.py",
            "required": False,
            "runner": "module_function",
            "function_name": "write_artifact_health_report",
            "output_artifacts": [
                "pm_bot/quality/artifact_health_report.v1.json",
                "pm_bot/quality/artifact_health_report.v1.md",
                "pm_bot/quality/expected_artifact_health_report.v1.json",
                "docs/PMBOT_QUALITY_001_RESULT.json",
                "docs/PMBOT_CODEX_B_ROUND003_RESULT.json",
            ],
        },
        {
            "step_id": "operator_review_pack",
            "script_path": "pm_bot/workbench/export_operator_review_pack.py",
            "required": True,
            "runner": "module_function",
            "function_name": "write_operator_review_pack_artifacts",
            "output_artifacts": [
                "pm_bot/workbench/operator_review_pack.v1.json",
                "pm_bot/workbench/operator_review_pack.v1.md",
                "pm_bot/workbench/expected_operator_review_pack.v1.json",
                "docs/PMBOT_WORKBENCH_001_RESULT.json",
                "docs/PMBOT_CODEX_A_ROUND003_RESULT.json",
            ],
        },
    ]


def _load_module(script_path, step_id):
    module_name = f"pmbot_workbench_export_{step_id}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _payload_reports_failure(payload):
    if not isinstance(payload, dict):
        return False
    status = payload.get("status")
    report_status = payload.get("report_status")
    blockers = payload.get("blockers")
    if status in {"blocked", "failed", "error", "health_failed"}:
        return True
    if report_status == "health_failed":
        return True
    return isinstance(blockers, list) and bool(blockers)


def _run_module_function(step, root):
    script_path = Path(root) / step["script_path"]
    module = _load_module(script_path, step["step_id"])
    function = getattr(module, step["function_name"])
    return function()


def _run_manual_command_inbox_review(step, root):
    script_path = Path(root) / step["script_path"]
    module = _load_module(script_path, step["step_id"])
    inbox_path = Path(root) / "pm_bot" / "operator" / "manual_command_inbox_fixture.v1.json"
    report = module.review_manual_command_inbox(Path(root), inbox_path)
    report_json = Path(root) / "pm_bot" / "operator" / "manual_command_inbox_review.v1.json"
    expected_json = Path(root) / "pm_bot" / "operator" / "expected_manual_command_inbox_review.v1.json"
    report_md = Path(root) / "pm_bot" / "operator" / "manual_command_inbox_review.v1.md"
    _write_json(report_json, report)
    _write_json(expected_json, report)
    _write_text(report_md, module.render_markdown(report))
    return {
        "task_id": report["task_id"],
        "status": "manual_command_inbox_review_exported",
        "files_written": step["output_artifacts"],
        "records_seen": report["records_seen"],
        "accepted_count": report["accepted_count"],
        "rejected_count": report["rejected_count"],
        "needs_human_review_count": report["needs_human_review_count"],
        "commands_executed": 0,
        "orders_created": 0,
        "network_calls": 0,
    }


def _run_step(step, root=ROOT):
    script_path = Path(root) / step["script_path"]
    base = {
        "step_id": step["step_id"],
        "script_path": step["script_path"],
        "required": step["required"],
        "status": None,
        "output_artifacts": list(step["output_artifacts"]),
    }
    if not script_path.exists():
        if step["required"]:
            return {**base, "status": "failed", "failure_type": "required_script_missing"}
        return {**base, "status": "skipped_optional"}

    try:
        if step["runner"] == "manual_command_inbox_review":
            payload = _run_manual_command_inbox_review(step, root)
        else:
            payload = _run_module_function(step, root)
    except Exception as exc:
        return {**base, "status": "failed", "failure_type": type(exc).__name__}

    if _payload_reports_failure(payload):
        return {**base, "status": "failed", "failure_type": "exporter_reported_failure"}
    return {**base, "status": "ran"}


def _ordered_unique(values):
    seen = set()
    ordered = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _warnings_for_steps(steps):
    warnings = []
    for step in steps:
        if step["status"] == "skipped_optional":
            warnings.append(f"optional exporter skipped because script is absent: {step['script_path']}")
        elif step["status"] == "failed" and not step["required"]:
            warnings.append(f"optional exporter failed: {step['step_id']} ({step.get('failure_type', 'unknown')})")
        elif step["status"] == "failed" and step["required"]:
            warnings.append(f"required exporter failed: {step['step_id']} ({step.get('failure_type', 'unknown')})")
    return warnings


def build_run_summary(step_results):
    required_steps_passed = all(
        step["status"] == "ran" for step in step_results if step["required"]
    )
    artifacts = []
    for step in step_results:
        if step["status"] == "ran":
            artifacts.extend(step["output_artifacts"])
    artifacts.extend(SUMMARY_OUTPUT_ARTIFACTS)
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "run_mode": RUN_MODE,
        "steps": step_results,
        "required_steps_passed": required_steps_passed,
        "optional_steps_skipped": [
            step["step_id"] for step in step_results if step["status"] == "skipped_optional"
        ],
        "artifacts_refreshed": _ordered_unique(artifacts),
        "warnings": _warnings_for_steps(step_results),
        "safety_flags": dict(SAFETY_FLAGS),
        "network_calls": 0,
        "commands_executed": 0,
        "orders_created": 0,
        "next_safe_action": (
            "Open pm_bot/workbench/operator_workbench_export_run.v1.md, then "
            "pm_bot/workbench/operator_review_pack.v1.md for manual local review."
        ),
    }


def render_markdown(summary):
    lines = [
        "# PMBOT Operator Workbench Export Run v1",
        "",
        f"- schema_version: {summary['schema_version']}",
        f"- task_id: {summary['task_id']}",
        f"- generated_by: {summary['generated_by']}",
        f"- run_mode: {summary['run_mode']}",
        f"- required_steps_passed: {str(summary['required_steps_passed']).lower()}",
        f"- optional_steps_skipped: {len(summary['optional_steps_skipped'])}",
        f"- network_calls: {summary['network_calls']}",
        f"- commands_executed: {summary['commands_executed']}",
        f"- orders_created: {summary['orders_created']}",
        "",
        "## Steps",
        "",
    ]
    for step in summary["steps"]:
        lines.append(
            "- "
            f"{step['step_id']}: status={step['status']}, required={str(step['required']).lower()}, "
            f"script={step['script_path']}"
        )
        if step.get("failure_type"):
            lines.append(f"  failure_type: {step['failure_type']}")
        for artifact in step["output_artifacts"]:
            lines.append(f"  output: {artifact}")

    lines.extend(["", "## Artifacts Refreshed", ""])
    for artifact in summary["artifacts_refreshed"]:
        lines.append(f"- {artifact}")

    lines.extend(["", "## Warnings", ""])
    if summary["warnings"]:
        lines.extend(f"- {warning}" for warning in summary["warnings"])
    else:
        lines.append("- none")

    lines.extend(["", "## Safety Flags", ""])
    for key in sorted(summary["safety_flags"]):
        lines.append(f"- {key}: {str(summary['safety_flags'][key]).lower()}")
    lines.extend(["", f"- next_safe_action: {summary['next_safe_action']}", ""])
    return "\n".join(lines)


def _result_payload(summary):
    completed = summary["required_steps_passed"]
    return {
        "task_id": TASK_ID,
        "status": "completed_ready_for_review" if completed else "blocked",
        "summary": (
            "Created deterministic manual local PMBOT operator workbench export runner."
            if completed
            else "Manual local PMBOT operator workbench export runner blocked on required workbench export."
        ),
        "runner": {
            "script": GENERATED_BY,
            "run_mode": RUN_MODE,
            "steps_run": [
                step["step_id"] for step in summary["steps"] if step["status"] == "ran"
            ],
            "optional_steps_skipped": list(summary["optional_steps_skipped"]),
            "required_steps_passed": summary["required_steps_passed"],
        },
        "files_created": [
            "pm_bot/workbench/run_operator_workbench_export.py",
            "pm_bot/workbench/operator_workbench_export_run.v1.json",
            "pm_bot/workbench/operator_workbench_export_run.v1.md",
            "pm_bot/workbench/expected_operator_workbench_export_run.v1.json",
            "pm_bot/workbench/tests/test_operator_workbench_export_runner.py",
            "docs/PMBOT_WORKBENCH_003_RESULT.json",
        ],
        "files_modified": [
            "docs/PMBOT_WORKBENCH_002_OPERATOR_QUICKSTART.md",
            "docs/PMBOT_WORKBENCH_001_RESULT.json",
            "docs/PMBOT_CODEX_A_ROUND003_RESULT.json",
            "docs/PMBOT_QUALITY_001_RESULT.json",
            "docs/PMBOT_CODEX_B_ROUND003_RESULT.json",
            "pm_bot/dashboard/portfolio_audit_state_preview.v1.json",
            "pm_bot/dashboard/portfolio_audit_state_preview.v1.md",
            "pm_bot/dashboard/expected_portfolio_audit_state_preview.v1.json",
            "pm_bot/quality/artifact_health_report.v1.json",
            "pm_bot/quality/artifact_health_report.v1.md",
            "pm_bot/quality/expected_artifact_health_report.v1.json",
            "pm_bot/workbench/operator_review_pack.v1.json",
            "pm_bot/workbench/operator_review_pack.v1.md",
            "pm_bot/workbench/expected_operator_review_pack.v1.json",
        ],
        "artifacts_refreshed": summary["artifacts_refreshed"],
        "run_summary_artifact": "pm_bot/workbench/operator_workbench_export_run.v1.json",
        "safety_flags": summary["safety_flags"],
        "network_calls": 0,
        "commands_executed": 0,
        "orders_created": 0,
        "warnings": summary["warnings"],
        "blockers": [] if completed else summary["warnings"],
        "next_action": summary["next_safe_action"],
    }


def write_run_artifacts(summary, root=ROOT):
    run_json = Path(root) / "pm_bot" / "workbench" / "operator_workbench_export_run.v1.json"
    expected_json = Path(root) / "pm_bot" / "workbench" / "expected_operator_workbench_export_run.v1.json"
    run_md = Path(root) / "pm_bot" / "workbench" / "operator_workbench_export_run.v1.md"
    result_json = Path(root) / "docs" / "PMBOT_WORKBENCH_003_RESULT.json"
    _write_json(run_json, summary)
    _write_json(expected_json, summary)
    _write_text(run_md, render_markdown(summary))
    _write_json(result_json, _result_payload(summary))


def run_operator_workbench_export(root=ROOT):
    step_results = [_run_step(step, root=root) for step in build_export_steps(root)]
    summary = build_run_summary(step_results)
    write_run_artifacts(summary, root=root)
    return summary


def exit_code_for_summary(summary):
    return 0 if summary["required_steps_passed"] else 2


def main(argv):
    args = _parse_args(argv)
    summary = run_operator_workbench_export(ROOT)
    if args.markdown:
        print(render_markdown(summary), end="")
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=True))
    return exit_code_for_summary(summary)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
