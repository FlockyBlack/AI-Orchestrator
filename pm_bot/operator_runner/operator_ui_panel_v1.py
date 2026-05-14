from __future__ import annotations

import hashlib
import html
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.authenticated_polymarket_connector import (
    summarize_authenticated_connector_capability_report,
)
from pm_bot.trading_core.wallet_signing_boundary import (
    build_wallet_signing_boundary_report,
    summarize_wallet_signing_boundary_report,
)
from pm_bot.trading_core.signed_order_payload_validation_gate import (
    summarize_signed_order_payload_validation_gate,
)
from pm_bot.trading_core.live_credentials_auth_boundary import (
    UI_REDACTION_WARNING,
    summarize_live_credentials_status,
)
from pm_bot.trading_core.live_enablement_config import summarize_live_enablement_config_preflight
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, mapping_rows
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_btc_analysis_ui_summary,
    validate_secret_boundary_btc_ui_summary,
    validate_secret_boundary_live_credentials_auth_summary,
    validate_secret_boundary_live_order_submission_boundary_summary,
    validate_secret_boundary_operator_ui_panel_authenticated_polymarket_connector_scaffold_summary,
    validate_secret_boundary_operator_ui_panel_signed_order_payload_validation_gate_summary,
    validate_secret_boundary_operator_ui_panel_wallet_signing_boundary_summary,
    validate_secret_boundary_risk_control_ui_summary,
    validate_secret_boundary_operator_ui_panel_action_state,
    validate_secret_boundary_operator_ui_panel_kill_switch_summary,
    validate_secret_boundary_operator_ui_panel_live_enablement_config_preflight_summary,
    validate_secret_boundary_operator_ui_panel_payload,
    validate_secret_boundary_operator_ui_panel_rendered_html,
    validate_secret_boundary_operator_ui_panel_rendered_json,
    validate_secret_boundary_operator_ui_panel_rendered_markdown,
    validate_secret_boundary_operator_ui_panel_risk_limit_summary,
    validate_secret_boundary_supervised_tiny_canary_approval_packet_summary,
)
from pm_bot.trading_core.btc_market_analysis_order_intent import summarize_btc_analysis_order_intent
from pm_bot.trading_core.live_order_submission_boundary import (
    BOUNDARY_NAME as LIVE_ORDER_SUBMISSION_BOUNDARY_NAME,
    summarize_live_order_submission_boundary_receipt,
)
from pm_bot.trading_core.tiny_live_canary_gonogo_gate import summarize_tiny_live_canary_gonogo_gate
from pm_bot.trading_core.supervised_tiny_canary_runbook import (
    summarize_supervised_tiny_canary_approval_packet,
)
from pm_bot.trading_core.risk_limit_control_plane import (
    build_default_risk_limit_policy,
    build_risk_control_plane_summary,
    summarize_risk_limit_decision,
    summarize_risk_limit_policy,
)
from pm_bot.trading_core.polymarket_btc_read_only_connector import summarize_btc_market_snapshot

OPERATOR_UI_PANEL_V1_CONTRACT = "pmbot_operator_ui_panel.v1"
OPERATOR_UI_PANEL_SECTION_CONTRACT = "pmbot_operator_ui_panel_section.v1"
OPERATOR_UI_PANEL_METRIC_CONTRACT = "pmbot_operator_ui_panel_metric.v1"
OPERATOR_UI_PANEL_WARNING_CONTRACT = "pmbot_operator_ui_panel_warning.v1"
OPERATOR_UI_PANEL_ACTION_STATE_CONTRACT = "pmbot_operator_ui_panel_action_state.v1"
OPERATOR_UI_PANEL_RISK_LIMIT_SUMMARY_CONTRACT = "pmbot_operator_ui_panel_risk_limit_summary.v1"
OPERATOR_UI_PANEL_RISK_CONTROL_SUMMARY_CONTRACT = "pmbot_operator_ui_panel_risk_control_summary.v1"
OPERATOR_UI_PANEL_KILL_SWITCH_SUMMARY_CONTRACT = "pmbot_operator_ui_panel_kill_switch_summary.v1"
OPERATOR_UI_PANEL_READINESS_SUMMARY_CONTRACT = "pmbot_operator_ui_panel_readiness_summary.v1"
OPERATOR_UI_PANEL_EVIDENCE_SUMMARY_CONTRACT = "pmbot_operator_ui_panel_evidence_summary.v1"
OPERATOR_UI_PANEL_BLOCKER_SUMMARY_CONTRACT = "pmbot_operator_ui_panel_blocker_summary.v1"
OPERATOR_UI_PANEL_BTC_MARKET_SUMMARY_CONTRACT = "pmbot_operator_ui_panel_btc_market_summary.v1"
OPERATOR_UI_PANEL_BTC_ANALYSIS_SUMMARY_CONTRACT = "pmbot_operator_ui_panel_btc_analysis_order_intent_summary.v1"
OPERATOR_UI_PANEL_LIVE_AUTH_SUMMARY_CONTRACT = "pmbot_operator_ui_panel_live_credentials_auth_summary.v1"
OPERATOR_UI_PANEL_LIVE_ORDER_BOUNDARY_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_live_order_submission_boundary_summary.v1"
)
OPERATOR_UI_PANEL_LIVE_ENABLEMENT_CONFIG_PREFLIGHT_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_live_enablement_config_preflight_summary.v1"
)
OPERATOR_UI_PANEL_AUTHENTICATED_POLYMARKET_CONNECTOR_SCAFFOLD_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_authenticated_polymarket_connector_scaffold_summary.v1"
)
OPERATOR_UI_PANEL_WALLET_SIGNING_BOUNDARY_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_wallet_signing_boundary_summary.v1"
)
OPERATOR_UI_PANEL_SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_signed_order_payload_validation_gate_summary.v1"
)
OPERATOR_UI_PANEL_TINY_CANARY_GONOGO_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_tiny_live_canary_gonogo_summary.v1"
)
OPERATOR_UI_PANEL_TELEGRAM_CONTROL_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_telegram_operator_control_bot_summary.v1"
)
OPERATOR_UI_PANEL_TELEGRAM_MINI_APP_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_telegram_mini_app_operator_panel_summary.v1"
)
OPERATOR_UI_PANEL_SUPERVISED_TINY_CANARY_APPROVAL_PACKET_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_supervised_tiny_canary_approval_packet_summary.v1"
)
OPERATOR_UI_PANEL_PAPER_CANARY_DRILL_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_paper_canary_drill_summary.v1"
)
OPERATOR_UI_PANEL_PAPER_TRADING_LOOP_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_paper_trading_loop_summary.v1"
)
OPERATOR_UI_PANEL_PUBLIC_MARKET_PAPER_LOOP_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_public_market_paper_loop_summary_054.v1"
)
OPERATOR_UI_PANEL_PAPER_DECISION_LEDGER_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_paper_decision_ledger_summary_055.v1"
)
OPERATOR_UI_PANEL_LIVE_CONNECTOR_PREFLIGHT_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_live_connector_preflight_summary_056.v1"
)
OPERATOR_UI_PANEL_AUTHENTICATED_CLOB_PREFLIGHT_SUMMARY_CONTRACT = (
    "pmbot_operator_ui_panel_authenticated_clob_preflight_summary_057.v1"
)
OPERATOR_UI_PANEL_VALIDATION_CONTRACT = "pmbot_operator_ui_panel_validation.v1"

TASK_ID = "ORCH-PMBOT-TRADING-MVP-036-OPERATOR-UI-PANEL-V1-READINESS-RISK-LIMITS-KILL-SWITCH"

PANEL_MODE = "paper/dry-run/live-disabled/future-canary-review"
LIVE_DISABLED_WARNING = "Live execution is disabled in this build."
NOT_AVAILABLE = "not_available"
REVIEW_PLACEHOLDER = "not_configured_review_placeholder"

FORCED_FALSE_EXECUTION_FIELDS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "live_connector_enabled",
    "allowed_for_live",
    "authenticated_polymarket_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "wallet_signing_enabled",
    "transaction_signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "wallet_enabled",
    "would_submit_order",
    "order_submission_enabled",
)

REQUIRED_SECTION_IDS = (
    "header_execution_posture",
    "readiness_evidence_bundle",
    "live_blockers",
    "live_credentials_auth_boundary",
    "btc_market_connector",
    "btc_analysis_order_intent",
    "live_order_submission_boundary",
    "live_enablement_config_preflight",
    "authenticated_polymarket_connector_scaffold",
    "wallet_signing_boundary",
    "signed_order_payload_validation_gate",
    "tiny_live_canary_gonogo_gate",
    "supervised_tiny_canary_approval_packet",
    "risk_control_plane",
    "risk_limits",
    "kill_switch",
    "telegram_operator_control_bot",
    "telegram_mini_app_operator_panel",
    "paper_trading_loop",
    "public_market_paper_loop",
    "paper_decision_ledger",
    "live_connector_preflight",
    "authenticated_clob_preflight",
    "paper_trading_summary",
    "operator_packets",
    "audit_replay",
    "next_gates",
)

NEXT_REQUIRED_GATES = (
    "UI reviewed",
    "risk limit control plane implemented",
    "live connector remains disabled until future gated task",
    "live credentials/auth boundary reviewed but not operator verified for live",
    "kill-switch live verification missing",
    "funding not configured",
    "real order adapter disabled",
    "operator live approval not implemented",
    "tiny canary still not executable",
    "authenticated Polymarket connector scaffold remains dry-run-only and non-executable",
    "wallet signing boundary remains review-only and non-executable",
    "signed order payload validation gate remains dry-run-only and non-executable",
    "supervised tiny canary approval packet remains review-only and not live approval",
    "Telegram operator control bot remains review-only and exposes no executable live action",
    "Telegram Mini App operator panel remains static review-only and exposes no executable live action",
    "live connector preflight remains review-only and cannot submit orders, sign, or enable live execution",
)


@dataclass(frozen=True)
class OperatorUIPanelMetric:
    metric_id: str
    label: str
    value: Any
    status: str = "review_only"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_METRIC_CONTRACT
        return value


@dataclass(frozen=True)
class OperatorUIPanelWarning:
    warning_id: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_WARNING_CONTRACT
        return value


@dataclass(frozen=True)
class OperatorUIPanelActionState:
    action_id: str
    label: str
    state: str
    execution_enabled: bool = False
    dry_run_control_only: bool = True
    live_action_exposed: bool = False
    requires_future_operator_task: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_ACTION_STATE_CONTRACT
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelSection:
    section_id: str
    title: str
    status: str
    metrics: tuple[Mapping[str, Any], ...]
    warnings: tuple[Mapping[str, Any], ...] = ()
    action_states: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_SECTION_CONTRACT
        value["metrics"] = [dict(row) for row in self.metrics]
        value["warnings"] = [dict(row) for row in self.warnings]
        value["action_states"] = [dict(row) for row in self.action_states]
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelRiskLimitSummary:
    max_daily_loss_usd: Any
    max_total_exposure_usd: Any
    max_market_exposure_usd: Any
    max_order_notional_usd: Any
    max_market_count: Any
    max_order_count: Any
    max_trades_per_day: Any
    cooldown_after_loss: Any
    halt_on_stale_data: bool
    halt_on_audit_mismatch: bool
    halt_on_kill_switch: bool
    halt_on_missing_operator_intent: bool
    review_config_visibility_only: bool = True
    risk_control_execution_gate_added: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_RISK_LIMIT_SUMMARY_CONTRACT
        value["risk_limit_panel_render_ready"] = True
        value["applies_to_live_execution"] = False
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelRiskControlSummary:
    risk_control_plane_status: str
    policy_id: str
    mode: str
    max_daily_loss_usd: Any
    max_total_exposure_usd: Any
    max_market_exposure_usd: Any
    max_order_notional_usd: Any
    max_orders_per_day: Any
    max_trades_per_day: Any
    max_active_markets: Any
    allowed_market_tags: tuple[str, ...]
    latest_decision_status: str
    latest_violations_count: int
    latest_halt_reasons_count: int
    allowed_for_dry_run: bool
    market_data_status: str = "not_evaluated"
    market_data_market_id: str = ""
    market_data_market_slug: str = ""
    market_data_market_status: str = "unknown"
    market_data_is_btc_related: bool | None = None
    market_data_stale: bool = False
    market_data_age_seconds: Any = None
    market_data_freshness_feed_ready: bool = False
    allowed_for_live: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_RISK_CONTROL_SUMMARY_CONTRACT
        value["allowed_market_tags"] = list(self.allowed_market_tags)
        value["risk_control_plane_ready"] = True
        value["risk_limits_enforced_for_order_intents"] = True
        value["future_btc_live_demo_supported_by_limits"] = True
        value["risk_control_panel_render_ready"] = True
        value["execution_enabling"] = False
        value["allowed_for_live"] = False
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelBTCMarketSummary:
    btc_market_connector_status: str
    market_id: str
    market_slug: str
    market_title: str
    is_btc_related: bool
    market_status: str
    is_open: bool
    is_resolved: bool
    stale: bool
    snapshot_age_seconds: Any
    best_bid: Any
    best_ask: Any
    last_price: Any
    spread: Any
    liquidity: Any
    price_status: str
    risk_control_market_data_status: str
    read_only_network_enabled: bool
    latest_btc_market_snapshot_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_BTC_MARKET_SUMMARY_CONTRACT
        value["btc_market_section_ready"] = True
        value["read_only"] = True
        value["execution_enabling"] = False
        value["allowed_for_live"] = False
        value["live_execution_approved"] = False
        value["canary_executable_now"] = False
        value["real_execution_available"] = False
        value["live_connector_enabled"] = False
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelBTCAnalysisOrderIntentSummary:
    btc_market_analysis_status: str
    btc_intent_candidate_status: str
    dry_run_order_intent_status: str
    intent_market_id: str
    intent_market_slug: str
    intent_notional_usd: Any
    intent_limit_price: Any
    risk_decision_status: str
    allowed_for_dry_run: bool
    allowed_for_live: bool
    analysis_is_not_live_recommendation: bool
    order_intent_is_not_order_submission: bool
    latest_btc_analysis_path: str = ""
    latest_btc_order_intent_path: str = ""
    latest_btc_risk_decision_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_BTC_ANALYSIS_SUMMARY_CONTRACT
        value["btc_analysis_order_intent_section_ready"] = True
        value["execution_enabling"] = False
        value["allowed_for_live"] = False
        value["live_execution_approved"] = False
        value["canary_executable_now"] = False
        value["real_execution_available"] = False
        value["live_connector_enabled"] = False
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelLiveCredentialsAuthSummary:
    live_credentials_boundary_status: str
    live_credentials_configured: bool
    required_credentials_count: int
    missing_credentials_count: int
    credential_statuses_redacted: tuple[Mapping[str, Any], ...]
    live_auth_ready_for_future_tiny_canary_review: bool
    warning: str
    authenticated_endpoints_enabled: bool = False
    signing_enabled: bool = False
    cryptographic_signing_enabled: bool = False
    wallet_signing_enabled: bool = False
    order_submission_enabled: bool = False
    allowed_for_live: bool = False
    canary_executable_now: bool = False
    live_execution_approved: bool = False
    real_execution_available: bool = False
    live_connector_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_LIVE_AUTH_SUMMARY_CONTRACT
        value["credential_statuses_redacted"] = [dict(row) for row in self.credential_statuses_redacted]
        value["live_credentials_auth_boundary_section_ready"] = True
        value["redacted_credential_status_ready"] = True
        value["secrets_redacted"] = True
        value["actual_secret_values_exposed"] = False
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelLiveOrderSubmissionBoundarySummary:
    boundary_name: str
    status: str
    dry_run_review_ready: bool
    market_id: str
    market_slug: str
    asset: str
    side: str
    outcome: str
    top_refusal_reasons: tuple[str, ...]
    top_blocker_reasons: tuple[str, ...]
    latest_live_order_submission_boundary_path: str
    would_submit_order: bool = False
    order_submission_enabled: bool = False
    authenticated_endpoint_required: bool = False
    authenticated_endpoint_enabled: bool = False
    authenticated_endpoints_enabled: bool = False
    signing_required_for_future_live: bool = False
    signing_enabled: bool = False
    wallet_required_for_future_live: bool = False
    wallet_enabled: bool = False
    allowed_for_live: bool = False
    canary_executable_now: bool = False
    live_execution_approved: bool = False
    real_execution_available: bool = False
    live_connector_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_LIVE_ORDER_BOUNDARY_SUMMARY_CONTRACT
        value["top_refusal_reasons"] = list(self.top_refusal_reasons)
        value["top_blocker_reasons"] = list(self.top_blocker_reasons)
        value["live_order_submission_boundary_section_ready"] = True
        value["boundary_is_not_live_approval"] = True
        value["receipt_is_not_order_submission"] = True
        value["execution_enabling"] = False
        value["would_submit_order"] = False
        value["order_submission_enabled"] = False
        value["authenticated_endpoint_enabled"] = False
        value["authenticated_endpoints_enabled"] = False
        value["signing_enabled"] = False
        value["wallet_enabled"] = False
        value["allowed_for_live"] = False
        value["live_execution_approved"] = False
        value["canary_executable_now"] = False
        value["real_execution_available"] = False
        value["live_connector_enabled"] = False
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelLiveEnablementConfigPreflightSummary:
    status: str
    future_live_requested: bool
    dry_run_review_allowed: bool
    allowed_for_live: bool
    top_blocked_reasons: tuple[str, ...]
    latest_live_enablement_config_preflight_path: str
    review_only: bool = True
    execution_enabling: bool = False
    live_approval: bool = False
    no_executable_action: bool = True
    canary_executable_now: bool = False
    live_execution_approved: bool = False
    real_execution_available: bool = False
    live_connector_enabled: bool = False
    order_submission_enabled: bool = False
    authenticated_polymarket_enabled: bool = False
    wallet_signing_enabled: bool = False
    resolved_blocker_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_LIVE_ENABLEMENT_CONFIG_PREFLIGHT_SUMMARY_CONTRACT
        value["top_blocked_reasons"] = list(self.top_blocked_reasons)
        value["live_enablement_config_preflight_section_ready"] = True
        value["allowed_for_live"] = False
        value["canary_executable_now"] = False
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["live_connector_enabled"] = False
        value["order_submission_enabled"] = False
        value["authenticated_polymarket_enabled"] = False
        value["wallet_signing_enabled"] = False
        value["resolved_blocker_count"] = 0
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelAuthenticatedPolymarketConnectorScaffoldSummary:
    status: str
    connector_name: str
    credentials_redacted_or_missing_only: bool
    configured_redacted_credential_count: int
    missing_credential_count: int
    top_blocked_reasons: tuple[str, ...]
    latest_authenticated_polymarket_connector_scaffold_path: str
    review_only: bool = True
    execution_enabling: bool = False
    live_approval: bool = False
    no_executable_action: bool = True
    network_calls_enabled: bool = False
    authenticated_calls_enabled: bool = False
    live_connector_enabled: bool = False
    order_submission_enabled: bool = False
    signing_enabled: bool = False
    cryptographic_signing_enabled: bool = False
    wallet_signing_enabled: bool = False
    real_execution_available: bool = False
    allowed_for_live: bool = False
    canary_executable_now: bool = False
    live_execution_approved: bool = False
    authenticated_polymarket_enabled: bool = False
    resolved_blocker_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = (
            OPERATOR_UI_PANEL_AUTHENTICATED_POLYMARKET_CONNECTOR_SCAFFOLD_SUMMARY_CONTRACT
        )
        value["top_blocked_reasons"] = list(self.top_blocked_reasons)
        value["authenticated_polymarket_connector_scaffold_section_ready"] = True
        value["credentials_summary"] = "redacted_or_missing_only"
        value["review_only"] = True
        value["execution_enabling"] = False
        value["live_approval"] = False
        value["no_executable_action"] = True
        value["network_calls_enabled"] = False
        value["authenticated_calls_enabled"] = False
        value["live_connector_enabled"] = False
        value["order_submission_enabled"] = False
        value["signing_enabled"] = False
        value["cryptographic_signing_enabled"] = False
        value["wallet_signing_enabled"] = False
        value["real_execution_available"] = False
        value["allowed_for_live"] = False
        value["canary_executable_now"] = False
        value["live_execution_approved"] = False
        value["authenticated_polymarket_enabled"] = False
        value["resolved_blocker_count"] = 0
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelWalletSigningBoundarySummary:
    status: str
    wallet_address_status: str
    signing_provider_status: str
    top_blocked_reasons: tuple[str, ...]
    latest_wallet_signing_boundary_path: str
    review_only: bool = True
    execution_enabling: bool = False
    live_approval: bool = False
    no_executable_action: bool = True
    wallet_signing_enabled: bool = False
    signing_enabled: bool = False
    cryptographic_signing_enabled: bool = False
    transaction_signing_enabled: bool = False
    signed_payload_generation_enabled: bool = False
    signed_order_generation_enabled: bool = False
    allowed_for_live: bool = False
    canary_executable_now: bool = False
    live_execution_approved: bool = False
    real_execution_available: bool = False
    live_connector_enabled: bool = False
    order_submission_enabled: bool = False
    resolved_blocker_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_WALLET_SIGNING_BOUNDARY_SUMMARY_CONTRACT
        value["top_blocked_reasons"] = list(self.top_blocked_reasons)
        value["wallet_signing_boundary_section_ready"] = True
        value["review_only"] = True
        value["execution_enabling"] = False
        value["live_approval"] = False
        value["no_executable_action"] = True
        value["wallet_signing_enabled"] = False
        value["signing_enabled"] = False
        value["cryptographic_signing_enabled"] = False
        value["transaction_signing_enabled"] = False
        value["signed_payload_generation_enabled"] = False
        value["signed_order_generation_enabled"] = False
        value["allowed_for_live"] = False
        value["canary_executable_now"] = False
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["live_connector_enabled"] = False
        value["order_submission_enabled"] = False
        value["resolved_blocker_count"] = 0
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelSignedOrderPayloadValidationGateSummary:
    status: str
    payload_shape_status: str
    top_blocked_reasons: tuple[str, ...]
    latest_signed_order_payload_validation_gate_path: str
    review_only: bool = True
    execution_enabling: bool = False
    live_approval: bool = False
    no_executable_action: bool = True
    signing_enabled: bool = False
    wallet_signing_enabled: bool = False
    signed_payload_generation_enabled: bool = False
    signed_order_generation_enabled: bool = False
    order_submission_enabled: bool = False
    authenticated_polymarket_enabled: bool = False
    live_connector_enabled: bool = False
    allowed_for_live: bool = False
    canary_executable_now: bool = False
    live_execution_approved: bool = False
    real_execution_available: bool = False
    resolved_blocker_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_SIGNED_ORDER_PAYLOAD_VALIDATION_GATE_SUMMARY_CONTRACT
        value["top_blocked_reasons"] = list(self.top_blocked_reasons)
        value["signed_order_payload_validation_gate_section_ready"] = True
        value["review_only"] = True
        value["execution_enabling"] = False
        value["live_approval"] = False
        value["no_executable_action"] = True
        value["signing_enabled"] = False
        value["wallet_signing_enabled"] = False
        value["signed_payload_generation_enabled"] = False
        value["signed_order_generation_enabled"] = False
        value["order_submission_enabled"] = False
        value["authenticated_polymarket_enabled"] = False
        value["live_connector_enabled"] = False
        value["allowed_for_live"] = False
        value["canary_executable_now"] = False
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["resolved_blocker_count"] = 0
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelKillSwitchSummary:
    kill_switch_requirements_defined: bool
    kill_switch_verified_for_live: bool
    kill_switch_blocks_live_execution: bool
    emergency_stop_documented: bool
    current_kill_switch_state: str
    latest_kill_switch_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_KILL_SWITCH_SUMMARY_CONTRACT
        value["kill_switch_panel_render_ready"] = True
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelTelegramOperatorControlSummary:
    configured: bool
    telegram_bot_token_status: str
    allowed_operator_ids_configured: bool
    allowed_operator_id_count: int
    operator_pause_requested: bool
    operator_kill_switch_requested: bool
    latest_telegram_operator_control_state_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_TELEGRAM_CONTROL_SUMMARY_CONTRACT
        value["telegram_operator_control_bot_section_ready"] = True
        value["review_only"] = True
        value["execution_enabling"] = False
        value["live_approval"] = False
        value["ui_exposes_no_executable_live_action"] = True
        value["raw_telegram_bot_token_exposed"] = False
        value["raw_operator_user_ids_exposed"] = False
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelTelegramMiniAppSummary:
    panel_artifact_available: bool
    review_only: bool
    live_actions_available: bool
    latest_telegram_mini_app_operator_panel_html_path: str = ""
    latest_telegram_mini_app_operator_panel_json_path: str = ""
    mini_app_url_status: str = "not_configured_review_placeholder"
    telegram_init_data_status: str = "not_configured_redacted"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_TELEGRAM_MINI_APP_SUMMARY_CONTRACT
        value["telegram_mini_app_operator_panel_section_ready"] = True
        value["telegram_mini_app_operator_panel_ready"] = self.panel_artifact_available
        value["review_only"] = True
        value["live_actions_available"] = False
        value["execution_enabling"] = False
        value["live_approval"] = False
        value["raw_telegram_bot_token_exposed"] = False
        value["raw_telegram_init_data_exposed"] = False
        value["raw_operator_user_ids_exposed"] = False
        value["ui_exposes_no_executable_live_action"] = True
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelSupervisedTinyCanaryApprovalPacketSummary:
    status: str
    approval_packet_ready_for_human_review: bool
    packet_cannot_be_interpreted_as_live_approval: bool
    operator_must_not_execute_from_this_packet: bool
    future_live_enabling_task_required: bool
    section_count: int
    operator_checklist_count: int
    future_required_action_count: int
    unresolved_blocker_count: int
    latest_supervised_tiny_canary_approval_packet_json_path: str = ""
    latest_supervised_tiny_canary_approval_packet_md_path: str = ""
    review_only: bool = True
    approval_packet_may_be_used_as_live_approval: bool = False
    live_execution_approved: bool = False
    canary_executable_now: bool = False
    real_execution_available: bool = False
    execution_enabling: bool = False
    order_submission_enabled: bool = False
    wallet_signing_enabled: bool = False
    signing_enabled: bool = False
    signed_payload_generation_enabled: bool = False
    signed_order_generation_enabled: bool = False
    authenticated_polymarket_enabled: bool = False
    live_connector_enabled: bool = False
    allowed_for_live: bool = False
    resolved_blocker_count: int = 0
    no_executable_action: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_SUPERVISED_TINY_CANARY_APPROVAL_PACKET_SUMMARY_CONTRACT
        value["supervised_tiny_canary_approval_packet_section_ready"] = True
        value["approval_packet_ready_for_human_review"] = self.approval_packet_ready_for_human_review
        value["packet_cannot_be_interpreted_as_live_approval"] = True
        value["approval_packet_may_be_used_as_live_approval"] = False
        value["operator_must_not_execute_from_this_packet"] = True
        value["future_live_enabling_task_required"] = True
        value["review_only"] = True
        value["execution_enabling"] = False
        value["no_executable_action"] = True
        value["live_execution_approved"] = False
        value["canary_executable_now"] = False
        value["real_execution_available"] = False
        value["order_submission_enabled"] = False
        value["wallet_signing_enabled"] = False
        value["signing_enabled"] = False
        value["signed_payload_generation_enabled"] = False
        value["signed_order_generation_enabled"] = False
        value["authenticated_polymarket_enabled"] = False
        value["live_connector_enabled"] = False
        value["allowed_for_live"] = False
        value["resolved_blocker_count"] = 0
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelReadinessSummary:
    mode: str
    current_execution_posture: str
    paper_trading_status: str
    operator_review_ready: bool
    evidence_bundle_review_ready: bool
    live_execution_approved: bool
    canary_executable_now: bool
    real_execution_available: bool
    live_connector_enabled: bool

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_READINESS_SUMMARY_CONTRACT
        value["warning"] = LIVE_DISABLED_WARNING
        value["operator_ui_panel_ready"] = True
        value["readiness_panel_render_ready"] = True
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelEvidenceSummary:
    readiness_evidence_bundle_status: str
    evidence_item_count: int
    missing_required_evidence_count: int
    latest_readiness_evidence_bundle_path: str
    readiness_bundle_is_not_live_approval: bool
    evidence_bundle_review_ready: bool
    validation_status: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_EVIDENCE_SUMMARY_CONTRACT
        value["readiness_evidence_bundle_is_not_live_approval"] = True
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelBlockerSummary:
    blocker_matrix_status: str
    total_blockers: int
    critical_blockers: int
    unresolved_blockers: int
    resolved_blockers: int
    top_blockers: tuple[Mapping[str, Any], ...]
    all_blockers_unresolved: bool
    why_live_execution_is_blocked: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_BLOCKER_SUMMARY_CONTRACT
        value["top_blockers"] = [dict(row) for row in self.top_blockers]
        value["why_live_execution_is_blocked"] = list(self.why_live_execution_is_blocked)
        value["blocker_panel_ready"] = True
        value.update(_panel_safety_flags())
        return value


