from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    normalize_path,
    write_json,
    write_text,
)

TASK_ID = "ORCH-PMBOT-RUNTIME-078J-FINAL-BLOCKER-ACTION-PLANNER-NO-LIVE"

DEFAULT_MARKET = "BTC"
DEFAULT_STRATEGY = "tiny-momentum"
DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "final_blocker_action_planner_078j"

MODE = "final blocker action planner / local artifact reducer / no-live"
EXECUTION_MODE = "final_blocker_action_planner_078j"

ACTION_CATEGORY_USER_LOCAL_ENV = "user/local env"
ACTION_CATEGORY_DEPENDENCY_INSTALL = "dependency install"
ACTION_CATEGORY_POLYMARKET_ACCOUNT = "Polymarket account"
ACTION_CATEGORY_CODE_TASK = "code task"
ACTION_CATEGORIES = {
    ACTION_CATEGORY_USER_LOCAL_ENV,
    ACTION_CATEGORY_DEPENDENCY_INSTALL,
    ACTION_CATEGORY_POLYMARKET_ACCOUNT,
    ACTION_CATEGORY_CODE_TASK,
}

RESULT_CONTRACT = "pmbot_final_blocker_action_planner_078j_result.v1"
LATEST_STATUS_CONTRACT = "pmbot_latest_final_blocker_action_planner_078j_status.v1"
ACTIONS_CONTRACT = "pmbot_final_blocker_action_planner_078j_actions.v1"
ACTION_CONTRACT = "pmbot_final_blocker_action_planner_078j_action.v1"
SAFETY_CONTRACT = "pmbot_final_blocker_action_planner_078j_safety.v1"
VALIDATION_CONTRACT = "pmbot_final_blocker_action_planner_078j_validation.v1"

STATUS_BLOCKED_MISSING_RUNTIME_CREDENTIAL_VISIBILITY = "blocked_missing_runtime_credential_visibility_artifact"
STATUS_BLOCKED_RUNTIME_CREDENTIALS_NOT_VISIBLE = "blocked_runtime_credentials_not_visible"
STATUS_BLOCKED_MISSING_FUNDER_ADDRESS = "blocked_missing_funder_address"
STATUS_BLOCKED_MISSING_FUNDER_CONTEXT = "blocked_missing_funder_wallet_context_artifact"
STATUS_BLOCKED_MISSING_READONLY_ACCOUNT_PROBE = "blocked_missing_live_account_readonly_probe_artifact"
STATUS_BLOCKED_POLYMARKET_SDK_UNAVAILABLE = "blocked_polymarket_sdk_unavailable"
STATUS_BLOCKED_READONLY_ACCOUNT_PROBE_NOT_READY = "blocked_live_account_readonly_probe_not_ready"
STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK = "blocked_missing_local_real_check_bundle"
STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK = "blocked_signer_diagnostic_not_ok"
STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY = "blocked_payload_dry_run_not_ready"
STATUS_BLOCKED_RISK_ENGINE_NOT_READY = "blocked_risk_engine_v2_not_ready"
STATUS_BLOCKED_FINAL_REDUCER_NOT_CLEAR = "blocked_final_blocker_reducer_not_clear"
STATUS_BLOCKED_FIRST_SUPERVISED_PACKET_NOT_READY = "blocked_first_supervised_tiny_order_packet_not_ready"
STATUS_BLOCKED_UNSAFE_LIVE_FLAG_OBSERVED = "blocked_unsafe_live_flag_observed_in_artifacts"
STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION = "blocked_missing_explicit_live_authorization"

READY_RUNTIME_CREDENTIALS = "runtime_credentials_visible"
READY_ACCOUNT_READONLY = "account_state_probe_succeeded_live_blocked"
READY_PAYLOAD = "payload_dry_run_ready_for_operator_review"
READY_RISK = "passed_review_check_no_live"
READY_FINAL_REDUCER = "review_ready_no_live_authorization"
READY_FIRST_SUPERVISED_PACKET = "ready_for_separate_live_authorization_packet"

SOURCE_CANDIDATES: dict[str, tuple[Path, ...]] = {
    "runtime_credential_visibility_077c": (
        Path("runtime_credential_visibility_077c/latest_runtime_credential_visibility_077c_status.json"),
        Path("runtime_credential_visibility_077c/runtime_credential_visibility_077c_result.json"),
    ),
    "funder_wallet_context_077g": (
        Path("funder_wallet_context_077g/latest_funder_wallet_context_077g_status.json"),
        Path("funder_wallet_context_077g/funder_wallet_context_077g_result.json"),
    ),
    "live_account_readonly_state_probe_070c": (
        Path("live_account_readonly_state_probe_070c/latest_live_account_readonly_state_status_070c.json"),
        Path("live_account_readonly_state_probe_070c/live_account_readonly_state_probe_070c_result.json"),
    ),
    "local_real_check_bundle_072c": (
        Path("local_real_check_bundle_072c/latest_local_real_check_bundle_status_072c.json"),
        Path("local_real_check_bundle_072c/local_real_check_bundle_072c_result.json"),
    ),
    "payload_dry_run_readiness_076d": (
        Path("payload_dry_run_readiness_076d/latest_payload_dry_run_readiness_076d_status.json"),
        Path("payload_dry_run_readiness_076d/payload_dry_run_readiness_076d_result.json"),
    ),
    "first_supervised_tiny_order_readiness_077a": (
        Path(
            "first_supervised_tiny_order_readiness_077a/"
            "latest_first_supervised_tiny_order_readiness_077a_status.json"
        ),
        Path("first_supervised_tiny_order_readiness_077a/first_supervised_tiny_order_readiness_077a_result.json"),
    ),
    "risk_engine_v2_074d": (
        Path("risk_engine_v2_074d/latest_risk_engine_v2_074d_status.json"),
        Path("risk_engine_v2_074d/risk_engine_v2_074d_result.json"),
    ),
    "first_live_order_final_blocker_reducer_072d": (
        Path("first_live_order_final_blocker_reducer_072d/latest_first_live_order_final_blockers_072d.json"),
        Path("first_live_order_final_blocker_reducer_072d/first_live_order_final_blocker_reducer_072d_result.json"),
    ),
}

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
    "--record-approval",
    "--order",
    "--order-payload",
    "--private-key",
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
    "--env-dump",
    "--print-env",
    "--browser",
    "--loop",
    "--daemon",
    "--scheduler",
)

