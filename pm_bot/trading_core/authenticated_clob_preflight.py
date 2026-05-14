from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from pm_bot.trading_core.authenticated_clob_preflight_models import (
    EXECUTION_MODE,
    L2_AUTH_HEADER_ROLES,
    MODE,
    NO_ORDER_BLOCKED_METHODS,
    STATUS_REAL_GET_CHECKED,
    LatestNoOrderAuthenticatedGetStatus,
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
    NoOrderAuthenticatedGetConfig,
    NoOrderAuthenticatedGetResult,
    NoOrderAuthenticatedRequestPlan,
    RealAuthReadOnlyOptInStatus,
    SafeNoOrderEndpointValidation,
    authenticated_clob_preflight_safety_flags,
    no_order_authenticated_get_safety_flags,
)
from pm_bot.trading_core.live_credentials_boundary import (
    PMBOT_POLYMARKET_CLOB_BASE_URL_ENV,
    build_redacted_l2_marker_presence_report,
    build_redacted_l2_credential_presence_report,
    build_unsafe_l2_marker_detection_report,
    l2_credential_presence_blockers,
    l2_marker_presence_blockers,
    validate_safe_clob_base_url_config,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, mapping_rows, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/authenticated_clob_preflight_057")
DEFAULT_CLOB_L2_MARKER_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058")
DEFAULT_NO_ORDER_AUTH_GET_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059")

LIVE_AUTH_READINESS_BLOCKERS_CONTRACT = "pmbot_live_auth_readiness_blockers_057.v1"
CLOB_L2_MARKER_PREFLIGHT_RESULT_CONTRACT = "pmbot_clob_l2_marker_preflight_result_058.v1"
CLOB_L2_MARKER_STATUS_CONTRACT = "pmbot_latest_clob_l2_marker_preflight_status_058.v1"
NO_ORDER_AUTH_BOUNDARY_PLAN_CONTRACT = "pmbot_no_order_auth_boundary_plan_058.v1"
CLOB_L2_MARKER_BLOCKERS_CONTRACT = "pmbot_clob_l2_marker_blockers_058.v1"
TASK_ID_058 = "ORCH-PMBOT-TRADING-MVP-058-CLOB-BASE-URL-AND-REDACTED-L2-MARKER-PREFLIGHT"
TASK_ID_059 = "ORCH-PMBOT-TRADING-MVP-059-OPTIONAL-NO-ORDER-AUTHENTICATED-GET-PREFLIGHT"

PMBOT_ALLOW_REAL_NO_ORDER_AUTH_GET_ENV = "PMBOT_ALLOW_REAL_NO_ORDER_AUTH_GET"

NO_ORDER_AUTH_GET_REQUEST_PLAN_CONTRACT = "pmbot_no_order_auth_get_request_plan_059.v1"
NO_ORDER_AUTH_GET_RESPONSE_EVIDENCE_CONTRACT = "pmbot_no_order_auth_get_response_evidence_059.v1"
NO_ORDER_AUTH_GET_BLOCKERS_CONTRACT = "pmbot_no_order_auth_get_blockers_059.v1"
NO_ORDER_AUTH_GET_BLOCKER_CONTRACT = "pmbot_no_order_auth_get_blocker_059.v1"

NO_ORDER_AUTH_GET_MOCK_ENDPOINT = "/auth/no-order-boundary/mock-get"
SAFE_NO_ORDER_AUTH_GET_ENDPOINT_ALLOWLIST = (NO_ORDER_AUTH_GET_MOCK_ENDPOINT,)
REAL_NO_ORDER_AUTH_GET_ENDPOINT_ALLOWLIST: tuple[str, ...] = ()
NO_ORDER_AUTH_GET_ENDPOINT_DENYLIST_TERMS = (
    "order",
    "cancel",
    "balance",
    "position",
    "fill",
    "trade",
    "wallet",
    "allowance",
    "approval",
    "approve",
    "auth/api-key",
    "auth/derive-api-key",
    "heartbeat",
)

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


def clob_l2_marker_preflight_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_CLOB_L2_MARKER_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "clob_l2_marker_preflight_058_result.json",
        "operator_md": root / "clob_l2_marker_preflight_058_operator.md",
        "latest_status": root / "latest_clob_l2_marker_preflight_status_058.json",
        "clob_base_url_config": root / "clob_base_url_config_058.json",
        "redacted_l2_marker_presence": root / "redacted_l2_marker_presence_058.json",
        "unsafe_l2_marker_detection": root / "unsafe_l2_marker_detection_058.json",
        "no_order_auth_boundary_plan": root / "no_order_auth_boundary_plan_058.json",
        "blockers": root / "clob_l2_marker_blockers_058.json",
    }


def no_order_auth_get_preflight_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_NO_ORDER_AUTH_GET_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "no_order_auth_get_preflight_059_result.json",
        "operator_md": root / "no_order_auth_get_preflight_059_operator.md",
        "latest_status": root / "latest_no_order_auth_get_preflight_status_059.json",
        "request_plan": root / "no_order_auth_get_request_plan_059.json",
        "endpoint_validation": root / "no_order_auth_get_endpoint_validation_059.json",
        "response_evidence": root / "no_order_auth_get_response_evidence_059.json",
        "blockers": root / "no_order_auth_get_blockers_059.json",
    }


