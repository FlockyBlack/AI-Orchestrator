from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from .codex_executor_contract import (
    CodexExecutionMode,
    CodexExecutionPacket,
    build_execution_packet,
    expected_result_schema_for_packet,
    validate_execution_packet,
)
from .plan_contract import PlanTaskSpec, load_plan_contract
from .plan_decomposer import get_next_runnable_tasks
from .plan_run_state import PlanRunState, load_state
from .plan_to_queue import inspect_queue


def create_execution_packet_for_next_task(
    run_id: str,
    queue_root: str | Path,
    adapter_mode: str = CodexExecutionMode.MANUAL_HANDOFF.value,
    task_id: str | None = None,
) -> CodexExecutionPacket:
    inspection = inspect_queue(queue_root, run_id)
    if inspection["status"] not in {"found", "invalid"}:
        raise FileNotFoundError(f"run_id not found: {run_id}")
    manifest = dict(inspection.get("manifest", {}))
    manifest["manifest_path"] = inspection.get("manifest_path", "")
    plan_file = str(manifest.get("source_plan_file") or "")
    if not plan_file:
        raise ValueError("queue manifest missing source_plan_file")
    plan = load_plan_contract(plan_file)
    state_path = Path(str(manifest.get("state_path") or inspection.get("state_path") or ""))
    state = load_state(state_path)
    task = _select_task(plan.tasks, state, task_id)
    packet = build_execution_packet(task, state, manifest, adapter_mode)
    validation = validate_execution_packet(packet)
    if not validation.valid:
        raise ValueError("invalid execution packet: " + "; ".join(validation.errors))
    return packet


def write_execution_packet(packet: CodexExecutionPacket | Mapping[str, Any], output_dir: str | Path) -> Path:
    packet_obj = _packet(packet)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    packet_path = target_dir / "packet.json"
    _write_json(packet_path, packet_obj.to_dict())
    _write_text(target_dir / "README.md", _render_readme(packet_obj))
    return packet_path


def write_execution_prompt(packet: CodexExecutionPacket | Mapping[str, Any], output_dir: str | Path) -> Path:
    packet_obj = _packet(packet)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = target_dir / "prompt.md"
    _write_text(prompt_path, render_execution_prompt(packet_obj))
    return prompt_path


def write_expected_result_template(packet: CodexExecutionPacket | Mapping[str, Any], output_dir: str | Path) -> Path:
    packet_obj = _packet(packet)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    template_path = target_dir / "expected_result_template.json"
    _write_json(template_path, expected_result_schema_for_packet(packet_obj))
    return template_path


def inspect_execution_packets(run_id: str, queue_root: str | Path) -> dict[str, Any]:
    inspection = inspect_queue(queue_root, run_id)
    if inspection["status"] not in {"found", "invalid"}:
        return {"status": "missing", "run_id": run_id, "packet_count": 0, "packets": [], "errors": inspection.get("errors", [])}
    run_dir = Path(str(inspection["run_dir"]))
    packets: list[dict[str, Any]] = []
    for packet_path in sorted((run_dir / "codex_packets").glob("*/packet.json")):
        payload = _read_json(packet_path)
        task_dir = packet_path.parent
        packets.append(
            {
                "packet_id": str(payload.get("packet_id") or ""),
                "task_id": str(payload.get("task_id") or task_dir.name),
                "adapter_mode": str(payload.get("adapter_mode") or ""),
                "requires_operator_approval": bool(payload.get("requires_operator_approval", False)),
                "packet_path": str(packet_path),
                "prompt_path": str(task_dir / "prompt.md"),
                "expected_result_template_path": str(task_dir / "expected_result_template.json"),
                "ingestion_report_json_path": str(task_dir / "ingestion_report.json"),
                "ingestion_report_exists": (task_dir / "ingestion_report.json").exists(),
                "created_at": str(payload.get("created_at") or ""),
            }
        )
    return {
        "status": "found",
        "run_id": run_id,
        "plan_id": str(inspection.get("plan_id") or ""),
        "packet_count": len(packets),
        "packets": packets,
        "latest_packet": packets[-1] if packets else None,
        "codex_packets_dir": str(run_dir / "codex_packets"),
        "errors": [],
    }


