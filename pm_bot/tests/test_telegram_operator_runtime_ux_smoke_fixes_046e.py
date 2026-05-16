from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_mini_app_operator_panel import build_telegram_mini_app_panel_artifact_summary

GENERATED_AT = "2026-05-14T00:00:00Z"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_INIT_DATA = "query_id=abc&user={raw-operator}&auth_date=1&hash=raw-init-data-secret"
MINI_APP_URL = "https://example.invalid/pmbot-panel"


def _context() -> dict[str, Any]:
    return {
        "raw_telegram_bot_token": RAW_TOKEN,
        "telegram_init_data": RAW_INIT_DATA,
        "telegram_mini_app_operator_panel_summary": build_telegram_mini_app_panel_artifact_summary(
            latest_panel_html_path="telegram_mini_app_operator_panel_044.html",
            latest_panel_json_path="telegram_mini_app_operator_panel_044.json",
            panel_artifact_available=True,
            generated_at=GENERATED_AT,
        ),
        "tiny_live_canary_gonogo_gate_summary": {
            "status": "NO_GO_UNRESOLVED_BLOCKERS",
            "overall_decision": "NO_GO",
            "unresolved_blocker_count": 2,
            "resolved_blocker_count": 0,
            "allowed_for_live": False,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
            "order_submission_enabled": False,
        },
        "live_connector_blocker_matrix": {
            "unresolved_blocker_count": 2,
            "resolved_blocker_count": 0,
            "blockers": [],
        },
    }


def _adapter(*, mini_app_url: str = "", artifact_dir: Path | None = None) -> runtime.TelegramOperatorRuntimeAdapter:
    return runtime.TelegramOperatorRuntimeAdapter(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            mini_app_url=mini_app_url,
            artifact_dir=artifact_dir,
            generated_at=GENERATED_AT,
        ),
        context=_context(),
    )


def test_runtime_start_language_panel_and_redaction_smoke() -> None:
    adapter = _adapter(mini_app_url=MINI_APP_URL)

    start = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")
    russian = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    panel = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    rendered = json.dumps(panel.to_redacted_dict(), sort_keys=True)

    assert start.text == "Выберите язык"
    assert russian.state["operator_language"] == "ru"
    assert "PMBOT — торговый помощник для Polymarket." in russian.text
    assert "Mini App — расширенная панель PMBOT" in panel.text
    assert panel.panel_button_url == MINI_APP_URL
    assert RAW_TOKEN not in rendered
    assert RAW_INIT_DATA not in rendered
    assert AUTHORIZED_USER_ID not in rendered


def test_runtime_language_command_and_menu_include_language() -> None:
    adapter = _adapter()

    language = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/language")
    menu = runtime.telegram_command_menu_items()

    assert [button.callback_data for button in language.keyboard.rows[0]] == ["pmbot:lang:ru", "pmbot:lang:en"]
    assert ("settings", "Settings") in menu
    assert runtime.is_supported_runtime_command("/language") is True


def test_runtime_panel_missing_url_keeps_local_fallback_review_only() -> None:
    adapter = _adapter()
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    redacted = reply.to_redacted_dict()

    assert "Mini App — расширенная панель PMBOT" in reply.text
    assert reply.panel_button_url == ""
    assert redacted["review_only"] is True
    assert redacted["live_execution_approved"] is False
    assert redacted["order_submission_enabled"] is False
