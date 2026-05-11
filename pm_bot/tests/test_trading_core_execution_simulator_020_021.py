from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path

from pm_bot.trading_core.execution_simulator import simulate_execution_for_intent
from pm_bot.trading_core.risk_gate import evaluate_paper_trade_intent
from pm_bot.trading_core.risk_limits import default_paper_risk_limits

FIXTURE_DIR = Path("pm_bot/tests/fixtures/trading_core")


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_observe_only_skipped() -> None:
    candidate = _load("paper_trade_intent_candidate.valid.json")
    candidate["paper_action_type"] = "observe_only"
    candidate["side_label"] = "no_action"
    candidate["intended_notional_usd"] = 0.0
    candidate["max_loss_usd"] = 0.0
    risk = evaluate_paper_trade_intent(candidate, default_paper_risk_limits())

    result = simulate_execution_for_intent(candidate, risk)

    assert result["execution_status"] == "skipped"
    assert result["simulated_fill"] is False


def test_blocked_rejected() -> None:
    candidate = _load("paper_trade_intent_candidate.blocked_wallet_required.json")
    risk = evaluate_paper_trade_intent(candidate, default_paper_risk_limits())

    result = simulate_execution_for_intent(candidate, risk)

    assert result["execution_status"] == "rejected"
    assert result["simulated_fill"] is False


def test_risk_allowed_simulated_entry_fills_in_paper_mode() -> None:
    candidate = _load("paper_trade_intent_candidate.valid.json")
    risk = evaluate_paper_trade_intent(candidate, default_paper_risk_limits())

    result = simulate_execution_for_intent(candidate, risk)

    assert result["execution_status"] == "immediate_fill"
    assert result["simulated_fill"] is True
    assert result["filled_notional_usd"] == 25.0
    assert result["paper_only"] is True


def test_no_real_order_wallet_endpoint_or_network(monkeypatch) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    candidate = deepcopy(_load("paper_trade_intent_candidate.valid.json"))
    risk = evaluate_paper_trade_intent(candidate, default_paper_risk_limits())

    result = simulate_execution_for_intent(candidate, risk)

    assert result["real_order_submitted"] is False
    assert result["wallet_used"] is False
    assert result["trading_endpoint_used"] is False
    assert result["live_price_used"] is False
