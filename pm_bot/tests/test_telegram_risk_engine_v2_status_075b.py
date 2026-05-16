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
from pm_bot.operator_runner.telegram_operator_i18n import HOME_BUTTON_ROWS_BY_LANGUAGE
from pm_bot.operator_runner.telegram_status_registry import (
    STATUS_SOURCES,
    TELEGRAM_RISK_ENGINE_V2_STATUS_075B_FLOW_ID,
    build_telegram_console_context,
    safe_action_by_callback,
    safe_action_by_id,
    telegram_console_button_rows,
)
from pm_bot.trading_core.risk_engine_v2_review import SAFE_CLI_COMMAND
from pm_bot.trading_core.telegram_risk_engine_v2_status_075b import (
    ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME,
    build_telegram_risk_engine_v2_status,
    render_telegram_risk_engine_v2_status_text,
    telegram_risk_engine_v2_status_artifact_paths,
    write_telegram_risk_engine_v2_status_075b_artifacts,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
RAW_SECRET = "raw-secret-risk-engine-v2-075b-never-output"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_074d_status(root: Path) -> None:
    _write_json(
        root / "risk_engine_v2_review_074d" / "latest_risk_engine_v2_review_status_074d.json",
        {
            "contract_version": "pmbot_risk_engine_v2_review_074d.v1",
            "task_id": "ORCH-PMBOT-RISK-ENGINE-V2-074D-REVIEW-NO-LIVE",
            "generated_at": GENERATED_AT,
            "status": "blocked_first_supervised_tiny_order_not_ready",
            "title": "🛡 Risk Engine v2",
            "market": "BTC",
            "strategy": "tiny-momentum",
            "gate_count": 7,
            "remaining_blocker_count": 12,
            "top_blockers": [
                "operator approval is not recorded or consumed",
                "separate live execution authorization is missing",
                "submit, cancel, signing, and wallet actions are forbidden",
            ],
            "unknown_evidence_groups": ["account_balance_allowance"],
            "unknown_group_count": 1,
            "last_artifact_timestamp": GENERATED_AT,
            "last_artifact_path": "pm_bot/trading_core/artifacts/risk_engine_v2_review_074d/latest_risk_engine_v2_review_status_074d.json",
            "source_artifact_available": True,
            "source_artifact_path": "pm_bot/trading_core/artifacts/risk_engine_v2_review_074d/latest_risk_engine_v2_review_status_074d.json",
            "safe_cli_command": SAFE_CLI_COMMAND,
            "allowed_for_live": False,
            "first_supervised_tiny_order_blocked": True,
            "review_only": True,
            "dry_run_only": True,
            "local_artifact_read_only": True,
            "execution_enabling": False,
            "raw_secret_fixture": RAW_SECRET,
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


def test_075b_builds_review_only_status_from_local_074d_artifact(tmp_path: Path) -> None:
    _write_074d_status(tmp_path)

    status = build_telegram_risk_engine_v2_status(artifact_root=tmp_path, generated_at=GENERATED_AT)
    text = render_telegram_risk_engine_v2_status_text(status, language="ru")
    rendered = json.dumps(status, sort_keys=True, ensure_ascii=False) + "\n" + text

    assert status["title"] == "🛡 Risk Engine v2"
    assert status["allowed_for_live"] is False
    assert status["first_supervised_tiny_order_blocked"] is True
    assert status["gate_count"] == 7
    assert status["remaining_blocker_count"] == 12
    assert status["unknown_evidence_groups"] == ["account_balance_allowance"]
    assert "allowed_for_live=false" in text
    assert "first_supervised_tiny_order_blocked=true" in text
    assert "gate_count=7" in text
    assert "remaining_blocker_count=12" in text
    assert SAFE_CLI_COMMAND in text
    assert RAW_SECRET not in rendered


def test_075b_writes_status_mini_app_and_safety_artifacts(tmp_path: Path) -> None:
    _write_074d_status(tmp_path)

    generated = write_telegram_risk_engine_v2_status_075b_artifacts(
        artifact_root=tmp_path,
        output_dir=tmp_path / ARTIFACT_DIR_NAME,
        generated_at=GENERATED_AT,
    )
    paths = telegram_risk_engine_v2_status_artifact_paths(tmp_path / ARTIFACT_DIR_NAME)

    assert paths["latest_status"].name == LATEST_STATUS_FILENAME
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert paths["mini_app_snapshot"].exists()
    assert paths["safety_snapshot"].exists()
    assert generated["mini_app_snapshot"]["no_network_fetch"] is True
    assert generated["mini_app_snapshot"]["no_live_controls"] is True
    assert generated["safety_snapshot"]["telegram_primary_menu_unchanged"] is True
    assert generated["latest_status"]["allowed_for_live"] is False


def test_075b_telegram_status_details_flow_reaches_risk_engine_without_primary_menu_clutter(tmp_path: Path) -> None:
    _write_074d_status(tmp_path)
    context = build_telegram_console_context(artifact_root=tmp_path, generated_at=GENERATED_AT)
    adapter = _adapter(context=context)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")

    status_reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:bot_status")
    risk_reply = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:risk_engine_v2")

    assert "🛡 Risk Engine v2" in _button_labels(status_reply)
    assert risk_reply.command == "/risk_engine_v2"
    assert "🛡 Risk Engine v2" in risk_reply.text
    assert "allowed_for_live=false" in risk_reply.text
    assert "first_supervised_tiny_order_blocked=true" in risk_reply.text
    assert "remaining_blocker_count=12" in risk_reply.text
    assert SAFE_CLI_COMMAND in risk_reply.text
    assert RAW_SECRET not in risk_reply.text

    ru_primary = tuple(label for row in HOME_BUTTON_ROWS_BY_LANGUAGE["ru"] for label, _callback in row)
    assert ru_primary == (
        "🔐 Подключение",
        "💰 Баланс",
        "📊 Сделки",
        "📈 PnL",
        "⚙️ Лимиты",
        "🤖 Статус",
        "🖥 Mini App",
        "🌐 Язык",
        "🚨 Стоп",
    )
    assert "🛡 Risk Engine v2" not in ru_primary
    assert CALLBACK_COMMAND_MAP["pmbot:risk_engine_v2"] == "/risk_engine_v2"


def test_075b_registry_console_and_mini_app_static_section_remain_safe() -> None:
    source = next(item for item in STATUS_SOURCES if item.flow_id == TELEGRAM_RISK_ENGINE_V2_STATUS_075B_FLOW_ID)
    console_labels = tuple(label for row in telegram_console_button_rows("ru") for label, _callback_data in row)
    html = Path("pm_bot/telegram_mini_app/index.html").read_text(encoding="utf-8")
    css = Path("pm_bot/telegram_mini_app/styles.css").read_text(encoding="utf-8")
    rendered = (html + "\n" + css).lower()

    assert source.artifact_dir_name == ARTIFACT_DIR_NAME
    assert source.latest_status_filename == LATEST_STATUS_FILENAME
    assert source.context_key == "telegram_risk_engine_v2_status_075b_status_summary"
    assert "🛡 Risk Engine v2" in console_labels
    assert safe_action_by_id("run_risk_engine_v2_review") is None
    assert safe_action_by_callback("pmbot:run:risk_engine_v2_review") is None
    assert 'id="risk-engine-v2"' in html
    assert "first_supervised_tiny_order_blocked" in html
    assert SAFE_CLI_COMMAND in html
    assert "<form" not in rendered
    assert "<input" not in rendered
    assert "<script" not in rendered
    assert "fetch(" not in rendered
    assert "connect-wallet" not in rendered
    assert "submit-order" not in rendered
    assert "cancel-order" not in rendered
