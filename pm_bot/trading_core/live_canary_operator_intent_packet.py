from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.live_connector_audit_replay import REPLAY_STATUS_PASSED
from pm_bot.trading_core.operator_live_approval_packet import OPERATOR_REVIEW_READY
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_operator_intent_acknowledgement,
    validate_secret_boundary_operator_intent_evidence_reference,
    validate_secret_boundary_operator_intent_packet,
)

TASK_ID = "ORCH-PMBOT-TRADING-MVP-034-LIVE-CANARY-DRY-RUN-OPERATOR-SIGNED-INTENT-PACKET"

LIVE_CANARY_OPERATOR_INTENT_PACKET_CONTRACT = "pmbot_live_canary_operator_intent_packet.v1"
LIVE_CANARY_OPERATOR_INTENT_ACKNOWLEDGEMENT_CONTRACT = (
    "pmbot_live_canary_operator_intent_acknowledgement.v1"
)
LIVE_CANARY_OPERATOR_INTENT_CHECKLIST_ITEM_CONTRACT = (
    "pmbot_live_canary_operator_intent_checklist_item.v1"
)
LIVE_CANARY_OPERATOR_INTENT_BLOCKER_CONTRACT = "pmbot_live_canary_operator_intent_blocker.v1"
LIVE_CANARY_OPERATOR_INTENT_EVIDENCE_REFERENCE_CONTRACT = (
    "pmbot_live_canary_operator_intent_evidence_reference.v1"
)
LIVE_CANARY_OPERATOR_INTENT_VALIDATION_CONTRACT = (
    "pmbot_live_canary_operator_intent_validation.v1"
)

INTENT_PACKET_STATUS_REVIEW_READY = "operator_intent_packet_review_ready"
INTENT_PACKET_STATUS_BLOCKED = "operator_intent_packet_blocked"

VALIDATION_STATUS_DRY_RUN_VALID = "intent_packet_valid_for_dry_run_review"
VALIDATION_STATUS_MISSING_REQUIRED_ARTIFACTS = "missing_required_artifacts"
VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT = "missing_operator_acknowledgement"
VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL = "forbidden_execution_approval_detected"
VALIDATION_STATUS_FORBIDDEN_SIGNING_FIELD = "forbidden_signing_field_detected"
VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_ACKNOWLEDGED = "unresolved_blockers_not_acknowledged"
VALIDATION_STATUS_SECRET_BOUNDARY_FAILED = "secret_boundary_failed"
VALIDATION_STATUS_AUDIT_REPLAY_NOT_REVIEWABLE = "audit_replay_not_reviewable"

NON_EXECUTION_STATEMENTS = (
    "This operator intent packet is a dry-run acknowledgement only.",
    "This packet does not authorize live execution.",
    "This packet does not authorize wallet access, signing, order placement, or authenticated endpoint usage.",
    "Real execution remains unavailable in this build.",
)

DEFAULT_OPERATOR_ACKNOWLEDGEMENT_TEXT = (
    "Dry-run operator intent acknowledgement placeholder: the operator reviewed the referenced artifacts "
    "for future canary preparation only, and this does not authorize live execution."
)
DEFAULT_HUMAN_SIGNED_ACKNOWLEDGEMENT_TEXT = (
    "Human acknowledgement only; no cryptographic signing, wallet signing, transaction signing, "
    "or order signing is requested or performed."
)

REQUIRED_REFERENCE_FIELDS = (
    "future_canary_shape_reference",
    "tiny_live_canary_preflight_contract_reference",
    "manual_runbook_reference",
    "operator_approval_packet_reference",
    "live_connector_audit_replay_reference",
    "disabled_connector_audit_reference",
    "secret_boundary_validation_reference",
    "disabled_connector_audit_reference",
    "blocker_matrix_reference",
    "risk_review_reference",
)

DEFAULT_UNRESOLVED_BLOCKER_IDS = (
    "PMBOT-LIVE-BLOCKER-025",
    "PMBOT-LIVE-BLOCKER-026",
    "PMBOT-LIVE-BLOCKER-027",
    "PMBOT-LIVE-BLOCKER-028",
    "PMBOT-LIVE-BLOCKER-029",
    "PMBOT-LIVE-BLOCKER-030",
    "PMBOT-LIVE-BLOCKER-031",
)


