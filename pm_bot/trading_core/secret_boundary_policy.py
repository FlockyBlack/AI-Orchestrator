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
        "signed_order",
        "raw_secret",
        "raw_private_key",
        "secret_value",
        "raw_transaction",
        "wallet_password",
        "recovery_phrase",
        "client_secret",
        "auth_header",
        "order_submission_payload",
        "transaction_payload",
        "authorization",
        "cookie",
        "set_cookie",
        "x_api_key",
        "clob_api_key",
        "clob_secret",
        "clob_passphrase",
        "api_key_value",
        "access_token_value",
        "telegram_bot_token",
        "raw_telegram_bot_token",
        "telegram_init_data",
        "raw_telegram_init_data",
        "telegram_web_app_init_data",
        "operator_user_id",
        "operator_user_ids",
        "raw_operator_user_id",
        "raw_operator_user_ids",
    }
)

FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        *FORBIDDEN_SECRET_FIELD_NAMES,
        "order_payload",
        "order_submission_payload",
        "signed_order",
        "transaction_payload",
        "raw_secret",
        "raw_private_key",
        "secret_value",
        "authorization",
        "cookie",
        "set_cookie",
        "x_api_key",
        "clob_api_key",
        "clob_secret",
        "clob_passphrase",
        "api_key_value",
        "access_token_value",
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
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_INIT_DATA",
    "TELEGRAM_WEB_APP_INIT_DATA",
)

