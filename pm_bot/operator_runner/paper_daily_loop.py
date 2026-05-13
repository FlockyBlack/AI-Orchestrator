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
from pm_bot.operator_runner.operator_ui_panel_v1 import (
    build_operator_ui_panel_v1,
    render_operator_ui_panel_v1_html,
    render_operator_ui_panel_v1_markdown,
    summarize_operator_ui_panel_v1,
)
from pm_bot.operator_runner.telegram_operator_control_bot import (
    build_telegram_operator_control_config,
    build_telegram_operator_control_summary,
)
from pm_bot.operator_runner.telegram_operator_control_state import build_telegram_operator_control_state
from pm_bot.operator_runner.telegram_mini_app_operator_panel import (
    build_telegram_mini_app_panel_artifact_summary,
    build_telegram_mini_app_panel_model,
    render_telegram_mini_app_panel_html,
    summarize_telegram_mini_app_panel_model,
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
from pm_bot.trading_core.live_credentials_auth_boundary import (
    build_default_live_credentials_boundary_config,
    evaluate_live_auth_boundary_for_tiny_canary,
    summarize_live_credentials_status,
)
from pm_bot.trading_core.live_enablement_config import (
    build_live_enablement_config_preflight,
    summarize_live_enablement_config_preflight,
)
from pm_bot.trading_core.live_order_submission_boundary import (
    build_live_order_submission_boundary_receipt,
    summarize_live_order_submission_boundary_receipt,
)
from pm_bot.trading_core.tiny_live_canary_gonogo_gate import (
    build_tiny_live_canary_gonogo_gate,
    summarize_tiny_live_canary_gonogo_gate,
)
from pm_bot.trading_core.live_connector_audit_replay import (
    build_live_connector_audit_replay,
    render_live_connector_audit_replay_markdown,
)
from pm_bot.trading_core.live_canary_operator_intent_packet import (
    build_live_canary_operator_intent_packet,
    render_live_canary_operator_intent_packet_markdown,
    summarize_live_canary_operator_intent_packet,
)
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
    summarize_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.operator_live_approval_packet import (
    build_operator_live_approval_packet,
    render_operator_live_approval_packet_markdown,
)
from pm_bot.trading_core.tiny_live_canary_manual_runbook import (
    build_tiny_live_canary_manual_runbook,
    render_tiny_live_canary_manual_runbook_markdown,
)
from pm_bot.trading_core.tiny_live_canary_preflight_contract import (
    build_tiny_live_canary_kill_switch_validation,
    build_tiny_live_canary_preflight_contract,
    evaluate_tiny_live_canary_preflight,
    render_tiny_live_canary_preflight_contract_markdown,
    render_tiny_live_canary_preflight_result_markdown,
)
from pm_bot.trading_core.real_wallet_connector_disabled_adapter import (
    DisabledRealWalletConnectorConfig,
    RealWalletConnectorDisabledAdapter,
    build_disabled_connector_passive_status,
    build_disabled_connector_request,
    render_disabled_connector_audit_record_markdown,
)
from pm_bot.trading_core.polymarket_btc_read_only_connector import (
    PolymarketBTCReadOnlyConnector,
    build_default_btc_fixture_market_payload,
    build_default_btc_read_only_config,
    summarize_btc_market_snapshot,
)
from pm_bot.trading_core.btc_market_analysis_order_intent import (
    evaluate_btc_analysis_to_order_intent,
    summarize_btc_analysis_order_intent,
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
from pm_bot.trading_core.risk_limit_control_plane import (
    RiskLimitDailyLossSnapshot,
    RiskLimitExposureSnapshot,
    RiskLimitOrderIntent,
    build_default_risk_limit_policy,
    build_default_risk_limit_state,
    build_risk_control_plane_summary,
    evaluate_risk_limits_for_order_intent,
    summarize_risk_limit_policy,
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
    operator_intent_packet_path: str
    readiness_evidence_bundle_path: str
    live_credentials_auth_boundary_path: str
    btc_market_snapshot_path: str
    btc_market_analysis_path: str
    btc_order_intent_dry_run_path: str
    btc_risk_decision_path: str
    live_order_submission_boundary_path: str
    live_enablement_config_preflight_path: str
    tiny_live_canary_gonogo_gate_path: str
    tiny_live_canary_preflight_contract_path: str
    tiny_live_canary_manual_runbook_path: str
    tiny_live_canary_preflight_result_path: str
    portfolio_path: str
    rollforward_path: str
    outcome_recheck_queue_path: str
    feedback_readiness_path: str
    dashboard_json_path: str
    dashboard_md_path: str
    operator_ui_panel_json_path: str
    operator_ui_panel_md_path: str
    operator_ui_panel_html_path: str
    telegram_mini_app_operator_panel_json_path: str
    telegram_mini_app_operator_panel_html_path: str
    telegram_operator_control_state_path: str
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
    tiny_live_canary_preflight_contract = build_tiny_live_canary_preflight_contract(generated_at=generated_at)
    tiny_live_canary_manual_runbook = build_tiny_live_canary_manual_runbook(generated_at=generated_at)
    tiny_live_canary_kill_switch_validation = build_tiny_live_canary_kill_switch_validation(
        tiny_live_canary_preflight_contract.get("kill_switch_requirement", {}),
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
        tiny_live_canary_preflight_contract_references=[
            tiny_live_canary_preflight_contract.get("contract_id", "")
        ],
        tiny_live_canary_manual_runbook_references=[
            tiny_live_canary_manual_runbook.get("runbook_id", "")
        ],
        operator_intent_packet_references=[
            normalize_path(paths["operator_intent_packet"])
            if active_config.write_artifacts
            else "live_canary_operator_intent_packet:current-run"
        ],
        readiness_evidence_bundle_references=[
            normalize_path(paths["readiness_evidence_bundle"])
            if active_config.write_artifacts
            else "live_canary_readiness_evidence_bundle:current-run"
        ],
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
        tiny_live_canary_preflight_contract=tiny_live_canary_preflight_contract,
        tiny_live_canary_manual_runbook=tiny_live_canary_manual_runbook,
        latest_audit_replay_path=(
            normalize_path(paths["live_connector_audit_replay"]) if active_config.write_artifacts else ""
        ),
        latest_tiny_canary_contract_path=(
            normalize_path(paths["tiny_live_canary_preflight_contract"]) if active_config.write_artifacts else ""
        ),
        latest_manual_runbook_path=(
            normalize_path(paths["tiny_live_canary_manual_runbook"]) if active_config.write_artifacts else ""
        ),
        generated_at=generated_at,
    )
    latest_operator_intent_packet_path = (
        normalize_path(paths["operator_intent_packet"]) if active_config.write_artifacts else ""
    )
    operator_intent_packet = build_live_canary_operator_intent_packet(
        tiny_live_canary_preflight_contract=tiny_live_canary_preflight_contract,
        tiny_live_canary_preflight_contract_reference=(
            normalize_path(paths["tiny_live_canary_preflight_contract"])
            if active_config.write_artifacts
            else tiny_live_canary_preflight_contract.get("contract_id", "")
        ),
        tiny_live_canary_manual_runbook=tiny_live_canary_manual_runbook,
        tiny_live_canary_manual_runbook_reference=(
            normalize_path(paths["tiny_live_canary_manual_runbook"])
            if active_config.write_artifacts
            else tiny_live_canary_manual_runbook.get("runbook_id", "")
        ),
        operator_approval_packet=operator_live_approval_packet,
        operator_approval_packet_reference=(
            normalize_path(paths["operator_live_approval_packet"])
            if active_config.write_artifacts
            else "operator_live_review_packet:current-run"
        ),
        live_connector_audit_replay=live_connector_audit_replay,
        live_connector_audit_replay_reference=(
            normalize_path(paths["live_connector_audit_replay"])
            if active_config.write_artifacts
            else live_connector_audit_replay.get("replay_id", "")
        ),
        disabled_connector_audit=disabled_connector_audit,
        disabled_connector_audit_reference=(
            normalize_path(paths["disabled_connector_audit"])
            if active_config.write_artifacts
            else disabled_connector_audit.get("audit_id", "")
        ),
        secret_boundary_validation=live_connector_audit_replay.get("secret_boundary_validation_summary", {}),
        blocker_matrix=live_connector_blocker_matrix,
        blocker_matrix_reference="live_connector_blocker_matrix:all-critical-blockers-unresolved",
        risk_review_reference=canary_readiness_packet.get("risk_decision_id", ""),
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
        tiny_live_canary_preflight_contract=tiny_live_canary_preflight_contract,
        tiny_live_canary_manual_runbook=tiny_live_canary_manual_runbook,
        operator_intent_packet=operator_intent_packet,
        latest_audit_replay_path=(
            normalize_path(paths["live_connector_audit_replay"]) if active_config.write_artifacts else ""
        ),
        latest_tiny_canary_contract_path=(
            normalize_path(paths["tiny_live_canary_preflight_contract"]) if active_config.write_artifacts else ""
        ),
        latest_manual_runbook_path=(
            normalize_path(paths["tiny_live_canary_manual_runbook"]) if active_config.write_artifacts else ""
        ),
        latest_operator_intent_packet_path=latest_operator_intent_packet_path,
        generated_at=generated_at,
    )
    tiny_live_canary_preflight_result = evaluate_tiny_live_canary_preflight(
        contract=tiny_live_canary_preflight_contract,
        manual_runbook=tiny_live_canary_manual_runbook,
        operator_packet=operator_live_approval_packet,
        operator_intent_packet=operator_intent_packet,
        audit_replay_result=live_connector_audit_replay,
        secret_boundary_validation=live_connector_audit_replay.get("secret_boundary_validation_summary", {}),
        blocker_matrix=live_connector_blocker_matrix,
        kill_switch_validation=tiny_live_canary_kill_switch_validation,
        generated_at=generated_at,
    )
    latest_readiness_evidence_bundle_path = (
        normalize_path(paths["readiness_evidence_bundle"]) if active_config.write_artifacts else ""
    )
    latest_btc_market_snapshot_path = (
        normalize_path(paths["btc_market_snapshot"]) if active_config.write_artifacts else ""
    )
    latest_btc_analysis_path = normalize_path(paths["btc_market_analysis"]) if active_config.write_artifacts else ""
    latest_btc_order_intent_path = (
        normalize_path(paths["btc_order_intent_dry_run"]) if active_config.write_artifacts else ""
    )
    latest_btc_risk_decision_path = normalize_path(paths["btc_risk_decision"]) if active_config.write_artifacts else ""
    latest_live_credentials_auth_boundary_path = (
        normalize_path(paths["live_credentials_auth_boundary"]) if active_config.write_artifacts else ""
    )
    latest_live_order_submission_boundary_path = (
        normalize_path(paths["live_order_submission_boundary"]) if active_config.write_artifacts else ""
    )
    latest_live_enablement_config_preflight_path = (
        normalize_path(paths["live_enablement_config_preflight"]) if active_config.write_artifacts else ""
    )
    latest_tiny_live_canary_gonogo_gate_path = (
        normalize_path(paths["tiny_live_canary_gonogo_gate"]) if active_config.write_artifacts else ""
    )
    live_enablement_config_preflight = build_live_enablement_config_preflight(
        config_source="paper_daily_loop_default_missing_config",
        generated_at=generated_at,
    )
    live_enablement_config_preflight_summary = summarize_live_enablement_config_preflight(
        live_enablement_config_preflight,
        latest_live_enablement_config_preflight_path=latest_live_enablement_config_preflight_path,
        generated_at=generated_at,
    )
    latest_telegram_operator_control_state_path = (
        normalize_path(paths["telegram_operator_control_state"]) if active_config.write_artifacts else ""
    )
    latest_telegram_mini_app_operator_panel_json_path = (
        normalize_path(paths["telegram_mini_app_operator_panel_json"]) if active_config.write_artifacts else ""
    )
    latest_telegram_mini_app_operator_panel_html_path = (
        normalize_path(paths["telegram_mini_app_operator_panel_html"]) if active_config.write_artifacts else ""
    )
    live_credentials_auth_boundary_config = build_default_live_credentials_boundary_config(
        generated_at=generated_at,
    )
    live_credentials_auth_boundary = evaluate_live_auth_boundary_for_tiny_canary(
        live_credentials_auth_boundary_config,
        generated_at=generated_at,
    )
    live_credentials_auth_boundary_summary = summarize_live_credentials_status(
        live_credentials_auth_boundary,
        generated_at=generated_at,
    )
    live_credentials_auth_boundary_summary["latest_live_credentials_auth_boundary_path"] = (
        latest_live_credentials_auth_boundary_path
    )
    btc_read_only_config = build_default_btc_read_only_config(generated_at=generated_at)
    btc_read_only_connector = PolymarketBTCReadOnlyConnector(btc_read_only_config)
    btc_read_only_connector_result = btc_read_only_connector.build_snapshot_from_fixture_payload(
        build_default_btc_fixture_market_payload(observed_at=generated_at),
        current_time=generated_at,
    )
    btc_market_snapshot = dict(btc_read_only_connector_result.get("snapshot") or {})
    btc_market_snapshot_summary = summarize_btc_market_snapshot(btc_market_snapshot)
    btc_market_snapshot_summary["latest_btc_market_snapshot_path"] = latest_btc_market_snapshot_path
    btc_read_only_connector_summary = {
        "contract_version": "pmbot_polymarket_btc_read_only_connector_daily_summary.v1",
        "config_id": btc_read_only_config.get("config_id"),
        "result_id": btc_read_only_connector_result.get("result_id"),
        "status": btc_read_only_connector_result.get("status"),
        "success": btc_read_only_connector_result.get("success") is True,
        "snapshot_id": btc_market_snapshot.get("snapshot_id", ""),
        "read_only": True,
        "network_enabled": btc_read_only_config.get("network_enabled") is True,
        "read_only_network_enabled": btc_read_only_config.get("network_enabled") is True,
        "network_attempted": btc_read_only_connector_result.get("network_attempted") is True,
        "external_api_calls_performed": btc_read_only_connector_result.get("external_api_calls_performed") is True,
        "authenticated_requests_supported": False,
        "order_submission_supported": False,
        "wallet_required": False,
        "execution_enabling": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        **btc_market_snapshot_summary,
    }
    risk_limit_policy = build_default_risk_limit_policy(generated_at=generated_at)
    btc_analysis_order_intent_result = evaluate_btc_analysis_to_order_intent(
        btc_market_snapshot,
        policy=risk_limit_policy,
        operator_intent_reference=clean_text(operator_intent_packet.get("packet_id"))
        or "live_canary_operator_intent_packet:current-run",
        readiness_evidence_reference=(
            latest_readiness_evidence_bundle_path or "live_canary_readiness_evidence_bundle:current-run"
        ),
        audit_replay_reference=live_connector_audit_replay.get("replay_id", "live_connector_audit_replay:current-run"),
        ui_panel_reference=normalize_path(paths["operator_ui_panel_json"]) if active_config.write_artifacts else "",
        latest_btc_analysis_path=latest_btc_analysis_path,
        latest_btc_order_intent_path=latest_btc_order_intent_path,
        latest_btc_risk_decision_path=latest_btc_risk_decision_path,
        live_auth_boundary_decision=live_credentials_auth_boundary,
        generated_at=generated_at,
    )
    btc_market_analysis = dict(btc_analysis_order_intent_result.get("analysis") or {})
    btc_order_intent_dry_run = dict(btc_analysis_order_intent_result.get("order_intent_plan") or {})
    latest_risk_limit_decision = dict(btc_analysis_order_intent_result.get("risk_decision") or {})
    btc_risk_decision_summary = dict(btc_analysis_order_intent_result.get("risk_decision_summary") or {})
    risk_control_plane_summary = dict(btc_analysis_order_intent_result.get("risk_control_plane_summary") or {})
    btc_analysis_order_intent_summary = summarize_btc_analysis_order_intent(
        btc_analysis_order_intent_result,
        latest_btc_analysis_path=latest_btc_analysis_path,
        latest_btc_order_intent_path=latest_btc_order_intent_path,
        latest_btc_risk_decision_path=latest_btc_risk_decision_path,
        generated_at=generated_at,
    )
    live_order_submission_boundary = build_live_order_submission_boundary_receipt(
        btc_dry_run_order_intent=btc_analysis_order_intent_result,
        risk_decision=latest_risk_limit_decision,
        risk_decision_summary=btc_risk_decision_summary,
        risk_control_plane_summary=risk_control_plane_summary,
        live_credentials_auth_boundary=live_credentials_auth_boundary,
        live_credentials_auth_boundary_summary=live_credentials_auth_boundary_summary,
        operator_approval_packet=operator_live_approval_packet,
        operator_intent_packet=operator_intent_packet,
        kill_switch_context=tiny_live_canary_kill_switch_validation,
        blocker_matrix=live_connector_blocker_matrix,
        generated_at=generated_at,
    )
    live_order_submission_boundary_summary = summarize_live_order_submission_boundary_receipt(
        live_order_submission_boundary,
        latest_live_order_submission_boundary_path=latest_live_order_submission_boundary_path,
        generated_at=generated_at,
    )
    provisional_tiny_live_canary_gonogo_gate = build_tiny_live_canary_gonogo_gate(
        market_id=clean_text(btc_market_snapshot_summary.get("market_id")),
        market_slug=clean_text(btc_market_snapshot_summary.get("market_slug")),
        btc_market_snapshot_summary=btc_market_snapshot_summary,
        btc_analysis_summary=btc_analysis_order_intent_summary,
        dry_run_order_intent_summary=btc_analysis_order_intent_summary,
        risk_limit_summary=risk_control_plane_summary,
        auth_boundary_summary=live_credentials_auth_boundary_summary,
        order_submission_boundary_summary=live_order_submission_boundary_summary,
        operator_signed_intent_summary=summarize_live_canary_operator_intent_packet(
            operator_intent_packet,
            latest_operator_intent_packet_path=latest_operator_intent_packet_path,
            generated_at=generated_at,
        ),
        readiness_evidence_summary={},
        live_enablement_config_preflight_summary=live_enablement_config_preflight_summary,
        kill_switch_summary=tiny_live_canary_kill_switch_validation,
        blocker_matrix=live_connector_blocker_matrix,
        latest_tiny_live_canary_gonogo_gate_path=latest_tiny_live_canary_gonogo_gate_path,
        generated_at=generated_at,
    )
    provisional_tiny_live_canary_gonogo_gate_summary = summarize_tiny_live_canary_gonogo_gate(
        provisional_tiny_live_canary_gonogo_gate,
        latest_tiny_live_canary_gonogo_gate_path=latest_tiny_live_canary_gonogo_gate_path,
        generated_at=generated_at,
    )
    telegram_operator_control_config = build_telegram_operator_control_config(generated_at=generated_at)
    telegram_operator_control_state = build_telegram_operator_control_state(generated_at=generated_at)
    provisional_telegram_operator_control_bot_summary = build_telegram_operator_control_summary(
        config=telegram_operator_control_config,
        state=telegram_operator_control_state,
        context={
            "btc_market_snapshot_summary": btc_market_snapshot_summary,
            "btc_analysis_order_intent_summary": btc_analysis_order_intent_summary,
            "risk_control_plane_summary": risk_control_plane_summary,
            "live_credentials_auth_boundary_summary": live_credentials_auth_boundary_summary,
            "live_order_submission_boundary_summary": live_order_submission_boundary_summary,
            "tiny_live_canary_gonogo_gate_summary": provisional_tiny_live_canary_gonogo_gate_summary,
            "live_connector_blocker_matrix": live_connector_blocker_matrix,
            "latest_telegram_operator_control_state_path": latest_telegram_operator_control_state_path,
        },
        latest_state_path=latest_telegram_operator_control_state_path,
        generated_at=generated_at,
    )
    provisional_telegram_mini_app_operator_panel_summary = build_telegram_mini_app_panel_artifact_summary(
        latest_panel_html_path=latest_telegram_mini_app_operator_panel_html_path,
        latest_panel_json_path=latest_telegram_mini_app_operator_panel_json_path,
        panel_artifact_available=active_config.write_artifacts,
        generated_at=generated_at,
    )
    readiness_evidence_bundle = build_live_canary_readiness_evidence_bundle(
        disabled_connector_status=build_disabled_connector_passive_status(
            result=disabled_connector_result,
            latest_disabled_connector_audit_path=(
                normalize_path(paths["disabled_connector_audit"]) if active_config.write_artifacts else ""
            ),
            live_canary_replay_acceptance_status="passed",
        ),
        disabled_connector_audit=disabled_connector_audit,
        secret_boundary_validation=live_connector_audit_replay.get("secret_boundary_validation_summary", {}),
        live_credentials_auth_boundary=live_credentials_auth_boundary_summary,
        live_canary_readiness_packet=canary_readiness_packet,
        canary_replay_acceptance={"status": "passed", "contract_version": "pmbot_live_canary_acceptance_matrix.v1"},
        live_connector_audit_replay=live_connector_audit_replay,
        operator_approval_packet=operator_live_approval_packet,
        tiny_live_canary_preflight_contract=tiny_live_canary_preflight_contract,
        tiny_live_canary_manual_runbook=tiny_live_canary_manual_runbook,
        operator_intent_packet=operator_intent_packet,
        blocker_matrix=live_connector_blocker_matrix,
        kill_switch_validation=tiny_live_canary_kill_switch_validation,
        preflight_result=tiny_live_canary_preflight_result,
        risk_limit_control_plane=risk_control_plane_summary,
        btc_read_only_market_connector=btc_read_only_connector_summary,
        btc_analysis_order_intent_dry_run=btc_analysis_order_intent_summary,
        live_order_submission_boundary_dry_run_adapter=live_order_submission_boundary_summary,
        tiny_live_canary_gonogo_gate=provisional_tiny_live_canary_gonogo_gate_summary,
        live_enablement_config_preflight=live_enablement_config_preflight,
        live_enablement_config_preflight_summary=live_enablement_config_preflight_summary,
        telegram_operator_control_bot_v1=provisional_telegram_operator_control_bot_summary,
        telegram_mini_app_operator_panel_v1=provisional_telegram_mini_app_operator_panel_summary,
        dry_run_receipt_references=[canary_dry_run_receipt.get("receipt_id", "")],
        result_artifact_references=[
            normalize_path(paths["result"]) if active_config.write_artifacts else "paper_daily_loop_result:current-run",
        ],
        artifact_reference_overrides={
            "disabled_connector_adapter_status": (
                normalize_path(paths["disabled_connector_audit"]) if active_config.write_artifacts else ""
            ),
            "live_canary_readiness_packet": (
                normalize_path(paths["canary_readiness_packet"]) if active_config.write_artifacts else ""
            ),
            "canary_replay_acceptance": "live_canary_acceptance_matrix:generated-governance-summary",
            "live_connector_audit_replay": (
                normalize_path(paths["live_connector_audit_replay"]) if active_config.write_artifacts else ""
            ),
            "operator_live_approval_packet": (
                normalize_path(paths["operator_live_approval_packet"]) if active_config.write_artifacts else ""
            ),
            "tiny_live_canary_preflight_contract": (
                normalize_path(paths["tiny_live_canary_preflight_contract"]) if active_config.write_artifacts else ""
            ),
            "tiny_live_canary_manual_runbook": (
                normalize_path(paths["tiny_live_canary_manual_runbook"]) if active_config.write_artifacts else ""
            ),
            "dry_run_operator_intent_packet": latest_operator_intent_packet_path,
            "live_credentials_auth_boundary": latest_live_credentials_auth_boundary_path,
            "live_connector_blocker_matrix": "live_connector_blocker_matrix:all-critical-blockers-unresolved",
            "kill_switch_requirements": (
                normalize_path(paths["tiny_live_canary_preflight_contract"]) if active_config.write_artifacts else ""
            ),
            "abort_conditions": (
                normalize_path(paths["tiny_live_canary_manual_runbook"]) if active_config.write_artifacts else ""
            ),
            "evidence_capture_checklist": (
                normalize_path(paths["tiny_live_canary_manual_runbook"]) if active_config.write_artifacts else ""
            ),
            "risk_review": canary_readiness_packet.get("risk_decision_id", ""),
            "risk_limit_control_plane": risk_control_plane_summary.get("policy_id", ""),
            "btc_read_only_market_connector": latest_btc_market_snapshot_path,
            "btc_market_analysis_to_order_intent_dry_run": latest_btc_order_intent_path,
            "live_order_submission_boundary_dry_run_adapter": latest_live_order_submission_boundary_path,
            "tiny_live_canary_manual_execution_checklist_and_final_gonogo_gate": (
                latest_tiny_live_canary_gonogo_gate_path
            ),
            "live_enablement_config_contract_and_runtime_preflight": (
                latest_live_enablement_config_preflight_path
                or "live_enablement_config_preflight_047:review_only_non_execution"
            ),
            "telegram_operator_control_bot_v1": latest_telegram_operator_control_state_path
            or "telegram_operator_control_bot_v1:review_only_non_execution",
            "telegram_mini_app_operator_panel_v1": latest_telegram_mini_app_operator_panel_html_path
            or "telegram_mini_app_operator_panel_v1:review_only_static_artifact",
        },
        generated_at=generated_at,
    )
    readiness_evidence_bundle_summary = summarize_live_canary_readiness_evidence_bundle(
        readiness_evidence_bundle,
        latest_readiness_evidence_bundle_path=latest_readiness_evidence_bundle_path,
        generated_at=generated_at,
    )
    tiny_live_canary_gonogo_gate = build_tiny_live_canary_gonogo_gate(
        market_id=clean_text(btc_market_snapshot_summary.get("market_id")),
        market_slug=clean_text(btc_market_snapshot_summary.get("market_slug")),
        btc_market_snapshot_summary=btc_market_snapshot_summary,
        btc_analysis_summary=btc_analysis_order_intent_summary,
        dry_run_order_intent_summary=btc_analysis_order_intent_summary,
        risk_limit_summary=risk_control_plane_summary,
        auth_boundary_summary=live_credentials_auth_boundary_summary,
        order_submission_boundary_summary=live_order_submission_boundary_summary,
        operator_signed_intent_summary=summarize_live_canary_operator_intent_packet(
            operator_intent_packet,
            latest_operator_intent_packet_path=latest_operator_intent_packet_path,
            generated_at=generated_at,
        ),
        readiness_evidence_summary=readiness_evidence_bundle_summary,
        live_enablement_config_preflight_summary=live_enablement_config_preflight_summary,
        kill_switch_summary=tiny_live_canary_kill_switch_validation,
        blocker_matrix=live_connector_blocker_matrix,
        latest_tiny_live_canary_gonogo_gate_path=latest_tiny_live_canary_gonogo_gate_path,
        generated_at=generated_at,
    )
    tiny_live_canary_gonogo_gate_summary = summarize_tiny_live_canary_gonogo_gate(
        tiny_live_canary_gonogo_gate,
        latest_tiny_live_canary_gonogo_gate_path=latest_tiny_live_canary_gonogo_gate_path,
        generated_at=generated_at,
    )
    telegram_operator_control_bot_summary = build_telegram_operator_control_summary(
        config=telegram_operator_control_config,
        state=telegram_operator_control_state,
        context={
            "btc_market_snapshot_summary": btc_market_snapshot_summary,
            "btc_analysis_order_intent_summary": btc_analysis_order_intent_summary,
            "risk_control_plane_summary": risk_control_plane_summary,
            "live_credentials_auth_boundary_summary": live_credentials_auth_boundary_summary,
            "live_order_submission_boundary_summary": live_order_submission_boundary_summary,
            "tiny_live_canary_gonogo_gate_summary": tiny_live_canary_gonogo_gate_summary,
            "readiness_evidence_bundle_summary": readiness_evidence_bundle_summary,
            "live_connector_blocker_matrix": live_connector_blocker_matrix,
            "telegram_mini_app_operator_panel_summary": provisional_telegram_mini_app_operator_panel_summary,
            "latest_telegram_operator_control_state_path": latest_telegram_operator_control_state_path,
        },
        latest_state_path=latest_telegram_operator_control_state_path,
        generated_at=generated_at,
    )
    for review_artifact in (operator_live_approval_packet, operator_intent_packet, live_connector_audit_replay):
        review_artifact["readiness_evidence_bundle_status"] = readiness_evidence_bundle.get("bundle_status")
        review_artifact["readiness_evidence_bundle_review_ready"] = (
            readiness_evidence_bundle.get("evidence_bundle_review_ready") is True
        )
        review_artifact["readiness_evidence_bundle_is_not_live_approval"] = True
        review_artifact["readiness_evidence_bundle_reference"] = (
            latest_readiness_evidence_bundle_path or readiness_evidence_bundle.get("bundle_id", "")
        )
    tiny_live_canary_preflight_result["readiness_evidence_bundle_status"] = readiness_evidence_bundle.get(
        "bundle_status"
    )
    tiny_live_canary_preflight_result["readiness_evidence_bundle_review_ready"] = (
        readiness_evidence_bundle.get("evidence_bundle_review_ready") is True
    )
    tiny_live_canary_preflight_result["readiness_evidence_bundle_is_not_live_approval"] = True
    strategy_ledger["live_connector_audit_replay_status"] = live_connector_audit_replay.get("status")
    strategy_ledger["operator_review_packet_status"] = operator_live_approval_packet.get("operator_packet_status")
    strategy_ledger["operator_intent_packet_status"] = operator_intent_packet.get("intent_packet_status")
    strategy_ledger["operator_intent_packet_review_ready"] = (
        operator_intent_packet.get("operator_intent_packet_review_ready") is True
    )
    strategy_ledger["operator_intent_is_not_live_approval"] = True
    strategy_ledger["tiny_live_canary_preflight_status"] = tiny_live_canary_preflight_result.get("status")
    strategy_ledger["manual_runbook_status"] = tiny_live_canary_manual_runbook.get("status")
    strategy_ledger["readiness_evidence_bundle_status"] = readiness_evidence_bundle.get("bundle_status")
    strategy_ledger["readiness_evidence_bundle_review_ready"] = (
        readiness_evidence_bundle.get("evidence_bundle_review_ready") is True
    )
    strategy_ledger["readiness_evidence_bundle_is_not_live_approval"] = True
    strategy_ledger["canary_executable_now"] = False
    strategy_ledger["live_execution_approved"] = False
    strategy_ledger["real_execution_available"] = False
    strategy_ledger["live_connector_enabled"] = False
    strategy_summary["live_connector_audit_replay_status"] = live_connector_audit_replay.get("status")
    strategy_summary["operator_review_packet_status"] = operator_live_approval_packet.get("operator_packet_status")
    strategy_summary["operator_intent_packet_status"] = operator_intent_packet.get("intent_packet_status")
    strategy_summary["operator_intent_packet_review_ready"] = (
        operator_intent_packet.get("operator_intent_packet_review_ready") is True
    )
    strategy_summary["operator_intent_is_not_live_approval"] = True
    strategy_summary["tiny_live_canary_preflight_status"] = tiny_live_canary_preflight_result.get("status")
    strategy_summary["manual_runbook_status"] = tiny_live_canary_manual_runbook.get("status")
    strategy_summary["readiness_evidence_bundle_status"] = readiness_evidence_bundle.get("bundle_status")
    strategy_summary["readiness_evidence_bundle_review_ready"] = (
        readiness_evidence_bundle.get("evidence_bundle_review_ready") is True
    )
    strategy_summary["readiness_evidence_bundle_is_not_live_approval"] = True
    strategy_summary["canary_executable_now"] = False
    strategy_summary["live_execution_approved"] = False
    strategy_summary["real_execution_available"] = False
    strategy_summary["live_connector_enabled"] = False
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
        operator_intent_packet=operator_intent_packet,
        live_connector_blocker_matrix=live_connector_blocker_matrix,
        tiny_live_canary_preflight_contract=tiny_live_canary_preflight_contract,
        tiny_live_canary_manual_runbook=tiny_live_canary_manual_runbook,
        tiny_live_canary_preflight_result=tiny_live_canary_preflight_result,
        readiness_evidence_bundle=readiness_evidence_bundle,
        readiness_evidence_bundle_summary=readiness_evidence_bundle_summary,
        live_credentials_auth_boundary=live_credentials_auth_boundary,
        live_credentials_auth_boundary_summary=live_credentials_auth_boundary_summary,
        live_enablement_config_preflight=live_enablement_config_preflight,
        live_enablement_config_preflight_summary=live_enablement_config_preflight_summary,
        risk_limit_policy=risk_limit_policy,
        latest_risk_limit_decision=latest_risk_limit_decision,
        risk_control_plane_summary=risk_control_plane_summary,
        btc_market_snapshot=btc_market_snapshot,
        btc_market_snapshot_summary=btc_market_snapshot_summary,
        btc_read_only_connector_summary=btc_read_only_connector_summary,
        btc_market_analysis=btc_market_analysis,
        btc_order_intent_dry_run=btc_order_intent_dry_run,
        btc_risk_decision_summary=btc_risk_decision_summary,
        btc_analysis_order_intent_summary=btc_analysis_order_intent_summary,
        live_order_submission_boundary=live_order_submission_boundary,
        live_order_submission_boundary_summary=live_order_submission_boundary_summary,
        tiny_live_canary_gonogo_gate=tiny_live_canary_gonogo_gate,
        tiny_live_canary_gonogo_gate_summary=tiny_live_canary_gonogo_gate_summary,
        telegram_operator_control_state=telegram_operator_control_state,
        telegram_operator_control_bot_summary=telegram_operator_control_bot_summary,
        telegram_mini_app_operator_panel_summary=provisional_telegram_mini_app_operator_panel_summary,
        latest_disabled_connector_audit_path=(
            normalize_path(paths["disabled_connector_audit"]) if active_config.write_artifacts else ""
        ),
        latest_audit_replay_path=(
            normalize_path(paths["live_connector_audit_replay"]) if active_config.write_artifacts else ""
        ),
        latest_operator_packet_path=(
            normalize_path(paths["operator_live_approval_packet"]) if active_config.write_artifacts else ""
        ),
        latest_operator_intent_packet_path=latest_operator_intent_packet_path,
        latest_tiny_canary_contract_path=(
            normalize_path(paths["tiny_live_canary_preflight_contract"]) if active_config.write_artifacts else ""
        ),
        latest_manual_runbook_path=(
            normalize_path(paths["tiny_live_canary_manual_runbook"]) if active_config.write_artifacts else ""
        ),
        latest_readiness_evidence_bundle_path=latest_readiness_evidence_bundle_path,
        latest_live_credentials_auth_boundary_path=latest_live_credentials_auth_boundary_path,
        latest_live_enablement_config_preflight_path=latest_live_enablement_config_preflight_path,
        latest_btc_market_snapshot_path=latest_btc_market_snapshot_path,
        latest_btc_analysis_path=latest_btc_analysis_path,
        latest_btc_order_intent_path=latest_btc_order_intent_path,
        latest_btc_risk_decision_path=latest_btc_risk_decision_path,
        latest_live_order_submission_boundary_path=latest_live_order_submission_boundary_path,
        latest_tiny_live_canary_gonogo_gate_path=latest_tiny_live_canary_gonogo_gate_path,
        latest_telegram_operator_control_state_path=latest_telegram_operator_control_state_path,
        latest_telegram_mini_app_operator_panel_json_path=latest_telegram_mini_app_operator_panel_json_path,
        latest_telegram_mini_app_operator_panel_html_path=latest_telegram_mini_app_operator_panel_html_path,
        source_evidence_refresh_ledger=source_evidence_refresh_ledger,
        generated_at=generated_at,
    )
    latest_operator_ui_panel_paths = {
        "operator_ui_panel_json": normalize_path(paths["operator_ui_panel_json"]) if active_config.write_artifacts else "",
        "operator_ui_panel_md": normalize_path(paths["operator_ui_panel_md"]) if active_config.write_artifacts else "",
        "operator_ui_panel_html": normalize_path(paths["operator_ui_panel_html"]) if active_config.write_artifacts else "",
        "telegram_mini_app_operator_panel_json": latest_telegram_mini_app_operator_panel_json_path,
        "telegram_mini_app_operator_panel_html": latest_telegram_mini_app_operator_panel_html_path,
        "paper_daily_loop_result": normalize_path(paths["result"]) if active_config.write_artifacts else "",
        "readiness_evidence_bundle": latest_readiness_evidence_bundle_path,
        "live_credentials_auth_boundary": latest_live_credentials_auth_boundary_path,
        "live_enablement_config_preflight": latest_live_enablement_config_preflight_path,
        "btc_market_snapshot": latest_btc_market_snapshot_path,
        "btc_market_analysis": latest_btc_analysis_path,
        "btc_order_intent_dry_run": latest_btc_order_intent_path,
        "btc_risk_decision": latest_btc_risk_decision_path,
        "live_order_submission_boundary": latest_live_order_submission_boundary_path,
        "tiny_live_canary_gonogo_gate": latest_tiny_live_canary_gonogo_gate_path,
        "operator_live_approval_packet": (
            normalize_path(paths["operator_live_approval_packet"]) if active_config.write_artifacts else ""
        ),
        "operator_intent_packet": latest_operator_intent_packet_path,
        "live_connector_audit_replay": (
            normalize_path(paths["live_connector_audit_replay"]) if active_config.write_artifacts else ""
        ),
        "tiny_live_canary_preflight_contract": (
            normalize_path(paths["tiny_live_canary_preflight_contract"]) if active_config.write_artifacts else ""
        ),
        "telegram_operator_control_state": latest_telegram_operator_control_state_path,
    }
    operator_ui_panel_v1 = build_operator_ui_panel_v1(
        dashboard=dashboard,
        readiness_evidence_bundle=readiness_evidence_bundle,
        readiness_evidence_bundle_summary=readiness_evidence_bundle_summary,
        blocker_matrix=live_connector_blocker_matrix,
        risk_limit_policy=risk_limit_policy,
        latest_risk_limit_decision=latest_risk_limit_decision,
        risk_control_plane_summary=risk_control_plane_summary,
        btc_market_snapshot=btc_market_snapshot,
        btc_read_only_connector_summary=btc_market_snapshot_summary,
        btc_analysis_order_intent_summary=btc_analysis_order_intent_summary,
        live_order_submission_boundary_receipt=live_order_submission_boundary,
        live_order_submission_boundary_summary=live_order_submission_boundary_summary,
        live_enablement_config_preflight=live_enablement_config_preflight,
        live_enablement_config_preflight_summary=live_enablement_config_preflight_summary,
        tiny_live_canary_gonogo_gate=tiny_live_canary_gonogo_gate,
        tiny_live_canary_gonogo_gate_summary=tiny_live_canary_gonogo_gate_summary,
        live_credentials_auth_boundary_summary=live_credentials_auth_boundary_summary,
        risk_limits=limits,
        risk_prep_config=risk_prep_config,
        portfolio_summary=portfolio_report.get("exposure_summary", {}),
        portfolio_state=portfolio_state,
        strategy_summary=strategy_summary,
        canary_readiness_summary=dashboard.get("live_canary_readiness_summary", {}),
        tiny_live_canary_preflight_result=tiny_live_canary_preflight_result,
        tiny_live_canary_preflight_contract=tiny_live_canary_preflight_contract,
        tiny_live_canary_manual_runbook=tiny_live_canary_manual_runbook,
        operator_live_approval_packet=operator_live_approval_packet,
        operator_intent_packet=operator_intent_packet,
        operator_intent_summary=dashboard.get("operator_intent_packet_summary", {}),
        live_connector_audit_replay=live_connector_audit_replay,
        live_connector_audit_operator_summary=dashboard.get("live_connector_audit_operator_summary", {}),
        telegram_operator_control_bot_summary=telegram_operator_control_bot_summary,
        telegram_mini_app_operator_panel_summary=provisional_telegram_mini_app_operator_panel_summary,
        latest_paths=latest_operator_ui_panel_paths,
        generated_at=generated_at,
    )
    dashboard["operator_ui_panel_v1_summary"] = summarize_operator_ui_panel_v1(operator_ui_panel_v1)
    dashboard["operator_ui_panel_v1_paths"] = latest_operator_ui_panel_paths
    telegram_mini_app_operator_panel = build_telegram_mini_app_panel_model(
        dashboard=dashboard,
        operator_ui_panel=operator_ui_panel_v1,
        telegram_operator_control_summary=telegram_operator_control_bot_summary,
        latest_panel_html_path=latest_telegram_mini_app_operator_panel_html_path,
        latest_panel_json_path=latest_telegram_mini_app_operator_panel_json_path,
        generated_at=generated_at,
    )
    telegram_mini_app_operator_panel_summary = summarize_telegram_mini_app_panel_model(
        telegram_mini_app_operator_panel
    )
    dashboard["telegram_mini_app_operator_panel_summary"] = telegram_mini_app_operator_panel_summary
    dashboard["telegram_mini_app_operator_panel_paths"] = {
        "telegram_mini_app_operator_panel_html": latest_telegram_mini_app_operator_panel_html_path,
        "telegram_mini_app_operator_panel_json": latest_telegram_mini_app_operator_panel_json_path,
    }
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
            operator_intent_packet,
            live_connector_blocker_matrix,
            btc_read_only_config,
            btc_read_only_connector_result,
            btc_market_snapshot,
            btc_market_snapshot_summary,
            btc_read_only_connector_summary,
            btc_analysis_order_intent_result,
            btc_market_analysis,
            btc_order_intent_dry_run,
            btc_risk_decision_summary,
            btc_analysis_order_intent_summary,
            live_order_submission_boundary,
            live_order_submission_boundary_summary,
            live_enablement_config_preflight,
            live_enablement_config_preflight_summary,
            tiny_live_canary_gonogo_gate,
            tiny_live_canary_gonogo_gate_summary,
            live_credentials_auth_boundary,
            live_credentials_auth_boundary_summary,
            risk_limit_policy,
            latest_risk_limit_decision or {},
            risk_control_plane_summary,
            readiness_evidence_bundle,
            telegram_operator_control_config,
            telegram_operator_control_state,
            telegram_operator_control_bot_summary,
            telegram_mini_app_operator_panel,
            telegram_mini_app_operator_panel_summary,
            tiny_live_canary_preflight_contract,
            tiny_live_canary_manual_runbook,
            tiny_live_canary_kill_switch_validation,
            tiny_live_canary_preflight_result,
            operator_ui_panel_v1,
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
        and btc_read_only_config.get("network_enabled") is False
        and btc_read_only_config.get("authenticated") is False
        and btc_read_only_config.get("order_submission_supported") is False
        and btc_read_only_config.get("wallet_required") is False
        and btc_read_only_connector_result.get("success") is True
        and btc_read_only_connector_result.get("network_attempted") is False
        and btc_read_only_connector_result.get("external_api_calls_performed") is False
        and btc_market_snapshot.get("is_btc_related") is True
        and btc_market_snapshot.get("stale") is False
        and btc_market_snapshot.get("risk_control_market_data_status") == "fresh_open_btc_market"
        and btc_market_snapshot_summary.get("read_only_network_enabled") is False
        and btc_read_only_connector_summary.get("order_submission_supported") is False
        and btc_read_only_connector_summary.get("authenticated_requests_supported") is False
        and btc_market_analysis.get("analysis_status") == "analysis_ready_for_dry_run_intent"
        and btc_market_analysis.get("analysis_is_not_live_recommendation") is True
        and btc_order_intent_dry_run.get("dry_run_order_intent_status") == "dry_run_intent_candidate_ready"
        and btc_order_intent_dry_run.get("order_intent_is_not_order_submission") is True
        and btc_risk_decision_summary.get("risk_decision_status") == "ALLOW_DRY_RUN"
        and btc_risk_decision_summary.get("allowed_for_dry_run") is True
        and btc_risk_decision_summary.get("allowed_for_live") is False
        and btc_analysis_order_intent_summary.get("analysis_is_not_live_recommendation") is True
        and btc_analysis_order_intent_summary.get("order_intent_is_not_order_submission") is True
        and btc_analysis_order_intent_summary.get("allowed_for_live") is False
        and live_order_submission_boundary.get("status") == "dry_run_submission_boundary_review_ready"
        and live_order_submission_boundary.get("allowed_for_dry_run_review") is True
        and live_order_submission_boundary.get("dry_run_submission_boundary_ready") is True
        and live_order_submission_boundary.get("boundary_is_not_live_approval") is True
        and live_order_submission_boundary.get("receipt_is_not_order_submission") is True
        and live_order_submission_boundary.get("would_submit_order") is False
        and live_order_submission_boundary.get("order_submission_enabled") is False
        and live_order_submission_boundary.get("authenticated_endpoint_required") is True
        and live_order_submission_boundary.get("authenticated_endpoint_enabled") is False
        and live_order_submission_boundary.get("authenticated_endpoints_enabled") is False
        and live_order_submission_boundary.get("signing_required_for_future_live") is True
        and live_order_submission_boundary.get("signing_enabled") is False
        and live_order_submission_boundary.get("cryptographic_signing_enabled") is False
        and live_order_submission_boundary.get("wallet_required_for_future_live") is True
        and live_order_submission_boundary.get("wallet_enabled") is False
        and live_order_submission_boundary.get("wallet_signing_enabled") is False
        and live_order_submission_boundary.get("allowed_for_live") is False
        and live_order_submission_boundary.get("live_execution_approved") is False
        and live_order_submission_boundary.get("real_execution_available") is False
        and live_order_submission_boundary.get("canary_executable_now") is False
        and live_order_submission_boundary.get("live_connector_enabled") is False
        and live_order_submission_boundary.get("real_order_submitted") is False
        and live_order_submission_boundary.get("execution_claimed") is False
        and live_order_submission_boundary.get("fill_claimed") is False
        and live_order_submission_boundary.get("network_used") is False
        and live_order_submission_boundary.get("external_api_calls_performed") is False
        and live_order_submission_boundary.get("environment_secrets_read") is False
        and live_order_submission_boundary.get("secrets_read") is False
        and live_order_submission_boundary.get("actual_secret_values_exposed") is False
        and live_order_submission_boundary.get("validation", {}).get("valid") is True
        and live_order_submission_boundary_summary.get("dry_run_review_ready") is True
        and live_order_submission_boundary_summary.get("order_submission_enabled") is False
        and live_order_submission_boundary_summary.get("would_submit_order") is False
        and live_order_submission_boundary_summary.get("authenticated_endpoint_enabled") is False
        and live_order_submission_boundary_summary.get("signing_enabled") is False
        and live_order_submission_boundary_summary.get("wallet_enabled") is False
        and live_order_submission_boundary_summary.get("allowed_for_live") is False
        and live_order_submission_boundary_summary.get("live_execution_approved") is False
        and live_order_submission_boundary_summary.get("real_execution_available") is False
        and live_order_submission_boundary_summary.get("canary_executable_now") is False
        and live_enablement_config_preflight.get("status") == "CONFIG_MISSING_BLOCKED"
        and live_enablement_config_preflight.get("future_live_requested") is False
        and live_enablement_config_preflight.get("dry_run_review_allowed") is False
        and live_enablement_config_preflight.get("allowed_for_live") is False
        and live_enablement_config_preflight.get("canary_executable_now") is False
        and live_enablement_config_preflight.get("live_execution_approved") is False
        and live_enablement_config_preflight.get("real_execution_available") is False
        and live_enablement_config_preflight.get("live_connector_enabled") is False
        and live_enablement_config_preflight.get("order_submission_enabled") is False
        and live_enablement_config_preflight.get("authenticated_polymarket_enabled") is False
        and live_enablement_config_preflight.get("wallet_signing_enabled") is False
        and live_enablement_config_preflight.get("resolved_blocker_count") == 0
        and live_enablement_config_preflight.get("validation", {}).get("valid") is True
        and live_enablement_config_preflight_summary.get("status") == "CONFIG_MISSING_BLOCKED"
        and live_enablement_config_preflight_summary.get("allowed_for_live") is False
        and live_enablement_config_preflight_summary.get("no_executable_action") is True
        and live_credentials_auth_boundary.get("live_credentials_boundary_ready") is True
        and live_credentials_auth_boundary.get("live_auth_presence_check_ready") is True
        and live_credentials_auth_boundary.get("redacted_credential_status_ready") is True
        and live_credentials_auth_boundary.get("safe_for_artifacts") is True
        and live_credentials_auth_boundary.get("secrets_redacted") is True
        and live_credentials_auth_boundary.get("actual_secret_values_exposed") is False
        and live_credentials_auth_boundary.get("authenticated_endpoints_enabled") is False
        and live_credentials_auth_boundary.get("order_submission_enabled") is False
        and live_credentials_auth_boundary.get("cryptographic_signing_enabled") is False
        and live_credentials_auth_boundary.get("wallet_signing_enabled") is False
        and live_credentials_auth_boundary.get("allowed_for_live") is False
        and live_credentials_auth_boundary.get("canary_executable_now") is False
        and live_credentials_auth_boundary.get("live_execution_approved") is False
        and live_credentials_auth_boundary.get("real_execution_available") is False
        and live_credentials_auth_boundary.get("live_connector_enabled") is False
        and live_credentials_auth_boundary_summary.get("redacted_credential_status_ready") is True
        and live_credentials_auth_boundary_summary.get("actual_secret_values_exposed") is False
        and live_credentials_auth_boundary_summary.get("authenticated_endpoints_enabled") is False
        and live_credentials_auth_boundary_summary.get("order_submission_enabled") is False
        and live_credentials_auth_boundary_summary.get("cryptographic_signing_enabled") is False
        and live_credentials_auth_boundary_summary.get("wallet_signing_enabled") is False
        and live_credentials_auth_boundary_summary.get("allowed_for_live") is False
        and live_credentials_auth_boundary_summary.get("canary_executable_now") is False
        and operator_live_approval_packet.get("operator_packet_status") == "operator_review_ready"
        and operator_live_approval_packet.get("operator_review_ready") is True
        and operator_live_approval_packet.get("live_execution_approved") is False
        and operator_live_approval_packet.get("real_execution_available") is False
        and operator_live_approval_packet.get("live_connector_enabled") is False
        and operator_live_approval_packet.get("operator_intent_is_not_live_approval") is True
        and operator_intent_packet.get("intent_packet_status") == "operator_intent_packet_review_ready"
        and operator_intent_packet.get("operator_intent_packet_review_ready") is True
        and operator_intent_packet.get("operator_intent_is_not_live_approval") is True
        and operator_intent_packet.get("operator_signed_intent_is_human_acknowledgement_only") is True
        and operator_intent_packet.get("live_execution_approved") is False
        and operator_intent_packet.get("real_execution_available") is False
        and operator_intent_packet.get("canary_executable_now") is False
        and tiny_live_canary_preflight_contract.get("preflight_contract_ready") is True
        and tiny_live_canary_manual_runbook.get("manual_runbook_ready") is True
        and tiny_live_canary_kill_switch_validation.get("requirements_defined") is True
        and tiny_live_canary_kill_switch_validation.get("verified_for_live") is False
        and tiny_live_canary_preflight_result.get("preflight_contract_ready") is True
        and tiny_live_canary_preflight_result.get("manual_runbook_ready") is True
        and tiny_live_canary_preflight_result.get("future_canary_shape_defined") is True
        and tiny_live_canary_preflight_result.get("canary_executable_now") is False
        and tiny_live_canary_preflight_result.get("live_execution_approved") is False
        and tiny_live_canary_preflight_result.get("real_execution_available") is False
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
        and dashboard.get("operator_intent_packet_summary", {}).get("operator_intent_packet_review_ready") is True
        and dashboard.get("operator_intent_packet_summary", {}).get("operator_intent_is_not_live_approval") is True
        and dashboard.get("operator_intent_packet_summary", {}).get("canary_executable_now") is False
        and dashboard.get("operator_intent_packet_summary", {}).get("live_execution_approved") is False
        and dashboard.get("operator_intent_packet_summary", {}).get("real_execution_available") is False
        and readiness_evidence_bundle.get("evidence_bundle_review_ready") is True
        and readiness_evidence_bundle.get("readiness_evidence_bundle_is_not_live_approval") is True
        and readiness_evidence_bundle.get("canary_executable_now") is False
        and readiness_evidence_bundle.get("live_execution_approved") is False
        and readiness_evidence_bundle.get("real_execution_available") is False
        and readiness_evidence_bundle.get("live_connector_enabled") is False
        and dashboard.get("readiness_evidence_bundle_summary", {}).get("readiness_evidence_bundle_review_ready") is True
        and dashboard.get("readiness_evidence_bundle_summary", {}).get("readiness_evidence_bundle_is_not_live_approval")
        is True
        and dashboard.get("readiness_evidence_bundle_summary", {}).get("canary_executable_now") is False
        and dashboard.get("readiness_evidence_bundle_summary", {}).get("live_execution_approved") is False
        and dashboard.get("readiness_evidence_bundle_summary", {}).get("real_execution_available") is False
        and dashboard.get("readiness_evidence_bundle_summary", {}).get("live_connector_enabled") is False
        and risk_limit_policy.get("risk_control_plane_ready") is True
        and risk_limit_policy.get("risk_limits_enforced_for_order_intents") is True
        and risk_limit_policy.get("live_execution_approved") is False
        and risk_limit_policy.get("canary_executable_now") is False
        and risk_limit_policy.get("real_execution_available") is False
        and risk_limit_policy.get("live_connector_enabled") is False
        and risk_control_plane_summary.get("risk_control_plane_ready") is True
        and risk_control_plane_summary.get("risk_limits_enforced_for_order_intents") is True
        and risk_control_plane_summary.get("market_data_status") == "fresh_open_btc_market"
        and risk_control_plane_summary.get("allowed_for_live") is False
        and risk_control_plane_summary.get("live_execution_approved") is False
        and risk_control_plane_summary.get("canary_executable_now") is False
        and risk_control_plane_summary.get("real_execution_available") is False
        and risk_control_plane_summary.get("live_connector_enabled") is False
        and (not latest_risk_limit_decision or latest_risk_limit_decision.get("allowed_for_live") is False)
        and dashboard.get("tiny_live_canary_preflight_runbook_summary", {}).get("canary_executable_now") is False
        and dashboard.get("tiny_live_canary_preflight_runbook_summary", {}).get("live_execution_approved") is False
        and dashboard.get("tiny_live_canary_preflight_runbook_summary", {}).get("real_execution_available") is False
        and operator_ui_panel_v1.get("operator_ui_panel_ready") is True
        and operator_ui_panel_v1.get("readiness_panel_render_ready") is True
        and operator_ui_panel_v1.get("risk_limit_panel_render_ready") is True
        and operator_ui_panel_v1.get("kill_switch_panel_render_ready") is True
        and operator_ui_panel_v1.get("ui_panel_is_not_live_execution_console") is True
        and operator_ui_panel_v1.get("ui_exposes_no_executable_live_action") is True
        and operator_ui_panel_v1.get("canary_executable_now") is False
        and operator_ui_panel_v1.get("live_execution_approved") is False
        and operator_ui_panel_v1.get("real_execution_available") is False
        and operator_ui_panel_v1.get("live_connector_enabled") is False
        and operator_ui_panel_v1.get("validation", {}).get("valid") is True
        and dashboard.get("operator_ui_panel_v1_summary", {}).get("operator_ui_panel_ready") is True
        and dashboard.get("operator_ui_panel_v1_summary", {}).get("live_execution_approved") is False
        and dashboard.get("operator_ui_panel_v1_summary", {}).get("canary_executable_now") is False
        and dashboard.get("operator_ui_panel_v1_summary", {}).get("real_execution_available") is False
        and dashboard.get("operator_ui_panel_v1_summary", {}).get("live_connector_enabled") is False
        and telegram_operator_control_state.get("operator_pause_requested") is False
        and telegram_operator_control_state.get("operator_kill_switch_requested") is False
        and telegram_operator_control_state.get("live_execution_approved") is False
        and telegram_operator_control_state.get("canary_executable_now") is False
        and telegram_operator_control_state.get("real_execution_available") is False
        and telegram_operator_control_state.get("live_connector_enabled") is False
        and telegram_operator_control_state.get("order_submission_enabled") is False
        and telegram_operator_control_bot_summary.get("review_only") is True
        and telegram_operator_control_bot_summary.get("execution_enabling") is False
        and telegram_operator_control_bot_summary.get("live_approval") is False
        and telegram_operator_control_bot_summary.get("allowed_for_live") is False
        and telegram_operator_control_bot_summary.get("canary_executable_now") is False
        and telegram_operator_control_bot_summary.get("live_execution_approved") is False
        and telegram_operator_control_bot_summary.get("real_execution_available") is False
        and telegram_operator_control_bot_summary.get("live_connector_enabled") is False
        and telegram_operator_control_bot_summary.get("order_submission_enabled") is False
        and dashboard.get("telegram_operator_control_bot_summary", {}).get("review_only") is True
        and dashboard.get("telegram_operator_control_bot_summary", {}).get("execution_enabling") is False
        and dashboard.get("telegram_operator_control_bot_summary", {}).get("live_execution_approved") is False
        and dashboard.get("telegram_operator_control_bot_summary", {}).get("canary_executable_now") is False
        and operator_ui_panel_v1.get("telegram_operator_control_bot_summary", {}).get(
            "telegram_operator_control_bot_section_ready"
        )
        is True
        and operator_ui_panel_v1.get("telegram_operator_control_bot_summary", {}).get("review_only") is True
        and operator_ui_panel_v1.get("telegram_operator_control_bot_summary", {}).get("execution_enabling") is False
        and telegram_mini_app_operator_panel.get("telegram_mini_app_operator_panel_ready") is True
        and telegram_mini_app_operator_panel.get("review_only") is True
        and telegram_mini_app_operator_panel.get("live_actions_available") is False
        and telegram_mini_app_operator_panel.get("execution_enabling") is False
        and telegram_mini_app_operator_panel.get("live_approval") is False
        and telegram_mini_app_operator_panel.get("allowed_for_live") is False
        and telegram_mini_app_operator_panel.get("canary_executable_now") is False
        and telegram_mini_app_operator_panel.get("live_execution_approved") is False
        and telegram_mini_app_operator_panel.get("real_execution_available") is False
        and telegram_mini_app_operator_panel.get("live_connector_enabled") is False
        and telegram_mini_app_operator_panel.get("order_submission_enabled") is False
        and telegram_mini_app_operator_panel.get("would_submit_order") is False
        and telegram_mini_app_operator_panel.get("validation", {}).get("valid") is True
        and telegram_mini_app_operator_panel_summary.get("review_only") is True
        and telegram_mini_app_operator_panel_summary.get("live_actions_available") is False
        and dashboard.get("telegram_mini_app_operator_panel_summary", {}).get("review_only") is True
        and dashboard.get("telegram_mini_app_operator_panel_summary", {}).get("live_actions_available") is False
        and operator_ui_panel_v1.get("telegram_mini_app_operator_panel_summary", {}).get(
            "telegram_mini_app_operator_panel_section_ready"
        )
        is True
        and operator_ui_panel_v1.get("telegram_mini_app_operator_panel_summary", {}).get("review_only") is True
        and operator_ui_panel_v1.get("telegram_mini_app_operator_panel_summary", {}).get("live_actions_available")
        is False
        and dashboard.get("btc_market_snapshot_summary", {}).get("is_btc_related") is True
        and dashboard.get("btc_market_snapshot_summary", {}).get("read_only_network_enabled") is False
        and dashboard.get("btc_read_only_connector_summary", {}).get("network_attempted") is False
        and dashboard.get("btc_market_analysis_summary", {}).get("btc_market_analysis_status")
        == "analysis_ready_for_dry_run_intent"
        and dashboard.get("btc_order_intent_dry_run_summary", {}).get("dry_run_order_intent_status")
        == "dry_run_intent_candidate_ready"
        and dashboard.get("btc_risk_decision_summary", {}).get("risk_decision_status") == "ALLOW_DRY_RUN"
        and dashboard.get("btc_analysis_order_intent_summary", {}).get("allowed_for_dry_run") is True
        and dashboard.get("btc_analysis_order_intent_summary", {}).get("allowed_for_live") is False
        and dashboard.get("live_order_submission_boundary_summary", {}).get("dry_run_review_ready") is True
        and dashboard.get("live_order_submission_boundary_summary", {}).get("order_submission_enabled") is False
        and dashboard.get("live_order_submission_boundary_summary", {}).get("would_submit_order") is False
        and dashboard.get("live_order_submission_boundary_summary", {}).get("allowed_for_live") is False
        and dashboard.get("live_order_submission_boundary_summary", {}).get("live_execution_approved") is False
        and dashboard.get("live_order_submission_boundary_summary", {}).get("real_execution_available") is False
        and dashboard.get("live_order_submission_boundary_summary", {}).get("canary_executable_now") is False
        and dashboard.get("live_enablement_config_preflight_summary", {}).get("status") == "CONFIG_MISSING_BLOCKED"
        and dashboard.get("live_enablement_config_preflight_summary", {}).get("allowed_for_live") is False
        and dashboard.get("live_enablement_config_preflight_summary", {}).get("canary_executable_now") is False
        and dashboard.get("live_enablement_config_preflight_summary", {}).get("live_execution_approved") is False
        and dashboard.get("live_enablement_config_preflight_summary", {}).get("real_execution_available") is False
        and dashboard.get("live_enablement_config_preflight_summary", {}).get("live_connector_enabled") is False
        and dashboard.get("live_enablement_config_preflight_summary", {}).get("order_submission_enabled") is False
        and dashboard.get("live_enablement_config_preflight_summary", {}).get("resolved_blocker_count") == 0
        and dashboard.get("live_credentials_auth_boundary_summary", {}).get("redacted_credential_status_ready")
        is True
        and dashboard.get("live_credentials_auth_boundary_summary", {}).get("actual_secret_values_exposed") is False
        and dashboard.get("live_credentials_auth_boundary_summary", {}).get("authenticated_endpoints_enabled") is False
        and dashboard.get("live_credentials_auth_boundary_summary", {}).get("order_submission_enabled") is False
        and dashboard.get("live_credentials_auth_boundary_summary", {}).get("cryptographic_signing_enabled") is False
        and dashboard.get("live_credentials_auth_boundary_summary", {}).get("wallet_signing_enabled") is False
        and dashboard.get("live_credentials_auth_boundary_summary", {}).get("allowed_for_live") is False
        and dashboard.get("btc_market_section_feed", {}).get("risk_control_market_data_status")
        == "fresh_open_btc_market"
        and operator_ui_panel_v1.get("btc_market_summary", {}).get("btc_market_section_ready") is True
        and operator_ui_panel_v1.get("btc_market_summary", {}).get("read_only_network_enabled") is False
        and operator_ui_panel_v1.get("btc_market_summary", {}).get("execution_enabling") is False
        and operator_ui_panel_v1.get("btc_analysis_order_intent_summary", {}).get(
            "btc_analysis_order_intent_section_ready"
        )
        is True
        and operator_ui_panel_v1.get("btc_analysis_order_intent_summary", {}).get("allowed_for_dry_run") is True
        and operator_ui_panel_v1.get("btc_analysis_order_intent_summary", {}).get("allowed_for_live") is False
        and operator_ui_panel_v1.get("live_order_submission_boundary_summary", {}).get("dry_run_review_ready") is True
        and operator_ui_panel_v1.get("live_order_submission_boundary_summary", {}).get("would_submit_order") is False
        and operator_ui_panel_v1.get("live_order_submission_boundary_summary", {}).get("order_submission_enabled")
        is False
        and operator_ui_panel_v1.get("live_order_submission_boundary_summary", {}).get("allowed_for_live") is False
        and operator_ui_panel_v1.get("live_enablement_config_preflight_summary", {}).get("status")
        == "CONFIG_MISSING_BLOCKED"
        and operator_ui_panel_v1.get("live_enablement_config_preflight_summary", {}).get("allowed_for_live")
        is False
        and operator_ui_panel_v1.get("live_enablement_config_preflight_summary", {}).get("no_executable_action")
        is True
        and operator_ui_panel_v1.get("live_credentials_auth_boundary_summary", {}).get(
            "redacted_credential_status_ready"
        )
        is True
        and operator_ui_panel_v1.get("live_credentials_auth_boundary_summary", {}).get("allowed_for_live") is False
        and dashboard.get("live_canary_readiness_summary", {}).get("dry_run_only_assertion")
        == "This checklist does not make live execution available."
        and tiny_live_canary_gonogo_gate.get("status") == "NO_GO_UNRESOLVED_BLOCKERS"
        and tiny_live_canary_gonogo_gate.get("overall_decision") == "NO_GO"
        and tiny_live_canary_gonogo_gate.get("explicit_human_approval_required") is True
        and tiny_live_canary_gonogo_gate.get("final_live_enablement_present") is False
        and tiny_live_canary_gonogo_gate.get("live_execution_approved") is False
        and tiny_live_canary_gonogo_gate.get("allowed_for_live") is False
        and tiny_live_canary_gonogo_gate.get("canary_executable_now") is False
        and tiny_live_canary_gonogo_gate.get("order_submission_enabled") is False
        and tiny_live_canary_gonogo_gate.get("real_execution_available") is False
        and tiny_live_canary_gonogo_gate.get("live_connector_enabled") is False
        and tiny_live_canary_gonogo_gate.get("resolved_blocker_count") == 0
        and tiny_live_canary_gonogo_gate_summary.get("no_executable_action") is True
        and dashboard.get("tiny_live_canary_gonogo_gate_summary", {}).get("status")
        == "NO_GO_UNRESOLVED_BLOCKERS"
        and dashboard.get("tiny_live_canary_gonogo_gate_summary", {}).get("overall_decision") == "NO_GO"
        and dashboard.get("operator_ui_panel_v1_summary", {}).get("tiny_live_canary_gonogo_no_executable_action")
        is True
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
        operator_intent_packet_path=(
            normalize_path(paths["operator_intent_packet"]) if active_config.write_artifacts else ""
        ),
        readiness_evidence_bundle_path=latest_readiness_evidence_bundle_path,
        live_credentials_auth_boundary_path=latest_live_credentials_auth_boundary_path,
        btc_market_snapshot_path=latest_btc_market_snapshot_path,
        btc_market_analysis_path=latest_btc_analysis_path,
        btc_order_intent_dry_run_path=latest_btc_order_intent_path,
        btc_risk_decision_path=latest_btc_risk_decision_path,
        live_order_submission_boundary_path=latest_live_order_submission_boundary_path,
        live_enablement_config_preflight_path=latest_live_enablement_config_preflight_path,
        tiny_live_canary_gonogo_gate_path=latest_tiny_live_canary_gonogo_gate_path,
        tiny_live_canary_preflight_contract_path=(
            normalize_path(paths["tiny_live_canary_preflight_contract"]) if active_config.write_artifacts else ""
        ),
        tiny_live_canary_manual_runbook_path=(
            normalize_path(paths["tiny_live_canary_manual_runbook"]) if active_config.write_artifacts else ""
        ),
        tiny_live_canary_preflight_result_path=(
            normalize_path(paths["tiny_live_canary_preflight_result"]) if active_config.write_artifacts else ""
        ),
        portfolio_path=normalize_path(paths["portfolio"]) if active_config.write_artifacts else "",
        rollforward_path=normalize_path(paths["rollforward"]) if active_config.write_artifacts else "",
        outcome_recheck_queue_path=normalize_path(paths["outcome_recheck"]) if active_config.write_artifacts else "",
        feedback_readiness_path=normalize_path(paths["feedback_readiness"]) if active_config.write_artifacts else "",
        dashboard_json_path=normalize_path(paths["dashboard_json"]) if active_config.write_artifacts else "",
        dashboard_md_path=normalize_path(paths["dashboard_md"]) if active_config.write_artifacts else "",
        operator_ui_panel_json_path=(
            normalize_path(paths["operator_ui_panel_json"]) if active_config.write_artifacts else ""
        ),
        operator_ui_panel_md_path=normalize_path(paths["operator_ui_panel_md"]) if active_config.write_artifacts else "",
        operator_ui_panel_html_path=(
            normalize_path(paths["operator_ui_panel_html"]) if active_config.write_artifacts else ""
        ),
        telegram_mini_app_operator_panel_json_path=(
            normalize_path(paths["telegram_mini_app_operator_panel_json"]) if active_config.write_artifacts else ""
        ),
        telegram_mini_app_operator_panel_html_path=(
            normalize_path(paths["telegram_mini_app_operator_panel_html"]) if active_config.write_artifacts else ""
        ),
        telegram_operator_control_state_path=latest_telegram_operator_control_state_path,
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
            operator_intent_packet=operator_intent_packet,
            readiness_evidence_bundle=readiness_evidence_bundle,
            live_credentials_auth_boundary=live_credentials_auth_boundary,
            btc_market_snapshot=btc_market_snapshot,
            btc_market_analysis=btc_market_analysis,
            btc_order_intent_dry_run=btc_order_intent_dry_run,
            btc_risk_decision=latest_risk_limit_decision,
            live_order_submission_boundary=live_order_submission_boundary,
            live_enablement_config_preflight=live_enablement_config_preflight,
            tiny_live_canary_gonogo_gate=tiny_live_canary_gonogo_gate,
            tiny_live_canary_preflight_contract=tiny_live_canary_preflight_contract,
            tiny_live_canary_manual_runbook=tiny_live_canary_manual_runbook,
            tiny_live_canary_preflight_result=tiny_live_canary_preflight_result,
            telegram_operator_control_state=telegram_operator_control_state,
            operator_ui_panel_v1=operator_ui_panel_v1,
            telegram_mini_app_operator_panel=telegram_mini_app_operator_panel,
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
        "operator_intent_packet": output_dir / "live_canary_operator_intent_packet.json",
        "operator_intent_packet_md": output_dir / "live_canary_operator_intent_packet.md",
        "readiness_evidence_bundle": output_dir / "live_canary_readiness_evidence_bundle.json",
        "live_credentials_auth_boundary": output_dir / "live_credentials_auth_boundary_040.json",
        "btc_market_snapshot": output_dir / "btc_market_snapshot_038.json",
        "btc_market_analysis": output_dir / "btc_market_analysis_039.json",
        "btc_order_intent_dry_run": output_dir / "btc_order_intent_dry_run_039.json",
        "btc_risk_decision": output_dir / "btc_risk_decision_039.json",
        "live_order_submission_boundary": output_dir / "live_order_submission_boundary_041.json",
        "live_enablement_config_preflight": output_dir / "live_enablement_config_preflight_047.json",
        "tiny_live_canary_gonogo_gate": output_dir / "tiny_live_canary_gonogo_gate_042.json",
        "tiny_live_canary_preflight_contract": output_dir / "tiny_live_canary_preflight_contract.json",
        "tiny_live_canary_preflight_contract_md": output_dir / "tiny_live_canary_preflight_contract.md",
        "tiny_live_canary_manual_runbook": output_dir / "tiny_live_canary_manual_runbook.json",
        "tiny_live_canary_manual_runbook_md": output_dir / "tiny_live_canary_manual_runbook.md",
        "tiny_live_canary_preflight_result": output_dir / "tiny_live_canary_preflight_result.json",
        "tiny_live_canary_preflight_result_md": output_dir / "tiny_live_canary_preflight_result.md",
        "portfolio": output_dir / "paper_daily_portfolio_state.json",
        "portfolio_md": output_dir / "paper_daily_portfolio_state.md",
        "rollforward": output_dir / "paper_daily_rollforward.json",
        "rollforward_md": output_dir / "paper_daily_rollforward.md",
        "audit": output_dir / "paper_daily_audit.json",
        "audit_md": output_dir / "paper_daily_audit.md",
        "dashboard_json": output_dir / "paper_daily_dashboard.json",
        "dashboard_md": output_dir / "paper_daily_dashboard.md",
        "operator_ui_panel_json": output_dir / "operator_ui_panel_v1.json",
        "operator_ui_panel_md": output_dir / "operator_ui_panel_v1.md",
        "operator_ui_panel_html": output_dir / "operator_ui_panel_v1.html",
        "telegram_mini_app_operator_panel_json": output_dir / "telegram_mini_app_operator_panel_044.json",
        "telegram_mini_app_operator_panel_html": output_dir / "telegram_mini_app_operator_panel_044.html",
        "telegram_operator_control_state": output_dir / "telegram_operator_control_state_043.json",
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


def _build_latest_risk_limit_decision(
    *,
    candidates: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
    live_connector_blocker_matrix: Mapping[str, Any],
    operator_intent_packet: Mapping[str, Any],
    btc_market_snapshot: Mapping[str, Any],
    readiness_evidence_bundle_reference: str,
    audit_replay_reference: str,
    ui_panel_reference: str,
    policy: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any] | None:
    intent_candidate = _first_dry_run_intent_candidate(candidates)
    if intent_candidate is None:
        return None
    intent = _risk_limit_intent_from_candidate(
        intent_candidate,
        operator_intent_reference=clean_text(operator_intent_packet.get("packet_id"))
        or "live_canary_operator_intent_packet:current-run",
        readiness_evidence_reference=readiness_evidence_bundle_reference,
        audit_replay_reference=audit_replay_reference,
        ui_panel_reference=ui_panel_reference,
        generated_at=generated_at,
    )
    exposure = _risk_limit_exposure_snapshot_for_candidate(
        intent_candidate,
        portfolio_state=portfolio_state,
        generated_at=generated_at,
    )
    daily_loss = RiskLimitDailyLossSnapshot(generated_at=generated_at).to_dict()
    state = build_default_risk_limit_state(
        exposure_snapshot=exposure,
        daily_loss_snapshot=daily_loss,
        unresolved_critical_blockers=list(live_connector_blocker_matrix.get("critical_blockers", [])),
        operator_intent_present=True,
        readiness_evidence_present=True,
        btc_market_snapshot=btc_market_snapshot,
        generated_at=generated_at,
    )
    return evaluate_risk_limits_for_order_intent(intent, state=state, policy=policy, generated_at=generated_at)


def _first_dry_run_intent_candidate(candidates: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for candidate in mapping_rows(candidates.get("candidates")):
        if float(candidate.get("intended_notional_usd", 0) or 0) > 0:
            return candidate
    return None


def _risk_limit_intent_from_candidate(
    candidate: Mapping[str, Any],
    *,
    operator_intent_reference: str,
    readiness_evidence_reference: str,
    audit_replay_reference: str,
    ui_panel_reference: str,
    generated_at: str,
) -> dict[str, Any]:
    market_id = clean_text(candidate.get("market_id"))
    return RiskLimitOrderIntent(
        intent_id=clean_text(candidate.get("intent_id")) or f"risk-limit-intent-{_slug(market_id)}",
        market_id=market_id,
        market_slug=_slug(candidate.get("market_slug") or market_id),
        market_tag=clean_text(candidate.get("market_tag") or candidate.get("market_category") or "PAPER"),
        market_category=clean_text(candidate.get("market_category") or "paper"),
        side_label=clean_text(candidate.get("side_label") or "track_yes"),
        notional_usd=float(candidate.get("intended_notional_usd", 0) or 0),
        quantity=float(candidate.get("quantity", 0) or 0),
        limit_price=float(candidate.get("limit_price", 0) or 0),
        intent_source=clean_text(candidate.get("analysis_source_path") or "paper_daily_loop"),
        created_at=clean_text(candidate.get("created_at") or generated_at),
        dry_run_only=True,
        operator_intent_reference=operator_intent_reference,
        readiness_evidence_reference=readiness_evidence_reference,
        audit_replay_reference=audit_replay_reference,
        ui_panel_reference=ui_panel_reference,
    ).to_dict()


def _risk_limit_exposure_snapshot_for_candidate(
    candidate: Mapping[str, Any],
    *,
    portfolio_state: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    market_id = clean_text(candidate.get("market_id"))
    exposure_by_market = dict(portfolio_state.get("exposure_by_market_usd", {}))
    market_exposure = round(float(exposure_by_market.get(market_id, 0) or 0), 2)
    active_market_ids = sorted(clean_text(key) for key, value in exposure_by_market.items() if clean_text(key) and float(value or 0) > 0)
    return RiskLimitExposureSnapshot(
        total_exposure_usd=float(portfolio_state.get("total_paper_exposure_usd", 0) or 0),
        market_exposure_usd=market_exposure,
        active_market_ids=tuple(active_market_ids),
        snapshot_reference=clean_text(portfolio_state.get("portfolio_id")) or "paper_daily_portfolio_state",
        generated_at=generated_at,
    ).to_dict()


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
    operator_intent_packet: Mapping[str, Any],
    live_connector_blocker_matrix: Mapping[str, Any],
    tiny_live_canary_preflight_contract: Mapping[str, Any],
    tiny_live_canary_manual_runbook: Mapping[str, Any],
    tiny_live_canary_preflight_result: Mapping[str, Any],
    readiness_evidence_bundle: Mapping[str, Any],
    readiness_evidence_bundle_summary: Mapping[str, Any],
    live_credentials_auth_boundary: Mapping[str, Any],
    live_credentials_auth_boundary_summary: Mapping[str, Any],
    live_enablement_config_preflight: Mapping[str, Any],
    live_enablement_config_preflight_summary: Mapping[str, Any],
    risk_limit_policy: Mapping[str, Any],
    latest_risk_limit_decision: Mapping[str, Any] | None,
    risk_control_plane_summary: Mapping[str, Any],
    btc_market_snapshot: Mapping[str, Any],
    btc_market_snapshot_summary: Mapping[str, Any],
    btc_read_only_connector_summary: Mapping[str, Any],
    btc_market_analysis: Mapping[str, Any],
    btc_order_intent_dry_run: Mapping[str, Any],
    btc_risk_decision_summary: Mapping[str, Any],
    btc_analysis_order_intent_summary: Mapping[str, Any],
    live_order_submission_boundary: Mapping[str, Any],
    live_order_submission_boundary_summary: Mapping[str, Any],
    tiny_live_canary_gonogo_gate: Mapping[str, Any],
    tiny_live_canary_gonogo_gate_summary: Mapping[str, Any],
    telegram_operator_control_state: Mapping[str, Any],
    telegram_operator_control_bot_summary: Mapping[str, Any],
    telegram_mini_app_operator_panel_summary: Mapping[str, Any],
    latest_disabled_connector_audit_path: str,
    latest_audit_replay_path: str,
    latest_operator_packet_path: str,
    latest_operator_intent_packet_path: str,
    latest_tiny_canary_contract_path: str,
    latest_manual_runbook_path: str,
    latest_readiness_evidence_bundle_path: str,
    latest_live_credentials_auth_boundary_path: str,
    latest_live_enablement_config_preflight_path: str,
    latest_btc_market_snapshot_path: str,
    latest_btc_analysis_path: str,
    latest_btc_order_intent_path: str,
    latest_btc_risk_decision_path: str,
    latest_live_order_submission_boundary_path: str,
    latest_tiny_live_canary_gonogo_gate_path: str,
    latest_telegram_operator_control_state_path: str,
    latest_telegram_mini_app_operator_panel_json_path: str,
    latest_telegram_mini_app_operator_panel_html_path: str,
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
        operator_intent_packet=operator_intent_packet,
        readiness_evidence_bundle=readiness_evidence_bundle,
        live_enablement_config_preflight_summary=live_enablement_config_preflight_summary,
        generated_at=generated_at,
    )
    canary_governance_summary["tiny_live_canary_preflight_status"] = tiny_live_canary_preflight_result.get("status")
    canary_governance_summary["manual_runbook_status"] = tiny_live_canary_manual_runbook.get("status")
    canary_governance_summary["canary_executable_now"] = False
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
            "operator_intent_packet_count": 1 if operator_intent_packet else 0,
            "readiness_evidence_bundle_count": 1 if readiness_evidence_bundle else 0,
            "live_credentials_required_count": int(
                live_credentials_auth_boundary_summary.get("required_credentials_count", 0) or 0
            ),
            "live_credentials_missing_count": int(
                live_credentials_auth_boundary_summary.get("missing_credentials_count", 0) or 0
            ),
            "btc_market_snapshot_count": 1 if btc_market_snapshot else 0,
            "btc_market_analysis_count": 1 if btc_market_analysis else 0,
            "btc_order_intent_dry_run_count": 1 if btc_order_intent_dry_run else 0,
            "btc_risk_decision_count": 1 if btc_risk_decision_summary else 0,
            "live_order_submission_boundary_count": 1 if live_order_submission_boundary else 0,
            "live_order_submission_boundary_review_ready_count": (
                1 if live_order_submission_boundary.get("allowed_for_dry_run_review") is True else 0
            ),
            "live_order_submission_boundary_blocked_count": (
                1 if live_order_submission_boundary.get("status") == "blocked" else 0
            ),
            "live_enablement_config_preflight_count": 1 if live_enablement_config_preflight else 0,
            "live_enablement_config_preflight_blocked_count": (
                1 if live_enablement_config_preflight.get("dry_run_review_allowed") is not True else 0
            ),
            "tiny_live_canary_gonogo_gate_count": 1 if tiny_live_canary_gonogo_gate else 0,
            "tiny_live_canary_gonogo_no_go_reason_count": int(
                tiny_live_canary_gonogo_gate_summary.get("no_go_reason_count", 0) or 0
            ),
            "tiny_live_canary_gonogo_unresolved_blocker_count": int(
                tiny_live_canary_gonogo_gate_summary.get("unresolved_blocker_count", 0) or 0
            ),
            "telegram_operator_control_state_count": 1 if telegram_operator_control_state else 0,
            "telegram_operator_control_pause_requested_count": (
                1 if telegram_operator_control_state.get("operator_pause_requested") is True else 0
            ),
            "telegram_operator_control_kill_switch_requested_count": (
                1 if telegram_operator_control_state.get("operator_kill_switch_requested") is True else 0
            ),
            "telegram_mini_app_operator_panel_count": (
                1 if telegram_mini_app_operator_panel_summary.get("panel_artifact_available") is True else 0
            ),
            "readiness_evidence_item_count": int(readiness_evidence_bundle.get("evidence_item_count", 0) or 0),
            "readiness_evidence_missing_required_count": int(
                readiness_evidence_bundle.get("missing_required_evidence_count", 0) or 0
            ),
            "tiny_live_canary_preflight_blocker_count": int(
                tiny_live_canary_preflight_result.get("blocker_count", 0) or 0
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
            "operator_intent_packet_status": strategy_ledger.get("operator_intent_packet_status"),
            "operator_intent_packet_review_ready": strategy_ledger.get("operator_intent_packet_review_ready") is True,
            "operator_intent_is_not_live_approval": True,
            "tiny_live_canary_preflight_status": strategy_ledger.get("tiny_live_canary_preflight_status"),
            "manual_runbook_status": strategy_ledger.get("manual_runbook_status"),
            "readiness_evidence_bundle_status": strategy_ledger.get("readiness_evidence_bundle_status"),
            "readiness_evidence_bundle_review_ready": (
                strategy_ledger.get("readiness_evidence_bundle_review_ready") is True
            ),
            "readiness_evidence_bundle_is_not_live_approval": True,
            "canary_executable_now": strategy_ledger.get("canary_executable_now") is True,
            "live_execution_approved": strategy_ledger.get("live_execution_approved") is True,
            "real_execution_available": strategy_ledger.get("real_execution_available") is True,
            "live_connector_enabled": strategy_ledger.get("live_connector_enabled") is True,
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
            "operator_intent_packet_status": strategy_summary.get("operator_intent_packet_status"),
            "operator_intent_packet_review_ready": strategy_summary.get("operator_intent_packet_review_ready") is True,
            "operator_intent_is_not_live_approval": True,
            "tiny_live_canary_preflight_status": strategy_summary.get("tiny_live_canary_preflight_status"),
            "manual_runbook_status": strategy_summary.get("manual_runbook_status"),
            "readiness_evidence_bundle_status": strategy_summary.get("readiness_evidence_bundle_status"),
            "readiness_evidence_bundle_review_ready": (
                strategy_summary.get("readiness_evidence_bundle_review_ready") is True
            ),
            "readiness_evidence_bundle_is_not_live_approval": True,
            "canary_executable_now": strategy_summary.get("canary_executable_now") is True,
            "live_execution_approved": strategy_summary.get("live_execution_approved") is True,
            "real_execution_available": strategy_summary.get("real_execution_available") is True,
            "live_connector_enabled": strategy_summary.get("live_connector_enabled") is True,
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
        "risk_limit_policy": dict(risk_limit_policy),
        "default_risk_limit_policy_summary": summarize_risk_limit_policy(risk_limit_policy),
        "latest_risk_limit_decision": dict(latest_risk_limit_decision or {}),
        "risk_control_plane_summary": dict(risk_control_plane_summary),
        "live_credentials_auth_boundary": dict(live_credentials_auth_boundary),
        "live_credentials_auth_boundary_summary": dict(live_credentials_auth_boundary_summary),
        "live_credentials_auth_boundary_section_feed": dict(live_credentials_auth_boundary_summary)
        | {
            "latest_live_credentials_auth_boundary_path": clean_text(latest_live_credentials_auth_boundary_path),
            "authenticated_endpoints_enabled": False,
            "signing_enabled": False,
            "cryptographic_signing_enabled": False,
            "wallet_signing_enabled": False,
            "order_submission_enabled": False,
            "allowed_for_live": False,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
        },
        "latest_live_credentials_auth_boundary_path": clean_text(latest_live_credentials_auth_boundary_path),
        "btc_market_snapshot": dict(btc_market_snapshot),
        "btc_market_snapshot_summary": dict(btc_market_snapshot_summary),
        "btc_read_only_connector_summary": dict(btc_read_only_connector_summary),
        "latest_btc_market_snapshot_path": clean_text(latest_btc_market_snapshot_path),
        "btc_market_analysis": dict(btc_market_analysis),
        "btc_order_intent_dry_run": dict(btc_order_intent_dry_run),
        "btc_risk_decision_summary": dict(btc_risk_decision_summary),
        "btc_analysis_order_intent_summary": dict(btc_analysis_order_intent_summary),
        "btc_market_analysis_summary": {
            "btc_market_analysis_status": btc_analysis_order_intent_summary.get("btc_market_analysis_status"),
            "analysis_id": btc_market_analysis.get("analysis_id"),
            "market_id": btc_market_analysis.get("market_id"),
            "market_slug": btc_market_analysis.get("market_slug"),
            "analysis_ready_for_dry_run_intent": (
                btc_market_analysis.get("analysis_ready_for_dry_run_intent") is True
            ),
            "analysis_is_not_live_recommendation": True,
            "allowed_for_live": False,
            "latest_btc_analysis_path": clean_text(latest_btc_analysis_path),
        },
        "btc_order_intent_dry_run_summary": {
            "btc_intent_candidate_status": btc_analysis_order_intent_summary.get("btc_intent_candidate_status"),
            "dry_run_order_intent_status": btc_analysis_order_intent_summary.get("dry_run_order_intent_status"),
            "intent_market_id": btc_analysis_order_intent_summary.get("intent_market_id"),
            "intent_market_slug": btc_analysis_order_intent_summary.get("intent_market_slug"),
            "intent_notional_usd": btc_analysis_order_intent_summary.get("intent_notional_usd"),
            "intent_limit_price": btc_analysis_order_intent_summary.get("intent_limit_price"),
            "order_intent_is_not_order_submission": True,
            "allowed_for_live": False,
            "latest_btc_order_intent_path": clean_text(latest_btc_order_intent_path),
        },
        "btc_risk_decision_summary": dict(btc_risk_decision_summary)
        | {
            "risk_decision_status": btc_analysis_order_intent_summary.get("risk_decision_status"),
            "allowed_for_dry_run": btc_analysis_order_intent_summary.get("allowed_for_dry_run") is True,
            "allowed_for_live": False,
            "latest_btc_risk_decision_path": clean_text(latest_btc_risk_decision_path),
        },
        "latest_btc_analysis_path": clean_text(latest_btc_analysis_path),
        "latest_btc_order_intent_path": clean_text(latest_btc_order_intent_path),
        "latest_btc_risk_decision_path": clean_text(latest_btc_risk_decision_path),
        "live_order_submission_boundary": dict(live_order_submission_boundary),
        "live_order_submission_boundary_summary": dict(live_order_submission_boundary_summary)
        | {
            "latest_live_order_submission_boundary_path": clean_text(latest_live_order_submission_boundary_path),
            "order_submission_enabled": False,
            "would_submit_order": False,
            "authenticated_endpoint_enabled": False,
            "signing_enabled": False,
            "wallet_enabled": False,
            "allowed_for_live": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "canary_executable_now": False,
            "live_connector_enabled": False,
        },
        "live_order_submission_boundary_section_feed": dict(live_order_submission_boundary_summary)
        | {
            "latest_live_order_submission_boundary_path": clean_text(latest_live_order_submission_boundary_path),
            "order_submission_enabled": False,
            "would_submit_order": False,
            "authenticated_endpoint_enabled": False,
            "authenticated_endpoints_enabled": False,
            "signing_enabled": False,
            "cryptographic_signing_enabled": False,
            "wallet_enabled": False,
            "wallet_signing_enabled": False,
            "allowed_for_live": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "canary_executable_now": False,
            "live_connector_enabled": False,
            "execution_enabling": False,
            "review_only": True,
        },
        "latest_live_order_submission_boundary_path": clean_text(latest_live_order_submission_boundary_path),
        "live_enablement_config_preflight": dict(live_enablement_config_preflight),
        "live_enablement_config_preflight_summary": dict(live_enablement_config_preflight_summary)
        | {
            "latest_live_enablement_config_preflight_path": clean_text(
                latest_live_enablement_config_preflight_path
            ),
            "allowed_for_live": False,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
            "order_submission_enabled": False,
            "authenticated_polymarket_enabled": False,
            "wallet_signing_enabled": False,
            "resolved_blocker_count": 0,
            "no_executable_action": True,
            "execution_enabling": False,
            "live_approval": False,
            "review_only": True,
        },
        "latest_live_enablement_config_preflight_path": clean_text(
            latest_live_enablement_config_preflight_path
        ),
        "tiny_live_canary_gonogo_gate": dict(tiny_live_canary_gonogo_gate),
        "tiny_live_canary_gonogo_gate_summary": dict(tiny_live_canary_gonogo_gate_summary),
        "latest_tiny_live_canary_gonogo_gate_path": clean_text(latest_tiny_live_canary_gonogo_gate_path),
        "telegram_operator_control_state": dict(telegram_operator_control_state),
        "telegram_operator_control_bot_summary": dict(telegram_operator_control_bot_summary)
        | {
            "latest_telegram_operator_control_state_path": clean_text(
                latest_telegram_operator_control_state_path
            ),
            "review_only": True,
            "execution_enabling": False,
            "live_approval": False,
            "allowed_for_live": False,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
            "order_submission_enabled": False,
            "would_submit_order": False,
        },
        "latest_telegram_operator_control_state_path": clean_text(latest_telegram_operator_control_state_path),
        "telegram_mini_app_operator_panel_summary": dict(telegram_mini_app_operator_panel_summary)
        | {
            "latest_telegram_mini_app_operator_panel_html_path": clean_text(
                latest_telegram_mini_app_operator_panel_html_path
            ),
            "latest_telegram_mini_app_operator_panel_json_path": clean_text(
                latest_telegram_mini_app_operator_panel_json_path
            ),
            "review_only": True,
            "live_actions_available": False,
            "execution_enabling": False,
            "live_approval": False,
            "allowed_for_live": False,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
            "order_submission_enabled": False,
            "would_submit_order": False,
        },
        "telegram_mini_app_operator_panel_paths": {
            "telegram_mini_app_operator_panel_html": clean_text(
                latest_telegram_mini_app_operator_panel_html_path
            ),
            "telegram_mini_app_operator_panel_json": clean_text(
                latest_telegram_mini_app_operator_panel_json_path
            ),
        },
        "latest_telegram_mini_app_operator_panel_html_path": clean_text(
            latest_telegram_mini_app_operator_panel_html_path
        ),
        "latest_telegram_mini_app_operator_panel_json_path": clean_text(
            latest_telegram_mini_app_operator_panel_json_path
        ),
        "btc_market_section_feed": {
            "btc_market_connector_status": btc_market_snapshot_summary.get("btc_market_connector_status"),
            "market_id": btc_market_snapshot_summary.get("market_id"),
            "market_slug": btc_market_snapshot_summary.get("market_slug"),
            "market_title": btc_market_snapshot_summary.get("market_title"),
            "is_btc_related": btc_market_snapshot_summary.get("is_btc_related") is True,
            "market_status": btc_market_snapshot_summary.get("market_status"),
            "is_open": btc_market_snapshot_summary.get("is_open") is True,
            "is_resolved": btc_market_snapshot_summary.get("is_resolved") is True,
            "stale": btc_market_snapshot_summary.get("stale") is True,
            "snapshot_age_seconds": btc_market_snapshot_summary.get("snapshot_age_seconds"),
            "best_bid": btc_market_snapshot_summary.get("best_bid"),
            "best_ask": btc_market_snapshot_summary.get("best_ask"),
            "last_price": btc_market_snapshot_summary.get("last_price"),
            "spread": btc_market_snapshot_summary.get("spread"),
            "liquidity": btc_market_snapshot_summary.get("liquidity"),
            "price_status": btc_market_snapshot_summary.get("price_status"),
            "risk_control_market_data_status": btc_market_snapshot_summary.get(
                "risk_control_market_data_status"
            ),
            "read_only_network_enabled": btc_market_snapshot_summary.get("read_only_network_enabled") is True,
            "latest_btc_market_snapshot_path": clean_text(latest_btc_market_snapshot_path),
            "execution_enabling": False,
            "allowed_for_live": False,
        },
        "btc_analysis_order_intent_section_feed": dict(btc_analysis_order_intent_summary)
        | {
            "execution_enabling": False,
            "allowed_for_live": False,
            "analysis_is_not_live_recommendation": True,
            "order_intent_is_not_order_submission": True,
        },
        "risk_limit_panel_feed": {
            "risk_control_plane_summary": dict(risk_control_plane_summary),
            "default_risk_limit_policy_summary": summarize_risk_limit_policy(risk_limit_policy),
            "latest_risk_limit_decision_present": bool(latest_risk_limit_decision),
            "market_data_status": risk_control_plane_summary.get("market_data_status"),
            "market_data_market_status": risk_control_plane_summary.get("market_data_market_status"),
            "market_data_stale": risk_control_plane_summary.get("market_data_stale") is True,
            "allowed_for_live": False,
            "live_execution_approved": False,
            "canary_executable_now": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
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
                operator_intent_packet_status=clean_text(operator_intent_packet.get("intent_packet_status")),
                operator_intent_packet_review_ready=(
                    operator_intent_packet.get("operator_intent_packet_review_ready") is True
                ),
                readiness_evidence_bundle_status=clean_text(readiness_evidence_bundle.get("bundle_status")),
                readiness_evidence_bundle_review_ready=(
                    readiness_evidence_bundle.get("evidence_bundle_review_ready") is True
                ),
                readiness_evidence_bundle_is_not_live_approval=True,
                evidence_item_count=int(readiness_evidence_bundle.get("evidence_item_count", 0) or 0),
                missing_required_evidence_count=int(
                    readiness_evidence_bundle.get("missing_required_evidence_count", 0) or 0
                ),
                unresolved_live_blocker_count=int(
                    readiness_evidence_bundle.get("unresolved_live_blocker_count", 0) or 0
                ),
                latest_readiness_evidence_bundle_path=latest_readiness_evidence_bundle_path,
                tiny_live_canary_gonogo_gate_status=tiny_live_canary_gonogo_gate_summary.get("status"),
                tiny_live_canary_gonogo_overall_decision=tiny_live_canary_gonogo_gate_summary.get(
                    "overall_decision"
                ),
                tiny_live_canary_gonogo_unresolved_blocker_count=tiny_live_canary_gonogo_gate_summary.get(
                    "unresolved_blocker_count"
                ),
                risk_control_plane_status=clean_text(
                    risk_control_plane_summary.get("risk_control_plane_status")
                ),
                live_enablement_config_preflight_summary=live_enablement_config_preflight_summary,
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
            "operator_intent_packet_status": canary_governance_summary.get("operator_intent_packet_status"),
            "operator_intent_packet_review_ready": (
                canary_governance_summary.get("operator_intent_packet_review_ready") is True
            ),
            "operator_intent_is_not_live_approval": True,
            "readiness_evidence_bundle_status": canary_governance_summary.get(
                "readiness_evidence_bundle_status"
            ),
            "readiness_evidence_bundle_review_ready": (
                canary_governance_summary.get("readiness_evidence_bundle_review_ready") is True
            ),
            "readiness_evidence_bundle_is_not_live_approval": True,
            "evidence_item_count": canary_governance_summary.get("evidence_item_count"),
            "missing_required_evidence_count": canary_governance_summary.get("missing_required_evidence_count"),
            "latest_readiness_evidence_bundle_path": latest_readiness_evidence_bundle_path,
            "tiny_live_canary_preflight_status": tiny_live_canary_preflight_result.get("status"),
            "manual_runbook_status": tiny_live_canary_manual_runbook.get("status"),
            "future_canary_shape_defined": tiny_live_canary_preflight_result.get("future_canary_shape_defined") is True,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "dry_run_only_assertion": canary_governance_summary.get("dry_run_only_assertion"),
            "governance_summary": canary_governance_summary,
        },
        "tiny_live_canary_preflight_runbook_summary": {
            "tiny_live_canary_preflight_status": clean_text(tiny_live_canary_preflight_result.get("status")),
            "manual_runbook_status": clean_text(tiny_live_canary_manual_runbook.get("status")),
            "future_canary_shape_defined": tiny_live_canary_preflight_result.get("future_canary_shape_defined")
            is True,
            "preflight_contract_ready": tiny_live_canary_preflight_result.get("preflight_contract_ready") is True,
            "manual_runbook_ready": tiny_live_canary_preflight_result.get("manual_runbook_ready") is True,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "kill_switch_requirements_defined": tiny_live_canary_preflight_result.get(
                "kill_switch_requirements_defined"
            )
            is True,
            "kill_switch_verified_for_live": False,
            "unresolved_live_blocker_count": int(
                tiny_live_canary_preflight_result.get("unresolved_live_blocker_count", 0) or 0
            ),
            "latest_tiny_canary_contract_path": clean_text(latest_tiny_canary_contract_path),
            "latest_manual_runbook_path": clean_text(latest_manual_runbook_path),
            "contract_id": clean_text(tiny_live_canary_preflight_contract.get("contract_id")),
            "runbook_id": clean_text(tiny_live_canary_manual_runbook.get("runbook_id")),
            "preflight_result_id": clean_text(tiny_live_canary_preflight_result.get("result_id")),
            "blocker_ids": list(tiny_live_canary_preflight_result.get("blocker_ids", [])),
            "readiness_evidence_bundle_status": readiness_evidence_bundle.get("bundle_status"),
            "readiness_evidence_bundle_review_ready": (
                readiness_evidence_bundle.get("evidence_bundle_review_ready") is True
            ),
            "readiness_evidence_bundle_is_not_live_approval": True,
            "operator_review_is_not_live_approval": True,
            "canary_preflight_is_not_execution_approval": True,
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
            "readiness_evidence_bundle_status": readiness_evidence_bundle.get("bundle_status"),
            "readiness_evidence_bundle_review_ready": (
                readiness_evidence_bundle.get("evidence_bundle_review_ready") is True
            ),
            "readiness_evidence_bundle_is_not_live_approval": True,
            "operator_review_is_not_live_approval": operator_live_approval_packet.get(
                "operator_review_is_not_live_approval"
            )
            is True,
        },
        "operator_intent_packet_summary": summarize_live_canary_operator_intent_packet(
            operator_intent_packet,
            latest_operator_intent_packet_path=latest_operator_intent_packet_path,
            generated_at=generated_at,
        )
        | {
            "operator_acknowledgement_model_ready": (
                operator_intent_packet.get("operator_acknowledgement_model_ready") is True
            ),
            "dry_run_intent_validation_ready": (
                operator_intent_packet.get("dry_run_intent_validation_ready") is True
            ),
            "unresolved_live_blocker_count": int(
                live_connector_blocker_matrix.get("unresolved_blocker_count", 0) or 0
            ),
        },
        "readiness_evidence_bundle_summary": dict(readiness_evidence_bundle_summary)
        | {
            "readiness_evidence_bundle_status": readiness_evidence_bundle.get("bundle_status"),
            "readiness_evidence_bundle_review_ready": (
                readiness_evidence_bundle.get("evidence_bundle_review_ready") is True
            ),
            "readiness_evidence_bundle_is_not_live_approval": True,
            "evidence_item_count": int(readiness_evidence_bundle.get("evidence_item_count", 0) or 0),
            "missing_required_evidence_count": int(
                readiness_evidence_bundle.get("missing_required_evidence_count", 0) or 0
            ),
            "unresolved_live_blocker_count": int(
                readiness_evidence_bundle.get("unresolved_live_blocker_count", 0) or 0
            ),
            "latest_readiness_evidence_bundle_path": clean_text(latest_readiness_evidence_bundle_path),
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
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
            "Review the Telegram operator control bot summary as a passive visibility/local-state surface only.",
            "Review the operator intent packet as dry-run human acknowledgement only, not live approval.",
            "Review the tiny live canary go/no-go gate as final manual review only; it exposes no executable action.",
            "Review source evidence freshness and missing evidence gaps before interpreting paper strategy output.",
            "Review the paper strategy evaluation ledger before interpreting paper readiness.",
            "Add saved local outcome resolution evidence before evaluating paper performance.",
            "Review carried-forward open paper positions and exposure before the next local paper run.",
            "Recheck unresolved markets only against saved local outcome artifacts.",
            "Prepare feedback records only for markets with explicit local resolution evidence.",
            "Keep this as an explicit one-shot local command, not a scheduler or autonomous loop.",
        ],
        "next_operator_action": (
            "Review risk decisions, strategy ledger, source evidence gaps, unresolved exposure, risk-prep config, go/no-go gate, and missing outcome evidence."
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
    operator_intent_packet: Mapping[str, Any],
    readiness_evidence_bundle: Mapping[str, Any],
    live_credentials_auth_boundary: Mapping[str, Any],
    btc_market_snapshot: Mapping[str, Any],
    btc_market_analysis: Mapping[str, Any],
    btc_order_intent_dry_run: Mapping[str, Any],
    btc_risk_decision: Mapping[str, Any],
    live_order_submission_boundary: Mapping[str, Any],
    live_enablement_config_preflight: Mapping[str, Any],
    tiny_live_canary_gonogo_gate: Mapping[str, Any],
    tiny_live_canary_preflight_contract: Mapping[str, Any],
    tiny_live_canary_manual_runbook: Mapping[str, Any],
    tiny_live_canary_preflight_result: Mapping[str, Any],
    telegram_operator_control_state: Mapping[str, Any],
    operator_ui_panel_v1: Mapping[str, Any],
    telegram_mini_app_operator_panel: Mapping[str, Any],
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
    write_json(paths["operator_intent_packet"], operator_intent_packet)
    write_text(
        paths["operator_intent_packet_md"],
        render_live_canary_operator_intent_packet_markdown(operator_intent_packet),
    )
    write_json(paths["readiness_evidence_bundle"], readiness_evidence_bundle)
    write_json(paths["live_credentials_auth_boundary"], live_credentials_auth_boundary)
    write_json(paths["btc_market_snapshot"], btc_market_snapshot)
    write_json(paths["btc_market_analysis"], btc_market_analysis)
    write_json(paths["btc_order_intent_dry_run"], btc_order_intent_dry_run)
    write_json(paths["btc_risk_decision"], btc_risk_decision)
    write_json(paths["live_order_submission_boundary"], live_order_submission_boundary)
    write_json(paths["live_enablement_config_preflight"], live_enablement_config_preflight)
    write_json(paths["tiny_live_canary_gonogo_gate"], tiny_live_canary_gonogo_gate)
    write_json(paths["tiny_live_canary_preflight_contract"], tiny_live_canary_preflight_contract)
    write_text(
        paths["tiny_live_canary_preflight_contract_md"],
        render_tiny_live_canary_preflight_contract_markdown(tiny_live_canary_preflight_contract),
    )
    write_json(paths["tiny_live_canary_manual_runbook"], tiny_live_canary_manual_runbook)
    write_text(
        paths["tiny_live_canary_manual_runbook_md"],
        render_tiny_live_canary_manual_runbook_markdown(tiny_live_canary_manual_runbook),
    )
    write_json(paths["tiny_live_canary_preflight_result"], tiny_live_canary_preflight_result)
    write_text(
        paths["tiny_live_canary_preflight_result_md"],
        render_tiny_live_canary_preflight_result_markdown(tiny_live_canary_preflight_result),
    )
    write_json(paths["telegram_operator_control_state"], telegram_operator_control_state)
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
    write_json(paths["operator_ui_panel_json"], operator_ui_panel_v1)
    write_text(paths["operator_ui_panel_md"], render_operator_ui_panel_v1_markdown(operator_ui_panel_v1))
    write_text(paths["operator_ui_panel_html"], render_operator_ui_panel_v1_html(operator_ui_panel_v1))
    write_json(paths["telegram_mini_app_operator_panel_json"], telegram_mini_app_operator_panel)
    write_text(
        paths["telegram_mini_app_operator_panel_html"],
        render_telegram_mini_app_panel_html(telegram_mini_app_operator_panel),
    )
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
        f"- Readiness evidence items: {counts.get('readiness_evidence_item_count')}",
        f"- Missing readiness evidence: {counts.get('readiness_evidence_missing_required_count')}",
        f"- Live order boundary artifacts: {counts.get('live_order_submission_boundary_count')}",
        f"- Live order boundary review-ready: {counts.get('live_order_submission_boundary_review_ready_count')}",
        f"- Live order boundary blocked: {counts.get('live_order_submission_boundary_blocked_count')}",
        f"- Live enablement config preflights: {counts.get('live_enablement_config_preflight_count')}",
        f"- Live enablement config blocked: {counts.get('live_enablement_config_preflight_blocked_count')}",
        f"- Tiny live canary go/no-go gates: {counts.get('tiny_live_canary_gonogo_gate_count')}",
        f"- Tiny go/no-go unresolved blockers: {counts.get('tiny_live_canary_gonogo_unresolved_blocker_count')}",
        f"- Telegram operator control states: {counts.get('telegram_operator_control_state_count')}",
        f"- Telegram pause requested: {counts.get('telegram_operator_control_pause_requested_count')}",
        f"- Telegram kill-switch requested: {counts.get('telegram_operator_control_kill_switch_requested_count')}",
        f"- Telegram Mini App panels: {counts.get('telegram_mini_app_operator_panel_count')}",
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
    tiny_preflight = dict(dashboard.get("tiny_live_canary_preflight_runbook_summary", {}))
    disabled_connector = dict(dashboard.get("disabled_real_connector_summary", {}))
    btc_market = dict(dashboard.get("btc_market_snapshot_summary", {}))
    btc_analysis = dict(dashboard.get("btc_analysis_order_intent_summary", {}))
    audit_operator = dict(dashboard.get("live_connector_audit_operator_summary", {}))
    operator_intent = dict(dashboard.get("operator_intent_packet_summary", {}))
    readiness_evidence = dict(dashboard.get("readiness_evidence_bundle_summary", {}))
    live_auth = dict(dashboard.get("live_credentials_auth_boundary_summary", {}))
    live_order_boundary = dict(dashboard.get("live_order_submission_boundary_summary", {}))
    live_enablement_config = dict(dashboard.get("live_enablement_config_preflight_summary", {}))
    tiny_gonogo = dict(dashboard.get("tiny_live_canary_gonogo_gate_summary", {}))
    telegram_control = dict(dashboard.get("telegram_operator_control_bot_summary", {}))
    telegram_state = dict(dashboard.get("telegram_operator_control_state", {}))
    telegram_mini_app = dict(dashboard.get("telegram_mini_app_operator_panel_summary", {}))
    telegram_mini_app_paths = dict(dashboard.get("telegram_mini_app_operator_panel_paths", {}))
    operator_ui_panel = dict(dashboard.get("operator_ui_panel_v1_summary", {}))
    operator_ui_panel_paths = dict(dashboard.get("operator_ui_panel_v1_paths", {}))
    risk_prep = dict(dashboard.get("risk_prep_config_status", {}))
    risk_control = dict(dashboard.get("risk_control_plane_summary", {}))
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
            f"- Operator intent packet status: `{canary.get('operator_intent_packet_status')}`",
            f"- Operator intent review ready: `{str(canary.get('operator_intent_packet_review_ready')).lower()}`",
            f"- Readiness evidence bundle: `{canary.get('readiness_evidence_bundle_status')}`",
            f"- Evidence bundle review ready: `{str(canary.get('readiness_evidence_bundle_review_ready')).lower()}`",
            f"- Evidence item count: {canary.get('evidence_item_count')}",
            f"- Missing required evidence: {canary.get('missing_required_evidence_count')}",
            f"- Tiny preflight status: `{canary.get('tiny_live_canary_preflight_status')}`",
            f"- Manual runbook status: `{canary.get('manual_runbook_status')}`",
            f"- Canary executable now: `{str(canary.get('canary_executable_now')).lower()}`",
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
            "## Tiny Live Canary Preflight And Manual Runbook",
            "",
            f"- Preflight status: `{tiny_preflight.get('tiny_live_canary_preflight_status')}`",
            f"- Manual runbook status: `{tiny_preflight.get('manual_runbook_status')}`",
            f"- Future canary shape defined: `{str(tiny_preflight.get('future_canary_shape_defined')).lower()}`",
            f"- Preflight contract ready: `{str(tiny_preflight.get('preflight_contract_ready')).lower()}`",
            f"- Manual runbook ready: `{str(tiny_preflight.get('manual_runbook_ready')).lower()}`",
            f"- Canary executable now: `{str(tiny_preflight.get('canary_executable_now')).lower()}`",
            f"- Live execution approved: `{str(tiny_preflight.get('live_execution_approved')).lower()}`",
            f"- Real execution available: `{str(tiny_preflight.get('real_execution_available')).lower()}`",
            f"- Kill-switch requirements defined: `{str(tiny_preflight.get('kill_switch_requirements_defined')).lower()}`",
            f"- Kill-switch verified for live: `{str(tiny_preflight.get('kill_switch_verified_for_live')).lower()}`",
            f"- Unresolved live blockers: {tiny_preflight.get('unresolved_live_blocker_count')}",
            f"- Latest preflight contract: `{tiny_preflight.get('latest_tiny_canary_contract_path')}`",
            f"- Latest manual runbook: `{tiny_preflight.get('latest_manual_runbook_path')}`",
            "",
            "## Live Credentials / Auth Boundary",
            "",
            f"- Boundary status: `{live_auth.get('live_credentials_boundary_status')}`",
            f"- Credentials configured: `{str(live_auth.get('live_credentials_configured')).lower()}`",
            f"- Required credentials: {live_auth.get('required_credentials_count')}",
            f"- Missing credentials: {live_auth.get('missing_credentials_count')}",
            f"- Future tiny canary auth review ready: `{str(live_auth.get('live_auth_ready_for_future_tiny_canary_review')).lower()}`",
            f"- Authenticated endpoints enabled: `{str(live_auth.get('authenticated_endpoints_enabled')).lower()}`",
            f"- Signing enabled: `{str(live_auth.get('signing_enabled')).lower()}`",
            f"- Order submission enabled: `{str(live_auth.get('order_submission_enabled')).lower()}`",
            f"- Allowed for live: `{str(live_auth.get('allowed_for_live')).lower()}`",
            f"- Canary executable now: `{str(live_auth.get('canary_executable_now')).lower()}`",
            f"- Live execution approved: `{str(live_auth.get('live_execution_approved')).lower()}`",
            f"- Real execution available: `{str(live_auth.get('real_execution_available')).lower()}`",
            f"- Live connector enabled: `{str(live_auth.get('live_connector_enabled')).lower()}`",
            f"- Latest auth boundary: `{live_auth.get('latest_live_credentials_auth_boundary_path')}`",
            f"- Warning: {live_auth.get('warning')}",
            "",
            "## Live Order Submission Boundary",
            "",
            f"- Status: `{live_order_boundary.get('status')}`",
            f"- Dry-run review ready: `{str(live_order_boundary.get('dry_run_review_ready')).lower()}`",
            f"- Market: `{live_order_boundary.get('market_id')}` / `{live_order_boundary.get('market_slug')}`",
            f"- Asset: `{live_order_boundary.get('asset')}`",
            f"- Side: `{live_order_boundary.get('side')}`",
            f"- Outcome: `{live_order_boundary.get('outcome')}`",
            f"- Would submit order: `{str(live_order_boundary.get('would_submit_order')).lower()}`",
            f"- Order submission enabled: `{str(live_order_boundary.get('order_submission_enabled')).lower()}`",
            f"- Authenticated endpoint required for future live: `{str(live_order_boundary.get('authenticated_endpoint_required')).lower()}`",
            f"- Authenticated endpoint enabled: `{str(live_order_boundary.get('authenticated_endpoint_enabled')).lower()}`",
            f"- Signing required for future live: `{str(live_order_boundary.get('signing_required_for_future_live')).lower()}`",
            f"- Signing enabled: `{str(live_order_boundary.get('signing_enabled')).lower()}`",
            f"- Wallet required for future live: `{str(live_order_boundary.get('wallet_required_for_future_live')).lower()}`",
            f"- Wallet enabled: `{str(live_order_boundary.get('wallet_enabled')).lower()}`",
            f"- Allowed for live: `{str(live_order_boundary.get('allowed_for_live')).lower()}`",
            f"- Canary executable now: `{str(live_order_boundary.get('canary_executable_now')).lower()}`",
            f"- Latest order boundary: `{live_order_boundary.get('latest_live_order_submission_boundary_path')}`",
            "- Refusal reasons:",
            *bullet_lines(str(item) for item in live_order_boundary.get("top_refusal_reasons", [])),
            "- Blocker reasons:",
            *bullet_lines(str(item) for item in live_order_boundary.get("top_blocker_reasons", [])),
            "",
            "## Live Enablement Config Preflight",
            "",
            f"- Status: `{live_enablement_config.get('status')}`",
            f"- Future live requested: `{str(live_enablement_config.get('future_live_requested')).lower()}`",
            f"- Dry-run review allowed: `{str(live_enablement_config.get('dry_run_review_allowed')).lower()}`",
            f"- Allowed for live: `{str(live_enablement_config.get('allowed_for_live')).lower()}`",
            f"- Canary executable now: `{str(live_enablement_config.get('canary_executable_now')).lower()}`",
            f"- Live execution approved: `{str(live_enablement_config.get('live_execution_approved')).lower()}`",
            f"- Real execution available: `{str(live_enablement_config.get('real_execution_available')).lower()}`",
            f"- Live connector enabled: `{str(live_enablement_config.get('live_connector_enabled')).lower()}`",
            f"- Order submission enabled: `{str(live_enablement_config.get('order_submission_enabled')).lower()}`",
            f"- Authenticated Polymarket enabled: `{str(live_enablement_config.get('authenticated_polymarket_enabled')).lower()}`",
            f"- Wallet signing enabled: `{str(live_enablement_config.get('wallet_signing_enabled')).lower()}`",
            f"- Resolved blockers: {live_enablement_config.get('resolved_blocker_count')}",
            f"- Latest preflight: `{live_enablement_config.get('latest_live_enablement_config_preflight_path')}`",
            "- Top blocked reasons:",
            *bullet_lines(str(item) for item in live_enablement_config.get("top_blocked_reasons", [])),
            "",
            "## Tiny Live Canary Go/No-Go Gate",
            "",
            f"- Status: `{tiny_gonogo.get('status')}`",
            f"- Overall decision: `{tiny_gonogo.get('overall_decision')}`",
            f"- Review-only status: `{tiny_gonogo.get('review_only_status')}`",
            f"- Manual checklist items: {tiny_gonogo.get('manual_execution_checklist_count')}",
            f"- Final pre-live checklist items: {tiny_gonogo.get('final_pre_live_checklist_count')}",
            f"- No-go reasons: {tiny_gonogo.get('no_go_reason_count')}",
            f"- Unresolved blockers: {tiny_gonogo.get('unresolved_blocker_count')}",
            f"- Resolved blockers: {tiny_gonogo.get('resolved_blocker_count')}",
            f"- Explicit human approval required: `{str(tiny_gonogo.get('explicit_human_approval_required')).lower()}`",
            f"- No executable action: `{str(tiny_gonogo.get('no_executable_action')).lower()}`",
            f"- Latest go/no-go packet: `{tiny_gonogo.get('latest_tiny_live_canary_gonogo_gate_path')}`",
            "- Top no-go reasons:",
            *bullet_lines(str(item) for item in tiny_gonogo.get("top_no_go_reasons", [])),
            "",
            "## Telegram Operator Control Bot",
            "",
            f"- Configured: `{str(telegram_control.get('configured')).lower()}`",
            f"- Bot token status: `{telegram_control.get('config', {}).get('telegram_bot_token_status') or telegram_control.get('telegram_bot_token_status')}`",
            f"- Allowed operator IDs configured: `{str(telegram_control.get('allowed_operator_ids_configured')).lower()}`",
            f"- Allowed operator ID count: `{telegram_control.get('allowed_operator_id_count')}`",
            f"- Pause requested: `{str(telegram_control.get('operator_pause_requested')).lower()}`",
            f"- Kill-switch requested: `{str(telegram_control.get('operator_kill_switch_requested')).lower()}`",
            f"- Review-only: `{str(telegram_control.get('review_only')).lower()}`",
            f"- Live approval: `{str(telegram_control.get('live_approval')).lower()}`",
            f"- Execution enabling: `{str(telegram_control.get('execution_enabling')).lower()}`",
            f"- Live execution approved: `{str(telegram_control.get('live_execution_approved')).lower()}`",
            f"- Canary executable now: `{str(telegram_control.get('canary_executable_now')).lower()}`",
            f"- Order submission enabled: `{str(telegram_control.get('order_submission_enabled')).lower()}`",
            f"- Latest state artifact: `{telegram_state.get('state_id')}` / `{telegram_control.get('latest_telegram_operator_control_state_path')}`",
            "",
            "## Telegram Mini App Operator Panel",
            "",
            f"- Panel artifact available: `{str(telegram_mini_app.get('panel_artifact_available')).lower()}`",
            f"- Review-only: `{str(telegram_mini_app.get('review_only')).lower()}`",
            f"- Live actions available: `{str(telegram_mini_app.get('live_actions_available')).lower()}`",
            f"- Execution enabling: `{str(telegram_mini_app.get('execution_enabling')).lower()}`",
            f"- Live approval: `{str(telegram_mini_app.get('live_approval')).lower()}`",
            f"- Allowed for live: `{str(telegram_mini_app.get('allowed_for_live')).lower()}`",
            f"- Canary executable now: `{str(telegram_mini_app.get('canary_executable_now')).lower()}`",
            f"- Order submission enabled: `{str(telegram_mini_app.get('order_submission_enabled')).lower()}`",
            f"- Mini App URL status: `{telegram_mini_app.get('mini_app_url_status')}`",
            f"- Telegram init data status: `{telegram_mini_app.get('telegram_init_data_status')}`",
            f"- HTML: `{telegram_mini_app_paths.get('telegram_mini_app_operator_panel_html')}`",
            f"- JSON: `{telegram_mini_app_paths.get('telegram_mini_app_operator_panel_json')}`",
            "",
            "## BTC Read-Only Market Connector",
            "",
            f"- Connector status: `{btc_market.get('btc_market_connector_status')}`",
            f"- Market: `{btc_market.get('market_id')}` / `{btc_market.get('market_slug')}`",
            f"- Title: {btc_market.get('market_title')}",
            f"- BTC related: `{str(btc_market.get('is_btc_related')).lower()}`",
            f"- Market status: `{btc_market.get('market_status')}`",
            f"- Open: `{str(btc_market.get('is_open')).lower()}`",
            f"- Resolved: `{str(btc_market.get('is_resolved')).lower()}`",
            f"- Stale: `{str(btc_market.get('stale')).lower()}`",
            f"- Age seconds: `{btc_market.get('snapshot_age_seconds')}`",
            f"- Best bid: `{btc_market.get('best_bid')}`",
            f"- Best ask: `{btc_market.get('best_ask')}`",
            f"- Last price: `{btc_market.get('last_price')}`",
            f"- Spread: `{btc_market.get('spread')}`",
            f"- Liquidity: `{btc_market.get('liquidity')}`",
            f"- Price status: `{btc_market.get('price_status')}`",
            f"- Risk market-data status: `{btc_market.get('risk_control_market_data_status')}`",
            f"- Read-only network enabled: `{str(btc_market.get('read_only_network_enabled')).lower()}`",
            f"- Latest BTC snapshot: `{btc_market.get('latest_btc_market_snapshot_path')}`",
            "",
            "## BTC Market Analysis And Dry-Run Order Intent",
            "",
            f"- Analysis status: `{btc_analysis.get('btc_market_analysis_status')}`",
            f"- Intent candidate status: `{btc_analysis.get('btc_intent_candidate_status')}`",
            f"- Dry-run order intent status: `{btc_analysis.get('dry_run_order_intent_status')}`",
            f"- Intent market: `{btc_analysis.get('intent_market_id')}` / `{btc_analysis.get('intent_market_slug')}`",
            f"- Intent notional USD: `{btc_analysis.get('intent_notional_usd')}`",
            f"- Intent limit price: `{btc_analysis.get('intent_limit_price')}`",
            f"- Risk decision status: `{btc_analysis.get('risk_decision_status')}`",
            f"- Allowed for dry-run: `{str(btc_analysis.get('allowed_for_dry_run')).lower()}`",
            f"- Allowed for live: `{str(btc_analysis.get('allowed_for_live')).lower()}`",
            f"- Analysis is not live recommendation: `{str(btc_analysis.get('analysis_is_not_live_recommendation')).lower()}`",
            f"- Order intent is not order submission: `{str(btc_analysis.get('order_intent_is_not_order_submission')).lower()}`",
            f"- Latest BTC analysis: `{btc_analysis.get('latest_btc_analysis_path')}`",
            f"- Latest BTC order intent: `{btc_analysis.get('latest_btc_order_intent_path')}`",
            f"- Latest BTC risk decision: `{btc_analysis.get('latest_btc_risk_decision_path')}`",
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
            "## Operator Intent Packet",
            "",
            f"- Intent packet status: `{operator_intent.get('operator_intent_packet_status')}`",
            f"- Review ready: `{str(operator_intent.get('operator_intent_packet_review_ready')).lower()}`",
            f"- Human acknowledgement only: `{str(operator_intent.get('operator_signed_intent_is_human_acknowledgement_only')).lower()}`",
            f"- Not live approval: `{str(operator_intent.get('operator_intent_is_not_live_approval')).lower()}`",
            f"- Canary executable now: `{str(operator_intent.get('canary_executable_now')).lower()}`",
            f"- Live execution approved: `{str(operator_intent.get('live_execution_approved')).lower()}`",
            f"- Real execution available: `{str(operator_intent.get('real_execution_available')).lower()}`",
            f"- Unresolved live blockers: {operator_intent.get('unresolved_live_blocker_count')}",
            f"- Kill-switch verified for live: `{str(operator_intent.get('kill_switch_verified_for_live')).lower()}`",
            f"- Latest operator intent packet: `{operator_intent.get('latest_operator_intent_packet_path')}`",
            "",
            "## Readiness Evidence Bundle",
            "",
            f"- Status: `{readiness_evidence.get('readiness_evidence_bundle_status')}`",
            f"- Review ready: `{str(readiness_evidence.get('readiness_evidence_bundle_review_ready')).lower()}`",
            f"- Not live approval: `{str(readiness_evidence.get('readiness_evidence_bundle_is_not_live_approval')).lower()}`",
            f"- Evidence items: {readiness_evidence.get('evidence_item_count')}",
            f"- Missing required evidence: {readiness_evidence.get('missing_required_evidence_count')}",
            f"- Unresolved live blockers: {readiness_evidence.get('unresolved_live_blocker_count')}",
            f"- Canary executable now: `{str(readiness_evidence.get('canary_executable_now')).lower()}`",
            f"- Live execution approved: `{str(readiness_evidence.get('live_execution_approved')).lower()}`",
            f"- Real execution available: `{str(readiness_evidence.get('real_execution_available')).lower()}`",
            f"- Live connector enabled: `{str(readiness_evidence.get('live_connector_enabled')).lower()}`",
            f"- Latest evidence bundle: `{readiness_evidence.get('latest_readiness_evidence_bundle_path')}`",
            "",
            "## Operator UI Panel v1",
            "",
            f"- Panel ready: `{str(operator_ui_panel.get('operator_ui_panel_ready')).lower()}`",
            f"- Readiness panel render ready: `{str(operator_ui_panel.get('readiness_panel_render_ready')).lower()}`",
            f"- Risk limit panel render ready: `{str(operator_ui_panel.get('risk_limit_panel_render_ready')).lower()}`",
            f"- Kill-switch panel render ready: `{str(operator_ui_panel.get('kill_switch_panel_render_ready')).lower()}`",
            f"- Static HTML render ready: `{str(operator_ui_panel.get('static_html_render_ready')).lower()}`",
            f"- Markdown render ready: `{str(operator_ui_panel.get('markdown_render_ready')).lower()}`",
            f"- JSON render ready: `{str(operator_ui_panel.get('json_render_ready')).lower()}`",
            f"- Not live execution console: `{str(operator_ui_panel.get('ui_panel_is_not_live_execution_console')).lower()}`",
            f"- Exposes executable live action: `{str(not operator_ui_panel.get('ui_exposes_no_executable_live_action')).lower()}`",
            f"- Live execution approved: `{str(operator_ui_panel.get('live_execution_approved')).lower()}`",
            f"- Canary executable now: `{str(operator_ui_panel.get('canary_executable_now')).lower()}`",
            f"- Real execution available: `{str(operator_ui_panel.get('real_execution_available')).lower()}`",
            f"- Live connector enabled: `{str(operator_ui_panel.get('live_connector_enabled')).lower()}`",
            f"- JSON: `{operator_ui_panel_paths.get('operator_ui_panel_json')}`",
            f"- Markdown: `{operator_ui_panel_paths.get('operator_ui_panel_md')}`",
            f"- HTML: `{operator_ui_panel_paths.get('operator_ui_panel_html')}`",
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
            "",
            "## Risk Limit Control Plane",
            "",
            f"- Status: `{risk_control.get('risk_control_plane_status')}`",
            f"- Policy: `{risk_control.get('policy_id')}`",
            f"- Mode: `{risk_control.get('mode')}`",
            f"- Max daily loss: `${risk_control.get('max_daily_loss_usd')}`",
            f"- Max total exposure: `${risk_control.get('max_total_exposure_usd')}`",
            f"- Max market exposure: `${risk_control.get('max_market_exposure_usd')}`",
            f"- Max order notional: `${risk_control.get('max_order_notional_usd')}`",
            f"- Max orders per day: `{risk_control.get('max_orders_per_day')}`",
            f"- Max trades per day: `{risk_control.get('max_trades_per_day')}`",
            f"- Max active markets: `{risk_control.get('max_active_markets')}`",
            f"- Allowed market tags: `{risk_control.get('allowed_market_tags')}`",
            f"- Latest decision: `{risk_control.get('latest_decision_status')}`",
            f"- Latest violations: {risk_control.get('latest_violations_count')}",
            f"- Latest halt reasons: {risk_control.get('latest_halt_reasons_count')}",
            f"- Allowed for dry-run: `{str(risk_control.get('allowed_for_dry_run')).lower()}`",
            f"- Allowed for live: `{str(risk_control.get('allowed_for_live')).lower()}`",
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
            f"- Tiny canary preflight contract: `{result.get('tiny_live_canary_preflight_contract_path')}`",
            f"- Tiny canary manual runbook: `{result.get('tiny_live_canary_manual_runbook_path')}`",
            f"- Tiny canary preflight result: `{result.get('tiny_live_canary_preflight_result_path')}`",
            f"- Live canary operator approval record: `{result.get('canary_operator_approval_record_path')}`",
            f"- Live canary readiness packet: `{result.get('canary_readiness_packet_path')}`",
            f"- Live canary dry-run receipt: `{result.get('canary_dry_run_receipt_path')}`",
            f"- Disabled real connector audit: `{dict(dashboard.get('disabled_real_connector_summary', {})).get('latest_disabled_connector_audit_path')}`",
            f"- Live connector audit replay: `{result.get('live_connector_audit_replay_path')}`",
            f"- Operator live review packet: `{result.get('operator_live_approval_packet_path')}`",
            f"- Operator intent packet: `{result.get('operator_intent_packet_path')}`",
            f"- Readiness evidence bundle: `{result.get('readiness_evidence_bundle_path')}`",
            f"- Live credentials/auth boundary: `{result.get('live_credentials_auth_boundary_path')}`",
            f"- BTC market analysis: `{result.get('btc_market_analysis_path')}`",
            f"- BTC dry-run order intent: `{result.get('btc_order_intent_dry_run_path')}`",
            f"- BTC risk decision: `{result.get('btc_risk_decision_path')}`",
            f"- Live order submission boundary: `{result.get('live_order_submission_boundary_path')}`",
            f"- Live enablement config preflight: `{result.get('live_enablement_config_preflight_path')}`",
            f"- Tiny live canary go/no-go gate: `{result.get('tiny_live_canary_gonogo_gate_path')}`",
            f"- Telegram operator control state: `{result.get('telegram_operator_control_state_path')}`",
            f"- Operator UI panel JSON: `{result.get('operator_ui_panel_json_path')}`",
            f"- Operator UI panel Markdown: `{result.get('operator_ui_panel_md_path')}`",
            f"- Operator UI panel HTML: `{result.get('operator_ui_panel_html_path')}`",
            f"- Telegram Mini App panel JSON: `{result.get('telegram_mini_app_operator_panel_json_path')}`",
            f"- Telegram Mini App panel HTML: `{result.get('telegram_mini_app_operator_panel_html_path')}`",
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
