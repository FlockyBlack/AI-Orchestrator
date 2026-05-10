from __future__ import annotations

import copy

from pm_bot.practical.public_fetch_execution_preflight import TASK_ID, build_execution_preflight


def _approval(max_request_count: int = 5) -> dict:
    return {
        "contract_version": "pmbot_scoped_public_read_only_fetch_approval.v1",
        "approval_id": "test-approval",
        "approval_for_task_id": TASK_ID,
        "approval_status": "approved_for_scoped_public_read_only_fetch_only",
        "approved_scope": {
            "finite_public_read_only_fetch": True,
            "max_request_count": max_request_count,
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


def test_execution_preflight_blocks_without_scoped_approval() -> None:
    approval = _approval()
    approval["approval_status"] = "pending"

    result = build_execution_preflight(
        approval=approval,
        request_manifest=_manifest([_intent(1)]),
        evidence_save_plan=_evidence_save_plan(),
        replay_plan=_replay_plan(),
    )

    assert result["ready_to_execute_public_read_only_fetch"] is False
    assert "approval_status is not approved for scoped public read-only fetch only" in result["blockers"]


def test_execution_preflight_blocks_if_request_count_exceeds_max() -> None:
    intents = [_intent(index) for index in range(1, 7)]

    result = build_execution_preflight(
        approval=_approval(),
        request_manifest=_manifest(intents),
        evidence_save_plan=_evidence_save_plan(),
        replay_plan=_replay_plan(),
    )

    assert result["ready_to_execute_public_read_only_fetch"] is False
    assert "request manifest count exceeds scoped approval max request count" in result["blockers"]


def test_execution_preflight_identifies_executable_vs_blocked_intents() -> None:
    blocked_intent = copy.deepcopy(_intent(2, "public_source_placeholder:public_static_web_page_placeholder:563650"))

    result = build_execution_preflight(
        approval=_approval(),
        request_manifest=_manifest([_intent(1), blocked_intent]),
        evidence_save_plan=_evidence_save_plan(),
        replay_plan=_replay_plan(),
    )

    assert result["ready_to_execute_public_read_only_fetch"] is True
    assert result["approved_request_count"] == 1
    assert result["blocked_request_count"] == 1
    assert result["executable_request_intents"][0]["request_intent_id"] == "intent-1"
    assert result["blocked_request_intents"][0]["request_intent_id"] == "intent-2"
