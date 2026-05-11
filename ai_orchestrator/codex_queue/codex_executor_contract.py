from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .plan_contract import PlanTaskSpec, load_plan_contract
from .result_acceptance_policy import reject_forbidden_claims


class CodexExecutionMode(str, Enum):
    MANUAL_HANDOFF = "manual_handoff"
    CODEX_CLI_DRY_RUN = "codex_cli_dry_run"
    CODEX_CLI_OPERATOR_APPROVED = "codex_cli_operator_approved"
    CODEX_APP_AUTOMATION_PROFILE = "codex_app_automation_profile"
    DISABLED = "disabled"


APPROVAL_REQUIRED_MODES = {
    CodexExecutionMode.MANUAL_HANDOFF.value,
    CodexExecutionMode.CODEX_CLI_OPERATOR_APPROVED.value,
    CodexExecutionMode.CODEX_APP_AUTOMATION_PROFILE.value,
}

SAFE_PACKET_MODES = {
    CodexExecutionMode.MANUAL_HANDOFF.value,
    CodexExecutionMode.CODEX_CLI_DRY_RUN.value,
    CodexExecutionMode.CODEX_CLI_OPERATOR_APPROVED.value,
    CodexExecutionMode.CODEX_APP_AUTOMATION_PROFILE.value,
}

DEFAULT_FORBIDDEN_ACTIONS = (
    "Do not use `git add .`, `git add -A`, or `git add --all`.",
    "Do not force push.",
    "Do not use wallet files, private keys, signing, orders, or trading endpoints.",
    "Do not use OpenRouter or Polymarket API unless a separate task explicitly approves it.",
    "Do not use authenticated endpoints.",
    "Do not use browser automation.",
    "Do not create daemons, schedulers, or background workers.",
)

DEFAULT_SAFETY_BOUNDARIES = (
    "operator_approval_required_for_codex_execution",
    "single_task_packet_only",
    "no_uncontrolled_codex_loop",
    "no_daemon_scheduler_or_background_worker",
    "no_wallet_signing_orders_or_trading",
    "no_openrouter_or_polymarket_api_without_separate_approval",
    "no_browser_automation_or_authenticated_endpoints",
    "selective_git_staging_only",
)

DEFAULT_SUBAGENT_PLAN = (
    "Scout",
    "Planner",
    "Builder",
    "Tester",
    "Reviewer",
    "Docs",
    "Integrator",
)

DEFAULT_ROLE_ASSIGNMENTS = {
    "Scout": "Read-only repo discovery and dependency/risk summary.",
    "Planner": "Scope decomposition and blocker detection before implementation.",
    "Builder": "Bounded implementation within allowed paths.",
    "Tester": "Targeted tests and edge-case validation with external services mocked.",
    "Reviewer": "Diff review, safety contract review, and staging-rule review.",
    "Docs": "Operator docs and result envelope updates without unsupported success claims.",
    "Integrator": "Aggregate role outputs and decide acceptance gates before selective staging.",
}

DEFAULT_SUBAGENT_EXPECTED_OUTPUTS = {
    "Scout": "scout_report",
    "Planner": "implementation_plan",
    "Builder": "implementation_notes",
    "Tester": "validation_report",
    "Reviewer": "review_report",
    "Docs": "docs_report",
    "Integrator": "integration_decision",
}

DEFAULT_MEMORY_CONTEXT_PATHS = (
    "AGENTS.md",
    "memory-bank/activeContext.md",
    "memory-bank/pmbotSafety.md",
    "memory-bank/codexAutomation.md",
    ".codex-agent/ultra-context.md",
    ".codex-agent/context-bundle.md",
)

DEFAULT_AGGREGATION_POLICY = (
    "Main Codex aggregates role outputs into one concise result JSON; "
    "blocked gates must be reported as blocked."
)

UNSAFE_GIT_COMMAND_PATTERNS = (
    "git add .",
    "git add -a",
    "git add --all",
    "git push --force",
    "git push -f",
    "--force-with-lease",
)

UNSAFE_CLAIM_PATTERNS = (
    "real trading",
    "real order submitted",
    "wallet used",
    "wallet signing",
    "private key",
    "signing key",
    "orders endpoint",
    "trading endpoint",
    "authenticated endpoint",
    "browser automation",
    "openrouter api",
    "openrouter used",
    "polymarket api",
    "polymarket api used",
    "daemon created",
    "scheduler created",
    "background worker created",
    "uncontrolled autonomous codex loop",
)


