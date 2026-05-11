from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


SUBAGENT_ROUTE_SCHEMA_VERSION = "codex_subagent_route.v1"

CATEGORY_PMBOT = "pmbot_paper_product"
CATEGORY_CODEX_AUTOMATION = "codex_automation"
CATEGORY_DOCS = "docs_maintenance"
CATEGORY_SAFETY_REVIEW = "safety_review"

CATEGORY_ALIASES = {
    "pmbot": CATEGORY_PMBOT,
    "pmbot_paper": CATEGORY_PMBOT,
    "pmbot_product": CATEGORY_PMBOT,
    "pmbot_paper_product": CATEGORY_PMBOT,
    "paper_product": CATEGORY_PMBOT,
    "codex": CATEGORY_CODEX_AUTOMATION,
    "automation": CATEGORY_CODEX_AUTOMATION,
    "codex_automation": CATEGORY_CODEX_AUTOMATION,
    "orch_automation": CATEGORY_CODEX_AUTOMATION,
    "docs": CATEGORY_DOCS,
    "documentation": CATEGORY_DOCS,
    "maintenance": CATEGORY_DOCS,
    "docs_maintenance": CATEGORY_DOCS,
    "review": CATEGORY_SAFETY_REVIEW,
    "safety": CATEGORY_SAFETY_REVIEW,
    "safety_review": CATEGORY_SAFETY_REVIEW,
}

COMMON_SAFETY_BOUNDARIES = (
    "paper_mode_only_for_pmbot",
    "no_wallet_private_key_signing_orders_or_trading_endpoints",
    "no_openrouter_or_polymarket_api_without_separate_approval",
    "no_browser_automation_or_authenticated_endpoints",
    "no_daemon_scheduler_or_background_worker",
    "selective_git_staging_only",
)

CATEGORY_ROUTES: dict[str, dict[str, Any]] = {
    CATEGORY_PMBOT: {
        "selected_profile": "Builder",
        "profile_file": "builder_agent.md",
        "subagent_plan": ("Scout", "Planner", "Builder", "Tester", "Reviewer", "Docs", "Integrator"),
        "reason": "PMBOT paper/product work uses Builder with Scout, Tester, Reviewer, Docs, and Integrator gates.",
        "category_safety_boundaries": ("pmbot_paper_only", "no_live_trading_permission"),
    },
    CATEGORY_CODEX_AUTOMATION: {
        "selected_profile": "Builder",
        "profile_file": "builder_agent.md",
        "subagent_plan": ("Scout", "Planner", "Builder", "Tester", "Reviewer", "Docs", "Integrator"),
        "reason": "Codex automation work uses Builder with full queue, panel, test, review, and docs gates.",
        "category_safety_boundaries": ("no_uncontrolled_codex_loop", "operator_supervision_required"),
    },
    CATEGORY_DOCS: {
        "selected_profile": "Docs",
        "profile_file": "docs_agent.md",
        "subagent_plan": ("Scout", "Docs", "Reviewer", "Integrator"),
        "reason": "Docs and maintenance work uses Docs with read-only discovery and review gates.",
        "category_safety_boundaries": ("no_fake_success_claims", "operator_artifacts_required"),
    },
    CATEGORY_SAFETY_REVIEW: {
        "selected_profile": "Reviewer",
        "profile_file": "reviewer_agent.md",
        "subagent_plan": ("Scout", "Reviewer", "Integrator"),
        "reason": "Safety and review work uses Reviewer with Scout evidence and Integrator acceptance gates.",
        "category_safety_boundaries": ("forbidden_action_scan_required", "git_staging_scan_required"),
    },
}

PROFILE_OUTPUTS = {
    "Scout": "scout_report",
    "Planner": "implementation_plan",
    "Builder": "implementation_notes",
    "Tester": "validation_report",
    "Reviewer": "review_report",
    "Docs": "docs_report",
    "Integrator": "integration_decision",
}


