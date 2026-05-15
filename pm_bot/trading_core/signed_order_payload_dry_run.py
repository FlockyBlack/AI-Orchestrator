from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text
from pm_bot.trading_core.signed_order_payload_dry_run_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    DEFAULT_MAX_NOTIONAL_USD,
    EXECUTION_MODE,
    LOCAL_DIAGNOSTIC_STATUS_MAX_NOTIONAL_EXCEEDED,
    LOCAL_DIAGNOSTIC_STATUS_MISSING_TOKEN_ID,
    LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED,
    LOCAL_DIAGNOSTIC_STATUS_SIGNING_NOT_IMPLEMENTED,
    MODE,
    REQUIRED_FALSE_FLAGS,
    SIGNED_ORDER_PAYLOAD_CONTRACT_CONTRACT,
    SIGNED_ORDER_PAYLOAD_DRY_RUN_RESULT_CONTRACT,
    SIGNED_ORDER_PAYLOAD_LATEST_STATUS_CONTRACT,
    STATUS_BLOCKED_NO_SUBMIT,
    TASK_ID,
    SignedOrderPayloadRedactionPolicy,
    SignedOrderPayloadSafetyContract,
    signed_order_payload_safety_flags,
    validate_signed_order_payload_dry_run_result,
)

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a")

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
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
)


def signed_order_payload_dry_run_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "signed_order_payload_dry_run_070a_result.json",
        "latest_status": root / "latest_signed_order_payload_dry_run_status_070a.json",
        "payload_contract": root / "signed_order_payload_contract_070a.json",
        "redaction_policy": root / "signed_order_payload_redaction_policy_070a.json",
        "safety_contract": root / "signed_order_payload_safety_contract_070a.json",
        "operator_md": root / "signed_order_payload_operator_summary_070a.md",
    }


