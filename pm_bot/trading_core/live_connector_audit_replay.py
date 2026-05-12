from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.real_wallet_connector_disabled_adapter import (
    CONNECTOR_STATUS_DISABLED,
    DISABLED_CONNECTOR_RESULT_STATUS,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_audit_record,
    validate_secret_boundary_audit_replay_record,
    validate_secret_boundary_result_artifact,
)

LIVE_CONNECTOR_AUDIT_REPLAY_INPUT_CONTRACT = "pmbot_live_connector_audit_replay_input.v1"
LIVE_CONNECTOR_AUDIT_REPLAY_RECORD_CONTRACT = "pmbot_live_connector_audit_replay_record.v1"
LIVE_CONNECTOR_AUDIT_REPLAY_RESULT_CONTRACT = "pmbot_live_connector_audit_replay_result.v1"
LIVE_CONNECTOR_REPLAY_MISMATCH_CONTRACT = "pmbot_live_connector_replay_mismatch.v1"

REPLAY_STATUS_PASSED = "replay_passed"
REPLAY_STATUS_FAILED = "replay_failed"
REPLAY_STATUS_BLOCKED_BY_DISABLED_CONNECTOR = "blocked_by_disabled_connector"
REPLAY_STATUS_BLOCKED_BY_UNRESOLVED_LIVE_BLOCKERS = "blocked_by_unresolved_live_blockers"
REPLAY_STATUS_BLOCKED_BY_SECRET_POLICY = "blocked_by_secret_policy"
REPLAY_STATUS_INSUFFICIENT_ARTIFACTS = "insufficient_artifacts"
ALLOWED_REPLAY_STATUSES = {
    REPLAY_STATUS_PASSED,
    REPLAY_STATUS_FAILED,
    REPLAY_STATUS_BLOCKED_BY_DISABLED_CONNECTOR,
    REPLAY_STATUS_BLOCKED_BY_UNRESOLVED_LIVE_BLOCKERS,
    REPLAY_STATUS_BLOCKED_BY_SECRET_POLICY,
    REPLAY_STATUS_INSUFFICIENT_ARTIFACTS,
}

REQUIRED_REFERENCE_GROUPS = (
    "canary_readiness_packet_references",
    "canary_replay_acceptance_references",
    "wallet_boundary_packet_references",
    "risk_decision_references",
    "secret_boundary_validation_summaries",
)


@dataclass(frozen=True)
class LiveConnectorReplayMismatch:
    mismatch_id: str
    field_path: str
    expected_value: Any
    actual_value: Any
    mismatch_type: str = "disabled_connector_replay_drift"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CONNECTOR_REPLAY_MISMATCH_CONTRACT
        return value


@dataclass(frozen=True)
class LiveConnectorAuditReplayRecord:
    replay_record_id: str
    source_audit_id: str
    request_id: str
    connector_id: str
    connector_status: str
    status: str
    source_result_id: str
    replayed_result_id: str
    replayed_audit_id: str
    blocked_reason_ids: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    record_hash: str
    deterministic: bool
    replay_status: str
    mismatch_count: int
    mismatches: tuple[Mapping[str, Any], ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CONNECTOR_AUDIT_REPLAY_RECORD_CONTRACT
        value["blocked_reason_ids"] = list(self.blocked_reason_ids)
        value["missing_prerequisites"] = list(self.missing_prerequisites)
        value["mismatches"] = [dict(row) for row in self.mismatches]
        value.update(_static_replay_safety_flags())
        value["disabled_connector_blocking_status"] = REPLAY_STATUS_BLOCKED_BY_DISABLED_CONNECTOR
        value["safety_summary"] = trading_core_safety_summary()
        return value


@dataclass(frozen=True)
class LiveConnectorAuditReplayInput:
    disabled_connector_audit_records: tuple[Mapping[str, Any], ...]
    canary_readiness_packet_references: tuple[str, ...]
    canary_replay_acceptance_references: tuple[str, ...]
    wallet_boundary_packet_references: tuple[str, ...]
    risk_decision_references: tuple[str, ...]
    secret_boundary_validation_summaries: tuple[Mapping[str, Any], ...]
    dry_run_receipt_references: tuple[str, ...] = ()
    tiny_live_canary_preflight_contract_references: tuple[str, ...] = ()
    tiny_live_canary_manual_runbook_references: tuple[str, ...] = ()
    operator_intent_packet_references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": LIVE_CONNECTOR_AUDIT_REPLAY_INPUT_CONTRACT,
            "disabled_connector_audit_records": [dict(row) for row in self.disabled_connector_audit_records],
            "canary_readiness_packet_references": list(self.canary_readiness_packet_references),
            "canary_replay_acceptance_references": list(self.canary_replay_acceptance_references),
            "wallet_boundary_packet_references": list(self.wallet_boundary_packet_references),
            "risk_decision_references": list(self.risk_decision_references),
            "secret_boundary_validation_summaries": [
                dict(row) for row in self.secret_boundary_validation_summaries
            ],
            "dry_run_receipt_references": list(self.dry_run_receipt_references),
            "tiny_live_canary_preflight_contract_references": list(
                self.tiny_live_canary_preflight_contract_references
            ),
            "tiny_live_canary_manual_runbook_references": list(
                self.tiny_live_canary_manual_runbook_references
            ),
            "operator_intent_packet_references": list(self.operator_intent_packet_references),
        }