@dataclass(frozen=True)
class SubagentRoute:
    schema_version: str
    task_id: str
    category: str
    selected_profile: str
    selected_profile_path: str
    selected_profile_exists: bool
    agents_md_path: str
    agents_md_exists: bool
    subagent_plan: tuple[str, ...]
    expected_outputs: dict[str, str]
    safety_boundaries: tuple[str, ...]
    live_trading_permission: bool
    reason: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["subagent_plan"] = list(self.subagent_plan)
        payload["safety_boundaries"] = list(self.safety_boundaries)
        payload["warnings"] = list(self.warnings)
        return payload


def route_subagent_profile(
    task_id: str,
    *,
    task_category: str = "",
    repo_root: str | Path = ".",
    allowed_paths: Iterable[str] = (),
    title: str = "",
    description: str = "",
) -> SubagentRoute:
    root = Path(repo_root).resolve(strict=False)
    category = normalize_task_category(task_category) or infer_task_category(
        task_id,
        allowed_paths=allowed_paths,
        title=title,
        description=description,
    )
    route = CATEGORY_ROUTES[category]
    profile_path = root / "agent_tasks" / "agents" / str(route["profile_file"])
    agents_md_path = root / "AGENTS.md"
    subagent_plan = tuple(str(value) for value in route["subagent_plan"])
    warnings: list[str] = []
    if not agents_md_path.exists():
        warnings.append("AGENTS.md was not found at the routed repo root")
    if not profile_path.exists():
        warnings.append(f"selected subagent profile was not found: {profile_path}")
    safety_boundaries = _unique_strings(
        [
            *COMMON_SAFETY_BOUNDARIES,
            *tuple(str(value) for value in route["category_safety_boundaries"]),
        ]
    )
    return SubagentRoute(
        schema_version=SUBAGENT_ROUTE_SCHEMA_VERSION,
        task_id=str(task_id),
        category=category,
        selected_profile=str(route["selected_profile"]),
        selected_profile_path=str(profile_path),
        selected_profile_exists=profile_path.exists(),
        agents_md_path=str(agents_md_path),
        agents_md_exists=agents_md_path.exists(),
        subagent_plan=subagent_plan,
        expected_outputs={role: PROFILE_OUTPUTS.get(role, f"{role.lower()}_output") for role in subagent_plan},
        safety_boundaries=tuple(safety_boundaries),
        live_trading_permission=False,
        reason=str(route["reason"]),
        warnings=tuple(warnings),
    )


def normalize_task_category(value: str) -> str:
    normalized = "_".join(str(value or "").strip().lower().replace("-", "_").split())
    return CATEGORY_ALIASES.get(normalized, normalized if normalized in CATEGORY_ROUTES else "")


def infer_task_category(
    task_id: str,
    *,
    allowed_paths: Iterable[str] = (),
    title: str = "",
    description: str = "",
) -> str:
    haystack = " ".join(
        [
            str(task_id or ""),
            str(title or ""),
            str(description or ""),
            *[str(path or "") for path in allowed_paths],
        ]
    ).lower()
    normalized_paths = tuple(str(path or "").replace("\\", "/").lower() for path in allowed_paths)
    if "orch-codex-automation" in haystack or "ai_orchestrator/codex_queue" in haystack or "ai_orchestrator/operator_panel" in haystack:
        return CATEGORY_CODEX_AUTOMATION
    if any(token in haystack for token in ("safety", "review", "audit")):
        return CATEGORY_SAFETY_REVIEW
    if "pmbot" in haystack or any(path.startswith("pm_bot/") for path in normalized_paths):
        return CATEGORY_PMBOT
    if any(path.startswith("docs/") for path in normalized_paths) or "maintenance" in haystack or "docs" in haystack:
        return CATEGORY_DOCS
    return CATEGORY_CODEX_AUTOMATION


def route_from_task_payload(
    task_payload: Mapping[str, Any],
    *,
    repo_root: str | Path = ".",
    task_category: str = "",
) -> SubagentRoute:
    return route_subagent_profile(
        str(task_payload.get("task_id") or ""),
        task_category=task_category or str(task_payload.get("task_category") or task_payload.get("category") or ""),
        repo_root=repo_root,
        allowed_paths=tuple(str(value) for value in task_payload.get("allowed_paths", [])),
        title=str(task_payload.get("title") or ""),
        description=str(task_payload.get("description") or task_payload.get("summary") or ""),
    )


def _unique_strings(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return result
