from __future__ import annotations

from pathlib import Path

from ai_orchestrator.symphony_adapter.symphony_session_plan import build_session_plan, validate_session_plan
from ai_orchestrator.symphony_adapter.symphony_task_contract import SymphonyTask
from ai_orchestrator.symphony_adapter.symphony_workspace_plan import build_workspace_plan_for_task


def test_session_plan_validates_with_local_schema_reference(tmp_path: Path) -> None:
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    (schema_dir / "ClientRequest.json").write_text('{"oneOf":[]}', encoding="utf-8")
    task = SymphonyTask(
        task_id="TEST-TASK-001",
        title="Task",
        description="Safe task.",
        source_plan_id="plan",
        source_run_id="run",
    )
    workspace_plan = build_workspace_plan_for_task(task, Path.cwd(), tmp_path / "workspaces")

    plan = build_session_plan(task, workspace_plan, schema_dir)
    validation = validate_session_plan(plan)

    assert validation["valid"] is True
    assert plan.app_server_transport == "stdio"
    assert plan.app_server_listen == "stdio://"
    assert plan.approval_policy == "on-request"
    assert "browser_automation" in plan.forbidden_tools
    assert plan.result_contract["safety_flags_must_be_false"]
