from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from pm_bot.trading_core.clob_l2_auth_readonly_probe import run_clob_l2_auth_readonly_probe
from pm_bot.trading_core.discovery_to_token_resolver_bridge import run_discovery_to_token_resolver_bridge
from pm_bot.trading_core.guarded_signer_diagnostic_smoke import run_guarded_signer_diagnostic_smoke
from pm_bot.trading_core.live_account_readonly_state_probe import run_live_account_readonly_state_probe
from pm_bot.trading_core.live_readonly_status_aggregator import run_live_readonly_status_aggregator
from pm_bot.trading_core.local_real_check_bundle_models import (
    CLOB_SUBCHECK_ID,
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    DISCOVERY_BRIDGE_SUBCHECK_ID,
    GUARDED_SIGNER_SUBCHECK_ID,
    LIVE_ACCOUNT_SUBCHECK_ID,
    LIVE_STATUS_SUBCHECK_ID,
    PUBLIC_DISCOVERY_SUBCHECK_ID,
    SUBCHECK_LABELS,
    SUBCHECK_SEQUENCE,
    TASK_ID,
    LocalRealCheckBundleBlocker,
    LocalRealCheckBundleLatestStatus,
    LocalRealCheckBundleResult,
    LocalRealCheckBundleSubcheckStatus,
    build_blockers_artifact,
    build_safety_snapshot,
    build_subchecks_artifact,
    bundle_status_from_subchecks,
    classify_subcheck_status,
    local_real_check_bundle_safety_flags,
)
from pm_bot.trading_core.public_gamma_market_client import PublicGammaMarketClient
from pm_bot.trading_core.public_market_token_discovery import run_public_market_token_discovery
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/local_real_check_bundle_072c")
DEFAULT_SUBCHECK_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--wallet-connect",
    "--private-key",
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
    "--sign",
    "--signing",
    "--order",
    "--order-payload",
    "--submit",
    "--cancel",
    "--approve-live",
    "--browser",
    "--loop",
    "--daemon",
    "--scheduler",
)

Runner = Callable[..., dict[str, Any]]

SUBCHECK_ARTIFACT_DIR_NAMES = {
    CLOB_SUBCHECK_ID: "clob_l2_auth_readonly_probe_067c",
    LIVE_ACCOUNT_SUBCHECK_ID: "live_account_readonly_state_probe_070c",
    GUARDED_SIGNER_SUBCHECK_ID: "guarded_signer_diagnostic_smoke_069a",
    PUBLIC_DISCOVERY_SUBCHECK_ID: "public_market_token_discovery_071a",
    DISCOVERY_BRIDGE_SUBCHECK_ID: "discovery_to_token_resolver_bridge_071d",
    LIVE_STATUS_SUBCHECK_ID: "live_readonly_status_aggregator_071b",
}


def local_real_check_bundle_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "local_real_check_bundle_072c_result.json",
        "latest_status": root / "latest_local_real_check_bundle_status_072c.json",
        "subchecks": root / "local_real_check_bundle_subchecks_072c.json",
        "blockers": root / "local_real_check_bundle_blockers_072c.json",
        "safety_snapshot": root / "local_real_check_bundle_safety_snapshot_072c.json",
        "operator_summary": root / "local_real_check_bundle_operator_summary_072c.md",
    }


