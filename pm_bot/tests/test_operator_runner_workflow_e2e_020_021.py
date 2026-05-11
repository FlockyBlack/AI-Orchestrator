from __future__ import annotations

import json
import socket

from pm_bot.operator_runner.run_operator_workflow_once import run_operator_workflow_once


def test_operator_workflow_e2e_one_shot_no_network_or_real_trading(monkeypatch, tmp_path) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network socket should not be used")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    out_dir = tmp_path / "run_001"

    result = run_operator_workflow_once(
        out_dir=out_dir,
        include_trading_core=True,
        no_live_fetch=True,
        no_real_trading=True,
    )
    final_report = json.loads((out_dir / "final_operator_report.json").read_text(encoding="utf-8"))

    assert result["run_once"] is True
    assert result["steps_failed"] == 0
    assert result["live_fetch_performed"] is False
    assert result["real_trading_enabled"] is False
    assert result["scheduler_created"] is False
    assert result["background_worker_created"] is False
    assert final_report["steps_failed"] == 0
    assert (out_dir / "daily_summary.json").exists()
    assert (out_dir / "trading_core" / "paper_trading_dashboard.json").exists()
    assert (out_dir / "operator_workflow_safety_scan.result.json").exists()
