from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pm_bot.operator_runner import telegram_runtime_smoke as smoke
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    SAFE_ACTION_COMMANDS,
    SUPPORTED_COMMANDS,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
    build_operator_home_keyboard,
)
from pm_bot.operator_runner.telegram_operator_i18n import (
    DEFAULT_OPERATOR_LANGUAGE,
    HOME_BUTTON_ROWS_BY_LANGUAGE,
)
from pm_bot.operator_runner.telegram_product_ux_067a import (
    ARTIFACT_DIR,
    EN_MAIN_MENU_LABELS,
    FORBIDDEN_LIVE_CONTROLS,
    I18N_SNAPSHOT_PATH,
    LATEST_STATUS_PATH,
    MENU_SNAPSHOT_PATH,
    RESULT_PATH,
    RU_MAIN_MENU_LABELS,
    SAFETY_SNAPSHOT_PATH,
    build_telegram_product_ux_i18n_snapshot,
    build_telegram_product_ux_menu_snapshot,
    build_telegram_product_ux_safety_snapshot,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_PRIVATE_KEY = "fake-private-key-067a"
RAW_API_SECRET = "fake-api-secret-067a"
RAW_PASSPHRASE = "fake-passphrase-067a"
RAW_WALLET = "0x1234567890abcdef067a"
RAW_FUNDER = "0xfunder1234567890abcdef067a"


def _context() -> dict[str, Any]:
    return {
        "raw_private_key_fixture": RAW_PRIVATE_KEY,
        "raw_api_secret_fixture": RAW_API_SECRET,
        "raw_passphrase_fixture": RAW_PASSPHRASE,
        "raw_wallet_fixture": RAW_WALLET,
        "raw_funder_fixture": RAW_FUNDER,
        "live_credentials_auth_boundary_summary": {
            "live_credentials_configured": True,
            "actual_secret_values_exposed": False,
            "authenticated_endpoints_enabled": False,
            "signing_enabled": False,
            "wallet_signing_enabled": False,
            "order_submission_enabled": False,
            "allowed_for_live": False,
        },
        "explicit_live_credentials_readiness_gate_status_summary": {
            "status": "redacted_presence_review_ready_live_blocked",
            "readiness_status": "blocked",
            "required_marker_presence": [
                _marker("PMBOT_POLYMARKET_L2_API_KEY_PRESENT", True),
                _marker("PMBOT_POLYMARKET_L2_API_SECRET_PRESENT", True),
                _marker("PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT", True),
                _marker("PMBOT_PRIVATE_KEY_CONFIGURED", True),
                _marker("PMBOT_WALLET_ADDRESS_CONFIGURED", True),
                _marker("PMBOT_SIGNATURE_TYPE_CONFIGURED", True),
                _marker("PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED", True),
            ],
            "credential_values_read": False,
            "raw_values_emitted": False,
            "allowed_for_live": False,
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


def _marker(label: str, present: bool) -> dict[str, Any]:
    return {
        "marker_label": label,
        "present": present,
        "value_redacted": True,
        "value_read": False,
        "raw_value_emitted": False,
    }


def _bot() -> TelegramOperatorControlBot:
    return TelegramOperatorControlBot(
        config=TelegramOperatorControlConfig(
            telegram_bot_configured=True,
            allowed_operator_user_ids=(AUTHORIZED_USER_ID,),
            generated_at=GENERATED_AT,
        ),
        context=_context(),
        generated_at=GENERATED_AT,
    )


def _labels(reply: Any) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def _callbacks_for_language(language: str) -> tuple[str, ...]:
    return tuple(callback_data for row in HOME_BUTTON_ROWS_BY_LANGUAGE[language] for _label, callback_data in row)


def test_ru_is_default_visible_language_and_language_commands_exist() -> None:
    bot = _bot()
    start = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/start")
    english = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/en")
    russian = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/ru")
    language = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/language")

    assert DEFAULT_OPERATOR_LANGUAGE == "ru"
    assert start.text == "Выберите язык"
    assert _labels(start) == ("🇷🇺 Русский", "🇬🇧 English")
    assert english.state["operator_language"] == "en"
    assert _labels(english) == ("Main menu",)
    assert russian.state["operator_language"] == "ru"
    assert _labels(russian) == ("Главное меню",)
    assert language.text == "Выберите язык"
    assert {"/ru", "/en", "/language"}.issubset(set(SUPPORTED_COMMANDS))


def test_main_menu_contains_product_labels_and_no_primary_debug_labels() -> None:
    ru_keyboard = build_operator_home_keyboard()
    en_keyboard = build_operator_home_keyboard("en")

    assert tuple(button.label for row in ru_keyboard.rows for button in row) == RU_MAIN_MENU_LABELS
    assert tuple(button.label for row in en_keyboard.rows for button in row) == EN_MAIN_MENU_LABELS
    assert _callbacks_for_language("ru") == (
        "pmbot:connection",
        "pmbot:balance",
        "pmbot:analytics",
        "pmbot:launch",
        "pmbot:stop",
        "pmbot:panel",
        "pmbot:settings",
    )
    primary_menu_text = json.dumps(HOME_BUTTON_ROWS_BY_LANGUAGE, ensure_ascii=False).lower()
    for debug_label in (
        "readiness gate",
        "blocker matrix",
        "supervised live enablement",
        "credentials readiness",
        "готовности credentials",
        "матрица блокеров",
    ):
        assert debug_label not in primary_menu_text


def test_connection_screen_redacts_all_secret_like_values() -> None:
    reply = _bot().handle_command(user_id=AUTHORIZED_USER_ID, text="/connection")
    rendered = reply.text + json.dumps(reply.to_dict(), ensure_ascii=False, sort_keys=True)

    assert "🔌 Подключение" in reply.text
    assert "API Key: подключен" in reply.text
    assert "API Secret: подключен" in reply.text
    assert "Passphrase: подключен" in reply.text
    assert "Wallet Address: подключен" in reply.text
    assert "Signature Type: подключен" in reply.text
    assert "Funder Address: подключен" in reply.text
    for raw in (RAW_PRIVATE_KEY, RAW_API_SECRET, RAW_PASSPHRASE, RAW_WALLET, RAW_FUNDER):
        assert raw not in rendered


def test_balance_trades_and_pnl_screens_do_not_emit_fake_data() -> None:
    bot = _bot()
    balance = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/balance")
    trades = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/trades")
    pnl = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/pnl")

    assert "Баланс: нет данных" in balance.text
    assert "Live-сделок пока не было" in trades.text
    assert "PnL пока недоступен: live-сделок ещё не было." in pnl.text
    combined = "\n".join([balance.text, trades.text, pnl.text]).lower()
    for fake_value in ("$0", "0.00", "usdc", "order_id", "filled", "profit:", "loss:"):
        assert fake_value not in combined


def test_bot_status_and_stop_remain_non_live_local_status_only() -> None:
    bot = _bot()
    status = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/bot_status")
    stop = bot.handle_command(user_id=AUTHORIZED_USER_ID, text="/stop")

    assert "Режим: review/dry-run" in status.text
    for line in (
        "allowed_for_live=false",
            "Live trading: выключен",
            "Отправка ордеров: выключена",
            "Подписание: выключено",
            "Wallet execution: выключен",
        ):
            assert line in status.text
    assert "Бот сейчас не запущен." in stop.text
    assert "operator_stop_requested=true" in stop.text
    assert stop.state["operator_stop_requested"] is True
    assert stop.summary["allowed_for_live"] is False
    assert stop.summary["order_submission_enabled"] is False
    assert stop.summary["wallet_enabled"] is False
    assert stop.summary["signing_enabled"] is False


def test_forbidden_telegram_live_controls_are_absent() -> None:
    records = [
        *SUPPORTED_COMMANDS,
        *SAFE_ACTION_COMMANDS,
        *CALLBACK_COMMAND_MAP.keys(),
        *CALLBACK_COMMAND_MAP.values(),
        *RU_MAIN_MENU_LABELS,
        *EN_MAIN_MENU_LABELS,
    ]
    rendered = "\n".join(records).lower()

    for forbidden in FORBIDDEN_LIVE_CONTROLS:
        assert forbidden.lower() not in rendered
    assert "run_signer" not in rendered
    assert "pmbot:run:signer" not in rendered
    assert "approve-live" not in rendered
    assert "send-order" not in rendered
    assert "connect-wallet" not in rendered


def test_telegram_runtime_smoke_and_067a_artifacts_keep_allowed_for_live_false() -> None:
    report = smoke.build_telegram_runtime_smoke_report(
        env={
            "PMBOT_TELEGRAM_BOT_TOKEN": "123456:raw-telegram-token-value",
            "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS": AUTHORIZED_USER_ID,
        },
        dependency_checker=lambda: {
            "dependency": "python-telegram-bot",
            "installed": True,
            "status": "installed",
            "error_category": "",
        },
        generated_at=GENERATED_AT,
    )
    menu = build_telegram_product_ux_menu_snapshot(generated_at=GENERATED_AT)
    i18n = build_telegram_product_ux_i18n_snapshot(generated_at=GENERATED_AT)
    safety = build_telegram_product_ux_safety_snapshot(generated_at=GENERATED_AT)

    assert report["review_only_safety_flags_ok"] is True
    assert report["review_only_safety_flags_expected_false"]["allowed_for_live"] is False
    assert menu["default_visible_language"] == "ru"
    assert menu["ru_main_menu_labels"] == list(RU_MAIN_MENU_LABELS)
    assert i18n["ru_first"] is True
    assert safety["allowed_for_live"] is False
    assert safety["live_trading_enabled"] is False
    assert safety["order_submission_enabled"] is False


def test_committed_067a_artifacts_exist_and_match_core_snapshots() -> None:
    expected_paths = (
        RESULT_PATH,
        LATEST_STATUS_PATH,
        MENU_SNAPSHOT_PATH,
        I18N_SNAPSHOT_PATH,
        SAFETY_SNAPSHOT_PATH,
    )
    for path in expected_paths:
        assert path.exists(), f"missing artifact: {path}"
        assert path.is_relative_to(ARTIFACT_DIR)

    menu = json.loads(MENU_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    i18n = json.loads(I18N_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    safety = json.loads(SAFETY_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    latest = json.loads(LATEST_STATUS_PATH.read_text(encoding="utf-8"))
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))

    assert menu["ru_main_menu_labels"] == list(RU_MAIN_MENU_LABELS)
    assert menu["en_main_menu_labels"] == list(EN_MAIN_MENU_LABELS)
    assert i18n["default_visible_language"] == "ru"
    assert safety["allowed_for_live"] is False
    assert latest["allowed_for_live"] is False
    assert result["safety_flags"]["allowed_for_live"] is False
