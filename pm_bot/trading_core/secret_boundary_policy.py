from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, clean_text

SECRET_BOUNDARY_POLICY_CONTRACT = "pmbot_secret_boundary_policy_static.v1"
STATIC_SECRET_VALIDATION_CONTRACT = "pmbot_static_secret_boundary_validation.v1"

FORBIDDEN_SECRET_FIELD_NAMES = frozenset(
    {
        "private_key",
        "privkey",
        "mnemonic",
        "seed_phrase",
        "seed",
        "secret",
        "api_key",
        "access_token",
        "bearer_token",
        "signature",
        "signed_payload",
        "raw_transaction",
        "wallet_password",
        "recovery_phrase",
        "client_secret",
        "auth_header",
    }
)

FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        *FORBIDDEN_SECRET_FIELD_NAMES,
        "signed_order",
        "submit_order",
        "place_order",
        "send_transaction",
    }
)

FORBIDDEN_ENV_VAR_NAME_PATTERNS = (
    "PRIVATE_KEY",
    "PRIVKEY",
    "MNEMONIC",
    "SEED_PHRASE",
    "RECOVERY_PHRASE",
    "WALLET_PASSWORD",
    "API_KEY",
    "ACCESS_TOKEN",
    "BEARER_TOKEN",
    "CLIENT_SECRET",
    "AUTH_HEADER",
    "SIGNATURE",
    "RAW_TRANSACTION",
)

SAFE_PLACEHOLDER_MARKERS = frozenset(
    {
        "<not_configured>",
        "<disabled>",
        "<redacted>",
        "not_applicable",
        "dry_run_only",
    }
)

SAFE_SECRET_METADATA_FIELD_NAMES = frozenset(
    {
        "secret_boundary_status",
        "secret_boundary_policy_contract",
        "secret_boundary_validation",
        "secret_boundary_policy",
        "secret_boundary_static_validation",
        "secret_boundary_not_configured",
        "secret_policy_status",
        "secret_policy_validation",
        "secret_policy_ready",
        "secrets_present",
        "secrets_not_configured",
        "secrets_read",
        "environment_secrets_read",
        "secret_like_field_rejected",
        "secret_like_field_paths",
        "forbidden_secret_field_names",
        "forbidden_secret_field_patterns",
        "forbidden_secret_field_paths",
        "forbidden_secret_field_count",
        "forbidden_env_var_names",
        "forbidden_env_var_patterns",
        "forbidden_env_var_reference_paths",
        "forbidden_payload_keys",
        "safe_secret_metadata_field_names",
        "safe_placeholder_markers",
        "static_secret_validation_ready",
        "private_key_or_mnemonic_handling_added",
    }
)

SAFE_NEGATIVE_SECRET_FIELD_NAMES = frozenset(
    {
        "no_private_key",
        "no_real_private_key_used",
        "private_key_used",
        "private_key_access_approved",
        "private_key_accessed",
        "private_key_material_accessed",
        "real_signature_created",
        "cryptographic_signing_performed",
        "real_order_submitted",
        "real_order_placement_added",
        "signed_payload_created",
        "raw_transaction_created",
        "auth_header_created",
        "bearer_token_used",
        "api_key_used",
        "access_token_used",
        "client_secret_used",
        "wallet_password_used",
        "mnemonic_used",
        "seed_phrase_used",
        "recovery_phrase_used",
    }
)

SAFE_NEGATIVE_SECRET_PREFIXES = ("no_", "not_", "without_", "disabled_")
SAFE_NEGATIVE_SECRET_SUFFIXES = (
    "_used",
    "_accessed",
    "_created",
    "_performed",
    "_submitted",
    "_approved",
    "_enabled",
    "_available",
    "_supported",
    "_configured",
    "_present",
    "_persisted",
    "_printed",
    "_added",
)


def build_secret_boundary_policy(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": SECRET_BOUNDARY_POLICY_CONTRACT,
        "generated_at": generated_at,
        "policy_id": "secret-boundary-policy-031-static",
        "policy_scope": "static_packet_config_receipt_audit_and_doc_examples_only",
        "forbidden_secret_field_names": sorted(FORBIDDEN_SECRET_FIELD_NAMES),
        "forbidden_env_var_name_patterns": list(FORBIDDEN_ENV_VAR_NAME_PATTERNS),
        "forbidden_payload_keys": sorted(FORBIDDEN_PAYLOAD_KEYS),
        "safe_placeholder_markers": sorted(SAFE_PLACEHOLDER_MARKERS),
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "static_validation_only": True,
    }


