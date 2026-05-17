from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from pm_bot.trading_core.artifact_resolution import DEFAULT_ARTIFACT_ROOT, resolve_artifact_root
from pm_bot.trading_core.funder_wallet_context_077g import run_funder_wallet_context_diagnostic
from pm_bot.trading_core.live_account_readonly_state_probe import (
    LiveAccountSdkBinding,
    load_polymarket_clob_sdk,
)
from pm_bot.trading_core.runtime_credential_visibility_077c import (
    run_runtime_credential_visibility_diagnostic,
)
from pm_bot.trading_core.schemas import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    normalize_path,
    write_json,
    write_text,
)

TASK_ID = "ORCH-PMBOT-RUNTIME-078G-LOCAL-ENVIRONMENT-SELF-TEST-BUNDLE-NO-LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"

MODE = "local environment self-test bundle / no-live / no-submit"
EXECUTION_MODE = "local_environment_self_test_bundle_078g"

RESULT_CONTRACT = "pmbot_local_environment_self_test_078g_result.v1"
LATEST_STATUS_CONTRACT = "pmbot_latest_local_environment_self_test_078g_status.v1"
CHECKS_CONTRACT = "pmbot_local_environment_self_test_078g_checks.v1"
BLOCKERS_CONTRACT = "pmbot_local_environment_self_test_078g_blockers.v1"
VALIDATION_CONTRACT = "pmbot_local_environment_self_test_078g_validation.v1"

STATUS_READY = "local_environment_ready_for_next_dry_run"
STATUS_BLOCKED_MISSING_FUNDER_ADDRESS = "blocked_missing_funder_address"
STATUS_BLOCKED_SDK_UNAVAILABLE = "blocked_sdk_unavailable"
STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK = "blocked_signer_diagnostic_not_ok"
STATUS_BLOCKED_PAYLOAD_READINESS_NOT_OK = "blocked_payload_readiness_not_ok"
STATUS_BLOCKED_TELEGRAM_RUNTIME_NOT_READY = "blocked_telegram_runtime_not_ready"

VALID_STATUSES = {
    STATUS_READY,
    STATUS_BLOCKED_MISSING_FUNDER_ADDRESS,
    STATUS_BLOCKED_SDK_UNAVAILABLE,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_PAYLOAD_READINESS_NOT_OK,
    STATUS_BLOCKED_TELEGRAM_RUNTIME_NOT_READY,
}

ARTIFACT_DIR_NAME = "local_environment_self_test_078g"
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME

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
    "--private-key",
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
    "--sign",
    "--signing",
    "--submit",
    "--cancel",
    "--approve-live",
    "--order",
    "--order-payload",
    "--post",
    "--put",
    "--patch",
    "--delete",
    "--browser",
    "--loop",
    "--daemon",
    "--scheduler",
    "--network-check",
    "--allow-private-key-diagnostic",
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
    "wallet_connection_ui_added",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "trading_write_call_performed",
    "network_write_performed",
    "network_post_performed",
    "network_put_performed",
    "network_patch_performed",
    "network_delete_performed",
    "full_signed_payload_output",
    "full_signed_payload_emitted",
    "raw_signed_payload_emitted",
    "raw_secret_values_emitted",
    "raw_values_emitted",
    "secrets_printed",
    "secrets_persisted",
    "wallet_files_read",
    "browser_profiles_read",
    "credential_stores_read",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

READY_ACCOUNT_READONLY_STATUSES = {
    "account_state_probe_succeeded_live_blocked",
    "account_readonly_probe_ok",
}
READY_LOCAL_REAL_CHECK_STATUSES = {
    "local_real_check_bundle_completed_reported_live_blocked",
    "local_real_check_bundle_completed_with_blockers_live_blocked",
}
READY_SELECTED_CANDIDATE_STATUS = "selected_candidate_artifact_recorded"
READY_SELECTED_TOKEN_STATUS = "selected_token_verified_for_payload_dry_run"
READY_SIGNER_STATUS = "signer_diagnostic_evidence_ok_for_payload_dry_run"
READY_PAYLOAD_STATUS = "payload_dry_run_ready_for_operator_review"
READY_FIRST_SUPERVISED_STATUS = "ready_for_separate_live_authorization_packet"

CheckBuilder = Callable[..., dict[str, Any]]
TelegramSmokeBuilder = Callable[..., Mapping[str, Any]]


def local_environment_self_test_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "local_environment_self_test_078g_result.json",
        "latest_status": root / "latest_local_environment_self_test_078g_status.json",
        "checks": root / "local_environment_self_test_078g_checks.json",
        "blockers": root / "local_environment_self_test_078g_blockers.json",
        "operator_md": root / "local_environment_self_test_078g_operator_summary.md",
        "telegram_smoke": root / "telegram_runtime_smoke_078g.json",
    }


