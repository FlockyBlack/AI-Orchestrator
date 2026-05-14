from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from pm_bot.trading_core.authenticated_clob_preflight_models import (
    EXECUTION_MODE,
    L2_AUTH_HEADER_ROLES,
    MODE,
    NO_ORDER_BLOCKED_METHODS,
    STATUS_BLOCKED,
    STATUS_CHECKED,
    STATUS_MISSING,
    STATUS_MOCKED,
    STATUS_PRESENT_REDACTED,
    STATUS_SKIPPED,
    STATUS_VALID,
    AuthHeaderBoundaryCheck,
    AuthenticatedClobPreflightConfig,
    AuthenticatedClobPreflightResult,
    ClobBaseUrlValidation,
    LatestAuthenticatedClobPreflightStatus,
    LiveAuthReadinessBlocker,
    NoOrderAuthenticatedRequestPlan,
    authenticated_clob_preflight_safety_flags,
)
from pm_bot.trading_core.live_credentials_boundary import (
    PMBOT_POLYMARKET_CLOB_BASE_URL_ENV,
    build_redacted_l2_credential_presence_report,
    l2_credential_presence_blockers,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/authenticated_clob_preflight_057")

LIVE_AUTH_READINESS_BLOCKERS_CONTRACT = "pmbot_live_auth_readiness_blockers_057.v1"

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--wallet",
    "--signing",
    "--sign",
    "--order",
    "--submit",
    "--cancel",
    "--approve-live",
    "--derive-api-key",
    "--private-key",
    "--wallet-connect",
    "--balances",
    "--positions",
)


def authenticated_clob_preflight_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "authenticated_clob_preflight_057_result.json",
        "operator_md": root / "authenticated_clob_preflight_057_operator.md",
        "latest_status": root / "latest_authenticated_clob_preflight_status_057.json",
        "credential_presence": root / "redacted_l2_credential_presence_057.json",
        "clob_base_url_validation": root / "clob_base_url_validation_057.json",
        "auth_header_boundary_check": root / "auth_header_boundary_check_057.json",
        "no_order_authenticated_request_plan": root / "no_order_authenticated_request_plan_057.json",
        "blockers": root / "live_auth_readiness_blockers_057.json",
    }


