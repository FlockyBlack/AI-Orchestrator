from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / "agent_tasks" / "agents"
PROFILE_FILES = [
    "scout_agent.md",
    "planner_agent.md",
    "builder_agent.md",
    "tester_agent.md",
    "reviewer_agent.md",
    "docs_agent.md",
    "integrator_agent.md",
]


def test_subagent_profiles_exist() -> None:
    assert (AGENTS_DIR / "README.md").exists()
    for filename in PROFILE_FILES:
        assert (AGENTS_DIR / filename).exists()


def test_scout_profile_is_read_only() -> None:
    text = (AGENTS_DIR / "scout_agent.md").read_text(encoding="utf-8").lower()
    assert "read-only" in text
    assert "no code changes" in text
    assert "no file edits" in text


def test_reviewer_profile_checks_safety_and_git_rules() -> None:
    text = (AGENTS_DIR / "reviewer_agent.md").read_text(encoding="utf-8").lower()
    assert "safety" in text
    assert "forbidden-action scan" in text
    assert "git staging scan" in text
    assert "no approval of broad git staging" in text
