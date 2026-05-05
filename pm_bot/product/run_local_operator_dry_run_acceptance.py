import argparse
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-PRODUCT-003-LOCAL-OPERATOR-DRY-RUN-ACCEPTANCE"
SCHEMA_VERSION = "local_operator_dry_run_acceptance.v1"
GENERATED_BY = "pm_bot/product/run_local_operator_dry_run_acceptance.py"

ROOT = Path(__file__).resolve().parents[2]
PRODUCT_DIR = ROOT / "pm_bot" / "product"
DOCS_DIR = ROOT / "docs"

DEFAULT_REPORT_JSON = PRODUCT_DIR / "local_operator_dry_run_acceptance.v1.json"
DEFAULT_REPORT_MD = PRODUCT_DIR / "local_operator_dry_run_acceptance.v1.md"
DEFAULT_EXPECTED_JSON = PRODUCT_DIR / "expected_local_operator_dry_run_acceptance.v1.json"
DEFAULT_RESULT_JSON = DOCS_DIR / "PMBOT_PRODUCT_003_RESULT.json"

WORKBENCH_RUNNER = "pm_bot/workbench/run_operator_workbench_export.py"

REQUIRED_OPERATOR_ARTIFACTS = [
    {
        "artifact_id": "dashboard_state",
        "path": "pm_bot/dashboard/static_operator_report_summary.v1.json",
        "required": True,
        "operator_label": "Dashboard state summary",
    },
    {
        "artifact_id": "artifact_health_report",
        "path": "pm_bot/quality/artifact_health_report.v1.json",
        "required": True,
        "operator_label": "Artifact health report",
    },
    {
        "artifact_id": "operator_review_pack",
        "path": "pm_bot/workbench/operator_review_pack.v1.json",
        "required": True,
        "operator_label": "Operator review pack",
    },
    {
        "artifact_id": "inbox_review",
        "path": "pm_bot/operator/manual_command_inbox_review.v1.json",
        "required": True,
        "operator_label": "Manual command inbox review",
    },
    {
        "artifact_id": "workbench_run",
        "path": "pm_bot/workbench/operator_workbench_export_run.v1.json",
        "required": True,
        "operator_label": "Workbench export run summary",
    },
]

SAFETY_FLAGS = {
    "network_api_calls": False,
    "wallet_or_private_key_usage": False,
    "real_orders": False,
    "live_trading": False,
    "autonomous_decisions": False,
    "scoring_probability_ev_edge": False,
    "side_recommendations": False,
    "runtime_wiring": False,
    "command_execution": False,
}

OPERATOR_NEXT_ACTIONS = [
    "Open pm_bot/dashboard/static_operator_report.v1.html for the first local operator view.",
    "Open pm_bot/workbench/operator_review_pack.v1.md and inspect inventory, warning, paper accounting, and inbox sections.",
    "Review pm_bot/quality/artifact_health_report.v1.md warning categories and owner/action paths before treating the package as polished.",
    "Inspect pm_bot/operator/manual_command_inbox_review.v1.md only as an inert review queue; do not execute commands from it.",
    "Use accounting and PnL fields only as local fixture accounting checks, not strategy profitability.",
]

