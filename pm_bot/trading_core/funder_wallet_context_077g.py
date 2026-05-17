from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.artifact_resolution import (
    DEFAULT_ARTIFACT_ROOT,
    resolve_artifact_subdir,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

TASK_ID = "ORCH-PMBOT-RUNTIME-077G-FUNDER-WALLET-CONTEXT-DIAGNOSTIC-NO-LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

MODE = "funder wallet context diagnostic / redacted env metadata / no-live"
EXECUTION_MODE = "funder_wallet_context_diagnostic"

FUNDER_WALLET_CONTEXT_RESULT_CONTRACT = "pmbot_funder_wallet_context_077g_result.v1"
FUNDER_WALLET_CONTEXT_LATEST_STATUS_CONTRACT = "pmbot_latest_funder_wallet_context_077g_status.v1"
FUNDER_WALLET_CONTEXT_OPERATOR_SUMMARY_CONTRACT = "pmbot_funder_wallet_context_077g_operator_summary.v1"
FUNDER_WALLET_CONTEXT_VALIDATION_CONTRACT = "pmbot_funder_wallet_context_077g_validation.v1"

STATUS_WALLET_CONTEXT_VISIBLE = "wallet_context_visible"
STATUS_BLOCKED_MISSING_WALLET_ADDRESS = "blocked_missing_wallet_address"
STATUS_BLOCKED_MISSING_FUNDER_ADDRESS = "blocked_missing_funder_address"
STATUS_FUNDER_EQUALS_WALLET_ADDRESS = "funder_equals_wallet_address"
STATUS_FUNDER_DIFFERS_FROM_WALLET_ADDRESS = "funder_differs_from_wallet_address"
STATUS_SIGNATURE_TYPE_PRESENT = "signature_type_present"
STATUS_BLOCKED_MISSING_SIGNATURE_TYPE = "blocked_missing_signature_type"

VALID_STATUSES = {
    STATUS_WALLET_CONTEXT_VISIBLE,
    STATUS_BLOCKED_MISSING_WALLET_ADDRESS,
    STATUS_BLOCKED_MISSING_FUNDER_ADDRESS,
    STATUS_FUNDER_EQUALS_WALLET_ADDRESS,
    STATUS_FUNDER_DIFFERS_FROM_WALLET_ADDRESS,
    STATUS_SIGNATURE_TYPE_PRESENT,
    STATUS_BLOCKED_MISSING_SIGNATURE_TYPE,
}

ARTIFACT_DIR_NAME = "funder_wallet_context_077g"
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME

POLYMARKET_WALLET_ADDRESS = "POLYMARKET_WALLET_ADDRESS"
POLYMARKET_FUNDER_ADDRESS = "POLYMARKET_FUNDER_ADDRESS"
POLYMARKET_SIGNATURE_TYPE = "POLYMARKET_SIGNATURE_TYPE"
POLYMARKET_PRIVATE_KEY = "POLYMARKET_PRIVATE_KEY"

REQUESTED_ENV_VAR_NAMES = (
    POLYMARKET_WALLET_ADDRESS,
    POLYMARKET_FUNDER_ADDRESS,
    POLYMARKET_SIGNATURE_TYPE,
    POLYMARKET_PRIVATE_KEY,
)

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--wallet-connect",
    "--connect-wallet",
    "--sign",
    "--signing",
    "--submit",
    "--cancel",
    "--approve-live",
    "--order",
    "--order-payload",
    "--private-key",
    "--polymarket-private-key",
    "--api-secret",
    "--passphrase",
    "--seed",
    "--mnemonic",
    "--env-dump",
    "--print-env",
    "--write-env",
    "--set-funder",
    "--copy-wallet-to-funder",
    "--browser",
    "--loop",
    "--daemon",
    "--scheduler",
)

