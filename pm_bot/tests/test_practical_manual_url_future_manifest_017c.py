from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/manual_url_collection_017c")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_future_manifest_exists_and_counts_match_valid_supplied_urls() -> None:
    validation = _load(ARTIFACT_DIR / "filled_url_validation_result_017c.json")
    manifest_path = ARTIFACT_DIR / "future_fetch_manifest_from_filled_packet_017c.json"
    manifest = _load(manifest_path)

    assert manifest_path.exists()
    assert (ARTIFACT_DIR / "future_fetch_manifest_from_filled_packet_017c.md").exists()
    assert manifest["contract_version"] == "pmbot_manual_url_to_fetch_manifest.v1"
    assert manifest["market_id"] == "573656"
    assert manifest["max_request_count"] == 3
    assert manifest["within_request_limit"] is True
    assert manifest["executable_request_count"] == validation["valid_url_count"] == 3
    assert manifest["missing_url_count"] == 0
    assert manifest["blocked_request_count"] == 0
    assert len(manifest["executable_request_intents"]) == 3
    assert len(manifest["executable_request_intents"]) <= manifest["max_request_count"]


def test_ready_for_operator_approval_depends_on_executable_safe_urls() -> None:
    manifest = _load(ARTIFACT_DIR / "future_fetch_manifest_from_filled_packet_017c.json")
    safety_report = _load(ARTIFACT_DIR / "filled_manifest_url_safety_report_017c.json")

    executable_count = manifest["executable_request_count"]
    all_safe = safety_report["all_executable_urls_pass_safety"]
    expected_ready = executable_count > 0 and all_safe and manifest["missing_url_count"] == 0 and manifest["blocked_request_count"] == 0

    assert manifest["ready_for_operator_approval"] is expected_ready
    assert safety_report["checked_request_count"] == executable_count
    assert safety_report["allowed_count"] == executable_count
    assert safety_report["blocked_count"] == 0
    assert safety_report["missing_url_count"] == 0
    assert safety_report["live_fetch_performed"] is False
    assert all(row["allowed"] is True for row in safety_report["per_request_safety"])


def test_preflight_remains_blocked_until_operator_approval() -> None:
    preflight = _load(ARTIFACT_DIR / "new_market_fetch_preflight_from_filled_urls_017c.result.json")

    assert (ARTIFACT_DIR / "new_market_fetch_preflight_from_filled_urls_017c.md").exists()
    assert preflight["ready_to_execute_public_read_only_fetch"] is False
    assert preflight["would_be_ready_after_operator_approval"] is True
    assert preflight["executable_request_count"] == 3
    assert preflight["request_count_within_limit"] is True
    assert preflight["missing_url_count"] == 0
    assert preflight["blocked_request_count"] == 0
    assert preflight["approval_required"] is True
    assert preflight["approval_granted"] is False
    assert preflight["approval_status"] == "pending"
    assert preflight["live_fetch_performed"] is False
    assert preflight["blockers"] == ["operator approval has not been granted"]
    assert all(row["allowed"] is True for row in preflight["per_request_safety"])


def test_manifest_and_preflight_do_not_perform_network_calls() -> None:
    manifest = _load(ARTIFACT_DIR / "future_fetch_manifest_from_filled_packet_017c.json")
    preflight = _load(ARTIFACT_DIR / "new_market_fetch_preflight_from_filled_urls_017c.result.json")

    for payload in (manifest, preflight):
        assert _flag_values(payload, "live_fetch_performed") <= {False}
        assert _flag_values(payload, "live_network_used") <= {False}
        assert _count_values(payload, "openrouter_calls_performed") <= {0}
        assert _count_values(payload, "new_polymarket_api_calls_performed") <= {0}
        assert _flag_values(payload, "orders_or_trading_actions") <= {False}
        assert _flag_values(payload, "wallet_or_private_key_access") <= {False}


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