@dataclass(frozen=True)
class OperatorUIPanelV1:
    panel_id: str
    task_id: str
    generated_at: str
    readiness_summary: Mapping[str, Any]
    evidence_summary: Mapping[str, Any]
    blocker_summary: Mapping[str, Any]
    live_credentials_auth_boundary_summary: Mapping[str, Any]
    btc_market_summary: Mapping[str, Any]
    btc_analysis_order_intent_summary: Mapping[str, Any]
    live_order_submission_boundary_summary: Mapping[str, Any]
    live_enablement_config_preflight_summary: Mapping[str, Any]
    authenticated_polymarket_connector_scaffold_summary: Mapping[str, Any]
    wallet_signing_boundary_summary: Mapping[str, Any]
    signed_order_payload_validation_gate_summary: Mapping[str, Any]
    tiny_live_canary_gonogo_gate_summary: Mapping[str, Any]
    supervised_tiny_canary_approval_packet_summary: Mapping[str, Any]
    risk_control_plane_summary: Mapping[str, Any]
    risk_limit_summary: Mapping[str, Any]
    kill_switch_summary: Mapping[str, Any]
    telegram_operator_control_bot_summary: Mapping[str, Any]
    telegram_mini_app_operator_panel_summary: Mapping[str, Any]
    paper_summary: Mapping[str, Any]
    paper_decision_ledger_status_summary: Mapping[str, Any]
    operator_packet_summary: Mapping[str, Any]
    audit_replay_summary: Mapping[str, Any]
    next_required_gates: tuple[str, ...]
    action_states: tuple[Mapping[str, Any], ...]
    sections: tuple[Mapping[str, Any], ...]
    render_outputs_supported: tuple[str, ...] = ("json", "markdown", "html")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_UI_PANEL_V1_CONTRACT
        value["schema_version"] = "036.v1"
        value["readiness_summary"] = dict(self.readiness_summary)
        value["evidence_summary"] = dict(self.evidence_summary)
        value["blocker_summary"] = dict(self.blocker_summary)
        value["live_credentials_auth_boundary_summary"] = dict(self.live_credentials_auth_boundary_summary)
        value["btc_market_summary"] = dict(self.btc_market_summary)
        value["btc_analysis_order_intent_summary"] = dict(self.btc_analysis_order_intent_summary)
        value["live_order_submission_boundary_summary"] = dict(self.live_order_submission_boundary_summary)
        value["live_enablement_config_preflight_summary"] = dict(
            self.live_enablement_config_preflight_summary
        )
        value["authenticated_polymarket_connector_scaffold_summary"] = dict(
            self.authenticated_polymarket_connector_scaffold_summary
        )
        value["wallet_signing_boundary_summary"] = dict(self.wallet_signing_boundary_summary)
        value["signed_order_payload_validation_gate_summary"] = dict(
            self.signed_order_payload_validation_gate_summary
        )
        value["tiny_live_canary_gonogo_gate_summary"] = dict(self.tiny_live_canary_gonogo_gate_summary)
        value["supervised_tiny_canary_approval_packet_summary"] = dict(
            self.supervised_tiny_canary_approval_packet_summary
        )
        value["risk_control_plane_summary"] = dict(self.risk_control_plane_summary)
        value["risk_limit_summary"] = dict(self.risk_limit_summary)
        value["kill_switch_summary"] = dict(self.kill_switch_summary)
        value["telegram_operator_control_bot_summary"] = dict(self.telegram_operator_control_bot_summary)
        value["telegram_mini_app_operator_panel_summary"] = dict(self.telegram_mini_app_operator_panel_summary)
        value["paper_summary"] = dict(self.paper_summary)
        value["paper_decision_ledger_status_summary"] = dict(self.paper_decision_ledger_status_summary)
        value["operator_packet_summary"] = dict(self.operator_packet_summary)
        value["audit_replay_summary"] = dict(self.audit_replay_summary)
        value["next_required_gates"] = list(self.next_required_gates)
        value["action_states"] = [dict(row) for row in self.action_states]
        value["sections"] = [dict(row) for row in self.sections]
        value["render_outputs_supported"] = list(self.render_outputs_supported)
        value["operator_ui_panel_ready"] = True
        value["readiness_panel_render_ready"] = True
        value["risk_limit_panel_render_ready"] = True
        value["risk_control_panel_render_ready"] = True
        value["kill_switch_panel_render_ready"] = True
        value["telegram_operator_control_bot_section_ready"] = True
        value["telegram_mini_app_operator_panel_section_ready"] = True
        value["paper_summary_panel_ready"] = True
        value["paper_decision_ledger_section_ready"] = True
        value["blocker_panel_ready"] = True
        value["live_credentials_auth_boundary_section_ready"] = True
        value["btc_market_section_ready"] = True
        value["btc_analysis_order_intent_section_ready"] = True
        value["live_order_submission_boundary_section_ready"] = True
        value["live_enablement_config_preflight_section_ready"] = True
        value["authenticated_polymarket_connector_scaffold_section_ready"] = True
        value["wallet_signing_boundary_section_ready"] = True
        value["signed_order_payload_validation_gate_section_ready"] = True
        value["tiny_live_canary_gonogo_gate_section_ready"] = True
        value["supervised_tiny_canary_approval_packet_section_ready"] = True
        value["static_html_render_ready"] = True
        value["markdown_render_ready"] = True
        value["json_render_ready"] = True
        value["ui_panel_is_not_live_execution_console"] = True
        value["ui_exposes_no_executable_live_action"] = True
        value["readiness_evidence_bundle_is_not_live_approval"] = True
        value["operator_intent_is_not_live_approval"] = True
        value.update(_panel_safety_flags())
        return value