def run_authenticated_clob_preflight(
    *,
    market: str = "BTC",
    dry_run: bool = True,
    mock_auth: bool = True,
    auth_presence_only: bool = False,
    no_order_auth_check: bool = True,
    clob_base_url: str = "",
    artifact_dir: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("authenticated CLOB preflight requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    active_environ = _active_environ(environ)
    configured_clob_base_url = clean_text(clob_base_url) or clean_text(
        active_environ.get(PMBOT_POLYMARKET_CLOB_BASE_URL_ENV)
    )
    paths = authenticated_clob_preflight_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    effective_no_order_auth_check = no_order_auth_check is True and auth_presence_only is not True

    config = AuthenticatedClobPreflightConfig(
        market=market_symbol,
        dry_run=True,
        mock_auth=mock_auth is True,
        auth_presence_only=auth_presence_only is True,
        no_order_auth_check=effective_no_order_auth_check,
        clob_base_url_configured=bool(configured_clob_base_url),
        artifact_dir=normalize_path(paths["root"]),
        generated_at=generated_at,
    ).to_dict()
    credential_presence = build_redacted_l2_credential_presence_report(
        environ=active_environ,
        generated_at=generated_at,
    )
    clob_validation = validate_clob_base_url(
        configured_clob_base_url,
        generated_at=generated_at,
    )
    auth_header_boundary = build_auth_header_boundary_check(
        credential_presence=credential_presence,
        clob_base_url_validation=clob_validation,
        auth_presence_only=auth_presence_only,
        generated_at=generated_at,
    )
    request_plan = build_no_order_authenticated_request_plan(
        credential_presence=credential_presence,
        clob_base_url_validation=clob_validation,
        auth_header_boundary_check=auth_header_boundary,
        no_order_auth_check=effective_no_order_auth_check,
        generated_at=generated_at,
    )
    blockers = build_live_auth_readiness_blockers(
        credential_presence=credential_presence,
        clob_base_url_validation=clob_validation,
        auth_header_boundary_check=auth_header_boundary,
        no_order_authenticated_request_plan=request_plan,
    )
    blockers_report = build_live_auth_readiness_blockers_report(
        blockers=blockers,
        generated_at=generated_at,
    )
    latest_status = LatestAuthenticatedClobPreflightStatus(
        market=market_symbol,
        status=_overall_status(
            credential_presence=credential_presence,
            clob_base_url_validation=clob_validation,
            auth_header_boundary_check=auth_header_boundary,
            no_order_authenticated_request_plan=request_plan,
        ),
        auth_presence_status=clean_text(credential_presence.get("status") or STATUS_MISSING),
        clob_base_url_status=clean_text(clob_validation.get("status") or STATUS_MISSING),
        auth_header_boundary_status=clean_text(auth_header_boundary.get("status") or STATUS_BLOCKED),
        no_order_auth_check_status=clean_text(request_plan.get("status") or STATUS_SKIPPED),
        blocker_count=len(blockers),
        blockers=tuple(blockers),
        artifact_path=path_refs["result"],
        latest_status_path=path_refs["latest_status"],
        operator_markdown_path=path_refs["operator_md"],
        credential_presence_path=path_refs["credential_presence"],
        clob_base_url_validation_path=path_refs["clob_base_url_validation"],
        auth_header_boundary_check_path=path_refs["auth_header_boundary_check"],
        no_order_authenticated_request_plan_path=path_refs["no_order_authenticated_request_plan"],
        blockers_path=path_refs["blockers"],
        generated_at=generated_at,
    ).to_dict()
    result = AuthenticatedClobPreflightResult(
        market=market_symbol,
        status=clean_text(latest_status.get("status")),
        config=config,
        credential_presence=credential_presence,
        clob_base_url_validation=clob_validation,
        auth_header_boundary_check=auth_header_boundary,
        no_order_authenticated_request_plan=request_plan,
        latest_status=latest_status,
        blockers=tuple(blockers),
        artifact_paths=path_refs,
        operator_summary=_operator_summary(latest_status),
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["credential_presence"], credential_presence)
    write_json(paths["clob_base_url_validation"], clob_validation)
    write_json(paths["auth_header_boundary_check"], auth_header_boundary)
    write_json(paths["no_order_authenticated_request_plan"], request_plan)
    write_json(paths["blockers"], blockers_report)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_authenticated_clob_preflight_markdown(result))
    return result


def validate_clob_base_url(value: Any, *, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    text = clean_text(value)
    if not text:
        return ClobBaseUrlValidation(
            status=STATUS_MISSING,
            base_url_present=False,
            scheme_status=STATUS_MISSING,
            host_status=STATUS_MISSING,
            unsafe_sensitive_value_detected=False,
            operator_safe_summary="PMBOT_POLYMARKET_CLOB_BASE_URL is missing; no CLOB request can be planned.",
            generated_at=generated_at,
        ).to_dict()
    lowered = text.lower()
    unsafe = any(marker in lowered for marker in ("private_key", "mnemonic", "seed_phrase", "secret", "token"))
    if unsafe:
        return ClobBaseUrlValidation(
            status="invalid_sensitive_looking_value_redacted",
            base_url_present=True,
            scheme_status=STATUS_BLOCKED,
            host_status=STATUS_BLOCKED,
            unsafe_sensitive_value_detected=True,
            operator_safe_summary="CLOB base URL looked sensitive and was not emitted.",
            generated_at=generated_at,
        ).to_dict()
    parsed = urlsplit(text)
    if parsed.scheme not in {"http", "https"}:
        return ClobBaseUrlValidation(
            status="invalid_scheme",
            base_url_present=True,
            scheme_status="invalid",
            host_status=STATUS_SKIPPED,
            unsafe_sensitive_value_detected=False,
            operator_safe_summary="CLOB base URL must use http or https.",
            generated_at=generated_at,
        ).to_dict()
    if not parsed.netloc:
        return ClobBaseUrlValidation(
            status="invalid_missing_host",
            base_url_present=True,
            scheme_status="valid",
            host_status="missing",
            unsafe_sensitive_value_detected=False,
            operator_safe_summary="CLOB base URL is missing a host.",
            generated_at=generated_at,
        ).to_dict()
    return ClobBaseUrlValidation(
        status=STATUS_VALID,
        base_url_present=True,
        scheme_status="valid",
        host_status="present_redacted",
        unsafe_sensitive_value_detected=False,
        operator_safe_summary="CLOB base URL shape is valid; value remains redacted in artifacts.",
        generated_at=generated_at,
    ).to_dict()


def build_auth_header_boundary_check(
    *,
    credential_presence: Mapping[str, Any],
    clob_base_url_validation: Mapping[str, Any],
    auth_presence_only: bool,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if auth_presence_only is True:
        status = STATUS_SKIPPED
        checked = False
    elif (
        credential_presence.get("status") == STATUS_PRESENT_REDACTED
        and credential_presence.get("unsafe_raw_value_detected") is not True
        and clob_base_url_validation.get("status") == STATUS_VALID
    ):
        status = STATUS_CHECKED
        checked = True
    else:
        status = STATUS_BLOCKED
        checked = True
    return AuthHeaderBoundaryCheck(
        status=status,
        auth_header_boundary_checked=checked,
        credential_presence_status=clean_text(credential_presence.get("status") or STATUS_MISSING),
        clob_base_url_status=clean_text(clob_base_url_validation.get("status") or STATUS_MISSING),
        required_header_roles=L2_AUTH_HEADER_ROLES,
        generated_at=generated_at,
    ).to_dict()


def build_no_order_authenticated_request_plan(
    *,
    credential_presence: Mapping[str, Any],
    clob_base_url_validation: Mapping[str, Any],
    auth_header_boundary_check: Mapping[str, Any],
    no_order_auth_check: bool,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if no_order_auth_check is not True:
        status = STATUS_SKIPPED
        performed = False
    elif (
        credential_presence.get("status") == STATUS_PRESENT_REDACTED
        and credential_presence.get("unsafe_raw_value_detected") is not True
        and clob_base_url_validation.get("status") == STATUS_VALID
        and auth_header_boundary_check.get("status") == STATUS_CHECKED
    ):
        status = STATUS_MOCKED
        performed = True
    else:
        status = STATUS_BLOCKED
        performed = True
    return NoOrderAuthenticatedRequestPlan(
        status=status,
        no_order_auth_check_performed=performed,
        request_method="GET",
        endpoint_path="/auth/no-order-boundary/mock-get",
        clob_base_url_status=clean_text(clob_base_url_validation.get("status") or STATUS_MISSING),
        credential_presence_status=clean_text(credential_presence.get("status") or STATUS_MISSING),
        authenticated_request_performed=False,
        generated_at=generated_at,
    ).to_dict()


def build_live_auth_readiness_blockers(
    *,
    credential_presence: Mapping[str, Any],
    clob_base_url_validation: Mapping[str, Any],
    auth_header_boundary_check: Mapping[str, Any],
    no_order_authenticated_request_plan: Mapping[str, Any],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if clob_base_url_validation.get("status") != STATUS_VALID:
        blockers.append(
            _blocker(
                "CLOB_BASE_URL_BLOCKED",
                "clob_config",
                "CLOB base URL is missing or invalid; authenticated CLOB readiness remains blocked.",
            )
        )
    if clob_base_url_validation.get("unsafe_sensitive_value_detected") is True:
        blockers.append(
            _blocker(
                "CLOB_BASE_URL_LOOKED_SENSITIVE",
                "clob_config",
                "CLOB base URL input looked sensitive and was redacted.",
            )
        )
    for reason in l2_credential_presence_blockers(credential_presence):
        blockers.append(_blocker("L2_CREDENTIAL_PRESENCE_BLOCKED", "l2_auth_boundary", reason))
    if auth_header_boundary_check.get("status") != STATUS_CHECKED:
        blockers.append(
            _blocker(
                "AUTH_HEADER_BOUNDARY_BLOCKED",
                "l2_auth_boundary",
                "Auth header boundary is not checked with valid redacted L2 markers and CLOB base URL.",
            )
        )
    if no_order_authenticated_request_plan.get("status") != STATUS_MOCKED:
        blockers.append(
            _blocker(
                "NO_ORDER_AUTH_CHECK_BLOCKED",
                "l2_auth_boundary",
                "Mocked no-order authenticated GET plan is blocked or skipped.",
            )
        )
    blockers.extend(
        [
            _blocker(
                "ORDER_SUBMISSION_BLOCKED",
                "execution_boundary",
                "Order submission remains unavailable in task 057.",
            ),
            _blocker(
                "ORDER_CANCELLATION_BLOCKED",
                "execution_boundary",
                "Order cancellation remains unavailable in task 057.",
            ),
            _blocker(
                "SIGNING_BLOCKED",
                "signing_boundary",
                "L1 auth, EIP-712 signing, HMAC generation, and signed payload generation remain unavailable.",
            ),
            _blocker(
                "WALLET_CONNECTION_BLOCKED",
                "wallet_boundary",
                "Wallet connection, private-key reads, and wallet spend remain unavailable.",
            ),
            _blocker(
                "BALANCE_READ_BLOCKED",
                "account_boundary",
                "Balance reads remain unavailable in task 057.",
            ),
            _blocker(
                "POSITION_READ_BLOCKED",
                "account_boundary",
                "Position reads remain unavailable in task 057.",
            ),
            _blocker(
                "LIVE_EXECUTION_BLOCKED",
                "live_approval_boundary",
                "Live execution is not approved and allowed_for_live remains false.",
            ),
        ]
    )
    return _dedupe_blockers(blockers)


def build_live_auth_readiness_blockers_report(
    *,
    blockers: Sequence[Mapping[str, Any]],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": LIVE_AUTH_READINESS_BLOCKERS_CONTRACT,
        "task_id": "ORCH-PMBOT-TRADING-MVP-057-AUTHENTICATED-NO-ORDER-CLOB-API-PREFLIGHT-REDACTED-BOUNDARY",
        "status": "live_auth_readiness_blocked",
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "blockers": [dict(row) for row in blockers],
        "generated_at": generated_at,
    }
    value.update(
        authenticated_clob_preflight_safety_flags(
            auth_presence_check_performed=False,
            auth_header_boundary_checked=False,
            no_order_auth_check_performed=False,
        )
    )
    return value


def render_authenticated_clob_preflight_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    request_status = _authenticated_request_summary(value)
    return "\n".join(
        [
            "Authenticated CLOB preflight completed.",
            f"Market: {clean_text(value.get('market'))}",
            "Mode: preflight / review-only",
            f"Auth presence: {clean_text(value.get('auth_presence_status') or value.get('auth_presence') or STATUS_MISSING)}",
            f"CLOB base URL: {clean_text(value.get('clob_base_url_status') or value.get('clob_base_url') or STATUS_MISSING)}",
            f"Auth header boundary: {clean_text(value.get('auth_header_boundary_status') or value.get('auth_header_boundary') or STATUS_BLOCKED)}",
            f"Authenticated request: {request_status}",
            "Order submission: blocked",
            "Signing: blocked",
            "Wallet: blocked",
            "Live execution: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_authenticated_clob_preflight_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    status = dict(value.get("latest_status", {}))
    credential_presence = dict(value.get("credential_presence", {}))
    clob = dict(value.get("clob_base_url_validation", {}))
    auth_header = dict(value.get("auth_header_boundary_check", {}))
    request_plan = dict(value.get("no_order_authenticated_request_plan", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Authenticated No-Order CLOB API Preflight 057",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market')}`",
        "- Mode: `preflight / review-only`",
        "- execution_mode: `preflight`",
        "- review_only: `true`",
        "- preflight_only: `true`",
        "",
        "## Auth Presence",
        "",
        f"- Auth presence status: `{credential_presence.get('status')}`",
        f"- Auth presence checked: `{str(credential_presence.get('auth_presence_check_performed') is True).lower()}`",
        f"- L2 markers configured: `{credential_presence.get('configured_count', 0)}`",
        f"- L2 markers missing: `{credential_presence.get('missing_count', 0)}`",
        f"- Unsafe raw marker detected: `{str(credential_presence.get('unsafe_raw_value_detected') is True).lower()}`",
        "- Credential values: `redacted_or_missing_only`",
        "- Raw credential values stored: `false`",
        "",
        "## CLOB Base URL",
        "",
        f"- CLOB base URL status: `{clob.get('status')}`",
        f"- CLOB base URL present: `{str(clob.get('base_url_present') is True).lower()}`",
        "- CLOB base URL value emitted: `false`",
        "",
        "## No-Order Boundary",
        "",
        f"- Auth header boundary status: `{auth_header.get('status')}`",
        f"- Auth header boundary checked: `{str(auth_header.get('auth_header_boundary_checked') is True).lower()}`",
        f"- No-order auth check status: `{request_plan.get('status')}`",
        f"- No-order auth check performed: `{str(request_plan.get('no_order_auth_check_performed') is True).lower()}`",
        "- Authenticated request performed: `false`",
        "- Allowed methods in plan: `GET`",
        "- Blocked methods in plan: `POST, PUT, PATCH, DELETE`",
        "",
        "## Safety",
        "",
        "- order submission blocked",
        "- order cancellation blocked",
        "- signing blocked",
        "- wallet connection blocked",
        "- balances blocked",
        "- positions blocked",
        "- live execution blocked",
        "- private_key_read: `false`",
        "- l1_auth_attempted: `false`",
        "- api_key_derivation_attempted: `false`",
        "- signed payload generated: `false`",
        "- authenticated_polymarket_enabled: `false`",
        "- live_connector_enabled: `false`",
        "- allowed_for_live: `false`",
        "- resolved_blocker_count: `0`",
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
        "",
        "## Next Operator Action",
        "",
        "- configure redacted L2 presence markers or review blockers; no live order available",
        f"- Latest status path: `{status.get('latest_status_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "authenticated CLOB preflight is review-only; unsupported live/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _overall_status(
    *,
    credential_presence: Mapping[str, Any],
    clob_base_url_validation: Mapping[str, Any],
    auth_header_boundary_check: Mapping[str, Any],
    no_order_authenticated_request_plan: Mapping[str, Any],
) -> str:
    if (
        credential_presence.get("status") == STATUS_PRESENT_REDACTED
        and credential_presence.get("unsafe_raw_value_detected") is not True
        and clob_base_url_validation.get("status") == STATUS_VALID
        and auth_header_boundary_check.get("status") == STATUS_CHECKED
        and no_order_authenticated_request_plan.get("status") == STATUS_MOCKED
    ):
        return "authenticated_clob_preflight_completed_live_blocked"
    return "authenticated_clob_preflight_completed_fail_closed"


def _operator_summary(status: Mapping[str, Any]) -> str:
    return (
        "Authenticated CLOB preflight completed as review-only. Auth presence="
        + clean_text(status.get("auth_presence_status"))
        + "; CLOB base URL="
        + clean_text(status.get("clob_base_url_status"))
        + "; order submission, signing, wallet use, balances, positions, and live execution are blocked."
    )


def _authenticated_request_summary(status: Mapping[str, Any]) -> str:
    if status.get("no_order_auth_check_status") == STATUS_MOCKED:
        return "mocked/no_order_get_checked"
    return "skipped"


def _blocker(blocker_id: str, category: str, reason: str) -> dict[str, Any]:
    return LiveAuthReadinessBlocker(
        blocker_id=clean_text(blocker_id),
        blocker_category=clean_text(category),
        severity="critical",
        reason=clean_text(reason),
    ).to_dict()


def _dedupe_blockers(blockers: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for blocker in blockers:
        row = dict(blocker)
        key = (clean_text(row.get("blocker_id")), clean_text(row.get("reason")))
        if key not in seen:
            seen.add(key)
            result.append(row)
    return result


def _active_environ(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    if environ is not None:
        return environ
    import os

    return os.environ
