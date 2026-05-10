from __future__ import annotations

import copy

from pm_bot.practical.public_fetch_execution_preflight import TASK_ID, validate_scoped_operator_approval
from pm_bot.practical.public_fetch_url_safety import validate_public_fetch_request_intent


def _approval() -> dict:
    return {
        "contract_version": "pmbot_scoped_public_read_only_fetch_approval.v1",
        "approval_id": "test-approval",
        "approval_for_task_id": TASK_ID,
        "approval_status": "approved_for_scoped_public_read_only_fetch_only",
        "approved_scope": {
            "finite_public_read_only_fetch": True,
            "max_request_count": 5,
            "approved_market_ids": ["563650", "597964", "598936", "691547", "692258"],
            "save_evidence_before_use": True,
            "replay_before_analysis_update": True,
            "no_authentication": True,
            "no_api_keys": True,
            "no_wallet": True,
            "no_orders": True,
            "no_trading": True,
            "no_scheduler": True,
            "no_background_worker": True,
            "no_browser_automation": True,
        },
        "blocked_scope": [
            "authenticated endpoints",
            "trading endpoints",
            "order endpoints",
            "wallet/signing/private key access",
            "OpenRouter",
            "autonomous execution",
            "polling/scheduler/background worker",
        ],
        "approved_by": "operator",
        "approved_at": "2026-05-10T00:00:00Z",
        "approval_source": "test",
        "expires_after_task": True,
        "reusable": False,
    }


def _intent(url: str = "https://example.org/public-evidence") -> dict:
    return {
        "request_intent_id": "intent-1",
        "market_id": "563650",
        "source_category": "public_static_web_page_placeholder",
        "source_name_or_placeholder": "Example public source",
        "source_reference_or_placeholder": url,
        "linked_hypothesis_id": "563650.test.paper_hypothesis",
        "requires_auth": False,
        "trading_or_order_endpoint": False,
        "wallet_or_signing_required": False,
    }


def test_scoped_approval_validates_and_is_task_scoped_non_reusable() -> None:
    approval = _approval()

    validation = validate_scoped_operator_approval(approval)

    assert validation["valid"] is True
    assert approval["approval_for_task_id"] == TASK_ID
    assert approval["reusable"] is False
    assert approval["expires_after_task"] is True


def test_placeholder_url_is_blocked() -> None:
    intent = _intent("public_source_placeholder:public_static_web_page_placeholder:563650")

    validation = validate_public_fetch_request_intent(intent, max_request_count=5)

    assert validation["allowed"] is False
    assert "source reference is a placeholder, not an explicit URL" in validation["blockers"]


def test_auth_looking_url_is_blocked() -> None:
    intent = _intent("https://user:pass@example.org/login?api_key=secret")

    validation = validate_public_fetch_request_intent(intent, max_request_count=5)

    assert validation["allowed"] is False
    assert "URL must not contain credentials" in validation["blockers"]
    assert "URL path contains blocked auth/trading/wallet hint: login" in validation["blockers"]
    assert "URL query contains sensitive credential-like key: api_key" in validation["blockers"]


def test_trading_order_wallet_looking_url_is_blocked() -> None:
    order_intent = _intent("https://example.org/orders")
    wallet_intent = _intent("https://example.org/wallet/sign")

    order_validation = validate_public_fetch_request_intent(order_intent, max_request_count=5)
    wallet_validation = validate_public_fetch_request_intent(wallet_intent, max_request_count=5)

    assert order_validation["allowed"] is False
    assert "URL path contains blocked auth/trading/wallet hint: orders" in order_validation["blockers"]
    assert wallet_validation["allowed"] is False
    assert "URL path contains blocked auth/trading/wallet hint: wallet" in wallet_validation["blockers"]
    assert "URL path contains blocked auth/trading/wallet hint: sign" in wallet_validation["blockers"]


def test_localhost_private_url_is_blocked_unless_fixture_mode() -> None:
    intent = _intent("http://127.0.0.1/public-fixture")

    blocked = validate_public_fetch_request_intent(intent, max_request_count=5)
    allowed_fixture = validate_public_fetch_request_intent(intent, max_request_count=5, fixture_mode=True)

    assert blocked["allowed"] is False
    assert "localhost/private/internal IP address is blocked" in blocked["blockers"]
    assert allowed_fixture["allowed"] is True
    assert "loopback IP URL allowed only in fixture mode" in allowed_fixture["warnings"]


def test_get_only_and_no_auth_headers_cookies_required() -> None:
    intent = _intent()
    intent["method"] = "POST"
    intent["required_headers"] = {"Authorization": "Bearer token", "Cookie": "session=1"}
    intent["cookies_required"] = True

    validation = validate_public_fetch_request_intent(intent, max_request_count=5)

    assert validation["allowed"] is False
    assert "only GET requests are allowed" in validation["blockers"]
    assert "request intent requires cookies" in validation["blockers"]
    assert "blocked auth/cookie/API-key header requested: Authorization" in validation["blockers"]
    assert "blocked auth/cookie/API-key header requested: Cookie" in validation["blockers"]

    safe_intent = copy.deepcopy(_intent())
    safe_validation = validate_public_fetch_request_intent(safe_intent, max_request_count=5)
    assert safe_validation["allowed"] is True
