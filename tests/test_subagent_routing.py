from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.subagent_routing import (
    CATEGORY_CODEX_AUTOMATION,
    CATEGORY_DOCS,
    CATEGORY_PMBOT,
    CATEGORY_SAFETY_REVIEW,
    infer_task_category,
    route_subagent_profile,
)


def test_subagent_routing_is_deterministic_for_explicit_category(tmp_path: Path) -> None:
    _write_profile_tree(tmp_path)

    first = route_subagent_profile(
        "PMBOT-PAPER-ACCOUNTING-001",
        task_category="pmbot_paper_product",
        repo_root=tmp_path,
    ).to_dict()
    second = route_subagent_profile(
        "PMBOT-PAPER-ACCOUNTING-001",
        task_category="pmbot_paper_product",
        repo_root=tmp_path,
    ).to_dict()

    assert first == second
    assert first["category"] == CATEGORY_PMBOT
    assert first["selected_profile"] == "Builder"
    assert first["live_trading_permission"] is False
    assert "no_live_trading_permission" in first["safety_boundaries"]


def test_subagent_routing_selects_docs_and_review_profiles(tmp_path: Path) -> None:
    _write_profile_tree(tmp_path)

    docs = route_subagent_profile("ORCH-DOCS-001", task_category="docs", repo_root=tmp_path)
    review = route_subagent_profile("ORCH-SAFETY-REVIEW-001", task_category="safety_review", repo_root=tmp_path)

    assert docs.category == CATEGORY_DOCS
    assert docs.selected_profile == "Docs"
    assert review.category == CATEGORY_SAFETY_REVIEW
    assert review.selected_profile == "Reviewer"


def test_subagent_category_inference_prefers_codex_automation_paths() -> None:
    category = infer_task_category(
        "ORCH-CODEX-AUTOMATION-029",
        allowed_paths=("ai_orchestrator/codex_queue/", "tests/"),
    )

    assert category == CATEGORY_CODEX_AUTOMATION


def _write_profile_tree(root: Path) -> None:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    agents_dir = root / "agent_tasks" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "builder_agent.md").write_text("# Builder Agent\n", encoding="utf-8")
    (agents_dir / "docs_agent.md").write_text("# Docs Agent\n", encoding="utf-8")
    (agents_dir / "reviewer_agent.md").write_text("# Reviewer Agent\n", encoding="utf-8")
