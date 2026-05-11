from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


SYMPHONY_TASK_SCHEMA_VERSION = "symphony_task.v1"


@dataclass(frozen=True)
class SymphonyTaskSource:
    kind: str = "ai_orchestrator_plan"
    source_plan_id: str = ""
    source_run_id: str = ""
    source_plan_file: str = ""
    task_spec_path: str = ""
    state_path: str = ""
    manifest_path: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SymphonyTaskSource":
        return cls(
            kind=str(payload.get("kind") or "ai_orchestrator_plan"),
            source_plan_id=str(payload.get("source_plan_id") or payload.get("plan_id") or ""),
            source_run_id=str(payload.get("source_run_id") or payload.get("run_id") or ""),
            source_plan_file=str(payload.get("source_plan_file") or ""),
            task_spec_path=str(payload.get("task_spec_path") or ""),
            state_path=str(payload.get("state_path") or ""),
            manifest_path=str(payload.get("manifest_path") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SymphonyTaskStatus:
    status: str = "pending"
    runnable: bool = False
    dependencies_satisfied: bool = False
    attempt: int = 0
    retry_count: int = 0
    blocked_reasons: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SymphonyTaskStatus":
        return cls(
            status=str(payload.get("status") or "pending"),
            runnable=bool(payload.get("runnable", False)),
            dependencies_satisfied=bool(payload.get("dependencies_satisfied", False)),
            attempt=int(payload.get("attempt", 0) or 0),
            retry_count=int(payload.get("retry_count", 0) or 0),
            blocked_reasons=tuple(str(value) for value in payload.get("blocked_reasons", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blocked_reasons"] = list(self.blocked_reasons)
        return payload


@dataclass(frozen=True)
class SymphonyAcceptancePolicy:
    gates: tuple[str, ...] = ()
    require_validation: bool = True
    require_safety_ok: bool = True
    require_operator_review: bool = True
    expected_artifacts: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SymphonyAcceptancePolicy":
        return cls(
            gates=tuple(str(value) for value in payload.get("gates", [])),
            require_validation=bool(payload.get("require_validation", True)),
            require_safety_ok=bool(payload.get("require_safety_ok", True)),
            require_operator_review=bool(payload.get("require_operator_review", True)),
            expected_artifacts=tuple(str(value) for value in payload.get("expected_artifacts", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["gates"] = list(self.gates)
        payload["expected_artifacts"] = list(self.expected_artifacts)
        return payload


@dataclass(frozen=True)
class SymphonyProofRequirement:
    proof_id: str
    description: str
    required: bool = True
    evidence_paths: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SymphonyProofRequirement":
        return cls(
            proof_id=str(payload.get("proof_id") or payload.get("id") or ""),
            description=str(payload.get("description") or ""),
            required=bool(payload.get("required", True)),
            evidence_paths=tuple(str(value) for value in payload.get("evidence_paths", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_paths"] = list(self.evidence_paths)
        return payload


@dataclass(frozen=True)
class SymphonyTask:
    task_id: str
    title: str
    description: str
    source_plan_id: str
    source_run_id: str
    dependencies: tuple[str, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    acceptance_gates: tuple[str, ...] = ()
    expected_artifacts: tuple[str, ...] = ()
    max_retries: int = 0
    safety_boundaries: tuple[str, ...] = ()
    proof_requirements: tuple[SymphonyProofRequirement, ...] = ()
    source: SymphonyTaskSource = field(default_factory=SymphonyTaskSource)
    status: SymphonyTaskStatus = field(default_factory=SymphonyTaskStatus)
    acceptance_policy: SymphonyAcceptancePolicy = field(default_factory=SymphonyAcceptancePolicy)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = SYMPHONY_TASK_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SymphonyTask":
        source_payload = payload.get("source", {})
        status_payload = payload.get("status", {})
        acceptance_payload = payload.get("acceptance_policy", {})
        return cls(
            task_id=str(payload.get("task_id") or ""),
            title=str(payload.get("title") or ""),
            description=str(payload.get("description") or ""),
            source_plan_id=str(payload.get("source_plan_id") or payload.get("plan_id") or ""),
            source_run_id=str(payload.get("source_run_id") or payload.get("run_id") or ""),
            dependencies=tuple(str(value) for value in payload.get("dependencies", [])),
            allowed_paths=tuple(str(value) for value in payload.get("allowed_paths", [])),
            forbidden_actions=tuple(str(value) for value in payload.get("forbidden_actions", [])),
            acceptance_gates=tuple(str(value) for value in payload.get("acceptance_gates", [])),
            expected_artifacts=tuple(str(value) for value in payload.get("expected_artifacts", [])),
            max_retries=int(payload.get("max_retries", 0) or 0),
            safety_boundaries=tuple(str(value) for value in payload.get("safety_boundaries", [])),
            proof_requirements=tuple(
                SymphonyProofRequirement.from_dict(item)
                for item in payload.get("proof_requirements", [])
                if isinstance(item, Mapping)
            ),
            source=SymphonyTaskSource.from_dict(source_payload) if isinstance(source_payload, Mapping) else SymphonyTaskSource(),
            status=SymphonyTaskStatus.from_dict(status_payload) if isinstance(status_payload, Mapping) else SymphonyTaskStatus(),
            acceptance_policy=(
                SymphonyAcceptancePolicy.from_dict(acceptance_payload)
                if isinstance(acceptance_payload, Mapping)
                else SymphonyAcceptancePolicy()
            ),
            metadata=dict(payload.get("metadata", {})) if isinstance(payload.get("metadata", {}), Mapping) else {},
            schema_version=str(payload.get("schema_version") or SYMPHONY_TASK_SCHEMA_VERSION),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "dependencies",
            "allowed_paths",
            "forbidden_actions",
            "acceptance_gates",
            "expected_artifacts",
            "safety_boundaries",
        ):
            payload[key] = list(payload[key])
        payload["proof_requirements"] = [item.to_dict() for item in self.proof_requirements]
        payload["source"] = self.source.to_dict()
        payload["status"] = self.status.to_dict()
        payload["acceptance_policy"] = self.acceptance_policy.to_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


def proof_requirements_from_task(
    acceptance_gates: tuple[str, ...],
    expected_artifacts: tuple[str, ...],
) -> tuple[SymphonyProofRequirement, ...]:
    requirements: list[SymphonyProofRequirement] = []
    for index, gate in enumerate(acceptance_gates, start=1):
        requirements.append(
            SymphonyProofRequirement(
                proof_id=f"acceptance_gate_{index}",
                description=gate,
                required=True,
            )
        )
    for index, artifact in enumerate(expected_artifacts, start=1):
        requirements.append(
            SymphonyProofRequirement(
                proof_id=f"expected_artifact_{index}",
                description=f"Expected artifact must be produced or explicitly blocked: {artifact}",
                required=True,
                evidence_paths=(artifact,),
            )
        )
    return tuple(requirements)