REQUIRED_FALSE_FLAGS = (
    "allowed_for_live",
    "trading_requested",
    "live_execution_approved",
    "live_execution_allowed",
    "live_execution_performed",
    "real_execution_available",
    "order_submission_enabled",
    "order_submission_attempted",
    "order_submission_performed",
    "order_submitted",
    "order_cancel_enabled",
    "order_cancellation_attempted",
    "order_cancellation_performed",
    "signing_enabled",
    "signing_attempted",
    "signing_by_default",
    "signer_instantiated",
    "signer_instantiation_attempted",
    "wallet_connection_attempted",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "full_signed_payload_output",
    "raw_values_emitted",
    "raw_secret_values_emitted",
    "private_key_raw_value_emitted",
    "api_secret_raw_value_emitted",
    "passphrase_raw_value_emitted",
    "full_signed_payload_emitted",
    "wallet_connection_ui_added",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
    "environment_modified",
    "dotenv_files_written",
    "funder_auto_inferred",
    "funder_auto_copied_from_wallet",
    "private_key_read",
)


@dataclass(frozen=True)
class EnvVarSpec:
    env_var_name: str
    group: str
    presence_only: bool = False


ENV_SPECS = (
    EnvVarSpec(POLYMARKET_WALLET_ADDRESS, "wallet"),
    EnvVarSpec(POLYMARKET_FUNDER_ADDRESS, "wallet"),
    EnvVarSpec(POLYMARKET_SIGNATURE_TYPE, "wallet"),
    EnvVarSpec(POLYMARKET_PRIVATE_KEY, "signer", presence_only=True),
)


def funder_wallet_context_artifact_paths(
    artifact_dir: str | Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Path]:
    root = resolve_artifact_subdir(
        ARTIFACT_DIR_NAME,
        artifact_dir=artifact_dir,
        environ=environ,
    )
    return {
        "root": root,
        "result": root / "funder_wallet_context_077g_result.json",
        "latest_status": root / "latest_funder_wallet_context_077g_status.json",
        "operator_md": root / "funder_wallet_context_077g_operator_summary.md",
    }


