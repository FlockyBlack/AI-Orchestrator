from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol

from .codex_execution_packet import (
    write_execution_packet,
    write_execution_prompt,
    write_expected_result_template,
)
from .codex_cli_executor import (
    CodexCliInvocationResult,
    collect_codex_result,
    invoke_codex_cli,
    load_codex_cli_executor_config,
    result_json_path_for_packet,
    validate_codex_cli_executor_config,
    write_invocation_log,
)
from .codex_executor_contract import (
    CodexExecutionMode,
    build_execution_packet,
    validate_execution_packet,
)
from .codex_result_ingestion import ingest_codex_result
from .plan_contract import PlanContract, PlanTaskSpec


@dataclass(frozen=True)
class TaskExecutionContext:
    task_spec: PlanTaskSpec
    plan: PlanContract
    queue_root: str | Path
    run_id: str
    plan_id: str
    repo_root: str | Path
    run_dir: str | Path
    state_summary: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskExecutionResult:
    status: str
    result_payload: dict[str, Any]
    artifact_paths: tuple[str, ...] = ()
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "result_payload": self.result_payload,
            "artifact_paths": list(self.artifact_paths),
            "message": self.message,
        }


class TaskExecutor(Protocol):
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        ...


@dataclass
class FakeTaskExecutor:
    blocked_task_ids: set[str] = field(default_factory=set)
    failed_task_ids: set[str] = field(default_factory=set)
    needs_retry_task_ids: set[str] = field(default_factory=set)
    handoff_task_ids: set[str] = field(default_factory=set)

    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        task = context.task_spec
        artifact_dir = Path(context.run_dir) / "artifacts"
        artifact_path = artifact_dir / f"{task.task_id}_fake_{_timestamp_for_filename()}.json"
        behavior = _fake_behavior_for_task(self, task)
        if behavior == "accepted":
            result_status = "completed"
            validation_passed = True
            message = "fake task completed"
            extra: dict[str, Any] = {}
        elif behavior == "blocked":
            result_status = "blocked"
            validation_passed = False
            message = "fake task blocked"
            extra = {"blocked_reason": "Injected fake blocker for deterministic test coverage."}
        elif behavior == "failed":
            result_status = "failed"
            validation_passed = False
            message = "fake task failed"
            extra = {"failure_reason": "Injected fake failure for deterministic test coverage."}
        elif behavior == "needs_retry":
            result_status = "needs_retry"
            validation_passed = False
            message = "fake task needs retry"
            extra = {"retry_reason": "Injected fake retry request for deterministic test coverage."}
        elif behavior == "requiring_operator_handoff":
            result_status = "requiring_operator_handoff"
            validation_passed = True
            message = "fake task requires operator handoff"
            extra = {"handoff_reason": "Injected fake handoff request for deterministic test coverage."}
        else:
            result_status = "failed"
            validation_passed = False
            message = f"unknown fake behavior: {behavior}"
            extra = {"failure_reason": message}

        payload = _base_payload(task, context, status=result_status)
        payload.update(
            {
                "validation_passed": validation_passed,
                "safety_ok": True,
                "artifacts": [str(artifact_path)],
                "commands_run": [],
                "fake_executor": True,
                "fake_behavior": behavior,
                "safety_boundaries_acknowledged": [
                    boundary.boundary_id for boundary in context.plan.safety_boundaries if boundary.required
                ],
                "real_order_submitted": False,
                "wallet_used": False,
                "trading_endpoint_used": False,
                "openrouter_used": False,
                "polymarket_api_used": False,
                "unsafe_git_staging_used": False,
                "force_push_used": False,
            }
        )
        payload.update(extra)
        _write_json(artifact_path, payload)
        return TaskExecutionResult(result_status, payload, (str(artifact_path),), message)


class LocalNoopExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        payload = _base_payload(context.task_spec, context, status="completed")
        payload.update(
            {
                "validation_passed": True,
                "safety_ok": True,
                "artifacts": [],
                "commands_run": [],
                "noop_executor": True,
                "safety_boundaries_acknowledged": [
                    boundary.boundary_id for boundary in context.plan.safety_boundaries if boundary.required
                ],
            }
        )
        return TaskExecutionResult("completed", payload, (), "noop task completed")


class CodexHandoffExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        task = context.task_spec
        handoff_dir = Path(context.run_dir) / "handoff"
        handoff_path = handoff_dir / f"{task.task_id}_codex_prompt.md"
        prompt = render_codex_handoff_prompt(context)
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text(prompt, encoding="utf-8")
        payload = _base_payload(task, context, status="requiring_operator_handoff")
        payload.update(
            {
                "validation_passed": True,
                "safety_ok": True,
                "artifacts": [str(handoff_path)],
                "handoff_prompt_path": str(handoff_path),
                "commands_run": [],
                "codex_invoked": False,
                "safety_boundaries_acknowledged": [
                    boundary.boundary_id for boundary in context.plan.safety_boundaries if boundary.required
                ],
            }
        )
        return TaskExecutionResult(
            "requiring_operator_handoff",
            payload,
            (str(handoff_path),),
            "Codex handoff prompt generated; Codex was not invoked.",
        )


class CodexPacketExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        packet, paths = _write_packet_artifacts(context, CodexExecutionMode.MANUAL_HANDOFF.value)
        validation = validate_execution_packet(packet)
        payload = _base_payload(context.task_spec, context, status="requiring_operator_handoff")
        payload.update(
            {
                "validation_passed": validation.valid,
                "safety_ok": validation.safety_ok,
                "artifacts": list(paths.values()),
                "commands_run": [],
                "codex_invoked": False,
                "adapter_mode": packet.adapter_mode,
                "requires_operator_handoff": True,
                "requires_operator_approval": packet.requires_operator_approval,
                "execution_packet_path": paths["packet"],
                "execution_prompt_path": paths["prompt"],
                "expected_result_template_path": paths["expected_result_template"],
                "readme_path": paths["readme"],
                "validation_errors": list(validation.errors),
                "validation_warnings": list(validation.warnings),
                "next_operator_action": "Open prompt.md, run it manually only if approved, then ingest the returned JSON.",
                "safety_boundaries_acknowledged": list(packet.safety_boundaries),
            }
        )
        return TaskExecutionResult(
            "requiring_operator_handoff",
            payload,
            (paths["prompt"], paths["packet"], paths["expected_result_template"], paths["readme"]),
            "Codex execution packet generated; Codex was not invoked.",
        )


class CodexCliDryRunExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        packet, paths = _write_packet_artifacts(context, CodexExecutionMode.CODEX_CLI_DRY_RUN.value)
        command = _future_codex_cli_command(packet.prompt_path, context.repo_root)
        dry_run_path = Path(packet.prompt_path).parent / "codex_cli_dry_run.json"
        dry_run_payload = {
            "schema_version": "codex_cli_dry_run.v1",
            "created_at": _utc_iso(),
            "packet_id": packet.packet_id,
            "task_id": packet.task_id,
            "run_id": packet.run_id,
            "adapter_mode": packet.adapter_mode,
            "future_command": command,
            "codex_invoked": False,
            "external_process_started": False,
            "requires_operator_approval_before_real_execution": True,
            "safety": {
                "daemon_created": False,
                "scheduler_created": False,
                "background_worker_created": False,
                "wallet_or_trading_used": False,
                "openrouter_used": False,
                "polymarket_api_used": False,
                "browser_automation_used": False,
            },
        }
        _write_json(dry_run_path, dry_run_payload)
        validation = validate_execution_packet(packet)
        artifact_paths = (paths["prompt"], paths["packet"], paths["expected_result_template"], str(dry_run_path), paths["readme"])
        payload = _base_payload(context.task_spec, context, status="adapter_dry_run_ready")
        payload.update(
            {
                "validation_passed": validation.valid,
                "safety_ok": validation.safety_ok,
                "artifacts": list(artifact_paths),
                "commands_run": [],
                "codex_invoked": False,
                "adapter_mode": packet.adapter_mode,
                "requires_operator_handoff": False,
                "requires_operator_approval": True,
                "execution_packet_path": paths["packet"],
                "execution_prompt_path": paths["prompt"],
                "expected_result_template_path": paths["expected_result_template"],
                "codex_cli_dry_run_path": str(dry_run_path),
                "future_codex_cli_command": command,
                "validation_errors": list(validation.errors),
                "validation_warnings": list(validation.warnings),
                "next_operator_action": "Review dry-run command and packet; no Codex process was started.",
                "safety_boundaries_acknowledged": list(packet.safety_boundaries),
            }
        )
        return TaskExecutionResult(
            "adapter_dry_run_ready",
            payload,
            artifact_paths,
            "Codex CLI dry-run artifact generated; Codex was not invoked.",
        )


