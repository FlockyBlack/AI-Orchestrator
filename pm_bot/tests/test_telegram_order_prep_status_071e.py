from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    SUPPORTED_COMMANDS,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_status_registry import (
    STATUS_SOURCES,
    TELEGRAM_ORDER_PREP_STATUS_071E_FLOW_ID,
    build_telegram_console_context,
    safe_action_by_callback,
    safe_action_by_id,
)
from pm_bot.trading_core.telegram_order_prep_status_071e import (
    ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME,
    RESULT_FILENAME,
    build_telegram_order_prep_status,
    telegram_order_prep_status_artifact_paths,
    write_telegram_order_prep_status_071e_artifacts,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_TOKEN_ID = "12345678901234567890071e"
RAW_ACCOUNT = "0x300600000000000000000000000000000000071e"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_ready_source_artifacts(root: Path) -> None:
    _write_json(
        root / "public_market_token_discovery_071a" / "latest_public_market_token_discovery_status_071a.json",
        {
            "contract_version": "fixture.public_market_token_discovery_071a.v1",
            "status": "public_market_token_discovery_completed",
            "market_candidate_count": 1,
            "outcome_token_candidate_count": 2,
            "market_slug": "fixture-market",
            "review_only": True,
        },
    )
    _write_json(
        root / "first_order_market_token_resolver_070b" / "latest_first_order_market_token_status_070b.json",
        {
            "contract_version": "fixture.first_order_market_token_resolver_070b.v1",
            "status": "first_order_market_token_ready",
            "market_slug": "fixture-market",
            "target_contract": {
                "token_id": RAW_TOKEN_ID,
                "market_slug": "fixture-market",
            },
            "token_id_present": True,
            "review_only": True,
        },
    )
    _write_json(
        root / "live_account_readonly_state_probe_070c" / "latest_live_account_readonly_state_status_070c.json",
        {
            "contract_version": "fixture.live_account_readonly_state_probe_070c.v1",
            "status": "completed_live_blocked",
            "account_state_probe_performed": True,
            "account_address": RAW_ACCOUNT,
            "review_only": True,
            "order_submission_enabled": False,
        },
    )
    _write_json(
        root / "signed_order_payload_dry_run_070a" / "latest_signed_order_payload_dry_run_status_070a.json",
        {
            "contract_version": "fixture.signed_order_payload_dry_run_070a.v1",
            "status": "order_payload_contract_ready_dry_run_only",
            "order_payload_contract_built": True,
            "payload_contract_fingerprint": "contract-fingerprint-071e",
            "token_id_present": True,
            "token_id": RAW_TOKEN_ID,
            "signing_attempted": False,
            "order_submission_attempted": False,
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


def test_071e_builds_status_from_local_source_artifacts_without_exposing_values(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path)

    generated = write_telegram_order_prep_status_071e_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    paths = telegram_order_prep_status_artifact_paths(tmp_path / ARTIFACT_DIR_NAME)
    latest = generated["latest_status"]
    rendered = json.dumps(generated, sort_keys=True, ensure_ascii=False)

    assert paths["result"].name == RESULT_FILENAME
    assert paths["latest_status"].name == LATEST_STATUS_FILENAME
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert paths["menu_snapshot"].exists()
    assert paths["safety_snapshot"].exists()
    assert latest["market_display_ru"] == "найден"
    assert latest["token_id_display_ru"] == "найден"
    assert latest["account_display_ru"] == "read-only OK"
    assert latest["signature_display_ru"] == "dry-run контракт готов"
    assert latest["order_submission_display_ru"] == "выключена"
    assert latest["live_display_ru"] == "выключен"
    assert "🧪 Подготовка первого ордера" in latest["status_text_ru"]
    assert "Рынок: найден" in latest["status_text_ru"]
    assert latest["local_artifact_read_only"] is True
    assert latest["order_submission_enabled"] is False
    assert latest["live_trading_enabled"] is False
    assert latest["signing_attempted"] is False
    assert latest["wallet_connection_attempted"] is False
    assert RAW_TOKEN_ID not in rendered
    assert RAW_ACCOUNT not in rendered


def test_071e_missing_artifacts_default_to_not_ready_without_probe(tmp_path: Path) -> None:
    status = build_telegram_order_prep_status(artifact_root=tmp_path, generated_at=GENERATED_AT)

    assert status["market_display_ru"] == "не найден"
    assert status["token_id_display_ru"] == "требуется выбор"
    assert status["account_display_ru"] == "не проверен"
    assert status["signature_display_ru"] == "не выполнялась"
    assert status["order_submission_display_ru"] == "выключена"
    assert status["live_display_ru"] == "выключен"
    assert status["market_discovery_artifact_available"] is False
    assert status["token_resolver_artifact_available"] is False
    assert status["account_readonly_artifact_available"] is False
    assert status["signed_payload_dry_run_artifact_available"] is False
    assert status["authenticated_endpoint_call_performed"] is False
    assert status["telegram_authenticated_call_performed"] is False


def test_071e_telegram_screen_renders_ru_status_with_refresh_and_back_only(tmp_path: Path) -> None:
    _write_ready_source_artifacts(tmp_path)
    write_telegram_order_prep_status_071e_artifacts(
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
    labels = _button_labels(reply)
    callbacks = _callback_data(reply)

    assert reply.command == "/order_prep_status"
    assert "🧪 Подготовка первого ордера" in reply.text
    assert "Рынок: найден" in reply.text
    assert "Token ID: найден" in reply.text
    assert "Аккаунт: read-only OK" in reply.text
    assert "Подпись: dry-run контракт готов" in reply.text
    assert "Отправка ордера: выключена" in reply.text
    assert "Live: выключен" in reply.text
    assert labels == ("Обновить статус", "Назад")
    assert callbacks == ("pmbot:order_prep_status", "pmbot:home")
    rendered_controls = " ".join([*labels, *callbacks, reply.text]).lower()
    for technical_label in ("gate", "062p", "provider", "static safety invariant report"):
        assert technical_label not in rendered_controls
    assert "dryrun" not in rendered_controls
    assert "submit" not in rendered_controls
    assert "cancel" not in rendered_controls


def test_071e_status_source_and_command_are_registered_without_run_action() -> None:
    source = next(item for item in STATUS_SOURCES if item.flow_id == TELEGRAM_ORDER_PREP_STATUS_071E_FLOW_ID)

    assert source.artifact_dir_name == ARTIFACT_DIR_NAME
    assert source.latest_status_filename == LATEST_STATUS_FILENAME
    assert source.context_key == "telegram_order_prep_status_071e_status_summary"
    assert "/order_prep_status" in SUPPORTED_COMMANDS
    assert CALLBACK_COMMAND_MAP["pmbot:order_prep_status"] == "/order_prep_status"
    assert safe_action_by_id("run_order_prep_status_071e") is None
    assert safe_action_by_callback("pmbot:run:order_prep_status_071e") is None