def run_funder_wallet_context_diagnostic(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
    head_before: str = "",
    head_after: str = "",
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("funder wallet context diagnostic requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    active_environ = os.environ if environ is None else environ
    paths = funder_wallet_context_artifact_paths(artifact_dir, environ=active_environ)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    env_rows = [_env_var_status(spec, active_environ) for spec in ENV_SPECS]
    rows_by_name = {row["env_var_name"]: row for row in env_rows}
    summary = _build_context_summary(active_environ=active_environ, rows_by_name=rows_by_name)
    status = _status_for_context(summary)
    statuses = _statuses_for_context(summary, status)
    suggested_safe_action = _suggested_safe_action(status)
    blockers = _build_blockers(
        summary=summary,
        status=status,
        suggested_safe_action=suggested_safe_action,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        status=status,
        statuses=statuses,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        summary=summary,
        blockers=blockers,
        suggested_safe_action=suggested_safe_action,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    result: dict[str, Any] = {
        "contract_version": FUNDER_WALLET_CONTEXT_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "statuses": statuses,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "environment_variable_allowlist": list(REQUESTED_ENV_VAR_NAMES),
        "env_var_statuses": env_rows,
        "context_summary": summary,
        "polymarket_funder_address_context": _funder_address_context(summary, suggested_safe_action),
        "suggested_safe_action": suggested_safe_action,
        "missing_required_env_vars": _missing_required_env_vars(summary),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary(status=status, summary=summary, action=suggested_safe_action),
        "head_before": clean_text(head_before),
        "head_after": clean_text(head_after),
        "generated_at": generated_at,
        **funder_wallet_context_safety_flags(),
    }
    result["validation"] = validate_funder_wallet_context_result(result)

    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_funder_wallet_context_markdown(result))
    return result


def render_funder_wallet_context_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    rows = [dict(row) for row in value.get("env_var_statuses", []) if isinstance(row, Mapping)]
    lines = [
        "Funder wallet context diagnostic 077G completed.",
        f"Status: {clean_text(value.get('status'))}",
        f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
        f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
        f"Wallet address present: {str(latest.get('wallet_address_present') is True).lower()}",
        f"Funder address present: {str(latest.get('funder_address_present') is True).lower()}",
        f"Signature type present: {str(latest.get('signature_type_present') is True).lower()}",
        f"Private key present: {str(latest.get('private_key_present') is True).lower()}",
        f"Wallet context visible: {str(latest.get('wallet_context_visible') is True).lower()}",
        f"Funder relationship: {clean_text(latest.get('funder_relationship_status')) or 'unknown'}",
        f"Suggested safe action: {clean_text(latest.get('suggested_safe_action'))}",
        "Raw secret output: false",
        "Funder auto inferred: false",
        "Funder auto copied from wallet: false",
        "Signer instantiated: false",
        "Order submission enabled: false",
        "Allowed for live: false",
        "Env variable status:",
    ]
    lines.extend(f"- {_render_env_row(row)}" for row in rows)
    lines.append(f"Artifact: {clean_text(latest.get('artifact_path'))}")
    return "\n".join(lines)


def render_funder_wallet_context_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    rows = [dict(row) for row in value.get("env_var_statuses", []) if isinstance(row, Mapping)]
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Funder Wallet Context Diagnostic 077G",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Statuses: `{', '.join(str(item) for item in value.get('statuses', []))}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        "- Mode: `funder wallet context diagnostic / redacted env metadata / no-live`",
        "- raw secret output: `false`",
        "- funder_auto_inferred: `false`",
        "- funder_auto_copied_from_wallet: `false`",
        "- signer instantiated: `false`",
        "- order submission enabled: `false`",
        "- allowed_for_live: `false`",
        "",
        "## Wallet Context",
        "",
        f"- wallet_address_present: `{str(latest.get('wallet_address_present') is True).lower()}`",
        f"- funder_address_present: `{str(latest.get('funder_address_present') is True).lower()}`",
        f"- signature_type_present: `{str(latest.get('signature_type_present') is True).lower()}`",
        f"- private_key_present: `{str(latest.get('private_key_present') is True).lower()}`",
        f"- wallet_context_visible: `{str(latest.get('wallet_context_visible') is True).lower()}`",
        f"- funder_relationship_status: `{latest.get('funder_relationship_status') or 'unknown'}`",
        f"- suggested_safe_action: `{latest.get('suggested_safe_action')}`",
        "",
        "## Environment Variables",
        "",
        *bullet_lines(_render_env_row(row) for row in rows),
        "",
        "## Blockers",
        "",
        *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
        "",
        "## Safety",
        "",
        "- this diagnostic reads only the explicit environment variable allowlist",
        "- it does not read dotenv files, wallet files, browser profiles, or credential stores",
        "- it does not modify environment variables or copy wallet address into funder address",
        "- it does not call Polymarket API, instantiate signers, sign payloads, submit orders, or cancel orders",
        "- POLYMARKET_PRIVATE_KEY is reported as presence only",
        "",
        "## Safe Next Command",
        "",
        "- `python -m pm_bot.operator_runner.funder_wallet_context_diagnostic --market BTC --strategy tiny-momentum --dry-run`",
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"`{path}`" for path in paths.values()),
    ]
    return "\n".join(lines).rstrip() + "\n"


