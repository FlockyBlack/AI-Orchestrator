from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.operator_runner.telegram_mini_app_operator_panel import (
    REQUIRED_SECTION_IDS,
    build_telegram_mini_app_panel_artifact_summary,
    build_telegram_mini_app_panel_model,
    render_telegram_mini_app_panel_html,
    render_telegram_mini_app_panel_json,
    summarize_telegram_mini_app_panel_model,
    validate_telegram_mini_app_panel_model,
)
from pm_bot.operator_runner.telegram_operator_control_bot import (
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
    build_telegram_operator_control_config,
    build_telegram_operator_control_summary,
)
from pm_bot.operator_runner.telegram_operator_control_state import build_telegram_operator_control_state
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.secret_boundary_policy import (
    build_secret_boundary_policy,
    validate_secret_boundary_telegram_mini_app_panel_payload,
    validate_secret_boundary_telegram_mini_app_panel_rendered_html,
    validate_secret_boundary_telegram_mini_app_panel_rendered_json,
)

GENERATED_AT = "2026-05-11T00:00:00Z"
AUTHORIZED_USER_ID = "1001"
RAW_TELEGRAM_TOKEN = "123456:raw-telegram-token-value"
RAW_INIT_DATA = "query_id=abc&user={raw-operator}&auth_date=1&hash=raw-init-data-secret"
RAW_SECRET = "sk-proj-raw-secret-value"
RAW_PRIVATE_KEY = "0x" + "a" * 64

FORCED_FALSE_FLAGS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "would_submit_order",
)