def run_clob_l2_marker_preflight(
    *,
    market: str = "BTC",
    dry_run: bool = True,
    mock_auth: bool = True,
    no_order_auth_check: bool = True,
    clob_base_url: str = "",
    artifact_dir: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("CLOB L2 marker preflight requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    active_environ = _active_environ(environ)
    configured_clob_base_url = clean_text(clob_base_url) or clean_text(
        active_environ.get(PMBOT_POLYMARKET_CLOB_BASE_URL_ENV)
    )
    paths = clob_l2_marker_preflight_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    clob_config = validate_safe_clob_base_url_config(
        configured_clob_base_url,
        environ=active_environ,
        generated_at=generated_at,
    )
    marker_presence = build_redacted_l2_marker_presence_report(
        environ=active_environ,
        generated_at=generated_at,
    )
    unsafe_detection = build_unsafe_l2_marker_detection_report(
        marker_presence,
        generated_at=generated_at,
    )
    auth_plan = build_no_order_auth_boundary_plan_058(
        clob_base_url_config=clob_config,
        marker_presence=marker_presence,
        mock_auth=mock_auth,
        no_order_auth_check=no_order_auth_check,
        generated_at=generated_at,
    )
    blockers = build_clob_l2_marker_blockers_058(
        clob_base_url_config=clob_config,
        marker_presence=marker_presence,
        unsafe_marker_detection=unsafe_detection,
        no_order_auth_boundary_plan=auth_plan,
    )
    blockers_report = build_clob_l2_marker_blockers_report_058(
        blockers=blockers,
        generated_at=generated_at,
    )
    status = _clob_l2_marker_overall_status(
        clob_base_url_config=clob_config,
        marker_presence=marker_presence,
        no_order_auth_boundary_plan=auth_plan,
    )
    latest_status = {
        "contract_version": CLOB_L2_MARKER_STATUS_CONTRACT,
        "task_id": TASK_ID_058,
        "market": market_symbol,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "clob_base_url_configured": clob_config.get("clob_base_url_configured") is True,
        "clob_base_url_status": clean_text(clob_config.get("status") or STATUS_MISSING),
        "clob_base_url_valid": clob_config.get("clob_base_url_valid") is True,
        "clob_base_url_missing": clob_config.get("clob_base_url_missing") is True,
        "clob_base_url_invalid": clob_config.get("clob_base_url_invalid") is True,
        "public_clob_base_url": clean_text(clob_config.get("public_clob_base_url")),
        "is_production_clob_base_url": clob_config.get("is_production_clob_base_url") is True,
        "auth_marker_presence_detected": marker_presence.get("auth_marker_presence_detected") is True,
        "l2_marker_presence_status": clean_text(marker_presence.get("status") or STATUS_MISSING),
        "l2_marker_set_complete": marker_presence.get("marker_set_complete") is True,
        "l2_marker_configured_count": int(marker_presence.get("configured_count", 0) or 0),
        "l2_marker_missing_count": int(marker_presence.get("missing_count", 0) or 0),
        "unsafe_raw_value_detected": unsafe_detection.get("unsafe_raw_value_detected") is True,
        "auth_boundary_mock_checked": auth_plan.get("auth_boundary_mock_checked") is True,
        "no_order_auth_plan_ready": auth_plan.get("no_order_auth_plan_ready") is True,
        "no_order_auth_check_status": clean_text(auth_plan.get("status") or STATUS_BLOCKED),
        "authenticated_request": "skipped_by_default",
        "authenticated_request_skipped_by_default": True,
        "authenticated_request_performed": False,
        "order_submission": "blocked",
        "order_cancellation": "blocked",
        "signing": "blocked",
        "wallet": "blocked",
        "balances": "blocked",
        "positions": "blocked",
        "live_execution": "blocked",
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "blockers": blockers,
        "top_blocker_reasons": [clean_text(row.get("reason")) for row in blockers[:8]],
        "artifact_path": path_refs["result"],
        "latest_status_path": path_refs["latest_status"],
        "operator_markdown_path": path_refs["operator_md"],
        "clob_base_url_config_path": path_refs["clob_base_url_config"],
        "redacted_l2_marker_presence_path": path_refs["redacted_l2_marker_presence"],
        "unsafe_l2_marker_detection_path": path_refs["unsafe_l2_marker_detection"],
        "no_order_auth_boundary_plan_path": path_refs["no_order_auth_boundary_plan"],
        "blockers_path": path_refs["blockers"],
        "next_operator_action": "configure safe CLOB base URL and redacted L2 marker variables; no live order available",
        "generated_at": generated_at,
    }
    latest_status.update(
        authenticated_clob_preflight_safety_flags(
            auth_presence_check_performed=True,
            auth_header_boundary_checked=auth_plan.get("auth_boundary_mock_checked") is True,
            no_order_auth_check_performed=auth_plan.get("no_order_auth_check_performed") is True,
        )
    )
    result = {
        "contract_version": CLOB_L2_MARKER_PREFLIGHT_RESULT_CONTRACT,
        "task_id": TASK_ID_058,
        "market": market_symbol,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "dry_run": True,
        "mock_auth": mock_auth is True,
        "clob_base_url_config": clob_config,
        "redacted_l2_marker_presence": marker_presence,
        "unsafe_l2_marker_detection": unsafe_detection,
        "no_order_auth_boundary_plan": auth_plan,
        "latest_status": latest_status,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "clob_base_url_configured": latest_status["clob_base_url_configured"],
        "clob_base_url_valid": latest_status["clob_base_url_valid"],
        "auth_marker_presence_detected": latest_status["auth_marker_presence_detected"],
        "l2_marker_set_complete": latest_status["l2_marker_set_complete"],
        "unsafe_raw_value_detected": latest_status["unsafe_raw_value_detected"],
        "auth_boundary_mock_checked": latest_status["auth_boundary_mock_checked"],
        "no_order_auth_plan_ready": latest_status["no_order_auth_plan_ready"],
        "authenticated_request_skipped_by_default": True,
        "artifact_paths": path_refs,
        "operator_summary": _clob_l2_marker_operator_summary(latest_status),
        "generated_at": generated_at,
    }
    result.update(
        authenticated_clob_preflight_safety_flags(
            auth_presence_check_performed=True,
            auth_header_boundary_checked=auth_plan.get("auth_boundary_mock_checked") is True,
            no_order_auth_check_performed=auth_plan.get("no_order_auth_check_performed") is True,
        )
    )
    write_json(paths["clob_base_url_config"], clob_config)
    write_json(paths["redacted_l2_marker_presence"], marker_presence)
    write_json(paths["unsafe_l2_marker_detection"], unsafe_detection)
    write_json(paths["no_order_auth_boundary_plan"], auth_plan)
    write_json(paths["blockers"], blockers_report)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_clob_l2_marker_preflight_markdown(result))
    return result


def run_no_order_auth_get_preflight(
    *,
    market: str = "BTC",
    dry_run: bool = True,
    no_order_auth_get_requested: bool = False,
    real_auth_read_only_requested: bool = False,
    clob_base_url: str = "",
    endpoint_path: str = NO_ORDER_AUTH_GET_MOCK_ENDPOINT,
    artifact_dir: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("no-order authenticated GET preflight requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    active_environ = _active_environ(environ)
    configured_clob_base_url = clean_text(clob_base_url) or clean_text(
        active_environ.get(PMBOT_POLYMARKET_CLOB_BASE_URL_ENV)
    )
    paths = no_order_auth_get_preflight_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    real_opt_in_present = _env_true(active_environ.get(PMBOT_ALLOW_REAL_NO_ORDER_AUTH_GET_ENV))
    endpoint_validation = validate_safe_no_order_auth_get_endpoint(
        endpoint_path,
        request_method="GET",
        real_auth_read_only_requested=real_auth_read_only_requested,
        generated_at=generated_at,
    )
    opt_in_status = build_real_auth_read_only_opt_in_status(
        real_auth_read_only_requested=real_auth_read_only_requested,
        real_auth_read_only_opt_in_present=real_opt_in_present,
        generated_at=generated_at,
    )
    config = NoOrderAuthenticatedGetConfig(
        market=market_symbol,
        dry_run=True,
        no_order_auth_get_requested=no_order_auth_get_requested is True,
        real_auth_read_only_requested=real_auth_read_only_requested is True,
        real_auth_read_only_opt_in_present=real_opt_in_present,
        request_method="GET",
        endpoint_path_sanitized=clean_text(endpoint_validation.get("endpoint_path_sanitized")),
        artifact_dir=normalize_path(paths["root"]),
        generated_at=generated_at,
    ).to_dict()
    request_plan = build_no_order_auth_get_request_plan_059(
        no_order_auth_get_requested=no_order_auth_get_requested,
        real_auth_read_only_requested=real_auth_read_only_requested,
        real_auth_read_only_opt_in_status=opt_in_status,
        endpoint_validation=endpoint_validation,
        clob_base_url=configured_clob_base_url,
        generated_at=generated_at,
    )
    response_evidence = build_no_order_auth_get_response_evidence_059(
        request_plan=request_plan,
        generated_at=generated_at,
    )
    blockers = build_no_order_auth_get_blockers_059(
        no_order_auth_get_requested=no_order_auth_get_requested,
        real_auth_read_only_requested=real_auth_read_only_requested,
        real_auth_read_only_opt_in_status=opt_in_status,
        endpoint_validation=endpoint_validation,
        request_plan=request_plan,
    )
    blockers_report = build_no_order_auth_get_blockers_report_059(
        blockers=blockers,
        generated_at=generated_at,
    )
    latest_status = LatestNoOrderAuthenticatedGetStatus(
        market=market_symbol,
        status=_no_order_auth_get_overall_status(request_plan),
        no_order_auth_get_status=clean_text(request_plan.get("status") or STATUS_SKIPPED),
        no_order_auth_get_requested=no_order_auth_get_requested is True,
        real_auth_read_only_requested=real_auth_read_only_requested is True,
        real_auth_read_only_opt_in_present=real_opt_in_present,
        real_authenticated_get_performed=False,
        request_method="GET",
        endpoint_path_sanitized=clean_text(endpoint_validation.get("endpoint_path_sanitized")),
        endpoint_safe_for_no_order_check=endpoint_validation.get("endpoint_safe_for_no_order_check") is True,
        endpoint_blocked_reason=clean_text(endpoint_validation.get("endpoint_blocked_reason")),
        status_code=None,
        auth_used=False,
        blocker_count=len(blockers),
        blockers=tuple(blockers),
        artifact_path=path_refs["result"],
        latest_status_path=path_refs["latest_status"],
        operator_markdown_path=path_refs["operator_md"],
        request_plan_path=path_refs["request_plan"],
        endpoint_validation_path=path_refs["endpoint_validation"],
        response_evidence_path=path_refs["response_evidence"] if response_evidence else "",
        blockers_path=path_refs["blockers"],
        generated_at=generated_at,
    ).to_dict()
    result = NoOrderAuthenticatedGetResult(
        market=market_symbol,
        status=clean_text(latest_status.get("status")),
        config=config,
        real_auth_read_only_opt_in_status=opt_in_status,
        safe_no_order_endpoint_validation=endpoint_validation,
        request_plan=request_plan,
        response_evidence=response_evidence,
        latest_status=latest_status,
        blockers=tuple(blockers),
        artifact_paths=path_refs,
        operator_summary=_no_order_auth_get_operator_summary(latest_status),
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["request_plan"], request_plan)
    write_json(paths["endpoint_validation"], endpoint_validation)
    if response_evidence:
        write_json(paths["response_evidence"], response_evidence)
    write_json(paths["blockers"], blockers_report)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_no_order_auth_get_preflight_markdown(result))
    return result


def run_authenticated_clob_preflight(
    *,
    market: str = "BTC",
    dry_run: bool = True,
    mock_auth: bool = True,
    auth_presence_only: bool = False,
    no_order_auth_check: bool = True,
    no_order_auth_get_requested: bool = False,
    real_auth_read_only_requested: bool = False,
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
    clob_l2_marker_preflight = run_clob_l2_marker_preflight(
        market=market_symbol,
        dry_run=True,
        mock_auth=mock_auth is True,
        no_order_auth_check=effective_no_order_auth_check,
        clob_base_url=configured_clob_base_url,
        artifact_dir=_derived_clob_l2_marker_artifact_dir(artifact_dir),
        environ=active_environ,
        generated_at=generated_at,
    )
    clob_l2_marker_summary = _clob_l2_marker_status_summary(
        dict(clob_l2_marker_preflight.get("latest_status", {}))
    )
    no_order_auth_get_preflight = run_no_order_auth_get_preflight(
        market=market_symbol,
        dry_run=True,
        no_order_auth_get_requested=no_order_auth_get_requested is True,
        real_auth_read_only_requested=real_auth_read_only_requested is True,
        clob_base_url=configured_clob_base_url,
        artifact_dir=_derived_no_order_auth_get_artifact_dir(artifact_dir),
        environ=active_environ,
        generated_at=generated_at,
    )
    no_order_auth_get_summary = _no_order_auth_get_status_summary(
        dict(no_order_auth_get_preflight.get("latest_status", {}))
    )

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
    latest_status["clob_l2_marker_preflight_status_summary"] = clob_l2_marker_summary
    latest_status["no_order_auth_get_preflight_status_summary"] = no_order_auth_get_summary
    latest_status["latest_clob_l2_marker_preflight_status_path"] = clean_text(
        clob_l2_marker_summary.get("latest_status_path")
    )
    latest_status["latest_no_order_auth_get_preflight_status_path"] = clean_text(
        no_order_auth_get_summary.get("latest_status_path")
    )
    latest_status["auth_marker_presence_detected"] = (
        clob_l2_marker_summary.get("auth_marker_presence_detected") is True
    )
    latest_status["clob_base_url_configured"] = clob_l2_marker_summary.get("clob_base_url_configured") is True
    latest_status["auth_boundary_mock_checked"] = (
        clob_l2_marker_summary.get("auth_boundary_mock_checked") is True
    )
    latest_status["no_order_auth_plan_ready"] = (
        clob_l2_marker_summary.get("no_order_auth_plan_ready") is True
    )
    latest_status["no_order_auth_get_requested"] = (
        no_order_auth_get_summary.get("no_order_auth_get_requested") is True
    )
    latest_status["real_auth_read_only_requested"] = (
        no_order_auth_get_summary.get("real_auth_read_only_requested") is True
    )
    latest_status["real_auth_read_only_opt_in_present"] = (
        no_order_auth_get_summary.get("real_auth_read_only_opt_in_present") is True
    )
    latest_status["no_order_auth_get_status"] = clean_text(
        no_order_auth_get_summary.get("no_order_auth_get_status") or STATUS_SKIPPED
    )
    latest_status["real_authenticated_get_performed"] = (
        no_order_auth_get_summary.get("real_authenticated_get_performed") is True
    )
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
    result["clob_l2_marker_preflight_status_summary"] = clob_l2_marker_summary
    result["no_order_auth_get_preflight_status_summary"] = no_order_auth_get_summary
    result["latest_clob_l2_marker_preflight_status_path"] = clean_text(
        clob_l2_marker_summary.get("latest_status_path")
    )
    result["latest_no_order_auth_get_preflight_status_path"] = clean_text(
        no_order_auth_get_summary.get("latest_status_path")
    )
    result["auth_marker_presence_detected"] = latest_status["auth_marker_presence_detected"]
    result["clob_base_url_configured"] = latest_status["clob_base_url_configured"]
    result["auth_boundary_mock_checked"] = latest_status["auth_boundary_mock_checked"]
    result["no_order_auth_plan_ready"] = latest_status["no_order_auth_plan_ready"]
    result["artifact_paths"]["clob_l2_marker_preflight"] = clean_text(
        clob_l2_marker_summary.get("artifact_path")
    )
    result["artifact_paths"]["no_order_auth_get_preflight"] = clean_text(
        no_order_auth_get_summary.get("artifact_path")
    )
    result["no_order_auth_get_requested"] = latest_status["no_order_auth_get_requested"]
    result["real_auth_read_only_requested"] = latest_status["real_auth_read_only_requested"]
    result["real_auth_read_only_opt_in_present"] = latest_status["real_auth_read_only_opt_in_present"]
    result["no_order_auth_get_status"] = latest_status["no_order_auth_get_status"]
    result["real_authenticated_get_performed"] = latest_status["real_authenticated_get_performed"]

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


def build_real_auth_read_only_opt_in_status(
    *,
    real_auth_read_only_requested: bool,
    real_auth_read_only_opt_in_present: bool,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if real_auth_read_only_requested is not True:
        status = STATUS_SKIPPED
        blocker_reason = ""
    elif real_auth_read_only_opt_in_present is True:
        status = STATUS_CHECKED
        blocker_reason = ""
    else:
        status = STATUS_BLOCKED
        blocker_reason = "real_no_order_auth_get_not_enabled"
    return RealAuthReadOnlyOptInStatus(
        status=status,
        real_auth_read_only_requested=real_auth_read_only_requested is True,
        real_auth_read_only_opt_in_present=real_auth_read_only_opt_in_present is True,
        env_var_name=PMBOT_ALLOW_REAL_NO_ORDER_AUTH_GET_ENV,
        blocker_reason=blocker_reason,
        generated_at=generated_at,
    ).to_dict()


def validate_safe_no_order_auth_get_endpoint(
    endpoint_path: str = NO_ORDER_AUTH_GET_MOCK_ENDPOINT,
    *,
    request_method: str = "GET",
    real_auth_read_only_requested: bool = False,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    method = clean_text(request_method).upper() or "GET"
    raw_endpoint = clean_text(endpoint_path)
    sanitized = _sanitize_endpoint_path(endpoint_path)
    raw_parsed = urlsplit(raw_endpoint)
    has_query_or_fragment = bool(raw_parsed.query or raw_parsed.fragment or "?" in raw_endpoint or "#" in raw_endpoint)
    lowered = sanitized.lower().strip("/")
    forbidden_terms = _forbidden_endpoint_terms_for_path(lowered)
    allowlist = REAL_NO_ORDER_AUTH_GET_ENDPOINT_ALLOWLIST if real_auth_read_only_requested else SAFE_NO_ORDER_AUTH_GET_ENDPOINT_ALLOWLIST
    allowlist_match = sanitized in allowlist
    blocked_reason = ""
    safe = True
    if method != "GET":
        safe = False
        blocked_reason = "non_get_method_blocked"
    elif not sanitized.startswith("/"):
        safe = False
        blocked_reason = "endpoint_path_must_be_relative_absolute_path"
    elif has_query_or_fragment:
        safe = False
        blocked_reason = "query_or_fragment_blocked"
    elif forbidden_terms:
        safe = False
        blocked_reason = "forbidden_endpoint:" + ",".join(forbidden_terms)
    elif not allowlist_match:
        safe = False
        blocked_reason = (
            "no_clearly_safe_authenticated_get_endpoint"
            if real_auth_read_only_requested
            else "endpoint_not_in_no_order_allowlist"
        )
    status = STATUS_CHECKED if safe else STATUS_BLOCKED
    return SafeNoOrderEndpointValidation(
        status=status,
        request_method=method,
        endpoint_path_sanitized=sanitized,
        endpoint_safe_for_no_order_check=safe,
        endpoint_blocked_reason=blocked_reason,
        forbidden_terms_detected=forbidden_terms,
        allowlist_match=allowlist_match,
        real_auth_read_only_requested=real_auth_read_only_requested is True,
        generated_at=generated_at,
    ).to_dict()


def build_no_order_auth_get_request_plan_059(
    *,
    no_order_auth_get_requested: bool,
    real_auth_read_only_requested: bool,
    real_auth_read_only_opt_in_status: Mapping[str, Any],
    endpoint_validation: Mapping[str, Any],
    clob_base_url: str,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    endpoint_safe = endpoint_validation.get("endpoint_safe_for_no_order_check") is True
    opt_in_present = real_auth_read_only_opt_in_status.get("real_auth_read_only_opt_in_present") is True
    if no_order_auth_get_requested is not True and real_auth_read_only_requested is True:
        status = STATUS_BLOCKED
        blocked_reason = "real_auth_read_only_requires_no_order_auth_get"
    elif no_order_auth_get_requested is not True:
        status = STATUS_SKIPPED
        blocked_reason = ""
    elif real_auth_read_only_requested is not True:
        status = STATUS_MOCKED
        blocked_reason = ""
    elif opt_in_present is not True:
        status = STATUS_BLOCKED
        blocked_reason = "real_no_order_auth_get_not_enabled"
    elif endpoint_safe is not True:
        status = STATUS_BLOCKED
        blocked_reason = clean_text(endpoint_validation.get("endpoint_blocked_reason")) or (
            "no_clearly_safe_authenticated_get_endpoint"
        )
    else:
        status = STATUS_BLOCKED
        blocked_reason = "real_authenticated_get_not_implemented_without_safe_endpoint"
    response_evidence_generated = status == STATUS_MOCKED
    value = {
        "contract_version": NO_ORDER_AUTH_GET_REQUEST_PLAN_CONTRACT,
        "task_id": TASK_ID_059,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "no_order_auth_get_requested": no_order_auth_get_requested is True,
        "real_auth_read_only_requested": real_auth_read_only_requested is True,
        "real_auth_read_only_opt_in_present": opt_in_present,
        "real_authenticated_get_performed": False,
        "request_method": "GET",
        "endpoint_path_sanitized": clean_text(endpoint_validation.get("endpoint_path_sanitized")),
        "endpoint_safe_for_no_order_check": endpoint_safe,
        "endpoint_blocked_reason": blocked_reason or clean_text(endpoint_validation.get("endpoint_blocked_reason")),
        "safe_endpoint_allowlist": list(SAFE_NO_ORDER_AUTH_GET_ENDPOINT_ALLOWLIST),
        "real_safe_endpoint_allowlist": list(REAL_NO_ORDER_AUTH_GET_ENDPOINT_ALLOWLIST),
        "clob_base_url_configured": bool(clean_text(clob_base_url)),
        "clob_base_url_value_emitted": False,
        "network_request_performed": False,
        "auth_headers_redacted_boundary_constructed": no_order_auth_get_requested is True,
        "auth_header_values_emitted": False,
        "request_headers_materialized": False,
        "hmac_sha256_signature_generated": False,
        "auth_used": False,
        "credentials_used": "redacted_presence_only",
        "credentials_values_exposed": False,
        "status_code": None,
        "mocked_response_evidence_generated": response_evidence_generated,
        "operator_safe_summary": _no_order_auth_get_plan_summary(status, blocked_reason),
        "generated_at": generated_at,
    }
    value.update(
        no_order_authenticated_get_safety_flags(
            no_order_auth_get_requested=no_order_auth_get_requested,
            real_auth_read_only_requested=real_auth_read_only_requested,
            real_auth_read_only_opt_in_present=opt_in_present,
            real_authenticated_get_performed=False,
            endpoint_safe_for_no_order_check=endpoint_safe,
            auth_used=False,
            auth_header_boundary_checked=no_order_auth_get_requested,
            no_order_auth_check_performed=no_order_auth_get_requested,
        )
    )
    return value


def build_no_order_auth_get_response_evidence_059(
    *,
    request_plan: Mapping[str, Any],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any] | None:
    if request_plan.get("status") != STATUS_MOCKED:
        return None
    value = {
        "contract_version": NO_ORDER_AUTH_GET_RESPONSE_EVIDENCE_CONTRACT,
        "task_id": TASK_ID_059,
        "status": "mocked_response_evidence",
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "no_order_auth_get_requested": request_plan.get("no_order_auth_get_requested") is True,
        "real_auth_read_only_requested": False,
        "real_auth_read_only_opt_in_present": False,
        "real_authenticated_get_performed": False,
        "request_method": "GET",
        "endpoint_path_sanitized": clean_text(request_plan.get("endpoint_path_sanitized")),
        "endpoint_safe_for_no_order_check": request_plan.get("endpoint_safe_for_no_order_check") is True,
        "endpoint_blocked_reason": "",
        "status_code": None,
        "network_request_performed": False,
        "mock_response_only": True,
        "auth_used": False,
        "credentials_used": "redacted_presence_only",
        "credentials_values_exposed": False,
        "headers_emitted": False,
        "body_emitted": False,
        "operator_safe_summary": "Mocked no-order authenticated GET evidence generated; no network request was sent.",
        "generated_at": generated_at,
    }
    value.update(
        no_order_authenticated_get_safety_flags(
            no_order_auth_get_requested=True,
            real_auth_read_only_requested=False,
            real_auth_read_only_opt_in_present=False,
            real_authenticated_get_performed=False,
            endpoint_safe_for_no_order_check=request_plan.get("endpoint_safe_for_no_order_check") is True,
            auth_used=False,
            auth_header_boundary_checked=True,
            no_order_auth_check_performed=True,
        )
    )
    return value


def build_no_order_auth_get_blockers_059(
    *,
    no_order_auth_get_requested: bool,
    real_auth_read_only_requested: bool,
    real_auth_read_only_opt_in_status: Mapping[str, Any],
    endpoint_validation: Mapping[str, Any],
    request_plan: Mapping[str, Any],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if no_order_auth_get_requested is not True and real_auth_read_only_requested is True:
        blockers.append(
            _no_order_auth_get_blocker(
                "real_auth_read_only_requires_no_order_auth_get",
                "operator_opt_in_boundary",
                "--real-auth-read-only requires --no-order-auth-get.",
            )
        )
    if request_plan.get("status") == STATUS_SKIPPED:
        blockers.append(
            _no_order_auth_get_blocker(
                "no_order_auth_get_not_requested",
                "operator_opt_in_boundary",
                "No-order authenticated GET preflight was not requested.",
            )
        )
    if (
        real_auth_read_only_requested is True
        and real_auth_read_only_opt_in_status.get("real_auth_read_only_opt_in_present") is not True
    ):
        blockers.append(
            _no_order_auth_get_blocker(
                "real_no_order_auth_get_not_enabled",
                "operator_opt_in_boundary",
                "PMBOT_ALLOW_REAL_NO_ORDER_AUTH_GET=true is required for a real no-order authenticated GET.",
            )
        )
    if request_plan.get("status") == STATUS_BLOCKED and endpoint_validation.get("endpoint_safe_for_no_order_check") is not True:
        blockers.append(
            _no_order_auth_get_blocker(
                clean_text(endpoint_validation.get("endpoint_blocked_reason")) or "endpoint_not_safe",
                "safe_endpoint_boundary",
                "No clearly safe no-order authenticated GET endpoint is available for real network mode.",
            )
        )
    blockers.extend(
        [
            _no_order_auth_get_blocker(
                "order_submission_blocked",
                "execution_boundary",
                "Order submission remains blocked.",
            ),
            _no_order_auth_get_blocker(
                "order_cancellation_blocked",
                "execution_boundary",
                "Order cancellation remains blocked.",
            ),
            _no_order_auth_get_blocker(
                "signing_blocked",
                "signing_boundary",
                "Signing, HMAC generation, and signed payload generation remain blocked.",
            ),
            _no_order_auth_get_blocker(
                "wallet_blocked",
                "wallet_boundary",
                "Wallet connection and private-key reads remain blocked.",
            ),
            _no_order_auth_get_blocker(
                "balance_read_blocked",
                "account_boundary",
                "Balance reads remain blocked.",
            ),
            _no_order_auth_get_blocker(
                "position_read_blocked",
                "account_boundary",
                "Position reads remain blocked.",
            ),
            _no_order_auth_get_blocker(
                "live_execution_blocked",
                "live_approval_boundary",
                "Live execution remains blocked and allowed_for_live remains false.",
            ),
        ]
    )
    return _dedupe_blockers(blockers)


def build_no_order_auth_get_blockers_report_059(
    *,
    blockers: Sequence[Mapping[str, Any]],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": NO_ORDER_AUTH_GET_BLOCKERS_CONTRACT,
        "task_id": TASK_ID_059,
        "status": "no_order_auth_get_preflight_blocked",
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "blockers": [dict(row) for row in blockers],
        "generated_at": generated_at,
    }
    value.update(
        no_order_authenticated_get_safety_flags(
            no_order_auth_get_requested=True,
            real_auth_read_only_requested=False,
            real_auth_read_only_opt_in_present=False,
            real_authenticated_get_performed=False,
            endpoint_safe_for_no_order_check=False,
            auth_used=False,
            auth_header_boundary_checked=False,
            no_order_auth_check_performed=True,
        )
    )
    return value


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


def build_no_order_auth_boundary_plan_058(
    *,
    clob_base_url_config: Mapping[str, Any],
    marker_presence: Mapping[str, Any],
    mock_auth: bool,
    no_order_auth_check: bool,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    ready = (
        mock_auth is True
        and no_order_auth_check is True
        and clob_base_url_config.get("clob_base_url_valid") is True
        and marker_presence.get("marker_set_complete") is True
        and marker_presence.get("unsafe_raw_value_detected") is not True
    )
    status = STATUS_MOCKED if ready else STATUS_BLOCKED
    if no_order_auth_check is not True:
        status = STATUS_SKIPPED
    value = {
        "contract_version": NO_ORDER_AUTH_BOUNDARY_PLAN_CONTRACT,
        "task_id": TASK_ID_058,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "review_only": True,
        "preflight_only": True,
        "mock_auth": mock_auth is True,
        "auth_boundary_mock_checked": ready,
        "no_order_auth_plan_ready": ready,
        "no_order_auth_check_performed": no_order_auth_check is True,
        "clob_base_url_status": clean_text(clob_base_url_config.get("status") or STATUS_MISSING),
        "l2_marker_presence_status": clean_text(marker_presence.get("status") or STATUS_MISSING),
        "request_method": "GET",
        "endpoint_path": "/auth/no-order-boundary/mock-get",
        "allowed_methods": ["GET"],
        "blocked_methods": list(NO_ORDER_BLOCKED_METHODS),
        "authenticated_request_skipped_by_default": True,
        "authenticated_request_performed": False,
        "network_request_performed": False,
        "request_headers_materialized": False,
        "header_values_emitted": False,
        "hmac_sha256_signature_generated": False,
        "order_endpoint_performed": False,
        "cancel_endpoint_performed": False,
        "balance_endpoint_performed": False,
        "position_endpoint_performed": False,
        "order_payload_included": False,
        "signed_payload_included": False,
        "operator_safe_summary": (
            "Mock no-order GET boundary is ready; no authenticated request is performed."
            if ready
            else "Mock no-order GET boundary is blocked or skipped; no authenticated request is performed."
        ),
        "generated_at": generated_at,
    }
    value.update(
        authenticated_clob_preflight_safety_flags(
            auth_presence_check_performed=True,
            auth_header_boundary_checked=ready,
            no_order_auth_check_performed=no_order_auth_check is True,
        )
    )
    return value


def build_clob_l2_marker_blockers_058(
    *,
    clob_base_url_config: Mapping[str, Any],
    marker_presence: Mapping[str, Any],
    unsafe_marker_detection: Mapping[str, Any],
    no_order_auth_boundary_plan: Mapping[str, Any],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if clob_base_url_config.get("clob_base_url_missing") is True:
        blockers.append(_marker_blocker("clob_base_url_missing", "clob_config", "CLOB base URL is missing."))
    elif clob_base_url_config.get("clob_base_url_valid") is not True:
        blockers.append(_marker_blocker("clob_base_url_invalid", "clob_config", "CLOB base URL is invalid or unsafe."))
    for reason in l2_marker_presence_blockers(marker_presence):
        if reason == "l2_markers_missing":
            blockers.append(_marker_blocker("l2_markers_missing", "l2_marker_boundary", "All L2 marker variables are missing."))
        elif reason == "l2_markers_incomplete":
            blockers.append(_marker_blocker("l2_markers_incomplete", "l2_marker_boundary", "L2 marker variables are incomplete."))
        elif reason.startswith("unsafe_raw_l2_marker_value:"):
            blockers.append(
                _marker_blocker(
                    "unsafe_raw_l2_marker_value",
                    "l2_marker_boundary",
                    "One or more L2 marker values looked like raw credential material and were blocked.",
                )
            )
        else:
            blockers.append(_marker_blocker("l2_marker_presence_blocked", "l2_marker_boundary", reason))
    if unsafe_marker_detection.get("unsafe_raw_value_detected") is True and not any(
        row.get("blocker_id") == "unsafe_raw_l2_marker_value" for row in blockers
    ):
        blockers.append(
            _marker_blocker(
                "unsafe_raw_l2_marker_value",
                "l2_marker_boundary",
                "One or more L2 marker values looked like raw credential material and were blocked.",
            )
        )
    if no_order_auth_boundary_plan.get("no_order_auth_plan_ready") is not True:
        blockers.append(
            _marker_blocker(
                "no_order_auth_boundary_not_ready",
                "auth_boundary",
                "No-order authenticated GET boundary is not ready with safe URL and redacted markers.",
            )
        )
    blockers.extend(
        [
            _marker_blocker(
                "authenticated_request_skipped_by_default",
                "auth_boundary",
                "Authenticated request is skipped by default in task 058.",
            ),
            _marker_blocker(
                "order_submission_blocked",
                "execution_boundary",
                "Order submission remains blocked.",
            ),
            _marker_blocker(
                "order_cancellation_blocked",
                "execution_boundary",
                "Order cancellation remains blocked.",
            ),
            _marker_blocker("signing_blocked", "signing_boundary", "Signing and signed payload generation remain blocked."),
            _marker_blocker("wallet_blocked", "wallet_boundary", "Wallet connection and private-key reads remain blocked."),
            _marker_blocker("balance_read_blocked", "account_boundary", "Balance reads remain blocked."),
            _marker_blocker("position_read_blocked", "account_boundary", "Position reads remain blocked."),
            _marker_blocker(
                "live_execution_blocked",
                "live_approval_boundary",
                "Live execution remains blocked and allowed_for_live remains false.",
            ),
        ]
    )
    return _dedupe_blockers(blockers)


def build_clob_l2_marker_blockers_report_058(
    *,
    blockers: Sequence[Mapping[str, Any]],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = {
        "contract_version": CLOB_L2_MARKER_BLOCKERS_CONTRACT,
        "task_id": TASK_ID_058,
        "status": "clob_l2_marker_preflight_blocked",
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "blockers": [dict(row) for row in blockers],
        "generated_at": generated_at,
    }
    value.update(
        authenticated_clob_preflight_safety_flags(
            auth_presence_check_performed=True,
            auth_header_boundary_checked=False,
            no_order_auth_check_performed=False,
        )
    )
    return value


def render_clob_l2_marker_preflight_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    status = dict(value.get("latest_status", {}))
    clob = dict(value.get("clob_base_url_config", {}))
    markers = dict(value.get("redacted_l2_marker_presence", {}))
    unsafe = dict(value.get("unsafe_l2_marker_detection", {}))
    plan = dict(value.get("no_order_auth_boundary_plan", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT CLOB Base URL and Redacted L2 Marker Preflight 058",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market')}`",
        "- Mode: `preflight / review-only`",
        "- execution_mode: `preflight`",
        "- review_only: `true`",
        "- preflight_only: `true`",
        "",
        "## CLOB Base URL",
        "",
        f"- Configured: `{str(clob.get('clob_base_url_configured') is True).lower()}`",
        f"- Status: `{clob.get('status')}`",
        f"- Valid: `{str(clob.get('clob_base_url_valid') is True).lower()}`",
        f"- Production URL: `{str(clob.get('is_production_clob_base_url') is True).lower()}`",
        "",
        "## Redacted L2 Markers",
        "",
        f"- Marker status: `{markers.get('status')}`",
        f"- Marker set complete: `{str(markers.get('marker_set_complete') is True).lower()}`",
        f"- Configured markers: `{markers.get('configured_count', 0)}`",
        f"- Missing markers: `{markers.get('missing_count', 0)}`",
        f"- Unsafe raw marker detected: `{str(unsafe.get('unsafe_raw_value_detected') is True).lower()}`",
        "- Marker values stored: `false`",
        "- Marker value hashes stored: `false`",
        "",
        "## No-Order Boundary",
        "",
        f"- Plan status: `{plan.get('status')}`",
        f"- Auth boundary mock checked: `{str(plan.get('auth_boundary_mock_checked') is True).lower()}`",
        f"- No-order auth plan ready: `{str(plan.get('no_order_auth_plan_ready') is True).lower()}`",
        "- Authenticated request performed: `false`",
        "- Authenticated request skipped by default: `true`",
        "- Allowed methods in plan: `GET`",
        "- Blocked methods in plan: `POST, PUT, PATCH, DELETE`",
        "",
        "## Safety",
        "",
        "- order submission blocked",
        "- order cancellation blocked",
        "- signing blocked",
        "- signed payload generation blocked",
        "- wallet connection blocked",
        "- balances blocked",
        "- positions blocked",
        "- live execution blocked",
        "- authenticated_polymarket_enabled: `false`",
        "- live_connector_enabled: `false`",
        "- allowed_for_live: `false`",
        "- resolved_blocker_count: `0`",
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
        "",
        "## Latest Status",
        "",
        f"- Latest status path: `{status.get('latest_status_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_no_order_auth_get_preflight_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    status = dict(value.get("latest_status", {}))
    request_plan = dict(value.get("request_plan", {}))
    endpoint = dict(value.get("safe_no_order_endpoint_validation", {}))
    opt_in = dict(value.get("real_auth_read_only_opt_in_status", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Optional No-Order Authenticated GET Preflight 059",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market')}`",
        "- Mode: `preflight / review-only`",
        "- execution_mode: `preflight`",
        "- review_only: `true`",
        "- preflight_only: `true`",
        "",
        "## Request Boundary",
        "",
        f"- No-order auth GET status: `{status.get('no_order_auth_get_status')}`",
        f"- No-order auth GET requested: `{str(status.get('no_order_auth_get_requested') is True).lower()}`",
        f"- Real auth read-only requested: `{str(status.get('real_auth_read_only_requested') is True).lower()}`",
        f"- Real auth opt-in present: `{str(status.get('real_auth_read_only_opt_in_present') is True).lower()}`",
        f"- Request method: `{request_plan.get('request_method')}`",
        f"- Endpoint path sanitized: `{endpoint.get('endpoint_path_sanitized')}`",
        f"- Endpoint safe for no-order check: `{str(endpoint.get('endpoint_safe_for_no_order_check') is True).lower()}`",
        f"- Endpoint blocked reason: `{endpoint.get('endpoint_blocked_reason')}`",
        f"- Opt-in blocker reason: `{opt_in.get('blocker_reason')}`",
        "- Allowed method: `GET`",
        "- Blocked methods: `POST, PUT, PATCH, DELETE`",
        "",
        "## Evidence",
        "",
        f"- Real authenticated GET performed: `{str(status.get('real_authenticated_get_performed') is True).lower()}`",
        f"- Status code: `{status.get('status_code')}`",
        f"- Auth used: `{str(status.get('auth_used') is True).lower()}`",
        "- Credentials used: `redacted_presence_only`",
        "- Credential values exposed: `false`",
        "- Header values stored: `false`",
        "- Signed payload generated: `false`",
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
        "- signing_attempted: `false`",
        "- signed_payload_generated: `false`",
        "- order_submission_attempted: `false`",
        "- order_cancellation_attempted: `false`",
        "- balance_read_attempted: `false`",
        "- position_read_attempted: `false`",
        "- wallet_connection_attempted: `false`",
        "- live_execution_approved: `false`",
        "- allowed_for_live: `false`",
        "- resolved_blocker_count: `0`",
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
        "",
        "## Latest Status",
        "",
        f"- Latest status path: `{status.get('latest_status_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_authenticated_clob_preflight_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    request_status = _authenticated_request_summary(value)
    no_order_auth_get = dict(value.get("no_order_auth_get_preflight_status_summary", {}))
    no_order_auth_get_status = clean_text(
        no_order_auth_get.get("no_order_auth_get_status")
        or value.get("no_order_auth_get_status")
        or STATUS_SKIPPED
    )
    l2_status = clean_text(
        value.get("auth_presence_status")
        or value.get("auth_presence")
        or dict(value.get("clob_l2_marker_preflight_status_summary", {})).get("l2_marker_presence_status")
        or STATUS_MISSING
    )
    clob_url_status = clean_text(value.get("clob_base_url_status") or value.get("clob_base_url") or STATUS_MISSING)
    return "\n".join(
        [
            "Authenticated CLOB preflight completed.",
            f"Market: {clean_text(value.get('market'))}",
            "Mode: preflight / review-only",
            f"Auth presence: {l2_status}",
            f"CLOB base URL: {clob_url_status}",
            f"CLOB URL: {clob_url_status}",
            f"L2 markers: {l2_status}",
            f"Auth header boundary: {clean_text(value.get('auth_header_boundary_status') or value.get('auth_header_boundary') or STATUS_BLOCKED)}",
            f"Authenticated request: {request_status}",
            f"No-order auth GET: {no_order_auth_get_status}",
            f"CLOB/L2 marker preflight: {clean_text(dict(value.get('clob_l2_marker_preflight_status_summary', {})).get('status') or 'not_available')}",
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
    no_order_auth_get = dict(value.get("no_order_auth_get_preflight_status_summary", {}))
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
        "## Optional No-Order Auth GET 059",
        "",
        f"- 059 status: `{no_order_auth_get.get('status', 'not_available')}`",
        f"- No-order auth GET: `{no_order_auth_get.get('no_order_auth_get_status', STATUS_SKIPPED)}`",
        f"- Real auth read-only requested: `{str(no_order_auth_get.get('real_auth_read_only_requested') is True).lower()}`",
        f"- Real auth opt-in present: `{str(no_order_auth_get.get('real_auth_read_only_opt_in_present') is True).lower()}`",
        f"- Real authenticated GET performed: `{str(no_order_auth_get.get('real_authenticated_get_performed') is True).lower()}`",
        f"- Request method: `{no_order_auth_get.get('request_method', 'GET')}`",
        f"- Endpoint path sanitized: `{no_order_auth_get.get('endpoint_path_sanitized', '')}`",
        f"- Endpoint blocked reason: `{no_order_auth_get.get('endpoint_blocked_reason', '')}`",
        "- Credentials used: `redacted_presence_only`",
        "- Credential values exposed: `false`",
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


def _clob_l2_marker_operator_summary(status: Mapping[str, Any]) -> str:
    return (
        "CLOB/L2 marker preflight completed as review-only. CLOB base URL="
        + clean_text(status.get("clob_base_url_status"))
        + "; L2 markers="
        + clean_text(status.get("l2_marker_presence_status"))
        + "; authenticated requests, order submission, signing, wallet use, balances, positions, and live execution remain blocked."
    )


def _clob_l2_marker_overall_status(
    *,
    clob_base_url_config: Mapping[str, Any],
    marker_presence: Mapping[str, Any],
    no_order_auth_boundary_plan: Mapping[str, Any],
) -> str:
    if (
        clob_base_url_config.get("clob_base_url_valid") is True
        and marker_presence.get("marker_set_complete") is True
        and marker_presence.get("unsafe_raw_value_detected") is not True
        and no_order_auth_boundary_plan.get("no_order_auth_plan_ready") is True
    ):
        return "clob_l2_marker_preflight_ready_live_blocked"
    return "clob_l2_marker_preflight_fail_closed"


def _clob_l2_marker_status_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or "not_available"),
        "mode": clean_text(value.get("mode") or MODE),
        "execution_mode": clean_text(value.get("execution_mode") or EXECUTION_MODE),
        "clob_base_url_configured": value.get("clob_base_url_configured") is True,
        "clob_base_url_status": clean_text(value.get("clob_base_url_status") or STATUS_MISSING),
        "clob_base_url_valid": value.get("clob_base_url_valid") is True,
        "clob_base_url_missing": value.get("clob_base_url_missing") is True,
        "clob_base_url_invalid": value.get("clob_base_url_invalid") is True,
        "public_clob_base_url": clean_text(value.get("public_clob_base_url")),
        "is_production_clob_base_url": value.get("is_production_clob_base_url") is True,
        "auth_marker_presence_detected": value.get("auth_marker_presence_detected") is True,
        "l2_marker_presence_status": clean_text(value.get("l2_marker_presence_status") or STATUS_MISSING),
        "l2_marker_set_complete": value.get("l2_marker_set_complete") is True,
        "l2_marker_configured_count": int(value.get("l2_marker_configured_count", 0) or 0),
        "l2_marker_missing_count": int(value.get("l2_marker_missing_count", 0) or 0),
        "unsafe_raw_value_detected": value.get("unsafe_raw_value_detected") is True,
        "auth_boundary_mock_checked": value.get("auth_boundary_mock_checked") is True,
        "no_order_auth_plan_ready": value.get("no_order_auth_plan_ready") is True,
        "authenticated_request_skipped_by_default": True,
        "authenticated_request_performed": False,
        "blocker_count": int(value.get("blocker_count", 0) or 0),
        "top_blocker_reasons": [
            clean_text(item) for item in value.get("top_blocker_reasons", []) if clean_text(item)
        ],
        "artifact_path": clean_text(value.get("artifact_path")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "clob_base_url_config_path": clean_text(value.get("clob_base_url_config_path")),
        "redacted_l2_marker_presence_path": clean_text(value.get("redacted_l2_marker_presence_path")),
        "unsafe_l2_marker_detection_path": clean_text(value.get("unsafe_l2_marker_detection_path")),
        "no_order_auth_boundary_plan_path": clean_text(value.get("no_order_auth_boundary_plan_path")),
        "blockers_path": clean_text(value.get("blockers_path")),
        "review_only": True,
        "preflight_only": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "signing_blocked": True,
        "wallet_connection_blocked": True,
        "balance_read_blocked": True,
        "position_read_blocked": True,
        "live_execution_blocked": True,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
    }


def _no_order_auth_get_overall_status(request_plan: Mapping[str, Any]) -> str:
    status = clean_text(request_plan.get("status") or STATUS_SKIPPED)
    if status == STATUS_MOCKED:
        return "no_order_auth_get_preflight_mocked_live_blocked"
    if status == STATUS_REAL_GET_CHECKED:
        return "no_order_auth_get_preflight_real_get_checked_live_blocked"
    if status == STATUS_SKIPPED:
        return "no_order_auth_get_preflight_skipped_live_blocked"
    return "no_order_auth_get_preflight_blocked_live_blocked"


def _no_order_auth_get_status_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    blockers = value.get("blockers") if isinstance(value.get("blockers"), list) else []
    top_blockers = value.get("top_blocker_reasons")
    if not isinstance(top_blockers, list):
        top_blockers = [
            clean_text(row.get("reason"))
            for row in mapping_rows(blockers)
            if clean_text(row.get("reason"))
        ][:8]
    return {
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market") or "not_available"),
        "mode": clean_text(value.get("mode") or MODE),
        "execution_mode": clean_text(value.get("execution_mode") or EXECUTION_MODE),
        "no_order_auth_get_status": clean_text(value.get("no_order_auth_get_status") or STATUS_SKIPPED),
        "no_order_auth_get_requested": value.get("no_order_auth_get_requested") is True,
        "real_auth_read_only_requested": value.get("real_auth_read_only_requested") is True,
        "real_auth_read_only_opt_in_present": value.get("real_auth_read_only_opt_in_present") is True,
        "real_authenticated_get_performed": value.get("real_authenticated_get_performed") is True,
        "request_method": "GET",
        "endpoint_path_sanitized": clean_text(value.get("endpoint_path_sanitized")),
        "endpoint_safe_for_no_order_check": value.get("endpoint_safe_for_no_order_check") is True,
        "endpoint_blocked_reason": clean_text(value.get("endpoint_blocked_reason")),
        "status_code": value.get("status_code"),
        "auth_used": value.get("auth_used") is True,
        "credentials_used": "redacted_presence_only",
        "credentials_values_exposed": False,
        "blocker_count": int(value.get("blocker_count", len(blockers)) or 0),
        "blockers": [dict(row) for row in mapping_rows(blockers)],
        "top_blocker_reasons": [clean_text(item) for item in top_blockers if clean_text(item)],
        "artifact_path": clean_text(value.get("artifact_path")),
        "latest_status_path": clean_text(value.get("latest_status_path")),
        "operator_markdown_path": clean_text(value.get("operator_markdown_path")),
        "request_plan_path": clean_text(value.get("request_plan_path")),
        "endpoint_validation_path": clean_text(value.get("endpoint_validation_path")),
        "response_evidence_path": clean_text(value.get("response_evidence_path")),
        "blockers_path": clean_text(value.get("blockers_path")),
        "review_only": True,
        "preflight_only": True,
        "order_submission_blocked": True,
        "order_cancellation_blocked": True,
        "signing_blocked": True,
        "wallet_connection_blocked": True,
        "balance_read_blocked": True,
        "position_read_blocked": True,
        "live_execution_blocked": True,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
    }


def _no_order_auth_get_operator_summary(status: Mapping[str, Any]) -> str:
    return (
        "No-order authenticated GET preflight completed as review-only. Status="
        + clean_text(status.get("no_order_auth_get_status"))
        + "; method=GET; order submission, cancellation, signing, wallet use, balances, positions, and live execution are blocked."
    )


def _no_order_auth_get_plan_summary(status: str, blocked_reason: str) -> str:
    if status == STATUS_SKIPPED:
        return "No-order authenticated GET was not requested; no request was sent."
    if status == STATUS_MOCKED:
        return "Mocked no-order authenticated GET boundary checked; no network request was sent."
    if blocked_reason:
        return f"No-order authenticated GET is blocked: {clean_text(blocked_reason)}."
    return "No-order authenticated GET is blocked; no request was sent."


def _blocker(blocker_id: str, category: str, reason: str) -> dict[str, Any]:
    return LiveAuthReadinessBlocker(
        blocker_id=clean_text(blocker_id),
        blocker_category=clean_text(category),
        severity="critical",
        reason=clean_text(reason),
    ).to_dict()


def _marker_blocker(blocker_id: str, category: str, reason: str) -> dict[str, Any]:
    value = {
        "contract_version": "pmbot_clob_l2_marker_blocker_058.v1",
        "task_id": TASK_ID_058,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "severity": "critical",
        "reason": clean_text(reason),
        "resolution_status": "unresolved",
        "blocks_live_execution": True,
        "resolved": False,
    }
    value.update(
        authenticated_clob_preflight_safety_flags(
            auth_presence_check_performed=True,
            auth_header_boundary_checked=False,
            no_order_auth_check_performed=False,
        )
    )
    return value


def _no_order_auth_get_blocker(blocker_id: str, category: str, reason: str) -> dict[str, Any]:
    value = {
        "contract_version": NO_ORDER_AUTH_GET_BLOCKER_CONTRACT,
        "task_id": TASK_ID_059,
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "severity": "critical",
        "reason": clean_text(reason),
        "resolution_status": "unresolved",
        "blocks_live_execution": True,
        "resolved": False,
    }
    value.update(
        no_order_authenticated_get_safety_flags(
            no_order_auth_get_requested=True,
            real_auth_read_only_requested=False,
            real_auth_read_only_opt_in_present=False,
            real_authenticated_get_performed=False,
            endpoint_safe_for_no_order_check=False,
            auth_used=False,
            auth_header_boundary_checked=False,
            no_order_auth_check_performed=True,
        )
    )
    return value


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


def _sanitize_endpoint_path(endpoint_path: str) -> str:
    text = clean_text(endpoint_path) or NO_ORDER_AUTH_GET_MOCK_ENDPOINT
    parsed = urlsplit(text)
    if parsed.scheme or parsed.netloc:
        path = parsed.path
    else:
        path = text.split("?", 1)[0].split("#", 1)[0]
    path = clean_text(path)
    if not path.startswith("/"):
        path = "/" + path
    return path or NO_ORDER_AUTH_GET_MOCK_ENDPOINT


def _forbidden_endpoint_terms_for_path(path_without_leading_slash: str) -> tuple[str, ...]:
    normalized = clean_text(path_without_leading_slash).lower().strip("/")
    segments = [segment for segment in normalized.split("/") if segment]
    found: list[str] = []
    if normalized in {"auth/api-key", "auth/derive-api-key"}:
        found.append(normalized)
    segment_terms = {
        "order",
        "orders",
        "cancel",
        "cancels",
        "cancellation",
        "cancellations",
        "balance",
        "balances",
        "position",
        "positions",
        "fill",
        "fills",
        "trade",
        "trades",
        "wallet",
        "wallets",
        "allowance",
        "allowances",
        "approval",
        "approvals",
        "approve",
        "heartbeat",
    }
    found.extend(segment for segment in segments if segment in segment_terms)
    result: list[str] = []
    for item in found:
        if item and item not in result:
            result.append(item)
    return tuple(result)


def _env_true(value: Any) -> bool:
    return clean_text(value).lower() in {"true", "1", "yes", "y", "on"}


def _derived_clob_l2_marker_artifact_dir(artifact_dir: str | Path | None) -> Path | None:
    if artifact_dir is None:
        return None
    return Path(artifact_dir) / "clob_l2_marker_preflight_058"


def _derived_no_order_auth_get_artifact_dir(artifact_dir: str | Path | None) -> Path | None:
    if artifact_dir is None:
        return None
    return Path(artifact_dir) / "no_order_auth_get_preflight_059"


def _active_environ(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    if environ is not None:
        return environ
    import os

    return os.environ
