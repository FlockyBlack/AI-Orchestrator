from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.operator_runner.paper_daily_config import (
    PaperDailyLoopConfig,
    attach_outcome_status_to_markets,
    generated_at_for_run_date,
    load_market_outcome_inputs,
    load_tracked_market_state,
    local_source_paths,
)
from pm_bot.trading_core.execution_simulator import (
    SIMULATED_EXECUTION_BATCH_CONTRACT,
    render_simulated_execution_results_markdown,
    simulate_execution_for_intent,
)
from pm_bot.trading_core.feedback_readiness import (
    build_feedback_readiness_summary,
    build_paper_outcome_recheck_queue,
    render_feedback_readiness_summary_markdown,
    render_paper_outcome_recheck_queue_markdown,
)
from pm_bot.trading_core.paper_portfolio_report import (
    build_paper_portfolio_report,
    render_paper_portfolio_report_markdown,
)
from pm_bot.trading_core.paper_position_ledger import render_paper_position_ledger_markdown
from pm_bot.trading_core.portfolio_rollforward import (
    build_paper_portfolio_rollforward,
    render_paper_portfolio_rollforward_markdown,
)
from pm_bot.trading_core.portfolio_state import build_portfolio_state, render_portfolio_state_markdown
from pm_bot.trading_core.post_execution_audit import build_post_execution_audit, render_post_execution_audit_markdown
from pm_bot.trading_core.risk_gate import (
    RISK_GATE_BATCH_CONTRACT,
    evaluate_paper_trade_intent,
    render_risk_gate_results_markdown,
)
from pm_bot.trading_core.risk_limits import default_paper_risk_limits, render_paper_risk_limits_markdown
from pm_bot.trading_core.schemas import (
    PAPER_POSITION_LEDGER_CONTRACT,
    PAPER_POSITION_RECORD_CONTRACT,
    assert_valid,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    normalize_path,
    trading_core_safety_summary,
    validate_paper_position_ledger,
    validate_paper_position_record,
    write_json,
    write_text,
)
from pm_bot.trading_core.trade_intent_candidate import (
    build_paper_trade_intent_candidates,
    render_paper_trade_intent_candidates_markdown,
)
from pm_bot.trading_core.unresolved_market_guard import (
    build_unresolved_market_report,
    reject_invented_outcomes,
)

PAPER_DAILY_LOOP_RESULT_CONTRACT = "pmbot_paper_daily_loop_result.v1"
PAPER_DAILY_DASHBOARD_CONTRACT = "pmbot_paper_daily_dashboard.v1"
PAPER_DAILY_IDEMPOTENCY_REPORT_CONTRACT = "pmbot_paper_daily_idempotency_report.v1"
PAPER_DAILY_SAFETY_SCAN_CONTRACT = "pmbot_paper_daily_safety_scan.v1"

UNSAFE_TRUE_FIELDS = {
    "allow_network",
    "allow_real_trading",
    "allow_openrouter",
    "allow_polymarket_api",
    "allow_real_orders",
    "allow_wallet",
    "allow_trading_endpoints",
    "allow_autonomous_execution",
    "real_order_allowed",
    "real_order_submitted",
    "wallet_required",
    "wallet_used",
    "private_key_used",
    "signing_used",
    "trading_endpoint_required",
    "trading_endpoint_used",
    "real_money_used",
    "autonomous_trading_enabled",
    "authenticated_endpoint_used",
    "authenticated_endpoints_used",
    "browser_automation_used",
    "openrouter_used",
    "polymarket_api_used",
    "outcome_invented",
}
UNSAFE_POSITIVE_COUNT_FIELDS = {
    "openrouter_calls_performed",
    "polymarket_api_calls_performed",
    "new_polymarket_api_calls_performed",
}


class PaperDailyLoopSafetyError(RuntimeError):
    pass


@dataclass(frozen=True)
class PaperDailyLoopResult:
    run_id: str
    run_date: str
    market_count: int
    paper_intent_count: int
    risk_allowed_count: int
    risk_blocked_count: int
    simulated_execution_count: int
    simulated_fill_count: int
    skipped_count: int
    rejected_count: int
    open_paper_position_count: int
    carried_forward_position_count: int
    total_paper_exposure_usd: float
    ledger_path: str
    portfolio_path: str
    rollforward_path: str
    outcome_recheck_queue_path: str
    feedback_readiness_path: str
    dashboard_json_path: str
    dashboard_md_path: str
    audit_path: str
    unresolved_market_count: int
    feedback_ready_count: int
    idempotency_passed: bool
    safety_ok: bool
    validation_passed: bool

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = PAPER_DAILY_LOOP_RESULT_CONTRACT
        return value


