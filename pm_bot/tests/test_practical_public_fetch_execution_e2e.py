from __future__ import annotations

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


def _fixture_fetcher(_intent: Mapping[str, Any], _url_safety: Mapping[str, Any]) -> dict:
    return {
        "status_code": 200,
        "final_url": "https://example.org/public-evidence",
        "headers": {"content-type": "text/plain"},
        "body": b"fixture-only public evidence body",
    }


def test_public_fetch_execution_e2e_with_mocked_response(tmp_path: Path) -> None:
    manifest = {
        "contract_version": "pmbot_public_fetch_request_manifest.v1",
        "request_manifest_id": "test-manifest",
        "request_intents": [
            {
                "request_intent_id": "intent-1",
                "market_id": "563650",
                "source_category": "public_static_web_page_placeholder",
                "source_name_or_placeholder": "Example public source",
                "source_reference_or_placeholder": "https://example.org/public-evidence",
                "linked_hypothesis_id": "563650.test.paper_hypothesis",
                "requires_auth": False,
                "trading_or_order_endpoint": False,
                "wallet_or_signing_required": False,
            }
        ],
    }

    summary = execute_controlled_public_fetch(
        approval=_approval(),
        request_manifest=manifest,
        evidence_save_plan={"evidence_save_required": True, "replay_before_analysis_update": True},
        replay_plan={"automatic_analysis_update_allowed": False, "automatic_trading_allowed": False},
        out_dir=tmp_path,
        fetcher=_fixture_fetcher,
        fixture_mode=True,
    )

    assert summary["request_count_succeeded"] == 1
    assert summary["live_fetch_performed"] is False
    assert summary["replay_performed"] is True
    assert (tmp_path / "analysis_update_candidate_report.json").exists()
    assert (tmp_path / "source_learning_public_fetch_pending.json").exists()
    assert (tmp_path / "operator_public_fetch_execution_card.json").exists()
    assert (tmp_path / "public_fetch_execution_safety_scan.result.json").exists()
    assert summary["safety_summary"]["openrouter_calls_performed"] == 0
    assert summary["safety_summary"]["authenticated_endpoints_used"] is False
    assert summary["safety_summary"]["wallet_or_private_key_access"] is False
    assert summary["safety_summary"]["orders_or_trading_actions"] is False
    assert summary["safety_summary"]["runtime_or_dispatcher_changes"] is False
    assert summary["safety_summary"]["market_recommendation_generated"] is False
    assert summary["safety_summary"]["probability_ev_edge_or_side_selection_generated"] is False
    assert summary["safety_summary"]["no_autonomous_training_performed"] is True
    assert summary["safety_summary"]["no_real_trade_decision"] is True