def validate_funder_wallet_context_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(value.get("status"))

    if value.get("contract_version") != FUNDER_WALLET_CONTEXT_RESULT_CONTRACT:
        errors.append(f"contract_version must be {FUNDER_WALLET_CONTEXT_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")
        statuses.append("task_id_mismatch")
    if status not in VALID_STATUSES:
        errors.append("status must be a recognized 077G funder wallet context status")
        statuses.append("invalid_status")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    for field in REQUIRED_FALSE_FLAGS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
            statuses.append("unsafe_flag_detected")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
        statuses.append("resolved_blocker_detected")

    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("nested_unsafe_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("nested_resolved_blocker_detected")
        if key in {"raw_value", "value", "secret", "private_key", "api_secret", "passphrase"}:
            errors.append(f"{path}.{key} must not be emitted")
            statuses.append("forbidden_raw_value_field_detected")

    for row in value.get("env_var_statuses", []):
        if not isinstance(row, Mapping):
            continue
        if row.get("env_var_name") == POLYMARKET_PRIVATE_KEY:
            if row.get("presence_only") is not True:
                errors.append("POLYMARKET_PRIVATE_KEY row must be presence_only")
                statuses.append("private_key_presence_only_missing")
            if "length" in row or "redacted_fingerprint_sha256_12" in row or "redacted_value_preview" in row:
                errors.append("POLYMARKET_PRIVATE_KEY row must not include length, fingerprint, or value preview")
                statuses.append("private_key_metadata_overexposed")

    summary = dict(value.get("context_summary", {}))
    if status == STATUS_BLOCKED_MISSING_FUNDER_ADDRESS:
        expected = "set POLYMARKET_FUNDER_ADDRESS if required by account/proxy wallet setup"
        if value.get("suggested_safe_action") != expected:
            errors.append("missing funder status must provide the required suggested_safe_action")
            statuses.append("missing_funder_suggested_action_mismatch")
        if summary.get("wallet_address_present") is not True:
            errors.append("blocked_missing_funder_address requires visible wallet address")
            statuses.append("missing_funder_without_wallet_context")
    if status == STATUS_FUNDER_EQUALS_WALLET_ADDRESS and summary.get("funder_matches_wallet_address") is not True:
        errors.append("funder_equals_wallet_address requires explicit equal wallet and funder env values")
        statuses.append("funder_equal_status_without_match")
    if status == STATUS_FUNDER_DIFFERS_FROM_WALLET_ADDRESS and summary.get("funder_differs_from_wallet_address") is not True:
        errors.append("funder_differs_from_wallet_address requires explicit different wallet and funder env values")
        statuses.append("funder_differs_status_without_difference")

    valid = not errors
    return {
        "contract_version": FUNDER_WALLET_CONTEXT_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["funder_wallet_context_result_valid"]
            if valid
            else ["funder_wallet_context_result_blocked"]
        ),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **funder_wallet_context_safety_flags(),
    }


def funder_wallet_context_safety_flags() -> dict[str, Any]:
    return {
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "paper_only": True,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "safe_summary_only": True,
        "non_executable": True,
        "explicit_env_var_allowlist_only": True,
        "broad_environment_scan_performed": False,
        "environment_files_read": False,
        "dotenv_files_read": False,
        "wallet_files_read": False,
        "browser_profiles_read": False,
        "credential_stores_read": False,
        "network_access_performed": False,
        "polymarket_api_calls_performed": 0,
        "environment_modified": False,
        "dotenv_files_written": False,
        "funder_auto_inferred": False,
        "funder_auto_copied_from_wallet": False,
        "raw_values_emitted": False,
        "raw_secret_values_emitted": False,
        "private_key_read": False,
        "private_key_raw_value_emitted": False,
        "api_secret_raw_value_emitted": False,
        "passphrase_raw_value_emitted": False,
        "full_signed_payload_output": False,
        "full_signed_payload_emitted": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "signing_by_default": False,
        "signer_instantiated": False,
        "signer_instantiation_attempted": False,
        "wallet_connection_attempted": False,
        "wallet_connection_ui_added": False,
        "wallet_signing_enabled": False,
        "wallet_signing_attempted": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "order_cancel_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "allowed_for_live": False,
        "trading_requested": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
    }


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "funder wallet context diagnostic is redacted/no-live/no-submit/no-sign/no-env-write; "
            "unsupported live/auth/wallet/sign/order/secret/env-write flag(s): "
            + ", ".join(requested)
        )


def _env_var_status(spec: EnvVarSpec, environ: Mapping[str, str]) -> dict[str, Any]:
    raw = environ.get(spec.env_var_name)
    text = "" if raw is None else str(raw)
    present = bool(text.strip())
    row: dict[str, Any] = {
        "contract_version": "pmbot_funder_wallet_context_077g_env_var_status.v1",
        "task_id": TASK_ID,
        "env_var_name": spec.env_var_name,
        "group": spec.group,
        "presence_only": spec.presence_only is True,
        "present": present,
        "redaction_status": "present_redacted" if present else "missing",
        "raw_value_emitted": False,
        "safe_for_artifacts": True,
    }
    if spec.presence_only:
        row["presence_only_reason"] = "POLYMARKET_PRIVATE_KEY presence only; length, fingerprint, and preview are not emitted"
        return row
    row["length"] = len(text) if present else 0
    row["redacted_fingerprint_sha256_12"] = (
        _redacted_fingerprint(spec.env_var_name, text) if present else ""
    )
    row["redacted_value_preview"] = _redacted_preview(text) if present else ""
    return row