@dataclass(frozen=True)
class LiveCanaryOperatorIntentEvidenceReference:
    reference_id: str
    artifact_type: str
    artifact_reference: str
    description: str
    reviewed: bool = True
    required: bool = True
    review_status: str = "reviewed_for_dry_run_intent_only"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_OPERATOR_INTENT_EVIDENCE_REFERENCE_CONTRACT
        value.update(_intent_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryOperatorIntentChecklistItem:
    item_id: str
    title: str
    acknowledgement_text: str
    acknowledged: bool = True
    required: bool = True
    status: str = "acknowledged_for_dry_run_review_only"
    blocks_live_execution_until_future_task: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_OPERATOR_INTENT_CHECKLIST_ITEM_CONTRACT
        value.update(_intent_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryOperatorIntentBlocker:
    blocker_id: str
    blocker_category: str
    message: str
    severity: str = "critical"
    resolution_status: str = "unresolved"
    acknowledged_by_operator_intent_review: bool = True
    blocks_canary_execution_now: bool = True

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_OPERATOR_INTENT_BLOCKER_CONTRACT
        value.update(_intent_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryOperatorIntentAcknowledgement:
    operator_identifier: str
    operator_acknowledged_at: str
    operator_acknowledgement_text: str
    human_signed_acknowledgement_text: str
    operator_signed_intent_acknowledgement: bool = True
    operator_signed_intent_is_human_acknowledgement_only: bool = True
    cryptographic_signing_performed: bool = False
    wallet_signing_performed: bool = False
    transaction_signing_performed: bool = False
    order_signing_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_OPERATOR_INTENT_ACKNOWLEDGEMENT_CONTRACT
        value.update(_intent_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryOperatorIntentValidationResult:
    validation_id: str
    valid: bool
    status: str
    statuses: tuple[str, ...]
    errors: tuple[str, ...]
    missing_required_artifacts: tuple[str, ...]
    forbidden_field_paths: tuple[str, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_OPERATOR_INTENT_VALIDATION_CONTRACT
        value["statuses"] = list(self.statuses)
        value["errors"] = list(self.errors)
        value["missing_required_artifacts"] = list(self.missing_required_artifacts)
        value["forbidden_field_paths"] = list(self.forbidden_field_paths)
        value["operator_intent_packet_review_ready"] = self.valid
        value["operator_intent_is_not_live_approval"] = True
        value.update(_intent_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCanaryOperatorIntentPacket:
    packet_id: str
    task_id: str
    intent_packet_status: str
    future_canary_shape_reference: str
    tiny_live_canary_preflight_contract_reference: str
    manual_runbook_reference: str
    operator_approval_packet_reference: str
    live_connector_audit_replay_reference: str
    disabled_connector_audit_reference: str
    secret_boundary_validation_reference: str
    blocker_matrix_reference: str
    risk_review_reference: str
    audit_replay_review_status: str
    operator_approval_packet_status: str
    secret_boundary_validation_summary: Mapping[str, Any]
    acknowledgement: Mapping[str, Any]
    evidence_references: tuple[Mapping[str, Any], ...]
    checklist: tuple[Mapping[str, Any], ...]
    blockers: tuple[Mapping[str, Any], ...]
    acknowledged_unresolved_blocker_ids: tuple[str, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CANARY_OPERATOR_INTENT_PACKET_CONTRACT
        value["schema_version"] = "034.v1"
        value["task_id"] = self.task_id
        value["non_execution_statements"] = list(NON_EXECUTION_STATEMENTS)
        value["operator_acknowledgement_text"] = clean_text(
            self.acknowledgement.get("operator_acknowledgement_text")
        )
        value["operator_acknowledged_at"] = clean_text(self.acknowledgement.get("operator_acknowledged_at"))
        value["operator_identifier"] = clean_text(self.acknowledgement.get("operator_identifier"))
        value["human_signed_acknowledgement_text"] = clean_text(
            self.acknowledgement.get("human_signed_acknowledgement_text")
        )
        value["operator_signed_intent_acknowledgement"] = (
            self.acknowledgement.get("operator_signed_intent_acknowledgement") is True
        )
        value["operator_signed_intent_is_human_acknowledgement_only"] = (
            self.acknowledgement.get("operator_signed_intent_is_human_acknowledgement_only") is True
        )
        value["secret_boundary_validation_summary"] = dict(self.secret_boundary_validation_summary)
        value["evidence_references"] = [dict(row) for row in self.evidence_references]
        value["checklist"] = [dict(row) for row in self.checklist]
        value["blockers"] = [dict(row) for row in self.blockers]
        value["acknowledged_unresolved_blocker_ids"] = list(self.acknowledged_unresolved_blocker_ids)
        value["unresolved_blocker_ids"] = list(self.acknowledged_unresolved_blocker_ids)
        value["unresolved_live_blocker_count"] = len(self.acknowledged_unresolved_blocker_ids)
        value["unresolved_blockers_acknowledged"] = bool(self.acknowledged_unresolved_blocker_ids)
        value["required_artifact_references_present"] = True
        value["operator_intent_packet_ready"] = self.intent_packet_status == INTENT_PACKET_STATUS_REVIEW_READY
        value["operator_acknowledgement_model_ready"] = True
        value["dry_run_intent_validation_ready"] = True
        value["operator_intent_packet_review_ready"] = (
            self.intent_packet_status == INTENT_PACKET_STATUS_REVIEW_READY
        )
        value["operator_intent_is_not_live_approval"] = True
        value["operator_review_is_not_live_approval"] = True
        value["operator_intent_packet_is_dry_run_acknowledgement_only"] = True
        value["manual_runbook_acknowledged"] = True
        value["kill_switch_requirements_acknowledged"] = True
        value["kill_switch_verified_for_live"] = False
        value["abort_conditions_acknowledged"] = True
        value["evidence_capture_acknowledged"] = True
        value["max_exposure_acknowledged"] = True
        value["manual_only_acknowledged"] = True
        value["explicit_non_execution_acknowledged"] = True
        value["live_connector_enabled"] = False
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["canary_executable_now"] = False
        value.update(_intent_safety_flags())
        value["safety_summary"] = trading_core_safety_summary()
        return value


def build_live_canary_operator_intent_packet(
    *,
    future_canary_shape_reference: str = "",
    tiny_live_canary_preflight_contract: Mapping[str, Any] | None = None,
    tiny_live_canary_preflight_contract_reference: str = "",
    tiny_live_canary_manual_runbook: Mapping[str, Any] | None = None,
    tiny_live_canary_manual_runbook_reference: str = "",
    operator_approval_packet: Mapping[str, Any] | None = None,
    operator_approval_packet_reference: str = "",
    live_connector_audit_replay: Mapping[str, Any] | None = None,
    live_connector_audit_replay_reference: str = "",
    disabled_connector_audit: Mapping[str, Any] | None = None,
    disabled_connector_audit_reference: str = "",
    secret_boundary_validation: Mapping[str, Any] | None = None,
    secret_boundary_validation_reference: str = "",
    blocker_matrix: Mapping[str, Any] | None = None,
    blocker_matrix_reference: str = "",
    risk_review_reference: str = "",
    acknowledged_unresolved_blocker_ids: Sequence[str] | None = None,
    operator_acknowledgement_text: str = DEFAULT_OPERATOR_ACKNOWLEDGEMENT_TEXT,
    human_signed_acknowledgement_text: str = DEFAULT_HUMAN_SIGNED_ACKNOWLEDGEMENT_TEXT,
    operator_acknowledged_at: str = "<operator_acknowledged_at>",
    operator_identifier: str = "<operator_identifier>",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    preflight_contract = dict(tiny_live_canary_preflight_contract or {})
    runbook = dict(tiny_live_canary_manual_runbook or {})
    operator_packet = dict(operator_approval_packet or {})
    audit_replay = dict(live_connector_audit_replay or {})
    disabled_audit = dict(disabled_connector_audit or {})
    secret_summary = _secret_boundary_summary(
        secret_boundary_validation,
        audit_replay=audit_replay,
        generated_at=generated_at,
    )
    blocker_matrix_value = dict(blocker_matrix or {})
    unresolved_ids = tuple(
        _clean_list(
            acknowledged_unresolved_blocker_ids
            or blocker_matrix_value.get("unresolved_blockers")
            or DEFAULT_UNRESOLVED_BLOCKER_IDS
        )
    )
    blockers = tuple(
        _intent_blockers(
            blocker_matrix=blocker_matrix_value,
            acknowledged_unresolved_blocker_ids=unresolved_ids,
        )
    )
    acknowledgement = LiveCanaryOperatorIntentAcknowledgement(
        operator_identifier=clean_text(operator_identifier) or "<operator_identifier>",
        operator_acknowledged_at=clean_text(operator_acknowledged_at) or "<operator_acknowledged_at>",
        operator_acknowledgement_text=clean_text(operator_acknowledgement_text),
        human_signed_acknowledgement_text=clean_text(human_signed_acknowledgement_text),
    ).to_dict()
    evidence_references = tuple(
        _evidence_references(
            future_canary_shape_reference=(
                clean_text(future_canary_shape_reference)
                or clean_text(dict(preflight_contract.get("limit_policy", {})).get("future_canary_shape"))
                or "tiny-live-canary-shape-033:one-manual-market-one-manual-order-sized-action"
            ),
            tiny_live_canary_preflight_contract_reference=(
                clean_text(tiny_live_canary_preflight_contract_reference)
                or _artifact_reference(
                    preflight_contract,
                    ("contract_id",),
                    "tiny_live_canary_preflight_contract:pending-local-review",
                )
            ),
            manual_runbook_reference=(
                clean_text(tiny_live_canary_manual_runbook_reference)
                or _artifact_reference(runbook, ("runbook_id",), "tiny_live_canary_manual_runbook:pending-local-review")
            ),
            operator_approval_packet_reference=(
                clean_text(operator_approval_packet_reference)
                or _artifact_reference(operator_packet, ("packet_id",), "operator_live_review_packet:pending-local-review")
            ),
            live_connector_audit_replay_reference=(
                clean_text(live_connector_audit_replay_reference)
                or _artifact_reference(audit_replay, ("replay_id",), "live_connector_audit_replay:pending-local-review")
            ),
            disabled_connector_audit_reference=(
                clean_text(disabled_connector_audit_reference)
                or _artifact_reference(disabled_audit, ("audit_id",), "disabled_connector_audit:pending-local-review")
            ),
            secret_boundary_validation_reference=(
                clean_text(secret_boundary_validation_reference)
                or _artifact_reference(
                    secret_summary,
                    ("validation_id", "status"),
                    "secret_boundary_validation:static-review-passed",
                )
            ),
            blocker_matrix_reference=(
                clean_text(blocker_matrix_reference)
                or _artifact_reference(
                    blocker_matrix_value,
                    ("contract_version", "status"),
                    "live_connector_blocker_matrix:all-critical-blockers-unresolved",
                )
            ),
            risk_review_reference=clean_text(risk_review_reference) or "risk_review:tiny-live-canary-limits-reviewed",
        )
    )
    checklist = tuple(_checklist_items())
    packet_id = _stable_id(
        "live-canary-operator-intent-packet-034",
        {
            "task_id": TASK_ID,
            "evidence_reference_ids": [row.get("reference_id") for row in evidence_references],
            "evidence_artifact_references": [row.get("artifact_reference") for row in evidence_references],
            "acknowledged_unresolved_blocker_ids": list(unresolved_ids),
            "operator_acknowledgement_text": clean_text(operator_acknowledgement_text),
            "human_signed_acknowledgement_text": clean_text(human_signed_acknowledgement_text),
        },
    )
    packet = LiveCanaryOperatorIntentPacket(
        packet_id=packet_id,
        task_id=TASK_ID,
        intent_packet_status=INTENT_PACKET_STATUS_REVIEW_READY,
        future_canary_shape_reference=_reference_value(evidence_references, "future_canary_shape"),
        tiny_live_canary_preflight_contract_reference=_reference_value(
            evidence_references,
            "tiny_live_canary_preflight_contract",
        ),
        manual_runbook_reference=_reference_value(evidence_references, "manual_runbook"),
        operator_approval_packet_reference=_reference_value(evidence_references, "operator_approval_packet"),
        live_connector_audit_replay_reference=_reference_value(evidence_references, "live_connector_audit_replay"),
        disabled_connector_audit_reference=_reference_value(evidence_references, "disabled_connector_audit"),
        secret_boundary_validation_reference=_reference_value(evidence_references, "secret_boundary_validation"),
        blocker_matrix_reference=_reference_value(evidence_references, "blocker_matrix"),
        risk_review_reference=_reference_value(evidence_references, "risk_review"),
        audit_replay_review_status=clean_text(audit_replay.get("status")) or REPLAY_STATUS_PASSED,
        operator_approval_packet_status=clean_text(operator_packet.get("operator_packet_status")) or OPERATOR_REVIEW_READY,
        secret_boundary_validation_summary=secret_summary,
        acknowledgement=acknowledgement,
        evidence_references=evidence_references,
        checklist=checklist,
        blockers=blockers,
        acknowledged_unresolved_blocker_ids=unresolved_ids,
        generated_at=generated_at,
    ).to_dict()
    validation = validate_live_canary_operator_intent_packet(packet, generated_at=generated_at)
    packet["validation"] = validation
    if validation.get("valid") is not True:
        packet["intent_packet_status"] = INTENT_PACKET_STATUS_BLOCKED
        packet["operator_intent_packet_review_ready"] = False
    return packet


def validate_live_canary_operator_intent_packet(
    packet: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    statuses: list[str] = []
    missing_required = [
        field for field in REQUIRED_REFERENCE_FIELDS if not clean_text(packet.get(field))
    ]
    if packet.get("contract_version") != LIVE_CANARY_OPERATOR_INTENT_PACKET_CONTRACT:
        errors.append(f"contract_version must be {LIVE_CANARY_OPERATOR_INTENT_PACKET_CONTRACT}")
        statuses.append(VALIDATION_STATUS_MISSING_REQUIRED_ARTIFACTS)
    if missing_required:
        errors.append(f"missing required artifact references: {', '.join(missing_required)}")
        statuses.append(VALIDATION_STATUS_MISSING_REQUIRED_ARTIFACTS)
    evidence = [row for row in packet.get("evidence_references", []) if isinstance(row, Mapping)]
    evidence_types = {clean_text(row.get("artifact_type")) for row in evidence}
    for artifact_type in (
        "future_canary_shape",
        "tiny_live_canary_preflight_contract",
        "manual_runbook",
        "operator_approval_packet",
        "live_connector_audit_replay",
        "disabled_connector_audit",
        "secret_boundary_validation",
        "blocker_matrix",
        "risk_review",
    ):
        if artifact_type not in evidence_types:
            errors.append(f"missing evidence reference for {artifact_type}")
            statuses.append(VALIDATION_STATUS_MISSING_REQUIRED_ARTIFACTS)
    for index, reference in enumerate(evidence):
        reference_validation = validate_secret_boundary_operator_intent_evidence_reference(
            dict(reference),
            generated_at=generated_at,
        )
        if reference_validation.get("valid") is not True:
            errors.append(f"evidence_references[{index}] violates static secret boundary")
            statuses.append(VALIDATION_STATUS_SECRET_BOUNDARY_FAILED)

    acknowledgement = dict(packet.get("acknowledgement", {}))
    acknowledgement_validation = validate_secret_boundary_operator_intent_acknowledgement(
        acknowledgement,
        generated_at=generated_at,
    )
    if not clean_text(packet.get("operator_acknowledgement_text")):
        errors.append("operator_acknowledgement_text must be present")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)
    if not clean_text(packet.get("human_signed_acknowledgement_text")):
        errors.append("human_signed_acknowledgement_text must explain human acknowledgement only")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)
    if packet.get("operator_signed_intent_acknowledgement") is not True:
        errors.append("operator_signed_intent_acknowledgement must be true for dry-run review")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)
    if packet.get("operator_signed_intent_is_human_acknowledgement_only") is not True:
        errors.append("operator signed intent must be marked as human acknowledgement only")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_SIGNING_FIELD)
    if acknowledgement_validation.get("valid") is not True:
        errors.append("operator acknowledgement violates static secret boundary")
        statuses.append(VALIDATION_STATUS_SECRET_BOUNDARY_FAILED)

    for field in (
        "live_execution_approved",
        "real_execution_available",
        "canary_executable_now",
        "live_connector_enabled",
        "live_execution_allowed",
        "live_execution_performed",
        "real_wallet_access_performed",
        "cryptographic_signing_performed",
        "real_order_placement_performed",
        "authenticated_endpoint_call_performed",
        "external_api_calls_performed",
    ):
        if packet.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
    if packet.get("operator_intent_is_not_live_approval") is not True:
        errors.append("operator_intent_is_not_live_approval must be true")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
    if packet.get("manual_runbook_acknowledged") is not True:
        errors.append("manual runbook must be acknowledged")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)
    if packet.get("kill_switch_requirements_acknowledged") is not True:
        errors.append("kill-switch requirements must be acknowledged")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)
    if packet.get("kill_switch_verified_for_live") is not False:
        errors.append("kill_switch_verified_for_live must remain false")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)
    if packet.get("abort_conditions_acknowledged") is not True:
        errors.append("abort conditions must be acknowledged")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)
    if packet.get("evidence_capture_acknowledged") is not True:
        errors.append("evidence capture requirements must be acknowledged")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)
    if packet.get("max_exposure_acknowledged") is not True:
        errors.append("max exposure limits must be acknowledged")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)
    if packet.get("manual_only_acknowledged") is not True:
        errors.append("manual-only process must be acknowledged")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)
    if packet.get("explicit_non_execution_acknowledged") is not True:
        errors.append("explicit non-execution statement must be acknowledged")
        statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)

    statement_text = json.dumps(packet.get("non_execution_statements", []), sort_keys=True)
    for statement in NON_EXECUTION_STATEMENTS:
        if statement not in statement_text:
            errors.append(f"missing non-execution statement: {statement}")
            statuses.append(VALIDATION_STATUS_MISSING_OPERATOR_ACKNOWLEDGEMENT)

    unresolved_ids = _clean_list(packet.get("acknowledged_unresolved_blocker_ids") or packet.get("unresolved_blocker_ids"))
    if not unresolved_ids or packet.get("unresolved_blockers_acknowledged") is not True:
        errors.append("unresolved blockers must be present and acknowledged")
        statuses.append(VALIDATION_STATUS_UNRESOLVED_BLOCKERS_NOT_ACKNOWLEDGED)

    secret_summary = dict(packet.get("secret_boundary_validation_summary", {}))
    if secret_summary.get("valid") is not True:
        errors.append("secret boundary validation summary must pass")
        statuses.append(VALIDATION_STATUS_SECRET_BOUNDARY_FAILED)
    if clean_text(packet.get("audit_replay_review_status")) not in {
        REPLAY_STATUS_PASSED,
        "reviewable",
        "reviewed",
        "referenced",
    }:
        errors.append("audit replay must be acceptable for dry-run review")
        statuses.append(VALIDATION_STATUS_AUDIT_REPLAY_NOT_REVIEWABLE)
    if clean_text(packet.get("operator_approval_packet_status")) not in {
        OPERATOR_REVIEW_READY,
        "operator_review_blocked",
        "review_only",
    }:
        errors.append("operator approval packet status must be review-only")
        statuses.append(VALIDATION_STATUS_FORBIDDEN_EXECUTION_APPROVAL)

    packet_secret_validation = validate_secret_boundary_operator_intent_packet(
        packet,
        generated_at=generated_at,
    )
    forbidden_paths = _clean_list(packet_secret_validation.get("forbidden_secret_field_paths"))
    forbidden_paths.extend(_clean_list(packet_secret_validation.get("forbidden_operator_intent_field_paths")))
    if packet_secret_validation.get("valid") is not True:
        errors.append("operator intent packet violates static secret boundary")
        if forbidden_paths:
            statuses.append(VALIDATION_STATUS_FORBIDDEN_SIGNING_FIELD)
        else:
            statuses.append(VALIDATION_STATUS_SECRET_BOUNDARY_FAILED)

    statuses = _dedupe(statuses)
    valid = not errors
    if valid:
        statuses = [VALIDATION_STATUS_DRY_RUN_VALID]
    status = statuses[0] if statuses else VALIDATION_STATUS_DRY_RUN_VALID
    return LiveCanaryOperatorIntentValidationResult(
        validation_id=_stable_id(
            "live-canary-operator-intent-validation-034",
            {
                "packet_id": packet.get("packet_id"),
                "errors": errors,
                "forbidden_field_paths": forbidden_paths,
                "missing_required_artifacts": missing_required,
            },
        ),
        valid=valid,
        status=status,
        statuses=tuple(statuses),
        errors=tuple(errors),
        missing_required_artifacts=tuple(missing_required),
        forbidden_field_paths=tuple(_dedupe(forbidden_paths)),
        generated_at=generated_at,
    ).to_dict()