def run_local_environment_self_test_bundle(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    sdk_loader: Callable[[], LiveAccountSdkBinding] | None = None,
    telegram_smoke_builder: TelegramSmokeBuilder | None = None,
    telegram_dependency_checker: Callable[[], Mapping[str, Any]] | None = None,
    telegram_runtime_import_checker: Callable[[], Mapping[str, Any]] | None = None,
    generated_at: str = GENERATED_AT,
    head_before: str = "",
    head_after: str = "",
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("local environment self-test bundle requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    active_environ = os.environ if environ is None else environ
    source_root = resolve_artifact_root(artifact_root, environ=active_environ)
    paths = local_environment_self_test_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    subdirs = _subcheck_dirs(paths["root"])

    runtime_result = run_runtime_credential_visibility_diagnostic(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        artifact_dir=subdirs["runtime_credential_visibility_077c"],
        environ=active_environ,
        generated_at=generated_at,
        head_before=head_before,
        head_after=head_after,
    )
    funder_result = run_funder_wallet_context_diagnostic(
        market=market_symbol,
        strategy=strategy_name,
        dry_run=True,
        artifact_dir=subdirs["funder_wallet_context_077g"],
        environ=active_environ,
        generated_at=generated_at,
        head_before=head_before,
        head_after=head_after,
    )
    clob_summary = _build_clob_sdk_account_readonly_summary(
        source_root=source_root,
        sdk_loader=sdk_loader,
        generated_at=generated_at,
    )
    local_real_check_summary = _summarize_existing_status(
        check_id="local_real_check_bundle",
        source_root=source_root,
        candidates=(
            Path("local_real_check_bundle_072c/latest_local_real_check_bundle_status_072c.json"),
            Path("local_real_check_bundle_072c/local_real_check_bundle_072c_result.json"),
        ),
        ready_statuses=READY_LOCAL_REAL_CHECK_STATUSES,
        generated_at=generated_at,
    )
    selected_candidate_summary = _summarize_existing_status(
        check_id="selected_candidate_artifact",
        source_root=source_root,
        candidates=(
            Path("selected_candidate_artifact_075d/latest_selected_candidate_artifact_075d.json"),
            Path("selected_candidate_artifact_075d/selected_candidate_artifact_075d.json"),
            Path("selected_candidate_artifact_075d/selected_candidate_artifact_075d_result.json"),
        ),
        ready_statuses={READY_SELECTED_CANDIDATE_STATUS},
        generated_at=generated_at,
    )
    selected_token_summary = _summarize_existing_status(
        check_id="selected_token_verification",
        source_root=source_root,
        candidates=(
            Path("selected_token_verification_bridge_076a/latest_selected_token_verification_076a_status.json"),
            Path("selected_token_verification_bridge_076a/selected_token_verification_076a_result.json"),
            Path("selected_token_verification_bridge_076a/selected_token_verification_076a_evidence.json"),
        ),
        ready_statuses={READY_SELECTED_TOKEN_STATUS},
        generated_at=generated_at,
    )
    signer_summary = _summarize_existing_status(
        check_id="signer_diagnostic_evidence",
        source_root=source_root,
        candidates=(
            Path("signer_diagnostic_evidence_bridge_076c/latest_signer_diagnostic_evidence_076c_status.json"),
            Path("signer_diagnostic_evidence_bridge_076c/signer_diagnostic_evidence_076c_result.json"),
        ),
        ready_statuses={READY_SIGNER_STATUS},
        generated_at=generated_at,
    )
    payload_summary = _summarize_existing_status(
        check_id="payload_dry_run_readiness",
        source_root=source_root,
        candidates=(
            Path("payload_dry_run_readiness_076d/latest_payload_dry_run_readiness_076d_status.json"),
            Path("payload_dry_run_readiness_076d/payload_dry_run_readiness_076d_result.json"),
        ),
        ready_statuses={READY_PAYLOAD_STATUS},
        generated_at=generated_at,
    )
    first_supervised_summary = _summarize_existing_status(
        check_id="first_supervised_tiny_order_readiness",
        source_root=source_root,
        candidates=(
            Path("first_supervised_tiny_order_readiness_077a/latest_first_supervised_tiny_order_readiness_077a_status.json"),
            Path("first_supervised_tiny_order_readiness_077a/first_supervised_tiny_order_readiness_077a_result.json"),
        ),
        ready_statuses={READY_FIRST_SUPERVISED_STATUS},
        generated_at=generated_at,
    )
    telegram_report = _build_telegram_smoke_report(
        env=active_environ,
        builder=telegram_smoke_builder,
        dependency_checker=telegram_dependency_checker,
        runtime_import_checker=telegram_runtime_import_checker,
        generated_at=generated_at,
    )
    write_json(paths["telegram_smoke"], telegram_report)

    checks = _build_checks(
        market=market_symbol,
        strategy=strategy_name,
        runtime_result=runtime_result,
        funder_result=funder_result,
        clob_summary=clob_summary,
        local_real_check_summary=local_real_check_summary,
        selected_candidate_summary=selected_candidate_summary,
        selected_token_summary=selected_token_summary,
        signer_summary=signer_summary,
        payload_summary=payload_summary,
        first_supervised_summary=first_supervised_summary,
        telegram_report=telegram_report,
        telegram_report_path=paths["telegram_smoke"],
        generated_at=generated_at,
    )
    blockers = _build_blockers(checks, generated_at=generated_at)
    status = _status_from_checks(checks)
    passed_count = sum(1 for check in checks if check.get("passed") is True)
    top_blockers = blockers[:5]
    next_commands = _dedupe(
        [clean_text(blocker.get("next_safe_command")) for blocker in top_blockers]
        + _baseline_safe_commands(market_symbol, strategy_name)
    )
    latest_status = _build_latest_status(
        status=status,
        market=market_symbol,
        strategy=strategy_name,
        checks=checks,
        blockers=blockers,
        next_commands=next_commands,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    checks_artifact = _build_checks_artifact(
        status=status,
        checks=checks,
        generated_at=generated_at,
    )
    blockers_artifact = _build_blockers_artifact(
        status=status,
        blockers=blockers,
        top_blockers=top_blockers,
        generated_at=generated_at,
    )
    result: dict[str, Any] = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "passed_count": passed_count,
        "check_count": len(checks),
        "blocker_count": len(blockers),
        "top_blockers": top_blockers,
        "exact_next_safe_commands": next_commands,
        "checks": checks,
        "latest_status": latest_status,
        "checks_artifact": checks_artifact,
        "blockers_artifact": blockers_artifact,
        "artifact_paths": path_refs,
        "input_artifact_root": normalize_path(source_root),
        "sub_artifact_dirs": {key: normalize_path(path) for key, path in subdirs.items()},
        "operator_summary": _operator_summary(status, passed_count, len(checks), len(blockers)),
        "head_before": clean_text(head_before),
        "head_after": clean_text(head_after),
        "generated_at": generated_at,
        **local_environment_self_test_safety_flags(),
    }
    result["validation"] = validate_local_environment_self_test_result(result)

    write_json(paths["checks"], checks_artifact)
    write_json(paths["blockers"], blockers_artifact)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_local_environment_self_test_markdown(result))
    return result


def render_local_environment_self_test_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    blockers = [dict(row) for row in value.get("top_blockers", []) if isinstance(row, Mapping)]
    commands = [clean_text(item) for item in value.get("exact_next_safe_commands", []) if clean_text(item)]
    lines = [
        "Local environment self-test bundle 078G completed.",
        f"Status: {clean_text(value.get('status'))}",
        f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
        f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
        f"Passed checks: {int(value.get('passed_count', 0) or 0)}/{int(value.get('check_count', 0) or 0)}",
        f"Blockers: {int(value.get('blocker_count', 0) or 0)}",
        "No live trading: true",
        "Order submission: blocked",
        "Order cancellation: blocked",
        "Signing by default: false",
        "Signer instantiated by default: false",
        "Wallet UI: not added",
        "Raw secrets emitted: false",
        "Top blockers:",
        *bullet_lines(
            f"{row.get('check_id')}: {row.get('status')} - {row.get('reason')}" for row in blockers
        ),
        "Exact next safe commands:",
        *bullet_lines(f"`{command}`" for command in commands),
        "Artifacts:",
        *bullet_lines(f"{key}: {path}" for key, path in dict(value.get("artifact_paths", {})).items()),
    ]
    return "\n".join(lines)


def render_local_environment_self_test_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    checks = [dict(row) for row in value.get("checks", []) if isinstance(row, Mapping)]
    blockers = [dict(row) for row in value.get("top_blockers", []) if isinstance(row, Mapping)]
    commands = [clean_text(item) for item in value.get("exact_next_safe_commands", []) if clean_text(item)]
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Local Environment Self-Test Bundle 078G",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        f"- Passed checks: `{value.get('passed_count')}/{value.get('check_count')}`",
        f"- Blockers: `{value.get('blocker_count')}`",
        "- Allowed for live: `false`",
        "- Order submission: `blocked`",
        "- Order cancellation: `blocked`",
        "- Signing by default: `false`",
        "- Signer instantiated by default: `false`",
        "- Raw secret output: `false`",
        "",
        "## Checks",
        "",
        *bullet_lines(
            f"`{row.get('check_id')}` status=`{row.get('status')}` passed=`{str(row.get('passed') is True).lower()}` artifact=`{row.get('artifact_path') or 'missing'}`"
            for row in checks
        ),
        "",
        "## Top Blockers",
        "",
        *bullet_lines(
            f"`{row.get('check_id')}` `{row.get('status')}` - {row.get('reason')}" for row in blockers
        ),
        "",
        "## Exact Next Safe Commands",
        "",
        *bullet_lines(f"`{command}`" for command in commands),
        "",
        "## Safety",
        "",
        "- this bundle does not submit or cancel orders",
        "- it does not sign by default or instantiate a signer",
        "- it does not add wallet UI, browser automation, daemon, scheduler, or background worker behavior",
        "- it emits status summaries and artifact paths only; raw secrets are not emitted",
        "- Telegram smoke is local-only by default and does not request a network check",
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"`{path}`" for path in paths.values()),
    ]
    return "\n".join(lines).rstrip() + "\n"


