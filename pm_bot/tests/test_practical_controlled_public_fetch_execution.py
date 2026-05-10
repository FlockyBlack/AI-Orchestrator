from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.practical.controlled_public_fetch_execution import execute_controlled_public_fetch
from pm_bot.practical.public_fetch_execution_preflight import TASK_ID


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
        "expires_after_task": True,
        "reusable": False,
    }


def _intent(index: int, url: str = "https://example.org/public-evidence") -> dict:
    return {
        "request_intent_id": f"intent-{index}",
        "market_id": "563650",
        "source_category": "public_static_web_page_placeholder",
        "source_name_or_placeholder": "Example public source",
        "source_reference_or_placeholder": url,
        "linked_hypothesis_id": "563650.test.paper_hypothesis",
        "requires_auth": False,
        "trading_or_order_endpoint": False,
        "wallet_or_signing_required": False,
    }


def _manifest(intents: list[dict]) -> dict:
    return {
        "contract_version": "pmbot_public_fetch_request_manifest.v1",
        "request_manifest_id": "test-manifest",
        "request_intents": intents,
    }


def _evidence_save_plan() -> dict:
    return {"evidence_save_required": True, "replay_before_analysis_update": True}


def _replay_plan() -> dict:
    return {"automatic_analysis_update_allowed": False, "automatic_trading_allowed": False}


def _fixture_fetcher(_intent: Mapping[str, Any], _url_safety: Mapping[str, Any]) -> dict:
    return {
        "status_code": 200,
        "final_url": "https://example.org/public-evidence",
        "headers": {"content-type": "text/plain"},
        "body": b"public fixture response for replay",
    }


def test_zero_fetch_path_works_when_manifest_has_no_concrete_urls(tmp_path: Path) -> None:
    summary = execute_controlled_public_fetch(
        approval=_approval(),
        request_manifest=_manifest([_intent(1, "public_source_placeholder:public_static_web_page_placeholder:563650")]),
        evidence_save_plan=_evidence_save_plan(),
        replay_plan=_replay_plan(),
        out_dir=tmp_path,
    )

    assert summary["live_fetch_performed"] is False
    assert summary["request_count_attempted"] == 0
    assert summary["request_count_blocked"] == 1
    assert (tmp_path / "evidence_packets" / "NO_EVIDENCE_CREATED.md").exists()
    assert (tmp_path / "replay" / "replay_blocked_no_evidence.json").exists()


def test_evidence_packet_created_only_for_successful_fixture_fetch(tmp_path: Path) -> None:
    summary = execute_controlled_public_fetch(
        approval=_approval(),
        request_manifest=_manifest([_intent(1)]),
        evidence_save_plan=_evidence_save_plan(),
        replay_plan=_replay_plan(),
        out_dir=tmp_path,
        fetcher=_fixture_fetcher,
        fixture_mode=True,
    )

    assert summary["request_count_attempted"] == 1
    assert summary["request_count_succeeded"] == 1
    assert summary["request_count_failed"] == 0
    assert summary["replay_performed"] is True
    packet_path = Path(summary["evidence_packets_created"][0])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["capture_mode"] == "fixture"
    assert packet["live_network_used"] is False
    assert packet["safe_for_replay"] is True