def validate_static_secret_boundary(
    value: Mapping[str, Any],
    *,
    artifact_type: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    forbidden_field_paths = find_forbidden_secret_field_paths(value)
    unsafe_flag_paths = find_unsafe_secret_flag_paths(value)
    validation_id = _stable_id(
        "static-secret-boundary-validation-031",
        {
            "artifact_type": artifact_type,
            "forbidden_field_paths": forbidden_field_paths,
            "unsafe_flag_paths": unsafe_flag_paths,
        },
    )
    valid = not forbidden_field_paths and not unsafe_flag_paths
    return {
        "contract_version": STATIC_SECRET_VALIDATION_CONTRACT,
        "validation_id": validation_id,
        "artifact_type": clean_text(artifact_type),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "forbidden_secret_field_paths": forbidden_field_paths,
        "forbidden_secret_field_count": len(forbidden_field_paths),
        "unsafe_active_secret_flag_paths": unsafe_flag_paths,
        "safe_placeholder_markers": sorted(SAFE_PLACEHOLDER_MARKERS),
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "static_validation_only": True,
    }


def validate_secret_boundary_config(value: Mapping[str, Any], *, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return validate_static_secret_boundary(value, artifact_type="config", generated_at=generated_at)


def validate_secret_boundary_request(value: Mapping[str, Any], *, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return validate_static_secret_boundary(value, artifact_type="request", generated_at=generated_at)


def validate_secret_boundary_receipt(value: Mapping[str, Any], *, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return validate_static_secret_boundary(value, artifact_type="receipt", generated_at=generated_at)


def validate_secret_boundary_audit_record(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(value, artifact_type="audit_record", generated_at=generated_at)


def validate_secret_boundary_doc_example(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(value, artifact_type="doc_example", generated_at=generated_at)


def validate_static_env_var_names(
    env_var_names: Sequence[str],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    forbidden_names = [
        clean_text(name)
        for name in env_var_names
        if clean_text(name) and is_forbidden_env_var_name(clean_text(name))
    ]
    validation_id = _stable_id(
        "static-env-var-name-validation-031",
        {"forbidden_env_var_names": sorted(forbidden_names)},
    )
    return {
        "contract_version": STATIC_SECRET_VALIDATION_CONTRACT,
        "validation_id": validation_id,
        "artifact_type": "env_var_name_list",
        "generated_at": generated_at,
        "valid": not forbidden_names,
        "status": "passed" if not forbidden_names else "blocked",
        "forbidden_env_var_names": sorted(forbidden_names),
        "forbidden_env_var_name_count": len(forbidden_names),
        "environment_inspected": False,
        "environment_secrets_read": False,
        "static_validation_only": True,
    }


def find_forbidden_secret_field_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            nested_path = f"{path}.{key_text}"
            if is_forbidden_secret_field_name(key_text):
                paths.append(nested_path)
            paths.extend(find_forbidden_secret_field_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(find_forbidden_secret_field_paths(nested, f"{path}[{index}]"))
    return paths


def find_unsafe_secret_flag_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            nested_path = f"{path}.{key_text}"
            if is_safe_negative_secret_metadata_field(key_text) and nested is True:
                paths.append(nested_path)
            paths.extend(find_unsafe_secret_flag_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(find_unsafe_secret_flag_paths(nested, f"{path}[{index}]"))
    return paths


def is_forbidden_secret_field_name(name: str) -> bool:
    normalized = _normalize_key(name)
    if not normalized:
        return False
    if normalized in SAFE_SECRET_METADATA_FIELD_NAMES:
        return False
    if is_safe_negative_secret_metadata_field(normalized):
        return False
    if normalized in FORBIDDEN_PAYLOAD_KEYS:
        return True
    for suffix in FORBIDDEN_PAYLOAD_KEYS:
        if normalized.endswith(f"_{suffix}"):
            return True
    return False


def is_forbidden_env_var_name(name: str) -> bool:
    normalized = _normalize_env_name(name)
    if not normalized:
        return False
    return any(pattern in normalized for pattern in FORBIDDEN_ENV_VAR_NAME_PATTERNS)


def is_safe_placeholder(value: Any) -> bool:
    return clean_text(value) in SAFE_PLACEHOLDER_MARKERS


def is_safe_negative_secret_metadata_field(name: str) -> bool:
    normalized = _normalize_key(name)
    if normalized in SAFE_NEGATIVE_SECRET_FIELD_NAMES:
        return True
    if normalized.startswith(SAFE_NEGATIVE_SECRET_PREFIXES):
        return True
    if any(normalized.endswith(suffix) for suffix in SAFE_NEGATIVE_SECRET_SUFFIXES):
        return any(secret_name in normalized for secret_name in FORBIDDEN_SECRET_FIELD_NAMES)
    return False


def _normalize_key(value: str) -> str:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _normalize_env_name(value: str) -> str:
    normalized = "".join(character if character.isalnum() else "_" for character in value.upper())
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