def validate_local_environment_self_test_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []
    status = clean_text(value.get("status"))

    if value.get("contract_version") != RESULT_CONTRACT:
        errors.append("contract_version mismatch")
        statuses.append("invalid_contract")
    if value.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")
        statuses.append("task_id_mismatch")
    if status not in VALID_STATUSES:
        errors.append("status is not a recognized 078G status")
        statuses.append("invalid_status")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if value.get("passed_count") != sum(1 for row in value.get("checks", []) if isinstance(row, Mapping) and row.get("passed") is True):
        errors.append("passed_count must match passed checks")
        statuses.append("passed_count_mismatch")
    if value.get("blocker_count") != len(value.get("top_blockers", [])) and value.get("blocker_count", 0) < len(value.get("top_blockers", [])):
        errors.append("blocker_count must be at least top_blockers length")
        statuses.append("blocker_count_mismatch")

    for path, key, nested in _walk_fields(value):
        if key in REQUIRED_FALSE_FLAGS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_false_flag_detected")
        if key == "resolved_blocker_count" and nested != 0:
            errors.append(f"{path}.{key} must be 0")
            statuses.append("resolved_blocker_detected")
        if key in {"raw_value", "private_key", "api_secret", "passphrase", "telegram_token", "signed_payload"} and nested:
            errors.append(f"{path}.{key} must not be emitted")
            statuses.append("raw_secret_field_detected")

    valid = not errors
    return {
        "contract_version": VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (["local_environment_self_test_078g_valid"] if valid else ["local_environment_self_test_078g_blocked"]),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **local_environment_self_test_safety_flags(),
    }


