from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

TASK_ID = "ORCH-PMBOT-RUNTIME-077C-CREDENTIAL-VISIBILITY-DIAGNOSTIC-AND-RUNBOOK-NO-LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

MODE = "runtime credential visibility diagnostic / redacted env metadata / no-live"
EXECUTION_MODE = "runtime_environment_visibility_diagnostic"

RUNTIME_CREDENTIAL_VISIBILITY_RESULT_CONTRACT = "pmbot_runtime_credential_visibility_077c_result.v1"
RUNTIME_CREDENTIAL_VISIBILITY_LATEST_STATUS_CONTRACT = "pmbot_latest_runtime_credential_visibility_077c_status.v1"
RUNTIME_CREDENTIAL_VISIBILITY_OPERATOR_SUMMARY_CONTRACT = (
    "pmbot_runtime_credential_visibility_077c_operator_summary.v1"
)
RUNTIME_CREDENTIAL_VISIBILITY_VALIDATION_CONTRACT = "pmbot_runtime_credential_visibility_077c_validation.v1"

STATUS_RUNTIME_CREDENTIALS_VISIBLE = "runtime_credentials_visible"
STATUS_BLOCKED_MISSING_PRIVATE_KEY = "blocked_missing_private_key"
STATUS_BLOCKED_MISSING_POLYMARKET_L2_CREDENTIALS = "blocked_missing_polymarket_l2_credentials"
STATUS_BLOCKED_MISSING_WALLET_ADDRESS = "blocked_missing_wallet_address"
STATUS_BLOCKED_MISSING_TELEGRAM_CREDENTIALS = "blocked_missing_telegram_credentials"

VALID_STATUSES = {
    STATUS_RUNTIME_CREDENTIALS_VISIBLE,
    STATUS_BLOCKED_MISSING_PRIVATE_KEY,
    STATUS_BLOCKED_MISSING_POLYMARKET_L2_CREDENTIALS,
    STATUS_BLOCKED_MISSING_WALLET_ADDRESS,
    STATUS_BLOCKED_MISSING_TELEGRAM_CREDENTIALS,
}

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "runtime_credential_visibility_077c"

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--wallet-connect",
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
    "--telegram-token",
    "--env-dump",
    "--print-env",
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
    "telegram_token_raw_value_emitted",
    "full_signed_payload_emitted",
    "wallet_connection_ui_added",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)


@dataclass(frozen=True)
class EnvVarSpec:
    env_var_name: str
    group: str
    required_for_prompt: bool = True
    required_for_runtime_status: bool = True
    runtime_alias_for: str = ""


REQUESTED_ENV_SPECS = (
    EnvVarSpec("POLYMARKET_API_KEY", "polymarket_l2"),
    EnvVarSpec("POLYMARKET_API_SECRET", "polymarket_l2"),
    EnvVarSpec("POLYMARKET_API_PASSPHRASE", "polymarket_l2"),
    EnvVarSpec("POLYMARKET_PRIVATE_KEY", "signer"),
    EnvVarSpec("POLYMARKET_WALLET_ADDRESS", "wallet"),
    EnvVarSpec("POLYMARKET_SIGNATURE_TYPE", "wallet"),
    EnvVarSpec("POLYMARKET_FUNDER_ADDRESS", "wallet"),
    EnvVarSpec(
        "TELEGRAM_BOT_TOKEN",
        "telegram_operator_reported",
        required_for_runtime_status=False,
    ),
    EnvVarSpec(
        "TELEGRAM_ALLOWED_OPERATOR_IDS",
        "telegram_operator_reported",
        required_for_runtime_status=False,
    ),
)

TELEGRAM_RUNTIME_ALIAS_SPECS = (
    EnvVarSpec(
        "PMBOT_TELEGRAM_BOT_TOKEN",
        "telegram_runtime",
        required_for_prompt=False,
        required_for_runtime_status=True,
        runtime_alias_for="TELEGRAM_BOT_TOKEN",
    ),
    EnvVarSpec(
        "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS",
        "telegram_runtime",
        required_for_prompt=False,
        required_for_runtime_status=True,
        runtime_alias_for="TELEGRAM_ALLOWED_OPERATOR_IDS",
    ),
)