def _build_context_summary(
    *,
    active_environ: Mapping[str, str],
    rows_by_name: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    def present(name: str) -> bool:
        return dict(rows_by_name.get(name, {})).get("present") is True

    wallet_present = present(POLYMARKET_WALLET_ADDRESS)
    funder_present = present(POLYMARKET_FUNDER_ADDRESS)
    signature_present = present(POLYMARKET_SIGNATURE_TYPE)
    pkey_present = present(POLYMARKET_PRIVATE_KEY)
    wallet_text = clean_text(active_environ.get(POLYMARKET_WALLET_ADDRESS))
    funder_text = clean_text(active_environ.get(POLYMARKET_FUNDER_ADDRESS))
    wallet_norm = _normalize_comparable_address(wallet_text)
    funder_norm = _normalize_comparable_address(funder_text)
    can_compare = bool(wallet_norm and funder_norm)
    matches = can_compare and wallet_norm == funder_norm
    differs = can_compare and wallet_norm != funder_norm
    relationship = ""
    if matches:
        relationship = STATUS_FUNDER_EQUALS_WALLET_ADDRESS
    elif differs:
        relationship = STATUS_FUNDER_DIFFERS_FROM_WALLET_ADDRESS
    return {
        "wallet_address_present": wallet_present,
        "funder_address_present": funder_present,
        "signature_type_present": signature_present,
        "private_key_present": pkey_present,
        "wallet_context_visible": wallet_present and funder_present and signature_present,
        "wallet_and_funder_comparable": can_compare,
        "funder_relationship_status": relationship or "unknown_not_compared",
        "funder_matches_wallet_address": matches,
        "funder_differs_from_wallet_address": differs,
        "funder_required_by_account_setup": "unknown_not_inferred",
        "funder_required_by_account_setup_inferred": False,
        "funder_required_for_complete_wallet_context": True,
        "funder_missing_but_wallet_present": wallet_present and not funder_present,
        "wallet_missing_blocks_funder_relationship_check": not wallet_present,
        "signature_type_missing": not signature_present,
        "claim_wallet_equals_funder_only_when_env_equal": matches,
        "funder_auto_inferred": False,
        "funder_auto_copied_from_wallet": False,
    }


def _status_for_context(summary: Mapping[str, Any]) -> str:
    if summary.get("wallet_address_present") is not True:
        return STATUS_BLOCKED_MISSING_WALLET_ADDRESS
    if summary.get("funder_address_present") is not True:
        return STATUS_BLOCKED_MISSING_FUNDER_ADDRESS
    if summary.get("signature_type_present") is not True:
        return STATUS_BLOCKED_MISSING_SIGNATURE_TYPE
    if summary.get("funder_matches_wallet_address") is True:
        return STATUS_FUNDER_EQUALS_WALLET_ADDRESS
    if summary.get("funder_differs_from_wallet_address") is True:
        return STATUS_FUNDER_DIFFERS_FROM_WALLET_ADDRESS
    return STATUS_WALLET_CONTEXT_VISIBLE


def _statuses_for_context(summary: Mapping[str, Any], status: str) -> list[str]:
    statuses = [status]
    if summary.get("wallet_context_visible") is True:
        statuses.append(STATUS_WALLET_CONTEXT_VISIBLE)
    if summary.get("signature_type_present") is True:
        statuses.append(STATUS_SIGNATURE_TYPE_PRESENT)
    elif summary.get("wallet_address_present") is True:
        statuses.append(STATUS_BLOCKED_MISSING_SIGNATURE_TYPE)
    relationship = clean_text(summary.get("funder_relationship_status"))
    if relationship in {STATUS_FUNDER_EQUALS_WALLET_ADDRESS, STATUS_FUNDER_DIFFERS_FROM_WALLET_ADDRESS}:
        statuses.append(relationship)
    if summary.get("wallet_address_present") is True and summary.get("funder_address_present") is not True:
        statuses.append(STATUS_BLOCKED_MISSING_FUNDER_ADDRESS)
    return _dedupe(statuses)


def _funder_address_context(summary: Mapping[str, Any], suggested_safe_action: str) -> dict[str, Any]:
    return {
        "env_var_name": POLYMARKET_FUNDER_ADDRESS,
        "present": summary.get("funder_address_present") is True,
        "status": (
            STATUS_BLOCKED_MISSING_FUNDER_ADDRESS
            if summary.get("funder_missing_but_wallet_present") is True
            else clean_text(summary.get("funder_relationship_status")) or "unknown_not_compared"
        ),
        "required_by_account_setup": "unknown_not_inferred",
        "required_by_account_setup_inferred": False,
        "required_for_complete_wallet_context": True,
        "relationship_to_wallet_address": clean_text(summary.get("funder_relationship_status")),
        "auto_inferred": False,
        "auto_copied_from_wallet": False,
        "suggested_safe_action": suggested_safe_action,
    }


def _build_latest_status(
    *,
    status: str,
    statuses: Sequence[str],
    market_symbol: str,
    strategy_name: str,
    summary: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    suggested_safe_action: str,
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": FUNDER_WALLET_CONTEXT_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "statuses": list(statuses),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "wallet_address_present": summary.get("wallet_address_present") is True,
        "funder_address_present": summary.get("funder_address_present") is True,
        "signature_type_present": summary.get("signature_type_present") is True,
        "private_key_present": summary.get("private_key_present") is True,
        "wallet_context_visible": summary.get("wallet_context_visible") is True,
        "funder_relationship_status": clean_text(summary.get("funder_relationship_status")),
        "funder_matches_wallet_address": summary.get("funder_matches_wallet_address") is True,
        "funder_differs_from_wallet_address": summary.get("funder_differs_from_wallet_address") is True,
        "funder_required_by_account_setup": "unknown_not_inferred",
        "funder_required_by_account_setup_inferred": False,
        "funder_required_for_complete_wallet_context": True,
        "suggested_safe_action": suggested_safe_action,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "operator_summary": _operator_summary(status=status, summary=summary, action=suggested_safe_action),
        "generated_at": generated_at,
    }
    value.update(funder_wallet_context_safety_flags())
    return value


def _build_blockers(
    *,
    summary: Mapping[str, Any],
    status: str,
    suggested_safe_action: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if summary.get("wallet_address_present") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_MISSING_WALLET_ADDRESS,
                "wallet_env_visibility",
                "POLYMARKET_WALLET_ADDRESS is missing in this runtime process context.",
                [POLYMARKET_WALLET_ADDRESS],
                suggested_safe_action="set POLYMARKET_WALLET_ADDRESS before evaluating funder context",
                generated_at=generated_at,
            )
        )
    if status == STATUS_BLOCKED_MISSING_FUNDER_ADDRESS:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_MISSING_FUNDER_ADDRESS,
                "funder_env_visibility",
                "POLYMARKET_FUNDER_ADDRESS is missing while POLYMARKET_WALLET_ADDRESS is visible.",
                [POLYMARKET_FUNDER_ADDRESS],
                suggested_safe_action=suggested_safe_action,
                generated_at=generated_at,
            )
        )
    if summary.get("signature_type_present") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_MISSING_SIGNATURE_TYPE,
                "signature_type_env_visibility",
                "POLYMARKET_SIGNATURE_TYPE is missing in this runtime process context.",
                [POLYMARKET_SIGNATURE_TYPE],
                suggested_safe_action="set POLYMARKET_SIGNATURE_TYPE to the account-required signature type",
                generated_at=generated_at,
            )
        )
    return blockers


