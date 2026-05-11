from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from codex_plan_helpers import write_plan


def test_codex_cli_dry_run_executor_does_not_invoke_external_codex(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"

    result = LongRunController(repo_root=tmp_path).run_plan(
        plan_path,
        queue_root,
        run_id="RUN1",
        max_steps=1,
        executor="codex_cli_dry_run",
    )
    dry_run = json.loads(Path(result["payload"]["codex_cli_dry_run_path"]).read_text(encoding="utf-8"))

    assert result["status"] == "adapter_dry_run_ready"
    assert dry_run["codex_invoked"] is False
    assert dry_run["external_process_started"] is False
    assert dry_run["future_command"][0] == "codex"