@dataclass(frozen=True)
class LiveConnectorAuditReplayResult:
    replay_id: str
    status: str
    records: tuple[Mapping[str, Any], ...]
    mismatches: tuple[Mapping[str, Any], ...]
    missing_artifacts: tuple[str, ...]
    artifact_references: Mapping[str, Any]
    secret_boundary_validation_summary: Mapping[str, Any]
    live_connector_blocker_summary: Mapping[str, Any]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CONNECTOR_AUDIT_REPLAY_RESULT_CONTRACT
        value["records"] = [dict(row) for row in self.records]
        value["mismatches"] = [dict(row) for row in self.mismatches]
        value["missing_artifacts"] = list(self.missing_artifacts)
        value["artifact_references"] = dict(self.artifact_references)
        value["secret_boundary_validation_summary"] = dict(self.secret_boundary_validation_summary)
        value["live_connector_blocker_summary"] = dict(self.live_connector_blocker_summary)
        value["record_count"] = len(self.records)
        value["mismatch_count"] = len(self.mismatches)
        value["deterministic"] = all(row.get("deterministic") is True for row in self.records)
        value["replay_passed"] = self.status == REPLAY_STATUS_PASSED
        value["blocking_statuses"] = _blocking_statuses(value)
        value.update(_static_replay_safety_flags())
        value["live_execution_approved"] = False
        value["live_connector_enabled"] = False
        value["tiny_live_canary_preflight_status"] = (
            "referenced"
            if value["artifact_references"].get("tiny_live_canary_preflight_contract_references")
            else "not_provided"
        )
        value["manual_runbook_status"] = (
            "referenced"
            if value["artifact_references"].get("tiny_live_canary_manual_runbook_references")
            else "not_provided"
        )
        value["operator_intent_packet_status"] = (
            "referenced" if value["artifact_references"].get("operator_intent_packet_references") else "not_provided"
        )
        value["canary_executable_now"] = False
        value["operator_review_artifact_only"] = True
        value["safety_summary"] = trading_core_safety_summary()
        return value