def _blocker(
    blocker_id: str,
    category: str,
    reason: str,
    missing_env_vars: Sequence[Any],
    *,
    suggested_safe_action: str,
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_funder_wallet_context_077g_blocker.v1",
        "task_id": TASK_ID,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "missing_env_vars": [clean_text(item) for item in missing_env_vars if clean_text(item)],
        "suggested_safe_action": clean_text(suggested_safe_action),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
        "allowed_for_live": False,
        "generated_at": generated_at,
    }
    value.update(funder_wallet_context_safety_flags())
    return value


def _operator_summary(*, status: str, summary: Mapping[str, Any], action: str) -> str:
    if status == STATUS_BLOCKED_MISSING_WALLET_ADDRESS:
        return "Wallet context is blocked because POLYMARKET_WALLET_ADDRESS is missing."
    if status == STATUS_BLOCKED_MISSING_FUNDER_ADDRESS:
        return (
            "Wallet address is visible, but POLYMARKET_FUNDER_ADDRESS is missing. "
            f"Suggested safe action: {action}."
        )
    if status == STATUS_BLOCKED_MISSING_SIGNATURE_TYPE:
        return "Wallet and funder are visible, but POLYMARKET_SIGNATURE_TYPE is missing."
    if status == STATUS_FUNDER_EQUALS_WALLET_ADDRESS:
        return (
            "Wallet context is visible and funder equals wallet only because both env vars are present "
            "and compare equal after normalization; no funder was inferred or copied."
        )
    if status == STATUS_FUNDER_DIFFERS_FROM_WALLET_ADDRESS:
        return (
            "Wallet context is visible and funder differs from wallet because both env vars are present "
            "and compare different after normalization; no funder was inferred or copied."
        )
    if summary.get("wallet_context_visible") is True:
        return "Wallet context is visible; funder relationship is not inferred beyond explicit env comparison."
    return "Wallet context diagnostic completed without enabling live execution."


