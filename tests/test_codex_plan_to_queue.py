from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.plan_to_queue import create_queue_from_plan
from codex_plan_helpers import write_plan


def test_create_queue_materializes_manifest_and_tasks(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plans" / "plan.json")
    queue_root = tmp_path / "agent_tasks"

    result = create_queue_from_plan(plan_path, queue_root, run_id="RUN001")

    manifest_path = Path(result.queue_paths["manifest"])
    assert result.status == "created"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["task_count"] == 3
    assert (queue_root / "generated" / "test_plan" / "RUN001" / "tasks" / "TEST-TASK-001.json").exists()


def test_create_queue_dry_run_does_not_write(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plans" / "plan.json")
    queue_root = tmp_path / "agent_tasks"

    result = create_queue_from_plan(plan_path, queue_root, run_id="DRY", dry_run=True)

    assert result.status == "dry_run"
    assert not Path(result.queue_paths["manifest"]).exists()
