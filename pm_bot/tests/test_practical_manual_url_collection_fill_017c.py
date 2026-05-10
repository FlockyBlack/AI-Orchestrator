from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_url_collection_017c")

EXPECTED_URLS = {
    "https://www.coingecko.com/en/coins/bitcoin",
    "https://coinmarketcap.com/currencies/bitcoin/",
    "https://polymarket.com/event/when-will-bitcoin-hit-150k",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_filled_packet_artifact_exists_and_has_three_supplied_urls() -> None:
    packet_path = ARTIFACT_DIR / "manual_public_url_collection_packet_573656.filled.json"
    packet = _load(packet_path)

    assert packet_path.exists()
    assert (ARTIFACT_DIR / "manual_public_url_collection_packet_573656.filled.md").exists()
    assert packet["contract_version"] == "pmbot_manual_public_url_collection_packet.v1"
    assert packet["market_id"] == "573656"
    assert packet["supplied_url_count"] == 3
    assert packet["filled_url_count"] == 3
    assert packet["missing_url_count"] == 0
    assert packet["blocked_url_count"] == 0
    assert {row["operator_supplied_url"] for row in packet["candidate_urls"]} == EXPECTED_URLS
    assert all(row["url_status"] == "supplied_pending_validation" for row in packet["candidate_urls"])
    assert all(row["requires_operator_review"] is True for row in packet["candidate_urls"])
    assert packet["live_fetch_performed"] is False


def test_supplied_urls_validate_locally_as_safe_public_urls() -> None:
    result = _load(ARTIFACT_DIR / "filled_url_validation_result_017c.json")

    assert (ARTIFACT_DIR / "filled_url_validation_result_017c.md").exists()
    assert result["supplied_url_count"] == 3
    assert result["filled_url_count"] == 3
    assert result["valid_url_count"] == 3
    assert result["valid_url_count"] >= 2
    assert result["missing_url_count"] == 0
    assert result["blocked_url_count"] == 0
    assert result["ready_for_fetch_manifest"] is True
    assert result["local_validation_only"] is True
    assert result["no_url_fetch_attempted"] is True
    assert result["live_fetch_performed"] is False
    assert result["request_count_within_limit"] is True
    assert not result["blockers"]

    rows = result["candidate_url_results"]
    assert all(row["url_status"] == "valid_public_http_url" for row in rows)
    assert all(row["url_safety_validation"]["allowed"] is True for row in rows)
    assert all(row["url_safety_validation"]["blockers"] == [] for row in rows)
    assert all(row["url_safety_validation"]["method"] == "GET" for row in rows)
    assert {row["operator_supplied_url"] for row in rows} == EXPECTED_URLS


def test_safety_flags_remain_safe_for_filled_packet_and_validation() -> None:
    packet = _load(ARTIFACT_DIR / "manual_public_url_collection_packet_573656.filled.json")
    result = _load(ARTIFACT_DIR / "filled_url_validation_result_017c.json")

    for payload in (packet, result):
        assert _flag_values(payload, "live_fetch_performed") <= {False}
        assert _flag_values(payload, "live_network_used") <= {False}
        assert _flag_values(payload, "authenticated_endpoints_used") <= {False}
        assert _flag_values(payload, "market_recommendation_generated") <= {False}
        assert _flag_values(payload, "probability_ev_edge_or_side_selection_generated") <= {False}
        assert _flag_values(payload, "orders_or_trading_actions") <= {False}
        assert _flag_values(payload, "wallet_or_private_key_access") <= {False}
        assert _count_values(payload, "openrouter_calls_performed") <= {0}
        assert _count_values(payload, "new_polymarket_api_calls_performed") <= {0}


def _flag_values(value: Any, key: str) -> set[Any]:
    found: set[Any] = set()
    if isinstance(value, dict):
        for item_key, item_value in value.items():
            if item_key == key:
                found.add(item_value)
            found.update(_flag_values(item_value, key))
    elif isinstance(value, list):
        for item in value:
            found.update(_flag_values(item, key))
    return found


def _count_values(value: Any, key: str) -> set[Any]:
    found: set[Any] = set()
    if isinstance(value, dict):
        for item_key, item_value in value.items():
            if item_key == key:
                found.add(item_value)
            found.update(_count_values(item_value, key))
    elif isinstance(value, list):
        for item in value:
            found.update(_count_values(item, key))
    return found
