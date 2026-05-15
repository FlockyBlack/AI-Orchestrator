from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.first_live_order_approval_models import (
    APPROVAL_TIMEOUT_MINUTES,
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    EXACT_REQUIRED_APPROVAL_TEXT,
    MAX_NOTIONAL_USD,
    MAX_ORDERS_PER_DAY,
    STATUS_DEFINED_EXECUTION_BLOCKED,
    STATUS_SCOPE_BLOCKED,
    FirstLiveOrderApprovalAuditRecordTemplate,
    FirstLiveOrderApprovalContractResult,
    FirstLiveOrderApprovalLimits,
    FirstLiveOrderApprovalRevocationPolicy,
    FirstLiveOrderApprovalScope,
    FirstLiveOrderApprovalTimeoutPolicy,
    FirstLiveOrderRequiredApprovalText,
    LatestFirstLiveOrderApprovalContractStatus,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/first_live_order_approval_contract_065d")

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
    "--approve",
    "--approve-live",
    "--record-approval",
    "--private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
    "--scheduler",
    "--daemon",
    "--background-loop",
)


def first_live_order_approval_contract_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "first_live_order_approval_contract_065d_result.json",
        "latest_status": root / "latest_first_live_order_approval_contract_status_065d.json",
        "approval_text": root / "first_live_order_required_approval_text_065d.json",
        "approval_scope": root / "first_live_order_approval_scope_065d.json",
        "approval_limits": root / "first_live_order_approval_limits_065d.json",
        "revocation_policy": root / "first_live_order_approval_revocation_policy_065d.json",
        "timeout_policy": root / "first_live_order_approval_timeout_policy_065d.json",
        "audit_template": root / "first_live_order_approval_audit_record_template_065d.json",
        "operator_summary": root / "first_live_order_approval_operator_summary_065d.md",
    }


def run_first_live_order_approval_contract(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("first live order approval contract requires --dry-run; execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = first_live_order_approval_contract_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    approval_text = FirstLiveOrderRequiredApprovalText(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    approval_scope = FirstLiveOrderApprovalScope(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    approval_limits = FirstLiveOrderApprovalLimits(generated_at=generated_at).to_dict()
    revocation_policy = FirstLiveOrderApprovalRevocationPolicy(generated_at=generated_at).to_dict()
    timeout_policy = FirstLiveOrderApprovalTimeoutPolicy(generated_at=generated_at).to_dict()
    audit_template = FirstLiveOrderApprovalAuditRecordTemplate(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    status = (
        STATUS_DEFINED_EXECUTION_BLOCKED
        if approval_scope.get("scope_valid") is True
        else STATUS_SCOPE_BLOCKED
    )
    latest_status = LatestFirstLiveOrderApprovalContractStatus(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        approval_text_path=path_refs["approval_text"],
        scope_path=path_refs["approval_scope"],
        limits_path=path_refs["approval_limits"],
        revocation_policy_path=path_refs["revocation_policy"],
        timeout_policy_path=path_refs["timeout_policy"],
        audit_template_path=path_refs["audit_template"],
        result_path=path_refs["result"],
        operator_summary_path=path_refs["operator_summary"],
        generated_at=generated_at,
    ).to_dict()
    result = FirstLiveOrderApprovalContractResult(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        required_approval_text=approval_text,
        approval_scope=approval_scope,
        approval_limits=approval_limits,
        revocation_policy=revocation_policy,
        timeout_policy=timeout_policy,
        audit_record_template=audit_template,
        latest_status=latest_status,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["approval_text"], approval_text)
    write_json(paths["approval_scope"], approval_scope)
    write_json(paths["approval_limits"], approval_limits)
    write_json(paths["revocation_policy"], revocation_policy)
    write_json(paths["timeout_policy"], timeout_policy)
    write_json(paths["audit_template"], audit_template)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_summary"], render_first_live_order_approval_contract_markdown(result))
    return result


def render_first_live_order_approval_contract_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "First live order approval contract completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Max notional USD: {float(value.get('max_notional_usd', 0) or 0):.2f}",
            f"Max orders per day: {int(value.get('max_orders_per_day', 0) or 0)}",
            f"Approval timeout minutes: {int(value.get('approval_timeout_minutes', 0) or 0)}",
            f"One-shot only: {str(value.get('one_shot_only') is True).lower()}",
            "Approval contract executable: false",
            "Allowed for live: false",
            "No approval means no execution: true",
            f"Required approval text artifact: {clean_text(value.get('approval_text_path'))}",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_first_live_order_approval_contract_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    scope = dict(value.get("approval_scope", {}))
    limits = dict(value.get("approval_limits", {}))
    timeout = dict(value.get("timeout_policy", {}))
    revocation = dict(value.get("revocation_policy", {}))
    audit_template = dict(value.get("audit_record_template", {}))
    lines = [
        "# PMBOT First Live Order Approval Contract 065D",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `definition-only / no execution`",
        "- approval_contract_executable: `false`",
        "- allowed_for_live: `false`",
        "- no approval means no execution",
        "",
        "## Exact Required Approval Text",
        "",
        "```text",
        EXACT_REQUIRED_APPROVAL_TEXT,
        "```",
        "",
        "## Scope",
        "",
        f"- allowed_markets: `{scope.get('allowed_markets')}`",
        f"- allowed_strategies: `{scope.get('allowed_strategies')}`",
        f"- scope_valid: `{str(scope.get('scope_valid') is True).lower()}`",
        "",
        "## Limits",
        "",
        f"- max_notional_usd: `{limits.get('max_notional_usd')}`",
        f"- max_orders_per_day: `{limits.get('max_orders_per_day')}`",
        f"- one_shot_only: `{str(limits.get('one_shot_only') is True).lower()}`",
        "- no scheduler, daemon, background loop, or autonomous repeat",
        "",
        "## Timeout",
        "",
        f"- approval_expires: `{str(timeout.get('approval_expires') is True).lower()}`",
        f"- approval_timeout_minutes: `{timeout.get('approval_timeout_minutes')}`",
        f"- expired_approval_blocks_future_use: `{str(timeout.get('expired_approval_blocks_future_use') is True).lower()}`",
        "",
        "## Revocation",
        "",
        f"- revocable_by_operator: `{str(revocation.get('revocable_by_operator') is True).lower()}`",
        f"- revocation_effect: `{revocation.get('revocation_effect')}`",
        "",
        "## Audit Template",
        "",
        *bullet_lines(audit_template.get("required_operator_artifacts", [])),
        "",
        "## Safety Boundary",
        "",
        "- this contract records no operator approval",
        "- this contract cannot perform a live action",
        "- no wallet connection, signer instantiation, signed payload, order action, authenticated trading call, credential read, fill, or PnL is produced",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "first live order approval contract is non-executable; unsupported live/auth/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )
