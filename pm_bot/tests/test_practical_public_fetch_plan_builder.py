from __future__ import annotations

import socket
from pathlib import Path

from pm_bot.practical.public_fetch_plan_builder import TRACKED_MARKET_IDS, build_fetch_plan_from_queue
from pm_bot.practical.public_read_only_fetch_contract import validate_fetch_plan

QUEUE = Path("pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json")
DEP_MAP = Path("pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.source_dependency_map.json")


def test_fetch_plan_built_from_real_market_batch_004_queue() -> None:
    plan = build_fetch_plan_from_queue(queue_path=QUEUE, source_dependency_map_path=DEP_MAP)

    assert plan["contract_version"] == "pmbot_public_read_only_fetch_plan.v1"
    assert plan["market_ids"] == list(TRACKED_MARKET_IDS)
    assert len(plan["requested_sources"]) == 10
    assert validate_fetch_plan(plan)["valid"] is True


def test_fetch_plan_includes_5_tracked_markets_if_artifacts_exist() -> None:
    assert QUEUE.exists()
    plan = build_fetch_plan_from_queue(queue_path=QUEUE, source_dependency_map_path=DEP_MAP)

    assert set(plan["market_ids"]) == set(TRACKED_MARKET_IDS)
    assert {source["market_id"] for source in plan["requested_sources"]} == set(TRACKED_MARKET_IDS)


def test_fetch_plan_builder_does_not_call_network(monkeypatch) -> None:
    def blocked(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network access is not allowed")

    monkeypatch.setattr(socket, "create_connection", blocked)

    plan = build_fetch_plan_from_queue(queue_path=QUEUE, source_dependency_map_path=DEP_MAP)

    assert plan["live_fetch_performed"] is False
