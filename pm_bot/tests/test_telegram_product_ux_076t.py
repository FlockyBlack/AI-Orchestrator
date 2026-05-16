from __future__ import annotations

import asyncio
import json
from typing import Any

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    SAFE_ACTION_COMMANDS,
    SUPPORTED_COMMANDS,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_operator_i18n import HOME_BUTTON_ROWS_BY_LANGUAGE
from pm_bot.operator_runner.telegram_product_ux_068c import EN_MAIN_MENU_LABELS, RU_MAIN_MENU_LABELS

GENERATED_AT = "2026-05-16T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_API_SECRET = "raw-api-secret-076t-never-output"
RAW_PASSPHRASE = "raw-passphrase-076t-never-output"
RAW_WALLET = "0x3006000000000000000000000000000000000760"
RAW_FUNDER = "0x1111000000000000000000000000000000000760"

START_LANGUAGE_LABELS = ("🇷🇺 Русский", "🇬🇧 English")
RU_PRODUCT_DESCRIPTION = (
    "PMBOT — торговый помощник для Polymarket.\n\n"
    "Он помогает подключить аккаунт, выбрать рынки, настроить лимиты, "
    "отслеживать баланс, аналитику и запускать торговлю под вашим контролем.\n\n"
    "Вы можете пользоваться быстрым Telegram-меню или открыть Mini App "
    "с расширенной панелью, графиками и подробной статистикой."
)
FORBIDDEN_PRIMARY_TERMS = (
    "DryRun",
    "Gate",
    "Provider",
    "Readiness",
    "Scaffold",
    "Runner",
    "Artifact",
    "Probe",
    "Debug",
    "Evidence",
    "Payload",
    "Blocker",
    "allowed_for_live",
)
FORBIDDEN_CONTROL_TERMS = (
    "submit",
    "cancel",
    "sign",
    "connect-wallet",
    "wallet-connect",
    "send-order",
    "submit-order",
    "cancel-order",
    "run_signer",
    "pmbot:run:signer",
)


class FakeCallbackQuery:
    def __init__(self, *, fail_edit: bool = False) -> None:
        self.fail_edit = fail_edit
        self.edit_calls: list[dict[str, Any]] = []

    async def edit_message_text(self, **kwargs: Any) -> None:
        if self.fail_edit:
            raise RuntimeError("message can't be edited")
        self.edit_calls.append(dict(kwargs))


class FakeMessage:
    def __init__(self) -> None:
        self.reply_calls: list[dict[str, Any]] = []

    async def reply_text(self, **kwargs: Any) -> None:
        self.reply_calls.append(dict(kwargs))


def _context(*, connected: bool = False) -> dict[str, Any]:
    status = {
        "api_keys_added": connected,
        "api_keys_status": "added" if connected else "not_added",
        "wallet_display": "0x3006...0760" if connected else "missing",
        "signature_type_display": "3" if connected else "missing",
        "funder_display": "0x1111...0760" if connected else "missing",
        "balance_status": "unknown",
        "open_positions_status": "unknown",
        "open_orders_status": "unknown",
        "last_check_timestamp": "2026-05-16T00:00:00+04:00" if connected else "",
        "credential_values_read": False,
        "raw_values_emitted": False,
        "allowed_for_live": False,
        "order_submission_enabled": False,
        "wallet_connection_attempted": False,
        "signing_enabled": False,
    }
    return {
        "raw_api_secret_fixture": RAW_API_SECRET,
        "raw_passphrase_fixture": RAW_PASSPHRASE,
        "raw_wallet_fixture": RAW_WALLET,
        "raw_funder_fixture": RAW_FUNDER,
        "telegram_connection_status_067e_status_summary": status,
        "telegram_operator_token_selection_074b_status_summary": {
            "selected_candidate_available": False,
            "token_id_selected": False,
            "allowed_for_live": False,
        },
    }


def _adapter(*, connected: bool = False, mini_app_url: str = "") -> runtime.TelegramOperatorRuntimeAdapter:
    context = _context(connected=connected)
    bot = TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=context,
        generated_at=GENERATED_AT,
    )
    return runtime.TelegramOperatorRuntimeAdapter(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            mini_app_url=mini_app_url,
            generated_at=GENERATED_AT,
        ),
        context=context,
        bot=bot,
    )