def _context() -> dict:
    mini_summary = build_telegram_mini_app_panel_artifact_summary(
        latest_panel_html_path="telegram_mini_app_operator_panel_044.html",
        latest_panel_json_path="telegram_mini_app_operator_panel_044.json",
        panel_artifact_available=True,
        generated_at=GENERATED_AT,
    )
    return {
        "raw_telegram_bot_token": RAW_TELEGRAM_TOKEN,
        "telegram_init_data": RAW_INIT_DATA,
        "private_key": RAW_PRIVATE_KEY,
        "auth_token": RAW_SECRET,
        "btc_market_snapshot_summary": {
            "btc_market_connector_status": "fixture_snapshot_validated_read_only",
            "market_id": "btc-canary-fixture",
            "market_slug": "btc-updown-may-2026",
            "market_title": "BTC Up/Down May 2026 fixture",
            "is_btc_related": True,
            "market_status": "open",
            "is_open": True,
            "is_resolved": False,
            "stale": False,
            "snapshot_age_seconds": 0,
            "price_status": "available_from_saved_fixture",
            "risk_control_market_data_status": "fresh_open_btc_market",
            "read_only_network_enabled": False,
            "latest_btc_market_snapshot_path": "btc_market_snapshot_038.json",
        },
        "btc_analysis_order_intent_summary": {
            "btc_market_analysis_status": "analysis_ready_for_dry_run_intent",
            "btc_intent_candidate_status": "dry_run_intent_candidate_ready",
            "dry_run_order_intent_status": "dry_run_intent_candidate_ready",
            "intent_market_id": "btc-canary-fixture",
            "intent_market_slug": "btc-updown-may-2026",
            "intent_notional_usd": 1.0,
            "intent_limit_price": 0.51,
            "risk_decision_status": "ALLOW_DRY_RUN",
            "allowed_for_dry_run": True,
            "allowed_for_live": False,
            "analysis_is_not_live_recommendation": True,
            "order_intent_is_not_order_submission": True,
        },
        "risk_control_plane_summary": {
            "risk_control_plane_status": "review_ready",
            "policy_id": "risk-limit-policy-037",
            "mode": "paper_dry_run",
            "max_daily_loss_usd": 5,
            "max_total_exposure_usd": 25,
            "max_market_exposure_usd": 2,
            "max_order_notional_usd": 1,
            "max_active_markets": 3,
            "max_trades_per_day": 2,
            "allowed_for_dry_run": True,
            "allowed_for_live": False,
        },
        "live_credentials_auth_boundary_summary": {
            "live_credentials_boundary_status": "review_only_execution_disabled",
            "live_credentials_configured": False,
            "required_credentials_count": 3,
            "missing_credentials_count": 3,
            "credential_statuses_redacted": [],
            "redacted_credential_status_ready": True,
            "secrets_redacted": True,
            "actual_secret_values_exposed": False,
            "authenticated_endpoints_enabled": False,
            "signing_enabled": False,
            "wallet_signing_enabled": False,
            "order_submission_enabled": False,
            "allowed_for_live": False,
        },
        "live_order_submission_boundary_summary": {
            "boundary_name": "live_order_submission_boundary",
            "status": "dry_run_submission_boundary_review_ready",
            "dry_run_review_ready": True,
            "market_id": "btc-canary-fixture",
            "market_slug": "btc-updown-may-2026",
            "top_refusal_reasons": ["order submission disabled"],
            "top_blocker_reasons": ["authenticated endpoint disabled"],
            "would_submit_order": False,
            "order_submission_enabled": False,
            "authenticated_endpoint_enabled": False,
            "signing_enabled": False,
            "wallet_enabled": False,
            "allowed_for_live": False,
        },
        "tiny_live_canary_gonogo_gate_summary": {
            "status": "NO_GO_UNRESOLVED_BLOCKERS",
            "overall_decision": "NO_GO",
            "review_only_status": "review_only_no_go",
            "top_no_go_reasons": ["live approval missing", "order submission disabled"],
            "unresolved_blocker_count": 2,
            "resolved_blocker_count": 0,
            "explicit_human_approval_required": True,
            "final_live_enablement_present": False,
            "no_executable_action": True,
            "allowed_for_live": False,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
            "order_submission_enabled": False,
        },
        "readiness_evidence_bundle_summary": {
            "readiness_evidence_bundle_status": "readiness_evidence_bundle_review_ready",
            "readiness_evidence_bundle_review_ready": True,
            "readiness_evidence_bundle_is_not_live_approval": True,
            "evidence_item_count": 22,
            "missing_required_evidence_count": 0,
            "missing_required_evidence": [],
            "unresolved_live_blocker_count": 2,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
        },
        "live_connector_blocker_matrix": {
            "status": "passed",
            "unresolved_blocker_count": 2,
            "resolved_blocker_count": 0,
            "all_blockers_unresolved": True,
            "blockers": [
                {
                    "blocker_id": "B1",
                    "severity": "critical",
                    "resolution_status": "unresolved",
                    "why_it_blocks_live_execution": "No live approval exists.",
                },
                {
                    "blocker_id": "B2",
                    "severity": "critical",
                    "resolution_status": "unresolved",
                    "why_it_blocks_live_execution": "Order submission is disabled.",
                },
            ],
        },
        "telegram_mini_app_operator_panel_summary": mini_summary,
    }


