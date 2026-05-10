from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.manual_url_to_fetch_manifest import build_future_fetch_manifest_from_manual_packet

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_url_collection_017b")
FIXTURE_DIR = Path("pm_bot/tests/fixtures/manual_url_collection_017b")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_unfilled_packet_creates_zero_executable_intents() -> None:
    packet = _load(ARTIFACT_DIR / "manual_public_url_collection_packet_573656.json")
    manifest = build_future_fetch_manifest_from_manual_packet(packet)

    assert manifest["contract_version"] == "pmbot_manual_url_to_fetch_manifest.v1"
    assert manifest["market_id"] == "573656"
    assert manifest["executable_request_count"] == 0
    assert manifest["missing_url_count"] == 3
    assert manifest["blocked_request_count"] == 0
    assert manifest["ready_for_operator_approval"] is False
    assert manifest["live_fetch_performed"] is False


def test_filled_valid_fixture_creates_executable_intents() -> None:
    packet = _load(FIXTURE_DIR / "manual_public_url_collection_packet.filled_valid.fixture.json")
    manifest = build_future_fetch_manifest_from_manual_packet(packet)

    assert manifest["executable_request_count"] == 3
    assert manifest["missing_url_count"] == 0
    assert manifest["blocked_request_count"] == 0
    assert manifest["ready_for_operator_approval"] is True
    assert all(row["method"] == "GET" for row in manifest["executable_request_intents"])
    assert all(row["live_fetch_performed"] is False for row in manifest["executable_request_intents"])


def test_blocked_fixture_creates_blocked_intents() -> None:
    packet = _load(FIXTURE_DIR / "manual_public_url_collection_packet.filled_blocked.fixture.json")
    manifest = build_future_fetch_manifest_from_manual_packet(packet)

    assert manifest["blocked_request_count"] == 1
    assert manifest["blocked_request_intents"]
    assert manifest["ready_for_operator_approval"] is False
    assert manifest["live_fetch_performed"] is False


def test_max_request_count_is_enforced() -> None:
    packet = _load(FIXTURE_DIR / "manual_public_url_collection_packet.filled_valid.fixture.json")
    manifest = build_future_fetch_manifest_from_manual_packet(packet, max_request_count=2)

    assert manifest["executable_request_count"] == 2
    assert manifest["blocked_request_count"] == 1
    assert manifest["within_request_limit"] is False
    assert any("max_request_count" in row["blocked_reason"] for row in manifest["blocked_request_intents"])
    assert manifest["ready_for_operator_approval"] is False


def test_ready_for_operator_approval_false_if_no_executable_urls() -> None:
    packet = _load(FIXTURE_DIR / "manual_public_url_collection_packet.unfilled.fixture.json")
    manifest = build_future_fetch_manifest_from_manual_packet(packet)

    assert manifest["executable_request_count"] == 0
    assert manifest["ready_for_operator_approval"] is False
    assert manifest["missing_url_count"] == 3


def test_manifest_builder_does_not_perform_network_calls() -> None:
    packet = _load(FIXTURE_DIR / "manual_public_url_collection_packet.filled_valid.fixture.json")
    manifest = build_future_fetch_manifest_from_manual_packet(packet)

    assert manifest["live_fetch_performed"] is False
    assert manifest["safety_summary"]["live_network_used"] is False
    assert manifest["safety_summary"]["openrouter_calls_performed"] == 0
    assert manifest["safety_summary"]["new_polymarket_api_calls_performed"] == 0
    assert manifest["safety_summary"]["orders_or_trading_actions"] is False
    assert manifest["safety_summary"]["wallet_or_private_key_access"] is False
