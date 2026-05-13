from __future__ import annotations

import hashlib
import html
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, mapping_rows
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_telegram_mini_app_panel_payload,
    validate_secret_boundary_telegram_mini_app_panel_rendered_html,
    validate_secret_boundary_telegram_mini_app_panel_rendered_json,
)

TELEGRAM_MINI_APP_OPERATOR_PANEL_CONTRACT = "pmbot_telegram_mini_app_operator_panel.v1"
TELEGRAM_MINI_APP_OPERATOR_PANEL_SECTION_CONTRACT = "pmbot_telegram_mini_app_operator_panel_section.v1"
TELEGRAM_MINI_APP_OPERATOR_PANEL_METRIC_CONTRACT = "pmbot_telegram_mini_app_operator_panel_metric.v1"
TELEGRAM_MINI_APP_OPERATOR_PANEL_SUMMARY_CONTRACT = "pmbot_telegram_mini_app_operator_panel_summary.v1"
TELEGRAM_MINI_APP_OPERATOR_PANEL_VALIDATION_CONTRACT = "pmbot_telegram_mini_app_operator_panel_validation.v1"

TASK_ID = "ORCH-PMBOT-TRADING-MVP-044-TELEGRAM-MINI-APP-OPERATOR-PANEL-V1"
PANEL_TITLE = "PMBOT Mini App Operator Panel v1"
PANEL_HTML_ARTIFACT_NAME = "telegram_mini_app_operator_panel_044.html"
PANEL_JSON_ARTIFACT_NAME = "telegram_mini_app_operator_panel_044.json"
MINI_APP_REVIEW_ONLY_NOTICE = (
    "This Telegram Mini App panel is review-only. No live order action is available. "
    "No wallet, signing, authenticated endpoint, or order submission path is enabled."
)

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "would_submit_order",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "wallet_signing_enabled",
    "wallet_enabled",
    "final_live_enablement_present",
    "live_approval",
)

REQUIRED_SECTION_IDS = (
    "header",
    "system_status",
    "btc_market",
    "dry_run_intent",
    "risk_limits",
    "auth_boundary",
    "order_submission_boundary",
    "go_no_go",
    "blockers",
    "evidence",
    "telegram_operator_control",
    "footer",
)


@dataclass(frozen=True)
class TelegramMiniAppPanelMetric:
    metric_id: str
    label: str
    value: Any
    status: str = "review_only"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TELEGRAM_MINI_APP_OPERATOR_PANEL_METRIC_CONTRACT
        return value