@dataclass
class CodexCliOperatorApprovedExecutor:
    future_approval_marker: str = ""

    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        if self.future_approval_marker != "ORCH_025_EXPLICIT_CODEX_CLI_INVOCATION_APPROVAL":
            raise NotImplementedError(
                "CodexCliOperatorApprovedExecutor is a 024 boundary stub. "
                "No Codex CLI invocation is implemented without a future explicit approval marker."
            )
        payload = _base_payload(context.task_spec, context, status="blocked")
        payload.update(
            {
                "validation_passed": False,
                "safety_ok": True,
                "artifacts": [],
                "commands_run": [],
                "codex_invoked": False,
                "adapter_mode": CodexExecutionMode.CODEX_CLI_OPERATOR_APPROVED.value,
                "blocked_reason": "Future approval marker was present, but actual Codex CLI invocation is intentionally not implemented in 024.",
            }
        )
        return TaskExecutionResult("blocked", payload, (), "Codex CLI invocation remains disabled in 024.")


@dataclass
class RealCodexCliExecutor:
    allow_real_codex_invocation: bool = False
    auto_ingest: bool = False
    config_path: str | Path | None = None
    timeout_seconds: int | None = None

    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        packet, paths = _write_packet_artifacts(context, CodexExecutionMode.CODEX_CLI_OPERATOR_APPROVED.value)
        config = load_codex_cli_executor_config(self.config_path or Path(context.queue_root) / "config" / "codex_executor_config.json")
        validation = validate_execution_packet(packet)
        config_validation = validate_codex_cli_executor_config(config)
        result_json_path = result_json_path_for_packet(packet, config)
        artifact_paths = _artifact_paths_from_real_codex(paths, result_json_path)

        if not validation.valid:
            return self._blocked(
                context,
                packet,
                paths,
                config,
                artifact_paths,
                "Codex execution packet validation failed.",
                list(validation.errors),
                validation_warnings=list(validation.warnings),
            )
        if not self.allow_real_codex_invocation:
            return self._blocked(
                context,
                packet,
                paths,
                config,
                artifact_paths,
                "Real Codex CLI invocation requires --allow-real-codex-invocation.",
                ["operator approval flag --allow-real-codex-invocation is required"],
            )
        if not self.auto_ingest:
            return self._blocked(
                context,
                packet,
                paths,
                config,
                artifact_paths,
                "Real Codex CLI executor requires --auto-ingest.",
                ["--auto-ingest is required for the codex_cli executor"],
            )
        if not config_validation["valid"]:
            return self._blocked(
                context,
                packet,
                paths,
                config,
                artifact_paths,
                "Codex CLI executor config is not enabled or safe.",
                list(config_validation["errors"]),
                validation_warnings=list(config_validation["warnings"]),
            )

        timeout = int(self.timeout_seconds or config.timeout_seconds)
        invocation = invoke_codex_cli(packet, config, timeout)
        artifact_paths = _artifact_paths_from_real_codex(paths, result_json_path, invocation)
        if invocation.status != "completed":
            status = "blocked" if invocation.status == "blocked" else "failed"
            return self._terminal_from_invocation(
                context,
                packet,
                paths,
                config,
                invocation,
                artifact_paths,
                status=status,
                message=f"Codex CLI invocation {invocation.status}.",
            )

        collected = collect_codex_result(packet, config)
        if collected["status"] == "missing":
            return self._terminal_from_invocation(
                context,
                packet,
                paths,
                config,
                invocation,
                artifact_paths,
                status="blocked",
                message="Codex CLI completed but did not write the required result JSON.",
                extra={"requires_result": True, "result_collection": collected},
            )
        if collected["status"] == "invalid":
            return self._terminal_from_invocation(
                context,
                packet,
                paths,
                config,
                invocation,
                artifact_paths,
                status="failed",
                message="Codex CLI result JSON failed validation.",
                extra={"result_collection": collected},
            )

        ingestion = ingest_codex_result(paths["packet"], str(result_json_path), context.queue_root)
        artifact_paths = _artifact_paths_from_real_codex(paths, result_json_path, invocation)
        report_json = str(ingestion.get("report_paths", {}).get("json", ""))
        report_md = str(ingestion.get("report_paths", {}).get("markdown", ""))
        if report_json:
            artifact_paths.append(report_json)
        if report_md:
            artifact_paths.append(report_md)
        artifact_paths = list(dict.fromkeys(path for path in artifact_paths if path))

        if ingestion["status"] not in {"accepted", "blocked", "failed", "needs_retry"}:
            payload = self._base_real_payload(
                context,
                packet,
                paths,
                config,
                status="failed",
                artifact_paths=artifact_paths,
            )
            payload.update(
                {
                    "validation_passed": False,
                    "safety_ok": False,
                    "codex_cli_invocation": invocation.to_dict(),
                    "result_collection": collected,
                    "codex_result_ingestion": ingestion,
                    "failure_reason": "auto-ingestion rejected the Codex result JSON",
                }
            )
            return TaskExecutionResult("failed", payload, tuple(artifact_paths), "Codex result rejected during auto-ingestion.")

        payload_status = "completed" if ingestion["status"] == "accepted" else ingestion["status"]
        payload = self._base_real_payload(
            context,
            packet,
            paths,
            config,
            status=payload_status,
            artifact_paths=artifact_paths,
        )
        payload.update(
            {
                "validation_passed": bool(ingestion.get("validation_passed", False)),
                "safety_ok": bool(ingestion.get("safety_ok", False)),
                "codex_cli_invocation": invocation.to_dict(),
                "result_collection": collected,
                "codex_result_ingestion": ingestion,
                "auto_ingested": True,
                "auto_ingest_status": ingestion["status"],
                "state_updated": bool(ingestion.get("state_updated", False)),
                "state_action": ingestion.get("state_action", ""),
                "result_json_path": str(result_json_path),
            }
        )
        return TaskExecutionResult(
            "auto_ingested",
            payload,
            tuple(artifact_paths),
            f"Codex CLI result auto-ingested with status {ingestion['status']}.",
        )

    def _blocked(
        self,
        context: TaskExecutionContext,
        packet: Any,
        paths: dict[str, str],
        config: Any,
        artifact_paths: list[str],
        message: str,
        errors: list[str],
        *,
        validation_warnings: list[str] | None = None,
    ) -> TaskExecutionResult:
        result_json_path = result_json_path_for_packet(packet, config)
        log_result = _blocked_invocation_result(packet, config, errors, validation_warnings or [])
        write_invocation_log(log_result)
        artifact_paths = _artifact_paths_from_real_codex(paths, result_json_path, log_result)
        payload = self._base_real_payload(
            context,
            packet,
            paths,
            config,
            status="blocked",
            artifact_paths=artifact_paths,
        )
        payload.update(
            {
                "validation_passed": False,
                "safety_ok": True,
                "codex_cli_invocation": log_result.to_dict(),
                "blocked_reason": message,
                "errors": list(errors),
                "warnings": list(validation_warnings or []),
            }
        )
        return TaskExecutionResult("blocked", payload, tuple(artifact_paths), message)

    def _terminal_from_invocation(
        self,
        context: TaskExecutionContext,
        packet: Any,
        paths: dict[str, str],
        config: Any,
        invocation: Any,
        artifact_paths: list[str],
        *,
        status: str,
        message: str,
        extra: Mapping[str, Any] | None = None,
    ) -> TaskExecutionResult:
        payload = self._base_real_payload(
            context,
            packet,
            paths,
            config,
            status=status,
            artifact_paths=artifact_paths,
        )
        payload.update(
            {
                "validation_passed": False,
                "safety_ok": status == "blocked",
                "codex_cli_invocation": invocation.to_dict(),
                "commands_run": [invocation.display_command] if invocation.command else [],
            }
        )
        if status == "blocked":
            payload["blocked_reason"] = message
        else:
            payload["failure_reason"] = message
        if extra:
            payload.update(dict(extra))
        return TaskExecutionResult(status, payload, tuple(artifact_paths), message)

    def _base_real_payload(
        self,
        context: TaskExecutionContext,
        packet: Any,
        paths: dict[str, str],
        config: Any,
        *,
        status: str,
        artifact_paths: list[str],
    ) -> dict[str, Any]:
        payload = _base_payload(context.task_spec, context, status=status)
        payload.update(
            {
                "artifacts": list(artifact_paths),
                "commands_run": [],
                "codex_invoked": False,
                "adapter_mode": packet.adapter_mode,
                "requires_operator_handoff": False,
                "requires_operator_approval": packet.requires_operator_approval,
                "real_codex_invocation_requires_operator_approval": True,
                "operator_approval_flag_present": self.allow_real_codex_invocation,
                "auto_ingest_requested": self.auto_ingest,
                "execution_packet_path": paths["packet"],
                "execution_prompt_path": paths["prompt"],
                "expected_result_template_path": paths["expected_result_template"],
                "result_json_path": str(result_json_path_for_packet(packet, config)),
                "codex_executor_config_path": config.config_path,
                "safety_boundaries_acknowledged": list(packet.safety_boundaries),
                "real_order_submitted": False,
                "wallet_used": False,
                "signing_used": False,
                "trading_endpoint_used": False,
                "authenticated_endpoint_used": False,
                "browser_automation_used": False,
                "openrouter_used": False,
                "polymarket_api_used": False,
                "unsafe_git_staging_used": False,
                "force_push_used": False,
                "daemon_created": False,
                "scheduler_created": False,
                "background_worker_created": False,
            }
        )
        return payload


class FutureCodexCliExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        raise NotImplementedError(
            "FutureCodexCliExecutor is a boundary stub only. This task must not self-invoke Codex."
        )


class FutureCodexAppAutomationExecutor:
    def execute(self, context: TaskExecutionContext) -> TaskExecutionResult:
        raise NotImplementedError(
            "FutureCodexAppAutomationExecutor is a boundary stub only. No Codex App automation is registered here."
        )


def render_codex_handoff_prompt(context: TaskExecutionContext) -> str:
    task = context.task_spec
    result_shape = {
        "task_id": task.task_id,
        "status": "completed|blocked|failed",
        "validation_passed": True,
        "safety_ok": True,
        "artifacts": [],
        "commands_run": [],
        "summary": "",
        "remaining_risks": [],
    }
    state_summary = dict(context.state_summary or {})
    completed = state_summary.get("completed_task_ids") or []
    compact_state = {
        "run_id": context.run_id,
        "plan_id": context.plan_id,
        "run_status": state_summary.get("status", ""),
        "completed_count": len(completed) if isinstance(completed, list) else state_summary.get("completed_count", 0),
        "blocked_task_ids": state_summary.get("blocked_task_ids", []),
        "failed_task_ids": state_summary.get("failed_task_ids", []),
        "retry_counts": state_summary.get("retry_counts", {}),
        "latest_checkpoint": state_summary.get("latest_checkpoint"),
    }
    lines = [
        f"# Codex Handoff: {task.task_id}",
        "",
        "Return only JSON matching the expected result shape. Do not include prose outside the JSON object.",
        "",
        f"- task_id: `{task.task_id}`",
        f"- repo_root: `{context.repo_root}`",
        f"- branch: `{context.plan.branch}`",
        f"- expected_current_head: `{context.plan.expected_head}`",
        f"- execution_lane: `{task.execution_lane}`",
        f"- max_retries: `{task.max_retries}`",
        "",
        "## Compact Run State",
        "",
        "```json",
        json.dumps(compact_state, indent=2, sort_keys=True),
        "```",
        "",
        "## Previously Completed Tasks",
        "",
        *_bullet_lines([str(value) for value in completed] if isinstance(completed, list) else []),
        "",
        "## Next Task Only",
        "",
        f"Title: {task.title}",
        "",
        task.description,
        "",
        "Dependencies:",
        *_bullet_lines(list(task.dependencies)),
        "",
        "## Allowed Paths",
        "",
        *_bullet_lines(task.allowed_paths),
        "",
        "## Forbidden Actions",
        "",
        *_bullet_lines(task.forbidden_actions),
        "",
        "## Expected Artifacts",
        "",
        *_bullet_lines(task.expected_artifacts),
        "",
        "## Acceptance Gates",
        "",
        *_bullet_lines(task.acceptance_gates),
        "",
        "## Required Result JSON Shape",
        "",
        "```json",
        json.dumps(result_shape, indent=2, sort_keys=True),
        "```",
        "",
        "## Safety Reminders",
        "",
        "- Do not use unsafe git staging. Never run `git add .`, `git add -A`, or `git add --all`.",
        "- Do not use wallet files, private keys, signing, orders, trading endpoints, or real-money flows.",
        "- Do not use OpenRouter or Polymarket API unless a separate task explicitly approves it.",
        "- Do not start daemons, schedulers, uncontrolled background workers, or browser automation.",
        "",
    ]
    return "\n".join(lines)