ALL_ENV_SPECS = (*REQUESTED_ENV_SPECS, *TELEGRAM_RUNTIME_ALIAS_SPECS)
REQUESTED_ENV_VAR_NAMES = tuple(spec.env_var_name for spec in REQUESTED_ENV_SPECS)
TELEGRAM_RUNTIME_ALIAS_ENV_VAR_NAMES = tuple(spec.env_var_name for spec in TELEGRAM_RUNTIME_ALIAS_SPECS)

POLYMARKET_L2_ENV_VAR_NAMES = (
    "POLYMARKET_API_KEY",
    "POLYMARKET_API_SECRET",
    "POLYMARKET_API_PASSPHRASE",
)
WALLET_ENV_VAR_NAMES = (
    "POLYMARKET_WALLET_ADDRESS",
    "POLYMARKET_SIGNATURE_TYPE",
    "POLYMARKET_FUNDER_ADDRESS",
)


def runtime_credential_visibility_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "runtime_credential_visibility_077c_result.json",
        "latest_status": root / "latest_runtime_credential_visibility_077c_status.json",
        "operator_md": root / "runtime_credential_visibility_077c_operator_summary.md",
    }


def run_runtime_credential_visibility_diagnostic(
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
        raise ValueError("runtime credential visibility diagnostic requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    paths = runtime_credential_visibility_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    active_environ = os.environ if environ is None else environ
    requested_rows = [_env_var_status(spec, active_environ) for spec in REQUESTED_ENV_SPECS]
    runtime_alias_rows = [_env_var_status(spec, active_environ) for spec in TELEGRAM_RUNTIME_ALIAS_SPECS]
    rows_by_name = {row["env_var_name"]: row for row in (*requested_rows, *runtime_alias_rows)}
    group_summary = _build_group_summary(rows_by_name)
    status = _status_for_group_summary(group_summary)
    blockers = _build_blockers(status=status, group_summary=group_summary, generated_at=generated_at)
    latest_status = _build_latest_status(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        group_summary=group_summary,
        blockers=blockers,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    result: dict[str, Any] = {
        "contract_version": RUNTIME_CREDENTIAL_VISIBILITY_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "environment_variable_allowlist": list(REQUESTED_ENV_VAR_NAMES),
        "telegram_runtime_alias_env_var_names": list(TELEGRAM_RUNTIME_ALIAS_ENV_VAR_NAMES),
        "requested_env_var_statuses": requested_rows,
        "runtime_alias_env_var_statuses": runtime_alias_rows,
        "group_summary": group_summary,
        "missing_required_env_vars": _missing_names(requested_rows),
        "missing_runtime_alias_env_vars": _missing_names(runtime_alias_rows),
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary(status=status, group_summary=group_summary),
        "head_before": clean_text(head_before),
        "head_after": clean_text(head_after),
        "generated_at": generated_at,
        **runtime_credential_visibility_safety_flags(),
    }
    result["validation"] = validate_runtime_credential_visibility_result(result)

    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_runtime_credential_visibility_markdown(result))
    return result


def render_runtime_credential_visibility_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    requested_rows = [dict(row) for row in value.get("requested_env_var_statuses", []) if isinstance(row, Mapping)]
    alias_rows = [dict(row) for row in value.get("runtime_alias_env_var_statuses", []) if isinstance(row, Mapping)]
    lines = [
        "Runtime credential visibility diagnostic 077C completed.",
        f"Status: {clean_text(value.get('status'))}",
        f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
        f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
        f"Prompt required vars visible: {int(latest.get('requested_present_count', 0) or 0)}/{len(REQUESTED_ENV_VAR_NAMES)}",
        f"Polymarket L2 visible: {str(latest.get('polymarket_l2_visible') is True).lower()}",
        f"Private key visible: {str(latest.get('private_key_visible') is True).lower()}",
        f"Wallet context visible: {str(latest.get('wallet_context_visible') is True).lower()}",
        f"Telegram runtime visible: {str(latest.get('telegram_credentials_visible') is True).lower()}",
        "Raw secret output: false",
        "Signer instantiated: false",
        "Order submission enabled: false",
        "Allowed for live: false",
        "Required env variable status:",
    ]
    lines.extend(f"- {_render_env_row(row)}" for row in requested_rows)
    lines.append("Telegram runtime alias status:")
    lines.extend(f"- {_render_env_row(row)}" for row in alias_rows)
    lines.append(f"Artifact: {clean_text(latest.get('artifact_path'))}")
    return "\n".join(lines)


def render_runtime_credential_visibility_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    requested_rows = [dict(row) for row in value.get("requested_env_var_statuses", []) if isinstance(row, Mapping)]
    alias_rows = [dict(row) for row in value.get("runtime_alias_env_var_statuses", []) if isinstance(row, Mapping)]
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Runtime Credential Visibility Diagnostic 077C",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        "- Mode: `runtime environment visibility diagnostic / redacted metadata / no-live`",
        "- raw secret output: `false`",
        "- signer instantiated: `false`",
        "- order submission enabled: `false`",
        "- allowed_for_live: `false`",
        "",
        "## Required Variables",
        "",
        *bullet_lines(_render_env_row(row) for row in requested_rows),
        "",
        "## Telegram Runtime Aliases",
        "",
        "- The Telegram runtime in this repo reads `PMBOT_TELEGRAM_BOT_TOKEN` and `PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS`.",
        *bullet_lines(_render_env_row(row) for row in alias_rows),
        "",
        "## Group Summary",
        "",
        f"- polymarket_l2_visible: `{str(latest.get('polymarket_l2_visible') is True).lower()}`",
        f"- private_key_visible: `{str(latest.get('private_key_visible') is True).lower()}`",
        f"- wallet_context_visible: `{str(latest.get('wallet_context_visible') is True).lower()}`",
        f"- telegram_credentials_visible: `{str(latest.get('telegram_credentials_visible') is True).lower()}`",
        "",
        "## Blockers",
        "",
        *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
        "",
        "## Safe Next Commands",
        "",
        "- `python -m pm_bot.operator_runner.runtime_credential_visibility_diagnostic --market BTC --strategy tiny-momentum --dry-run`",
        "- `python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge --market BTC --strategy tiny-momentum --dry-run`",
        "- `python -m pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet --market BTC --strategy tiny-momentum --dry-run`",
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"`{path}`" for path in paths.values()),
    ]
    return "\n".join(lines).rstrip() + "\n"