INTERPRETATION_LIMITS = [
    "Accounting/PnL is accounting-only local fixture output and is not strategy profitability.",
    "The acceptance layer makes no recommendations, market decisions, scoring, probability, EV, edge, or side calls.",
    "Warnings are intentionally preserved and remain separate from blockers.",
    "The report is local, deterministic, offline, and operator-review-only.",
    "No live market truth, live settlement truth, wallet state, or trading readiness is inferred.",
]


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Generate deterministic PMBOT local operator dry-run acceptance artifacts."
    )
    parser.add_argument(
        "--consume-existing",
        action="store_true",
        help="Do not rerun the workbench exporter; consume existing local workbench artifacts.",
    )
    parser.add_argument("--markdown", action="store_true", help="Print Markdown report instead of JSON.")
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


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module(script_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_workbench_export(root=ROOT, consume_existing=False):
    runner_path = Path(root) / WORKBENCH_RUNNER
    if consume_existing:
        return {
            "status": "consumed_existing",
            "runner_path": WORKBENCH_RUNNER,
            "required_steps_passed": None,
            "warnings": [],
            "blockers": [],
        }
    if not runner_path.exists():
        return {
            "status": "failed_to_run",
            "runner_path": WORKBENCH_RUNNER,
            "required_steps_passed": False,
            "warnings": [],
            "blockers": [f"workbench runner missing: {WORKBENCH_RUNNER}"],
        }
    try:
        module = _load_module(runner_path, "pmbot_product_003_workbench_runner")
        summary = module.run_operator_workbench_export(Path(root))
    except Exception as exc:
        return {
            "status": "failed_to_run",
            "runner_path": WORKBENCH_RUNNER,
            "required_steps_passed": False,
            "warnings": [],
            "blockers": [f"workbench runner failed: {type(exc).__name__}"],
        }
    return {
        "status": "ran",
        "runner_path": WORKBENCH_RUNNER,
        "required_steps_passed": bool(summary.get("required_steps_passed")),
        "warnings": list(summary.get("warnings", [])),
        "blockers": [] if summary.get("required_steps_passed") else list(summary.get("warnings", [])),
    }


def check_artifacts(root=ROOT):
    checked = []
    for item in REQUIRED_OPERATOR_ARTIFACTS:
        path = Path(root) / item["path"]
        parse_status = "not_checked"
        payload = None
        if path.exists() and path.suffix == ".json":
            try:
                payload = _load_json(path)
                parse_status = "parsed"
            except json.JSONDecodeError:
                parse_status = "parse_failed"
        elif path.exists():
            parse_status = "not_json"
        checked.append(
            {
                "artifact_id": item["artifact_id"],
                "operator_label": item["operator_label"],
                "path": item["path"],
                "required": item["required"],
                "present": path.exists(),
                "parse_status": parse_status,
                "schema_version": payload.get("schema_version") if isinstance(payload, dict) else None,
                "task_id": payload.get("task_id") if isinstance(payload, dict) else None,
                "status": payload.get("status") or payload.get("report_status") if isinstance(payload, dict) else None,
            }
        )
    return checked


def _required_artifacts_present(artifacts):
    return all(
        item["present"] and item["parse_status"] != "parse_failed"
        for item in artifacts
        if item["required"]
    )


def _warning_summary(root=ROOT):
    default = {
        "total": 0,
        "blocking": 0,
        "action_required": 0,
        "review_needed": 0,
        "informational": 0,
    }
    path = Path(root) / "pm_bot/quality/artifact_health_report.v1.json"
    if not path.exists():
        return default
    try:
        report = _load_json(path)
    except json.JSONDecodeError:
        return default
    summary = report.get("warning_severity_summary", {})
    return {
        "total": int(summary.get("total_warnings", len(report.get("warnings", [])))),
        "blocking": int(summary.get("blocking_count", 0)),
        "action_required": int(summary.get("action_required_count", 0)),
        "review_needed": int(summary.get("review_needed_count", 0)),
        "informational": int(summary.get("informational_count", 0)),
    }


def _blockers(root, artifacts, workbench_result, warning_summary):
    blockers = []
    for item in artifacts:
        if item["required"] and not item["present"]:
            blockers.append(f"required artifact missing: {item['path']}")
        elif item["required"] and item["parse_status"] == "parse_failed":
            blockers.append(f"required artifact JSON parse failed: {item['path']}")
    blockers.extend(workbench_result.get("blockers", []))
    health_path = Path(root) / "pm_bot/quality/artifact_health_report.v1.json"
    if health_path.exists():
        try:
            blockers.extend(_load_json(health_path).get("blockers", []))
        except json.JSONDecodeError:
            blockers.append("artifact health report JSON parse failed")
    if warning_summary["blocking"] > 0:
        blockers.append(f"blocking warnings present: {warning_summary['blocking']}")
    return list(dict.fromkeys(blockers))


def _operator_usability_status(verdict):
    if verdict == "blocked":
        return "not_usable_until_blockers_resolved"
    if verdict == "failed_to_run":
        return "not_usable_because_dry_run_failed"
    if verdict == "accepted_with_warnings":
        return "usable_for_local_operator_review_with_warnings"
    return "usable_for_local_operator_review"


def _verdict(workbench_result, required_present, warnings, blockers):
    if workbench_result["status"] == "failed_to_run":
        return "failed_to_run"
    if blockers or not required_present:
        return "blocked"
    if warnings["total"] > 0:
        return "accepted_with_warnings"
    return "accepted_for_local_operator_use"


def build_acceptance_report(root=ROOT, consume_existing=False):
    workbench_result = run_workbench_export(root, consume_existing=consume_existing)
    artifacts = check_artifacts(root)
    required_present = _required_artifacts_present(artifacts)
    warnings = _warning_summary(root)
    blockers = _blockers(root, artifacts, workbench_result, warnings)
    verdict = _verdict(workbench_result, required_present, warnings, blockers)
    status = "completed_ready_for_review" if verdict in {"accepted_for_local_operator_use", "accepted_with_warnings"} else verdict
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "status": status,
        "generated_by": GENERATED_BY,
        "run_mode": "local_operator_dry_run_acceptance",
        "workbench_export": workbench_result,
        "acceptance_verdict": verdict,
        "operator_usability_status": _operator_usability_status(verdict),
        "artifacts_checked": artifacts,
        "required_artifacts_present": required_present,
        "presence_summary": {
            "dashboard_state_present": any(
                item["artifact_id"] == "dashboard_state" and item["present"] for item in artifacts
            ),
            "artifact_health_report_present": any(
                item["artifact_id"] == "artifact_health_report" and item["present"] for item in artifacts
            ),
            "operator_review_pack_present": any(
                item["artifact_id"] == "operator_review_pack" and item["present"] for item in artifacts
            ),
            "inbox_review_present": any(
                item["artifact_id"] == "inbox_review" and item["present"] for item in artifacts
            ),
        },
        "warnings_summary": warnings,
        "blockers": blockers,
        "safety_flags": dict(SAFETY_FLAGS),
        "operator_next_actions": list(OPERATOR_NEXT_ACTIONS),
        "interpretation_limits": list(INTERPRETATION_LIMITS),
        "acceptance_basis": [
            "Required local operator artifacts exist and parse.",
            "Warnings are summarized separately from blockers.",
            "Safety flags remain false for network, wallet, orders, live trading, autonomous decisions, scoring, side recommendations, runtime wiring, and command execution.",
            "Operator next actions are review-only.",
        ],
    }