def summarize_live_canary_operator_intent_packet(
    packet: Mapping[str, Any],
    *,
    latest_operator_intent_packet_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    validation = validate_live_canary_operator_intent_packet(packet, generated_at=generated_at)
    return {
        "operator_intent_packet_status": clean_text(packet.get("intent_packet_status")),
        "operator_intent_packet_review_ready": validation.get("valid") is True,
        "operator_intent_is_not_live_approval": True,
        "operator_signed_intent_is_human_acknowledgement_only": (
            packet.get("operator_signed_intent_is_human_acknowledgement_only") is True
        ),
        "validation_status": clean_text(validation.get("status")),
        "validation_errors": list(validation.get("errors", [])),
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "unresolved_live_blocker_count": int(packet.get("unresolved_live_blocker_count", 0) or 0),
        "kill_switch_verified_for_live": False,
        "latest_operator_intent_packet_path": clean_text(latest_operator_intent_packet_path),
    }


def render_live_canary_operator_intent_packet_markdown(packet: Mapping[str, Any]) -> str:
    summary = summarize_live_canary_operator_intent_packet(packet)
    lines = [
        "# PMBOT Live Canary Dry-Run Operator Intent Packet",
        "",
        f"- Packet: `{packet.get('packet_id')}`",
        f"- Status: `{packet.get('intent_packet_status')}`",
        f"- Review ready: `{str(summary.get('operator_intent_packet_review_ready')).lower()}`",
        f"- Human acknowledgement only: `{str(packet.get('operator_signed_intent_is_human_acknowledgement_only')).lower()}`",
        f"- Live execution approved: `{str(packet.get('live_execution_approved')).lower()}`",
        f"- Real execution available: `{str(packet.get('real_execution_available')).lower()}`",
        f"- Canary executable now: `{str(packet.get('canary_executable_now')).lower()}`",
        "",
        "## Non-Execution Statements",
        "",
        *bullet_lines(str(item) for item in packet.get("non_execution_statements", [])),
        "",
        "## Evidence References",
        "",
        *bullet_lines(
            f"`{row.get('artifact_type')}` `{row.get('artifact_reference')}`"
            for row in packet.get("evidence_references", [])
            if isinstance(row, Mapping)
        ),
        "",
        "## Acknowledged Blockers",
        "",
        *bullet_lines(str(item) for item in packet.get("acknowledged_unresolved_blocker_ids", [])),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _evidence_references(
    *,
    future_canary_shape_reference: str,
    tiny_live_canary_preflight_contract_reference: str,
    manual_runbook_reference: str,
    operator_approval_packet_reference: str,
    live_connector_audit_replay_reference: str,
    disabled_connector_audit_reference: str,
    secret_boundary_validation_reference: str,
    blocker_matrix_reference: str,
    risk_review_reference: str,
) -> list[dict[str, Any]]:
    rows = [
        (
            "future_canary_shape",
            future_canary_shape_reference,
            "Future tiny canary shape reviewed as one manual market and one manual order-sized action.",
        ),
        (
            "tiny_live_canary_preflight_contract",
            tiny_live_canary_preflight_contract_reference,
            "Tiny live canary preflight contract reviewed as non-executable.",
        ),
        ("manual_runbook", manual_runbook_reference, "Manual runbook reviewed and acknowledged."),
        (
            "operator_approval_packet",
            operator_approval_packet_reference,
            "Operator live review packet reviewed as review-only and not live approval.",
        ),
        (
            "live_connector_audit_replay",
            live_connector_audit_replay_reference,
            "Live connector audit replay reviewed as deterministic and non-executable.",
        ),
        (
            "disabled_connector_audit",
            disabled_connector_audit_reference,
            "Disabled connector audit reviewed as refusal-only.",
        ),
        (
            "secret_boundary_validation",
            secret_boundary_validation_reference,
            "Static secret boundary validation reviewed without reading real secrets.",
        ),
        ("blocker_matrix", blocker_matrix_reference, "Unresolved critical live blockers reviewed."),
        ("risk_review", risk_review_reference, "Tiny exposure limits and risk review acknowledged."),
    ]
    return [
        LiveCanaryOperatorIntentEvidenceReference(
            reference_id=_stable_id(
                "live-canary-operator-intent-evidence-034",
                {"artifact_type": artifact_type, "artifact_reference": reference},
            ),
            artifact_type=artifact_type,
            artifact_reference=reference,
            description=description,
        ).to_dict()
        for artifact_type, reference, description in rows
    ]


def _checklist_items() -> list[dict[str, Any]]:
    rows = [
        (
            "acknowledge_dry_run_only",
            "Acknowledge dry-run-only scope.",
            NON_EXECUTION_STATEMENTS[0],
        ),
        (
            "acknowledge_no_live_authorization",
            "Acknowledge this is not live authorization.",
            NON_EXECUTION_STATEMENTS[1],
        ),
        (
            "acknowledge_no_wallet_signing_order_or_auth",
            "Acknowledge no wallet access, signing, order placement, or authenticated endpoint usage.",
            NON_EXECUTION_STATEMENTS[2],
        ),
        (
            "acknowledge_real_execution_unavailable",
            "Acknowledge real execution remains unavailable.",
            NON_EXECUTION_STATEMENTS[3],
        ),
        (
            "acknowledge_kill_switch_requirements_not_live_verified",
            "Acknowledge kill-switch requirements are reviewed but not live-verified.",
            "Kill-switch requirements are acknowledged for future review only and are not live-verified.",
        ),
        (
            "acknowledge_abort_conditions",
            "Acknowledge abort conditions.",
            "Abort review on missing artifacts, live capability, secret requests, or autonomous execution paths.",
        ),
        (
            "acknowledge_evidence_requirements",
            "Acknowledge evidence capture requirements.",
            "Evidence references must be captured before any separate future gated task.",
        ),
        (
            "acknowledge_max_exposure_limits",
            "Acknowledge tiny max exposure limits.",
            "Max exposure limits are reviewed as placeholders only and do not enable execution.",
        ),
    ]
    return [
        LiveCanaryOperatorIntentChecklistItem(
            item_id=item_id,
            title=title,
            acknowledgement_text=text,
        ).to_dict()
        for item_id, title, text in rows
    ]


def _intent_blockers(
    *,
    blocker_matrix: Mapping[str, Any],
    acknowledged_unresolved_blocker_ids: Sequence[str],
) -> list[dict[str, Any]]:
    matrix_rows = [
        row
        for row in blocker_matrix.get("blockers", [])
        if isinstance(row, Mapping) and clean_text(row.get("blocker_id")) in set(acknowledged_unresolved_blocker_ids)
    ]
    if not matrix_rows:
        matrix_rows = [
            {
                "blocker_id": blocker_id,
                "blocker_category": "operator_intent_packet_dry_run_only",
                "why_it_blocks_live_execution": "Operator intent is a dry-run acknowledgement only.",
            }
            for blocker_id in acknowledged_unresolved_blocker_ids
        ]
    return [
        LiveCanaryOperatorIntentBlocker(
            blocker_id=clean_text(row.get("blocker_id")),
            blocker_category=clean_text(row.get("blocker_category")) or "live_canary_blocker_unresolved",
            message=clean_text(row.get("why_it_blocks_live_execution"))
            or "This blocker remains unresolved and blocks live execution.",
            severity=clean_text(row.get("severity")) or "critical",
            resolution_status=clean_text(row.get("resolution_status")) or "unresolved",
        ).to_dict()
        for row in matrix_rows
    ]


def _secret_boundary_summary(
    secret_boundary_validation: Mapping[str, Any] | None,
    *,
    audit_replay: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    if secret_boundary_validation is not None:
        return dict(secret_boundary_validation)
    audit_summary = audit_replay.get("secret_boundary_validation_summary")
    if isinstance(audit_summary, Mapping) and audit_summary:
        return dict(audit_summary)
    return {
        "contract_version": "pmbot_static_secret_boundary_validation.v1",
        "validation_id": _stable_id(
            "static-secret-boundary-validation-034-default",
            {"artifact_type": "operator_intent_packet_default"},
        ),
        "artifact_type": "operator_intent_packet_default",
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


def _reference_value(references: Sequence[Mapping[str, Any]], artifact_type: str) -> str:
    for reference in references:
        if clean_text(reference.get("artifact_type")) == artifact_type:
            return clean_text(reference.get("artifact_reference"))
    return ""


def _artifact_reference(artifact: Mapping[str, Any], fields: Sequence[str], fallback: str) -> str:
    for field in fields:
        text = clean_text(artifact.get(field))
        if text:
            return text
    return fallback


def _intent_safety_flags() -> dict[str, Any]:
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
        "wallet_signing_performed": False,
        "transaction_signing_performed": False,
        "order_signing_performed": False,
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
