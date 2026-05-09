from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.queue_health import (
    collect_queue_health,
    recommend_next_action,
    summarize_task_state,
)
from ai_orchestrator.codex_queue.result_schema import default_result
from ai_orchestrator.codex_queue.schema import default_packet


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _packet(task_id: str, status: str) -> dict:
    packet = default_packet()
    packet["task_id"] = task_id
    packet["title"] = f"{task_id} health test"
    packet["status"] = status
    packet["created_at"] = "2026-05-09T00:00:00Z"
    packet["task_type"] = "local_docs_only"
    packet["priority"] = "low"
    packet["summary"] = "Safe local queue health test task."
    packet["instructions"] = ["Create a harmless docs note."]
    packet["repo"]["base_branch"] = "master"
    packet["repo"]["allowed_paths"] = ["docs/"]
    packet["repo"]["forbidden_paths"] = ["runtime/", "dispatcher/", "run_codex/", "pm_bot/"]
    packet["expected_outputs"] = ["docs/result.md"]
    packet["acceptance_checks"] = []
    if status in {"approved", "planned", "running", "review", "done", "blocked"}:
        packet["approved_by"] = "operator"
        packet["approved_at"] = "2026-05-09T00:00:00Z"
    return packet


def _write_task(queue_root: Path, task_id: str, status: str) -> None:
    _write_json(queue_root / status / f"{task_id}.task.json", _packet(task_id, status))


def _write_plan(queue_root: Path, task_id: str) -> None:
    _write_json(
        queue_root / "planned" / f"{task_id}.plan.json",
        {
            "task_id": task_id,
            "handoff_prompt_path": str(queue_root / "planned" / f"{task_id}.handoff_prompt.md"),
            "workspace_plan_path": str(queue_root / "planned" / f"{task_id}.workspace_plan.json"),
        },
    )


def _write_workspace_plan(queue_root: Path, task_id: str) -> None:
    _write_json(
        queue_root / "planned" / f"{task_id}.workspace_plan.json",
        {
            "task_id": task_id,
            "status": "planned",
            "branch_created": False,
            "worktree_created": False,
            "suggested_branch_name": f"codex/{task_id.lower()}",
            "suggested_worktree_path": str(queue_root.parent / "worktrees" / task_id.lower()),
        },
    )


def _write_result(queue_root: Path, task_id: str) -> None:
    result = default_result()
    result["task_id"] = task_id
    result["completed_at"] = "2026-05-09T00:00:00Z"
    result["summary"] = "Manual result for health tests."
    result["files_created"] = ["docs/result.md"]
    _write_json(queue_root / "review" / f"{task_id}.result.json", result)


def _minimal_summary(
    *,
    state: str | None,
    plan: bool = False,
    handoff: bool = False,
    workspace: bool = False,
    result: bool = False,
    ingestion: bool = False,
    review: bool = False,
    ready: bool = False,
) -> dict:
    return {
        "state": state,
        "plan": {"found": plan},
        "handoff_prompt": {"found": handoff},
        "workspace_plan": {"found": workspace},
        "result_packet": {"found": result},
        "ingestion": {"allowed": ingestion},
        "review_report": {"found": review, "ready_for_mark_done": ready},
    }


def test_queue_health_counts_task_packets_by_state(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    for state in ("inbox", "approved", "planned", "review", "done", "blocked"):
        _write_task(queue_root, f"ORCH-HEALTH-{state.upper()}", state)

    health = collect_queue_health(queue_root)

    assert health["counts"]["inbox"] == 1
    assert health["counts"]["approved"] == 1
    assert health["counts"]["planned"] == 1
    assert health["counts"]["review"] == 1
    assert health["counts"]["done"] == 1
    assert health["counts"]["blocked"] == 1


def test_queue_health_detects_approved_task_without_plan(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-HEALTH-NO-PLAN"
    _write_task(queue_root, task_id, "approved")

    health = collect_queue_health(queue_root)
    summary = summarize_task_state(queue_root, task_id)

    assert health["approved_tasks_without_plans_count"] == 1
    assert health["approved_tasks_without_plans"][0]["task_id"] == task_id
    assert summary["next_action"] == "run_plan"


def test_queue_health_detects_planned_task_with_handoff_prompt(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-HEALTH-HANDOFF"
    _write_task(queue_root, task_id, "planned")
    _write_plan(queue_root, task_id)
    _write_text(queue_root / "planned" / f"{task_id}.handoff_prompt.md", "# Handoff\n")

    health = collect_queue_health(queue_root)
    summary = summarize_task_state(queue_root, task_id)

    assert health["planned_tasks_with_handoff_prompts_count"] == 1
    assert health["planned_tasks_with_handoff_prompts"][0]["task_id"] == task_id
    assert summary["next_action"] == "run_workspace_plan"


def test_queue_health_detects_result_waiting_for_ingestion(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-HEALTH-RESULT"
    _write_task(queue_root, task_id, "approved")
    _write_result(queue_root, task_id)

    health = collect_queue_health(queue_root)
    summary = summarize_task_state(queue_root, task_id)

    assert health["review_results_waiting_for_ingestion_count"] == 1
    assert health["review_results_waiting_for_ingestion"][0]["task_id"] == task_id
    assert summary["next_action"] == "ingest_result"


def test_next_action_recommendations_cover_major_states() -> None:
    assert recommend_next_action(_minimal_summary(state="inbox")) == "create_or_approve_task"
    assert recommend_next_action(_minimal_summary(state="approved")) == "run_plan"
    assert (
        recommend_next_action(_minimal_summary(state="approved", plan=True, handoff=True))
        == "run_workspace_plan"
    )
    assert (
        recommend_next_action(
            _minimal_summary(state="approved", plan=True, handoff=True, workspace=True)
        )
        == "manual_codex_handoff_ready"
    )
    assert recommend_next_action(_minimal_summary(state="approved", result=True)) == "ingest_result"
    assert (
        recommend_next_action(_minimal_summary(state="approved", result=True, ingestion=True))
        == "review_result"
    )
    assert (
        recommend_next_action(
            _minimal_summary(state="approved", result=True, ingestion=True, review=True, ready=True)
        )
        == "ready_for_mark_done"
    )
    assert recommend_next_action(_minimal_summary(state="blocked")) == "blocked_requires_operator_attention"
    assert recommend_next_action(_minimal_summary(state="done")) == "done_no_action_needed"