FORCED_FALSE_FIELDS = (
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
    "order_cancelled",
    "signing_enabled",
    "signing_attempted",
    "signing_by_default",
    "signer_instantiated",
    "signer_instantiation_attempted",
    "wallet_connection_attempted",
    "wallet_connection_ui_added",
    "wallet_signing_enabled",
    "wallet_signing_attempted",
    "wallet_connect_enabled",
    "authenticated_endpoint_enabled",
    "authenticated_request_performed",
    "full_signed_payload_output",
    "raw_values_emitted",
    "raw_secret_values_emitted",
    "private_key_raw_value_emitted",
    "api_secret_raw_value_emitted",
    "passphrase_raw_value_emitted",
    "full_signed_payload_emitted",
    "environment_modified",
    "dotenv_files_written",
    "wallet_files_read",
    "secret_files_read",
    "browser_automation_added",
    "scheduler_or_daemon_added",
    "background_worker_added",
    "autonomous_live_trading_added",
)

UNSAFE_TRUE_SOURCE_FIELDS = {
    *FORCED_FALSE_FIELDS,
    "live_ready",
    "submit_ready",
    "ready_for_submit",
    "order_payload_contract_executable",
    "signed_payload_generated",
    "signed_order_payload_generated",
    "wallet_connected",
    "real_order_submitted",
    "real_order_cancelled",
}

FORBIDDEN_RAW_KEYS = {
    "private_key",
    "seed_phrase",
    "mnemonic",
    "api_secret",
    "api_secret_value",
    "auth_token",
    "passphrase",
    "secret",
    "raw_secret",
    "raw_value",
    "signature",
    "signed_payload",
    "signed_order",
    "order_id",
    "client_order_id",
    "tx_hash",
    "transaction_hash",
    "fill",
    "fills",
    "balance",
    "balances",
    "position",
    "positions",
    "pnl",
}


def final_blocker_action_planner_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "final_blocker_action_planner_078j_result.json",
        "latest_status": root / "latest_final_blocker_action_planner_078j_status.json",
        "actions": root / "final_blocker_action_planner_078j_actions.json",
        "safety_snapshot": root / "final_blocker_action_planner_078j_safety_snapshot.json",
        "operator_md": root / "final_blocker_action_planner_078j_operator_summary.md",
    }


def run_final_blocker_action_planner(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    runtime_credential_visibility_path: str | Path | None = None,
    funder_wallet_context_path: str | Path | None = None,
    live_account_readonly_probe_path: str | Path | None = None,
    local_real_check_bundle_path: str | Path | None = None,
    payload_dry_run_readiness_path: str | Path | None = None,
    first_supervised_tiny_order_readiness_path: str | Path | None = None,
    risk_engine_v2_path: str | Path | None = None,
    final_blocker_reducer_path: str | Path | None = None,
    generated_at: str = GENERATED_AT,
    head_before: str = "",
    head_after: str = "",
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("final blocker action planner requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    source_root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    explicit_paths = {
        "runtime_credential_visibility_077c": runtime_credential_visibility_path,
        "funder_wallet_context_077g": funder_wallet_context_path,
        "live_account_readonly_state_probe_070c": live_account_readonly_probe_path,
        "local_real_check_bundle_072c": local_real_check_bundle_path,
        "payload_dry_run_readiness_076d": payload_dry_run_readiness_path,
        "first_supervised_tiny_order_readiness_077a": first_supervised_tiny_order_readiness_path,
        "risk_engine_v2_074d": risk_engine_v2_path,
        "first_live_order_final_blocker_reducer_072d": final_blocker_reducer_path,
    }
    source_artifacts = {
        source_id: _load_source_artifact(
            _select_source_path(source_root, SOURCE_CANDIDATES[source_id], explicit_paths.get(source_id)),
            source_id,
        )
        for source_id in SOURCE_CANDIDATES
    }
    paths = final_blocker_action_planner_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    actions = _build_ordered_actions(
        source_artifacts=source_artifacts,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    )
    non_live_checks_passed = _all_non_live_checks_pass(source_artifacts) and not actions
    if non_live_checks_passed:
        actions.append(
            _action(
                priority=1,
                blocker_id=STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION,
                category=ACTION_CATEGORY_USER_LOCAL_ENV,
                action=(
                    "explicit live authorization is still missing; request it only in a separate operator-approved "
                    "task after all no-live checks remain passing"
                ),
                exact_safe_command=_safe_command(
                    "first_supervised_tiny_order_readiness_packet",
                    market_symbol,
                    strategy_name,
                ),
                reason=(
                    "All known no-live readiness artifacts are passing, but this planner cannot create or consume "
                    "live authorization."
                ),
                source_artifact_keys=("first_supervised_tiny_order_readiness_077a",),
                generated_at=generated_at,
                only_after_all_no_live_checks_pass=True,
            )
        )

    actions_artifact = _build_actions_artifact(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        actions=actions,
        generated_at=generated_at,
    )
    safety_snapshot = _build_safety_snapshot(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        source_artifacts=source_artifacts,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        actions=actions,
        non_live_checks_passed=non_live_checks_passed,
        source_artifacts=source_artifacts,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    result: dict[str, Any] = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": latest_status["status"],
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "review_only": True,
        "local_artifact_read_only": True,
        "input_artifacts": {
            source_id: _source_artifact_summary(source) for source_id, source in source_artifacts.items()
        },
        "ordered_next_actions": [dict(row) for row in actions],
        "next_actions": [dict(row) for row in actions],
        "blocker_count": len(actions),
        "top_blocker": latest_status["top_blocker"],
        "top_blocker_action": dict(actions[0]) if actions else {},
        "non_live_checks_passed": non_live_checks_passed,
        "explicit_live_authorization_present": False,
        "explicit_live_authorization_action_deferred_until_no_live_checks_pass": not non_live_checks_passed,
        "actions_artifact": actions_artifact,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary(latest_status),
        "head_before": clean_text(head_before),
        "head_after": clean_text(head_after),
        "generated_at": generated_at,
        **final_blocker_action_planner_safety_flags(),
    }
    result["validation"] = validate_final_blocker_action_planner_result(result)

    write_json(paths["actions"], actions_artifact)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_final_blocker_action_planner_markdown(result))
    return result


