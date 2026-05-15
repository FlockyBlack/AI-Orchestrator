from __future__ import annotations

import json
from pathlib import Path

from pm_bot.operator_runner.operator_ui_panel_v1 import build_operator_ui_panel_v1
from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.operator_runner.telegram_operator_control_bot import (
    FakeTelegramTransport,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
    build_telegram_operator_control_config,
    build_telegram_operator_control_summary,
)
from pm_bot.operator_runner.telegram_operator_control_state import (
    build_telegram_operator_control_state,
    validate_telegram_operator_control_state,
)
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.secret_boundary_policy import (
    build_secret_boundary_policy,
    validate_secret_boundary_telegram_operator_control_config,
    validate_secret_boundary_telegram_operator_control_state,
    validate_secret_boundary_telegram_operator_control_summary,
)

GENERATED_AT = "2026-05-11T00:00:00Z"
AUTHORIZED_USER_ID = "1001"
UNAUTHORIZED_USER_ID = "9999"

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
    return {
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
            "best_bid": 0.49,
            "best_ask": 0.51,
            "last_price": 0.50,
            "spread": 0.02,
            "liquidity": 1000.0,
            "price_status": "available_from_saved_fixture",
            "risk_control_market_data_status": "fresh_open_btc_market",
            "read_only_network_enabled": False,
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
            "asset": "BTC",
            "side": "BUY",
            "outcome": "UP",
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
            "manual_execution_checklist_count": 5,
            "final_pre_live_checklist_count": 4,
            "no_go_reason_count": 2,
            "top_no_go_reasons": ["live approval missing", "order submission disabled"],
            "unresolved_blocker_count": 2,
            "resolved_blocker_count": 0,
            "explicit_human_approval_required": True,
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
            "evidence_item_count": 21,
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
    }


def _bot(context: dict | None = None) -> TelegramOperatorControlBot:
    return TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=_context() if context is None else context,
        generated_at=GENERATED_AT,
    )


def test_unauthorized_user_is_denied_safely_without_raw_identifier() -> None:
    transport = FakeTelegramTransport()
    bot = TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(allowed_operator_user_ids=(AUTHORIZED_USER_ID,)),
        context=_context(),
        transport=transport,
    )

    response = bot.handle_command(user_id=UNAUTHORIZED_USER_ID, text="/status")

    assert response.authorized is False
    assert "Access denied" in response.text
    assert UNAUTHORIZED_USER_ID not in response.text
    assert "live trading" not in response.text.lower() or "review-only" in response.text.lower()
    assert transport.messages[0]["chat_id_hash"].startswith("telegram-chat-sha256:")
    assert UNAUTHORIZED_USER_ID not in json.dumps(response.to_dict(), sort_keys=True)
    for flag in FORCED_FALSE_FLAGS:
        assert response.to_dict()[flag] is False


def test_authorized_start_and_help_work_and_state_no_execution() -> None:
    bot = _bot()

    start = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/start")
    help_response = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/help")

    assert start.authorized is True
    assert "Выбери язык" in start.text
    assert "🇷🇺 Русский" in [button.label for row in start.keyboard.rows for button in row]
    assert "🇬🇧 English" in [button.label for row in start.keyboard.rows for button in row]
    assert "/status" in help_response.text
    assert "отправка ордеров" in help_response.text
    assert validate_telegram_operator_control_state(help_response.state)["valid"] is True
    for flag in FORCED_FALSE_FLAGS:
        assert help_response.to_dict()[flag] is False


def test_status_reports_review_only_live_blocked_and_gonogo() -> None:
    response = _bot().handle_command(user_id=AUTHORIZED_USER_ID, text="/status")

    assert "🤖 Статус" in response.text
    assert "Режим: review/dry-run" in response.text
    assert "allowed_for_live=false" in response.text
    assert "Live trading: выключен" in response.text
    assert "Отправка ордеров: выключена" in response.text


def test_btc_missing_context_does_not_invent_live_market_data() -> None:
    response = _bot(context={}).handle_command(user_id=AUTHORIZED_USER_ID, text="/btc")

    assert "no saved BTC market snapshot" in response.text
    assert "No live market values are invented" in response.text
    assert "Best bid" not in response.text
    assert response.summary["network_used"] is False


def test_btc_intent_risk_auth_order_gonogo_evidence_and_blockers_commands() -> None:
    bot = _bot()

    btc = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/btc")
    intent = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/intent")
    risk = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/risk")
    auth = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/auth")
    order = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/order")
    gonogo = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/gonogo")
    evidence = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/evidence")
    blockers = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/blockers")

    assert "saved read-only artifact/fixture" in btc.text
    assert "Read-only: true" in btc.text
    assert "dry-run only" in intent.text
    assert "order_intent_is_not_order_submission: true" in intent.text
    assert "Max order: 1" in risk.text
    assert "Max orders/day: 2" in risk.text
    assert "API ключи:" in auth.text
    assert AUTHORIZED_USER_ID not in auth.text
    assert "Значения ключей никогда не показываются." in auth.text
    assert "order_submission_enabled: false" in order.text
    assert "would_submit_order: false" in order.text
    assert "Итог: NO_GO" in gonogo.text
    assert "Решённые блокеры: 0" in gonogo.text
    assert "Evidence items: 21" in evidence.text
    assert "Недостающие evidence: 0" in evidence.text
    assert "Нерешённые блокеры: 2" in blockers.text
    assert "resolved_blocker_count остаётся 0" in blockers.text


