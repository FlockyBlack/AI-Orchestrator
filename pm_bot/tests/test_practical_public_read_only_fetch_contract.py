from __future__ import annotations

import copy
import json
from pathlib import Path

from pm_bot.practical.public_read_only_fetch_contract import validate_fetch_plan

FIXTURE = Path("pm_bot/tests/fixtures/public_read_only_fetch_prep/fetch_plan_5_markets.valid.json")


def _plan() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_valid_fetch_plan_validates() -> None:
    validation = validate_fetch_plan(_plan())

    assert validation["valid"] is True
    assert validation["errors"] == []


def test_auth_required_true_is_blocked() -> None:
    plan = _plan()
    plan["auth_required"] = True

    validation = validate_fetch_plan(plan)

    assert validation["valid"] is False
    assert any("auth_required" in error for error in validation["errors"])


def test_trading_endpoint_category_is_blocked() -> None:
    plan = _plan()
    plan["requested_sources"] = copy.deepcopy(plan["requested_sources"])
    plan["requested_sources"][0]["source_category"] = "trading_endpoint"

    validation = validate_fetch_plan(plan)

    assert validation["valid"] is False
    assert any("trading_endpoint" in error for error in validation["errors"])


def test_wallet_signing_category_is_blocked() -> None:
    plan = _plan()
    plan["requested_sources"] = copy.deepcopy(plan["requested_sources"])
    plan["requested_sources"][0]["source_category"] = "wallet_signing_endpoint"

    validation = validate_fetch_plan(plan)

    assert validation["valid"] is False
    assert any("wallet_signing_endpoint" in error for error in validation["errors"])