def render_final_blocker_action_planner_cli_summary(result_or_status: Mapping[str, Any]) -> str:
    value = dict(result_or_status or {})
    status = dict(value.get("latest_status", value))
    actions = [dict(row) for row in status.get("ordered_next_actions", []) if isinstance(row, Mapping)]
    lines = [
        "PMBOT final blocker action planner 078J completed.",
        f"Status: {clean_text(status.get('status'))}",
        f"Market: {clean_text(status.get('market_symbol') or status.get('market'))}",
        f"Strategy: {clean_text(status.get('strategy_name') or status.get('strategy'))}",
        f"Blocker count: {int(status.get('blocker_count', 0) or 0)}",
        f"Top blocker: {clean_text(status.get('top_blocker')) or 'none'}",
        f"Non-live checks passed: {str(status.get('non_live_checks_passed') is True).lower()}",
        "Allowed for live: false",
        "Trading requested: false",
        "Submit/cancel/sign/wallet connect: blocked",
        "Ordered next actions:",
    ]
    for row in actions:
        lines.append(
            f"- {int(row.get('priority', 0) or 0)}. {clean_text(row.get('blocker_id'))} "
            f"[{clean_text(row.get('category'))}] command={clean_text(row.get('exact_safe_command'))}"
        )
    lines.append(f"Artifact: {clean_text(status.get('artifact_path'))}")
    return "\n".join(lines)


