from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/outcome_recheck_source_learning_013")
QUEUE_JSON = ARTIFACT_DIR / "outcome_recheck_queue_013.json"
QUEUE_MD = ARTIFACT_DIR / "outcome_recheck_queue_013.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_outcome_recheck_queue_exists() -> None:
    queue = _load(QUEUE_JSON)

    assert QUEUE_MD.exists()
    assert queue["contract_version"] == "pmbot_outcome_recheck_queue.v1"
    assert queue["queue_id"] == "outcome-recheck-queue-013"


def test_outcome_recheck_queue_tracks_existing_markets() -> None:
    queue = _load(QUEUE_JSON)

    assert queue["tracked_market_count"] >= 5
    assert len(queue["recheck_items"]) >= 5
    assert {row["market_id"] for row in queue["recheck_items"]} >= {
        "563650",
        "597964",
        "598936",
        "691547",
        "692258",
    }


def test_outcome_recheck_queue_keeps_outcomes_unresolved_without_local_resolution() -> None:
    queue = _load(QUEUE_JSON)

    assert queue["unresolved_count"] >= 1
    assert queue["resolved_count"] == 0
    assert queue["ambiguous_count"] == 0
    assert queue["void_count"] == 0
    assert queue["local_resolution_record_count"] == 0
    assert queue["no_local_resolution_available_count"] == queue["tracked_market_count"]
    assert queue["safety_summary"]["outcome_resolution_invented"] is False


def test_recheck_items_include_next_operator_actions() -> None:
    queue = _load(QUEUE_JSON)

    assert all(row["next_operator_action"] for row in queue["recheck_items"])
    assert any(row["recheck_priority"] == "high" for row in queue["recheck_items"])
    assert any(row["update_applied_count"] == 1 for row in queue["recheck_items"])


def test_outcome_recheck_queue_uses_no_live_network() -> None:
    queue = _load(QUEUE_JSON)
    safety = queue["safety_summary"]

    assert safety["live_network_used"] is False
    assert safety["new_live_fetch_performed"] is False
    assert safety["openrouter_calls_performed"] == 0
    assert safety["new_polymarket_api_calls_performed"] == 0
    assert safety["authenticated_endpoints_used"] is False
    assert safety["wallet_or_private_key_access"] is False
    assert safety["orders_or_trading_actions"] is False
