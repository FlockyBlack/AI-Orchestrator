from __future__ import annotations

import json
import socket

import pytest

from pm_bot.operator_runner.paper_daily_config import (
    PaperDailyConfigError,
    PaperDailyLoopConfig,
    attach_outcome_status_to_markets,
    load_market_outcome_inputs,
    load_tracked_market_state,
)
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.feedback_readiness import build_feedback_readiness_summary
from pm_bot.trading_core.paper_portfolio_report import build_paper_portfolio_report
from pm_bot.trading_core.unresolved_market_guard import (
    UnresolvedMarketGuardError,
    reject_invented_outcomes,
    verify_markets_unresolved,
)


def _config(tmp_path, *, run_date: str = "2026-05-11") -> PaperDailyLoopConfig:
    return PaperDailyLoopConfig(run_date=run_date, max_markets=6, output_dir=tmp_path)


def test_paper_daily_loop_runs_local_only(monkeypatch, tmp_path) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    result = run_paper_daily_loop(_config(tmp_path))

    assert result.market_count == 6
    assert result.unresolved_market_count == 6
    assert result.feedback_ready_count == 0
    assert result.safety_ok is True


def test_paper_daily_loop_writes_dashboard(tmp_path) -> None:
    result = run_paper_daily_loop(_config(tmp_path))

    dashboard_path = tmp_path / "paper_daily_dashboard.json"
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))

    assert dashboard_path.exists()
    assert (tmp_path / "paper_daily_dashboard.md").exists()
    assert (tmp_path / "paper_daily_portfolio_state.json").exists()
    assert (tmp_path / "paper_daily_ledger.json").exists()
    assert (tmp_path / "paper_daily_audit.json").exists()
    assert (tmp_path / "paper_daily_safety_scan.json").exists()
    assert (tmp_path / "paper_daily_idempotency_report.json").exists()
    assert (tmp_path / "paper_daily_rollforward.json").exists()
    assert (tmp_path / "paper_daily_outcome_recheck_queue.json").exists()
    assert (tmp_path / "paper_daily_feedback_readiness.json").exists()
    assert dashboard["run_id"] == result.run_id
    assert dashboard["counts"]["market_count"] == 6
    assert dashboard["counts"]["unresolved_market_count"] == 6
    assert dashboard["counts"]["feedback_ready_count"] == 0
    assert dashboard["open_paper_positions"]
    assert dashboard["feedback_readiness"]["blocked_feedback_count"] == 6
    assert dashboard["outcome_recheck_queue"]["needs_future_outcome_check_count"] == 6


def test_paper_daily_loop_idempotent_rerun_no_duplicate_fills(tmp_path) -> None:
    first = run_paper_daily_loop(_config(tmp_path))
    second = run_paper_daily_loop(_config(tmp_path))
    ledger = json.loads((tmp_path / "paper_daily_ledger.json").read_text(encoding="utf-8"))
    idempotency = json.loads((tmp_path / "paper_daily_idempotency_report.json").read_text(encoding="utf-8"))
    keys = [row["idempotency_key"] for row in ledger["positions"]]

    assert first.simulated_fill_count == 2
    assert second.simulated_fill_count == 2
    assert ledger["open_position_count"] == 2
    assert len(keys) == len(set(keys))
    assert idempotency["new_applied_count"] == 0
    assert idempotency["already_applied_count"] == 2
    assert idempotency["duplicate_fill_prevented_count"] == 2
    assert idempotency["idempotency_passed"] is True


def test_paper_daily_loop_rolls_forward_open_positions_across_run_dates(tmp_path) -> None:
    first = run_paper_daily_loop(_config(tmp_path, run_date="2026-05-11"))
    second = run_paper_daily_loop(_config(tmp_path, run_date="2026-05-12"))
    ledger = json.loads((tmp_path / "paper_daily_ledger.json").read_text(encoding="utf-8"))
    rollforward = json.loads((tmp_path / "paper_daily_rollforward.json").read_text(encoding="utf-8"))
    idempotency = json.loads((tmp_path / "paper_daily_idempotency_report.json").read_text(encoding="utf-8"))

    assert first.open_paper_position_count == 2
    assert second.open_paper_position_count == 2
    assert second.carried_forward_position_count == 2
    assert second.total_paper_exposure_usd == 50.0
    assert ledger["open_position_count"] == 2
    assert {row["run_date"] for row in ledger["positions"]} == {"2026-05-11"}
    assert rollforward["previous_ledger_loaded"] is True
    assert rollforward["previous_portfolio_loaded"] is True
    assert rollforward["carried_forward_position_count"] == 2
    assert rollforward["new_position_count"] == 0
    assert rollforward["current_total_paper_exposure_usd"] == 50.0
    assert idempotency["already_open_position_count"] == 2
    assert idempotency["duplicate_fill_prevented_count"] == 2
    assert idempotency["new_applied_count"] == 0