def test_pause_and_kill_record_safe_local_markers_only() -> None:
    bot = _bot()

    pause = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/pause")
    kill = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/kill")
    state = kill.state

    assert "локальный маркер Telegram operator-control state" in pause.text
    assert "Live-исполнения здесь нет" in pause.text
    assert "Отмена ордеров" in kill.text
    assert state["operator_pause_requested"] is True
    assert state["operator_kill_switch_requested"] is True
    assert state["does_not_modify_trading_execution"] is True
    assert state["order_submission_enabled"] is False
    assert state["live_execution_approved"] is False
    assert validate_secret_boundary_telegram_operator_control_state(state)["valid"] is True


def test_summary_and_config_redact_telegram_sensitive_config() -> None:
    raw_token = "123456:raw-telegram-token-value"
    config = build_telegram_operator_control_config(
        telegram_bot_configured=True,
        allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
        generated_at=GENERATED_AT,
    )
    state = build_telegram_operator_control_state(generated_at=GENERATED_AT)
    summary = build_telegram_operator_control_summary(
        config=config,
        state=state,
        context=_context(),
        latest_state_path="telegram_operator_control_state_043.json",
        generated_at=GENERATED_AT,
    )
    rendered = json.dumps(summary, sort_keys=True)
    policy = build_secret_boundary_policy()

    assert raw_token not in rendered
    assert AUTHORIZED_USER_ID not in rendered
    assert config["telegram_bot_token_status"] == "configured_redacted"
    assert config["allowed_operator_id_count"] == 1
    assert config["allowed_operator_ids_redacted"] is True
    assert summary["review_only"] is True
    assert summary["execution_enabling"] is False
    assert summary["live_approval"] is False
    assert validate_secret_boundary_telegram_operator_control_config(config)["valid"] is True
    assert validate_secret_boundary_telegram_operator_control_summary(summary)["valid"] is True
    assert "PMBOT_TELEGRAM_BOT_TOKEN" in policy["sensitive_redacted_config_keys"]
    assert "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS" in policy["sensitive_redacted_config_keys"]


def test_operator_ui_panel_includes_telegram_operator_control_passive_section() -> None:
    summary = build_telegram_operator_control_summary(
        config=build_telegram_operator_control_config(allowed_operator_user_ids=(AUTHORIZED_USER_ID,)),
        state=build_telegram_operator_control_state(
            operator_pause_requested=True,
            operator_kill_switch_requested=True,
        ),
        context=_context(),
    )

    panel = build_operator_ui_panel_v1(
        dashboard=_context(),
        telegram_operator_control_bot_summary=summary,
    )
    section_ids = {section["section_id"] for section in panel["sections"]}
    telegram = panel["telegram_operator_control_bot_summary"]

    assert "telegram_operator_control_bot" in section_ids
    assert telegram["telegram_operator_control_bot_section_ready"] is True
    assert telegram["allowed_operator_ids_configured"] is True
    assert telegram["operator_pause_requested"] is True
    assert telegram["operator_kill_switch_requested"] is True
    assert telegram["review_only"] is True
    assert telegram["live_execution_approved"] is False
    assert telegram["order_submission_enabled"] is False


def test_paper_daily_loop_emits_telegram_state_artifact_and_summary(tmp_path: Path) -> None:
    result = run_paper_daily_loop(
        PaperDailyLoopConfig(run_date="2026-05-11", max_markets=6, output_dir=tmp_path)
    )
    state = json.loads((tmp_path / "telegram_operator_control_state_043.json").read_text(encoding="utf-8"))
    dashboard = json.loads((tmp_path / "paper_daily_dashboard.json").read_text(encoding="utf-8"))
    panel = json.loads((tmp_path / "operator_ui_panel_v1.json").read_text(encoding="utf-8"))

    assert result.validation_passed is True
    assert result.telegram_operator_control_state_path.endswith("telegram_operator_control_state_043.json")
    assert state["operator_pause_requested"] is False
    assert state["operator_kill_switch_requested"] is False
    assert state["order_submission_enabled"] is False
    assert dashboard["telegram_operator_control_bot_summary"]["review_only"] is True
    assert dashboard["telegram_operator_control_bot_summary"]["execution_enabling"] is False
    assert panel["telegram_operator_control_bot_summary"]["telegram_operator_control_bot_section_ready"] is True
    assert "Telegram Operator Control Bot" in (tmp_path / "paper_daily_dashboard.md").read_text(encoding="utf-8")


def test_evidence_bundle_includes_telegram_operator_control_review_only_item() -> None:
    telegram_summary = build_telegram_operator_control_summary(
        config=build_telegram_operator_control_config(),
        state=build_telegram_operator_control_state(),
        context=_context(),
    )
    bundle = build_live_canary_readiness_evidence_bundle(
        telegram_operator_control_bot_v1=telegram_summary,
        artifact_reference_overrides={
            "telegram_operator_control_bot_v1": "telegram_operator_control_state_043.json"
        },
    )
    items = {item["evidence_type"]: item for item in bundle["evidence_items"]}
    item = items["telegram_operator_control_bot_v1"]

    assert item["review_only"] is True
    assert item["execution_enabling"] is False
    assert item["live_approval"] is False
    assert item["allowed_for_live"] is False
    assert item["canary_executable_now"] is False
    assert item["order_submission_enabled"] is False
    assert bundle["validation"]["valid"] is True


def test_all_live_execution_flags_remain_false_and_blockers_unresolved() -> None:
    summary = build_telegram_operator_control_summary(
        config=build_telegram_operator_control_config(),
        state=build_telegram_operator_control_state(),
        context=_context(),
    )
    blockers = summary["blocker_summary"]

    for flag in FORCED_FALSE_FLAGS:
        assert summary[flag] is False
    assert summary["live_approval"] is False
    assert summary["execution_enabling"] is False
    assert blockers["resolved_blocker_count"] == 0
    assert blockers["unresolved_blocker_count"] == 2
    assert summary["network_used"] is False
    assert summary["external_api_calls_performed"] is False