@dataclass(frozen=True)
class TelegramMiniAppPanelSection:
    section_id: str
    title: str
    status: str
    metrics: tuple[Mapping[str, Any], ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TELEGRAM_MINI_APP_OPERATOR_PANEL_SECTION_CONTRACT
        value["metrics"] = [dict(row) for row in self.metrics]
        value["warnings"] = list(self.warnings)
        value.update(_mini_app_safety_flags())
        return value


@dataclass(frozen=True)
class TelegramMiniAppPanelModel:
    panel_id: str
    task_id: str
    generated_at: str
    title: str
    decision_status: str
    review_posture: str
    artifact_paths: Mapping[str, str]
    sections: tuple[Mapping[str, Any], ...]
    top_no_go_reasons: tuple[str, ...]
    top_blocker_reasons: tuple[str, ...]
    missing_evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TELEGRAM_MINI_APP_OPERATOR_PANEL_CONTRACT
        value["schema_version"] = "044.v1"
        value["artifact_paths"] = dict(self.artifact_paths)
        value["sections"] = [dict(row) for row in self.sections]
        value["top_no_go_reasons"] = list(self.top_no_go_reasons)
        value["top_blocker_reasons"] = list(self.top_blocker_reasons)
        value["missing_evidence"] = list(self.missing_evidence)
        value["telegram_mini_app_operator_panel_ready"] = True
        value["static_html_render_ready"] = True
        value["json_render_ready"] = True
        value["review_only"] = True
        value["live_blocked"] = True
        value["no_executable_live_action"] = True
        value["mini_app_buttons_disabled_or_local_only"] = True
        value["raw_telegram_bot_token_exposed"] = False
        value["raw_telegram_init_data_exposed"] = False
        value["raw_operator_user_ids_exposed"] = False
        value["resolved_blocker_count"] = 0
        value.update(_mini_app_safety_flags())
        return value


def build_telegram_mini_app_panel_artifact_summary(
    *,
    latest_panel_html_path: str = "",
    latest_panel_json_path: str = "",
    panel_artifact_available: bool | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    html_path = clean_text(latest_panel_html_path)
    json_path = clean_text(latest_panel_json_path)
    available = bool(panel_artifact_available) if panel_artifact_available is not None else bool(html_path or json_path)
    summary = {
        "contract_version": TELEGRAM_MINI_APP_OPERATOR_PANEL_SUMMARY_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "telegram_mini_app_operator_panel_ready": available,
        "panel_artifact_available": available,
        "review_only": True,
        "live_actions_available": False,
        "execution_enabling": False,
        "live_approval": False,
        "latest_telegram_mini_app_operator_panel_html_path": html_path,
        "latest_telegram_mini_app_operator_panel_json_path": json_path,
        "mini_app_url_status": "not_configured_review_placeholder",
        "telegram_init_data_status": "not_configured_redacted",
        "raw_telegram_init_data_exposed": False,
        "raw_telegram_bot_token_exposed": False,
        "raw_operator_user_ids_exposed": False,
    }
    summary.update(_mini_app_safety_flags())
    return summary


def build_telegram_mini_app_panel_model(
    *,
    dashboard: Mapping[str, Any] | None = None,
    operator_ui_panel: Mapping[str, Any] | None = None,
    btc_market_summary: Mapping[str, Any] | None = None,
    btc_analysis_order_intent_summary: Mapping[str, Any] | None = None,
    risk_control_plane_summary: Mapping[str, Any] | None = None,
    risk_limit_summary: Mapping[str, Any] | None = None,
    live_credentials_auth_boundary_summary: Mapping[str, Any] | None = None,
    live_order_submission_boundary_summary: Mapping[str, Any] | None = None,
    tiny_live_canary_gonogo_gate_summary: Mapping[str, Any] | None = None,
    blocker_summary: Mapping[str, Any] | None = None,
    readiness_evidence_bundle_summary: Mapping[str, Any] | None = None,
    telegram_operator_control_summary: Mapping[str, Any] | None = None,
    latest_panel_html_path: str = "",
    latest_panel_json_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    dashboard_value = dict(dashboard or {})
    operator_panel_value = dict(operator_ui_panel or {})
    btc_market = _first_mapping(
        btc_market_summary,
        operator_panel_value.get("btc_market_summary"),
        dashboard_value.get("btc_market_snapshot_summary"),
        dashboard_value.get("btc_market_section_feed"),
    )
    intent = _first_mapping(
        btc_analysis_order_intent_summary,
        operator_panel_value.get("btc_analysis_order_intent_summary"),
        dashboard_value.get("btc_analysis_order_intent_summary"),
        dashboard_value.get("btc_order_intent_dry_run_summary"),
    )
    risk_control = _first_mapping(
        risk_control_plane_summary,
        operator_panel_value.get("risk_control_plane_summary"),
        dashboard_value.get("risk_control_plane_summary"),
        dashboard_value.get("default_risk_limit_policy_summary"),
    )
    risk_limits = _first_mapping(
        risk_limit_summary,
        operator_panel_value.get("risk_limit_summary"),
        dashboard_value.get("default_risk_limit_policy_summary"),
        dashboard_value.get("risk_limit_policy"),
    )
    auth = _first_mapping(
        live_credentials_auth_boundary_summary,
        operator_panel_value.get("live_credentials_auth_boundary_summary"),
        dashboard_value.get("live_credentials_auth_boundary_summary"),
        dashboard_value.get("live_credentials_auth_boundary_section_feed"),
    )
    order = _first_mapping(
        live_order_submission_boundary_summary,
        operator_panel_value.get("live_order_submission_boundary_summary"),
        dashboard_value.get("live_order_submission_boundary_summary"),
        dashboard_value.get("live_order_submission_boundary_section_feed"),
    )
    gonogo = _first_mapping(
        tiny_live_canary_gonogo_gate_summary,
        operator_panel_value.get("tiny_live_canary_gonogo_gate_summary"),
        dashboard_value.get("tiny_live_canary_gonogo_gate_summary"),
    )
    blockers = _normalize_blockers(
        _first_mapping(
            blocker_summary,
            operator_panel_value.get("blocker_summary"),
            dashboard_value.get("live_connector_blocker_matrix"),
            dashboard_value.get("live_canary_readiness_summary"),
        )
    )
    evidence = _first_mapping(
        readiness_evidence_bundle_summary,
        operator_panel_value.get("evidence_summary"),
        dashboard_value.get("readiness_evidence_bundle_summary"),
        dashboard_value.get("readiness_evidence_bundle"),
    )
    telegram = _first_mapping(
        telegram_operator_control_summary,
        operator_panel_value.get("telegram_operator_control_bot_summary"),
        dashboard_value.get("telegram_operator_control_bot_summary"),
    )

    decision_status = clean_text(gonogo.get("overall_decision") or gonogo.get("status") or "NO_GO")
    no_go_reasons = tuple(_clean_list(gonogo.get("top_no_go_reasons"))[:5])
    blocker_reasons = tuple(_top_blocker_reasons(blockers)[:5])
    missing_evidence = tuple(_clean_list(evidence.get("missing_required_evidence"))[:5])

    sections = (
        _section(
            "header",
            "Header",
            "review_only_live_blocked",
            [
                _metric("title", "Panel", PANEL_TITLE),
                _metric("review_only", "Review-only", True),
                _metric("live_blocked", "Live blocked", True),
                _metric("current_decision", "Current decision/status", decision_status),
            ],
            ("No live execution control is exposed by this panel.",),
        ),
        _section(
            "system_status",
            "System Status",
            "all_execution_flags_false",
            [_metric(field, field, False) for field in (
                "allowed_for_live",
                "canary_executable_now",
                "live_execution_approved",
                "real_execution_available",
                "live_connector_enabled",
                "order_submission_enabled",
            )],
        ),
        _section(
            "btc_market",
            "BTC Market",
            "read_only_saved_artifact",
            [
                _metric("market_id", "Market ID", btc_market.get("market_id") or "not_available"),
                _metric("market_slug", "Market slug", btc_market.get("market_slug") or "not_available"),
                _metric("market_status", "Open/fresh status", _btc_status_text(btc_market)),
                _metric("source_marker", "Read-only source marker", _btc_source_marker(btc_market)),
                _metric("no_invented_live_values", "No invented live values", True),
            ],
        ),
        _section(
            "dry_run_intent",
            "Dry-Run Intent",
            "dry_run_only",
            [
                _metric("dry_run_only", "Dry-run only", True),
                _metric("intent_status", "Intent status", intent.get("dry_run_order_intent_status") or intent.get("btc_intent_candidate_status") or "not_available"),
                _metric("intent_market", "Intent market", intent.get("intent_market_slug") or intent.get("intent_market_id") or "not_available"),
                _metric("intent_notional_usd", "Intent notional USD", _display_value(intent.get("intent_notional_usd"))),
                _metric("risk_decision_status", "Risk decision", intent.get("risk_decision_status") or "not_available"),
                _metric("not_order_submission", "Not order submission", True),
            ],
        ),
        _section(
            "risk_limits",
            "Risk Limits",
            "review_visibility_only",
            [
                _metric("max_order_notional_usd", "Max order notional", _first_value(risk_control, risk_limits, "max_order_notional_usd")),
                _metric("max_daily_loss_usd", "Daily loss cap", _first_value(risk_control, risk_limits, "max_daily_loss_usd")),
                _metric("max_total_exposure_usd", "Exposure cap", _first_value(risk_control, risk_limits, "max_total_exposure_usd")),
                _metric("max_active_markets", "Active market limit", _first_value(risk_control, risk_limits, "max_active_markets", "max_market_count")),
                _metric("max_trades_per_day", "Max dry-run intents/day", _first_value(risk_control, risk_limits, "max_trades_per_day", "max_order_count")),
                _metric("allowed_for_live", "Allowed for live", False),
            ],
        ),
        _section(
            "auth_boundary",
            "Auth Boundary",
            "redacted_missing_only",
            [
                _metric("live_credentials_configured", "Live credentials", _configured_or_missing(auth.get("live_credentials_configured"))),
                _metric("credential_statuses", "Credential statuses", "missing/configured:redacted only"),
                _metric("telegram_init_data_status", "Telegram init data", "not_configured_redacted"),
                _metric("authenticated_endpoints_enabled", "Authenticated endpoints disabled", False),
                _metric("raw_secrets_exposed", "Raw secrets exposed", False),
            ],
        ),
        _section(
            "order_submission_boundary",
            "Order Submission Boundary",
            "disabled",
            [
                _metric("would_submit_order", "Would submit order", False),
                _metric("order_submission_enabled", "Order submission enabled", False),
                _metric("signing_enabled", "Signing enabled", False),
                _metric("wallet_enabled", "Wallet enabled", False),
                _metric("boundary_status", "Boundary status", order.get("status") or "not_available"),
            ],
        ),
        _section(
            "go_no_go",
            "Go/No-Go",
            "no_go",
            [
                _metric("gate_decision", "042 gate decision", decision_status),
                _metric("explicit_human_approval_required", "Explicit human approval required", gonogo.get("explicit_human_approval_required") is not False),
                _metric("final_live_enablement_present", "Final live enablement present", False),
                _metric("canary_executable_now", "Canary executable now", False),
                _metric("live_execution_approved", "Live execution approved", False),
            ],
            no_go_reasons or ("Live blockers remain unresolved.",),
        ),
        _section(
            "blockers",
            "Blockers",
            "unresolved",
            [
                _metric("resolved_blocker_count", "Resolved blocker count", 0),
                _metric("unresolved_blocker_count", "Unresolved blocker count", blockers.get("unresolved_blocker_count")),
                _metric("live_blockers_unresolved", "Live blockers unresolved", True),
            ],
            blocker_reasons or ("Live execution remains blocked by unresolved safety gates.",),
        ),
        _section(
            "evidence",
            "Evidence",
            "review_only",
            [
                _metric("evidence_item_count", "Readiness evidence items", _int_or_zero(evidence.get("evidence_item_count"))),
                _metric("missing_required_evidence_count", "Missing evidence", _int_or_zero(evidence.get("missing_required_evidence_count"))),
                _metric("review_only_indicator", "Review-only indicators", True),
                _metric("not_live_approval", "Evidence is not live approval", True),
            ],
            missing_evidence,
        ),
        _section(
            "telegram_operator_control",
            "Telegram Operator Control",
            "local_state_markers_only",
            [
                _metric("telegram_bot_token_status", "Telegram token", _telegram_token_status(telegram)),
                _metric("allowed_operator_ids_configured", "Allowed operator configured", telegram.get("allowed_operator_ids_configured") is True),
                _metric("operator_pause_requested", "Pause requested", telegram.get("operator_pause_requested") is True),
                _metric("operator_kill_switch_requested", "Kill-switch requested", telegram.get("operator_kill_switch_requested") is True),
                _metric("local_markers_only", "Pause/kill local markers only", True),
            ],
            ("Pause and kill states do not modify execution, orders, wallets, or endpoints.",),
        ),
        _section(
            "footer",
            "Footer",
            "review_only_no_live_actions",
            [
                _metric("review_only_notice", "Notice", MINI_APP_REVIEW_ONLY_NOTICE),
                _metric("live_actions_available", "Live actions available", False),
                _metric("wallet_signing_order_submission_enabled", "Wallet/signing/order submission enabled", False),
            ],
        ),
    )
    artifact_summary = build_telegram_mini_app_panel_artifact_summary(
        latest_panel_html_path=latest_panel_html_path,
        latest_panel_json_path=latest_panel_json_path,
        panel_artifact_available=None,
        generated_at=generated_at,
    )
    panel_id = _stable_id(
        "telegram-mini-app-operator-panel-044",
        {
            "decision_status": decision_status,
            "sections": [section.get("section_id") for section in sections],
            "btc_market": {
                "market_id": btc_market.get("market_id"),
                "market_slug": btc_market.get("market_slug"),
                "market_status": btc_market.get("market_status"),
            },
            "blockers": blockers,
            "telegram": {
                "configured": telegram.get("configured"),
                "allowed": telegram.get("allowed_operator_ids_configured"),
                "pause": telegram.get("operator_pause_requested"),
                "kill": telegram.get("operator_kill_switch_requested"),
            },
            "artifact_paths": artifact_summary,
        },
    )
    model = TelegramMiniAppPanelModel(
        panel_id=panel_id,
        task_id=TASK_ID,
        generated_at=generated_at,
        title=PANEL_TITLE,
        decision_status=decision_status,
        review_posture="review_only_live_blocked_static_telegram_mini_app",
        artifact_paths={
            "html": clean_text(latest_panel_html_path),
            "json": clean_text(latest_panel_json_path),
        },
        sections=sections,
        top_no_go_reasons=no_go_reasons,
        top_blocker_reasons=blocker_reasons,
        missing_evidence=missing_evidence,
    ).to_dict()
    for key, value in artifact_summary.items():
        if key not in {"contract_version", "task_id", "generated_at"}:
            model[key] = value
    model["telegram_mini_app_operator_panel_ready"] = True
    model["validation"] = validate_telegram_mini_app_panel_model(model, generated_at=generated_at)
    return model


def render_telegram_mini_app_panel_json(model: Mapping[str, Any], *, include_validation: bool = True) -> str:
    value = dict(model)
    if not include_validation:
        value.pop("validation", None)
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def render_telegram_mini_app_panel_html(model: Mapping[str, Any]) -> str:
    sections = []
    for section in mapping_rows(model.get("sections")):
        metrics = "".join(
            "<div class=\"metric\">"
            f"<span>{html.escape(clean_text(metric.get('label')))}</span>"
            f"<strong>{html.escape(_display_value(metric.get('value')))}</strong>"
            "</div>"
            for metric in mapping_rows(section.get("metrics"))
        )
        warnings = "".join(
            f"<li>{html.escape(clean_text(item))}</li>"
            for item in _clean_list(section.get("warnings"))
        )
        sections.append(
            "<section class=\"panel-card\">"
            f"<div class=\"card-heading\"><h2>{html.escape(clean_text(section.get('title')))}</h2>"
            f"<span>{html.escape(clean_text(section.get('status')))}</span></div>"
            f"{metrics}"
            + (f"<ul class=\"warnings\">{warnings}</ul>" if warnings else "")
            + "</section>"
        )
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"  <title>{html.escape(PANEL_TITLE)}</title>\n"
        "  <style>\n"
        "    :root { color-scheme: light; font-family: Arial, Helvetica, sans-serif; }\n"
        "    * { box-sizing: border-box; }\n"
        "    body { margin: 0; background: #f4f7f6; color: #18232e; }\n"
        "    header { padding: 20px 16px 14px; background: #12343b; color: #ffffff; }\n"
        "    header h1 { margin: 0 0 8px; font-size: 1.35rem; line-height: 1.2; letter-spacing: 0; }\n"
        "    header p { margin: 4px 0; color: #d8f0ee; }\n"
        "    main { width: min(100%, 920px); margin: 0 auto; padding: 14px; }\n"
        "    .status-strip { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 0 0 12px; }\n"
        "    .pill { border: 1px solid #c8d7d3; background: #ffffff; border-radius: 8px; padding: 10px; font-weight: 700; color: #12343b; }\n"
        "    .pill.blocked { color: #9b2c2c; border-color: #e4b5b5; }\n"
        "    .panel-card { background: #ffffff; border: 1px solid #d8e2df; border-radius: 8px; margin: 0 0 12px; padding: 14px; box-shadow: 0 1px 2px rgba(18,52,59,0.05); }\n"
        "    .card-heading { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 8px; }\n"
        "    .card-heading h2 { margin: 0; font-size: 1rem; line-height: 1.25; letter-spacing: 0; }\n"
        "    .card-heading span { color: #576b74; font-size: 0.78rem; text-align: right; overflow-wrap: anywhere; }\n"
        "    .metric { display: grid; grid-template-columns: minmax(120px, 44%) 1fr; gap: 10px; border-top: 1px solid #edf2f1; padding: 9px 0; }\n"
        "    .metric span { color: #576b74; overflow-wrap: anywhere; }\n"
        "    .metric strong { color: #18232e; font-weight: 700; overflow-wrap: anywhere; }\n"
        "    .warnings { margin: 8px 0 0 18px; padding: 0; color: #8a4b12; }\n"
        "    .static-actions { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }\n"
        "    button { border: 1px solid #c8d7d3; background: #e9efed; color: #576b74; border-radius: 8px; padding: 9px 11px; }\n"
        "    footer { padding: 16px; color: #41545d; font-size: 0.9rem; }\n"
        "    @media (max-width: 560px) { .status-strip { grid-template-columns: 1fr; } .metric { grid-template-columns: 1fr; gap: 3px; } }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <header>\n"
        f"    <h1>{html.escape(PANEL_TITLE)}</h1>\n"
        "    <p>review-only</p>\n"
        "    <p>live blocked</p>\n"
        f"    <p>Current decision/status: {html.escape(clean_text(model.get('decision_status') or 'NO_GO'))}</p>\n"
        "  </header>\n"
        "  <main>\n"
        "    <div class=\"status-strip\"><div class=\"pill\">Static local artifact</div><div class=\"pill blocked\">No live order action</div></div>\n"
        "    <div class=\"static-actions\"><button type=\"button\" disabled>Refresh status unavailable</button><button type=\"button\" disabled>Evidence view local-only</button></div>\n"
        + "\n".join(sections)
        + "  </main>\n"
        f"  <footer>{html.escape(MINI_APP_REVIEW_ONLY_NOTICE)}</footer>\n"
        "</body>\n"
        "</html>\n"
    )


def summarize_telegram_mini_app_panel_model(model: Mapping[str, Any]) -> dict[str, Any]:
    validation = dict(model.get("validation", {}))
    summary = {
        "contract_version": TELEGRAM_MINI_APP_OPERATOR_PANEL_SUMMARY_CONTRACT,
        "task_id": TASK_ID,
        "panel_id": clean_text(model.get("panel_id")),
        "generated_at": clean_text(model.get("generated_at")) or GENERATED_AT,
        "telegram_mini_app_operator_panel_ready": model.get("telegram_mini_app_operator_panel_ready") is True,
        "panel_artifact_available": bool(dict(model.get("artifact_paths", {})).get("html") or dict(model.get("artifact_paths", {})).get("json")),
        "review_only": True,
        "live_actions_available": False,
        "execution_enabling": False,
        "live_approval": False,
        "decision_status": clean_text(model.get("decision_status") or "NO_GO"),
        "validation_status": clean_text(validation.get("status") or "not_validated"),
        "validation_error_count": len(validation.get("errors", [])),
        "section_count": len(mapping_rows(model.get("sections"))),
        "latest_telegram_mini_app_operator_panel_html_path": clean_text(dict(model.get("artifact_paths", {})).get("html")),
        "latest_telegram_mini_app_operator_panel_json_path": clean_text(dict(model.get("artifact_paths", {})).get("json")),
        "mini_app_url_status": clean_text(model.get("mini_app_url_status")) or "not_configured_review_placeholder",
        "telegram_init_data_status": clean_text(model.get("telegram_init_data_status")) or "not_configured_redacted",
        "raw_telegram_init_data_exposed": False,
        "raw_telegram_bot_token_exposed": False,
        "raw_operator_user_ids_exposed": False,
        "resolved_blocker_count": 0,
    }
    summary.update(_mini_app_safety_flags())
    return summary


def validate_telegram_mini_app_panel_model(
    model: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    statuses: list[str] = []
    value = dict(model)
    if value.get("contract_version") != TELEGRAM_MINI_APP_OPERATOR_PANEL_CONTRACT:
        errors.append(f"contract_version must be {TELEGRAM_MINI_APP_OPERATOR_PANEL_CONTRACT}")
    section_ids = [clean_text(section.get("section_id")) for section in mapping_rows(value.get("sections"))]
    for section_id in REQUIRED_SECTION_IDS:
        if section_id not in section_ids:
            errors.append(f"missing required section {section_id}")
            statuses.append("missing_required_section")
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
    if value.get("live_blocked") is not True:
        errors.append("live_blocked must be true")
    if value.get("no_executable_live_action") is not True:
        errors.append("no_executable_live_action must be true")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("execution_flag_detected")
    if _section_metric_value(value, "blockers", "resolved_blocker_count") not in (0, "0"):
        errors.append("blockers.resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")
    order_metrics = {
        metric.get("metric_id"): metric.get("value")
        for section in mapping_rows(value.get("sections"))
        if section.get("section_id") == "order_submission_boundary"
        for metric in mapping_rows(section.get("metrics"))
    }
    for metric_id in ("would_submit_order", "order_submission_enabled", "signing_enabled", "wallet_enabled"):
        if order_metrics.get(metric_id) is not False:
            errors.append(f"order_submission_boundary.{metric_id} must be false")
            statuses.append("order_boundary_execution_flag_detected")
    if value.get("raw_telegram_bot_token_exposed") is not False:
        errors.append("raw_telegram_bot_token_exposed must be false")
    if value.get("raw_telegram_init_data_exposed") is not False:
        errors.append("raw_telegram_init_data_exposed must be false")
    if value.get("raw_operator_user_ids_exposed") is not False:
        errors.append("raw_operator_user_ids_exposed must be false")

    payload_validation = validate_secret_boundary_telegram_mini_app_panel_payload(
        value,
        generated_at=generated_at,
    )
    rendered_json_validation = validate_secret_boundary_telegram_mini_app_panel_rendered_json(
        render_telegram_mini_app_panel_json(value, include_validation=False),
        generated_at=generated_at,
    )
    rendered_html_validation = validate_secret_boundary_telegram_mini_app_panel_rendered_html(
        render_telegram_mini_app_panel_html(value),
        generated_at=generated_at,
    )
    for label, validation in (
        ("payload", payload_validation),
        ("rendered_json", rendered_json_validation),
        ("rendered_html", rendered_html_validation),
    ):
        if validation.get("valid") is not True:
            errors.append(f"{label} violates static secret boundary")
            statuses.append(f"{label}_secret_boundary_blocked")
    valid = not errors
    return {
        "contract_version": TELEGRAM_MINI_APP_OPERATOR_PANEL_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "telegram-mini-app-operator-panel-validation-044",
            {"panel_id": value.get("panel_id"), "errors": errors, "statuses": statuses},
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": _dedupe(statuses) or (["telegram_mini_app_operator_panel_valid"] if valid else ["telegram_mini_app_operator_panel_blocked"]),
        "errors": errors,
        "payload_secret_boundary_validation": payload_validation,
        "rendered_json_secret_boundary_validation": rendered_json_validation,
        "rendered_html_secret_boundary_validation": rendered_html_validation,
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
    }


def _section(
    section_id: str,
    title: str,
    status: str,
    metrics: Sequence[Mapping[str, Any]],
    warnings: Sequence[str] = (),
) -> dict[str, Any]:
    return TelegramMiniAppPanelSection(
        section_id=section_id,
        title=title,
        status=status,
        metrics=tuple(metrics),
        warnings=tuple(clean_text(item) for item in warnings if clean_text(item)),
    ).to_dict()


def _metric(metric_id: str, label: str, value: Any, *, status: str = "review_only", notes: str = "") -> dict[str, Any]:
    return TelegramMiniAppPanelMetric(
        metric_id=metric_id,
        label=label,
        value=value,
        status=status,
        notes=notes,
    ).to_dict()


def _mini_app_safety_flags() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "execution_enabling": False,
        "live_approval": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "wallet_enabled": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "would_submit_order": False,
        "order_submission_enabled": False,
        "real_order_submitted": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "final_live_enablement_present": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "browser_automation_added": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping) and value:
            return dict(value)
    return {}


def _normalize_blockers(blockers: Mapping[str, Any]) -> dict[str, Any]:
    rows = [dict(row) for row in mapping_rows(blockers.get("blockers") or blockers.get("top_blockers"))]
    unresolved = [row for row in rows if clean_text(row.get("resolution_status")) != "resolved"]
    resolved = [row for row in rows if clean_text(row.get("resolution_status")) == "resolved"]
    unresolved_count = _int_or_zero(
        blockers.get("unresolved_blocker_count"),
        blockers.get("unresolved_blockers"),
        blockers.get("unresolved_live_blocker_count"),
        blockers.get("unresolved_live_connector_blocker_count"),
        len(unresolved),
    )
    resolved_count = _int_or_zero(
        blockers.get("resolved_blocker_count"),
        blockers.get("resolved_blockers"),
        blockers.get("resolved_live_blocker_count"),
        blockers.get("resolved_live_connector_blocker_count"),
        len(resolved),
    )
    return dict(blockers) | {
        "unresolved_blocker_count": unresolved_count,
        "resolved_blocker_count": resolved_count,
        "top_blocker_reasons": _top_blocker_reasons(blockers),
    }


def _top_blocker_reasons(blockers: Mapping[str, Any]) -> list[str]:
    direct = _clean_list(blockers.get("top_blocker_reasons") or blockers.get("why_live_execution_is_blocked"))
    if direct:
        return direct
    rows = [dict(row) for row in mapping_rows(blockers.get("top_blockers") or blockers.get("blockers"))]
    return _clean_list(
        row.get("reason") or row.get("why_it_blocks_live_execution") or row.get("blocker_name") or row.get("message")
        for row in rows
    )


def _clean_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values] if clean_text(values) else []
    try:
        return [clean_text(item) for item in values if clean_text(item)]
    except TypeError:
        return []


def _int_or_zero(*values: Any) -> int:
    for value in values:
        if isinstance(value, bool) or value is None or value == "":
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _display_value(value: Any) -> str:
    if value is None or value == "":
        return "not_available"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, tuple)):
        return ", ".join(_display_value(item) for item in value) if value else "none"
    if isinstance(value, Mapping):
        return json.dumps(dict(value), sort_keys=True)
    return clean_text(value)


