from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_orchestrator.codex_queue.operator_cli import main
from codex_plan_helpers import write_plan
from test_codex_app_server_protocol_index import _write_schema_dir


def test_cli_app_server_schema_probe_returns_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    schema_dir = _write_schema_dir(tmp_path)

    exit_code = main(["app-server-schema-probe", "--schema-dir", str(schema_dir)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["schema_probe_passed"] is True
    assert "initialize" in output["protocol_capabilities"]["client_requests"]


def test_cli_app_server_dry_run_without_approval_does_not_start(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    queue_root = tmp_path / "agent_tasks"
    fake = _fake_app_server()

    exit_code = main(
        [
            "app-server-dry-run",
            "--repo-root",
            str(tmp_path),
            "--queue-root",
            str(queue_root),
            "--schema-dir",
            str(schema_dir),
            "--codex-command-part",
            sys.executable,
            "--codex-command-part",
            str(fake),
            "--codex-command-part",
            "startup_failure",
        ]
    )
    action = _latest_action(queue_root)

    assert exit_code == 0
    assert action["status"] == "requires_operator_approval"
    assert action["process_started"] is False
    assert action["real_app_server_started"] is False


def test_cli_app_server_dry_run_with_fake_command_writes_artifacts(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    queue_root = tmp_path / "agent_tasks"

    exit_code = main(
        [
            "app-server-dry-run",
            "--repo-root",
            str(tmp_path),
            "--queue-root",
            str(queue_root),
            "--schema-dir",
            str(schema_dir),
            "--timeout-seconds",
            "3",
            "--operator-approved",
            "--codex-command-part",
            sys.executable,
            "--codex-command-part",
            str(_fake_app_server()),
            "--codex-command-part",
            "success",
        ]
    )
    action = _latest_action(queue_root)
    artifact_paths = action["artifact_paths"]

    assert exit_code == 0
    assert action["process_started"] is True
    assert action["process_stopped"] is True
    assert action["protocol_probe_succeeded"] is True
    for path in artifact_paths.values():
        assert Path(path).exists()


def test_cli_create_app_server_session_plan_writes_artifacts(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    schema_dir = _write_schema_dir(tmp_path)
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--max-steps", "1", "--executor", "fake"]) == 0
    run_id = _latest_action(queue_root)["run_id"]

    exit_code = main(
        [
            "create-app-server-session-plan",
            "--run-id",
            run_id,
            "--queue-root",
            str(queue_root),
            "--workspace-root",
            str(tmp_path / "workspaces"),
            "--schema-dir",
            str(schema_dir),
        ]
    )
    action = _latest_action(queue_root)

    assert exit_code == 0
    assert action["command"] == "create-app-server-session-plan"
    assert action["real_app_server_started"] is False
    assert action["app_server_session_plan"]["dry_run_session_plan_valid"] is True
    for path in action["app_server_session_plan"]["artifact_paths"].values():
        assert Path(path).exists()


def _fake_app_server() -> Path:
    return Path(__file__).parent / "fixtures" / "fake_app_server" / "fake_app_server.py"


def _latest_action(queue_root: Path) -> dict:
    return json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))
