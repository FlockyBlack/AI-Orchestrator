from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    SAFE_ACTION_COMMANDS,
    SUPPORTED_COMMANDS,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_operator_i18n import HOME_BUTTON_ROWS_BY_LANGUAGE
from pm_bot.operator_runner.telegram_product_ux_068c import RU_MAIN_MENU_LABELS
from pm_bot.trading_core.runtime_credential_visibility_077c import run_runtime_credential_visibility_diagnostic

GENERATED_AT = "2026-05-17T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value-077e-never-output"
RAW_API_KEY = "raw-api-key-077e-never-output"
RAW_API_SECRET = "raw-api-secret-077e-never-output"
RAW_PASSPHRASE = "raw-passphrase-077e-never-output"
RAW_PRIVATE_KEY = "raw-private-key-077e-never-output"
RAW_WALLET = "0x300600000000000000000000000000000000077e"
RAW_FUNDER = "0x111100000000000000000000000000000000077e"
RAW_OPERATOR_IDS = "123456789,987654321"


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


def _env(*, include_funder: bool = True) -> dict[str, str]:
    env = {
        "POLYMARKET_API_KEY": RAW_API_KEY,
        "POLYMARKET_API_SECRET": RAW_API_SECRET,
        "POLYMARKET_API_PASSPHRASE": RAW_PASSPHRASE,
        "POLYMARKET_PRIVATE_KEY": RAW_PRIVATE_KEY,
        "POLYMARKET_WALLET_ADDRESS": RAW_WALLET,
        "POLYMARKET_SIGNATURE_TYPE": "2",
        "PMBOT_TELEGRAM_BOT_TOKEN": RAW_TOKEN,
        "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS": RAW_OPERATOR_IDS,
    }
    if include_funder:
        env["POLYMARKET_FUNDER_ADDRESS"] = RAW_FUNDER
    return env


def _runtime_visibility_context(tmp_path: Path, *, include_funder: bool = True) -> dict[str, Any]:
    result = run_runtime_credential_visibility_diagnostic(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path / ("with_funder" if include_funder else "missing_funder"),
        environ=_env(include_funder=include_funder),
        generated_at=GENERATED_AT,
    )
    return {
        "runtime_credential_visibility_077c_result": result,
        "runtime_credential_visibility_077c_status_summary": result,
        "signer_diagnostic_evidence_076c_status_summary": {
            "status": "blocked_signer_diagnostic_failed",
            "signer_diagnostic_evidence_ok_for_payload_dry_run": False,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_enabled": False,
            "signer_instantiated": False,
        },
    }


def _adapter(context: Mapping[str, Any]) -> runtime.TelegramOperatorRuntimeAdapter:
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


def test_connection_screen_uses_runtime_credential_visibility_and_redacts_present_values(tmp_path: Path) -> None:
    reply = _adapter(_runtime_visibility_context(tmp_path, include_funder=True)).handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:connection",
    )
    rendered = _rendered(reply)

    assert "Подключение Polymarket" in reply.text
    assert "Статус ключей:" in reply.text
    for label in (
        "API Key: подключен",
        "API Secret: подключен",
        "Passphrase: подключен",
        "Private Key: подключен",
        "Wallet Address: подключен",
        "Signature Type: подключен",
        "Funder Address: подключен",
        "Bot Token: подключен",
        "Operator IDs: подключен",
    ):
        assert label in reply.text
    assert "длина " in reply.text
    assert "отпечаток sha256:" in reply.text
    for raw in (
        RAW_API_KEY,
        RAW_API_SECRET,
        RAW_PASSPHRASE,
        RAW_PRIVATE_KEY,
        RAW_WALLET,
        RAW_FUNDER,
        RAW_TOKEN,
        RAW_OPERATOR_IDS,
    ):
        assert raw not in rendered