def _telegram_summary(*, pause: bool = False, kill: bool = False) -> dict:
    return build_telegram_operator_control_summary(
        config=build_telegram_operator_control_config(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        state=build_telegram_operator_control_state(
            operator_pause_requested=pause,
            operator_kill_switch_requested=kill,
            generated_at=GENERATED_AT,
        ),
        context=_context(),
        latest_state_path="telegram_operator_control_state_043.json",
        generated_at=GENERATED_AT,
    )


def _panel() -> dict:
    return build_telegram_mini_app_panel_model(
        dashboard=_context(),
        telegram_operator_control_summary=_telegram_summary(pause=True, kill=True),
        latest_panel_html_path="telegram_mini_app_operator_panel_044.html",
        latest_panel_json_path="telegram_mini_app_operator_panel_044.json",
        generated_at=GENERATED_AT,
    )


def test_panel_model_includes_required_sections_and_forced_false_statuses() -> None:
    panel = _panel()
    section_ids = {section["section_id"] for section in panel["sections"]}

    assert set(REQUIRED_SECTION_IDS).issubset(section_ids)
    assert panel["validation"]["valid"] is True
    assert validate_telegram_mini_app_panel_model(panel)["valid"] is True
    assert panel["review_only"] is True
    assert panel["live_blocked"] is True
    assert panel["resolved_blocker_count"] == 0
    for flag in FORCED_FALSE_FLAGS:
        assert panel[flag] is False


def test_html_renderer_is_deterministic_review_only_live_blocked_and_secret_safe() -> None:
    panel = _panel()
    html_one = render_telegram_mini_app_panel_html(panel)
    html_two = render_telegram_mini_app_panel_html(deepcopy(panel))
    json_one = render_telegram_mini_app_panel_json(panel)
    json_two = render_telegram_mini_app_panel_json(deepcopy(panel))

    assert html_one == html_two
    assert json_one == json_two
    assert "PMBOT Mini App Operator Panel v1" in html_one
    assert "review-only" in html_one
    assert "live blocked" in html_one
    assert "No live order action" in html_one
    assert "<script" not in html_one.lower()
    assert "https://" not in html_one.lower()
    assert "http://" not in html_one.lower()
    assert ">BUY<" not in html_one
    assert ">SELL<" not in html_one
    assert ">TRADE<" not in html_one
    for sensitive in (RAW_TELEGRAM_TOKEN, RAW_INIT_DATA, RAW_SECRET, RAW_PRIVATE_KEY):
        assert sensitive not in html_one
        assert sensitive not in json_one
    assert validate_secret_boundary_telegram_mini_app_panel_rendered_html(html_one)["valid"] is True
    assert validate_secret_boundary_telegram_mini_app_panel_rendered_json(json_one)["valid"] is True
    assert validate_secret_boundary_telegram_mini_app_panel_payload(panel)["valid"] is True


def test_boundaries_blockers_evidence_and_telegram_markers_are_passive() -> None:
    panel = _panel()
    sections = {section["section_id"]: section for section in panel["sections"]}

    system = {metric["metric_id"]: metric["value"] for metric in sections["system_status"]["metrics"]}
    order = {metric["metric_id"]: metric["value"] for metric in sections["order_submission_boundary"]["metrics"]}
    auth = {metric["metric_id"]: metric["value"] for metric in sections["auth_boundary"]["metrics"]}
    blockers = {metric["metric_id"]: metric["value"] for metric in sections["blockers"]["metrics"]}
    telegram = {metric["metric_id"]: metric["value"] for metric in sections["telegram_operator_control"]["metrics"]}

    assert system["allowed_for_live"] is False
    assert system["canary_executable_now"] is False
    assert system["live_execution_approved"] is False
    assert system["real_execution_available"] is False
    assert system["live_connector_enabled"] is False
    assert system["order_submission_enabled"] is False
    assert order["would_submit_order"] is False
    assert order["order_submission_enabled"] is False
    assert order["signing_enabled"] is False
    assert order["wallet_enabled"] is False
    assert auth["live_credentials_configured"] == "missing"
    assert auth["credential_statuses"] == "missing/configured:redacted only"
    assert auth["authenticated_endpoints_enabled"] is False
    assert blockers["resolved_blocker_count"] == 0
    assert blockers["unresolved_blocker_count"] == 2
    assert telegram["operator_pause_requested"] is True
    assert telegram["operator_kill_switch_requested"] is True
    assert telegram["local_markers_only"] is True


def test_operator_ui_panel_includes_passive_mini_app_section() -> None:
    summary = summarize_telegram_mini_app_panel_model(_panel())
    panel = build_operator_ui_panel_v1(
        dashboard=_context(),
        blocker_matrix=_context()["live_connector_blocker_matrix"],
        telegram_operator_control_bot_summary=_telegram_summary(),
        telegram_mini_app_operator_panel_summary=summary,
        latest_paths={
            "telegram_mini_app_operator_panel_html": "telegram_mini_app_operator_panel_044.html",
            "telegram_mini_app_operator_panel_json": "telegram_mini_app_operator_panel_044.json",
        },
    )
    section_ids = {section["section_id"] for section in panel["sections"]}
    mini = panel["telegram_mini_app_operator_panel_summary"]

    assert "telegram_mini_app_operator_panel" in section_ids
    assert mini["telegram_mini_app_operator_panel_section_ready"] is True
    assert mini["panel_artifact_available"] is True
    assert mini["review_only"] is True
    assert mini["live_actions_available"] is False
    assert mini["execution_enabling"] is False
    assert panel["validation"]["valid"] is True


def test_evidence_bundle_includes_mini_app_review_only_item() -> None:
    summary = summarize_telegram_mini_app_panel_model(_panel())
    bundle = build_live_canary_readiness_evidence_bundle(
        telegram_operator_control_bot_v1=_telegram_summary(),
        telegram_mini_app_operator_panel_v1=summary,
        artifact_reference_overrides={
            "telegram_mini_app_operator_panel_v1": "telegram_mini_app_operator_panel_044.html"
        },
    )
    items = {item["evidence_type"]: item for item in bundle["evidence_items"]}
    item = items["telegram_mini_app_operator_panel_v1"]

    assert item["review_only"] is True
    assert item["execution_enabling"] is False
    assert item["live_approval"] is False
    assert item["allowed_for_live"] is False
    assert item["canary_executable_now"] is False
    assert item["order_submission_enabled"] is False
    assert bundle["validation"]["valid"] is True


def test_telegram_panel_command_returns_safe_artifact_info_without_secrets() -> None:
    summary = summarize_telegram_mini_app_panel_model(_panel())
    context = _context() | {"telegram_mini_app_operator_panel_summary": summary}
    bot = TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=context,
        generated_at=GENERATED_AT,
    )

    response = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/panel")

    assert response.authorized is True
    assert "🌐 Mini App" in response.text
    assert "Mini App — расширенная панель PMBOT" in response.text
    assert RAW_TELEGRAM_TOKEN not in response.text
    assert RAW_INIT_DATA not in response.text
    assert RAW_SECRET not in response.text
    assert response.summary["network_used"] is False


