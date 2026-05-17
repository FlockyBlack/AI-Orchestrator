from __future__ import annotations

import re
from pathlib import Path

SCAFFOLD_DIR = Path("pm_bot/telegram_mini_app")
INDEX_HTML = SCAFFOLD_DIR / "index.html"
STYLES_CSS = SCAFFOLD_DIR / "styles.css"


def _rendered() -> str:
    return INDEX_HTML.read_text(encoding="utf-8") + "\n" + STYLES_CSS.read_text(encoding="utf-8")


def test_077h_connection_balance_analytics_launch_readiness_and_stop_panels_are_visible() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    for phrase in (
        "API Key",
        "API Secret",
        "Passphrase",
        "Кошелёк",
        "Funder",
        "Credential visibility",
        "данные берутся из локальных диагностических артефактов",
        "Проверяется в Telegram / CLI",
        "Баланс unavailable до read-only проверки аккаунта",
        "SDK unavailable",
        "account artifact missing",
        "Сегодня",
        "7 дней",
        "30 дней",
        "нет PnL",
        "Лимит на день",
        "Максимальный убыток",
        "selected markets placeholder",
        "финальная проверка требуется",
        "Выбранный токен",
        "selected token verified",
        "Диагностика подписи",
        "Payload readiness",
        "Риск-статус",
        "Финальная готовность",
        "Run commands",
        "runtime_credential_visibility_diagnostic",
        "funder_wallet_context_diagnostic",
        "live_account_readonly_state_probe",
        "first_supervised_tiny_order_readiness_packet",
        "No-live stop marker",
        "Остановка показывает локальный статус",
    ):
        assert phrase in html

    for section_id in ("connection", "balance", "analytics", "launch-stop", "readiness", "help", "stop"):
        assert f'id="{section_id}"' in html


def test_077h_panels_are_static_no_live_and_do_not_collect_or_submit_anything() -> None:
    rendered = _rendered().lower()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<script",
        "<button",
        "onclick",
        "fetch(",
        "xmlhttprequest",
        "connect wallet",
        "wallet connect",
        "private key",
        "api secret input",
        "submit order",
        "cancel order",
        "sign transaction",
        "trading_requested=true",
        "allowed_for_live=true",
    ):
        assert forbidden not in rendered


def test_077h_dashboard_does_not_add_fake_balance_pnl_or_raw_account_values() -> None:
    rendered = INDEX_HTML.read_text(encoding="utf-8").lower()

    for forbidden_value in (
        "$0",
        "0.00",
        "usdc",
        "realized_pnl",
        "unrealized_pnl",
        "profit:",
        "loss:",
    ):
        assert forbidden_value not in rendered
    assert "данные не подставляются" in rendered
    assert "нет pnl" in rendered
    assert not re.search(r"0x[0-9a-f]{20,}", rendered)
    assert not re.search(r"\b\d{20,}\b", rendered)


def test_077h_styles_define_product_cards_without_expanding_navigation_contract() -> None:
    css = STYLES_CSS.read_text(encoding="utf-8")

    for class_name in (
        "launch-list",
        "readiness-card",
        "readiness-list",
        "stop-marker",
        "stop-list",
        "help-card",
        "command-list",
    ):
        assert class_name in css
    assert "grid-template-columns: repeat(10" in css
