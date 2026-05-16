from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner import telegram_runtime_smoke as smoke
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    SAFE_ACTION_COMMANDS,
    SUPPORTED_COMMANDS,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_operator_i18n import HOME_BUTTON_ROWS_BY_LANGUAGE
from pm_bot.operator_runner.telegram_product_ux_068c import EN_MAIN_MENU_LABELS, RU_MAIN_MENU_LABELS
from pm_bot.operator_runner.telegram_single_message_product_menu_069c import (
    ARTIFACT_DIR,
    EN_SNAPSHOT_PATH,
    FORBIDDEN_LIVE_CONTROL_TERMS,
    LATEST_STATUS_PATH,
    NAVIGATION_SNAPSHOT_PATH,
    RESULT_PATH,
    RU_SNAPSHOT_PATH,
    SAFETY_SNAPSHOT_PATH,
    START_LANGUAGE_LABELS,
    TECHNICAL_PRIMARY_MENU_BLOCKLIST,
    build_en_snapshot,
    build_navigation_snapshot,
    build_ru_snapshot,
    build_safety_snapshot,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_PRIVATE_KEY = "raw-private-key-069c-never-output"
RAW_API_SECRET = "raw-api-secret-069c-never-output"
RAW_PASSPHRASE = "raw-passphrase-069c-never-output"
RAW_WALLET = "0x3006000000000000000000000000000000008989"
RAW_FUNDER = "0x1111000000000000000000000000000000005555"


class FakeCallbackQuery:
    def __init__(self, *, fail_edit: bool = False, edit_error: str = "message can't be edited") -> None:
        self.fail_edit = fail_edit
        self.edit_error = edit_error
        self.edit_calls: list[dict[str, Any]] = []

    async def edit_message_text(self, **kwargs: Any) -> None:
        if self.fail_edit:
            raise RuntimeError(self.edit_error)
        self.edit_calls.append(kwargs)


class FakeMessage:
    def __init__(self) -> None:
        self.reply_calls: list[dict[str, Any]] = []

    async def reply_text(self, **kwargs: Any) -> None:
        self.reply_calls.append(kwargs)


def _context() -> dict[str, Any]:
    return {
        "raw_private_key_fixture": RAW_PRIVATE_KEY,
        "raw_api_secret_fixture": RAW_API_SECRET,
        "raw_passphrase_fixture": RAW_PASSPHRASE,
        "raw_wallet_fixture": RAW_WALLET,
        "raw_funder_fixture": RAW_FUNDER,
        "telegram_connection_status_067e_status_summary": {
            "api_keys_added": True,
            "api_keys_status": "added",
            "private_key_added": True,
            "private_key_status": "added",
            "wallet_display": "0x3006...8989",
            "signature_type_display": "3",
            "funder_display": "0x1111...5555",
            "l2_auth_probe_display": "ok",
            "credential_values_read": False,
            "raw_values_emitted": False,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "wallet_connection_attempted": False,
            "signing_enabled": False,
        },
        "telegram_real_check_results_073t_status_summary": {
            "contract_version": "pmbot_telegram_real_check_results_status_073t.v1",
            "source_artifact_available": True,
            "api_keys_found": True,
            "api_keys_display_ru": "найдены",
            "l2_auth_status": "ok",
            "l2_auth_display_ru": "OK",
            "account_status": "ok",
            "account_display_ru": "OK",
            "signer_status": "ok",
            "signer_display_ru": "OK",
            "market_found": True,
            "market_display_ru": "найден",
            "token_id_selected": True,
            "token_id_display_ru": "выбран",
            "live_enabled": False,
            "live_display_ru": "выключен",
            "raw_token_id_exposed": False,
            "raw_account_values_exposed": False,
            "raw_secret_output": False,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "wallet_connection_attempted": False,
            "signing_attempted": False,
        },
    }


def _adapter(*, mini_app_url: str = "") -> runtime.TelegramOperatorRuntimeAdapter:
    bot = TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=_context(),
        generated_at=GENERATED_AT,
    )
    return runtime.TelegramOperatorRuntimeAdapter(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            mini_app_url=mini_app_url,
            generated_at=GENERATED_AT,
        ),
        context=_context(),
        bot=bot,
    )


