from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from pm_bot.trading_core.execution_simulator import run_execution_simulator
from pm_bot.trading_core.future_real_adapter_boundary import write_future_real_adapter_boundary
from pm_bot.trading_core.paper_position_ledger import run_paper_position_ledger
from pm_bot.trading_core.portfolio_state import run_portfolio_state
from pm_bot.trading_core.post_execution_audit import run_post_execution_audit
from pm_bot.trading_core.risk_gate import run_risk_gate
from pm_bot.trading_core.risk_limits import write_default_paper_risk_limits
from pm_bot.trading_core.schemas import (
    GENERATED_AT,
    load_json_object,
    normalize_path,
    trading_core_safety_summary,
    write_json,
    write_text,
)
from pm_bot.trading_core.trade_intent_candidate import (
    DEFAULT_ACTIVE_HYPOTHESES_PATH,
    DEFAULT_FILLED_URL_DASHBOARD_PATH,
    DEFAULT_MARKET_QUEUE_PATH,
    build_paper_trade_intent_candidates,
    render_paper_trade_intent_candidates_markdown,
)
from pm_bot.trading_core.trading_core_safety_scan import run_trading_core_safety_scan
from pm_bot.trading_core.trading_dashboard import run_paper_trading_dashboard

WORKFLOW_STEP_CONTRACT = "pmbot_operator_workflow_step_result.v1"

DAILY_SUMMARY_SOURCE_JSON = Path("pm_bot/practical/artifacts/add_market_016/daily_workflow_summary_after_add_016.json")
DAILY_SUMMARY_SOURCE_MD = Path("pm_bot/practical/artifacts/add_market_016/daily_workflow_summary_after_add_016.md")
PRACTICAL_DASHBOARD_SOURCE_JSON = Path(
    "pm_bot/practical/artifacts/manual_url_collection_017c/public_evidence_dashboard_url_filled_pending_approval_017c.json"
)
PRACTICAL_DASHBOARD_SOURCE_MD = Path(
    "pm_bot/practical/artifacts/manual_url_collection_017c/public_evidence_dashboard_url_filled_pending_approval_017c.md"
)


