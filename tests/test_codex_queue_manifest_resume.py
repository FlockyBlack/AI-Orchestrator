from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.plan_to_queue import (
    create_queue_from_plan,
    inspect_queue,
    load_queue_manifest,
    validate_queue_manifest,
)
from codex_plan_helpers import write_plan


def test_queue_manifest_validates_and_creation_is_idempotent(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plans" / "plan.json")
    queue_root = tmp_path / "agent_tasks"

    first = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")
    second = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")
    manifest = load_queue_manifest(queue_root, "RUN1")
    inspection = inspect_queue(queue_root, "RUN1")

    assert first.status == "created"
    assert second.status == "exists"
    assert validate_queue_manifest(manifest)["valid"] is True
    assert inspection["status"] == "found"
    assert manifest["source_plan_sha256"]
    assert manifest["state_path"].endswith("state.json")


def test_conflicting_existing_queue_manifest_blocks(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plans" / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    first = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")
    manifest_path = Path(first.queue_paths["manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_plan_sha256"] = "conflict"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    second = create_queue_from_plan(plan_path, queue_root, run_id="RUN1")

    assert second.status == "blocked"
    assert second.errors