def local_environment_self_test_safety_flags() -> dict[str, Any]:
    return {
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "paper_only": True,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "local_status_bundle_only": True,
        "safe_summary_only": True,
        "non_executable": True,
        "allowed_for_live": False,
        "trading_requested": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "order_cancel_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
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
        "trading_write_call_performed": False,
        "network_write_performed": False,
        "network_post_performed": False,
        "network_put_performed": False,
        "network_patch_performed": False,
        "network_delete_performed": False,
        "full_signed_payload_output": False,
        "full_signed_payload_emitted": False,
        "raw_signed_payload_emitted": False,
        "raw_secret_values_emitted": False,
        "raw_values_emitted": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "wallet_files_read": False,
        "browser_profiles_read": False,
        "credential_stores_read": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "telegram_network_check_requested": False,
        "polymarket_trading_api_call_performed": False,
        "resolved_blocker_count": 0,
    }


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "local environment self-test bundle is no-live/no-submit/no-cancel/no-sign-by-default; "
            "unsupported live/auth/wallet/sign/order/network/browser/loop flag(s): "
            + ", ".join(requested)
        )


def _subcheck_dirs(root: Path) -> dict[str, Path]:
    return {
        "runtime_credential_visibility_077c": root / "runtime_credential_visibility_077c",
        "funder_wallet_context_077g": root / "funder_wallet_context_077g",
        "selected_token_verification_bridge_076a": root / "selected_token_verification_bridge_076a",
        "signer_diagnostic_evidence_bridge_076c": root / "signer_diagnostic_evidence_bridge_076c",
        "payload_dry_run_readiness_076d": root / "payload_dry_run_readiness_076d",
        "first_supervised_tiny_order_readiness_077a": root / "first_supervised_tiny_order_readiness_077a",
    }


def _build_clob_sdk_account_readonly_summary(
    *,
    source_root: Path,
    sdk_loader: Callable[[], LiveAccountSdkBinding] | None,
    generated_at: str,
) -> dict[str, Any]:
    try:
        binding = (sdk_loader or load_polymarket_clob_sdk)()
        sdk_error = ""
    except Exception as exc:  # pragma: no cover - defensive import-side-effect guard
        binding = LiveAccountSdkBinding(
            status="dependency_missing",
            attempted_modules=(),
            error_type=type(exc).__name__,
            error_message_sanitized="sdk_detection_failed",
        )
        sdk_error = type(exc).__name__
    sdk_available = binding.status == "available"
    account_source = _load_first_existing_json(
        source_root,
        (
            Path("live_account_readonly_state_probe_070c/latest_live_account_readonly_state_status_070c.json"),
            Path("live_account_readonly_state_probe_070c/live_account_readonly_state_probe_070c_result.json"),
        ),
    )
    account_status = clean_text(account_source.get("status")) or "account_readonly_probe_missing"
    account_ready = account_status in READY_ACCOUNT_READONLY_STATUSES or account_source.get("account_state_probe_performed") is True
    status = account_status
    if not sdk_available and not account_ready:
        status = STATUS_BLOCKED_SDK_UNAVAILABLE
    return {
        "check_id": "clob_sdk_account_readonly_probe",
        "status": status,
        "sdk_detection_status": "available" if sdk_available else STATUS_BLOCKED_SDK_UNAVAILABLE,
        "sdk_available": sdk_available,
        "selected_sdk_module": clean_text(binding.module_name),
        "attempted_sdk_modules": [clean_text(item) for item in binding.attempted_modules],
        "sdk_error_type": clean_text(sdk_error or binding.error_type),
        "account_readonly_status": account_status,
        "account_readonly_probe_artifact_available": account_source.get("available") is True,
        "account_readonly_probe_performed": account_source.get("account_state_probe_performed") is True,
        "account_readonly_probe_ready": account_ready,
        "artifact_path": clean_text(account_source.get("path")),
        "latest_status_path": clean_text(account_source.get("path")),
        "passed": sdk_available and account_ready,
        "generated_at": generated_at,
        **local_environment_self_test_safety_flags(),
    }


