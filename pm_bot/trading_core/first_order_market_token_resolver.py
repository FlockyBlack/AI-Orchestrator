from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.first_order_market_token_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    EXECUTION_MODE,
    FIRST_ORDER_MARKET_TOKEN_RESULT_CONTRACT,
    FirstOrderMarketTokenContract,
    FirstOrderMarketTokenLatestStatus,
    MODE,
    STATUS_BLOCKED_INVALID_CONDITION_ID,
    STATUS_BLOCKED_INVALID_MARKET_SLUG,
    STATUS_BLOCKED_INVALID_TOKEN_ID,
    STATUS_BLOCKED_MISSING_TOKEN_ID,
    STATUS_BLOCKED_SCOPE_MISMATCH,
    STATUS_READY,
    TASK_ID,
    first_order_market_token_safety_flags,
    validate_first_order_market_token_result,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b")

MARKET_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,198}[a-z0-9]$")
CONDITION_ID_PATTERN = re.compile(r"^0x[0-9a-fA-F]{64}$")
TOKEN_ID_PATTERN = re.compile(r"^[1-9][0-9]{0,77}$")

LOCAL_MARKET_DISCOVERY_ARTIFACTS = (
    Path("pm_bot/trading_core/artifacts/public_market_paper_loop_054/normalized_public_market_snapshot_054.json"),
    Path("pm_bot/trading_core/artifacts/public_market_paper_loop_054/public_market_evidence_pack_054.json"),
    Path("pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_normalized_market_052.json"),
    Path("pm_bot/trading_core/artifacts/paper_trading_loop_053/paper_trading_market_snapshot_053.json"),
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
    "--sign",
    "--signing",
    "--submit",
    "--cancel",
    "--approve-live",
    "--private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--order-payload",
)


def first_order_market_token_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "first_order_market_token_resolver_070b_result.json",
        "latest_status": root / "latest_first_order_market_token_status_070b.json",
        "target_contract": root / "first_order_market_token_contract_070b.json",
        "validation": root / "first_order_market_token_validation_070b.json",
        "operator_md": root / "first_order_market_token_operator_summary_070b.md",
    }


