from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)
from pm_bot.trading_core.funder_wallet_context_077g import run_funder_wallet_context_diagnostic
from pm_bot.trading_core.live_account_readonly_state_probe import (
    LiveAccountSdkBinding,
    run_live_account_readonly_state_probe,
)
from pm_bot.trading_core.runtime_credential_visibility_077c import (
    run_runtime_credential_visibility_diagnostic,
)

GENERATED_AT = "2026-05-17T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"


def _env(root: Path | None = None) -> dict[str, str]:
    env = {
        "POLYMARKET_API_KEY": "fake-api-key-never-output-078a",
        "POLYMARKET_API_SECRET": "fake-api-secret-never-output-078a",
        "POLYMARKET_API_PASSPHRASE": "fake-passphrase-never-output-078a",
        "POLYMARKET_PRIVATE_KEY": "0x" + "8" * 64,
        "POLYMARKET_WALLET_ADDRESS": "0x300600000000000000000000000000000000078a",
        "POLYMARKET_SIGNATURE_TYPE": "2",
        "PMBOT_TELEGRAM_BOT_TOKEN": "123456:fake-telegram-token-never-output-078a",
        "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS": "123456789,987654321",
    }
    if root is not None:
        env["PMBOT_ARTIFACT_DIR"] = str(root)
    return env


def _missing_sdk() -> LiveAccountSdkBinding:
    return LiveAccountSdkBinding(status="not_available", attempted_modules=())


def _run_diagnostics(environ: Mapping[str, str]) -> None:
    run_runtime_credential_visibility_diagnostic(environ=environ, generated_at=GENERATED_AT)
    run_funder_wallet_context_diagnostic(environ=environ, generated_at=GENERATED_AT)
    run_live_account_readonly_state_probe(
        environ=environ,
        sdk_loader=_missing_sdk,
        generated_at=GENERATED_AT,
    )


def _adapter(context: Mapping[str, Any], artifact_root: Path) -> runtime.TelegramOperatorRuntimeAdapter:
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
            bot_token="123456:fake-telegram-token-never-output-078a",
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            artifact_dir=artifact_root,
            generated_at=GENERATED_AT,
        ),
        context=context,
        bot=bot,
    )


def _rendered(reply: runtime.TelegramRuntimeReply) -> str:
    return reply.text + "\n" + json.dumps(reply.to_redacted_dict(), ensure_ascii=False, sort_keys=True)


def test_default_repo_relative_artifact_subdirs_are_preserved(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    _run_diagnostics(_env())

    default_root = tmp_path / "pm_bot" / "trading_core" / "artifacts"
    assert (
        default_root
        / "runtime_credential_visibility_077c"
        / "runtime_credential_visibility_077c_result.json"
    ).exists()
    assert (
        default_root
        / "funder_wallet_context_077g"
        / "funder_wallet_context_077g_result.json"
    ).exists()
    assert (
        default_root
        / "live_account_readonly_state_probe_070c"
        / "latest_live_account_readonly_state_status_070c.json"
    ).exists()


def test_pmbot_artifact_dir_override_is_shared_by_diagnostics_connection_and_balance(tmp_path: Path) -> None:
    artifact_root = tmp_path / "pmbot_artifacts"
    _run_diagnostics(_env(artifact_root))

    assert (
        artifact_root
        / "runtime_credential_visibility_077c"
        / "runtime_credential_visibility_077c_result.json"
    ).exists()
    assert (
        artifact_root
        / "funder_wallet_context_077g"
        / "latest_funder_wallet_context_077g_status.json"
    ).exists()
    assert (
        artifact_root
        / "live_account_readonly_state_probe_070c"
        / "latest_live_account_readonly_state_status_070c.json"
    ).exists()

    context = runtime.load_runtime_context(artifact_root, generated_at=GENERATED_AT)
    adapter = _adapter(context, artifact_root)
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:lang:ru")
    connection = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:connection")
    balance = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:balance")
    rendered = _rendered(connection) + "\n" + _rendered(balance)

    for label in (
        "API Key: подключен",
        "API Secret: подключен",
        "Passphrase: подключен",
        "Private Key: подключен",
        "Wallet Address: подключен",
        "Signature Type: подключен",
        "Bot Token: подключен",
        "Operator IDs: подключен",
    ):
        assert label in connection.text
    assert "Funder Address: не подключен" in connection.text
    assert "Баланс может быть недоступен: не указан Funder Address." in balance.text
    assert "Баланс недоступен: сначала завершите подключение." not in balance.text

    for raw in _env(artifact_root).values():
        if raw in {str(artifact_root), "2"}:
            continue
        assert raw not in rendered