def _build_telegram_smoke_report(
    *,
    env: Mapping[str, str],
    builder: TelegramSmokeBuilder | None,
    dependency_checker: Callable[[], Mapping[str, Any]] | None,
    runtime_import_checker: Callable[[], Mapping[str, Any]] | None,
    generated_at: str,
) -> dict[str, Any]:
    if builder is not None:
        report = dict(
            builder(
                env=env,
                network_check=False,
                dependency_checker=dependency_checker,
                runtime_import_checker=runtime_import_checker,
                generated_at=generated_at,
            )
        )
    else:
        from pm_bot.operator_runner.telegram_runtime_smoke import build_telegram_runtime_smoke_report

        report = build_telegram_runtime_smoke_report(
            env=env,
            network_check=False,
            dependency_checker=dependency_checker,
            runtime_import_checker=runtime_import_checker,
            generated_at=generated_at,
        )
    report["network_check_requested"] = False
    report["no_network_by_default"] = True
    report["raw_telegram_bot_token_exposed"] = False
    report["raw_operator_user_ids_exposed"] = False
    report.update(local_environment_self_test_safety_flags())
    return report


def _build_checks(
    *,
    market: str,
    strategy: str,
    runtime_result: Mapping[str, Any],
    funder_result: Mapping[str, Any],
    clob_summary: Mapping[str, Any],
    local_real_check_summary: Mapping[str, Any],
    selected_candidate_summary: Mapping[str, Any],
    selected_token_summary: Mapping[str, Any],
    signer_summary: Mapping[str, Any],
    payload_summary: Mapping[str, Any],
    first_supervised_summary: Mapping[str, Any],
    telegram_report: Mapping[str, Any],
    telegram_report_path: Path,
    generated_at: str,
) -> list[dict[str, Any]]:
    runtime_latest = dict(runtime_result.get("latest_status", {}))
    funder_latest = dict(funder_result.get("latest_status", {}))
    telegram_env = dict(telegram_report.get("env_status", {}))
    telegram_passed = telegram_report.get("ready_to_start_runtime") is True and telegram_report.get("review_only_safety_flags_ok") is True
    command_suffix = f"--market {market} --strategy {strategy} --dry-run"
    return [
        _check(
            check_id="runtime_credential_visibility",
            label="Runtime credential visibility",
            status=clean_text(runtime_result.get("status")),
            passed=runtime_result.get("status") == "runtime_credentials_visible",
            artifact_path=_path_from(runtime_latest, "artifact_path"),
            latest_status_path=_path_from(runtime_latest, "latest_status_path"),
            reason=_runtime_reason(runtime_latest),
            next_safe_command=f"python -m pm_bot.operator_runner.runtime_credential_visibility_diagnostic {command_suffix}",
            details={
                "polymarket_l2_visible": runtime_latest.get("polymarket_l2_visible") is True,
                "private_key_visible": runtime_latest.get("private_key_visible") is True,
                "wallet_context_visible": runtime_latest.get("wallet_context_visible") is True,
                "telegram_credentials_visible": runtime_latest.get("telegram_credentials_visible") is True,
            },
            generated_at=generated_at,
        ),
        _check(
            check_id="funder_wallet_context",
            label="Funder/wallet context",
            status=clean_text(funder_result.get("status")),
            passed=funder_latest.get("wallet_context_visible") is True,
            artifact_path=_path_from(funder_latest, "artifact_path"),
            latest_status_path=_path_from(funder_latest, "latest_status_path"),
            reason=_funder_reason(funder_latest),
            next_safe_command=f"python -m pm_bot.operator_runner.funder_wallet_context_diagnostic {command_suffix}",
            details={
                "wallet_address_present": funder_latest.get("wallet_address_present") is True,
                "funder_address_present": funder_latest.get("funder_address_present") is True,
                "signature_type_present": funder_latest.get("signature_type_present") is True,
                "funder_relationship_status": clean_text(funder_latest.get("funder_relationship_status")),
            },
            generated_at=generated_at,
        ),
        _check(
            check_id="clob_sdk_account_readonly_probe",
            label="CLOB SDK detection / account read-only probe",
            status=clean_text(clob_summary.get("status")),
            passed=clob_summary.get("passed") is True,
            artifact_path=clean_text(clob_summary.get("artifact_path")),
            latest_status_path=clean_text(clob_summary.get("latest_status_path")),
            reason=_clob_reason(clob_summary),
            next_safe_command=f"python -m pm_bot.operator_runner.live_account_readonly_state_probe {command_suffix}",
            details={
                "sdk_detection_status": clean_text(clob_summary.get("sdk_detection_status")),
                "sdk_available": clob_summary.get("sdk_available") is True,
                "selected_sdk_module": clean_text(clob_summary.get("selected_sdk_module")),
                "account_readonly_status": clean_text(clob_summary.get("account_readonly_status")),
                "account_readonly_probe_performed": clob_summary.get("account_readonly_probe_performed") is True,
            },
            generated_at=generated_at,
        ),
        _check_from_summary(
            check_id="local_real_check_bundle",
            label="Local real-check bundle",
            summary=local_real_check_summary,
            next_safe_command=f"python -m pm_bot.operator_runner.local_real_check_bundle {command_suffix}",
            generated_at=generated_at,
        ),
        _check_from_summary(
            check_id="selected_candidate_artifact",
            label="Selected candidate artifact",
            summary=selected_candidate_summary,
            next_safe_command=f"python -m pm_bot.operator_runner.selected_candidate_artifact {command_suffix} --candidate-index 0",
            generated_at=generated_at,
        ),
        _check_from_summary(
            check_id="selected_token_verification",
            label="Selected token verification",
            summary=selected_token_summary,
            next_safe_command=f"python -m pm_bot.operator_runner.selected_token_verification_bridge {command_suffix}",
            generated_at=generated_at,
        ),
        _check_from_summary(
            check_id="signer_diagnostic_evidence",
            label="Signer diagnostic evidence",
            summary=signer_summary,
            next_safe_command=f"python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge {command_suffix}",
            generated_at=generated_at,
        ),
        _check_from_summary(
            check_id="payload_dry_run_readiness",
            label="Payload dry-run readiness",
            summary=payload_summary,
            next_safe_command=f"python -m pm_bot.operator_runner.payload_dry_run_readiness_review {command_suffix}",
            generated_at=generated_at,
        ),
        _check_from_summary(
            check_id="first_supervised_tiny_order_readiness",
            label="First supervised tiny order readiness",
            summary=first_supervised_summary,
            next_safe_command=f"python -m pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet {command_suffix}",
            generated_at=generated_at,
        ),
        _check(
            check_id="telegram_runtime_smoke",
            label="Telegram runtime smoke",
            status="telegram_runtime_ready" if telegram_passed else STATUS_BLOCKED_TELEGRAM_RUNTIME_NOT_READY,
            passed=telegram_passed,
            artifact_path=normalize_path(telegram_report_path),
            latest_status_path=normalize_path(telegram_report_path),
            reason=_telegram_reason(telegram_report),
            next_safe_command="python -m pm_bot.operator_runner.telegram_runtime_smoke --json",
            details={
                "ready_to_start_runtime": telegram_report.get("ready_to_start_runtime") is True,
                "telegram_token_status": clean_text(telegram_env.get("telegram_token")),
                "allowed_operator_id_count": int(telegram_env.get("allowed_operator_id_count", 0) or 0),
                "dependency_status": clean_text(dict(telegram_report.get("dependency_check", {})).get("status")),
                "runtime_module_import_status": clean_text(dict(telegram_report.get("runtime_module_import", {})).get("status")),
                "network_check_requested": telegram_report.get("network_check_requested") is True,
            },
            generated_at=generated_at,
        ),
    ]