def test_paper_daily_loop_rejects_network(tmp_path) -> None:
    with pytest.raises(PaperDailyConfigError):
        PaperDailyLoopConfig(output_dir=tmp_path, allow_network=True)


def test_paper_daily_loop_rejects_real_trading_flag(tmp_path) -> None:
    with pytest.raises(PaperDailyConfigError):
        PaperDailyLoopConfig(output_dir=tmp_path, allow_real_trading=True)


def test_unresolved_market_guard_preserves_unresolved_status(tmp_path) -> None:
    config = _config(tmp_path)
    state = load_tracked_market_state(config)
    markets = list(state["market_queue"]["items"])
    outcomes = load_market_outcome_inputs(markets)
    enriched = attach_outcome_status_to_markets(markets, outcomes)

    report = verify_markets_unresolved(enriched)

    assert report["unresolved_verified"] is True
    assert report["unresolved_market_count"] == 6
    assert all(row["outcome_status"] == "unresolved" for row in report["markets"])


def test_feedback_readiness_blocks_current_unresolved_markets(tmp_path) -> None:
    run_paper_daily_loop(_config(tmp_path))
    summary = json.loads((tmp_path / "paper_daily_feedback_readiness.json").read_text(encoding="utf-8"))
    queue = json.loads((tmp_path / "paper_daily_outcome_recheck_queue.json").read_text(encoding="utf-8"))

    assert summary["total_tracked_markets"] == 6
    assert summary["unresolved_count"] == 6
    assert summary["resolved_count"] == 0
    assert summary["feedback_ready_count"] == 0
    assert len(summary["blocked_items"]) == 6
    assert all(row["feedback_blocked_reason"] == "local outcome status is unresolved" for row in summary["blocked_items"])
    assert queue["needs_future_outcome_check_count"] == 6
    assert all(row["needs_future_outcome_check"] is True for row in queue["recheck_items"])


def test_feedback_readiness_requires_saved_local_resolution_evidence() -> None:
    markets = [
        {"market_id": "resolved-1", "market_title": "Resolved local fixture"},
        {"market_id": "blocked-1", "market_title": "Blocked local fixture"},
    ]
    outcomes = [
        {
            "market_id": "resolved-1",
            "outcome_status": "resolved",
            "resolution_source_reference": "pm_bot/tests/fixtures/practical_one_market/outcome_resolved_aligned.synthetic",
        },
        {"market_id": "blocked-1", "outcome_status": "resolved", "resolution_source_reference": ""},
    ]

    summary = build_feedback_readiness_summary(tracked_markets=markets, outcome_inputs=outcomes)

    assert summary["total_tracked_markets"] == 2
    assert summary["resolved_count"] == 2
    assert summary["feedback_ready_count"] == 1
    assert {row["market_id"] for row in summary["ready_items"]} == {"resolved-1"}
    assert summary["blocked_items"][0]["feedback_blocked_reason"] == "local resolution status lacks explicit saved evidence"


def test_unresolved_market_guard_rejects_invented_outcome() -> None:
    markets = [{"market_id": "563650", "market_title": "fixture", "outcome_status": "unresolved"}]
    invented_outcomes = [{"market_id": "563650", "outcome_status": "resolved", "resolution_source_reference": ""}]

    with pytest.raises(UnresolvedMarketGuardError):
        reject_invented_outcomes(markets, invented_outcomes)


def test_paper_portfolio_report_counts_open_positions(tmp_path) -> None:
    run_paper_daily_loop(_config(tmp_path))
    ledger = json.loads((tmp_path / "paper_daily_ledger.json").read_text(encoding="utf-8"))
    portfolio = json.loads((tmp_path / "paper_daily_portfolio_state.json").read_text(encoding="utf-8"))

    report = build_paper_portfolio_report(ledger, portfolio)

    assert report["exposure_summary"]["open_paper_position_count"] == 2
    assert report["exposure_summary"]["total_paper_exposure_usd"] == 50.0
    assert len(report["open_paper_positions"]) == 2


def test_daily_loop_result_has_safety_ok_true(tmp_path) -> None:
    result = run_paper_daily_loop(_config(tmp_path))

    assert result.safety_ok is True
    assert result.validation_passed is True


def test_daily_loop_no_wallet_orders_trading_endpoint_flags(tmp_path) -> None:
    run_paper_daily_loop(_config(tmp_path))
    safety = json.loads((tmp_path / "paper_daily_safety_scan.json").read_text(encoding="utf-8"))
    flags = safety["safety_flags"]

    assert safety["safety_ok"] is True
    assert flags["real_order_submitted"] is False
    assert flags["wallet_used"] is False
    assert flags["private_key_used"] is False
    assert flags["signing_used"] is False
    assert flags["trading_endpoint_used"] is False
    assert flags["real_money_used"] is False
    assert flags["authenticated_endpoint_used"] is False
    assert flags["openrouter_used"] is False
    assert flags["polymarket_api_used"] is False
