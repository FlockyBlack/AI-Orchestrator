from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import (
    validate_secret_boundary_live_auth_boundary_decision,
    validate_secret_boundary_live_credentials_config,
    validate_secret_boundary_live_credentials_status_report,
)

LIVE_CREDENTIALS_AUTH_BOUNDARY_CONFIG_CONTRACT = "pmbot_live_credentials_auth_boundary_config.v1"
LIVE_CREDENTIAL_REQUIREMENT_CONTRACT = "pmbot_live_credential_requirement.v1"
LIVE_CREDENTIAL_PRESENCE_STATUS_CONTRACT = "pmbot_live_credential_presence_status.v1"
LIVE_CREDENTIALS_STATUS_REPORT_CONTRACT = "pmbot_live_credentials_status_report.v1"
LIVE_AUTH_BOUNDARY_VIOLATION_CONTRACT = "pmbot_live_auth_boundary_violation.v1"
LIVE_AUTH_BOUNDARY_DECISION_CONTRACT = "pmbot_live_auth_boundary_decision.v1"
LIVE_CREDENTIALS_AUTH_BOUNDARY_SUMMARY_CONTRACT = "pmbot_live_credentials_auth_boundary_summary.v1"

DECISION_AUTH_BOUNDARY_REVIEW_READY = "AUTH_BOUNDARY_REVIEW_READY"
DECISION_MISSING_REQUIRED_CREDENTIALS = "MISSING_REQUIRED_CREDENTIALS"
DECISION_LIVE_MODE_NOT_EXPLICITLY_ENABLED = "LIVE_MODE_NOT_EXPLICITLY_ENABLED"
DECISION_AUTHENTICATED_ENDPOINTS_STILL_DISABLED = "AUTHENTICATED_ENDPOINTS_STILL_DISABLED"
DECISION_SIGNING_STILL_DISABLED = "SIGNING_STILL_DISABLED"
DECISION_ORDER_SUBMISSION_STILL_DISABLED = "ORDER_SUBMISSION_STILL_DISABLED"
DECISION_SECRET_POLICY_VIOLATION = "SECRET_POLICY_VIOLATION"

REDACTED_CONFIGURED = "<configured:redacted>"
REDACTED_MISSING = "<missing>"
UI_REDACTION_WARNING = "Credentials status is redacted. This panel never displays secrets."

FORCED_FALSE_EXECUTION_FIELDS = (
    "authenticated_endpoints_enabled",
    "order_submission_enabled",
    "cryptographic_signing_enabled",
    "wallet_signing_enabled",
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
)

DEFAULT_LIVE_CREDENTIAL_REQUIREMENTS = (
    ("polymarket_private_key_placeholder", "POLYMARKET_PRIVATE_KEY", "wallet private key placeholder name"),
    ("polymarket_funder_address", "POLYMARKET_FUNDER_ADDRESS", "wallet funder address placeholder name"),
    ("polymarket_clob_api_key", "POLYMARKET_CLOB_API_KEY", "CLOB API key placeholder name"),
    ("polymarket_clob_secret", "POLYMARKET_CLOB_SECRET", "CLOB secret placeholder name"),
    ("polymarket_clob_passphrase", "POLYMARKET_CLOB_PASSPHRASE", "CLOB passphrase placeholder name"),
    ("polymarket_chain_id", "POLYMARKET_CHAIN_ID", "chain ID placeholder name"),
    ("polymarket_network", "POLYMARKET_NETWORK", "network placeholder name"),
)


@dataclass(frozen=True)
class LiveCredentialRequirement:
    requirement_id: str
    env_var_name: str
    description: str
    required_for_future_tiny_canary_auth_review: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": LIVE_CREDENTIAL_REQUIREMENT_CONTRACT,
            "requirement_id": clean_text(self.requirement_id),
            "env_var_name": clean_text(self.env_var_name),
            "description": clean_text(self.description),
            "required_for_future_tiny_canary_auth_review": (
                self.required_for_future_tiny_canary_auth_review is True
            ),
            **_auth_boundary_safety_flags(),
        }