def render_final_blocker_action_planner_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    actions = [dict(row) for row in value.get("ordered_next_actions", []) if isinstance(row, Mapping)]
    source_artifacts = dict(value.get("input_artifacts", {}))
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Final Blocker Action Planner 078J",
        "",
        f"- status: `{clean_text(value.get('status'))}`",
        f"- market: `{clean_text(value.get('market_symbol') or value.get('market'))}`",
        f"- strategy: `{clean_text(value.get('strategy_name') or value.get('strategy'))}`",
        f"- blocker_count: `{int(value.get('blocker_count', 0) or 0)}`",
        f"- top_blocker: `{clean_text(value.get('top_blocker')) or 'none'}`",
        f"- non_live_checks_passed: `{str(value.get('non_live_checks_passed') is True).lower()}`",
        "- allowed_for_live: `false`",
        "- trading_requested: `false`",
        "- no submit, no cancel, no signing by default, no wallet connect",
        "",
        "## Ordered Next Actions",
        "",
    ]
    for action in actions:
        lines.extend(
            [
                f"### {int(action.get('priority', 0) or 0)}. {clean_text(action.get('blocker_id'))}",
                "",
                f"- category: `{clean_text(action.get('category'))}`",
                f"- action: {clean_text(action.get('action'))}",
                f"- exact_safe_command: `{clean_text(action.get('exact_safe_command'))}`",
                f"- reason: {clean_text(action.get('reason'))}",
                "",
            ]
        )
    lines.extend(
        [
            "## Input Artifacts",
            "",
            *bullet_lines(
                f"`{key}` available={row.get('available') is True} parsed={row.get('parsed') is True} "
                f"status=`{clean_text(row.get('status')) or 'missing'}` path=`{clean_text(row.get('path'))}`"
                for key, row in source_artifacts.items()
                if isinstance(row, Mapping)
            ),
            "",
            "## Artifacts",
            "",
            *bullet_lines(f"`{path}`" for path in paths.values()),
            "",
            "## Safety Statement",
            "",
            "078J is a local no-live planner. It reads only existing PMBOT JSON readiness artifacts, writes "
            "prioritized next-action artifacts, and does not read raw secrets, connect wallets, sign payloads, "
            "submit or cancel orders, call Polymarket endpoints, start browser automation, create schedulers, "
            "create daemons, or run background workers.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def validate_final_blocker_action_planner_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    statuses: list[str] = []

    if value.get("contract_version") != RESULT_CONTRACT:
        errors.append(f"contract_version must be {RESULT_CONTRACT}")
        statuses.append("invalid_contract")
    if value.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")
        statuses.append("task_id_mismatch")
    if value.get("dry_run") is not True:
        errors.append("dry_run must be true")
        statuses.append("dry_run_missing")
    if int(value.get("blocker_count", 0) or 0) != len(value.get("ordered_next_actions", [])):
        errors.append("blocker_count must match ordered_next_actions length")
        statuses.append("blocker_count_mismatch")
    if int(value.get("blocker_count", 0) or 0) <= 0:
        errors.append("at least one next action is required; fake pass is forbidden")
        statuses.append("fake_pass_detected")

    for row in value.get("ordered_next_actions", []):
        if not isinstance(row, Mapping):
            errors.append("each ordered_next_actions row must be an object")
            statuses.append("invalid_action_row")
            continue
        if clean_text(row.get("category")) not in ACTION_CATEGORIES:
            errors.append("action category must be one of the allowed 078J categories")
            statuses.append("invalid_action_category")
        command = clean_text(row.get("exact_safe_command"))
        if not command:
            errors.append("each action must provide exact_safe_command")
            statuses.append("missing_exact_safe_command")
        for flag in FORBIDDEN_RUNTIME_FLAGS:
            if flag in command.lower().split():
                errors.append(f"forbidden runtime flag appears in action command: {flag}")
                statuses.append("forbidden_runtime_flag_in_action")
        if row.get("only_after_all_no_live_checks_pass") is True and value.get("non_live_checks_passed") is not True:
            errors.append("explicit authorization action can only appear after all no-live checks pass")
            statuses.append("explicit_auth_action_not_gated")

    if value.get("non_live_checks_passed") is True:
        action_ids = {
            clean_text(row.get("blocker_id"))
            for row in value.get("ordered_next_actions", [])
            if isinstance(row, Mapping)
        }
        if action_ids != {STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION}:
            errors.append("when no-live checks pass, the only remaining action must be explicit live authorization")
            statuses.append("unexpected_action_after_no_live_pass")

    for path, key, nested in _walk_fields(value):
        if key in FORCED_FALSE_FIELDS and nested is not False:
            errors.append(f"{path}.{key} must be false")
            statuses.append("unsafe_flag_detected")
        if key in FORBIDDEN_RAW_KEYS:
            errors.append(f"{path}.{key} is forbidden in 078J artifacts")
            statuses.append("forbidden_raw_key_detected")

    valid = not errors
    return {
        "contract_version": VALIDATION_CONTRACT,
        "task_id": TASK_ID,
        "valid": valid,
        "status": "passed" if valid else "blocked_validation_failed",
        "statuses": _dedupe(statuses)
        or (["final_blocker_action_planner_valid"] if valid else ["final_blocker_action_planner_blocked"]),
        "errors": errors,
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        **final_blocker_action_planner_safety_flags(),
    }


def final_blocker_action_planner_safety_flags() -> dict[str, Any]:
    return {
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "paper_only": True,
        "review_only": True,
        "preflight_only": True,
        "dry_run_only": True,
        "safe_summary_only": True,
        "non_executable": True,
        "local_artifact_read_only": True,
        "raw_source_payloads_embedded": False,
        "network_access_performed": False,
        "polymarket_api_calls_performed": 0,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "raw_values_emitted": False,
        "raw_secret_values_emitted": False,
        "secret_files_read": False,
        "wallet_files_read": False,
        "wallet_connect_enabled": False,
        "wallet_connection_attempted": False,
        "full_signed_payload_output": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "signing_by_default": False,
        "signer_instantiated": False,
        "signer_instantiation_attempted": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_submission_performed": False,
        "order_submitted": False,
        "order_cancel_enabled": False,
        "order_cancellation_attempted": False,
        "order_cancellation_performed": False,
        "order_cancelled": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_request_performed": False,
        "live_execution_approved": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "allowed_for_live": False,
        "trading_requested": False,
        "no_live_execution": True,
        "no_submit": True,
        "no_cancel": True,
        "no_default_signing": True,
        "no_wallet_connect": True,
        "no_raw_secrets": True,
        "no_fake_pass": True,
    }


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "final blocker action planner is no-live/no-submit/no-sign/no-wallet; unsupported flag(s): "
            + ", ".join(requested)
        )


def _build_ordered_actions(
    *,
    source_artifacts: Mapping[str, Mapping[str, Any]],
    market_symbol: str,
    strategy_name: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    unsafe_sources = [
        source_id
        for source_id, source in source_artifacts.items()
        if _source_has_unsafe_true_flags(_payload(source))
    ]
    if unsafe_sources:
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_UNSAFE_LIVE_FLAG_OBSERVED,
            category=ACTION_CATEGORY_CODE_TASK,
            action="review unsafe true-state fields in readiness artifacts before continuing",
            exact_safe_command="python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run",
            reason="At least one input artifact exposes an execution-related field with a truthy value.",
            source_artifact_keys=tuple(unsafe_sources),
            generated_at=generated_at,
        )
        return actions

    runtime = source_artifacts["runtime_credential_visibility_077c"]
    funder = source_artifacts["funder_wallet_context_077g"]
    account = source_artifacts["live_account_readonly_state_probe_070c"]
    local_real = source_artifacts["local_real_check_bundle_072c"]
    payload = source_artifacts["payload_dry_run_readiness_076d"]
    first_packet = source_artifacts["first_supervised_tiny_order_readiness_077a"]
    risk = source_artifacts["risk_engine_v2_074d"]
    final_reducer = source_artifacts["first_live_order_final_blocker_reducer_072d"]

    if _source_missing(runtime):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_MISSING_RUNTIME_CREDENTIAL_VISIBILITY,
            category=ACTION_CATEGORY_CODE_TASK,
            action="rerun runtime credential visibility diagnostic in dry-run mode",
            exact_safe_command=_safe_command("runtime_credential_visibility_diagnostic", market_symbol, strategy_name),
            reason="Runtime credential visibility artifact is missing or unreadable.",
            source_artifact_keys=("runtime_credential_visibility_077c",),
            generated_at=generated_at,
        )
    if not _source_missing(funder) and _funder_missing(funder):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_MISSING_FUNDER_ADDRESS,
            category=ACTION_CATEGORY_USER_LOCAL_ENV,
            action="set POLYMARKET_FUNDER_ADDRESS if required by account/proxy wallet setup",
            exact_safe_command=_safe_command("funder_wallet_context_diagnostic", market_symbol, strategy_name),
            reason="Funder wallet context reports a missing funder address; no funder is inferred or copied.",
            source_artifact_keys=("funder_wallet_context_077g",),
            generated_at=generated_at,
        )
    elif _source_missing(funder):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_MISSING_FUNDER_CONTEXT,
            category=ACTION_CATEGORY_CODE_TASK,
            action="rerun funder wallet context diagnostic in dry-run mode",
            exact_safe_command=_safe_command("funder_wallet_context_diagnostic", market_symbol, strategy_name),
            reason="Funder wallet context artifact is missing or unreadable.",
            source_artifact_keys=("funder_wallet_context_077g",),
            generated_at=generated_at,
        )

    if not _runtime_credentials_ready(runtime) and not _runtime_missing_only_funder(runtime):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_RUNTIME_CREDENTIALS_NOT_VISIBLE,
            category=ACTION_CATEGORY_USER_LOCAL_ENV,
            action="make required runtime credential variables visible locally without printing raw values",
            exact_safe_command=_safe_command("runtime_credential_visibility_diagnostic", market_symbol, strategy_name),
            reason="Runtime credential visibility is not complete; downstream signer and account checks must stay blocked.",
            source_artifact_keys=("runtime_credential_visibility_077c",),
            generated_at=generated_at,
        )

    if _source_missing(account):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_MISSING_READONLY_ACCOUNT_PROBE,
            category=ACTION_CATEGORY_CODE_TASK,
            action="rerun the live account read-only probe in dry-run mode",
            exact_safe_command=_safe_command("live_account_readonly_state_probe", market_symbol, strategy_name),
            reason="Live account read-only probe artifact is missing or unreadable.",
            source_artifact_keys=("live_account_readonly_state_probe_070c",),
            generated_at=generated_at,
        )
    elif _sdk_unavailable(account):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_POLYMARKET_SDK_UNAVAILABLE,
            category=ACTION_CATEGORY_DEPENDENCY_INSTALL,
            action="install/check py-clob-client, then rerun the read-only probe",
            exact_safe_command="python -m pip install py-clob-client",
            reason="The read-only account probe reports that the supported Polymarket CLOB SDK is unavailable.",
            source_artifact_keys=("live_account_readonly_state_probe_070c",),
            generated_at=generated_at,
            follow_up_safe_command=_safe_command("live_account_readonly_state_probe", market_symbol, strategy_name),
        )
    elif not _account_readonly_ready(account):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_READONLY_ACCOUNT_PROBE_NOT_READY,
            category=ACTION_CATEGORY_POLYMARKET_ACCOUNT,
            action="resolve the read-only account probe blocker without submitting, cancelling, signing, or connecting a wallet",
            exact_safe_command=_safe_command("live_account_readonly_state_probe", market_symbol, strategy_name),
            reason="Read-only account evidence is not yet a succeeded live-blocked probe.",
            source_artifact_keys=("live_account_readonly_state_probe_070c",),
            generated_at=generated_at,
        )

    if not _local_real_check_ready(local_real):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK,
            category=ACTION_CATEGORY_CODE_TASK,
            action="rerun the local real-check bundle in dry-run mode",
            exact_safe_command=_safe_command("local_real_check_bundle", market_symbol, strategy_name),
            reason="Local real-check bundle evidence is missing or not readable.",
            source_artifact_keys=("local_real_check_bundle_072c",),
            generated_at=generated_at,
        )

    if _signer_diagnostic_not_ok(payload, first_packet):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
            category=ACTION_CATEGORY_CODE_TASK,
            action="rerun guarded signer diagnostic after env is visible, then bridge signer evidence",
            exact_safe_command=_safe_command("guarded_signer_diagnostic_smoke", market_symbol, strategy_name),
            reason="Signer diagnostic evidence is missing, failed, or not OK for payload dry-run readiness.",
            source_artifact_keys=("payload_dry_run_readiness_076d", "first_supervised_tiny_order_readiness_077a"),
            generated_at=generated_at,
            follow_up_safe_command=_safe_command("signer_diagnostic_evidence_bridge", market_symbol, strategy_name),
            preconditions=("runtime credential visibility is complete",),
        )
    elif not _payload_ready(payload):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY,
            category=ACTION_CATEGORY_CODE_TASK,
            action="rerun payload readiness after signer OK",
            exact_safe_command=_safe_command("payload_dry_run_readiness_review", market_symbol, strategy_name),
            reason="Payload dry-run readiness is not ready for operator review.",
            source_artifact_keys=("payload_dry_run_readiness_076d",),
            generated_at=generated_at,
            preconditions=("signer diagnostic evidence is OK",),
        )

    if not _risk_engine_ready(risk):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_RISK_ENGINE_NOT_READY,
            category=ACTION_CATEGORY_CODE_TASK,
            action="rerun Risk Engine v2 review in dry-run mode",
            exact_safe_command=_safe_command("risk_engine_v2_review", market_symbol, strategy_name),
            reason="Risk Engine v2 does not report a no-live passed review.",
            source_artifact_keys=("risk_engine_v2_074d",),
            generated_at=generated_at,
        )
    if not _final_reducer_clear(final_reducer):
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_FINAL_REDUCER_NOT_CLEAR,
            category=ACTION_CATEGORY_CODE_TASK,
            action="rerun the final blocker reducer and resolve any remaining no-live blockers",
            exact_safe_command=_safe_command("first_live_order_final_blocker_reducer", market_symbol, strategy_name),
            reason="Final blocker reducer is missing or still reports remaining blockers.",
            source_artifact_keys=("first_live_order_final_blocker_reducer_072d",),
            generated_at=generated_at,
        )
    if not _first_supervised_packet_ready(first_packet) and not actions:
        _append_action(
            actions,
            blocker_id=STATUS_BLOCKED_FIRST_SUPERVISED_PACKET_NOT_READY,
            category=ACTION_CATEGORY_CODE_TASK,
            action="rerun the first supervised tiny order readiness packet in dry-run mode",
            exact_safe_command=_safe_command("first_supervised_tiny_order_readiness_packet", market_symbol, strategy_name),
            reason="The 077A packet is not yet ready for a separate live authorization request.",
            source_artifact_keys=("first_supervised_tiny_order_readiness_077a",),
            generated_at=generated_at,
        )
    return actions


