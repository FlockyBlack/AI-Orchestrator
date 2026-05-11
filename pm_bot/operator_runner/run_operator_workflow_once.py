from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Sequence

from pm_bot.operator_runner.workflow_config import (
    OPERATOR_ARTIFACT_DIR,
    default_operator_workflow_config,
    validate_operator_workflow_config,
    write_operator_workflow_config,
)
from pm_bot.operator_runner.workflow_report import build_final_operator_report, write_final_operator_report
from pm_bot.operator_runner.workflow_safety_scan import run_operator_workflow_safety_scan
from pm_bot.operator_runner.workflow_steps import run_workflow_steps
from pm_bot.trading_core.schemas import GENERATED_AT, normalize_path, write_json, write_text

OPERATOR_WORKFLOW_RUN_RESULT_CONTRACT = "pmbot_operator_workflow_run_result.v1"


def run_operator_workflow_once(
    *,
    out_dir: str | Path,
    include_trading_core: bool = True,
    no_live_fetch: bool = True,
    no_real_trading: bool = True,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = default_operator_workflow_config(
        run_id="operator-workflow-night-020-021-run-001",
        artifact_root=output_dir,
        generated_at=generated_at,
    )
    config["include_trading_core"] = include_trading_core
    config["allow_live_fetch"] = False if no_live_fetch else config["allow_live_fetch"]
    config["allow_real_trading"] = False if no_real_trading else config["allow_real_trading"]
    valid, errors = validate_operator_workflow_config(config)
    if not valid:
        raise ValueError(f"operator workflow config failed safety validation: {'; '.join(errors)}")

    write_operator_workflow_config(
        config=config,
        out_json_path=OPERATOR_ARTIFACT_DIR / "operator_workflow_config.json",
        out_md_path=OPERATOR_ARTIFACT_DIR / "operator_workflow_config.md",
    )
    write_operator_workflow_config(
        config=config,
        out_json_path=output_dir / "operator_workflow_config.json",
        out_md_path=output_dir / "operator_workflow_config.md",
    )

    step_result = run_workflow_steps(out_dir=output_dir, generated_at=generated_at)
    steps = step_result["steps"]
    artifacts = step_result["context"]["artifacts"]

    workflow_scan_json = output_dir / "operator_workflow_safety_scan.result.json"
    workflow_scan_md = output_dir / "operator_workflow_safety_scan.md"
    workflow_scan = run_operator_workflow_safety_scan(
        artifact_dirs=[output_dir],
        out_json_path=workflow_scan_json,
        out_md_path=workflow_scan_md,
        generated_at=generated_at,
    )

    final_report_json = output_dir / "final_operator_report.json"
    final_report_md = output_dir / "final_operator_report.md"
    final_report = build_final_operator_report(
        run_id=config["run_id"],
        steps=steps,
        artifacts=artifacts,
        workflow_safety_scan_path=normalize_path(workflow_scan_json),
        trading_core_safety_scan_path=artifacts.get("trading_core_safety_scan_path", ""),
        generated_at=generated_at,
    )
    write_final_operator_report(report=final_report, out_json_path=final_report_json, out_md_path=final_report_md)

    passed = [step for step in steps if step.get("status") == "passed"]
    failed = [step for step in steps if step.get("status") == "failed"]
    result = {
        "contract_version": OPERATOR_WORKFLOW_RUN_RESULT_CONTRACT,
        "run_id": config["run_id"],
        "generated_at": generated_at,
        "run_once": True,
        "repeat_count": 1,
        "out_dir": normalize_path(output_dir),
        "steps_run": len(steps),
        "steps_passed": len(passed),
        "steps_failed": len(failed),
        "step_results": steps,
        "final_operator_report_path": normalize_path(final_report_json),
        "operator_workflow_safety_scan_path": normalize_path(workflow_scan_json),
        "paper_trading_dashboard_path": artifacts.get("paper_trading_dashboard_path", ""),
        "portfolio_state_path": artifacts.get("portfolio_state_path", ""),
        "audit_path": artifacts.get("audit_path", ""),
        "safety_ok": workflow_scan.get("safety_ok") is True and not failed,
        "live_fetch_performed": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_used": False,
        "orders_used": False,
        "real_trading_enabled": False,
        "scheduler_created": False,
        "daemon_created": False,
        "background_worker_created": False,
        "infinite_loop_created": False,
    }
    write_json(output_dir / "operator_workflow_run_result.json", result)
    write_text(output_dir / "operator_workflow_run_result.md", render_operator_workflow_run_result_markdown(result))
    return result


def render_operator_workflow_run_result_markdown(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Operator Workflow Run Result",
            "",
            f"- Run ID: `{result.get('run_id')}`",
            f"- Run once: `{str(result.get('run_once')).lower()}`",
            f"- Repeat count: `{result.get('repeat_count')}`",
            f"- Steps run: {result.get('steps_run')}",
            f"- Steps passed: {result.get('steps_passed')}",
            f"- Steps failed: {result.get('steps_failed')}",
            f"- Safety OK: `{str(result.get('safety_ok')).lower()}`",
            f"- Final report: `{result.get('final_operator_report_path')}`",
            "",
            "## Safety",
            "",
            "- No live fetch, OpenRouter, Polymarket API, authenticated endpoint, wallet, order, real trading, scheduler, daemon, background worker, polling loop, or infinite loop.",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the PMBOT explicit one-shot local operator workflow.")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--include-trading-core", action="store_true", default=False)
    parser.add_argument("--no-live-fetch", action="store_true", default=False)
    parser.add_argument("--no-real-trading", action="store_true", default=False)
    args = parser.parse_args(argv)
    run_operator_workflow_once(
        out_dir=args.out_dir,
        include_trading_core=args.include_trading_core,
        no_live_fetch=args.no_live_fetch,
        no_real_trading=args.no_real_trading,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
