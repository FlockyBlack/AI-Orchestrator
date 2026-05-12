from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    bullet_lines,
    clean_text,
    normalize_path,
    trading_core_safety_summary,
    write_json,
    write_text,
)
from pm_bot.trading_core.secret_boundary_policy import (
    build_secret_boundary_policy,
    validate_secret_boundary_audit_record,
    validate_secret_boundary_config,
    validate_secret_boundary_request,
)

DISABLED_REAL_WALLET_CONNECTOR_CONFIG_CONTRACT = "pmbot_disabled_real_wallet_connector_config.v1"
DISABLED_REAL_WALLET_CONNECTOR_REQUEST_CONTRACT = "pmbot_disabled_real_wallet_connector_request.v1"
DISABLED_REAL_WALLET_CONNECTOR_RESULT_CONTRACT = "pmbot_disabled_real_wallet_connector_result.v1"
DISABLED_REAL_WALLET_CONNECTOR_AUDIT_CONTRACT = "pmbot_disabled_real_wallet_connector_audit_record.v1"
DISABLED_REAL_WALLET_CONNECTOR_VALIDATION_CONTRACT = "pmbot_disabled_real_wallet_connector_validation.v1"

CONNECTOR_STATUS_DISABLED = "disabled"
DISABLED_CONNECTOR_RESULT_STATUS = "blocked_disabled"

REQUIRED_DISABLED_CONNECTOR_BLOCKED_REASONS = (
    "real_wallet_connector_disabled",
    "secrets_not_configured",
    "real_order_submission_unavailable",
    "authenticated_endpoints_blocked",
    "operator_live_approval_not_supported_in_this_build",
    "production_kill_switch_not_wired_to_live_adapter",
    "live_connector_audit_sink_not_finalized",
)

DISABLED_CONNECTOR_UNRESOLVED_BLOCKER_IDS = (
    "real_wallet_connector_disabled",
    "secret_boundary_not_configured",
    "authenticated_endpoint_boundary_missing",
    "real_order_submission_disabled",
    "live_operator_approval_not_implemented",
    "production_kill_switch_not_wired_to_live_adapter",
    "live_connector_audit_sink_not_finalized",
)


@dataclass(frozen=True)
class DisabledRealWalletConnectorConfig:
    connector_id: str = "disabled-real-wallet-connector-031"
    connector_status: str = CONNECTOR_STATUS_DISABLED
    dry_run_only: bool = True
    require_risk_decision_reference: bool = True
    require_wallet_boundary_packet_reference: bool = True
    require_canary_readiness_packet_reference: bool = False
    require_replay_acceptance_reference: bool = False
    secrets_present: str = "not_inspected"
    secret_boundary_status: str = "static_policy_only"
    allow_secret_inspection: bool = False
    allow_network: bool = False
    allow_real_wallet_access: bool = False
    allow_cryptographic_signing: bool = False
    allow_real_order_submission: bool = False
    allow_authenticated_endpoints: bool = False
    operator_live_approval_supported: bool = False
    production_kill_switch_wired_to_live_adapter: bool = False
    live_connector_audit_sink_finalized: bool = False
    real_execution_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = DISABLED_REAL_WALLET_CONNECTOR_CONFIG_CONTRACT
        value["secret_boundary_policy"] = build_secret_boundary_policy()
        value["blocked_reason_ids"] = list(REQUIRED_DISABLED_CONNECTOR_BLOCKED_REASONS)
        return value


@dataclass(frozen=True)
class DisabledRealWalletConnectorRequest:
    request_id: str
    run_id: str
    market_id: str
    risk_decision_reference: str
    wallet_boundary_packet_reference: str
    canary_readiness_packet_reference: str = ""
    replay_acceptance_reference: str = ""
    requested_action: str = "disabled_connector_boundary_check"
    dry_run_only: bool = True
    operator_context_reference: str = "not_applicable"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = DISABLED_REAL_WALLET_CONNECTOR_REQUEST_CONTRACT
        return value