def run_workflow_steps(*, out_dir: str | Path, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trading_dir = output_dir / "trading_core"
    trading_dir.mkdir(parents=True, exist_ok=True)
    context: dict[str, Any] = {
        "out_dir": output_dir,
        "trading_dir": trading_dir,
        "generated_at": generated_at,
        "artifacts": {},
    }
    steps: list[dict[str, Any]] = []
    for name, func in (
        ("load_latest_practical_state", step_load_latest_practical_state),
        ("build_daily_summary", step_build_daily_summary),
        ("refresh_practical_dashboard", step_refresh_practical_dashboard),
        ("build_paper_trade_intents", step_build_paper_trade_intents),
        ("write_paper_risk_limits", step_write_paper_risk_limits),
        ("run_risk_gate", step_run_risk_gate),
        ("run_execution_simulator", step_run_execution_simulator),
        ("build_paper_position_ledger", step_build_paper_position_ledger),
        ("build_portfolio_state", step_build_portfolio_state),
        ("run_post_execution_audit", step_run_post_execution_audit),
        ("build_paper_trading_dashboard", step_build_paper_trading_dashboard),
        ("write_future_real_adapter_boundary", step_write_future_real_adapter_boundary),
        ("run_trading_core_safety_scan", step_run_trading_core_safety_scan),
    ):
        steps.append(_run_step(name, func, context))
    return {"steps": steps, "context": context}


def step_load_latest_practical_state(context: dict[str, Any]) -> dict[str, Any]:
    market_queue = load_json_object(DEFAULT_MARKET_QUEUE_PATH, label="market queue")
    active_hypotheses = load_json_object(DEFAULT_ACTIVE_HYPOTHESES_PATH, label="active hypotheses")
    dashboard = load_json_object(DEFAULT_FILLED_URL_DASHBOARD_PATH, label="filled URL dashboard")
    state = {
        "contract_version": "pmbot_operator_latest_practical_state.v1",
        "generated_at": context["generated_at"],
        "market_queue_path": normalize_path(DEFAULT_MARKET_QUEUE_PATH),
        "active_hypotheses_path": normalize_path(DEFAULT_ACTIVE_HYPOTHESES_PATH),
        "practical_dashboard_path": normalize_path(DEFAULT_FILLED_URL_DASHBOARD_PATH),
        "tracked_market_count": market_queue.get("tracked_market_count"),
        "active_hypothesis_count": active_hypotheses.get("active_hypothesis_count"),
        "feedback_ready_count": 0,
        "unresolved_outcome_count": active_hypotheses.get("unresolved_count"),
        "ready_for_operator_approval": dashboard.get("ready_for_operator_approval"),
        "safety_summary": trading_core_safety_summary(),
    }
    out_json = context["out_dir"] / "latest_practical_state.json"
    out_md = context["out_dir"] / "latest_practical_state.md"
    write_json(out_json, state)
    write_text(
        out_md,
        "\n".join(
            [
                "# Latest Practical State",
                "",
                f"- Tracked markets: {state['tracked_market_count']}",
                f"- Active hypotheses: {state['active_hypothesis_count']}",
                f"- Unresolved outcomes: {state['unresolved_outcome_count']}",
                f"- Feedback ready: {state['feedback_ready_count']}",
            ]
        )
        + "\n",
    )
    context["artifacts"]["latest_practical_state_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_build_daily_summary(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["out_dir"] / "daily_summary.json"
    out_md = context["out_dir"] / "daily_summary.md"
    summary = load_json_object(DAILY_SUMMARY_SOURCE_JSON, label="daily summary after add")
    write_json(out_json, summary)
    write_text(out_md, DAILY_SUMMARY_SOURCE_MD.read_text(encoding="utf-8"))
    context["artifacts"]["daily_summary_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_refresh_practical_dashboard(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["out_dir"] / "tracked_market_dashboard.json"
    out_md = context["out_dir"] / "tracked_market_dashboard.md"
    dashboard = load_json_object(PRACTICAL_DASHBOARD_SOURCE_JSON, label="practical tracked dashboard")
    write_json(out_json, dashboard)
    write_text(out_md, PRACTICAL_DASHBOARD_SOURCE_MD.read_text(encoding="utf-8"))
    context["artifacts"]["practical_dashboard_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_build_paper_trade_intents(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "paper_trade_intent_candidates.json"
    out_md = context["trading_dir"] / "paper_trade_intent_candidates.md"
    batch = build_paper_trade_intent_candidates(generated_at=context["generated_at"])
    write_json(out_json, batch)
    write_text(out_md, render_paper_trade_intent_candidates_markdown(batch))
    context["candidates_batch"] = batch
    context["artifacts"]["paper_trade_intent_candidates_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_write_paper_risk_limits(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "paper_risk_limits.json"
    out_md = context["trading_dir"] / "paper_risk_limits.md"
    limits = write_default_paper_risk_limits(out_json_path=out_json, out_md_path=out_md)
    context["risk_limits"] = limits
    context["artifacts"]["risk_limits_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_run_risk_gate(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "risk_gate_results.json"
    out_md = context["trading_dir"] / "risk_gate_results.md"
    report = run_risk_gate(
        candidates_batch=context["candidates_batch"],
        limits=context["risk_limits"],
        out_json_path=out_json,
        out_md_path=out_md,
        generated_at=context["generated_at"],
    )
    context["risk_gate_batch"] = report
    context["artifacts"]["risk_gate_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_run_execution_simulator(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "simulated_execution_results.json"
    out_md = context["trading_dir"] / "simulated_execution_results.md"
    report = run_execution_simulator(
        candidates_batch=context["candidates_batch"],
        risk_gate_batch=context["risk_gate_batch"],
        out_json_path=out_json,
        out_md_path=out_md,
        generated_at=context["generated_at"],
    )
    context["execution_batch"] = report
    context["artifacts"]["simulated_execution_results_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_build_paper_position_ledger(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "paper_position_ledger.json"
    out_md = context["trading_dir"] / "paper_position_ledger.md"
    ledger = run_paper_position_ledger(
        execution_batch=context["execution_batch"],
        out_json_path=out_json,
        out_md_path=out_md,
        generated_at=context["generated_at"],
    )
    context["ledger"] = ledger
    context["artifacts"]["paper_position_ledger_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_build_portfolio_state(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "paper_portfolio_state.json"
    out_md = context["trading_dir"] / "paper_portfolio_state.md"
    state = run_portfolio_state(
        ledger=context["ledger"],
        risk_limits=context["risk_limits"],
        out_json_path=out_json,
        out_md_path=out_md,
        generated_at=context["generated_at"],
    )
    context["portfolio_state"] = state
    context["artifacts"]["portfolio_state_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_run_post_execution_audit(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "post_execution_audit.json"
    out_md = context["trading_dir"] / "post_execution_audit.md"
    audit = run_post_execution_audit(
        candidates_batch=context["candidates_batch"],
        risk_gate_batch=context["risk_gate_batch"],
        execution_batch=context["execution_batch"],
        ledger=context["ledger"],
        portfolio_state=context["portfolio_state"],
        out_json_path=out_json,
        out_md_path=out_md,
        generated_at=context["generated_at"],
    )
    context["audit"] = audit
    context["artifacts"]["audit_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_build_paper_trading_dashboard(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "paper_trading_dashboard.json"
    out_md = context["trading_dir"] / "paper_trading_dashboard.md"
    dashboard = run_paper_trading_dashboard(
        candidates_batch=context["candidates_batch"],
        risk_gate_batch=context["risk_gate_batch"],
        execution_batch=context["execution_batch"],
        ledger=context["ledger"],
        portfolio_state=context["portfolio_state"],
        audit=context["audit"],
        out_json_path=out_json,
        out_md_path=out_md,
        generated_at=context["generated_at"],
    )
    context["paper_trading_dashboard"] = dashboard
    context["artifacts"]["paper_trading_dashboard_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_write_future_real_adapter_boundary(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "future_real_adapter_boundary.json"
    out_md = context["trading_dir"] / "future_real_adapter_boundary.md"
    boundary = write_future_real_adapter_boundary(out_json_path=out_json, out_md_path=out_md, generated_at=context["generated_at"])
    context["future_real_adapter_boundary"] = boundary
    context["artifacts"]["future_real_adapter_boundary_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)]}


def step_run_trading_core_safety_scan(context: dict[str, Any]) -> dict[str, Any]:
    out_json = context["trading_dir"] / "trading_core_safety_scan.result.json"
    out_md = context["trading_dir"] / "trading_core_safety_scan.md"
    report = run_trading_core_safety_scan(
        artifact_dirs=[context["trading_dir"]],
        out_json_path=out_json,
        out_md_path=out_md,
        generated_at=context["generated_at"],
    )
    context["trading_core_safety_scan"] = report
    context["artifacts"]["trading_core_safety_scan_path"] = normalize_path(out_json)
    return {"output_paths": [normalize_path(out_json), normalize_path(out_md)], "safety_ok": report.get("safety_ok")}


def _run_step(name: str, func: Callable[[dict[str, Any]], dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    try:
        result = func(context)
        return {
            "contract_version": WORKFLOW_STEP_CONTRACT,
            "step_name": name,
            "status": "passed",
            "output_paths": result.get("output_paths", []),
            "safety_ok": result.get("safety_ok", True),
            "error": "",
        }
    except Exception as exc:
        return {
            "contract_version": WORKFLOW_STEP_CONTRACT,
            "step_name": name,
            "status": "failed",
            "output_paths": [],
            "safety_ok": False,
            "error": str(exc),
        }