def run_paper_daily_loop(config: PaperDailyLoopConfig | None = None) -> PaperDailyLoopResult:
    active_config = config or PaperDailyLoopConfig()
    generated_at = generated_at_for_run_date(active_config.run_date)
    output_dir = Path(active_config.output_dir)
    paths = _daily_paths(output_dir)
    previous_state = _load_previous_daily_state(paths, active_config)

    practical_state = load_tracked_market_state(active_config)
    markets = list(mapping_rows(practical_state.get("market_queue", {}).get("items")))
    outcome_inputs = load_market_outcome_inputs(markets)
    tracked_markets = attach_outcome_status_to_markets(markets, outcome_inputs)
    reject_invented_outcomes(tracked_markets, outcome_inputs)
    unresolved_report = build_unresolved_market_report(tracked_markets, generated_at=generated_at)
    outcome_recheck_queue = build_paper_outcome_recheck_queue(
        tracked_markets=tracked_markets,
        outcome_inputs=outcome_inputs,
        generated_at=generated_at,
    )
    feedback_readiness = build_feedback_readiness_summary(
        tracked_markets=tracked_markets,
        outcome_inputs=outcome_inputs,
        generated_at=generated_at,
    )

    candidates = _build_daily_candidates(
        state=practical_state,
        config=active_config,
        generated_at=generated_at,
    )
    limits = _build_daily_risk_limits(active_config, generated_at=generated_at)
    risk_gate = _build_risk_gate_batch(candidates, limits, generated_at=generated_at)
    executions = _build_execution_batch(candidates, risk_gate, active_config, generated_at=generated_at)
    ledger, idempotency_report = _build_idempotent_ledger(
        execution_batch=executions,
        ledger_path=paths["ledger"],
        config=active_config,
        previous_ledger=previous_state["ledger"],
        generated_at=generated_at,
    )
    _attach_idempotency_statuses(executions, idempotency_report)
    portfolio_state = build_portfolio_state(
        ledger=ledger,
        risk_limits=limits,
        unresolved_market_count=int(feedback_readiness.get("unresolved_count", 0) or 0),
        feedback_ready_count=int(feedback_readiness.get("feedback_ready_count", 0) or 0),
        generated_at=generated_at,
    )
    rollforward_report = build_paper_portfolio_rollforward(
        previous_ledger=previous_state["ledger"],
        previous_portfolio_state=previous_state["portfolio"],
        current_ledger=ledger,
        current_portfolio_state=portfolio_state,
        idempotency_report=idempotency_report,
        run_id=active_config.run_id,
        run_date=active_config.run_date,
        generated_at=generated_at,
    )
    audit_ledger = _ledger_for_current_execution(ledger, executions, generated_at=generated_at)
    audit = build_post_execution_audit(
        candidates_batch=candidates,
        risk_gate_batch=risk_gate,
        execution_batch=executions,
        ledger=audit_ledger,
        portfolio_state=build_portfolio_state(
            ledger=audit_ledger,
            risk_limits=limits,
            unresolved_market_count=int(feedback_readiness.get("unresolved_count", 0) or 0),
            feedback_ready_count=int(feedback_readiness.get("feedback_ready_count", 0) or 0),
            generated_at=generated_at,
        ),
        generated_at=generated_at,
    )
    portfolio_report = build_paper_portfolio_report(
        ledger,
        portfolio_state,
        execution_batch=executions,
        generated_at=generated_at,
    )
    dashboard = _build_daily_dashboard(
        config=active_config,
        tracked_markets=tracked_markets,
        unresolved_report=unresolved_report,
        candidates=candidates,
        risk_gate=risk_gate,
        executions=executions,
        ledger=ledger,
        portfolio_state=portfolio_state,
        audit=audit,
        idempotency_report=idempotency_report,
        rollforward_report=rollforward_report,
        outcome_recheck_queue=outcome_recheck_queue,
        feedback_readiness=feedback_readiness,
        portfolio_report=portfolio_report,
        generated_at=generated_at,
    )
    safety_scan = _build_daily_safety_scan(
        config=active_config,
        artifacts=[
            candidates,
            limits,
            risk_gate,
            executions,
            ledger,
            portfolio_state,
            audit,
            dashboard,
            idempotency_report,
            unresolved_report,
            outcome_recheck_queue,
            feedback_readiness,
            rollforward_report,
            portfolio_report,
        ],
        generated_at=generated_at,
    )
    if not safety_scan["safety_ok"]:
        if active_config.write_artifacts:
            _write_safety_scan(paths, safety_scan)
        raise PaperDailyLoopSafetyError(f"daily paper loop safety scan failed: {safety_scan['issues']}")

    validation_passed = (
        feedback_readiness.get("outcome_resolution_invented") is False
        and audit.get("audit_passed") is True
        and idempotency_report.get("idempotency_passed") is True
        and safety_scan["safety_ok"] is True
    )
    result = PaperDailyLoopResult(
        run_id=active_config.run_id,
        run_date=active_config.run_date,
        market_count=len(tracked_markets),
        paper_intent_count=int(candidates.get("paper_intent_count", 0) or 0),
        risk_allowed_count=int(risk_gate.get("risk_allowed_count", 0) or 0),
        risk_blocked_count=int(risk_gate.get("risk_blocked_count", 0) or 0),
        simulated_execution_count=int(executions.get("simulated_execution_count", 0) or 0),
        simulated_fill_count=int(executions.get("simulated_fill_count", 0) or 0),
        skipped_count=int(executions.get("skipped_count", 0) or 0),
        rejected_count=int(executions.get("rejected_count", 0) or 0),
        open_paper_position_count=int(ledger.get("open_position_count", 0) or 0),
        carried_forward_position_count=int(rollforward_report.get("carried_forward_position_count", 0) or 0),
        total_paper_exposure_usd=float(portfolio_state.get("total_paper_exposure_usd", 0) or 0),
        ledger_path=normalize_path(paths["ledger"]) if active_config.write_artifacts else "",
        portfolio_path=normalize_path(paths["portfolio"]) if active_config.write_artifacts else "",
        rollforward_path=normalize_path(paths["rollforward"]) if active_config.write_artifacts else "",
        outcome_recheck_queue_path=normalize_path(paths["outcome_recheck"]) if active_config.write_artifacts else "",
        feedback_readiness_path=normalize_path(paths["feedback_readiness"]) if active_config.write_artifacts else "",
        dashboard_json_path=normalize_path(paths["dashboard_json"]) if active_config.write_artifacts else "",
        dashboard_md_path=normalize_path(paths["dashboard_md"]) if active_config.write_artifacts else "",
        audit_path=normalize_path(paths["audit"]) if active_config.write_artifacts else "",
        unresolved_market_count=int(feedback_readiness.get("unresolved_count", 0) or 0),
        feedback_ready_count=int(feedback_readiness.get("feedback_ready_count", 0) or 0),
        idempotency_passed=idempotency_report.get("idempotency_passed") is True,
        safety_ok=safety_scan["safety_ok"] is True,
        validation_passed=validation_passed,
    )
    if active_config.write_artifacts:
        _write_daily_artifacts(
            paths=paths,
            config=active_config,
            candidates=candidates,
            limits=limits,
            risk_gate=risk_gate,
            executions=executions,
            ledger=ledger,
            portfolio_state=portfolio_state,
            audit=audit,
            dashboard=dashboard,
            safety_scan=safety_scan,
            idempotency_report=idempotency_report,
            unresolved_report=unresolved_report,
            outcome_recheck_queue=outcome_recheck_queue,
            feedback_readiness=feedback_readiness,
            rollforward_report=rollforward_report,
            portfolio_report=portfolio_report,
            result=result,
        )
    return result