def run_local_real_check_bundle(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    allow_private_key_diagnostic: bool = False,
    artifact_dir: str | Path | None = None,
    subcheck_artifact_root: str | Path | None = None,
    public_discovery_local_artifact_paths: Sequence[str | Path] | None = None,
    public_discovery_query: str = "",
    public_discovery_slug: str = "",
    public_discovery_tag_id: str = "",
    public_discovery_limit: int = 25,
    selected_candidate_id: str = "",
    environ: Mapping[str, str] | None = None,
    public_client: PublicGammaMarketClient | None = None,
    generated_at: str = GENERATED_AT,
    secret_redaction_values: Sequence[str] | None = None,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("local real-check bundle requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    paths = local_real_check_bundle_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    subcheck_root = Path(subcheck_artifact_root) if subcheck_artifact_root else DEFAULT_SUBCHECK_ARTIFACT_ROOT
    redaction_values = tuple(clean_text(item) for item in (secret_redaction_values or ()) if clean_text(item))

    subchecks: list[dict[str, Any]] = []
    source_results: dict[str, dict[str, Any]] = {}

    clob_result = _run_subcheck(
        CLOB_SUBCHECK_ID,
        run_clob_l2_auth_readonly_probe,
        {
            "market": market_symbol,
            "strategy": strategy_name,
            "dry_run": True,
            "artifact_dir": _subcheck_artifact_dir(subcheck_root, CLOB_SUBCHECK_ID),
            "generated_at": generated_at,
            **({"environ": environ} if environ is not None else {}),
        },
        sequence_index=1,
        redaction_values=redaction_values,
        generated_at=generated_at,
    )
    source_results[CLOB_SUBCHECK_ID] = clob_result["result"]
    subchecks.append(clob_result["status"])

    account_result = _run_subcheck(
        LIVE_ACCOUNT_SUBCHECK_ID,
        run_live_account_readonly_state_probe,
        {
            "market": market_symbol,
            "strategy": strategy_name,
            "dry_run": True,
            "artifact_dir": _subcheck_artifact_dir(subcheck_root, LIVE_ACCOUNT_SUBCHECK_ID),
            "generated_at": generated_at,
            **({"environ": environ} if environ is not None else {}),
        },
        sequence_index=2,
        redaction_values=redaction_values,
        generated_at=generated_at,
    )
    source_results[LIVE_ACCOUNT_SUBCHECK_ID] = account_result["result"]
    subchecks.append(account_result["status"])

    signer_result = _run_subcheck(
        GUARDED_SIGNER_SUBCHECK_ID,
        run_guarded_signer_diagnostic_smoke,
        {
            "market": market_symbol,
            "strategy": strategy_name,
            "dry_run": True,
            "allow_private_key_diagnostic": allow_private_key_diagnostic is True,
            "artifact_dir": _subcheck_artifact_dir(subcheck_root, GUARDED_SIGNER_SUBCHECK_ID),
            "generated_at": generated_at,
            **({"env": environ} if environ is not None else {}),
        },
        sequence_index=3,
        redaction_values=redaction_values,
        generated_at=generated_at,
    )
    source_results[GUARDED_SIGNER_SUBCHECK_ID] = signer_result["result"]
    subchecks.append(signer_result["status"])

    discovery_result = _run_subcheck(
        PUBLIC_DISCOVERY_SUBCHECK_ID,
        run_public_market_token_discovery,
        {
            "market": market_symbol,
            "strategy": strategy_name,
            "dry_run": True,
            "query": public_discovery_query,
            "slug": public_discovery_slug,
            "tag_id": public_discovery_tag_id,
            "limit": public_discovery_limit,
            "artifact_dir": _subcheck_artifact_dir(subcheck_root, PUBLIC_DISCOVERY_SUBCHECK_ID),
            "local_artifact_paths": public_discovery_local_artifact_paths,
            "public_client": public_client,
            "generated_at": generated_at,
        },
        sequence_index=4,
        redaction_values=redaction_values,
        generated_at=generated_at,
    )
    source_results[PUBLIC_DISCOVERY_SUBCHECK_ID] = discovery_result["result"]
    subchecks.append(discovery_result["status"])

    discovery_path = _result_artifact_path(source_results[PUBLIC_DISCOVERY_SUBCHECK_ID])
    bridge_result = _run_subcheck(
        DISCOVERY_BRIDGE_SUBCHECK_ID,
        run_discovery_to_token_resolver_bridge,
        {
            "market": market_symbol,
            "strategy": strategy_name,
            "dry_run": True,
            "discovery_result_path": discovery_path or None,
            "discovery_artifacts_dir": _subcheck_artifact_dir(subcheck_root, PUBLIC_DISCOVERY_SUBCHECK_ID),
            "selected_candidate_id": selected_candidate_id,
            "artifact_dir": _subcheck_artifact_dir(subcheck_root, DISCOVERY_BRIDGE_SUBCHECK_ID),
            "generated_at": generated_at,
        },
        sequence_index=5,
        redaction_values=redaction_values,
        generated_at=generated_at,
    )
    source_results[DISCOVERY_BRIDGE_SUBCHECK_ID] = bridge_result["result"]
    subchecks.append(bridge_result["status"])

    aggregate_result = _run_subcheck(
        LIVE_STATUS_SUBCHECK_ID,
        run_live_readonly_status_aggregator,
        {
            "market": market_symbol,
            "strategy": strategy_name,
            "dry_run": True,
            "artifact_root": subcheck_root,
            "artifact_dir": _subcheck_artifact_dir(subcheck_root, LIVE_STATUS_SUBCHECK_ID),
            "generated_at": generated_at,
        },
        sequence_index=6,
        redaction_values=redaction_values,
        generated_at=generated_at,
    )
    source_results[LIVE_STATUS_SUBCHECK_ID] = aggregate_result["result"]
    subchecks.append(aggregate_result["status"])

    blockers = _build_consolidated_blockers(
        subchecks=subchecks,
        source_results=source_results,
        redaction_values=redaction_values,
        generated_at=generated_at,
    )
    status = bundle_status_from_subchecks(subchecks, blockers)
    safety_snapshot = build_safety_snapshot(
        market=market_symbol,
        strategy=strategy_name,
        private_key_diagnostic_requested=allow_private_key_diagnostic is True,
        generated_at=generated_at,
    )
    latest_status = LocalRealCheckBundleLatestStatus(
        market=market_symbol,
        strategy=strategy_name,
        status=status,
        subchecks=tuple(subchecks),
        blocker_count=len(blockers),
        artifact_paths=path_refs,
        private_key_diagnostic_requested=allow_private_key_diagnostic is True,
        generated_at=generated_at,
    ).to_dict()
    result = LocalRealCheckBundleResult(
        market=market_symbol,
        strategy=strategy_name,
        status=status,
        subchecks=tuple(subchecks),
        blockers=tuple(blockers),
        latest_status=latest_status,
        safety_snapshot=safety_snapshot,
        artifact_paths=path_refs,
        operator_summary=_operator_summary(latest_status),
        private_key_diagnostic_requested=allow_private_key_diagnostic is True,
        generated_at=generated_at,
    ).to_dict()
    subchecks_artifact = build_subchecks_artifact(subchecks, generated_at=generated_at)
    blockers_artifact = build_blockers_artifact(blockers, generated_at=generated_at)

    write_json(paths["subchecks"], subchecks_artifact)
    write_json(paths["blockers"], blockers_artifact)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_summary"], render_local_real_check_bundle_markdown(result))
    return result


def render_local_real_check_bundle_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    subcheck_statuses = dict(value.get("subcheck_statuses", {}))
    lines = [
        "Local real-check bundle 072C completed.",
        f"Status: {clean_text(value.get('status'))}",
        f"Market: {clean_text(value.get('market'))}",
        f"Strategy: {clean_text(value.get('strategy'))}",
        f"Subchecks completed: {int(value.get('subcheck_completed_count', 0) or 0)}/{int(value.get('subcheck_count', 0) or 0)}",
        f"Subchecks failed: {int(value.get('subcheck_failed_count', 0) or 0)}",
        f"Subchecks blocked: {int(value.get('subcheck_blocked_count', 0) or 0)}",
        f"Blockers: {int(value.get('blocker_count', 0) or 0)}",
        f"Private key diagnostic requested: {str(value.get('private_key_diagnostic_requested') is True).lower()}",
        "Allowed for live: false",
        "Bundle executable for live: false",
        "Order submission: blocked",
        "Order cancellation: blocked",
        "Order payload signing: blocked",
        "Trading write endpoints: blocked",
    ]
    lines.extend(
        f"{SUBCHECK_LABELS.get(subcheck_id, subcheck_id)}: {clean_text(subcheck_statuses.get(subcheck_id)) or 'unknown'}"
        for subcheck_id in SUBCHECK_SEQUENCE
    )
    lines.append(f"Artifact: {clean_text(value.get('artifact_path'))}")
    return "\n".join(lines)


def render_local_real_check_bundle_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    subchecks = [dict(row) for row in value.get("subchecks", []) if isinstance(row, Mapping)]
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    lines = [
        "# PMBOT Local Real-Check Bundle 072C",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market')}`",
        f"- Strategy: `{value.get('strategy')}`",
        "- Manual one-shot only: `true`",
        "- Allowed for live: `false`",
        "- Bundle executable for live: `false`",
        f"- Private key diagnostic requested: `{str(value.get('private_key_diagnostic_requested') is True).lower()}`",
        f"- Subchecks completed: `{latest.get('subcheck_completed_count')}/{latest.get('subcheck_count')}`",
        f"- Subchecks failed: `{latest.get('subcheck_failed_count')}`",
        f"- Subchecks blocked: `{latest.get('subcheck_blocked_count')}`",
        f"- Blockers: `{value.get('blocker_count')}`",
        "",
        "## Subchecks",
        "",
        *bullet_lines(
            f"`{row.get('subcheck_id')}` status=`{row.get('status')}` classification=`{row.get('classification')}` artifact=`{row.get('artifact_path') or 'missing'}`"
            for row in subchecks
        ),
        "",
        "## Consolidated Blockers",
        "",
        *bullet_lines(
            f"`{row.get('blocker_id')}` `{row.get('subcheck_id') or 'bundle'}` - {row.get('reason')}"
            for row in blockers
        ),
        "",
        "## Safety",
        "",
        "- no order submission or cancellation",
        "- no order payload signing",
        "- no trading write endpoint is called",
        "- no live trading enablement is produced",
        "- no raw secret value is written by the bundle",
        "- subcheck failures remain visible in `local_real_check_bundle_subchecks_072c.json`",
        "- `allowed_for_live=false` and `bundle_executable_for_live=false` are forced",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "local real-check bundle is dry-run/no-live; unsupported live/auth/wallet/sign/order/browser/loop flag(s): "
            + ", ".join(requested)
        )


def _run_subcheck(
    subcheck_id: str,
    runner: Runner,
    kwargs: Mapping[str, Any],
    *,
    sequence_index: int,
    redaction_values: Sequence[str],
    generated_at: str,
) -> dict[str, Any]:
    try:
        result = runner(**dict(kwargs))
        status = _subcheck_status_from_result(
            subcheck_id=subcheck_id,
            result=result,
            sequence_index=sequence_index,
            redaction_values=redaction_values,
            generated_at=generated_at,
        )
        return {"result": dict(result), "status": status}
    except Exception as exc:
        status_text = "subcheck_exception_preserved_live_blocked"
        status = LocalRealCheckBundleSubcheckStatus(
            subcheck_id=subcheck_id,
            subcheck_label=SUBCHECK_LABELS.get(subcheck_id, subcheck_id),
            sequence_index=sequence_index,
            status=status_text,
            classification="failed",
            completed=False,
            failed=True,
            exception_type=type(exc).__name__,
            error_message_sanitized=_sanitize_text(str(exc), redaction_values),
            blocker_count=1,
            source_blocker_count=0,
            status_fields={},
            generated_at=generated_at,
        ).to_dict()
        return {"result": {}, "status": status}


def _subcheck_status_from_result(
    *,
    subcheck_id: str,
    result: Mapping[str, Any],
    sequence_index: int,
    redaction_values: Sequence[str],
    generated_at: str,
) -> dict[str, Any]:
    latest = _latest_status_payload(result)
    status_text = clean_text(latest.get("status") or result.get("status")) or "unknown"
    blockers = _source_blockers(result, latest)
    classification = classify_subcheck_status(status_text, failed=False)
    status_fields = _status_fields_for_subcheck(subcheck_id, result=result, latest=latest)
    return LocalRealCheckBundleSubcheckStatus(
        subcheck_id=subcheck_id,
        subcheck_label=SUBCHECK_LABELS.get(subcheck_id, subcheck_id),
        sequence_index=sequence_index,
        status=_sanitize_text(status_text, redaction_values),
        classification=classification,
        completed=True,
        failed=False,
        artifact_path=_artifact_path(result, latest),
        latest_status_path=_latest_status_path(result, latest),
        blocker_count=len(blockers) + (1 if classification in {"blocked", "unknown"} and not blockers else 0),
        source_blocker_count=len(blockers),
        status_fields=status_fields,
        generated_at=generated_at,
    ).to_dict()


def _build_consolidated_blockers(
    *,
    subchecks: Sequence[Mapping[str, Any]],
    source_results: Mapping[str, Mapping[str, Any]],
    redaction_values: Sequence[str],
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for row in subchecks:
        subcheck_id = clean_text(row.get("subcheck_id"))
        source_status = clean_text(row.get("status"))
        source_result = dict(source_results.get(subcheck_id, {}))
        source_latest = _latest_status_payload(source_result)
        source_blockers = _source_blockers(source_result, source_latest)
        if row.get("failed") is True:
            blockers.append(
                LocalRealCheckBundleBlocker(
                    blocker_id=f"{subcheck_id}:subcheck_exception",
                    blocker_category="subcheck_failure",
                    subcheck_id=subcheck_id,
                    source_status=source_status,
                    reason=_sanitize_text(
                        clean_text(row.get("error_message_sanitized"))
                        or "Subcheck raised an exception; no success was inferred.",
                        redaction_values,
                    ),
                    generated_at=generated_at,
                ).to_dict()
            )
        for index, source_blocker in enumerate(source_blockers, start=1):
            blocker_value = dict(source_blocker)
            blockers.append(
                LocalRealCheckBundleBlocker(
                    blocker_id=f"{subcheck_id}:{clean_text(blocker_value.get('blocker_id')) or index}",
                    blocker_category=clean_text(blocker_value.get("blocker_category")) or "subcheck_blocker",
                    subcheck_id=subcheck_id,
                    source_status=source_status,
                    source_blocker_id=clean_text(blocker_value.get("blocker_id")),
                    reason=_sanitize_text(
                        clean_text(blocker_value.get("reason")) or "Subcheck reported an unresolved blocker.",
                        redaction_values,
                    ),
                    severity=clean_text(blocker_value.get("severity")) or "critical",
                    generated_at=generated_at,
                ).to_dict()
            )
        if row.get("classification") in {"blocked", "unknown"} and not source_blockers:
            blockers.append(
                LocalRealCheckBundleBlocker(
                    blocker_id=f"{subcheck_id}:reported_{row.get('classification')}",
                    blocker_category="subcheck_status",
                    subcheck_id=subcheck_id,
                    source_status=source_status,
                    reason=f"Subcheck reported status {source_status}; the bundle did not infer success.",
                    generated_at=generated_at,
                ).to_dict()
            )
    blockers.extend(
        [
            LocalRealCheckBundleBlocker(
                blocker_id="local_real_check_bundle_allowed_for_live_false",
                blocker_category="live_execution",
                reason="The local real-check bundle is an operator diagnostic only and always sets allowed_for_live=false.",
                generated_at=generated_at,
            ).to_dict(),
            LocalRealCheckBundleBlocker(
                blocker_id="local_real_check_bundle_not_executable_for_live",
                blocker_category="live_execution",
                reason="The bundle output is not an executable live-trading packet.",
                generated_at=generated_at,
            ).to_dict(),
        ]
    )
    return _dedupe_blockers(blockers)


def _status_fields_for_subcheck(
    subcheck_id: str,
    *,
    result: Mapping[str, Any],
    latest: Mapping[str, Any],
) -> dict[str, Any]:
    latest_value = dict(latest)
    result_value = dict(result)
    if subcheck_id == CLOB_SUBCHECK_ID:
        return _pick_status_fields(
            latest_value,
            (
                "auth_verified",
                "credential_presence_status",
                "sdk_status",
                "balance_allowance_probe_status",
                "l2_authenticated_readonly_probe_attempted",
                "l2_authenticated_readonly_probe_performed",
            ),
        )
    if subcheck_id == LIVE_ACCOUNT_SUBCHECK_ID:
        return _pick_status_fields(
            latest_value,
            (
                "credential_presence_status",
                "sdk_status",
                "account_status",
                "open_orders_status",
                "balance_allowance_status",
                "balance_allowance_availability_status",
                "wallet_address_status",
                "signature_type_status",
                "funder_address_status",
                "account_state_probe_attempted",
                "account_state_probe_performed",
            ),
        )
    if subcheck_id == GUARDED_SIGNER_SUBCHECK_ID:
        return {
            "diagnostic_requested": latest_value.get("diagnostic_requested") is True,
            "diagnostic_private_key_read": latest_value.get("private_key_read") is True,
            "diagnostic_challenge_signed": latest_value.get("diagnostic_challenge_signed") is True,
            "derived_wallet_matches_expected": clean_text(latest_value.get("derived_wallet_matches_expected")),
            "diagnostic_status": clean_text(latest_value.get("diagnostic_status")),
        }
    if subcheck_id == PUBLIC_DISCOVERY_SUBCHECK_ID:
        return _pick_status_fields(
            result_value,
            (
                "source_records_attempted",
                "market_candidate_count",
                "outcome_token_candidate_count",
            ),
        )
    if subcheck_id == DISCOVERY_BRIDGE_SUBCHECK_ID:
        return _pick_status_fields(
            result_value,
            (
                "source_discovery_artifact_present",
                "source_backed_candidate_count",
                "valid_source_backed_candidate_count",
                "invalid_source_backed_token_count",
            ),
        ) | _pick_status_fields(
            latest_value,
            (
                "operator_selection_required",
                "target_token_id_present",
                "target_token_id_source_backed",
            ),
        )
    if subcheck_id == LIVE_STATUS_SUBCHECK_ID:
        return _pick_status_fields(
            latest_value,
            (
                "l2_auth_status",
                "open_orders_status",
                "balance_status",
                "allowance_status",
                "wallet_address_status",
                "funder_status",
                "signature_type_status",
                "source_available_count",
                "unknown_status_count",
            ),
        )
    return {}


def _pick_status_fields(payload: Mapping[str, Any], keys: Sequence[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in keys:
        if key in payload:
            result[key] = payload[key]
    return result


def _latest_status_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    latest = result.get("latest_status")
    if isinstance(latest, Mapping):
        return dict(latest)
    return dict(result)


def _source_blockers(result: Mapping[str, Any], latest: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in (result.get("blockers"), latest.get("blockers")):
        if not isinstance(source, list):
            continue
        for row in source:
            if isinstance(row, Mapping):
                rows.append(dict(row))
    return _dedupe_blockers(rows)


def _artifact_path(result: Mapping[str, Any], latest: Mapping[str, Any]) -> str:
    candidates = (
        latest.get("artifact_path"),
        latest.get("result_path"),
        _mapping_get(result.get("artifact_paths"), "result"),
        _mapping_get(latest.get("artifact_paths"), "result"),
    )
    return _first_text(*candidates)


def _result_artifact_path(result: Mapping[str, Any]) -> str:
    latest = _latest_status_payload(result)
    return _artifact_path(result, latest)


def _latest_status_path(result: Mapping[str, Any], latest: Mapping[str, Any]) -> str:
    candidates = (
        latest.get("latest_status_path"),
        _mapping_get(result.get("artifact_paths"), "latest_status"),
        _mapping_get(latest.get("artifact_paths"), "latest_status"),
    )
    return _first_text(*candidates)


def _mapping_get(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return None


def _subcheck_artifact_dir(root: Path, subcheck_id: str) -> Path:
    return root / SUBCHECK_ARTIFACT_DIR_NAMES[subcheck_id]


def _operator_summary(latest_status: Mapping[str, Any]) -> str:
    value = dict(latest_status or {})
    return (
        "Local real-check bundle completed with status="
        + clean_text(value.get("status"))
        + "; subchecks_completed="
        + str(int(value.get("subcheck_completed_count", 0) or 0))
        + "/"
        + str(int(value.get("subcheck_count", 0) or 0))
        + "; blockers="
        + str(int(value.get("blocker_count", 0) or 0))
        + "; allowed_for_live=false; bundle_executable_for_live=false; no submit, cancel, order-payload signing, live enablement, or trading write endpoint was added."
    )


def _first_text(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def _sanitize_text(value: Any, redaction_values: Sequence[str]) -> str:
    text = clean_text(value)
    if not text:
        return ""
    redacted = text
    for raw in redaction_values:
        raw_text = clean_text(raw)
        if raw_text:
            redacted = redacted.replace(raw_text, "[REDACTED]")
    redacted = re.sub(r"0x[0-9a-fA-F]{64}", "[REDACTED_HEX_64]", redacted)
    redacted = re.sub(r"0x[0-9a-fA-F]{40}", "[REDACTED_ADDRESS]", redacted)
    redacted = re.sub(r"(?i)(api[_-]?secret|passphrase|private[_-]?key)=\S+", r"\1=[REDACTED]", redacted)
    return redacted[:500]


def _dedupe_blockers(blockers: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in blockers:
        value = dict(row)
        key = clean_text(value.get("blocker_id")) or clean_text(value.get("reason"))
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


__all__ = [
    "DEFAULT_ARTIFACT_DIR",
    "DEFAULT_SUBCHECK_ARTIFACT_ROOT",
    "fail_closed_for_forbidden_flags",
    "local_real_check_bundle_artifact_paths",
    "local_real_check_bundle_safety_flags",
    "render_local_real_check_bundle_cli_summary",
    "render_local_real_check_bundle_markdown",
    "run_local_real_check_bundle",
    "TASK_ID",
]
