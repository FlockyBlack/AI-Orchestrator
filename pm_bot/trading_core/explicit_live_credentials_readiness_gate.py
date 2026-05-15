from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.explicit_live_credentials_readiness_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    DEFAULT_MARKER_REQUIREMENTS,
    EXECUTION_FLAG_MARKERS,
    FORCED_FALSE_EXECUTION_FIELDS,
    MARKER_CATEGORY_EXECUTION_FLAG_BLOCKED,
    MARKER_CATEGORY_MISSING,
    MARKER_CATEGORY_NOT_CHECKED,
    MARKER_CATEGORY_PRESENT_REDACTED,
    MARKER_GROUP_EXECUTION_FLAG,
    MANUAL_CONTROL_MARKERS,
    REQUIRED_UNRESOLVED_BLOCKER_IDS,
    STATUS_BLOCKED,
    STATUS_REDACTED_PRESENCE_REVIEW_READY,
    TASK_ID,
    LATEST_EXPLICIT_LIVE_CREDENTIALS_READINESS_STATUS_CONTRACT,
    ExplicitLiveCredentialMarkerPresence,
    ExplicitLiveCredentialMarkerPresenceReport,
    ExplicitLiveCredentialMarkerRequirement,
    ExplicitLiveCredentialsOperatorApprovalBoundary,
    ExplicitLiveCredentialsOperatorChecklist,
    ExplicitLiveCredentialsReadinessBlocker,
    ExplicitLiveCredentialsReadinessBlockerMatrix,
    ExplicitLiveCredentialsReadinessGate,
    ExplicitLiveCredentialsReadinessSummary,
    ExplicitLiveCredentialsSafetyPolicyValidation,
    explicit_live_credentials_readiness_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064")

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--wallet-connect",
    "--signing",
    "--sign",
    "--submit",
    "--cancel",
    "--approve-live",
    "--order",
    "--balance",
    "--balances",
    "--position",
    "--positions",
    "--fills",
    "--pnl",
    "--private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
    "--env-dump",
)


def explicit_live_credentials_readiness_gate_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "explicit_live_credentials_readiness_gate_064_result.json",
        "operator_md": root / "explicit_live_credentials_readiness_gate_064_operator.md",
        "latest_status": root / "latest_explicit_live_credentials_readiness_gate_status_064.json",
        "marker_presence": root / "redacted_marker_presence_064.json",
        "operator_approval_boundary": root / "operator_approval_boundary_064.json",
        "safety_policy_validation": root / "credential_safety_policy_validation_064.json",
        "blockers": root / "live_credentials_readiness_blockers_064.json",
        "operator_checklist": root / "explicit_live_credentials_operator_checklist_064.json",
        "readiness_summary": root / "explicit_live_credentials_readiness_summary_064.json",
    }