def _first_value(primary: Mapping[str, Any], secondary: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if primary.get(key) not in (None, ""):
            return primary.get(key)
        if secondary.get(key) not in (None, ""):
            return secondary.get(key)
    return "not_available"


def _configured_or_missing(value: Any) -> str:
    return "configured:redacted" if value is True else "missing"


def _telegram_token_status(telegram: Mapping[str, Any]) -> str:
    config = dict(telegram.get("config", {})) if isinstance(telegram.get("config"), Mapping) else {}
    return clean_text(
        telegram.get("telegram_bot_token_status")
        or config.get("telegram_bot_token_status")
        or "missing"
    )


def _btc_status_text(btc_market: Mapping[str, Any]) -> str:
    status = clean_text(btc_market.get("risk_control_market_data_status") or btc_market.get("market_status"))
    if status:
        return status
    open_text = "open" if btc_market.get("is_open") is True else "open status not_available"
    stale_text = "stale" if btc_market.get("stale") is True else "fresh status not_available"
    return f"{open_text}; {stale_text}"


def _btc_source_marker(btc_market: Mapping[str, Any]) -> str:
    if clean_text(btc_market.get("latest_btc_market_snapshot_path")):
        return clean_text(btc_market.get("latest_btc_market_snapshot_path"))
    if clean_text(btc_market.get("btc_market_connector_status")):
        return clean_text(btc_market.get("btc_market_connector_status"))
    return "saved_fixture_or_local_artifact"


def _section_metric_value(model: Mapping[str, Any], section_id: str, metric_id: str) -> Any:
    for section in mapping_rows(model.get("sections")):
        if clean_text(section.get("section_id")) != section_id:
            continue
        for metric in mapping_rows(section.get("metrics")):
            if clean_text(metric.get("metric_id")) == metric_id:
                return metric.get("value")
    return None


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
