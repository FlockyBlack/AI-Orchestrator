from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_readiness_evidence_blocker_summary,
    validate_secret_boundary_readiness_evidence_bundle,
    validate_secret_boundary_readiness_evidence_item,
    validate_secret_boundary_readiness_evidence_manifest,
    validate_secret_boundary_readiness_evidence_reference,
)

TASK_ID = "ORCH-PMBOT-TRADING-MVP-035-LIVE-CANARY-DRY-RUN-READINESS-EVIDENCE-BUNDLE"

LIVE_CANARY_READINESS_EVIDENCE_BUNDLE_CONTRACT = "pmbot_live_canary_readiness_evidence_bundle.v1"
LIVE_CANARY_READINESS_EVIDENCE_ITEM_CONTRACT = "pmbot_live_canary_readiness_evidence_item.v1"
LIVE_CANARY_READINESS_EVIDENCE_REFERENCE_CONTRACT = "pmbot_live_canary_readiness_evidence_reference.v1"
LIVE_CANARY_READINESS_EVIDENCE_VALIDATION_CONTRACT = (
    "pmbot_live_canary_readiness_evidence_validation.v1"
)
LIVE_CANARY_READINESS_EVIDENCE_BLOCKER_CONTRACT = "pmbot_live_canary_readiness_evidence_blocker.v1"
LIVE_CANARY_READINESS_EVIDENCE_SUMMARY_CONTRACT = "pmbot_live_canary_readiness_evidence_summary.v1"
LIVE_CANARY_READINESS_EVIDENCE_MANIFEST_CONTRACT = "pmbot_live_canary_readiness_evidence_manifest.v1"

BUNDLE_STATUS_REVIEW_READY = "readiness_evidence_bundle_review_ready"
BUNDLE_STATUS_BLOCKED = "readiness_evidence_bundle_blocked"
ITEM_STATUS_PRESENT_REVIEW_READY = "present_review_ready"
ITEM_STATUS_MISSING_REQUIRED_EVIDENCE = "missing_required_evidence"
ITEM_STATUS_REVIEW_ONLY_NON_EXECUTABLE = "review_only_non_executable"

VALIDATION_STATUS_DRY_RUN_VALID = "evidence_bundle_valid_for_dry_run_review"
VALIDATION_STATUS_MISSING_REQUIRED_EVIDENCE = "missing_required_evidence"
VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_PRESENT = "unresolved_blockers_not_present"
VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL = "forbidden_execution_approval_detected"
VALIDATION_STATUS_FORBIDDEN_SECRET_OR_SIGNING_FIELD = "forbidden_secret_or_signing_field_detected"
VALIDATION_STATUS_DISABLED_CONNECTOR_EVIDENCE_MISSING = "disabled_connector_evidence_missing"
VALIDATION_STATUS_SECRET_BOUNDARY_EVIDENCE_MISSING = "secret_boundary_evidence_missing"
VALIDATION_STATUS_AUDIT_REPLAY_EVIDENCE_MISSING = "audit_replay_evidence_missing"
VALIDATION_STATUS_OPERATOR_PACKET_EVIDENCE_MISSING = "operator_packet_evidence_missing"
VALIDATION_STATUS_OPERATOR_INTENT_EVIDENCE_MISSING = "operator_intent_evidence_missing"
VALIDATION_STATUS_PREFLIGHT_CONTRACT_EVIDENCE_MISSING = "preflight_contract_evidence_missing"
VALIDATION_STATUS_MANUAL_RUNBOOK_EVIDENCE_MISSING = "manual_runbook_evidence_missing"
VALIDATION_STATUS_KILL_SWITCH_EVIDENCE_MISSING = "kill_switch_evidence_missing"

NON_EXECUTION_STATEMENTS = (
    "This readiness evidence bundle is review evidence only.",
    "This readiness evidence bundle does not authorize live execution.",
    "This readiness evidence bundle does not enable wallet access, signing, order placement, authenticated endpoints, or real execution.",
    "Live connector blockers remain unresolved and canary execution remains disabled.",
)

REQUIRED_EVIDENCE_TYPES = (
    "disabled_connector_adapter_status",
    "secret_boundary_validation_summary",
    "live_canary_readiness_packet",
    "canary_replay_acceptance",
    "live_connector_audit_replay",
    "operator_live_approval_packet",
    "tiny_live_canary_preflight_contract",
    "tiny_live_canary_manual_runbook",
    "dry_run_operator_intent_packet",
    "live_connector_blocker_matrix",
    "kill_switch_requirements",
    "abort_conditions",
    "evidence_capture_checklist",
    "risk_review",
    "risk_limit_control_plane",
)

OPTIONAL_EVIDENCE_TYPES = (
    "dry_run_receipt_references",
    "result_artifact_references",
)

FORCED_FALSE_EXECUTION_FIELDS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "live_connector_enabled",
)

DEFAULT_035_BLOCKERS = (
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-032",
        "blocker_category": "readiness_evidence_bundle_review_only",
        "message": "The readiness evidence bundle is a review artifact only.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-033",
        "blocker_category": "readiness_evidence_bundle_not_live_approval",
        "message": "The readiness evidence bundle does not authorize live execution.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-034",
        "blocker_category": "readiness_evidence_bundle_not_operator_executed",
        "message": "The readiness evidence bundle has not been executed as an operator approval workflow.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-035",
        "blocker_category": "evidence_bundle_does_not_resolve_live_blockers",
        "message": "The evidence bundle links blockers but does not resolve them.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-036",
        "blocker_category": "live_canary_execution_still_disabled",
        "message": "No code path may execute a live canary in this build.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-037",
        "blocker_category": "live_canary_real_funding_still_not_configured",
        "message": "No live funding source, balance check, or reconciliation path exists.",
    },
    {
        "blocker_id": "PMBOT-LIVE-BLOCKER-038",
        "blocker_category": "live_canary_order_adapter_still_disabled",
        "message": "No order adapter can submit, place, or transmit real orders.",
    },
)

