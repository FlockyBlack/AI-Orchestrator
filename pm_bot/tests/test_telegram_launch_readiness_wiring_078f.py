from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner.telegram_operator_control_bot import (
    TelegramOperatorControlBot,
    TelegramOperatorControlConfig,
)

GENERATED_AT = "2026-05-17T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"


def _first_supervised_status(**overrides: Any) -> dict[str, Any]:
    status = {
        "contract_version": "pmbot_latest_first_supervised_tiny_order_readiness_077a_status.v1",
        "status": "blocked_signer_diagnostic_not_ok",
        "market": "BTC",
        "market_symbol": "BTC",
        "strategy": "tiny-momentum",
        "strategy_name": "tiny-momentum",
        "selected_candidate_status": "selected_candidate_artifact_recorded",
        "selected_candidate_ready": True,
        "selected_token_verification_status": "selected_token_verified_for_payload_dry_run",
        "selected_token_verified": True,
        "signer_diagnostic_status": "blocked_signer_diagnostic_failed",
        "signer_diagnostic_ok": False,
        "payload_dry_run_readiness_status": "blocked_signer_diagnostic_failed",
        "payload_dry_run_ready": False,
        "risk_engine_status": "blocked_risk_engine_v2_review",
        "risk_engine_ready": False,
        "final_blocker_reducer_status": "blocked_remaining_first_live_order_final_blockers",
        "final_blocker_reducer_clear": False,
        "static_safety_report_status": "passed_with_warnings",
        "static_safety_report_ok": True,
        "explicit_live_authorization_present": False,
        "first_supervised_tiny_order_ready_for_authorization": False,
        "first_supervised_tiny_order_ready_for_execution": False,
        "blocker_count": 1,
        "current_top_blocker": "blocked_signer_diagnostic_not_ok",
        "artifact_path": "pm_bot/trading_core/artifacts/first_supervised_tiny_order_readiness_077a/first_supervised_tiny_order_readiness_077a_result.json",
        "latest_status_path": "pm_bot/trading_core/artifacts/first_supervised_tiny_order_readiness_077a/latest_first_supervised_tiny_order_readiness_077a_status.json",
        "next_recommended_safe_command": "python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge --market BTC --strategy tiny-momentum --dry-run",
        "allowed_for_live": False,
        "order_submission_enabled": False,
        "signing_enabled": False,
        "trading_requested": False,
    }
    status.update(overrides)
    return status


def _payload_readiness_status(**overrides: Any) -> dict[str, Any]:
    status = {
        "contract_version": "pmbot_latest_payload_dry_run_readiness_076d_status.v1",
        "status": "blocked_signer_diagnostic_failed",
        "market": "BTC",
        "market_symbol": "BTC",
        "strategy": "tiny-momentum",
        "strategy_name": "tiny-momentum",
        "selected_candidate_status": "selected_candidate_artifact_recorded",
        "selected_candidate_ready": True,
        "selected_token_verification_status": "selected_token_verified_for_payload_dry_run",
        "selected_token_verified": True,
        "signer_diagnostic_status": "blocked_signer_diagnostic_failed",
        "signer_diagnostic_ok": False,
        "payload_dry_run_status": "selected_token_payload_readiness_not_ready:blocked_signer_diagnostic_failed",
        "payload_dry_run_ready": False,
        "risk_status": "blocked_risk_engine_or_final_reducer",
        "risk_engine_v2_status": "blocked_risk_engine_v2_review",
        "risk_engine_v2_ready": False,
        "final_blocker_reducer_status": "blocked_remaining_first_live_order_final_blockers",
        "final_blocker_reducer_clear": False,
        "static_safety_report_status": "passed_with_warnings",
        "static_safety_report_ok": True,
        "final_blockers": ["blocked_signer_diagnostic_failed"],
        "artifact_path": "pm_bot/trading_core/artifacts/payload_dry_run_readiness_076d/payload_dry_run_readiness_076d_result.json",
        "latest_status_path": "pm_bot/trading_core/artifacts/payload_dry_run_readiness_076d/latest_payload_dry_run_readiness_076d_status.json",
        "allowed_for_live": False,
        "order_submission_enabled": False,
        "signing_enabled": False,
    }
    status.update(overrides)
    return status