def build_live_connector_audit_replay(
    replay_input: LiveConnectorAuditReplayInput | Mapping[str, Any] | None = None,
    *,
    disabled_connector_audit_records: Sequence[Mapping[str, Any]] | None = None,
    canary_readiness_packet_references: Sequence[str] | None = None,
    canary_replay_acceptance_references: Sequence[str] | None = None,
    wallet_boundary_packet_references: Sequence[str] | None = None,
    risk_decision_references: Sequence[str] | None = None,
    secret_boundary_validation_summaries: Sequence[Mapping[str, Any]] | None = None,
    dry_run_receipt_references: Sequence[str] | None = None,
    tiny_live_canary_preflight_contract_references: Sequence[str] | None = None,
    tiny_live_canary_manual_runbook_references: Sequence[str] | None = None,
    operator_intent_packet_references: Sequence[str] | None = None,
    live_connector_blocker_matrix: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    replay_value = _coerce_input(
        replay_input,
        disabled_connector_audit_records=disabled_connector_audit_records,
        canary_readiness_packet_references=canary_readiness_packet_references,
        canary_replay_acceptance_references=canary_replay_acceptance_references,
        wallet_boundary_packet_references=wallet_boundary_packet_references,
        risk_decision_references=risk_decision_references,
        secret_boundary_validation_summaries=secret_boundary_validation_summaries,
        dry_run_receipt_references=dry_run_receipt_references,
        tiny_live_canary_preflight_contract_references=tiny_live_canary_preflight_contract_references,
        tiny_live_canary_manual_runbook_references=tiny_live_canary_manual_runbook_references,
        operator_intent_packet_references=operator_intent_packet_references,
    )
    blocker_matrix = dict(live_connector_blocker_matrix or build_live_connector_blocker_matrix(generated_at=generated_at))
    missing_artifacts = _missing_artifacts(replay_value)
    secret_summary = _secret_boundary_summary(
        replay_value.secret_boundary_validation_summaries,
        replay_value.disabled_connector_audit_records,
        generated_at=generated_at,
    )
    records = tuple(
        _build_replay_record(record, generated_at=generated_at)
        for record in replay_value.disabled_connector_audit_records
    )
    mismatches = tuple(mismatch for row in records for mismatch in row.get("mismatches", []))
    blocker_summary = _blocker_summary(blocker_matrix)
    status = _result_status(
        missing_artifacts=missing_artifacts,
        secret_summary=secret_summary,
        mismatches=mismatches,
        records=records,
    )
    artifact_references = {
        "canary_readiness_packet_references": list(replay_value.canary_readiness_packet_references),
        "canary_replay_acceptance_references": list(replay_value.canary_replay_acceptance_references),
        "wallet_boundary_packet_references": list(replay_value.wallet_boundary_packet_references),
        "risk_decision_references": list(replay_value.risk_decision_references),
        "dry_run_receipt_references": list(replay_value.dry_run_receipt_references),
        "tiny_live_canary_preflight_contract_references": list(
            replay_value.tiny_live_canary_preflight_contract_references
        ),
        "tiny_live_canary_manual_runbook_references": list(
            replay_value.tiny_live_canary_manual_runbook_references
        ),
        "operator_intent_packet_references": list(replay_value.operator_intent_packet_references),
    }
    replay_id = _stable_id(
        "live-connector-audit-replay-032",
        {
            "record_hashes": [row.get("record_hash") for row in records],
            "artifact_references": artifact_references,
            "missing_artifacts": missing_artifacts,
            "status": status,
        },
    )
    result = LiveConnectorAuditReplayResult(
        replay_id=replay_id,
        status=status,
        records=records,
        mismatches=mismatches,
        missing_artifacts=tuple(missing_artifacts),
        artifact_references=artifact_references,
        secret_boundary_validation_summary=secret_summary,
        live_connector_blocker_summary=blocker_summary,
        generated_at=generated_at,
    ).to_dict()
    result_validation = validate_secret_boundary_result_artifact(result, generated_at=generated_at)
    result["result_secret_boundary_validation"] = result_validation
    if result_validation.get("valid") is not True:
        result["status"] = REPLAY_STATUS_BLOCKED_BY_SECRET_POLICY
        result["replay_passed"] = False
    return result


def validate_live_connector_audit_replay(
    replay_result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    errors: list[str] = []
    if replay_result.get("contract_version") != LIVE_CONNECTOR_AUDIT_REPLAY_RESULT_CONTRACT:
        errors.append(f"contract_version must be {LIVE_CONNECTOR_AUDIT_REPLAY_RESULT_CONTRACT}")
    if clean_text(replay_result.get("status")) not in ALLOWED_REPLAY_STATUSES:
        errors.append("status must be a supported live connector audit replay status")
    if not clean_text(replay_result.get("replay_id")):
        errors.append("replay_id must be present")
    if int(replay_result.get("record_count", 0) or 0) <= 0:
        errors.append("at least one disabled connector audit record must be replayed")
    if replay_result.get("real_execution_available") is not False:
        errors.append("real_execution_available must be false")
    if replay_result.get("live_execution_approved") is not False:
        errors.append("live_execution_approved must be false")
    if replay_result.get("live_connector_enabled") is not False:
        errors.append("live_connector_enabled must be false")
    if replay_result.get("canary_executable_now") is not False:
        errors.append("canary_executable_now must be false")
    if replay_result.get("external_api_calls_performed") is not False:
        errors.append("external_api_calls_performed must be false")
    if replay_result.get("deterministic") is not True:
        errors.append("replay output must be deterministic")
    secret_summary = dict(replay_result.get("secret_boundary_validation_summary", {}))
    if secret_summary.get("valid") is not True:
        errors.append("secret boundary validation must pass")
    blocker_summary = dict(replay_result.get("live_connector_blocker_summary", {}))
    if blocker_summary.get("all_live_connector_blockers_unresolved") is not True:
        errors.append("live connector blockers must remain unresolved")
    if clean_text(replay_result.get("status")) == REPLAY_STATUS_PASSED and replay_result.get("mismatch_count") != 0:
        errors.append("replay_passed status cannot include mismatches")
    result_secret_validation = validate_secret_boundary_result_artifact(replay_result, generated_at=generated_at)
    if result_secret_validation.get("valid") is not True:
        errors.append("result artifact violates static secret boundary")
    return {
        "contract_version": "pmbot_live_connector_audit_replay_validation.v1",
        "generated_at": generated_at,
        "valid": not errors,
        "status": "passed" if not errors else "blocked",
        "validation_errors": errors,
        "result_secret_boundary_validation": result_secret_validation,
        "real_execution_available": False,
        "live_execution_approved": False,
        "external_api_calls_performed": False,
        "static_validation_only": True,
    }


def render_live_connector_audit_replay_markdown(replay_result: Mapping[str, Any]) -> str:
    blocker_summary = dict(replay_result.get("live_connector_blocker_summary", {}))
    secret_summary = dict(replay_result.get("secret_boundary_validation_summary", {}))
    lines = [
        "# PMBOT Live Connector Audit Replay",
        "",
        "- This is a deterministic local replay of disabled connector refusal artifacts.",
        f"- Replay: `{replay_result.get('replay_id')}`",
        f"- Status: `{replay_result.get('status')}`",
        f"- Records: {replay_result.get('record_count')}",
        f"- Mismatches: {replay_result.get('mismatch_count')}",
        f"- Deterministic: `{str(replay_result.get('deterministic')).lower()}`",
        f"- Real execution available: `{str(replay_result.get('real_execution_available')).lower()}`",
        f"- Live execution approved: `{str(replay_result.get('live_execution_approved')).lower()}`",
        f"- Tiny canary preflight: `{replay_result.get('tiny_live_canary_preflight_status')}`",
        f"- Manual runbook: `{replay_result.get('manual_runbook_status')}`",
        f"- Operator intent packet: `{replay_result.get('operator_intent_packet_status')}`",
        f"- Canary executable now: `{str(replay_result.get('canary_executable_now')).lower()}`",
        f"- Secret boundary: `{secret_summary.get('status')}`",
        f"- Unresolved live blockers: {blocker_summary.get('unresolved_live_connector_blocker_count')}",
        "",
        "## Blocking Statuses",
        "",
        *bullet_lines(str(item) for item in replay_result.get("blocking_statuses", [])),
        "",
        "## Missing Artifacts",
        "",
        *bullet_lines(str(item) for item in replay_result.get("missing_artifacts", [])),
    ]
    return "\n".join(lines).rstrip() + "\n"


def compare_replay_records(
    original_record: Mapping[str, Any],
    replayed_record: Mapping[str, Any],
) -> list[dict[str, Any]]:
    comparisons = (
        ("$.audit_id", clean_text(replayed_record.get("replayed_audit_id")), clean_text(original_record.get("audit_id"))),
        ("$.result_id", clean_text(replayed_record.get("replayed_result_id")), clean_text(original_record.get("result_id"))),
        ("$.request_id", clean_text(replayed_record.get("request_id")), clean_text(original_record.get("request_id"))),
        ("$.connector_id", clean_text(replayed_record.get("connector_id")), clean_text(original_record.get("connector_id"))),
        (
            "$.connector_status",
            CONNECTOR_STATUS_DISABLED,
            clean_text(original_record.get("connector_status")),
        ),
        ("$.status", DISABLED_CONNECTOR_RESULT_STATUS, clean_text(original_record.get("status"))),
        (
            "$.blocked_reason_ids",
            list(replayed_record.get("blocked_reason_ids", [])),
            _clean_list(original_record.get("blocked_reason_ids")),
        ),
        (
            "$.missing_prerequisites",
            list(replayed_record.get("missing_prerequisites", [])),
            _clean_list(original_record.get("missing_prerequisites")),
        ),
        ("$.real_execution_available", False, original_record.get("real_execution_available")),
        ("$.external_api_calls_performed", False, original_record.get("external_api_calls_performed")),
        ("$.environment_secrets_read", False, original_record.get("environment_secrets_read")),
        ("$.real_wallet_access_performed", False, original_record.get("real_wallet_access_performed")),
        ("$.cryptographic_signing_performed", False, original_record.get("cryptographic_signing_performed")),
        ("$.real_order_placement_performed", False, original_record.get("real_order_placement_performed")),
        (
            "$.authenticated_endpoint_call_performed",
            False,
            original_record.get("authenticated_endpoint_call_performed"),
        ),
    )
    mismatches: list[dict[str, Any]] = []
    for field_path, expected, actual in comparisons:
        if expected != actual:
            mismatches.append(
                LiveConnectorReplayMismatch(
                    mismatch_id=_stable_id(
                        "live-connector-replay-mismatch-032",
                        {
                            "field_path": field_path,
                            "expected_value": expected,
                            "actual_value": actual,
                        },
                    ),
                    field_path=field_path,
                    expected_value=expected,
                    actual_value=actual,
                ).to_dict()
            )
    return mismatches


def _build_replay_record(record: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    original = dict(record)
    request_id = clean_text(original.get("request_id"))
    connector_id = clean_text(original.get("connector_id")) or "disabled-real-wallet-connector-031"
    blocked_reason_ids = tuple(_clean_list(original.get("blocked_reason_ids")))
    missing_prerequisites = tuple(_clean_list(original.get("missing_prerequisites")))
    replayed_result_id = _stable_id(
        "disabled-real-wallet-connector-result-031",
        {
            "request_id": request_id,
            "connector_id": connector_id,
            "blocked_reason_ids": list(blocked_reason_ids),
        },
    )
    replayed_audit_id = _stable_id(
        "disabled-real-wallet-connector-audit-031",
        {
            "request_id": request_id,
            "result_id": replayed_result_id,
            "connector_id": connector_id,
        },
    )
    record_hash = _stable_id(
        "live-connector-audit-replay-record-hash-032",
        {
            "source_audit_id": clean_text(original.get("audit_id")),
            "request_id": request_id,
            "connector_id": connector_id,
            "blocked_reason_ids": list(blocked_reason_ids),
            "missing_prerequisites": list(missing_prerequisites),
            "replayed_result_id": replayed_result_id,
            "replayed_audit_id": replayed_audit_id,
        },
    )
    replay_record_base = {
        "replayed_audit_id": replayed_audit_id,
        "replayed_result_id": replayed_result_id,
        "request_id": request_id,
        "connector_id": connector_id,
        "connector_status": CONNECTOR_STATUS_DISABLED,
        "status": DISABLED_CONNECTOR_RESULT_STATUS,
        "blocked_reason_ids": list(blocked_reason_ids),
        "missing_prerequisites": list(missing_prerequisites),
    }
    mismatches = compare_replay_records(original, replay_record_base)
    deterministic = record_hash == _stable_id(
        "live-connector-audit-replay-record-hash-032",
        {
            "source_audit_id": clean_text(original.get("audit_id")),
            "request_id": request_id,
            "connector_id": connector_id,
            "blocked_reason_ids": list(blocked_reason_ids),
            "missing_prerequisites": list(missing_prerequisites),
            "replayed_result_id": replayed_result_id,
            "replayed_audit_id": replayed_audit_id,
        },
    )
    replay_status = REPLAY_STATUS_PASSED if not mismatches and deterministic else REPLAY_STATUS_FAILED
    secret_validation = validate_secret_boundary_audit_replay_record(replay_record_base, generated_at=generated_at)
    if secret_validation.get("valid") is not True:
        replay_status = REPLAY_STATUS_BLOCKED_BY_SECRET_POLICY
    replay_record = LiveConnectorAuditReplayRecord(
        replay_record_id=_stable_id(
            "live-connector-audit-replay-record-032",
            {"source_audit_id": original.get("audit_id"), "record_hash": record_hash},
        ),
        source_audit_id=clean_text(original.get("audit_id")),
        request_id=request_id,
        connector_id=connector_id,
        connector_status=CONNECTOR_STATUS_DISABLED,
        status=DISABLED_CONNECTOR_RESULT_STATUS,
        source_result_id=clean_text(original.get("result_id")),
        replayed_result_id=replayed_result_id,
        replayed_audit_id=replayed_audit_id,
        blocked_reason_ids=blocked_reason_ids,
        missing_prerequisites=missing_prerequisites,
        record_hash=record_hash,
        deterministic=deterministic,
        replay_status=replay_status,
        mismatch_count=len(mismatches),
        mismatches=tuple(mismatches),
        generated_at=generated_at,
    ).to_dict()
    replay_record["record_secret_boundary_validation"] = secret_validation
    return replay_record


def _coerce_input(
    replay_input: LiveConnectorAuditReplayInput | Mapping[str, Any] | None,
    *,
    disabled_connector_audit_records: Sequence[Mapping[str, Any]] | None,
    canary_readiness_packet_references: Sequence[str] | None,
    canary_replay_acceptance_references: Sequence[str] | None,
    wallet_boundary_packet_references: Sequence[str] | None,
    risk_decision_references: Sequence[str] | None,
    secret_boundary_validation_summaries: Sequence[Mapping[str, Any]] | None,
    dry_run_receipt_references: Sequence[str] | None,
    tiny_live_canary_preflight_contract_references: Sequence[str] | None,
    tiny_live_canary_manual_runbook_references: Sequence[str] | None,
    operator_intent_packet_references: Sequence[str] | None,
) -> LiveConnectorAuditReplayInput:
    if isinstance(replay_input, LiveConnectorAuditReplayInput):
        return replay_input
    value = dict(replay_input or {})
    return LiveConnectorAuditReplayInput(
        disabled_connector_audit_records=tuple(
            dict(row)
            for row in (disabled_connector_audit_records or value.get("disabled_connector_audit_records") or [])
            if isinstance(row, Mapping)
        ),
        canary_readiness_packet_references=tuple(
            _clean_list(canary_readiness_packet_references or value.get("canary_readiness_packet_references"))
        ),
        canary_replay_acceptance_references=tuple(
            _clean_list(canary_replay_acceptance_references or value.get("canary_replay_acceptance_references"))
        ),
        wallet_boundary_packet_references=tuple(
            _clean_list(wallet_boundary_packet_references or value.get("wallet_boundary_packet_references"))
        ),
        risk_decision_references=tuple(_clean_list(risk_decision_references or value.get("risk_decision_references"))),
        secret_boundary_validation_summaries=tuple(
            dict(row)
            for row in (
                secret_boundary_validation_summaries or value.get("secret_boundary_validation_summaries") or []
            )
            if isinstance(row, Mapping)
        ),
        dry_run_receipt_references=tuple(
            _clean_list(dry_run_receipt_references or value.get("dry_run_receipt_references"))
        ),
        tiny_live_canary_preflight_contract_references=tuple(
            _clean_list(
                tiny_live_canary_preflight_contract_references
                or value.get("tiny_live_canary_preflight_contract_references")
            )
        ),
        tiny_live_canary_manual_runbook_references=tuple(
            _clean_list(
                tiny_live_canary_manual_runbook_references
                or value.get("tiny_live_canary_manual_runbook_references")
            )
        ),
        operator_intent_packet_references=tuple(
            _clean_list(operator_intent_packet_references or value.get("operator_intent_packet_references"))
        ),
    )


def _missing_artifacts(replay_input: LiveConnectorAuditReplayInput) -> list[str]:
    values = replay_input.to_dict()
    missing = []
    if not replay_input.disabled_connector_audit_records:
        missing.append("disabled_connector_audit_records")
    for group in REQUIRED_REFERENCE_GROUPS:
        if not values.get(group):
            missing.append(group)
    for index, record in enumerate(replay_input.disabled_connector_audit_records):
        for field in ("audit_id", "request_id", "result_id", "connector_id", "status"):
            if not clean_text(record.get(field)):
                missing.append(f"disabled_connector_audit_records[{index}].{field}")
    return missing


def _secret_boundary_summary(
    summaries: Sequence[Mapping[str, Any]],
    audit_records: Sequence[Mapping[str, Any]],
    *,
    generated_at: str,
) -> dict[str, Any]:
    validations = [dict(row) for row in summaries]
    validations.extend(validate_secret_boundary_audit_record(dict(row), generated_at=generated_at) for row in audit_records)
    failed = [
        clean_text(row.get("validation_id") or row.get("artifact_type") or f"validation_{index}")
        for index, row in enumerate(validations)
        if row.get("valid") is not True or clean_text(row.get("status")) == "blocked"
    ]
    return {
        "validation_count": len(validations),
        "failed_validation_count": len(failed),
        "failed_validation_ids": failed,
        "valid": bool(validations) and not failed,
        "status": "passed" if validations and not failed else "blocked",
        "static_secret_validation_only": True,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
    }


def _blocker_summary(blocker_matrix: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "blocker_matrix_status": clean_text(blocker_matrix.get("status")),
        "live_connector_blocker_count": int(blocker_matrix.get("blocker_count", 0) or 0),
        "critical_blocker_count": int(blocker_matrix.get("critical_blocker_count", 0) or 0),
        "unresolved_live_connector_blocker_count": int(blocker_matrix.get("unresolved_blocker_count", 0) or 0),
        "resolved_live_connector_blocker_count": int(blocker_matrix.get("resolved_blocker_count", 0) or 0),
        "all_live_connector_blockers_unresolved": blocker_matrix.get("all_blockers_unresolved") is True,
        "unresolved_live_connector_blocker_ids": _clean_list(blocker_matrix.get("unresolved_blockers")),
        "live_blocker_status": REPLAY_STATUS_BLOCKED_BY_UNRESOLVED_LIVE_BLOCKERS,
        "live_execution_available": False,
    }


def _result_status(
    *,
    missing_artifacts: Sequence[str],
    secret_summary: Mapping[str, Any],
    mismatches: Sequence[Mapping[str, Any]],
    records: Sequence[Mapping[str, Any]],
) -> str:
    if missing_artifacts:
        return REPLAY_STATUS_INSUFFICIENT_ARTIFACTS
    if secret_summary.get("valid") is not True:
        return REPLAY_STATUS_BLOCKED_BY_SECRET_POLICY
    if mismatches:
        return REPLAY_STATUS_FAILED
    if not records:
        return REPLAY_STATUS_INSUFFICIENT_ARTIFACTS
    return REPLAY_STATUS_PASSED


def _blocking_statuses(result: Mapping[str, Any]) -> list[str]:
    statuses = [REPLAY_STATUS_BLOCKED_BY_DISABLED_CONNECTOR]
    blocker_summary = dict(result.get("live_connector_blocker_summary", {}))
    if int(blocker_summary.get("unresolved_live_connector_blocker_count", 0) or 0) > 0:
        statuses.append(REPLAY_STATUS_BLOCKED_BY_UNRESOLVED_LIVE_BLOCKERS)
    if dict(result.get("secret_boundary_validation_summary", {})).get("valid") is not True:
        statuses.append(REPLAY_STATUS_BLOCKED_BY_SECRET_POLICY)
    if result.get("missing_artifacts"):
        statuses.append(REPLAY_STATUS_INSUFFICIENT_ARTIFACTS)
    if result.get("mismatch_count"):
        statuses.append(REPLAY_STATUS_FAILED)
    return _dedupe(statuses)


def _static_replay_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "passive_artifact_only": True,
        "static_replay_only": True,
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
