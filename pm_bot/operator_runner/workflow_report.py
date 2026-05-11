from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, normalize_path, trading_core_safety_summary, write_json, write_text

OPERATOR_WORKFLOW_RUN_REPORT_CONTRACT = "pmbot_operator_workflow_run_report.v1"


def build_final_operator_report(
    *,
    run_id: str,
    steps: list[Mapping[str, Any]],
    artifacts: Mapping[str, Any],
    workflow_safety_scan_path: str,
    trading_core_safety_scan_path: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    passed = [step for step in steps if step.get("status") == "passed"]
    failed = [step for step in steps if step.get("status") == "failed"]
    report = {
        "contract_version": OPERATOR_WORKFLOW_RUN_REPORT_CONTRACT,
        "run_id": run_id,
        "generated_at": generated_at,
        "steps_run": len(steps),
        "steps_passed": len(passed),
        "steps_failed": len(failed),
        "daily_summary_path": artifacts.get("daily_summary_path", ""),
        "paper_trading_dashboard_path": artifacts.get("paper_trading_dashboard_path", ""),
        "portfolio_state_path": artifacts.get("portfolio_state_path", ""),
        "audit_path": artifacts.get("audit_path", ""),
        "safety_scan_paths": [trading_core_safety_scan_path, workflow_safety_scan_path],
        "next_operator_actions": [
            "Open the final operator report and paper trading dashboard.",
            "Review observe-only markets that still lack saved public evidence.",
            "Keep outcome updates manual until saved local resolution evidence exists.",
            "Use the next Codex task suggestion for the paper loop and automation recovery milestone.",
        ],
        "next_codex_task_suggestion": "ORCH-PMBOT-TRADING-MVP-022-PAPER-TRADING-LOOP-DAILY-RUN-AND-CODEX-AUTOMATION-RECOVERY",
        "safety_summary": {
            **trading_core_safety_summary(),
            "workflow_safety_scan_path": workflow_safety_scan_path,
            "trading_core_safety_scan_path": trading_core_safety_scan_path,
            "one_shot": True,
            "repeat_count": 1,
            "background_mode_allowed": False,
        },
    }
    return report


def write_final_operator_report(
    *,
    report: Mapping[str, Any],
    out_json_path: str | Path,
    out_md_path: str | Path,
) -> dict[str, Any]:
    active_report = dict(report)
    write_json(out_json_path, active_report)
    write_text(out_md_path, render_final_operator_report_markdown(active_report))
    return active_report


def render_final_operator_report_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Final Operator Report",
            "",
            f"- Run ID: `{report.get('run_id')}`",
            f"- Steps run: {report.get('steps_run')}",
            f"- Steps passed: {report.get('steps_passed')}",
            f"- Steps failed: {report.get('steps_failed')}",
            f"- Daily summary: `{report.get('daily_summary_path')}`",
            f"- Paper trading dashboard: `{report.get('paper_trading_dashboard_path')}`",
            f"- Portfolio state: `{report.get('portfolio_state_path')}`",
            f"- Audit: `{report.get('audit_path')}`",
            "",
            "## Safety scans",
            "",
            *bullet_lines(str(path) for path in report.get("safety_scan_paths", [])),
            "",
            "## Next operator actions",
            "",
            *bullet_lines(str(item) for item in report.get("next_operator_actions", [])),
            "",
            "## Next Codex task suggestion",
            "",
            f"- `{report.get('next_codex_task_suggestion')}`",
            "",
            "## Safety summary",
            "",
            "- One explicit local command, one run, then exit.",
            "- No live fetch, OpenRouter, Polymarket API, wallet, order, real trading, scheduler, daemon, background worker, polling loop, or infinite loop.",
        ]
    ) + "\n"


def final_report_paths(out_dir: str | Path) -> tuple[str, str]:
    root = Path(out_dir)
    return normalize_path(root / "final_operator_report.json"), normalize_path(root / "final_operator_report.md")