def _connected_context() -> dict[str, Any]:
    return {
        "telegram_connection_status_067e_status_summary": {
            "api_keys_added": True,
            "api_keys_status": "added",
            "wallet_display": "0x3006...0760",
            "signature_type_display": "3",
            "funder_display": "0x1111...0760",
            "credential_values_read": False,
            "raw_values_emitted": False,
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_enabled": False,
        },
        "telegram_balance_readonly_status_077f_status_summary": {
            "contract_version": "pmbot_telegram_balance_readonly_status_077f.v1",
            "status": "balance_readonly_account_probe_blocked_sdk_unavailable",
            "screen_variant": "account_probe_blocked_sdk_unavailable",
            "screen_available": True,
            "credentials_visible": True,
            "polymarket_l2_visible": True,
            "wallet_context_complete": True,
            "funder_address_present": True,
            "account_readonly_artifact_available": True,
            "account_probe_blocked_sdk_unavailable": True,
            "account_sdk_status": "sdk_unavailable",
            "allowed_for_live": False,
            "order_submission_enabled": False,
            "signing_enabled": False,
        },
        "payload_dry_run_readiness_076d_status_summary": _payload_readiness_status(),
        "first_supervised_tiny_order_readiness_077a_status_summary": _first_supervised_status(),
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


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def test_launch_screen_uses_077a_076d_readiness_and_user_blockers() -> None:
    adapter = _adapter(_connected_context())
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:limit:5")
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:max_loss:2")
    adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:market:btc")

    launch = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch")

    assert "Запуск пока недоступен: требуется завершить проверки." in launch.text
    assert "Лимит на день: $5" in launch.text
    assert "Максимальный убыток: $2" in launch.text
    assert "Рынки: BTC" in launch.text
    assert "Подключение: готово" in launch.text
    assert "Баланс/аккаунт: SDK недоступен" in launch.text
    assert "Кандидат: выбран" in launch.text
    assert "Token ID: проверен" in launch.text
    assert "Подпись: не проверена" in launch.text
    assert "Payload dry-run: заблокирован" in launch.text
    assert "Risk Engine: требует проверки" in launch.text
    assert "Финальная готовность: заблокирована" in launch.text
    assert "- подпись не проверена" in launch.text
    assert "- SDK баланса недоступен" in launch.text
    assert "- нет финального разрешения на live" in launch.text
    assert _labels(launch) == ("🔄 Обновить", "📋 Подробнее", "🔌 Подключение", "💰 Баланс", "⬅️ Главное меню")
    assert "blocked_signer_diagnostic_failed" not in launch.text
    assert "allowed_for_live" not in launch.text


def test_launch_details_and_legacy_start_remain_no_live() -> None:
    adapter = _adapter(_connected_context())

    details = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:details")
    prelaunch = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch:start")

    assert "📋 Подробнее" in details.text
    assert "077A final readiness: blocked_signer_diagnostic_not_ok" in details.text
    assert "076D payload dry-run: blocked_signer_diagnostic_failed" in details.text
    assert "signer_diagnostic_status: blocked_signer_diagnostic_failed" in details.text
    assert "live authorization: missing" in details.text
    assert "order submission/signing: disabled" in details.text
    assert "Запуск не выполнен: режим no-live." in prelaunch.text
    assert "Запуск пока недоступен: требуется завершить проверки." in prelaunch.text
    assert "trading_requested=false" in prelaunch.text
    assert prelaunch.state["trading_requested"] is False
    assert prelaunch.summary["order_submission_enabled"] is False
    assert prelaunch.summary["signing_enabled"] is False


def test_runtime_context_loads_077a_076d_artifacts_for_launch(tmp_path: Path) -> None:
    _write_json(
        tmp_path
        / "first_supervised_tiny_order_readiness_077a"
        / "latest_first_supervised_tiny_order_readiness_077a_status.json",
        _first_supervised_status(daily_limit="$10", max_loss="$1", selected_markets=["BTC"]),
    )
    _write_json(
        tmp_path / "payload_dry_run_readiness_076d" / "latest_payload_dry_run_readiness_076d_status.json",
        _payload_readiness_status(),
    )
    _write_json(
        tmp_path / "telegram_wallet_auth_status_067e" / "latest_telegram_wallet_auth_status_067e.json",
        _connected_context()["telegram_connection_status_067e_status_summary"],
    )
    _write_json(
        tmp_path / "telegram_balance_readonly_status_077f" / "latest_telegram_balance_readonly_status_077f.json",
        _connected_context()["telegram_balance_readonly_status_077f_status_summary"],
    )

    adapter = runtime.TelegramOperatorRuntimeAdapter(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            artifact_dir=tmp_path,
            generated_at=GENERATED_AT,
        )
    )

    launch = adapter.handle_callback(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", callback_data="pmbot:launch")

    assert "Подпись: не проверена" in launch.text
    assert "Payload dry-run: заблокирован" in launch.text
    assert "Risk Engine: требует проверки" in launch.text
    assert launch.summary["first_supervised_tiny_order_readiness_077a_status_summary"]["status"] == (
        "blocked_signer_diagnostic_not_ok"
    )
    assert launch.summary["payload_dry_run_readiness_076d_status_summary"]["status"] == (
        "blocked_signer_diagnostic_failed"
    )