@dataclass(frozen=True)
class CodexExecutionPacket:
    packet_id: str
    run_id: str
    plan_id: str
    task_id: str
    created_at: str
    repo_root: str
    branch: str
    expected_head: str
    queue_manifest_path: str
    state_path: str
    task_spec_path: str
    allowed_paths: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    acceptance_gates: tuple[str, ...] = ()
    prompt_path: str = ""
    expected_result_path: str = ""
    adapter_mode: str = CodexExecutionMode.MANUAL_HANDOFF.value
    requires_operator_approval: bool = True
    safety_boundaries: tuple[str, ...] = ()
    subagent_plan: tuple[str, ...] = ()
    role_assignments: dict[str, str] = field(default_factory=dict)
    subagent_expected_outputs: dict[str, str] = field(default_factory=dict)
    main_agent_aggregation_policy: str = ""
    memory_context_paths: tuple[str, ...] = ()
    agents_md_path: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CodexExecutionPacket":
        return cls(
            packet_id=str(payload.get("packet_id") or ""),
            run_id=str(payload.get("run_id") or ""),
            plan_id=str(payload.get("plan_id") or ""),
            task_id=str(payload.get("task_id") or ""),
            created_at=str(payload.get("created_at") or ""),
            repo_root=str(payload.get("repo_root") or ""),
            branch=str(payload.get("branch") or ""),
            expected_head=str(payload.get("expected_head") or ""),
            queue_manifest_path=str(payload.get("queue_manifest_path") or ""),
            state_path=str(payload.get("state_path") or ""),
            task_spec_path=str(payload.get("task_spec_path") or ""),
            allowed_paths=tuple(str(value) for value in payload.get("allowed_paths", [])),
            forbidden_actions=tuple(str(value) for value in payload.get("forbidden_actions", [])),
            acceptance_gates=tuple(str(value) for value in payload.get("acceptance_gates", [])),
            prompt_path=str(payload.get("prompt_path") or ""),
            expected_result_path=str(payload.get("expected_result_path") or ""),
            adapter_mode=str(payload.get("adapter_mode") or ""),
            requires_operator_approval=bool(payload.get("requires_operator_approval", False)),
            safety_boundaries=tuple(str(value) for value in payload.get("safety_boundaries", [])),
            subagent_plan=tuple(str(value) for value in payload.get("subagent_plan", [])),
            role_assignments=_string_mapping(payload.get("role_assignments", {})),
            subagent_expected_outputs=_string_mapping(payload.get("subagent_expected_outputs", {})),
            main_agent_aggregation_policy=str(payload.get("main_agent_aggregation_policy") or ""),
            memory_context_paths=tuple(str(value) for value in payload.get("memory_context_paths", [])),
            agents_md_path=str(payload.get("agents_md_path") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "allowed_paths",
            "forbidden_actions",
            "acceptance_gates",
            "safety_boundaries",
            "subagent_plan",
            "memory_context_paths",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True)
class CodexExecutionResultEnvelope:
    packet_id: str
    run_id: str
    plan_id: str
    task_id: str
    received_at: str
    adapter_mode: str
    status: str
    result_payload: dict[str, Any]
    result_path: str = ""
    validation_passed: bool = False
    safety_ok: bool = False
    acceptance_status: str = ""
    acceptance_reasons: tuple[str, ...] = ()
    artifact_paths: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CodexExecutionResultEnvelope":
        result_payload = payload.get("result_payload", {})
        return cls(
            packet_id=str(payload.get("packet_id") or ""),
            run_id=str(payload.get("run_id") or ""),
            plan_id=str(payload.get("plan_id") or ""),
            task_id=str(payload.get("task_id") or ""),
            received_at=str(payload.get("received_at") or _utc_iso()),
            adapter_mode=str(payload.get("adapter_mode") or ""),
            status=str(payload.get("status") or ""),
            result_payload=dict(result_payload) if isinstance(result_payload, Mapping) else {},
            result_path=str(payload.get("result_path") or ""),
            validation_passed=bool(payload.get("validation_passed", False)),
            safety_ok=bool(payload.get("safety_ok", False)),
            acceptance_status=str(payload.get("acceptance_status") or ""),
            acceptance_reasons=tuple(str(value) for value in payload.get("acceptance_reasons", [])),
            artifact_paths=tuple(str(value) for value in payload.get("artifact_paths", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["acceptance_reasons"] = list(self.acceptance_reasons)
        payload["artifact_paths"] = list(self.artifact_paths)
        return payload


@dataclass(frozen=True)
class CodexAdapterValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    safety_ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "safety_ok": self.safety_ok,
        }


def build_execution_packet(
    task_spec: PlanTaskSpec | Mapping[str, Any],
    state: Any,
    manifest: Mapping[str, Any],
    adapter_mode: str | CodexExecutionMode,
) -> CodexExecutionPacket:
    task = _task_mapping(task_spec)
    state_payload = _mapping_from_state(state)
    mode = _mode_value(adapter_mode)
    plan = _load_plan_from_manifest(manifest)
    run_id = str(state_payload.get("run_id") or manifest.get("run_id") or "")
    plan_id = str(state_payload.get("plan_id") or manifest.get("plan_id") or "")
    task_id = str(task.get("task_id") or "")
    state_path = str(manifest.get("state_path") or "")
    run_root = Path(state_path).parent if state_path else Path(str(manifest.get("queue_paths", {}).get("run_root") or "."))
    output_dir = run_root / "codex_packets" / task_id
    safety_boundaries = _merge_unique(
        [
            *_plan_safety_boundaries(plan),
            *DEFAULT_SAFETY_BOUNDARIES,
            f"adapter_mode:{mode}",
        ]
    )
    forbidden_actions = _merge_unique([*task.get("forbidden_actions", []), *DEFAULT_FORBIDDEN_ACTIONS])
    return CodexExecutionPacket(
        packet_id=f"cpkt_{run_id}_{task_id}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        run_id=run_id,
        plan_id=plan_id,
        task_id=task_id,
        created_at=_utc_iso(),
        repo_root=str(plan.repo_root or ".") if plan else str(manifest.get("repo_root") or "."),
        branch=str(plan.branch or "master") if plan else str(manifest.get("branch") or "master"),
        expected_head=str(
            state_payload.get("git_head_start")
            or state_payload.get("git_head_last_verified")
            or (plan.expected_head if plan and plan.expected_head else "")
            or manifest.get("expected_head")
            or ""
        ),
        queue_manifest_path=str(state_payload.get("queue_manifest_path") or manifest.get("manifest_path") or ""),
        state_path=state_path,
        task_spec_path=str(dict(manifest.get("task_paths", {})).get(task_id) or ""),
        allowed_paths=tuple(str(value) for value in task.get("allowed_paths", [])),
        forbidden_actions=tuple(forbidden_actions),
        acceptance_gates=tuple(str(value) for value in task.get("acceptance_gates", [])),
        prompt_path=str(output_dir / "prompt.md"),
        expected_result_path=str(output_dir / "expected_result_template.json"),
        adapter_mode=mode,
        requires_operator_approval=mode in APPROVAL_REQUIRED_MODES,
        safety_boundaries=tuple(safety_boundaries),
        subagent_plan=DEFAULT_SUBAGENT_PLAN,
        role_assignments=dict(DEFAULT_ROLE_ASSIGNMENTS),
        subagent_expected_outputs=dict(DEFAULT_SUBAGENT_EXPECTED_OUTPUTS),
        main_agent_aggregation_policy=DEFAULT_AGGREGATION_POLICY,
        memory_context_paths=DEFAULT_MEMORY_CONTEXT_PATHS,
        agents_md_path="AGENTS.md",
    )


def validate_execution_packet(packet: CodexExecutionPacket | Mapping[str, Any]) -> CodexAdapterValidationResult:
    packet_obj = _packet(packet)
    errors: list[str] = []
    warnings: list[str] = []
    if not packet_obj.packet_id.strip():
        errors.append("missing packet_id")
    if not packet_obj.run_id.strip():
        errors.append("missing run_id")
    if not packet_obj.task_id.strip():
        errors.append("missing task_id")
    if not packet_obj.plan_id.strip():
        errors.append("missing plan_id")
    if packet_obj.adapter_mode not in SAFE_PACKET_MODES:
        errors.append(f"unsafe adapter mode: {packet_obj.adapter_mode or '<missing>'}")
    if packet_obj.adapter_mode == CodexExecutionMode.DISABLED.value:
        errors.append("disabled adapter mode cannot execute a packet")
    if packet_obj.adapter_mode in APPROVAL_REQUIRED_MODES:
        if not packet_obj.requires_operator_approval:
            errors.append("adapter mode requires operator approval but packet flag is false")
        if not _has_approval_marker(packet_obj):
            errors.append("adapter mode requires operator approval marker")
    if not packet_obj.allowed_paths:
        warnings.append("packet has no allowed_paths")
    if not packet_obj.forbidden_actions:
        errors.append("packet has no forbidden_actions")

    errors.extend(_scan_unsafe_git_commands(packet_obj.to_dict()))
    errors.extend(_scan_forbidden_positive_claims(_packet_scan_payload(packet_obj)))
    errors.extend(_required_forbidden_action_coverage(packet_obj))
    return CodexAdapterValidationResult(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
        safety_ok=not errors,
    )


def expected_result_schema_for_packet(packet: CodexExecutionPacket | Mapping[str, Any]) -> dict[str, Any]:
    packet_obj = _packet(packet)
    result_payload = {
        "schema_version": "codex_plan_task_result.v1",
        "task_id": packet_obj.task_id,
        "plan_id": packet_obj.plan_id,
        "run_id": packet_obj.run_id,
        "status": "completed|blocked|failed|needs_retry",
        "validation_passed": True,
        "safety_ok": True,
        "artifacts": [],
        "commands_run": [],
        "summary": "",
        "remaining_risks": [],
        "safety_boundaries_acknowledged": list(packet_obj.safety_boundaries),
        "subagent_outputs": {role: "" for role in packet_obj.subagent_plan},
        "memory_context_used": list(packet_obj.memory_context_paths),
        "aggregation_notes": "",
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
    return {
        "packet_id": packet_obj.packet_id,
        "run_id": packet_obj.run_id,
        "plan_id": packet_obj.plan_id,
        "task_id": packet_obj.task_id,
        "received_at": "<ISO-8601 UTC timestamp>",
        "adapter_mode": packet_obj.adapter_mode,
        "status": "completed|blocked|failed|needs_retry",
        "result_payload": result_payload,
        "result_path": "",
        "validation_passed": True,
        "safety_ok": True,
        "acceptance_status": "pending_operator_ingestion",
        "acceptance_reasons": [],
        "artifact_paths": [],
    }


def load_execution_result_envelope(path: str | Path) -> CodexExecutionResultEnvelope:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Codex result envelope JSON must be an object")
    return CodexExecutionResultEnvelope.from_dict(payload)


def validate_execution_result_envelope(
    envelope: CodexExecutionResultEnvelope | Mapping[str, Any],
    packet: CodexExecutionPacket | Mapping[str, Any],
) -> CodexAdapterValidationResult:
    packet_obj = _packet(packet)
    envelope_obj = _envelope(envelope)
    errors: list[str] = []
    warnings: list[str] = []
    for field_name in ("packet_id", "run_id", "plan_id", "task_id", "adapter_mode", "status"):
        if not str(getattr(envelope_obj, field_name) or "").strip():
            errors.append(f"missing result envelope field: {field_name}")
    if envelope_obj.packet_id and envelope_obj.packet_id != packet_obj.packet_id:
        errors.append(f"packet_id mismatch: expected {packet_obj.packet_id}, got {envelope_obj.packet_id}")
    if envelope_obj.run_id and envelope_obj.run_id != packet_obj.run_id:
        errors.append(f"run_id mismatch: expected {packet_obj.run_id}, got {envelope_obj.run_id}")
    if envelope_obj.plan_id and envelope_obj.plan_id != packet_obj.plan_id:
        errors.append(f"plan_id mismatch: expected {packet_obj.plan_id}, got {envelope_obj.plan_id}")
    if envelope_obj.task_id != packet_obj.task_id:
        errors.append(f"task_id mismatch: expected {packet_obj.task_id}, got {envelope_obj.task_id}")
    if envelope_obj.adapter_mode and envelope_obj.adapter_mode != packet_obj.adapter_mode:
        errors.append(f"adapter_mode mismatch: expected {packet_obj.adapter_mode}, got {envelope_obj.adapter_mode}")
    if not isinstance(envelope_obj.result_payload, dict) or not envelope_obj.result_payload:
        errors.append("missing result_payload")
    elif str(envelope_obj.result_payload.get("task_id") or "") != packet_obj.task_id:
        errors.append(
            f"result_payload task_id mismatch: expected {packet_obj.task_id}, got {envelope_obj.result_payload.get('task_id')}"
        )
    if envelope_obj.validation_passed is not True:
        warnings.append("result envelope validation_passed is not true")
    if envelope_obj.safety_ok is not True:
        errors.append("result envelope safety_ok must be true")

    result_scan_payload = _strip_acknowledged_safety_text(envelope_obj.to_dict())
    errors.extend(reject_forbidden_claims(result_scan_payload))
    errors.extend(_scan_unsafe_git_commands(result_scan_payload))
    errors.extend(_scan_forbidden_positive_claims(result_scan_payload))
    return CodexAdapterValidationResult(
        valid=not errors,
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
        safety_ok=not errors,
    )


def _packet(packet: CodexExecutionPacket | Mapping[str, Any]) -> CodexExecutionPacket:
    if isinstance(packet, CodexExecutionPacket):
        return packet
    return CodexExecutionPacket.from_dict(packet)


def _envelope(envelope: CodexExecutionResultEnvelope | Mapping[str, Any]) -> CodexExecutionResultEnvelope:
    if isinstance(envelope, CodexExecutionResultEnvelope):
        return envelope
    return CodexExecutionResultEnvelope.from_dict(envelope)


def _mode_value(mode: str | CodexExecutionMode) -> str:
    if isinstance(mode, CodexExecutionMode):
        return mode.value
    return str(mode or "").strip()


def _task_mapping(task_spec: PlanTaskSpec | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(task_spec, Mapping):
        return dict(task_spec)
    return task_spec.to_dict()


def _mapping_from_state(state: Any) -> dict[str, Any]:
    if isinstance(state, Mapping):
        return dict(state)
    if hasattr(state, "to_dict"):
        payload = state.to_dict()
        return dict(payload) if isinstance(payload, Mapping) else {}
    return {}


def _string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def _load_plan_from_manifest(manifest: Mapping[str, Any]) -> Any:
    source = Path(str(manifest.get("source_plan_file") or ""))
    if not source.exists():
        return None
    try:
        return load_plan_contract(source)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _plan_safety_boundaries(plan: Any) -> list[str]:
    if not plan:
        return []
    return [
        f"{boundary.boundary_id}: {boundary.description}" if boundary.description else boundary.boundary_id
        for boundary in plan.safety_boundaries
        if boundary.required
    ]


def _merge_unique(values: list[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _has_approval_marker(packet: CodexExecutionPacket) -> bool:
    return any("operator_approval_required" in value.lower() for value in packet.safety_boundaries)


def _packet_scan_payload(packet: CodexExecutionPacket) -> dict[str, Any]:
    payload = packet.to_dict()
    payload.pop("forbidden_actions", None)
    payload.pop("safety_boundaries", None)
    return payload


def _scan_unsafe_git_commands(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for text in _flatten_strings(payload):
        lowered = text.lower()
        for pattern in UNSAFE_GIT_COMMAND_PATTERNS:
            if pattern in lowered and not _looks_like_prohibition(lowered, pattern):
                errors.append(f"unsafe git command claim: {pattern}")
    return errors


def _scan_forbidden_positive_claims(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for text in _flatten_strings(payload):
        lowered = text.lower()
        for pattern in UNSAFE_CLAIM_PATTERNS:
            if pattern in lowered and not _looks_like_prohibition(lowered, pattern):
                errors.append(f"forbidden action claim: {pattern}")
    return errors


def _required_forbidden_action_coverage(packet: CodexExecutionPacket) -> list[str]:
    joined = " ".join(packet.forbidden_actions).lower()
    required = {
        "unsafe git staging": ("git add .", "git add -a", "git add --all", "unsafe git"),
        "force push": ("force push", "git push --force", "git push -f"),
        "wallet/signing/orders/trading": ("wallet", "signing", "orders", "trading"),
        "OpenRouter": ("openrouter",),
        "Polymarket API": ("polymarket",),
        "browser automation": ("browser automation",),
        "authenticated endpoints": ("authenticated",),
        "daemon/scheduler/background worker": ("daemon", "scheduler", "background worker"),
    }
    errors: list[str] = []
    for label, terms in required.items():
        if not any(term in joined for term in terms):
            errors.append(f"packet forbidden_actions missing coverage for {label}")
    return errors


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


def _strip_acknowledged_safety_text(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_acknowledged_safety_text(item)
            for key, item in value.items()
            if str(key) != "safety_boundaries_acknowledged"
        }
    if isinstance(value, list):
        return [_strip_acknowledged_safety_text(item) for item in value]
    return value


def _looks_like_prohibition(text: str, pattern: str) -> bool:
    index = text.find(pattern)
    if index < 0:
        return False
    prefix = text[max(0, index - 40):index]
    sentence = text[max(0, index - 96): index + len(pattern) + 96]
    return (
        "do not " in prefix
        or "never " in prefix
        or "no " in prefix
        or "not " in prefix
        or "forbidden" in sentence
        or "unless explicitly approved" in sentence
        or "without separate approval" in sentence
        or "false" in sentence
    )


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
