from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, trading_core_safety_summary
from pm_bot.trading_core.tiny_live_canary_manual_runbook import (
    validate_tiny_live_canary_manual_runbook,
)

TINY_LIVE_CANARY_PREFLIGHT_CONTRACT = "pmbot_tiny_live_canary_preflight_contract.v1"
TINY_LIVE_CANARY_LIMIT_POLICY_CONTRACT = "pmbot_tiny_live_canary_limit_policy.v1"
TINY_LIVE_CANARY_EVIDENCE_REQUIREMENT_CONTRACT = "pmbot_tiny_live_canary_evidence_requirement.v1"
TINY_LIVE_CANARY_STOP_CONDITION_CONTRACT = "pmbot_tiny_live_canary_stop_condition.v1"
TINY_LIVE_CANARY_MANUAL_APPROVAL_REQUIREMENT_CONTRACT = (
    "pmbot_tiny_live_canary_manual_approval_requirement.v1"
)
TINY_LIVE_CANARY_KILL_SWITCH_REQUIREMENT_CONTRACT = "pmbot_tiny_live_canary_kill_switch_requirement.v1"
TINY_LIVE_CANARY_KILL_SWITCH_VALIDATION_CONTRACT = "pmbot_tiny_live_canary_kill_switch_validation.v1"
TINY_LIVE_CANARY_PREFLIGHT_BLOCKER_CONTRACT = "pmbot_tiny_live_canary_preflight_blocker.v1"
TINY_LIVE_CANARY_PREFLIGHT_RESULT_CONTRACT = "pmbot_tiny_live_canary_preflight_result.v1"

PREFLIGHT_STATUS_READY = "ready_for_future_review_only"
PREFLIGHT_STATUS_BLOCKED = "blocked_missing_static_preflight_artifacts"
LIMIT_POLICY_STATUS_REVIEW_ONLY = "review_only_non_executable"
KILL_SWITCH_STATUS_REQUIREMENTS_DEFINED = "requirements_defined_not_live_verified"

REQUIRED_EVIDENCE_KEYS = (
    "operator_review_packet",
    "disabled_connector_audit_replay",
    "secret_boundary_validation",
    "live_connector_blocker_matrix",
    "manual_runbook_acknowledgement",
    "kill_switch_requirement_packet",
    "evidence_capture_packet",
)


@dataclass(frozen=True)
class TinyLiveCanaryLimitPolicy:
    max_market_count: int = 1
    max_order_count: int = 1
    max_position_size_usd: float = 1.0
    max_total_notional_usd: float = 1.0
    allowed_market_status: str = "review_only"
    limit_policy_status: str = LIMIT_POLICY_STATUS_REVIEW_ONLY

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_LIMIT_POLICY_CONTRACT
        value["future_canary_shape"] = "one_manual_market_one_manual_order_sized_action"
        value["limits_are_placeholders_not_execution_authority"] = True
        value.update(_preflight_safety_flags())
        return value


@dataclass(frozen=True)
class TinyLiveCanaryEvidenceRequirement:
    requirement_id: str
    artifact_key: str
    title: str
    description: str
    required: bool = True
    operator_must_capture: bool = True
    status: str = "required_before_future_review"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_EVIDENCE_REQUIREMENT_CONTRACT
        value.update(_preflight_safety_flags())
        return value


@dataclass(frozen=True)
class TinyLiveCanaryStopCondition:
    condition_id: str
    title: str
    operator_action: str
    blocks_live_execution: bool = True
    manual_stop_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_STOP_CONDITION_CONTRACT
        value.update(_preflight_safety_flags())
        return value


@dataclass(frozen=True)
class TinyLiveCanaryManualApprovalRequirement:
    requirement_id: str
    title: str
    description: str
    required: bool = True
    collected_in_this_build: bool = False
    operator_review_is_not_live_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_MANUAL_APPROVAL_REQUIREMENT_CONTRACT
        value.update(_preflight_safety_flags())
        return value


