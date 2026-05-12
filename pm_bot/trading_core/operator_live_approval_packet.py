from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.live_connector_audit_replay import REPLAY_STATUS_PASSED
from pm_bot.trading_core.real_wallet_connector_disabled_adapter import CONNECTOR_STATUS_DISABLED
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_operator_approval_packet,
    validate_secret_boundary_operator_checklist_item,
)

OPERATOR_LIVE_APPROVAL_CHECKLIST_ITEM_CONTRACT = "pmbot_operator_live_review_checklist_item.v1"
OPERATOR_LIVE_APPROVAL_PACKET_CONTRACT = "pmbot_operator_live_review_packet.v1"
OPERATOR_LIVE_APPROVAL_PACKET_RESULT_CONTRACT = "pmbot_operator_live_review_packet_result.v1"
OPERATOR_LIVE_APPROVAL_PACKET_VALIDATION_CONTRACT = "pmbot_operator_live_review_packet_validation.v1"

OPERATOR_REVIEW_READY = "operator_review_ready"
OPERATOR_REVIEW_BLOCKED = "operator_review_blocked"
NON_APPROVAL_STATEMENT = "This packet is for operator review only and does not authorize live execution."


@dataclass(frozen=True)
class OperatorLiveApprovalChecklistItem:
    item_id: str
    title: str
    evidence_reference: str
    required: bool = True
    status: str = "pending_operator_review"
    operator_confirmation_required: bool = True
    live_execution_approval_item: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_LIVE_APPROVAL_CHECKLIST_ITEM_CONTRACT
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["local_artifact_only"] = True
        return value


@dataclass(frozen=True)
class OperatorLiveApprovalPacket:
    packet_id: str
    operator_packet_status: str
    disabled_connector_status: Mapping[str, Any]
    blocker_matrix_summary: Mapping[str, Any]
    unresolved_blocker_ids: tuple[str, ...]
    secret_boundary_validation_summary: Mapping[str, Any]
    audit_replay_status: str
    dry_run_receipt_references: tuple[str, ...]
    canary_readiness_references: tuple[str, ...]
    canary_replay_acceptance_references: tuple[str, ...]
    wallet_boundary_references: tuple[str, ...]
    risk_decision_references: tuple[str, ...]
    tiny_live_canary_preflight_summary: Mapping[str, Any]
    operator_intent_packet_summary: Mapping[str, Any]
    required_human_checklist: tuple[Mapping[str, Any], ...]
    latest_audit_replay_path: str
    latest_tiny_canary_contract_path: str
    latest_manual_runbook_path: str
    latest_operator_intent_packet_path: str
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_LIVE_APPROVAL_PACKET_CONTRACT
        value["disabled_connector_status"] = dict(self.disabled_connector_status)
        value["blocker_matrix_summary"] = dict(self.blocker_matrix_summary)
        value["unresolved_blocker_ids"] = list(self.unresolved_blocker_ids)
        value["secret_boundary_validation_summary"] = dict(self.secret_boundary_validation_summary)
        value["dry_run_receipt_references"] = list(self.dry_run_receipt_references)
        value["canary_readiness_references"] = list(self.canary_readiness_references)
        value["canary_replay_acceptance_references"] = list(self.canary_replay_acceptance_references)
        value["wallet_boundary_references"] = list(self.wallet_boundary_references)
        value["risk_decision_references"] = list(self.risk_decision_references)
        value["tiny_live_canary_preflight_summary"] = dict(self.tiny_live_canary_preflight_summary)
        value["operator_intent_packet_summary"] = dict(self.operator_intent_packet_summary)
        value["required_human_checklist"] = [dict(row) for row in self.required_human_checklist]
        value["operator_review_ready"] = self.operator_packet_status == OPERATOR_REVIEW_READY
        value["operator_intent_packet_status"] = clean_text(
            self.operator_intent_packet_summary.get("operator_intent_packet_status")
        )
        value["operator_intent_packet_review_ready"] = (
            self.operator_intent_packet_summary.get("operator_intent_packet_review_ready") is True
        )
        value["operator_intent_is_not_live_approval"] = True
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["live_connector_enabled"] = False
        value["canary_executable_now"] = False
        value["operator_review_is_not_live_approval"] = True
        value["non_approval_statement"] = NON_APPROVAL_STATEMENT
        value.update(_packet_safety_flags())
        value["safety_summary"] = trading_core_safety_summary()
        return value