def _suggested_safe_action(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING_FUNDER_ADDRESS:
        return "set POLYMARKET_FUNDER_ADDRESS if required by account/proxy wallet setup"
    if status == STATUS_BLOCKED_MISSING_WALLET_ADDRESS:
        return "set POLYMARKET_WALLET_ADDRESS before evaluating funder context"
    if status == STATUS_BLOCKED_MISSING_SIGNATURE_TYPE:
        return "set POLYMARKET_SIGNATURE_TYPE to the account-required signature type"
    return "no automatic funder action; rerun this dry-run diagnostic after any operator-managed env change"


def _missing_required_env_vars(summary: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    if summary.get("wallet_address_present") is not True:
        missing.append(POLYMARKET_WALLET_ADDRESS)
    if summary.get("wallet_address_present") is True and summary.get("funder_address_present") is not True:
        missing.append(POLYMARKET_FUNDER_ADDRESS)
    if summary.get("signature_type_present") is not True:
        missing.append(POLYMARKET_SIGNATURE_TYPE)
    return missing


def _render_env_row(row: Mapping[str, Any]) -> str:
    base = (
        f"{clean_text(row.get('env_var_name'))}: "
        f"present={str(row.get('present') is True).lower()} "
        f"redaction={clean_text(row.get('redaction_status')) or 'missing'}"
    )
    if row.get("presence_only") is True:
        return base + " presence_only=true"
    return (
        base
        + f" length={int(row.get('length', 0) or 0)} "
        + f"fingerprint={clean_text(row.get('redacted_fingerprint_sha256_12')) or 'missing'} "
        + f"preview={clean_text(row.get('redacted_value_preview')) or 'missing'}"
    )


def _redacted_fingerprint(env_var_name: str, value: str) -> str:
    payload = f"pmbot-077g\0{env_var_name}\0{len(value)}\0{value}".encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:12]


def _redacted_preview(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if text.lower().startswith("0x") and len(text) >= 10:
        return f"{text[:6]}...{text[-4:]}"
    return "present_redacted"


def _normalize_comparable_address(value: str) -> str:
    return clean_text(value).lower()


def _walk_fields(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            rows.append((path, key_text, nested))
            rows.extend(_walk_fields(nested, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_fields(nested, f"{path}[{index}]"))
    return rows


def _dedupe(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result