def _daily_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "config": output_dir / "paper_daily_config.json",
        "config_md": output_dir / "paper_daily_config.md",
        "intents": output_dir / "paper_daily_intents.json",
        "intents_md": output_dir / "paper_daily_intents.md",
        "risk_limits": output_dir / "paper_daily_risk_limits.json",
        "risk_limits_md": output_dir / "paper_daily_risk_limits.md",
        "risk_gate": output_dir / "paper_daily_risk_gate.json",
        "risk_gate_md": output_dir / "paper_daily_risk_gate.md",
        "executions": output_dir / "paper_daily_simulated_executions.json",
        "executions_md": output_dir / "paper_daily_simulated_executions.md",
        "ledger": output_dir / "paper_daily_ledger.json",
        "ledger_md": output_dir / "paper_daily_ledger.md",
        "portfolio": output_dir / "paper_daily_portfolio_state.json",
        "portfolio_md": output_dir / "paper_daily_portfolio_state.md",
        "rollforward": output_dir / "paper_daily_rollforward.json",
        "rollforward_md": output_dir / "paper_daily_rollforward.md",
        "audit": output_dir / "paper_daily_audit.json",
        "audit_md": output_dir / "paper_daily_audit.md",
        "dashboard_json": output_dir / "paper_daily_dashboard.json",
        "dashboard_md": output_dir / "paper_daily_dashboard.md",
        "safety": output_dir / "paper_daily_safety_scan.json",
        "idempotency": output_dir / "paper_daily_idempotency_report.json",
        "idempotency_md": output_dir / "paper_daily_idempotency_report.md",
        "unresolved": output_dir / "paper_daily_unresolved_market_report.json",
        "outcome_recheck": output_dir / "paper_daily_outcome_recheck_queue.json",
        "outcome_recheck_md": output_dir / "paper_daily_outcome_recheck_queue.md",
        "feedback_readiness": output_dir / "paper_daily_feedback_readiness.json",
        "feedback_readiness_md": output_dir / "paper_daily_feedback_readiness.md",
        "portfolio_report": output_dir / "paper_daily_portfolio_report.json",
        "portfolio_report_md": output_dir / "paper_daily_portfolio_report.md",
        "run_report_md": output_dir / "paper_daily_run_report.md",
        "result": output_dir / "paper_daily_loop_result.json",
    }


def _load_previous_daily_state(
    paths: Mapping[str, Path],
    config: PaperDailyLoopConfig,
) -> dict[str, dict[str, Any] | None]:
    ledger_path = Path(config.previous_ledger_path) if config.previous_ledger_path is not None else paths["ledger"]
    portfolio_path = (
        Path(config.previous_portfolio_path) if config.previous_portfolio_path is not None else paths["portfolio"]
    )
    previous_ledger = load_json_object(ledger_path, label="previous paper daily ledger") if ledger_path.exists() else None
    previous_portfolio = (
        load_json_object(portfolio_path, label="previous paper daily portfolio") if portfolio_path.exists() else None
    )
    return {"ledger": previous_ledger, "portfolio": previous_portfolio}


def _build_daily_candidates(
    *,
    state: Mapping[str, Any],
    config: PaperDailyLoopConfig,
    generated_at: str,
) -> dict[str, Any]:
    candidates = build_paper_trade_intent_candidates(state=state, generated_at=generated_at)
    daily_candidates = []
    for candidate in mapping_rows(candidates.get("candidates")):
        row = dict(candidate)
        row["daily_run_id"] = config.run_id
        row["run_date"] = config.run_date
        row["idempotency_key"] = _idempotency_key(config.run_date, row.get("market_id"), row.get("intent_id"))
        daily_candidates.append(row)
    result = dict(candidates)
    result["batch_id"] = f"paper-trade-intent-candidates-022-{config.run_date}"
    result["daily_run_id"] = config.run_id
    result["run_date"] = config.run_date
    result["paper_intent_count"] = len(daily_candidates)
    result["simulated_entry_count"] = len([row for row in daily_candidates if row.get("paper_action_type") == "simulated_entry"])
    result["observe_only_count"] = len([row for row in daily_candidates if row.get("paper_action_type") == "observe_only"])
    result["candidates"] = daily_candidates
    return result


def _build_daily_risk_limits(config: PaperDailyLoopConfig, *, generated_at: str) -> dict[str, Any]:
    limits = default_paper_risk_limits(generated_at=generated_at)
    limits["risk_limits_id"] = f"paper-risk-limits-022-{config.run_date}"
    limits["max_total_paper_exposure_usd"] = config.max_total_paper_exposure_usd
    limits["max_market_paper_exposure_usd"] = config.max_single_market_paper_exposure_usd
    limits["daily_run_id"] = config.run_id
    limits["run_date"] = config.run_date
    return limits