def _labels(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def _callbacks(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.callback_data for row in reply.keyboard.rows for button in row if button.callback_data)


def _rendered(reply: runtime.TelegramRuntimeReply) -> str:
    return reply.text + "\n" + json.dumps(reply.to_redacted_dict(), ensure_ascii=False, sort_keys=True)


def test_first_launch_shows_only_language_selection() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")

    assert reply.text == "Выберите язык"
    assert _labels(reply) == START_LANGUAGE_LABELS
    assert _callbacks(reply) == ("pmbot:lang:ru", "pmbot:lang:en")
    assert not set(RU_MAIN_MENU_LABELS).intersection(_labels(reply))


def test_product_description_appears_after_language_choice() -> None:
    reply = _adapter().handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    assert reply.text == RU_PRODUCT_DESCRIPTION
    assert _labels(reply) == ("Главное меню",)
    for forbidden in ("no live trading", "dry-run", "scaffold", "readiness", "blocked", "allowed_for_live=false"):
        assert forbidden not in reply.text.lower()


def test_main_menu_contains_only_product_level_labels() -> None:
    adapter = _adapter()
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    ru = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:home")
    en = _adapter().handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")

    assert _labels(ru) == RU_MAIN_MENU_LABELS
    assert _labels(en) == ("Main menu",)
    assert tuple(label for row in HOME_BUTTON_ROWS_BY_LANGUAGE["en"] for label, _callback in row) == EN_MAIN_MENU_LABELS
    rendered = "\n".join(RU_MAIN_MENU_LABELS + EN_MAIN_MENU_LABELS)
    for forbidden in FORBIDDEN_PRIMARY_TERMS:
        assert forbidden not in rendered


def test_connection_screen_redacts_secrets_and_shows_statuses() -> None:
    reply = _adapter(connected=True).handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:connection",
    )
    rendered = _rendered(reply)

    assert "🔌 Подключение" in reply.text
    assert "API Key: подключен" in reply.text
    assert "API Secret: подключен" in reply.text
    assert "Passphrase: подключен" in reply.text
    assert "Wallet address: подключен (0x3006...0760)" in reply.text
    assert "Signature type: подключен (3)" in reply.text
    assert "Funder address: подключен (0x1111...0760)" in reply.text
    assert "Ключи должны быть доступны процессу Telegram-бота" in reply.text
    assert _labels(reply) == (
        "➕ Подключить API-ключи",
        "🔍 Проверить подключение",
        "📘 Инструкция",
        "🗑 Удалить подключение",
        "⬅️ Главное меню",
    )
    for raw in (RAW_API_SECRET, RAW_PASSPHRASE, RAW_WALLET, RAW_FUNDER):
        assert raw not in rendered


def test_connection_setup_is_guided_and_does_not_collect_chat_secrets() -> None:
    reply = _adapter().handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:connection:setup")

    assert "Безопасное подключение выполняется через переменные окружения" in reply.text
    assert "Значения не вводятся в чат" in reply.text
    assert "зашифрованное хранилище" in reply.text.lower()
    assert "<input" not in reply.text.lower()


def test_balance_missing_connection_routes_to_connection() -> None:
    reply = _adapter(connected=False).handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:balance",
    )

    assert "Баланс недоступен: сначала завершите подключение." in reply.text
    assert _labels(reply) == ("🔌 Перейти к подключению",)
    assert _callbacks(reply) == ("pmbot:connection",)


def test_connected_balance_without_account_artifact_shows_safe_readonly_probe_command() -> None:
    reply = _adapter(connected=True).handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:balance",
    )

    assert "Ключи видны, но проверка аккаунта ещё не выполнена." in reply.text
    assert "python -m pm_bot.operator_runner.live_account_readonly_state_probe --market BTC --strategy tiny-momentum --dry-run" in reply.text
    assert _labels(reply) == ("🔄 Обновить", "🔌 Подключение", "⬅️ Главное меню")
    for fake_value in ("$0", "0.00", "order_id", "filled", "profit:", "loss:"):
        assert fake_value.lower() not in reply.text.lower()


def test_analytics_uses_product_empty_state_without_fake_pnl() -> None:
    reply = _adapter().handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:analytics")

    assert "Сегодня: нет данных" in reply.text
    assert "7 дней: нет данных" in reply.text
    assert "30 дней: нет данных" in reply.text
    assert "Сделок: нет данных" in reply.text
    assert "Winrate: нет данных" in reply.text
    assert "Максимальная просадка: нет данных" in reply.text
    assert "Данных пока нет. Аналитика появится после первых сделок или после подключения истории аккаунта." in reply.text
    assert _labels(reply) == ("🔄 Обновить", "📈 Подробнее", "⬅️ Главное меню")


