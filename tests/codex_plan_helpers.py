from __future__ import annotations

import json
from pathlib import Path


def minimal_plan(task_count: int = 3) -> dict:
    tasks = []
    previous = None
    for index in range(1, task_count + 1):
        task_id = f"TEST-TASK-{index:03d}"
        tasks.append(
            {
                "task_id": task_id,
                "title": f"Task {index}",
                "description": f"Safe local test task {index}.",
                "dependencies": [previous] if previous else [],
                "allowed_paths": ["docs/", "tests/"],
                "forbidden_actions": ["wallet", "orders", "unsafe git staging"],
                "acceptance_gates": ["validation passes", "safety_ok true"],
                "expected_artifacts": [f"docs/task_{index}.md"],
                "max_retries": 1,
                "execution_mode": "fake",
                "execution_lane": "lane_a",
            }
        )
        previous = task_id
    return {
        "plan_id": "test_plan",
        "version": "1.0",
        "title": "Test plan",
        "description": "Safe local test plan.",
        "owner": "tests",
        "created_at": "2026-05-11T00:00:00Z",
        "repo_root": ".",
        "branch": "master",
        "expected_head": "",
        "mode": "long_supervised",
        "continue_until": "blocked_or_done",
        "max_steps_default": 50,
        "safety_boundaries": [
            {"boundary_id": "local_only", "description": "Local only", "required": True}
        ],
        "execution_lanes": [
            {"lane_id": "lane_a", "title": "Lane A", "allowed_roots": ["docs/", "tests/"]}
        ],
        "milestones": [
            {"milestone_id": "M1", "title": "Milestone", "task_ids": [task["task_id"] for task in tasks]}
        ],
        "tasks": tasks,
        "acceptance_gates": [
            {"gate_id": "validation", "description": "Validation passes", "required": True}
        ],
        "commit_policy": {"selective_staging_only": True, "unsafe_staging": False},
        "push_policy": {"allowed": False, "force": False},
        "dashboard_policy": {"write_json": True},
    }


def write_plan(path: Path, plan: dict | None = None) -> Path:
    payload = plan or minimal_plan()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
