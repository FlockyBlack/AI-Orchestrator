from __future__ import annotations

import json

from pm_bot.operator_runner.run_operator_workflow_once import run_operator_workflow_once


def test_final_report_contains_required_paths_and_safety(tmp_path) -> None:
    out_dir = tmp_path / "run_001"
    run_operator_workflow_once(
        out_dir=out_dir,
        include_trading_core=True,
        no_live_fetch=True,
        no_real_trading=True,
    )

    report = json.loads((out_dir / "final_operator_report.json").read_text(encoding="utf-8"))

    assert report["contract_version"] == "pmbot_operator_workflow_run_report.v1"
    assert report["steps_failed"] == 0
    assert report["daily_summary_path"]
    assert report["paper_trading_dashboard_path"]
    assert report["portfolio_state_path"]
    assert report["audit_path"]
    assert len(report["safety_scan_paths"]) == 2
    assert report["safety_summary"]["one_shot"] is True
    assert report["safety_summary"]["background_mode_allowed"] is False


def test_operator_workflow_safety_scan_passes(tmp_path) -> None:
    out_dir = tmp_path / "run_001"
    run_operator_workflow_once(
        out_dir=out_dir,
        include_trading_core=True,
        no_live_fetch=True,
        no_real_trading=True,
    )

    safety = json.loads((out_dir / "operator_workflow_safety_scan.result.json").read_text(encoding="utf-8"))

    assert safety["safety_ok"] is True
    assert safety["issue_count"] == 0
    assert safety["confirmed"]["live_fetch"] is False
    assert safety["confirmed"]["real_trading"] is False
