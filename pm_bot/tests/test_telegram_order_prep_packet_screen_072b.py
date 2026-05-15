from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_operator_i18n import HOME_BUTTON_ROWS_BY_LANGUAGE
from pm_bot.operator_runner.telegram_status_registry import (
    STATUS_SOURCES,
    TELEGRAM_ORDER_PREP_PACKET_STATUS_072B_FLOW_ID,
    build_telegram_console_context,
    safe_action_by_callback,
    safe_action_by_id,
)
from pm_bot.trading_core.telegram_order_prep_packet_status_072b import (
    ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME,
    RESULT_FILENAME,
    build_telegram_order_prep_packet_status,
    telegram_order_prep_packet_status_artifact_paths,
    write_telegram_order_prep_packet_status_072b_artifacts,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_TOKEN_ID = "12345678901234567890072b"
RAW_ACCOUNT = "0x300600000000000000000000000000000000072b"
RAW_SECRET = "raw-secret-072b"


class FakeCallbackQuery:
    def __init__(self) -> None:
        self.edit_calls: list[dict[str, Any]] = []

    async def edit_message_text(self, **kwargs: Any) -> None:
        self.edit_calls.append(dict(kwargs))


class FakeMessage:
    def __init__(self) -> None:
        self.reply_calls: list[dict[str, Any]] = []

    async def reply_text(self, **kwargs: Any) -> None:
        self.reply_calls.append(dict(kwargs))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_blocked_072a_packet(root: Path) -> None:
    _write_json(
        root / "order_prep_packet_072a" / "latest_order_prep_packet_072a.json",
        {
            "contract_version": "fixture.order_prep_packet_072a.v1",
            "status": "blocked_review_only",
            "market_found": True,
            "market_slug": "fixture-market",
            "token_id_selected": True,
            "selected_token_id": RAW_TOKEN_ID,
            "account_status": "error",
            "account_address": RAW_ACCOUNT,
            "l2_auth_status": "blocked",
            "signer_status": "error",
            "approval_required": True,
            "payload_dry_run_status": "blocked",
            "raw_secret_fixture": RAW_SECRET,
            "order_submission_enabled": False,
            "live_trading_enabled": False,
            "review_only": True,
        },
    )


def _adapter(*, context: Mapping[str, Any]) -> runtime.TelegramOperatorRuntimeAdapter:
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


def _button_labels(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.label for row in reply.keyboard.rows for button in row)


def _callback_data(reply: runtime.TelegramRuntimeReply) -> tuple[str, ...]:
    return tuple(button.callback_data for row in reply.keyboard.rows for button in row if button.callback_data)


def test_072b_missing_072a_artifact_shows_packet_not_built(tmp_path: Path) -> None:
    generated = write_telegram_order_prep_packet_status_072b_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    status = generated["latest_status"]
    paths = telegram_order_prep_packet_status_artifact_paths(tmp_path / ARTIFACT_DIR_NAME)

    assert paths["result"].name == RESULT_FILENAME
    assert paths["latest_status"].name == LATEST_STATUS_FILENAME
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert status["order_prep_packet_072a_artifact_available"] is False
    assert status["missing_packet_message_ru"] == "Пакет подготовки ещё не собран"
    assert "Пакет подготовки ещё не собран" in status["status_text_ru"]
    assert "Рынок: не найден" in status["status_text_ru"]
    assert "Token ID: требуется выбор" in status["status_text_ru"]
    assert "Payload dry-run: заблокирован" in status["status_text_ru"]
    assert status["live_trading_enabled"] is False
    assert status["order_submission_enabled"] is False
    assert status["telegram_authenticated_call_performed"] is False


def test_072b_summarizes_blocked_packet_without_raw_values(tmp_path: Path) -> None:
    _write_blocked_072a_packet(tmp_path)
    generated = write_telegram_order_prep_packet_status_072b_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    latest = generated["latest_status"]
    rendered = json.dumps(generated, sort_keys=True, ensure_ascii=False)

    assert latest["order_prep_packet_072a_artifact_available"] is True
    assert latest["market_display_ru"] == "найден"
    assert latest["token_id_display_ru"] == "выбран"
    assert latest["account_display_ru"] == "ошибка"
    assert latest["l2_auth_display_ru"] == "blocked"
    assert latest["signer_display_ru"] == "ошибка"
    assert latest["approval_display_ru"] == "требуется"
    assert latest["payload_dry_run_display_ru"] == "заблокирован"
    assert latest["live_display_ru"] == "выключен"
    assert latest["order_submission_display_ru"] == "выключена"
    assert RAW_TOKEN_ID not in rendered
    assert RAW_ACCOUNT not in rendered
    assert RAW_SECRET not in rendered


def test_072b_telegram_screen_uses_refresh_find_check_back_only(tmp_path: Path) -> None:
    _write_blocked_072a_packet(tmp_path)
    write_telegram_order_prep_packet_status_072b_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    reply = adapter.handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:order_prep_status",
    )

    assert reply.command == "/order_prep_status"
    assert "🧪 Подготовка первого ордера" in reply.text
    assert "Рынок: найден" in reply.text
    assert "Token ID: выбран" in reply.text
    assert "L2 auth: blocked" in reply.text
    assert "Signer: ошибка" in reply.text
    assert "Approval: требуется" in reply.text
    assert "Payload dry-run: заблокирован" in reply.text
    assert "Live: выключен" in reply.text
    assert "Отправка ордера: выключена" in reply.text
    assert _button_labels(reply) == ("🔄 Обновить", "🔎 Найти рынок", "🧪 Проверить подключение", "⬅️ Назад")
    assert _callback_data(reply) == (
        "pmbot:order_prep_status",
        "pmbot:btc",
        "pmbot:connection_status",
        "pmbot:home",
    )


