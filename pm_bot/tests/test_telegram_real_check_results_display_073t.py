from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_status_registry import (
    TELEGRAM_REAL_CHECK_RESULTS_073T_FLOW_ID,
    STATUS_SOURCES,
    execute_safe_telegram_operator_action,
    safe_action_by_callback,
    safe_action_by_id,
)
from pm_bot.operator_runner.telegram_status_registry import build_telegram_console_context
from pm_bot.trading_core.telegram_real_check_results_display_073t import (
    ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME,
    MINI_APP_SNAPSHOT_FILENAME,
    RESULT_FILENAME,
    SAFETY_SNAPSHOT_FILENAME,
    build_telegram_real_check_results_status,
    telegram_real_check_results_artifact_paths,
    write_telegram_real_check_results_073t_artifacts,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_TOKEN_ID = "12345678901234567890073"
RAW_ACCOUNT = "0x300600000000000000000000000000000000073t"
RAW_SECRET = "raw-secret-073t"
MINI_APP_INDEX = Path("pm_bot/telegram_mini_app/index.html")
MINI_APP_STYLES = Path("pm_bot/telegram_mini_app/styles.css")
ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/telegram_real_check_results_073t")


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


class Completed:
    returncode = 0
    stdout = "Local real-check bundle 072C completed."
    stderr = ""


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_072c_fixture(root: Path) -> None:
    _write_json(
        root / "local_real_check_bundle_072c" / "local_real_check_bundle_072c_result.json",
        {
            "contract_version": "fixture.local_real_check_bundle_072c.v1",
            "status": "local_real_check_bundle_completed_with_blockers_live_blocked",
            "raw_token_id_fixture": RAW_TOKEN_ID,
            "raw_account_fixture": RAW_ACCOUNT,
            "raw_secret_fixture": RAW_SECRET,
            "subchecks": [
                {
                    "subcheck_id": "clob_l2_auth_readonly_probe_067c",
                    "status": "blocked_missing_l2_credentials",
                    "classification": "blocked",
                    "status_fields": {
                        "credential_presence_status": "blocked_missing_l2_credentials",
                        "l2_authenticated_readonly_probe_performed": False,
                    },
                },
                {
                    "subcheck_id": "live_account_readonly_state_probe_070c",
                    "status": "blocked_missing_l2_credentials",
                    "classification": "blocked",
                    "status_fields": {
                        "account_state_probe_performed": False,
                        "account_status": "blocked_missing_l2_credentials",
                    },
                },
                {
                    "subcheck_id": "guarded_signer_diagnostic_smoke_069a",
                    "status": "blocked_diagnostic_not_requested",
                    "classification": "blocked",
                    "status_fields": {
                        "diagnostic_requested": False,
                        "diagnostic_challenge_signed": False,
                        "diagnostic_status": "diagnostic_not_requested",
                    },
                },
                {
                    "subcheck_id": "public_market_token_discovery_071a",
                    "status": "source_backed_candidates_ready",
                    "classification": "reported_success",
                    "status_fields": {
                        "market_candidate_count": 1,
                        "outcome_token_candidate_count": 2,
                    },
                },
                {
                    "subcheck_id": "discovery_to_token_resolver_bridge_071d",
                    "status": "operator_selection_required_multiple_source_backed_candidates",
                    "classification": "blocked",
                    "status_fields": {
                        "operator_selection_required": True,
                        "target_token_id_present": False,
                    },
                },
                {
                    "subcheck_id": "live_readonly_status_aggregator_071b",
                    "status": "live_readonly_status_aggregated",
                    "classification": "reported_success",
                    "status_fields": {
                        "l2_auth_status": "blocked_missing_l2_credentials",
                    },
                },
            ],
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "wallet_connection_attempted": False,
            "signing_attempted": False,
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


def test_073t_missing_artifacts_show_not_run_message(tmp_path: Path) -> None:
    generated = write_telegram_real_check_results_073t_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    status = generated["latest_status"]

    assert status["source_artifact_available"] is False
    assert status["missing_artifacts_message_ru"] == "Проверка ещё не запускалась"
    assert "Проверка ещё не запускалась" in status["status_text_ru"]
    assert "API ключи: не найдены" in status["status_text_ru"]
    assert "L2 auth: не проверено" in status["status_text_ru"]
    assert "Аккаунт: не проверен" in status["status_text_ru"]
    assert "Signer: не проверен" in status["status_text_ru"]
    assert "Рынок: не найден" in status["status_text_ru"]
    assert "Token ID: требуется выбор" in status["status_text_ru"]
    assert "Live: выключен" in status["status_text_ru"]


def test_073t_summarizes_072c_without_raw_values(tmp_path: Path) -> None:
    _write_072c_fixture(tmp_path)
    generated = write_telegram_real_check_results_073t_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    latest = generated["latest_status"]
    rendered = json.dumps(generated, sort_keys=True, ensure_ascii=False)

    assert latest["local_real_check_bundle_072c_artifact_available"] is True
    assert latest["api_keys_display_ru"] == "не найдены"
    assert latest["l2_auth_display_ru"] == "ошибка"
    assert latest["account_display_ru"] == "ошибка"
    assert latest["signer_display_ru"] == "не проверен"
    assert latest["market_display_ru"] == "найден"
    assert latest["token_id_display_ru"] == "требуется выбор"
    assert latest["live_display_ru"] == "выключен"
    assert RAW_TOKEN_ID not in rendered
    assert RAW_ACCOUNT not in rendered
    assert RAW_SECRET not in rendered


def test_073t_telegram_connection_screen_uses_same_message_safe_controls(tmp_path: Path) -> None:
    _write_072c_fixture(tmp_path)
    write_telegram_real_check_results_073t_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:connection")
    rendered = reply.text + "\n" + json.dumps(reply.to_redacted_dict(), sort_keys=True, ensure_ascii=False)

    assert "🔌 Подключение" in reply.text
    assert "API Key: не подключен" in reply.text
    assert "API Secret: не подключен" in reply.text
    assert "Passphrase: не подключен" in reply.text
    assert "Wallet Address: не подключен" in reply.text
    assert "Signature Type: не подключен" in reply.text
    assert "Funder Address: не подключен" in reply.text
    assert _button_labels(reply) == (
        "🔄 Проверить снова",
        "📘 Инструкция",
        "💰 Перейти к балансу",
        "⬅️ Главное меню",
    )
    assert _callback_data(reply) == (
        "pmbot:connection:check",
        "pmbot:connection:instruction",
        "pmbot:balance",
        "pmbot:home",
    )
    for raw in (RAW_TOKEN, RAW_TOKEN_ID, RAW_ACCOUNT, RAW_SECRET):
        assert raw not in rendered

    query = FakeCallbackQuery()
    message = FakeMessage()
    result = asyncio.run(
        runtime.telegram_callback_edit_renderer(query=query, message=message, reply=reply, reply_markup=None)
    )

    assert result == "edited"
    assert len(query.edit_calls) == 1
    assert query.edit_calls[0]["text"] == reply.text
    assert message.reply_calls == []


def test_073t_local_check_button_maps_to_safe_synchronous_dry_run_command() -> None:
    source = next(item for item in STATUS_SOURCES if item.flow_id == TELEGRAM_REAL_CHECK_RESULTS_073T_FLOW_ID)
    action = safe_action_by_callback("pmbot:run:local_real_check_bundle_072c")
    calls: list[dict[str, Any]] = []

    def runner(command: tuple[str, ...], **kwargs: Any) -> Completed:
        calls.append({"command": command, "kwargs": kwargs})
        return Completed()

    result = execute_safe_telegram_operator_action(
        "run_local_real_check_bundle_072c",
        command_runner=runner,
        generated_at=GENERATED_AT,
    )

    assert source.artifact_dir_name == ARTIFACT_DIR_NAME
    assert source.latest_status_filename == LATEST_STATUS_FILENAME
    assert source.context_key == "telegram_real_check_results_073t_status_summary"
    assert CALLBACK_COMMAND_MAP["pmbot:connection"] == "/connection"
    assert action is not None
    assert safe_action_by_id("run_local_real_check_bundle_072c") == action
    assert action.module == "pm_bot.operator_runner.local_real_check_bundle"
    assert action.args == ("--market", "BTC", "--strategy", "tiny-momentum", "--dry-run")
    assert result["status"] == "completed"
    assert calls[0]["kwargs"]["timeout"] == 120
    assert calls[0]["kwargs"]["check"] is False
    assert calls[0]["kwargs"]["capture_output"] is True
    assert calls[0]["command"][1:] == ("-m", "pm_bot.operator_runner.local_real_check_bundle", *action.args)


def test_073t_mini_app_card_and_artifacts_are_static_safe() -> None:
    html = MINI_APP_INDEX.read_text(encoding="utf-8")
    rendered = (html + "\n" + MINI_APP_STYLES.read_text(encoding="utf-8")).lower()

    assert "Подключение" in html
    for phrase in (
        "API Key",
        "API Secret",
        "Passphrase",
        "Signature type",
        "Funder",
        "Баланс недоступен",
        "Аналитика",
        "Позиции",
        "Выбор рынков",
        "Контроль риска",
        "Запуск пока недоступен",
    ):
        assert phrase in html

    assert "<form" not in rendered
    assert "<input" not in rendered
    assert "<script" not in rendered
    assert "<button" not in rendered
    assert "fetch(" not in rendered
    assert "xmlhttprequest" not in rendered
    assert not re.search(r"0x[0-9a-fA-F]{20,}", html)
    assert not re.search(r"\b\d{20,}\b", html)

    for filename in (RESULT_FILENAME, LATEST_STATUS_FILENAME, MINI_APP_SNAPSHOT_FILENAME, SAFETY_SNAPSHOT_FILENAME):
        path = ARTIFACT_DIR / filename
        assert path.exists(), f"missing artifact: {path}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["review_only"] is True
        assert payload["local_artifact_read_only"] is True
        assert payload["network_used"] is False
        assert payload["authenticated_request_performed"] is False
        assert payload["wallet_connection_attempted"] is False
        assert payload["signing_attempted"] is False
        assert payload["order_submission_attempted"] is False
        assert payload["order_cancellation_attempted"] is False
        assert payload["allowed_for_live"] is False


def test_073t_artifact_paths_and_direct_builder_contract(tmp_path: Path) -> None:
    _write_072c_fixture(tmp_path)
    status = build_telegram_real_check_results_status(artifact_root=tmp_path, generated_at=GENERATED_AT)
    paths = telegram_real_check_results_artifact_paths(tmp_path / ARTIFACT_DIR_NAME)

    assert paths["result"].name == RESULT_FILENAME
    assert paths["latest_status"].name == LATEST_STATUS_FILENAME
    assert status["contract_version"] == "pmbot_telegram_real_check_results_status_073t.v1"
    assert status["status_text_ru"].splitlines() == [
        "🔐 Проверка подключения",
        "API ключи: не найдены",
        "L2 auth: ошибка",
        "Аккаунт: ошибка",
        "Signer: не проверен",
        "Рынок: найден",
        "Token ID: требуется выбор",
        "Live: выключен",
    ]
