from __future__ import annotations

from ai_orchestrator.symphony_adapter.app_server_adapter_boundary import (
    build_app_server_adapter_plan,
    render_app_server_start_command,
    validate_app_server_adapter_plan,
)
from ai_orchestrator.symphony_adapter.codex_app_server_protocol import CodexAppServerSchemaIndex
from ai_orchestrator.symphony_adapter.symphony_session_plan import CodexAppServerSessionPlan


def test_app_server_start_command_renders_but_is_not_executed() -> None:
    session = CodexAppServerSessionPlan(
        session_id="session",
        task_id="task",
        workspace_path="/tmp/workspace",
        prompt_path="/tmp/workspace/prompt.md",
        expected_result_path="/tmp/workspace/result.json",
        approval_policy="on-request",
        sandbox_policy={"type": "workspaceWrite", "writableRoots": ["/tmp/workspace"], "networkAccess": False},
        allowed_tools=("file_read",),
        forbidden_tools=("browser_automation", "openrouter"),
        result_contract={"safety_flags_must_be_false": ["openrouter_used"]},
    )
    index = CodexAppServerSchemaIndex(
        schema_dir="/tmp/schema",
        version="v2",
        protocol_schema_path="/tmp/schema/codex_app_server_protocol.v2.schemas.json",
        client_request_path="/tmp/schema/ClientRequest.json",
        server_request_path="/tmp/schema/ServerRequest.json",
        server_notification_path="/tmp/schema/ServerNotification.json",
        client_requests=("initialize", "thread/start", "turn/start"),
        server_requests=("item/commandExecution/requestApproval",),
        server_notifications=("turn/completed",),
        approval_message_types=("item/commandExecution/requestApproval",),
        session_message_types=("initialize", "thread/start", "turn/start", "turn/completed"),
        auth_message_types=(),
        git_review_message_types=(),
        request_param_refs={},
        server_request_param_refs={},
        notification_param_refs={},
        json_files=(),
        ts_files=(),
    )

    plan = build_app_server_adapter_plan(session, index)
    validation = validate_app_server_adapter_plan(plan)

    assert validation["valid"] is True
    assert render_app_server_start_command(plan) == "codex app-server --listen stdio://"
    assert plan.real_app_server_started is False
    assert plan.daemon_created is False
