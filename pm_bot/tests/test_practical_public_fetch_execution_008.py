from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.saved_public_evidence_packet import assert_valid_saved_public_evidence_packet

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_execution_008")
ENRICHMENT_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_url_enrichment_007b")
TASK_ID = "ORCH-PMBOT-PRACTICAL-008-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-WITH-CONCRETE-URL-MANIFEST"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_scoped_approval_artifact_validates() -> None:
    approval = _load(ARTIFACT_DIR / "operator_approval_scoped_public_fetch_008.json")
    manifest = _load(ENRICHMENT_DIR / "enriched_fetch_request_manifest.json")
    executable_ids = {row["request_intent_id"] for row in manifest["executable_request_intents"]}
    executable_markets = {row["market_id"] for row in manifest["executable_request_intents"]}

    assert approval["contract_version"] == "pmbot_scoped_public_read_only_fetch_approval.v1"
    assert approval["approval_for_task_id"] == TASK_ID
    assert approval["approval_status"] == "approved_for_scoped_public_read_only_fetch_only"
    assert approval["max_request_count"] == 5
    assert approval["method_allowed"] == "GET"
    assert approval["public_http_only"] is True
    assert approval["no_authentication"] is True
    assert approval["no_api_keys"] is True
    assert approval["no_cookies"] is True
    assert approval["no_browser_automation"] is True
    assert approval["no_wallet"] is True
    assert approval["no_orders"] is True
    assert approval["no_trading"] is True
    assert approval["save_evidence_before_use"] is True
    assert approval["replay_before_analysis_update"] is True
    assert approval["automatic_analysis_update_allowed"] is False
    assert approval["reusable"] is False
    assert approval["expires_after_task"] is True
    assert set(approval["approved_request_intent_ids"]) == executable_ids
    assert set(approval["approved_market_ids"]) == executable_markets


def test_execution_preflight_exists_and_is_scoped_to_executable_manifest_requests() -> None:
    preflight = _load(ARTIFACT_DIR / "execution_preflight_008.result.json")
    manifest = _load(ENRICHMENT_DIR / "enriched_fetch_request_manifest.json")
    executable_ids = {row["request_intent_id"] for row in manifest["executable_request_intents"]}
    missing_ids = {row["request_intent_id"] for row in manifest["missing_url_request_intents"]}
    blocked_ids = {row["request_intent_id"] for row in manifest["blocked_request_intents"]}
    eligible_ids = {row["request_intent_id"] for row in preflight["eligible_request_intents"]}

    assert preflight["ready_to_execute_public_read_only_fetch"] is True
    assert preflight["executable_request_count"] <= 5
    assert preflight["approved_request_count"] <= 5
    assert preflight["within_request_limit"] is True
    assert preflight["live_fetch_performed"] is False
    assert eligible_ids == executable_ids
    assert eligible_ids.isdisjoint(missing_ids)
    assert eligible_ids.isdisjoint(blocked_ids)


def test_fetch_summary_request_counts_and_safety_flags_are_safe() -> None:
    summary = _load(ARTIFACT_DIR / "fetch_execution_summary_008.result.json")
    result = _load(Path("docs/ORCH_PMBOT_PRACTICAL_008_RESULT.json"))

    assert summary["request_count_attempted"] <= 5
    assert summary["request_count_attempted"] == (
        summary["request_count_succeeded"] + summary["request_count_failed"]
    )
    assert summary["request_count_blocked"] == 0
    assert summary["safety_summary"]["openrouter_calls_performed"] == 0
    assert summary["safety_summary"]["authenticated_endpoints_used"] is False
    assert summary["safety_summary"]["wallet_or_private_key_access"] is False
    assert summary["safety_summary"]["orders_or_trading_actions"] is False
    assert summary["safety_summary"]["market_recommendation_generated"] is False
    assert summary["safety_summary"]["probability_ev_edge_or_side_selection_generated"] is False
    assert result["automatic_analysis_update_performed"] is False


def test_missing_and_blocked_request_intents_are_not_fetched() -> None:
    manifest = _load(ENRICHMENT_DIR / "enriched_fetch_request_manifest.json")
    summary = _load(ARTIFACT_DIR / "fetch_execution_summary_008.result.json")
    fetched_ids = {row["request_intent_id"] for row in summary["fetch_results"]}
    executable_ids = {row["request_intent_id"] for row in manifest["executable_request_intents"]}
    missing_ids = {row["request_intent_id"] for row in manifest["missing_url_request_intents"]}
    blocked_ids = {row["request_intent_id"] for row in manifest["blocked_request_intents"]}

    assert fetched_ids <= executable_ids
    assert fetched_ids.isdisjoint(missing_ids)
    assert fetched_ids.isdisjoint(blocked_ids)


def test_evidence_packets_validate_or_no_fake_evidence_is_created() -> None:
    summary = _load(ARTIFACT_DIR / "fetch_execution_summary_008.result.json")
    evidence_dir = ARTIFACT_DIR / "evidence_packets"
    evidence_paths = [Path(path) for path in summary["evidence_packets_created"]]

    if summary["evidence_packets_created_count"] == 0:
        assert (evidence_dir / "NO_EVIDENCE_CREATED.md").exists()
        marker = _load(evidence_dir / "no_evidence_created.json")
        assert marker["no_fake_evidence_created"] is True
        assert not list(evidence_dir.glob("public_fetch_008_*.json"))
    else:
        assert len(evidence_paths) == summary["evidence_packets_created_count"]
        assert not (evidence_dir / "no_evidence_created.json").exists()
        for path in evidence_paths:
            packet = _load(path)
            assert_valid_saved_public_evidence_packet(packet)
            assert packet["capture_mode"] == "future_public_read_only_fetch"
            assert packet["live_network_used"] is True
            assert packet["auth_used"] is False
            assert packet["credentials_used"] is False
            assert packet["wallet_or_private_key_access"] is False
            assert packet["orders_or_trading_actions"] is False
            assert packet["safe_for_replay"] is True