def validate_runtime_credential_visibility_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(value.get("status"))

    if value.get("contract_version") != RUNTIME_CREDENTIAL_VISIBILITY_RESULT_CONTRACT:
        errors.append(f"contract_version must be {RUNTIME_CREDENTIAL_VISIBILITY_RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")
        statuses.append("task_id_mismatch")
    if status not in VALID_STATUSES:
        errors.append("status must be a recognized 077C runtime credential visibility status")
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
        if key in {"raw_value", "value", "secret", "private_key", "api_secret", "passphrase", "telegram_token"}:
            errors.append(f"{path}.{key} must not be emitted")
            statuses.append("forbidden_raw_value_field_detected")

    valid = not errors
    return {
        "contract_version": RUNTIME_CREDENTIAL_VISIBILITY_VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (
            ["runtime_credential_visibility_result_valid"]
            if valid
            else ["runtime_credential_visibility_result_blocked"]
        ),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **runtime_credential_visibility_safety_flags(),
    }


def runtime_credential_visibility_safety_flags() -> dict[str, Any]:
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
        "telegram_messages_read": False,
        "telegram_secret_collection_added": False,
        "raw_values_emitted": False,
        "raw_secret_values_emitted": False,
        "private_key_raw_value_emitted": False,
        "api_secret_raw_value_emitted": False,
        "passphrase_raw_value_emitted": False,
        "telegram_token_raw_value_emitted": False,
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
            "runtime credential visibility diagnostic is redacted/no-live/no-submit; unsupported "
            "live/auth/wallet/sign/order/secret-dump flag(s): "
            + ", ".join(requested)
        )


def _env_var_status(spec: EnvVarSpec, environ: Mapping[str, str]) -> dict[str, Any]:
    raw = environ.get(spec.env_var_name)
    text = "" if raw is None else str(raw)
    present = bool(text.strip())
    length = len(text) if present else 0
    fingerprint = _redacted_fingerprint(spec.env_var_name, text) if present else ""
    row = {
        "contract_version": "pmbot_runtime_credential_visibility_077c_env_var_status.v1",
        "task_id": TASK_ID,
        "env_var_name": spec.env_var_name,
        "group": spec.group,
        "required_for_prompt": spec.required_for_prompt is True,
        "required_for_runtime_status": spec.required_for_runtime_status is True,
        "runtime_alias_for": spec.runtime_alias_for,
        "present": present,
        "length": length,
        "redacted_fingerprint_sha256_12": fingerprint,
        "redaction_status": "present_redacted" if present else "missing",
        "raw_value_emitted": False,
        "safe_for_artifacts": True,
        "parsed_item_count": _operator_id_count(text) if "ALLOWED_OPERATOR_IDS" in spec.env_var_name and present else 0,
    }
    return row