def render_execution_prompt(packet: CodexExecutionPacket) -> str:
    template = expected_result_schema_for_packet(packet)
    lines = [
        f"# Codex Execution Packet: {packet.task_id}",
        "",
        "Return only concise JSON matching the exact result template below. Do not include prose outside the JSON object.",
        "",
        "## Packet",
        "",
        f"- packet_id: `{packet.packet_id}`",
        f"- task_id: `{packet.task_id}`",
        f"- run_id: `{packet.run_id}`",
        f"- plan_id: `{packet.plan_id}`",
        f"- adapter_mode: `{packet.adapter_mode}`",
        f"- requires_operator_approval: `{packet.requires_operator_approval}`",
        "",
        "## Repository",
        "",
        f"- repo_root: `{packet.repo_root}`",
        f"- branch: `{packet.branch}`",
        f"- expected HEAD: `{packet.expected_head}`",
        "",
        "## Queue State",
        "",
        f"- state_path: `{packet.state_path}`",
        f"- queue_manifest_path: `{packet.queue_manifest_path}`",
        f"- task_spec_path: `{packet.task_spec_path}`",
        "",
        "## Allowed Paths",
        "",
        *_bullet_lines(packet.allowed_paths),
        "",
        "## Forbidden Actions",
        "",
        *_bullet_lines(packet.forbidden_actions),
        "",
        "## Acceptance Gates",
        "",
        *_bullet_lines(packet.acceptance_gates),
        "",
        "## Safety Instructions",
        "",
        "- Do not use unsafe git staging. Never run `git add .`, `git add -A`, or `git add --all`.",
        "- Do not use force push.",
        "- Do not use wallet files, private keys, signing, orders, trading endpoints, or real-money flows.",
        "- Do not use OpenRouter or Polymarket API unless a separate task explicitly approves it.",
        "- Do not use authenticated endpoints.",
        "- Do not use browser automation.",
        "- Do not create a daemon, scheduler, background worker, or uncontrolled autonomous loop.",
        "- Work on this task only and report blockers instead of inventing success.",
        "",
        "## Expected Artifacts",
        "",
        f"- packet.json: `{_packet_dir(packet) / 'packet.json'}`",
        f"- prompt.md: `{packet.prompt_path}`",
        f"- expected_result_template.json: `{packet.expected_result_path}`",
        f"- ingestion_report.json: `{_packet_dir(packet) / 'ingestion_report.json'}`",
        "",
        "## Exact Result JSON Template",
        "",
        "```json",
        json.dumps(template, indent=2, sort_keys=True),
        "```",
        "",
    ]
    return "\n".join(lines)


def _select_task(tasks: tuple[PlanTaskSpec, ...], state: PlanRunState, task_id: str | None) -> PlanTaskSpec:
    if task_id:
        for task in tasks:
            if task.task_id == task_id:
                return task
        raise ValueError(f"task_id not found in plan: {task_id}")
    next_tasks = get_next_runnable_tasks(
        tasks,
        completed=state.completed_task_ids,
        blocked=state.blocked_task_ids,
        failed=state.failed_task_ids,
    )
    if not next_tasks:
        raise ValueError("no runnable task available for Codex execution packet")
    return next_tasks[0]


def _packet(packet: CodexExecutionPacket | Mapping[str, Any]) -> CodexExecutionPacket:
    if isinstance(packet, CodexExecutionPacket):
        return packet
    return CodexExecutionPacket.from_dict(packet)


def _packet_dir(packet: CodexExecutionPacket) -> Path:
    return Path(packet.prompt_path).parent if packet.prompt_path else Path(packet.state_path).parent / "codex_packets" / packet.task_id


def _render_readme(packet: CodexExecutionPacket) -> str:
    return "\n".join(
        [
            f"# Codex Packet: {packet.task_id}",
            "",
            f"- packet_id: `{packet.packet_id}`",
            f"- run_id: `{packet.run_id}`",
            f"- adapter_mode: `{packet.adapter_mode}`",
            f"- requires_operator_approval: `{packet.requires_operator_approval}`",
            f"- prompt: `{packet.prompt_path}`",
            f"- expected_result_template: `{packet.expected_result_path}`",
            "",
            "This packet is a manual/safe adapter boundary artifact. It does not invoke Codex, start a worker, register a scheduler, call network services, or access credentials.",
            "",
        ]
    )


def _bullet_lines(values: tuple[str, ...] | list[str]) -> list[str]:
    if not values:
        return ["- None"]
    return [f"- {value}" for value in values]


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _write_text(path, json.dumps(dict(payload), indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, content: str) -> None:
    target = _io_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _io_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    resolved = path.resolve(strict=False)
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return resolved
    return Path("\\\\?\\" + text)


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
