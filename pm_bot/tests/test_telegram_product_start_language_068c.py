from __future__ import annotations

import json
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_runtime_smoke as smoke
from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    SAFE_ACTION_COMMANDS,
    SUPPORTED_COMMANDS,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_operator_i18n import HOME_BUTTON_ROWS_BY_LANGUAGE
from pm_bot.operator_runner.telegram_product_ux_068c import (
    EN_MAIN_MENU_LABELS,
    FORBIDDEN_LIVE_CONTROLS,
    RU_MAIN_MENU_LABELS,
    START_LANGUAGE_LABELS,
    build_en_menu_snapshot,
    build_ru_menu_snapshot,
    build_safety_snapshot,
    build_start_menu_snapshot,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_PRIVATE_KEY = "raw-private-key-068c-never-output"
RAW_API_SECRET = "raw-api-secret-068c-never-output"
RAW_PASSPHRASE = "raw-passphrase-068c-never-output"
RAW_WALLET = "0x3006000000000000000000000000000000008989"
RAW_FUNDER = "0x1111000000000000000000000000000000005555"

ENGINEERING_DEBUG_LABELS = (
    "supervised live enablement gate",
    "credentials readiness gate",
    "blocker matrix",
    "static safety invariant report",
    "tiny order scaffold",
    "pre-live gate",
    "signer smoke contract",
)


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
            "api_keys_display_ru": "добавлены",
            "api_keys_display_en": "added",
            "private_key_added": True,
            "private_key_status": "added",
            "private_key_display_ru": "добавлен",
            "private_key_display_en": "added",
            "wallet_display": "0x3006...8989",
            "signature_type_display": "3",
            "funder_display": "0x1111...5555",
            "l2_auth_probe_display": "ok",
            "open_orders_status": "known_from_probe",
            "balance_allowance_status": "known_from_probe",
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
        "risk_control_plane_summary": {
            "max_order_notional_usd": 1,
            "max_daily_loss_usd": 5,
            "max_total_exposure_usd": 25,
            "max_market_exposure_usd": 2,
            "max_active_markets": 3,
            "max_trades_per_day": 2,
            "allowed_for_live": False,
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


def _callbacks(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.callback_data for row in reply.keyboard.rows for button in row if button.callback_data)


def _select_ru(adapter: runtime.TelegramOperatorRuntimeAdapter) -> runtime.TelegramRuntimeReply:
    return adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")


def _select_en(adapter: runtime.TelegramOperatorRuntimeAdapter) -> runtime.TelegramRuntimeReply:
    return adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:en")


def test_start_shows_language_picker_first() -> None:
    reply = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")

    assert reply.text == "Выберите язык"
    assert _labels(reply) == START_LANGUAGE_LABELS
    assert _callbacks(reply) == ("pmbot:lang:ru", "pmbot:lang:en")
    assert not set(RU_MAIN_MENU_LABELS).intersection(_labels(reply))
    assert reply.state["operator_language_selected"] is False


def test_ru_language_choice_shows_ru_main_menu() -> None:
    adapter = _adapter()
    adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")
    reply = _select_ru(adapter)

    assert reply.state["operator_language"] == "ru"
    assert "PMBOT — торговый помощник для Polymarket." in reply.text
    assert _labels(reply) == ("Главное меню",)
    menu = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:home")
    assert _labels(menu) == RU_MAIN_MENU_LABELS


def test_en_language_choice_shows_en_main_menu() -> None:
    adapter = _adapter()
    adapter.handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/start")
    reply = _select_en(adapter)

    assert reply.state["operator_language"] == "en"
    assert "PMBOT is a trading assistant for Polymarket." in reply.text
    assert _labels(reply) == ("Main menu",)
    menu = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:home")
    assert _labels(menu) == EN_MAIN_MENU_LABELS


def test_required_ru_and_en_buttons_are_primary_menu_labels() -> None:
    ru_labels = tuple(label for row in HOME_BUTTON_ROWS_BY_LANGUAGE["ru"] for label, _callback in row)
    en_labels = tuple(label for row in HOME_BUTTON_ROWS_BY_LANGUAGE["en"] for label, _callback in row)

    assert ru_labels == RU_MAIN_MENU_LABELS
    assert en_labels == EN_MAIN_MENU_LABELS
    for label in RU_MAIN_MENU_LABELS:
        assert label in ru_labels
    for label in EN_MAIN_MENU_LABELS:
        assert label in en_labels


def test_english_buttons_and_engineering_labels_are_not_ru_primary_menu_labels() -> None:
    ru_labels = _labels(_select_ru(_adapter()))
    rendered = "\n".join(ru_labels).lower()
    en_only = set(EN_MAIN_MENU_LABELS) - {"📈 PnL", "🖥 Mini App"}

    assert not en_only.intersection(ru_labels)
    for label in ENGINEERING_DEBUG_LABELS:
        assert label not in rendered


def test_connection_screen_redacts_values_and_uses_product_copy() -> None:
    adapter = _adapter()
    _select_ru(adapter)
    reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:connection")
    rendered = reply.text + json.dumps(reply.to_redacted_dict(), ensure_ascii=False, sort_keys=True)

    assert "🔌 Подключение" in reply.text
    assert "API Key: подключен" in reply.text
    assert "API Secret: подключен" in reply.text
    assert "Passphrase: подключен" in reply.text
    assert "Wallet address: подключен (0x3006...8989)" in reply.text
    assert "Signature type: подключен (3)" in reply.text
    assert "Funder address: подключен (0x1111...5555)" in reply.text
    for raw in (RAW_PRIVATE_KEY, RAW_API_SECRET, RAW_PASSPHRASE, RAW_WALLET, RAW_FUNDER):
        assert raw not in rendered


def test_balance_trades_and_pnl_do_not_fake_accounting_values() -> None:
    adapter = _adapter()
    _select_ru(adapter)

    balance = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:balance")
    trades = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:trades")
    pnl = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:pnl")
    combined = "\n".join([balance.text, trades.text, pnl.text]).lower()

    assert "Кошелёк: 0x3006...8989" in balance.text
    assert "Баланс: нет данных" in balance.text
    assert "Live-сделок пока не было" in trades.text
    assert "PnL пока недоступен: live-сделок ещё не было." in pnl.text
    for fake_value in ("$0", "0.00", "usdc", "order_id", "filled", "profit:", "loss:"):
        assert fake_value not in combined


def test_bot_status_limits_connection_check_mini_app_and_stop_are_safe_product_controls() -> None:
    adapter = _adapter()
    _select_ru(adapter)

    bot_status = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:bot_status")
    limits = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:limits")
    connection_check = adapter.handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:connection_status",
    )
    panel = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:panel")
    stop = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:stop")

    for line in (
        "Режим: review/dry-run",
        "Live trading: выключен",
        "Отправка ордеров: выключена",
        "Подписание: выключено",
        "Wallet execution: выключен",
    ):
        assert line in bot_status.text
    assert "Режим: supervised tiny mode" in limits.text
    assert "🧪 Проверить подключение" in _labels(connection_check)
    assert "Mini App — расширенная панель PMBOT" in panel.text
    assert "Бот сейчас не запущен." in stop.text
    assert "operator_stop_requested=true" in stop.text
    assert stop.state["operator_stop_requested"] is True
    assert stop.summary["allowed_for_live"] is False
    assert stop.summary["order_submission_enabled"] is False
    assert stop.summary["wallet_enabled"] is False
    assert stop.summary["signing_enabled"] is False


def test_forbidden_live_sign_wallet_send_controls_are_not_primary_controls() -> None:
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

    for forbidden in FORBIDDEN_LIVE_CONTROLS:
        assert forbidden.lower() not in rendered
    assert "run_signer" not in rendered
    assert "pmbot:run:signer" not in rendered
    assert "approve-live" not in rendered
    assert "send-order" not in rendered
    assert "connect-wallet" not in rendered


def test_068c_snapshots_and_runtime_smoke_keep_live_disabled() -> None:
    start = build_start_menu_snapshot(generated_at=GENERATED_AT)
    ru = build_ru_menu_snapshot(generated_at=GENERATED_AT)
    en = build_en_menu_snapshot(generated_at=GENERATED_AT)
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

    assert start["language_labels"] == list(START_LANGUAGE_LABELS)
    assert ru["labels"] == list(RU_MAIN_MENU_LABELS)
    assert en["labels"] == list(EN_MAIN_MENU_LABELS)
    assert ru["engineering_debug_labels_are_not_primary_menu_labels"] is True
    assert safety["allowed_for_live"] is False
    assert safety["order_submission_enabled"] is False
    assert report["review_only_safety_flags_ok"] is True
    assert report["review_only_safety_flags_expected_false"]["allowed_for_live"] is False