def run_first_order_market_token_resolver(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    market_slug: str = "",
    condition_id: str = "",
    token_id: str = "",
    outcome_name: str = "",
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("first order market/token resolver requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    market_slug_text = clean_text(market_slug)
    condition_id_text = clean_text(condition_id)
    token_id_text = clean_text(token_id)
    outcome_text = clean_text(outcome_name)
    paths = first_order_market_token_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    scope_valid = market_symbol == DEFAULT_ALLOWED_MARKET and strategy_name == DEFAULT_ALLOWED_STRATEGY
    market_slug_format_status = validate_market_slug_format(market_slug_text)
    condition_id_format_status = validate_condition_id_format(condition_id_text)
    token_id_format_status = validate_token_id_format(token_id_text)
    status = _status_for_inputs(
        scope_valid=scope_valid,
        market_slug_format_status=market_slug_format_status,
        condition_id_format_status=condition_id_format_status,
        token_id_format_status=token_id_format_status,
    )
    local_refs = tuple(_local_market_discovery_references())
    blockers = tuple(
        _build_blockers(
            status=status,
            scope_valid=scope_valid,
            market_slug_format_status=market_slug_format_status,
            condition_id_format_status=condition_id_format_status,
            token_id_format_status=token_id_format_status,
            generated_at=generated_at,
        )
    )

    target_contract = FirstOrderMarketTokenContract(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        market_slug=market_slug_text,
        condition_id=condition_id_text,
        token_id=token_id_text if token_id_format_status == "valid" else "",
        outcome_name=outcome_text,
        scope_valid=scope_valid,
        market_slug_format_status=market_slug_format_status,
        condition_id_format_status=condition_id_format_status,
        token_id_format_status=token_id_format_status,
        token_id_source="explicit_cli" if token_id_text else "missing_explicit_cli",
        local_market_discovery_artifacts=local_refs,
        blockers=blockers,
        generated_at=generated_at,
    ).to_dict()
    latest_status = FirstOrderMarketTokenLatestStatus(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        market_slug=market_slug_text,
        condition_id=condition_id_text,
        token_id=target_contract["token_id"],
        token_id_format_status=token_id_format_status,
        token_id_source=target_contract["token_id_source"],
        blocker_count=len(blockers),
        artifact_path=path_refs["result"],
        latest_status_path=path_refs["latest_status"],
        target_contract_path=path_refs["target_contract"],
        validation_path=path_refs["validation"],
        operator_markdown_path=path_refs["operator_md"],
        generated_at=generated_at,
    ).to_dict()
    result: dict[str, Any] = {
        "contract_version": FIRST_ORDER_MARKET_TOKEN_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "dry_run": True,
        "target_contract_only": True,
        "target_contract_executable": False,
        "target_contract": target_contract,
        "latest_status": latest_status,
        "local_market_discovery_artifacts": [dict(row) for row in local_refs],
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary(status),
        "generated_at": generated_at,
    }
    result.update(first_order_market_token_safety_flags())
    validation = validate_first_order_market_token_result(result, generated_at=generated_at)
    result["validation"] = validation

    write_json(paths["target_contract"], target_contract)
    write_json(paths["validation"], validation)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_first_order_market_token_markdown(result))
    return result


def validate_market_slug_format(value: str) -> str:
    text = clean_text(value)
    if not text:
        return "missing_optional"
    return "valid" if MARKET_SLUG_PATTERN.fullmatch(text) else "invalid"


def validate_condition_id_format(value: str) -> str:
    text = clean_text(value)
    if not text:
        return "missing_optional"
    return "valid" if CONDITION_ID_PATTERN.fullmatch(text) else "invalid"


def validate_token_id_format(value: str) -> str:
    text = clean_text(value)
    if not text:
        return "missing_required"
    return "valid" if TOKEN_ID_PATTERN.fullmatch(text) else "invalid"


def render_first_order_market_token_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    token_display = clean_text(value.get("token_id")) or "missing"
    return "\n".join(
        [
            "First order market token resolver 070B completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Market slug: {clean_text(value.get('market_slug')) or 'missing'}",
            f"Condition id: {clean_text(value.get('condition_id')) or 'missing'}",
            f"Token id: {token_display}",
            f"Token id format: {clean_text(value.get('token_id_format_status'))}",
            "Token id generated: false",
            "Allowed for live: false",
            "Order generation: blocked",
            "Signing: blocked",
            "Order submission: blocked",
            "Authenticated trading: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_first_order_market_token_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    target = dict(value.get("target_contract", {}))
    latest = dict(value.get("latest_status", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    local_refs = [
        dict(row) for row in value.get("local_market_discovery_artifacts", []) if isinstance(row, Mapping)
    ]
    lines = [
        "# PMBOT First Order Market Token Resolver 070B",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `first order market token resolver / dry-run / no-trading`",
        "- target_contract_only: `true`",
        "- target_contract_executable: `false`",
        "- allowed_for_live: `false`",
        "",
        "## Target Contract",
        "",
        f"- market_slug: `{target.get('market_slug') or 'missing'}`",
        f"- condition_id: `{target.get('condition_id') or 'missing'}`",
        f"- token_id: `{target.get('token_id') or 'missing'}`",
        f"- token_id_source: `{target.get('token_id_source')}`",
        f"- token_id_format_status: `{target.get('token_id_format_status')}`",
        "- token_id_generated: `false`",
        "- fake_token_id_generated: `false`",
        "",
        "## Safety",
        "",
        "- no order payload generated",
        "- no signing attempted",
        "- no order submission attempted",
        "- no order cancellation attempted",
        "- no wallet connection attempted",
        "- no authenticated trading call attempted",
        "- no network trading call attempted",
        "- no browser automation added",
        "- no scheduler, daemon, background worker, or autonomous loop added",
        "",
        "## Local References",
        "",
        *bullet_lines(
            f"`{row.get('path')}` exists={str(row.get('exists') is True).lower()} used_for_token_id=false"
            for row in local_refs
        ),
        "",
        "## Blockers",
        "",
        *bullet_lines(row.get("reason") for row in blockers),
        "",
        "## Next Operator Action",
        "",
        f"- {latest.get('next_operator_action')}",
        f"- Latest status path: `{latest.get('latest_status_path')}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "first order market/token resolver is no-trading; unsupported live/auth/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _status_for_inputs(
    *,
    scope_valid: bool,
    market_slug_format_status: str,
    condition_id_format_status: str,
    token_id_format_status: str,
) -> str:
    if scope_valid is not True:
        return STATUS_BLOCKED_SCOPE_MISMATCH
    if market_slug_format_status == "invalid":
        return STATUS_BLOCKED_INVALID_MARKET_SLUG
    if condition_id_format_status == "invalid":
        return STATUS_BLOCKED_INVALID_CONDITION_ID
    if token_id_format_status == "missing_required":
        return STATUS_BLOCKED_MISSING_TOKEN_ID
    if token_id_format_status == "invalid":
        return STATUS_BLOCKED_INVALID_TOKEN_ID
    return STATUS_READY


def _build_blockers(
    *,
    status: str,
    scope_valid: bool,
    market_slug_format_status: str,
    condition_id_format_status: str,
    token_id_format_status: str,
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if scope_valid is not True:
        blockers.append(
            _blocker(
                "scope_mismatch",
                "scope",
                "Resolver scope is limited to BTC market and tiny-momentum strategy.",
                generated_at=generated_at,
            )
        )
    if market_slug_format_status == "invalid":
        blockers.append(
            _blocker(
                "invalid_market_slug_format",
                "market_slug",
                "market_slug format validation failed; expected lowercase letters, numbers, and hyphens.",
                generated_at=generated_at,
            )
        )
    if condition_id_format_status == "invalid":
        blockers.append(
            _blocker(
                "invalid_condition_id_format",
                "condition_id",
                "condition_id format validation failed; expected 0x-prefixed 32-byte hex string.",
                generated_at=generated_at,
            )
        )
    if token_id_format_status == "missing_required":
        blockers.append(
            _blocker(
                "missing_token_id",
                "token_id",
                "No explicit token_id was provided; the resolver must not invent or infer one.",
                generated_at=generated_at,
            )
        )
    if token_id_format_status == "invalid":
        blockers.append(
            _blocker(
                "invalid_token_id_format",
                "token_id",
                "token_id format validation failed; expected a positive decimal string.",
                generated_at=generated_at,
            )
        )
    blockers.extend(
        [
            _blocker(
                "live_execution_blocked",
                "live_execution",
                "allowed_for_live=false and this task does not authorize live execution.",
                generated_at=generated_at,
            ),
            _blocker(
                "order_generation_blocked",
                "order_generation",
                "Only a market/token target contract may be produced; no order payload is generated.",
                generated_at=generated_at,
            ),
            _blocker(
                "signing_blocked",
                "signing",
                "Signing and signed payload generation remain blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "submission_and_cancel_blocked",
                "submission",
                "Order submission and cancellation remain blocked.",
                generated_at=generated_at,
            ),
            _blocker(
                "authenticated_trading_blocked",
                "authenticated_trading",
                "Authenticated trading calls are not performed by this resolver.",
                generated_at=generated_at,
            ),
        ]
    )
    if status == STATUS_READY:
        blockers.append(
            _blocker(
                "separate_operator_approval_required",
                "operator_approval",
                "A valid target contract is still review-only and requires a separate operator-approved task.",
                generated_at=generated_at,
            )
        )
    return blockers


def _blocker(blocker_id: str, category: str, reason: str, *, generated_at: str) -> dict[str, Any]:
    value = {
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_live_execution": True,
        "generated_at": generated_at,
    }
    value.update(first_order_market_token_safety_flags())
    return value


def _local_market_discovery_references() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in LOCAL_MARKET_DISCOVERY_ARTIFACTS:
        rows.append(
            {
                "path": normalize_path(path),
                "exists": path.exists(),
                "reference_only": True,
                "used_for_token_id": False,
                "token_id_ingested": False,
                "network_access_performed": False,
            }
        )
    return rows


def _operator_summary(status: str) -> str:
    if status == STATUS_BLOCKED_MISSING_TOKEN_ID:
        return "Resolver blocked because token_id is missing; no fake token_id was generated."
    if status == STATUS_READY:
        return "Resolver accepted the explicit token_id format and produced a review-only target contract."
    return "Resolver blocked on scope or input format validation before any live-capable action."
