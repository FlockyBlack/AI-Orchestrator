from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ai_orchestrator.codex_queue.plan_contract import PlanContract, PlanTaskSpec, load_plan_contract
from ai_orchestrator.codex_queue.plan_run_state import PlanRunState, load_state

from .symphony_session_plan import CodexAppServerSessionPlan
from .symphony_task_contract import (
    SymphonyAcceptancePolicy,
    SymphonyTask,
    SymphonyTaskSource,
    SymphonyTaskStatus,
    proof_requirements_from_task,
)
from .symphony_workspace_plan import SymphonyWorkspacePlan


def map_plan_task_to_symphony_task(
    plan_task: PlanTaskSpec | Mapping[str, Any],
    run_state: PlanRunState | Mapping[str, Any],
    plan_contract: PlanContract | Mapping[str, Any],
) -> SymphonyTask:
    task = plan_task if isinstance(plan_task, PlanTaskSpec) else PlanTaskSpec.from_dict(plan_task)
    state = run_state if isinstance(run_state, PlanRunState) else PlanRunState.from_dict(run_state)
    plan = plan_contract if isinstance(plan_contract, PlanContract) else PlanContract.from_dict(plan_contract)
    completed = set(state.completed_task_ids)
    blocked = set(state.blocked_task_ids)
    failed = set(state.failed_task_ids)
    dependencies_satisfied = all(dependency in completed for dependency in task.dependencies)
    status = _task_status(task.task_id, dependencies_satisfied, completed, blocked, failed)
    safety_boundaries = tuple(
        f"{boundary.boundary_id}: {boundary.description}" if boundary.description else boundary.boundary_id
        for boundary in plan.safety_boundaries
        if boundary.required
    )
    acceptance_policy = SymphonyAcceptancePolicy(
        gates=task.acceptance_gates,
        expected_artifacts=task.expected_artifacts,
        require_validation=True,
        require_safety_ok=True,
        require_operator_review=True,
    )
    return SymphonyTask(
        task_id=task.task_id,
        title=task.title,
        description=task.description,
        source_plan_id=plan.plan_id,
        source_run_id=state.run_id,
        dependencies=task.dependencies,
        allowed_paths=task.allowed_paths,
        forbidden_actions=task.forbidden_actions,
        acceptance_gates=task.acceptance_gates,
        expected_artifacts=task.expected_artifacts,
        max_retries=task.max_retries,
        safety_boundaries=safety_boundaries,
        proof_requirements=proof_requirements_from_task(task.acceptance_gates, task.expected_artifacts),
        source=SymphonyTaskSource(
            source_plan_id=plan.plan_id,
            source_run_id=state.run_id,
            source_plan_file=str(plan.raw.get("_source_plan_file", "")) if isinstance(plan.raw, Mapping) else "",
            state_path="",
            manifest_path=state.queue_manifest_path,
        ),
        status=SymphonyTaskStatus(
            status=status,
            runnable=status == "runnable",
            dependencies_satisfied=dependencies_satisfied,
            attempt=int(state.task_states.get(task.task_id).attempts if task.task_id in state.task_states else 0),
            retry_count=int(state.retry_counts.get(task.task_id, 0)),
            blocked_reasons=tuple(_blocked_reasons(task.task_id, status, task.dependencies, completed, state)),
        ),
        acceptance_policy=acceptance_policy,
        metadata={
            "execution_mode": task.execution_mode,
            "execution_lane": task.execution_lane,
            "milestone_id": task.milestone_id,
            **dict(task.metadata),
        },
    )


def map_queue_task_to_symphony_task(
    task_spec_path: str | Path,
    state_path: str | Path,
    manifest_path: str | Path,
) -> SymphonyTask:
    task_payload = _read_json(task_spec_path)
    manifest = _read_json(manifest_path)
    plan_file = str(manifest.get("source_plan_file") or "")
    plan = load_plan_contract(plan_file)
    state = load_state(state_path)
    task = PlanTaskSpec.from_dict(task_payload)
    symphony_task = map_plan_task_to_symphony_task(task, state, plan)
    source = SymphonyTaskSource(
        source_plan_id=plan.plan_id,
        source_run_id=state.run_id,
        source_plan_file=plan_file,
        task_spec_path=str(task_spec_path),
        state_path=str(state_path),
        manifest_path=str(manifest_path),
    )
    return SymphonyTask.from_dict({**symphony_task.to_dict(), "source": source.to_dict()})


