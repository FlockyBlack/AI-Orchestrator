from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlsplit

from pm_bot.trading_core.live_connector_preflight_models import (
    EXECUTION_MODE,
    MODE,
    STATUS_AUTH_BLOCKED,
    STATUS_AUTH_CHECKED,
    STATUS_AUTH_MISSING,
    STATUS_AUTH_SKIPPED,
    STATUS_NETWORK_FAILED,
    STATUS_NETWORK_OK,
    STATUS_NETWORK_SKIPPED,
    AuthBoundaryPreflightResult,
    LatestLiveConnectorPreflightStatus,
    LiveConnectorPreflightConfig,
    LiveConnectorPreflightResult,
    LiveReadinessBlocker,
    NetworkPreflightResult,
    live_connector_preflight_safety_flags,
)
from pm_bot.trading_core.live_credentials_boundary import (
    PMBOT_POLYMARKET_CLOB_BASE_URL_ENV,
    build_live_credentials_presence_report,
    credential_presence_blockers,
)
from pm_bot.trading_core.public_gamma_market_client import (
    DEFAULT_GAMMA_BASE_URL,
    READ_ONLY_METHOD,
    PublicGammaFetchError,
    PublicGammaMarketClient,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/live_connector_preflight_056")

LIVE_CONNECTOR_PREFLIGHT_BLOCKERS_CONTRACT = "pmbot_live_connector_preflight_blockers_056.v1"

ReadOnlyTransport = Callable[[str, float], tuple[int | None, Any]]

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
    "--authenticated",
)


class LiveConnectorPublicPreflightClient:
    """Public GET-only preflight client; it has no wallet, signing, or trade methods."""

    def __init__(
        self,
        *,
        gamma_base_url: str | None = None,
        clob_base_url: str = "",
        timeout_seconds: float = 5.0,
        transport: ReadOnlyTransport | None = None,
    ) -> None:
        self.gamma_base_url = clean_text(gamma_base_url) or DEFAULT_GAMMA_BASE_URL
        self.clob_base_url = clean_text(clob_base_url)
        self.timeout_seconds = float(timeout_seconds or 5.0)
        self._transport = transport

    def check_public_gamma(self, *, market: str, generated_at: str = GENERATED_AT) -> dict[str, Any]:
        client = PublicGammaMarketClient(
            base_url=self.gamma_base_url,
            timeout_seconds=self.timeout_seconds,
            transport=self._transport,
        )
        try:
            fetch_result = client.search_public_markets(
                market=market,
                limit=1,
                timeout_seconds=self.timeout_seconds,
                generated_at=generated_at,
            )
        except PublicGammaFetchError as exc:
            error_payload = dict(exc.error_payload)
            return {
                "status": STATUS_NETWORK_FAILED,
                "base_url_status": _base_url_shape_status(self.gamma_base_url),
                "endpoint_path": clean_text(error_payload.get("endpoint_path") or "/events"),
                "status_code": None,
                "response_observed": False,
                "response_snapshot_hash": "",
                "normalized_market_count": 0,
                "error_category": clean_text(error_payload.get("error_type") or type(exc).__name__),
                "error_message_redacted": "public GET failed; no credentials or auth headers were used",
            }
        response = dict(fetch_result.get("response_evidence", {}))
        return {
            "status": STATUS_NETWORK_OK,
            "base_url_status": _base_url_shape_status(fetch_result.get("base_url") or self.gamma_base_url),
            "endpoint_path": clean_text(fetch_result.get("endpoint_path") or "/events"),
            "status_code": response.get("status_code"),
            "response_observed": True,
            "response_snapshot_hash": clean_text(response.get("response_snapshot_hash")),
            "normalized_market_count": int(response.get("normalized_market_count", 0) or 0),
            "error_category": "",
            "error_message_redacted": "",
        }

    def check_public_clob_shape(self) -> dict[str, Any]:
        status = _base_url_shape_status(self.clob_base_url)
        if status == "missing":
            return {
                "status": STATUS_NETWORK_SKIPPED,
                "base_url_status": status,
                "reason": "PMBOT_POLYMARKET_CLOB_BASE_URL not configured; no CLOB request made",
            }
        if status != "valid_public_url_shape":
            return {
                "status": STATUS_NETWORK_FAILED,
                "base_url_status": status,
                "reason": "configured CLOB base URL shape is not safe for public preflight",
            }
        return {
            "status": STATUS_NETWORK_SKIPPED,
            "base_url_status": status,
            "reason": "CLOB public read endpoint not used because this repo has no documented safe CLOB public GET adapter",
        }