def _base_payload(task: PlanTaskSpec, context: TaskExecutionContext, *, status: str) -> dict[str, Any]:
    return {
        "schema_version": "codex_plan_task_result.v1",
        "task_id": task.task_id,
        "plan_id": context.plan_id,
        "run_id": context.run_id,
        "status": status,
        "completed_at": _utc_iso(),
        "summary": f"{status} by local executor for {task.task_id}.",
    }


def _fake_behavior_for_task(executor: FakeTaskExecutor, task: PlanTaskSpec) -> str:
    metadata_behavior = str(task.metadata.get("fake_behavior") or "").strip().lower()
    if metadata_behavior:
        return metadata_behavior
    if task.task_id in executor.handoff_task_ids:
        return "requiring_operator_handoff"
    if task.task_id in executor.blocked_task_ids:
        return "blocked"
    if task.task_id in executor.failed_task_ids:
        return "failed"
    if task.task_id in executor.needs_retry_task_ids:
        return "needs_retry"
    return "accepted"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    target = _io_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_packet_artifacts(context: TaskExecutionContext, adapter_mode: str) -> tuple[Any, dict[str, str]]:
    run_dir = Path(context.run_dir)
    manifest = _read_json(run_dir / "manifest.json")
    manifest["manifest_path"] = str(run_dir / "manifest.json")
    state = _read_json(run_dir / "state.json")
    packet = build_execution_packet(context.task_spec, state, manifest, adapter_mode)
    output_dir = Path(packet.prompt_path).parent
    packet_path = write_execution_packet(packet, output_dir)
    prompt_path = write_execution_prompt(packet, output_dir)
    template_path = write_expected_result_template(packet, output_dir)
    readme_path = output_dir / "README.md"
    return packet, {
        "packet": str(packet_path),
        "prompt": str(prompt_path),
        "expected_result_template": str(template_path),
        "readme": str(readme_path),
    }


