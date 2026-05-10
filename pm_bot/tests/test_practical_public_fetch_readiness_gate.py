from __future__ import annotations

import copy
import json
from pathlib import Path

from pm_bot.practical.public_fetch_readiness_gate import evaluate_public_fetch_readiness

FIXTURE_DIR = Path("pm_bot/tests/fixtures/public_read_only_fetch_prep")


def _plan() -> dict:
    return json.loads((FIXTURE_DIR / "fetch_plan_5_markets.valid.json").read_text(encoding="utf-8"))


def _approval() -> dict:
    return json.loads((FIXTURE_DIR / "operator_approval_pending.valid.json").read_text(encoding="utf-8"))


def test_approval_granted_false_blocks_readiness() -> None:
    result = evaluate_public_fetch_readiness(fetch_plan=_plan(), approval=_approval())

    assert result["ready_for_controlled_public_fetch"] is False
    assert any("approval has not been granted" in blocker.lower() for blocker in result["blockers"])


def test_auth_wallet_order_trading_categories_block_readiness() -> None:
    plan = _plan()
    plan["requested_sources"] = copy.deepcopy(plan["requested_sources"])
    plan["requested_sources"][0]["source_category"] = "trading_endpoint"
    plan["requested_sources"][1]["wallet_required"] = True
    plan["auth_required"] = True
    plan["order_endpoint_allowed"] = True

    result = evaluate_public_fetch_readiness(fetch_plan=plan, approval=_approval())

    assert result["ready_for_controlled_public_fetch"] is False
    assert any("trading_endpoint" in blocker for blocker in result["blockers"])
    assert any("wallet" in blocker.lower() for blocker in result["blockers"])
    assert any("auth" in blocker.lower() for blocker in result["blockers"])
    assert any("order" in blocker.lower() for blocker in result["blockers"])


def test_readiness_gate_requires_evidence_save_and_replay_requirement() -> None:
    plan = _plan()
    plan["evidence_save_required"] = False
    plan["replay_required_before_analysis_update"] = False

    result = evaluate_public_fetch_readiness(fetch_plan=plan, approval=_approval())

    assert result["ready_for_controlled_public_fetch"] is False
    assert any("Evidence save" in blocker for blocker in result["blockers"])
    assert any("replay" in blocker.lower() for blocker in result["blockers"])


def test_generated_sample_remains_not_ready() -> None:
    result = json.loads(
        Path("pm_bot/practical/artifacts/public_read_only_fetch_prep_005/public_fetch_readiness_gate.result.json").read_text(
            encoding="utf-8"
        )
    )

    assert result["ready_for_controlled_public_fetch"] is False
    assert result["approval_status"]["operator_approval_required"] is True
    assert result["approval_status"]["operator_approval_granted"] is False