def live_connector_preflight_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "live_connector_preflight_056_result.json",
        "operator_md": root / "live_connector_preflight_056_operator.md",
        "latest_status": root / "latest_live_connector_preflight_status_056.json",
        "network_evidence": root / "live_connector_network_evidence_056.json",
        "credential_presence": root / "live_credentials_presence_056.json",
        "blockers": root / "live_readiness_blockers_056.json",
    }


def run_live_connector_preflight(
    *,
    market: str = "BTC",
    dry_run: bool = True,
    public_only: bool = True,
    network_check: bool = False,
    auth_check: bool = False,
    artifact_dir: str | Path | None = None,
    public_client: LiveConnectorPublicPreflightClient | None = None,
    environ: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("live connector preflight requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    paths = live_connector_preflight_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    active_environ = _active_environ(environ)
    effective_auth_check = auth_check is True and public_only is not True
    clob_base_url = clean_text(active_environ.get(PMBOT_POLYMARKET_CLOB_BASE_URL_ENV))
    client = public_client or LiveConnectorPublicPreflightClient(clob_base_url=clob_base_url)

    config = LiveConnectorPreflightConfig(
        market=market_symbol,
        dry_run=True,
        public_only=public_only is True,
        network_check=network_check is True,
        auth_check=effective_auth_check,
        artifact_dir=normalize_path(paths["root"]),
        generated_at=generated_at,
    ).to_dict()
    network = _run_public_network_preflight(
        client=client,
        market=market_symbol,
        network_check=network_check,
        generated_at=generated_at,
    )
    credential_presence = build_live_credentials_presence_report(
        environ=active_environ,
        auth_check=effective_auth_check,
        generated_at=generated_at,
    )
    auth_boundary = _build_auth_boundary_result(
        credential_presence=credential_presence,
        generated_at=generated_at,
    )
    blockers = _build_live_readiness_blockers(
        network=network,
        auth_boundary=auth_boundary,
        credential_presence=credential_presence,
    )
    blockers_report = _build_blockers_report(blockers=blockers, generated_at=generated_at)
    latest_status = LatestLiveConnectorPreflightStatus(
        market=market_symbol,
        status=_overall_status(network=network, auth_boundary=auth_boundary),
        public_network_status=clean_text(network.get("public_network_status") or STATUS_NETWORK_SKIPPED),
        auth_boundary_status=clean_text(auth_boundary.get("auth_boundary_status") or STATUS_AUTH_SKIPPED),
        blocker_count=len(blockers),
        blockers=tuple(blockers),
        artifact_path=path_refs["result"],
        latest_status_path=path_refs["latest_status"],
        operator_markdown_path=path_refs["operator_md"],
        network_evidence_path=path_refs["network_evidence"],
        credential_presence_path=path_refs["credential_presence"],
        blockers_path=path_refs["blockers"],
        generated_at=generated_at,
    ).to_dict()
    result = LiveConnectorPreflightResult(
        market=market_symbol,
        status=clean_text(latest_status.get("status")),
        config=config,
        network_preflight=network,
        auth_boundary=auth_boundary,
        latest_status=latest_status,
        blockers=tuple(blockers),
        artifact_paths=path_refs,
        operator_summary=_operator_summary(latest_status),
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["network_evidence"], network)
    write_json(paths["credential_presence"], credential_presence)
    write_json(paths["blockers"], blockers_report)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_live_connector_preflight_markdown(result))
    return result


def render_live_connector_preflight_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Live connector preflight completed.",
            f"Market: {clean_text(value.get('market'))}",
            "Mode: preflight / review-only",
            f"Public network: {clean_text(value.get('public_network_status') or value.get('public_network') or STATUS_NETWORK_SKIPPED)}",
            f"Auth boundary: {clean_text(value.get('auth_boundary_status') or value.get('auth_boundary') or STATUS_AUTH_SKIPPED)}",
            "Order submission: blocked",
            "Signing: blocked",
            "Live execution: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_live_connector_preflight_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    status = dict(value.get("latest_status", {}))
    network = dict(value.get("network_preflight", {}))
    auth = dict(value.get("auth_boundary", {}))
    credential_presence = dict(auth.get("credential_presence_report", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Live Connector Preflight 056",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market')}`",
        "- Mode: `preflight / review-only`",
        "- execution_mode: `paper_or_preflight`",
        "- review_only: `true`",
        "- preflight_only: `true`",
        "",
        "## Public Network",
        "",
        f"- Public network status: `{network.get('public_network_status')}`",
        f"- Public network check performed: `{str(network.get('public_network_check_performed') is True).lower()}`",
        f"- Request method: `{network.get('request_method')}`",
        f"- Gamma status: `{network.get('gamma_status')}`",
        f"- Gamma base URL status: `{network.get('gamma_base_url_status')}`",
        f"- CLOB public read status: `{network.get('clob_public_read_status')}`",
        "",
        "## Credential Presence",
        "",
        f"- Auth boundary status: `{auth.get('auth_boundary_status')}`",
        f"- Auth presence check performed: `{str(auth.get('auth_presence_check_performed') is True).lower()}`",
        f"- Credential markers configured: `{credential_presence.get('configured_count', 0)}`",
        f"- Credential markers missing: `{credential_presence.get('missing_count', 0)}`",
        "- Credential values: `redacted_or_missing_only`",
        "- Raw credential values stored: `false`",
        "",
        "## Safety",
        "",
        "- order submission blocked",
        "- signing blocked",
        "- wallet connection blocked",
        "- live execution blocked",
        "- authenticated request performed: `false`",
        "- signed payload generated: `false`",
        "- allowed_for_live: `false`",
        "- resolved_blocker_count: `0`",
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
        "",
        "## Next Operator Action",
        "",
        "- review preflight only, no live order available",
        f"- Latest status path: `{status.get('latest_status_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "live connector preflight is review-only; unsupported live/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _run_public_network_preflight(
    *,
    client: LiveConnectorPublicPreflightClient,
    market: str,
    network_check: bool,
    generated_at: str,
) -> dict[str, Any]:
    gamma = client.check_public_gamma(market=market, generated_at=generated_at)
    clob = client.check_public_clob_shape() if network_check else {
        "status": STATUS_NETWORK_SKIPPED,
        "base_url_status": "not_requested",
        "reason": "pass --network-check to evaluate configured CLOB base URL shape; no CLOB request is made",
    }
    public_status = STATUS_NETWORK_OK if gamma.get("status") == STATUS_NETWORK_OK else STATUS_NETWORK_FAILED
    return NetworkPreflightResult(
        public_network_status=public_status,
        public_network_check_performed=True,
        request_method=READ_ONLY_METHOD,
        gamma_status=clean_text(gamma.get("status")),
        gamma_base_url_status=clean_text(gamma.get("base_url_status")),
        gamma_endpoint_path=clean_text(gamma.get("endpoint_path")),
        gamma_status_code=gamma.get("status_code") if isinstance(gamma.get("status_code"), int) else None,
        gamma_response_observed=gamma.get("response_observed") is True,
        gamma_response_snapshot_hash=clean_text(gamma.get("response_snapshot_hash")),
        gamma_normalized_market_count=int(gamma.get("normalized_market_count", 0) or 0),
        clob_public_read_status=clean_text(clob.get("status")),
        clob_base_url_status=clean_text(clob.get("base_url_status")),
        network_error_category=clean_text(gamma.get("error_category")),
        network_error_message_redacted=clean_text(gamma.get("error_message_redacted")),
        generated_at=generated_at,
    ).to_dict()


def _build_auth_boundary_result(
    *,
    credential_presence: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    blockers = [
        _blocker(
            "AUTH_BOUNDARY_BLOCKED",
            "auth_boundary",
            reason,
        )
        for reason in credential_presence_blockers(credential_presence)
    ]
    if credential_presence.get("auth_presence_check_performed") is not True:
        status = STATUS_AUTH_SKIPPED
    elif blockers:
        status = STATUS_AUTH_MISSING
    elif credential_presence.get("status") == STATUS_AUTH_CHECKED:
        status = STATUS_AUTH_CHECKED
    else:
        status = STATUS_AUTH_BLOCKED
    return AuthBoundaryPreflightResult(
        auth_boundary_status=status,
        auth_presence_check_performed=credential_presence.get("auth_presence_check_performed") is True,
        credential_presence_report=credential_presence,
        blockers=tuple(blockers),
        authenticated_request_performed=False,
        generated_at=generated_at,
    ).to_dict()


def _build_live_readiness_blockers(
    *,
    network: Mapping[str, Any],
    auth_boundary: Mapping[str, Any],
    credential_presence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if network.get("public_network_status") != STATUS_NETWORK_OK:
        blockers.append(
            _blocker(
                "PUBLIC_NETWORK_PREFLIGHT_FAILED",
                "network",
                "Public Gamma GET preflight did not return ok; live remains blocked.",
            )
        )
    if auth_boundary.get("auth_boundary_status") == STATUS_AUTH_SKIPPED:
        blockers.append(
            _blocker(
                "AUTH_PRESENCE_CHECK_NOT_REQUESTED",
                "auth_boundary",
                "Auth presence was not requested; public-only preflight cannot establish live readiness.",
            )
        )
    for reason in credential_presence_blockers(credential_presence):
        blockers.append(_blocker("AUTH_PREFLIGHT_CONFIG_BLOCKED", "auth_boundary", reason))
    blockers.extend(
        [
            _blocker(
                "ORDER_SUBMISSION_BLOCKED",
                "execution_boundary",
                "Order submission remains unavailable in task 056.",
            ),
            _blocker(
                "ORDER_CANCELLATION_BLOCKED",
                "execution_boundary",
                "Order cancellation remains unavailable in task 056.",
            ),
            _blocker(
                "SIGNING_BLOCKED",
                "signing_boundary",
                "Cryptographic signing and signed payload generation remain unavailable.",
            ),
            _blocker(
                "WALLET_CONNECTION_BLOCKED",
                "wallet_boundary",
                "Wallet connection and wallet spend remain unavailable.",
            ),
            _blocker(
                "LIVE_EXECUTION_BLOCKED",
                "live_approval_boundary",
                "Live execution is not approved and allowed_for_live remains false.",
            ),
        ]
    )
    return _dedupe_blockers(blockers)


def _build_blockers_report(*, blockers: Sequence[Mapping[str, Any]], generated_at: str) -> dict[str, Any]:
    value = {
        "contract_version": LIVE_CONNECTOR_PREFLIGHT_BLOCKERS_CONTRACT,
        "task_id": "ORCH-PMBOT-TRADING-MVP-056-SUPERVISED-LIVE-CONNECTOR-AUTH-NETWORK-PREFLIGHT-NO-ORDER-SUBMISSION",
        "status": "live_readiness_blocked",
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "blockers": [dict(row) for row in blockers],
        "generated_at": generated_at,
    }
    value.update(
        live_connector_preflight_safety_flags(
            public_network_check_performed=False,
            auth_presence_check_performed=False,
        )
    )
    return value


def _blocker(blocker_id: str, category: str, reason: str) -> dict[str, Any]:
    return LiveReadinessBlocker(
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


def _overall_status(*, network: Mapping[str, Any], auth_boundary: Mapping[str, Any]) -> str:
    if network.get("public_network_status") == STATUS_NETWORK_OK and auth_boundary.get("auth_boundary_status") in {
        STATUS_AUTH_CHECKED,
        STATUS_AUTH_SKIPPED,
    }:
        return "preflight_completed_live_blocked"
    return "preflight_completed_fail_closed"


def _operator_summary(status: Mapping[str, Any]) -> str:
    return (
        "Live connector preflight completed as review-only. Public network status="
        + clean_text(status.get("public_network_status"))
        + "; auth boundary="
        + clean_text(status.get("auth_boundary_status"))
        + "; order submission, signing, wallet use, and live execution are blocked."
    )


def _base_url_shape_status(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "missing"
    lowered = text.lower()
    if any(marker in lowered for marker in ("private_key", "mnemonic", "seed_phrase", "secret", "token")):
        return "invalid_sensitive_looking_value_redacted"
    parsed = urlsplit(text)
    if parsed.scheme not in {"http", "https"}:
        return "invalid_scheme"
    if not parsed.netloc:
        return "invalid_missing_host"
    return "valid_public_url_shape"


def _active_environ(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    if environ is not None:
        return environ
    import os

    return os.environ