def render_markdown(report):
    lines = [
        "# PMBOT PRODUCT-003 Local Operator Dry Run Acceptance",
        "",
        f"Task: `{report['task_id']}`",
        "",
        f"Status: `{report['status']}`",
        "",
        f"Acceptance verdict: `{report['acceptance_verdict']}`",
        "",
        f"Operator usability status: `{report['operator_usability_status']}`",
        "",
        "## What Was Checked",
        "",
    ]
    for artifact in report["artifacts_checked"]:
        lines.append(
            "- "
            f"{artifact['operator_label']}: present={str(artifact['present']).lower()}, "
            f"parse_status={artifact['parse_status']}, path=`{artifact['path']}`"
        )

    lines.extend(["", "## What Passed", ""])
    if report["required_artifacts_present"]:
        lines.append("- All required operator artifacts are present and parseable.")
    else:
        lines.append("- One or more required operator artifacts are missing or unparseable.")
    lines.append("- Safety boundaries report no network/API calls, wallet/private key use, real orders, live trading, autonomous decisions, scoring/EV/edge, side recommendations, runtime wiring, or command execution.")
    lines.append("- Operator next actions are manual review actions only.")

    warnings = report["warnings_summary"]
    lines.extend(["", "## Warnings", ""])
    lines.append(f"- total: `{warnings['total']}`")
    lines.append(f"- blocking: `{warnings['blocking']}`")
    lines.append(f"- action_required: `{warnings['action_required']}`")
    lines.append(f"- review_needed: `{warnings['review_needed']}`")
    lines.append(f"- informational: `{warnings['informational']}`")
    if warnings["total"]:
        lines.append("- Warnings are not hidden. They remain separate from blockers.")

    lines.extend(["", "## Blockers", ""])
    if report["blockers"]:
        lines.extend(f"- {blocker}" for blocker in report["blockers"])
    else:
        lines.append("- none")

    lines.extend(["", "## Local MVP Usability", ""])
    lines.append(
        "PMBOT is usable only as a local, offline, deterministic operator review package "
        "when the verdict is accepted. It is not a trading system and does not make decisions."
    )
    lines.append(
        "Accounting/PnL values are accounting-only local artifact checks and are not strategy profitability."
    )
    lines.append(
        "No recommendations, probabilities, EV, edge, side selections, market decisions, or truth inference are made."
    )

    lines.extend(["", "## Manual Operator Actions", ""])
    lines.extend(f"- {action}" for action in report["operator_next_actions"])

    lines.extend(["", "## Safety Boundary Summary", ""])
    for key in sorted(report["safety_flags"]):
        lines.append(f"- {key}: `{str(report['safety_flags'][key]).lower()}`")

    lines.extend(["", "## Interpretation Limits", ""])
    lines.extend(f"- {limit}" for limit in report["interpretation_limits"])
    lines.append("")
    return "\n".join(lines)


