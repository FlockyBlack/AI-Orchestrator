from __future__ import annotations

import copy
import json
from pathlib import Path

from pm_bot.practical.public_fetch_url_manifest_enrichment import build_enriched_fetch_request_manifest

FIXTURE_PATH = Path("pm_bot/tests/fixtures/public_read_only_fetch_url_enrichment/public_url_mapping.manual_fixture.json")


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _intent(index: int, *, market_id: str = "563650", category: str = "public_static_web_page_placeholder") -> dict:
    return {
        "request_intent_id": f"intent-{index}",
        "market_id": market_id,
        "market_title": "Test market",
        "source_category": category,
        "source_name_or_placeholder": "Test source",
        "source_reference_or_placeholder": f"public_source_placeholder:{category}:{market_id}",
        "expected_evidence_type": "public page snapshot",
        "linked_hypothesis_id": f"{market_id}.hypothesis",
        "requires_auth": False,
        "trading_or_order_endpoint": False,
        "wallet_or_signing_required": False,
        "live_fetch_performed": False,
    }


def _manifest(intents: list[dict]) -> dict:
    return {
        "contract_version": "pmbot_public_fetch_request_manifest.v1",
        "request_manifest_id": "test-manifest",
        "market_ids": sorted({row["market_id"] for row in intents}),
        "request_intents": intents,
    }


def test_placeholder_manifest_entries_become_missing_url_request_intents() -> None:
    result = build_enriched_fetch_request_manifest(original_manifest=_manifest([_intent(1)]))

    assert result["executable_request_count"] == 0
    assert result["missing_url_count"] == 1
    assert result["missing_url_request_intents"][0]["request_intent_id"] == "intent-1"
    assert result["live_fetch_performed"] is False


def test_concrete_https_fixture_url_becomes_executable_request_intent() -> None:
    original = json.loads(
        Path("pm_bot/practical/artifacts/public_read_only_fetch_approval_006/fetch_request_manifest_5_markets.json").read_text(
            encoding="utf-8"
        )
    )

    result = build_enriched_fetch_request_manifest(original_manifest=original, manual_url_mapping_fixture=_fixture())

    assert result["executable_request_count"] == 5
    assert all(row["source_url"].startswith("https://") for row in result["executable_request_intents"])
    assert result["within_request_limit"] is True


def test_auth_trading_wallet_order_looking_urls_become_blocked_request_intents() -> None:
    auth_intent = _intent(1)
    auth_intent["source_reference_or_placeholder"] = "https://user:pass@example.org/login?api_key=secret"
    order_intent = _intent(2)
    order_intent["source_reference_or_placeholder"] = "https://example.org/orders"
    wallet_intent = _intent(3)
    wallet_intent["source_reference_or_placeholder"] = "https://example.org/wallet/sign"

    result = build_enriched_fetch_request_manifest(original_manifest=_manifest([auth_intent, order_intent, wallet_intent]))

    assert result["blocked_request_count"] == 3
    assert result["executable_request_count"] == 0
    assert all(row["blocked_url_present"] is True for row in result["blocked_request_intents"])


def test_request_count_is_capped_at_five_and_omitted_candidates_are_recorded() -> None:
    intents = []
    for index in range(1, 7):
        intent = _intent(index, market_id=str(100000 + index))
        intent["source_reference_or_placeholder"] = f"https://example.org/public-evidence/{index}"
        intents.append(intent)

    result = build_enriched_fetch_request_manifest(original_manifest=_manifest(intents), max_request_count=5)

    assert result["executable_request_count"] == 5
    assert result["omitted_safe_candidate_count"] == 1
    assert result["omitted_safe_candidates"][0]["concrete_public_url_omitted"] is True
    assert "source_url" not in result["omitted_safe_candidates"][0]


def test_no_live_fetch_is_performed_and_required_fields_exist() -> None:
    intent = _intent(1)
    intent["source_reference_or_placeholder"] = "https://example.org/public-evidence"
    result = build_enriched_fetch_request_manifest(original_manifest=_manifest([copy.deepcopy(intent)]))

    for field in (
        "contract_version",
        "executable_request_intents",
        "blocked_request_intents",
        "missing_url_request_intents",
        "request_count_total",
        "executable_request_count",
        "blocked_request_count",
        "missing_url_count",
        "max_request_count",
        "within_request_limit",
        "live_fetch_performed",
    ):
        assert field in result
    assert result["live_fetch_performed"] is False