def run_explicit_live_credentials_readiness_gate(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    marker_requirements: Sequence[tuple[str, str, bool]] = DEFAULT_MARKER_REQUIREMENTS,
    marker_presence: Mapping[str, bool] | None = None,
    environ: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("explicit live credentials readiness gate requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = explicit_live_credentials_readiness_gate_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    requirements = _build_marker_requirements(marker_requirements, generated_at=generated_at)
    marker_checks = _build_marker_checks(
        requirements=requirements,
        marker_presence=marker_presence,
        environ=environ,
        generated_at=generated_at,
    )
    marker_presence_report = ExplicitLiveCredentialMarkerPresenceReport(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        marker_requirements=tuple(requirements),
        marker_checks=tuple(marker_checks),
        generated_at=generated_at,
    ).to_dict()

    present_by_label = {
        clean_text(row.get("marker_label")): row.get("present") is True
        for row in marker_checks
        if isinstance(row, Mapping)
    }
    operator_approval_boundary = ExplicitLiveCredentialsOperatorApprovalBoundary(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        operator_review_marker_present=present_by_label.get(
            "PMBOT_LIVE_CREDENTIALS_OPERATOR_REVIEW_RECORD_PRESENT"
        )
        is True,
        dual_control_review_marker_present=present_by_label.get(
            "PMBOT_LIVE_CREDENTIALS_DUAL_CONTROL_REVIEW_PRESENT"
        )
        is True,
        generated_at=generated_at,
    ).to_dict()
    safety_policy_validation = ExplicitLiveCredentialsSafetyPolicyValidation(
        marker_presence_report=marker_presence_report,
        generated_at=generated_at,
    ).to_dict()
    blockers = _build_blockers(
        marker_presence_report=marker_presence_report,
        generated_at=generated_at,
    )
    blocker_matrix = ExplicitLiveCredentialsReadinessBlockerMatrix(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        blockers=tuple(blockers),
        generated_at=generated_at,
    ).to_dict()
    operator_checklist = ExplicitLiveCredentialsOperatorChecklist(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        marker_presence_report=marker_presence_report,
        operator_approval_boundary=operator_approval_boundary,
        safety_policy_validation=safety_policy_validation,
        blocker_matrix=blocker_matrix,
        generated_at=generated_at,
    ).to_dict()
    readiness_summary = ExplicitLiveCredentialsReadinessSummary(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        marker_presence_path=path_refs["marker_presence"],
        operator_approval_boundary_path=path_refs["operator_approval_boundary"],
        safety_policy_validation_path=path_refs["safety_policy_validation"],
        blocker_matrix_path=path_refs["blockers"],
        marker_presence_report=marker_presence_report,
        operator_approval_boundary=operator_approval_boundary,
        safety_policy_validation=safety_policy_validation,
        blocker_matrix=blocker_matrix,
        generated_at=generated_at,
    ).to_dict()
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        marker_presence_report=marker_presence_report,
        readiness_summary=readiness_summary,
        blocker_matrix=blocker_matrix,
        path_refs=path_refs,
        generated_at=generated_at,
    )
    result = ExplicitLiveCredentialsReadinessGate(
        status=clean_text(readiness_summary.get("readiness_status")) or STATUS_BLOCKED,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        marker_presence_report=marker_presence_report,
        operator_approval_boundary=operator_approval_boundary,
        safety_policy_validation=safety_policy_validation,
        blocker_matrix=blocker_matrix,
        operator_checklist=operator_checklist,
        readiness_summary=readiness_summary,
        latest_status=latest_status,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["marker_presence"], marker_presence_report)
    write_json(paths["operator_approval_boundary"], operator_approval_boundary)
    write_json(paths["safety_policy_validation"], safety_policy_validation)
    write_json(paths["blockers"], blocker_matrix)
    write_json(paths["operator_checklist"], operator_checklist)
    write_json(paths["readiness_summary"], readiness_summary)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_explicit_live_credentials_readiness_gate_markdown(result))
    return result


