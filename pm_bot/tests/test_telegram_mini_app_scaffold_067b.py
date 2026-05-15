from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

from pm_bot.operator_runner import telegram_operator_runtime as runtime
from pm_bot.operator_runner import telegram_runtime_smoke

GENERATED_AT = "2026-05-15T00:00:00+04:00"
AUTHORIZED_USER_ID = "1001"
RAW_TOKEN = "123456:raw-telegram-token-value"
MINI_APP_URL = "https://example.invalid/pmbot-mini-app"

SCAFFOLD_DIR = Path("pm_bot/telegram_mini_app")
INDEX_HTML = SCAFFOLD_DIR / "index.html"
STYLES_CSS = SCAFFOLD_DIR / "styles.css"
ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/telegram_mini_app_067b")

REQUIRED_MENU_LABELS = (
    "Главная",
    "Подключение",
    "Баланс",
    "Сделки",
    "PnL",
    "Статус",
    "Лимиты",
    "Стоп",
)

FORCED_FALSE_FLAGS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "would_submit_order",
    "wallet_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
)


def _adapter(*, mini_app_url: str = "") -> runtime.TelegramOperatorRuntimeAdapter:
    return runtime.TelegramOperatorRuntimeAdapter(
        config=runtime.TelegramRuntimeConfig(
            bot_token=RAW_TOKEN,
            allowed_operator_ids=(AUTHORIZED_USER_ID,),
            mini_app_url=mini_app_url,
            generated_at=GENERATED_AT,
        ),
        context={
            "telegram_mini_app_operator_panel_summary": {
                "telegram_mini_app_operator_panel_ready": True,
                "panel_artifact_available": True,
                "review_only": True,
                "live_actions_available": False,
                "execution_enabling": False,
                "live_approval": False,
            },
            "tiny_live_canary_gonogo_gate_summary": {
                "overall_decision": "NO_GO",
                "resolved_blocker_count": 0,
                "allowed_for_live": False,
                "canary_executable_now": False,
                "live_execution_approved": False,
                "real_execution_available": False,
                "live_connector_enabled": False,
                "order_submission_enabled": False,
            },
        },
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_static_scaffold_has_ru_dashboard_shell_and_no_client_side_persistence() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    css = STYLES_CSS.read_text(encoding="utf-8")
    lower_html = html.lower()
    rendered = html + "\n" + css

    for label in REQUIRED_MENU_LABELS:
        assert label in html
    for placeholder in (
        "real check results: local static artifacts only; no live controls",
        "balance: not connected",
        "trades: no live data",
        "PnL: unavailable until live trades exist",
        "live mode: disabled",
        "risk limits: tiny mode planned",
    ):
        assert placeholder in html

    assert "<form" not in lower_html
    assert "<input" not in lower_html
    assert "<textarea" not in lower_html
    assert "<script" not in lower_html
    assert "localstorage" not in rendered.lower()
    assert "sessionstorage" not in rendered.lower()
    assert "fetch(" not in rendered.lower()
    assert "xmlhttprequest" not in rendered.lower()


def test_mini_app_button_is_url_marker_driven_and_missing_url_is_graceful(monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    configured = _adapter(mini_app_url=MINI_APP_URL).handle_text(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        text="/panel",
    )
    missing = _adapter().handle_text(user_id=AUTHORIZED_USER_ID, chat_id="chat-1", text="/panel")
    invalid = _adapter(mini_app_url="javascript:alert(1)").handle_text(
        user_id=AUTHORIZED_USER_ID,
        chat_id="chat-1",
        text="/panel",
    )
    first_button = configured.keyboard.rows[0][0]
    redacted = json.dumps(configured.to_redacted_dict(), sort_keys=True)

    assert first_button.label == "Открыть PMBOT"
    assert first_button.web_app_url == MINI_APP_URL
    assert configured.panel_button_url == MINI_APP_URL
    assert configured.panel_button_text == "Открыть PMBOT"
    assert MINI_APP_URL not in redacted
    assert missing.panel_button_url == ""
    assert "Mini App URL не настроен" in missing.text
    assert invalid.panel_button_url == ""
    assert "проверку безопасности" in invalid.text


def test_runtime_config_uses_mini_app_url_marker_without_persisting_raw_value() -> None:
    load_result = runtime.load_runtime_config(
        {
            runtime.TELEGRAM_BOT_TOKEN_ENV: RAW_TOKEN,
            runtime.ALLOWED_OPERATOR_IDS_ENV: AUTHORIZED_USER_ID,
            runtime.TELEGRAM_MINI_APP_URL_ENV: MINI_APP_URL,
        },
        generated_at=GENERATED_AT,
    )
    status = load_result.config.to_redacted_status()
    rendered = json.dumps(status, sort_keys=True)

    assert load_result.ok is True
    assert status["mini_app_url_status"] == "configured"
    assert runtime.TELEGRAM_MINI_APP_URL_ENV == "PMBOT_TELEGRAM_MINI_APP_URL"
    assert MINI_APP_URL not in rendered
    assert RAW_TOKEN not in rendered
    assert AUTHORIZED_USER_ID not in rendered


def test_067b_artifacts_are_passive_and_do_not_store_secret_field_names_or_fake_values() -> None:
    forbidden_secret_field_names = (
        "private_key",
        "api_secret",
        "passphrase",
        "mnemonic",
        "seed_phrase",
        "raw_secret",
        "clob_secret",
    )
    forbidden_runtime_artifact_keys = {
        "balance",
        "balances",
        "pnl",
        "realized_pnl",
        "unrealized_pnl",
        "order_id",
        "fill",
        "fills",
        "position",
        "positions",
    }

    for path in sorted(ARTIFACT_DIR.glob("*.json")):
        text = path.read_text(encoding="utf-8").lower()
        payload = _read_json(path)
        for field_name in forbidden_secret_field_names:
            assert field_name not in text, path
        assert _forbidden_key_paths(payload, forbidden_runtime_artifact_keys) == []

    safety = _read_json(ARTIFACT_DIR / "telegram_mini_app_safety_snapshot_067b.json")
    for flag in FORCED_FALSE_FLAGS:
        assert safety[flag] is False
    assert safety["no_fake_accounting_values"] is True
    assert safety["no_live_trading_controls"] is True
    assert safety["no_secret_value_fields"] is True


def test_menu_and_status_snapshots_match_scaffold_and_webapp_marker_contract() -> None:
    menu = _read_json(ARTIFACT_DIR / "telegram_mini_app_menu_snapshot_067b.json")
    status = _read_json(ARTIFACT_DIR / "latest_telegram_mini_app_status_067b.json")
    labels = tuple(item["label"] for item in menu["menu_items"])

    assert labels == REQUIRED_MENU_LABELS
    assert menu["launch_button"]["label"] == "🖥 Открыть PMBOT"
    assert menu["launch_button"]["env_marker"] == "PMBOT_TELEGRAM_MINI_APP_URL"
    assert menu["launch_button"]["url_marker_driven_only"] is True
    assert status["button_label"] == "🖥 Открыть PMBOT"
    assert status["missing_url_message"] == "Mini App URL не настроен"
    assert status["url_marker_driven_only"] is True
    for flag in FORCED_FALSE_FLAGS:
        assert status[flag] is False


def test_runtime_smoke_reports_marker_status_and_ru_first_launch_button() -> None:
    configured = telegram_runtime_smoke.build_telegram_runtime_smoke_report(
        env={
            runtime.TELEGRAM_BOT_TOKEN_ENV: RAW_TOKEN,
            runtime.ALLOWED_OPERATOR_IDS_ENV: AUTHORIZED_USER_ID,
            runtime.TELEGRAM_MINI_APP_URL_ENV: MINI_APP_URL,
        },
        dependency_checker=lambda: {
            "dependency": "python-telegram-bot",
            "installed": True,
            "status": "installed",
            "error_category": "",
        },
        generated_at=GENERATED_AT,
    )
    missing = telegram_runtime_smoke.build_telegram_runtime_smoke_report(
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

    assert configured["expected_telegram_buttons"]["mini_app_launch_button"] == "Открыть PMBOT"
    assert configured["env_status"]["mini_app_url_env"] == "PMBOT_TELEGRAM_MINI_APP_URL"
    assert configured["env_status"]["mini_app_url_status"] == "configured"
    assert missing["env_status"]["mini_app_url_status"] == "missing"
    assert MINI_APP_URL not in json.dumps(configured, sort_keys=True)


def _forbidden_key_paths(value: Any, forbidden_keys: set[str], path: str = "$") -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            next_path = f"{path}.{key}"
            if str(key).lower() in forbidden_keys:
                paths.append(next_path)
            paths.extend(_forbidden_key_paths(nested, forbidden_keys, next_path))
        return paths
    if isinstance(value, list):
        paths = []
        for index, nested in enumerate(value):
            paths.extend(_forbidden_key_paths(nested, forbidden_keys, f"{path}[{index}]"))
        return paths
    return []