def _artifact_paths_from_real_codex(
    paths: Mapping[str, str],
    result_json_path: str | Path,
    invocation: CodexCliInvocationResult | None = None,
) -> list[str]:
    artifact_paths = [
        str(paths.get("prompt", "")),
        str(paths.get("packet", "")),
        str(paths.get("expected_result_template", "")),
        str(paths.get("readme", "")),
        str(result_json_path),
    ]
    if invocation is not None:
        artifact_paths.extend(
            [
                invocation.stdout_log_path,
                invocation.stderr_log_path,
                invocation.invocation_log_path,
                invocation.invocation_markdown_path,
            ]
        )
    return list(dict.fromkeys(path for path in artifact_paths if path))


def _blocked_invocation_result(
    packet: Any,
    config: Any,
    errors: list[str],
    warnings: list[str],
) -> CodexCliInvocationResult:
    result_json_path = result_json_path_for_packet(packet, config)
    packet_dir = Path(packet.prompt_path).parent
    return CodexCliInvocationResult(
        status="blocked",
        packet_id=packet.packet_id,
        task_id=packet.task_id,
        run_id=packet.run_id,
        plan_id=packet.plan_id,
        command=[],
        display_command="",
        cwd=str(Path(packet.repo_root or ".").resolve(strict=False)),
        prompt_path=packet.prompt_path,
        packet_path=str(packet_dir / "packet.json"),
        result_json_path=str(result_json_path),
        started_at=_utc_iso(),
        ended_at=_utc_iso(),
        timeout_seconds=int(getattr(config, "timeout_seconds", 0) or 0),
        stdout_log_path=str(packet_dir / "codex_cli_stdout.log"),
        stderr_log_path=str(packet_dir / "codex_cli_stderr.log"),
        invocation_log_path=str(packet_dir / "codex_cli_invocation.json"),
        invocation_markdown_path=str(packet_dir / "codex_cli_invocation.md"),
        result_json_exists=Path(result_json_path).exists(),
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _future_codex_cli_command(prompt_path: str, repo_root: str | Path) -> list[str]:
    return [
        "codex",
        "exec",
        "--sandbox",
        "workspace-write",
        "--cd",
        str(repo_root),
        "--json",
        "--prompt-file",
        str(prompt_path),
    ]


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _io_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    resolved = path.resolve(strict=False)
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return resolved
    return Path("\\\\?\\" + text)


def _bullet_lines(values: tuple[str, ...] | list[str]) -> list[str]:
    if not values:
        return ["- None"]
    return [f"- {value}" for value in values]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_for_filename() -> str:
    return datetime.now(timezone.utc).strftime("%H%M%S%f")
