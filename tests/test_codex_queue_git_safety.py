from __future__ import annotations

import re

import pytest

from ai_orchestrator.codex_queue.git_safety import (
    build_safe_branch_name,
    classify_working_tree_status,
    detect_dangerous_git_state,
    validate_branch_name,
)


def test_branch_name_sanitizer_produces_safe_codex_task_branch() -> None:
    branch_name = build_safe_branch_name("ORCH-SYMPHONY-005_WORKSPACE:PLAN?")

    assert branch_name.startswith("codex/")
    assert "orch-symphony-005-workspace-plan" in branch_name
    assert len(branch_name) <= 96
    assert re.fullmatch(r"[a-z0-9/-]+", branch_name)
    assert validate_branch_name(branch_name)["valid"] is True


@pytest.mark.parametrize(
    "branch_name",
    [
        "Codex/Uppercase",
        "codex/bad branch",
        "codex/bad:name",
        "codex//double",
        "/codex/leading",
        "codex/trailing/",
    ],
)
def test_invalid_branch_names_are_rejected(branch_name: str) -> None:
    validation = validate_branch_name(branch_name)

    assert validation["valid"] is False
    assert validation["errors"]


def test_git_safety_parser_counts_untracked_files() -> None:
    classification = classify_working_tree_status(["?? docs/new.md", "?? tests/new_test.py"])

    assert classification["is_clean"] is False
    assert classification["untracked_count"] == 2
    assert classification["tracked_changes_count"] == 0


def test_git_safety_parser_detects_tracked_modified_files() -> None:
    classification = classify_working_tree_status([" M ai_orchestrator/example.py", "A  tests/example.py"])

    assert classification["is_clean"] is False
    assert classification["tracked_changes_count"] == 2
    assert classification["untracked_count"] == 0
    assert any("tracked files have local changes" in warning for warning in classification["warnings"])


def test_git_safety_parser_detects_conflict_like_status_lines_and_blocks() -> None:
    dangerous = detect_dangerous_git_state(["UU ai_orchestrator/example.py", "AA tests/example.py"])

    assert dangerous["blocked"] is True
    assert dangerous["conflict_lines"] == ["UU ai_orchestrator/example.py", "AA tests/example.py"]
    assert dangerous["errors"] == ["merge/rebase conflict indicators detected in git status"]