def test_072b_controls_do_not_expose_live_order_sign_wallet_or_fake_accounting(tmp_path: Path) -> None:
    _write_blocked_072a_packet(tmp_path)
    write_telegram_order_prep_packet_status_072b_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    reply = adapter.handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:order_prep_status",
    )
    controls = " ".join([*_button_labels(reply), *_callback_data(reply)]).lower()
    rendered = f"{reply.text}\n{controls}".lower()

    for forbidden_control in (
        "submit",
        "cancel",
        "connect-wallet",
        "connect wallet",
        "unlock-wallet",
        "enable-live",
        "approve-live",
        "trade now",
    ):
        assert forbidden_control not in controls
    for fake_accounting in ("$0", "0.00", "usdc", "order_id", "filled", "profit:", "loss:"):
        assert fake_accounting not in rendered
    assert RAW_TOKEN not in rendered
    assert RAW_TOKEN_ID not in rendered
    assert RAW_ACCOUNT not in rendered
    assert RAW_SECRET not in rendered


def test_072b_same_message_navigation_is_preserved(tmp_path: Path) -> None:
    write_telegram_order_prep_packet_status_072b_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context)
    reply = adapter.handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:order_prep_status",
    )
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


def test_072b_registry_runtime_and_primary_menu_remain_safe() -> None:
    status = build_telegram_order_prep_packet_status(artifact_root=Path("does-not-exist"), generated_at=GENERATED_AT)
    source = next(item for item in STATUS_SOURCES if item.flow_id == TELEGRAM_ORDER_PREP_PACKET_STATUS_072B_FLOW_ID)
    primary_menu_labels = tuple(label for rows in HOME_BUTTON_ROWS_BY_LANGUAGE.values() for row in rows for label, _ in row)
    primary_menu_callbacks = tuple(
        callback for rows in HOME_BUTTON_ROWS_BY_LANGUAGE.values() for row in rows for _, callback in row
    )

    assert source.artifact_dir_name == ARTIFACT_DIR_NAME
    assert source.latest_status_filename == LATEST_STATUS_FILENAME
    assert source.context_key == "telegram_order_prep_packet_status_072b_status_summary"
    assert CALLBACK_COMMAND_MAP["pmbot:order_prep_status"] == "/order_prep_status"
    assert safe_action_by_id("run_order_prep_packet_status_072b") is None
    assert safe_action_by_callback("pmbot:run:order_prep_packet_status_072b") is None
    assert status["local_artifact_read_only"] is True
    assert "🔄 Обновить" not in primary_menu_labels
    assert "🔎 Найти рынок" not in primary_menu_labels
    assert "🧪 Проверить подключение" not in primary_menu_labels
    assert "pmbot:order_prep_status" not in primary_menu_callbacks
    assert "pmbot:connection_status" not in primary_menu_callbacks