def _labels(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def _rendered(reply: runtime.TelegramRuntimeReply) -> str:
    return reply.text + "\n" + json.dumps(reply.to_redacted_dict(), ensure_ascii=False, sort_keys=True)


def test_start_shows_only_language_picker_first() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")

    assert reply.text == "Выберите язык"
    assert _labels(reply) == START_LANGUAGE_LABELS
    assert not set(RU_MAIN_MENU_LABELS).intersection(_labels(reply))
    assert reply.state["operator_language_selected"] is False


def test_selecting_ru_and_en_switches_to_clean_main_menu() -> None:
    adapter = _adapter()
    adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")

    ru = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    assert ru.state["operator_language"] == "ru"
    assert "PMBOT — торговый помощник для Polymarket." in ru.text
    assert _labels(ru) == ("Главное меню",)
    ru_menu = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:home")
    assert "PMBOT\nГлавное меню" in ru_menu.text
    assert _labels(ru_menu) == RU_MAIN_MENU_LABELS
    en = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")
    assert en.state["operator_language"] == "en"
    assert "PMBOT is a trading assistant for Polymarket." in en.text
    assert _labels(en) == ("Main menu",)


def test_ru_and_en_primary_menus_have_only_required_product_buttons() -> None:
    ru_labels = tuple(label for row in HOME_BUTTON_ROWS_BY_LANGUAGE["ru"] for label, _callback in row)
    en_labels = tuple(label for row in HOME_BUTTON_ROWS_BY_LANGUAGE["en"] for label, _callback in row)

    assert ru_labels == RU_MAIN_MENU_LABELS
    assert en_labels == EN_MAIN_MENU_LABELS
    for labels in (ru_labels, en_labels):
        rendered = "\n".join(labels).lower()
        for forbidden in TECHNICAL_PRIMARY_MENU_BLOCKLIST:
            assert forbidden.lower() not in rendered


def test_normal_callback_navigation_uses_edit_message_renderer_not_send_new_message() -> None:
    adapter = _adapter()
    reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    query = FakeCallbackQuery()
    message = FakeMessage()

    result = asyncio.run(
        runtime.telegram_callback_edit_renderer(
            query=query,
            message=message,
            reply=reply,
            reply_markup=None,
        )
    )

    assert result == "edited"
    assert len(query.edit_calls) == 1
    assert query.edit_calls[0]["text"] == reply.text
    assert message.reply_calls == []


def test_callback_edit_fallback_sends_one_replacement_message() -> None:
    adapter = _adapter()
    reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:balance")
    query = FakeCallbackQuery(fail_edit=True)
    message = FakeMessage()

    result = asyncio.run(
        runtime.telegram_callback_edit_renderer(
            query=query,
            message=message,
            reply=reply,
            reply_markup=None,
        )
    )

    assert result == "replacement_sent"
    assert len(message.reply_calls) == 1
    assert message.reply_calls[0]["text"] == reply.text

    missing_query = FakeCallbackQuery(fail_edit=True, edit_error="message to edit not found")
    missing_message = FakeMessage()
    missing_result = asyncio.run(
        runtime.telegram_callback_edit_renderer(
            query=missing_query,
            message=missing_message,
            reply=reply,
            reply_markup=None,
        )
    )

    assert missing_result == "replacement_sent"
    assert len(missing_message.reply_calls) == 1


def test_every_product_screen_has_back_button_and_expected_scoped_buttons() -> None:
    adapter = _adapter()
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    expected = {
        "pmbot:connection": ("🔄 Проверить снова", "📘 Инструкция", "💰 Перейти к балансу", "⬅️ Главное меню"),
        "pmbot:balance": ("🔄 Обновить", "📌 Позиции", "📜 Ордера", "⬅️ Главное меню"),
        "pmbot:analytics": ("🔄 Обновить", "📈 Подробнее", "⬅️ Главное меню"),
        "pmbot:launch": ("💵 Лимит на день", "📉 Максимальный убыток", "🎯 Выбор рынков", "▶️ Запустить", "⬅️ Главное меню"),
        "pmbot:panel": ("⬅️ Главное меню",),
        "pmbot:settings": ("🌐 Изменить язык", "⬅️ Главное меню"),
        "pmbot:stop": ("🚀 Перейти к запуску", "⬅️ Главное меню"),
    }
    for callback_data, labels in expected.items():
        reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data=callback_data)
        for label in labels:
            assert label in _labels(reply), callback_data


def test_connection_screen_redacts_all_secrets_and_shows_presence_only_status() -> None:
    adapter = _adapter()
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:connection")
    rendered = _rendered(reply)

    assert "🔌 Подключение" in reply.text
    assert "API Key: подключен" in reply.text
    assert "API Secret: подключен" in reply.text
    assert "Passphrase: подключен" in reply.text
    assert "Wallet Address: подключен (0x3006...8989)" in reply.text
    assert "Signature Type: подключен (3)" in reply.text
    assert "Funder Address: подключен (0x1111...5555)" in reply.text
    for raw in (RAW_PRIVATE_KEY, RAW_API_SECRET, RAW_PASSPHRASE, RAW_WALLET, RAW_FUNDER):
        assert raw not in rendered


