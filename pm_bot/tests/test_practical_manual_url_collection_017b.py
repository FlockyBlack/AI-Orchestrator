from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pm_bot.practical.manual_public_url_collection import validate_manual_public_url_collection_packet

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_url_collection_017b")
FIXTURE_DIR = Path("pm_bot/tests/fixtures/manual_url_collection_017b")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_unfilled_packet_validates_as_incomplete() -> None:
    packet = _load(ARTIFACT_DIR / "manual_public_url_collection_packet_573656.json")
    result = validate_manual_public_url_collection_packet(packet)

    assert packet["contract_version"] == "pmbot_manual_public_url_collection_packet.v1"
    assert packet["market_id"] == "573656"
    assert packet["operator_fill_required"] is True
    assert packet["filled_url_count"] == 0
    assert packet["missing_url_count"] == 3
    assert len(packet["candidate_urls"]) == 3
    assert all(row["operator_supplied_url"] is None for row in packet["candidate_urls"])
    assert all(row["url_status"] == "missing" for row in packet["candidate_urls"])
    assert result["ready_for_fetch_manifest"] is False
    assert result["filled_url_count"] == 0
    assert result["missing_url_count"] == 3
    assert result["blockers"]


def test_filled_valid_fixture_validates_as_ready_for_manifest() -> None:
    packet = _load(FIXTURE_DIR / "manual_public_url_collection_packet.filled_valid.fixture.json")
    result = validate_manual_public_url_collection_packet(packet)

    assert packet["synthetic_test_only"] is True
    assert packet["not_real_market_urls"] is True
    assert result["filled_url_count"] == 3
    assert result["missing_url_count"] == 0
    assert result["blocked_url_count"] == 0
    assert result["valid_url_count"] == 3
    assert result["ready_for_fetch_manifest"] is True
    assert all(row["url_status"] == "valid_public_http_url" for row in result["candidate_url_results"])


def test_blocked_fixture_flags_blocked_url() -> None:
    packet = _load(FIXTURE_DIR / "manual_public_url_collection_packet.filled_blocked.fixture.json")
    result = validate_manual_public_url_collection_packet(packet)

    assert packet["synthetic_test_only"] is True
    assert result["filled_url_count"] == 3
    assert result["blocked_url_count"] == 1
    assert result["ready_for_fetch_manifest"] is False
    assert any(row["url_status"] == "blocked" for row in result["candidate_url_results"])
    assert any("blocked" in blocker for blocker in result["blockers"])


def test_no_live_fetch_occurs_and_missing_count_is_correct() -> None:
    packet = _load(ARTIFACT_DIR / "manual_public_url_collection_packet_573656.json")
    result = _load(ARTIFACT_DIR / "manual_url_collection_validation_result_017b.json")

    assert packet["live_fetch_performed"] is False
    assert result["live_fetch_performed"] is False
    assert result["missing_url_count"] == 3
    assert result["filled_url_count"] == 0
    assert result["ready_for_fetch_manifest"] is False


def test_manual_url_collection_has_no_unsafe_flags() -> None:
    packet = _load(ARTIFACT_DIR / "manual_public_url_collection_packet_573656.json")
    result = _load(ARTIFACT_DIR / "manual_url_collection_validation_result_017b.json")

    for payload in (packet, result):
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