def _append_action(
    actions: list[dict[str, Any]],
    *,
    blocker_id: str,
    category: str,
    action: str,
    exact_safe_command: str,
    reason: str,
    source_artifact_keys: Sequence[str],
    generated_at: str,
    follow_up_safe_command: str = "",
    preconditions: Sequence[str] = (),
) -> None:
    existing = {clean_text(row.get("blocker_id")) for row in actions}
    if blocker_id in existing:
        return
    actions.append(
        _action(
            priority=len(actions) + 1,
            blocker_id=blocker_id,
            category=category,
            action=action,
            exact_safe_command=exact_safe_command,
            reason=reason,
            source_artifact_keys=source_artifact_keys,
            generated_at=generated_at,
            follow_up_safe_command=follow_up_safe_command,
            preconditions=preconditions,
        )
    )


def _action(
    *,
    priority: int,
    blocker_id: str,
    category: str,
    action: str,
    exact_safe_command: str,
    reason: str,
    source_artifact_keys: Sequence[str],
    generated_at: str,
    follow_up_safe_command: str = "",
    preconditions: Sequence[str] = (),
    only_after_all_no_live_checks_pass: bool = False,
) -> dict[str, Any]:
    value = {
        "contract_version": ACTION_CONTRACT,
        "task_id": TASK_ID,
        "priority": priority,
        "action_id": f"action_{priority:02d}_{clean_text(blocker_id)}",
        "blocker_id": clean_text(blocker_id),
        "status": "unresolved",
        "category": clean_text(category),
        "action": clean_text(action),
        "reason": clean_text(reason),
        "exact_safe_command": clean_text(exact_safe_command),
        "follow_up_safe_command": clean_text(follow_up_safe_command),
        "preconditions": [clean_text(item) for item in preconditions if clean_text(item)],
        "source_artifact_keys": [clean_text(item) for item in source_artifact_keys if clean_text(item)],
        "only_after_all_no_live_checks_pass": only_after_all_no_live_checks_pass,
        "requires_separate_operator_task": blocker_id == STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION,
        "generated_at": generated_at,
    }
    value.update(final_blocker_action_planner_safety_flags())
    return value