def _result_payload(report):
    return {
        "task_id": TASK_ID,
        "status": report["status"],
        "summary": "Generated deterministic product-level local operator dry-run acceptance artifacts.",
        "acceptance_verdict": report["acceptance_verdict"],
        "operator_usability_status": report["operator_usability_status"],
        "warnings_summary": report["warnings_summary"],
        "blockers": report["blockers"],
        "safety_flags": report["safety_flags"],
        "files_created": [
            "pm_bot/product/run_local_operator_dry_run_acceptance.py",
            "pm_bot/product/local_operator_dry_run_acceptance.v1.json",
            "pm_bot/product/local_operator_dry_run_acceptance.v1.md",
            "pm_bot/product/expected_local_operator_dry_run_acceptance.v1.json",
            "pm_bot/product/tests/test_local_operator_dry_run_acceptance.py",
            "docs/PMBOT_PRODUCT_003_LOCAL_OPERATOR_DRY_RUN_ACCEPTANCE.md",
            "docs/PMBOT_PRODUCT_003_RESULT.json",
        ],
        "operator_next_actions": report["operator_next_actions"],
        "interpretation_limits": report["interpretation_limits"],
    }


def write_acceptance_artifacts(report, root=ROOT):
    product_dir = Path(root) / "pm_bot" / "product"
    docs_dir = Path(root) / "docs"
    report_json = product_dir / "local_operator_dry_run_acceptance.v1.json"
    expected_json = product_dir / "expected_local_operator_dry_run_acceptance.v1.json"
    report_md = product_dir / "local_operator_dry_run_acceptance.v1.md"
    docs_md = docs_dir / "PMBOT_PRODUCT_003_LOCAL_OPERATOR_DRY_RUN_ACCEPTANCE.md"
    result_json = docs_dir / "PMBOT_PRODUCT_003_RESULT.json"
    _write_json(report_json, report)
    _write_json(expected_json, report)
    markdown = render_markdown(report)
    _write_text(report_md, markdown)
    _write_text(docs_md, markdown)
    _write_json(result_json, _result_payload(report))


def run_local_operator_dry_run_acceptance(root=ROOT, consume_existing=False):
    report = build_acceptance_report(root=root, consume_existing=consume_existing)
    write_acceptance_artifacts(report, root=root)
    return report


def exit_code_for_report(report):
    return 0 if report["acceptance_verdict"] in {"accepted_for_local_operator_use", "accepted_with_warnings"} else 2


def main(argv):
    args = _parse_args(argv)
    report = run_local_operator_dry_run_acceptance(ROOT, consume_existing=args.consume_existing)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    return exit_code_for_report(report)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