@dataclass(frozen=True)
class OperatorLiveApprovalPacketResult:
    result_id: str
    operator_packet_status: str
    operator_review_ready: bool
    packet_id: str
    validation: Mapping[str, Any]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = OPERATOR_LIVE_APPROVAL_PACKET_RESULT_CONTRACT
        value["validation"] = dict(self.validation)
        value["live_execution_approved"] = False
        value["real_execution_available"] = False
        value["live_connector_enabled"] = False
        value["operator_review_is_not_live_approval"] = True
        value["non_approval_statement"] = NON_APPROVAL_STATEMENT
        value.update(_packet_safety_flags())
        return value


def build_operator_live_approval_packet(
    *,
    audit_replay_result: Mapping[str, Any],
    disabled_connector_status: Mapping[str, Any],
    blocker_matrix: Mapping[str, Any],
    secret_boundary_validation_summary: Mapping[str, Any] | None = None,
    dry_run_receipt_references: Sequence[str] | None = None,
    canary_readiness_references: Sequence[str] | None = None,
    canary_replay_acceptance_references: Sequence[str] | None = None,
    wallet_boundary_references: Sequence[str] | None = None,
    risk_decision_references: Sequence[str] | None = None,
    tiny_live_canary_preflight_contract: Mapping[str, Any] | None = None,
    tiny_live_canary_manual_runbook: Mapping[str, Any] | None = None,
    tiny_live_canary_preflight_result: Mapping[str, Any] | None = None,
    operator_intent_packet: Mapping[str, Any] | None = None,
    latest_audit_replay_path: str = "",
    latest_tiny_canary_contract_path: str = "",
    latest_manual_runbook_path: str = "",
    latest_operator_intent_packet_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    replay_refs = dict(audit_replay_result.get("artifact_references", {}))
    dry_run_refs = _clean_list(dry_run_receipt_references or replay_refs.get("dry_run_receipt_references"))
    canary_refs = _clean_list(canary_readiness_references or replay_refs.get("canary_readiness_packet_references"))
    canary_replay_refs = _clean_list(
        canary_replay_acceptance_references or replay_refs.get("canary_replay_acceptance_references")
    )
    wallet_refs = _clean_list(wallet_boundary_references or replay_refs.get("wallet_boundary_packet_references"))
    risk_refs = _clean_list(risk_decision_references or replay_refs.get("risk_decision_references"))
    blocker_summary = _blocker_summary(blocker_matrix)
    unresolved_ids = tuple(_clean_list(blocker_matrix.get("unresolved_blockers")))
    secret_summary = dict(
        secret_boundary_validation_summary or audit_replay_result.get("secret_boundary_validation_summary", {})
    )
    tiny_preflight_summary = _tiny_live_canary_preflight_summary(
        contract=tiny_live_canary_preflight_contract,
        manual_runbook=tiny_live_canary_manual_runbook,
        preflight_result=tiny_live_canary_preflight_result,
        latest_tiny_canary_contract_path=latest_tiny_canary_contract_path,
        latest_manual_runbook_path=latest_manual_runbook_path,
    )
    operator_intent_summary = _operator_intent_packet_summary(
        operator_intent_packet,
        latest_operator_intent_packet_path=latest_operator_intent_packet_path,
    )
    checklist = tuple(
        _default_checklist(
            disabled_connector_status=disabled_connector_status,
            blocker_summary=blocker_summary,
            audit_replay_result=audit_replay_result,
            dry_run_receipt_references=dry_run_refs,
            canary_readiness_references=canary_refs,
            wallet_boundary_references=wallet_refs,
            risk_decision_references=risk_refs,
            tiny_live_canary_preflight_summary=tiny_preflight_summary,
            operator_intent_packet_summary=operator_intent_summary,
        )
    )
    static_ready = _static_review_ready(
        audit_replay_result=audit_replay_result,
        disabled_connector_status=disabled_connector_status,
        blocker_summary=blocker_summary,
        secret_summary=secret_summary,
        dry_run_receipt_references=dry_run_refs,
        canary_readiness_references=canary_refs,
        canary_replay_acceptance_references=canary_replay_refs,
        wallet_boundary_references=wallet_refs,
        risk_decision_references=risk_refs,
        checklist=checklist,
    )
    packet_id = _stable_id(
        "operator-live-review-packet-032",
        {
            "audit_replay_id": clean_text(audit_replay_result.get("replay_id")),
            "audit_replay_status": clean_text(audit_replay_result.get("status")),
            "disabled_connector_status": clean_text(disabled_connector_status.get("connector_status")),
            "unresolved_blocker_ids": list(unresolved_ids),
            "dry_run_receipt_references": dry_run_refs,
            "canary_readiness_references": canary_refs,
            "canary_replay_acceptance_references": canary_replay_refs,
            "wallet_boundary_references": wallet_refs,
            "risk_decision_references": risk_refs,
            "tiny_live_canary_preflight_summary": tiny_preflight_summary,
            "operator_intent_packet_summary": operator_intent_summary,
            "operator_review_ready": static_ready,
        },
    )
    packet = OperatorLiveApprovalPacket(
        packet_id=packet_id,
        operator_packet_status=OPERATOR_REVIEW_READY if static_ready else OPERATOR_REVIEW_BLOCKED,
        disabled_connector_status=disabled_connector_status,
        blocker_matrix_summary=blocker_summary,
        unresolved_blocker_ids=unresolved_ids,
        secret_boundary_validation_summary=secret_summary,
        audit_replay_status=clean_text(audit_replay_result.get("status")),
        dry_run_receipt_references=tuple(dry_run_refs),
        canary_readiness_references=tuple(canary_refs),
        canary_replay_acceptance_references=tuple(canary_replay_refs),
        wallet_boundary_references=tuple(wallet_refs),
        risk_decision_references=tuple(risk_refs),
        tiny_live_canary_preflight_summary=tiny_preflight_summary,
        operator_intent_packet_summary=operator_intent_summary,
        required_human_checklist=checklist,
        latest_audit_replay_path=clean_text(latest_audit_replay_path),
        latest_tiny_canary_contract_path=clean_text(latest_tiny_canary_contract_path),
        latest_manual_runbook_path=clean_text(latest_manual_runbook_path),
        latest_operator_intent_packet_path=clean_text(latest_operator_intent_packet_path),
        generated_at=generated_at,
    ).to_dict()
    validation = validate_operator_live_approval_packet(packet, generated_at=generated_at)
    validation_detail = dict(validation.get("validation", {}))
    packet["validation"] = {
        "valid": validation_detail.get("valid"),
        "status": validation_detail.get("status"),
        "validation_errors": list(validation_detail.get("validation_errors", [])),
    }
    if validation_detail.get("valid") is not True:
        packet["operator_packet_status"] = OPERATOR_REVIEW_BLOCKED
        packet["operator_review_ready"] = False
    return packet


def validate_operator_live_approval_packet(
    packet: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    if packet.get("contract_version") != OPERATOR_LIVE_APPROVAL_PACKET_CONTRACT:
        errors.append(f"contract_version must be {OPERATOR_LIVE_APPROVAL_PACKET_CONTRACT}")
    if clean_text(packet.get("operator_packet_status")) not in {OPERATOR_REVIEW_READY, OPERATOR_REVIEW_BLOCKED}:
        errors.append("operator_packet_status must be a supported review status")
    if packet.get("non_approval_statement") != NON_APPROVAL_STATEMENT:
        errors.append("non_approval_statement must explicitly deny live execution authorization")
    if packet.get("operator_review_is_not_live_approval") is not True:
        errors.append("operator_review_is_not_live_approval must be true")
    for field in ("live_execution_approved", "real_execution_available", "live_connector_enabled"):
        if packet.get(field) is not False:
            errors.append(f"{field} must be false")
    if packet.get("canary_executable_now") is not False:
        errors.append("canary_executable_now must be false")
    preflight_summary = dict(packet.get("tiny_live_canary_preflight_summary", {}))
    for field in ("canary_executable_now", "live_execution_approved", "real_execution_available"):
        if preflight_summary.get(field) is not False:
            errors.append(f"tiny_live_canary_preflight_summary.{field} must be false")
    intent_summary = dict(packet.get("operator_intent_packet_summary", {}))
    if intent_summary:
        if intent_summary.get("operator_intent_is_not_live_approval") is not True:
            errors.append("operator intent packet must remain distinct from live approval")
        for field in ("canary_executable_now", "live_execution_approved", "real_execution_available"):
            if intent_summary.get(field) is not False:
                errors.append(f"operator_intent_packet_summary.{field} must be false")
    if packet.get("operator_intent_is_not_live_approval") is not True:
        errors.append("operator_intent_is_not_live_approval must be true")
    if dict(packet.get("disabled_connector_status", {})).get("connector_status") != CONNECTOR_STATUS_DISABLED:
        errors.append("disabled connector status must remain disabled")
    if dict(packet.get("disabled_connector_status", {})).get("real_execution_available") is not False:
        errors.append("disabled connector real_execution_available must be false")
    if clean_text(packet.get("audit_replay_status")) != REPLAY_STATUS_PASSED:
        errors.append("audit replay must pass before operator review packet is ready")
    blocker_summary = dict(packet.get("blocker_matrix_summary", {}))
    if blocker_summary.get("all_live_connector_blockers_unresolved") is not True:
        errors.append("all live connector blockers must remain unresolved")
    if int(blocker_summary.get("unresolved_live_blocker_count", 0) or 0) <= 0:
        errors.append("unresolved live blocker count must be positive")
    if dict(packet.get("secret_boundary_validation_summary", {})).get("valid") is not True:
        errors.append("secret boundary validation summary must pass")
    for field in (
        "dry_run_receipt_references",
        "canary_readiness_references",
        "canary_replay_acceptance_references",
        "wallet_boundary_references",
        "risk_decision_references",
        "unresolved_blocker_ids",
    ):
        if not _clean_list(packet.get(field)):
            errors.append(f"{field} must contain at least one reference")
    checklist = [row for row in packet.get("required_human_checklist", []) if isinstance(row, Mapping)]
    if not checklist:
        errors.append("required_human_checklist must not be empty")
    for index, item in enumerate(checklist):
        item_validation = validate_secret_boundary_operator_checklist_item(dict(item), generated_at=generated_at)
        if item_validation.get("valid") is not True:
            errors.append(f"required_human_checklist[{index}] violates static secret boundary")
        if item.get("live_execution_approved") is not False:
            errors.append(f"required_human_checklist[{index}].live_execution_approved must be false")
        if item.get("live_execution_approval_item") is not False:
            errors.append(f"required_human_checklist[{index}].live_execution_approval_item must be false")
    packet_secret_validation = validate_secret_boundary_operator_approval_packet(packet, generated_at=generated_at)
    if packet_secret_validation.get("valid") is not True:
        errors.append("operator packet violates static secret boundary")
    operator_review_ready = not errors and packet.get("operator_packet_status") == OPERATOR_REVIEW_READY
    return OperatorLiveApprovalPacketResult(
        result_id=_stable_id(
            "operator-live-review-packet-result-032",
            {"packet_id": packet.get("packet_id"), "errors": errors},
        ),
        operator_packet_status=OPERATOR_REVIEW_READY if operator_review_ready else OPERATOR_REVIEW_BLOCKED,
        operator_review_ready=operator_review_ready,
        packet_id=clean_text(packet.get("packet_id")),
        validation={
            "contract_version": OPERATOR_LIVE_APPROVAL_PACKET_VALIDATION_CONTRACT,
            "generated_at": generated_at,
            "valid": operator_review_ready,
            "status": "passed" if operator_review_ready else "blocked",
            "validation_errors": errors,
            "packet_secret_boundary_validation": packet_secret_validation,
        },
        generated_at=generated_at,
    ).to_dict()


def render_operator_live_approval_packet_markdown(packet: Mapping[str, Any]) -> str:
    tiny_preflight = dict(packet.get("tiny_live_canary_preflight_summary", {}))
    operator_intent = dict(packet.get("operator_intent_packet_summary", {}))
    lines = [
        "# PMBOT Operator Live Review Packet",
        "",
        f"- Packet: `{packet.get('packet_id')}`",
        f"- Status: `{packet.get('operator_packet_status')}`",
        f"- Operator review ready: `{str(packet.get('operator_review_ready')).lower()}`",
        f"- Live execution approved: `{str(packet.get('live_execution_approved')).lower()}`",
        f"- Real execution available: `{str(packet.get('real_execution_available')).lower()}`",
        f"- Live connector enabled: `{str(packet.get('live_connector_enabled')).lower()}`",
        f"- Non-approval statement: {packet.get('non_approval_statement')}",
        "",
        "## Replay And Blockers",
        "",
        f"- Audit replay status: `{packet.get('audit_replay_status')}`",
        f"- Disabled connector: `{dict(packet.get('disabled_connector_status', {})).get('connector_status')}`",
        f"- Unresolved blockers: {len(packet.get('unresolved_blocker_ids', []))}",
        f"- Tiny canary preflight: `{tiny_preflight.get('preflight_contract_status')}`",
        f"- Manual runbook: `{tiny_preflight.get('manual_runbook_status')}`",
        f"- Operator intent packet: `{operator_intent.get('operator_intent_packet_status')}`",
        f"- Canary executable now: `{str(tiny_preflight.get('canary_executable_now')).lower()}`",
        "",
        "## Required Human Checklist",
        "",
        *bullet_lines(
            f"`{row.get('item_id')}` `{row.get('status')}` {row.get('title')}"
            for row in packet.get("required_human_checklist", [])
            if isinstance(row, Mapping)
        ),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _static_review_ready(
    *,
    audit_replay_result: Mapping[str, Any],
    disabled_connector_status: Mapping[str, Any],
    blocker_summary: Mapping[str, Any],
    secret_summary: Mapping[str, Any],
    dry_run_receipt_references: Sequence[str],
    canary_readiness_references: Sequence[str],
    canary_replay_acceptance_references: Sequence[str],
    wallet_boundary_references: Sequence[str],
    risk_decision_references: Sequence[str],
    checklist: Sequence[Mapping[str, Any]],
) -> bool:
    return (
        clean_text(audit_replay_result.get("status")) == REPLAY_STATUS_PASSED
        and audit_replay_result.get("real_execution_available") is False
        and disabled_connector_status.get("connector_status") == CONNECTOR_STATUS_DISABLED
        and disabled_connector_status.get("real_execution_available") is False
        and blocker_summary.get("all_live_connector_blockers_unresolved") is True
        and int(blocker_summary.get("unresolved_live_blocker_count", 0) or 0) > 0
        and secret_summary.get("valid") is True
        and bool(dry_run_receipt_references)
        and bool(canary_readiness_references)
        and bool(canary_replay_acceptance_references)
        and bool(wallet_boundary_references)
        and bool(risk_decision_references)
        and bool(checklist)
    )


def _default_checklist(
    *,
    disabled_connector_status: Mapping[str, Any],
    blocker_summary: Mapping[str, Any],
    audit_replay_result: Mapping[str, Any],
    dry_run_receipt_references: Sequence[str],
    canary_readiness_references: Sequence[str],
    wallet_boundary_references: Sequence[str],
    risk_decision_references: Sequence[str],
    tiny_live_canary_preflight_summary: Mapping[str, Any],
    operator_intent_packet_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = [
        OperatorLiveApprovalChecklistItem(
            item_id="review_disabled_connector_refusal",
            title="Review that the disabled connector refused execution and remains disabled.",
            evidence_reference=clean_text(disabled_connector_status.get("latest_disabled_connector_audit_path")),
        ),
        OperatorLiveApprovalChecklistItem(
            item_id="review_unresolved_live_blockers",
            title="Review that all critical live blockers remain unresolved.",
            evidence_reference=",".join(_clean_list(blocker_summary.get("unresolved_live_blocker_ids"))),
        ),
        OperatorLiveApprovalChecklistItem(
            item_id="review_secret_boundary_static_validation",
            title="Review static secret-boundary validation summaries.",
            evidence_reference=clean_text(dict(audit_replay_result.get("secret_boundary_validation_summary", {})).get("status")),
        ),
        OperatorLiveApprovalChecklistItem(
            item_id="review_audit_replay_determinism",
            title="Review deterministic audit replay output and mismatch count.",
            evidence_reference=clean_text(audit_replay_result.get("replay_id")),
        ),
        OperatorLiveApprovalChecklistItem(
            item_id="review_dry_run_artifact_references",
            title="Review dry-run receipt, canary readiness, wallet boundary, and risk decision references.",
            evidence_reference=";".join(
                [
                    ",".join(dry_run_receipt_references),
                    ",".join(canary_readiness_references),
                    ",".join(wallet_boundary_references),
                    ",".join(risk_decision_references),
                ]
            ),
        ),
        OperatorLiveApprovalChecklistItem(
            item_id="confirm_review_not_live_approval",
            title=NON_APPROVAL_STATEMENT,
            evidence_reference="operator_review_only",
        ),
    ]
    if clean_text(tiny_live_canary_preflight_summary.get("preflight_contract_status")) != "not_generated":
        rows.append(
            OperatorLiveApprovalChecklistItem(
                item_id="review_tiny_live_canary_preflight_runbook",
                title="Review tiny live canary preflight contract and manual runbook references as non-approval artifacts.",
                evidence_reference=";".join(
                    [
                        clean_text(tiny_live_canary_preflight_summary.get("latest_tiny_canary_contract_path")),
                        clean_text(tiny_live_canary_preflight_summary.get("latest_manual_runbook_path")),
                    ]
                ),
            )
        )
    if clean_text(operator_intent_packet_summary.get("operator_intent_packet_status")) != "not_generated":
        rows.append(
            OperatorLiveApprovalChecklistItem(
                item_id="review_operator_intent_packet_dry_run_only",
                title="Review dry-run operator intent packet as a human acknowledgement artifact only.",
                evidence_reference=clean_text(
                    operator_intent_packet_summary.get("latest_operator_intent_packet_path")
                    or operator_intent_packet_summary.get("operator_intent_packet_status")
                ),
            )
        )
    return [row.to_dict() for row in rows]


def _blocker_summary(blocker_matrix: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "blocker_matrix_status": clean_text(blocker_matrix.get("status")),
        "live_connector_blocker_count": int(blocker_matrix.get("blocker_count", 0) or 0),
        "critical_blocker_count": int(blocker_matrix.get("critical_blocker_count", 0) or 0),
        "unresolved_live_blocker_count": int(blocker_matrix.get("unresolved_blocker_count", 0) or 0),
        "resolved_live_blocker_count": int(blocker_matrix.get("resolved_blocker_count", 0) or 0),
        "all_live_connector_blockers_unresolved": blocker_matrix.get("all_blockers_unresolved") is True,
        "unresolved_live_blocker_ids": _clean_list(blocker_matrix.get("unresolved_blockers")),
        "live_execution_available": False,
    }


def _packet_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "passive_artifact_only": True,
        "operator_review_packet_only": True,
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
        "live_execution_performed": False,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "canary_executable_now": False,
        "outcome_resolution_invented": False,
        "pnl_invented": False,
    }


def _tiny_live_canary_preflight_summary(
    *,
    contract: Mapping[str, Any] | None,
    manual_runbook: Mapping[str, Any] | None,
    preflight_result: Mapping[str, Any] | None,
    latest_tiny_canary_contract_path: str,
    latest_manual_runbook_path: str,
) -> dict[str, Any]:
    contract_value = dict(contract or {})
    runbook_value = dict(manual_runbook or {})
    result_value = dict(preflight_result or {})
    return {
        "preflight_contract_status": clean_text(
            dict(contract_value.get("validation", {})).get("status")
            or ("passed" if contract_value.get("preflight_contract_ready") is True else "not_generated")
        ),
        "manual_runbook_status": clean_text(
            runbook_value.get("status") or ("passed" if runbook_value.get("manual_runbook_ready") is True else "not_generated")
        ),
        "preflight_result_status": clean_text(result_value.get("status") or "not_generated"),
        "preflight_contract_ready": contract_value.get("preflight_contract_ready") is True,
        "manual_runbook_ready": runbook_value.get("manual_runbook_ready") is True,
        "future_canary_shape_defined": (
            contract_value.get("future_tiny_canary_defined") is True
            or result_value.get("future_canary_shape_defined") is True
        ),
        "kill_switch_requirements_defined": (
            dict(contract_value.get("kill_switch_requirement", {})).get("requirements_defined") is True
            or result_value.get("kill_switch_requirements_defined") is True
        ),
        "kill_switch_verified_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "latest_tiny_canary_contract_path": clean_text(latest_tiny_canary_contract_path),
        "latest_manual_runbook_path": clean_text(latest_manual_runbook_path),
        "operator_review_is_not_live_approval": True,
    }


def _operator_intent_packet_summary(
    operator_intent_packet: Mapping[str, Any] | None,
    *,
    latest_operator_intent_packet_path: str,
) -> dict[str, Any]:
    value = dict(operator_intent_packet or {})
    if not value:
        return {
            "operator_intent_packet_status": "not_generated",
            "operator_intent_packet_review_ready": False,
            "operator_intent_is_not_live_approval": True,
            "operator_signed_intent_is_human_acknowledgement_only": True,
            "canary_executable_now": False,
            "live_execution_approved": False,
            "real_execution_available": False,
            "latest_operator_intent_packet_path": clean_text(latest_operator_intent_packet_path),
        }
    return {
        "operator_intent_packet_status": clean_text(value.get("intent_packet_status")),
        "operator_intent_packet_review_ready": value.get("operator_intent_packet_review_ready") is True,
        "operator_intent_is_not_live_approval": value.get("operator_intent_is_not_live_approval") is True,
        "operator_signed_intent_is_human_acknowledgement_only": (
            value.get("operator_signed_intent_is_human_acknowledgement_only") is True
        ),
        "validation_status": clean_text(dict(value.get("validation", {})).get("status")),
        "unresolved_live_blocker_count": int(value.get("unresolved_live_blocker_count", 0) or 0),
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "latest_operator_intent_packet_path": clean_text(latest_operator_intent_packet_path),
    }


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [clean_text(item) for item in value if clean_text(item)]
    text = clean_text(value)
    return [text] if text else []


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
