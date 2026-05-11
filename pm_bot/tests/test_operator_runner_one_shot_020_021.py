from __future__ import annotations

import json

from pm_bot.operator_runner.run_operator_workflow_once import run_operator_workflow_once


def test_one_shot_runner_executes_once_and_creates_outputs(tmp_path) -> None:
    out_dir = tmp_path / "run_001"

    result = run_operator_workflow_once(
        out_dir=out_dir,
        include_trading_core=True,
        no_live_fetch=True,
        no_real_trading=True,
    )

    assert result["run_once"] is True
    assert result["repeat_count"] == 1
    assert result["scheduler_created"] is False
    assert result["daemon_created"] is False
    assert result["background_worker_created"] is False
    assert result["steps_failed"] == 0
    assert result["safety_ok"] is True
    assert (out_dir / "operator_workflow_run_result.json").exists()
    assert (out_dir / "final_operator_report.json").exists()


def test_one_shot_run_result_has_no_unsafe_flags(tmp_path) -> None:
    out_dir = tmp_path / "run_001"
    run_operator_workflow_once(
        out_dir=out_dir,
        include_trading_core=True,
        no_live_fetch=True,
        no_real_trading=True,
    )

    result = json.loads((out_dir / "operator_workflow_run_result.json").read_text(encoding="utf-8"))

    assert result["live_fetch_performed"] is False
    assert result["openrouter_calls_performed"] == 0
    assert result["polymarket_api_calls_performed"] == 0
    assert result["authenticated_endpoints_used"] is False
    assert result["wallet_used"] is False
    assert result["orders_used"] is False
    assert result["real_trading_enabled"] is False