def render_explicit_live_credentials_readiness_gate_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Explicit live credentials readiness gate completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Redacted presence review ready: {str(value.get('redacted_presence_review_ready') is True).lower()}",
            f"Missing required markers: {int(value.get('missing_required_marker_count', 0) or 0)}",
            f"Present execution flags: {int(value.get('present_execution_flag_count', 0) or 0)}",
            "Allowed for live: false",
            "Credential values read: false",
            "Live execution: blocked",
            "Authenticated calls: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Signing: blocked",
            "Wallet: blocked",
            f"Resolved blockers: {int(value.get('resolved_blocker_count', 0) or 0)}",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_explicit_live_credentials_readiness_gate_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    marker_report = dict(value.get("marker_presence_report", {}))
    readiness_summary = dict(value.get("readiness_summary", {}))
    operator_boundary = dict(value.get("operator_approval_boundary", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Explicit Live Credentials Readiness Gate 064",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `redacted presence-only / review-only`",
        "- execution_mode: `preflight`",
        "- dry_run_only: `true`",
        "- non_executable: `true`",
        "- allowed_for_live: `false`",
        "- live_ready: `false`",
        "- resolved_blocker_count: `0`",
        "",
        "## Marker Presence",
        "",
        f"- marker_count: `{marker_report.get('marker_count')}`",
        f"- required_marker_count: `{marker_report.get('required_marker_count')}`",
        f"- missing_required_marker_count: `{marker_report.get('missing_required_marker_count')}`",
        f"- present_execution_flag_count: `{marker_report.get('present_execution_flag_count')}`",
        "- presence_only: `true`",
        "- presence_booleans_only: `true`",
        "- explicit_allowlist_only: `true`",
        "- broad_environment_scan_performed: `false`",
        "- environment_values_read: `false`",
        "- raw_values_emitted: `false`",
        "",
        "## Operator Approval Boundary",
        "",
        f"- operator_review_marker_present: `{str(operator_boundary.get('operator_review_marker_present') is True).lower()}`",
        f"- dual_control_review_marker_present: `{str(operator_boundary.get('dual_control_review_marker_present') is True).lower()}`",
        "- operator_approved: `false`",
        "- operator_review_does_not_enable_live: `true`",
        "- separate_live_enabling_task_required: `true`",
        "",
        "## Readiness Meaning",
        "",
        f"- redacted_presence_review_ready: `{str(readiness_summary.get('redacted_presence_review_ready') is True).lower()}`",
        "- this is not live authorization",
        "- no credential value validation was performed",
        "- no wallet, signing, authenticated request, order submission, or cancellation path exists here",
        "",
        "## Blockers",
        "",
        *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
        "",
        "## Required False Flags",
        "",
        *bullet_lines(f"`{field}=false`" for field in FORCED_FALSE_EXECUTION_FIELDS),
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "explicit live credentials readiness gate is presence-only; unsupported live/auth/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    marker_presence_report: Mapping[str, Any],
    readiness_summary: Mapping[str, Any],
    blocker_matrix: Mapping[str, Any],
    path_refs: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": LATEST_EXPLICIT_LIVE_CREDENTIALS_READINESS_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(readiness_summary.get("readiness_status")) or STATUS_BLOCKED,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "readiness_status": clean_text(readiness_summary.get("readiness_status")) or STATUS_BLOCKED,
        "redacted_presence_review_ready": readiness_summary.get("redacted_presence_review_ready") is True,
        "live_ready": False,
        "allowed_for_live": False,
        "marker_count": int(marker_presence_report.get("marker_count", 0) or 0),
        "required_marker_count": int(marker_presence_report.get("required_marker_count", 0) or 0),
        "missing_required_marker_count": int(marker_presence_report.get("missing_required_marker_count", 0) or 0),
        "present_execution_flag_count": int(marker_presence_report.get("present_execution_flag_count", 0) or 0),
        "blocker_count": int(blocker_matrix.get("blocker_count", 0) or 0),
        "resolved_blocker_count": 0,
        "required_unresolved_blocker_ids": list(REQUIRED_UNRESOLVED_BLOCKER_IDS),
        "unresolved_blocker_ids": list(blocker_matrix.get("unresolved_blocker_ids", [])),
        "artifact_path": clean_text(path_refs.get("result")),
        "latest_status_path": clean_text(path_refs.get("latest_status")),
        "operator_markdown_path": clean_text(path_refs.get("operator_md")),
        "marker_presence_path": clean_text(path_refs.get("marker_presence")),
        "operator_approval_boundary_path": clean_text(path_refs.get("operator_approval_boundary")),
        "safety_policy_validation_path": clean_text(path_refs.get("safety_policy_validation")),
        "blockers_path": clean_text(path_refs.get("blockers")),
        "operator_checklist_path": clean_text(path_refs.get("operator_checklist")),
        "readiness_summary_path": clean_text(path_refs.get("readiness_summary")),
        "operator_summary": (
            "Redacted presence-only credential readiness artifacts generated. Live execution remains blocked and "
            "allowed_for_live remains false."
        ),
        "generated_at": generated_at,
    }
    value.update(explicit_live_credentials_readiness_safety_flags())
    return value


def _build_marker_requirements(
    marker_requirements: Sequence[tuple[str, str, bool]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for marker_label, marker_group, required in marker_requirements:
        label = clean_text(marker_label)
        if not label or label in seen:
            continue
        seen.add(label)
        rows.append(
            ExplicitLiveCredentialMarkerRequirement(
                marker_label=label,
                marker_group=marker_group,
                required_for_redacted_review=required is True,
                generated_at=generated_at,
            ).to_dict()
        )
    return rows


def _build_marker_checks(
    *,
    requirements: Sequence[Mapping[str, Any]],
    marker_presence: Mapping[str, bool] | None,
    environ: Mapping[str, str] | None,
    generated_at: str,
) -> list[dict[str, Any]]:
    active_environ = os.environ if environ is None else environ
    explicit_presence = dict(marker_presence or {})
    checks: list[dict[str, Any]] = []
    for requirement in requirements:
        label = clean_text(requirement.get("marker_label"))
        group = clean_text(requirement.get("marker_group"))
        required = requirement.get("required_for_redacted_review") is True
        present = explicit_presence.get(label) is True if marker_presence is not None else label in active_environ
        checks.append(
            ExplicitLiveCredentialMarkerPresence(
                marker_label=label,
                marker_group=group,
                present=present,
                required_for_redacted_review=required,
                result_category=_marker_result_category(group=group, present=present),
                generated_at=generated_at,
            ).to_dict()
        )
    return checks


def _marker_result_category(*, group: str, present: bool) -> str:
    if group == MARKER_GROUP_EXECUTION_FLAG:
        return MARKER_CATEGORY_EXECUTION_FLAG_BLOCKED if present else MARKER_CATEGORY_NOT_CHECKED
    return MARKER_CATEGORY_PRESENT_REDACTED if present else MARKER_CATEGORY_MISSING


def _build_blockers(
    *,
    marker_presence_report: Mapping[str, Any],
    generated_at: str,
) -> list[dict[str, Any]]:
    rows: list[tuple[str, str, str]] = [
        ("live_execution_not_approved", "live_execution", "Live execution approval remains false."),
        (
            "credentials_not_value_verified_by_pmbot",
            "credential_boundary",
            "PMBOT did not read, validate, fingerprint, or serialize credential values.",
        ),
        (
            "operator_review_does_not_enable_execution",
            "operator_boundary",
            "Operator marker presence is review evidence only and cannot enable live execution.",
        ),
        (
            "authenticated_polymarket_requests_blocked",
            "authenticated_request",
            "Authenticated Polymarket requests remain blocked.",
        ),
        ("wallet_connection_blocked", "wallet_boundary", "Wallet connection remains blocked."),
        ("signer_instantiation_blocked", "signing_boundary", "Signer instantiation remains blocked."),
        ("private_key_reads_blocked", "credential_boundary", "Private key reads remain blocked."),
        ("api_secret_reads_blocked", "credential_boundary", "API secret reads remain blocked."),
        (
            "signed_payload_generation_blocked",
            "signing_boundary",
            "Signed payload generation remains blocked.",
        ),
        ("order_submission_blocked", "order_submission", "Order submission remains blocked."),
        ("order_cancellation_blocked", "order_cancellation", "Order cancellation remains blocked."),
        ("balance_reads_blocked", "account_runtime", "Balance reads remain blocked."),
        ("position_reads_blocked", "account_runtime", "Position reads remain blocked."),
        (
            "kill_switch_not_bound_to_live_adapter",
            "kill_switch",
            "Kill-switch markers are not bound to any live adapter in this gate.",
        ),
        (
            "rollback_cancel_plan_not_implemented",
            "rollback_cancel",
            "Rollback and cancellation implementation remains a later task.",
        ),
        (
            "first_live_order_task_not_present",
            "future_live_order",
            "A separate first tiny live order task is still required.",
        ),
    ]
    for marker in marker_presence_report.get("missing_required_markers", []):
        label = clean_text(marker)
        if label:
            rows.append(
                (
                    f"missing_required_marker:{label}",
                    "marker_presence",
                    f"Required marker `{label}` is absent; only presence metadata was recorded.",
                )
            )
    for marker in marker_presence_report.get("present_execution_flags", []):
        label = clean_text(marker)
        if label:
            rows.append(
                (
                    f"execution_flag_present_blocked:{label}",
                    "execution_flag_boundary",
                    f"Execution flag marker `{label}` is present and blocked; its value was not read.",
                )
            )
    return [
        ExplicitLiveCredentialsReadinessBlocker(
            blocker_id=blocker_id,
            blocker_category=category,
            reason=reason,
            generated_at=generated_at,
        ).to_dict()
        for blocker_id, category, reason in rows
    ]
