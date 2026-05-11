from __future__ import annotations

from pathlib import Path

from ai_orchestrator.operator_panel.panel_app import route_get, route_post
from test_codex_app_server_protocol_index import _write_schema_dir


def test_panel_renders_app_server_section(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"

    html = route_get("/app-server", "", tmp_path, queue_root)

    assert "App Server" in html
    assert "Probe schema" in html
    assert "Run short app-server dry-run" in html
    assert "allow_real_task_execution" in html


def test_panel_refuses_dry_run_without_confirmation(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    queue_root = tmp_path / "agent_tasks"

    result = route_post(
        "/actions/app-server-dry-run",
        {"schema_dir": str(schema_dir), "approval_text": ""},
        tmp_path,
        queue_root,
    )

    assert result["status"] == "blocked"
    assert result["process_started"] is False
    assert "exact confirmation text" in result["errors"][0]
