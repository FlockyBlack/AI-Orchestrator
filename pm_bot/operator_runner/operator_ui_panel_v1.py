from __future__ import annotations

import hashlib
import html
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, mapping_rows
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_risk_control_ui_summary,
    validate_secret_boundary_operator_ui_panel_action_state,
    validate_secret_boundary_operator_ui_panel_kill_switch_summary,
    validate_secret_boundary_operator_ui_panel_payload,
    validate_secret_boundary_operator_ui_panel_rendered_html,
    validate_secret_boundary_operator_ui_panel_rendered_json,
    validate_secret_boundary_operator_ui_panel_rendered_markdown,
    validate_secret_boundary_operator_ui_panel_risk_limit_summary,
)
from pm_bot.trading_core.risk_limit_control_plane import (
    build_default_risk_limit_policy,
    build_risk_control_plane_summary,
    summarize_risk_limit_decision,
    summarize_risk_limit_policy,
)

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
)

REQUIRED_SECTION_IDS = (
    "header_execution_posture",
    "readiness_evidence_bundle",
    "live_blockers",
    "risk_control_plane",
    "risk_limits",
    "kill_switch",
    "paper_trading_summary",
    "operator_packets",
    "audit_replay",
    "next_gates",
)

NEXT_REQUIRED_GATES = (
    "UI reviewed",
    "risk limit control plane implemented",
    "live connector remains disabled until future gated task",
    "secrets/auth boundary still not configured for live",
    "kill-switch live verification missing",
    "funding not configured",
    "real order adapter disabled",
    "operator live approval not implemented",
    "tiny canary still not executable",
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
    risk_control_plane_summary: Mapping[str, Any]
    risk_limit_summary: Mapping[str, Any]
    kill_switch_summary: Mapping[str, Any]
    paper_summary: Mapping[str, Any]
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
        value["risk_control_plane_summary"] = dict(self.risk_control_plane_summary)
        value["risk_limit_summary"] = dict(self.risk_limit_summary)
        value["kill_switch_summary"] = dict(self.kill_switch_summary)
        value["paper_summary"] = dict(self.paper_summary)
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
        value["paper_summary_panel_ready"] = True
        value["blocker_panel_ready"] = True
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
    readiness = _build_readiness_summary(
        operator_review_ready=operator_packet_summary.get("operator_approval_packet_review_ready") is True,
        evidence_bundle_review_ready=evidence_summary.get("evidence_bundle_review_ready") is True,
    )
    action_states = tuple(_build_action_states())
    sections = _build_sections(
        readiness=readiness,
        evidence=evidence_summary,
        blockers=blocker_summary,
        risk_control=risk_control_summary,
        risk=risk_summary,
        kill_switch=kill_switch_summary,
        paper=paper_summary,
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
            "risk_control": risk_control_summary,
            "risk": risk_summary,
            "kill_switch": kill_switch_summary,
            "paper": paper_summary,
        },
    )
    panel = OperatorUIPanelV1(
        panel_id=panel_id,
        task_id=TASK_ID,
        generated_at=generated_at,
        readiness_summary=readiness,
        evidence_summary=evidence_summary,
        blocker_summary=blocker_summary,
        risk_control_plane_summary=risk_control_summary,
        risk_limit_summary=risk_summary,
        kill_switch_summary=kill_switch_summary,
        paper_summary=paper_summary,
        operator_packet_summary=operator_packet_summary,
        audit_replay_summary=audit_summary,
        next_required_gates=NEXT_REQUIRED_GATES,
        action_states=action_states,
        sections=tuple(sections),
    ).to_dict()
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
        "risk_control_plane_status": dict(panel.get("risk_control_plane_summary", {})).get(
            "risk_control_plane_status"
        ),
        "risk_control_plane_ready": dict(panel.get("risk_control_plane_summary", {})).get(
            "risk_control_plane_ready"
        )
        is True,
        "latest_risk_limit_decision_status": dict(panel.get("risk_control_plane_summary", {})).get(
            "latest_decision_status"
        ),
        "risk_limit_status": "review_config_visibility_only",
        "kill_switch_status": dict(panel.get("kill_switch_summary", {})).get("current_kill_switch_state"),
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
    risk_control: Mapping[str, Any],
    risk: Mapping[str, Any],
    kill_switch: Mapping[str, Any],
    paper: Mapping[str, Any],
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
        "external_api_calls_performed": False,
        "real_wallet_integration_added": False,
        "real_wallet_access_performed": False,
        "private_key_or_mnemonic_handling_added": False,
        "cryptographic_signing_added": False,
        "cryptographic_signing_performed": False,
        "wallet_signing_added": False,
        "wallet_signing_performed": False,
        "transaction_signing_added": False,
        "transaction_signing_performed": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "authenticated_endpoint_added": False,
        "authenticated_endpoint_call_performed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "real_execution_available": False,
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