def _check_from_summary(
    *,
    check_id: str,
    label: str,
    summary: Mapping[str, Any],
    next_safe_command: str,
    generated_at: str,
) -> dict[str, Any]:
    return _check(
        check_id=check_id,
        label=label,
        status=clean_text(summary.get("status")),
        passed=summary.get("passed") is True,
        artifact_path=clean_text(summary.get("artifact_path")),
        latest_status_path=clean_text(summary.get("latest_status_path")),
        reason=clean_text(summary.get("reason")),
        next_safe_command=next_safe_command,
        details=dict(summary.get("details", {})),
        generated_at=generated_at,
    )


def _check(
    *,
    check_id: str,
    label: str,
    status: str,
    passed: bool,
    artifact_path: str,
    latest_status_path: str,
    reason: str,
    next_safe_command: str,
    details: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "check_id": clean_text(check_id),
        "label": clean_text(label),
        "status": clean_text(status) or "missing",
        "passed": passed is True,
        "blocker": passed is not True,
        "reason": clean_text(reason),
        "artifact_path": clean_text(artifact_path),
        "latest_status_path": clean_text(latest_status_path),
        "next_safe_command": clean_text(next_safe_command),
        "details": dict(details),
        "source_payload_embedded": False,
        "raw_secret_values_embedded": False,
        "generated_at": generated_at,
    }
    value.update(local_environment_self_test_safety_flags())
    return value


def _summarize_existing_status(
    *,
    check_id: str,
    source_root: Path,
    candidates: Sequence[Path],
    ready_statuses: set[str],
    generated_at: str,
) -> dict[str, Any]:
    payload = _load_first_existing_json(source_root, candidates)
    status = clean_text(payload.get("status")) or "missing"
    readiness_field_names = (
        "selected_candidate_artifact_recorded",
        "selected_by_operator",
        "selected_token_verified_for_payload_dry_run",
        "signer_diagnostic_evidence_ok_for_payload_dry_run",
        "payload_dry_run_ready",
        "first_supervised_tiny_order_ready_for_authorization",
    )
    readiness_fields = {
        name: payload.get(name) is True
        for name in readiness_field_names
        if name in payload
    }
    passed = payload.get("available") is True and (
        status in ready_statuses
        or any(readiness_fields.values())
        or payload.get("selected_by_operator") is True and status == READY_SELECTED_CANDIDATE_STATUS
    )
    return {
        "check_id": check_id,
        "status": status,
        "passed": passed,
        "artifact_path": clean_text(payload.get("path")),
        "latest_status_path": clean_text(payload.get("path")),
        "reason": "" if passed else f"{check_id} artifact status is {status}; success was not inferred.",
        "details": {
            "artifact_available": payload.get("available") is True,
            "contract_version": clean_text(payload.get("contract_version")),
            "source_status": status,
            **readiness_fields,
            "source_payload_embedded": False,
        },
        "generated_at": generated_at,
        **local_environment_self_test_safety_flags(),
    }


