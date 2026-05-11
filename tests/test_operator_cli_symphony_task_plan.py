from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import main
from codex_plan_helpers import write_plan
from test_codex_app_server_protocol_index import _write_schema_dir


def test_cli_create_symphony_task_plan_writes_expected_artifacts(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    schema_dir = _write_schema_dir(tmp_path)
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--max-steps", "1", "--executor", "fake"]) == 0
    run_id = _latest_action(queue_root)["run_id"]

    exit_code = main(
        [
            "create-symphony-task-plan",
            "--run-id",
            run_id,
            "--queue-root",
            str(queue_root),
            "--workspace-root",
            str(tmp_path / "workspaces"),
            "--app-server-schema-dir",
            str(schema_dir),
        ]
    )
    action = _latest_action(queue_root)
    artifact_paths = action["symphony_task_plan"]["artifact_paths"]

    assert exit_code == 0
    assert action["command"] == "create-symphony-task-plan"
    assert action["task_id"] == "TEST-TASK-002"
    assert action["schema_index_passed"] is True
    assert action["symphony_mapping_passed"] is True
    assert action["real_app_server_started"] is False
    for path in artifact_paths.values():
        assert Path(path).exists()
    session_plan = json.loads(Path(artifact_paths["session_plan"]).read_text(encoding="utf-8"))
    adapter_plan = json.loads(Path(artifact_paths["app_server_adapter_plan"]).read_text(encoding="utf-8"))
    assert session_plan["app_server_listen"] == "stdio://"
    assert adapter_plan["real_app_server_started"] is False


def _latest_action(queue_root: Path) -> dict:
    return json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
