from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.runbook import generate_controlled_runbook
from ai_orchestrator.codex_queue.schema import default_packet


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _approved_packet(task_id: str) -> dict:
    packet = default_packet()
    packet["task_id"] = task_id
    packet["title"] = f"{task_id} runbook test"
    packet["status"] = "approved"
    packet["created_at"] = "2026-05-09T00:00:00Z"
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    packet["task_type"] = "local_docs_only"
    packet["priority"] = "low"
    packet["summary"] = "Safe local runbook test task."
    packet["instructions"] = ["Create a harmless docs note."]
    packet["repo"]["base_branch"] = "master"
    packet["repo"]["allowed_paths"] = ["docs/"]
    packet["repo"]["forbidden_paths"] = ["runtime/", "dispatcher/", "run_codex/", "pm_bot/"]
    packet["acceptance_checks"] = []
    packet["expected_outputs"] = ["docs/result.md"]
    return packet


def _write_ready_task(queue_root: Path, task_id: str) -> Path:
    handoff_path = queue_root / "planned" / f"{task_id}.handoff_prompt.md"
    workspace_plan_path = queue_root / "planned" / f"{task_id}.workspace_plan.json"
    _write_json(queue_root / "approved" / f"{task_id}.task.json", _approved_packet(task_id))
    _write_json(
        queue_root / "planned" / f"{task_id}.plan.json",
        {
            "task_id": task_id,
            "handoff_prompt_path": str(handoff_path),
            "workspace_plan_path": str(workspace_plan_path),
        },
    )
    _write_text(handoff_path, "# Manual handoff\n")
    _write_json(
        workspace_plan_path,
        {
            "task_id": task_id,
            "status": "planned",
            "branch_created": False,
            "worktree_created": False,
            "suggested_branch_name": f"codex/{task_id.lower()}",
            "suggested_worktree_path": str(queue_root.parent / "worktrees" / task_id.lower()),
        },
    )
    return handoff_path


def test_runbook_writes_latest_json_and_markdown_reports(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-RUNBOOK-READY"
    _write_ready_task(queue_root, task_id)

    report = generate_controlled_runbook(queue_root)

    latest_json = queue_root / "reports" / "latest_controlled_codex_runbook.json"
    latest_md = queue_root / "reports" / "latest_controlled_codex_runbook.md"
    assert latest_json.exists()
    assert latest_md.exists()
    assert report["report_paths"]["latest_controlled_runbook_json"] == str(latest_json)


def test_runbook_includes_handoff_prompt_path_for_ready_task(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-RUNBOOK-HANDOFF"
    handoff_path = _write_ready_task(queue_root, task_id)

    report = generate_controlled_runbook(queue_root)

    ready = report["ready_for_manual_codex_handoff"]
    assert len(ready) == 1
    assert ready[0]["task_id"] == task_id
    assert ready[0]["handoff_prompt_path"] == str(handoff_path.resolve(strict=False))


def test_runbook_states_codex_is_not_executed_automatically(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_ready_task(queue_root, "ORCH-RUNBOOK-SAFETY")

    generate_controlled_runbook(queue_root)

    markdown = (queue_root / "reports" / "latest_controlled_codex_runbook.md").read_text(encoding="utf-8")
    payload = json.loads(
        (queue_root / "reports" / "latest_controlled_codex_runbook.json").read_text(encoding="utf-8")
    )
    assert "Codex is not executed automatically" in markdown
    assert payload["manual_gate"]["codex_is_not_executed_automatically"] is True
    assert payload["codex_execution_added"] is False
    assert payload["branch_created"] is False
    assert payload["worktree_created"] is False
