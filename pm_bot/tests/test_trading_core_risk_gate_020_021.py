from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from pm_bot.trading_core.risk_gate import evaluate_paper_trade_intent
from pm_bot.trading_core.risk_limits import default_paper_risk_limits

FIXTURE_DIR = Path("pm_bot/tests/fixtures/trading_core")


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_paper_intent_evaluated_allowed() -> None:
    result = evaluate_paper_trade_intent(_load("paper_trade_intent_candidate.valid.json"), default_paper_risk_limits())

    assert result["allowed"] is True
    assert result["blocked"] is False
    assert result["operator_review_required"] is True


def test_wallet_required_blocked() -> None:
    result = evaluate_paper_trade_intent(
        _load("paper_trade_intent_candidate.blocked_wallet_required.json"),
        default_paper_risk_limits(),
    )

    assert result["blocked"] is True
    assert "wallet_required_true" in result["block_reasons"]


def test_trading_endpoint_required_blocked() -> None:
    candidate = _load("paper_trade_intent_candidate.valid.json")
    candidate["trading_endpoint_required"] = True

    result = evaluate_paper_trade_intent(candidate, default_paper_risk_limits())

    assert result["blocked"] is True
    assert "trading_endpoint_required_true" in result["block_reasons"]


def test_exceeds_single_intent_limit_blocked() -> None:
    result = evaluate_paper_trade_intent(
        _load("paper_trade_intent_candidate.exceeds_limit.json"),
        default_paper_risk_limits(),
    )

    assert result["blocked"] is True
    assert "intended_notional_exceeds_single_intent_limit" in result["block_reasons"]


def test_non_paper_intent_blocked() -> None:
    candidate = _load("paper_trade_intent_candidate.valid.json")
    candidate["paper_only"] = False

    result = evaluate_paper_trade_intent(candidate, default_paper_risk_limits())

    assert result["blocked"] is True
    assert "paper_only_not_true" in result["block_reasons"]


def test_exposure_limit_enforced() -> None:
    candidate = _load("paper_trade_intent_candidate.valid.json")

    result = evaluate_paper_trade_intent(
        candidate,
        default_paper_risk_limits(),
        current_market_exposure_usd=90,
    )

    assert result["blocked"] is True
    assert "market_exposure_limit_exceeded" in result["block_reasons"]


def test_operator_review_required() -> None:
    candidate = deepcopy(_load("paper_trade_intent_candidate.valid.json"))
    candidate["operator_review_required"] = False

    result = evaluate_paper_trade_intent(candidate, default_paper_risk_limits())

    assert result["blocked"] is True
    assert "operator_review_not_required" in result["block_reasons"]