def test_missing_funder_address_is_clear_and_balance_routes_to_connection(tmp_path: Path) -> None:
    adapter = _adapter(_runtime_visibility_context(tmp_path, include_funder=False))

    connection = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:connection")
    balance = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:balance")

    assert "Wallet Address: подключен" in connection.text
    assert "Funder Address: не подключен" in connection.text
    assert "Funder Address не указан." in connection.text
    assert "Для некоторых проверок Polymarket может потребоваться funder/proxy wallet address." in connection.text
    assert "Если funder совпадает с wallet address, можно временно использовать тот же адрес." in connection.text
    assert "python -m pm_bot.operator_runner.funder_wallet_context_diagnostic --market BTC --strategy tiny-momentum --dry-run" in connection.text
    assert "Баланс может быть недоступен: не указан Funder Address." in balance.text
    assert "Проверьте раздел Подключение." in balance.text
    assert _labels(balance) == ("🔌 Подключение",)
    assert _callbacks(balance) == ("pmbot:connection",)


def test_refresh_and_instruction_screens_are_registered_and_safe(tmp_path: Path) -> None:
    adapter = _adapter(_runtime_visibility_context(tmp_path, include_funder=False))

    connection = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:connection")
    instruction = adapter.handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:connection:instruction",
    )

    assert CALLBACK_COMMAND_MAP["pmbot:connection:check"] == "/connection_check"
    assert _labels(connection) == ("🔄 Проверить снова", "📘 Инструкция", "💰 Перейти к балансу", "⬅️ Главное меню")
    assert "POLYMARKET_API_KEY" in instruction.text
    assert "POLYMARKET_API_SECRET" in instruction.text
    assert "POLYMARKET_API_PASSPHRASE" in instruction.text
    assert "POLYMARKET_PRIVATE_KEY" in instruction.text
    assert "POLYMARKET_WALLET_ADDRESS" in instruction.text
    assert "POLYMARKET_SIGNATURE_TYPE" in instruction.text
    assert "POLYMARKET_FUNDER_ADDRESS" in instruction.text
    assert "PMBOT_TELEGRAM_BOT_TOKEN" in instruction.text
    assert "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS" in instruction.text
    assert (
        "python -m pm_bot.operator_runner.runtime_credential_visibility_diagnostic --market BTC --strategy tiny-momentum --dry-run"
        in instruction.text
    )
    assert "Никогда не отправляйте private key/API secret/passphrase в Telegram chat." in instruction.text
    assert RAW_API_SECRET not in _rendered(instruction)


def test_launch_blocks_when_credential_or_signer_chain_is_incomplete(tmp_path: Path) -> None:
    adapter = _adapter(_runtime_visibility_context(tmp_path, include_funder=False))

    launch = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch")
    prelaunch = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:start")

    assert "Запуск пока недоступен: требуется завершить подключение и проверку подписи." in launch.text
    assert "Запуск пока недоступен: требуется завершить подключение и проверку подписи." in prelaunch.text
    assert "allowed_for_live" not in launch.text
    assert "allowed_for_live" not in prelaunch.text
    assert prelaunch.summary["order_submission_enabled"] is False
    assert prelaunch.summary["signing_enabled"] is False


def test_primary_menu_same_message_navigation_and_no_live_controls(tmp_path: Path) -> None:
    adapter = _adapter(_runtime_visibility_context(tmp_path, include_funder=False))
    reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:connection")
    query = FakeCallbackQuery()
    message = FakeMessage()

    assert tuple(label for row in HOME_BUTTON_ROWS_BY_LANGUAGE["ru"] for label, _callback in row) == RU_MAIN_MENU_LABELS
    result = asyncio.run(
        runtime.telegram_callback_edit_renderer(query=query, message=message, reply=reply, reply_markup=None)
    )
    assert result == "edited"
    assert len(query.edit_calls) == 1
    assert query.edit_calls[0]["text"] == reply.text
    assert message.reply_calls == []

    records = [
        *SUPPORTED_COMMANDS,
        *SAFE_ACTION_COMMANDS,
        *CALLBACK_COMMAND_MAP.keys(),
        *CALLBACK_COMMAND_MAP.values(),
        *RU_MAIN_MENU_LABELS,
        *_labels(reply),
    ]
    rendered = "\n".join(records).lower()
    for forbidden in (
        "submit-order",
        "cancel-order",
        "send-order",
        "run_signer",
        "pmbot:run:signer",
        "connect-wallet",
        "wallet-connect",
        "approve-live",
    ):
        assert forbidden not in rendered