@dataclass(frozen=True)
class DisabledRealWalletConnectorResult:
    result_id: str
    request_id: str
    connector_id: str
    connector_status: str
    status: str
    execution_refused: bool
    dry_run_only: bool
    real_execution_available: bool
    blocked_reason_ids: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    validation: Mapping[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = DISABLED_REAL_WALLET_CONNECTOR_RESULT_CONTRACT
        value["blocked_reason_ids"] = list(self.blocked_reason_ids)
        value["missing_prerequisites"] = list(self.missing_prerequisites)
        value.update(_disabled_connector_safety_flags())
        value["safety_summary"] = trading_core_safety_summary()
        return value


@dataclass(frozen=True)
class DisabledRealWalletConnectorAuditRecord:
    audit_id: str
    request_id: str
    result_id: str
    connector_id: str
    connector_status: str
    status: str
    blocked_reason_ids: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    validation: Mapping[str, Any]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = DISABLED_REAL_WALLET_CONNECTOR_AUDIT_CONTRACT
        value["blocked_reason_ids"] = list(self.blocked_reason_ids)
        value["missing_prerequisites"] = list(self.missing_prerequisites)
        value["secrets_present"] = "not_inspected"
        value["secret_boundary_status"] = "static_policy_only"
        value["audit_scope"] = "disabled_connector_boundary_only"
        value["local_artifact_only"] = True
        value.update(_disabled_connector_safety_flags())
        value["safety_summary"] = trading_core_safety_summary()
        return value


class RealWalletConnectorDisabledAdapter:
    def __init__(self, config: DisabledRealWalletConnectorConfig | Mapping[str, Any] | None = None) -> None:
        self.config = _coerce_config(config)

    def build_blocked_result(
        self,
        request: DisabledRealWalletConnectorRequest | Mapping[str, Any],
        *,
        generated_at: str = GENERATED_AT,
    ) -> dict[str, Any]:
        return build_disabled_connector_result(request, config=self.config, generated_at=generated_at)

    def build_audit_record(
        self,
        request: DisabledRealWalletConnectorRequest | Mapping[str, Any],
        *,
        generated_at: str = GENERATED_AT,
    ) -> dict[str, Any]:
        result = self.build_blocked_result(request, generated_at=generated_at)
        return build_disabled_connector_audit_record(request=request, result=result, config=self.config, generated_at=generated_at)


def build_disabled_connector_request(
    *,
    run_id: str,
    market_id: str,
    risk_decision_reference: str,
    wallet_boundary_packet_reference: str,
    canary_readiness_packet_reference: str = "",
    replay_acceptance_reference: str = "",
    dry_run_only: bool = True,
) -> DisabledRealWalletConnectorRequest:
    request_id = _stable_id(
        "disabled-real-wallet-connector-request-031",
        {
            "run_id": clean_text(run_id),
            "market_id": clean_text(market_id),
            "risk_decision_reference": clean_text(risk_decision_reference),
            "wallet_boundary_packet_reference": clean_text(wallet_boundary_packet_reference),
            "canary_readiness_packet_reference": clean_text(canary_readiness_packet_reference),
            "replay_acceptance_reference": clean_text(replay_acceptance_reference),
            "dry_run_only": dry_run_only,
        },
    )
    return DisabledRealWalletConnectorRequest(
        request_id=request_id,
        run_id=clean_text(run_id),
        market_id=clean_text(market_id),
        risk_decision_reference=clean_text(risk_decision_reference),
        wallet_boundary_packet_reference=clean_text(wallet_boundary_packet_reference),
        canary_readiness_packet_reference=clean_text(canary_readiness_packet_reference),
        replay_acceptance_reference=clean_text(replay_acceptance_reference),
        dry_run_only=dry_run_only,
    )


def validate_disabled_connector_request(
    request: DisabledRealWalletConnectorRequest | Mapping[str, Any],
    *,
    config: DisabledRealWalletConnectorConfig | Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    request_map = _to_mapping(request)
    connector_config = _coerce_config(config)
    config_map = _to_config_mapping_for_validation(config, connector_config)
    request_secret_validation = validate_secret_boundary_request(request_map, generated_at=generated_at)
    config_secret_validation = validate_secret_boundary_config(config_map, generated_at=generated_at)

    blocker_ids = list(REQUIRED_DISABLED_CONNECTOR_BLOCKED_REASONS)
    missing_prerequisites: list[str] = []
    validation_errors: list[str] = []

    if connector_config.dry_run_only is not True:
        _append_unique(validation_errors, "config_dry_run_only_required")
        _append_unique(blocker_ids, "dry_run_only_required")
    if request_map.get("dry_run_only") is not True:
        _append_unique(validation_errors, "dry_run_only_required")
        _append_unique(blocker_ids, "dry_run_only_required")
    if request_map.get("contract_version") not in {None, DISABLED_REAL_WALLET_CONNECTOR_REQUEST_CONTRACT}:
        _append_unique(validation_errors, "request_contract_version_invalid")
    for field in ("request_id", "run_id", "market_id"):
        if not clean_text(request_map.get(field)):
            _append_unique(validation_errors, f"{field}_required")

    _require_reference(
        request_map,
        "risk_decision_reference",
        "missing_risk_decision_reference",
        connector_config.require_risk_decision_reference,
        missing_prerequisites,
        blocker_ids,
    )
    _require_reference(
        request_map,
        "wallet_boundary_packet_reference",
        "missing_wallet_boundary_packet_reference",
        connector_config.require_wallet_boundary_packet_reference,
        missing_prerequisites,
        blocker_ids,
    )
    _require_reference(
        request_map,
        "canary_readiness_packet_reference",
        "missing_canary_readiness_packet_reference",
        connector_config.require_canary_readiness_packet_reference,
        missing_prerequisites,
        blocker_ids,
    )
    _require_reference(
        request_map,
        "replay_acceptance_reference",
        "missing_replay_acceptance_reference",
        connector_config.require_replay_acceptance_reference,
        missing_prerequisites,
        blocker_ids,
    )

    if request_secret_validation.get("valid") is not True:
        _append_unique(validation_errors, "request_secret_boundary_violation")
        _append_unique(blocker_ids, "secret_like_field_rejected")
    if config_secret_validation.get("valid") is not True:
        _append_unique(validation_errors, "config_secret_boundary_violation")
        _append_unique(blocker_ids, "secret_like_field_rejected")

    valid = not validation_errors and not missing_prerequisites
    return {
        "contract_version": DISABLED_REAL_WALLET_CONNECTOR_VALIDATION_CONTRACT,
        "generated_at": generated_at,
        "status": "blocked",
        "valid": valid,
        "request_id": clean_text(request_map.get("request_id")),
        "connector_status": CONNECTOR_STATUS_DISABLED,
        "blocked_reason_ids": blocker_ids,
        "missing_prerequisites": missing_prerequisites,
        "validation_errors": validation_errors,
        "request_secret_boundary_validation": request_secret_validation,
        "config_secret_boundary_validation": config_secret_validation,
        "dry_run_only_required": True,
        "static_secret_validation_only": True,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "real_execution_available": False,
    }


def build_disabled_connector_result(
    request: DisabledRealWalletConnectorRequest | Mapping[str, Any],
    *,
    config: DisabledRealWalletConnectorConfig | Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    connector_config = _coerce_config(config)
    request_map = _to_mapping(request)
    validation = validate_disabled_connector_request(request_map, config=connector_config, generated_at=generated_at)
    result_id = _stable_id(
        "disabled-real-wallet-connector-result-031",
        {
            "request_id": clean_text(request_map.get("request_id")),
            "connector_id": connector_config.connector_id,
            "blocked_reason_ids": validation.get("blocked_reason_ids", []),
        },
    )
    result = DisabledRealWalletConnectorResult(
        result_id=result_id,
        request_id=clean_text(request_map.get("request_id")),
        connector_id=connector_config.connector_id,
        connector_status=CONNECTOR_STATUS_DISABLED,
        status=DISABLED_CONNECTOR_RESULT_STATUS,
        execution_refused=True,
        dry_run_only=True,
        real_execution_available=False,
        blocked_reason_ids=tuple(clean_text(item) for item in validation.get("blocked_reason_ids", [])),
        missing_prerequisites=tuple(clean_text(item) for item in validation.get("missing_prerequisites", [])),
        validation=validation,
        created_at=generated_at,
    ).to_dict()
    return result


def build_disabled_connector_audit_record(
    *,
    request: DisabledRealWalletConnectorRequest | Mapping[str, Any],
    result: Mapping[str, Any],
    config: DisabledRealWalletConnectorConfig | Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    connector_config = _coerce_config(config)
    request_map = _to_mapping(request)
    audit_id = _stable_id(
        "disabled-real-wallet-connector-audit-031",
        {
            "request_id": clean_text(request_map.get("request_id")),
            "result_id": clean_text(result.get("result_id")),
            "connector_id": connector_config.connector_id,
        },
    )
    audit_record = DisabledRealWalletConnectorAuditRecord(
        audit_id=audit_id,
        request_id=clean_text(request_map.get("request_id")),
        result_id=clean_text(result.get("result_id")),
        connector_id=connector_config.connector_id,
        connector_status=CONNECTOR_STATUS_DISABLED,
        status=DISABLED_CONNECTOR_RESULT_STATUS,
        blocked_reason_ids=tuple(clean_text(item) for item in result.get("blocked_reason_ids", [])),
        missing_prerequisites=tuple(clean_text(item) for item in result.get("missing_prerequisites", [])),
        validation=dict(result.get("validation", {})),
        generated_at=generated_at,
    ).to_dict()
    audit_validation = validate_secret_boundary_audit_record(audit_record, generated_at=generated_at)
    audit_record["audit_secret_boundary_validation"] = audit_validation
    audit_record["audit_valid"] = audit_validation.get("valid") is True
    return audit_record


def build_disabled_connector_passive_status(
    *,
    result: Mapping[str, Any] | None = None,
    latest_disabled_connector_audit_path: str = "",
    live_canary_replay_acceptance_status: str = "",
) -> dict[str, Any]:
    result_value = dict(result or {})
    blocker_ids = [
        clean_text(item)
        for item in result_value.get("blocked_reason_ids", REQUIRED_DISABLED_CONNECTOR_BLOCKED_REASONS)
        if clean_text(item)
    ]
    return {
        "connector_status": CONNECTOR_STATUS_DISABLED,
        "real_execution_available": False,
        "secrets_present": "not_inspected",
        "secret_boundary_status": "static_policy_only",
        "blocked_reason_count": len(blocker_ids),
        "blocker_ids": blocker_ids,
        "latest_disabled_connector_audit_path": clean_text(latest_disabled_connector_audit_path),
        "live_canary_replay_acceptance_status": clean_text(live_canary_replay_acceptance_status),
        "dry_run_only": True,
        "passive_dashboard_only": True,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "external_api_calls_performed": False,
    }


def write_disabled_connector_audit_record(
    *,
    audit_record: Mapping[str, Any],
    out_json_path: str | Path = ARTIFACT_DIR / "disabled_real_wallet_connector_audit.json",
    out_md_path: str | Path = ARTIFACT_DIR / "disabled_real_wallet_connector_audit.md",
) -> dict[str, str]:
    write_json(out_json_path, dict(audit_record))
    write_text(out_md_path, render_disabled_connector_audit_record_markdown(audit_record))
    return {"json": normalize_path(out_json_path), "md": normalize_path(out_md_path)}


def render_disabled_connector_audit_record_markdown(audit_record: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Disabled Real Wallet Connector Audit",
        "",
        "- The real wallet connector is disabled and cannot perform live execution.",
        f"- Connector status: `{audit_record.get('connector_status')}`",
        f"- Result status: `{audit_record.get('status')}`",
        f"- Real execution available: `{str(audit_record.get('real_execution_available')).lower()}`",
        f"- Secrets present: `{audit_record.get('secrets_present')}`",
        f"- Secret boundary: `{audit_record.get('secret_boundary_status')}`",
        "",
        "## Blockers",
        "",
        *bullet_lines(str(item) for item in audit_record.get("blocked_reason_ids", [])),
        "",
        "## Missing Prerequisites",
        "",
        *bullet_lines(str(item) for item in audit_record.get("missing_prerequisites", [])),
    ]
    return "\n".join(lines).rstrip() + "\n"


def _coerce_config(
    config: DisabledRealWalletConnectorConfig | Mapping[str, Any] | None,
) -> DisabledRealWalletConnectorConfig:
    if isinstance(config, DisabledRealWalletConnectorConfig):
        return config
    if isinstance(config, Mapping):
        fields = {field.name for field in DisabledRealWalletConnectorConfig.__dataclass_fields__.values()}
        return DisabledRealWalletConnectorConfig(**{key: value for key, value in config.items() if key in fields})
    return DisabledRealWalletConnectorConfig()


def _to_mapping(value: DisabledRealWalletConnectorRequest | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, DisabledRealWalletConnectorRequest):
        return value.to_dict()
    return dict(value)


def _to_config_mapping_for_validation(
    value: DisabledRealWalletConnectorConfig | Mapping[str, Any] | None,
    connector_config: DisabledRealWalletConnectorConfig,
) -> dict[str, Any]:
    if isinstance(value, DisabledRealWalletConnectorConfig):
        return value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    return connector_config.to_dict()


def _require_reference(
    request: Mapping[str, Any],
    field: str,
    blocker_id: str,
    required: bool,
    missing_prerequisites: list[str],
    blocker_ids: list[str],
) -> None:
    if required and not clean_text(request.get(field)):
        _append_unique(missing_prerequisites, field)
        _append_unique(blocker_ids, blocker_id)


def _disabled_connector_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "passive_artifact_only": True,
        "paper_only": True,
        "dry_run_only": True,
        "live_prep_only": True,
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


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