@dataclass(frozen=True)
class TinyLiveCanaryKillSwitchRequirement:
    requirement_id: str = "tiny_live_canary_kill_switch_requirement_033"
    operator_visible_kill_switch_required: bool = True
    dry_run_kill_switch_simulation_required: bool = True
    real_connector_must_remain_disabled_in_current_build: bool = True
    live_connector_must_not_be_enabled_until_separate_future_gated_task: bool = True
    emergency_stop_instructions_must_be_documented: bool = True
    no_scheduler_daemon_may_bypass_operator: bool = True
    requirements_defined: bool = True
    verified_for_live: bool = False
    blocks_live_execution: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_KILL_SWITCH_REQUIREMENT_CONTRACT
        value["status"] = KILL_SWITCH_STATUS_REQUIREMENTS_DEFINED
        value.update(_preflight_safety_flags())
        return value


@dataclass(frozen=True)
class TinyLiveCanaryKillSwitchValidation:
    validation_id: str
    requirement_id: str
    requirements_defined: bool
    verified_for_live: bool
    blocks_live_execution: bool
    status: str
    errors: tuple[str, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_KILL_SWITCH_VALIDATION_CONTRACT
        value["errors"] = list(self.errors)
        value["valid"] = not self.errors
        value.update(_preflight_safety_flags())
        return value


@dataclass(frozen=True)
class TinyLiveCanaryPreflightBlocker:
    blocker_id: str
    blocker_category: str
    message: str
    severity: str = "critical"
    resolution_status: str = "unresolved"
    blocks_canary_execution_now: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_PREFLIGHT_BLOCKER_CONTRACT
        value.update(_preflight_safety_flags())
        return value


@dataclass(frozen=True)
class TinyLiveCanaryPreflightContract:
    contract_id: str
    limit_policy: TinyLiveCanaryLimitPolicy
    evidence_requirements: tuple[TinyLiveCanaryEvidenceRequirement, ...]
    stop_conditions: tuple[TinyLiveCanaryStopCondition, ...]
    manual_approval_requirements: tuple[TinyLiveCanaryManualApprovalRequirement, ...]
    kill_switch_requirement: TinyLiveCanaryKillSwitchRequirement
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_PREFLIGHT_CONTRACT
        value["limit_policy"] = self.limit_policy.to_dict()
        value["evidence_requirements"] = [row.to_dict() for row in self.evidence_requirements]
        value["stop_conditions"] = [row.to_dict() for row in self.stop_conditions]
        value["manual_approval_requirements"] = [
            row.to_dict() for row in self.manual_approval_requirements
        ]
        value["kill_switch_requirement"] = self.kill_switch_requirement.to_dict()
        value["preflight_contract_ready"] = True
        value["future_tiny_canary_defined"] = True
        value["required_manual_operator_approval"] = True
        value["required_kill_switch_verified"] = True
        value["required_disabled_connector_audit_replay"] = True
        value["required_operator_packet"] = True
        value["required_secret_boundary_validation"] = True
        value["required_blocker_review"] = True
        value["required_manual_runbook_acknowledgement"] = True
        value["required_no_autonomous_scheduler"] = True
        value["required_no_real_execution_in_this_build"] = True
        value["operator_review_is_not_live_approval"] = True
        value["canary_preflight_is_not_execution_approval"] = True
        value.update(_preflight_safety_flags())
        value["safety_summary"] = trading_core_safety_summary()
        return value


@dataclass(frozen=True)
class TinyLiveCanaryPreflightResult:
    result_id: str
    status: str
    contract_id: str
    blockers: tuple[Mapping[str, Any], ...]
    validation_errors: tuple[str, ...]
    preflight_contract_ready: bool
    manual_runbook_ready: bool
    future_canary_shape_defined: bool
    kill_switch_requirements_defined: bool
    kill_switch_verified_for_live: bool
    unresolved_live_blocker_count: int
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = TINY_LIVE_CANARY_PREFLIGHT_RESULT_CONTRACT
        value["blockers"] = [dict(row) for row in self.blockers]
        value["blocker_ids"] = [clean_text(row.get("blocker_id")) for row in self.blockers]
        value["blocker_categories"] = [clean_text(row.get("blocker_category")) for row in self.blockers]
        value["blocker_count"] = len(self.blockers)
        value["validation_errors"] = list(self.validation_errors)
        value["static_preflight_checks_passed"] = not self.blockers and not self.validation_errors
        value["future_tiny_canary_defined"] = self.future_canary_shape_defined
        value["live_connector_blockers_remain_unresolved"] = self.unresolved_live_blocker_count > 0
        value["operator_review_is_not_live_approval"] = True
        value["canary_preflight_is_not_execution_approval"] = True
        value.update(_preflight_safety_flags())
        return value


def build_tiny_live_canary_preflight_contract(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    limit_policy = TinyLiveCanaryLimitPolicy()
    evidence_requirements = tuple(
        [
            TinyLiveCanaryEvidenceRequirement(
                requirement_id="operator_review_packet_required",
                artifact_key="operator_review_packet",
                title="Operator review packet",
                description="Review-only packet must exist and must not authorize live execution.",
            ),
            TinyLiveCanaryEvidenceRequirement(
                requirement_id="disabled_connector_audit_replay_required",
                artifact_key="disabled_connector_audit_replay",
                title="Disabled connector audit replay",
                description="Replay must prove the connector remains disabled, deterministic, and local.",
            ),
            TinyLiveCanaryEvidenceRequirement(
                requirement_id="secret_boundary_validation_required",
                artifact_key="secret_boundary_validation",
                title="Static secret-boundary validation",
                description="Validation must pass without reading, printing, persisting, or requesting real secrets.",
            ),
            TinyLiveCanaryEvidenceRequirement(
                requirement_id="blocker_matrix_review_required",
                artifact_key="live_connector_blocker_matrix",
                title="Live connector blocker matrix",
                description="Critical blockers must remain unresolved and visible to the operator.",
            ),
            TinyLiveCanaryEvidenceRequirement(
                requirement_id="manual_runbook_acknowledgement_required",
                artifact_key="manual_runbook_acknowledgement",
                title="Manual runbook acknowledgement",
                description="Operator must acknowledge the manual runbook and non-execution statement.",
            ),
            TinyLiveCanaryEvidenceRequirement(
                requirement_id="kill_switch_requirement_packet_required",
                artifact_key="kill_switch_requirement_packet",
                title="Kill-switch requirement packet",
                description="Kill-switch requirements must be defined but not live-verified in this build.",
            ),
            TinyLiveCanaryEvidenceRequirement(
                requirement_id="evidence_capture_packet_required",
                artifact_key="evidence_capture_packet",
                title="Evidence capture packet",
                description="Future review must capture contract, runbook, blocker, and stop-condition evidence.",
            ),
        ]
    )
    stop_conditions = tuple(
        [
            TinyLiveCanaryStopCondition(
                condition_id="missing_or_invalid_artifact",
                title="Missing or invalid artifact",
                operator_action="Stop review if any required artifact is missing, invalid, stale, or contradictory.",
            ),
            TinyLiveCanaryStopCondition(
                condition_id="live_capability_detected",
                title="Live capability detected",
                operator_action="Stop review if any artifact reports live execution approved, live connector enabled, or real execution available.",
            ),
            TinyLiveCanaryStopCondition(
                condition_id="secret_or_wallet_material_requested",
                title="Secret or wallet material requested",
                operator_action="Stop review if any step asks for private keys, mnemonics, credential material, wallet access, signing, or authenticated endpoint use.",
            ),
            TinyLiveCanaryStopCondition(
                condition_id="scheduler_or_autonomy_detected",
                title="Scheduler or autonomy detected",
                operator_action="Stop review if any scheduler, daemon, recursive loop, or autonomous execution path can bypass the operator.",
            ),
        ]
    )
    manual_approval_requirements = tuple(
        [
            TinyLiveCanaryManualApprovalRequirement(
                requirement_id="manual_operator_identity_required",
                title="Manual operator identity required",
                description="A future evidence packet must identify the responsible operator.",
            ),
            TinyLiveCanaryManualApprovalRequirement(
                requirement_id="manual_runbook_acknowledgement_required",
                title="Manual runbook acknowledgement required",
                description="A future operator must acknowledge the runbook and non-execution statement.",
            ),
            TinyLiveCanaryManualApprovalRequirement(
                requirement_id="separate_future_live_gate_required",
                title="Separate future live gate required",
                description="This build cannot approve live execution; a separate future gated task is required.",
            ),
        ]
    )
    contract = TinyLiveCanaryPreflightContract(
        contract_id=_stable_id(
            "tiny-live-canary-preflight-contract-033",
            {
                "limit_policy": limit_policy.to_dict(),
                "evidence_requirement_ids": [row.requirement_id for row in evidence_requirements],
                "stop_condition_ids": [row.condition_id for row in stop_conditions],
                "manual_approval_requirement_ids": [row.requirement_id for row in manual_approval_requirements],
            },
        ),
        limit_policy=limit_policy,
        evidence_requirements=evidence_requirements,
        stop_conditions=stop_conditions,
        manual_approval_requirements=manual_approval_requirements,
        kill_switch_requirement=TinyLiveCanaryKillSwitchRequirement(),
        generated_at=generated_at,
    ).to_dict()
    validation = validate_tiny_live_canary_preflight_contract(contract)
    contract["validation"] = validation
    return contract


def validate_tiny_live_canary_preflight_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if contract.get("contract_version") != TINY_LIVE_CANARY_PREFLIGHT_CONTRACT:
        errors.append(f"contract_version must be {TINY_LIVE_CANARY_PREFLIGHT_CONTRACT}")
    limit_policy = dict(contract.get("limit_policy", {}))
    if limit_policy.get("max_market_count") != 1:
        errors.append("max_market_count must be 1")
    if limit_policy.get("max_order_count") != 1:
        errors.append("max_order_count must be 1")
    for field in ("max_position_size_usd", "max_total_notional_usd"):
        value = limit_policy.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or float(value) <= 0:
            errors.append(f"{field} must be a positive tiny numeric placeholder")
    if clean_text(limit_policy.get("allowed_market_status")) != "review_only":
        errors.append("allowed_market_status must be review_only")
    requirement_keys = {
        clean_text(row.get("artifact_key"))
        for row in contract.get("evidence_requirements", [])
        if isinstance(row, Mapping)
    }
    missing_requirements = [key for key in REQUIRED_EVIDENCE_KEYS if key not in requirement_keys]
    if missing_requirements:
        errors.append(f"missing evidence requirements: {', '.join(missing_requirements)}")
    if not contract.get("stop_conditions"):
        errors.append("stop_conditions must not be empty")
    if not contract.get("manual_approval_requirements"):
        errors.append("manual_approval_requirements must not be empty")
    kill_switch = dict(contract.get("kill_switch_requirement", {}))
    if kill_switch.get("requirements_defined") is not True:
        errors.append("kill-switch requirements must be defined")
    if kill_switch.get("verified_for_live") is not False:
        errors.append("kill-switch verified_for_live must be false in this build")
    if kill_switch.get("blocks_live_execution") is not True:
        errors.append("kill-switch must block live execution")
    for field in (
        "required_manual_operator_approval",
        "required_kill_switch_verified",
        "required_disabled_connector_audit_replay",
        "required_operator_packet",
        "required_secret_boundary_validation",
        "required_blocker_review",
        "required_manual_runbook_acknowledgement",
        "required_no_autonomous_scheduler",
        "required_no_real_execution_in_this_build",
        "operator_review_is_not_live_approval",
        "canary_preflight_is_not_execution_approval",
    ):
        if contract.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in ("live_execution_approved", "real_execution_available", "canary_executable_now"):
        if contract.get(field) is not False:
            errors.append(f"{field} must be false")
    return {
        "contract_version": "pmbot_tiny_live_canary_preflight_contract_validation.v1",
        "valid": not errors,
        "status": "passed" if not errors else "blocked",
        "errors": errors,
        "preflight_contract_ready": not errors,
        "live_execution_approved": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "static_validation_only": True,
    }


def build_tiny_live_canary_kill_switch_validation(
    requirement: Mapping[str, Any] | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    requirement_value = dict(requirement or TinyLiveCanaryKillSwitchRequirement().to_dict())
    errors: list[str] = []
    if requirement_value.get("requirements_defined") is not True:
        errors.append("requirements_defined must be true")
    if requirement_value.get("verified_for_live") is not False:
        errors.append("verified_for_live must be false in this build")
    if requirement_value.get("blocks_live_execution") is not True:
        errors.append("blocks_live_execution must be true")
    if requirement_value.get("real_connector_must_remain_disabled_in_current_build") is not True:
        errors.append("real connector must remain disabled in current build")
    validation = TinyLiveCanaryKillSwitchValidation(
        validation_id=_stable_id(
            "tiny-live-canary-kill-switch-validation-033",
            {"requirement_id": requirement_value.get("requirement_id"), "errors": errors},
        ),
        requirement_id=clean_text(requirement_value.get("requirement_id")),
        requirements_defined=requirement_value.get("requirements_defined") is True,
        verified_for_live=requirement_value.get("verified_for_live") is True,
        blocks_live_execution=requirement_value.get("blocks_live_execution") is True,
        status=KILL_SWITCH_STATUS_REQUIREMENTS_DEFINED if not errors else "blocked",
        errors=tuple(errors),
        generated_at=generated_at,
    ).to_dict()
    validation["requirement"] = requirement_value
    return validation


def evaluate_tiny_live_canary_preflight(
    *,
    contract: Mapping[str, Any] | None = None,
    manual_runbook: Mapping[str, Any] | None = None,
    operator_packet: Mapping[str, Any] | None = None,
    audit_replay_result: Mapping[str, Any] | None = None,
    secret_boundary_validation: Mapping[str, Any] | None = None,
    blocker_matrix: Mapping[str, Any] | None = None,
    kill_switch_validation: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    contract_value = dict(contract or build_tiny_live_canary_preflight_contract(generated_at=generated_at))
    contract_validation = validate_tiny_live_canary_preflight_contract(contract_value)
    blockers: list[dict[str, Any]] = []
    validation_errors = list(contract_validation.get("errors", []))
    if contract_validation.get("valid") is not True:
        blockers.append(
            _blocker(
                "TINY-CANARY-PREFLIGHT-CONTRACT-INVALID",
                "tiny_live_canary_preflight_contract_invalid",
                "Tiny live canary preflight contract did not validate.",
            )
        )

    runbook_ready = False
    if manual_runbook is None:
        blockers.append(
            _blocker(
                "TINY-CANARY-MANUAL-RUNBOOK-MISSING",
                "manual_runbook_missing",
                "Manual runbook artifact is required before future canary review.",
            )
        )
    else:
        runbook_validation = validate_tiny_live_canary_manual_runbook(
            manual_runbook,
            generated_at=generated_at,
        )
        runbook_ready = runbook_validation.get("valid") is True
        if not runbook_ready:
            validation_errors.extend(runbook_validation.get("errors", []))
            blockers.append(
                _blocker(
                    "TINY-CANARY-MANUAL-RUNBOOK-INVALID",
                    "manual_runbook_invalid",
                    "Manual runbook must validate before future canary review.",
                )
            )

    if operator_packet is None:
        blockers.append(
            _blocker(
                "TINY-CANARY-OPERATOR-PACKET-MISSING",
                "live_canary_manual_approval_not_collected",
                "Operator review packet is missing; review is not live approval.",
            )
        )
    else:
        packet = dict(operator_packet)
        if packet.get("operator_review_ready") is not True:
            blockers.append(
                _blocker(
                    "TINY-CANARY-OPERATOR-PACKET-NOT-READY",
                    "operator_packet_not_review_ready",
                    "Operator packet must be review-ready before future canary preflight can pass.",
                )
            )
        if packet.get("live_execution_approved") is not False:
            blockers.append(
                _blocker(
                    "TINY-CANARY-OPERATOR-PACKET-UNSAFE",
                    "operator_packet_claims_live_approval",
                    "Operator packet must never approve live execution.",
                )
            )

    if audit_replay_result is None:
        blockers.append(
            _blocker(
                "TINY-CANARY-AUDIT-REPLAY-MISSING",
                "tiny_live_canary_preflight_contract_review_only",
                "Disabled connector audit replay is required before future canary review.",
            )
        )
    else:
        replay = dict(audit_replay_result)
        if clean_text(replay.get("status")) != "replay_passed":
            blockers.append(
                _blocker(
                    "TINY-CANARY-AUDIT-REPLAY-NOT-PASSED",
                    "audit_replay_not_passed",
                    "Disabled connector audit replay must pass before future canary review.",
                )
            )
        for field in ("real_execution_available", "live_execution_approved", "live_connector_enabled"):
            if replay.get(field) is not False:
                blockers.append(
                    _blocker(
                        f"TINY-CANARY-AUDIT-REPLAY-{field.upper()}",
                        "audit_replay_claims_live_capability",
                        f"Audit replay field {field} must be false.",
                    )
                )

    if secret_boundary_validation is None:
        blockers.append(
            _blocker(
                "TINY-CANARY-SECRET-BOUNDARY-MISSING",
                "secret_boundary_validation_missing",
                "Static secret-boundary validation is required before future canary review.",
            )
        )
    elif dict(secret_boundary_validation).get("valid") is not True:
        blockers.append(
            _blocker(
                "TINY-CANARY-SECRET-BOUNDARY-BLOCKED",
                "secret_boundary_validation_blocked",
                "Static secret-boundary validation must pass without inspecting real secrets.",
            )
        )

    unresolved_live_blocker_count = 0
    if blocker_matrix is None:
        blockers.append(
            _blocker(
                "TINY-CANARY-BLOCKER-MATRIX-MISSING",
                "live_connector_blocker_matrix_missing",
                "Live connector blocker matrix is required before future canary review.",
            )
        )
    else:
        matrix = dict(blocker_matrix)
        unresolved_live_blocker_count = int(matrix.get("unresolved_blocker_count", 0) or 0)
        if matrix.get("all_blockers_unresolved") is not True or unresolved_live_blocker_count <= 0:
            blockers.append(
                _blocker(
                    "TINY-CANARY-BLOCKERS-NOT-UNRESOLVED",
                    "live_connector_blockers_not_unresolved",
                    "All live connector blockers must remain unresolved in this build.",
                )
            )
        if matrix.get("live_execution_available") is not False:
            blockers.append(
                _blocker(
                    "TINY-CANARY-BLOCKER-MATRIX-UNSAFE",
                    "blocker_matrix_claims_live_execution_available",
                    "Blocker matrix must not report live execution as available.",
                )
            )

    kill_switch_requirements_defined = False
    kill_switch_verified_for_live = False
    if kill_switch_validation is None:
        blockers.append(
            _blocker(
                "TINY-CANARY-KILL-SWITCH-VALIDATION-MISSING",
                "kill_switch_not_live_verified",
                "Kill-switch requirement validation is required and must remain not live-verified in this build.",
            )
        )
    else:
        kill_switch = dict(kill_switch_validation)
        kill_switch_requirements_defined = kill_switch.get("requirements_defined") is True
        kill_switch_verified_for_live = kill_switch.get("verified_for_live") is True
        if kill_switch.get("valid") is not True:
            blockers.append(
                _blocker(
                    "TINY-CANARY-KILL-SWITCH-VALIDATION-BLOCKED",
                    "kill_switch_validation_blocked",
                    "Kill-switch requirements must be defined and must block live execution.",
                )
            )
        if kill_switch_verified_for_live:
            blockers.append(
                _blocker(
                    "TINY-CANARY-KILL-SWITCH-LIVE-VERIFIED-UNEXPECTED",
                    "kill_switch_live_verified_unexpected",
                    "Kill-switch verified_for_live must remain false in this build.",
                )
            )

    status = PREFLIGHT_STATUS_READY if not blockers and not validation_errors else PREFLIGHT_STATUS_BLOCKED
    result = TinyLiveCanaryPreflightResult(
        result_id=_stable_id(
            "tiny-live-canary-preflight-result-033",
            {
                "contract_id": contract_value.get("contract_id"),
                "blocker_ids": [row.get("blocker_id") for row in blockers],
                "validation_errors": validation_errors,
                "status": status,
            },
        ),
        status=status,
        contract_id=clean_text(contract_value.get("contract_id")),
        blockers=tuple(blockers),
        validation_errors=tuple(validation_errors),
        preflight_contract_ready=contract_validation.get("valid") is True,
        manual_runbook_ready=runbook_ready,
        future_canary_shape_defined=contract_validation.get("valid") is True,
        kill_switch_requirements_defined=kill_switch_requirements_defined,
        kill_switch_verified_for_live=kill_switch_verified_for_live,
        unresolved_live_blocker_count=unresolved_live_blocker_count,
        generated_at=generated_at,
    ).to_dict()
    return result


def render_tiny_live_canary_preflight_contract_markdown(contract: Mapping[str, Any]) -> str:
    limit = dict(contract.get("limit_policy", {}))
    kill_switch = dict(contract.get("kill_switch_requirement", {}))
    lines = [
        "# PMBOT Tiny Live Canary Preflight Contract",
        "",
        f"- Contract: `{contract.get('contract_id')}`",
        f"- Preflight contract ready: `{str(contract.get('preflight_contract_ready')).lower()}`",
        f"- Future tiny canary defined: `{str(contract.get('future_tiny_canary_defined')).lower()}`",
        f"- Canary executable now: `{str(contract.get('canary_executable_now')).lower()}`",
        f"- Live execution approved: `{str(contract.get('live_execution_approved')).lower()}`",
        f"- Real execution available: `{str(contract.get('real_execution_available')).lower()}`",
        "",
        "## Limits",
        "",
        f"- Max markets: {limit.get('max_market_count')}",
        f"- Max order count: {limit.get('max_order_count')}",
        f"- Max position size USD: `{limit.get('max_position_size_usd')}`",
        f"- Max total notional USD: `{limit.get('max_total_notional_usd')}`",
        f"- Allowed market status: `{limit.get('allowed_market_status')}`",
        "",
        "## Evidence Requirements",
        "",
        *bullet_lines(
            f"`{row.get('artifact_key')}` {row.get('title')}"
            for row in contract.get("evidence_requirements", [])
            if isinstance(row, Mapping)
        ),
        "",
        "## Kill-Switch",
        "",
        f"- Requirements defined: `{str(kill_switch.get('requirements_defined')).lower()}`",
        f"- Verified for live: `{str(kill_switch.get('verified_for_live')).lower()}`",
        f"- Blocks live execution: `{str(kill_switch.get('blocks_live_execution')).lower()}`",
        "",
        "## Stop Conditions",
        "",
        *bullet_lines(
            f"`{row.get('condition_id')}` {row.get('operator_action')}"
            for row in contract.get("stop_conditions", [])
            if isinstance(row, Mapping)
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_tiny_live_canary_preflight_result_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Tiny Live Canary Preflight Result",
        "",
        f"- Result: `{result.get('result_id')}`",
        f"- Status: `{result.get('status')}`",
        f"- Static preflight checks passed: `{str(result.get('static_preflight_checks_passed')).lower()}`",
        f"- Preflight contract ready: `{str(result.get('preflight_contract_ready')).lower()}`",
        f"- Manual runbook ready: `{str(result.get('manual_runbook_ready')).lower()}`",
        f"- Future canary shape defined: `{str(result.get('future_canary_shape_defined')).lower()}`",
        f"- Kill-switch requirements defined: `{str(result.get('kill_switch_requirements_defined')).lower()}`",
        f"- Kill-switch verified for live: `{str(result.get('kill_switch_verified_for_live')).lower()}`",
        f"- Canary executable now: `{str(result.get('canary_executable_now')).lower()}`",
        f"- Live execution approved: `{str(result.get('live_execution_approved')).lower()}`",
        f"- Real execution available: `{str(result.get('real_execution_available')).lower()}`",
        f"- Unresolved live blockers: {result.get('unresolved_live_blocker_count')}",
        "",
        "## Preflight Blockers",
        "",
        *bullet_lines(
            f"`{row.get('blocker_id')}` `{row.get('blocker_category')}` {row.get('message')}"
            for row in result.get("blockers", [])
            if isinstance(row, Mapping)
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _blocker(blocker_id: str, blocker_category: str, message: str) -> dict[str, Any]:
    return TinyLiveCanaryPreflightBlocker(
        blocker_id=blocker_id,
        blocker_category=blocker_category,
        message=message,
    ).to_dict()


def _preflight_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "passive_artifact_only": True,
        "manual_review_only": True,
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "real_wallet_access_performed": False,
        "cryptographic_signing_performed": False,
        "real_order_placement_performed": False,
        "authenticated_endpoint_call_performed": False,
        "real_execution_available": False,
        "live_execution_approved": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "canary_executable_now": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