def _build_blockers(checks: Sequence[Mapping[str, Any]], *, generated_at: str) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for check in checks:
        if check.get("passed") is True:
            continue
        blocker_id = clean_text(check.get("status")) or clean_text(check.get("check_id"))
        reason = clean_text(check.get("reason")) or f"{clean_text(check.get('label'))} is not ready."
        value = {
            "contract_version": "pmbot_local_environment_self_test_078g_blocker.v1",
            "task_id": TASK_ID,
            "blocker_id": blocker_id,
            "check_id": clean_text(check.get("check_id")),
            "status": clean_text(check.get("status")),
            "reason": reason,
            "severity": "critical",
            "resolution_status": "unresolved",
            "resolved": False,
            "blocks_next_dry_run": True,
            "blocks_live_execution": True,
            "next_safe_command": clean_text(check.get("next_safe_command")),
            "generated_at": generated_at,
        }
        value.update(local_environment_self_test_safety_flags())
        blockers.append(value)
    return blockers


def _status_from_checks(checks: Sequence[Mapping[str, Any]]) -> str:
    by_id = {clean_text(check.get("check_id")): dict(check) for check in checks}
    funder = by_id.get("funder_wallet_context", {})
    funder_details = dict(funder.get("details", {}))
    clob = by_id.get("clob_sdk_account_readonly_probe", {})
    signer = by_id.get("signer_diagnostic_evidence", {})
    payload = by_id.get("payload_dry_run_readiness", {})
    first_supervised = by_id.get("first_supervised_tiny_order_readiness", {})
    telegram = by_id.get("telegram_runtime_smoke", {})

    if funder.get("passed") is not True and (
        funder_details.get("funder_address_present") is not True
        or funder_details.get("wallet_address_present") is not True
        or funder_details.get("signature_type_present") is not True
    ):
        return STATUS_BLOCKED_MISSING_FUNDER_ADDRESS
    if clob.get("passed") is not True:
        return STATUS_BLOCKED_SDK_UNAVAILABLE
    if signer.get("passed") is not True or first_supervised.get("status") == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK:
        return STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK
    if payload.get("passed") is not True or first_supervised.get("passed") is not True:
        return STATUS_BLOCKED_PAYLOAD_READINESS_NOT_OK
    for check in checks:
        if check.get("passed") is not True and clean_text(check.get("check_id")) != "telegram_runtime_smoke":
            return STATUS_BLOCKED_PAYLOAD_READINESS_NOT_OK
    if telegram.get("passed") is not True:
        return STATUS_BLOCKED_TELEGRAM_RUNTIME_NOT_READY
    return STATUS_READY