def _build_actions_artifact(
    *,
    market_symbol: str,
    strategy_name: str,
    actions: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": ACTIONS_CONTRACT,
        "task_id": TASK_ID,
        "status": _status_for_actions(actions),
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "ordered_next_actions": [dict(row) for row in actions],
        "blocker_count": len(actions),
        "top_blocker": clean_text(actions[0].get("blocker_id")) if actions else "",
        "action_categories": sorted(ACTION_CATEGORIES),
        "generated_at": generated_at,
    }
    value.update(final_blocker_action_planner_safety_flags())
    return value


def _build_safety_snapshot(
    *,
    market_symbol: str,
    strategy_name: str,
    source_artifacts: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SAFETY_CONTRACT,
        "task_id": TASK_ID,
        "status": "no_live_action_planner_safety_snapshot",
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "observed_artifacts": {
            source_id: _source_artifact_summary(source) for source_id, source in source_artifacts.items()
        },
        "observed_artifact_count": len(source_artifacts),
        "unknown_remains_unknown": True,
        "generated_at": generated_at,
    }
    value.update(final_blocker_action_planner_safety_flags())
    return value


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    actions: Sequence[Mapping[str, Any]],
    non_live_checks_passed: bool,
    source_artifacts: Mapping[str, Mapping[str, Any]],
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": _status_for_actions(actions),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "blocker_count": len(actions),
        "top_blocker": clean_text(actions[0].get("blocker_id")) if actions else "",
        "ordered_next_actions": [dict(row) for row in actions],
        "input_artifact_statuses": {
            source_id: clean_text(source.get("status")) or "missing"
            for source_id, source in source_artifacts.items()
        },
        "non_live_checks_passed": non_live_checks_passed,
        "explicit_live_authorization_present": False,
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "actions_path": clean_text(artifact_paths.get("actions")),
        "safety_snapshot_path": clean_text(artifact_paths.get("safety_snapshot")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "generated_at": generated_at,
    }
    value.update(final_blocker_action_planner_safety_flags())
    return value