def test_balance_trades_and_pnl_do_not_fake_account_values() -> None:
    adapter = _adapter()
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    balance = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:balance")
    trades = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:trades")
    pnl = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:pnl")
    combined = "\n".join([balance.text, trades.text, pnl.text]).lower()

    assert "Кошелёк: 0x3006...8989" in balance.text
    assert "Баланс: нет данных" in balance.text
    assert "Live-сделок пока не было." in trades.text
    assert "Открытые ордера: неизвестно" in trades.text
    assert "PnL пока недоступен: live-сделок ещё не было." in pnl.text
    for fake_value in ("$0", "0.00", "usdc", "order_id", "filled", "profit:", "loss:"):
        assert fake_value not in combined


def test_status_limits_mini_app_and_stop_remain_status_only() -> None:
    adapter = _adapter()
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    status = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:bot_status")
    limits = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:limits")
    missing_panel = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:panel")
    configured_panel = _adapter(mini_app_url="https://example.com/pmbot").handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:panel",
    )
    stop = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:stop")

    for line in (
        "Режим: review/dry-run",
        "Live trading: выключен",
        "Отправка ордеров: выключена",
        "Подписание: выключено",
        "Wallet execution: выключен",
        "allowed_for_live=false",
    ):
        assert line in status.text
    for line in (
        "Режим: supervised tiny mode",
        "Max order:",
        "Max orders/day:",
        "Автоторговля: выключена",
        "Live: выключен",
    ):
        assert line in limits.text
    assert "Mini App — расширенная панель PMBOT" in missing_panel.text
    assert "Mini App — расширенная панель PMBOT" in configured_panel.text
    assert "Открыть Mini App" in _labels(configured_panel)
    assert configured_panel.keyboard.rows[0][0].web_app_url == "https://example.com/pmbot"
    assert "Бот сейчас не запущен." in stop.text
    assert "trading_requested=false" in stop.text
    assert "operator_stop_requested=true" in stop.text
    assert stop.state["operator_stop_requested"] is True
    assert stop.summary["order_cancel_enabled"] is False
    assert stop.summary["order_submission_enabled"] is False


def test_forbidden_live_sign_wallet_order_controls_absent_from_user_controls() -> None:
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

    for forbidden in FORBIDDEN_LIVE_CONTROL_TERMS:
        assert forbidden.lower() not in rendered


def test_069c_snapshots_artifacts_and_runtime_smoke_confirm_safety() -> None:
    ru = build_ru_snapshot(generated_at=GENERATED_AT)
    en = build_en_snapshot(generated_at=GENERATED_AT)
    navigation = build_navigation_snapshot(generated_at=GENERATED_AT)
    safety = build_safety_snapshot(generated_at=GENERATED_AT)
    report = smoke.build_telegram_runtime_smoke_report(
        env={
            runtime.TELEGRAM_BOT_TOKEN_ENV: RAW_TOKEN,
            runtime.ALLOWED_OPERATOR_IDS_ENV: AUTHORIZED_USER_ID,
        },
        dependency_checker=lambda: {
            "dependency": "python-telegram-bot",
            "installed": True,
            "status": "installed",
            "error_category": "",
        },
        generated_at=GENERATED_AT,
    )

    assert ru["main_menu_labels"] == list(RU_MAIN_MENU_LABELS)
    assert en["main_menu_labels"] == list(EN_MAIN_MENU_LABELS)
    assert navigation["single_message_navigation"] is True
    assert navigation["normal_callbacks_use_edit_message_text"] is True
    assert safety["no_live_trading"] is True
    assert safety["no_order_submission"] is True
    assert safety["no_signing"] is True
    assert safety["no_wallet_connection"] is True
    assert safety["no_fake_balance"] is True
    assert safety["no_fake_trades"] is True
    assert safety["no_fake_pnl"] is True
    assert report["review_only_safety_flags_ok"] is True


def test_committed_069c_artifacts_exist_and_confirm_required_flags() -> None:
    for path in (
        RESULT_PATH,
        LATEST_STATUS_PATH,
        RU_SNAPSHOT_PATH,
        EN_SNAPSHOT_PATH,
        NAVIGATION_SNAPSHOT_PATH,
        SAFETY_SNAPSHOT_PATH,
    ):
        assert path.exists(), f"missing artifact: {path}"
        assert path.is_relative_to(ARTIFACT_DIR)

    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in (RESULT_PATH, LATEST_STATUS_PATH, SAFETY_SNAPSHOT_PATH)]
    for payload in payloads:
        safety = payload.get("safety_flags", payload)
        assert safety["single_message_navigation"] is True
        assert safety["primary_menu_is_product_only"] is True
        assert safety["debug_labels_hidden_from_primary_menu"] is True
        for flag in (
            "no_live_trading",
            "no_order_submission",
            "no_signing",
            "no_wallet_connection",
            "no_secret_values_emitted",
            "no_fake_balance",
            "no_fake_trades",
            "no_fake_pnl",
        ):
            assert safety[flag] is True, flag
