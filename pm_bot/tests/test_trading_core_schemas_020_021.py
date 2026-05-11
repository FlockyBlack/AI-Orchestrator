from __future__ import annotations

import json
from pathlib import Path

from pm_bot.trading_core.schemas import (
    validate_paper_trade_intent_candidate,
    validate_portfolio_state,
    validate_simulated_execution_result,
)

FIXTURE_DIR = Path("pm_bot/tests/fixtures/trading_core")


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_paper_trade_intent_candidate_schema() -> None:
    valid, errors = validate_paper_trade_intent_candidate(_load("paper_trade_intent_candidate.valid.json"))

    assert valid is True
    assert errors == []


def test_wallet_required_candidate_fails_schema_safety_flag() -> None:
    valid, errors = validate_paper_trade_intent_candidate(
        _load("paper_trade_intent_candidate.blocked_wallet_required.json")
    )

    assert valid is False
    assert "wallet_required must be false" in errors


def test_valid_simulated_execution_result_schema() -> None:
    valid, errors = validate_simulated_execution_result(_load("simulated_execution_result.valid.json"))

    assert valid is True
    assert errors == []


def test_empty_portfolio_state_schema() -> None:
    valid, errors = validate_portfolio_state(_load("paper_portfolio_state.empty.json"))

    assert valid is True
    assert errors == []
