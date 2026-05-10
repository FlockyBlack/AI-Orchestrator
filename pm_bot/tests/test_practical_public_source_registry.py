from __future__ import annotations

from pm_bot.practical.public_source_registry import (
    allowed_source_categories,
    blocked_source_categories,
    build_public_source_registry,
    validate_source_category,
)


def test_registry_lists_allowed_and_blocked_categories() -> None:
    registry = build_public_source_registry()

    assert "public_market_metadata_endpoint_placeholder" in allowed_source_categories()
    assert "public_resolution_source_page_placeholder" in allowed_source_categories()
    assert "authenticated_endpoint" in blocked_source_categories()
    assert "trading_endpoint" in blocked_source_categories()
    assert registry["allowed_sources"]
    assert registry["blocked_sources"]


def test_trading_endpoint_category_is_blocked() -> None:
    validation = validate_source_category("trading_endpoint")

    assert validation["allowed"] is False
    assert validation["blocked"] is True


def test_wallet_signing_category_is_blocked() -> None:
    validation = validate_source_category("wallet_signing_endpoint")

    assert validation["allowed"] is False
    assert validation["blocked"] is True


def test_source_category_validation_is_deterministic() -> None:
    first = validate_source_category("public_static_web_page_placeholder")
    second = validate_source_category("public_static_web_page_placeholder")

    assert first == second
    assert first["allowed"] is True
