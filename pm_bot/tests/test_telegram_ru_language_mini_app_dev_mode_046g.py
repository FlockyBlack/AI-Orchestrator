from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_mini_app_operator_panel import build_telegram_mini_app_panel_artifact_summary
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    FORBIDDEN_BUTTON_LABEL_TERMS,
)

GENERATED_AT = "2026-05-14T00:00:00Z"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_INIT_DATA = "query_id=abc&user={raw-operator}&auth_date=1&hash=raw-init-data-secret"
MINI_APP_URL = "https://example.invalid/pmbot-panel"

REQUIRED_STABLE_CALLBACKS = {
    "pmbot:connection",
    "pmbot:balance",
    "pmbot:analytics",
    "pmbot:launch",
    "pmbot:panel",
    "pmbot:stop",
    "pmbot:settings",
    "pmbot:lang:ru",
    "pmbot:lang:en",
}

FORCED_FALSE_FLAGS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "would_submit_order",
)


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
            "top_no_go_reasons": ["live approval missing", "order submission disabled"],
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
            "blockers": [
                {
                    "blocker_id": "B1",
                    "resolution_status": "unresolved",
                    "why_it_blocks_live_execution": "No live approval exists.",
                }
            ],
        },
        "risk_control_plane_summary": {
            "max_order_notional_usd": 1,
            "max_daily_loss_usd": 5,
            "max_total_exposure_usd": 25,
            "max_market_exposure_usd": 2,
            "max_active_markets": 3,
            "max_trades_per_day": 2,
            "allowed_for_live": False,
        },
        "readiness_evidence_bundle_summary": {
            "readiness_evidence_bundle_status": "readiness_evidence_bundle_review_ready",
            "evidence_item_count": 22,
            "missing_required_evidence_count": 0,
            "missing_required_evidence": [],
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "live_connector_enabled": False,
        },
    }


def _adapter(
    *,
    mini_app_url: str = "",
    artifact_dir: Path | None = None,
) -> runtime.TelegramOperatorRuntimeAdapter:
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


def _button_labels(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def _callback_data(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.callback_data for row in reply.keyboard.rows for button in row if button.callback_data)


def _select_ru(adapter: runtime.TelegramOperatorRuntimeAdapter) -> runtime.TelegramRuntimeReply:
    return adapter.handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:lang:ru",
    )


def test_start_uses_ru_first_home_when_language_is_not_selected() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")

    assert reply.text == "Выберите язык"
    assert _button_labels(reply) == ("🇷🇺 Русский", "🇬🇧 English")
    assert set(_callback_data(reply)) == {"pmbot:lang:ru", "pmbot:lang:en"}


def test_russian_and_english_language_can_be_selected_via_callback() -> None:
    russian = _adapter().handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:lang:ru",
    )
    english = _adapter().handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:lang:en",
    )

    assert russian.state["operator_language"] == "ru"
    assert "PMBOT — торговый помощник для Polymarket." in russian.text
    assert english.state["operator_language"] == "en"
    assert "PMBOT is a trading assistant for Polymarket." in english.text


def test_language_command_shows_both_language_choices() -> None:
    adapter = _adapter()
    _select_ru(adapter)

    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/language")

    assert reply.text == "Выберите язык"
    assert _button_labels(reply) == ("🇷🇺 Русский", "🇬🇧 English")
    assert _callback_data(reply) == ("pmbot:lang:ru", "pmbot:lang:en")


def test_russian_home_keyboard_uses_expected_labels_and_stable_callbacks() -> None:
    adapter = _adapter()
    _select_ru(adapter)
    reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:home")

    assert "PMBOT\nГлавное меню" in reply.text
    assert _button_labels(reply) == (
        "🔌 Подключение",
        "💰 Баланс",
        "📊 Аналитика",
        "🚀 Запуск",
        "⛔ Остановить",
        "🌐 Mini App",
        "⚙️ Настройки",
    )
    assert set(_callback_data(reply)) == REQUIRED_STABLE_CALLBACKS - {"pmbot:lang:ru", "pmbot:lang:en"}


def test_callback_data_remains_stable_and_language_independent() -> None:
    assert REQUIRED_STABLE_CALLBACKS.issubset(set(CALLBACK_COMMAND_MAP))

    ru_adapter = _adapter()
    _select_ru(ru_adapter)
    ru_home = ru_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:home")
    en_adapter = _adapter()
    en_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    en_home = en_adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:home")
    ru_language = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/language")

    home_callbacks = REQUIRED_STABLE_CALLBACKS - {"pmbot:lang:ru", "pmbot:lang:en"}
    assert set(_callback_data(ru_home)) == home_callbacks
    assert set(_callback_data(en_home)) == home_callbacks
    assert set(_callback_data(ru_language)) == {"pmbot:lang:ru", "pmbot:lang:en"}