def _build_latest_status(
    *,
    status: str,
    market: str,
    strategy: str,
    checks: Sequence[Mapping[str, Any]],
    blockers: Sequence[Mapping[str, Any]],
    next_commands: Sequence[str],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    check_statuses = {clean_text(row.get("check_id")): clean_text(row.get("status")) for row in checks}
    value = {
        "contract_version": LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market,
        "market_symbol": market,
        "strategy": strategy,
        "strategy_name": strategy,
        "passed_count": sum(1 for check in checks if check.get("passed") is True),
        "check_count": len(checks),
        "blocker_count": len(blockers),
        "top_blockers": [dict(row) for row in blockers[:5]],
        "exact_next_safe_commands": list(next_commands),
        "check_statuses": check_statuses,
        "runtime_credential_visibility_status": check_statuses.get("runtime_credential_visibility", ""),
        "funder_wallet_context_status": check_statuses.get("funder_wallet_context", ""),
        "clob_sdk_account_readonly_probe_status": check_statuses.get("clob_sdk_account_readonly_probe", ""),
        "local_real_check_bundle_status": check_statuses.get("local_real_check_bundle", ""),
        "selected_candidate_artifact_status": check_statuses.get("selected_candidate_artifact", ""),
        "selected_token_verification_status": check_statuses.get("selected_token_verification", ""),
        "signer_diagnostic_evidence_status": check_statuses.get("signer_diagnostic_evidence", ""),
        "payload_dry_run_readiness_status": check_statuses.get("payload_dry_run_readiness", ""),
        "first_supervised_tiny_order_readiness_status": check_statuses.get("first_supervised_tiny_order_readiness", ""),
        "telegram_runtime_smoke_status": check_statuses.get("telegram_runtime_smoke", ""),
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "checks_path": clean_text(artifact_paths.get("checks")),
        "blockers_path": clean_text(artifact_paths.get("blockers")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "generated_at": generated_at,
    }
    value.update(local_environment_self_test_safety_flags())
    return value


def _build_checks_artifact(
    *,
    status: str,
    checks: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": CHECKS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "checks": [dict(row) for row in checks],
        "check_count": len(checks),
        "passed_count": sum(1 for check in checks if check.get("passed") is True),
        "generated_at": generated_at,
    }
    value.update(local_environment_self_test_safety_flags())
    return value


def _build_blockers_artifact(
    *,
    status: str,
    blockers: Sequence[Mapping[str, Any]],
    top_blockers: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "blockers": [dict(row) for row in blockers],
        "top_blockers": [dict(row) for row in top_blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "generated_at": generated_at,
    }
    value.update(local_environment_self_test_safety_flags())
    return value


def _load_first_existing_json(source_root: Path, candidates: Sequence[Path]) -> dict[str, Any]:
    for relative in candidates:
        path = source_root / relative
        if not path.exists() or not path.is_file():
            continue
        try:
            payload = load_json_object(path, label=f"078G source artifact {relative}")
        except Exception as exc:
            return {
                "available": True,
                "parsed": False,
                "path": normalize_path(path),
                "status": "unreadable",
                "contract_version": "",
                "errors": [type(exc).__name__],
            }
        payload["available"] = True
        payload["parsed"] = True
        payload["path"] = normalize_path(path)
        payload["contract_version"] = clean_text(payload.get("contract_version"))
        return payload
    first = candidates[0] if candidates else Path("missing")
    return {
        "available": False,
        "parsed": False,
        "path": normalize_path(source_root / first),
        "status": "missing",
        "contract_version": "",
        "errors": ["artifact_missing"],
    }


def _baseline_safe_commands(market: str, strategy: str) -> list[str]:
    suffix = f"--market {market} --strategy {strategy} --dry-run"
    return [
        f"python -m pm_bot.operator_runner.local_environment_self_test_bundle {suffix}",
        "python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run",
    ]


def _runtime_reason(latest: Mapping[str, Any]) -> str:
    missing: list[str] = []
    missing.extend(clean_text(item) for item in latest.get("polymarket_l2_missing_env_vars", []) if clean_text(item))
    missing.extend(clean_text(item) for item in latest.get("private_key_missing_env_vars", []) if clean_text(item))
    missing.extend(clean_text(item) for item in latest.get("wallet_context_missing_env_vars", []) if clean_text(item))
    missing.extend(clean_text(item) for item in latest.get("telegram_runtime_alias_missing_env_vars", []) if clean_text(item))
    return "" if not missing else "Missing runtime env visibility: " + ", ".join(_dedupe(missing))


def _funder_reason(latest: Mapping[str, Any]) -> str:
    missing: list[str] = []
    if latest.get("wallet_address_present") is not True:
        missing.append("POLYMARKET_WALLET_ADDRESS")
    if latest.get("funder_address_present") is not True:
        missing.append("POLYMARKET_FUNDER_ADDRESS")
    if latest.get("signature_type_present") is not True:
        missing.append("POLYMARKET_SIGNATURE_TYPE")
    return "" if not missing else "Missing funder/wallet context: " + ", ".join(missing)


def _clob_reason(summary: Mapping[str, Any]) -> str:
    if summary.get("sdk_available") is not True:
        return "No supported Polymarket CLOB SDK module is importable in this Python runtime."
    if summary.get("account_readonly_probe_ready") is not True:
        status = clean_text(summary.get("account_readonly_status")) or "missing"
        return f"Account read-only probe status is {status}; success was not inferred."
    return ""


def _telegram_reason(report: Mapping[str, Any]) -> str:
    if report.get("ready_to_start_runtime") is True and report.get("review_only_safety_flags_ok") is True:
        return ""
    errors = [clean_text(item) for item in report.get("config_errors", []) if clean_text(item)]
    dependency = clean_text(dict(report.get("dependency_check", {})).get("status"))
    runtime_import = clean_text(dict(report.get("runtime_module_import", {})).get("status"))
    parts = []
    if errors:
        parts.append("config errors: " + ", ".join(errors))
    if dependency != "installed":
        parts.append(f"python-telegram-bot={dependency or 'missing'}")
    if runtime_import != "ok":
        parts.append(f"runtime_import={runtime_import or 'failed'}")
    return "; ".join(parts) or "Telegram runtime smoke is not ready."


def _path_from(payload: Mapping[str, Any], key: str) -> str:
    return clean_text(payload.get(key))


def _operator_summary(status: str, passed_count: int, check_count: int, blocker_count: int) -> str:
    if status == STATUS_READY:
        return (
            f"Local environment self-test is ready for the next dry-run chain; {passed_count}/{check_count} "
            "checks passed. Live execution remains blocked."
        )
    return (
        f"Local environment self-test is blocked with status={status}; {passed_count}/{check_count} "
        f"checks passed and {blocker_count} blocker(s) remain. Resolve top blockers, then rerun the dry-run bundle."
    )


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


__all__ = [
    "DEFAULT_ARTIFACT_DIR",
    "TASK_ID",
    "fail_closed_for_forbidden_flags",
    "local_environment_self_test_artifact_paths",
    "local_environment_self_test_safety_flags",
    "render_local_environment_self_test_cli_summary",
    "render_local_environment_self_test_markdown",
    "run_local_environment_self_test_bundle",
    "validate_local_environment_self_test_result",
]
