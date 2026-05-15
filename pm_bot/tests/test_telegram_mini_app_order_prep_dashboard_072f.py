from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCAFFOLD_DIR = Path("pm_bot/telegram_mini_app")
INDEX_HTML = SCAFFOLD_DIR / "index.html"
STYLES_CSS = SCAFFOLD_DIR / "styles.css"
ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/telegram_mini_app_order_prep_072f")

REQUIRED_ARTIFACTS = (
    "telegram_mini_app_order_prep_072f_result.json",
    "latest_telegram_mini_app_order_prep_status_072f.json",
    "telegram_mini_app_order_prep_ui_snapshot_072f.json",
    "telegram_mini_app_order_prep_safety_snapshot_072f.json",
)

REQUIRED_TRUE_FLAGS = (
    "static_review_only",
    "local_artifact_read_only",
    "no_network_fetch",
    "no_secret_forms",
    "no_secret_inputs",
    "no_secret_persistence",
    "no_live_trading",
    "no_wallet_connection",
    "no_order_submission",
    "no_order_cancel",
    "no_signing",
    "no_raw_token_id_displayed",
    "no_raw_account_values_displayed",
)

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "live_connector_enabled",
    "order_submission_enabled",
    "order_cancellation_enabled",
    "wallet_connection_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
)

FORBIDDEN_LIVE_CONTROL_TERMS = (
    "run_signer",
    "pmbot:run:signer",
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
    "connect wallet",
    "wallet connect",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _anchor_records(html: str) -> list[str]:
    return re.findall(r"<a\b[^>]*>.*?</a>", html, flags=re.IGNORECASE | re.DOTALL)


def test_072f_order_prep_section_is_static_ru_first_and_visible() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    css = STYLES_CSS.read_text(encoding="utf-8")

    assert 'id="order-prep"' in html
    assert 'href="#order-prep"' in html
    assert "🧪 Подготовка первого ордера" in html
    assert "order-prep-card" in html
    assert "order-prep-list" in css
    assert "grid-template-columns: repeat(9" in css

    for phrase in (
        "Рынок",
        "BTC",
        "из локального 071A artifact",
        "Token ID",
        "не выбран",
        "token_id_present=false",
        "Аккаунт",
        "не проверен",
        "Signer",
        "Approval",
        "Payload dry-run",
        "artifact есть",
        "Live выключен",
        "allowed_for_live=false",
        "Safe placeholder активен для отсутствующих значений",
    ):
        assert phrase in html


def test_072f_section_has_no_forms_scripts_network_fetch_or_live_controls() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    rendered = (html + "\n" + STYLES_CSS.read_text(encoding="utf-8")).lower()

    assert "<form" not in rendered
    assert "<input" not in rendered
    assert "<textarea" not in rendered
    assert "<script" not in rendered
    assert "<button" not in rendered
    assert "onclick" not in rendered
    assert "type=\"password\"" not in rendered
    assert "localstorage" not in rendered
    assert "sessionstorage" not in rendered
    assert "fetch(" not in rendered
    assert "xmlhttprequest" not in rendered
    for control in FORBIDDEN_LIVE_CONTROL_TERMS:
        assert control.lower() not in rendered
    for anchor in _anchor_records(html):
        assert anchor.lower().count("href=\"#") == 1


def test_072f_section_does_not_expose_raw_token_account_or_secret_values() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    order_prep_section = re.search(
        r'<article class="card order-prep-card".*?</article>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert order_prep_section is not None
    rendered = order_prep_section.group(0)

    assert not re.search(r"0x[0-9a-fA-F]{20,}", rendered)
    assert not re.search(r"\b\d{20,}\b", rendered)
    assert "private key" not in rendered.lower()
    assert "api secret" not in rendered.lower()
    assert "mnemonic" not in rendered.lower()
    assert "seed phrase" not in rendered.lower()
    assert "raw value не показан" in rendered


def test_072f_artifacts_exist_and_match_dashboard_status() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    for filename in REQUIRED_ARTIFACTS:
        path = ARTIFACT_DIR / filename
        assert path.exists(), f"missing artifact: {path}"

    latest = _read_json(ARTIFACT_DIR / "latest_telegram_mini_app_order_prep_status_072f.json")
    status = latest["order_prep_status"]

    assert status["market"]["display_ru"] == "BTC"
    assert status["market"]["artifact_available"] is True
    assert status["token_id"]["display_ru"] == "не выбран"
    assert status["token_id"]["token_id_present"] is False
    assert status["account"]["display_ru"] == "не проверен"
    assert status["signer"]["display_ru"] == "выключен"
    assert status["approval"]["display_ru"] == "не проверен"
    assert status["payload_dry_run"]["display_ru"] == "artifact есть"
    assert status["live"]["display_ru"] == "выключен"

    for item in status.values():
        assert item["display_ru"] in html


def test_072f_safety_artifacts_keep_required_boundaries() -> None:
    for filename in REQUIRED_ARTIFACTS:
        payload = _read_json(ARTIFACT_DIR / filename)
        for flag in REQUIRED_TRUE_FLAGS:
            assert payload[flag] is True, f"{filename}:{flag}"
        for flag in REQUIRED_FALSE_FLAGS:
            assert payload[flag] is False, f"{filename}:{flag}"
        assert payload["network_used"] is False
        assert payload["authenticated_request_performed"] is False
        assert payload["wallet_connection_attempted"] is False
        assert payload["signing_attempted"] is False
        assert payload["order_submission_attempted"] is False
        assert payload["order_cancellation_attempted"] is False
        assert payload["real_order_submitted"] is False
        assert payload["real_order_cancelled"] is False
        assert payload["resolved_blocker_count"] == 0

    safety = _read_json(ARTIFACT_DIR / "telegram_mini_app_order_prep_safety_snapshot_072f.json")
    assert safety["status"] == "safe_static_order_prep_dashboard"
    assert safety["source_artifact_reads"] == "committed_json_snapshots_only"