def _build_risk_gate_batch(
    candidates: Mapping[str, Any],
    limits: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    market_exposure: dict[str, float] = {}
    total_exposure = 0.0
    open_positions = 0
    results = []
    for candidate in mapping_rows(candidates.get("candidates")):
        market_id = clean_text(candidate.get("market_id"))
        result = evaluate_paper_trade_intent(
            candidate,
            limits,
            current_market_exposure_usd=market_exposure.get(market_id, 0.0),
            current_total_exposure_usd=total_exposure,
            current_open_positions=open_positions,
        )
        result["daily_run_id"] = candidates.get("daily_run_id", "")
        result["run_date"] = candidates.get("run_date", "")
        result["idempotency_key"] = clean_text(candidate.get("idempotency_key"))
        results.append(result)
        if result["allowed"] and float(candidate.get("intended_notional_usd", 0) or 0) > 0:
            notional = float(candidate.get("intended_notional_usd", 0) or 0)
            market_exposure[market_id] = round(market_exposure.get(market_id, 0.0) + notional, 2)
            total_exposure = round(total_exposure + notional, 2)
            open_positions += 1
    return {
        "contract_version": RISK_GATE_BATCH_CONTRACT,
        "batch_id": f"risk-gate-results-022-{candidates.get('run_date', '')}",
        "generated_at": generated_at,
        "daily_run_id": candidates.get("daily_run_id", ""),
        "run_date": candidates.get("run_date", ""),
        "risk_allowed_count": len([row for row in results if row["allowed"]]),
        "risk_blocked_count": len([row for row in results if row["blocked"]]),
        "results": results,
        "paper_exposure_reserved_usd": total_exposure,
        "safety_summary": trading_core_safety_summary(),
    }


def _build_execution_batch(
    candidates: Mapping[str, Any],
    risk_gate: Mapping[str, Any],
    config: PaperDailyLoopConfig,
    *,
    generated_at: str,
) -> dict[str, Any]:
    risk_by_intent = {clean_text(row.get("intent_id")): row for row in mapping_rows(risk_gate.get("results"))}
    results = []
    for candidate in mapping_rows(candidates.get("candidates")):
        risk_result = risk_by_intent[clean_text(candidate.get("intent_id"))]
        result = simulate_execution_for_intent(candidate, risk_result, generated_at=generated_at)
        result["execution_id"] = f"sim-exec-022-{_slug(candidate.get('idempotency_key'))}"
        result["daily_run_id"] = config.run_id
        result["run_date"] = config.run_date
        result["idempotency_key"] = clean_text(candidate.get("idempotency_key"))
        result["idempotency_status"] = "not_applied"
        results.append(result)
    return {
        "contract_version": SIMULATED_EXECUTION_BATCH_CONTRACT,
        "batch_id": f"simulated-execution-results-022-{config.run_date}",
        "generated_at": generated_at,
        "daily_run_id": config.run_id,
        "run_date": config.run_date,
        "simulated_execution_count": len(results),
        "simulated_fill_count": len([row for row in results if row["simulated_fill"]]),
        "skipped_count": len([row for row in results if row["execution_status"] == "skipped"]),
        "rejected_count": len([row for row in results if row["execution_status"] == "rejected"]),
        "results": results,
        "safety_summary": trading_core_safety_summary(),
    }


def _build_idempotent_ledger(
    *,
    execution_batch: Mapping[str, Any],
    ledger_path: Path,
    config: PaperDailyLoopConfig,
    previous_ledger: Mapping[str, Any] | None = None,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    existing_positions: list[Mapping[str, Any]] = []
    duplicate_existing_keys: list[str] = []
    duplicate_existing_open_keys: list[str] = []
    if previous_ledger is not None or (config.write_artifacts and ledger_path.exists()):
        existing = dict(previous_ledger or load_json_object(ledger_path, label="existing paper daily ledger"))
        seen_keys: set[str] = set()
        seen_open_keys: set[str] = set()
        for position in mapping_rows(existing.get("positions")):
            if clean_text(position.get("outcome_status") or "unresolved") != "unresolved":
                continue
            key = clean_text(position.get("idempotency_key") or position.get("source_execution_id"))
            if key in seen_keys:
                duplicate_existing_keys.append(key)
                continue
            seen_keys.add(key)
            open_key = _open_position_key(position.get("market_id"), position.get("intent_id"))
            if open_key in seen_open_keys:
                duplicate_existing_open_keys.append(open_key)
                continue
            seen_open_keys.add(open_key)
            existing_positions.append(position)

    positions_by_key = {
        clean_text(position.get("idempotency_key") or position.get("source_execution_id")): dict(position)
        for position in existing_positions
    }
    positions_by_open_key = {
        _open_position_key(position.get("market_id"), position.get("intent_id")): dict(position)
        for position in existing_positions
    }
    status_by_key: list[dict[str, Any]] = []
    new_positions = []
    already_applied = []
    already_open_positions = []
    for execution in mapping_rows(execution_batch.get("results")):
        if execution.get("simulated_fill") is not True:
            status_by_key.append(
                {
                    "idempotency_key": clean_text(execution.get("idempotency_key")),
                    "market_id": clean_text(execution.get("market_id")),
                    "status": "no_fill",
                }
            )
            continue
        key = clean_text(execution.get("idempotency_key"))
        open_key = _open_position_key(execution.get("market_id"), execution.get("intent_id"))
        if key in positions_by_key:
            already_applied.append(key)
            status_by_key.append(
                {
                    "idempotency_key": key,
                    "market_id": clean_text(execution.get("market_id")),
                    "status": "already_applied",
                }
            )
            continue
        if open_key in positions_by_open_key:
            existing_position = positions_by_open_key[open_key]
            already_open_positions.append(key)
            status_by_key.append(
                {
                    "idempotency_key": key,
                    "market_id": clean_text(execution.get("market_id")),
                    "status": "already_open_position",
                    "carried_position_id": clean_text(existing_position.get("position_id")),
                    "carried_idempotency_key": clean_text(existing_position.get("idempotency_key")),
                }
            )
            continue
        position = _paper_position_from_execution(execution, config=config, generated_at=generated_at)
        positions_by_key[key] = position
        positions_by_open_key[open_key] = position
        new_positions.append(key)
        status_by_key.append(
            {
                "idempotency_key": key,
                "market_id": clean_text(execution.get("market_id")),
                "status": "newly_applied",
            }
        )

    positions = sorted(positions_by_key.values(), key=lambda row: clean_text(row.get("position_id")))
    total_exposure = round(sum(float(row.get("paper_exposure_usd", 0) or 0) for row in positions), 2)
    ledger = {
        "contract_version": PAPER_POSITION_LEDGER_CONTRACT,
        "ledger_id": "paper-daily-ledger-022",
        "generated_at": generated_at,
        "daily_run_id": config.run_id,
        "run_date": config.run_date,
        "idempotency_mode": config.idempotency_mode,
        "positions": positions,
        "open_position_count": len(positions),
        "unresolved_position_count": len([row for row in positions if row.get("outcome_status") == "unresolved"]),
        "total_paper_exposure_usd": total_exposure,
        "paper_only": True,
        "real_positions_created": False,
        "live_prices_used": False,
        "safety_summary": trading_core_safety_summary(),
    }
    valid, errors = validate_paper_position_ledger(ledger)
    assert_valid(ledger["ledger_id"], valid, errors)
    idempotency_report = {
        "contract_version": PAPER_DAILY_IDEMPOTENCY_REPORT_CONTRACT,
        "generated_at": generated_at,
        "run_id": config.run_id,
        "run_date": config.run_date,
        "idempotency_mode": config.idempotency_mode,
        "checked_execution_count": int(execution_batch.get("simulated_execution_count", 0) or 0),
        "simulated_fill_count": int(execution_batch.get("simulated_fill_count", 0) or 0),
        "carried_forward_position_count": len(existing_positions),
        "carried_forward_position_ids": [clean_text(row.get("position_id")) for row in existing_positions],
        "new_applied_count": len(new_positions),
        "already_applied_count": len(already_applied),
        "already_open_position_count": len(already_open_positions),
        "duplicate_fill_prevented_count": len(already_applied) + len(already_open_positions),
        "duplicate_existing_key_count": len(duplicate_existing_keys),
        "duplicate_existing_keys": duplicate_existing_keys,
        "duplicate_existing_open_position_count": len(duplicate_existing_open_keys),
        "duplicate_existing_open_position_keys": duplicate_existing_open_keys,
        "status_by_key": status_by_key,
        "idempotency_passed": not duplicate_existing_keys and not duplicate_existing_open_keys,
    }
    return ledger, idempotency_report


def _paper_position_from_execution(
    execution: Mapping[str, Any],
    *,
    config: PaperDailyLoopConfig,
    generated_at: str,
) -> dict[str, Any]:
    key = clean_text(execution.get("idempotency_key"))
    record = {
        "contract_version": PAPER_POSITION_RECORD_CONTRACT,
        "position_id": f"paper-position-022-{_slug(key)}",
        "opened_at": generated_at,
        "daily_run_id": config.run_id,
        "run_date": config.run_date,
        "idempotency_key": key,
        "source_execution_id": clean_text(execution.get("execution_id")),
        "intent_id": clean_text(execution.get("intent_id")),
        "market_id": clean_text(execution.get("market_id")),
        "market_title": clean_text(execution.get("market_title")),
        "hypothesis_id": clean_text(execution.get("hypothesis_id")),
        "side_label": "track_yes",
        "side_label_meaning": "paper tracking label only; not a real market side or recommendation",
        "notional_usd": float(execution.get("filled_notional_usd", 0) or 0),
        "max_loss_usd": float(execution.get("filled_notional_usd", 0) or 0),
        "paper_fill_price_usd": execution.get("paper_fill_price_usd"),
        "paper_units": float(execution.get("paper_units", 0) or 0),
        "paper_exposure_usd": float(execution.get("filled_notional_usd", 0) or 0),
        "outcome_status": "unresolved",
        "realized_pnl_usd": None,
        "unrealized_pnl_usd": None,
        "pnl_note": "No real PnL is computed because there is no local resolved outcome and no live price.",
        "paper_only": True,
        "real_position": False,
        "live_price_used": False,
    }
    valid, errors = validate_paper_position_record(record)
    assert_valid(record["position_id"], valid, errors)
    return record


def _attach_idempotency_statuses(
    execution_batch: dict[str, Any],
    idempotency_report: Mapping[str, Any],
) -> None:
    statuses = {
        clean_text(row.get("idempotency_key")): clean_text(row.get("status"))
        for row in mapping_rows(idempotency_report.get("status_by_key"))
    }
    for execution in mapping_rows(execution_batch.get("results")):
        execution["idempotency_status"] = statuses.get(clean_text(execution.get("idempotency_key")), "not_applied")


def _ledger_for_current_execution(
    ledger: Mapping[str, Any],
    execution_batch: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    current_keys = {
        clean_text(row.get("idempotency_key"))
        for row in mapping_rows(execution_batch.get("results"))
        if row.get("simulated_fill") is True
    }
    current_open_keys = {
        _open_position_key(row.get("market_id"), row.get("intent_id"))
        for row in mapping_rows(execution_batch.get("results"))
        if row.get("simulated_fill") is True
    }
    positions = [
        dict(row)
        for row in mapping_rows(ledger.get("positions"))
        if clean_text(row.get("idempotency_key")) in current_keys
        or _open_position_key(row.get("market_id"), row.get("intent_id")) in current_open_keys
    ]
    total_exposure = round(sum(float(row.get("paper_exposure_usd", 0) or 0) for row in positions), 2)
    scoped = dict(ledger)
    scoped["ledger_id"] = f"{ledger.get('ledger_id')}-current-run"
    scoped["generated_at"] = generated_at
    scoped["positions"] = positions
    scoped["open_position_count"] = len(positions)
    scoped["unresolved_position_count"] = len([row for row in positions if row.get("outcome_status") == "unresolved"])
    scoped["total_paper_exposure_usd"] = total_exposure
    return scoped


def _build_daily_dashboard(
    *,
    config: PaperDailyLoopConfig,
    tracked_markets: Sequence[Mapping[str, Any]],
    unresolved_report: Mapping[str, Any],
    candidates: Mapping[str, Any],
    risk_gate: Mapping[str, Any],
    executions: Mapping[str, Any],
    ledger: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
    audit: Mapping[str, Any],
    idempotency_report: Mapping[str, Any],
    rollforward_report: Mapping[str, Any],
    outcome_recheck_queue: Mapping[str, Any],
    feedback_readiness: Mapping[str, Any],
    portfolio_report: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    blocked = [row for row in mapping_rows(risk_gate.get("results")) if row.get("blocked") is True]
    rejected = [row for row in mapping_rows(executions.get("results")) if row.get("execution_status") == "rejected"]
    skipped = [row for row in mapping_rows(executions.get("results")) if row.get("execution_status") == "skipped"]
    return {
        "contract_version": PAPER_DAILY_DASHBOARD_CONTRACT,
        "dashboard_id": f"paper-daily-dashboard-022-{config.run_date}",
        "generated_at": generated_at,
        "run_id": config.run_id,
        "run_date": config.run_date,
        "tracked_markets": [
            {
                "market_id": clean_text(row.get("market_id")),
                "market_title": clean_text(row.get("market_title")),
                "outcome_status": clean_text(row.get("outcome_status") or "unknown"),
                "feedback_ready": _feedback_ready_for_market(row, feedback_readiness),
                "feedback_blocked_reason": _feedback_blocked_reason_for_market(row, feedback_readiness),
            }
            for row in tracked_markets
        ],
        "counts": {
            "market_count": len(tracked_markets),
            "paper_intent_count": int(candidates.get("paper_intent_count", 0) or 0),
            "risk_allowed_count": int(risk_gate.get("risk_allowed_count", 0) or 0),
            "risk_blocked_count": int(risk_gate.get("risk_blocked_count", 0) or 0),
            "simulated_execution_count": int(executions.get("simulated_execution_count", 0) or 0),
            "simulated_fill_count": int(executions.get("simulated_fill_count", 0) or 0),
            "skipped_count": int(executions.get("skipped_count", 0) or 0),
            "rejected_count": int(executions.get("rejected_count", 0) or 0),
            "open_paper_position_count": int(ledger.get("open_position_count", 0) or 0),
            "carried_forward_position_count": int(rollforward_report.get("carried_forward_position_count", 0) or 0),
            "total_paper_exposure_usd": float(portfolio_state.get("total_paper_exposure_usd", 0) or 0),
            "unresolved_market_count": int(feedback_readiness.get("unresolved_count", 0) or 0),
            "resolved_market_count": int(feedback_readiness.get("resolved_count", 0) or 0),
            "feedback_ready_count": int(feedback_readiness.get("feedback_ready_count", 0) or 0),
        },
        "portfolio_summary": portfolio_report.get("exposure_summary", {}),
        "open_paper_positions": portfolio_report.get("open_paper_positions", []),
        "carried_forward_positions": rollforward_report.get("carried_forward_positions", []),
        "unresolved_markets": feedback_readiness.get("blocked_items", []),
        "outcome_recheck_queue": {
            "queue_id": outcome_recheck_queue.get("queue_id"),
            "needs_future_outcome_check_count": outcome_recheck_queue.get("needs_future_outcome_check_count"),
            "feedback_ready_count": outcome_recheck_queue.get("feedback_ready_count"),
            "recheck_items": outcome_recheck_queue.get("recheck_items", []),
        },
        "feedback_readiness": {
            "summary_id": feedback_readiness.get("summary_id"),
            "total_tracked_markets": feedback_readiness.get("total_tracked_markets"),
            "unresolved_count": feedback_readiness.get("unresolved_count"),
            "resolved_count": feedback_readiness.get("resolved_count"),
            "feedback_ready_count": feedback_readiness.get("feedback_ready_count"),
            "blocked_feedback_count": feedback_readiness.get("blocked_feedback_count"),
            "blocked_items": feedback_readiness.get("blocked_items", []),
        },
        "blocked_details": _daily_detail_rows(blocked),
        "rejected_details": _daily_detail_rows(rejected),
        "skipped_details": _daily_detail_rows(skipped),
        "idempotency": {
            "idempotency_mode": idempotency_report.get("idempotency_mode"),
            "new_applied_count": idempotency_report.get("new_applied_count"),
            "already_applied_count": idempotency_report.get("already_applied_count"),
            "already_open_position_count": idempotency_report.get("already_open_position_count"),
            "duplicate_fill_prevented_count": idempotency_report.get("duplicate_fill_prevented_count"),
            "carried_forward_position_count": idempotency_report.get("carried_forward_position_count"),
            "idempotency_passed": idempotency_report.get("idempotency_passed"),
        },
        "rollforward": {
            "previous_ledger_loaded": rollforward_report.get("previous_ledger_loaded"),
            "previous_portfolio_loaded": rollforward_report.get("previous_portfolio_loaded"),
            "carried_forward_position_count": rollforward_report.get("carried_forward_position_count"),
            "new_position_count": rollforward_report.get("new_position_count"),
            "current_total_paper_exposure_usd": rollforward_report.get("current_total_paper_exposure_usd"),
            "duplicate_fill_prevented_count": rollforward_report.get("duplicate_fill_prevented_count"),
        },
        "audit_status": {
            "audit_passed": audit.get("audit_passed"),
            "violation_count": len(audit.get("violations", [])),
            "warning_count": len(audit.get("warnings", [])),
        },
        "safety_flags": _daily_safety_flags(),
        "next_operator_actions": [
            "Review carried-forward open paper positions and exposure before the next local paper run.",
            "Recheck unresolved markets only against saved local outcome artifacts.",
            "Prepare feedback records only for markets with explicit local resolution evidence.",
            "Keep this as an explicit one-shot local command, not a scheduler or autonomous loop.",
        ],
        "next_operator_action": "Review rollforward, unresolved outcome queue, and feedback readiness artifacts.",
        "paper_only": True,
        "source_paths": local_source_paths(),
    }


def _daily_detail_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    details = []
    for row in rows:
        details.append(
            {
                "market_id": clean_text(row.get("market_id")),
                "intent_id": clean_text(row.get("intent_id")),
                "status": clean_text(row.get("risk_gate_status") or row.get("execution_status")),
                "reason": clean_text(row.get("execution_reason")),
                "block_reasons": [clean_text(item) for item in row.get("block_reasons", [])],
                "warnings": [clean_text(item) for item in row.get("warnings", [])],
            }
        )
    return details


def _feedback_ready_for_market(market: Mapping[str, Any], feedback_readiness: Mapping[str, Any]) -> bool:
    market_id = clean_text(market.get("market_id"))
    ready_ids = {clean_text(row.get("market_id")) for row in mapping_rows(feedback_readiness.get("ready_items"))}
    return market_id in ready_ids


def _feedback_blocked_reason_for_market(market: Mapping[str, Any], feedback_readiness: Mapping[str, Any]) -> str:
    market_id = clean_text(market.get("market_id"))
    for row in mapping_rows(feedback_readiness.get("blocked_items")):
        if clean_text(row.get("market_id")) == market_id:
            return clean_text(row.get("feedback_blocked_reason"))
    return ""


def _build_daily_safety_scan(
    *,
    config: PaperDailyLoopConfig,
    artifacts: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    for path, key, value in _walk_flags(config.to_dict()):
        if key in UNSAFE_TRUE_FIELDS and value is True:
            issues.append(_safety_issue(path, key, value))
    for index, artifact in enumerate(artifacts):
        for path, key, value in _walk_flags(artifact, path=f"$artifacts[{index}]"):
            if key in UNSAFE_TRUE_FIELDS and value is True:
                issues.append(_safety_issue(path, key, value))
            if key in UNSAFE_POSITIVE_COUNT_FIELDS and isinstance(value, int) and value > 0:
                issues.append(_safety_issue(path, key, value))
    return {
        "contract_version": PAPER_DAILY_SAFETY_SCAN_CONTRACT,
        "generated_at": generated_at,
        "run_id": config.run_id,
        "run_date": config.run_date,
        "issue_count": len(issues),
        "issues": issues,
        "safety_ok": not issues,
        "safety_flags": _daily_safety_flags(),
    }


def _daily_safety_flags() -> dict[str, bool]:
    return {
        "real_order_submitted": False,
        "wallet_used": False,
        "private_key_used": False,
        "signing_used": False,
        "trading_endpoint_used": False,
        "real_money_used": False,
        "autonomous_trading_enabled": False,
        "authenticated_endpoint_used": False,
        "browser_automation_used": False,
        "openrouter_used": False,
        "polymarket_api_used": False,
        "outcome_invented": False,
    }


def _walk_flags(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            rows.append((path, str(key), nested))
            rows.extend(_walk_flags(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_flags(nested, f"{path}[{index}]"))
    return rows


def _safety_issue(path: str, key: str, value: Any) -> dict[str, str]:
    return {"path": path, "field": key, "value": repr(value), "issue_type": "unsafe_daily_loop_flag"}


def _write_daily_artifacts(
    *,
    paths: Mapping[str, Path],
    config: PaperDailyLoopConfig,
    candidates: Mapping[str, Any],
    limits: Mapping[str, Any],
    risk_gate: Mapping[str, Any],
    executions: Mapping[str, Any],
    ledger: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
    audit: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    idempotency_report: Mapping[str, Any],
    unresolved_report: Mapping[str, Any],
    outcome_recheck_queue: Mapping[str, Any],
    feedback_readiness: Mapping[str, Any],
    rollforward_report: Mapping[str, Any],
    portfolio_report: Mapping[str, Any],
    result: PaperDailyLoopResult,
) -> None:
    write_json(paths["config"], config.to_dict())
    write_text(paths["config_md"], _render_config_markdown(config))
    write_json(paths["intents"], candidates)
    write_text(paths["intents_md"], render_paper_trade_intent_candidates_markdown(candidates))
    write_json(paths["risk_limits"], limits)
    write_text(paths["risk_limits_md"], render_paper_risk_limits_markdown(limits))
    write_json(paths["risk_gate"], risk_gate)
    write_text(paths["risk_gate_md"], render_risk_gate_results_markdown(risk_gate))
    write_json(paths["executions"], executions)
    write_text(paths["executions_md"], render_simulated_execution_results_markdown(executions))
    write_json(paths["ledger"], ledger)
    write_text(paths["ledger_md"], render_paper_position_ledger_markdown(ledger))
    write_json(paths["portfolio"], portfolio_state)
    write_text(paths["portfolio_md"], render_portfolio_state_markdown(portfolio_state))
    write_json(paths["rollforward"], rollforward_report)
    write_text(paths["rollforward_md"], render_paper_portfolio_rollforward_markdown(rollforward_report))
    write_json(paths["audit"], audit)
    write_text(paths["audit_md"], render_post_execution_audit_markdown(audit))
    write_json(paths["dashboard_json"], dashboard)
    write_text(paths["dashboard_md"], _render_daily_dashboard_markdown(dashboard))
    _write_safety_scan(paths, safety_scan)
    write_json(paths["idempotency"], idempotency_report)
    write_text(paths["idempotency_md"], _render_idempotency_markdown(idempotency_report))
    write_json(paths["unresolved"], unresolved_report)
    write_json(paths["outcome_recheck"], outcome_recheck_queue)
    write_text(paths["outcome_recheck_md"], render_paper_outcome_recheck_queue_markdown(outcome_recheck_queue))
    write_json(paths["feedback_readiness"], feedback_readiness)
    write_text(paths["feedback_readiness_md"], render_feedback_readiness_summary_markdown(feedback_readiness))
    write_json(paths["portfolio_report"], portfolio_report)
    write_text(paths["portfolio_report_md"], render_paper_portfolio_report_markdown(portfolio_report))
    write_text(paths["run_report_md"], _render_daily_run_report(result.to_dict(), dashboard, safety_scan))
    write_json(paths["result"], result.to_dict())


def _write_safety_scan(paths: Mapping[str, Path], safety_scan: Mapping[str, Any]) -> None:
    write_json(paths["safety"], safety_scan)


def _render_config_markdown(config: PaperDailyLoopConfig) -> str:
    rows = [
        f"run_id: `{config.run_id}`",
        f"run_date: `{config.run_date}`",
        f"max_markets: `{config.max_markets}`",
        f"output_dir: `{normalize_path(config.output_dir)}`",
        f"previous_ledger_path: `{normalize_path(config.previous_ledger_path) if config.previous_ledger_path else ''}`",
        f"previous_portfolio_path: `{normalize_path(config.previous_portfolio_path) if config.previous_portfolio_path else ''}`",
        f"allow_network: `{str(config.allow_network).lower()}`",
        f"allow_real_trading: `{str(config.allow_real_trading).lower()}`",
        f"allow_openrouter: `{str(config.allow_openrouter).lower()}`",
        f"allow_polymarket_api: `{str(config.allow_polymarket_api).lower()}`",
        f"idempotency_mode: `{config.idempotency_mode}`",
        f"write_artifacts: `{str(config.write_artifacts).lower()}`",
    ]
    return "\n".join(["# PMBOT Paper Daily Loop Config", "", *bullet_lines(rows)]) + "\n"


def _render_daily_dashboard_markdown(dashboard: Mapping[str, Any]) -> str:
    counts = dict(dashboard.get("counts", {}))
    lines = [
        "# PMBOT Paper Daily Dashboard",
        "",
        f"- Run ID: `{dashboard.get('run_id')}`",
        f"- Run date: `{dashboard.get('run_date')}`",
        f"- Tracked markets: {counts.get('market_count')}",
        f"- Unresolved markets: {counts.get('unresolved_market_count')}",
        f"- Feedback ready: {counts.get('feedback_ready_count')}",
        f"- Paper intents: {counts.get('paper_intent_count')}",
        f"- Risk allowed: {counts.get('risk_allowed_count')}",
        f"- Risk blocked: {counts.get('risk_blocked_count')}",
        f"- Simulated executions: {counts.get('simulated_execution_count')}",
        f"- Simulated fills: {counts.get('simulated_fill_count')}",
        f"- Open paper positions: {counts.get('open_paper_position_count')}",
        f"- Carried-forward positions: {counts.get('carried_forward_position_count')}",
        f"- Total paper exposure: `${counts.get('total_paper_exposure_usd')}`",
        "",
        "## Tracked Markets",
        "",
    ]
    for market in dashboard.get("tracked_markets", []):
        lines.append(f"- `{market.get('market_id')}` `{market.get('outcome_status')}` - {market.get('market_title')}")
    lines.extend(["", "## Open Paper Positions", ""])
    lines.extend(
        bullet_lines(
            f"`{row.get('market_id')}` `${row.get('paper_exposure_usd')}` `{row.get('outcome_status')}`"
            for row in mapping_rows(dashboard.get("open_paper_positions"))
        )
    )
    lines.extend(["", "## Carried-Forward Positions", ""])
    lines.extend(
        bullet_lines(
            f"`{row.get('market_id')}` `${row.get('paper_exposure_usd')}` `{row.get('outcome_status')}`"
            for row in mapping_rows(dashboard.get("carried_forward_positions"))
        )
    )
    lines.extend(["", "## Feedback Readiness", ""])
    readiness = dict(dashboard.get("feedback_readiness", {}))
    lines.extend(
        bullet_lines(
            [
                f"total_tracked_markets: `{readiness.get('total_tracked_markets')}`",
                f"unresolved_count: `{readiness.get('unresolved_count')}`",
                f"resolved_count: `{readiness.get('resolved_count')}`",
                f"feedback_ready_count: `{readiness.get('feedback_ready_count')}`",
                f"blocked_feedback_count: `{readiness.get('blocked_feedback_count')}`",
            ]
        )
    )
    lines.extend(
        [
            "",
            "## Blocked, Rejected, Skipped",
            "",
            f"- Blocked: {len(dashboard.get('blocked_details', []))}",
            f"- Rejected: {len(dashboard.get('rejected_details', []))}",
            f"- Skipped: {len(dashboard.get('skipped_details', []))}",
            "",
            "## Idempotency",
            "",
            *bullet_lines(f"{key}: `{value}`" for key, value in dict(dashboard.get("idempotency", {})).items()),
            "",
            "## Safety Flags",
            "",
            *bullet_lines(f"{key}: `{str(value).lower()}`" for key, value in dict(dashboard.get("safety_flags", {})).items()),
            "",
            "## Next Operator Action",
            "",
            *bullet_lines(str(item) for item in dashboard.get("next_operator_actions", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def _render_idempotency_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Daily Idempotency Report",
        "",
        f"- Run ID: `{report.get('run_id')}`",
        f"- Run date: `{report.get('run_date')}`",
        f"- Carried-forward positions: {report.get('carried_forward_position_count')}",
        f"- New applied fills: {report.get('new_applied_count')}",
        f"- Already applied fills: {report.get('already_applied_count')}",
        f"- Already open positions: {report.get('already_open_position_count')}",
        f"- Duplicate fills prevented: {report.get('duplicate_fill_prevented_count')}",
        f"- Idempotency passed: `{str(report.get('idempotency_passed')).lower()}`",
        "",
        "## Status by Key",
        "",
    ]
    lines.extend(
        bullet_lines(
            f"`{row.get('idempotency_key')}` `{row.get('status')}`"
            for row in mapping_rows(report.get("status_by_key"))
        )
    )
    return "\n".join(lines) + "\n"


def _render_daily_run_report(
    result: Mapping[str, Any],
    dashboard: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# PMBOT Paper Daily Loop Run Report",
            "",
            f"- Run ID: `{result.get('run_id')}`",
            f"- Run date: `{result.get('run_date')}`",
            f"- Validation passed: `{str(result.get('validation_passed')).lower()}`",
            f"- Safety OK: `{str(result.get('safety_ok')).lower()}`",
            f"- Dashboard: `{result.get('dashboard_json_path')}`",
            f"- Ledger: `{result.get('ledger_path')}`",
            f"- Portfolio: `{result.get('portfolio_path')}`",
            f"- Safety issues: {safety_scan.get('issue_count')}",
            "",
            "## Next Operator Action",
            "",
            f"- {dashboard.get('next_operator_action')}",
        ]
    ) + "\n"


def _idempotency_key(run_date: str, market_id: Any, intent_id: Any) -> str:
    return ":".join([clean_text(run_date), clean_text(market_id), clean_text(intent_id)])


def _open_position_key(market_id: Any, intent_id: Any) -> str:
    return ":".join([clean_text(market_id), clean_text(intent_id)])


def _slug(value: Any) -> str:
    clean = clean_text(value).replace(":", "-").replace("/", "-").replace("\\", "-")
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in clean)