SAFE_PLACEHOLDER_MARKERS = frozenset(
    {
        "<not_configured>",
        "<disabled>",
        "<redacted>",
        "<configured:redacted>",
        "<missing>",
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
        "forbidden_secret_or_signing_field_detected",
        "forbidden_secret_or_signing_field_paths",
        "safe_secret_metadata_field_names",
        "safe_placeholder_markers",
        "static_secret_validation_ready",
        "private_key_or_mnemonic_handling_added",
        "readiness_evidence_bundle_secret_boundary_validation",
        "readiness_evidence_bundle_static_validation",
        "readiness_evidence_bundle_is_not_live_approval",
        "risk_limit_control_plane_secret_boundary_validation",
        "risk_limit_policy_secret_boundary_validation",
        "risk_limit_order_intent_secret_boundary_validation",
        "risk_limit_decision_secret_boundary_validation",
        "risk_control_ui_summary_secret_boundary_validation",
        "risk_control_plane_does_not_submit_orders",
        "btc_connector_config_secret_boundary_validation",
        "btc_market_snapshot_secret_boundary_validation",
        "btc_connector_result_secret_boundary_validation",
        "btc_ui_summary_secret_boundary_validation",
        "btc_evidence_item_secret_boundary_validation",
        "btc_market_analysis_config_secret_boundary_validation",
        "btc_market_analysis_result_secret_boundary_validation",
        "btc_dry_run_order_intent_plan_secret_boundary_validation",
        "btc_dry_run_order_intent_result_secret_boundary_validation",
        "btc_risk_decision_summary_secret_boundary_validation",
        "btc_analysis_ui_summary_secret_boundary_validation",
        "live_credentials_config_secret_boundary_validation",
        "live_credentials_status_report_secret_boundary_validation",
        "live_auth_boundary_decision_secret_boundary_validation",
        "live_credentials_auth_summary_secret_boundary_validation",
        "live_credentials_auth_artifact_secret_boundary_validation",
        "auth_boundary_decision_secret_boundary_validation",
        "status_report_secret_boundary_validation",
        "redacted_preview",
        "credential_statuses_redacted",
        "redacted_credential_status_ready",
        "safe_for_artifacts",
        "secrets_redacted",
        "actual_secret_values_exposed",
        "raw_secret_values_read_by_tests",
        "raw_secret_values_printed",
        "raw_secret_values_persisted",
        "live_order_submission_boundary_receipt_secret_boundary_validation",
        "live_order_submission_boundary_summary_secret_boundary_validation",
        "live_enablement_config_preflight_secret_boundary_validation",
        "live_enablement_config_preflight_summary_secret_boundary_validation",
        "operator_ui_panel_live_enablement_config_preflight_summary_secret_boundary_validation",
        "wallet_signing_boundary_secret_boundary_validation",
        "wallet_signing_boundary_summary_secret_boundary_validation",
        "operator_ui_panel_wallet_signing_boundary_summary_secret_boundary_validation",
        "wallet_signing_boundary_section_ready",
        "wallet_readiness_status",
        "wallet_address_status",
        "signing_provider_status",
        "signing_dry_run_only_marker_status",
        "live_enablement_config_preflight_section_ready",
        "no_raw_secrets_parsed_or_emitted",
        "config_values_redacted_where_sensitive",
        "tiny_live_canary_gonogo_gate_secret_boundary_validation",
        "tiny_live_canary_gonogo_gate_summary_secret_boundary_validation",
        "telegram_operator_control_config_secret_boundary_validation",
        "telegram_operator_control_state_secret_boundary_validation",
        "telegram_operator_control_summary_secret_boundary_validation",
        "telegram_mini_app_operator_panel_payload_secret_boundary_validation",
        "telegram_mini_app_operator_panel_rendered_html_secret_boundary_validation",
        "telegram_mini_app_operator_panel_rendered_json_secret_boundary_validation",
        "telegram_mini_app_operator_panel_section_ready",
        "telegram_mini_app_operator_panel_ready",
        "telegram_mini_app_url_status",
        "telegram_init_data_status",
        "telegram_bot_token_status",
        "telegram_bot_configured",
        "raw_telegram_bot_token_exposed",
        "raw_telegram_init_data_exposed",
        "raw_telegram_data_persisted",
        "raw_operator_user_ids_exposed",
        "raw_operator_user_id_persisted",
        "operator_user_hash_only",
        "allowed_operator_ids_redacted",
        "allowed_operator_ids_configured",
        "allowed_operator_id_count",
        "telegram_operator_control_bot_section_ready",
        "no_executable_action",
        "would_submit_order",
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

SAFE_TRUE_SECRET_METADATA_FIELD_NAMES = frozenset(
    {
        "no_executable_action",
        "no_executable_live_action",
        "no_raw_secrets_parsed_or_emitted",
        "no_signature_returned",
        "no_signed_payload_returned",
        "no_signed_order_returned",
        "no_transaction_hash_returned",
        "no_order_id_returned",
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

ALLOWED_HUMAN_OPERATOR_SIGNED_INTENT_FIELD_NAMES = frozenset(
    {
        "operator_signed_intent_acknowledgement",
        "operator_signed_intent_is_human_acknowledgement_only",
        "human_signed_acknowledgement_text",
    }
)

FORBIDDEN_OPERATOR_INTENT_FIELD_NAMES = frozenset(
    {
        "private_key",
        "mnemonic",
        "seed_phrase",
        "signature",
        "signed_order",
        "signed_payload",
        "raw_transaction",
        "auth_header",
        "bearer_token",
        "api_key",
        "order_submission_payload",
        "transaction_payload",
    }
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
        "sensitive_redacted_config_keys": [
            "PMBOT_TELEGRAM_BOT_TOKEN",
            "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS",
            "PMBOT_TELEGRAM_MINI_APP_URL",
            "PMBOT_TELEGRAM_INIT_DATA",
        ],
        "non_secret_live_enablement_config_keys": [
            "PMBOT_LIVE_MODE",
            "PMBOT_LIVE_CANARY_ENABLED",
            "PMBOT_ORDER_SUBMISSION_ENABLED",
            "PMBOT_AUTHENTICATED_POLYMARKET_ENABLED",
            "PMBOT_WALLET_SIGNING_ENABLED",
            "PMBOT_MAX_ORDER_NOTIONAL_USD",
            "PMBOT_DAILY_LOSS_CAP_USD",
            "PMBOT_TOTAL_EXPOSURE_CAP_USD",
            "PMBOT_MAX_LIVE_TRADES_PER_DAY",
            "PMBOT_ALLOWED_MARKET_SLUGS",
            "PMBOT_ALLOWED_MARKET_IDS",
            "PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL",
            "PMBOT_REQUIRE_KILL_SWITCH_READY",
        ],
        "sensitive_redacted_config_notes": [
            "Telegram bot tokens are sensitive and may only be surfaced as missing or configured_redacted.",
            "Telegram allowed operator user IDs are sensitive configuration and should be summarized by presence/count or hashed identifiers only.",
            "Telegram operator control bot v1 is non-execution: it does not submit orders, sign payloads, connect wallets, or call authenticated endpoints.",
            "Telegram Mini App URLs and init data are sensitive configuration and may only be surfaced as missing or configured_redacted status.",
            "Telegram Mini App operator panel v1 is non-execution: it is a static review surface and does not submit orders, sign payloads, connect wallets, or call authenticated endpoints.",
            "PMBOT live enablement config keys are non-secret review configuration only; they must not include private keys, tokens, seed phrases, raw credentials, signed payloads, or authorization material.",
            "If future live enablement config adds sensitive categories, artifacts must redact values and expose only missing/configured status.",
        ],
    }


def validate_static_secret_boundary(
    value: Mapping[str, Any],
    *,
    artifact_type: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    forbidden_field_paths = find_forbidden_secret_field_paths(value)
    forbidden_value_paths = find_actual_secret_value_paths(value)
    unsafe_flag_paths = find_unsafe_secret_flag_paths(value)
    validation_id = _stable_id(
        "static-secret-boundary-validation-031",
        {
            "artifact_type": artifact_type,
            "forbidden_field_paths": forbidden_field_paths,
            "forbidden_value_paths": forbidden_value_paths,
            "unsafe_flag_paths": unsafe_flag_paths,
        },
    )
    valid = not forbidden_field_paths and not forbidden_value_paths and not unsafe_flag_paths
    return {
        "contract_version": STATIC_SECRET_VALIDATION_CONTRACT,
        "validation_id": validation_id,
        "artifact_type": clean_text(artifact_type),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "forbidden_secret_field_paths": forbidden_field_paths,
        "forbidden_secret_field_count": len(forbidden_field_paths),
        "forbidden_secret_value_paths": forbidden_value_paths,
        "forbidden_secret_value_count": len(forbidden_value_paths),
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


def validate_secret_boundary_audit_replay_record(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(value, artifact_type="audit_replay_record", generated_at=generated_at)


def validate_secret_boundary_operator_approval_packet(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(value, artifact_type="operator_approval_packet", generated_at=generated_at)


def validate_secret_boundary_operator_checklist_item(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="operator_approval_checklist_item",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_intent_packet(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_operator_intent_boundary(
        value,
        artifact_type="operator_intent_packet",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_intent_acknowledgement(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_operator_intent_boundary(
        value,
        artifact_type="operator_intent_acknowledgement",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_intent_evidence_reference(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_operator_intent_boundary(
        value,
        artifact_type="operator_intent_evidence_reference",
        generated_at=generated_at,
    )


def validate_static_operator_intent_boundary(
    value: Mapping[str, Any],
    *,
    artifact_type: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    base_validation = validate_static_secret_boundary(value, artifact_type=artifact_type, generated_at=generated_at)
    forbidden_operator_paths = find_forbidden_operator_intent_field_paths(value)
    human_signed_paths = find_human_operator_signed_intent_field_paths(value)
    if human_signed_paths and not _human_operator_signed_context_declared(value):
        forbidden_operator_paths.extend(human_signed_paths)
    forbidden_operator_paths = _dedupe_paths(forbidden_operator_paths)
    validation_id = _stable_id(
        "static-operator-intent-boundary-validation-034",
        {
            "artifact_type": artifact_type,
            "base_validation_id": base_validation.get("validation_id"),
            "forbidden_operator_intent_field_paths": forbidden_operator_paths,
        },
    )
    valid = base_validation.get("valid") is True and not forbidden_operator_paths
    result = dict(base_validation)
    result.update(
        {
            "validation_id": validation_id,
            "artifact_type": clean_text(artifact_type),
            "valid": valid,
            "status": "passed" if valid else "blocked",
            "forbidden_operator_intent_field_paths": forbidden_operator_paths,
            "forbidden_operator_intent_field_count": len(forbidden_operator_paths),
            "human_operator_signed_intent_field_paths": human_signed_paths,
            "operator_signed_intent_human_context_required": bool(human_signed_paths),
            "operator_signed_intent_human_context_present": (
                _human_operator_signed_context_declared(value) if human_signed_paths else True
            ),
            "operator_signed_intent_is_not_cryptographic": True,
        }
    )
    return result


def validate_secret_boundary_tiny_canary_preflight_contract(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="tiny_canary_preflight_contract",
        generated_at=generated_at,
    )


def validate_secret_boundary_tiny_canary_manual_runbook(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="tiny_canary_manual_runbook",
        generated_at=generated_at,
    )


def validate_secret_boundary_tiny_canary_kill_switch_requirement_packet(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="tiny_canary_kill_switch_requirement_packet",
        generated_at=generated_at,
    )


def validate_secret_boundary_tiny_canary_evidence_requirement_packet(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="tiny_canary_evidence_requirement_packet",
        generated_at=generated_at,
    )


def validate_secret_boundary_readiness_evidence_bundle(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="readiness_evidence_bundle",
        generated_at=generated_at,
    )


def validate_secret_boundary_readiness_evidence_item(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="readiness_evidence_item",
        generated_at=generated_at,
    )


def validate_secret_boundary_readiness_evidence_manifest(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="readiness_evidence_manifest",
        generated_at=generated_at,
    )


def validate_secret_boundary_readiness_evidence_reference(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="readiness_evidence_reference",
        generated_at=generated_at,
    )


def validate_secret_boundary_readiness_evidence_blocker_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="readiness_evidence_blocker_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_ui_panel_payload(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="operator_ui_panel_payload",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_ui_panel_action_state(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="operator_ui_panel_action_state",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_ui_panel_risk_limit_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="operator_ui_panel_risk_limit_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_risk_limit_policy(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="risk_limit_policy",
        generated_at=generated_at,
    )


def validate_secret_boundary_risk_limit_order_intent(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="risk_limit_order_intent",
        generated_at=generated_at,
    )


def validate_secret_boundary_risk_limit_decision(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="risk_limit_decision",
        generated_at=generated_at,
    )


def validate_secret_boundary_risk_control_ui_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="risk_control_ui_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_connector_config(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_read_only_connector_config",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_market_snapshot(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_market_snapshot",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_connector_result(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_read_only_connector_result",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_ui_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_read_only_ui_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_evidence_item(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_read_only_evidence_item",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_analysis_config(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_market_analysis_config",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_analysis_result(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_market_analysis_result",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_dry_run_order_intent_plan(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_dry_run_order_intent_plan",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_dry_run_order_intent_result(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_dry_run_order_intent_result",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_risk_decision_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_risk_decision_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_btc_analysis_ui_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="btc_analysis_ui_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_live_credentials_config(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="live_credentials_config",
        generated_at=generated_at,
    )


def validate_secret_boundary_live_credentials_status_report(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="live_credentials_status_report",
        generated_at=generated_at,
    )


def validate_secret_boundary_live_auth_boundary_decision(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="live_auth_boundary_decision",
        generated_at=generated_at,
    )


def validate_secret_boundary_live_credentials_auth_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="live_credentials_auth_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_live_order_submission_boundary_receipt(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="live_order_submission_boundary_receipt",
        generated_at=generated_at,
    )


def validate_secret_boundary_live_order_submission_boundary_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="live_order_submission_boundary_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_live_enablement_config_preflight(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="live_enablement_config_preflight",
        generated_at=generated_at,
    )


def validate_secret_boundary_live_enablement_config_preflight_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="live_enablement_config_preflight_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_wallet_signing_boundary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="wallet_signing_boundary",
        generated_at=generated_at,
    )


def validate_secret_boundary_wallet_signing_boundary_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="wallet_signing_boundary_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_ui_panel_wallet_signing_boundary_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="operator_ui_panel_wallet_signing_boundary_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_ui_panel_live_enablement_config_preflight_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="operator_ui_panel_live_enablement_config_preflight_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_tiny_live_canary_gonogo_gate(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="tiny_live_canary_gonogo_gate",
        generated_at=generated_at,
    )


def validate_secret_boundary_telegram_operator_control_config(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="telegram_operator_control_config",
        generated_at=generated_at,
    )


def validate_secret_boundary_telegram_operator_control_state(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="telegram_operator_control_state",
        generated_at=generated_at,
    )


def validate_secret_boundary_telegram_operator_control_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="telegram_operator_control_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_telegram_mini_app_panel_payload(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="telegram_mini_app_operator_panel_payload",
        generated_at=generated_at,
    )


def validate_secret_boundary_telegram_mini_app_panel_rendered_json(
    value: str,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return _rendered_text_boundary_validation(
            value,
            artifact_type="telegram_mini_app_operator_panel_rendered_json",
            generated_at=generated_at,
        )
    if isinstance(parsed, Mapping):
        return validate_static_secret_boundary(
            parsed,
            artifact_type="telegram_mini_app_operator_panel_rendered_json",
            generated_at=generated_at,
        )
    return _rendered_text_boundary_validation(
        value,
        artifact_type="telegram_mini_app_operator_panel_rendered_json",
        generated_at=generated_at,
    )


def validate_secret_boundary_telegram_mini_app_panel_rendered_html(
    value: str,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return _rendered_text_boundary_validation(
        value,
        artifact_type="telegram_mini_app_operator_panel_rendered_html",
        generated_at=generated_at,
    )


def validate_secret_boundary_paper_daily_loop_auth_artifact(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="paper_daily_loop_live_credentials_auth_artifact",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_ui_panel_kill_switch_summary(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(
        value,
        artifact_type="operator_ui_panel_kill_switch_summary",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_ui_panel_rendered_json(
    value: str,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return _rendered_text_boundary_validation(
            value,
            artifact_type="operator_ui_panel_rendered_json",
            generated_at=generated_at,
        )
    if isinstance(parsed, Mapping):
        return validate_static_secret_boundary(
            parsed,
            artifact_type="operator_ui_panel_rendered_json",
            generated_at=generated_at,
        )
    return _rendered_text_boundary_validation(
        value,
        artifact_type="operator_ui_panel_rendered_json",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_ui_panel_rendered_markdown(
    value: str,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return _rendered_text_boundary_validation(
        value,
        artifact_type="operator_ui_panel_rendered_markdown",
        generated_at=generated_at,
    )


def validate_secret_boundary_operator_ui_panel_rendered_html(
    value: str,
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return _rendered_text_boundary_validation(
        value,
        artifact_type="operator_ui_panel_rendered_html",
        generated_at=generated_at,
    )


def validate_secret_boundary_result_artifact(
    value: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return validate_static_secret_boundary(value, artifact_type="result_artifact", generated_at=generated_at)


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
            if (
                _normalize_key(key_text) not in SAFE_TRUE_SECRET_METADATA_FIELD_NAMES
                and is_safe_negative_secret_metadata_field(key_text)
                and nested is True
            ):
                paths.append(nested_path)
            paths.extend(find_unsafe_secret_flag_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(find_unsafe_secret_flag_paths(nested, f"{path}[{index}]"))
    return paths


def find_actual_secret_value_paths(value: Any, path: str = "$", parent_key: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            paths.extend(find_actual_secret_value_paths(nested, f"{path}.{key_text}", key_text))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(find_actual_secret_value_paths(nested, f"{path}[{index}]", parent_key))
    elif isinstance(value, str):
        secret_like = _looks_like_actual_secret_value(value) or (
            _looks_like_hex_private_key(value)
            and not _value_allowed_as_public_identifier_metadata(value, parent_key=parent_key)
        )
        if secret_like and not _value_allowed_as_symbolic_live_credential_metadata(value, parent_key=parent_key):
            paths.append(path)
    return paths


def find_forbidden_operator_intent_field_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            nested_path = f"{path}.{key_text}"
            if is_forbidden_operator_intent_field_name(key_text):
                paths.append(nested_path)
            paths.extend(find_forbidden_operator_intent_field_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(find_forbidden_operator_intent_field_paths(nested, f"{path}[{index}]"))
    return paths


def find_human_operator_signed_intent_field_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            nested_path = f"{path}.{key_text}"
            if _normalize_key(key_text) in ALLOWED_HUMAN_OPERATOR_SIGNED_INTENT_FIELD_NAMES:
                paths.append(nested_path)
            paths.extend(find_human_operator_signed_intent_field_paths(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(find_human_operator_signed_intent_field_paths(nested, f"{path}[{index}]"))
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


def is_forbidden_operator_intent_field_name(name: str) -> bool:
    normalized = _normalize_key(name)
    if not normalized:
        return False
    if normalized in ALLOWED_HUMAN_OPERATOR_SIGNED_INTENT_FIELD_NAMES:
        return False
    if normalized in FORBIDDEN_OPERATOR_INTENT_FIELD_NAMES:
        return True
    tokens = [token for token in normalized.split("_") if token]
    if "signature" in tokens:
        return True
    if "signed" in tokens:
        return True
    for suffix in FORBIDDEN_OPERATOR_INTENT_FIELD_NAMES:
        if normalized.endswith(f"_{suffix}") or normalized == suffix:
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


def _looks_like_actual_secret_value(value: Any) -> bool:
    text = clean_text(value)
    if not text:
        return False
    lowered = text.lower()
    if "-----begin" in lowered and "private key" in lowered:
        return True
    if lowered.startswith("bearer "):
        return True
    if lowered.startswith(("sk-", "sk_live_", "pk_live_", "sk-proj-")):
        return True
    if "authorization: bearer " in lowered:
        return True
    if "auth_header=" in lowered:
        return True
    if any(
        marker in lowered
        for marker in (
            "mnemonic:",
            "seed phrase:",
            "seed_phrase=",
            "raw_secret=",
            "raw_private_key=",
            "secret_value=",
            "signed_order=",
            "signed_payload=",
            "raw_transaction=",
            "order_submission_payload=",
            "transaction_payload=",
        )
    ):
        return True
    return False


def _looks_like_hex_private_key(value: str) -> bool:
    text = clean_text(value)
    if text.startswith(("0x", "0X")):
        text = text[2:]
    if len(text) < 64:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in text)


def _value_allowed_as_symbolic_live_credential_metadata(value: str, *, parent_key: str) -> bool:
    text = clean_text(value)
    if not text:
        return False
    normalized_parent = _normalize_key(parent_key)
    symbolic_parent_names = {
        "env_var_name",
        "config_key",
        "requirement_id",
        "missing_requirements",
        "policy_violation_code",
        "code",
        "decision_status",
        "boundary_statuses",
        "live_credentials_boundary_status",
    }
    if normalized_parent not in symbolic_parent_names:
        return False
    if text in SAFE_PLACEHOLDER_MARKERS:
        return True
    return text.upper() == text and all(character.isalnum() or character == "_" for character in text)


def _value_allowed_as_public_identifier_metadata(value: str, *, parent_key: str) -> bool:
    normalized_parent = _normalize_key(parent_key)
    if any(
        normalized_parent.endswith(suffix)
        for suffix in (
            "_id",
            "_ids",
            "_hash",
            "_hashes",
            "_reference",
            "_references",
        )
    ):
        return True
    return normalized_parent in {
        "id",
        "ids",
        "hash",
        "hashes",
        "condition_id",
        "token_id",
        "asset_id",
        "market_id",
        "snapshot_id",
        "source_payload_hash",
        "payload_hash",
    }


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


def _human_operator_signed_context_declared(value: Any) -> bool:
    try:
        text = json.dumps(value, sort_keys=True).lower()
    except TypeError:
        text = str(value).lower()
    if "human acknowledgement only" not in text:
        return False
    if "cryptographic signing" not in text:
        return False
    if isinstance(value, Mapping):
        flag = value.get("operator_signed_intent_is_human_acknowledgement_only")
        if flag is True:
            return True
    return "does not authorize live execution" in text or "no cryptographic signing" in text


def _rendered_text_boundary_validation(
    value: str,
    *,
    artifact_type: str,
    generated_at: str,
) -> dict[str, Any]:
    text = str(value)
    forbidden_tokens = []
    for key in sorted(FORBIDDEN_PAYLOAD_KEYS):
        if _contains_rendered_forbidden_token(text, key):
            forbidden_tokens.append(key)
    validation_id = _stable_id(
        "static-rendered-secret-boundary-validation-036",
        {"artifact_type": artifact_type, "forbidden_rendered_tokens": forbidden_tokens},
    )
    valid = not forbidden_tokens
    return {
        "contract_version": STATIC_SECRET_VALIDATION_CONTRACT,
        "validation_id": validation_id,
        "artifact_type": clean_text(artifact_type),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "forbidden_secret_field_paths": [],
        "forbidden_secret_field_count": 0,
        "forbidden_rendered_tokens": forbidden_tokens,
        "forbidden_rendered_token_count": len(forbidden_tokens),
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "static_validation_only": True,
    }


def _contains_rendered_forbidden_token(text: str, token: str) -> bool:
    normalized_text = text.lower()
    normalized_token = token.lower()
    delimiters = {'"', "'", "`", "<", ">", ":", "=", " ", "\n", "\t"}
    start = 0
    while True:
        index = normalized_text.find(normalized_token, start)
        if index < 0:
            return False
        before = normalized_text[index - 1] if index > 0 else " "
        after_index = index + len(normalized_token)
        after = normalized_text[after_index] if after_index < len(normalized_text) else " "
        if before in delimiters and after in delimiters:
            return True
        start = index + len(normalized_token)


def _dedupe_paths(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
