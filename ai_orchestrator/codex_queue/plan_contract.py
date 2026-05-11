from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping


UNSAFE_GIT_STAGING_PATTERNS = (
    "git add .",
    "git add -a",
    "git add --all",
)

FORCE_PUSH_PATTERNS = (
    "git push --force",
    "git push -f",
    "--force-with-lease",
)

DANGEROUS_REQUEST_PATTERNS = (
    "submit real order",
    "place real order",
    "real order submitted",
    "execute real trade",
    "enable real trading",
    "autonomous real trading",
    "enable autonomous trading",
    "use wallet",
    "wallet signing",
    "sign transaction",
    "private key",
    "trading endpoint",
    "authenticated endpoint",
    "browser automation",
    "openrouter api call",
    "call openrouter",
    "use openrouter",
    "polymarket api call",
    "call polymarket api",
    "use polymarket api",
)


@dataclass(frozen=True)
class SafetyBoundary:
    boundary_id: str
    description: str
    required: bool = True

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SafetyBoundary":
        return cls(
            boundary_id=str(payload.get("boundary_id") or payload.get("id") or ""),
            description=str(payload.get("description") or ""),
            required=bool(payload.get("required", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AcceptanceGate:
    gate_id: str
    description: str
    required: bool = True

    @classmethod
    def from_dict(cls, payload: Any) -> "AcceptanceGate":
        if isinstance(payload, str):
            return cls(gate_id=payload, description=payload)
        if not isinstance(payload, Mapping):
            return cls(gate_id="", description=str(payload))
        return cls(
            gate_id=str(payload.get("gate_id") or payload.get("id") or payload.get("name") or ""),
            description=str(payload.get("description") or payload.get("command") or ""),
            required=bool(payload.get("required", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionLane:
    lane_id: str
    title: str = ""
    description: str = ""
    allowed_roots: tuple[str, ...] = ()
    max_parallel: int = 1
    dry_run_only: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExecutionLane":
        return cls(
            lane_id=str(payload.get("lane_id") or payload.get("id") or ""),
            title=str(payload.get("title") or payload.get("name") or ""),
            description=str(payload.get("description") or ""),
            allowed_roots=tuple(str(value) for value in payload.get("allowed_roots", [])),
            max_parallel=int(payload.get("max_parallel", 1) or 1),
            dry_run_only=bool(payload.get("dry_run_only", True)),
            metadata={key: value for key, value in payload.items() if key not in {
                "lane_id",
                "id",
                "title",
                "name",
                "description",
                "allowed_roots",
                "max_parallel",
                "dry_run_only",
            }},
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_roots"] = list(self.allowed_roots)
        return payload


@dataclass(frozen=True)
class PlanMilestone:
    milestone_id: str
    title: str
    description: str = ""
    task_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PlanMilestone":
        return cls(
            milestone_id=str(payload.get("milestone_id") or payload.get("id") or ""),
            title=str(payload.get("title") or ""),
            description=str(payload.get("description") or ""),
            task_ids=tuple(str(value) for value in payload.get("task_ids", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_ids"] = list(self.task_ids)
        return payload


@dataclass(frozen=True)
class PlanTaskSpec:
    task_id: str
    title: str
    description: str
    dependencies: tuple[str, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    acceptance_gates: tuple[str, ...] = ()
    expected_artifacts: tuple[str, ...] = ()
    max_retries: int = 0
    execution_mode: str = "fake"
    execution_lane: str = "default"
    milestone_id: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PlanTaskSpec":
        return cls(
            task_id=str(payload.get("task_id") or ""),
            title=str(payload.get("title") or ""),
            description=str(payload.get("description") or ""),
            dependencies=tuple(str(value) for value in payload.get("dependencies", [])),
            allowed_paths=tuple(str(value) for value in payload.get("allowed_paths", [])),
            forbidden_actions=tuple(str(value) for value in payload.get("forbidden_actions", [])),
            acceptance_gates=tuple(_gate_to_text(value) for value in payload.get("acceptance_gates", [])),
            expected_artifacts=tuple(str(value) for value in payload.get("expected_artifacts", [])),
            max_retries=int(payload.get("max_retries", 0) or 0),
            execution_mode=str(payload.get("execution_mode") or "fake"),
            execution_lane=str(payload.get("execution_lane") or "default"),
            milestone_id=str(payload.get("milestone_id") or ""),
            metadata={key: value for key, value in payload.items() if key not in {
                "task_id",
                "title",
                "description",
                "dependencies",
                "allowed_paths",
                "forbidden_actions",
                "acceptance_gates",
                "expected_artifacts",
                "max_retries",
                "execution_mode",
                "execution_lane",
                "milestone_id",
            }},
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["dependencies"] = list(self.dependencies)
        payload["allowed_paths"] = list(self.allowed_paths)
        payload["forbidden_actions"] = list(self.forbidden_actions)
        payload["acceptance_gates"] = list(self.acceptance_gates)
        payload["expected_artifacts"] = list(self.expected_artifacts)
        return payload


@dataclass(frozen=True)
class PlanContract:
    plan_id: str
    version: str
    title: str = ""
    description: str = ""
    owner: str = ""
    created_at: str = ""
    repo_root: str = ""
    branch: str = ""
    expected_head: str = ""
    mode: str = "long_supervised"
    continue_until: str = "blocked_or_done"
    max_steps_default: int = 50
    safety_boundaries: tuple[SafetyBoundary, ...] = ()
    execution_lanes: tuple[ExecutionLane, ...] = ()
    milestones: tuple[PlanMilestone, ...] = ()
    tasks: tuple[PlanTaskSpec, ...] = ()
    acceptance_gates: tuple[AcceptanceGate, ...] = ()
    commit_policy: Mapping[str, Any] = field(default_factory=dict)
    push_policy: Mapping[str, Any] = field(default_factory=dict)
    dashboard_policy: Mapping[str, Any] = field(default_factory=dict)
    memory_policy: Mapping[str, Any] | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PlanContract":
        return cls(
            plan_id=str(payload.get("plan_id") or ""),
            version=str(payload.get("version") or ""),
            title=str(payload.get("title") or ""),
            description=str(payload.get("description") or ""),
            owner=str(payload.get("owner") or ""),
            created_at=str(payload.get("created_at") or ""),
            repo_root=str(payload.get("repo_root") or ""),
            branch=str(payload.get("branch") or ""),
            expected_head=str(payload.get("expected_head") or ""),
            mode=str(payload.get("mode") or "long_supervised"),
            continue_until=str(payload.get("continue_until") or "blocked_or_done"),
            max_steps_default=int(payload.get("max_steps_default", 50) or 50),
            safety_boundaries=tuple(
                SafetyBoundary.from_dict(item)
                for item in _mapping_list(payload.get("safety_boundaries", []))
            ),
            execution_lanes=tuple(
                ExecutionLane.from_dict(item)
                for item in _mapping_list(payload.get("execution_lanes", []))
            ),
            milestones=tuple(
                PlanMilestone.from_dict(item)
                for item in _mapping_list(payload.get("milestones", []))
            ),
            tasks=tuple(
                PlanTaskSpec.from_dict(item)
                for item in _mapping_list(payload.get("tasks", []))
            ),
            acceptance_gates=tuple(
                AcceptanceGate.from_dict(item)
                for item in payload.get("acceptance_gates", [])
            ),
            commit_policy=dict(payload.get("commit_policy") or {}),
            push_policy=dict(payload.get("push_policy") or {}),
            dashboard_policy=dict(payload.get("dashboard_policy") or {}),
            memory_policy=dict(payload["memory_policy"]) if isinstance(payload.get("memory_policy"), Mapping) else None,
            raw=dict(payload),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
            "created_at": self.created_at,
            "repo_root": self.repo_root,
            "branch": self.branch,
            "expected_head": self.expected_head,
            "mode": self.mode,
            "continue_until": self.continue_until,
            "max_steps_default": self.max_steps_default,
            "safety_boundaries": [item.to_dict() for item in self.safety_boundaries],
            "execution_lanes": [item.to_dict() for item in self.execution_lanes],
            "milestones": [item.to_dict() for item in self.milestones],
            "tasks": [item.to_dict() for item in self.tasks],
            "acceptance_gates": [item.to_dict() for item in self.acceptance_gates],
            "commit_policy": dict(self.commit_policy),
            "push_policy": dict(self.push_policy),
            "dashboard_policy": dict(self.dashboard_policy),
            "memory_policy": dict(self.memory_policy) if self.memory_policy else None,
        }


@dataclass(frozen=True)
class PlanValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    plan_id: str = ""
    task_count: int = 0
    lane_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "plan_id": self.plan_id,
            "task_count": self.task_count,
            "lane_count": self.lane_count,
        }


def load_plan_contract(path: str | Path) -> PlanContract:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("plan contract JSON must be an object")
    return PlanContract.from_dict(payload)


def validate_plan_contract(plan: PlanContract) -> PlanValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not plan.plan_id.strip():
        errors.append("missing plan_id")
    if not plan.version.strip():
        errors.append("missing version")
    if not plan.tasks:
        errors.append("plan must contain at least one task")

    task_ids = [task.task_id for task in plan.tasks]
    lane_ids = [lane.lane_id for lane in plan.execution_lanes]
    milestone_ids = [milestone.milestone_id for milestone in plan.milestones]

    errors.extend(_duplicates("task", task_ids))
    errors.extend(_duplicates("lane", lane_ids))
    errors.extend(_duplicates("milestone", milestone_ids))
    if any(not task_id for task_id in task_ids):
        errors.append("task_id must be non-empty for every task")
    if any(not lane_id for lane_id in lane_ids):
        errors.append("lane_id must be non-empty for every execution lane")

    known_tasks = set(task_ids)
    known_lanes = set(lane_ids)
    for task in plan.tasks:
        for dependency in task.dependencies:
            if dependency not in known_tasks:
                errors.append(f"task {task.task_id} has unknown dependency: {dependency}")
        if known_lanes and task.execution_lane not in known_lanes:
            errors.append(f"task {task.task_id} references unknown execution_lane: {task.execution_lane}")
        if task.max_retries < 0:
            errors.append(f"task {task.task_id} max_retries must not be negative")
        if not task.allowed_paths:
            warnings.append(f"task {task.task_id} has no allowed_paths")
        errors.extend(_scan_task_for_danger(task))

    errors.extend(_detect_cycles(plan.tasks))
    errors.extend(_scan_policy_for_danger("commit_policy", plan.commit_policy))
    errors.extend(_scan_policy_for_danger("push_policy", plan.push_policy))

    if _truthy_policy(plan.push_policy, "force") or _truthy_policy(plan.push_policy, "force_push"):
        errors.append("push_policy must not allow force push")
    if _truthy_policy(plan.commit_policy, "unsafe_staging"):
        errors.append("commit_policy must not allow unsafe staging")
    if _truthy_policy(plan.raw, "openrouter_approved") is False and _truthy_policy(plan.raw, "use_openrouter"):
        errors.append("OpenRouter usage is not allowed unless explicitly approved")
    if _truthy_policy(plan.raw, "polymarket_api_approved") is False and _truthy_policy(plan.raw, "use_polymarket_api"):
        errors.append("Polymarket API usage is not allowed unless explicitly approved")

    return PlanValidationResult(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        plan_id=plan.plan_id,
        task_count=len(plan.tasks),
        lane_count=len(plan.execution_lanes),
    )


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _gate_to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return str(value.get("description") or value.get("command") or value.get("gate_id") or value)
    return str(value)


def _duplicates(label: str, values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if not value:
            continue
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return [f"duplicate {label} ID: {value}" for value in duplicates]


def _detect_cycles(tasks: tuple[PlanTaskSpec, ...]) -> list[str]:
    graph = {task.task_id: set(task.dependencies) for task in tasks}
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: list[str] = []

    def visit(task_id: str, path: list[str]) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            cycle_start = path.index(task_id) if task_id in path else 0
            cycles.append("dependency cycle: " + " -> ".join(path[cycle_start:] + [task_id]))
            return
        visiting.add(task_id)
        for dependency in sorted(graph.get(task_id, ())):
            if dependency in graph:
                visit(dependency, path + [dependency])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in sorted(graph):
        visit(task_id, [task_id])
    return cycles


def _scan_task_for_danger(task: PlanTaskSpec) -> list[str]:
    errors: list[str] = []
    scan_values = [
        task.title,
        task.description,
        task.execution_mode,
        *task.acceptance_gates,
        *task.expected_artifacts,
    ]
    for text in scan_values:
        errors.extend(_danger_errors(f"task {task.task_id}", text))
    if _unresolved_outcome_without_evidence(task.description):
        errors.append(f"task {task.task_id} marks unresolved market outcomes as resolved without evidence")
    return errors


def _scan_policy_for_danger(label: str, policy: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for text in _flatten_strings(policy):
        errors.extend(_danger_errors(label, text))
    return errors


def _danger_errors(label: str, text: Any) -> list[str]:
    value = str(text).strip().lower()
    if not value:
        return []
    errors: list[str] = []
    for pattern in UNSAFE_GIT_STAGING_PATTERNS:
        if pattern in value:
            errors.append(f"{label} contains unsafe git staging command: {pattern}")
    for pattern in FORCE_PUSH_PATTERNS:
        if pattern in value:
            errors.append(f"{label} contains force push command: {pattern}")
    for pattern in DANGEROUS_REQUEST_PATTERNS:
        if pattern in value and not _looks_like_safety_prohibition(value, pattern):
            errors.append(f"{label} requests forbidden action: {pattern}")
    return errors


def _looks_like_safety_prohibition(text: str, pattern: str) -> bool:
    index = text.find(pattern)
    if index < 0:
        return False
    prefix = text[max(0, index - 24):index]
    sentence = text[max(0, index - 80): index + len(pattern) + 80]
    return (
        "no " in prefix
        or "do not " in prefix
        or "forbid" in prefix
        or "forbidden" in sentence
        or "unless explicitly approved" in sentence
    )


def _unresolved_outcome_without_evidence(text: str) -> bool:
    value = text.lower()
    return "unresolved market" in value and "resolved" in value and "without evidence" in value


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        result: list[str] = []
        for item in value.values():
            result.extend(_flatten_strings(item))
        return result
    if isinstance(value, list | tuple | set):
        result = []
        for item in value:
            result.extend(_flatten_strings(item))
        return result
    return [str(value)] if value is not None else []


def _truthy_policy(policy: Mapping[str, Any], key: str) -> bool:
    return bool(policy.get(key, False))
