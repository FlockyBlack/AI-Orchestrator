from __future__ import annotations

from typing import Any, Mapping, Sequence

from pm_bot.trading_core.live_connector_preflight_models import (
    STATUS_AUTH_CHECKED,
    STATUS_AUTH_MISSING,
    STATUS_AUTH_SKIPPED,
    CredentialPresenceReport,
    live_connector_preflight_safety_flags,
)
from pm_bot.trading_core.authenticated_clob_preflight_models import (
    STATUS_MISSING as STATUS_L2_MISSING,
    STATUS_PRESENT_REDACTED,
    RedactedL2CredentialPresence,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

PMBOT_POLYMARKET_LIVE_PREFLIGHT_ENABLED_ENV = "PMBOT_POLYMARKET_LIVE_PREFLIGHT_ENABLED"
PMBOT_POLYMARKET_CLOB_BASE_URL_ENV = "PMBOT_POLYMARKET_CLOB_BASE_URL"
PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT_ENV = "PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT"
PMBOT_POLYMARKET_L2_API_KEY_PRESENT_ENV = "PMBOT_POLYMARKET_L2_API_KEY_PRESENT"
PMBOT_POLYMARKET_L2_API_SECRET_PRESENT_ENV = "PMBOT_POLYMARKET_L2_API_SECRET_PRESENT"
PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT_ENV = "PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT"

EXISTING_REDACTED_AUTH_MARKER_ENV_VARS = (
    "PMBOT_POLYMARKET_API_KEY_CONFIGURED",
    "PMBOT_POLYMARKET_API_SECRET_CONFIGURED",
    "PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED",
)

DEFAULT_LIVE_PREFLIGHT_ENV_VARS = (
    PMBOT_POLYMARKET_LIVE_PREFLIGHT_ENABLED_ENV,
    PMBOT_POLYMARKET_CLOB_BASE_URL_ENV,
    PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT_ENV,
    *EXISTING_REDACTED_AUTH_MARKER_ENV_VARS,
)

DEFAULT_L2_CREDENTIAL_PRESENCE_ENV_VARS = (
    PMBOT_POLYMARKET_CLOB_BASE_URL_ENV,
    PMBOT_POLYMARKET_L2_API_KEY_PRESENT_ENV,
    PMBOT_POLYMARKET_L2_API_SECRET_PRESENT_ENV,
    PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT_ENV,
)

LIVE_ENABLEMENT_FLAG_ENV_VARS = (
    "PMBOT_LIVE_MODE",
    "PMBOT_LIVE_CANARY_ENABLED",
    "PMBOT_ORDER_SUBMISSION_ENABLED",
    "PMBOT_AUTHENTICATED_POLYMARKET_ENABLED",
    "PMBOT_WALLET_SIGNING_ENABLED",
)

TRUE_STRINGS = frozenset({"true", "1", "yes", "y", "on"})


def build_live_credentials_presence_report(
    *,
    environ: Mapping[str, str] | None = None,
    auth_check: bool = False,
    expected_env_vars: Sequence[str] = DEFAULT_LIVE_PREFLIGHT_ENV_VARS,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if auth_check is not True:
        return build_skipped_live_credentials_presence_report(generated_at=generated_at)

    active_environ = _active_environ(environ)
    items: list[dict[str, Any]] = []
    missing: list[str] = []
    configured_count = 0
    unsafe_config_combinations: list[str] = []
    for env_var_name in expected_env_vars:
        env_name = clean_text(env_var_name)
        present = _env_present(active_environ, env_name)
        if present:
            configured_count += 1
            if _looks_like_secret_marker_value(active_environ.get(env_name)):
                unsafe_config_combinations.append(
                    f"{env_name}_value_looked_sensitive_and_was_not_serialized"
                )
        else:
            missing.append(env_name)
        items.append(_presence_item(env_name, present=present, source="environment_presence_redacted"))

    for flag_env_name in LIVE_ENABLEMENT_FLAG_ENV_VARS:
        if _parse_bool(active_environ.get(flag_env_name)) is True:
            unsafe_config_combinations.append(f"{flag_env_name}_requested_true_but_preflight_blocks_live")

    missing_count = len(missing)
    status = STATUS_AUTH_CHECKED if missing_count == 0 and not unsafe_config_combinations else STATUS_AUTH_MISSING
    summary = (
        "Auth presence markers are configured, but authenticated requests, signing, wallet use, and order "
        "submission remain blocked."
        if status == STATUS_AUTH_CHECKED
        else "Auth presence check is blocked or incomplete; only redacted presence metadata was produced."
    )
    report = CredentialPresenceReport(
        status=status,
        auth_presence_check_performed=True,
        env_presence_items=tuple(items),
        configured_count=configured_count,
        missing_count=missing_count,
        missing_env_vars=tuple(missing),
        unsafe_config_combinations=tuple(_dedupe(unsafe_config_combinations)),
        operator_safe_summary=summary,
        generated_at=generated_at,
    ).to_dict()
    report["environment_presence_checked"] = True
    report["environment_values_serialized"] = False
    report["credential_presence_check_scope"] = "explicit_env_var_presence_only"
    report["auth_boundary_status"] = status
    return report


def build_skipped_live_credentials_presence_report(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    report = CredentialPresenceReport(
        status=STATUS_AUTH_SKIPPED,
        auth_presence_check_performed=False,
        env_presence_items=(),
        configured_count=0,
        missing_count=0,
        missing_env_vars=(),
        unsafe_config_combinations=(),
        operator_safe_summary="Auth presence check skipped; public-only preflight remains non-executable.",
        generated_at=generated_at,
    ).to_dict()
    report["environment_presence_checked"] = False
    report["environment_values_serialized"] = False
    report["credential_presence_check_scope"] = "skipped_public_only"
    report["auth_boundary_status"] = STATUS_AUTH_SKIPPED
    return report


def credential_presence_blockers(report: Mapping[str, Any]) -> list[str]:
    value = dict(report or {})
    if value.get("auth_presence_check_performed") is not True:
        return ["auth_presence_check_not_requested_public_only"]
    blockers: list[str] = []
    for env_name in value.get("missing_env_vars", []):
        blockers.append(f"missing_required_env_presence_marker:{clean_text(env_name)}")
    blockers.extend(clean_text(item) for item in value.get("unsafe_config_combinations", []) if clean_text(item))
    return _dedupe(blockers)


def summarize_live_credentials_presence_report(report: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(report or {})
    return {
        "status": clean_text(value.get("status") or STATUS_AUTH_SKIPPED),
        "auth_boundary_status": clean_text(value.get("auth_boundary_status") or value.get("status") or STATUS_AUTH_SKIPPED),
        "auth_presence_check_performed": value.get("auth_presence_check_performed") is True,
        "configured_count": int(value.get("configured_count", 0) or 0),
        "missing_count": int(value.get("missing_count", 0) or 0),
        "missing_env_vars": [clean_text(item) for item in value.get("missing_env_vars", [])],
        "unsafe_config_combinations": [
            clean_text(item) for item in value.get("unsafe_config_combinations", [])
        ],
        "redacted_presence_only": True,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        **live_connector_preflight_safety_flags(
            public_network_check_performed=False,
            auth_presence_check_performed=value.get("auth_presence_check_performed") is True,
        ),
    }


def build_redacted_l2_credential_presence_report(
    *,
    environ: Mapping[str, str] | None = None,
    expected_env_vars: Sequence[str] = DEFAULT_L2_CREDENTIAL_PRESENCE_ENV_VARS,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_environ = _active_environ(environ)
    items: list[dict[str, Any]] = []
    missing: list[str] = []
    unsafe_env_vars: list[str] = []
    configured_count = 0
    for env_var_name in expected_env_vars:
        env_name = clean_text(env_var_name)
        present = _env_present(active_environ, env_name)
        if present:
            configured_count += 1
            if _looks_like_unsafe_l2_marker_value(env_name, active_environ.get(env_name)):
                unsafe_env_vars.append(env_name)
        else:
            missing.append(env_name)
        items.append(
            _presence_item(
                env_name,
                present=present,
                source="l2_environment_presence_redacted",
            )
        )

    missing_count = len(missing)
    unsafe_detected = bool(unsafe_env_vars)
    status = STATUS_PRESENT_REDACTED if missing_count == 0 else STATUS_L2_MISSING
    if missing_count == 0 and unsafe_detected:
        summary = (
            "All L2 presence markers exist, but one or more marker values looked like raw material and were "
            "not serialized; live auth remains blocked."
        )
    elif missing_count == 0:
        summary = "All L2 presence markers exist as redacted markers; no authenticated request is performed."
    else:
        summary = "L2 credential presence is incomplete; only missing/present_redacted metadata was produced."
    report = RedactedL2CredentialPresence(
        status=status,
        auth_presence_check_performed=True,
        env_presence_items=tuple(items),
        configured_count=configured_count,
        missing_count=missing_count,
        missing_env_vars=tuple(missing),
        unsafe_raw_value_detected=unsafe_detected,
        unsafe_raw_value_env_vars=tuple(_dedupe(unsafe_env_vars)),
        operator_safe_summary=summary,
        generated_at=generated_at,
    ).to_dict()
    report["environment_presence_checked"] = True
    report["environment_values_serialized"] = False
    report["credential_presence_check_scope"] = "l2_marker_env_var_presence_only"
    report["supported_marker_env_vars"] = list(expected_env_vars)
    return report


def l2_credential_presence_blockers(report: Mapping[str, Any]) -> list[str]:
    value = dict(report or {})
    blockers: list[str] = []
    for env_name in value.get("missing_env_vars", []):
        blockers.append(f"missing_required_l2_presence_marker:{clean_text(env_name)}")
    for env_name in value.get("unsafe_raw_value_env_vars", []):
        blockers.append(f"unsafe_raw_l2_marker_value_detected:{clean_text(env_name)}")
    return _dedupe(blockers)


def summarize_redacted_l2_credential_presence_report(report: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(report or {})
    return {
        "status": clean_text(value.get("status") or STATUS_L2_MISSING),
        "auth_presence_check_performed": value.get("auth_presence_check_performed") is True,
        "configured_count": int(value.get("configured_count", 0) or 0),
        "missing_count": int(value.get("missing_count", 0) or 0),
        "missing_env_vars": [clean_text(item) for item in value.get("missing_env_vars", [])],
        "unsafe_raw_value_detected": value.get("unsafe_raw_value_detected") is True,
        "unsafe_raw_value_env_vars": [
            clean_text(item) for item in value.get("unsafe_raw_value_env_vars", [])
        ],
        "redacted_presence_only": True,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "raw_credential_values_persisted": False,
    }


def _presence_item(env_var_name: str, *, present: bool, source: str) -> dict[str, Any]:
    return {
        "env_var_name": clean_text(env_var_name),
        "present": present is True,
        "value_length_category": "present_redacted" if present else "missing",
        "presence_status": "present_redacted" if present else "missing",
        "source": clean_text(source),
        "raw_value_emitted": False,
        "actual_secret_value_exposed": False,
        "safe_for_artifacts": True,
    }


def _active_environ(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    if environ is not None:
        return environ
    import os

    return os.environ


def _env_present(environ: Mapping[str, str], env_name: str) -> bool:
    return env_name in environ and clean_text(environ.get(env_name)) != ""


def _parse_bool(value: Any) -> bool:
    return clean_text(value).lower() in TRUE_STRINGS


def _looks_like_secret_marker_value(value: Any) -> bool:
    text = clean_text(value)
    lowered = text.lower()
    if not text:
        return False
    if lowered.startswith(("sk-", "sk_live_", "sk-proj-", "bearer ")):
        return True
    if "-----begin" in lowered and "private key" in lowered:
        return True
    if any(
        marker in lowered
        for marker in (
            "mnemonic:",
            "seed phrase:",
            "seed_phrase=",
            "raw_secret=",
            "secret_value=",
            "signed_payload=",
            "signed_order=",
            "auth_header=",
        )
    ):
        return True
    return False


def _looks_like_unsafe_l2_marker_value(env_name: str, value: Any) -> bool:
    text = clean_text(value)
    lowered = text.lower()
    if not text:
        return False
    if env_name == PMBOT_POLYMARKET_CLOB_BASE_URL_ENV:
        return _looks_like_secret_marker_value(text)
    safe_marker_values = {
        "true",
        "1",
        "yes",
        "y",
        "on",
        "present",
        "configured",
        "redacted",
        "present_redacted",
    }
    if lowered in safe_marker_values:
        return False
    return True


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
