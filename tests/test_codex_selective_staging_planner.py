from __future__ import annotations

from ai_orchestrator.codex_queue.selective_staging_planner import (
    build_selective_staging_plan,
    render_git_add_commands,
    validate_staging_plan,
)


def test_selective_staging_never_renders_unsafe_git_add() -> None:
    plan = build_selective_staging_plan(
        ".",
        [
            "ai_orchestrator/codex_queue/plan_contract.py",
            "docs/result.md",
            ".env",
            "unrelated/file.txt",
        ],
        allowed_roots=["ai_orchestrator/codex_queue/", "docs/"],
        blocked_patterns=[".env", "secret", "wallet"],
    )

    commands = render_git_add_commands(plan)

    assert plan.valid is True
    assert "ai_orchestrator/codex_queue/plan_contract.py" in plan.allowed_files
    assert ".env" in plan.blocked_files
    assert not any(command in {"git add .", "git add -A", "git add --all"} for command in commands)
    assert all(command.startswith("git add -- ") for command in commands)


def test_validate_staging_plan_accepts_explicit_paths() -> None:
    plan = build_selective_staging_plan(".", ["tests/test_file.py"], allowed_roots=["tests/"], blocked_patterns=[])

    validation = validate_staging_plan(plan)

    assert validation["valid"] is True