def _redacted_fingerprint(env_var_name: str, value: str) -> str:
    payload = f"pmbot-077c\0{env_var_name}\0{len(value)}\0{value}".encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:12]


def _operator_id_count(value: str) -> int:
    return len([item for item in re.split(r"[,;\s]+", value.strip()) if item])


def _build_group_summary(rows_by_name: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    def present(name: str) -> bool:
        return dict(rows_by_name.get(name, {})).get("present") is True

    requested_rows = [dict(rows_by_name[name]) for name in REQUESTED_ENV_VAR_NAMES if name in rows_by_name]
    alias_rows = [dict(rows_by_name[name]) for name in TELEGRAM_RUNTIME_ALIAS_ENV_VAR_NAMES if name in rows_by_name]
    l2_missing = [name for name in POLYMARKET_L2_ENV_VAR_NAMES if not present(name)]
    wallet_missing = [name for name in WALLET_ENV_VAR_NAMES if not present(name)]
    prompt_telegram_missing = [
        name
        for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_OPERATOR_IDS")
        if not present(name)
    ]
    runtime_telegram_missing = [
        name
        for name in ("PMBOT_TELEGRAM_BOT_TOKEN", "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS")
        if not present(name)
    ]
    prompt_telegram_visible = not prompt_telegram_missing
    runtime_telegram_visible = not runtime_telegram_missing
    telegram_credentials_visible = prompt_telegram_visible or runtime_telegram_visible
    return {
        "requested_env_var_count": len(REQUESTED_ENV_VAR_NAMES),
        "requested_present_count": len([row for row in requested_rows if row.get("present") is True]),
        "runtime_alias_env_var_count": len(TELEGRAM_RUNTIME_ALIAS_ENV_VAR_NAMES),
        "runtime_alias_present_count": len([row for row in alias_rows if row.get("present") is True]),
        "polymarket_l2_visible": not l2_missing,
        "polymarket_l2_missing_env_vars": l2_missing,
        "private_key_visible": present("POLYMARKET_PRIVATE_KEY"),
        "private_key_missing_env_vars": [] if present("POLYMARKET_PRIVATE_KEY") else ["POLYMARKET_PRIVATE_KEY"],
        "wallet_context_visible": not wallet_missing,
        "wallet_context_missing_env_vars": wallet_missing,
        "telegram_prompt_alias_visible": prompt_telegram_visible,
        "telegram_prompt_alias_missing_env_vars": prompt_telegram_missing,
        "telegram_runtime_alias_visible": runtime_telegram_visible,
        "telegram_runtime_alias_missing_env_vars": runtime_telegram_missing,
        "telegram_credentials_visible": telegram_credentials_visible,
    }


def _status_for_group_summary(summary: Mapping[str, Any]) -> str:
    if summary.get("private_key_visible") is not True:
        return STATUS_BLOCKED_MISSING_PRIVATE_KEY
    if summary.get("polymarket_l2_visible") is not True:
        return STATUS_BLOCKED_MISSING_POLYMARKET_L2_CREDENTIALS
    if summary.get("wallet_context_visible") is not True:
        return STATUS_BLOCKED_MISSING_WALLET_ADDRESS
    if summary.get("telegram_credentials_visible") is not True:
        return STATUS_BLOCKED_MISSING_TELEGRAM_CREDENTIALS
    return STATUS_RUNTIME_CREDENTIALS_VISIBLE


def _build_latest_status(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    group_summary: Mapping[str, Any],
    blockers: Sequence[Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": RUNTIME_CREDENTIAL_VISIBILITY_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "requested_env_var_count": int(group_summary.get("requested_env_var_count", 0) or 0),
        "requested_present_count": int(group_summary.get("requested_present_count", 0) or 0),
        "runtime_alias_present_count": int(group_summary.get("runtime_alias_present_count", 0) or 0),
        "polymarket_l2_visible": group_summary.get("polymarket_l2_visible") is True,
        "private_key_visible": group_summary.get("private_key_visible") is True,
        "wallet_context_visible": group_summary.get("wallet_context_visible") is True,
        "telegram_credentials_visible": group_summary.get("telegram_credentials_visible") is True,
        "telegram_runtime_alias_visible": group_summary.get("telegram_runtime_alias_visible") is True,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "operator_summary": _operator_summary(status=status, group_summary=group_summary),
        "generated_at": generated_at,
    }
    value.update(runtime_credential_visibility_safety_flags())
    return value


def _build_blockers(
    *,
    status: str,
    group_summary: Mapping[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if group_summary.get("private_key_visible") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_MISSING_PRIVATE_KEY,
                "signer_env_visibility",
                "POLYMARKET_PRIVATE_KEY is missing in this runtime process context.",
                group_summary.get("private_key_missing_env_vars", []),
                generated_at=generated_at,
            )
        )
    if group_summary.get("polymarket_l2_visible") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_MISSING_POLYMARKET_L2_CREDENTIALS,
                "polymarket_l2_env_visibility",
                "One or more Polymarket L2 credential variables are missing in this runtime process context.",
                group_summary.get("polymarket_l2_missing_env_vars", []),
                generated_at=generated_at,
            )
        )
    if group_summary.get("wallet_context_visible") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_MISSING_WALLET_ADDRESS,
                "wallet_env_visibility",
                "Wallet address, signature type, or funder address context is missing in this runtime process context.",
                group_summary.get("wallet_context_missing_env_vars", []),
                generated_at=generated_at,
            )
        )
    if group_summary.get("telegram_credentials_visible") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_MISSING_TELEGRAM_CREDENTIALS,
                "telegram_env_visibility",
                "Telegram credential variables are missing for both prompt aliases and repo runtime aliases.",
                [
                    *group_summary.get("telegram_prompt_alias_missing_env_vars", []),
                    *group_summary.get("telegram_runtime_alias_missing_env_vars", []),
                ],
                generated_at=generated_at,
            )
        )
    blockers.append(
        _blocker(
            "live_execution_still_blocked",
            "live_execution",
            "This diagnostic only reports redacted runtime visibility metadata and cannot enable live execution.",
            (),
            generated_at=generated_at,
            severity="info",
        )
    )
    return blockers