def test_paper_daily_loop_emits_mini_app_html_json_artifacts_without_network(monkeypatch, tmp_path: Path) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    panel = json.loads((tmp_path / "telegram_mini_app_operator_panel_044.json").read_text(encoding="utf-8"))
    html = (tmp_path / "telegram_mini_app_operator_panel_044.html").read_text(encoding="utf-8")
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    operator_ui = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.telegram_mini_app_operator_panel_html_path.endswith("telegram_mini_app_operator_panel_044.html")
    assert result.telegram_mini_app_operator_panel_json_path.endswith("telegram_mini_app_operator_panel_044.json")
    assert panel["telegram_mini_app_operator_panel_ready"] is True
    assert panel["review_only"] is True
    assert panel["live_actions_available"] is False
    assert panel["allowed_for_live"] is False
    assert panel["canary_executable_now"] is False
    assert panel["validation"]["valid"] is True
    assert "review-only" in html
    assert "No live order action" in html
    assert dashboard["telegram_mini_app_operator_panel_summary"]["review_only"] is True
    assert dashboard["telegram_mini_app_operator_panel_summary"]["live_actions_available"] is False
    assert operator_ui["telegram_mini_app_operator_panel_summary"]["live_actions_available"] is False


def test_secret_policy_classifies_telegram_mini_app_sensitive_values() -> None:
    policy = build_secret_boundary_policy()

    assert "PMBOT_TELEGRAM_MINI_APP_URL" in policy["sensitive_redacted_config_keys"]
    assert "PMBOT_TELEGRAM_INIT_DATA" in policy["sensitive_redacted_config_keys"]
    assert validate_secret_boundary_telegram_mini_app_panel_payload(
        {"telegram_init_data": RAW_INIT_DATA}
    )["valid"] is False
