from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_url_enrichment_007b")


def _load(name: str) -> dict:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def test_enriched_manifest_artifact_exists_and_is_valid() -> None:
    manifest = _load("enriched_fetch_request_manifest.json")

    assert manifest["contract_version"] == "pmbot_enriched_public_fetch_request_manifest.v1"
    assert manifest["executable_request_count"] <= manifest["max_request_count"]
    assert manifest["within_request_limit"] is True
    assert manifest["live_fetch_performed"] is False


def test_url_safety_report_exists_and_is_valid() -> None:
    report = _load("enriched_manifest_url_safety_report.json")

    assert report["contract_version"] == "pmbot_enriched_public_fetch_url_safety_report.v1"
    assert report["checked_request_count"] == report["allowed_count"]
    assert report["live_fetch_performed"] is False
    assert report["global_blockers"] == []


def test_pending_approval_artifact_exists_and_approval_granted_false() -> None:
    approval = _load("scoped_approval_for_enriched_manifest.pending.json")

    assert approval["approval_status"] == "pending"
    assert approval["operator_approval_required"] is True
    assert approval["operator_approval_granted"] is False
    assert approval["live_fetch_performed"] is False


def test_operator_card_exists() -> None:
    card = _load("concrete_url_manifest_operator_card.json")

    assert card["contract_version"] == "pmbot_concrete_url_manifest_operator_card.v1"
    assert card["live_fetch_performed"] is False
    assert "concrete_safe_urls" in card


def test_safety_scan_passes_and_has_no_unsafe_flags() -> None:
    scan = _load("url_enrichment_safety_scan.result.json")

    assert scan["url_enrichment_safety_scan_passed"] is True
    assert scan["safety_ok"] is True
    assert scan["live_fetch_performed"] is False
    assert scan["openrouter_calls_performed"] == 0
    assert scan["polymarket_api_calls_performed"] == 0
    assert scan["authenticated_endpoints_used"] is False
    assert scan["wallet_or_private_key_access"] is False
    assert scan["orders_or_trading_actions"] is False
    assert scan["runtime_or_dispatcher_changes"] is False
    assert scan["market_recommendation_generated"] is False
    assert scan["probability_ev_edge_or_side_selection_generated"] is False
    assert scan["operator_approval_granted"] is False