def test_launch_flow_exposes_limits_markets_and_prelaunch_summary() -> None:
    adapter = _adapter()

    launch = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch")
    limit_menu = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:limit")
    selected_limit = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:limit:5")
    selected_loss = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:max_loss:2")
    selected_market = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:market:btc")
    prelaunch = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:start")

    assert "Запуск торговли" in launch.text
    assert "Настройте лимиты и выберите рынки" in launch.text
    assert _labels(launch) == ("💵 Лимит на день", "📉 Максимальный убыток", "🎯 Выбор рынков", "▶️ Запустить", "⬅️ Главное меню")
    assert _labels(limit_menu)[:5] == ("$5", "$10", "$25", "$50", "Ввести вручную")
    assert "Лимит на день выбран: $5" in selected_limit.text
    assert "Максимальный убыток выбран: $2" in selected_loss.text
    assert "Рынок добавлен: BTC" in selected_market.text
    assert "Лимит на день: $5" in prelaunch.text
    assert "Максимальный убыток: $2" in prelaunch.text
    assert "Рынки: BTC" in prelaunch.text
    assert "Подключение: не готово" in prelaunch.text
    assert "Баланс/аккаунт: недоступен" in prelaunch.text
    assert "Риск: требуется финальная проверка" in prelaunch.text
    assert "Token ID: требуется выбор" in prelaunch.text
    assert "Запуск пока недоступен: требуется финальная проверка и подтверждение." in prelaunch.text
    assert "allowed_for_live" not in prelaunch.text
    assert prelaunch.summary["order_submission_enabled"] is False
    assert prelaunch.summary["signing_enabled"] is False


def test_stop_flow_does_not_claim_live_stop_when_runtime_is_not_running() -> None:
    reply = _adapter().handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:stop")

    assert "Бот сейчас не запущен." in reply.text
    assert "trading_requested=false" in reply.text
    assert "operator_stop_requested=true" in reply.text
    assert _labels(reply) == ("🚀 Перейти к запуску", "⬅️ Главное меню")
    assert reply.state["trading_requested"] is False
    assert reply.state["operator_stop_requested"] is True
    assert "остановлены реальные ордера" not in reply.text.lower()


def test_mini_app_screen_has_product_copy_and_open_button() -> None:
    reply = _adapter(mini_app_url="https://example.com/pmbot").handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:panel",
    )

    assert "Mini App — расширенная панель PMBOT с графиками, настройками, аналитикой и подробной статистикой." in reply.text
    assert _labels(reply) == ("Открыть Mini App", "⬅️ Главное меню")
    assert reply.keyboard.rows[0][0].web_app_url == "https://example.com/pmbot"
    rendered = _rendered(reply).lower()
    assert "connect wallet" not in rendered
    assert "submit order" not in rendered
    assert "cancel order" not in rendered
    assert "sign transaction" not in rendered


def test_settings_offers_language_change_and_main_menu() -> None:
    reply = _adapter().handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:settings")

    assert "⚙️ Настройки" in reply.text
    assert "Язык: русский" in reply.text
    assert _labels(reply) == ("🌐 Изменить язык", "⬅️ Главное меню")


def test_same_message_navigation_remains_intact() -> None:
    reply = _adapter().handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:connection")
    query = FakeCallbackQuery()
    message = FakeMessage()

    result = asyncio.run(
        runtime.telegram_callback_edit_renderer(query=query, message=message, reply=reply, reply_markup=None)
    )

    assert result == "edited"
    assert len(query.edit_calls) == 1
    assert query.edit_calls[0]["text"] == reply.text
    assert message.reply_calls == []

    fallback_query = FakeCallbackQuery(fail_edit=True)
    fallback_message = FakeMessage()
    fallback = asyncio.run(
        runtime.telegram_callback_edit_renderer(
            query=fallback_query,
            message=fallback_message,
            reply=reply,
            reply_markup=None,
        )
    )
    assert fallback == "replacement_sent"
    assert len(fallback_message.reply_calls) == 1


def test_no_submit_cancel_sign_wallet_controls_added() -> None:
    records = [
        *SUPPORTED_COMMANDS,
        *SAFE_ACTION_COMMANDS,
        *CALLBACK_COMMAND_MAP.keys(),
        *CALLBACK_COMMAND_MAP.values(),
        *RU_MAIN_MENU_LABELS,
        *EN_MAIN_MENU_LABELS,
        *START_LANGUAGE_LABELS,
    ]
    rendered = "\n".join(records).lower()

    for forbidden in FORBIDDEN_CONTROL_TERMS:
        assert forbidden not in rendered
    assert "connect wallet" not in rendered
    assert "wallet connect" not in rendered