def _operator_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    top = clean_text(value.get("top_blocker")) or "none"
    count = int(value.get("blocker_count", 0) or 0)
    if value.get("non_live_checks_passed") is True:
        return (
            "All known no-live checks pass, but explicit live authorization is still missing and must be "
            "handled only in a separate operator-approved task. No live action is authorized here."
        )
    return (
        f"Final blocker action planning found {count} unresolved next action(s). Top blocker: {top}. "
        "No live action is authorized here."
    )


def _status_for_actions(actions: Sequence[Mapping[str, Any]]) -> str:
    if not actions:
        return STATUS_BLOCKED_FIRST_SUPERVISED_PACKET_NOT_READY
    return clean_text(actions[0].get("blocker_id")) or STATUS_BLOCKED_FIRST_SUPERVISED_PACKET_NOT_READY


def _select_source_path(
    source_root: Path,
    candidates: Sequence[Path],
    explicit_path: str | Path | None,
) -> Path:
    if explicit_path:
        return Path(explicit_path)
    for candidate in candidates:
        path = source_root / candidate
        if path.exists() and path.is_file():
            return path
    return source_root / candidates[0]


def _load_source_artifact(path: Path, source_id: str) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {
            "source_id": source_id,
            "available": False,
            "parsed": False,
            "status": "missing",
            "path": normalize_path(path),
            "contract_version": "",
            "blocker_count": 0,
            "read_error_type": "",
            "payload": {},
        }
    try:
        payload = load_json_object(path, label=source_id)
    except Exception as exc:
        return {
            "source_id": source_id,
            "available": True,
            "parsed": False,
            "status": "invalid_or_unreadable",
            "path": normalize_path(path),
            "contract_version": "",
            "blocker_count": 0,
            "read_error_type": type(exc).__name__,
            "payload": {},
        }
    return {
        "source_id": source_id,
        "available": True,
        "parsed": True,
        "status": _text_field(payload, "status") or "status_missing",
        "path": normalize_path(path),
        "contract_version": _text_field(payload, "contract_version"),
        "blocker_count": _safe_int(_field(payload, "blocker_count")),
        "remaining_blocker_count": _safe_int(_field(payload, "remaining_blocker_count")),
        "allowed_for_live_status": _bool_status(_field(payload, "allowed_for_live")),
        "trading_requested_status": _bool_status(_field(payload, "trading_requested")),
        "payload": payload,
    }


def _source_artifact_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": clean_text(source.get("source_id")),
        "available": source.get("available") is True,
        "parsed": source.get("parsed") is True,
        "status": clean_text(source.get("status")),
        "contract_version": clean_text(source.get("contract_version")),
        "blocker_count": _safe_int(source.get("blocker_count")),
        "remaining_blocker_count": _safe_int(source.get("remaining_blocker_count")),
        "allowed_for_live_status": clean_text(source.get("allowed_for_live_status")) or "unknown",
        "trading_requested_status": clean_text(source.get("trading_requested_status")) or "unknown",
        "path": clean_text(source.get("path")),
        "read_error_type": clean_text(source.get("read_error_type")),
        "source_payload_embedded": False,
    }


def _source_missing(source: Mapping[str, Any]) -> bool:
    return source.get("available") is not True or source.get("parsed") is not True


