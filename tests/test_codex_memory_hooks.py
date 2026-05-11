from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.memory_hooks import collect_local_project_context_snapshot, render_memory_context_for_task
from ai_orchestrator.codex_queue.plan_contract import PlanContract
from codex_plan_helpers import minimal_plan


def test_collect_local_snapshot_skips_sensitive_files(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text("hello", encoding="utf-8")
    (tmp_path / "docs" / ".env").write_text("SECRET=bad", encoding="utf-8")

    snapshot = collect_local_project_context_snapshot(tmp_path, ["docs/"])

    assert any(item["path"] == "docs/note.md" for item in snapshot.files)
    assert not any(".env" in item["path"] for item in snapshot.files)


def test_render_memory_context_for_task(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text("hello", encoding="utf-8")
    plan = PlanContract.from_dict(minimal_plan(1))
    snapshot = collect_local_project_context_snapshot(tmp_path, ["docs/"])

    rendered = render_memory_context_for_task(plan.tasks[0], snapshot)

    assert "Local Memory Context" in rendered
    assert "does not install Locus" in rendered