NEXT_REQUIRED_GATES = (
    "separate future operator-approved task before any live connector design work",
    "separate future dual-control live approval model",
    "separate future live credential handling policy",
    "separate future kill-switch verification against any live adapter boundary",
    "separate future disabled-first order adapter design without enabling submission",
)


@dataclass(frozen=True)
class LiveCanaryReadinessEvidenceReference:
    reference_id: str
    evidence_type: str
    source_component: str
    reference_path_or_id: str
    description: str
    present: bool = True
    review_ready: bool = True
    execution_enabling: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_READINESS_EVIDENCE_REFERENCE_CONTRACT
        value.update(_evidence_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryReadinessEvidenceItem:
    evidence_id: str
    evidence_type: str
    source_component: str
    reference_path_or_id: str
    status: str
    required_for_future_live_canary_review: bool
    present: bool
    review_ready: bool
    execution_enabling: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_READINESS_EVIDENCE_ITEM_CONTRACT
        value.update(_evidence_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryReadinessEvidenceBlocker:
    blocker_id: str
    blocker_category: str
    message: str
    severity: str = "critical"
    resolution_status: str = "unresolved"
    blocks_canary_execution_now: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_READINESS_EVIDENCE_BLOCKER_CONTRACT
        value.update(_evidence_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryReadinessEvidenceSummary:
    summary_id: str
    status: str
    readiness_evidence_bundle_ready: bool
    evidence_bundle_review_ready: bool
    readiness_chain_complete_for_dry_run_review: bool
    evidence_manifest_ready: bool
    evidence_item_count: int
    missing_required_evidence_count: int
    unresolved_live_blocker_count: int
    warnings: tuple[str, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_READINESS_EVIDENCE_SUMMARY_CONTRACT
        value["warnings"] = list(self.warnings)
        value["readiness_evidence_bundle_is_not_live_approval"] = True
        value["readiness_evidence_bundle_review_ready"] = self.evidence_bundle_review_ready
        value["operator_intent_remains_human_acknowledgement_only"] = True
        value.update(_evidence_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryReadinessEvidenceValidationResult:
    validation_id: str
    valid: bool
    status: str
    statuses: tuple[str, ...]
    errors: tuple[str, ...]
    missing_required_evidence: tuple[str, ...]
    forbidden_field_paths: tuple[str, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_READINESS_EVIDENCE_VALIDATION_CONTRACT
        value["statuses"] = list(self.statuses)
        value["errors"] = list(self.errors)
        value["missing_required_evidence"] = list(self.missing_required_evidence)
        value["forbidden_field_paths"] = list(self.forbidden_field_paths)
        value["readiness_evidence_bundle_ready"] = self.valid
        value["evidence_bundle_review_ready"] = self.valid
        value["readiness_chain_complete_for_dry_run_review"] = self.valid
        value["readiness_evidence_bundle_is_not_live_approval"] = True
        value.update(_evidence_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryReadinessEvidenceBundle:
    bundle_id: str
    task_id: str
    bundle_status: str
    evidence_items: tuple[Mapping[str, Any], ...]
    evidence_references: tuple[Mapping[str, Any], ...]
    unresolved_blockers: tuple[Mapping[str, Any], ...]
    artifact_chain: tuple[Mapping[str, Any], ...]
    blocker_summary: Mapping[str, Any]
    current_execution_posture: Mapping[str, Any]
    safety_summary: Mapping[str, Any]
    non_execution_statements: tuple[str, ...]
    next_required_gates: tuple[str, ...]
    warnings: tuple[str, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_READINESS_EVIDENCE_BUNDLE_CONTRACT
        value["schema_version"] = "035.v1"
        value["evidence_items"] = [dict(row) for row in self.evidence_items]
        value["evidence_references"] = [dict(row) for row in self.evidence_references]
        value["unresolved_blockers"] = [dict(row) for row in self.unresolved_blockers]
        value["artifact_chain"] = [dict(row) for row in self.artifact_chain]
        value["blocker_summary"] = dict(self.blocker_summary)
        value["current_execution_posture"] = dict(self.current_execution_posture)
        value["safety_summary"] = dict(self.safety_summary)
        value["non_execution_statements"] = list(self.non_execution_statements)
        value["next_required_gates"] = list(self.next_required_gates)
        value["warnings"] = list(self.warnings)
        value["generated_for_review_only"] = True
        value["readiness_evidence_bundle_ready"] = self.bundle_status == BUNDLE_STATUS_REVIEW_READY
        value["evidence_bundle_review_ready"] = self.bundle_status == BUNDLE_STATUS_REVIEW_READY
        value["readiness_chain_complete_for_dry_run_review"] = self.bundle_status == BUNDLE_STATUS_REVIEW_READY
        value["evidence_manifest_ready"] = True
        value["readiness_evidence_bundle_is_not_live_approval"] = True
        value["operator_intent_remains_human_acknowledgement_only"] = True
        value["evidence_item_count"] = len(self.evidence_items)
        value["missing_required_evidence_count"] = len(
            _missing_required_evidence_types([dict(row) for row in self.evidence_items])
        )
        value["unresolved_live_blocker_count"] = len(self.unresolved_blockers)
        value.update(_evidence_safety_flags())
        return value


def build_live_canary_readiness_evidence_bundle(
    *,
    disabled_connector_status: Mapping[str, Any] | None = None,
    disabled_connector_audit: Mapping[str, Any] | None = None,
    secret_boundary_validation: Mapping[str, Any] | None = None,
    live_canary_readiness_packet: Mapping[str, Any] | None = None,
    canary_replay_acceptance: Mapping[str, Any] | None = None,
    live_connector_audit_replay: Mapping[str, Any] | None = None,
    operator_approval_packet: Mapping[str, Any] | None = None,
    tiny_live_canary_preflight_contract: Mapping[str, Any] | None = None,
    tiny_live_canary_manual_runbook: Mapping[str, Any] | None = None,
    operator_intent_packet: Mapping[str, Any] | None = None,
    blocker_matrix: Mapping[str, Any] | None = None,
    kill_switch_validation: Mapping[str, Any] | None = None,
    preflight_result: Mapping[str, Any] | None = None,
    risk_limit_control_plane: Mapping[str, Any] | None = None,
    dry_run_receipt_references: Sequence[str] | None = None,
    result_artifact_references: Sequence[str] | None = None,
    artifact_reference_overrides: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    disabled_status = dict(disabled_connector_status or {})
    disabled_audit = dict(disabled_connector_audit or {})
    secret_summary = _secret_boundary_summary(
        secret_boundary_validation,
        live_connector_audit_replay=live_connector_audit_replay,
        disabled_connector_audit=disabled_audit,
        generated_at=generated_at,
    )
    readiness_packet = dict(live_canary_readiness_packet or {})
    replay_acceptance = dict(canary_replay_acceptance or {})
    audit_replay = dict(live_connector_audit_replay or {})
    operator_packet = dict(operator_approval_packet or {})
    preflight_contract = dict(tiny_live_canary_preflight_contract or {})
    manual_runbook = dict(tiny_live_canary_manual_runbook or {})
    intent_packet = dict(operator_intent_packet or {})
    matrix = dict(blocker_matrix or {})
    kill_switch = dict(kill_switch_validation or {})
    preflight = dict(preflight_result or {})
    risk_control = dict(risk_limit_control_plane or {})
    overrides = {clean_text(key): clean_text(value) for key, value in dict(artifact_reference_overrides or {}).items()}

    items = _build_evidence_items(
        disabled_connector_status=disabled_status,
        disabled_connector_audit=disabled_audit,
        secret_boundary_validation=secret_summary,
        live_canary_readiness_packet=readiness_packet,
        canary_replay_acceptance=replay_acceptance,
        live_connector_audit_replay=audit_replay,
        operator_approval_packet=operator_packet,
        tiny_live_canary_preflight_contract=preflight_contract,
        tiny_live_canary_manual_runbook=manual_runbook,
        operator_intent_packet=intent_packet,
        blocker_matrix=matrix,
        kill_switch_validation=kill_switch,
        preflight_result=preflight,
        risk_limit_control_plane=risk_control,
        dry_run_receipt_references=dry_run_receipt_references,
        result_artifact_references=result_artifact_references,
        artifact_reference_overrides=overrides,
    )
    references = tuple(_reference_from_item(item) for item in items)
    blockers = tuple(_evidence_blockers(matrix))
    blocker_summary = _blocker_summary(blockers, matrix)
    current_posture = _current_execution_posture()
    warnings = tuple(_bundle_warnings(items=items, blockers=blockers))
    bundle_id = _stable_id(
        "live-canary-readiness-evidence-bundle-035",
        {
            "task_id": TASK_ID,
            "evidence_types": [item.get("evidence_type") for item in items],
            "evidence_references": [item.get("reference_path_or_id") for item in items],
            "blocker_ids": [row.get("blocker_id") for row in blockers],
        },
    )
    bundle = LiveCanaryReadinessEvidenceBundle(
        bundle_id=bundle_id,
        task_id=TASK_ID,
        bundle_status=BUNDLE_STATUS_REVIEW_READY,
        evidence_items=tuple(items),
        evidence_references=references,
        unresolved_blockers=blockers,
        artifact_chain=references,
        blocker_summary=blocker_summary,
        current_execution_posture=current_posture,
        safety_summary=trading_core_safety_summary(),
        non_execution_statements=NON_EXECUTION_STATEMENTS,
        next_required_gates=NEXT_REQUIRED_GATES,
        warnings=warnings,
        generated_at=generated_at,
    ).to_dict()
    validation = validate_live_canary_readiness_evidence_bundle(bundle, generated_at=generated_at)
    bundle["validation"] = validation
    if validation.get("valid") is not True:
        bundle["bundle_status"] = BUNDLE_STATUS_BLOCKED
        bundle["readiness_evidence_bundle_ready"] = False
        bundle["evidence_bundle_review_ready"] = False
        bundle["readiness_chain_complete_for_dry_run_review"] = False
        bundle["missing_required_evidence_count"] = len(validation.get("missing_required_evidence", []))
    return bundle


def validate_live_canary_readiness_evidence_bundle(
    bundle: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    statuses: list[str] = []

    if bundle.get("contract_version") != LIVE_CANARY_READINESS_EVIDENCE_BUNDLE_CONTRACT:
        errors.append(f"contract_version must be {LIVE_CANARY_READINESS_EVIDENCE_BUNDLE_CONTRACT}")
        statuses.append(VALIDATION_STATUS_MISSING_REQUIRED_EVIDENCE)

    items = [dict(row) for row in bundle.get("evidence_items", []) if isinstance(row, Mapping)]
    missing_required = _missing_required_evidence_types(items)
    if missing_required:
        errors.append(f"missing required evidence: {', '.join(missing_required)}")
        statuses.append(VALIDATION_STATUS_MISSING_REQUIRED_EVIDENCE)
    status_by_missing_type = {
        "disabled_connector_adapter_status": VALIDATION_STATUS_DISABLED_CONNECTOR_EVIDENCE_MISSING,
        "secret_boundary_validation_summary": VALIDATION_STATUS_SECRET_BOUNDARY_EVIDENCE_MISSING,
        "live_connector_audit_replay": VALIDATION_STATUS_AUDIT_REPLAY_EVIDENCE_MISSING,
        "operator_live_approval_packet": VALIDATION_STATUS_OPERATOR_PACKET_EVIDENCE_MISSING,
        "dry_run_operator_intent_packet": VALIDATION_STATUS_OPERATOR_INTENT_EVIDENCE_MISSING,
        "tiny_live_canary_preflight_contract": VALIDATION_STATUS_PREFLIGHT_CONTRACT_EVIDENCE_MISSING,
        "tiny_live_canary_manual_runbook": VALIDATION_STATUS_MANUAL_RUNBOOK_EVIDENCE_MISSING,
        "kill_switch_requirements": VALIDATION_STATUS_KILL_SWITCH_EVIDENCE_MISSING,
        "risk_limit_control_plane": "risk_limit_control_plane_evidence_missing",
    }
    statuses.extend(status_by_missing_type[item] for item in missing_required if item in status_by_missing_type)

    for index, item in enumerate(items):
        if item.get("execution_enabling") is not False:
            errors.append(f"evidence_items[{index}].execution_enabling must be false")
            statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
        item_validation = validate_secret_boundary_readiness_evidence_item(item, generated_at=generated_at)
        if item_validation.get("valid") is not True:
            errors.append(f"evidence_items[{index}] violates static secret boundary")
            statuses.append(VALIDATION_STATUS_FORBIDDEN_SECRET_OR_SIGNING_FIELD)

    references = [dict(row) for row in bundle.get("evidence_references", []) if isinstance(row, Mapping)]
    for index, reference in enumerate(references):
        if reference.get("execution_enabling") is not False:
            errors.append(f"evidence_references[{index}].execution_enabling must be false")
            statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
        reference_validation = validate_secret_boundary_readiness_evidence_reference(
            reference,
            generated_at=generated_at,
        )
        if reference_validation.get("valid") is not True:
            errors.append(f"evidence_references[{index}] violates static secret boundary")
            statuses.append(VALIDATION_STATUS_FORBIDDEN_SECRET_OR_SIGNING_FIELD)

    blockers = [dict(row) for row in bundle.get("unresolved_blockers", []) if isinstance(row, Mapping)]
    if not blockers:
        errors.append("unresolved blockers must be present and non-empty")
        statuses.append(VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_PRESENT)
    if any(clean_text(row.get("resolution_status")) == "resolved" for row in blockers):
        errors.append("readiness evidence bundle cannot contain resolved live blockers")
        statuses.append(VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_PRESENT)

    blocker_summary = dict(bundle.get("blocker_summary", {}))
    if int(blocker_summary.get("unresolved_live_blocker_count", 0) or 0) <= 0:
        errors.append("blocker_summary.unresolved_live_blocker_count must be positive")
        statuses.append(VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_PRESENT)
    if blocker_summary.get("all_live_connector_blockers_unresolved") is not True:
        errors.append("all live connector blockers must remain unresolved")
        statuses.append(VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_PRESENT)
    blocker_validation = validate_secret_boundary_readiness_evidence_blocker_summary(
        blocker_summary,
        generated_at=generated_at,
    )
    if blocker_validation.get("valid") is not True:
        errors.append("blocker summary violates static secret boundary")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_SECRET_OR_SIGNING_FIELD)

    statement_text = json.dumps(bundle.get("non_execution_statements", []), sort_keys=True)
    for statement in NON_EXECUTION_STATEMENTS:
        if statement not in statement_text:
            errors.append(f"missing non-execution statement: {statement}")
            statuses.append(VALIDATION_STATUS_MISSING_REQUIRED_EVIDENCE)

    current_posture = dict(bundle.get("current_execution_posture", {}))
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if bundle.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
        if current_posture.get(field) is not False:
            errors.append(f"current_execution_posture.{field} must be false")
            statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
    if bundle.get("readiness_evidence_bundle_is_not_live_approval") is not True:
        errors.append("readiness_evidence_bundle_is_not_live_approval must be true")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
    if bundle.get("generated_for_review_only") is not True:
        errors.append("generated_for_review_only must be true")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)

    secret_validation = validate_secret_boundary_readiness_evidence_bundle(bundle, generated_at=generated_at)
    forbidden_paths = _clean_list(secret_validation.get("forbidden_secret_field_paths"))
    if secret_validation.get("valid") is not True:
        errors.append("readiness evidence bundle violates static secret boundary")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_SECRET_OR_SIGNING_FIELD)

    statuses = _dedupe(statuses)
    valid = not errors
    if valid:
        statuses = [VALIDATION_STATUS_DRY_RUN_VALID]
    status = statuses[0] if statuses else VALIDATION_STATUS_DRY_RUN_VALID
    return LiveCanaryReadinessEvidenceValidationResult(
        validation_id=_stable_id(
            "live-canary-readiness-evidence-validation-035",
            {
                "bundle_id": bundle.get("bundle_id"),
                "missing_required_evidence": missing_required,
                "errors": errors,
                "forbidden_field_paths": forbidden_paths,
            },
        ),
        valid=valid,
        status=status,
        statuses=tuple(statuses),
        errors=tuple(errors),
        missing_required_evidence=tuple(missing_required),
        forbidden_field_paths=tuple(_dedupe(forbidden_paths)),
        generated_at=generated_at,
    ).to_dict()


def summarize_live_canary_readiness_evidence_bundle(
    bundle: Mapping[str, Any],
    *,
    latest_readiness_evidence_bundle_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    validation = validate_live_canary_readiness_evidence_bundle(bundle, generated_at=generated_at)
    summary = LiveCanaryReadinessEvidenceSummary(
        summary_id=_stable_id(
            "live-canary-readiness-evidence-summary-035",
            {
                "bundle_id": bundle.get("bundle_id"),
                "validation_status": validation.get("status"),
                "latest_path": clean_text(latest_readiness_evidence_bundle_path),
            },
        ),
        status=clean_text(bundle.get("bundle_status")) or BUNDLE_STATUS_BLOCKED,
        readiness_evidence_bundle_ready=validation.get("valid") is True,
        evidence_bundle_review_ready=validation.get("valid") is True,
        readiness_chain_complete_for_dry_run_review=validation.get("valid") is True,
        evidence_manifest_ready=True,
        evidence_item_count=int(bundle.get("evidence_item_count", 0) or 0),
        missing_required_evidence_count=len(validation.get("missing_required_evidence", [])),
        unresolved_live_blocker_count=int(bundle.get("unresolved_live_blocker_count", 0) or 0),
        warnings=tuple(_clean_list(bundle.get("warnings"))),
        generated_at=generated_at,
    ).to_dict()
    summary["validation_status"] = validation.get("status")
    summary["validation_errors"] = list(validation.get("errors", []))
    summary["missing_required_evidence"] = list(validation.get("missing_required_evidence", []))
    summary["latest_readiness_evidence_bundle_path"] = clean_text(latest_readiness_evidence_bundle_path)
    return summary


def summarize_live_canary_readiness_evidence_bundle_for_operator_ui_panel(
    bundle: Mapping[str, Any],
    *,
    latest_readiness_evidence_bundle_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    summary = summarize_live_canary_readiness_evidence_bundle(
        bundle,
        latest_readiness_evidence_bundle_path=latest_readiness_evidence_bundle_path,
        generated_at=generated_at,
    )
    return {
        "contract_version": "pmbot_live_canary_readiness_evidence_operator_ui_summary.v1",
        "readiness_evidence_bundle_status": summary.get("status"),
        "readiness_evidence_bundle_review_ready": summary.get("readiness_evidence_bundle_review_ready") is True,
        "readiness_evidence_bundle_is_not_live_approval": True,
        "evidence_item_count": int(summary.get("evidence_item_count", 0) or 0),
        "missing_required_evidence_count": int(summary.get("missing_required_evidence_count", 0) or 0),
        "unresolved_live_blocker_count": int(summary.get("unresolved_live_blocker_count", 0) or 0),
        "latest_readiness_evidence_bundle_path": summary.get("latest_readiness_evidence_bundle_path", ""),
        "validation_status": summary.get("validation_status", ""),
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def build_live_canary_readiness_evidence_manifest(
    bundle: Mapping[str, Any] | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    bundle_value = dict(bundle or build_live_canary_readiness_evidence_bundle(generated_at=generated_at))
    validation = validate_live_canary_readiness_evidence_bundle(bundle_value, generated_at=generated_at)
    manifest = {
        "contract_version": LIVE_CANARY_READINESS_EVIDENCE_MANIFEST_CONTRACT,
        "task_id": TASK_ID,
        "version": "035.v1",
        "generated_at": generated_at,
        "generated_for_review_only": True,
        "current_execution_posture": dict(bundle_value.get("current_execution_posture", _current_execution_posture())),
        "artifact_chain": [dict(row) for row in bundle_value.get("artifact_chain", []) if isinstance(row, Mapping)],
        "blocker_summary": dict(bundle_value.get("blocker_summary", {})),
        "safety_summary": dict(bundle_value.get("safety_summary", trading_core_safety_summary())),
        "evidence_items": [
            dict(row) for row in bundle_value.get("evidence_items", []) if isinstance(row, Mapping)
        ],
        "missing_evidence": list(validation.get("missing_required_evidence", [])),
        "warnings": list(bundle_value.get("warnings", [])),
        "next_required_gates": list(bundle_value.get("next_required_gates", NEXT_REQUIRED_GATES)),
        "validation": {
            "valid": validation.get("valid") is True,
            "status": clean_text(validation.get("status")),
            "statuses": list(validation.get("statuses", [])),
            "errors": list(validation.get("errors", [])),
        },
        "readiness_evidence_bundle_status": clean_text(bundle_value.get("bundle_status")),
        "readiness_evidence_bundle_ready": validation.get("valid") is True,
        "evidence_bundle_review_ready": validation.get("valid") is True,
        "readiness_chain_complete_for_dry_run_review": validation.get("valid") is True,
        "readiness_evidence_bundle_is_not_live_approval": True,
        "operator_intent_remains_human_acknowledgement_only": True,
        "evidence_item_count": int(bundle_value.get("evidence_item_count", 0) or 0),
        "missing_required_evidence_count": len(validation.get("missing_required_evidence", [])),
        "unresolved_live_blocker_count": int(bundle_value.get("unresolved_live_blocker_count", 0) or 0),
    }
    manifest.update(_evidence_safety_flags())
    return manifest


def validate_live_canary_readiness_evidence_manifest(
    manifest: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    statuses: list[str] = []
    if manifest.get("contract_version") != LIVE_CANARY_READINESS_EVIDENCE_MANIFEST_CONTRACT:
        errors.append(f"contract_version must be {LIVE_CANARY_READINESS_EVIDENCE_MANIFEST_CONTRACT}")
        statuses.append(VALIDATION_STATUS_MISSING_REQUIRED_EVIDENCE)
    if manifest.get("generated_for_review_only") is not True:
        errors.append("generated_for_review_only must be true")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if manifest.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
        if dict(manifest.get("current_execution_posture", {})).get(field) is not False:
            errors.append(f"current_execution_posture.{field} must be false")
            statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
    if manifest.get("readiness_evidence_bundle_is_not_live_approval") is not True:
        errors.append("readiness_evidence_bundle_is_not_live_approval must be true")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
    if int(manifest.get("unresolved_live_blocker_count", 0) or 0) <= 0:
        errors.append("unresolved_live_blocker_count must be positive")
        statuses.append(VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_PRESENT)
    secret_validation = validate_secret_boundary_readiness_evidence_manifest(manifest, generated_at=generated_at)
    forbidden_paths = _clean_list(secret_validation.get("forbidden_secret_field_paths"))
    if secret_validation.get("valid") is not True:
        errors.append("readiness evidence manifest violates static secret boundary")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_SECRET_OR_SIGNING_FIELD)
    valid = not errors
    statuses = [VALIDATION_STATUS_DRY_RUN_VALID] if valid else _dedupe(statuses)
    status = statuses[0] if statuses else VALIDATION_STATUS_DRY_RUN_VALID
    return LiveCanaryReadinessEvidenceValidationResult(
        validation_id=_stable_id(
            "live-canary-readiness-evidence-manifest-validation-035",
            {
                "task_id": manifest.get("task_id"),
                "errors": errors,
                "forbidden_field_paths": forbidden_paths,
            },
        ),
        valid=valid,
        status=status,
        statuses=tuple(statuses),
        errors=tuple(errors),
        missing_required_evidence=tuple(_clean_list(manifest.get("missing_evidence"))),
        forbidden_field_paths=tuple(_dedupe(forbidden_paths)),
        generated_at=generated_at,
    ).to_dict()


def _build_evidence_items(
    *,
    disabled_connector_status: Mapping[str, Any],
    disabled_connector_audit: Mapping[str, Any],
    secret_boundary_validation: Mapping[str, Any],
    live_canary_readiness_packet: Mapping[str, Any],
    canary_replay_acceptance: Mapping[str, Any],
    live_connector_audit_replay: Mapping[str, Any],
    operator_approval_packet: Mapping[str, Any],
    tiny_live_canary_preflight_contract: Mapping[str, Any],
    tiny_live_canary_manual_runbook: Mapping[str, Any],
    operator_intent_packet: Mapping[str, Any],
    blocker_matrix: Mapping[str, Any],
    kill_switch_validation: Mapping[str, Any],
    preflight_result: Mapping[str, Any],
    risk_limit_control_plane: Mapping[str, Any],
    dry_run_receipt_references: Sequence[str] | None,
    result_artifact_references: Sequence[str] | None,
    artifact_reference_overrides: Mapping[str, str],
) -> list[dict[str, Any]]:
    kill_switch = dict(
        kill_switch_validation
        or tiny_live_canary_preflight_contract.get("kill_switch_requirement", {})
        or {}
    )
    rows = [
        _item(
            "disabled_connector_adapter_status",
            "real_wallet_connector_disabled_adapter",
            _override_or_reference(
                artifact_reference_overrides,
                "disabled_connector_adapter_status",
                disabled_connector_audit,
                ("audit_id", "connector_id"),
                "disabled-real-wallet-connector-031:disabled",
            ),
            clean_text(
                disabled_connector_status.get("connector_status")
                or disabled_connector_audit.get("connector_status")
                or "disabled"
            ),
            "Disabled connector still reports refusal-only status and no real execution availability.",
            review_ready=(
                clean_text(
                    disabled_connector_status.get("connector_status")
                    or disabled_connector_audit.get("connector_status")
                    or "disabled"
                )
                == "disabled"
                and (disabled_connector_status.get("real_execution_available") is not True)
                and (disabled_connector_audit.get("real_execution_available") is not True)
            ),
        ),
        _item(
            "secret_boundary_validation_summary",
            "secret_boundary_policy",
            _override_or_reference(
                artifact_reference_overrides,
                "secret_boundary_validation_summary",
                secret_boundary_validation,
                ("validation_id", "status"),
                "static-secret-boundary-validation-031:passed",
            ),
            clean_text(secret_boundary_validation.get("status") or "passed"),
            "Static secret boundary summary is present; no environment secrets are inspected.",
            review_ready=secret_boundary_validation.get("valid") is not False,
        ),
        _item(
            "live_canary_readiness_packet",
            "live_canary_readiness",
            _override_or_reference(
                artifact_reference_overrides,
                "live_canary_readiness_packet",
                live_canary_readiness_packet,
                ("canary_id", "contract_version"),
                "live_canary_readiness_packet:029-reviewable",
            ),
            clean_text(live_canary_readiness_packet.get("canary_status") or "reviewable"),
            "Readiness packet reference is linked for dry-run review only.",
        ),
        _item(
            "canary_replay_acceptance",
            "live_canary_replay_acceptance",
            _override_or_reference(
                artifact_reference_overrides,
                "canary_replay_acceptance",
                canary_replay_acceptance,
                ("matrix_id", "contract_version", "status"),
                "live_canary_acceptance_matrix-030:passed",
            ),
            clean_text(canary_replay_acceptance.get("status") or "passed"),
            "Canary replay acceptance is reviewable and still non-executable.",
            review_ready=clean_text(canary_replay_acceptance.get("status") or "passed") in {"passed", "reviewable"},
        ),
        _item(
            "live_connector_audit_replay",
            "live_connector_audit_replay",
            _override_or_reference(
                artifact_reference_overrides,
                "live_connector_audit_replay",
                live_connector_audit_replay,
                ("replay_id", "status"),
                "live_connector_audit_replay-032:replay_passed",
            ),
            clean_text(live_connector_audit_replay.get("status") or "replay_passed"),
            "Audit replay is deterministic and cannot enable the connector.",
            review_ready=clean_text(live_connector_audit_replay.get("status") or "replay_passed")
            in {"replay_passed", "reviewable", "referenced"},
        ),
        _item(
            "operator_live_approval_packet",
            "operator_live_approval_packet",
            _override_or_reference(
                artifact_reference_overrides,
                "operator_live_approval_packet",
                operator_approval_packet,
                ("packet_id", "operator_packet_status"),
                "operator_live_review_packet-032:operator_review_ready",
            ),
            clean_text(operator_approval_packet.get("operator_packet_status") or "operator_review_ready"),
            "Operator packet remains review-only and is not live approval.",
            review_ready=clean_text(operator_approval_packet.get("operator_packet_status") or "operator_review_ready")
            in {"operator_review_ready", "review_only"},
        ),
        _item(
            "tiny_live_canary_preflight_contract",
            "tiny_live_canary_preflight_contract",
            _override_or_reference(
                artifact_reference_overrides,
                "tiny_live_canary_preflight_contract",
                tiny_live_canary_preflight_contract,
                ("contract_id", "contract_version"),
                "tiny_live_canary_preflight_contract-033:review_only",
            ),
            clean_text(
                dict(tiny_live_canary_preflight_contract.get("validation", {})).get("status")
                or "passed"
            ),
            "Tiny canary preflight contract exists and is non-execution approval only.",
            review_ready=tiny_live_canary_preflight_contract.get("preflight_contract_ready") is not False,
        ),
        _item(
            "tiny_live_canary_manual_runbook",
            "tiny_live_canary_manual_runbook",
            _override_or_reference(
                artifact_reference_overrides,
                "tiny_live_canary_manual_runbook",
                tiny_live_canary_manual_runbook,
                ("runbook_id", "status"),
                "tiny_live_canary_manual_runbook-033:review_only",
            ),
            clean_text(tiny_live_canary_manual_runbook.get("status") or "manual_runbook_ready_for_future_review_only"),
            "Manual runbook exists and has not been operator-executed as live approval.",
            review_ready=tiny_live_canary_manual_runbook.get("manual_runbook_ready") is not False,
        ),
        _item(
            "dry_run_operator_intent_packet",
            "live_canary_operator_intent_packet",
            _override_or_reference(
                artifact_reference_overrides,
                "dry_run_operator_intent_packet",
                operator_intent_packet,
                ("packet_id", "intent_packet_status"),
                "live_canary_operator_intent_packet-034:human_acknowledgement_only",
            ),
            clean_text(operator_intent_packet.get("intent_packet_status") or "operator_intent_packet_review_ready"),
            "Operator intent remains a human acknowledgement artifact only.",
            review_ready=operator_intent_packet.get("operator_intent_is_not_live_approval") is not False,
        ),
        _item(
            "live_connector_blocker_matrix",
            "live_canary_replay_acceptance",
            _override_or_reference(
                artifact_reference_overrides,
                "live_connector_blocker_matrix",
                blocker_matrix,
                ("contract_version", "status"),
                "live_connector_blocker_matrix:all-critical-blockers-unresolved",
            ),
            "all_critical_live_blockers_unresolved"
            if blocker_matrix.get("all_blockers_unresolved") is not False
            else "blockers_not_all_unresolved",
            "Blocker matrix remains unresolved and does not make the canary executable.",
            review_ready=blocker_matrix.get("all_blockers_unresolved") is not False,
        ),
        _item(
            "kill_switch_requirements",
            "tiny_live_canary_preflight_contract",
            _override_or_reference(
                artifact_reference_overrides,
                "kill_switch_requirements",
                kill_switch,
                ("requirement_id", "validation_id", "status"),
                "tiny_live_canary_kill_switch_requirement-033:requirements_defined_not_live_verified",
            ),
            clean_text(kill_switch.get("status") or "requirements_defined_not_live_verified"),
            "Kill-switch requirements are defined but not live-verified.",
            review_ready=kill_switch.get("verified_for_live") is not True,
        ),
        _item(
            "abort_conditions",
            "tiny_live_canary_manual_runbook",
            _override_or_reference(
                artifact_reference_overrides,
                "abort_conditions",
                tiny_live_canary_manual_runbook,
                ("runbook_id", "status"),
                "tiny_live_canary_manual_runbook-033:abort_conditions",
            ),
            ITEM_STATUS_REVIEW_ONLY_NON_EXECUTABLE,
            "Abort conditions are documented for review and do not execute anything.",
        ),
        _item(
            "evidence_capture_checklist",
            "tiny_live_canary_manual_runbook",
            _override_or_reference(
                artifact_reference_overrides,
                "evidence_capture_checklist",
                tiny_live_canary_manual_runbook,
                ("runbook_id", "status"),
                "tiny_live_canary_manual_runbook-033:evidence_capture_checklist",
            ),
            ITEM_STATUS_REVIEW_ONLY_NON_EXECUTABLE,
            "Evidence capture checklist is documented for future review only.",
        ),
        _item(
            "risk_review",
            "paper_strategy_and_risk_review",
            _override_or_reference(
                artifact_reference_overrides,
                "risk_review",
                live_canary_readiness_packet,
                ("risk_decision_id", "contract_version"),
                "risk_review:tiny-live-canary-limits-reviewed",
            ),
            clean_text(preflight_result.get("status") or "reviewable"),
            "Risk review reference is non-advisory and not a live trading signal.",
        ),
        _item(
            "risk_limit_control_plane",
            "risk_limit_control_plane",
            _override_or_reference(
                artifact_reference_overrides,
                "risk_limit_control_plane",
                risk_limit_control_plane,
                ("policy_id", "risk_control_plane_status", "contract_version"),
                "risk_limit_control_plane-037:review_ready_execution_disabled",
            ),
            clean_text(risk_limit_control_plane.get("risk_control_plane_status") or "review_ready"),
            "Risk limit control plane policy is present for review; it does not enable live execution.",
            review_ready=(
                risk_limit_control_plane.get("risk_control_plane_ready") is not False
                and risk_limit_control_plane.get("execution_enabling") is not True
                and risk_limit_control_plane.get("allowed_for_live") is not True
            ),
        ),
    ]
    receipt_refs = _clean_list(dry_run_receipt_references)
    if receipt_refs:
        rows.append(
            _item(
                "dry_run_receipt_references",
                "live_canary_readiness",
                ";".join(receipt_refs),
                ITEM_STATUS_REVIEW_ONLY_NON_EXECUTABLE,
                "Dry-run receipt references are linked when available.",
                required=False,
            )
        )
    result_refs = _clean_list(result_artifact_references)
    if result_refs:
        rows.append(
            _item(
                "result_artifact_references",
                "operator_result_artifacts",
                ";".join(result_refs),
                ITEM_STATUS_REVIEW_ONLY_NON_EXECUTABLE,
                "Result artifact references are linked when available.",
                required=False,
            )
        )
    return rows


def _item(
    evidence_type: str,
    source_component: str,
    reference_path_or_id: str,
    status: str,
    notes: str,
    *,
    required: bool = True,
    present: bool = True,
    review_ready: bool = True,
) -> dict[str, Any]:
    item_status = clean_text(status) or (
        ITEM_STATUS_PRESENT_REVIEW_READY if present and review_ready else ITEM_STATUS_MISSING_REQUIRED_EVIDENCE
    )
    return LiveCanaryReadinessEvidenceItem(
        evidence_id=_stable_id(
            "live-canary-readiness-evidence-item-035",
            {
                "evidence_type": evidence_type,
                "source_component": source_component,
                "reference_path_or_id": reference_path_or_id,
                "required": required,
            },
        ),
        evidence_type=evidence_type,
        source_component=source_component,
        reference_path_or_id=reference_path_or_id,
        status=item_status,
        required_for_future_live_canary_review=required,
        present=present,
        review_ready=review_ready,
        execution_enabling=False,
        notes=notes,
    ).to_dict()


def _reference_from_item(item: Mapping[str, Any]) -> dict[str, Any]:
    return LiveCanaryReadinessEvidenceReference(
        reference_id=_stable_id(
            "live-canary-readiness-evidence-reference-035",
            {
                "evidence_type": item.get("evidence_type"),
                "reference_path_or_id": item.get("reference_path_or_id"),
            },
        ),
        evidence_type=clean_text(item.get("evidence_type")),
        source_component=clean_text(item.get("source_component")),
        reference_path_or_id=clean_text(item.get("reference_path_or_id")),
        description=clean_text(item.get("notes")),
        present=item.get("present") is True,
        review_ready=item.get("review_ready") is True,
        execution_enabling=False,
    ).to_dict()


def _evidence_blockers(blocker_matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    matrix_rows = [
        dict(row)
        for row in blocker_matrix.get("blockers", [])
        if isinstance(row, Mapping) and clean_text(row.get("blocker_id"))
    ]
    rows = matrix_rows if matrix_rows else [dict(row) for row in DEFAULT_035_BLOCKERS]
    return [
        LiveCanaryReadinessEvidenceBlocker(
            blocker_id=clean_text(row.get("blocker_id")),
            blocker_category=clean_text(row.get("blocker_category")) or clean_text(row.get("blocker_name")),
            message=clean_text(row.get("why_it_blocks_live_execution") or row.get("message"))
            or "This blocker remains unresolved and blocks live execution.",
            severity=clean_text(row.get("severity")) or "critical",
            resolution_status=clean_text(row.get("resolution_status")) or "unresolved",
            blocks_canary_execution_now=True,
        ).to_dict()
        for row in rows
    ]


def _blocker_summary(blockers: Sequence[Mapping[str, Any]], blocker_matrix: Mapping[str, Any]) -> dict[str, Any]:
    unresolved = [row for row in blockers if clean_text(row.get("resolution_status")) != "resolved"]
    resolved = [row for row in blockers if clean_text(row.get("resolution_status")) == "resolved"]
    return {
        "blocker_matrix_status": clean_text(blocker_matrix.get("status") or "reviewable"),
        "live_connector_blocker_count": len(blockers),
        "critical_blocker_count": len([row for row in blockers if clean_text(row.get("severity")) == "critical"]),
        "unresolved_live_blocker_count": len(unresolved),
        "resolved_live_blocker_count": len(resolved),
        "all_live_connector_blockers_unresolved": len(resolved) == 0 and bool(unresolved),
        "unresolved_live_blocker_ids": [clean_text(row.get("blocker_id")) for row in unresolved],
        "readiness_evidence_bundle_does_not_resolve_blockers": True,
        "live_execution_available": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
    }


def _missing_required_evidence_types(items: Sequence[Mapping[str, Any]]) -> list[str]:
    ready_types = {
        clean_text(item.get("evidence_type"))
        for item in items
        if item.get("required_for_future_live_canary_review") is True
        and item.get("present") is True
        and item.get("review_ready") is True
        and item.get("execution_enabling") is False
    }
    return [evidence_type for evidence_type in REQUIRED_EVIDENCE_TYPES if evidence_type not in ready_types]


def _bundle_warnings(
    *,
    items: Sequence[Mapping[str, Any]],
    blockers: Sequence[Mapping[str, Any]],
) -> list[str]:
    warnings = []
    if _missing_required_evidence_types(items):
        warnings.append("required evidence is missing or not review-ready")
    if not blockers:
        warnings.append("unresolved live blocker list is missing")
    warnings.append("kill-switch requirements are defined but not live-verified")
    warnings.append("readiness evidence bundle does not approve live execution")
    return warnings


def _secret_boundary_summary(
    secret_boundary_validation: Mapping[str, Any] | None,
    *,
    live_connector_audit_replay: Mapping[str, Any] | None,
    disabled_connector_audit: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    if secret_boundary_validation is not None:
        return dict(secret_boundary_validation)
    replay_summary = dict(live_connector_audit_replay or {}).get("secret_boundary_validation_summary")
    if isinstance(replay_summary, Mapping) and replay_summary:
        return dict(replay_summary)
    audit_summary = disabled_connector_audit.get("audit_secret_boundary_validation")
    if isinstance(audit_summary, Mapping) and audit_summary:
        return dict(audit_summary)
    return {
        "contract_version": "pmbot_static_secret_boundary_validation.v1",
        "validation_id": "static-secret-boundary-validation-035-default",
        "artifact_type": "readiness_evidence_bundle_default",
        "generated_at": generated_at,
        "valid": True,
        "status": "passed",
        "static_validation_only": True,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
    }


def _override_or_reference(
    overrides: Mapping[str, str],
    evidence_type: str,
    artifact: Mapping[str, Any],
    fields: Sequence[str],
    fallback: str,
) -> str:
    override = clean_text(overrides.get(evidence_type))
    if override:
        return override
    for field in fields:
        text = clean_text(artifact.get(field))
        if text:
            return text
    return fallback


def _current_execution_posture() -> dict[str, Any]:
    value = {
        "posture": "review_only_live_execution_impossible",
        "generated_for_review_only": True,
        "readiness_evidence_bundle_is_not_live_approval": True,
        "operator_intent_remains_human_acknowledgement_only": True,
    }
    value.update(_evidence_safety_flags())
    return value


def _evidence_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "passive_artifact_only": True,
        "manual_review_only": True,
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "execution_enabling": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "real_wallet_integration_added": False,
        "real_wallet_access_performed": False,
        "private_key_or_mnemonic_handling_added": False,
        "cryptographic_signing_added": False,
        "cryptographic_signing_performed": False,
        "wallet_signing_added": False,
        "wallet_signing_performed": False,
        "transaction_signing_added": False,
        "transaction_signing_performed": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "authenticated_endpoint_added": False,
        "authenticated_endpoint_call_performed": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "real_execution_available": False,
        "live_execution_approved": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "canary_executable_now": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [clean_text(item) for item in value if clean_text(item)]
    text = clean_text(value)
    return [text] if text else []


def _dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
