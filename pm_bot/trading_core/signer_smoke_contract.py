from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text
from pm_bot.trading_core.signer_smoke_contract_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    EXECUTION_MODE,
    MODE,
    REQUIRED_FALSE_FLAGS,
    SIGNER_SMOKE_CONTRACT_RESULT_CONTRACT,
    SIGNER_SMOKE_LATEST_STATUS_CONTRACT,
    STATUS_BLOCKED,
    TASK_ID,
    FutureSignerSmokeContract,
    SignerSmokeRedactionPolicy,
    SignerSmokeSafetyContract,
    signer_smoke_safety_flags,
    validate_signer_smoke_contract,
)

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/signer_smoke_contract_068a")

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
    "--order-payload",
    "--private-key",
    "--read-private-key",
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
)


def signer_smoke_contract_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "signer_smoke_contract_068a_result.json",
        "latest_status": root / "latest_signer_smoke_contract_status_068a.json",
        "safety_contract": root / "signer_smoke_safety_contract_068a.json",
        "redaction_policy": root / "signer_smoke_redaction_policy_068a.json",
        "operator_md": root / "signer_smoke_operator_summary_068a.md",
    }


def build_signer_smoke_contract(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("signer smoke contract is dry-run only; executable signer smoke is not enabled")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = signer_smoke_contract_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    future_contract = FutureSignerSmokeContract(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    safety_contract = SignerSmokeSafetyContract(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    redaction_policy = SignerSmokeRedactionPolicy(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        path_refs=path_refs,
        generated_at=generated_at,
    )

    result = {
        "contract_version": SIGNER_SMOKE_CONTRACT_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
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
        "contract_only": True,
        "non_executable": True,
        "allowed_for_live": False,
        "signer_smoke_executable": False,
        "signer_smoke_executable_default": False,
        "order_payload_signing_enabled": False,
        "future_signer_smoke_contract": future_contract,
        "safety_contract": safety_contract,
        "redaction_policy": redaction_policy,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "operator_summary": (
            "068A generated a contract-only signer smoke scaffold. Dry-run mode did not read credential "
            "material, derive an address, sign a diagnostic challenge, sign an order payload, submit/cancel "
            "orders, connect a wallet, or call authenticated trading endpoints."
        ),
        "generated_at": generated_at,
    }
    result.update(signer_smoke_safety_flags())
    result["validation"] = validate_signer_smoke_contract(result, generated_at=generated_at)

    write_json(paths["safety_contract"], safety_contract)
    write_json(paths["redaction_policy"], redaction_policy)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_signer_smoke_contract_markdown(result))
    return result


def render_signer_smoke_contract_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Signer smoke contract 068A completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            "Signer smoke executable: false",
            "Allowed for live: false",
            "Private key read: false",
            "Address derivation: documented future check only",
            "Diagnostic challenge signing: documented future check only",
            "Order payload signing: disabled",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Authenticated trading: blocked",
            "Wallet connection: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_signer_smoke_contract_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Signer Smoke Contract 068A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `signer smoke contract / contract-only / dry-run`",
        "- execution_mode: `preflight`",
        "- contract_only: `true`",
        "- signer_smoke_executable: `false`",
        "- allowed_for_live: `false`",
        "- private_key_read: `false`",
        "- polymarket_private_key_read: `false`",
        "- address_derivation_performed: `false`",
        "- diagnostic_challenge_signing_attempted: `false`",
        "- order_payload_signing_enabled: `false`",
        "- order_submission_enabled: `false`",
        "- order_cancellation_enabled: `false`",
        "- authenticated_trading_enabled: `false`",
        "- wallet_connection_enabled: `false`",
        "",
        "## Future Contract Scope",
        "",
        "- a separate future task may define opt-in address derivation",
        "- a separate future task may define opt-in non-order diagnostic challenge signing",
        "- future mode must remain redacted and explicit",
        "- future mode must not sign order payloads",
        "- future mode must not submit or cancel orders",
        "- future mode must not log raw key material",
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
            "signer smoke contract is contract-only; unsupported live/auth/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    path_refs: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": SIGNER_SMOKE_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "artifact_path": clean_text(path_refs.get("result")),
        "latest_status_path": clean_text(path_refs.get("latest_status")),
        "safety_contract_path": clean_text(path_refs.get("safety_contract")),
        "redaction_policy_path": clean_text(path_refs.get("redaction_policy")),
        "operator_markdown_path": clean_text(path_refs.get("operator_md")),
        "operator_summary": "Contract-only signer smoke scaffold generated; execution remains disabled.",
        "generated_at": generated_at,
    }
    value.update(signer_smoke_safety_flags())
    return value