def _payload(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = source.get("payload")
    return dict(payload) if isinstance(payload, Mapping) else {}


def _runtime_credentials_ready(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    return (
        source.get("parsed") is True
        and (
            clean_text(source.get("status")) == READY_RUNTIME_CREDENTIALS
            or (
                _field(payload, "polymarket_l2_visible") is True
                and _field(payload, "private_key_visible") is True
                and _field(payload, "wallet_context_visible") is True
            )
        )
    )


def _runtime_missing_only_funder(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    missing = _clean_list(_field(payload, "wallet_context_missing_env_vars"))
    return missing == ["POLYMARKET_FUNDER_ADDRESS"]


def _funder_missing(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    return (
        clean_text(source.get("status")) == "blocked_missing_funder_address"
        or _field(payload, "funder_address_present") is False
        and _field(payload, "wallet_address_present") is True
    )


def _funder_ready(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    status = clean_text(source.get("status"))
    return (
        source.get("parsed") is True
        and (
            status in {"wallet_context_visible", "funder_equals_wallet_address", "funder_differs_from_wallet_address"}
            or (
                _field(payload, "wallet_context_visible") is True
                and _field(payload, "funder_address_present") is True
                and _field(payload, "signature_type_present") is True
            )
        )
    )


def _sdk_unavailable(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    status = clean_text(source.get("status"))
    return status in {"blocked_sdk_unavailable", "blocked_dependency_missing"} or _has_blocker(
        payload,
        "polymarket_clob_sdk_dependency_missing",
    )


def _account_readonly_ready(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    return (
        source.get("parsed") is True
        and (
            clean_text(source.get("status")) == READY_ACCOUNT_READONLY
            or _field(payload, "account_state_probe_performed") is True
        )
    )


def _local_real_check_ready(source: Mapping[str, Any]) -> bool:
    return source.get("parsed") is True and clean_text(source.get("status")) not in {"", "missing", "invalid_or_unreadable"}


def _signer_diagnostic_not_ok(payload_source: Mapping[str, Any], first_packet_source: Mapping[str, Any]) -> bool:
    statuses = {
        clean_text(payload_source.get("status")),
        clean_text(first_packet_source.get("status")),
        _text_field(_payload(payload_source), "signer_diagnostic_status"),
        _text_field(_payload(first_packet_source), "signer_diagnostic_status"),
        _text_field(_payload(payload_source), "current_top_blocker"),
        _text_field(_payload(first_packet_source), "current_top_blocker"),
    }
    if statuses & {
        "blocked_signer_diagnostic_failed",
        "blocked_signer_diagnostic_not_ok",
        "blocked_missing_signer_diagnostic_evidence",
    }:
        return True
    payload = _payload(payload_source)
    first_packet = _payload(first_packet_source)
    if _field(payload, "signer_diagnostic_ok") is False:
        return True
    return _field(first_packet, "signer_diagnostic_ok") is False


def _payload_ready(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    return (
        source.get("parsed") is True
        and (
            clean_text(source.get("status")) == READY_PAYLOAD
            or _field(payload, "payload_dry_run_ready") is True
        )
    )


def _risk_engine_ready(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    remaining = _safe_int(_field(payload, "remaining_blocker_count"))
    return (
        source.get("parsed") is True
        and (
            clean_text(source.get("status")) == READY_RISK
            or _field(payload, "risk_engine_v2_ready") is True
        )
        and remaining == 0
    )


def _final_reducer_clear(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    remaining = _safe_int(_field(payload, "remaining_blocker_count"))
    return (
        source.get("parsed") is True
        and (
            clean_text(source.get("status")) == READY_FINAL_REDUCER
            or remaining == 0
        )
    )


def _first_supervised_packet_ready(source: Mapping[str, Any]) -> bool:
    payload = _payload(source)
    return (
        source.get("parsed") is True
        and (
            clean_text(source.get("status")) == READY_FIRST_SUPERVISED_PACKET
            or _field(payload, "first_supervised_tiny_order_ready_for_authorization") is True
        )
    )


def _all_non_live_checks_pass(source_artifacts: Mapping[str, Mapping[str, Any]]) -> bool:
    return (
        _runtime_credentials_ready(source_artifacts["runtime_credential_visibility_077c"])
        and _funder_ready(source_artifacts["funder_wallet_context_077g"])
        and _account_readonly_ready(source_artifacts["live_account_readonly_state_probe_070c"])
        and _local_real_check_ready(source_artifacts["local_real_check_bundle_072c"])
        and _payload_ready(source_artifacts["payload_dry_run_readiness_076d"])
        and _risk_engine_ready(source_artifacts["risk_engine_v2_074d"])
        and _final_reducer_clear(source_artifacts["first_live_order_final_blocker_reducer_072d"])
        and _first_supervised_packet_ready(source_artifacts["first_supervised_tiny_order_readiness_077a"])
    )


def _source_has_unsafe_true_flags(payload: Mapping[str, Any]) -> bool:
    for _, key, nested in _walk_fields(payload):
        if key in UNSAFE_TRUE_SOURCE_FIELDS and nested is True:
            return True
    return False


def _has_blocker(payload: Mapping[str, Any], blocker_id: str) -> bool:
    target = clean_text(blocker_id)
    for _, key, nested in _walk_fields(payload):
        if key == "blocker_id" and clean_text(nested) == target:
            return True
    return False


def _safe_command(runner_name: str, market_symbol: str, strategy_name: str) -> str:
    return f"python -m pm_bot.operator_runner.{runner_name} --market {market_symbol} --strategy {strategy_name} --dry-run"


def _field(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        if key in value:
            return value[key]
        for nested in value.values():
            found = _field(nested, key)
            if found is not _MISSING:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _field(nested, key)
            if found is not _MISSING:
                return found
    return _MISSING


def _text_field(value: Any, key: str) -> str:
    found = _field(value, key)
    if found is _MISSING:
        return ""
    return clean_text(found)


def _safe_int(value: Any) -> int:
    if value is _MISSING:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _bool_status(value: Any) -> str:
    if value is True:
        return "unsafe_true"
    if value is False:
        return "safe_false"
    return "unknown"


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [item.strip() for item in value.split(",")]
    elif isinstance(value, Sequence):
        candidates = [clean_text(item) for item in value]
    else:
        candidates = []
    return [item for item in candidates if item]


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


class _Missing:
    pass


_MISSING = _Missing()
