from __future__ import annotations

import json

from pm_bot.operator_runner.paper_daily_config import PaperDailyLoopConfig
from pm_bot.operator_runner.paper_daily_loop import run_paper_daily_loop
from pm_bot.trading_core.risk_prep_config import (
    FUTURE_RISK_ENGINE_CONFIG_CONTRACT,
    build_default_future_risk_engine_config,
    validate_future_risk_engine_config,
)


def _config(tmp_path, *, run_date: str = "2026-05-11") -> PaperDailyLoopConfig:
    return PaperDailyLoopConfig(run_date=run_date, max_markets=6, output_dir=tmp_path)


def _load_json(path):  # type: ignore[no-untyped-def]
    return json.loads(path.read_text(encoding="utf-8"))


def test_strategy_evaluation_ledger_is_idempotent_for_daily_rerun(tmp_path) -> None:
    run_paper_daily_loop(_config(tmp_path))
    first = _load_json(tmp_path / "paper_strategy_evaluation_ledger.json")
    first_record_ids = [row["evaluation_record_id"] for row in first["records"]]

    run_paper_daily_loop(_config(tmp_path))
    second = _load_json(tmp_path / "paper_strategy_evaluation_ledger.json")
    second_record_ids = [row["evaluation_record_id"] for row in second["records"]]

    assert first["record_count"] == 6
    assert second["record_count"] == 6
    assert second["filled_record_count"] == 2
    assert second["open_position_record_count"] == 2
    assert first_record_ids == second_record_ids
    assert second["idempotency"]["record_ids_unique"] is True
    assert len(second_record_ids) == len(set(second_record_ids))


def test_strategy_evaluation_records_required_links_and_risk_fields(tmp_path) -> None:
    result = run_paper_daily_loop(_config(tmp_path))
    ledger = _load_json(tmp_path / "paper_strategy_evaluation_ledger.json")

    assert ledger["run_id"] == result.run_id
    assert ledger["unresolved_paper_exposure_usd"] == 50.0
    for record in ledger["records"]:
        assert record["run_id"] == result.run_id
        assert record["market_id"]
        assert "hypothesis_id" in record
        assert record["simulated_action_type"] in {"simulated_entry", "observe_only"}
        assert "risk_gate_status" in record["risk_gate_result"]
        assert "portfolio_exposure_impact" in record
        assert "analysis_artifact_path" in record["source_links"]
        assert "evidence_artifact_paths" in record["source_links"]


def test_strategy_summary_does_not_invent_pnl_for_unresolved_markets(tmp_path) -> None:
    run_paper_daily_loop(_config(tmp_path))
    ledger = _load_json(tmp_path / "paper_strategy_evaluation_ledger.json")
    summary = _load_json(tmp_path / "paper_strategy_evaluation_summary.json")

    assert summary["performance_readiness_status"] == "blocked_pending_outcome_resolution"
    assert summary["paper_realized_pnl_usd"] is None
    assert summary["paper_unrealized_pnl_usd"] is None
    assert summary["unresolved_pnl_not_invented"] is True
    assert summary["unresolved_paper_exposure_usd"] == 50.0
    assert summary["feedback_ready_count"] == 0
    assert summary["hypotheses_waiting_for_outcome_resolution"]
    assert "saved_local_outcome_resolution" in summary["missing_future_evaluation_data"]
    assert all(record["realized_pnl_usd"] is None for record in ledger["records"])
    assert all(record["unrealized_pnl_usd"] is None for record in ledger["records"])


def test_future_risk_engine_config_validates() -> None:
    config = build_default_future_risk_engine_config()
    valid, errors = validate_future_risk_engine_config(config)

    assert valid is True
    assert errors == []
    assert config["contract_version"] == FUTURE_RISK_ENGINE_CONFIG_CONTRACT
    assert config["max_total_exposure_usd"] == 0.0
    assert config["max_per_market_exposure_usd"] == 0.0
    assert config["market_allowlist"] == []
    assert config["market_denylist"] == []
    assert config["per_run_action_cap"] == 0
    assert config["kill_switch_enabled"] is True
    assert config["manual_approval_required"] is True


def test_future_risk_engine_config_rejects_disabled_required_gate() -> None:
    config = build_default_future_risk_engine_config()
    config["kill_switch_enabled"] = False

    valid, errors = validate_future_risk_engine_config(config)

    assert valid is False
    assert "kill_switch_enabled must be true" in errors


def test_daily_dashboard_shows_strategy_ledger_exposure_and_risk_prep(tmp_path) -> None:
    run_paper_daily_loop(_config(tmp_path))
    dashboard = _load_json(tmp_path / "paper_daily_dashboard.json")

    assert dashboard["paper_strategy_ledger_status"]["record_count"] == 6
    assert dashboard["paper_strategy_ledger_status"]["unresolved_paper_exposure_usd"] == 50.0
    assert dashboard["paper_strategy_ledger_status"]["unresolved_pnl_not_invented"] is True
    assert dashboard["counts"]["unresolved_paper_exposure_usd"] == 50.0
    assert dashboard["risk_prep_config_status"]["present"] is True
    assert dashboard["risk_prep_config_status"]["valid"] is True
    assert dashboard["risk_prep_config_status"]["kill_switch_enabled"] is True
    assert dashboard["risk_prep_config_status"]["manual_approval_required"] is True
    assert "strategy ledger" in dashboard["next_operator_action"]


def test_daily_loop_keeps_wallet_order_and_signing_integrations_disabled(tmp_path) -> None:
    run_paper_daily_loop(_config(tmp_path))
    risk_config = _load_json(tmp_path / "future_risk_engine_config.json")
    safety = _load_json(tmp_path / "paper_daily_safety_scan.json")

    assert safety["safety_ok"] is True
    assert safety["safety_flags"]["wallet_used"] is False
    assert safety["safety_flags"]["signing_used"] is False
    assert safety["safety_flags"]["trading_endpoint_used"] is False
    assert risk_config["wallet_integration_enabled"] is False
    assert risk_config["signing_integration_enabled"] is False
    assert risk_config["order_placement_enabled"] is False
    assert risk_config["authenticated_endpoint_integration_enabled"] is False
    assert risk_config["applied_to_real_execution"] is False
