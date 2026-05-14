from __future__ import annotations

from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

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
PMBOT_POLYMARKET_PRODUCTION_CLOB_BASE_URL = "https://clob.polymarket.com"

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

DEFAULT_REDACTED_L2_MARKER_ENV_VARS = (
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
ALLOWED_L2_MARKER_VALUES = frozenset({"true", "present", "1"})

CLOB_BASE_URL_CONFIG_CONTRACT = "pmbot_clob_base_url_config_058.v1"
REDACTED_L2_MARKER_PRESENCE_CONTRACT = "pmbot_redacted_l2_marker_presence_058.v1"
UNSAFE_L2_MARKER_DETECTION_CONTRACT = "pmbot_unsafe_l2_marker_detection_058.v1"


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


def validate_safe_clob_base_url_config(
    value: Any = "",
    *,
    environ: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_environ = _active_environ(environ)
    text = clean_text(value) or clean_text(active_environ.get(PMBOT_POLYMARKET_CLOB_BASE_URL_ENV))
    base = {
        "contract_version": CLOB_BASE_URL_CONFIG_CONTRACT,
        "generated_at": generated_at,
        "env_var_name": PMBOT_POLYMARKET_CLOB_BASE_URL_ENV,
        "clob_base_url_configured": bool(text),
        "clob_base_url_missing": not bool(text),
        "clob_base_url_valid": False,
        "clob_base_url_invalid": False,
        "clob_base_url_status": STATUS_L2_MISSING,
        "status": STATUS_L2_MISSING,
        "public_clob_base_url": "",
        "public_clob_base_url_emitted": False,
        "clob_base_url_host": "",
        "clob_base_url_scheme": "",
        "is_production_clob_base_url": False,
        "unsafe_sensitive_value_detected": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "raw_credential_values_persisted": False,
        "private_key_envs_checked": False,
        "l1_private_key_material_requested": False,
        "operator_safe_summary": "PMBOT_POLYMARKET_CLOB_BASE_URL is missing.",
    }
    if not text:
        return base

    lowered = text.lower()
    if _looks_like_secret_marker_value(text) or any(
        marker in lowered for marker in ("private_key", "mnemonic", "seed_phrase", "secret", "token")
    ):
        base.update(
            {
                "status": "unsafe_sensitive_looking_value_redacted",
                "clob_base_url_status": "unsafe_sensitive_looking_value_redacted",
                "clob_base_url_invalid": True,
                "unsafe_sensitive_value_detected": True,
                "operator_safe_summary": "CLOB base URL input looked sensitive and was not emitted.",
            }
        )
        return base

    parsed = urlsplit(text)
    if parsed.scheme not in {"http", "https"}:
        base.update(
            {
                "status": "invalid_scheme",
                "clob_base_url_status": "invalid_scheme",
                "clob_base_url_invalid": True,
                "clob_base_url_scheme": clean_text(parsed.scheme),
                "operator_safe_summary": "CLOB base URL must use http or https.",
            }
        )
        return base
    if not parsed.netloc:
        base.update(
            {
                "status": "invalid_missing_host",
                "clob_base_url_status": "invalid_missing_host",
                "clob_base_url_invalid": True,
                "clob_base_url_scheme": parsed.scheme,
                "operator_safe_summary": "CLOB base URL is missing a host.",
            }
        )
        return base
    if parsed.username or parsed.password:
        base.update(
            {
                "status": "invalid_userinfo_blocked",
                "clob_base_url_status": "invalid_userinfo_blocked",
                "clob_base_url_invalid": True,
                "unsafe_sensitive_value_detected": True,
                "operator_safe_summary": "CLOB base URL must not contain userinfo.",
            }
        )
        return base
    if parsed.query or parsed.fragment:
        base.update(
            {
                "status": "invalid_query_or_fragment",
                "clob_base_url_status": "invalid_query_or_fragment",
                "clob_base_url_invalid": True,
                "operator_safe_summary": "CLOB base URL must not contain query parameters or fragments.",
            }
        )
        return base

    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    if normalized.endswith("://"):
        normalized = f"{parsed.scheme}://{parsed.netloc}"
    base.update(
        {
            "status": "valid_public_url_shape",
            "clob_base_url_status": "valid_public_url_shape",
            "clob_base_url_valid": True,
            "clob_base_url_invalid": False,
            "public_clob_base_url": normalized,
            "public_clob_base_url_emitted": True,
            "clob_base_url_host": parsed.netloc,
            "clob_base_url_scheme": parsed.scheme,
            "is_production_clob_base_url": normalized == PMBOT_POLYMARKET_PRODUCTION_CLOB_BASE_URL,
            "operator_safe_summary": "CLOB base URL shape is valid; public URL is safe to display.",
        }
    )
    return base


def build_redacted_l2_marker_presence_report(
    *,
    environ: Mapping[str, str] | None = None,
    expected_env_vars: Sequence[str] = DEFAULT_REDACTED_L2_MARKER_ENV_VARS,
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
        marker_status = "missing"
        if present:
            configured_count += 1
            if _is_allowed_l2_marker_value(active_environ.get(env_name)):
                marker_status = "present_redacted"
            else:
                marker_status = "unsafe_raw_value_detected"
                unsafe_env_vars.append(env_name)
        else:
            missing.append(env_name)
        items.append(
            {
                "env_var_name": env_name,
                "present": present,
                "marker_status": marker_status,
                "presence_status": "present_redacted" if present else "missing",
                "value_allowed_marker": marker_status == "present_redacted",
                "raw_value_emitted": False,
                "actual_secret_value_exposed": False,
                "value_hash_emitted": False,
                "value_prefix_emitted": False,
                "value_suffix_emitted": False,
                "safe_for_artifacts": True,
            }
        )

    missing_count = len(missing)
    unsafe_detected = bool(unsafe_env_vars)
    marker_set_complete = missing_count == 0 and not unsafe_detected
    if unsafe_detected:
        status = "unsafe_raw_value_detected"
        summary = "One or more L2 marker variables looked like raw credential material and were not emitted."
    elif marker_set_complete:
        status = STATUS_PRESENT_REDACTED
        summary = "All L2 marker variables are present as allowed redacted markers."
    elif configured_count == 0:
        status = STATUS_L2_MISSING
        summary = "L2 marker variables are missing."
    else:
        status = "incomplete"
        summary = "L2 marker variables are incomplete."

    return {
        "contract_version": REDACTED_L2_MARKER_PRESENCE_CONTRACT,
        "generated_at": generated_at,
        "status": status,
        "marker_presence_status": status,
        "auth_marker_presence_detected": marker_set_complete,
        "marker_set_complete": marker_set_complete,
        "expected_marker_count": len(tuple(expected_env_vars)),
        "configured_count": configured_count,
        "missing_count": missing_count,
        "missing_env_vars": missing,
        "unsafe_raw_value_detected": unsafe_detected,
        "unsafe_raw_value_env_vars": _dedupe(unsafe_env_vars),
        "env_presence_items": items,
        "supported_marker_env_vars": list(expected_env_vars),
        "allowed_marker_values": sorted(ALLOWED_L2_MARKER_VALUES),
        "redacted_presence_only": True,
        "environment_presence_checked": True,
        "environment_values_serialized": False,
        "credential_presence_check_scope": "l2_marker_env_var_presence_only",
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "raw_credential_values_persisted": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "value_hashes_emitted": False,
        "private_key_envs_checked": False,
        "l1_private_key_material_requested": False,
        "operator_safe_summary": summary,
    }


def build_unsafe_l2_marker_detection_report(
    marker_presence: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(marker_presence or {})
    unsafe_env_vars = [clean_text(item) for item in value.get("unsafe_raw_value_env_vars", []) if clean_text(item)]
    return {
        "contract_version": UNSAFE_L2_MARKER_DETECTION_CONTRACT,
        "generated_at": generated_at,
        "status": "unsafe_marker_detected" if unsafe_env_vars else "no_unsafe_marker_detected",
        "unsafe_raw_value_detected": bool(unsafe_env_vars),
        "unsafe_raw_value_env_vars": unsafe_env_vars,
        "unsafe_raw_value_count": len(unsafe_env_vars),
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "raw_credential_values_persisted": False,
        "value_hashes_emitted": False,
        "value_prefixes_emitted": False,
        "value_suffixes_emitted": False,
        "operator_safe_summary": (
            "Unsafe marker values were detected by env var name only; values were not emitted."
            if unsafe_env_vars
            else "No unsafe L2 marker values were detected."
        ),
    }


def l2_marker_presence_blockers(report: Mapping[str, Any]) -> list[str]:
    value = dict(report or {})
    missing_env_vars = [clean_text(item) for item in value.get("missing_env_vars", []) if clean_text(item)]
    unsafe_env_vars = [
        clean_text(item) for item in value.get("unsafe_raw_value_env_vars", []) if clean_text(item)
    ]
    blockers: list[str] = []
    expected_count = int(value.get("expected_marker_count", len(DEFAULT_REDACTED_L2_MARKER_ENV_VARS)) or 0)
    if len(missing_env_vars) >= expected_count:
        blockers.append("l2_markers_missing")
    elif missing_env_vars:
        blockers.append("l2_markers_incomplete")
    blockers.extend(f"missing_l2_marker:{env_name}" for env_name in missing_env_vars)
    blockers.extend(f"unsafe_raw_l2_marker_value:{env_name}" for env_name in unsafe_env_vars)
    return _dedupe(blockers)


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


def _is_allowed_l2_marker_value(value: Any) -> bool:
    return clean_text(value).lower() in ALLOWED_L2_MARKER_VALUES


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
