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
from pm_bot.source_quality.public_evidence_refresh import (
    build_public_evidence_refresh_artifacts,
    build_public_evidence_refresh_request_from_candidates,
    render_pending_approval_packet,
    render_public_evidence_refresh_report,
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
from pm_bot.trading_core.live_canary_readiness import (
    build_canary_dashboard_summary,
    build_canary_dry_run_acceptance_receipt,
    build_canary_operator_approval_record,
    build_canary_readiness_packet,
    render_canary_dry_run_receipt_markdown,
    render_canary_operator_approval_markdown,
    render_canary_readiness_packet_markdown,
    select_canary_market_id,
)
from pm_bot.trading_core.live_canary_replay_acceptance import (
    build_canary_governance_summary,
    build_live_connector_blocker_matrix,
)
from pm_bot.trading_core.live_connector_audit_replay import (
    build_live_connector_audit_replay,
    render_live_connector_audit_replay_markdown,
)
from pm_bot.trading_core.operator_live_approval_packet import (
    build_operator_live_approval_packet,
    render_operator_live_approval_packet_markdown,
)
from pm_bot.trading_core.real_wallet_connector_disabled_adapter import (
    DisabledRealWalletConnectorConfig,
    RealWalletConnectorDisabledAdapter,
    build_disabled_connector_passive_status,
    build_disabled_connector_request,
    render_disabled_connector_audit_record_markdown,
)
from pm_bot.trading_core.paper_portfolio_report import (
    build_paper_portfolio_report,
    render_paper_portfolio_report_markdown,
)
from pm_bot.trading_core.paper_strategy_evaluation import (
    build_paper_strategy_evaluation_ledger,
    build_paper_strategy_evaluation_summary,
    render_paper_strategy_evaluation_ledger_markdown,
    render_paper_strategy_evaluation_summary_markdown,
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
from pm_bot.trading_core.risk_engine import (
    build_risk_decision_ledger,
    render_risk_decision_ledger_markdown,
)
from pm_bot.trading_core.risk_limits import default_paper_risk_limits, render_paper_risk_limits_markdown
from pm_bot.trading_core.risk_prep_config import (
    build_default_future_risk_engine_config,
    render_future_risk_engine_config_markdown,
)
from pm_bot.trading_core.signing_simulator import (
    build_dry_run_execution_receipt_ledger,
    render_dry_run_execution_receipt_ledger_markdown,
)
from pm_bot.trading_core.wallet_execution_boundary import (
    build_wallet_boundary_audit_ledger,
    render_wallet_boundary_audit_ledger_markdown,
)
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
    "authenticated_endpoint_called",
    "authenticated_endpoint_call_performed",
    "browser_automation_used",
    "network_used",
    "external_api_calls_performed",
    "external_api_call_performed",
    "openrouter_used",
    "polymarket_api_used",
    "live_execution_allowed",
    "live_execution_enabled",
    "live_execution_performed",
    "real_signature_created",
    "real_wallet_access_performed",
    "cryptographic_signing_performed",
    "real_order_placement_performed",
    "real_wallet_used",
    "outcome_invented",
    "outcome_resolution_invented",
    "pnl_invented",
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
    strategy_ledger_path: str
    strategy_summary_path: str
    source_evidence_refresh_path: str
    source_evidence_quality_ledger_path: str
    source_evidence_pending_approval_path: str
    risk_decision_ledger_path: str
    risk_prep_config_path: str
    wallet_boundary_audit_ledger_path: str
    dry_run_receipt_ledger_path: str
    canary_operator_approval_record_path: str
    canary_readiness_packet_path: str
    canary_dry_run_receipt_path: str
    live_connector_audit_replay_path: str
    operator_live_approval_packet_path: str
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
    source_evidence_refresh_request = build_public_evidence_refresh_request_from_candidates(
        candidates_batch=candidates,
        tracked_markets=tracked_markets,
        generated_at=generated_at,
    )
    source_evidence_refresh_artifacts = build_public_evidence_refresh_artifacts(source_evidence_refresh_request)
    source_evidence_refresh_ledger = source_evidence_refresh_artifacts["ledger"]
    source_evidence_quality_ledger = source_evidence_refresh_artifacts["quality_ledger"]
    source_evidence_pending_approval = source_evidence_refresh_artifacts["pending_approval_packet"]
    risk_prep_config = build_default_future_risk_engine_config(generated_at=generated_at)
    risk_decision_ledger = build_risk_decision_ledger(
        candidates_batch=candidates,
        risk_config=risk_prep_config,
        source_evidence_refresh_ledger=source_evidence_refresh_ledger,
        generated_at=generated_at,
    )
    wallet_boundary_audit_ledger = build_wallet_boundary_audit_ledger(
        candidates_batch=candidates,
        risk_decision_ledger=risk_decision_ledger,
        risk_config=risk_prep_config,
        generated_at=generated_at,
    )
    dry_run_receipt_ledger = build_dry_run_execution_receipt_ledger(
        wallet_boundary_audit_ledger=wallet_boundary_audit_ledger,
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
    strategy_ledger = build_paper_strategy_evaluation_ledger(
        candidates_batch=candidates,
        risk_gate_batch=risk_gate,
        execution_batch=executions,
        position_ledger=ledger,
        portfolio_state=portfolio_state,
        feedback_readiness=feedback_readiness,
        source_evidence_refresh_ledger=source_evidence_refresh_ledger,
        risk_decision_ledger=risk_decision_ledger,
        dry_run_receipt_ledger=dry_run_receipt_ledger,
        generated_at=generated_at,
    )
    strategy_summary = build_paper_strategy_evaluation_summary(
        strategy_ledger=strategy_ledger,
        feedback_readiness=feedback_readiness,
        portfolio_state=portfolio_state,
        generated_at=generated_at,
    )
    canary_market_id = select_canary_market_id(
        paper_strategy_ledger=strategy_ledger,
        risk_decision_ledger=risk_decision_ledger,
        wallet_boundary_audit_ledger=wallet_boundary_audit_ledger,
        source_evidence_status=source_evidence_refresh_ledger,
    )
    canary_operator_approval_record = build_canary_operator_approval_record(
        run_id=active_config.run_id,
        market_id=canary_market_id,
        approval_status="not_requested",
        generated_at=generated_at,
    )
    canary_readiness_packet = build_canary_readiness_packet(
        paper_strategy_ledger=strategy_ledger,
        source_evidence_status=source_evidence_refresh_ledger,
        risk_decision_ledger=risk_decision_ledger,
        wallet_boundary_audit_ledger=wallet_boundary_audit_ledger,
        signing_simulator_receipt_ledger=dry_run_receipt_ledger,
        operator_approval_record=canary_operator_approval_record,
        run_context={
            "run_id": active_config.run_id,
            "run_date": active_config.run_date,
            "tracked_markets": tracked_markets,
        },
        canary_market_id=canary_market_id,
        generated_at=generated_at,
    )
    canary_dry_run_receipt = build_canary_dry_run_acceptance_receipt(
        canary_readiness_packet,
        generated_at=generated_at,
    )
    disabled_connector_config = DisabledRealWalletConnectorConfig(
        require_canary_readiness_packet_reference=True,
        require_replay_acceptance_reference=True,
    )
    disabled_connector_request = build_disabled_connector_request(
        run_id=active_config.run_id,
        market_id=canary_market_id,
        risk_decision_reference=canary_readiness_packet.get("risk_decision_id", ""),
        wallet_boundary_packet_reference=canary_readiness_packet.get("wallet_boundary_packet_id", ""),
        canary_readiness_packet_reference=canary_readiness_packet.get("canary_id", ""),
        replay_acceptance_reference=canary_dry_run_receipt.get("receipt_id", ""),
        dry_run_only=True,
    )
    disabled_connector_adapter = RealWalletConnectorDisabledAdapter(disabled_connector_config)
    disabled_connector_result = disabled_connector_adapter.build_blocked_result(
        disabled_connector_request,
        generated_at=generated_at,
    )
    disabled_connector_audit = disabled_connector_adapter.build_audit_record(
        disabled_connector_request,
        generated_at=generated_at,
    )
    live_connector_blocker_matrix = build_live_connector_blocker_matrix(generated_at=generated_at)
    live_connector_audit_replay = build_live_connector_audit_replay(
        disabled_connector_audit_records=[disabled_connector_audit],
        canary_readiness_packet_references=[canary_readiness_packet.get("canary_id", "")],
        canary_replay_acceptance_references=[canary_dry_run_receipt.get("receipt_id", "")],
        wallet_boundary_packet_references=[canary_readiness_packet.get("wallet_boundary_packet_id", "")],
        risk_decision_references=[canary_readiness_packet.get("risk_decision_id", "")],
        secret_boundary_validation_summaries=[
            disabled_connector_audit.get("audit_secret_boundary_validation", {}),
            disabled_connector_result.get("validation", {}).get("request_secret_boundary_validation", {}),
            disabled_connector_result.get("validation", {}).get("config_secret_boundary_validation", {}),
        ],
        dry_run_receipt_references=[canary_dry_run_receipt.get("receipt_id", "")],
        live_connector_blocker_matrix=live_connector_blocker_matrix,
        generated_at=generated_at,
    )
    operator_live_approval_packet = build_operator_live_approval_packet(
        audit_replay_result=live_connector_audit_replay,
        disabled_connector_status=build_disabled_connector_passive_status(
            result=disabled_connector_result,
            latest_disabled_connector_audit_path=(
                normalize_path(paths["disabled_connector_audit"]) if active_config.write_artifacts else ""
            ),
            live_canary_replay_acceptance_status="passed",
        ),
        blocker_matrix=live_connector_blocker_matrix,
        dry_run_receipt_references=[canary_dry_run_receipt.get("receipt_id", "")],
        canary_readiness_references=[canary_readiness_packet.get("canary_id", "")],
        canary_replay_acceptance_references=[canary_dry_run_receipt.get("receipt_id", "")],
        wallet_boundary_references=[canary_readiness_packet.get("wallet_boundary_packet_id", "")],
        risk_decision_references=[canary_readiness_packet.get("risk_decision_id", "")],
        latest_audit_replay_path=(
            normalize_path(paths["live_connector_audit_replay"]) if active_config.write_artifacts else ""
        ),
        generated_at=generated_at,
    )
    strategy_ledger["live_connector_audit_replay_status"] = live_connector_audit_replay.get("status")
    strategy_ledger["operator_review_packet_status"] = operator_live_approval_packet.get("operator_packet_status")
    strategy_ledger["live_execution_approved"] = False
    strategy_ledger["real_execution_available"] = False
    strategy_summary["live_connector_audit_replay_status"] = live_connector_audit_replay.get("status")
    strategy_summary["operator_review_packet_status"] = operator_live_approval_packet.get("operator_packet_status")
    strategy_summary["live_execution_approved"] = False
    strategy_summary["real_execution_available"] = False
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
        strategy_ledger=strategy_ledger,
        strategy_summary=strategy_summary,
        risk_decision_ledger=risk_decision_ledger,
        risk_prep_config=risk_prep_config,
        wallet_boundary_audit_ledger=wallet_boundary_audit_ledger,
        dry_run_receipt_ledger=dry_run_receipt_ledger,
        canary_readiness_packet=canary_readiness_packet,
        canary_dry_run_receipt=canary_dry_run_receipt,
        disabled_connector_result=disabled_connector_result,
        disabled_connector_audit=disabled_connector_audit,
        live_connector_audit_replay=live_connector_audit_replay,
        operator_live_approval_packet=operator_live_approval_packet,
        live_connector_blocker_matrix=live_connector_blocker_matrix,
        latest_disabled_connector_audit_path=(
            normalize_path(paths["disabled_connector_audit"]) if active_config.write_artifacts else ""
        ),
        latest_audit_replay_path=(
            normalize_path(paths["live_connector_audit_replay"]) if active_config.write_artifacts else ""
        ),
        latest_operator_packet_path=(
            normalize_path(paths["operator_live_approval_packet"]) if active_config.write_artifacts else ""
        ),
        source_evidence_refresh_ledger=source_evidence_refresh_ledger,
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
            source_evidence_refresh_request,
            source_evidence_refresh_ledger,
            source_evidence_quality_ledger,
            rollforward_report,
            portfolio_report,
            strategy_ledger,
            strategy_summary,
            risk_decision_ledger,
            risk_prep_config,
            wallet_boundary_audit_ledger,
            dry_run_receipt_ledger,
            canary_operator_approval_record,
            canary_readiness_packet,
            canary_dry_run_receipt,
            disabled_connector_result,
            disabled_connector_audit,
            live_connector_audit_replay,
            operator_live_approval_packet,
            live_connector_blocker_matrix,
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
        and strategy_summary.get("unresolved_pnl_not_invented") is True
        and source_evidence_refresh_ledger.get("network_used") is False
        and source_evidence_refresh_ledger.get("external_api_calls_performed") is False
        and risk_decision_ledger.get("network_used") is False
        and risk_decision_ledger.get("external_api_calls_performed") is False
        and risk_decision_ledger.get("outcome_resolution_invented") is False
        and risk_decision_ledger.get("pnl_invented") is False
        and risk_prep_config.get("validation", {}).get("valid") is True
        and wallet_boundary_audit_ledger.get("external_api_calls_performed") is False
        and wallet_boundary_audit_ledger.get("outcome_resolution_invented") is False
        and wallet_boundary_audit_ledger.get("pnl_invented") is False
        and wallet_boundary_audit_ledger.get("applied_to_paper_execution") is False
        and wallet_boundary_audit_ledger.get("applied_to_real_execution") is False
        and dry_run_receipt_ledger.get("external_api_calls_performed") is False
        and dry_run_receipt_ledger.get("network_used") is False
        and dry_run_receipt_ledger.get("wallet_used") is False
        and dry_run_receipt_ledger.get("signing_used") is False
        and dry_run_receipt_ledger.get("real_signing_performed") is False
        and dry_run_receipt_ledger.get("real_order_submitted") is False
        and dry_run_receipt_ledger.get("authenticated_endpoint_used") is False
        and dry_run_receipt_ledger.get("outcome_resolution_invented") is False
        and dry_run_receipt_ledger.get("pnl_invented") is False
        and dry_run_receipt_ledger.get("applied_to_paper_execution") is False
        and dry_run_receipt_ledger.get("applied_to_real_execution") is False
        and canary_readiness_packet.get("external_api_call_performed") is False
        and canary_readiness_packet.get("real_wallet_used") is False
        and canary_readiness_packet.get("private_key_used") is False
        and canary_readiness_packet.get("real_signature_created") is False
        and canary_readiness_packet.get("real_order_submitted") is False
        and canary_readiness_packet.get("authenticated_endpoint_called") is False
        and canary_readiness_packet.get("live_execution_performed") is False
        and canary_readiness_packet.get("outcome_resolution_invented") is False
        and canary_readiness_packet.get("pnl_invented") is False
        and canary_dry_run_receipt.get("external_api_call_performed") is False
        and canary_dry_run_receipt.get("real_wallet_used") is False
        and canary_dry_run_receipt.get("private_key_used") is False
        and canary_dry_run_receipt.get("real_signature_created") is False
        and canary_dry_run_receipt.get("real_order_submitted") is False
        and canary_dry_run_receipt.get("authenticated_endpoint_called") is False
        and canary_dry_run_receipt.get("live_execution_performed") is False
        and canary_dry_run_receipt.get("outcome_resolution_invented") is False
        and canary_dry_run_receipt.get("pnl_invented") is False
        and disabled_connector_result.get("real_execution_available") is False
        and disabled_connector_result.get("execution_refused") is True
        and disabled_connector_result.get("external_api_calls_performed") is False
        and disabled_connector_result.get("environment_secrets_read") is False
        and disabled_connector_result.get("secrets_read") is False
        and disabled_connector_result.get("real_wallet_access_performed") is False
        and disabled_connector_result.get("cryptographic_signing_performed") is False
        and disabled_connector_result.get("real_order_placement_performed") is False
        and disabled_connector_result.get("authenticated_endpoint_call_performed") is False
        and disabled_connector_audit.get("audit_valid") is True
        and disabled_connector_audit.get("real_execution_available") is False
        and disabled_connector_audit.get("external_api_calls_performed") is False
        and disabled_connector_audit.get("environment_secrets_read") is False
        and live_connector_audit_replay.get("status") == "replay_passed"
        and live_connector_audit_replay.get("real_execution_available") is False
        and live_connector_audit_replay.get("live_execution_approved") is False
        and live_connector_audit_replay.get("external_api_calls_performed") is False
        and operator_live_approval_packet.get("operator_packet_status") == "operator_review_ready"
        and operator_live_approval_packet.get("operator_review_ready") is True
        and operator_live_approval_packet.get("live_execution_approved") is False
        and operator_live_approval_packet.get("real_execution_available") is False
        and operator_live_approval_packet.get("live_connector_enabled") is False
        and dashboard.get("live_canary_readiness_summary", {}).get("canary_replay_passed") is True
        and dashboard.get("live_canary_readiness_summary", {}).get("acceptance_matrix_passed") is True
        and int(dashboard.get("live_canary_readiness_summary", {}).get("live_connector_blocker_count", 0) or 0) >= 10
        and dashboard.get("disabled_real_connector_summary", {}).get("connector_status") == "disabled"
        and dashboard.get("disabled_real_connector_summary", {}).get("real_execution_available") is False
        and dashboard.get("disabled_real_connector_summary", {}).get("secrets_present") == "not_inspected"
        and dashboard.get("disabled_real_connector_summary", {}).get("secret_boundary_status") == "static_policy_only"
        and dashboard.get("live_connector_audit_operator_summary", {}).get("audit_replay_status") == "replay_passed"
        and dashboard.get("live_connector_audit_operator_summary", {}).get("operator_review_ready") is True
        and dashboard.get("live_connector_audit_operator_summary", {}).get("live_execution_approved") is False
        and dashboard.get("live_connector_audit_operator_summary", {}).get("real_execution_available") is False
        and dashboard.get("live_canary_readiness_summary", {}).get("dry_run_only_assertion")
        == "This checklist does not make live execution available."
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
        strategy_ledger_path=normalize_path(paths["strategy_ledger"]) if active_config.write_artifacts else "",
        strategy_summary_path=normalize_path(paths["strategy_summary"]) if active_config.write_artifacts else "",
        source_evidence_refresh_path=normalize_path(paths["source_evidence_refresh"]) if active_config.write_artifacts else "",
        source_evidence_quality_ledger_path=normalize_path(paths["source_evidence_quality"]) if active_config.write_artifacts else "",
        source_evidence_pending_approval_path=(
            normalize_path(paths["source_evidence_pending_approval"])
            if active_config.write_artifacts and source_evidence_pending_approval is not None
            else ""
        ),
        risk_decision_ledger_path=normalize_path(paths["risk_decision_ledger"]) if active_config.write_artifacts else "",
        risk_prep_config_path=normalize_path(paths["risk_prep_config"]) if active_config.write_artifacts else "",
        wallet_boundary_audit_ledger_path=(
            normalize_path(paths["wallet_boundary_audit_ledger"]) if active_config.write_artifacts else ""
        ),
        dry_run_receipt_ledger_path=(
            normalize_path(paths["dry_run_receipts"]) if active_config.write_artifacts else ""
        ),
        canary_operator_approval_record_path=(
            normalize_path(paths["canary_operator_approval"]) if active_config.write_artifacts else ""
        ),
        canary_readiness_packet_path=(
            normalize_path(paths["canary_readiness_packet"]) if active_config.write_artifacts else ""
        ),
        canary_dry_run_receipt_path=(
            normalize_path(paths["canary_dry_run_receipt"]) if active_config.write_artifacts else ""
        ),
        live_connector_audit_replay_path=(
            normalize_path(paths["live_connector_audit_replay"]) if active_config.write_artifacts else ""
        ),
        operator_live_approval_packet_path=(
            normalize_path(paths["operator_live_approval_packet"]) if active_config.write_artifacts else ""
        ),
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
            source_evidence_refresh_request=source_evidence_refresh_request,
            source_evidence_refresh_ledger=source_evidence_refresh_ledger,
            source_evidence_quality_ledger=source_evidence_quality_ledger,
            source_evidence_pending_approval=source_evidence_pending_approval,
            rollforward_report=rollforward_report,
            portfolio_report=portfolio_report,
            strategy_ledger=strategy_ledger,
            strategy_summary=strategy_summary,
            risk_decision_ledger=risk_decision_ledger,
            risk_prep_config=risk_prep_config,
            wallet_boundary_audit_ledger=wallet_boundary_audit_ledger,
            dry_run_receipt_ledger=dry_run_receipt_ledger,
            canary_operator_approval_record=canary_operator_approval_record,
            canary_readiness_packet=canary_readiness_packet,
            canary_dry_run_receipt=canary_dry_run_receipt,
            disabled_connector_audit=disabled_connector_audit,
            live_connector_audit_replay=live_connector_audit_replay,
            operator_live_approval_packet=operator_live_approval_packet,
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
        "strategy_ledger": output_dir / "paper_strategy_evaluation_ledger.json",
        "strategy_ledger_md": output_dir / "paper_strategy_evaluation_ledger.md",
        "strategy_summary": output_dir / "paper_strategy_evaluation_summary.json",
        "strategy_summary_md": output_dir / "paper_strategy_evaluation_summary.md",
        "source_evidence_refresh_request": output_dir / "public_evidence_refresh_request.json",
        "source_evidence_refresh": output_dir / "public_evidence_refresh_ledger.json",
        "source_evidence_refresh_md": output_dir / "public_evidence_refresh_report.md",
        "source_evidence_quality": output_dir / "public_evidence_quality_ledger.json",
        "source_evidence_pending_approval": output_dir / "public_evidence_refresh_pending_approval_packet.json",
        "source_evidence_pending_approval_md": output_dir / "public_evidence_refresh_pending_approval_packet.md",
        "risk_decision_ledger": output_dir / "risk_engine_decision_ledger.json",
        "risk_decision_ledger_md": output_dir / "risk_engine_decision_ledger.md",
        "risk_prep_config": output_dir / "future_risk_engine_config.json",
        "risk_prep_config_md": output_dir / "future_risk_engine_config.md",
        "wallet_boundary_audit_ledger": output_dir / "wallet_boundary_audit_ledger.json",
        "wallet_boundary_audit_ledger_md": output_dir / "wallet_boundary_audit_ledger.md",
        "dry_run_receipts": output_dir / "dry_run_execution_receipts.json",
        "dry_run_receipts_md": output_dir / "dry_run_execution_receipts.md",
        "canary_operator_approval": output_dir / "live_canary_operator_approval_record.json",
        "canary_operator_approval_md": output_dir / "live_canary_operator_approval_record.md",
        "canary_readiness_packet": output_dir / "live_canary_readiness_packet.json",
        "canary_readiness_packet_md": output_dir / "live_canary_readiness_packet.md",
        "canary_dry_run_receipt": output_dir / "live_canary_dry_run_acceptance_receipt.json",
        "canary_dry_run_receipt_md": output_dir / "live_canary_dry_run_acceptance_receipt.md",
        "disabled_connector_audit": output_dir / "disabled_real_wallet_connector_audit.json",
        "disabled_connector_audit_md": output_dir / "disabled_real_wallet_connector_audit.md",
        "live_connector_audit_replay": output_dir / "live_connector_audit_replay.json",
        "live_connector_audit_replay_md": output_dir / "live_connector_audit_replay.md",
        "operator_live_approval_packet": output_dir / "operator_live_approval_packet.json",
        "operator_live_approval_packet_md": output_dir / "operator_live_approval_packet.md",
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
    strategy_ledger: Mapping[str, Any],
    strategy_summary: Mapping[str, Any],
    risk_decision_ledger: Mapping[str, Any],
    risk_prep_config: Mapping[str, Any],
    wallet_boundary_audit_ledger: Mapping[str, Any],
    dry_run_receipt_ledger: Mapping[str, Any],
    canary_readiness_packet: Mapping[str, Any],
    canary_dry_run_receipt: Mapping[str, Any],
    disabled_connector_result: Mapping[str, Any],
    disabled_connector_audit: Mapping[str, Any],
    live_connector_audit_replay: Mapping[str, Any],
    operator_live_approval_packet: Mapping[str, Any],
    live_connector_blocker_matrix: Mapping[str, Any],
    latest_disabled_connector_audit_path: str,
    latest_audit_replay_path: str,
    latest_operator_packet_path: str,
    source_evidence_refresh_ledger: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    blocked = [row for row in mapping_rows(risk_gate.get("results")) if row.get("blocked") is True]
    rejected = [row for row in mapping_rows(executions.get("results")) if row.get("execution_status") == "rejected"]
    skipped = [row for row in mapping_rows(executions.get("results")) if row.get("execution_status") == "skipped"]
    source_status_by_market = _source_status_by_market(source_evidence_refresh_ledger)
    source_counts = dict(source_evidence_refresh_ledger.get("summary_counts", {}))
    source_quality = dict(source_evidence_refresh_ledger.get("quality_ledger", {}))
    canary_governance_summary = build_canary_governance_summary(
        packet=canary_readiness_packet,
        receipt=canary_dry_run_receipt,
        audit_replay_result=live_connector_audit_replay,
        operator_approval_packet=operator_live_approval_packet,
        generated_at=generated_at,
    )
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
                "source_gap_status": source_status_by_market.get(clean_text(row.get("market_id")), {}).get(
                    "gap_status",
                    "gaps_present",
                ),
                "source_missing_reference_count": source_status_by_market.get(clean_text(row.get("market_id")), {}).get(
                    "missing_source_reference_count",
                    0,
                ),
                "source_stale_count": source_status_by_market.get(clean_text(row.get("market_id")), {}).get(
                    "stale_count",
                    0,
                ),
                "source_missing_local_capture_count": source_status_by_market.get(
                    clean_text(row.get("market_id")),
                    {},
                ).get("missing_local_capture_count", 0),
                "source_url_refresh_not_executed_count": source_status_by_market.get(
                    clean_text(row.get("market_id")),
                    {},
                ).get("source_url_refresh_not_executed_count", 0),
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
            "paper_strategy_ledger_record_count": int(strategy_ledger.get("record_count", 0) or 0),
            "unresolved_paper_exposure_usd": float(strategy_summary.get("unresolved_paper_exposure_usd", 0) or 0),
            "risk_decision_allowed_count": int(risk_decision_ledger.get("allowed_count", 0) or 0),
            "risk_decision_blocked_count": int(risk_decision_ledger.get("blocked_count", 0) or 0),
            "risk_decision_needs_manual_approval_count": int(
                risk_decision_ledger.get("needs_manual_approval_count", 0) or 0
            ),
            "wallet_boundary_packets_created": int(
                wallet_boundary_audit_ledger.get("boundary_packets_created", 0) or 0
            ),
            "wallet_boundary_blocked_packet_count": int(
                wallet_boundary_audit_ledger.get("blocked_packet_count", 0) or 0
            ),
            "wallet_boundary_missing_approval_count": int(
                wallet_boundary_audit_ledger.get("missing_approval_count", 0) or 0
            ),
            "wallet_boundary_missing_risk_decision_count": int(
                wallet_boundary_audit_ledger.get("missing_risk_decision_count", 0) or 0
            ),
            "wallet_boundary_kill_switch_block_count": int(
                wallet_boundary_audit_ledger.get("kill_switch_block_count", 0) or 0
            ),
            "dry_run_receipt_count": int(dry_run_receipt_ledger.get("receipt_count", 0) or 0),
            "dry_run_receipt_ready_count": int(
                dry_run_receipt_ledger.get("dry_run_receipt_ready_count", 0) or 0
            ),
            "dry_run_receipt_blocked_count": int(dry_run_receipt_ledger.get("blocked_receipt_count", 0) or 0),
            "live_canary_readiness_packet_count": 1 if canary_readiness_packet else 0,
            "live_canary_dry_run_ready_count": (
                1 if canary_readiness_packet.get("canary_status") == "dry_run_ready" else 0
            ),
            "live_canary_blocked_count": 1 if canary_readiness_packet.get("canary_status") == "blocked" else 0,
            "live_canary_needs_operator_approval_count": (
                1 if canary_readiness_packet.get("canary_status") == "needs_operator_approval" else 0
            ),
            "live_connector_blocker_count": int(canary_governance_summary.get("live_connector_blocker_count", 0) or 0),
            "live_connector_critical_blocker_count": int(
                canary_governance_summary.get("critical_blocker_count", 0) or 0
            ),
            "live_connector_audit_replay_record_count": int(
                live_connector_audit_replay.get("record_count", 0) or 0
            ),
            "operator_live_review_checklist_count": len(
                operator_live_approval_packet.get("required_human_checklist", [])
            ),
            "disabled_connector_blocked_reason_count": len(disabled_connector_result.get("blocked_reason_ids", [])),
            "source_evidence_refresh_record_count": int(source_counts.get("records", 0) or 0),
            "source_evidence_gap_count": int(
                dict(source_quality.get("summary_counts", {})).get("missing_evidence_gaps", 0) or 0
            ),
            "unresolved_market_count": int(feedback_readiness.get("unresolved_count", 0) or 0),
            "resolved_market_count": int(feedback_readiness.get("resolved_count", 0) or 0),
            "feedback_ready_count": int(feedback_readiness.get("feedback_ready_count", 0) or 0),
        },
        "portfolio_summary": portfolio_report.get("exposure_summary", {}),
        "paper_strategy_ledger_status": {
            "ledger_id": strategy_ledger.get("ledger_id"),
            "record_count": strategy_ledger.get("record_count"),
            "filled_record_count": strategy_ledger.get("filled_record_count"),
            "open_position_record_count": strategy_ledger.get("open_position_record_count"),
            "unresolved_position_record_count": strategy_ledger.get("unresolved_position_record_count"),
            "unresolved_paper_exposure_usd": strategy_ledger.get("unresolved_paper_exposure_usd"),
            "record_ids_unique": strategy_ledger.get("idempotency", {}).get("record_ids_unique"),
            "unresolved_pnl_not_invented": strategy_ledger.get("unresolved_pnl_not_invented"),
            "live_connector_audit_replay_status": strategy_ledger.get("live_connector_audit_replay_status"),
            "operator_review_packet_status": strategy_ledger.get("operator_review_packet_status"),
            "live_execution_approved": strategy_ledger.get("live_execution_approved") is True,
            "real_execution_available": strategy_ledger.get("real_execution_available") is True,
        },
        "paper_strategy_evaluation_summary": {
            "summary_id": strategy_summary.get("summary_id"),
            "performance_readiness_status": strategy_summary.get("performance_readiness_status"),
            "performance_statement": strategy_summary.get("performance_statement"),
            "paper_realized_pnl_usd": strategy_summary.get("paper_realized_pnl_usd"),
            "paper_unrealized_pnl_usd": strategy_summary.get("paper_unrealized_pnl_usd"),
            "unresolved_pnl_not_invented": strategy_summary.get("unresolved_pnl_not_invented"),
            "live_connector_audit_replay_status": strategy_summary.get("live_connector_audit_replay_status"),
            "operator_review_packet_status": strategy_summary.get("operator_review_packet_status"),
            "live_execution_approved": strategy_summary.get("live_execution_approved") is True,
            "real_execution_available": strategy_summary.get("real_execution_available") is True,
            "hypotheses_waiting_for_outcome_resolution": strategy_summary.get(
                "hypotheses_waiting_for_outcome_resolution",
                [],
            ),
            "missing_future_evaluation_data": strategy_summary.get("missing_future_evaluation_data", []),
        },
        "risk_prep_config_status": {
            "present": True,
            "config_id": risk_prep_config.get("config_id"),
            "contract_version": risk_prep_config.get("contract_version"),
            "valid": risk_prep_config.get("validation", {}).get("valid"),
            "max_total_exposure_usd": risk_prep_config.get("max_total_exposure_usd"),
            "max_per_market_exposure_usd": risk_prep_config.get("max_per_market_exposure_usd"),
            "market_allowlist_count": len(risk_prep_config.get("market_allowlist", [])),
            "market_denylist_count": len(risk_prep_config.get("market_denylist", [])),
            "per_run_action_cap": risk_prep_config.get("per_run_action_cap"),
            "kill_switch_enabled": risk_prep_config.get("kill_switch_enabled"),
            "manual_approval_required": risk_prep_config.get("manual_approval_required"),
        },
        "risk_decision_ledger_status": {
            "ledger_id": risk_decision_ledger.get("ledger_id"),
            "decision_count": risk_decision_ledger.get("decision_count"),
            "allowed_count": risk_decision_ledger.get("allowed_count"),
            "blocked_count": risk_decision_ledger.get("blocked_count"),
            "needs_manual_approval_count": risk_decision_ledger.get("needs_manual_approval_count"),
            "reason_code_summary": risk_decision_ledger.get("reason_code_summary", {}),
            "unresolved_evidence_gap_awareness": risk_decision_ledger.get(
                "unresolved_evidence_gap_awareness",
                {},
            ),
            "passive_reporting_only": risk_decision_ledger.get("passive_reporting_only") is True,
            "applied_to_paper_execution": risk_decision_ledger.get("applied_to_paper_execution") is True,
            "applied_to_real_execution": risk_decision_ledger.get("applied_to_real_execution") is True,
            "external_api_calls_performed": risk_decision_ledger.get("external_api_calls_performed") is True,
            "outcome_resolution_invented": risk_decision_ledger.get("outcome_resolution_invented") is True,
            "pnl_invented": risk_decision_ledger.get("pnl_invented") is True,
        },
        "wallet_boundary_summary": {
            "ledger_id": wallet_boundary_audit_ledger.get("ledger_id"),
            "boundary_packets_created": wallet_boundary_audit_ledger.get("boundary_packets_created"),
            "blocked_packet_count": wallet_boundary_audit_ledger.get("blocked_packet_count"),
            "missing_approval_count": wallet_boundary_audit_ledger.get("missing_approval_count"),
            "missing_risk_decision_count": wallet_boundary_audit_ledger.get("missing_risk_decision_count"),
            "kill_switch_block_count": wallet_boundary_audit_ledger.get("kill_switch_block_count"),
            "needs_manual_approval_count": wallet_boundary_audit_ledger.get("needs_manual_approval_count"),
            "approved_for_future_simulation_count": wallet_boundary_audit_ledger.get(
                "approved_for_future_simulation_count"
            ),
            "reason_code_summary": wallet_boundary_audit_ledger.get("reason_code_summary", {}),
            "safety_assertion": wallet_boundary_audit_ledger.get("safety_assertion"),
            "passive_artifact_only": wallet_boundary_audit_ledger.get("passive_artifact_only") is True,
            "applied_to_paper_execution": wallet_boundary_audit_ledger.get("applied_to_paper_execution") is True,
            "applied_to_real_execution": wallet_boundary_audit_ledger.get("applied_to_real_execution") is True,
            "external_api_calls_performed": wallet_boundary_audit_ledger.get("external_api_calls_performed") is True,
        },
        "dry_run_receipt_summary": {
            "ledger_id": dry_run_receipt_ledger.get("ledger_id"),
            "mode": dry_run_receipt_ledger.get("mode"),
            "simulation_mode": dry_run_receipt_ledger.get("simulation_mode"),
            "receipt_count": dry_run_receipt_ledger.get("receipt_count"),
            "dry_run_receipt_ready_count": dry_run_receipt_ledger.get("dry_run_receipt_ready_count"),
            "blocked_receipt_count": dry_run_receipt_ledger.get("blocked_receipt_count"),
            "receipt_ids_unique": dry_run_receipt_ledger.get("receipt_ids_unique"),
            "reason_code_summary": dry_run_receipt_ledger.get("reason_code_summary", {}),
            "gate_enforcement_summary": dry_run_receipt_ledger.get("gate_enforcement_summary", {}),
            "passive_artifact_only": dry_run_receipt_ledger.get("passive_artifact_only") is True,
            "applied_to_paper_execution": dry_run_receipt_ledger.get("applied_to_paper_execution") is True,
            "applied_to_real_execution": dry_run_receipt_ledger.get("applied_to_real_execution") is True,
            "wallet_used": dry_run_receipt_ledger.get("wallet_used") is True,
            "signing_used": dry_run_receipt_ledger.get("signing_used") is True,
            "real_signing_performed": dry_run_receipt_ledger.get("real_signing_performed") is True,
            "real_order_submitted": dry_run_receipt_ledger.get("real_order_submitted") is True,
            "authenticated_endpoint_used": dry_run_receipt_ledger.get("authenticated_endpoint_used") is True,
            "external_api_calls_performed": dry_run_receipt_ledger.get("external_api_calls_performed") is True,
        },
        "live_canary_readiness_summary": {
            **build_canary_dashboard_summary(
                canary_readiness_packet,
                canary_dry_run_receipt,
                live_connector_audit_replay_status=clean_text(live_connector_audit_replay.get("status")),
                operator_review_packet_status=clean_text(
                    operator_live_approval_packet.get("operator_packet_status")
                ),
                operator_review_ready=operator_live_approval_packet.get("operator_review_ready") is True,
            ),
            "canary_replay_status": canary_governance_summary.get("canary_replay_status"),
            "canary_replay_passed": canary_governance_summary.get("canary_replay_passed"),
            "acceptance_matrix_status": canary_governance_summary.get("acceptance_matrix_status"),
            "acceptance_matrix_passed": canary_governance_summary.get("acceptance_matrix_passed"),
            "acceptance_matrix_case_count": canary_governance_summary.get("acceptance_matrix_case_count"),
            "acceptance_matrix_failed_case_count": canary_governance_summary.get(
                "acceptance_matrix_failed_case_count"
            ),
            "live_connector_blocker_count": canary_governance_summary.get("live_connector_blocker_count"),
            "unresolved_live_connector_blocker_count": canary_governance_summary.get(
                "unresolved_live_connector_blocker_count"
            ),
            "resolved_live_connector_blocker_count": canary_governance_summary.get(
                "resolved_live_connector_blocker_count"
            ),
            "all_live_connector_blockers_unresolved": canary_governance_summary.get(
                "all_live_connector_blockers_unresolved"
            ),
            "live_connector_blocker_ids": canary_governance_summary.get("live_connector_blocker_ids"),
            "critical_blocker_count": canary_governance_summary.get("critical_blocker_count"),
            "critical_blockers": canary_governance_summary.get("critical_blockers"),
            "next_recommended_non_live_task": canary_governance_summary.get("next_recommended_non_live_task"),
            "operator_approval_packet_status": canary_governance_summary.get("operator_approval_packet_status"),
            "operator_review_ready": canary_governance_summary.get("operator_review_ready") is True,
            "live_execution_approved": False,
            "real_execution_available": False,
            "dry_run_only_assertion": canary_governance_summary.get("dry_run_only_assertion"),
            "governance_summary": canary_governance_summary,
        },
        "disabled_real_connector_summary": build_disabled_connector_passive_status(
            result=disabled_connector_result,
            latest_disabled_connector_audit_path=latest_disabled_connector_audit_path,
            live_canary_replay_acceptance_status=clean_text(canary_governance_summary.get("acceptance_matrix_status")),
        )
        | {
            "audit_id": disabled_connector_audit.get("audit_id"),
            "audit_valid": disabled_connector_audit.get("audit_valid"),
            "result_id": disabled_connector_result.get("result_id"),
        },
        "live_connector_audit_operator_summary": {
            "audit_replay_status": clean_text(live_connector_audit_replay.get("status")),
            "operator_packet_status": clean_text(operator_live_approval_packet.get("operator_packet_status")),
            "operator_review_ready": operator_live_approval_packet.get("operator_review_ready") is True,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
            "unresolved_live_blocker_count": int(
                live_connector_blocker_matrix.get("unresolved_blocker_count", 0) or 0
            ),
            "disabled_connector_status": clean_text(disabled_connector_result.get("connector_status")),
            "secret_boundary_status": clean_text(
                dict(live_connector_audit_replay.get("secret_boundary_validation_summary", {})).get("status")
            ),
            "latest_operator_packet_path": clean_text(latest_operator_packet_path),
            "latest_audit_replay_path": clean_text(latest_audit_replay_path),
            "operator_review_is_not_live_approval": operator_live_approval_packet.get(
                "operator_review_is_not_live_approval"
            )
            is True,
        },
        "source_evidence_refresh_status": {
            "refresh_id": source_evidence_refresh_ledger.get("refresh_id"),
            "run_mode": source_evidence_refresh_ledger.get("run_mode"),
            "default_no_network_mode": source_evidence_refresh_ledger.get("default_no_network_mode"),
            "network_used": source_evidence_refresh_ledger.get("network_used"),
            "external_api_calls_performed": source_evidence_refresh_ledger.get("external_api_calls_performed"),
            "pending_approval_packet_ready": source_evidence_refresh_ledger.get("pending_approval_packet_ready"),
            "summary_counts": source_evidence_refresh_ledger.get("summary_counts", {}),
            "freshness_status_counts": source_quality.get("freshness_status_counts", {}),
            "market_source_status": source_quality.get("market_source_status", []),
            "missing_evidence_gaps": source_quality.get("missing_evidence_gaps", []),
        },
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
            "Review the passive risk engine decision ledger before any future execution-layer design work.",
            "Review the passive dry-run execution receipts before any future execution-layer design work.",
            "Review the live connector audit replay and operator review packet as non-approval artifacts only.",
            "Review source evidence freshness and missing evidence gaps before interpreting paper strategy output.",
            "Review the paper strategy evaluation ledger before interpreting paper readiness.",
            "Add saved local outcome resolution evidence before evaluating paper performance.",
            "Review carried-forward open paper positions and exposure before the next local paper run.",
            "Recheck unresolved markets only against saved local outcome artifacts.",
            "Prepare feedback records only for markets with explicit local resolution evidence.",
            "Keep this as an explicit one-shot local command, not a scheduler or autonomous loop.",
        ],
        "next_operator_action": (
            "Review risk decisions, strategy ledger, source evidence gaps, unresolved exposure, risk-prep config, and missing outcome evidence."
        ),
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


def _source_status_by_market(source_evidence_refresh_ledger: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    quality = dict(source_evidence_refresh_ledger.get("quality_ledger", {}))
    return {
        clean_text(row.get("market_id")): row
        for row in mapping_rows(quality.get("market_source_status"))
        if clean_text(row.get("market_id"))
    }


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
        "real_order_placement_performed": False,
        "real_signature_created": False,
        "cryptographic_signing_performed": False,
        "real_wallet_used": False,
        "real_wallet_access_performed": False,
        "wallet_used": False,
        "private_key_used": False,
        "signing_used": False,
        "trading_endpoint_used": False,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "live_execution_performed": False,
        "real_money_used": False,
        "autonomous_trading_enabled": False,
        "authenticated_endpoint_used": False,
        "authenticated_endpoint_called": False,
        "authenticated_endpoint_call_performed": False,
        "browser_automation_used": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "external_api_call_performed": False,
        "openrouter_used": False,
        "polymarket_api_used": False,
        "outcome_invented": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
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
    source_evidence_refresh_request: Mapping[str, Any],
    source_evidence_refresh_ledger: Mapping[str, Any],
    source_evidence_quality_ledger: Mapping[str, Any],
    source_evidence_pending_approval: Mapping[str, Any] | None,
    rollforward_report: Mapping[str, Any],
    portfolio_report: Mapping[str, Any],
    strategy_ledger: Mapping[str, Any],
    strategy_summary: Mapping[str, Any],
    risk_decision_ledger: Mapping[str, Any],
    risk_prep_config: Mapping[str, Any],
    wallet_boundary_audit_ledger: Mapping[str, Any],
    dry_run_receipt_ledger: Mapping[str, Any],
    canary_operator_approval_record: Mapping[str, Any],
    canary_readiness_packet: Mapping[str, Any],
    canary_dry_run_receipt: Mapping[str, Any],
    disabled_connector_audit: Mapping[str, Any],
    live_connector_audit_replay: Mapping[str, Any],
    operator_live_approval_packet: Mapping[str, Any],
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
    write_json(paths["strategy_ledger"], strategy_ledger)
    write_text(paths["strategy_ledger_md"], render_paper_strategy_evaluation_ledger_markdown(strategy_ledger))
    write_json(paths["strategy_summary"], strategy_summary)
    write_text(paths["strategy_summary_md"], render_paper_strategy_evaluation_summary_markdown(strategy_summary))
    write_json(paths["risk_decision_ledger"], risk_decision_ledger)
    write_text(paths["risk_decision_ledger_md"], render_risk_decision_ledger_markdown(risk_decision_ledger))
    write_json(paths["wallet_boundary_audit_ledger"], wallet_boundary_audit_ledger)
    write_text(
        paths["wallet_boundary_audit_ledger_md"],
        render_wallet_boundary_audit_ledger_markdown(wallet_boundary_audit_ledger),
    )
    write_json(paths["dry_run_receipts"], dry_run_receipt_ledger)
    write_text(paths["dry_run_receipts_md"], render_dry_run_execution_receipt_ledger_markdown(dry_run_receipt_ledger))
    write_json(paths["canary_operator_approval"], canary_operator_approval_record)
    write_text(
        paths["canary_operator_approval_md"],
        render_canary_operator_approval_markdown(canary_operator_approval_record),
    )
    write_json(paths["canary_readiness_packet"], canary_readiness_packet)
    write_text(paths["canary_readiness_packet_md"], render_canary_readiness_packet_markdown(canary_readiness_packet))
    write_json(paths["canary_dry_run_receipt"], canary_dry_run_receipt)
    write_text(paths["canary_dry_run_receipt_md"], render_canary_dry_run_receipt_markdown(canary_dry_run_receipt))
    write_json(paths["disabled_connector_audit"], disabled_connector_audit)
    write_text(
        paths["disabled_connector_audit_md"],
        render_disabled_connector_audit_record_markdown(disabled_connector_audit),
    )
    write_json(paths["live_connector_audit_replay"], live_connector_audit_replay)
    write_text(
        paths["live_connector_audit_replay_md"],
        render_live_connector_audit_replay_markdown(live_connector_audit_replay),
    )
    write_json(paths["operator_live_approval_packet"], operator_live_approval_packet)
    write_text(
        paths["operator_live_approval_packet_md"],
        render_operator_live_approval_packet_markdown(operator_live_approval_packet),
    )
    write_json(paths["source_evidence_refresh_request"], source_evidence_refresh_request)
    write_json(paths["source_evidence_refresh"], source_evidence_refresh_ledger)
    write_text(paths["source_evidence_refresh_md"], render_public_evidence_refresh_report(source_evidence_refresh_ledger))
    write_json(paths["source_evidence_quality"], source_evidence_quality_ledger)
    if source_evidence_pending_approval is not None:
        write_json(paths["source_evidence_pending_approval"], source_evidence_pending_approval)
        write_text(
            paths["source_evidence_pending_approval_md"],
            render_pending_approval_packet(source_evidence_pending_approval),
        )
    write_json(paths["risk_prep_config"], risk_prep_config)
    write_text(paths["risk_prep_config_md"], render_future_risk_engine_config_markdown(risk_prep_config))
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
    source_status = dict(dashboard.get("source_evidence_refresh_status", {}))
    source_counts = dict(source_status.get("summary_counts", {}))
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
        f"- Paper strategy ledger records: {counts.get('paper_strategy_ledger_record_count')}",
        f"- Unresolved paper exposure: `${counts.get('unresolved_paper_exposure_usd')}`",
        f"- Risk engine blocked: {counts.get('risk_decision_blocked_count')}",
        f"- Risk engine needs manual approval: {counts.get('risk_decision_needs_manual_approval_count')}",
        f"- Wallet boundary packets: {counts.get('wallet_boundary_packets_created')}",
        f"- Wallet boundary blocked: {counts.get('wallet_boundary_blocked_packet_count')}",
        f"- Wallet boundary missing approval: {counts.get('wallet_boundary_missing_approval_count')}",
        f"- Wallet boundary missing risk decision: {counts.get('wallet_boundary_missing_risk_decision_count')}",
        f"- Wallet boundary kill switch blocks: {counts.get('wallet_boundary_kill_switch_block_count')}",
        f"- Dry-run receipts: {counts.get('dry_run_receipt_count')}",
        f"- Dry-run receipts ready: {counts.get('dry_run_receipt_ready_count')}",
        f"- Dry-run receipts blocked: {counts.get('dry_run_receipt_blocked_count')}",
        f"- Live canary readiness packets: {counts.get('live_canary_readiness_packet_count')}",
        f"- Live canary dry-run ready: {counts.get('live_canary_dry_run_ready_count')}",
        f"- Live canary blocked: {counts.get('live_canary_blocked_count')}",
        f"- Live canary needs operator approval: {counts.get('live_canary_needs_operator_approval_count')}",
        f"- Source evidence records: {counts.get('source_evidence_refresh_record_count')}",
        f"- Source evidence gaps: {counts.get('source_evidence_gap_count')}",
        "",
        "## Tracked Markets",
        "",
    ]
    for market in dashboard.get("tracked_markets", []):
        lines.append(
            f"- `{market.get('market_id')}` `{market.get('outcome_status')}` "
            f"`source:{market.get('source_gap_status')}` - {market.get('market_title')}"
        )
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
    strategy_status = dict(dashboard.get("paper_strategy_ledger_status", {}))
    strategy_summary = dict(dashboard.get("paper_strategy_evaluation_summary", {}))
    risk_decisions = dict(dashboard.get("risk_decision_ledger_status", {}))
    wallet_boundary = dict(dashboard.get("wallet_boundary_summary", {}))
    dry_run_receipts = dict(dashboard.get("dry_run_receipt_summary", {}))
    dry_run_gates = dict(dry_run_receipts.get("gate_enforcement_summary", {}))
    canary = dict(dashboard.get("live_canary_readiness_summary", {}))
    disabled_connector = dict(dashboard.get("disabled_real_connector_summary", {}))
    audit_operator = dict(dashboard.get("live_connector_audit_operator_summary", {}))
    risk_prep = dict(dashboard.get("risk_prep_config_status", {}))
    lines.extend(
        [
            "",
            "## Paper Strategy Ledger",
            "",
            f"- Ledger: `{strategy_status.get('ledger_id')}`",
            f"- Records: {strategy_status.get('record_count')}",
            f"- Filled paper records: {strategy_status.get('filled_record_count')}",
            f"- Open position records: {strategy_status.get('open_position_record_count')}",
            f"- Unresolved paper exposure: `${strategy_status.get('unresolved_paper_exposure_usd')}`",
            f"- Record IDs unique: `{str(strategy_status.get('record_ids_unique')).lower()}`",
            f"- Unresolved PnL not invented: `{str(strategy_status.get('unresolved_pnl_not_invented')).lower()}`",
            "",
            "## Paper Evaluation Readiness",
            "",
            f"- Readiness: `{strategy_summary.get('performance_readiness_status')}`",
            f"- Paper realized PnL: `{strategy_summary.get('paper_realized_pnl_usd')}`",
            f"- Paper unrealized PnL: `{strategy_summary.get('paper_unrealized_pnl_usd')}`",
            "- Missing future evaluation data:",
            *bullet_lines(str(item) for item in strategy_summary.get("missing_future_evaluation_data", [])),
            "",
            "## Risk Engine Decision Ledger",
            "",
            f"- Ledger: `{risk_decisions.get('ledger_id')}`",
            f"- Decisions: {risk_decisions.get('decision_count')}",
            f"- Allowed: {risk_decisions.get('allowed_count')}",
            f"- Blocked: {risk_decisions.get('blocked_count')}",
            f"- Needs manual approval: {risk_decisions.get('needs_manual_approval_count')}",
            f"- Passive reporting only: `{str(risk_decisions.get('passive_reporting_only')).lower()}`",
            f"- Applied to paper execution: `{str(risk_decisions.get('applied_to_paper_execution')).lower()}`",
            f"- Applied to real execution: `{str(risk_decisions.get('applied_to_real_execution')).lower()}`",
            "- Reason code summary:",
            *bullet_lines(
                f"{key}: `{value}`" for key, value in dict(risk_decisions.get("reason_code_summary", {})).items()
            ),
            "",
            "## Wallet Boundary Summary",
            "",
            f"- Ledger: `{wallet_boundary.get('ledger_id')}`",
            f"- Boundary packets created: {wallet_boundary.get('boundary_packets_created')}",
            f"- Blocked packets: {wallet_boundary.get('blocked_packet_count')}",
            f"- Missing approval: {wallet_boundary.get('missing_approval_count')}",
            f"- Missing risk decision: {wallet_boundary.get('missing_risk_decision_count')}",
            f"- Kill switch blocks: {wallet_boundary.get('kill_switch_block_count')}",
            f"- Needs manual approval: {wallet_boundary.get('needs_manual_approval_count')}",
            f"- Approved for future simulation: {wallet_boundary.get('approved_for_future_simulation_count')}",
            f"- Passive artifact only: `{str(wallet_boundary.get('passive_artifact_only')).lower()}`",
            f"- Applied to paper execution: `{str(wallet_boundary.get('applied_to_paper_execution')).lower()}`",
            f"- Applied to real execution: `{str(wallet_boundary.get('applied_to_real_execution')).lower()}`",
            f"- External API calls performed: `{str(wallet_boundary.get('external_api_calls_performed')).lower()}`",
            f"- Safety assertion: {wallet_boundary.get('safety_assertion')}",
            "- Reason code summary:",
            *bullet_lines(
                f"{key}: `{value}`" for key, value in dict(wallet_boundary.get("reason_code_summary", {})).items()
            ),
            "",
            "## Dry-Run Execution Receipts",
            "",
            f"- Ledger: `{dry_run_receipts.get('ledger_id')}`",
            f"- Mode: `{dry_run_receipts.get('mode')}` / `{dry_run_receipts.get('simulation_mode')}`",
            f"- Receipts: {dry_run_receipts.get('receipt_count')}",
            f"- Ready receipts: {dry_run_receipts.get('dry_run_receipt_ready_count')}",
            f"- Blocked receipts: {dry_run_receipts.get('blocked_receipt_count')}",
            f"- Receipt IDs unique: `{str(dry_run_receipts.get('receipt_ids_unique')).lower()}`",
            f"- Risk gate enforced: `{str(dry_run_gates.get('risk_decision_required')).lower()}`",
            f"- Kill switch enforced: `{str(dry_run_gates.get('kill_switch_must_be_disabled')).lower()}`",
            f"- Manual approval gate enforced: `{str(dry_run_gates.get('manual_approval_gate_required')).lower()}`",
            f"- Evidence gate enforced: `{str(dry_run_gates.get('evidence_gate_required')).lower()}`",
            f"- Forbidden fields rejected: `{str(dry_run_gates.get('forbidden_fields_rejected')).lower()}`",
            f"- Passive artifact only: `{str(dry_run_receipts.get('passive_artifact_only')).lower()}`",
            f"- Applied to paper execution: `{str(dry_run_receipts.get('applied_to_paper_execution')).lower()}`",
            f"- Applied to real execution: `{str(dry_run_receipts.get('applied_to_real_execution')).lower()}`",
            f"- External API calls performed: `{str(dry_run_receipts.get('external_api_calls_performed')).lower()}`",
            "- Reason code summary:",
            *bullet_lines(
                f"{key}: `{value}`" for key, value in dict(dry_run_receipts.get("reason_code_summary", {})).items()
            ),
            "",
            "## Live Canary Readiness",
            "",
            f"- Canary: `{canary.get('canary_id')}`",
            f"- Readiness status: `{canary.get('canary_readiness_status')}`",
            f"- Dry-run acceptance status: `{canary.get('dry_run_acceptance_status')}`",
            f"- Operator approval status: `{canary.get('operator_approval_status')}`",
            f"- Risk decision status: `{canary.get('risk_decision_status')}`",
            f"- Wallet boundary status: `{canary.get('wallet_boundary_status')}`",
            f"- Signing simulator receipt status: `{canary.get('signing_simulator_receipt_status')}`",
            f"- Live execution allowed: `{str(canary.get('live_execution_allowed')).lower()}`",
            f"- External API call performed: `{str(canary.get('external_api_call_performed')).lower()}`",
            f"- Canary replay status: `{canary.get('canary_replay_status')}`",
            f"- Acceptance matrix status: `{canary.get('acceptance_matrix_status')}`",
            f"- Acceptance matrix failed cases: {canary.get('acceptance_matrix_failed_case_count')}",
            f"- Live connector blockers: {canary.get('live_connector_blocker_count')}",
            f"- Critical live connector blockers: {canary.get('critical_blocker_count')}",
            f"- Unresolved live connector blockers: {canary.get('unresolved_live_connector_blocker_count')}",
            f"- Resolved live connector blockers: {canary.get('resolved_live_connector_blocker_count')}",
            f"- Dry-run-only assertion: {canary.get('dry_run_only_assertion')}",
            "- Blocked reason summary:",
            *bullet_lines(str(item) for item in canary.get("blocked_reason_summary", [])),
            "- Missing artifact summary:",
            *bullet_lines(str(item) for item in canary.get("missing_artifact_summary", [])),
            "- Critical blockers:",
            *bullet_lines(str(item) for item in canary.get("critical_blockers", [])),
            "- Next recommended non-live task:",
            f"- {canary.get('next_recommended_non_live_task')}",
            "- Next operator action:",
            f"- {canary.get('next_operator_action')}",
            "",
            "## Disabled Real Connector",
            "",
            f"- Connector status: `{disabled_connector.get('connector_status')}`",
            f"- Real execution available: `{str(disabled_connector.get('real_execution_available')).lower()}`",
            f"- Secrets present: `{disabled_connector.get('secrets_present')}`",
            f"- Secret boundary: `{disabled_connector.get('secret_boundary_status')}`",
            f"- Blocked reasons: {disabled_connector.get('blocked_reason_count')}",
            f"- Latest audit: `{disabled_connector.get('latest_disabled_connector_audit_path')}`",
            f"- Replay acceptance status: `{disabled_connector.get('live_canary_replay_acceptance_status')}`",
            "- Blocker IDs:",
            *bullet_lines(str(item) for item in disabled_connector.get("blocker_ids", [])),
            "",
            "## Live Connector Audit And Operator Review",
            "",
            f"- Audit replay status: `{audit_operator.get('audit_replay_status')}`",
            f"- Operator packet status: `{audit_operator.get('operator_packet_status')}`",
            f"- Operator review ready: `{str(audit_operator.get('operator_review_ready')).lower()}`",
            f"- Live execution approved: `{str(audit_operator.get('live_execution_approved')).lower()}`",
            f"- Real execution available: `{str(audit_operator.get('real_execution_available')).lower()}`",
            f"- Live connector enabled: `{str(audit_operator.get('live_connector_enabled')).lower()}`",
            f"- Unresolved live blockers: {audit_operator.get('unresolved_live_blocker_count')}",
            f"- Disabled connector status: `{audit_operator.get('disabled_connector_status')}`",
            f"- Secret boundary status: `{audit_operator.get('secret_boundary_status')}`",
            f"- Latest audit replay: `{audit_operator.get('latest_audit_replay_path')}`",
            f"- Latest operator packet: `{audit_operator.get('latest_operator_packet_path')}`",
            "",
            "## Source Evidence Refresh",
            "",
            f"- Refresh: `{source_status.get('refresh_id')}`",
            f"- Run mode: `{source_status.get('run_mode')}`",
            f"- Default no-network mode: `{str(source_status.get('default_no_network_mode')).lower()}`",
            f"- Network used: `{str(source_status.get('network_used')).lower()}`",
            f"- External API calls performed: `{str(source_status.get('external_api_calls_performed')).lower()}`",
            f"- Records: {source_counts.get('records')}",
            f"- Local captures ingested: {source_counts.get('local_captured_references')}",
            f"- Missing source gaps: {source_counts.get('missing_source_reference_records')}",
            f"- Missing local captures: {source_counts.get('missing_local_capture_records')}",
            f"- Pending approval records: {source_counts.get('pending_approval_records')}",
            f"- Approved source URLs not fetched: {source_counts.get('source_url_refresh_not_executed_records')}",
            f"- Stale records: {source_counts.get('stale_records')}",
            "- Market source status:",
            *bullet_lines(
                f"`{row.get('market_id')}` `{row.get('gap_status')}` "
                f"missing {row.get('missing_source_reference_count')} "
                f"missing_local {row.get('missing_local_capture_count')} "
                f"stale {row.get('stale_count')}"
                for row in source_status.get("market_source_status", [])
            ),
            "",
            "## Risk Prep Config",
            "",
            f"- Present: `{str(risk_prep.get('present')).lower()}`",
            f"- Valid: `{str(risk_prep.get('valid')).lower()}`",
            f"- Max total exposure: `${risk_prep.get('max_total_exposure_usd')}`",
            f"- Max per-market exposure: `${risk_prep.get('max_per_market_exposure_usd')}`",
            f"- Market allowlist count: {risk_prep.get('market_allowlist_count')}",
            f"- Market denylist count: {risk_prep.get('market_denylist_count')}",
            f"- Per-run action cap: {risk_prep.get('per_run_action_cap')}",
            f"- Kill switch enabled: `{str(risk_prep.get('kill_switch_enabled')).lower()}`",
            f"- Manual approval required: `{str(risk_prep.get('manual_approval_required')).lower()}`",
        ]
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
            f"- Strategy ledger: `{result.get('strategy_ledger_path')}`",
            f"- Strategy summary: `{result.get('strategy_summary_path')}`",
            f"- Risk decision ledger: `{result.get('risk_decision_ledger_path')}`",
            f"- Wallet boundary audit ledger: `{result.get('wallet_boundary_audit_ledger_path')}`",
            f"- Dry-run execution receipts: `{result.get('dry_run_receipt_ledger_path')}`",
            f"- Live canary operator approval record: `{result.get('canary_operator_approval_record_path')}`",
            f"- Live canary readiness packet: `{result.get('canary_readiness_packet_path')}`",
            f"- Live canary dry-run receipt: `{result.get('canary_dry_run_receipt_path')}`",
            f"- Disabled real connector audit: `{dict(dashboard.get('disabled_real_connector_summary', {})).get('latest_disabled_connector_audit_path')}`",
            f"- Live connector audit replay: `{result.get('live_connector_audit_replay_path')}`",
            f"- Operator live review packet: `{result.get('operator_live_approval_packet_path')}`",
            f"- Source evidence refresh: `{result.get('source_evidence_refresh_path')}`",
            f"- Source evidence quality ledger: `{result.get('source_evidence_quality_ledger_path')}`",
            f"- Source evidence pending approval: `{result.get('source_evidence_pending_approval_path')}`",
            f"- Risk prep config: `{result.get('risk_prep_config_path')}`",
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
