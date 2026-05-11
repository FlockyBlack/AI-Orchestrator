from __future__ import annotations

from ai_orchestrator.codex_queue.commit_push_verify import push_and_verify, selective_commit
from ai_orchestrator.codex_queue.selective_staging_planner import build_selective_staging_plan


def test_selective_commit_dry_run_renders_explicit_commands() -> None:
    plan = build_selective_staging_plan(".", ["docs/result.md"], allowed_roots=["docs/"], blocked_patterns=[])

    result = selective_commit(".", plan, "test commit", dry_run=True)

    assert result.status == "dry_run"
    assert ["git", "add", "--", "docs/result.md"] in result.commands
    assert not any(command == ["git", "add", "."] for command in result.commands)


def test_push_and_verify_dry_run_does_not_push() -> None:
    result = push_and_verify(".", "master", dry_run=True)

    assert result.status == "dry_run"
    assert result.commands[0] == ["git", "push", "origin", "master"]