def build_operator_ui_panel_v1(
    *,
    dashboard: Mapping[str, Any] | None = None,
    readiness_evidence_bundle: Mapping[str, Any] | None = None,
    readiness_evidence_bundle_summary: Mapping[str, Any] | None = None,
    blocker_matrix: Mapping[str, Any] | None = None,
    risk_limit_policy: Mapping[str, Any] | None = None,
    latest_risk_limit_decision: Mapping[str, Any] | None = None,
    risk_control_plane_summary: Mapping[str, Any] | None = None,
    btc_market_snapshot: Mapping[str, Any] | None = None,
    btc_read_only_connector_summary: Mapping[str, Any] | None = None,
    btc_analysis_order_intent_summary: Mapping[str, Any] | None = None,
    live_order_submission_boundary_receipt: Mapping[str, Any] | None = None,
    live_order_submission_boundary_summary: Mapping[str, Any] | None = None,
    live_enablement_config_preflight: Mapping[str, Any] | None = None,
    live_enablement_config_preflight_summary: Mapping[str, Any] | None = None,
    authenticated_polymarket_connector_scaffold: Mapping[str, Any] | None = None,
    authenticated_polymarket_connector_scaffold_summary: Mapping[str, Any] | None = None,
    wallet_signing_boundary_report: Mapping[str, Any] | None = None,
    wallet_signing_boundary_summary: Mapping[str, Any] | None = None,
    signed_order_payload_validation_gate: Mapping[str, Any] | None = None,
    signed_order_payload_validation_gate_summary: Mapping[str, Any] | None = None,
    tiny_live_canary_gonogo_gate: Mapping[str, Any] | None = None,
    tiny_live_canary_gonogo_gate_summary: Mapping[str, Any] | None = None,
    supervised_tiny_canary_approval_packet: Mapping[str, Any] | None = None,
    supervised_tiny_canary_approval_packet_summary: Mapping[str, Any] | None = None,
    live_credentials_auth_boundary_summary: Mapping[str, Any] | None = None,
    risk_limits: Mapping[str, Any] | None = None,
    risk_prep_config: Mapping[str, Any] | None = None,
    portfolio_summary: Mapping[str, Any] | None = None,
    portfolio_state: Mapping[str, Any] | None = None,
    strategy_summary: Mapping[str, Any] | None = None,
    canary_readiness_summary: Mapping[str, Any] | None = None,
    tiny_live_canary_preflight_result: Mapping[str, Any] | None = None,
    tiny_live_canary_preflight_contract: Mapping[str, Any] | None = None,
    tiny_live_canary_manual_runbook: Mapping[str, Any] | None = None,
    operator_live_approval_packet: Mapping[str, Any] | None = None,
    operator_intent_packet: Mapping[str, Any] | None = None,
    operator_intent_summary: Mapping[str, Any] | None = None,
    live_connector_audit_replay: Mapping[str, Any] | None = None,
    live_connector_audit_operator_summary: Mapping[str, Any] | None = None,
    live_connector_preflight_status_summary: Mapping[str, Any] | None = None,
    authenticated_clob_preflight_status_summary: Mapping[str, Any] | None = None,
    telegram_operator_control_bot_summary: Mapping[str, Any] | None = None,
    telegram_mini_app_operator_panel_summary: Mapping[str, Any] | None = None,
    latest_paths: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    dashboard_value = dict(dashboard or {})
    paths = {clean_text(key): clean_text(value) for key, value in dict(latest_paths or {}).items()}
    evidence_summary = _build_evidence_summary(
        readiness_evidence_bundle=readiness_evidence_bundle,
        readiness_evidence_bundle_summary=(
            readiness_evidence_bundle_summary
            or dashboard_value.get("readiness_evidence_bundle_summary", {})
        ),
        latest_path=paths.get("readiness_evidence_bundle", ""),
    )
    blocker_summary = _build_blocker_summary(
        blocker_matrix=blocker_matrix,
        canary_readiness_summary=canary_readiness_summary or dashboard_value.get("live_canary_readiness_summary", {}),
    )
    policy = dict(risk_limit_policy or dashboard_value.get("risk_limit_policy", {}) or build_default_risk_limit_policy(generated_at=generated_at))
    latest_decision = latest_risk_limit_decision or dashboard_value.get("latest_risk_limit_decision")
    risk_control_summary = _build_risk_control_plane_summary(
        risk_control_plane_summary=risk_control_plane_summary
        or dashboard_value.get("risk_control_plane_summary", {}),
        risk_limit_policy=policy,
        latest_risk_limit_decision=latest_decision if isinstance(latest_decision, Mapping) else None,
        generated_at=generated_at,
    )
    btc_market_summary = _build_btc_market_summary(
        btc_market_snapshot=btc_market_snapshot or dashboard_value.get("btc_market_snapshot", {}),
        btc_read_only_connector_summary=(
            btc_read_only_connector_summary
            or dashboard_value.get("btc_market_snapshot_summary", {})
            or dashboard_value.get("btc_read_only_connector_summary", {})
        ),
        latest_btc_market_snapshot_path=(
            paths.get("btc_market_snapshot", "")
            or clean_text(dashboard_value.get("latest_btc_market_snapshot_path"))
        ),
    )
    btc_analysis_summary = _build_btc_analysis_order_intent_summary(
        btc_analysis_order_intent_summary=(
            btc_analysis_order_intent_summary
            or dashboard_value.get("btc_analysis_order_intent_summary", {})
            or dashboard_value.get("btc_market_analysis_summary", {})
        ),
        latest_btc_analysis_path=paths.get("btc_market_analysis", "")
        or clean_text(dashboard_value.get("latest_btc_analysis_path")),
        latest_btc_order_intent_path=paths.get("btc_order_intent_dry_run", "")
        or clean_text(dashboard_value.get("latest_btc_order_intent_path")),
        latest_btc_risk_decision_path=paths.get("btc_risk_decision", "")
        or clean_text(dashboard_value.get("latest_btc_risk_decision_path")),
        generated_at=generated_at,
    )
    live_order_boundary_summary = _build_live_order_submission_boundary_summary(
        live_order_submission_boundary_receipt=(
            live_order_submission_boundary_receipt
            or dashboard_value.get("live_order_submission_boundary_receipt", {})
        ),
        live_order_submission_boundary_summary=(
            live_order_submission_boundary_summary
            or dashboard_value.get("live_order_submission_boundary_summary", {})
            or dashboard_value.get("live_order_submission_boundary_section_feed", {})
        ),
        latest_live_order_submission_boundary_path=paths.get("live_order_submission_boundary", "")
        or clean_text(dashboard_value.get("latest_live_order_submission_boundary_path")),
        generated_at=generated_at,
    )
    live_enablement_config_summary = _build_live_enablement_config_preflight_summary(
        live_enablement_config_preflight=live_enablement_config_preflight
        or dashboard_value.get("live_enablement_config_preflight", {}),
        live_enablement_config_preflight_summary=(
            live_enablement_config_preflight_summary
            or dashboard_value.get("live_enablement_config_preflight_summary", {})
        ),
        latest_live_enablement_config_preflight_path=paths.get("live_enablement_config_preflight", "")
        or clean_text(dashboard_value.get("latest_live_enablement_config_preflight_path")),
        generated_at=generated_at,
    )
    authenticated_connector_summary = _build_authenticated_polymarket_connector_scaffold_summary(
        authenticated_polymarket_connector_scaffold=authenticated_polymarket_connector_scaffold
        or dashboard_value.get("authenticated_polymarket_connector_scaffold", {}),
        authenticated_polymarket_connector_scaffold_summary=(
            authenticated_polymarket_connector_scaffold_summary
            or dashboard_value.get("authenticated_polymarket_connector_scaffold_summary", {})
        ),
        latest_authenticated_polymarket_connector_scaffold_path=(
            paths.get("authenticated_polymarket_connector_scaffold", "")
            or clean_text(dashboard_value.get("latest_authenticated_polymarket_connector_scaffold_path"))
        ),
        generated_at=generated_at,
    )
    wallet_signing_boundary_ui_summary = _build_wallet_signing_boundary_summary(
        wallet_signing_boundary_report=wallet_signing_boundary_report
        or dashboard_value.get("wallet_signing_boundary_report", {}),
        wallet_signing_boundary_summary=(
            wallet_signing_boundary_summary
            or dashboard_value.get("wallet_signing_boundary_summary", {})
        ),
        latest_wallet_signing_boundary_path=paths.get("wallet_signing_boundary", "")
        or clean_text(dashboard_value.get("latest_wallet_signing_boundary_path")),
        generated_at=generated_at,
    )
    signed_order_payload_validation_gate_ui_summary = _build_signed_order_payload_validation_gate_summary(
        signed_order_payload_validation_gate=signed_order_payload_validation_gate
        or dashboard_value.get("signed_order_payload_validation_gate", {}),
        signed_order_payload_validation_gate_summary=(
            signed_order_payload_validation_gate_summary
            or dashboard_value.get("signed_order_payload_validation_gate_summary", {})
        ),
        latest_signed_order_payload_validation_gate_path=paths.get("signed_order_payload_validation_gate", "")
        or clean_text(dashboard_value.get("latest_signed_order_payload_validation_gate_path")),
        generated_at=generated_at,
    )
    gonogo_summary = _build_tiny_live_canary_gonogo_gate_summary(
        tiny_live_canary_gonogo_gate=tiny_live_canary_gonogo_gate
        or dashboard_value.get("tiny_live_canary_gonogo_gate", {}),
        tiny_live_canary_gonogo_gate_summary=(
            tiny_live_canary_gonogo_gate_summary
            or dashboard_value.get("tiny_live_canary_gonogo_gate_summary", {})
        ),
        latest_tiny_live_canary_gonogo_gate_path=paths.get("tiny_live_canary_gonogo_gate", "")
        or clean_text(dashboard_value.get("latest_tiny_live_canary_gonogo_gate_path")),
        generated_at=generated_at,
    )
    supervised_tiny_canary_packet_summary = _build_supervised_tiny_canary_approval_packet_summary(
        supervised_tiny_canary_approval_packet=supervised_tiny_canary_approval_packet
        or dashboard_value.get("supervised_tiny_canary_approval_packet", {}),
        supervised_tiny_canary_approval_packet_summary=(
            supervised_tiny_canary_approval_packet_summary
            or dashboard_value.get("supervised_tiny_canary_approval_packet_summary", {})
        ),
        latest_supervised_tiny_canary_approval_packet_json_path=(
            paths.get("supervised_tiny_canary_approval_packet", "")
            or clean_text(dashboard_value.get("latest_supervised_tiny_canary_approval_packet_path"))
        ),
        latest_supervised_tiny_canary_approval_packet_md_path=(
            paths.get("supervised_tiny_canary_approval_packet_md", "")
            or clean_text(dashboard_value.get("latest_supervised_tiny_canary_approval_packet_md_path"))
        ),
        generated_at=generated_at,
    )
    live_auth_summary = _build_live_credentials_auth_boundary_summary(
        live_credentials_auth_boundary_summary=(
            live_credentials_auth_boundary_summary
            or dashboard_value.get("live_credentials_auth_boundary_summary", {})
            or dashboard_value.get("live_credentials_auth_boundary_section_feed", {})
            or btc_analysis_summary
        ),
        generated_at=generated_at,
    )
    risk_summary = _build_risk_limit_summary(
        risk_limits=risk_limits,
        risk_prep_config=risk_prep_config,
        risk_limit_policy=policy,
        risk_control_plane_summary=risk_control_summary,
    )
    kill_switch_summary = _build_kill_switch_summary(
        preflight_result=tiny_live_canary_preflight_result
        or dashboard_value.get("tiny_live_canary_preflight_runbook_summary", {}),
        preflight_contract=tiny_live_canary_preflight_contract,
        manual_runbook=tiny_live_canary_manual_runbook,
        latest_reference=paths.get("tiny_live_canary_preflight_contract", ""),
    )
    telegram_control_summary = _build_telegram_operator_control_bot_summary(
        telegram_operator_control_bot_summary=telegram_operator_control_bot_summary
        or dashboard_value.get("telegram_operator_control_bot_summary", {}),
        latest_reference=paths.get("telegram_operator_control_state", "")
        or clean_text(dashboard_value.get("latest_telegram_operator_control_state_path")),
    )
    telegram_mini_app_summary = _build_telegram_mini_app_operator_panel_summary(
        telegram_mini_app_operator_panel_summary=telegram_mini_app_operator_panel_summary
        or dashboard_value.get("telegram_mini_app_operator_panel_summary", {}),
        latest_html_reference=paths.get("telegram_mini_app_operator_panel_html", "")
        or clean_text(dashboard_value.get("latest_telegram_mini_app_operator_panel_html_path")),
        latest_json_reference=paths.get("telegram_mini_app_operator_panel_json", "")
        or clean_text(dashboard_value.get("latest_telegram_mini_app_operator_panel_json_path")),
    )
    operator_packet_summary = _build_operator_packet_summary(
        operator_live_approval_packet=operator_live_approval_packet,
        operator_intent_packet=operator_intent_packet,
        operator_intent_summary=operator_intent_summary or dashboard_value.get("operator_intent_packet_summary", {}),
        operator_review_summary=dashboard_value.get("live_connector_audit_operator_summary", {}),
        latest_operator_packet_path=paths.get("operator_live_approval_packet", ""),
        latest_operator_intent_packet_path=paths.get("operator_intent_packet", ""),
    )
    audit_summary = _build_audit_replay_summary(
        live_connector_audit_replay=live_connector_audit_replay,
        audit_operator_summary=live_connector_audit_operator_summary
        or dashboard_value.get("live_connector_audit_operator_summary", {}),
        latest_audit_replay_path=paths.get("live_connector_audit_replay", ""),
    )
    paper_summary = _build_paper_summary(
        dashboard=dashboard_value,
        portfolio_summary=portfolio_summary or dashboard_value.get("portfolio_summary", {}),
        portfolio_state=portfolio_state,
        strategy_summary=strategy_summary or dashboard_value.get("paper_strategy_evaluation_summary", {}),
        latest_paper_run_reference=paths.get("paper_daily_loop_result", ""),
    )
    paper_canary_drill_summary = _build_paper_canary_drill_summary(
        paper_canary_drill_status=(
            dashboard_value.get("paper_canary_drill_status_summary")
            or dashboard_value.get("paper_canary_drill_status")
            or dashboard_value.get("latest_paper_canary_status")
            or {}
        ),
        latest_status_path=paths.get("paper_canary_drill_status", "")
        or clean_text(dashboard_value.get("latest_paper_canary_status_path")),
    )
    paper_trading_loop_summary = _build_paper_trading_loop_summary(
        paper_trading_loop_status=(
            dashboard_value.get("paper_trading_loop_status_summary")
            or dashboard_value.get("paper_trading_loop_status")
            or dashboard_value.get("latest_paper_trading_status")
            or {}
        ),
        latest_status_path=paths.get("paper_trading_loop_status", "")
        or clean_text(dashboard_value.get("latest_paper_trading_status_path")),
    )
    public_market_paper_loop_summary = _build_public_market_paper_loop_summary(
        public_market_paper_loop_status=(
            dashboard_value.get("public_market_paper_loop_status_summary")
            or dashboard_value.get("public_market_paper_loop_status")
            or dashboard_value.get("latest_public_market_paper_status")
            or {}
        ),
        latest_status_path=paths.get("public_market_paper_loop_status", "")
        or clean_text(dashboard_value.get("latest_public_market_paper_status_path")),
    )
    paper_decision_ledger_summary = _build_paper_decision_ledger_summary(
        paper_decision_ledger_status=(
            dashboard_value.get("paper_decision_ledger_status_summary")
            or dashboard_value.get("paper_decision_ledger_status")
            or dashboard_value.get("latest_paper_decision_ledger_status")
            or {}
        ),
        latest_status_path=paths.get("paper_decision_ledger_status", "")
        or clean_text(dashboard_value.get("latest_paper_decision_ledger_status_path")),
    )
    live_connector_preflight_summary = _build_live_connector_preflight_summary(
        live_connector_preflight_status=(
            live_connector_preflight_status_summary
            or dashboard_value.get("live_connector_preflight_status_summary")
            or dashboard_value.get("live_connector_preflight_status")
            or dashboard_value.get("latest_live_connector_preflight_status")
            or {}
        ),
        latest_status_path=paths.get("live_connector_preflight_status", "")
        or clean_text(dashboard_value.get("latest_live_connector_preflight_status_path")),
    )
    authenticated_clob_preflight_summary = _build_authenticated_clob_preflight_summary(
        authenticated_clob_preflight_status=(
            authenticated_clob_preflight_status_summary
            or dashboard_value.get("authenticated_clob_preflight_status_summary")
            or dashboard_value.get("authenticated_clob_preflight_status")
            or dashboard_value.get("latest_authenticated_clob_preflight_status")
            or {}
        ),
        latest_status_path=paths.get("authenticated_clob_preflight_status", "")
        or clean_text(dashboard_value.get("latest_authenticated_clob_preflight_status_path")),
    )
    readiness = _build_readiness_summary(
        operator_review_ready=operator_packet_summary.get("operator_approval_packet_review_ready") is True,
        evidence_bundle_review_ready=evidence_summary.get("evidence_bundle_review_ready") is True,
    )
    action_states = tuple(_build_action_states())
    sections = _build_sections(
        readiness=readiness,
        evidence=evidence_summary,
        blockers=blocker_summary,
        live_auth=live_auth_summary,
        btc_market=btc_market_summary,
        btc_analysis_order_intent=btc_analysis_summary,
        live_order_submission_boundary=live_order_boundary_summary,
        live_enablement_config_preflight=live_enablement_config_summary,
        authenticated_polymarket_connector_scaffold=authenticated_connector_summary,
        wallet_signing_boundary=wallet_signing_boundary_ui_summary,
        signed_order_payload_validation_gate=signed_order_payload_validation_gate_ui_summary,
        tiny_live_canary_gonogo_gate=gonogo_summary,
        supervised_tiny_canary_approval_packet=supervised_tiny_canary_packet_summary,
        risk_control=risk_control_summary,
        risk=risk_summary,
        kill_switch=kill_switch_summary,
        telegram_operator_control=telegram_control_summary,
        telegram_mini_app=telegram_mini_app_summary,
        paper=paper_summary,
        paper_canary_drill=paper_canary_drill_summary,
        paper_trading_loop=paper_trading_loop_summary,
        public_market_paper_loop=public_market_paper_loop_summary,
        paper_decision_ledger=paper_decision_ledger_summary,
        live_connector_preflight=live_connector_preflight_summary,
        authenticated_clob_preflight=authenticated_clob_preflight_summary,
        operator_packets=operator_packet_summary,
        audit=audit_summary,
        action_states=action_states,
    )
    panel_id = _stable_id(
        "operator-ui-panel-v1-036",
        {
            "mode": PANEL_MODE,
            "evidence_status": evidence_summary.get("readiness_evidence_bundle_status"),
            "evidence_item_count": evidence_summary.get("evidence_item_count"),
            "missing_required_evidence_count": evidence_summary.get("missing_required_evidence_count"),
            "blocker_count": blocker_summary.get("total_blockers"),
            "unresolved_blocker_count": blocker_summary.get("unresolved_blockers"),
            "live_auth": live_auth_summary,
            "btc_market": btc_market_summary,
            "btc_analysis_order_intent": btc_analysis_summary,
            "live_order_submission_boundary": live_order_boundary_summary,
            "live_enablement_config_preflight": live_enablement_config_summary,
            "authenticated_polymarket_connector_scaffold": authenticated_connector_summary,
            "wallet_signing_boundary": wallet_signing_boundary_ui_summary,
            "signed_order_payload_validation_gate": signed_order_payload_validation_gate_ui_summary,
            "tiny_live_canary_gonogo_gate": gonogo_summary,
            "supervised_tiny_canary_approval_packet": supervised_tiny_canary_packet_summary,
            "risk_control": risk_control_summary,
            "risk": risk_summary,
            "kill_switch": kill_switch_summary,
            "telegram_operator_control": telegram_control_summary,
            "telegram_mini_app": telegram_mini_app_summary,
            "paper": paper_summary,
            "paper_canary_drill": paper_canary_drill_summary,
            "paper_trading_loop": paper_trading_loop_summary,
            "public_market_paper_loop": public_market_paper_loop_summary,
            "paper_decision_ledger": paper_decision_ledger_summary,
            "live_connector_preflight": live_connector_preflight_summary,
            "authenticated_clob_preflight": authenticated_clob_preflight_summary,
        },
    )
    panel = OperatorUIPanelV1(
        panel_id=panel_id,
        task_id=TASK_ID,
        generated_at=generated_at,
        readiness_summary=readiness,
        evidence_summary=evidence_summary,
        blocker_summary=blocker_summary,
        live_credentials_auth_boundary_summary=live_auth_summary,
        btc_market_summary=btc_market_summary,
        btc_analysis_order_intent_summary=btc_analysis_summary,
        live_order_submission_boundary_summary=live_order_boundary_summary,
        live_enablement_config_preflight_summary=live_enablement_config_summary,
        authenticated_polymarket_connector_scaffold_summary=authenticated_connector_summary,
        wallet_signing_boundary_summary=wallet_signing_boundary_ui_summary,
        signed_order_payload_validation_gate_summary=signed_order_payload_validation_gate_ui_summary,
        tiny_live_canary_gonogo_gate_summary=gonogo_summary,
        supervised_tiny_canary_approval_packet_summary=supervised_tiny_canary_packet_summary,
        risk_control_plane_summary=risk_control_summary,
        risk_limit_summary=risk_summary,
        kill_switch_summary=kill_switch_summary,
        telegram_operator_control_bot_summary=telegram_control_summary,
        telegram_mini_app_operator_panel_summary=telegram_mini_app_summary,
        paper_summary=paper_summary,
        paper_decision_ledger_status_summary=paper_decision_ledger_summary,
        operator_packet_summary=operator_packet_summary,
        audit_replay_summary=audit_summary,
        next_required_gates=NEXT_REQUIRED_GATES,
        action_states=action_states,
        sections=tuple(sections),
    ).to_dict()
    panel["paper_canary_drill_status_summary"] = paper_canary_drill_summary
    panel["paper_canary_drill_section_ready"] = True
    panel["paper_trading_loop_status_summary"] = paper_trading_loop_summary
    panel["paper_trading_loop_section_ready"] = True
    panel["public_market_paper_loop_status_summary"] = public_market_paper_loop_summary
    panel["public_market_paper_loop_section_ready"] = True
    panel["paper_decision_ledger_status_summary"] = paper_decision_ledger_summary
    panel["paper_decision_ledger_section_ready"] = True
    panel["live_connector_preflight_status_summary"] = live_connector_preflight_summary
    panel["live_connector_preflight_section_ready"] = True
    panel["authenticated_clob_preflight_status_summary"] = authenticated_clob_preflight_summary
    panel["authenticated_clob_preflight_section_ready"] = True
    validation = validate_operator_ui_panel_v1(panel, generated_at=generated_at)
    panel["validation"] = validation
    return panel


def validate_operator_ui_panel_v1(
    panel: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    statuses: list[str] = []
    panel_value = dict(panel)
    if panel_value.get("contract_version") != OPERATOR_UI_PANEL_V1_CONTRACT:
        errors.append(f"contract_version must be {OPERATOR_UI_PANEL_V1_CONTRACT}")
    if panel_value.get("operator_ui_panel_ready") is not True:
        errors.append("operator_ui_panel_ready must be true")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if panel_value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_live_execution_flag")
    if panel_value.get("ui_panel_is_not_live_execution_console") is not True:
        errors.append("ui_panel_is_not_live_execution_console must be true")
    if panel_value.get("ui_exposes_no_executable_live_action") is not True:
        errors.append("ui_exposes_no_executable_live_action must be true")

    section_ids = [clean_text(row.get("section_id")) for row in mapping_rows(panel_value.get("sections"))]
    for section_id in REQUIRED_SECTION_IDS:
        if section_id not in section_ids:
            errors.append(f"missing required section {section_id}")

    risk_validation = validate_secret_boundary_operator_ui_panel_risk_limit_summary(
        dict(panel_value.get("risk_limit_summary", {})),
        generated_at=generated_at,
    )
    if risk_validation.get("valid") is not True:
        errors.append("risk_limit_summary violates static secret boundary")
        statuses.append("risk_limit_summary_secret_boundary_blocked")

    risk_control_validation = validate_secret_boundary_risk_control_ui_summary(
        dict(panel_value.get("risk_control_plane_summary", {})),
        generated_at=generated_at,
    )
    if risk_control_validation.get("valid") is not True:
        errors.append("risk_control_plane_summary violates static secret boundary")
        statuses.append("risk_control_summary_secret_boundary_blocked")
    if panel_value.get("risk_control_plane_summary", {}).get("allowed_for_live") is not False:
        errors.append("risk_control_plane_summary.allowed_for_live must be false")
        statuses.append("risk_control_live_allowance_detected")

    live_auth_validation = validate_secret_boundary_live_credentials_auth_summary(
        dict(panel_value.get("live_credentials_auth_boundary_summary", {})),
        generated_at=generated_at,
    )
    if live_auth_validation.get("valid") is not True:
        errors.append("live_credentials_auth_boundary_summary violates static secret boundary")
        statuses.append("live_credentials_auth_summary_secret_boundary_blocked")
    live_auth_summary = dict(panel_value.get("live_credentials_auth_boundary_summary", {}))
    for field in (
        "authenticated_endpoints_enabled",
        "signing_enabled",
        "cryptographic_signing_enabled",
        "wallet_signing_enabled",
        "order_submission_enabled",
        "allowed_for_live",
        "canary_executable_now",
        "live_execution_approved",
        "real_execution_available",
        "live_connector_enabled",
    ):
        if live_auth_summary.get(field) is not False:
            errors.append(f"live_credentials_auth_boundary_summary.{field} must be false")
            statuses.append("live_auth_execution_flag_detected")

    btc_ui_validation = validate_secret_boundary_btc_ui_summary(
        dict(panel_value.get("btc_market_summary", {})),
        generated_at=generated_at,
    )
    if btc_ui_validation.get("valid") is not True:
        errors.append("btc_market_summary violates static secret boundary")
        statuses.append("btc_market_summary_secret_boundary_blocked")
    if panel_value.get("btc_market_summary", {}).get("execution_enabling") is not False:
        errors.append("btc_market_summary.execution_enabling must be false")
        statuses.append("btc_market_execution_enabling_detected")
    if panel_value.get("btc_market_summary", {}).get("allowed_for_live") is not False:
        errors.append("btc_market_summary.allowed_for_live must be false")
        statuses.append("btc_market_live_allowance_detected")

    btc_analysis_ui_validation = validate_secret_boundary_btc_analysis_ui_summary(
        dict(panel_value.get("btc_analysis_order_intent_summary", {})),
        generated_at=generated_at,
    )
    if btc_analysis_ui_validation.get("valid") is not True:
        errors.append("btc_analysis_order_intent_summary violates static secret boundary")
        statuses.append("btc_analysis_summary_secret_boundary_blocked")
    if panel_value.get("btc_analysis_order_intent_summary", {}).get("allowed_for_live") is not False:
        errors.append("btc_analysis_order_intent_summary.allowed_for_live must be false")
        statuses.append("btc_analysis_live_allowance_detected")
    if (
        panel_value.get("btc_analysis_order_intent_summary", {}).get("order_intent_is_not_order_submission")
        is not True
    ):
        errors.append("btc_analysis_order_intent_summary.order_intent_is_not_order_submission must be true")
    if (
        panel_value.get("btc_analysis_order_intent_summary", {}).get("analysis_is_not_live_recommendation")
        is not True
    ):
        errors.append("btc_analysis_order_intent_summary.analysis_is_not_live_recommendation must be true")

    live_order_boundary_summary = dict(panel_value.get("live_order_submission_boundary_summary", {}))
    live_order_boundary_validation = validate_secret_boundary_live_order_submission_boundary_summary(
        live_order_boundary_summary,
        generated_at=generated_at,
    )
    if live_order_boundary_validation.get("valid") is not True:
        errors.append("live_order_submission_boundary_summary violates static secret boundary")
        statuses.append("live_order_boundary_summary_secret_boundary_blocked")
    for field in (
        "would_submit_order",
        "order_submission_enabled",
        "authenticated_endpoint_enabled",
        "authenticated_endpoints_enabled",
        "signing_enabled",
        "wallet_enabled",
        "allowed_for_live",
        "canary_executable_now",
        "live_execution_approved",
        "real_execution_available",
        "live_connector_enabled",
    ):
        if live_order_boundary_summary.get(field) is not False:
            errors.append(f"live_order_submission_boundary_summary.{field} must be false")
            statuses.append("live_order_boundary_execution_flag_detected")
    if live_order_boundary_summary.get("boundary_is_not_live_approval") is not True:
        errors.append("live_order_submission_boundary_summary.boundary_is_not_live_approval must be true")
    if live_order_boundary_summary.get("receipt_is_not_order_submission") is not True:
        errors.append("live_order_submission_boundary_summary.receipt_is_not_order_submission must be true")

    live_enablement_config_summary = dict(panel_value.get("live_enablement_config_preflight_summary", {}))
    live_enablement_config_validation = (
        validate_secret_boundary_operator_ui_panel_live_enablement_config_preflight_summary(
            live_enablement_config_summary,
            generated_at=generated_at,
        )
    )
    if live_enablement_config_validation.get("valid") is not True:
        errors.append("live_enablement_config_preflight_summary violates static secret boundary")
        statuses.append("live_enablement_config_preflight_summary_secret_boundary_blocked")
    if live_enablement_config_summary.get("live_enablement_config_preflight_section_ready") is not True:
        errors.append("live_enablement_config_preflight_section_ready must be true")
        statuses.append("live_enablement_config_preflight_section_missing")
    if live_enablement_config_summary.get("review_only") is not True:
        errors.append("live_enablement_config_preflight_summary.review_only must be true")
        statuses.append("live_enablement_config_preflight_not_review_only")
    if live_enablement_config_summary.get("no_executable_action") is not True:
        errors.append("live_enablement_config_preflight_summary.no_executable_action must be true")
        statuses.append("live_enablement_config_preflight_executable_action_detected")
    if live_enablement_config_summary.get("execution_enabling") is not False:
        errors.append("live_enablement_config_preflight_summary.execution_enabling must be false")
        statuses.append("live_enablement_config_preflight_execution_enabling_detected")
    if live_enablement_config_summary.get("live_approval") is not False:
        errors.append("live_enablement_config_preflight_summary.live_approval must be false")
        statuses.append("live_enablement_config_preflight_live_approval_detected")
    if live_enablement_config_summary.get("resolved_blocker_count") != 0:
        errors.append("live_enablement_config_preflight_summary.resolved_blocker_count must be 0")
        statuses.append("live_enablement_config_preflight_resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if live_enablement_config_summary.get(field) is not False:
            errors.append(f"live_enablement_config_preflight_summary.{field} must be false")
            statuses.append("live_enablement_config_preflight_execution_flag_detected")

    authenticated_connector_summary = dict(
        panel_value.get("authenticated_polymarket_connector_scaffold_summary", {})
    )
    authenticated_connector_validation = (
        validate_secret_boundary_operator_ui_panel_authenticated_polymarket_connector_scaffold_summary(
            authenticated_connector_summary,
            generated_at=generated_at,
        )
    )
    if authenticated_connector_validation.get("valid") is not True:
        errors.append("authenticated_polymarket_connector_scaffold_summary violates static secret boundary")
        statuses.append("authenticated_polymarket_connector_scaffold_summary_secret_boundary_blocked")
    if (
        authenticated_connector_summary.get("authenticated_polymarket_connector_scaffold_section_ready")
        is not True
    ):
        errors.append("authenticated_polymarket_connector_scaffold_section_ready must be true")
        statuses.append("authenticated_polymarket_connector_scaffold_section_missing")
    if authenticated_connector_summary.get("review_only") is not True:
        errors.append("authenticated_polymarket_connector_scaffold_summary.review_only must be true")
        statuses.append("authenticated_polymarket_connector_scaffold_not_review_only")
    if authenticated_connector_summary.get("no_executable_action") is not True:
        errors.append("authenticated_polymarket_connector_scaffold_summary.no_executable_action must be true")
        statuses.append("authenticated_polymarket_connector_scaffold_executable_action_detected")
    if authenticated_connector_summary.get("execution_enabling") is not False:
        errors.append("authenticated_polymarket_connector_scaffold_summary.execution_enabling must be false")
        statuses.append("authenticated_polymarket_connector_scaffold_execution_enabling_detected")
    if authenticated_connector_summary.get("live_approval") is not False:
        errors.append("authenticated_polymarket_connector_scaffold_summary.live_approval must be false")
        statuses.append("authenticated_polymarket_connector_scaffold_live_approval_detected")
    if authenticated_connector_summary.get("resolved_blocker_count") != 0:
        errors.append("authenticated_polymarket_connector_scaffold_summary.resolved_blocker_count must be 0")
        statuses.append("authenticated_polymarket_connector_scaffold_resolved_blocker_detected")
    if authenticated_connector_summary.get("credentials_redacted_or_missing_only") is not True:
        errors.append("authenticated_polymarket_connector_scaffold_summary credentials must be redacted or missing")
        statuses.append("authenticated_polymarket_connector_scaffold_credential_redaction_missing")
    for field in (
        "network_calls_enabled",
        "authenticated_calls_enabled",
        "live_connector_enabled",
        "order_submission_enabled",
        "signing_enabled",
        "cryptographic_signing_enabled",
        "wallet_signing_enabled",
        "real_execution_available",
        "allowed_for_live",
        "canary_executable_now",
        "live_execution_approved",
        "authenticated_polymarket_enabled",
    ):
        if authenticated_connector_summary.get(field) is not False:
            errors.append(f"authenticated_polymarket_connector_scaffold_summary.{field} must be false")
            statuses.append("authenticated_polymarket_connector_scaffold_execution_flag_detected")

    wallet_signing_summary = dict(panel_value.get("wallet_signing_boundary_summary", {}))
    wallet_signing_validation = validate_secret_boundary_operator_ui_panel_wallet_signing_boundary_summary(
        wallet_signing_summary,
        generated_at=generated_at,
    )
    if wallet_signing_validation.get("valid") is not True:
        errors.append("wallet_signing_boundary_summary violates static secret boundary")
        statuses.append("wallet_signing_boundary_summary_secret_boundary_blocked")
    if wallet_signing_summary.get("wallet_signing_boundary_section_ready") is not True:
        errors.append("wallet_signing_boundary_section_ready must be true")
        statuses.append("wallet_signing_boundary_section_missing")
    if wallet_signing_summary.get("review_only") is not True:
        errors.append("wallet_signing_boundary_summary.review_only must be true")
        statuses.append("wallet_signing_boundary_review_only_missing")
    if wallet_signing_summary.get("no_executable_action") is not True:
        errors.append("wallet_signing_boundary_summary.no_executable_action must be true")
        statuses.append("wallet_signing_boundary_executable_action_detected")
    if wallet_signing_summary.get("resolved_blocker_count") != 0:
        errors.append("wallet_signing_boundary_summary.resolved_blocker_count must be 0")
        statuses.append("wallet_signing_boundary_resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if wallet_signing_summary.get(field) is not False:
            errors.append(f"wallet_signing_boundary_summary.{field} must be false")
            statuses.append("wallet_signing_boundary_execution_flag_detected")

    signed_payload_gate_summary = dict(panel_value.get("signed_order_payload_validation_gate_summary", {}))
    signed_payload_gate_validation = (
        validate_secret_boundary_operator_ui_panel_signed_order_payload_validation_gate_summary(
            signed_payload_gate_summary,
            generated_at=generated_at,
        )
    )
    if signed_payload_gate_validation.get("valid") is not True:
        errors.append("signed_order_payload_validation_gate_summary violates static secret boundary")
        statuses.append("signed_order_payload_validation_gate_summary_secret_boundary_blocked")
    if signed_payload_gate_summary.get("signed_order_payload_validation_gate_section_ready") is not True:
        errors.append("signed_order_payload_validation_gate_section_ready must be true")
        statuses.append("signed_order_payload_validation_gate_section_missing")
    if signed_payload_gate_summary.get("review_only") is not True:
        errors.append("signed_order_payload_validation_gate_summary.review_only must be true")
        statuses.append("signed_order_payload_validation_gate_review_only_missing")
    if signed_payload_gate_summary.get("no_executable_action") is not True:
        errors.append("signed_order_payload_validation_gate_summary.no_executable_action must be true")
        statuses.append("signed_order_payload_validation_gate_executable_action_detected")
    if signed_payload_gate_summary.get("resolved_blocker_count") != 0:
        errors.append("signed_order_payload_validation_gate_summary.resolved_blocker_count must be 0")
        statuses.append("signed_order_payload_validation_gate_resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if signed_payload_gate_summary.get(field) is not False:
            errors.append(f"signed_order_payload_validation_gate_summary.{field} must be false")
            statuses.append("signed_order_payload_validation_gate_execution_flag_detected")

    gonogo_summary = dict(panel_value.get("tiny_live_canary_gonogo_gate_summary", {}))
    if gonogo_summary.get("no_executable_action") is not True:
        errors.append("tiny_live_canary_gonogo_gate_summary.no_executable_action must be true")
        statuses.append("gonogo_gate_executable_action_detected")
    if gonogo_summary.get("explicit_human_approval_required") is not True:
        errors.append("tiny_live_canary_gonogo_gate_summary.explicit_human_approval_required must be true")
        statuses.append("gonogo_gate_missing_human_approval_requirement")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if gonogo_summary.get(field) is not False:
            errors.append(f"tiny_live_canary_gonogo_gate_summary.{field} must be false")
            statuses.append("gonogo_gate_execution_flag_detected")

    supervised_packet_summary = dict(panel_value.get("supervised_tiny_canary_approval_packet_summary", {}))
    supervised_packet_validation = validate_secret_boundary_supervised_tiny_canary_approval_packet_summary(
        supervised_packet_summary,
        generated_at=generated_at,
    )
    if supervised_packet_validation.get("valid") is not True:
        errors.append("supervised_tiny_canary_approval_packet_summary violates static secret boundary")
        statuses.append("supervised_tiny_canary_approval_packet_summary_secret_boundary_blocked")
    if supervised_packet_summary.get("supervised_tiny_canary_approval_packet_section_ready") is not True:
        errors.append("supervised_tiny_canary_approval_packet_section_ready must be true")
        statuses.append("supervised_tiny_canary_approval_packet_section_missing")
    if supervised_packet_summary.get("review_only") is not True:
        errors.append("supervised_tiny_canary_approval_packet_summary.review_only must be true")
        statuses.append("supervised_tiny_canary_approval_packet_not_review_only")
    if supervised_packet_summary.get("approval_packet_may_be_used_as_live_approval") is not False:
        errors.append(
            "supervised_tiny_canary_approval_packet_summary."
            "approval_packet_may_be_used_as_live_approval must be false"
        )
        statuses.append("supervised_tiny_canary_approval_packet_live_approval_interpretation_detected")
    if supervised_packet_summary.get("packet_cannot_be_interpreted_as_live_approval") is not True:
        errors.append(
            "supervised_tiny_canary_approval_packet_summary."
            "packet_cannot_be_interpreted_as_live_approval must be true"
        )
        statuses.append("supervised_tiny_canary_approval_packet_live_approval_interpretation_detected")
    if supervised_packet_summary.get("operator_must_not_execute_from_this_packet") is not True:
        errors.append("supervised_tiny_canary_approval_packet_summary.operator_must_not_execute must be true")
        statuses.append("supervised_tiny_canary_approval_packet_execution_interpretation_detected")
    if supervised_packet_summary.get("future_live_enabling_task_required") is not True:
        errors.append("supervised_tiny_canary_approval_packet_summary.future_live_enabling_task_required must be true")
        statuses.append("supervised_tiny_canary_approval_packet_missing_future_gate")
    if supervised_packet_summary.get("no_executable_action") is not True:
        errors.append("supervised_tiny_canary_approval_packet_summary.no_executable_action must be true")
        statuses.append("supervised_tiny_canary_approval_packet_executable_action_detected")
    if supervised_packet_summary.get("resolved_blocker_count") != 0:
        errors.append("supervised_tiny_canary_approval_packet_summary.resolved_blocker_count must be 0")
        statuses.append("supervised_tiny_canary_approval_packet_resolved_blocker_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if supervised_packet_summary.get(field) is not False:
            errors.append(f"supervised_tiny_canary_approval_packet_summary.{field} must be false")
            statuses.append("supervised_tiny_canary_approval_packet_execution_flag_detected")

    kill_validation = validate_secret_boundary_operator_ui_panel_kill_switch_summary(
        dict(panel_value.get("kill_switch_summary", {})),
        generated_at=generated_at,
    )
    if kill_validation.get("valid") is not True:
        errors.append("kill_switch_summary violates static secret boundary")
        statuses.append("kill_switch_summary_secret_boundary_blocked")

    action_live_exposed = []
    for index, action in enumerate(mapping_rows(panel_value.get("action_states"))):
        if action.get("execution_enabled") is not False:
            errors.append(f"action_states[{index}].execution_enabled must be false")
            statuses.append("executable_action_detected")
        if action.get("live_action_exposed") is not False:
            action_live_exposed.append(index)
        action_validation = validate_secret_boundary_operator_ui_panel_action_state(
            dict(action),
            generated_at=generated_at,
        )
        if action_validation.get("valid") is not True:
            errors.append(f"action_states[{index}] violates static secret boundary")
            statuses.append("action_state_secret_boundary_blocked")
    if action_live_exposed:
        errors.append(f"live action exposed at indexes {action_live_exposed}")
        statuses.append("live_action_exposed")

    for path, key, value in _walk_flags(panel_value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and value is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_live_execution_flag")
    if panel_value.get("risk_limit_summary", {}).get("risk_control_execution_gate_added") is not False:
        errors.append("risk_control_execution_gate_added must be false")
    if panel_value.get("kill_switch_summary", {}).get("kill_switch_verified_for_live") is not False:
        errors.append("kill_switch_verified_for_live must be false")
    telegram_summary = dict(panel_value.get("telegram_operator_control_bot_summary", {}))
    if telegram_summary.get("telegram_operator_control_bot_section_ready") is not True:
        errors.append("telegram_operator_control_bot_section_ready must be true")
        statuses.append("telegram_operator_control_section_missing")
    if telegram_summary.get("review_only") is not True:
        errors.append("telegram_operator_control_bot_summary.review_only must be true")
        statuses.append("telegram_operator_control_review_only_missing")
    if telegram_summary.get("execution_enabling") is not False:
        errors.append("telegram_operator_control_bot_summary.execution_enabling must be false")
        statuses.append("telegram_operator_control_execution_enabling_detected")
    if telegram_summary.get("live_approval") is not False:
        errors.append("telegram_operator_control_bot_summary.live_approval must be false")
        statuses.append("telegram_operator_control_live_approval_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if telegram_summary.get(field) is not False:
            errors.append(f"telegram_operator_control_bot_summary.{field} must be false")
            statuses.append("telegram_operator_control_execution_flag_detected")
    mini_app_summary = dict(panel_value.get("telegram_mini_app_operator_panel_summary", {}))
    if mini_app_summary.get("telegram_mini_app_operator_panel_section_ready") is not True:
        errors.append("telegram_mini_app_operator_panel_section_ready must be true")
        statuses.append("telegram_mini_app_section_missing")
    if mini_app_summary.get("review_only") is not True:
        errors.append("telegram_mini_app_operator_panel_summary.review_only must be true")
        statuses.append("telegram_mini_app_review_only_missing")
    if mini_app_summary.get("live_actions_available") is not False:
        errors.append("telegram_mini_app_operator_panel_summary.live_actions_available must be false")
        statuses.append("telegram_mini_app_live_action_detected")
    if mini_app_summary.get("execution_enabling") is not False:
        errors.append("telegram_mini_app_operator_panel_summary.execution_enabling must be false")
        statuses.append("telegram_mini_app_execution_enabling_detected")
    if mini_app_summary.get("live_approval") is not False:
        errors.append("telegram_mini_app_operator_panel_summary.live_approval must be false")
        statuses.append("telegram_mini_app_live_approval_detected")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if mini_app_summary.get(field) is not False:
            errors.append(f"telegram_mini_app_operator_panel_summary.{field} must be false")
            statuses.append("telegram_mini_app_execution_flag_detected")
    if panel_value.get("evidence_summary", {}).get("readiness_bundle_is_not_live_approval") is not True:
        errors.append("readiness_bundle_is_not_live_approval must be true")
    if panel_value.get("blocker_summary", {}).get("all_blockers_unresolved") is not True:
        errors.append("all_blockers_unresolved must be true")

    payload_validation = validate_secret_boundary_operator_ui_panel_payload(
        panel_value,
        generated_at=generated_at,
    )
    if payload_validation.get("valid") is not True:
        errors.append("operator UI panel payload violates static secret boundary")
        statuses.append("payload_secret_boundary_blocked")

    rendered_json = render_operator_ui_panel_v1_json(panel_value, include_validation=False)
    rendered_json_validation = validate_secret_boundary_operator_ui_panel_rendered_json(
        rendered_json,
        generated_at=generated_at,
    )
    rendered_md_validation = validate_secret_boundary_operator_ui_panel_rendered_markdown(
        render_operator_ui_panel_v1_markdown(panel_value),
        generated_at=generated_at,
    )
    rendered_html_validation = validate_secret_boundary_operator_ui_panel_rendered_html(
        render_operator_ui_panel_v1_html(panel_value),
        generated_at=generated_at,
    )
    for label, validation in (
        ("rendered_json", rendered_json_validation),
        ("rendered_markdown", rendered_md_validation),
        ("rendered_html", rendered_html_validation),
    ):
        if validation.get("valid") is not True:
            errors.append(f"{label} violates static secret boundary")
            statuses.append(f"{label}_secret_boundary_blocked")

    valid = not errors
    return {
        "contract_version": OPERATOR_UI_PANEL_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "operator-ui-panel-validation-036",
            {"panel_id": panel_value.get("panel_id"), "errors": errors, "statuses": statuses},
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses) or (["operator_ui_panel_valid"] if valid else ["operator_ui_panel_blocked"]),
        "errors": errors,
        "secret_boundary_validation": payload_validation,
        "btc_market_summary_secret_boundary_validation": btc_ui_validation,
        "btc_analysis_summary_secret_boundary_validation": btc_analysis_ui_validation,
        "live_credentials_auth_summary_secret_boundary_validation": live_auth_validation,
        "live_order_submission_boundary_summary_secret_boundary_validation": live_order_boundary_validation,
        "operator_ui_panel_live_enablement_config_preflight_summary_secret_boundary_validation": (
            live_enablement_config_validation
        ),
        "operator_ui_panel_authenticated_polymarket_connector_scaffold_summary_secret_boundary_validation": (
            authenticated_connector_validation
        ),
        "operator_ui_panel_wallet_signing_boundary_summary_secret_boundary_validation": wallet_signing_validation,
        "operator_ui_panel_signed_order_payload_validation_gate_summary_secret_boundary_validation": (
            signed_payload_gate_validation
        ),
        "supervised_tiny_canary_approval_packet_summary_secret_boundary_validation": (
            supervised_packet_validation
        ),
        "rendered_json_secret_boundary_validation": rendered_json_validation,
        "rendered_markdown_secret_boundary_validation": rendered_md_validation,
        "rendered_html_secret_boundary_validation": rendered_html_validation,
        "operator_ui_panel_ready": valid,
        "ui_panel_is_not_live_execution_console": True,
        "ui_exposes_no_executable_live_action": True,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def summarize_operator_ui_panel_v1(panel: Mapping[str, Any]) -> dict[str, Any]:
    validation = dict(panel.get("validation", {}))
    return {
        "contract_version": "pmbot_operator_ui_panel_summary.v1",
        "panel_id": clean_text(panel.get("panel_id")),
        "operator_ui_panel_ready": panel.get("operator_ui_panel_ready") is True,
        "readiness_panel_render_ready": panel.get("readiness_panel_render_ready") is True,
        "risk_limit_panel_render_ready": panel.get("risk_limit_panel_render_ready") is True,
        "kill_switch_panel_render_ready": panel.get("kill_switch_panel_render_ready") is True,
        "telegram_operator_control_bot_section_ready": panel.get(
            "telegram_operator_control_bot_section_ready"
        )
        is True,
        "paper_canary_drill_section_ready": panel.get("paper_canary_drill_section_ready") is True,
        "paper_canary_drill_status": dict(panel.get("paper_canary_drill_status_summary", {})).get("status"),
        "paper_canary_drill_market": dict(panel.get("paper_canary_drill_status_summary", {})).get("market"),
        "paper_canary_drill_live_execution": dict(panel.get("paper_canary_drill_status_summary", {})).get(
            "live_execution"
        ),
        "paper_canary_drill_latest_status_path": dict(
            panel.get("paper_canary_drill_status_summary", {})
        ).get("latest_status_path"),
        "paper_trading_loop_section_ready": panel.get("paper_trading_loop_section_ready") is True,
        "paper_trading_loop_status": dict(panel.get("paper_trading_loop_status_summary", {})).get("status"),
        "paper_trading_loop_market": dict(panel.get("paper_trading_loop_status_summary", {})).get("market"),
        "paper_trading_loop_strategy": dict(panel.get("paper_trading_loop_status_summary", {})).get(
            "strategy_name"
        ),
        "paper_trading_loop_live_execution": dict(panel.get("paper_trading_loop_status_summary", {})).get(
            "live_execution"
        ),
        "paper_trading_loop_risk_decision": dict(panel.get("paper_trading_loop_status_summary", {})).get(
            "risk_decision"
        ),
        "paper_trading_loop_intent_status": dict(panel.get("paper_trading_loop_status_summary", {})).get(
            "paper_intent_status"
        ),
        "paper_trading_loop_latest_status_path": dict(
            panel.get("paper_trading_loop_status_summary", {})
        ).get("latest_status_path"),
        "public_market_paper_loop_section_ready": panel.get("public_market_paper_loop_section_ready") is True,
        "public_market_paper_loop_status": dict(
            panel.get("public_market_paper_loop_status_summary", {})
        ).get("status"),
        "public_market_paper_loop_source": dict(
            panel.get("public_market_paper_loop_status_summary", {})
        ).get("source"),
        "public_market_paper_loop_evidence_pack_path": dict(
            panel.get("public_market_paper_loop_status_summary", {})
        ).get("evidence_pack_path"),
        "public_market_paper_loop_live_execution": dict(
            panel.get("public_market_paper_loop_status_summary", {})
        ).get("live_execution"),
        "public_market_paper_loop_risk_decision": dict(
            panel.get("public_market_paper_loop_status_summary", {})
        ).get("risk_decision"),
        "public_market_paper_loop_intent_status": dict(
            panel.get("public_market_paper_loop_status_summary", {})
        ).get("paper_intent_status"),
        "paper_decision_ledger_section_ready": panel.get("paper_decision_ledger_section_ready") is True,
        "paper_decision_ledger_last_outcome": dict(
            panel.get("paper_decision_ledger_status_summary", {})
        ).get("last_outcome"),
        "paper_decision_ledger_entry_count": dict(
            panel.get("paper_decision_ledger_status_summary", {})
        ).get("ledger_entry_count"),
        "paper_decision_ledger_count_by_outcome": dict(
            panel.get("paper_decision_ledger_status_summary", {})
        ).get("count_by_outcome"),
        "paper_decision_ledger_evidence_pack_path": dict(
            panel.get("paper_decision_ledger_status_summary", {})
        ).get("evidence_pack_path"),
        "paper_decision_ledger_live_execution_blocked": dict(
            panel.get("paper_decision_ledger_status_summary", {})
        ).get("live_execution_blocked"),
        "live_connector_preflight_section_ready": panel.get("live_connector_preflight_section_ready") is True,
        "live_connector_preflight_status": dict(
            panel.get("live_connector_preflight_status_summary", {})
        ).get("status"),
        "live_connector_preflight_public_network_status": dict(
            panel.get("live_connector_preflight_status_summary", {})
        ).get("public_network_status"),
        "live_connector_preflight_auth_boundary_status": dict(
            panel.get("live_connector_preflight_status_summary", {})
        ).get("auth_boundary_status"),
        "live_connector_preflight_order_submission_blocked": dict(
            panel.get("live_connector_preflight_status_summary", {})
        ).get("order_submission_blocked"),
        "live_connector_preflight_signing_blocked": dict(
            panel.get("live_connector_preflight_status_summary", {})
        ).get("signing_blocked"),
        "live_connector_preflight_live_execution_blocked": dict(
            panel.get("live_connector_preflight_status_summary", {})
        ).get("live_execution_blocked"),
        "authenticated_clob_preflight_section_ready": panel.get(
            "authenticated_clob_preflight_section_ready"
        )
        is True,
        "authenticated_clob_preflight_status": dict(
            panel.get("authenticated_clob_preflight_status_summary", {})
        ).get("status"),
        "authenticated_clob_preflight_auth_presence_status": dict(
            panel.get("authenticated_clob_preflight_status_summary", {})
        ).get("auth_presence_status"),
        "authenticated_clob_preflight_clob_base_url_status": dict(
            panel.get("authenticated_clob_preflight_status_summary", {})
        ).get("clob_base_url_status"),
        "authenticated_clob_preflight_order_submission_blocked": dict(
            panel.get("authenticated_clob_preflight_status_summary", {})
        ).get("order_submission_blocked"),
        "authenticated_clob_preflight_signing_blocked": dict(
            panel.get("authenticated_clob_preflight_status_summary", {})
        ).get("signing_blocked"),
        "authenticated_clob_preflight_wallet_connection_blocked": dict(
            panel.get("authenticated_clob_preflight_status_summary", {})
        ).get("wallet_connection_blocked"),
        "authenticated_clob_preflight_live_execution_blocked": dict(
            panel.get("authenticated_clob_preflight_status_summary", {})
        ).get("live_execution_blocked"),
        "paper_summary_panel_ready": panel.get("paper_summary_panel_ready") is True,
        "blocker_panel_ready": panel.get("blocker_panel_ready") is True,
        "static_html_render_ready": panel.get("static_html_render_ready") is True,
        "markdown_render_ready": panel.get("markdown_render_ready") is True,
        "json_render_ready": panel.get("json_render_ready") is True,
        "validation_status": clean_text(validation.get("status") or "not_validated"),
        "validation_error_count": len(validation.get("errors", [])),
        "ui_panel_is_not_live_execution_console": panel.get("ui_panel_is_not_live_execution_console") is True,
        "ui_exposes_no_executable_live_action": panel.get("ui_exposes_no_executable_live_action") is True,
        "readiness_evidence_bundle_status": dict(panel.get("evidence_summary", {})).get(
            "readiness_evidence_bundle_status"
        ),
        "blocker_matrix_status": dict(panel.get("blocker_summary", {})).get("blocker_matrix_status"),
        "live_credentials_auth_boundary_section_ready": dict(
            panel.get("live_credentials_auth_boundary_summary", {})
        ).get("live_credentials_auth_boundary_section_ready")
        is True,
        "live_credentials_boundary_status": dict(panel.get("live_credentials_auth_boundary_summary", {})).get(
            "live_credentials_boundary_status"
        ),
        "live_credentials_configured": dict(panel.get("live_credentials_auth_boundary_summary", {})).get(
            "live_credentials_configured"
        )
        is True,
        "redacted_credential_status_ready": dict(panel.get("live_credentials_auth_boundary_summary", {})).get(
            "redacted_credential_status_ready"
        )
        is True,
        "risk_control_plane_status": dict(panel.get("risk_control_plane_summary", {})).get(
            "risk_control_plane_status"
        ),
        "risk_control_plane_ready": dict(panel.get("risk_control_plane_summary", {})).get(
            "risk_control_plane_ready"
        )
        is True,
        "btc_market_section_ready": dict(panel.get("btc_market_summary", {})).get("btc_market_section_ready")
        is True,
        "btc_market_connector_status": dict(panel.get("btc_market_summary", {})).get(
            "btc_market_connector_status"
        ),
        "btc_market_status": dict(panel.get("btc_market_summary", {})).get("market_status"),
        "btc_market_stale": dict(panel.get("btc_market_summary", {})).get("stale") is True,
        "btc_analysis_order_intent_section_ready": dict(
            panel.get("btc_analysis_order_intent_summary", {})
        ).get("btc_analysis_order_intent_section_ready")
        is True,
        "btc_market_analysis_status": dict(panel.get("btc_analysis_order_intent_summary", {})).get(
            "btc_market_analysis_status"
        ),
        "btc_intent_candidate_status": dict(panel.get("btc_analysis_order_intent_summary", {})).get(
            "btc_intent_candidate_status"
        ),
        "dry_run_order_intent_status": dict(panel.get("btc_analysis_order_intent_summary", {})).get(
            "dry_run_order_intent_status"
        ),
        "btc_analysis_allowed_for_dry_run": dict(panel.get("btc_analysis_order_intent_summary", {})).get(
            "allowed_for_dry_run"
        )
        is True,
        "live_order_submission_boundary_section_ready": dict(
            panel.get("live_order_submission_boundary_summary", {})
        ).get("live_order_submission_boundary_section_ready")
        is True,
        "live_order_submission_boundary_status": dict(
            panel.get("live_order_submission_boundary_summary", {})
        ).get("status"),
        "live_order_submission_boundary_dry_run_review_ready": dict(
            panel.get("live_order_submission_boundary_summary", {})
        ).get("dry_run_review_ready")
        is True,
        "live_order_submission_boundary_order_submission_enabled": dict(
            panel.get("live_order_submission_boundary_summary", {})
        ).get("order_submission_enabled")
        is True,
        "live_enablement_config_preflight_section_ready": dict(
            panel.get("live_enablement_config_preflight_summary", {})
        ).get("live_enablement_config_preflight_section_ready")
        is True,
        "live_enablement_config_preflight_status": dict(
            panel.get("live_enablement_config_preflight_summary", {})
        ).get("status"),
        "live_enablement_config_future_live_requested": dict(
            panel.get("live_enablement_config_preflight_summary", {})
        ).get("future_live_requested")
        is True,
        "live_enablement_config_dry_run_review_allowed": dict(
            panel.get("live_enablement_config_preflight_summary", {})
        ).get("dry_run_review_allowed")
        is True,
        "live_enablement_config_allowed_for_live": False,
        "authenticated_polymarket_connector_scaffold_section_ready": dict(
            panel.get("authenticated_polymarket_connector_scaffold_summary", {})
        ).get("authenticated_polymarket_connector_scaffold_section_ready")
        is True,
        "authenticated_polymarket_connector_scaffold_status": dict(
            panel.get("authenticated_polymarket_connector_scaffold_summary", {})
        ).get("status"),
        "authenticated_polymarket_connector_network_calls_enabled": False,
        "authenticated_polymarket_connector_authenticated_calls_enabled": False,
        "authenticated_polymarket_connector_order_submission_enabled": False,
        "authenticated_polymarket_connector_real_execution_available": False,
        "authenticated_polymarket_connector_credentials_redacted_or_missing_only": dict(
            panel.get("authenticated_polymarket_connector_scaffold_summary", {})
        ).get("credentials_redacted_or_missing_only")
        is True,
        "wallet_signing_boundary_section_ready": dict(
            panel.get("wallet_signing_boundary_summary", {})
        ).get("wallet_signing_boundary_section_ready")
        is True,
        "wallet_signing_boundary_status": dict(panel.get("wallet_signing_boundary_summary", {})).get("status"),
        "wallet_signing_enabled": dict(panel.get("wallet_signing_boundary_summary", {})).get(
            "wallet_signing_enabled"
        )
        is True,
        "signing_enabled": dict(panel.get("wallet_signing_boundary_summary", {})).get("signing_enabled")
        is True,
        "signed_payload_generation_enabled": dict(
            panel.get("wallet_signing_boundary_summary", {})
        ).get("signed_payload_generation_enabled")
        is True,
        "wallet_signing_boundary_no_executable_action": dict(
            panel.get("wallet_signing_boundary_summary", {})
        ).get("no_executable_action")
        is True,
        "signed_order_payload_validation_gate_section_ready": dict(
            panel.get("signed_order_payload_validation_gate_summary", {})
        ).get("signed_order_payload_validation_gate_section_ready")
        is True,
        "signed_order_payload_validation_gate_status": dict(
            panel.get("signed_order_payload_validation_gate_summary", {})
        ).get("status"),
        "signed_order_payload_shape_status": dict(
            panel.get("signed_order_payload_validation_gate_summary", {})
        ).get("payload_shape_status"),
        "signed_order_payload_validation_gate_no_executable_action": dict(
            panel.get("signed_order_payload_validation_gate_summary", {})
        ).get("no_executable_action")
        is True,
        "signed_order_payload_validation_gate_review_only": dict(
            panel.get("signed_order_payload_validation_gate_summary", {})
        ).get("review_only")
        is True,
        "signed_order_payload_validation_gate_signing_enabled": False,
        "signed_order_payload_validation_gate_signed_payload_generation_enabled": False,
        "signed_order_payload_validation_gate_signed_order_generation_enabled": False,
        "signed_order_payload_validation_gate_order_submission_enabled": False,
        "tiny_live_canary_gonogo_gate_section_ready": dict(
            panel.get("tiny_live_canary_gonogo_gate_summary", {})
        ).get("tiny_live_canary_gonogo_gate_section_ready")
        is True,
        "tiny_live_canary_gonogo_gate_status": dict(
            panel.get("tiny_live_canary_gonogo_gate_summary", {})
        ).get("status"),
        "tiny_live_canary_gonogo_overall_decision": dict(
            panel.get("tiny_live_canary_gonogo_gate_summary", {})
        ).get("overall_decision"),
        "tiny_live_canary_gonogo_no_executable_action": dict(
            panel.get("tiny_live_canary_gonogo_gate_summary", {})
        ).get("no_executable_action")
        is True,
        "tiny_live_canary_gonogo_unresolved_blocker_count": dict(
            panel.get("tiny_live_canary_gonogo_gate_summary", {})
        ).get("unresolved_blocker_count"),
        "supervised_tiny_canary_approval_packet_section_ready": dict(
            panel.get("supervised_tiny_canary_approval_packet_summary", {})
        ).get("supervised_tiny_canary_approval_packet_section_ready")
        is True,
        "supervised_tiny_canary_approval_packet_status": dict(
            panel.get("supervised_tiny_canary_approval_packet_summary", {})
        ).get("status"),
        "supervised_tiny_canary_approval_packet_review_only": dict(
            panel.get("supervised_tiny_canary_approval_packet_summary", {})
        ).get("review_only")
        is True,
        "supervised_tiny_canary_approval_packet_cannot_approve_live": dict(
            panel.get("supervised_tiny_canary_approval_packet_summary", {})
        ).get("packet_cannot_be_interpreted_as_live_approval")
        is True,
        "supervised_tiny_canary_approval_packet_no_executable_action": dict(
            panel.get("supervised_tiny_canary_approval_packet_summary", {})
        ).get("no_executable_action")
        is True,
        "supervised_tiny_canary_approval_packet_live_execution_approved": False,
        "supervised_tiny_canary_approval_packet_canary_executable_now": False,
        "supervised_tiny_canary_approval_packet_order_submission_enabled": False,
        "supervised_tiny_canary_approval_packet_resolved_blocker_count": 0,
        "latest_risk_limit_decision_status": dict(panel.get("risk_control_plane_summary", {})).get(
            "latest_decision_status"
        ),
        "risk_limit_status": "review_config_visibility_only",
        "kill_switch_status": dict(panel.get("kill_switch_summary", {})).get("current_kill_switch_state"),
        "telegram_operator_control_configured": dict(
            panel.get("telegram_operator_control_bot_summary", {})
        ).get("configured")
        is True,
        "telegram_operator_control_allowed_operator_ids_configured": dict(
            panel.get("telegram_operator_control_bot_summary", {})
        ).get("allowed_operator_ids_configured")
        is True,
        "telegram_operator_control_pause_requested": dict(
            panel.get("telegram_operator_control_bot_summary", {})
        ).get("operator_pause_requested")
        is True,
        "telegram_operator_control_kill_switch_requested": dict(
            panel.get("telegram_operator_control_bot_summary", {})
        ).get("operator_kill_switch_requested")
        is True,
        "telegram_mini_app_operator_panel_section_ready": dict(
            panel.get("telegram_mini_app_operator_panel_summary", {})
        ).get("telegram_mini_app_operator_panel_section_ready")
        is True,
        "telegram_mini_app_operator_panel_artifact_available": dict(
            panel.get("telegram_mini_app_operator_panel_summary", {})
        ).get("panel_artifact_available")
        is True,
        "telegram_mini_app_operator_panel_review_only": dict(
            panel.get("telegram_mini_app_operator_panel_summary", {})
        ).get("review_only")
        is True,
        "telegram_mini_app_operator_panel_live_actions_available": dict(
            panel.get("telegram_mini_app_operator_panel_summary", {})
        ).get("live_actions_available")
        is True,
        "telegram_mini_app_operator_panel_live_actions_blocked": dict(
            panel.get("telegram_mini_app_operator_panel_summary", {})
        ).get("live_actions_available")
        is False,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def render_operator_ui_panel_v1_json(
    panel: Mapping[str, Any],
    *,
    include_validation: bool = True,
) -> str:
    value = dict(panel)
    if not include_validation:
        value.pop("validation", None)
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def render_operator_ui_panel_v1_markdown(panel: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Operator UI Panel v1",
        "",
        f"- Panel: `{panel.get('panel_id')}`",
        f"- Mode: `{dict(panel.get('readiness_summary', {})).get('mode')}`",
        f"- Live execution approved: `{str(panel.get('live_execution_approved')).lower()}`",
        f"- Canary executable now: `{str(panel.get('canary_executable_now')).lower()}`",
        f"- Real execution available: `{str(panel.get('real_execution_available')).lower()}`",
        f"- Live connector enabled: `{str(panel.get('live_connector_enabled')).lower()}`",
        f"- Warning: {LIVE_DISABLED_WARNING}",
        "",
    ]
    for section in mapping_rows(panel.get("sections")):
        lines.extend([f"## {section.get('title')}", "", f"- Status: `{section.get('status')}`"])
        for metric in mapping_rows(section.get("metrics")):
            lines.append(
                f"- {metric.get('label')}: `{_markdown_value(metric.get('value'))}`"
                + (f" ({metric.get('notes')})" if clean_text(metric.get("notes")) else "")
            )
        warnings = mapping_rows(section.get("warnings"))
        if warnings:
            lines.append("- Warnings:")
            lines.extend(bullet_lines(row.get("message") for row in warnings))
        actions = mapping_rows(section.get("action_states"))
        if actions:
            lines.append("- Action states:")
            lines.extend(
                bullet_lines(
                    f"{row.get('label')}: `{row.get('state')}`, execution_enabled=`{str(row.get('execution_enabled')).lower()}`"
                    for row in actions
                )
            )
        lines.append("")
    lines.extend(["## Next Required Gates", ""])
    lines.extend(bullet_lines(panel.get("next_required_gates", [])))
    return "\n".join(lines).rstrip() + "\n"


def render_operator_ui_panel_v1_html(panel: Mapping[str, Any]) -> str:
    title = "PMBOT Operator UI Panel v1"
    section_html = []
    for section in mapping_rows(panel.get("sections")):
        rows = []
        for metric in mapping_rows(section.get("metrics")):
            rows.append(
                "<tr>"
                f"<th>{html.escape(clean_text(metric.get('label')))}</th>"
                f"<td>{html.escape(_display_value(metric.get('value')))}</td>"
                f"<td>{html.escape(clean_text(metric.get('status')))}</td>"
                "</tr>"
            )
        warnings = "".join(
            f"<li>{html.escape(clean_text(row.get('message')))}</li>"
            for row in mapping_rows(section.get("warnings"))
        )
        actions = "".join(
            "<li>"
            f"{html.escape(clean_text(row.get('label')))}: "
            f"{html.escape(clean_text(row.get('state')))} "
            f"(execution_enabled={str(row.get('execution_enabled')).lower()})"
            "</li>"
            for row in mapping_rows(section.get("action_states"))
        )
        section_html.append(
            "<section>"
            f"<h2>{html.escape(clean_text(section.get('title')))}</h2>"
            f"<p class=\"status\">Status: {html.escape(clean_text(section.get('status')))}</p>"
            "<table><tbody>"
            + "".join(rows)
            + "</tbody></table>"
            + (f"<h3>Warnings</h3><ul>{warnings}</ul>" if warnings else "")
            + (f"<h3>Action States</h3><ul>{actions}</ul>" if actions else "")
            + "</section>"
        )
    gates = "".join(f"<li>{html.escape(clean_text(item))}</li>" for item in panel.get("next_required_gates", []))
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"  <title>{html.escape(title)}</title>\n"
        "  <style>\n"
        "    :root { color-scheme: light; font-family: Arial, sans-serif; }\n"
        "    body { margin: 0; background: #f7f8fa; color: #1f2933; }\n"
        "    header { background: #12343b; color: #fff; padding: 24px 32px; }\n"
        "    main { max-width: 1120px; margin: 0 auto; padding: 24px 20px 40px; }\n"
        "    section { background: #fff; border: 1px solid #d9e2ec; border-radius: 6px; margin: 0 0 16px; padding: 18px; }\n"
        "    h1, h2, h3 { margin: 0 0 10px; }\n"
        "    p { margin: 6px 0; }\n"
        "    .warning { color: #8a3412; font-weight: 700; }\n"
        "    .status { color: #334e68; }\n"
        "    table { width: 100%; border-collapse: collapse; table-layout: fixed; }\n"
        "    th, td { border-top: 1px solid #eef2f6; padding: 8px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }\n"
        "    th { width: 34%; color: #334e68; font-weight: 700; }\n"
        "    ul { margin: 8px 0 0 20px; padding: 0; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <header>\n"
        f"    <h1>{html.escape(title)}</h1>\n"
        f"    <p>Mode: {html.escape(clean_text(dict(panel.get('readiness_summary', {})).get('mode')))}</p>\n"
        f"    <p class=\"warning\">{html.escape(LIVE_DISABLED_WARNING)}</p>\n"
        "  </header>\n"
        "  <main>\n"
        + "\n".join(section_html)
        + f"\n<section><h2>Next Required Gates</h2><ul>{gates}</ul></section>\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def _build_readiness_summary(*, operator_review_ready: bool, evidence_bundle_review_ready: bool) -> dict[str, Any]:
    return OperatorUIPanelReadinessSummary(
        mode=PANEL_MODE,
        current_execution_posture="paper_active_dry_run_review_live_disabled",
        paper_trading_status="paper_local_only",
        operator_review_ready=operator_review_ready,
        evidence_bundle_review_ready=evidence_bundle_review_ready,
        live_execution_approved=False,
        canary_executable_now=False,
        real_execution_available=False,
        live_connector_enabled=False,
    ).to_dict()


def _build_evidence_summary(
    *,
    readiness_evidence_bundle: Mapping[str, Any] | None,
    readiness_evidence_bundle_summary: Mapping[str, Any] | None,
    latest_path: str,
) -> dict[str, Any]:
    bundle = dict(readiness_evidence_bundle or {})
    summary = dict(readiness_evidence_bundle_summary or {})
    return OperatorUIPanelEvidenceSummary(
        readiness_evidence_bundle_status=clean_text(
            summary.get("readiness_evidence_bundle_status")
            or summary.get("status")
            or bundle.get("bundle_status")
            or NOT_AVAILABLE
        ),
        evidence_item_count=_int_or_zero(summary.get("evidence_item_count"), bundle.get("evidence_item_count")),
        missing_required_evidence_count=_int_or_zero(
            summary.get("missing_required_evidence_count"),
            bundle.get("missing_required_evidence_count"),
        ),
        latest_readiness_evidence_bundle_path=clean_text(
            summary.get("latest_readiness_evidence_bundle_path") or latest_path
        ),
        readiness_bundle_is_not_live_approval=True,
        evidence_bundle_review_ready=(
            summary.get("readiness_evidence_bundle_review_ready") is True
            or summary.get("evidence_bundle_review_ready") is True
            or bundle.get("evidence_bundle_review_ready") is True
        ),
        validation_status=clean_text(summary.get("validation_status") or dict(bundle.get("validation", {})).get("status")),
    ).to_dict()


def _build_blocker_summary(
    *,
    blocker_matrix: Mapping[str, Any] | None,
    canary_readiness_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    matrix = dict(blocker_matrix or {})
    canary = dict(canary_readiness_summary or {})
    blockers = [dict(row) for row in mapping_rows(matrix.get("blockers"))]
    unresolved_rows = [row for row in blockers if clean_text(row.get("resolution_status")) != "resolved"]
    resolved_rows = [row for row in blockers if clean_text(row.get("resolution_status")) == "resolved"]
    top_blockers = tuple(
        {
            "blocker_id": clean_text(row.get("blocker_id")),
            "reason": clean_text(row.get("why_it_blocks_live_execution") or row.get("blocker_name") or row.get("message")),
            "severity": clean_text(row.get("severity") or "critical"),
            "resolution_status": clean_text(row.get("resolution_status") or "unresolved"),
        }
        for row in blockers[:8]
    )
    unresolved_count = _int_or_zero(matrix.get("unresolved_blocker_count"), canary.get("unresolved_live_connector_blocker_count"))
    total_count = _int_or_zero(matrix.get("blocker_count"), canary.get("live_connector_blocker_count"), len(blockers))
    critical_count = _int_or_zero(matrix.get("critical_blocker_count"), canary.get("critical_blocker_count"))
    resolved_count = _int_or_zero(matrix.get("resolved_blocker_count"), len(resolved_rows))
    if blockers and unresolved_count == 0:
        unresolved_count = len(unresolved_rows)
    reasons = tuple(
        _dedupe(
            [
                clean_text(row.get("why_it_blocks_live_execution") or row.get("blocker_name") or row.get("message"))
                for row in blockers[:8]
            ]
            or list(canary.get("blocked_reason_summary", []))
        )
    )
    return OperatorUIPanelBlockerSummary(
        blocker_matrix_status=clean_text(matrix.get("status") or canary.get("acceptance_matrix_status") or NOT_AVAILABLE),
        total_blockers=total_count,
        critical_blockers=critical_count,
        unresolved_blockers=unresolved_count,
        resolved_blockers=resolved_count,
        top_blockers=top_blockers,
        all_blockers_unresolved=(matrix.get("all_blockers_unresolved") is True or (unresolved_count > 0 and resolved_count == 0)),
        why_live_execution_is_blocked=reasons
        or (
            "Live connector remains disabled.",
            "Kill-switch verification for live is missing.",
            "Operator live approval is not implemented.",
        ),
    ).to_dict()


def _build_risk_limit_summary(
    *,
    risk_limits: Mapping[str, Any] | None,
    risk_prep_config: Mapping[str, Any] | None,
    risk_limit_policy: Mapping[str, Any] | None,
    risk_control_plane_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    limits = dict(risk_limits or {})
    config = dict(risk_prep_config or {})
    policy = dict(risk_limit_policy or {})
    risk_control = dict(risk_control_plane_summary or {})
    return OperatorUIPanelRiskLimitSummary(
        max_daily_loss_usd=_first_available(
            policy.get("max_daily_loss_usd"),
            risk_control.get("max_daily_loss_usd"),
            REVIEW_PLACEHOLDER,
        ),
        max_total_exposure_usd=_first_available(
            policy.get("max_total_exposure_usd"),
            risk_control.get("max_total_exposure_usd"),
            config.get("max_total_exposure_usd"),
            limits.get("max_total_paper_exposure_usd"),
            REVIEW_PLACEHOLDER,
        ),
        max_market_exposure_usd=_first_available(
            policy.get("max_market_exposure_usd"),
            risk_control.get("max_market_exposure_usd"),
            config.get("max_market_exposure_usd"),
            config.get("max_per_market_exposure_usd"),
            limits.get("max_market_paper_exposure_usd"),
            REVIEW_PLACEHOLDER,
        ),
        max_order_notional_usd=_first_available(
            policy.get("max_order_notional_usd"),
            risk_control.get("max_order_notional_usd"),
            config.get("max_single_action_notional_usd"),
            limits.get("max_single_intent_notional_usd"),
            REVIEW_PLACEHOLDER,
        ),
        max_market_count=_first_available(
            policy.get("max_active_markets"),
            risk_control.get("max_active_markets"),
            len(config.get("market_allowlist", []))
            if isinstance(config.get("market_allowlist"), list) and config.get("market_allowlist")
            else None,
            REVIEW_PLACEHOLDER,
        ),
        max_order_count=_first_available(
            policy.get("max_orders_per_day"),
            risk_control.get("max_orders_per_day"),
            config.get("per_run_action_cap"),
            REVIEW_PLACEHOLDER,
        ),
        max_trades_per_day=_first_available(
            policy.get("max_trades_per_day"),
            risk_control.get("max_trades_per_day"),
            config.get("per_run_action_cap"),
            REVIEW_PLACEHOLDER,
        ),
        cooldown_after_loss=_first_available(
            policy.get("cooldown_after_loss_minutes"),
            REVIEW_PLACEHOLDER,
        ),
        halt_on_stale_data=policy.get("halt_on_stale_market_data") is True
        or config.get("require_fresh_evidence") is not False,
        halt_on_audit_mismatch=True,
        halt_on_kill_switch=policy.get("halt_on_kill_switch") is True
        or config.get("kill_switch_enabled") is not False,
        halt_on_missing_operator_intent=policy.get("halt_on_missing_operator_intent") is not False,
    ).to_dict()


def _build_btc_market_summary(
    *,
    btc_market_snapshot: Mapping[str, Any] | None,
    btc_read_only_connector_summary: Mapping[str, Any] | None,
    latest_btc_market_snapshot_path: str,
) -> dict[str, Any]:
    snapshot = dict(btc_market_snapshot or {})
    summary = dict(btc_read_only_connector_summary or {})
    if snapshot:
        snapshot_summary = summarize_btc_market_snapshot(snapshot)
        merged = dict(snapshot_summary)
        merged.update({key: value for key, value in summary.items() if value not in ("", None, [])})
        summary = merged
    return OperatorUIPanelBTCMarketSummary(
        btc_market_connector_status=clean_text(summary.get("btc_market_connector_status") or NOT_AVAILABLE),
        market_id=clean_text(summary.get("market_id")),
        market_slug=clean_text(summary.get("market_slug")),
        market_title=clean_text(summary.get("market_title")),
        is_btc_related=summary.get("is_btc_related") is True,
        market_status=clean_text(summary.get("market_status") or NOT_AVAILABLE),
        is_open=summary.get("is_open") is True,
        is_resolved=summary.get("is_resolved") is True,
        stale=summary.get("stale") is True,
        snapshot_age_seconds=summary.get("snapshot_age_seconds"),
        best_bid=summary.get("best_bid"),
        best_ask=summary.get("best_ask"),
        last_price=summary.get("last_price"),
        spread=summary.get("spread"),
        liquidity=summary.get("liquidity"),
        price_status=clean_text(summary.get("price_status") or NOT_AVAILABLE),
        risk_control_market_data_status=clean_text(
            summary.get("risk_control_market_data_status") or NOT_AVAILABLE
        ),
        read_only_network_enabled=summary.get("read_only_network_enabled") is True,
        latest_btc_market_snapshot_path=clean_text(
            summary.get("latest_btc_market_snapshot_path") or latest_btc_market_snapshot_path
        ),
    ).to_dict()


def _build_btc_analysis_order_intent_summary(
    *,
    btc_analysis_order_intent_summary: Mapping[str, Any] | None,
    latest_btc_analysis_path: str,
    latest_btc_order_intent_path: str,
    latest_btc_risk_decision_path: str,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(btc_analysis_order_intent_summary or {})
    if not provided:
        provided = summarize_btc_analysis_order_intent(
            latest_btc_analysis_path=latest_btc_analysis_path,
            latest_btc_order_intent_path=latest_btc_order_intent_path,
            latest_btc_risk_decision_path=latest_btc_risk_decision_path,
            generated_at=generated_at,
        )
    return OperatorUIPanelBTCAnalysisOrderIntentSummary(
        btc_market_analysis_status=clean_text(provided.get("btc_market_analysis_status") or NOT_AVAILABLE),
        btc_intent_candidate_status=clean_text(provided.get("btc_intent_candidate_status") or NOT_AVAILABLE),
        dry_run_order_intent_status=clean_text(provided.get("dry_run_order_intent_status") or NOT_AVAILABLE),
        intent_market_id=clean_text(provided.get("intent_market_id")),
        intent_market_slug=clean_text(provided.get("intent_market_slug")),
        intent_notional_usd=provided.get("intent_notional_usd"),
        intent_limit_price=provided.get("intent_limit_price"),
        risk_decision_status=clean_text(provided.get("risk_decision_status") or NOT_AVAILABLE),
        allowed_for_dry_run=provided.get("allowed_for_dry_run") is True,
        allowed_for_live=False,
        analysis_is_not_live_recommendation=True,
        order_intent_is_not_order_submission=True,
        latest_btc_analysis_path=clean_text(provided.get("latest_btc_analysis_path") or latest_btc_analysis_path),
        latest_btc_order_intent_path=clean_text(
            provided.get("latest_btc_order_intent_path") or latest_btc_order_intent_path
        ),
        latest_btc_risk_decision_path=clean_text(
            provided.get("latest_btc_risk_decision_path") or latest_btc_risk_decision_path
        ),
    ).to_dict()


def _build_live_credentials_auth_boundary_summary(
    *,
    live_credentials_auth_boundary_summary: Mapping[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(live_credentials_auth_boundary_summary or {})
    if not provided or not clean_text(
        provided.get("live_credentials_boundary_status") or provided.get("decision_status")
    ):
        provided = summarize_live_credentials_status(generated_at=generated_at)
    statuses = [
        dict(row)
        for row in mapping_rows(provided.get("credential_statuses_redacted"))
    ]
    result = OperatorUIPanelLiveCredentialsAuthSummary(
        live_credentials_boundary_status=clean_text(
            provided.get("live_credentials_boundary_status") or provided.get("decision_status") or NOT_AVAILABLE
        ),
        live_credentials_configured=provided.get("live_credentials_configured") is True,
        required_credentials_count=_int_or_zero(provided.get("required_credentials_count"), len(statuses)),
        missing_credentials_count=_int_or_zero(provided.get("missing_credentials_count"), 0),
        credential_statuses_redacted=tuple(statuses),
        live_auth_ready_for_future_tiny_canary_review=(
            provided.get("live_auth_ready_for_future_tiny_canary_review") is True
        ),
        warning=clean_text(provided.get("warning")) or UI_REDACTION_WARNING,
        authenticated_endpoints_enabled=False,
        signing_enabled=False,
        cryptographic_signing_enabled=False,
        wallet_signing_enabled=False,
        order_submission_enabled=False,
        allowed_for_live=False,
        canary_executable_now=False,
        live_execution_approved=False,
        real_execution_available=False,
        live_connector_enabled=False,
    ).to_dict()
    validation = validate_secret_boundary_live_credentials_auth_summary(result, generated_at=generated_at)
    result["live_credentials_auth_summary_secret_boundary_validation"] = validation
    if validation.get("valid") is not True:
        result["live_credentials_boundary_status"] = "SECRET_POLICY_VIOLATION"
        result["live_auth_ready_for_future_tiny_canary_review"] = False
    return result


def _build_live_order_submission_boundary_summary(
    *,
    live_order_submission_boundary_receipt: Mapping[str, Any] | None,
    live_order_submission_boundary_summary: Mapping[str, Any] | None,
    latest_live_order_submission_boundary_path: str,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(live_order_submission_boundary_summary or {})
    if not provided and live_order_submission_boundary_receipt:
        provided = summarize_live_order_submission_boundary_receipt(
            live_order_submission_boundary_receipt,
            latest_live_order_submission_boundary_path=latest_live_order_submission_boundary_path,
            generated_at=generated_at,
        )
    return OperatorUIPanelLiveOrderSubmissionBoundarySummary(
        boundary_name=clean_text(provided.get("boundary_name") or LIVE_ORDER_SUBMISSION_BOUNDARY_NAME),
        status=clean_text(provided.get("status") or NOT_AVAILABLE),
        dry_run_review_ready=provided.get("dry_run_review_ready") is True
        or provided.get("allowed_for_dry_run_review") is True,
        market_id=clean_text(provided.get("market_id")),
        market_slug=clean_text(provided.get("market_slug")),
        asset=clean_text(provided.get("asset") or "BTC"),
        side=clean_text(provided.get("side")),
        outcome=clean_text(provided.get("outcome")),
        top_refusal_reasons=tuple(clean_text(item) for item in provided.get("top_refusal_reasons", []) if clean_text(item)),
        top_blocker_reasons=tuple(clean_text(item) for item in provided.get("top_blocker_reasons", []) if clean_text(item)),
        latest_live_order_submission_boundary_path=clean_text(
            provided.get("latest_live_order_submission_boundary_path")
            or latest_live_order_submission_boundary_path
        ),
        would_submit_order=False,
        order_submission_enabled=False,
        authenticated_endpoint_required=provided.get("authenticated_endpoint_required") is True,
        authenticated_endpoint_enabled=False,
        authenticated_endpoints_enabled=False,
        signing_required_for_future_live=provided.get("signing_required_for_future_live") is True,
        signing_enabled=False,
        wallet_required_for_future_live=provided.get("wallet_required_for_future_live") is True,
        wallet_enabled=False,
        allowed_for_live=False,
        canary_executable_now=False,
        live_execution_approved=False,
        real_execution_available=False,
        live_connector_enabled=False,
    ).to_dict()


def _build_live_enablement_config_preflight_summary(
    *,
    live_enablement_config_preflight: Mapping[str, Any] | None,
    live_enablement_config_preflight_summary: Mapping[str, Any] | None,
    latest_live_enablement_config_preflight_path: str,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(live_enablement_config_preflight_summary or {})
    if not provided:
        provided = summarize_live_enablement_config_preflight(
            live_enablement_config_preflight,
            latest_live_enablement_config_preflight_path=latest_live_enablement_config_preflight_path,
            generated_at=generated_at,
        )
    return OperatorUIPanelLiveEnablementConfigPreflightSummary(
        status=clean_text(provided.get("status") or NOT_AVAILABLE),
        future_live_requested=provided.get("future_live_requested") is True,
        dry_run_review_allowed=provided.get("dry_run_review_allowed") is True
        or provided.get("allowed_for_dry_run_review") is True,
        allowed_for_live=False,
        top_blocked_reasons=tuple(
            clean_text(item)
            for item in (
                list(provided.get("top_blocked_reasons", []))
                or list(provided.get("blocked_reasons", []))
            )[:5]
            if clean_text(item)
        ),
        latest_live_enablement_config_preflight_path=clean_text(
            provided.get("latest_live_enablement_config_preflight_path")
            or latest_live_enablement_config_preflight_path
        ),
    ).to_dict()


def _build_authenticated_polymarket_connector_scaffold_summary(
    *,
    authenticated_polymarket_connector_scaffold: Mapping[str, Any] | None,
    authenticated_polymarket_connector_scaffold_summary: Mapping[str, Any] | None,
    latest_authenticated_polymarket_connector_scaffold_path: str,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(authenticated_polymarket_connector_scaffold_summary or {})
    if not provided:
        provided = summarize_authenticated_connector_capability_report(
            authenticated_polymarket_connector_scaffold,
            latest_authenticated_polymarket_connector_scaffold_path=(
                latest_authenticated_polymarket_connector_scaffold_path
            ),
            generated_at=generated_at,
        )
    return OperatorUIPanelAuthenticatedPolymarketConnectorScaffoldSummary(
        status=clean_text(provided.get("status") or NOT_AVAILABLE),
        connector_name=clean_text(
            provided.get("connector_name") or "authenticated_polymarket_connector_scaffold_dry_run_only"
        ),
        credentials_redacted_or_missing_only=(
            provided.get("credentials_redacted_or_missing_only") is not False
        ),
        configured_redacted_credential_count=int(
            provided.get("configured_redacted_credential_count", 0) or 0
        ),
        missing_credential_count=int(provided.get("missing_credential_count", 0) or 0),
        top_blocked_reasons=tuple(
            clean_text(item)
            for item in list(provided.get("top_blocked_reasons", []))[:5]
            if clean_text(item)
        ),
        latest_authenticated_polymarket_connector_scaffold_path=clean_text(
            provided.get("latest_authenticated_polymarket_connector_scaffold_path")
            or latest_authenticated_polymarket_connector_scaffold_path
        ),
    ).to_dict()


def _build_wallet_signing_boundary_summary(
    *,
    wallet_signing_boundary_report: Mapping[str, Any] | None,
    wallet_signing_boundary_summary: Mapping[str, Any] | None,
    latest_wallet_signing_boundary_path: str,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(wallet_signing_boundary_summary or {})
    if not provided:
        report = dict(wallet_signing_boundary_report or build_wallet_signing_boundary_report(generated_at=generated_at))
        provided = summarize_wallet_signing_boundary_report(
            report,
            latest_wallet_signing_boundary_path=latest_wallet_signing_boundary_path,
            generated_at=generated_at,
        )
    return OperatorUIPanelWalletSigningBoundarySummary(
        status=clean_text(provided.get("status") or "SIGNING_DISABLED_REVIEW_ONLY"),
        wallet_address_status=clean_text(provided.get("wallet_address_status") or "missing"),
        signing_provider_status=clean_text(provided.get("signing_provider_status") or "missing"),
        top_blocked_reasons=tuple(
            clean_text(item)
            for item in (
                list(provided.get("top_blocked_reasons", []))
                or list(provided.get("blocked_reasons", []))
            )[:5]
            if clean_text(item)
        ),
        latest_wallet_signing_boundary_path=clean_text(
            provided.get("latest_wallet_signing_boundary_path") or latest_wallet_signing_boundary_path
        ),
    ).to_dict()


def _build_signed_order_payload_validation_gate_summary(
    *,
    signed_order_payload_validation_gate: Mapping[str, Any] | None,
    signed_order_payload_validation_gate_summary: Mapping[str, Any] | None,
    latest_signed_order_payload_validation_gate_path: str,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(signed_order_payload_validation_gate_summary or {})
    if not provided:
        provided = summarize_signed_order_payload_validation_gate(
            signed_order_payload_validation_gate,
            latest_signed_order_payload_validation_gate_path=latest_signed_order_payload_validation_gate_path,
            generated_at=generated_at,
        )
    return OperatorUIPanelSignedOrderPayloadValidationGateSummary(
        status=clean_text(provided.get("status") or "SIGNING_DISABLED_REVIEW_ONLY"),
        payload_shape_status=clean_text(
            provided.get("payload_shape_status")
            or provided.get("status")
            or "SIGNING_DISABLED_REVIEW_ONLY"
        ),
        top_blocked_reasons=tuple(
            clean_text(item)
            for item in (
                list(provided.get("top_blocked_reasons", []))
                or list(provided.get("blocked_reasons", []))
            )[:5]
            if clean_text(item)
        ),
        latest_signed_order_payload_validation_gate_path=clean_text(
            provided.get("latest_signed_order_payload_validation_gate_path")
            or latest_signed_order_payload_validation_gate_path
        ),
    ).to_dict()


def _build_tiny_live_canary_gonogo_gate_summary(
    *,
    tiny_live_canary_gonogo_gate: Mapping[str, Any] | None,
    tiny_live_canary_gonogo_gate_summary: Mapping[str, Any] | None,
    latest_tiny_live_canary_gonogo_gate_path: str,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(tiny_live_canary_gonogo_gate_summary or {})
    if not provided and tiny_live_canary_gonogo_gate:
        provided = summarize_tiny_live_canary_gonogo_gate(
            tiny_live_canary_gonogo_gate,
            latest_tiny_live_canary_gonogo_gate_path=latest_tiny_live_canary_gonogo_gate_path,
            generated_at=generated_at,
        )
    summary = {
        "contract_version": OPERATOR_UI_PANEL_TINY_CANARY_GONOGO_SUMMARY_CONTRACT,
        "gate_name": clean_text(
            provided.get("gate_name") or "tiny_live_canary_manual_execution_checklist_and_final_gonogo_gate"
        ),
        "status": clean_text(provided.get("status") or NOT_AVAILABLE),
        "review_only_status": clean_text(
            provided.get("review_only_status") or provided.get("status") or NOT_AVAILABLE
        ),
        "overall_decision": clean_text(provided.get("overall_decision") or "NO_GO"),
        "decision_level": clean_text(provided.get("decision_level") or "FINAL_MANUAL_REVIEW_ONLY"),
        "market_id": clean_text(provided.get("market_id")),
        "market_slug": clean_text(provided.get("market_slug")),
        "manual_execution_checklist_count": int(provided.get("manual_execution_checklist_count", 0) or 0),
        "manual_execution_checklist_pending_count": int(
            provided.get("manual_execution_checklist_pending_count", 0) or 0
        ),
        "final_pre_live_checklist_count": int(provided.get("final_pre_live_checklist_count", 0) or 0),
        "no_go_reason_count": int(provided.get("no_go_reason_count", 0) or 0),
        "top_no_go_reasons": list(provided.get("top_no_go_reasons", []))[:5],
        "unresolved_blocker_count": int(provided.get("unresolved_blocker_count", 0) or 0),
        "resolved_blocker_count": int(provided.get("resolved_blocker_count", 0) or 0),
        "explicit_human_approval_required": True,
        "no_executable_action": True,
        "packet_complete_for_operator_review": provided.get("packet_complete_for_operator_review") is True,
        "latest_tiny_live_canary_gonogo_gate_path": clean_text(
            latest_tiny_live_canary_gonogo_gate_path
            or provided.get("latest_tiny_live_canary_gonogo_gate_path")
        ),
        "tiny_live_canary_gonogo_gate_section_ready": True,
        "final_live_enablement_present": False,
        "live_execution_approved": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "order_submission_enabled": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "execution_enabling": False,
        "review_only": True,
    }
    summary.update({field: False for field in FORCED_FALSE_EXECUTION_FIELDS})
    return summary


def _build_supervised_tiny_canary_approval_packet_summary(
    *,
    supervised_tiny_canary_approval_packet: Mapping[str, Any] | None,
    supervised_tiny_canary_approval_packet_summary: Mapping[str, Any] | None,
    latest_supervised_tiny_canary_approval_packet_json_path: str,
    latest_supervised_tiny_canary_approval_packet_md_path: str,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(supervised_tiny_canary_approval_packet_summary or {})
    packet = dict(supervised_tiny_canary_approval_packet or {})
    if not provided and packet:
        provided = summarize_supervised_tiny_canary_approval_packet(
            packet,
            latest_supervised_tiny_canary_approval_packet_json_path=(
                latest_supervised_tiny_canary_approval_packet_json_path
            ),
            latest_supervised_tiny_canary_approval_packet_md_path=(
                latest_supervised_tiny_canary_approval_packet_md_path
            ),
            generated_at=generated_at,
        )
    return OperatorUIPanelSupervisedTinyCanaryApprovalPacketSummary(
        status=clean_text(
            provided.get("status")
            or packet.get("status")
            or "REVIEW_READY_BLOCKED_FOR_LIVE"
        ),
        approval_packet_ready_for_human_review=(
            provided.get("approval_packet_ready_for_human_review") is True
            or packet.get("approval_packet_ready_for_human_review") is True
        ),
        packet_cannot_be_interpreted_as_live_approval=True,
        operator_must_not_execute_from_this_packet=True,
        future_live_enabling_task_required=True,
        section_count=_int_or_zero(provided.get("section_count"), packet.get("section_count"), 0),
        operator_checklist_count=_int_or_zero(
            provided.get("operator_checklist_count"),
            len(mapping_rows(packet.get("operator_checklist"))),
            0,
        ),
        future_required_action_count=_int_or_zero(
            provided.get("future_required_action_count"),
            len(mapping_rows(packet.get("future_required_actions"))),
            0,
        ),
        unresolved_blocker_count=_int_or_zero(
            provided.get("unresolved_blocker_count"),
            packet.get("unresolved_blocker_count"),
            0,
        ),
        latest_supervised_tiny_canary_approval_packet_json_path=clean_text(
            latest_supervised_tiny_canary_approval_packet_json_path
            or provided.get("latest_supervised_tiny_canary_approval_packet_json_path")
        ),
        latest_supervised_tiny_canary_approval_packet_md_path=clean_text(
            latest_supervised_tiny_canary_approval_packet_md_path
            or provided.get("latest_supervised_tiny_canary_approval_packet_md_path")
        ),
    ).to_dict()


def _build_risk_control_plane_summary(
    *,
    risk_control_plane_summary: Mapping[str, Any] | None,
    risk_limit_policy: Mapping[str, Any] | None,
    latest_risk_limit_decision: Mapping[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    provided = dict(risk_control_plane_summary or {})
    if provided:
        return OperatorUIPanelRiskControlSummary(
            risk_control_plane_status=clean_text(
                provided.get("risk_control_plane_status") or "ready_no_intent_evaluated"
            ),
            policy_id=clean_text(provided.get("policy_id")),
            mode=clean_text(provided.get("mode")),
            max_daily_loss_usd=provided.get("max_daily_loss_usd", REVIEW_PLACEHOLDER),
            max_total_exposure_usd=provided.get("max_total_exposure_usd", REVIEW_PLACEHOLDER),
            max_market_exposure_usd=provided.get("max_market_exposure_usd", REVIEW_PLACEHOLDER),
            max_order_notional_usd=provided.get("max_order_notional_usd", REVIEW_PLACEHOLDER),
            max_orders_per_day=provided.get("max_orders_per_day", REVIEW_PLACEHOLDER),
            max_trades_per_day=provided.get("max_trades_per_day", REVIEW_PLACEHOLDER),
            max_active_markets=provided.get("max_active_markets", REVIEW_PLACEHOLDER),
            allowed_market_tags=tuple(clean_text(item) for item in provided.get("allowed_market_tags", []) if clean_text(item)),
            latest_decision_status=clean_text(provided.get("latest_decision_status") or "not_evaluated"),
            latest_violations_count=_int_or_zero(provided.get("latest_violations_count"), 0),
            latest_halt_reasons_count=_int_or_zero(provided.get("latest_halt_reasons_count"), 0),
            allowed_for_dry_run=provided.get("allowed_for_dry_run") is True,
            market_data_status=clean_text(provided.get("market_data_status") or "not_evaluated"),
            market_data_market_id=clean_text(provided.get("market_data_market_id")),
            market_data_market_slug=clean_text(provided.get("market_data_market_slug")),
            market_data_market_status=clean_text(provided.get("market_data_market_status") or "unknown"),
            market_data_is_btc_related=_bool_or_none(provided.get("market_data_is_btc_related")),
            market_data_stale=provided.get("market_data_stale") is True,
            market_data_age_seconds=provided.get("market_data_age_seconds"),
            market_data_freshness_feed_ready=provided.get("market_data_freshness_feed_ready") is True,
            allowed_for_live=False,
        ).to_dict()
    policy = dict(risk_limit_policy or build_default_risk_limit_policy(generated_at=generated_at))
    summary = build_risk_control_plane_summary(
        policy=policy,
        latest_decision=latest_risk_limit_decision,
        generated_at=generated_at,
    )
    decision_summary = summarize_risk_limit_decision(latest_risk_limit_decision)
    policy_summary = summarize_risk_limit_policy(policy)
    return OperatorUIPanelRiskControlSummary(
        risk_control_plane_status=clean_text(summary.get("risk_control_plane_status")),
        policy_id=clean_text(policy_summary.get("policy_id")),
        mode=clean_text(policy_summary.get("mode")),
        max_daily_loss_usd=policy_summary.get("max_daily_loss_usd"),
        max_total_exposure_usd=policy_summary.get("max_total_exposure_usd"),
        max_market_exposure_usd=policy_summary.get("max_market_exposure_usd"),
        max_order_notional_usd=policy_summary.get("max_order_notional_usd"),
        max_orders_per_day=policy_summary.get("max_orders_per_day"),
        max_trades_per_day=policy_summary.get("max_trades_per_day"),
        max_active_markets=policy_summary.get("max_active_markets"),
        allowed_market_tags=tuple(policy_summary.get("allowed_market_tags", [])),
        latest_decision_status=clean_text(decision_summary.get("latest_decision_status")),
        latest_violations_count=_int_or_zero(decision_summary.get("latest_violations_count"), 0),
        latest_halt_reasons_count=_int_or_zero(decision_summary.get("latest_halt_reasons_count"), 0),
        allowed_for_dry_run=decision_summary.get("allowed_for_dry_run") is True,
        market_data_status=clean_text(summary.get("market_data_status") or "not_evaluated"),
        market_data_market_id=clean_text(summary.get("market_data_market_id")),
        market_data_market_slug=clean_text(summary.get("market_data_market_slug")),
        market_data_market_status=clean_text(summary.get("market_data_market_status") or "unknown"),
        market_data_is_btc_related=_bool_or_none(summary.get("market_data_is_btc_related")),
        market_data_stale=summary.get("market_data_stale") is True,
        market_data_age_seconds=summary.get("market_data_age_seconds"),
        market_data_freshness_feed_ready=summary.get("market_data_freshness_feed_ready") is True,
        allowed_for_live=False,
    ).to_dict()


def _build_kill_switch_summary(
    *,
    preflight_result: Mapping[str, Any] | None,
    preflight_contract: Mapping[str, Any] | None,
    manual_runbook: Mapping[str, Any] | None,
    latest_reference: str,
) -> dict[str, Any]:
    result = dict(preflight_result or {})
    contract = dict(preflight_contract or {})
    kill_switch_requirement = dict(contract.get("kill_switch_requirement", {}))
    runbook = dict(manual_runbook or {})
    requirements_defined = (
        result.get("kill_switch_requirements_defined") is True
        or kill_switch_requirement.get("requirements_defined") is True
    )
    verified_for_live = False
    blocks_live = (
        kill_switch_requirement.get("blocks_live_execution") is True
        or result.get("kill_switch_verified_for_live") is False
        or requirements_defined
    )
    emergency_stop_documented = (
        runbook.get("manual_runbook_ready") is True
        or clean_text(runbook.get("status")).startswith("manual_runbook_ready")
        or bool(runbook)
    )
    state = "blocks_live" if blocks_live else "not_live_verified"
    if not requirements_defined:
        state = "dry_run_only"
    return OperatorUIPanelKillSwitchSummary(
        kill_switch_requirements_defined=requirements_defined,
        kill_switch_verified_for_live=verified_for_live,
        kill_switch_blocks_live_execution=blocks_live,
        emergency_stop_documented=emergency_stop_documented,
        current_kill_switch_state=state,
        latest_kill_switch_reference=latest_reference,
    ).to_dict()


def _build_telegram_operator_control_bot_summary(
    *,
    telegram_operator_control_bot_summary: Mapping[str, Any] | None,
    latest_reference: str,
) -> dict[str, Any]:
    provided = dict(telegram_operator_control_bot_summary or {})
    config = dict(provided.get("config", {}))
    state = dict(provided.get("state_summary", {}))
    return OperatorUIPanelTelegramOperatorControlSummary(
        configured=provided.get("configured") is True or config.get("telegram_bot_configured") is True,
        telegram_bot_token_status=clean_text(
            config.get("telegram_bot_token_status")
            or provided.get("telegram_bot_token_status")
            or "missing"
        ),
        allowed_operator_ids_configured=(
            provided.get("allowed_operator_ids_configured") is True
            or config.get("allowed_operator_ids_configured") is True
        ),
        allowed_operator_id_count=_int_or_zero(
            provided.get("allowed_operator_id_count"),
            config.get("allowed_operator_id_count"),
        ),
        operator_pause_requested=(
            provided.get("operator_pause_requested") is True
            or state.get("operator_pause_requested") is True
        ),
        operator_kill_switch_requested=(
            provided.get("operator_kill_switch_requested") is True
            or state.get("operator_kill_switch_requested") is True
        ),
        latest_telegram_operator_control_state_path=clean_text(
            provided.get("latest_telegram_operator_control_state_path")
            or state.get("latest_telegram_operator_control_state_path")
            or latest_reference
        ),
    ).to_dict()


def _build_telegram_mini_app_operator_panel_summary(
    *,
    telegram_mini_app_operator_panel_summary: Mapping[str, Any] | None,
    latest_html_reference: str,
    latest_json_reference: str,
) -> dict[str, Any]:
    provided = dict(telegram_mini_app_operator_panel_summary or {})
    html_reference = clean_text(
        provided.get("latest_telegram_mini_app_operator_panel_html_path")
        or latest_html_reference
    )
    json_reference = clean_text(
        provided.get("latest_telegram_mini_app_operator_panel_json_path")
        or latest_json_reference
    )
    artifact_available = (
        provided.get("panel_artifact_available") is True
        or provided.get("telegram_mini_app_operator_panel_ready") is True
        or bool(html_reference or json_reference)
    )
    return OperatorUIPanelTelegramMiniAppSummary(
        panel_artifact_available=artifact_available,
        review_only=True,
        live_actions_available=False,
        latest_telegram_mini_app_operator_panel_html_path=html_reference,
        latest_telegram_mini_app_operator_panel_json_path=json_reference,
        mini_app_url_status=clean_text(
            provided.get("mini_app_url_status") or "not_configured_review_placeholder"
        ),
        telegram_init_data_status=clean_text(
            provided.get("telegram_init_data_status") or "not_configured_redacted"
        ),
    ).to_dict()


def _build_paper_summary(
    *,
    dashboard: Mapping[str, Any],
    portfolio_summary: Mapping[str, Any] | None,
    portfolio_state: Mapping[str, Any] | None,
    strategy_summary: Mapping[str, Any] | None,
    latest_paper_run_reference: str,
) -> dict[str, Any]:
    counts = dict(dashboard.get("counts", {}))
    portfolio = dict(portfolio_summary or {})
    state = dict(portfolio_state or {})
    strategy = dict(strategy_summary or {})
    realized = _first_available(strategy.get("paper_realized_pnl_usd"), NOT_AVAILABLE)
    unrealized = _first_available(strategy.get("paper_unrealized_pnl_usd"), NOT_AVAILABLE)
    exposure = _first_available(
        portfolio.get("total_paper_exposure_usd"),
        state.get("total_paper_exposure_usd"),
        counts.get("total_paper_exposure_usd"),
        NOT_AVAILABLE,
    )
    positions = _first_available(
        portfolio.get("open_paper_position_count"),
        state.get("open_position_count"),
        counts.get("open_paper_position_count"),
        NOT_AVAILABLE,
    )
    return {
        "contract_version": "pmbot_operator_ui_panel_paper_summary.v1",
        "paper_status": "paper_local_only",
        "paper_pnl": {"realized_usd": realized, "unrealized_usd": unrealized},
        "paper_exposure": exposure,
        "paper_positions_count": positions,
        "latest_paper_run_reference": clean_text(latest_paper_run_reference),
        "paper_strategy_evaluation_status": clean_text(
            strategy.get("performance_readiness_status")
            or dashboard.get("paper_strategy_ledger_status", {}).get("record_count")
            or NOT_AVAILABLE
        ),
        "unresolved_pnl_not_invented": strategy.get("unresolved_pnl_not_invented") is not False,
        "pnl_invented": False,
        "outcome_resolution_invented": False,
        "paper_summary_panel_ready": True,
        **_panel_safety_flags(),
    }


def _build_operator_packet_summary(
    *,
    operator_live_approval_packet: Mapping[str, Any] | None,
    operator_intent_packet: Mapping[str, Any] | None,
    operator_intent_summary: Mapping[str, Any] | None,
    operator_review_summary: Mapping[str, Any] | None,
    latest_operator_packet_path: str,
    latest_operator_intent_packet_path: str,
) -> dict[str, Any]:
    approval = dict(operator_live_approval_packet or {})
    intent = dict(operator_intent_packet or {})
    intent_summary = dict(operator_intent_summary or {})
    review_summary = dict(operator_review_summary or {})
    return {
        "contract_version": "pmbot_operator_ui_panel_operator_packet_summary.v1",
        "operator_approval_packet_status": clean_text(
            approval.get("operator_packet_status")
            or review_summary.get("operator_packet_status")
            or NOT_AVAILABLE
        ),
        "operator_approval_packet_review_ready": (
            approval.get("operator_review_ready") is True or review_summary.get("operator_review_ready") is True
        ),
        "operator_approval_is_not_live_approval": True,
        "operator_intent_packet_status": clean_text(
            intent.get("intent_packet_status")
            or intent_summary.get("operator_intent_packet_status")
            or NOT_AVAILABLE
        ),
        "operator_intent_packet_review_ready": (
            intent.get("operator_intent_packet_review_ready") is True
            or intent_summary.get("operator_intent_packet_review_ready") is True
        ),
        "operator_intent_is_human_acknowledgement_only": (
            intent.get("operator_signed_intent_is_human_acknowledgement_only") is True
            or intent_summary.get("operator_signed_intent_is_human_acknowledgement_only") is True
            or intent_summary.get("operator_intent_packet_review_ready") is True
        ),
        "operator_intent_is_not_live_approval": True,
        "latest_operator_packet_path": clean_text(latest_operator_packet_path),
        "latest_operator_intent_packet_path": clean_text(latest_operator_intent_packet_path),
        **_panel_safety_flags(),
    }


def _build_audit_replay_summary(
    *,
    live_connector_audit_replay: Mapping[str, Any] | None,
    audit_operator_summary: Mapping[str, Any] | None,
    latest_audit_replay_path: str,
) -> dict[str, Any]:
    replay = dict(live_connector_audit_replay or {})
    summary = dict(audit_operator_summary or {})
    return {
        "contract_version": "pmbot_operator_ui_panel_audit_replay_summary.v1",
        "audit_replay_status": clean_text(replay.get("status") or summary.get("audit_replay_status") or NOT_AVAILABLE),
        "replay_passed_or_reviewable": clean_text(replay.get("status") or summary.get("audit_replay_status"))
        in {"replay_passed", "reviewable", "passed"},
        "mismatch_count": _int_or_zero(replay.get("mismatch_count"), replay.get("audit_mismatch_count"), 0),
        "replay_is_not_execution": True,
        "latest_audit_replay_path": clean_text(latest_audit_replay_path or summary.get("latest_audit_replay_path")),
        **_panel_safety_flags(),
    }


def _build_paper_canary_drill_summary(
    *,
    paper_canary_drill_status: Mapping[str, Any] | None,
    latest_status_path: str,
) -> dict[str, Any]:
    status = dict(paper_canary_drill_status or {})
    return {
        "contract_version": OPERATOR_UI_PANEL_PAPER_CANARY_DRILL_SUMMARY_CONTRACT,
        "paper_canary_drill_section_ready": True,
        "status": clean_text(status.get("status") or NOT_AVAILABLE),
        "market": clean_text(status.get("market") or NOT_AVAILABLE),
        "market_id": clean_text(status.get("market_id")),
        "market_slug": clean_text(status.get("market_slug")),
        "mode": clean_text(status.get("mode") or "paper / review-only"),
        "live_execution": clean_text(status.get("live_execution") or "blocked"),
        "overall_decision": clean_text(status.get("overall_decision") or "NO_GO"),
        "go_no_go_status": clean_text(status.get("go_no_go_status") or "NO_GO_UNRESOLVED_BLOCKERS"),
        "paper_order_intent_status": clean_text(
            status.get("paper_order_intent_status") or "not_available"
        ),
        "artifact": clean_text(status.get("artifact")),
        "latest_status_path": clean_text(status.get("latest_status_path") or latest_status_path),
        **_panel_safety_flags(),
    }


def _build_paper_trading_loop_summary(
    *,
    paper_trading_loop_status: Mapping[str, Any] | None,
    latest_status_path: str,
) -> dict[str, Any]:
    status = dict(paper_trading_loop_status or {})
    return {
        "contract_version": OPERATOR_UI_PANEL_PAPER_TRADING_LOOP_SUMMARY_CONTRACT,
        "paper_trading_loop_section_ready": True,
        "status": clean_text(status.get("status") or NOT_AVAILABLE),
        "market": clean_text(status.get("market") or status.get("market_symbol") or NOT_AVAILABLE),
        "strategy_name": clean_text(status.get("strategy_name") or NOT_AVAILABLE),
        "mode": clean_text(status.get("mode") or "paper / review-only"),
        "live_execution": clean_text(status.get("live_execution") or "blocked"),
        "live_execution_blocked": True,
        "signal_status": clean_text(status.get("signal_status") or NOT_AVAILABLE),
        "risk_decision": clean_text(status.get("risk_decision") or NOT_AVAILABLE),
        "paper_intent_status": clean_text(status.get("paper_intent_status") or "no_paper_intent"),
        "paper_intent_summary": clean_text(status.get("paper_intent_summary")),
        "artifact": clean_text(status.get("artifact_path") or status.get("artifact")),
        "latest_status_path": clean_text(status.get("latest_status_path") or latest_status_path),
        "operator_markdown_path": clean_text(status.get("operator_markdown_path")),
        "next_operator_action": clean_text(
            status.get("next_operator_action") or "review only, no live action available"
        ),
        **_panel_safety_flags(),
    }


def _build_public_market_paper_loop_summary(
    *,
    public_market_paper_loop_status: Mapping[str, Any] | None,
    latest_status_path: str,
) -> dict[str, Any]:
    status = dict(public_market_paper_loop_status or {})
    return {
        "contract_version": OPERATOR_UI_PANEL_PUBLIC_MARKET_PAPER_LOOP_SUMMARY_CONTRACT,
        "public_market_paper_loop_section_ready": True,
        "status": clean_text(status.get("status") or NOT_AVAILABLE),
        "market": clean_text(status.get("market") or status.get("market_symbol") or NOT_AVAILABLE),
        "strategy_name": clean_text(status.get("strategy_name") or NOT_AVAILABLE),
        "source": clean_text(status.get("source") or NOT_AVAILABLE),
        "source_type": clean_text(status.get("source_type") or NOT_AVAILABLE),
        "mode": clean_text(status.get("mode") or "paper / review-only"),
        "live_execution": clean_text(status.get("live_execution") or "blocked"),
        "live_execution_blocked": True,
        "evidence_pack_path": clean_text(status.get("evidence_pack_path")),
        "normalized_snapshot_path": clean_text(status.get("normalized_snapshot_path")),
        "signal_status": clean_text(status.get("signal_status") or NOT_AVAILABLE),
        "risk_decision": clean_text(status.get("risk_decision") or NOT_AVAILABLE),
        "paper_intent_status": clean_text(status.get("paper_intent_status") or "no_paper_intent"),
        "paper_intent_summary": clean_text(status.get("paper_intent_summary")),
        "artifact": clean_text(status.get("artifact_path") or status.get("artifact")),
        "latest_status_path": clean_text(status.get("latest_status_path") or latest_status_path),
        "next_operator_action": clean_text(
            status.get("next_operator_action") or "review only, no live action available"
        ),
        "auth_used": False,
        "credentials_used": False,
        "wallet_used": False,
        "signing_used": False,
        "order_endpoint_used": False,
        **_panel_safety_flags(),
    }


def _build_paper_decision_ledger_summary(
    *,
    paper_decision_ledger_status: Mapping[str, Any] | None,
    latest_status_path: str,
) -> dict[str, Any]:
    status = dict(paper_decision_ledger_status or {})
    counts = status.get("count_by_outcome") if isinstance(status.get("count_by_outcome"), Mapping) else {}
    return {
        "contract_version": OPERATOR_UI_PANEL_PAPER_DECISION_LEDGER_SUMMARY_CONTRACT,
        "paper_decision_ledger_section_ready": True,
        "status": clean_text(status.get("status") or NOT_AVAILABLE),
        "market": clean_text(status.get("market") or status.get("market_symbol") or NOT_AVAILABLE),
        "strategy_name": clean_text(status.get("strategy_name") or NOT_AVAILABLE),
        "source_type": clean_text(status.get("source_type") or NOT_AVAILABLE),
        "latest_run_source": clean_text(status.get("latest_run_source") or NOT_AVAILABLE),
        "last_outcome": clean_text(status.get("last_outcome") or NOT_AVAILABLE),
        "ledger_entry_count": _int_or_zero(status.get("ledger_entry_count")),
        "count_by_outcome": dict(counts),
        "evidence_pack_path": clean_text(status.get("evidence_pack_path")),
        "latest_ledger_path": clean_text(status.get("latest_ledger_path") or latest_status_path),
        "summary_path": clean_text(status.get("summary_path")),
        "trace_path": clean_text(status.get("trace_path")),
        "operator_markdown_path": clean_text(status.get("operator_markdown_path")),
        "mode": clean_text(status.get("mode") or "paper / review-only"),
        "live_execution": clean_text(status.get("live_execution") or "blocked"),
        "live_execution_blocked": True,
        "next_operator_action": clean_text(
            status.get("next_operator_action") or "review only; no live action available"
        ),
        **_panel_safety_flags(),
    }


def _build_live_connector_preflight_summary(
    *,
    live_connector_preflight_status: Mapping[str, Any] | None,
    latest_status_path: str,
) -> dict[str, Any]:
    status = dict(live_connector_preflight_status or {})
    blockers = status.get("blockers") if isinstance(status.get("blockers"), list) else []
    top_blockers = status.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:8]
    return {
        "contract_version": OPERATOR_UI_PANEL_LIVE_CONNECTOR_PREFLIGHT_SUMMARY_CONTRACT,
        "live_connector_preflight_section_ready": True,
        "status": clean_text(status.get("status") or NOT_AVAILABLE),
        "market": clean_text(status.get("market") or NOT_AVAILABLE),
        "mode": clean_text(status.get("mode") or "preflight / review-only"),
        "execution_mode": clean_text(status.get("execution_mode") or "paper_or_preflight"),
        "public_network_status": clean_text(
            status.get("public_network_status") or status.get("public_network") or NOT_AVAILABLE
        ),
        "auth_boundary_status": clean_text(
            status.get("auth_boundary_status") or status.get("auth_boundary") or NOT_AVAILABLE
        ),
        "blocker_count": _int_or_zero(status.get("blocker_count"), len(blockers)),
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "artifact_path": clean_text(status.get("artifact_path")),
        "latest_status_path": clean_text(status.get("latest_status_path") or latest_status_path),
        "operator_markdown_path": clean_text(status.get("operator_markdown_path")),
        "network_evidence_path": clean_text(status.get("network_evidence_path")),
        "credential_presence_path": clean_text(status.get("credential_presence_path")),
        "blockers_path": clean_text(status.get("blockers_path")),
        "review_only": True,
        "preflight_only": True,
        "order_submission_blocked": True,
        "signing_blocked": True,
        "wallet_connection_blocked": True,
        "live_execution_blocked": True,
        "next_operator_action": clean_text(
            status.get("next_operator_action") or "review preflight only, no live order available"
        ),
        **_panel_safety_flags(),
    }


def _build_authenticated_clob_preflight_summary(
    *,
    authenticated_clob_preflight_status: Mapping[str, Any] | None,
    latest_status_path: str,
) -> dict[str, Any]:
    status = dict(authenticated_clob_preflight_status or {})
    blockers = status.get("blockers") if isinstance(status.get("blockers"), list) else []
    top_blockers = status.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:8]
    return {
        "contract_version": OPERATOR_UI_PANEL_AUTHENTICATED_CLOB_PREFLIGHT_SUMMARY_CONTRACT,
        "authenticated_clob_preflight_section_ready": True,
        "status": clean_text(status.get("status") or NOT_AVAILABLE),
        "market": clean_text(status.get("market") or NOT_AVAILABLE),
        "mode": clean_text(status.get("mode") or "preflight / review-only"),
        "execution_mode": clean_text(status.get("execution_mode") or "preflight"),
        "auth_presence_status": clean_text(
            status.get("auth_presence_status") or status.get("auth_presence") or NOT_AVAILABLE
        ),
        "auth_presence_checked": status.get("auth_presence_check_performed") is True,
        "auth_presence_detected": status.get("auth_presence_detected") is True,
        "clob_base_url_status": clean_text(
            status.get("clob_base_url_status") or status.get("clob_base_url") or NOT_AVAILABLE
        ),
        "header_boundary_status": clean_text(
            status.get("auth_header_boundary_status")
            or status.get("auth_header_boundary")
            or status.get("header_boundary_status")
            or NOT_AVAILABLE
        ),
        "auth_boundary_checked": status.get("auth_boundary_checked") is True,
        "no_order_auth_check_status": clean_text(
            status.get("no_order_auth_check_status") or NOT_AVAILABLE
        ),
        "no_order_auth_check_performed": status.get("no_order_auth_check_performed") is True,
        "authenticated_request_performed": False,
        "blocker_count": _int_or_zero(status.get("blocker_count"), len(blockers)),
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "artifact_path": clean_text(status.get("artifact_path")),
        "latest_status_path": clean_text(status.get("latest_status_path") or latest_status_path),
        "operator_markdown_path": clean_text(status.get("operator_markdown_path")),
        "credential_presence_path": clean_text(status.get("credential_presence_path")),
        "clob_base_url_validation_path": clean_text(status.get("clob_base_url_validation_path")),
        "header_boundary_check_path": clean_text(status.get("auth_header_boundary_check_path")),
        "no_order_authenticated_request_plan_path": clean_text(
            status.get("no_order_authenticated_request_plan_path")
        ),
        "blockers_path": clean_text(status.get("blockers_path")),
        "review_only": True,
        "preflight_only": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "signing_blocked": True,
        "wallet_connection_blocked": True,
        "balance_read_blocked": True,
        "position_read_blocked": True,
        "live_execution_blocked": True,
        "next_operator_action": clean_text(
            status.get("next_operator_action")
            or "configure redacted L2 presence markers or review blockers; no live order available"
        ),
        **_panel_safety_flags(),
    }


def _build_action_states() -> list[dict[str, Any]]:
    return [
        OperatorUIPanelActionState(
            action_id="inspect_readiness_evidence_bundle",
            label="Inspect readiness evidence bundle",
            state="read_only_available",
            requires_future_operator_task=False,
            notes="Static review only.",
        ).to_dict(),
        OperatorUIPanelActionState(
            action_id="inspect_blocker_matrix",
            label="Inspect blocker matrix",
            state="read_only_available",
            requires_future_operator_task=False,
            notes="All live blockers remain unresolved.",
        ).to_dict(),
        OperatorUIPanelActionState(
            action_id="inspect_risk_limits",
            label="Inspect risk limits",
            state="read_only_available",
            requires_future_operator_task=False,
            notes="Config visibility only; no live risk gate is added.",
        ).to_dict(),
        OperatorUIPanelActionState(
            action_id="inspect_kill_switch",
            label="Inspect kill-switch status",
            state="read_only_available",
            requires_future_operator_task=False,
            notes="Requirements are visible; live verification remains missing.",
        ).to_dict(),
        OperatorUIPanelActionState(
            action_id="inspect_tiny_live_canary_gonogo_gate",
            label="Inspect go/no-go gate",
            state="read_only_available",
            requires_future_operator_task=False,
            notes="Final gate is passive review only and exposes no executable action.",
        ).to_dict(),
        OperatorUIPanelActionState(
            action_id="inspect_supervised_tiny_canary_approval_packet",
            label="Inspect supervised tiny canary approval packet",
            state="read_only_available",
            requires_future_operator_task=False,
            notes="Approval packet is review-only and cannot approve or execute live trading.",
        ).to_dict(),
        OperatorUIPanelActionState(
            action_id="future_canary_gate_status",
            label="Future canary gate status",
            state="blocked_not_executable",
            notes="The panel shows why the future canary remains blocked.",
        ).to_dict(),
    ]


def _build_sections(
    *,
    readiness: Mapping[str, Any],
    evidence: Mapping[str, Any],
    blockers: Mapping[str, Any],
    live_auth: Mapping[str, Any],
    btc_market: Mapping[str, Any],
    btc_analysis_order_intent: Mapping[str, Any],
    live_order_submission_boundary: Mapping[str, Any],
    live_enablement_config_preflight: Mapping[str, Any],
    authenticated_polymarket_connector_scaffold: Mapping[str, Any],
    wallet_signing_boundary: Mapping[str, Any],
    signed_order_payload_validation_gate: Mapping[str, Any],
    tiny_live_canary_gonogo_gate: Mapping[str, Any],
    supervised_tiny_canary_approval_packet: Mapping[str, Any],
    risk_control: Mapping[str, Any],
    risk: Mapping[str, Any],
    kill_switch: Mapping[str, Any],
    telegram_operator_control: Mapping[str, Any],
    telegram_mini_app: Mapping[str, Any],
    paper: Mapping[str, Any],
    paper_canary_drill: Mapping[str, Any],
    paper_trading_loop: Mapping[str, Any],
    public_market_paper_loop: Mapping[str, Any],
    paper_decision_ledger: Mapping[str, Any],
    live_connector_preflight: Mapping[str, Any],
    authenticated_clob_preflight: Mapping[str, Any],
    operator_packets: Mapping[str, Any],
    audit: Mapping[str, Any],
    action_states: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _section(
            "header_execution_posture",
            "Header / Execution Posture",
            "live_disabled",
            [
                _metric("mode", "Mode", readiness.get("mode")),
                _metric("real_execution_available", "Real execution available", False),
                _metric("live_execution_approved", "Live execution approved", False),
                _metric("canary_executable_now", "Canary executable now", False),
                _metric("live_connector_enabled", "Live connector enabled", False),
                _metric("operator_review_ready", "Operator review ready", readiness.get("operator_review_ready")),
                _metric(
                    "evidence_bundle_review_ready",
                    "Evidence bundle review ready",
                    readiness.get("evidence_bundle_review_ready"),
                ),
            ],
            warnings=[_warning("live_execution_disabled", "critical", LIVE_DISABLED_WARNING)],
            action_states=action_states,
        ),
        _section(
            "readiness_evidence_bundle",
            "Readiness Evidence Bundle",
            clean_text(evidence.get("readiness_evidence_bundle_status") or NOT_AVAILABLE),
            [
                _metric("readiness_evidence_bundle_status", "Bundle status", evidence.get("readiness_evidence_bundle_status")),
                _metric("evidence_item_count", "Evidence item count", evidence.get("evidence_item_count")),
                _metric("missing_required_evidence_count", "Missing required evidence", evidence.get("missing_required_evidence_count")),
                _metric("latest_readiness_evidence_bundle_path", "Latest bundle reference", evidence.get("latest_readiness_evidence_bundle_path")),
                _metric("readiness_bundle_is_not_live_approval", "Bundle is not live approval", True),
            ],
        ),
        _section(
            "paper_canary_drill",
            "Paper Canary Drill",
            clean_text(paper_canary_drill.get("status") or NOT_AVAILABLE),
            [
                _metric("status", "Status", paper_canary_drill.get("status")),
                _metric("market", "Market", paper_canary_drill.get("market")),
                _metric("mode", "Mode", paper_canary_drill.get("mode")),
                _metric("live_execution", "Live execution", paper_canary_drill.get("live_execution")),
                _metric("overall_decision", "Overall decision", paper_canary_drill.get("overall_decision")),
                _metric("go_no_go_status", "Go/no-go status", paper_canary_drill.get("go_no_go_status")),
                _metric(
                    "paper_order_intent_status",
                    "Paper order intent status",
                    paper_canary_drill.get("paper_order_intent_status"),
                ),
                _metric("artifact", "Artifact", paper_canary_drill.get("artifact")),
                _metric("latest_status_path", "Latest status", paper_canary_drill.get("latest_status_path")),
                _metric("review_only", "Review-only", True),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
            ],
            warnings=[
                _warning(
                    "paper_canary_review_only",
                    "warning",
                    "Paper canary drill status is review-only and cannot approve or enable live execution.",
                )
            ],
        ),
        _section(
            "paper_trading_loop",
            "Paper Trading Loop",
            clean_text(paper_trading_loop.get("status") or NOT_AVAILABLE),
            [
                _metric("status", "Status", paper_trading_loop.get("status")),
                _metric("market", "Market", paper_trading_loop.get("market")),
                _metric("strategy_name", "Strategy", paper_trading_loop.get("strategy_name")),
                _metric("mode", "Mode", paper_trading_loop.get("mode")),
                _metric("live_execution", "Live execution", paper_trading_loop.get("live_execution")),
                _metric("live_execution_blocked", "Live execution blocked", True),
                _metric("signal_status", "Signal status", paper_trading_loop.get("signal_status")),
                _metric("risk_decision", "Risk decision", paper_trading_loop.get("risk_decision")),
                _metric("paper_intent_status", "Paper intent status", paper_trading_loop.get("paper_intent_status")),
                _metric("paper_intent_summary", "Paper intent summary", paper_trading_loop.get("paper_intent_summary")),
                _metric("artifact", "Artifact", paper_trading_loop.get("artifact")),
                _metric("latest_status_path", "Latest status", paper_trading_loop.get("latest_status_path")),
                _metric("review_only", "Review-only", True),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
            ],
            warnings=[
                _warning(
                    "paper_trading_loop_review_only",
                    "warning",
                    "Paper trading loop status is review-only and exposes no executable live action.",
                )
            ],
        ),
        _section(
            "public_market_paper_loop",
            "Public Market Paper Loop",
            clean_text(public_market_paper_loop.get("status") or NOT_AVAILABLE),
            [
                _metric("status", "Status", public_market_paper_loop.get("status")),
                _metric("market", "Market", public_market_paper_loop.get("market")),
                _metric("strategy_name", "Strategy", public_market_paper_loop.get("strategy_name")),
                _metric("source", "Source", public_market_paper_loop.get("source")),
                _metric("source_type", "Source type", public_market_paper_loop.get("source_type")),
                _metric("mode", "Mode", public_market_paper_loop.get("mode")),
                _metric("live_execution", "Live execution", public_market_paper_loop.get("live_execution")),
                _metric("live_execution_blocked", "Live execution blocked", True),
                _metric("evidence_pack_path", "Evidence pack", public_market_paper_loop.get("evidence_pack_path")),
                _metric("risk_decision", "Risk decision", public_market_paper_loop.get("risk_decision")),
                _metric(
                    "paper_intent_status",
                    "Paper intent status",
                    public_market_paper_loop.get("paper_intent_status"),
                ),
                _metric(
                    "paper_intent_summary",
                    "Paper intent summary",
                    public_market_paper_loop.get("paper_intent_summary"),
                ),
                _metric("artifact", "Artifact", public_market_paper_loop.get("artifact")),
                _metric("latest_status_path", "Latest status", public_market_paper_loop.get("latest_status_path")),
                _metric("review_only", "Review-only", True),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
            ],
            warnings=[
                _warning(
                    "public_market_paper_loop_review_only",
                    "warning",
                    "Public market paper loop status is passive review-only and exposes no executable live action.",
                )
            ],
        ),
        _section(
            "paper_decision_ledger",
            "Paper Decision Ledger",
            clean_text(paper_decision_ledger.get("last_outcome") or NOT_AVAILABLE),
            [
                _metric("status", "Status", paper_decision_ledger.get("status")),
                _metric("market", "Market", paper_decision_ledger.get("market")),
                _metric("strategy_name", "Strategy", paper_decision_ledger.get("strategy_name")),
                _metric("source_type", "Source type", paper_decision_ledger.get("source_type")),
                _metric("last_outcome", "Last outcome", paper_decision_ledger.get("last_outcome")),
                _metric("ledger_entry_count", "Ledger entries", paper_decision_ledger.get("ledger_entry_count")),
                _metric(
                    "count_by_outcome",
                    "Count by outcome",
                    paper_decision_ledger.get("count_by_outcome"),
                ),
                _metric("evidence_pack_path", "Evidence pack", paper_decision_ledger.get("evidence_pack_path")),
                _metric("latest_ledger_path", "Ledger", paper_decision_ledger.get("latest_ledger_path")),
                _metric("live_execution_blocked", "Live execution blocked", True),
                _metric("review_only", "Review-only", True),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
            ],
            warnings=[
                _warning(
                    "paper_decision_ledger_review_only",
                    "warning",
                    "Paper decision ledger status is passive review-only and exposes no executable live action.",
                )
            ],
        ),
        _section(
            "live_connector_preflight",
            "Live Connector Preflight",
            clean_text(live_connector_preflight.get("status") or NOT_AVAILABLE),
            [
                _metric("status", "Status", live_connector_preflight.get("status")),
                _metric("market", "Market", live_connector_preflight.get("market")),
                _metric("mode", "Mode", live_connector_preflight.get("mode")),
                _metric(
                    "public_network_status",
                    "Public network",
                    live_connector_preflight.get("public_network_status"),
                ),
                _metric(
                    "auth_boundary_status",
                    "Auth boundary",
                    live_connector_preflight.get("auth_boundary_status"),
                ),
                _metric("blocker_count", "Blockers", live_connector_preflight.get("blocker_count")),
                _metric(
                    "top_blocker_reasons",
                    "Top blockers",
                    live_connector_preflight.get("top_blocker_reasons"),
                ),
                _metric("order_submission_blocked", "Order submission blocked", True),
                _metric("signing_blocked", "Signing blocked", True),
                _metric("live_execution_blocked", "Live execution blocked", True),
                _metric(
                    "latest_status_path",
                    "Latest status",
                    live_connector_preflight.get("latest_status_path"),
                ),
                _metric("review_only", "Review-only", True),
                _metric("preflight_only", "Preflight-only", True),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
                _metric("live_connector_enabled", "Live connector enabled", False),
                _metric("allowed_for_live", "Allowed for live", False),
            ],
            warnings=[
                _warning(
                    "live_connector_preflight_review_only",
                    "critical",
                    "Live connector preflight is passive review-only and exposes no executable live action.",
                )
            ],
        ),
        _section(
            "authenticated_clob_preflight",
            "Authenticated CLOB Preflight",
            clean_text(authenticated_clob_preflight.get("status") or NOT_AVAILABLE),
            [
                _metric("status", "Status", authenticated_clob_preflight.get("status")),
                _metric("market", "Market", authenticated_clob_preflight.get("market")),
                _metric("mode", "Mode", authenticated_clob_preflight.get("mode")),
                _metric(
                    "auth_presence_status",
                    "Auth presence",
                    authenticated_clob_preflight.get("auth_presence_status"),
                ),
                _metric(
                    "clob_base_url_status",
                    "CLOB base URL",
                    authenticated_clob_preflight.get("clob_base_url_status"),
                ),
                _metric(
                    "header_boundary_status",
                    "Header boundary",
                    authenticated_clob_preflight.get("header_boundary_status"),
                ),
                _metric(
                    "no_order_auth_check_status",
                    "No-order auth check",
                    authenticated_clob_preflight.get("no_order_auth_check_status"),
                ),
                _metric("blocker_count", "Blockers", authenticated_clob_preflight.get("blocker_count")),
                _metric(
                    "top_blocker_reasons",
                    "Top blockers",
                    authenticated_clob_preflight.get("top_blocker_reasons"),
                ),
                _metric("order_submission_blocked", "Order submission blocked", True),
                _metric("order_cancellation_blocked", "Order cancellation blocked", True),
                _metric("signing_blocked", "Signing blocked", True),
                _metric("wallet_connection_blocked", "Wallet connection blocked", True),
                _metric("balance_read_blocked", "Balances blocked", True),
                _metric("position_read_blocked", "Positions blocked", True),
                _metric("live_execution_blocked", "Live execution blocked", True),
                _metric(
                    "latest_status_path",
                    "Latest status",
                    authenticated_clob_preflight.get("latest_status_path"),
                ),
                _metric("review_only", "Review-only", True),
                _metric("preflight_only", "Preflight-only", True),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
                _metric("authenticated_polymarket_enabled", "Authenticated trading enabled", False),
                _metric("live_connector_enabled", "Live connector enabled", False),
                _metric("allowed_for_live", "Allowed for live", False),
            ],
            warnings=[
                _warning(
                    "authenticated_clob_preflight_review_only",
                    "critical",
                    "Authenticated CLOB preflight is passive review-only and exposes no executable live action.",
                )
            ],
        ),
        _section(
            "live_blockers",
            "Live Blockers",
            "blocked",
            [
                _metric("total_blockers", "Total blockers", blockers.get("total_blockers")),
                _metric("critical_blockers", "Critical blockers", blockers.get("critical_blockers")),
                _metric("unresolved_blockers", "Unresolved blockers", blockers.get("unresolved_blockers")),
                _metric("resolved_blockers", "Resolved blockers", blockers.get("resolved_blockers")),
                _metric("all_blockers_unresolved", "All blockers unresolved", blockers.get("all_blockers_unresolved")),
                _metric("top_blockers", "Top blocker IDs", [row.get("blocker_id") for row in blockers.get("top_blockers", [])]),
            ],
        ),
        _section(
            "live_credentials_auth_boundary",
            "Live Credentials / Auth Boundary",
            clean_text(live_auth.get("live_credentials_boundary_status") or NOT_AVAILABLE),
            [
                _metric(
                    "live_credentials_boundary_status",
                    "Boundary status",
                    live_auth.get("live_credentials_boundary_status"),
                ),
                _metric(
                    "live_credentials_configured",
                    "Live credentials configured",
                    live_auth.get("live_credentials_configured"),
                ),
                _metric(
                    "required_credentials_count",
                    "Required credentials",
                    live_auth.get("required_credentials_count"),
                ),
                _metric(
                    "missing_credentials_count",
                    "Missing credentials",
                    live_auth.get("missing_credentials_count"),
                ),
                _metric(
                    "credential_statuses_redacted",
                    "Credential statuses redacted",
                    live_auth.get("credential_statuses_redacted"),
                ),
                _metric(
                    "authenticated_endpoints_enabled",
                    "Authenticated endpoints enabled",
                    False,
                ),
                _metric("signing_enabled", "Signing enabled", False),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("allowed_for_live", "Allowed for live", False),
                _metric("canary_executable_now", "Canary executable now", False),
                _metric("live_execution_approved", "Live execution approved", False),
                _metric("warning", "Warning", live_auth.get("warning") or UI_REDACTION_WARNING),
            ],
            warnings=[
                _warning(
                    "credentials_status_redacted",
                    "warning",
                    live_auth.get("warning") or UI_REDACTION_WARNING,
                )
            ],
        ),
        _section(
            "btc_market_connector",
            "BTC Market Connector",
            clean_text(btc_market.get("btc_market_connector_status") or NOT_AVAILABLE),
            [
                _metric("btc_market_connector_status", "Connector status", btc_market.get("btc_market_connector_status")),
                _metric("market_id", "Market ID", btc_market.get("market_id")),
                _metric("market_slug", "Market slug", btc_market.get("market_slug")),
                _metric("market_title", "Market title", btc_market.get("market_title")),
                _metric("is_btc_related", "BTC related", btc_market.get("is_btc_related")),
                _metric("market_status", "Market status", btc_market.get("market_status")),
                _metric("is_open", "Open", btc_market.get("is_open")),
                _metric("is_resolved", "Resolved", btc_market.get("is_resolved")),
                _metric("stale", "Stale", btc_market.get("stale")),
                _metric("snapshot_age_seconds", "Snapshot age seconds", btc_market.get("snapshot_age_seconds")),
                _metric("best_bid", "Best bid", btc_market.get("best_bid")),
                _metric("best_ask", "Best ask", btc_market.get("best_ask")),
                _metric("last_price", "Last price", btc_market.get("last_price")),
                _metric("spread", "Spread", btc_market.get("spread")),
                _metric("liquidity", "Liquidity", btc_market.get("liquidity")),
                _metric("price_status", "Price status", btc_market.get("price_status")),
                _metric(
                    "risk_control_market_data_status",
                    "Risk market-data status",
                    btc_market.get("risk_control_market_data_status"),
                ),
                _metric("read_only_network_enabled", "Read-only network enabled", btc_market.get("read_only_network_enabled")),
                _metric(
                    "latest_btc_market_snapshot_path",
                    "Latest BTC market snapshot",
                    btc_market.get("latest_btc_market_snapshot_path"),
                ),
            ],
        ),
        _section(
            "btc_analysis_order_intent",
            "BTC Analysis / Order Intent",
            clean_text(btc_analysis_order_intent.get("btc_market_analysis_status") or NOT_AVAILABLE),
            [
                _metric(
                    "btc_market_analysis_status",
                    "BTC market analysis status",
                    btc_analysis_order_intent.get("btc_market_analysis_status"),
                ),
                _metric(
                    "btc_intent_candidate_status",
                    "Intent candidate status",
                    btc_analysis_order_intent.get("btc_intent_candidate_status"),
                ),
                _metric(
                    "dry_run_order_intent_status",
                    "Dry-run order intent status",
                    btc_analysis_order_intent.get("dry_run_order_intent_status"),
                ),
                _metric("intent_market_id", "Intent market ID", btc_analysis_order_intent.get("intent_market_id")),
                _metric("intent_market_slug", "Intent market slug", btc_analysis_order_intent.get("intent_market_slug")),
                _metric(
                    "intent_notional_usd",
                    "Intent notional USD",
                    btc_analysis_order_intent.get("intent_notional_usd"),
                ),
                _metric(
                    "intent_limit_price",
                    "Intent limit price",
                    btc_analysis_order_intent.get("intent_limit_price"),
                ),
                _metric(
                    "risk_decision_status",
                    "Risk decision status",
                    btc_analysis_order_intent.get("risk_decision_status"),
                ),
                _metric(
                    "allowed_for_dry_run",
                    "Allowed for dry-run",
                    btc_analysis_order_intent.get("allowed_for_dry_run"),
                ),
                _metric("allowed_for_live", "Allowed for live", False),
                _metric(
                    "analysis_is_not_live_recommendation",
                    "Analysis is not live recommendation",
                    True,
                ),
                _metric(
                    "order_intent_is_not_order_submission",
                    "Order intent is not order submission",
                    True,
                ),
                _metric(
                    "latest_btc_analysis_path",
                    "Latest BTC analysis",
                    btc_analysis_order_intent.get("latest_btc_analysis_path"),
                ),
                _metric(
                    "latest_btc_order_intent_path",
                    "Latest BTC order intent",
                    btc_analysis_order_intent.get("latest_btc_order_intent_path"),
                ),
                _metric(
                    "latest_btc_risk_decision_path",
                    "Latest BTC risk decision",
                    btc_analysis_order_intent.get("latest_btc_risk_decision_path"),
                ),
            ],
        ),
        _section(
            "live_order_submission_boundary",
            "Live Order Submission Boundary",
            clean_text(live_order_submission_boundary.get("status") or NOT_AVAILABLE),
            [
                _metric("boundary_name", "Boundary", live_order_submission_boundary.get("boundary_name")),
                _metric("dry_run_review_ready", "Dry-run review ready", live_order_submission_boundary.get("dry_run_review_ready")),
                _metric("market_id", "Market ID", live_order_submission_boundary.get("market_id")),
                _metric("market_slug", "Market slug", live_order_submission_boundary.get("market_slug")),
                _metric("asset", "Asset", live_order_submission_boundary.get("asset")),
                _metric("side", "Side", live_order_submission_boundary.get("side")),
                _metric("outcome", "Outcome", live_order_submission_boundary.get("outcome")),
                _metric("would_submit_order", "Would submit order", False),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric(
                    "authenticated_endpoint_required",
                    "Authenticated endpoint required for future live",
                    live_order_submission_boundary.get("authenticated_endpoint_required"),
                ),
                _metric("authenticated_endpoint_enabled", "Authenticated endpoint enabled", False),
                _metric(
                    "signing_required_for_future_live",
                    "Signing required for future live",
                    live_order_submission_boundary.get("signing_required_for_future_live"),
                ),
                _metric("signing_enabled", "Signing enabled", False),
                _metric(
                    "wallet_required_for_future_live",
                    "Wallet required for future live",
                    live_order_submission_boundary.get("wallet_required_for_future_live"),
                ),
                _metric("wallet_enabled", "Wallet enabled", False),
                _metric("allowed_for_live", "Allowed for live", False),
                _metric("live_execution_approved", "Live execution approved", False),
                _metric(
                    "top_refusal_reasons",
                    "Top refusal reasons",
                    live_order_submission_boundary.get("top_refusal_reasons"),
                ),
                _metric(
                    "top_blocker_reasons",
                    "Top blocker reasons",
                    live_order_submission_boundary.get("top_blocker_reasons"),
                ),
                _metric(
                    "latest_live_order_submission_boundary_path",
                    "Latest boundary receipt",
                    live_order_submission_boundary.get("latest_live_order_submission_boundary_path"),
                ),
            ],
        ),
        _section(
            "live_enablement_config_preflight",
            "Live Enablement Config Preflight",
            clean_text(live_enablement_config_preflight.get("status") or NOT_AVAILABLE),
            [
                _metric("status", "Status", live_enablement_config_preflight.get("status")),
                _metric(
                    "future_live_requested",
                    "Future live requested",
                    live_enablement_config_preflight.get("future_live_requested"),
                ),
                _metric(
                    "dry_run_review_allowed",
                    "Dry-run review allowed",
                    live_enablement_config_preflight.get("dry_run_review_allowed"),
                ),
                _metric("allowed_for_live", "Allowed for live", False),
                _metric("canary_executable_now", "Canary executable now", False),
                _metric("live_execution_approved", "Live execution approved", False),
                _metric("real_execution_available", "Real execution available", False),
                _metric("live_connector_enabled", "Live connector enabled", False),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric(
                    "authenticated_polymarket_enabled",
                    "Authenticated Polymarket enabled",
                    False,
                ),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric(
                    "top_blocked_reasons",
                    "Top blocked reasons",
                    live_enablement_config_preflight.get("top_blocked_reasons"),
                ),
                _metric("no_executable_action", "No executable action", True),
                _metric(
                    "latest_live_enablement_config_preflight_path",
                    "Latest config preflight",
                    live_enablement_config_preflight.get("latest_live_enablement_config_preflight_path"),
                ),
            ],
            warnings=[
                _warning(
                    "live_enablement_config_preflight_passive_only",
                    "critical",
                    "Live enablement config preflight is passive review only and exposes no executable live action.",
                )
            ],
        ),
        _section(
            "authenticated_polymarket_connector_scaffold",
            "Authenticated Polymarket Connector Scaffold",
            clean_text(authenticated_polymarket_connector_scaffold.get("status") or NOT_AVAILABLE),
            [
                _metric("status", "Status", authenticated_polymarket_connector_scaffold.get("status")),
                _metric(
                    "authenticated_calls_enabled",
                    "Authenticated calls enabled",
                    False,
                ),
                _metric("network_calls_enabled", "Network calls enabled", False),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric("real_execution_available", "Real execution available", False),
                _metric(
                    "credentials_redacted_or_missing_only",
                    "Credentials redacted/missing only",
                    authenticated_polymarket_connector_scaffold.get("credentials_redacted_or_missing_only"),
                ),
                _metric(
                    "configured_redacted_credential_count",
                    "Configured credential statuses",
                    authenticated_polymarket_connector_scaffold.get("configured_redacted_credential_count"),
                ),
                _metric(
                    "missing_credential_count",
                    "Missing credential statuses",
                    authenticated_polymarket_connector_scaffold.get("missing_credential_count"),
                ),
                _metric(
                    "top_blocked_reasons",
                    "Top blocked reasons",
                    authenticated_polymarket_connector_scaffold.get("top_blocked_reasons"),
                ),
                _metric("no_executable_action", "No executable action", True),
                _metric(
                    "latest_authenticated_polymarket_connector_scaffold_path",
                    "Latest scaffold artifact",
                    authenticated_polymarket_connector_scaffold.get(
                        "latest_authenticated_polymarket_connector_scaffold_path"
                    ),
                ),
            ],
            warnings=[
                _warning(
                    "authenticated_polymarket_connector_scaffold_passive_only",
                    "critical",
                    "Authenticated Polymarket connector scaffold is passive review only and exposes no executable live action.",
                )
            ],
        ),
        _section(
            "wallet_signing_boundary",
            "Wallet Signing Boundary",
            clean_text(wallet_signing_boundary.get("status") or "SIGNING_DISABLED_REVIEW_ONLY"),
            [
                _metric("status", "Status", wallet_signing_boundary.get("status")),
                _metric(
                    "wallet_address_status",
                    "Wallet address status",
                    wallet_signing_boundary.get("wallet_address_status"),
                ),
                _metric(
                    "signing_provider_status",
                    "Signing provider status",
                    wallet_signing_boundary.get("signing_provider_status"),
                ),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
                _metric(
                    "signed_payload_generation_enabled",
                    "Signed payload generation enabled",
                    False,
                ),
                _metric("signed_order_generation_enabled", "Signed order generation enabled", False),
                _metric("transaction_signing_enabled", "Transaction signing enabled", False),
                _metric("allowed_for_live", "Allowed for live", False),
                _metric("real_execution_available", "Real execution available", False),
                _metric(
                    "top_blocked_reasons",
                    "Top blocked reasons",
                    wallet_signing_boundary.get("top_blocked_reasons"),
                ),
                _metric("no_executable_action", "No executable action", True),
                _metric(
                    "latest_wallet_signing_boundary_path",
                    "Latest boundary artifact",
                    wallet_signing_boundary.get("latest_wallet_signing_boundary_path"),
                ),
            ],
            warnings=[
                _warning(
                    "wallet_signing_boundary_review_only",
                    "critical",
                    "Wallet signing boundary is passive review only and exposes no executable signing or wallet action.",
                )
            ],
        ),
        _section(
            "signed_order_payload_validation_gate",
            "Signed Order Payload Validation Gate",
            clean_text(signed_order_payload_validation_gate.get("payload_shape_status") or NOT_AVAILABLE),
            [
                _metric("status", "Status", signed_order_payload_validation_gate.get("status")),
                _metric(
                    "payload_shape_status",
                    "Payload shape status",
                    signed_order_payload_validation_gate.get("payload_shape_status"),
                ),
                _metric("signing_enabled", "Signing enabled", False),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric(
                    "signed_payload_generation_enabled",
                    "Signed payload generation enabled",
                    False,
                ),
                _metric("signed_order_generation_enabled", "Signed order generation enabled", False),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("allowed_for_live", "Allowed for live", False),
                _metric(
                    "top_blocked_reasons",
                    "Top blocked reasons",
                    signed_order_payload_validation_gate.get("top_blocked_reasons"),
                ),
                _metric("no_executable_action", "No executable action", True),
                _metric(
                    "latest_signed_order_payload_validation_gate_path",
                    "Latest signed payload gate",
                    signed_order_payload_validation_gate.get(
                        "latest_signed_order_payload_validation_gate_path"
                    ),
                ),
            ],
            warnings=[
                _warning(
                    "signed_order_payload_validation_gate_review_only",
                    "critical",
                    "Signed order payload validation gate is passive review only and exposes no executable signing or submission action.",
                )
            ],
        ),
        _section(
            "tiny_live_canary_gonogo_gate",
            "Tiny Live Canary Go/No-Go Gate",
            clean_text(tiny_live_canary_gonogo_gate.get("status") or NOT_AVAILABLE),
            [
                _metric("overall_decision", "Overall decision", tiny_live_canary_gonogo_gate.get("overall_decision")),
                _metric("review_only_status", "Review-only status", tiny_live_canary_gonogo_gate.get("review_only_status")),
                _metric(
                    "manual_execution_checklist_count",
                    "Manual checklist items",
                    tiny_live_canary_gonogo_gate.get("manual_execution_checklist_count"),
                ),
                _metric(
                    "final_pre_live_checklist_count",
                    "Final pre-live checklist items",
                    tiny_live_canary_gonogo_gate.get("final_pre_live_checklist_count"),
                ),
                _metric("top_no_go_reasons", "Top no-go reasons", tiny_live_canary_gonogo_gate.get("top_no_go_reasons")),
                _metric(
                    "unresolved_blocker_count",
                    "Unresolved blockers",
                    tiny_live_canary_gonogo_gate.get("unresolved_blocker_count"),
                ),
                _metric(
                    "resolved_blocker_count",
                    "Resolved blockers",
                    tiny_live_canary_gonogo_gate.get("resolved_blocker_count"),
                ),
                _metric(
                    "explicit_human_approval_required",
                    "Explicit human approval required",
                    True,
                ),
                _metric("no_executable_action", "No executable action", True),
                _metric("final_live_enablement_present", "Final live enablement present", False),
                _metric("live_execution_approved", "Live execution approved", False),
                _metric("canary_executable_now", "Canary executable now", False),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric(
                    "latest_tiny_live_canary_gonogo_gate_path",
                    "Latest go/no-go packet",
                    tiny_live_canary_gonogo_gate.get("latest_tiny_live_canary_gonogo_gate_path"),
                ),
            ],
        ),
        _section(
            "supervised_tiny_canary_approval_packet",
            "Supervised Tiny Canary Approval Packet",
            clean_text(supervised_tiny_canary_approval_packet.get("status") or "REVIEW_READY_BLOCKED_FOR_LIVE"),
            [
                _metric("status", "Status", supervised_tiny_canary_approval_packet.get("status")),
                _metric(
                    "approval_packet_ready_for_human_review",
                    "Ready for human review",
                    supervised_tiny_canary_approval_packet.get("approval_packet_ready_for_human_review"),
                ),
                _metric("review_only", "Review-only", True),
                _metric(
                    "packet_cannot_be_interpreted_as_live_approval",
                    "Cannot be interpreted as live approval",
                    True,
                ),
                _metric(
                    "approval_packet_may_be_used_as_live_approval",
                    "May be used as live approval",
                    False,
                ),
                _metric(
                    "operator_must_not_execute_from_this_packet",
                    "Operator must not execute from packet",
                    True,
                ),
                _metric(
                    "future_live_enabling_task_required",
                    "Future live-enabling task required",
                    True,
                ),
                _metric(
                    "operator_checklist_count",
                    "Operator checklist items",
                    supervised_tiny_canary_approval_packet.get("operator_checklist_count"),
                ),
                _metric(
                    "future_required_action_count",
                    "Future required actions",
                    supervised_tiny_canary_approval_packet.get("future_required_action_count"),
                ),
                _metric(
                    "unresolved_blocker_count",
                    "Unresolved blockers",
                    supervised_tiny_canary_approval_packet.get("unresolved_blocker_count"),
                ),
                _metric("resolved_blocker_count", "Resolved blockers", 0),
                _metric("live_execution_approved", "Live execution approved", False),
                _metric("canary_executable_now", "Canary executable now", False),
                _metric("real_execution_available", "Real execution available", False),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("wallet_signing_enabled", "Wallet signing enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
                _metric(
                    "signed_payload_generation_enabled",
                    "Signed payload generation enabled",
                    False,
                ),
                _metric("signed_order_generation_enabled", "Signed order generation enabled", False),
                _metric(
                    "authenticated_polymarket_enabled",
                    "Authenticated Polymarket enabled",
                    False,
                ),
                _metric("live_connector_enabled", "Live connector enabled", False),
                _metric("no_executable_action", "No executable action", True),
                _metric(
                    "latest_supervised_tiny_canary_approval_packet_json_path",
                    "Latest approval packet JSON",
                    supervised_tiny_canary_approval_packet.get(
                        "latest_supervised_tiny_canary_approval_packet_json_path"
                    ),
                ),
                _metric(
                    "latest_supervised_tiny_canary_approval_packet_md_path",
                    "Latest approval packet Markdown",
                    supervised_tiny_canary_approval_packet.get(
                        "latest_supervised_tiny_canary_approval_packet_md_path"
                    ),
                ),
            ],
            warnings=[
                _warning(
                    "supervised_tiny_canary_approval_packet_not_live_approval",
                    "critical",
                    "Approval packet is review-only; it does not approve or enable live execution.",
                )
            ],
        ),
        _section(
            "risk_control_plane",
            "Risk Control Plane",
            clean_text(risk_control.get("risk_control_plane_status") or "ready_no_intent_evaluated"),
            [
                _metric("risk_control_plane_status", "Control plane status", risk_control.get("risk_control_plane_status")),
                _metric("policy_id", "Policy ID", risk_control.get("policy_id")),
                _metric("mode", "Mode", risk_control.get("mode")),
                _metric("max_daily_loss_usd", "Max daily loss USD", risk_control.get("max_daily_loss_usd")),
                _metric("max_total_exposure_usd", "Max total exposure USD", risk_control.get("max_total_exposure_usd")),
                _metric("max_market_exposure_usd", "Max market exposure USD", risk_control.get("max_market_exposure_usd")),
                _metric("max_order_notional_usd", "Max order notional USD", risk_control.get("max_order_notional_usd")),
                _metric("max_orders_per_day", "Max orders per day", risk_control.get("max_orders_per_day")),
                _metric("max_trades_per_day", "Max trades per day", risk_control.get("max_trades_per_day")),
                _metric("max_active_markets", "Max active markets", risk_control.get("max_active_markets")),
                _metric("allowed_market_tags", "Allowed market tags", risk_control.get("allowed_market_tags")),
                _metric("market_data_status", "Market data status", risk_control.get("market_data_status")),
                _metric("market_data_market_status", "Market data market status", risk_control.get("market_data_market_status")),
                _metric("market_data_stale", "Market data stale", risk_control.get("market_data_stale")),
                _metric("market_data_age_seconds", "Market data age seconds", risk_control.get("market_data_age_seconds")),
                _metric("latest_decision_status", "Latest decision status", risk_control.get("latest_decision_status")),
                _metric("latest_violations_count", "Latest violations", risk_control.get("latest_violations_count")),
                _metric("latest_halt_reasons_count", "Latest halt reasons", risk_control.get("latest_halt_reasons_count")),
                _metric("allowed_for_dry_run", "Allowed for dry-run", risk_control.get("allowed_for_dry_run")),
                _metric("allowed_for_live", "Allowed for live", False),
            ],
        ),
        _section(
            "risk_limits",
            "Risk Limits",
            "review_config_visibility_only",
            [
                _metric("max_daily_loss_usd", "Max daily loss USD", risk.get("max_daily_loss_usd")),
                _metric("max_total_exposure_usd", "Max total exposure USD", risk.get("max_total_exposure_usd")),
                _metric("max_market_exposure_usd", "Max market exposure USD", risk.get("max_market_exposure_usd")),
                _metric("max_order_notional_usd", "Max order notional USD", risk.get("max_order_notional_usd")),
                _metric("max_market_count", "Max market count", risk.get("max_market_count")),
                _metric("max_order_count", "Max order count", risk.get("max_order_count")),
                _metric("max_trades_per_day", "Max trades per day", risk.get("max_trades_per_day")),
                _metric("cooldown_after_loss", "Cooldown after loss", risk.get("cooldown_after_loss")),
                _metric("halt_on_stale_data", "Halt on stale data", risk.get("halt_on_stale_data")),
                _metric("halt_on_audit_mismatch", "Halt on audit mismatch", risk.get("halt_on_audit_mismatch")),
                _metric("halt_on_kill_switch", "Halt on kill-switch", risk.get("halt_on_kill_switch")),
                _metric("halt_on_missing_operator_intent", "Halt on missing operator intent", risk.get("halt_on_missing_operator_intent")),
            ],
        ),
        _section(
            "kill_switch",
            "Kill-Switch",
            clean_text(kill_switch.get("current_kill_switch_state") or "blocks_live"),
            [
                _metric("kill_switch_requirements_defined", "Requirements defined", kill_switch.get("kill_switch_requirements_defined")),
                _metric("kill_switch_verified_for_live", "Verified for live", False),
                _metric("kill_switch_blocks_live_execution", "Blocks live execution", kill_switch.get("kill_switch_blocks_live_execution")),
                _metric("emergency_stop_documented", "Emergency stop documented", kill_switch.get("emergency_stop_documented")),
                _metric("current_kill_switch_state", "Current state", kill_switch.get("current_kill_switch_state")),
            ],
        ),
        _section(
            "telegram_operator_control_bot",
            "Telegram Operator Control Bot",
            "review_only",
            [
                _metric("configured", "Configured", telegram_operator_control.get("configured")),
                _metric(
                    "telegram_bot_token_status",
                    "Bot token status",
                    telegram_operator_control.get("telegram_bot_token_status"),
                ),
                _metric(
                    "allowed_operator_ids_configured",
                    "Allowed operator IDs configured",
                    telegram_operator_control.get("allowed_operator_ids_configured"),
                ),
                _metric(
                    "allowed_operator_id_count",
                    "Allowed operator ID count",
                    telegram_operator_control.get("allowed_operator_id_count"),
                ),
                _metric(
                    "operator_pause_requested",
                    "Pause requested",
                    telegram_operator_control.get("operator_pause_requested"),
                ),
                _metric(
                    "operator_kill_switch_requested",
                    "Kill-switch requested",
                    telegram_operator_control.get("operator_kill_switch_requested"),
                ),
                _metric("review_only", "Review-only", True),
                _metric("live_execution_approved", "Live execution approved", False),
                _metric("canary_executable_now", "Canary executable now", False),
                _metric("real_execution_available", "Real execution available", False),
                _metric("live_connector_enabled", "Live connector enabled", False),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric(
                    "latest_telegram_operator_control_state_path",
                    "Latest Telegram state artifact",
                    telegram_operator_control.get("latest_telegram_operator_control_state_path"),
                ),
            ],
            warnings=[
                _warning(
                    "telegram_control_review_only",
                    "warning",
                    "Telegram operator control is passive review/local state only and exposes no executable live action.",
                )
            ],
        ),
        _section(
            "telegram_mini_app_operator_panel",
            "Telegram Mini App Operator Panel",
            "static_review_only",
            [
                _metric(
                    "panel_artifact_available",
                    "Panel artifact available",
                    telegram_mini_app.get("panel_artifact_available"),
                ),
                _metric("review_only", "Review-only", True),
                _metric("live_actions_available", "Live actions available", False),
                _metric(
                    "latest_telegram_mini_app_operator_panel_html_path",
                    "Local HTML artifact",
                    telegram_mini_app.get("latest_telegram_mini_app_operator_panel_html_path"),
                ),
                _metric(
                    "latest_telegram_mini_app_operator_panel_json_path",
                    "Local JSON artifact",
                    telegram_mini_app.get("latest_telegram_mini_app_operator_panel_json_path"),
                ),
                _metric(
                    "mini_app_url_status",
                    "Mini App URL status",
                    telegram_mini_app.get("mini_app_url_status"),
                ),
                _metric(
                    "telegram_init_data_status",
                    "Telegram init data status",
                    telegram_mini_app.get("telegram_init_data_status"),
                ),
                _metric("execution_enabling", "Execution enabling", False),
                _metric("live_approval", "Live approval", False),
            ],
            warnings=[
                _warning(
                    "telegram_mini_app_review_only",
                    "warning",
                    "Telegram Mini App panel is a static review artifact and exposes no executable live action.",
                )
            ],
        ),
        _section(
            "paper_trading_summary",
            "Paper Trading Summary",
            clean_text(paper.get("paper_status")),
            [
                _metric("paper_pnl", "Paper PnL", paper.get("paper_pnl")),
                _metric("paper_exposure", "Paper exposure", paper.get("paper_exposure")),
                _metric("paper_positions_count", "Paper positions count", paper.get("paper_positions_count")),
                _metric("latest_paper_run_reference", "Latest paper run reference", paper.get("latest_paper_run_reference")),
                _metric("paper_strategy_evaluation_status", "Paper strategy evaluation status", paper.get("paper_strategy_evaluation_status")),
            ],
        ),
        _section(
            "operator_packets",
            "Operator Packets",
            "review_only",
            [
                _metric("operator_approval_packet_status", "Operator approval packet status", operator_packets.get("operator_approval_packet_status")),
                _metric("operator_intent_packet_status", "Operator intent packet status", operator_packets.get("operator_intent_packet_status")),
                _metric("operator_intent_is_human_acknowledgement_only", "Operator intent is human acknowledgement only", operator_packets.get("operator_intent_is_human_acknowledgement_only")),
                _metric("operator_intent_is_not_live_approval", "Operator intent is not live approval", True),
            ],
        ),
        _section(
            "audit_replay",
            "Audit / Replay",
            clean_text(audit.get("audit_replay_status")),
            [
                _metric("audit_replay_status", "Audit replay status", audit.get("audit_replay_status")),
                _metric("replay_passed_or_reviewable", "Replay passed/reviewable", audit.get("replay_passed_or_reviewable")),
                _metric("mismatch_count", "Mismatch count", audit.get("mismatch_count")),
                _metric("replay_is_not_execution", "Replay is not execution", True),
            ],
        ),
        _section(
            "next_gates",
            "Next Gates",
            "future_gates_required",
            [_metric("next_required_gates", "Next required gates", list(NEXT_REQUIRED_GATES))],
        ),
    ]


def _section(
    section_id: str,
    title: str,
    status: str,
    metrics: Sequence[Mapping[str, Any]],
    *,
    warnings: Sequence[Mapping[str, Any]] | None = None,
    action_states: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    return OperatorUIPanelSection(
        section_id=section_id,
        title=title,
        status=status,
        metrics=tuple(metrics),
        warnings=tuple(warnings or ()),
        action_states=tuple(action_states or ()),
    ).to_dict()


def _metric(metric_id: str, label: str, value: Any, *, status: str = "review_only", notes: str = "") -> dict[str, Any]:
    return OperatorUIPanelMetric(metric_id=metric_id, label=label, value=value, status=status, notes=notes).to_dict()


def _warning(warning_id: str, severity: str, message: str) -> dict[str, Any]:
    return OperatorUIPanelWarning(warning_id=warning_id, severity=severity, message=message).to_dict()


def _panel_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "read_only_panel": True,
        "dry_run_control_only": True,
        "paper_only": True,
        "execution_enabling": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "network_used": False,
        "network_calls_enabled": False,
        "external_api_calls_performed": False,
        "real_wallet_integration_added": False,
        "real_wallet_access_performed": False,
        "private_key_or_mnemonic_handling_added": False,
        "cryptographic_signing_added": False,
        "cryptographic_signing_performed": False,
        "wallet_signing_added": False,
        "wallet_signing_performed": False,
        "transaction_signing_added": False,
        "transaction_signing_enabled": False,
        "transaction_signing_performed": False,
        "signed_payload_generation_enabled": False,
        "signed_payload_created": False,
        "signed_order_generation_enabled": False,
        "signed_order_created": False,
        "signature_present": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "authenticated_endpoint_added": False,
        "authenticated_calls_enabled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_signing_enabled": False,
        "wallet_enabled": False,
        "would_submit_order": False,
        "order_submission_enabled": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "real_execution_available": False,
        "allowed_for_live": False,
        "live_execution_approved": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "canary_executable_now": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _first_available(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value:
            continue
        return value
    return NOT_AVAILABLE


def _int_or_zero(*values: Any) -> int:
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = clean_text(value).lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def _display_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return clean_text(value)


def _markdown_value(value: Any) -> str:
    return _display_value(value).replace("`", "'")


def _walk_flags(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            rows.append((path, key_text, nested))
            rows.extend(_walk_flags(nested, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_flags(nested, f"{path}[{index}]"))
    return rows


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
