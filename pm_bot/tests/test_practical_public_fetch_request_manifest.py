from __future__ import annotations

import copy
import json
from pathlib import Path

from pm_bot.practical.public_fetch_request_manifest import build_public_fetch_request_manifest

PREP_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_prep_005")


def _fetch_plan() -> dict:
    return json.loads((PREP_DIR / "fetch_plan_5_markets.json").read_text(encoding="utf-8"))


def _link_map() -> dict:
    return json.loads((PREP_DIR / "fetch_plan_to_active_hypotheses_link_map.json").read_text(encoding="utf-8"))


def test_manifest_is_built_from_fetch_plan() -> None:
    plan = _fetch_plan()
    manifest = build_public_fetch_request_manifest(fetch_plan=plan, link_map=_link_map())

    assert manifest["contract_version"] == "pmbot_public_fetch_request_manifest.v1"
    assert manifest["request_intent_count"] == len(plan["requested_sources"])
    assert manifest["market_ids"] == plan["market_ids"]


def test_request_intents_are_local_only_and_non_executable() -> None:
    manifest = build_public_fetch_request_manifest(fetch_plan=_fetch_plan(), link_map=_link_map())

    for intent in manifest["request_intents"]:
        assert intent["market_id"]
        assert intent["requires_auth"] is False
        assert intent["trading_or_order_endpoint"] is False
        assert intent["wallet_or_signing_required"] is False
        assert intent["live_fetch_performed"] is False
        assert intent["linked_hypothesis_id"]


def test_blocked_source_categories_are_marked_blocked() -> None:
    plan = copy.deepcopy(_fetch_plan())
    plan["requested_sources"][0]["source_category"] = "trading_endpoint"

    manifest = build_public_fetch_request_manifest(fetch_plan=plan, link_map=_link_map())
    blocked_intent = manifest["request_intents"][0]

    assert blocked_intent["allowed_by_registry"] is False
    assert blocked_intent["blocked_reason"]
