from __future__ import annotations

from pm_bot.practical.public_fetch_approval_packet import build_approval_blocker_scenarios


def test_approval_blocker_scenarios_all_block() -> None:
    blockers = build_approval_blocker_scenarios()

    assert blockers["contract_version"] == "pmbot_public_fetch_approval_blocker_scenarios.v1"
    assert blockers["scenario_count"] == 10
    assert all(scenario["expected_behavior"] == "block" for scenario in blockers["scenarios"])
    assert all(scenario["safe_recovery_action"] for scenario in blockers["scenarios"])


def test_broad_unrestricted_approval_scenario_is_blocked() -> None:
    blockers = build_approval_blocker_scenarios()

    broad = [
        scenario
        for scenario in blockers["scenarios"]
        if scenario["scenario_id"] == "broad_unrestricted_fetch_requested"
    ]

    assert len(broad) == 1
    assert broad[0]["expected_behavior"] == "block"
    assert "limited" in broad[0]["reason"]
