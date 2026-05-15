from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCAFFOLD_DIR = Path("pm_bot/telegram_mini_app")
INDEX_HTML = SCAFFOLD_DIR / "index.html"
STYLES_CSS = SCAFFOLD_DIR / "styles.css"
ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/telegram_mini_app_product_dashboard_068d")

REQUIRED_ARTIFACTS = (
    "telegram_mini_app_product_dashboard_068d_result.json",
    "latest_telegram_mini_app_product_dashboard_status_068d.json",
    "telegram_mini_app_product_dashboard_menu_snapshot_068d.json",
    "telegram_mini_app_product_dashboard_safety_snapshot_068d.json",
    "telegram_mini_app_product_dashboard_ui_snapshot_068d.json",
)

REQUIRED_SECTIONS = (
    "Подключение",
    "Баланс",
    "Сделки",
    "PnL",
    "Статус",
    "Лимиты",
    "Стоп",
)

REQUIRED_SAFETY_TRUE_FLAGS = (
    "no_secret_inputs",
    "no_secret_persistence",
    "no_live_trading",
    "no_wallet_connection",
    "no_order_submission",
    "no_order_cancel",
    "no_signing",
    "no_fake_balance",
    "no_fake_trades",
    "no_fake_pnl",
)

FORBIDDEN_LIVE_CONTROL_TERMS = (
    "run_signer",
    "pmbot:run:signer",
    "Run Signer",
    "approve-live",
    "send-order",
    "submit-order",
    "cancel-order",
    "connect-wallet",
    "unlock-wallet",
    "live-enable",
    "live-execute",
    "approve live",
    "send order",
    "submit order",
    "cancel order",
    "connect wallet",
    "wallet connect",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _anchor_records(html: str) -> list[str]:
    return re.findall(r"<a\b[^>]*>.*?</a>", html, flags=re.IGNORECASE | re.DOTALL)


def test_static_dashboard_files_exist_and_have_ru_product_shell() -> None:
    assert INDEX_HTML.exists()
    assert STYLES_CSS.exists()

    html = INDEX_HTML.read_text(encoding="utf-8")
    css = STYLES_CSS.read_text(encoding="utf-8")

    assert "PMBOT" in html
    assert "AI-ассистент для Polymarket" in html
    assert "Режим: безопасный / dry-run / review-only" in html
    assert "dashboard-grid" in html
    assert "bottom-nav" in html
    assert "color-scheme: dark" in css
    for label in REQUIRED_SECTIONS:
        assert label in html


def test_dashboard_connection_balance_trades_pnl_status_limits_and_stop_copy() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    for phrase in (
        "Проверка подключения",
        "API ключи",
        "не найдены",
        "L2 auth",
        "ошибка",
        "Аккаунт",
        "Signer",
        "не проверен",
        "Рынок",
        "найден",
        "Token ID",
        "требуется выбор",
        "Проверка ещё не запускалась",
        "Баланс пока не проверен",
        "Запустите read-only проверку подключения",
        "Live-сделок пока не было",
        "Открытые ордера: неизвестно",
        "PnL пока недоступен: live-сделок ещё не было",
        "Live trading",
        "Отправка ордеров",
        "Подписание",
        "allowed_for_live",
        "Max order",
        "&lt;= $1 planned",
        "Max orders/day",
        "Автоторговля",
        "Emergency Stop",
        "Live отмены ордеров в Mini App пока нет",
    ):
        assert phrase in html


def test_dashboard_has_no_secret_forms_inputs_persistence_or_network_code() -> None:
    rendered = (INDEX_HTML.read_text(encoding="utf-8") + "\n" + STYLES_CSS.read_text(encoding="utf-8")).lower()

    assert "<form" not in rendered
    assert "<input" not in rendered
    assert "<textarea" not in rendered
    assert "<script" not in rendered
    assert "type=\"password\"" not in rendered
    assert "name=\"private" not in rendered
    assert "name=\"api" not in rendered
    assert "name=\"passphrase" not in rendered
    assert "name=\"seed" not in rendered
    assert "name=\"mnemonic" not in rendered
    assert "localstorage" not in rendered
    assert "sessionstorage" not in rendered
    assert "fetch(" not in rendered
    assert "xmlhttprequest" not in rendered


def test_dashboard_does_not_render_fake_balance_trades_or_pnl_values() -> None:
    rendered = INDEX_HTML.read_text(encoding="utf-8").lower()

    for forbidden_value in (
        "$0",
        "0.00",
        "usdc",
        "order_id",
        "filled",
        "realized_pnl",
        "unrealized_pnl",
        "profit:",
        "loss:",
    ):
        assert forbidden_value not in rendered
    assert "фейковый баланс не показывается" in rendered
    assert "фейковые сделки не показываются" in rendered
    assert "фейковый pnl не показывается" in rendered


def test_dashboard_shows_disabled_review_only_dry_run_status_without_live_controls() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    rendered = html.lower()

    for phrase in (
        "live trading выключен",
        "review-only",
        "dry-run",
        "allowed_for_live=false",
        "отправка ордеров",
        "выключена",
        "подписание",
        "выключено",
    ):
        assert phrase.lower() in rendered
    assert "<button" not in rendered
    assert "onclick" not in rendered
    for control in FORBIDDEN_LIVE_CONTROL_TERMS:
        assert control.lower() not in rendered
    for anchor in _anchor_records(html):
        assert anchor.lower().count("href=\"#") == 1


def test_068d_artifacts_exist_and_confirm_required_safety_booleans() -> None:
    for filename in REQUIRED_ARTIFACTS:
        path = ARTIFACT_DIR / filename
        assert path.exists(), f"missing artifact: {path}"
        payload = _read_json(path)
        for flag in REQUIRED_SAFETY_TRUE_FLAGS:
            assert payload[flag] is True, f"{path}:{flag}"

    safety = _read_json(ARTIFACT_DIR / "telegram_mini_app_product_dashboard_safety_snapshot_068d.json")
    for flag in (
        "allowed_for_live",
        "live_connector_enabled",
        "order_submission_enabled",
        "wallet_connection_enabled",
        "signing_enabled",
        "signed_payload_generation_enabled",
        "signed_order_generation_enabled",
    ):
        assert safety[flag] is False
    assert safety["resolved_blocker_count"] == 0


def test_menu_snapshot_matches_static_navigation_and_mini_app_launch_contract() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    menu = _read_json(ARTIFACT_DIR / "telegram_mini_app_product_dashboard_menu_snapshot_068d.json")
    labels = tuple(item["label"] for item in menu["menu_items"])

    assert labels == ("Главная", *REQUIRED_SECTIONS)
    assert menu["launch_button"]["label"] == "Открыть PMBOT"
    assert menu["launch_button"]["env_marker"] == "PMBOT_TELEGRAM_MINI_APP_URL"
    assert menu["launch_button"]["url_marker_driven_only"] is True
    for item in menu["menu_items"]:
        assert f'href="#{item["id"]}"' in html