def test_panel_with_mini_app_url_includes_safe_russian_button_without_redacted_url_exposure() -> None:
    adapter = _adapter(mini_app_url=MINI_APP_URL)
    _select_ru(adapter)

    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    first_button = reply.keyboard.rows[0][0]
    redacted = json.dumps(reply.to_redacted_dict(), sort_keys=True)

    assert "Mini App — расширенная панель PMBOT" in reply.text
    assert first_button.label == "Открыть Mini App"
    assert first_button.web_app_url == MINI_APP_URL
    assert reply.panel_button_url == MINI_APP_URL
    assert MINI_APP_URL not in redacted
    assert RAW_TOKEN not in redacted
    assert RAW_INIT_DATA not in redacted
    assert AUTHORIZED_USER_ID not in redacted


def test_panel_without_mini_app_url_gives_clear_russian_local_tunnel_fallback() -> None:
    adapter = _adapter()
    _select_ru(adapter)

    reply = adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")

    assert "Mini App — расширенная панель PMBOT" in reply.text
    assert reply.panel_button_url == ""
    assert _button_labels(reply) == ("⬅️ Главное меню",)


def test_no_token_init_data_raw_operator_id_or_forbidden_execution_button_labels_are_exposed() -> None:
    adapter = _adapter(mini_app_url=MINI_APP_URL)
    _select_ru(adapter)
    replies = [
        adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/status"),
        adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel"),
        adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/language"),
    ]

    for reply in replies:
        rendered = json.dumps(reply.to_redacted_dict(), sort_keys=True)
        assert RAW_TOKEN not in reply.text
        assert RAW_INIT_DATA not in reply.text
        assert AUTHORIZED_USER_ID not in reply.text
        assert RAW_TOKEN not in rendered
        assert RAW_INIT_DATA not in rendered
        assert AUTHORIZED_USER_ID not in rendered
        for label in _button_labels(reply):
            upper_label = label.upper()
            assert not any(term in upper_label for term in FORBIDDEN_BUTTON_LABEL_TERMS)


def test_pause_and_kill_remain_local_markers_only_with_russian_language(tmp_path: Path) -> None:
    adapter = _adapter(artifact_dir=tmp_path)
    _select_ru(adapter)

    pause = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:pause")
    kill = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:kill")
    persisted = json.loads((tmp_path / "telegram_operator_control_state_043.json").read_text(encoding="utf-8"))

    assert "локальный маркер" in pause.text
    assert "live-исполнение не выполнялись" in kill.text
    assert persisted["operator_language"] == "ru"
    assert persisted["operator_pause_requested"] is True
    assert persisted["operator_kill_switch_requested"] is True
    assert persisted["does_not_modify_trading_execution"] is True
    assert persisted["order_submission_enabled"] is False
    assert persisted["live_execution_approved"] is False
    assert AUTHORIZED_USER_ID not in json.dumps(persisted, sort_keys=True)


def test_live_flags_remain_false_resolved_blockers_zero_and_no_external_network(monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    adapter = _adapter(mini_app_url=MINI_APP_URL)
    _select_ru(adapter)

    for callback_data in REQUIRED_STABLE_CALLBACKS - {"pmbot:lang:ru", "pmbot:lang:en"}:
        reply = adapter.handle_callback(
            user_id=AUTHORIZED_USER_ID,
            chat_id="chat-1",
            callback_data=callback_data,
        )
        redacted = reply.to_redacted_dict()
        blockers = dict(reply.summary.get("blocker_summary", {}))

        assert blockers.get("resolved_blocker_count") == 0
        assert redacted["resolved_blocker_count"] == 0
        for flag in FORCED_FALSE_FLAGS:
            assert reply.summary[flag] is False
            assert redacted[flag] is False
        assert redacted["network_used"] is False
        assert redacted["external_api_calls_performed"] is False


def test_local_mini_app_dev_mode_doc_includes_tunnel_and_server_instructions() -> None:
    doc = Path(
        "docs/ORCH_PMBOT_TRADING_MVP_046G_TELEGRAM_RU_LANGUAGE_AND_LOCAL_MINI_APP_DEV_MODE.md"
    ).read_text(encoding="utf-8")

    assert "python -m http.server 8080" in doc
    assert "cloudflared tunnel --url http://localhost:8080" in doc
    assert "ngrok http 8080" in doc
    assert "PMBOT_TELEGRAM_MINI_APP_URL" in doc
    assert "python -m pm_bot.operator_runner.telegram_operator_runtime" in doc
    assert "review-only" in doc
    assert "does not enable trading" in doc