@dataclass(frozen=True)
class LiveCredentialsAuthBoundaryConfig:
    config_id: str
    credential_requirements: tuple[Mapping[str, Any], ...]
    live_mode_explicitly_requested: bool = False
    allow_environment_provider: bool = False
    authenticated_endpoints_enabled: bool = False
    order_submission_enabled: bool = False
    cryptographic_signing_enabled: bool = False
    wallet_signing_enabled: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CREDENTIALS_AUTH_BOUNDARY_CONFIG_CONTRACT
        value["credential_requirements"] = [dict(row) for row in self.credential_requirements]
        value["required_credentials_count"] = len(value["credential_requirements"])
        value["live_credentials_boundary_ready"] = True
        value["provider_abstraction_ready"] = True
        value["future_tiny_canary_auth_contract_ready"] = True
        value.update(_auth_boundary_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCredentialPresenceStatus:
    requirement_id: str
    env_var_name: str
    present: bool
    redacted_preview: str
    source: str
    safe_for_artifacts: bool = True
    policy_violation: bool = False
    policy_violation_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CREDENTIAL_PRESENCE_STATUS_CONTRACT
        value.update(_auth_boundary_safety_flags())
        return value


@dataclass(frozen=True)
class LiveCredentialsStatusReport:
    report_id: str
    config_id: str
    credential_statuses: tuple[Mapping[str, Any], ...]
    required_credentials_count: int
    present_credentials_count: int
    missing_credentials_count: int
    missing_requirements: tuple[str, ...]
    policy_violation_count: int
    provider_source: str
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_CREDENTIALS_STATUS_REPORT_CONTRACT
        value["credential_statuses"] = [dict(row) for row in self.credential_statuses]
        value["credential_statuses_redacted"] = [dict(row) for row in self.credential_statuses]
        value["missing_requirements"] = list(self.missing_requirements)
        value["all_required_credentials_present"] = self.missing_credentials_count == 0
        value["live_credentials_configured"] = self.missing_credentials_count == 0
        value["safe_for_artifacts"] = True
        value["redacted_credential_status_ready"] = True
        value["live_auth_presence_check_ready"] = True
        value.update(_auth_boundary_safety_flags())
        return value


@dataclass(frozen=True)
class LiveAuthBoundaryViolation:
    violation_id: str
    code: str
    severity: str
    message: str
    blocks_live_execution: bool = True
    blocks_review_ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_AUTH_BOUNDARY_VIOLATION_CONTRACT
        value.update(_auth_boundary_safety_flags())
        return value


@dataclass(frozen=True)
class LiveAuthBoundaryDecision:
    decision_id: str
    config_id: str
    decision_status: str
    boundary_statuses: tuple[str, ...]
    live_credentials_configured: bool
    live_mode_explicitly_requested: bool
    live_auth_ready_for_future_tiny_canary_review: bool
    credential_status_report: Mapping[str, Any]
    violations: tuple[Mapping[str, Any], ...]
    missing_requirements: tuple[str, ...]
    human_summary: str
    authenticated_endpoints_enabled: bool = False
    order_submission_enabled: bool = False
    cryptographic_signing_enabled: bool = False
    wallet_signing_enabled: bool = False
    allowed_for_live: bool = False
    canary_executable_now: bool = False
    live_execution_approved: bool = False
    real_execution_available: bool = False
    live_connector_enabled: bool = False
    generated_at: str = GENERATED_AT

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_AUTH_BOUNDARY_DECISION_CONTRACT
        value["boundary_statuses"] = list(self.boundary_statuses)
        value["credential_status_report"] = dict(self.credential_status_report)
        value["credential_statuses_redacted"] = list(
            self.credential_status_report.get("credential_statuses_redacted", [])
        )
        value["violations"] = [dict(row) for row in self.violations]
        value["missing_requirements"] = list(self.missing_requirements)
        value["live_credentials_boundary_ready"] = True
        value["provider_abstraction_ready"] = True
        value["live_auth_presence_check_ready"] = True
        value["redacted_credential_status_ready"] = True
        value["future_tiny_canary_auth_contract_ready"] = True
        value["safe_for_artifacts"] = True
        value["secrets_redacted"] = True
        value["actual_secret_values_exposed"] = False
        value.update(_auth_boundary_safety_flags())
        return value


class LiveAuthBoundaryProvider:
    provider_source = "injected_provider"

    def credential_present(self, requirement: Mapping[str, Any]) -> bool:
        raise NotImplementedError

    def policy_violation_code(self, requirement: Mapping[str, Any]) -> str:
        return ""

    def source_for_requirement(self, requirement: Mapping[str, Any]) -> str:
        return self.provider_source


class FakeLiveCredentialProvider(LiveAuthBoundaryProvider):
    provider_source = "fake_provider"

    def __init__(
        self,
        configured_values: Mapping[str, Any] | Sequence[str] | None = None,
        *,
        source: str = "fake_provider",
    ) -> None:
        self.provider_source = clean_text(source) or "fake_provider"
        if configured_values is None:
            self._values: dict[str, Any] = {}
        elif isinstance(configured_values, Mapping):
            self._values = {clean_text(key): value for key, value in configured_values.items()}
        else:
            self._values = {clean_text(item): REDACTED_CONFIGURED for item in configured_values}

    def credential_present(self, requirement: Mapping[str, Any]) -> bool:
        value = self._lookup(requirement)
        return clean_text(value) != ""

    def policy_violation_code(self, requirement: Mapping[str, Any]) -> str:
        value = self._lookup(requirement)
        if clean_text(value) and _looks_like_unsafe_provider_value(value):
            return "unsafe_provider_value_pattern"
        return ""

    def _lookup(self, requirement: Mapping[str, Any]) -> Any:
        env_name = clean_text(requirement.get("env_var_name"))
        requirement_id = clean_text(requirement.get("requirement_id"))
        if env_name in self._values:
            return self._values[env_name]
        return self._values.get(requirement_id, "")


class EnvironmentLiveCredentialProvider(LiveAuthBoundaryProvider):
    def __init__(
        self,
        *,
        enabled: bool = False,
        environ: Mapping[str, str] | None = None,
        source: str = "environment_provider",
    ) -> None:
        self.enabled = enabled is True
        self.environ = environ
        self.provider_source = clean_text(source) or "environment_provider"

    def credential_present(self, requirement: Mapping[str, Any]) -> bool:
        if not self.enabled:
            return False
        env_name = clean_text(requirement.get("env_var_name"))
        return clean_text(self._active_environ().get(env_name)) != ""

    def policy_violation_code(self, requirement: Mapping[str, Any]) -> str:
        if not self.enabled:
            return ""
        env_name = clean_text(requirement.get("env_var_name"))
        value = self._active_environ().get(env_name)
        if clean_text(value) and _looks_like_unsafe_provider_value(value):
            return "unsafe_provider_value_pattern"
        return ""

    def source_for_requirement(self, requirement: Mapping[str, Any]) -> str:
        return self.provider_source if self.enabled else "env_provider_disabled"

    def _active_environ(self) -> Mapping[str, str]:
        if self.environ is not None:
            return self.environ
        import os

        return os.environ


def build_default_live_credentials_boundary_config(
    *,
    config_id: str = "live-credentials-auth-boundary-040-default",
    live_mode_explicitly_requested: bool = False,
    credential_requirements: Sequence[Mapping[str, Any]] | None = None,
    allow_environment_provider: bool = False,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    requirements = (
        tuple(_requirement_from_mapping(row) for row in credential_requirements)
        if credential_requirements is not None
        else tuple(
            LiveCredentialRequirement(
                requirement_id=requirement_id,
                env_var_name=env_var_name,
                description=description,
            ).to_dict()
            for requirement_id, env_var_name, description in DEFAULT_LIVE_CREDENTIAL_REQUIREMENTS
        )
    )
    config = LiveCredentialsAuthBoundaryConfig(
        config_id=clean_text(config_id),
        credential_requirements=requirements,
        live_mode_explicitly_requested=live_mode_explicitly_requested is True,
        allow_environment_provider=allow_environment_provider is True,
        generated_at=generated_at,
    ).to_dict()
    validation = validate_live_credentials_boundary_config(config, generated_at=generated_at)
    config["validation"] = validation
    if validation.get("valid") is not True:
        raise ValueError("; ".join(validation.get("errors", [])))
    return config


def validate_live_credentials_boundary_config(
    config: LiveCredentialsAuthBoundaryConfig | Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = _mapping(config)
    errors: list[str] = []
    if value.get("contract_version") != LIVE_CREDENTIALS_AUTH_BOUNDARY_CONFIG_CONTRACT:
        errors.append(f"contract_version must be {LIVE_CREDENTIALS_AUTH_BOUNDARY_CONFIG_CONTRACT}")
    if not clean_text(value.get("config_id")):
        errors.append("config_id must be non-empty")
    requirements = [dict(row) for row in value.get("credential_requirements", []) if isinstance(row, Mapping)]
    if not requirements:
        errors.append("credential_requirements must be non-empty")
    requirement_ids = [clean_text(row.get("requirement_id")) for row in requirements]
    env_names = [clean_text(row.get("env_var_name")) for row in requirements]
    if len(requirement_ids) != len(set(requirement_ids)):
        errors.append("requirement_id values must be unique")
    if len(env_names) != len(set(env_names)):
        errors.append("env_var_name values must be unique")
    for index, requirement in enumerate(requirements):
        if requirement.get("contract_version") != LIVE_CREDENTIAL_REQUIREMENT_CONTRACT:
            errors.append(f"credential_requirements[{index}].contract_version must be {LIVE_CREDENTIAL_REQUIREMENT_CONTRACT}")
        if not clean_text(requirement.get("requirement_id")):
            errors.append(f"credential_requirements[{index}].requirement_id must be non-empty")
        env_name = clean_text(requirement.get("env_var_name"))
        if not env_name or not _is_symbolic_env_var_name(env_name):
            errors.append(f"credential_requirements[{index}].env_var_name must be an uppercase symbolic name")
        if requirement.get("required_for_future_tiny_canary_auth_review") is not True:
            errors.append(f"credential_requirements[{index}] must be required for future tiny canary auth review")
    for field in FORCED_FALSE_EXECUTION_FIELDS[:4]:
        if value.get(field) is not False:
            errors.append(f"{field} must be false in this build")
    if value.get("allow_environment_provider") is not False:
        errors.append("allow_environment_provider must be false by default in this build")
    boundary_validation = validate_secret_boundary_live_credentials_config(value, generated_at=generated_at)
    if boundary_validation.get("valid") is not True:
        errors.append("live credentials config violates secret boundary")
    valid = not errors
    return {
        "contract_version": "pmbot_live_credentials_auth_boundary_config_validation.v1",
        "validation_id": _stable_id(
            "live-credentials-auth-boundary-config-validation-040",
            {"config_id": value.get("config_id"), "errors": errors},
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        "symbolic_credential_names_allowed": True,
        "config_secret_boundary_validation": boundary_validation,
        "live_credentials_boundary_ready": valid,
        "provider_abstraction_ready": True,
        "future_tiny_canary_auth_contract_ready": valid,
        **_auth_boundary_safety_flags(),
    }


def evaluate_live_credentials_status(
    config: LiveCredentialsAuthBoundaryConfig | Mapping[str, Any] | None = None,
    provider: LiveAuthBoundaryProvider | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_config = _mapping(config or build_default_live_credentials_boundary_config(generated_at=generated_at))
    validation = validate_live_credentials_boundary_config(active_config, generated_at=generated_at)
    if validation.get("valid") is not True:
        raise ValueError("; ".join(validation.get("errors", [])))
    active_provider = provider or FakeLiveCredentialProvider()
    statuses: list[dict[str, Any]] = []
    for requirement in active_config.get("credential_requirements", []):
        row = dict(requirement)
        present = active_provider.credential_present(row)
        violation_code = active_provider.policy_violation_code(row)
        statuses.append(
            LiveCredentialPresenceStatus(
                requirement_id=clean_text(row.get("requirement_id")),
                env_var_name=clean_text(row.get("env_var_name")),
                present=present,
                redacted_preview=REDACTED_CONFIGURED if present else REDACTED_MISSING,
                source=active_provider.source_for_requirement(row),
                policy_violation=bool(violation_code),
                policy_violation_code=violation_code,
            ).to_dict()
        )
    missing = [
        clean_text(row.get("requirement_id"))
        for row in statuses
        if row.get("present") is not True
    ]
    report = LiveCredentialsStatusReport(
        report_id=_stable_id(
            "live-credentials-status-report-040",
            {
                "config_id": active_config.get("config_id"),
                "statuses": [
                    {
                        "requirement_id": row.get("requirement_id"),
                        "env_var_name": row.get("env_var_name"),
                        "present": row.get("present"),
                        "source": row.get("source"),
                        "policy_violation": row.get("policy_violation"),
                    }
                    for row in statuses
                ],
            },
        ),
        config_id=clean_text(active_config.get("config_id")),
        credential_statuses=tuple(statuses),
        required_credentials_count=len(statuses),
        present_credentials_count=len([row for row in statuses if row.get("present") is True]),
        missing_credentials_count=len(missing),
        missing_requirements=tuple(missing),
        policy_violation_count=len([row for row in statuses if row.get("policy_violation") is True]),
        provider_source=clean_text(active_provider.provider_source),
        generated_at=generated_at,
    ).to_dict()
    boundary_validation = validate_secret_boundary_live_credentials_status_report(report, generated_at=generated_at)
    report["status_report_secret_boundary_validation"] = boundary_validation
    if boundary_validation.get("valid") is not True:
        report["safe_for_artifacts"] = False
    return report


def evaluate_live_auth_boundary_for_tiny_canary(
    config: LiveCredentialsAuthBoundaryConfig | Mapping[str, Any] | None = None,
    provider: LiveAuthBoundaryProvider | None = None,
    *,
    status_report: Mapping[str, Any] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_config = _mapping(config or build_default_live_credentials_boundary_config(generated_at=generated_at))
    config_validation = validate_live_credentials_boundary_config(active_config, generated_at=generated_at)
    report = dict(
        status_report
        or evaluate_live_credentials_status(active_config, provider, generated_at=generated_at)
    )
    missing = tuple(clean_text(item) for item in report.get("missing_requirements", []) if clean_text(item))
    policy_violations = [
        row for row in report.get("credential_statuses", []) if isinstance(row, Mapping) and row.get("policy_violation") is True
    ]
    violations: list[dict[str, Any]] = []
    if config_validation.get("valid") is not True:
        violations.append(
            _violation(
                DECISION_SECRET_POLICY_VIOLATION,
                "Live credentials/auth config did not pass symbolic-name and secret-boundary validation.",
                blocks_review_ready=True,
            )
        )
    if report.get("safe_for_artifacts") is not True or policy_violations:
        violations.append(
            _violation(
                DECISION_SECRET_POLICY_VIOLATION,
                "Credential status report failed the no-secret artifact policy.",
                blocks_review_ready=True,
            )
        )
    if missing:
        violations.append(
            _violation(
                DECISION_MISSING_REQUIRED_CREDENTIALS,
                "Required live credential names are not all configured in the injected provider.",
                blocks_review_ready=True,
            )
        )
    live_mode_requested = active_config.get("live_mode_explicitly_requested") is True
    if not live_mode_requested:
        violations.append(
            _violation(
                DECISION_LIVE_MODE_NOT_EXPLICITLY_ENABLED,
                "Live mode was not explicitly requested for this boundary review.",
                blocks_review_ready=True,
            )
        )
    disabled_live_gate_violations = (
        _violation(
            DECISION_AUTHENTICATED_ENDPOINTS_STILL_DISABLED,
            "Authenticated endpoint usage remains disabled in this build.",
        ),
        _violation(
            DECISION_SIGNING_STILL_DISABLED,
            "Cryptographic and wallet signing remain disabled in this build.",
        ),
        _violation(
            DECISION_ORDER_SUBMISSION_STILL_DISABLED,
            "Order submission remains disabled in this build.",
        ),
    )
    violations.extend(disabled_live_gate_violations)
    review_blockers = [row for row in violations if row.get("blocks_review_ready") is True]
    if any(row.get("code") == DECISION_SECRET_POLICY_VIOLATION for row in review_blockers):
        decision_status = DECISION_SECRET_POLICY_VIOLATION
    elif any(row.get("code") == DECISION_MISSING_REQUIRED_CREDENTIALS for row in review_blockers):
        decision_status = DECISION_MISSING_REQUIRED_CREDENTIALS
    elif any(row.get("code") == DECISION_LIVE_MODE_NOT_EXPLICITLY_ENABLED for row in review_blockers):
        decision_status = DECISION_LIVE_MODE_NOT_EXPLICITLY_ENABLED
    else:
        decision_status = DECISION_AUTH_BOUNDARY_REVIEW_READY
    live_credentials_configured = report.get("live_credentials_configured") is True
    review_ready = (
        decision_status == DECISION_AUTH_BOUNDARY_REVIEW_READY
        and live_credentials_configured
        and live_mode_requested
    )
    statuses = _dedupe([decision_status] + [row.get("code", "") for row in violations])
    decision = LiveAuthBoundaryDecision(
        decision_id=_stable_id(
            "live-auth-boundary-decision-040",
            {
                "config_id": active_config.get("config_id"),
                "decision_status": decision_status,
                "boundary_statuses": statuses,
                "missing": missing,
            },
        ),
        config_id=clean_text(active_config.get("config_id")),
        decision_status=decision_status,
        boundary_statuses=tuple(statuses),
        live_credentials_configured=live_credentials_configured,
        live_mode_explicitly_requested=live_mode_requested,
        live_auth_ready_for_future_tiny_canary_review=review_ready,
        credential_status_report=report,
        violations=tuple(violations),
        missing_requirements=missing,
        human_summary=_human_summary(
            decision_status=decision_status,
            live_credentials_configured=live_credentials_configured,
            live_mode_requested=live_mode_requested,
        ),
        generated_at=generated_at,
    ).to_dict()
    boundary_validation = validate_secret_boundary_live_auth_boundary_decision(decision, generated_at=generated_at)
    decision["auth_boundary_decision_secret_boundary_validation"] = boundary_validation
    if boundary_validation.get("valid") is not True:
        decision["decision_status"] = DECISION_SECRET_POLICY_VIOLATION
        decision["live_auth_ready_for_future_tiny_canary_review"] = False
    return decision


def summarize_live_credentials_status(
    value: Mapping[str, Any] | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active = dict(value or evaluate_live_auth_boundary_for_tiny_canary(generated_at=generated_at))
    report = dict(active.get("credential_status_report", active))
    statuses = [
        dict(row)
        for row in (
            active.get("credential_statuses_redacted")
            or report.get("credential_statuses_redacted")
            or report.get("credential_statuses")
            or []
        )
        if isinstance(row, Mapping)
    ]
    decision_status = clean_text(
        active.get("decision_status")
        or report.get("status")
        or DECISION_MISSING_REQUIRED_CREDENTIALS
    )
    summary = {
        "contract_version": LIVE_CREDENTIALS_AUTH_BOUNDARY_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "live-credentials-auth-boundary-summary-040",
            {
                "decision_status": decision_status,
                "report_id": report.get("report_id"),
                "configured": active.get("live_credentials_configured", report.get("live_credentials_configured")),
            },
        ),
        "generated_at": generated_at,
        "live_credentials_boundary_status": decision_status,
        "decision_status": decision_status,
        "boundary_statuses": list(active.get("boundary_statuses", [decision_status])),
        "live_credentials_configured": (
            active.get("live_credentials_configured") is True
            or report.get("live_credentials_configured") is True
        ),
        "live_mode_explicitly_requested": active.get("live_mode_explicitly_requested") is True,
        "live_auth_ready_for_future_tiny_canary_review": (
            active.get("live_auth_ready_for_future_tiny_canary_review") is True
        ),
        "required_credentials_count": int(report.get("required_credentials_count", len(statuses)) or 0),
        "present_credentials_count": int(report.get("present_credentials_count", 0) or 0),
        "missing_credentials_count": int(report.get("missing_credentials_count", 0) or 0),
        "missing_requirements": list(active.get("missing_requirements", report.get("missing_requirements", []))),
        "credential_statuses_redacted": statuses,
        "warning": UI_REDACTION_WARNING,
        "authenticated_endpoints_enabled": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "wallet_signing_enabled": False,
        "order_submission_enabled": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "safe_for_artifacts": True,
        "secrets_redacted": True,
        "actual_secret_values_exposed": False,
        "live_credentials_boundary_ready": True,
        "provider_abstraction_ready": True,
        "redacted_credential_status_ready": True,
        "future_tiny_canary_auth_contract_ready": True,
    }
    summary.update(_auth_boundary_safety_flags())
    return summary


def _requirement_from_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return LiveCredentialRequirement(
        requirement_id=clean_text(value.get("requirement_id")),
        env_var_name=clean_text(value.get("env_var_name")),
        description=clean_text(value.get("description")),
        required_for_future_tiny_canary_auth_review=(
            value.get("required_for_future_tiny_canary_auth_review") is not False
        ),
    ).to_dict()


def _violation(code: str, message: str, *, blocks_review_ready: bool = False) -> dict[str, Any]:
    return LiveAuthBoundaryViolation(
        violation_id=_stable_id("live-auth-boundary-violation-040", {"code": code, "message": message}),
        code=clean_text(code),
        severity="critical",
        message=clean_text(message),
        blocks_live_execution=True,
        blocks_review_ready=blocks_review_ready,
    ).to_dict()


def _human_summary(
    *,
    decision_status: str,
    live_credentials_configured: bool,
    live_mode_requested: bool,
) -> str:
    if decision_status == DECISION_AUTH_BOUNDARY_REVIEW_READY:
        return (
            "Live credential names are configured in the injected provider and redacted for review. "
            "Authenticated endpoints, signing, and order submission remain disabled, so the canary is not executable."
        )
    if decision_status == DECISION_MISSING_REQUIRED_CREDENTIALS:
        return "Required live credential names are missing; dry-run review may continue but live remains blocked."
    if decision_status == DECISION_LIVE_MODE_NOT_EXPLICITLY_ENABLED:
        return "Live mode was not explicitly requested; the boundary stays review-only and non-executable."
    if decision_status == DECISION_SECRET_POLICY_VIOLATION:
        return "A secret boundary policy violation was detected; no live auth review is ready."
    return (
        f"Live credentials configured={str(live_credentials_configured).lower()}, "
        f"live mode requested={str(live_mode_requested).lower()}; live remains unavailable."
    )


def _is_symbolic_env_var_name(value: str) -> bool:
    return re.fullmatch(r"[A-Z][A-Z0-9_]*", clean_text(value)) is not None


def _looks_like_unsafe_provider_value(value: Any) -> bool:
    text = clean_text(value)
    if not text:
        return False
    lowered = text.lower()
    if "-----begin" in lowered and "private key" in lowered:
        return True
    if lowered.startswith("bearer "):
        return True
    if lowered.startswith(("sk-", "sk_live_", "pk_live_")):
        return True
    if re.fullmatch(r"0x[a-fA-F0-9]{64,}", text):
        return True
    return any(
        marker in lowered
        for marker in (
            "mnemonic:",
            "seed phrase:",
            "seed_phrase=",
            "raw_secret=",
            "signed_order",
            "signed_payload",
            "raw_transaction",
            "auth_header=",
        )
    )


def _mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError("live credentials auth boundary value must be a mapping or expose to_dict()")


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, sort_keys=True)
        return value
    except TypeError:
        if isinstance(value, Mapping):
            return {clean_text(key): _json_safe(nested) for key, nested in value.items()}
        if isinstance(value, list):
            return [_json_safe(item) for item in value]
        return clean_text(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(_json_safe(payload), sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _auth_boundary_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "static_artifact_only": True,
        "passive_artifact_only": True,
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "execution_enabling": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_secret_values_printed": False,
        "raw_secret_values_persisted": False,
        "real_wallet_integration_added": False,
        "real_wallet_access_performed": False,
        "private_key_or_mnemonic_handling_added": False,
        "cryptographic_signing_added": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "wallet_signing_added": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "transaction_signing_added": False,
        "transaction_signing_performed": False,
        "real_order_placement_added": False,
        "real_order_placement_performed": False,
        "authenticated_endpoint_added": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_endpoint_call_performed": False,
        "order_submission_enabled": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "outcome_resolution_invented": False,
        "price_data_invented": False,
        "fill_data_invented": False,
        "pnl_invented": False,
        "safety_summary": trading_core_safety_summary(),
    }