def build_signed_order_payload_dry_run(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    token_id: str = "",
    max_notional_usd: float = DEFAULT_MAX_NOTIONAL_USD,
    allow_local_order_payload_signing_diagnostic: bool = False,
    artifact_dir: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("signed order payload dry-run requires --dry-run; live execution is blocked")

    del env
    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    token_text = clean_text(token_id)
    notional = _normalize_notional(max_notional_usd)
    paths = signed_order_payload_dry_run_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    local_diagnostic = _local_signing_diagnostic_status(
        requested=allow_local_order_payload_signing_diagnostic is True,
        token_id=token_text,
        max_notional_usd=notional,
    )
    safety_contract = SignedOrderPayloadSafetyContract(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        max_notional_usd=notional,
        generated_at=generated_at,
    ).to_dict()
    redaction_policy = SignedOrderPayloadRedactionPolicy(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    payload_contract = _build_payload_contract(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        token_id=token_text,
        max_notional_usd=notional,
        local_diagnostic=local_diagnostic,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        payload_contract=payload_contract,
        local_diagnostic=local_diagnostic,
        path_refs=path_refs,
        generated_at=generated_at,
    )

    result = {
        "contract_version": SIGNED_ORDER_PAYLOAD_DRY_RUN_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED_NO_SUBMIT,
        "local_signing_diagnostic_status": local_diagnostic["local_signing_diagnostic_status"],
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "review_only": True,
        "preflight_only": True,
        "dry_run": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "local_artifact_only": True,
        "order_payload_contract_built": True,
        "order_payload_contract_executable": False,
        "deterministic_contract": True,
        "token_id_present": bool(token_text),
        "token_id_fingerprint_sha256": _sha256_text(token_text) if token_text else "",
        "max_notional_usd": notional,
        "max_notional_within_guard": notional <= DEFAULT_MAX_NOTIONAL_USD,
        "local_signing_diagnostic_requested": allow_local_order_payload_signing_diagnostic is True,
        "local_signing_diagnostic_requirements_met": local_diagnostic[
            "local_signing_diagnostic_requirements_met"
        ],
        "local_signing_diagnostic_block_reason": local_diagnostic["block_reason"],
        "signing_not_implemented": local_diagnostic["local_signing_diagnostic_status"]
        == LOCAL_DIAGNOSTIC_STATUS_SIGNING_NOT_IMPLEMENTED,
        "dependency_status": local_diagnostic["dependency_status"],
        "payload_contract": payload_contract,
        "safety_contract": safety_contract,
        "redaction_policy": redaction_policy,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary_for_status(local_diagnostic["local_signing_diagnostic_status"]),
        "generated_at": generated_at,
    }
    result.update(signed_order_payload_safety_flags())
    result["validation"] = validate_signed_order_payload_dry_run_result(result, generated_at=generated_at)

    write_json(paths["payload_contract"], payload_contract)
    write_json(paths["redaction_policy"], redaction_policy)
    write_json(paths["safety_contract"], safety_contract)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_signed_order_payload_dry_run_markdown(result))
    return result


def render_signed_order_payload_dry_run_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Signed order payload dry-run 070A completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Local signing diagnostic status: {clean_text(value.get('local_signing_diagnostic_status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Token id present: {str(value.get('token_id_present') is True).lower()}",
            f"Max notional USD: {value.get('max_notional_usd')}",
            "Private key read: false",
            "Local payload signing attempted: false",
            "Signed payload submit enabled: false",
            "Order submission enabled: false",
            "Order cancellation enabled: false",
            "Network writes: blocked",
            "Allowed for live: false",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_signed_order_payload_dry_run_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Signed Order Payload Dry-Run 070A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Local signing diagnostic status: `{value.get('local_signing_diagnostic_status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        f"- Token id present: `{str(value.get('token_id_present') is True).lower()}`",
        f"- Max notional USD: `{value.get('max_notional_usd')}`",
        "- Default mode reads private key: `false`",
        "- Order payload contract executable: `false`",
        "- Local payload signing attempted: `false`",
        "- Signed payload submit enabled: `false`",
        "- Order submission enabled: `false`",
        "- Order cancellation enabled: `false`",
        "- Authenticated trading enabled: `false`",
        "- Network writes performed: `false`",
        "- Allowed for live: `false`",
        "",
        "## Contract Scope",
        "",
        "- deterministic field contract only",
        "- token id value is represented only by presence and SHA-256 fingerprint",
        "- no private key, API secret, passphrase, wallet file, or browser wallet is read",
        "- no real SDK signing path is enabled in this task",
        "- optional local order payload signing diagnostic fails closed as `signing_not_implemented` once guards pass",
        "- no signed material is printed, stored, submitted, or canceled",
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"`{path}`" for path in paths.values()),
        "",
        "## Required False Flags",
        "",
        *bullet_lines(f"`{field}=false`" for field in REQUIRED_FALSE_FLAGS),
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "signed order payload dry-run is no-submit/no-cancel; unsupported live/auth/wallet/order flag(s): "
            + ", ".join(requested)
        )


def _build_payload_contract(
    *,
    market_symbol: str,
    strategy_name: str,
    token_id: str,
    max_notional_usd: float,
    local_diagnostic: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    fields = [
        _field_spec("market_symbol", "string", "review label; not a live market selection signal"),
        _field_spec("token_id", "string", "required only for a future separately approved local diagnostic"),
        _field_spec("strategy_name", "string", "operator review label"),
        _field_spec("side", "enum_placeholder", "field name only; no side value is selected by this dry-run"),
        _field_spec("outcome", "enum_placeholder", "field name only; no outcome value is selected by this dry-run"),
        _field_spec("price", "decimal_placeholder", "field name only; no executable price is emitted"),
        _field_spec("size", "decimal_placeholder", "field name only; no executable size is emitted"),
        _field_spec("max_notional_usd", "decimal", "must be less than or equal to 1.0 for future diagnostics"),
        _field_spec("order_type", "enum_placeholder", "field name only; no executable type is emitted"),
        _field_spec("time_in_force", "enum_placeholder", "field name only; no executable time policy is emitted"),
        _field_spec("operator_approval_reference", "string_placeholder", "future reference only; not approval here"),
        _field_spec("risk_decision_reference", "string_placeholder", "future reference only; not approval here"),
        _field_spec("connector_capability_reference", "string_placeholder", "future read-only capability reference"),
        _field_spec("wallet_boundary_reference", "string_placeholder", "future non-secret boundary reference"),
    ]
    fingerprint_payload = {
        "contract_version": SIGNED_ORDER_PAYLOAD_CONTRACT_CONTRACT,
        "task_id": TASK_ID,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "token_id_present": bool(token_id),
        "token_id_fingerprint_sha256": _sha256_text(token_id) if token_id else "",
        "max_notional_usd": max_notional_usd,
        "field_specs": fields,
    }
    value = {
        "contract_version": SIGNED_ORDER_PAYLOAD_CONTRACT_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED_NO_SUBMIT,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "contract_only": True,
        "deterministic_contract": True,
        "order_payload_contract_executable": False,
        "token_id_present": bool(token_id),
        "token_id_fingerprint_sha256": _sha256_text(token_id) if token_id else "",
        "max_notional_usd": max_notional_usd,
        "max_notional_within_guard": max_notional_usd <= DEFAULT_MAX_NOTIONAL_USD,
        "field_specs": fields,
        "field_count": len(fields),
        "local_signing_diagnostic_status": clean_text(
            local_diagnostic.get("local_signing_diagnostic_status")
        ),
        "payload_contract_fingerprint_sha256": _stable_hash(fingerprint_payload),
        "generated_at": generated_at,
    }
    value.update(signed_order_payload_safety_flags())
    return value


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    payload_contract: Mapping[str, Any],
    local_diagnostic: Mapping[str, Any],
    path_refs: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SIGNED_ORDER_PAYLOAD_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED_NO_SUBMIT,
        "local_signing_diagnostic_status": clean_text(
            local_diagnostic.get("local_signing_diagnostic_status")
        ),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "token_id_present": payload_contract.get("token_id_present") is True,
        "token_id_fingerprint_sha256": clean_text(payload_contract.get("token_id_fingerprint_sha256")),
        "max_notional_usd": payload_contract.get("max_notional_usd"),
        "max_notional_within_guard": payload_contract.get("max_notional_within_guard") is True,
        "local_signing_diagnostic_requested": local_diagnostic.get("local_signing_diagnostic_requested") is True,
        "local_signing_diagnostic_requirements_met": local_diagnostic.get(
            "local_signing_diagnostic_requirements_met"
        )
        is True,
        "local_signing_diagnostic_block_reason": clean_text(local_diagnostic.get("block_reason")),
        "payload_contract_fingerprint_sha256": clean_text(
            payload_contract.get("payload_contract_fingerprint_sha256")
        ),
        "artifact_path": clean_text(path_refs.get("result")),
        "latest_status_path": clean_text(path_refs.get("latest_status")),
        "payload_contract_path": clean_text(path_refs.get("payload_contract")),
        "redaction_policy_path": clean_text(path_refs.get("redaction_policy")),
        "safety_contract_path": clean_text(path_refs.get("safety_contract")),
        "operator_markdown_path": clean_text(path_refs.get("operator_md")),
        "operator_summary": _operator_summary_for_status(
            clean_text(local_diagnostic.get("local_signing_diagnostic_status"))
        ),
        "generated_at": generated_at,
    }
    value.update(signed_order_payload_safety_flags())
    return value


def _field_spec(field_name: str, expected_type: str, description: str) -> dict[str, Any]:
    return {
        "field_name": clean_text(field_name),
        "expected_type": clean_text(expected_type),
        "required_for_future_executable_task": True,
        "value_emitted_by_070a": False,
        "description": clean_text(description),
    }


def _local_signing_diagnostic_status(
    *,
    requested: bool,
    token_id: str,
    max_notional_usd: float,
) -> dict[str, Any]:
    base = {
        "local_signing_diagnostic_requested": requested is True,
        "local_signing_diagnostic_requirements_met": False,
        "local_signing_diagnostic_status": LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED,
        "dependency_status": "not_loaded",
        "block_reason": LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED,
    }
    if requested is not True:
        return base
    if max_notional_usd > DEFAULT_MAX_NOTIONAL_USD:
        base.update(
            {
                "local_signing_diagnostic_status": LOCAL_DIAGNOSTIC_STATUS_MAX_NOTIONAL_EXCEEDED,
                "block_reason": LOCAL_DIAGNOSTIC_STATUS_MAX_NOTIONAL_EXCEEDED,
            }
        )
        return base
    if not clean_text(token_id):
        base.update(
            {
                "local_signing_diagnostic_status": LOCAL_DIAGNOSTIC_STATUS_MISSING_TOKEN_ID,
                "block_reason": LOCAL_DIAGNOSTIC_STATUS_MISSING_TOKEN_ID,
            }
        )
        return base
    base.update(
        {
            "local_signing_diagnostic_requirements_met": True,
            "local_signing_diagnostic_status": LOCAL_DIAGNOSTIC_STATUS_SIGNING_NOT_IMPLEMENTED,
            "dependency_status": "not_loaded",
            "block_reason": LOCAL_DIAGNOSTIC_STATUS_SIGNING_NOT_IMPLEMENTED,
        }
    )
    return base


def _operator_summary_for_status(local_status: str) -> str:
    summaries = {
        LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED: (
            "Default dry-run generated a deterministic non-executable payload contract without reading keys, "
            "signing, submitting, canceling, or making network writes."
        ),
        LOCAL_DIAGNOSTIC_STATUS_MAX_NOTIONAL_EXCEEDED: (
            "The optional local signing diagnostic was requested, but the max notional guard exceeded 1 USD. "
            "The runner failed closed before any signing path."
        ),
        LOCAL_DIAGNOSTIC_STATUS_MISSING_TOKEN_ID: (
            "The optional local signing diagnostic was requested, but no token id was provided. The runner "
            "failed closed before any signing path."
        ),
        LOCAL_DIAGNOSTIC_STATUS_SIGNING_NOT_IMPLEMENTED: (
            "The optional local signing diagnostic guards passed, but real SDK signing is intentionally not "
            "implemented in 070A. The runner failed closed with no signed material."
        ),
    }
    return summaries.get(clean_text(local_status), summaries[LOCAL_DIAGNOSTIC_STATUS_NOT_REQUESTED])


def _normalize_notional(value: Any) -> float:
    if isinstance(value, bool):
        return DEFAULT_MAX_NOTIONAL_USD
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_NOTIONAL_USD
    return numeric


def _sha256_text(value: str) -> str:
    return hashlib.sha256(clean_text(value).encode("utf-8")).hexdigest()


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
