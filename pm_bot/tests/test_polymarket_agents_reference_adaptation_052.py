from __future__ import annotations

import ast
import socket
from pathlib import Path

from pm_bot.trading_core.polymarket_market_models import (
    DONOR_REFERENCE_COMMIT,
    DONOR_REFERENCE_LICENSE,
    DONOR_REFERENCE_REPOSITORY,
    PAPER_FILTER_PASSED,
    normalize_polymarket_market_payload,
    paper_tradeable_filter_status,
    summarize_normalized_polymarket_market,
    validate_normalized_polymarket_market,
)
from pm_bot.trading_core.polymarket_public_market_data import (
    DEFAULT_FIXTURE_SOURCE,
    build_btc_polymarket_style_fixture_payload,
    load_polymarket_public_market_snapshot,
    to_btc_connector_fixture_payload,
)

GENERATED_AT = "2026-05-14T00:00:00Z"

AUDIT_DOC = Path("docs/ORCH_PMBOT_TRADING_MVP_052_POLYMARKET_AGENTS_REFERENCE_AUDIT.md")

DONOR_FORBIDDEN_IMPORT_NAMES = {
    "POLYGON_WALLET_PRIVATE_KEY",
    "Signer",
    "OrderBuilder",
    "build_signed_order",
    "create_and_post_order",
    "create_market_order",
    "post_order",
    "execute_market_order",
    "send_raw_transaction",
    "sign_transaction",
}

NEW_RUNTIME_FILES = (
    Path("pm_bot/trading_core/polymarket_market_models.py"),
    Path("pm_bot/trading_core/polymarket_public_market_data.py"),
    Path("pm_bot/trading_core/paper_canary_drill.py"),
    Path("pm_bot/operator_runner/paper_canary_drill.py"),
)

FORCED_FALSE_FIELDS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
)


def test_reference_audit_exists_and_classifies_safe_fixture_future_and_forbidden_components() -> None:
    text = AUDIT_DOC.read_text(encoding="utf-8")

    for heading in (
        "## safe_to_adapt_now",
        "## adapt_as_fixture_only",
        "## reference_only_for_future_live_enablement",
        "## forbidden_in_this_task",
    ):
        assert heading in text
    assert "agents/polymarket/gamma.py" in text
    assert "agents/utils/objects.py" in text
    assert "Gamma public market/event metadata patterns" in text
    assert "Market/event normalization ideas" in text
    assert "CLI/operator command structure ideas" in text
    assert "RAG/search/news architecture ideas" in text
    for forbidden_name in DONOR_FORBIDDEN_IMPORT_NAMES:
        assert f"`{forbidden_name}`" in text
    assert "MIT" in text
    assert "No donor live execution, wallet, signing, or order submission code was imported" in text


def test_btc_polymarket_style_fixture_normalizes_to_paper_safe_market_model() -> None:
    fixture = build_btc_polymarket_style_fixture_payload(fetched_at=GENERATED_AT)
    market = normalize_polymarket_market_payload(
        fixture,
        source=DEFAULT_FIXTURE_SOURCE,
        fetched_at=GENERATED_AT,
        fixture_mode=True,
        generated_at=GENERATED_AT,
    )
    summary = summarize_normalized_polymarket_market(market)

    assert validate_normalized_polymarket_market(market, generated_at=GENERATED_AT)["valid"] is True
    assert market["market_id"] == "pm-agents-052-btc-fixture-market"
    assert market["condition_id"] == "pm-agents-052-btc-fixture-condition"
    assert market["slug"] == "btc-paper-canary-fixture-052"
    assert market["outcomes"] == ["Yes", "No"]
    assert market["outcome_prices"] == [0.52, 0.48]
    assert market["clob_token_ids"] == [
        "pm-agents-052-btc-yes-token",
        "pm-agents-052-btc-no-token",
    ]
    assert paper_tradeable_filter_status(market) == PAPER_FILTER_PASSED
    assert summary["paper_tradeable_filter_status"] == PAPER_FILTER_PASSED
    assert market["source"] == DEFAULT_FIXTURE_SOURCE
    assert market["fixture_mode"] is True
    assert market["donor_reference_repository"] == DONOR_REFERENCE_REPOSITORY
    assert market["donor_reference_commit"] == DONOR_REFERENCE_COMMIT
    assert market["donor_reference_license"] == DONOR_REFERENCE_LICENSE
    for field in FORCED_FALSE_FIELDS:
        assert market[field] is False
        assert summary[field] is False


def test_public_market_snapshot_is_fixture_only_and_btc_connector_compatible() -> None:
    snapshot = load_polymarket_public_market_snapshot(
        market="BTC",
        fetched_at=GENERATED_AT,
        generated_at=GENERATED_AT,
    )
    connector_payload = snapshot["btc_connector_fixture_payload"]

    assert snapshot["snapshot_status"] == "fixture_snapshot_ready"
    assert snapshot["market"] == "BTC"
    assert snapshot["fixture_mode"] is True
    assert snapshot["network_check_requested"] is False
    assert snapshot["network_used"] is False
    assert snapshot["external_api_calls_performed"] is False
    assert connector_payload["id"] == "pm-agents-052-btc-fixture-market"
    assert connector_payload["active"] is True
    assert connector_payload["closed"] is False
    assert connector_payload["outcomes"][0]["name"] == "Yes"
    assert connector_payload["bestBid"] == 0.51
    assert connector_payload["bestAsk"] == 0.53
    assert to_btc_connector_fixture_payload(snapshot["normalized_market"], fetched_at=GENERATED_AT) == connector_payload
    for field in FORCED_FALSE_FIELDS:
        assert snapshot[field] is False


def test_network_check_flag_is_explicit_but_still_fixture_only_without_socket(monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("paper canary fixture loader must not open network sockets")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    snapshot = load_polymarket_public_market_snapshot(
        market="BTC",
        network_check=True,
        fetched_at=GENERATED_AT,
        generated_at=GENERATED_AT,
    )

    assert snapshot["network_check_requested"] is True
    assert snapshot["network_check_status"] == "not_implemented_fixture_only"
    assert snapshot["network_used"] is False
    assert snapshot["authenticated_polymarket_enabled"] is False
    assert snapshot["live_connector_enabled"] is False


def test_donor_forbidden_names_are_not_imported_into_new_runtime_paths() -> None:
    imported_names: dict[str, set[str]] = {}
    for path in NEW_RUNTIME_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.update(alias.asname or alias.name for alias in node.names)
        imported_names[str(path)] = names

    for path, names in imported_names.items():
        assert not (names & DONOR_FORBIDDEN_IMPORT_NAMES), path
