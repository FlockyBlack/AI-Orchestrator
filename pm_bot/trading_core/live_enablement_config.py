from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.authenticated_polymarket_connector import (
    CREDENTIAL_STATUS_ENV_VARS as AUTHENTICATED_POLYMARKET_CREDENTIAL_STATUS_ENV_VARS,
    build_authenticated_connector_capability_report,
    summarize_authenticated_connector_capability_report,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, trading_core_safety_summary
from pm_bot.trading_core.secret_boundary_policy import validate_static_secret_boundary
from pm_bot.trading_core.wallet_signing_boundary import (
    SAFE_ENV_CONFIG_KEYS as WALLET_SIGNING_SAFE_ENV_CONFIG_KEYS,
    build_wallet_signing_boundary_report,
    summarize_wallet_signing_boundary_report,
)

LIVE_ENABLEMENT_CONFIG_PREFLIGHT_CONTRACT = "pmbot_live_enablement_config_preflight.v1"
LIVE_ENABLEMENT_CONFIG_PREFLIGHT_SUMMARY_CONTRACT = (
    "pmbot_live_enablement_config_preflight_summary.v1"
)
LIVE_ENABLEMENT_CONFIG_PREFLIGHT_VALIDATION_CONTRACT = (
    "pmbot_live_enablement_config_preflight_validation.v1"
)

SCHEMA_VERSION = "047.v1"
CONTRACT_NAME = "pmbot_live_enablement_config_contract_and_runtime_preflight"

STATUS_CONFIG_MISSING_BLOCKED = "CONFIG_MISSING_BLOCKED"
STATUS_CONFIG_INVALID_BLOCKED = "CONFIG_INVALID_BLOCKED"
STATUS_LIVE_FLAGS_REQUESTED_BUT_BLOCKED = "LIVE_FLAGS_REQUESTED_BUT_BLOCKED"
STATUS_REVIEW_ONLY_PREFLIGHT_READY = "REVIEW_ONLY_PREFLIGHT_READY"

FORBIDDEN_LIVE_STATUSES = {
    "LIVE_READY",
    "GO_FOR_LIVE",
    "EXECUTION_ENABLED",
    "ORDER_SUBMISSION_ENABLED",
}

TRUE_STRINGS = frozenset({"true", "1", "yes"})
FALSE_STRINGS = frozenset({"false", "0", "no"})
ACCEPTED_BOOLEAN_STRINGS = tuple(sorted(TRUE_STRINGS | FALSE_STRINGS))

LIVE_FLAG_ENV_VARS = (
    "PMBOT_LIVE_MODE",
    "PMBOT_LIVE_CANARY_ENABLED",
    "PMBOT_ORDER_SUBMISSION_ENABLED",
    "PMBOT_AUTHENTICATED_POLYMARKET_ENABLED",
    "PMBOT_WALLET_SIGNING_ENABLED",
)
REQUIRED_BOOLEAN_ENV_VARS = (
    *LIVE_FLAG_ENV_VARS,
    "PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL",
    "PMBOT_REQUIRE_KILL_SWITCH_READY",
)
RISK_LIMIT_ENV_VARS = (
    "PMBOT_MAX_ORDER_NOTIONAL_USD",
    "PMBOT_DAILY_LOSS_CAP_USD",
    "PMBOT_TOTAL_EXPOSURE_CAP_USD",
    "PMBOT_MAX_LIVE_TRADES_PER_DAY",
)
MARKET_SCOPE_ENV_VARS = (
    "PMBOT_ALLOWED_MARKET_SLUGS",
    "PMBOT_ALLOWED_MARKET_IDS",
)
WALLET_SIGNING_BOUNDARY_MARKER_ENV_VARS = (
    "PMBOT_WALLET_ADDRESS_CONFIGURED",
    "PMBOT_SIGNING_PROVIDER_CONFIGURED",
    "PMBOT_SIGNING_DRY_RUN_ONLY",
)
KNOWN_CONFIG_ENV_VARS = (
    *REQUIRED_BOOLEAN_ENV_VARS,
    *RISK_LIMIT_ENV_VARS,
    *MARKET_SCOPE_ENV_VARS,
    *AUTHENTICATED_POLYMARKET_CREDENTIAL_STATUS_ENV_VARS,
    *WALLET_SIGNING_BOUNDARY_MARKER_ENV_VARS,
)

FORCED_FALSE_EXECUTION_FIELDS = (
    "allowed_for_live",
    "canary_executable_now",
    "live_execution_approved",
    "real_execution_available",
    "live_connector_enabled",
    "order_submission_enabled",
    "authenticated_polymarket_enabled",
    "wallet_signing_enabled",
    "transaction_signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_endpoints_enabled",
    "signing_enabled",
    "cryptographic_signing_enabled",
    "wallet_enabled",
    "would_submit_order",
    "real_order_submitted",
    "live_execution_allowed",
    "live_execution_enabled",
    "live_execution_performed",
    "execution_enabling",
    "execution_enabled",
    "live_action_exposed",
)


@dataclass(frozen=True)
class LiveEnablementConfigPreflight:
    preflight_id: str
    schema_version: str
    contract_name: str
    status: str
    config_source: str
    generated_at: str
    parsed_flags_summary: Mapping[str, Any]
    risk_limit_config_summary: Mapping[str, Any]
    allowed_market_scope_summary: Mapping[str, Any]
    manual_approval_requirement_summary: Mapping[str, Any]
    kill_switch_requirement_summary: Mapping[str, Any]
    authenticated_polymarket_connector_scaffold_summary: Mapping[str, Any]
    wallet_signing_boundary_summary: Mapping[str, Any]
    blocked_reasons: tuple[str, ...]
    violation_reasons: tuple[str, ...]
    operator_required_actions: tuple[str, ...]
    future_live_requested: bool
    dry_run_review_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["contract_version"] = LIVE_ENABLEMENT_CONFIG_PREFLIGHT_CONTRACT
        value["parsed_flags_summary"] = dict(self.parsed_flags_summary)
        value["risk_limit_config_summary"] = dict(self.risk_limit_config_summary)
        value["allowed_market_scope_summary"] = dict(self.allowed_market_scope_summary)
        value["manual_approval_requirement_summary"] = dict(self.manual_approval_requirement_summary)
        value["kill_switch_requirement_summary"] = dict(self.kill_switch_requirement_summary)
        value["authenticated_polymarket_connector_scaffold_summary"] = dict(
            self.authenticated_polymarket_connector_scaffold_summary
        )
        value["wallet_signing_boundary_summary"] = dict(self.wallet_signing_boundary_summary)
        value["blocked_reasons"] = list(self.blocked_reasons)
        value["violation_reasons"] = list(self.violation_reasons)
        value["operator_required_actions"] = list(self.operator_required_actions)
        value["allowed_for_dry_run_review"] = self.dry_run_review_allowed
        value["review_only"] = True
        value["execution_enabling"] = False
        value["live_approval"] = False
        value["resolved_blocker_count"] = 0
        value["unresolved_blocker_count"] = len(self.blocked_reasons) + len(self.violation_reasons)
        value["no_raw_secrets_parsed_or_emitted"] = True
        value["config_values_redacted_where_sensitive"] = True
        value.update(_preflight_safety_flags())
        return value


def build_live_enablement_config_preflight(
    config: Mapping[str, Any] | None = None,
    *,
    config_source: str = "provided_mapping",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    source = {clean_text(key): value for key, value in dict(config or {}).items()}
    flags = _parse_flags(source)
    risk_limits = _parse_risk_limits(source)
    market_scope = _parse_market_scope(source)
    manual_approval = _manual_approval_summary(flags)
    kill_switch = _kill_switch_summary(flags)
    authenticated_connector_report = build_authenticated_connector_capability_report(
        source,
        generated_at=generated_at,
    )
    authenticated_connector_summary = summarize_authenticated_connector_capability_report(
        authenticated_connector_report,
        generated_at=generated_at,
    )
    wallet_signing_boundary = build_wallet_signing_boundary_report(
        {
            env_var: source[env_var]
            for env_var in WALLET_SIGNING_SAFE_ENV_CONFIG_KEYS
            if env_var in source
        },
        config_source=f"{clean_text(config_source) or 'provided_mapping'}:wallet_signing_boundary_safe_markers",
        generated_at=generated_at,
    )
    wallet_signing_boundary_summary = summarize_wallet_signing_boundary_report(
        wallet_signing_boundary,
        generated_at=generated_at,
    )

    missing = _missing_required_config(flags, risk_limits, market_scope)
    violations = _validation_violations(flags, risk_limits, market_scope)
    live_requested_flags = [
        env_var
        for env_var in LIVE_FLAG_ENV_VARS
        if dict(flags["flags"][env_var]).get("parsed_value") is True
    ]
    future_live_requested = bool(live_requested_flags)

    blocked_reasons: list[str] = []
    if missing:
        blocked_reasons.append("missing_required_live_enablement_config")
        blocked_reasons.extend(f"missing:{item}" for item in missing)
    if future_live_requested:
        blocked_reasons.append("operator_requested_live_flags_but_task_047_blocks_live_execution")
        blocked_reasons.extend(f"requested_but_blocked:{item}" for item in live_requested_flags)
    if manual_approval.get("requirement_satisfied") is not True:
        blocked_reasons.append("manual_operator_approval_requirement_not_satisfied")
    if kill_switch.get("requirement_satisfied") is not True:
        blocked_reasons.append("kill_switch_ready_requirement_not_satisfied")
    blocked_reasons.append("task_047_does_not_enable_live_execution")

    status = _status(
        missing_required=bool(missing),
        invalid=bool(violations),
        future_live_requested=future_live_requested,
    )
    dry_run_review_allowed = status == STATUS_REVIEW_ONLY_PREFLIGHT_READY
    if dry_run_review_allowed:
        blocked_reasons = ["live_execution_still_disabled_by_task_047_review_only_contract"]
    blocked_reasons.append("wallet_signing_boundary_scaffold_dry_run_only_review_only")

    preflight_id = _stable_id(
        "live-enablement-config-preflight-047",
        {
            "status": status,
            "config_source": clean_text(config_source),
            "flags": flags,
            "risk_limits": risk_limits,
            "market_scope": market_scope,
            "violations": violations,
        },
    )
    preflight = LiveEnablementConfigPreflight(
        preflight_id=preflight_id,
        schema_version=SCHEMA_VERSION,
        contract_name=CONTRACT_NAME,
        status=status,
        config_source=clean_text(config_source) or "provided_mapping",
        generated_at=generated_at,
        parsed_flags_summary=flags,
        risk_limit_config_summary=risk_limits,
        allowed_market_scope_summary=market_scope,
        manual_approval_requirement_summary=manual_approval,
        kill_switch_requirement_summary=kill_switch,
        authenticated_polymarket_connector_scaffold_summary=authenticated_connector_summary,
        wallet_signing_boundary_summary=wallet_signing_boundary_summary,
        blocked_reasons=tuple(_dedupe(blocked_reasons)),
        violation_reasons=tuple(_dedupe(violations)),
        operator_required_actions=tuple(
            _operator_required_actions(
                status=status,
                missing_required=missing,
                violations=violations,
                future_live_requested=future_live_requested,
            )
        ),
        future_live_requested=future_live_requested,
        dry_run_review_allowed=dry_run_review_allowed,
    ).to_dict()
    validation = validate_live_enablement_config_preflight(preflight, generated_at=generated_at)
    preflight["validation"] = validation
    if validation.get("valid") is not True and preflight["status"] == STATUS_REVIEW_ONLY_PREFLIGHT_READY:
        preflight["status"] = STATUS_CONFIG_INVALID_BLOCKED
        preflight["dry_run_review_allowed"] = False
        preflight["allowed_for_dry_run_review"] = False
        preflight["validation"] = validate_live_enablement_config_preflight(
            preflight,
            generated_at=generated_at,
        )
    return preflight


def build_live_enablement_config_preflight_from_env(
    environ: Mapping[str, str] | None = None,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if environ is None:
        import os

        active_environ: Mapping[str, Any] = os.environ
    else:
        active_environ = environ
    return build_live_enablement_config_preflight(
        {env_var: active_environ.get(env_var) for env_var in KNOWN_CONFIG_ENV_VARS if env_var in active_environ},
        config_source="environment_whitelisted_non_secret_keys",
        generated_at=generated_at,
    )


def summarize_live_enablement_config_preflight(
    preflight: Mapping[str, Any] | None = None,
    *,
    latest_live_enablement_config_preflight_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(preflight or build_live_enablement_config_preflight(generated_at=generated_at))
    validation = (
        dict(value.get("validation", {}))
        if isinstance(value.get("validation"), Mapping)
        else validate_live_enablement_config_preflight(value, generated_at=generated_at)
        if value
        else {"valid": False, "status": "blocked", "errors": ["preflight not provided"]}
    )
    risk = dict(value.get("risk_limit_config_summary", {}))
    market = dict(value.get("allowed_market_scope_summary", {}))
    manual = dict(value.get("manual_approval_requirement_summary", {}))
    kill_switch = dict(value.get("kill_switch_requirement_summary", {}))
    authenticated_connector = dict(value.get("authenticated_polymarket_connector_scaffold_summary", {}))
    wallet_signing_boundary = dict(value.get("wallet_signing_boundary_summary", {}))
    summary = {
        "contract_version": LIVE_ENABLEMENT_CONFIG_PREFLIGHT_SUMMARY_CONTRACT,
        "summary_id": _stable_id(
            "live-enablement-config-preflight-summary-047",
            {
                "preflight_id": value.get("preflight_id"),
                "status": value.get("status"),
                "latest_path": clean_text(latest_live_enablement_config_preflight_path),
            },
        ),
        "schema_version": SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "generated_at": generated_at,
        "preflight_id": clean_text(value.get("preflight_id")),
        "status": clean_text(value.get("status") or STATUS_CONFIG_MISSING_BLOCKED),
        "config_source": clean_text(value.get("config_source")),
        "future_live_requested": value.get("future_live_requested") is True,
        "dry_run_review_allowed": value.get("dry_run_review_allowed") is True,
        "allowed_for_dry_run_review": value.get("allowed_for_dry_run_review") is True,
        "risk_limits_configured": risk.get("risk_limits_configured") is True,
        "risk_limit_invalid_count": int(risk.get("invalid_count", 0) or 0),
        "allowed_market_scope_configured": market.get("configured") is True,
        "allowed_market_scope_valid": market.get("valid") is True,
        "allowed_market_count": int(market.get("allowed_market_count", 0) or 0),
        "manual_operator_approval_required": manual.get("requirement_satisfied") is True,
        "kill_switch_ready_required": kill_switch.get("requirement_satisfied") is True,
        "authenticated_polymarket_connector_scaffold_status": clean_text(
            authenticated_connector.get("status") or "REVIEW_ONLY"
        ),
        "authenticated_polymarket_connector_scaffold_review_only": (
            authenticated_connector.get("review_only") is True
        ),
        "authenticated_polymarket_connector_network_calls_enabled": False,
        "authenticated_polymarket_connector_authenticated_calls_enabled": False,
        "authenticated_polymarket_connector_order_submission_enabled": False,
        "authenticated_polymarket_connector_credentials_redacted_or_missing_only": (
            authenticated_connector.get("credentials_redacted_or_missing_only") is not False
        ),
        "wallet_signing_boundary_status": clean_text(
            wallet_signing_boundary.get("status") or "SIGNING_DISABLED_REVIEW_ONLY"
        ),
        "wallet_signing_boundary_review_only": wallet_signing_boundary.get("review_only") is not False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "transaction_signing_enabled": False,
        "blocked_reasons": list(value.get("blocked_reasons", []))[:8],
        "top_blocked_reasons": list(value.get("blocked_reasons", []))[:5],
        "violation_reasons": list(value.get("violation_reasons", []))[:8],
        "validation_status": clean_text(validation.get("status") or "blocked"),
        "validation_valid": validation.get("valid") is True,
        "latest_live_enablement_config_preflight_path": clean_text(
            latest_live_enablement_config_preflight_path
            or value.get("latest_live_enablement_config_preflight_path")
        ),
        "review_only": True,
        "execution_enabling": False,
        "live_approval": False,
        "resolved_blocker_count": 0,
        "no_executable_action": True,
        "no_raw_secrets_parsed_or_emitted": True,
    }
    summary.update(_preflight_safety_flags())
    return summary


def validate_live_enablement_config_preflight(
    preflight: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(preflight or {})
    errors: list[str] = []
    statuses: list[str] = []
    if value.get("contract_version") != LIVE_ENABLEMENT_CONFIG_PREFLIGHT_CONTRACT:
        errors.append(f"contract_version must be {LIVE_ENABLEMENT_CONFIG_PREFLIGHT_CONTRACT}")
        statuses.append("invalid_contract")
    if clean_text(value.get("schema_version")) != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
        statuses.append("invalid_schema_version")
    if clean_text(value.get("contract_name")) != CONTRACT_NAME:
        errors.append(f"contract_name must be {CONTRACT_NAME}")
        statuses.append("invalid_contract_name")
    status = clean_text(value.get("status"))
    if status in FORBIDDEN_LIVE_STATUSES:
        errors.append(f"{status} is forbidden in task 047")
        statuses.append("forbidden_live_status")
    if status not in {
        STATUS_CONFIG_MISSING_BLOCKED,
        STATUS_CONFIG_INVALID_BLOCKED,
        STATUS_LIVE_FLAGS_REQUESTED_BUT_BLOCKED,
        STATUS_REVIEW_ONLY_PREFLIGHT_READY,
    }:
        errors.append("status is not a supported 047 preflight status")
        statuses.append("unsupported_status")
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_execution_flag_detected")
    for path, key, nested in _walk_flags(value):
        if key in FORCED_FALSE_EXECUTION_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_execution_flag_detected")
        if clean_text(nested).upper() in FORBIDDEN_LIVE_STATUSES:
            errors.append(f"{path}.{key} must not contain forbidden live status {nested}")
            statuses.append("forbidden_live_status")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must remain 0")
        statuses.append("resolved_blocker_detected")
    if value.get("live_approval") is not False:
        errors.append("live_approval must be false")
        statuses.append("live_approval_detected")
    if value.get("execution_enabling") is not False:
        errors.append("execution_enabling must be false")
        statuses.append("execution_enabling_detected")
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
        statuses.append("review_only_missing")
    if status == STATUS_REVIEW_ONLY_PREFLIGHT_READY and value.get("dry_run_review_allowed") is not True:
        errors.append("REVIEW_ONLY_PREFLIGHT_READY requires dry_run_review_allowed true")
        statuses.append("review_only_not_marked_ready")
    if status != STATUS_REVIEW_ONLY_PREFLIGHT_READY and value.get("dry_run_review_allowed") is not False:
        errors.append("blocked preflight statuses require dry_run_review_allowed false")
        statuses.append("blocked_status_marked_dry_run_ready")
    if value.get("allowed_for_live") is not False:
        errors.append("allowed_for_live must remain false")
        statuses.append("allowed_for_live_detected")
    if value.get("future_live_requested") is True and status != STATUS_LIVE_FLAGS_REQUESTED_BUT_BLOCKED:
        if status not in {STATUS_CONFIG_INVALID_BLOCKED, STATUS_CONFIG_MISSING_BLOCKED}:
            errors.append(
                "future_live_requested requires LIVE_FLAGS_REQUESTED_BUT_BLOCKED unless config is missing or invalid"
            )
            statuses.append("future_live_request_status_mismatch")

    secret_validation = validate_static_secret_boundary(
        value,
        artifact_type="live_enablement_config_preflight",
        generated_at=generated_at,
    )
    if secret_validation.get("valid") is not True:
        errors.append("live enablement config preflight violates static secret boundary")
        statuses.append("secret_boundary_blocked")

    valid = not errors
    if valid:
        statuses = ["live_enablement_config_preflight_valid"]
    else:
        statuses = _dedupe(statuses)
    return {
        "contract_version": LIVE_ENABLEMENT_CONFIG_PREFLIGHT_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "live-enablement-config-preflight-validation-047",
            {
                "preflight_id": value.get("preflight_id"),
                "status": status,
                "errors": errors,
            },
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "statuses": statuses,
        "errors": errors,
        "secret_boundary_validation": secret_validation,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "authenticated_polymarket_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "transaction_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "resolved_blocker_count": 0,
    }


def _parse_flags(config: Mapping[str, Any]) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    invalid: list[str] = []
    missing: list[str] = []
    for env_var in REQUIRED_BOOLEAN_ENV_VARS:
        configured = env_var in config
        parsed_value = False
        state = "missing"
        invalid_reason = ""
        if configured:
            parsed, reason = _parse_bool(config.get(env_var))
            if reason:
                state = "invalid"
                invalid_reason = reason
                invalid.append(env_var)
            else:
                parsed_value = parsed is True
                state = "configured"
        else:
            missing.append(env_var)
        rows[env_var] = {
            "env_var_name": env_var,
            "configured": configured,
            "state": state,
            "missing": not configured,
            "invalid": state == "invalid",
            "accepted_values": list(ACCEPTED_BOOLEAN_STRINGS),
            "parsed_value": parsed_value,
            "requested_value": parsed_value,
            "effective_value": False if env_var in LIVE_FLAG_ENV_VARS else parsed_value,
            "requested_but_blocked": env_var in LIVE_FLAG_ENV_VARS and parsed_value is True,
            "invalid_reason": invalid_reason,
        }
    return {
        "contract_version": "pmbot_live_enablement_config_flags_summary.v1",
        "boolean_parse_policy": "case_insensitive_true_false_1_0_yes_no_only",
        "flags": rows,
        "configured_count": len([row for row in rows.values() if row["configured"]]),
        "missing_count": len(missing),
        "invalid_count": len(invalid),
        "missing_env_vars": missing,
        "invalid_env_vars": invalid,
        "operator_requested_live_flags": [
            env_var for env_var in LIVE_FLAG_ENV_VARS if rows[env_var]["parsed_value"] is True
        ],
        "future_live_requested": any(rows[env_var]["parsed_value"] is True for env_var in LIVE_FLAG_ENV_VARS),
        "all_live_execution_flags_effective_false": True,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "authenticated_polymarket_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "transaction_signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
    }


def _parse_risk_limits(config: Mapping[str, Any]) -> dict[str, Any]:
    limits: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    invalid: list[str] = []
    for env_var in RISK_LIMIT_ENV_VARS:
        configured = env_var in config
        state = "missing"
        parsed_value: float | int | None = None
        invalid_reason = ""
        if configured:
            if env_var == "PMBOT_MAX_LIVE_TRADES_PER_DAY":
                parsed_int, reason = _parse_positive_int(config.get(env_var))
                if reason:
                    state = "invalid"
                    invalid_reason = reason
                    invalid.append(env_var)
                else:
                    state = "configured"
                    parsed_value = parsed_int
            else:
                parsed_decimal, reason = _parse_positive_decimal(config.get(env_var))
                if reason:
                    state = "invalid"
                    invalid_reason = reason
                    invalid.append(env_var)
                else:
                    state = "configured"
                    parsed_value = float(parsed_decimal)
        else:
            missing.append(env_var)
        limits[env_var] = {
            "env_var_name": env_var,
            "configured": configured,
            "state": state,
            "missing": not configured,
            "invalid": state == "invalid",
            "parsed_value": parsed_value,
            "invalid_reason": invalid_reason,
            "raw_value_emitted": False,
        }
    return {
        "contract_version": "pmbot_live_enablement_risk_limit_config_summary.v1",
        "limits": limits,
        "risk_limits_configured": not missing and not invalid,
        "configured_count": len([row for row in limits.values() if row["configured"]]),
        "missing_count": len(missing),
        "invalid_count": len(invalid),
        "missing_env_vars": missing,
        "invalid_env_vars": invalid,
        "numeric_parse_policy": "positive finite numeric values required; max trades per day requires positive integer",
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
    }


def _parse_market_scope(config: Mapping[str, Any]) -> dict[str, Any]:
    configured_slug = "PMBOT_ALLOWED_MARKET_SLUGS" in config
    configured_ids = "PMBOT_ALLOWED_MARKET_IDS" in config
    raw_scope_type = "missing"
    values: list[str] = []
    redacted_count = 0
    invalid_reasons: list[str] = []
    if configured_slug and configured_ids:
        raw_scope_type = "invalid_multiple_scope_env_vars"
        invalid_reasons.append("configure exactly one of PMBOT_ALLOWED_MARKET_SLUGS or PMBOT_ALLOWED_MARKET_IDS")
        values = [
            *_parse_csv_values(config.get("PMBOT_ALLOWED_MARKET_SLUGS")),
            *_parse_csv_values(config.get("PMBOT_ALLOWED_MARKET_IDS")),
        ]
    elif configured_slug:
        raw_scope_type = "market_slugs"
        values = _parse_csv_values(config.get("PMBOT_ALLOWED_MARKET_SLUGS"))
    elif configured_ids:
        raw_scope_type = "market_ids"
        values = _parse_csv_values(config.get("PMBOT_ALLOWED_MARKET_IDS"))

    safe_values = []
    for item in values:
        if _looks_sensitive_config_value(item):
            safe_values.append("<redacted:sensitive_config_value>")
            redacted_count += 1
        else:
            safe_values.append(item)

    if configured_slug or configured_ids:
        if not values:
            invalid_reasons.append("market scope must include exactly one non-empty value")
        if len(values) != 1:
            invalid_reasons.append("market scope must include exactly one BTC-related market")
        if len(values) == 1 and not _is_btc_related_market_value(values[0]):
            invalid_reasons.append("allowed market must be BTC-related")
        if redacted_count:
            invalid_reasons.append("market scope contained sensitive-looking value and was redacted")

    configured = configured_slug or configured_ids
    valid = configured and not invalid_reasons
    state = "configured" if valid else "invalid" if configured else "missing"
    btc_related_values = [item for item in values if _is_btc_related_market_value(item)]
    return {
        "contract_version": "pmbot_live_enablement_allowed_market_scope_summary.v1",
        "configured": configured,
        "state": state,
        "scope_type": raw_scope_type,
        "valid": valid,
        "allowed_market_count": len(values),
        "btc_related_market_count": len(btc_related_values),
        "exactly_one_btc_related_market": len(values) == 1 and len(btc_related_values) == 1,
        "allowed_market_slugs": safe_values if raw_scope_type == "market_slugs" else [],
        "allowed_market_ids": safe_values if raw_scope_type == "market_ids" else [],
        "raw_values_emitted": False,
        "redacted_sensitive_value_count": redacted_count,
        "invalid_reasons": invalid_reasons,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
    }


def _manual_approval_summary(flags: Mapping[str, Any]) -> dict[str, Any]:
    flag = dict(dict(flags.get("flags", {})).get("PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL", {}))
    return {
        "contract_version": "pmbot_live_enablement_manual_approval_requirement_summary.v1",
        "env_var_name": "PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL",
        "configured": flag.get("configured") is True,
        "state": clean_text(flag.get("state") or "missing"),
        "required_value": True,
        "parsed_value": flag.get("parsed_value") is True,
        "requirement_satisfied": flag.get("parsed_value") is True and flag.get("state") == "configured",
        "manual_operator_approval_required": flag.get("parsed_value") is True,
        "live_approval": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
    }


def _kill_switch_summary(flags: Mapping[str, Any]) -> dict[str, Any]:
    flag = dict(dict(flags.get("flags", {})).get("PMBOT_REQUIRE_KILL_SWITCH_READY", {}))
    return {
        "contract_version": "pmbot_live_enablement_kill_switch_requirement_summary.v1",
        "env_var_name": "PMBOT_REQUIRE_KILL_SWITCH_READY",
        "configured": flag.get("configured") is True,
        "state": clean_text(flag.get("state") or "missing"),
        "required_value": True,
        "parsed_value": flag.get("parsed_value") is True,
        "requirement_satisfied": flag.get("parsed_value") is True and flag.get("state") == "configured",
        "kill_switch_ready_required": flag.get("parsed_value") is True,
        "kill_switch_verified_for_live": False,
        "kill_switch_blocks_live_execution": True,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
    }


def _missing_required_config(
    flags: Mapping[str, Any],
    risk_limits: Mapping[str, Any],
    market_scope: Mapping[str, Any],
) -> list[str]:
    missing = list(flags.get("missing_env_vars", []))
    missing.extend(risk_limits.get("missing_env_vars", []))
    if market_scope.get("configured") is not True:
        missing.append("PMBOT_ALLOWED_MARKET_SLUGS_OR_PMBOT_ALLOWED_MARKET_IDS")
    return _dedupe(missing)


def _validation_violations(
    flags: Mapping[str, Any],
    risk_limits: Mapping[str, Any],
    market_scope: Mapping[str, Any],
) -> list[str]:
    violations = []
    violations.extend(f"invalid_boolean:{env_var}" for env_var in flags.get("invalid_env_vars", []))
    violations.extend(f"invalid_numeric:{env_var}" for env_var in risk_limits.get("invalid_env_vars", []))
    violations.extend(
        f"invalid_market_scope:{reason}" for reason in market_scope.get("invalid_reasons", [])
    )
    return _dedupe(violations)


def _status(*, missing_required: bool, invalid: bool, future_live_requested: bool) -> str:
    if invalid:
        return STATUS_CONFIG_INVALID_BLOCKED
    if missing_required:
        return STATUS_CONFIG_MISSING_BLOCKED
    if future_live_requested:
        return STATUS_LIVE_FLAGS_REQUESTED_BUT_BLOCKED
    return STATUS_REVIEW_ONLY_PREFLIGHT_READY


def _operator_required_actions(
    *,
    status: str,
    missing_required: Sequence[str],
    violations: Sequence[str],
    future_live_requested: bool,
) -> list[str]:
    actions = [
        "Review this preflight as a non-executable config contract artifact.",
        "Keep live connector, order submission, authenticated Polymarket access, and wallet signing disabled.",
        "Use a separate future operator-approved task before any live-enabling work.",
    ]
    if missing_required:
        actions.append("Provide every required non-secret PMBOT live enablement config key for review.")
    if violations:
        actions.append("Fix invalid boolean, numeric, or market-scope config values before review.")
    if future_live_requested or status == STATUS_LIVE_FLAGS_REQUESTED_BUT_BLOCKED:
        actions.append("Remove true live/execution/auth/signing flags; task 047 blocks live execution even when requested.")
    if status == STATUS_REVIEW_ONLY_PREFLIGHT_READY:
        actions.append("Treat REVIEW_ONLY_PREFLIGHT_READY as dry-run review readiness only, not live approval.")
    return _dedupe(actions)


def _parse_bool(value: Any) -> tuple[bool | None, str]:
    text = clean_text(value).lower()
    if text in TRUE_STRINGS:
        return True, ""
    if text in FALSE_STRINGS:
        return False, ""
    return None, "boolean value must be one of true/false/1/0/yes/no"


def _parse_positive_decimal(value: Any) -> tuple[Decimal, str]:
    text = clean_text(value)
    try:
        parsed = Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal("0"), "numeric value must be a finite positive decimal"
    if not parsed.is_finite() or parsed <= 0:
        return Decimal("0"), "numeric value must be greater than zero"
    return parsed, ""


def _parse_positive_int(value: Any) -> tuple[int, str]:
    text = clean_text(value)
    if not text or not text.isdigit():
        return 0, "integer value must be a positive whole number"
    parsed = int(text)
    if parsed <= 0:
        return 0, "integer value must be greater than zero"
    return parsed, ""


def _parse_csv_values(value: Any) -> list[str]:
    return [clean_text(item) for item in clean_text(value).split(",") if clean_text(item)]


def _is_btc_related_market_value(value: Any) -> bool:
    text = clean_text(value).lower()
    return "btc" in text or "bitcoin" in text


def _looks_sensitive_config_value(value: Any) -> bool:
    text = clean_text(value)
    lowered = text.lower()
    if not text:
        return False
    if lowered.startswith(("sk-", "sk_live_", "sk-proj-", "bearer ")):
        return True
    if any(
        marker in lowered
        for marker in (
            "private_key",
            "mnemonic",
            "seed_phrase",
            "secret",
            "access_token",
            "api_key",
            "signed_payload",
            "signed_order",
            "telegram_bot_token",
        )
    ):
        return True
    return False


def _preflight_safety_flags() -> dict[str, Any]:
    return {
        "local_artifact_only": True,
        "passive_artifact_only": True,
        "review_only": True,
        "dry_run_only": True,
        "paper_only": True,
        "execution_enabling": False,
        "execution_enabled": False,
        "live_approval": False,
        "live_execution_allowed": False,
        "live_execution_enabled": False,
        "live_execution_performed": False,
        "live_action_exposed": False,
        "allowed_for_live": False,
        "canary_executable_now": False,
        "live_execution_approved": False,
        "real_execution_available": False,
        "live_connector_enabled": False,
        "order_submission_enabled": False,
        "authenticated_polymarket_enabled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_endpoint_called": False,
        "authenticated_endpoint_call_performed": False,
        "signing_enabled": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "transaction_signing_enabled": False,
        "transaction_signing_performed": False,
        "signed_payload_generation_enabled": False,
        "signed_payload_created": False,
        "signed_order_generation_enabled": False,
        "signed_order_created": False,
        "signature_present": False,
        "wallet_enabled": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "wallet_used": False,
        "real_wallet_used": False,
        "private_key_used": False,
        "real_signature_created": False,
        "real_order_submitted": False,
        "would_submit_order": False,
        "order_submitted": False,
        "order_submission_claimed": False,
        "real_order_placement_performed": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "external_api_call_performed": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_secret_values_printed": False,
        "raw_secret_values_persisted": False,
        "browser_automation_used": False,
        "scheduler_created": False,
        "daemon_created": False,
        "autonomous_trading_enabled": False,
        "safety_summary": trading_core_safety_summary(),
    }


def _walk_flags(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            rows.append((path, key_text, nested))
            rows.extend(_walk_flags(nested, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_flags(nested, f"{path}[{index}]"))
    return rows


def _dedupe(values: Sequence[Any]) -> list[str]:
    rows: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in rows:
            rows.append(text)
    return rows


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"