def _blocker(
    blocker_id: str,
    category: str,
    reason: str,
    missing_env_vars: Sequence[Any],
    *,
    generated_at: str,
    severity: str = "critical",
) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_runtime_credential_visibility_077c_blocker.v1",
        "task_id": TASK_ID,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "missing_env_vars": [clean_text(item) for item in missing_env_vars if clean_text(item)],
        "severity": clean_text(severity) or "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
        "allowed_for_live": False,
        "generated_at": generated_at,
    }
    value.update(runtime_credential_visibility_safety_flags())
    return value


def _operator_summary(*, status: str, group_summary: Mapping[str, Any]) -> str:
    if status == STATUS_RUNTIME_CREDENTIALS_VISIBLE:
        return (
            "All blocking runtime credential groups are visible in this process. This is diagnostic evidence only; "
            "live execution, signing by default, submit, and cancel remain blocked."
        )
    if status == STATUS_BLOCKED_MISSING_PRIVATE_KEY:
        return "This process cannot see POLYMARKET_PRIVATE_KEY, so signer diagnostics will fail closed."
    if status == STATUS_BLOCKED_MISSING_POLYMARKET_L2_CREDENTIALS:
        missing = ", ".join(group_summary.get("polymarket_l2_missing_env_vars", []))
        return f"This process cannot see all Polymarket L2 credentials. Missing: {missing}."
    if status == STATUS_BLOCKED_MISSING_WALLET_ADDRESS:
        missing = ", ".join(group_summary.get("wallet_context_missing_env_vars", []))
        return f"This process cannot see all wallet context variables. Missing: {missing}."
    return "This process cannot see Telegram credential variables for the operator runtime."


def _render_env_row(row: Mapping[str, Any]) -> str:
    return (
        f"{clean_text(row.get('env_var_name'))}: "
        f"present={str(row.get('present') is True).lower()} "
        f"length={int(row.get('length', 0) or 0)} "
        f"fingerprint={clean_text(row.get('redacted_fingerprint_sha256_12')) or 'missing'}"
    )


def _missing_names(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    return [clean_text(row.get("env_var_name")) for row in rows if row.get("present") is not True]


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
