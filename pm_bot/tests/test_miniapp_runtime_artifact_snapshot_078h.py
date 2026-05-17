from __future__ import annotations

import re
from pathlib import Path

SCAFFOLD_DIR = Path("pm_bot/telegram_mini_app")
INDEX_HTML = SCAFFOLD_DIR / "index.html"
STYLES_CSS = SCAFFOLD_DIR / "styles.css"

EXPECTED_COMMANDS = (
    "python -m pm_bot.operator_runner.runtime_credential_visibility_diagnostic --market BTC --strategy tiny-momentum --dry-run",
    "python -m pm_bot.operator_runner.funder_wallet_context_diagnostic --market BTC --strategy tiny-momentum --dry-run",
    "python -m pm_bot.operator_runner.live_account_readonly_state_probe --market BTC --strategy tiny-momentum --dry-run",
    "python -m pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet --market BTC --strategy tiny-momentum --dry-run",
)


def _rendered() -> str:
    return INDEX_HTML.read_text(encoding="utf-8") + "\n" + STYLES_CSS.read_text(encoding="utf-8")


def test_078h_static_miniapp_mirrors_runtime_artifact_snapshot_statuses() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    for phrase in (
        "Credential visibility",
        "runtime_credential_visibility_077c",
        "Funder / wallet context",
        "funder_wallet_context_077g",
        "данные берутся из локальных диагностических артефактов",
        "SDK unavailable",
        "account artifact missing",
        "real artifact only",
        "Readiness packet",
        "first supervised tiny order readiness packet",
        "Top blockers",
        "no live start",
        "selected token verified",
        "Signer diagnostic",
        "signer diagnostic status",
        "Payload readiness",
        "Risk engine",
        "Final blocker",
    ):
        assert phrase in html


def test_078h_help_card_lists_only_local_diagnostic_commands() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="help"' in html
    assert "Run commands" in html
    for command in EXPECTED_COMMANDS:
        assert command in html
    assert "Mini App не запускает эти команды" in html
    assert "Оператор выполняет их отдельно в CLI" in html


def test_078h_layout_expands_navigation_for_help_without_scripted_live_surface() -> None:
    rendered = _rendered().lower()
    css = STYLES_CSS.read_text(encoding="utf-8")

    assert "help-card" in css
    assert "command-list" in css
    assert "grid-template-columns: repeat(10" in css
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
        "secret form",
        "submit order",
        "cancel order",
        "sign transaction",
    ):
        assert forbidden not in rendered


def test_078h_snapshot_does_not_show_fake_balance_pnl_or_raw_runtime_values() -> None:
    rendered = INDEX_HTML.read_text(encoding="utf-8").lower()

    for forbidden_value in (
        "$0",
        "0.00",
        "fake balance",
        "fake pnl",
        "realized_pnl",
        "unrealized_pnl",
        "profit:",
        "loss:",
    ):
        assert forbidden_value not in rendered
    assert not re.search(r"0x[0-9a-f]{20,}", rendered)
    assert not re.search(r"\b\d{20,}\b", rendered)
