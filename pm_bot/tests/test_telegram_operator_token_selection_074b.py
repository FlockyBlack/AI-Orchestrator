from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    CALLBACK_COMMAND_MAP,
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.operator_runner.telegram_status_registry import (
    STATUS_SOURCES,
    TELEGRAM_OPERATOR_TOKEN_SELECTION_074B_FLOW_ID,
    build_telegram_console_context,
    safe_action_by_callback,
    safe_action_by_id,
    telegram_console_button_rows,
)
from pm_bot.trading_core.telegram_operator_token_selection_074b import (
    ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME,
    RESULT_FILENAME,
    build_candidate_cli_instruction,
    build_telegram_operator_token_selection_status,
    telegram_operator_token_selection_artifact_paths,
    write_telegram_operator_token_selection_074b_artifacts,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_TOKEN_ID_1 = "123456789012345678900741"
RAW_TOKEN_ID_2 = "123456789012345678900742"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_073b_candidate_artifact(root: Path) -> None:
    _write_json(
        root / "operator_token_selection_packet_073b" / "operator_token_selection_candidates_073b.json",
        {
            "contract_version": "pmbot_operator_token_selection_candidates_073b.v1",
            "status": "selection_required",
            "candidate_index_base": 0,
            "source_backed_candidate_count": 2,
            "source_backed_candidates": [
                {
                    "candidate_index": 0,
                    "candidate_id": "candidate-074b-1",
                    "market_slug": "btc-up-or-down-074b",
                    "question": "Will BTC close above the local review threshold?",
                    "outcome_name": "Yes",
                    "outcome_index": 0,
                    "token_id": RAW_TOKEN_ID_1,
                    "source_ids": ["public_market_token_discovery_071a"],
                    "source_backed": True,
                    "token_id_source_backed": True,
                    "operator_selectable": True,
                },
                {
                    "candidate_index": 1,
                    "candidate_id": "candidate-074b-2",
                    "market_slug": "btc-up-or-down-074b",
                    "question": "Will BTC close above the local review threshold?",
                    "outcome_name": "No",
                    "outcome_index": 1,
                    "token_id": RAW_TOKEN_ID_2,
                    "source_ids": ["public_market_token_discovery_071a"],
                    "source_backed": True,
                    "token_id_source_backed": True,
                    "operator_selectable": True,
                },
            ],
            "allowed_for_live": False,
            "review_only": True,
            "dry_run_only": True,
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


def test_074b_builds_token_selection_screen_from_073b_artifact_without_raw_token_ids(tmp_path: Path) -> None:
    _write_073b_candidate_artifact(tmp_path)

    generated = write_telegram_operator_token_selection_074b_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    paths = telegram_operator_token_selection_artifact_paths(tmp_path / ARTIFACT_DIR_NAME)
    latest = generated["latest_status"]
    rendered = json.dumps(generated, sort_keys=True, ensure_ascii=False)

    assert paths["result"].name == RESULT_FILENAME
    assert paths["latest_status"].name == LATEST_STATUS_FILENAME
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert latest["telegram_screen_title_ru"] == "🎯 Выбор рынка / Token ID"
    assert latest["source_073b_artifact_available"] is True
    assert latest["source_backed_candidate_count"] == 2
    assert latest["operator_selection_required"] is True
    assert latest["explicit_operator_selection_required"] is True
    assert latest["selection_artifact_write_performed"] is False
    assert latest["telegram_button_selection_writes_local_artifacts"] is False
    assert latest["candidate_list"][0]["market_title"] == "Will BTC close above the local review threshold?"
    assert latest["candidate_list"][0]["outcome_label"] == "Yes"
    assert latest["candidate_list"][0]["source_backed"] is True
    assert latest["candidate_list"][0]["token_id_short"] == "123456...0741"
    assert RAW_TOKEN_ID_1 not in rendered
    assert RAW_TOKEN_ID_2 not in rendered


def test_074b_missing_candidates_stays_review_only_and_selection_required(tmp_path: Path) -> None:
    status = build_telegram_operator_token_selection_status(artifact_root=tmp_path, generated_at=GENERATED_AT)

    assert status["source_backed_candidate_count"] == 0
    assert status["operator_selection_required"] is True
    assert "Кандидаты из локальных artifacts не найдены." in status["status_text_ru"]
    assert status["network_used"] is False
    assert status["order_submission_enabled"] is False
    assert status["signing_enabled"] is False
    assert status["wallet_enabled"] is False
    assert status["live_trading_enabled"] is False


def test_074b_telegram_screen_renders_refresh_candidate_buttons_and_back(tmp_path: Path) -> None:
    _write_073b_candidate_artifact(tmp_path)
    write_telegram_operator_token_selection_074b_artifacts(
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
        callback_data="pmbot:token_selection",
    )

    assert reply.command == "/token_selection"
    assert "🎯 Выбор рынка / Token ID" in reply.text
    assert "Рынок: Will BTC close above the local review threshold?" in reply.text
    assert "Исход: Yes" in reply.text
    assert "Исход: No" in reply.text
    assert "Token ID: 123456...0741" in reply.text
    assert "source-backed: да" in reply.text
    assert "Требуется явный выбор оператора: да" in reply.text
    assert _button_labels(reply) == ("Обновить", "Кандидат 1", "Кандидат 2", "Назад")
    assert _callback_data(reply) == (
        "pmbot:token_selection",
        "pmbot:token_selection:candidate:0",
        "pmbot:token_selection:candidate:1",
        "pmbot:home",
    )
    rendered = f"{reply.text}\n{' '.join(_button_labels(reply))}\n{' '.join(_callback_data(reply))}"
    assert RAW_TOKEN_ID_1 not in rendered
    assert RAW_TOKEN_ID_2 not in rendered


def test_074b_candidate_button_shows_cli_instruction_without_writing_artifacts(tmp_path: Path) -> None:
    _write_073b_candidate_artifact(tmp_path)
    write_telegram_operator_token_selection_074b_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    first_reply = adapter.handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:token_selection:candidate:0",
    )
    reply = adapter.handle_callback(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        callback_data="pmbot:token_selection:candidate:1",
    )

    assert first_reply.command == "/token_candidate_1"
    assert "Кнопка кандидата: 1" in first_reply.text
    assert build_candidate_cli_instruction(0) in first_reply.text
    assert reply.command == "/token_candidate_2"
    assert "Кнопка кандидата: 2" in reply.text
    assert "Запись local selection artifacts: нет" in reply.text
    assert build_candidate_cli_instruction(1) in reply.text
    assert "--candidate-index 1" in reply.text
    assert RAW_TOKEN_ID_1 not in reply.text
    assert RAW_TOKEN_ID_2 not in reply.text


def test_074b_registry_runtime_and_console_menu_remain_safe() -> None:
    source = next(item for item in STATUS_SOURCES if item.flow_id == TELEGRAM_OPERATOR_TOKEN_SELECTION_074B_FLOW_ID)
    labels = tuple(label for row in telegram_console_button_rows("ru") for label, _callback_data in row)

    assert source.artifact_dir_name == ARTIFACT_DIR_NAME
    assert source.latest_status_filename == LATEST_STATUS_FILENAME
    assert source.context_key == "telegram_operator_token_selection_074b_status_summary"
    assert "Выбор рынка / Token ID" in labels
    assert CALLBACK_COMMAND_MAP["pmbot:token_selection"] == "/token_selection"
    assert CALLBACK_COMMAND_MAP["pmbot:token_selection:candidate:0"] == "/token_candidate_1"
    assert CALLBACK_COMMAND_MAP["pmbot:token_selection:candidate:1"] == "/token_candidate_2"
    assert safe_action_by_id("run_operator_token_selection_074b") is None
    assert safe_action_by_callback("pmbot:run:operator_token_selection_074b") is None
