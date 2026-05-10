from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_evidence_plan_017")
PLAN_JSON = ARTIFACT_DIR / "new_market_public_evidence_plan_017.json"

ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
SIGNAL_PATTERN = re.compile(
    r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b",
    re.IGNORECASE,
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_evidence_plan_exists_for_new_market() -> None:
    plan = _load(PLAN_JSON)

    assert (ARTIFACT_DIR / "new_market_public_evidence_plan_017.md").exists()
    assert plan["contract_version"] == "pmbot_new_market_public_evidence_plan.v1"
    assert plan["source_market_id"] == "573656"
    assert plan["source_market_title"] == "Will Bitcoin hit $150k by December 31, 2026?"
    assert plan["linked_hypothesis_id"] == "573656.analysis.ceab64191597.paper_hypothesis"


def test_evidence_plan_is_local_only_and_requires_operator_approval() -> None:
    plan = _load(PLAN_JSON)

    assert plan["operator_approval_required_before_fetch"] is True
    assert plan["live_fetch_performed"] is False
    assert plan["no_real_trade_decision"] is True
    assert plan["safety_summary"]["new_live_fetch_performed"] is False
    assert plan["safety_summary"]["new_polymarket_api_calls_performed"] == 0
    assert plan["safety_summary"]["openrouter_calls_performed"] == 0


def test_missing_url_items_are_reported_when_no_concrete_urls_exist() -> None:
    plan = _load(PLAN_JSON)

    assert plan["concrete_public_urls"] == []
    assert len(plan["missing_url_items"]) >= 3
    assert any(row["source_name"] == "public Bitcoin price reference category" for row in plan["missing_url_items"])


def test_evidence_plan_has_no_unsafe_flags_or_trading_language() -> None:
    plan = _load(PLAN_JSON)
    text = PLAN_JSON.read_text(encoding="utf-8")

    assert _flag_values(plan, "market_recommendation_generated") <= {False}
    assert _flag_values(plan, "probability_ev_edge_or_side_selection_generated") <= {False}
    assert _flag_values(plan, "orders_or_trading_actions") <= {False}
    assert _flag_values(plan, "wallet_or_private_key_access") <= {False}
    _assert_no_unsafe_signal_text(text)


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


def _assert_no_unsafe_signal_text(text: str) -> None:
    for line in text.splitlines():
        lowered = line.lower()
        if any(phrase in lowered for phrase in ("no ", "false", "prohibited", "not generated")):
            continue
        assert ACTION_PATTERN.search(line) is None
        assert SIGNAL_PATTERN.search(line) is None