def map_symphony_task_to_codex_packet(
    symphony_task: SymphonyTask | Mapping[str, Any],
    workspace_plan: SymphonyWorkspacePlan | Mapping[str, Any],
    session_plan: CodexAppServerSessionPlan | Mapping[str, Any],
) -> dict[str, Any]:
    task = symphony_task if isinstance(symphony_task, SymphonyTask) else SymphonyTask.from_dict(symphony_task)
    workspace = workspace_plan if isinstance(workspace_plan, SymphonyWorkspacePlan) else SymphonyWorkspacePlan.from_dict(workspace_plan)
    session = session_plan if isinstance(session_plan, CodexAppServerSessionPlan) else CodexAppServerSessionPlan.from_dict(session_plan)
    prompt_preview = _render_prompt_preview(task, workspace, session)
    return {
        "schema_version": "symphony_codex_app_server_packet.v1",
        "packet_id": f"symphony_packet_{task.source_run_id}_{task.task_id}",
        "task_id": task.task_id,
        "plan_id": task.source_plan_id,
        "run_id": task.source_run_id,
        "workspace_path": workspace.workspace_path,
        "session_id": session.session_id,
        "app_server_transport": session.app_server_transport,
        "app_server_listen": session.app_server_listen,
        "protocol_version": session.protocol_version,
        "requests": {
            "initialize": {
                "id": 1,
                "method": session.initialize_method,
                "params": {
                    "capabilities": {"experimentalApi": True},
                    "clientInfo": {
                        "name": "ai-orchestrator-symphony-adapter",
                        "title": "AI-Orchestrator Symphony Adapter",
                        "version": "0.1.0",
                    },
                },
            },
            "thread_start": {
                "id": 2,
                "method": session.thread_start_method,
                "params": {
                    "cwd": workspace.workspace_path,
                    "approvalPolicy": session.approval_policy,
                    "sandbox": "workspace-write",
                    "serviceName": "ai-orchestrator",
                },
            },
            "turn_start_template": {
                "id": 3,
                "method": session.turn_start_method,
                "params": {
                    "threadId": "<thread.id from thread/start response>",
                    "input": [{"type": "text", "text": prompt_preview}],
                    "cwd": workspace.workspace_path,
                    "approvalPolicy": session.approval_policy,
                    "sandboxPolicy": dict(session.sandbox_policy),
                    "outputSchema": dict(session.result_contract),
                },
            },
        },
        "result_contract": dict(session.result_contract),
        "safety": {
            "render_only": True,
            "real_app_server_started": False,
            "real_codex_invocation": False,
            "daemon_created": False,
            "scheduler_created": False,
            "background_worker_created": False,
            "external_network_used": False,
        },
    }


def _task_status(
    task_id: str,
    dependencies_satisfied: bool,
    completed: set[str],
    blocked: set[str],
    failed: set[str],
) -> str:
    if task_id in completed:
        return "completed"
    if task_id in blocked:
        return "blocked"
    if task_id in failed:
        return "failed"
    if dependencies_satisfied:
        return "runnable"
    return "waiting_dependencies"


def _blocked_reasons(
    task_id: str,
    status: str,
    dependencies: tuple[str, ...],
    completed: set[str],
    state: PlanRunState,
) -> list[str]:
    if status == "waiting_dependencies":
        return [f"dependency_not_completed:{dependency}" for dependency in dependencies if dependency not in completed]
    task_state = state.task_states.get(task_id)
    return list(task_state.errors) if task_state else []


def _render_prompt_preview(task: SymphonyTask, workspace: SymphonyWorkspacePlan, session: CodexAppServerSessionPlan) -> str:
    return "\n".join(
        [
            f"# Symphony Task {task.task_id}",
            "",
            task.description,
            "",
            f"Workspace: {workspace.workspace_path}",
            f"Expected result path: {session.expected_result_path}",
            "",
            "Forbidden actions:",
            *(f"- {value}" for value in task.forbidden_actions),
        ]
    )


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON file must contain an object: {path}")
    return dict(payload)
