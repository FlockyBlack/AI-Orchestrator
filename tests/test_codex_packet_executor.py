from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from codex_plan_helpers import write_plan


def test_codex_packet_executor_creates_packet_and_stops_for_handoff(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"

    result = LongRunController(repo_root=tmp_path).run_plan(
        plan_path,
        queue_root,
        run_id="RUN1",
        max_steps=3,
        executor="codex_packet",
    )

    assert result["status"] == "requiring_operator_handoff"
    assert result["requires_operator_handoff"] is True
    assert Path(result["execution_packet_path"]).exists()
    assert Path(result["execution_prompt_path"]).exists()
    assert Path(result["expected_result_template_path"]).exists()


def test_codex_packet_executor_updates_dashboard_latest_packet_path(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"

    result = LongRunController(repo_root=tmp_path).run_plan(
        plan_path,
        queue_root,
        run_id="RUN1",
        max_steps=1,
        executor="codex_packet",
    )
    dashboard = json.loads(Path(result["dashboard_path"]).read_text(encoding="utf-8"))

    assert dashboard["latest_codex_packet_path"] == result["execution_packet_path"]
