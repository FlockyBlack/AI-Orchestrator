from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.live_order_boundary_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    EXECUTION_MODE,
    LIVE_ORDER_BOUNDARY_CONTRACT_RESULT_CONTRACT,
    LIVE_ORDER_BOUNDARY_LATEST_STATUS_CONTRACT,
    LIVE_ORDER_NON_EXECUTABLE_INTERFACES_CONTRACT,
    MODE,
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED,
    TASK_ID,
    FutureLiveOrderBoundaryChecklist,
    LiveBoundarySafetyContract,
    NonExecutableOrderCancelBoundary,
    NonExecutableOrderSubmissionBoundary,
    NonExecutableSignerBoundary,
    RedactionPolicy,
    live_boundary_safety_flags,
    validate_live_order_boundary_contract,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/live_order_boundary_contract_065b")

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
    "--private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
)


def live_order_boundary_contract_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "live_order_boundary_contract_065b_result.json",
        "latest_status": root / "latest_live_order_boundary_contract_status_065b.json",
        "safety_contract": root / "live_order_boundary_safety_contract_065b.json",
        "redaction_policy": root / "live_order_redaction_policy_065b.json",
        "checklist": root / "live_order_boundary_checklist_065b.json",
        "interfaces": root / "live_order_non_executable_interfaces_065b.json",
        "operator_md": root / "live_order_boundary_operator_summary_065b.md",
    }


def build_live_order_boundary_contract(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("live order boundary contract requires --dry-run; executable live boundaries are blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = live_order_boundary_contract_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    signer_boundary = NonExecutableSignerBoundary(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    order_submission_boundary = NonExecutableOrderSubmissionBoundary(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    order_cancel_boundary = NonExecutableOrderCancelBoundary(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    safety_contract = LiveBoundarySafetyContract(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    redaction_policy = RedactionPolicy(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    checklist = FutureLiveOrderBoundaryChecklist(
        safety_contract=safety_contract,
        redaction_policy=redaction_policy,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    interfaces = _build_non_executable_interfaces(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        signer_boundary=signer_boundary,
        order_submission_boundary=order_submission_boundary,
        order_cancel_boundary=order_cancel_boundary,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        path_refs=path_refs,
        generated_at=generated_at,
    )
    result = {
        "contract_version": LIVE_ORDER_BOUNDARY_CONTRACT_RESULT_CONTRACT,
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
        "interface_only": True,
        "non_executable": True,
        "all_boundaries_non_executable": True,
        "all_boundaries_interface_only": True,
        "allowed_for_live": False,
        "boundary_is_executable": False,
        "resolved_blocker_count": 0,
        "signer_boundary": signer_boundary,
        "order_submission_boundary": order_submission_boundary,
        "order_cancel_boundary": order_cancel_boundary,
        "safety_contract": safety_contract,
        "redaction_policy": redaction_policy,
        "future_live_order_boundary_checklist": checklist,
        "non_executable_interfaces": interfaces,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "operator_summary": (
            "065B produced only non-executable signer/order boundary interface artifacts. It did not instantiate "
            "a signer, read credential values, generate signed material, submit/cancel orders, connect a wallet, "
            "or make authenticated trading calls."
        ),
        "generated_at": generated_at,
    }
    result.update(live_boundary_safety_flags())
    result["validation"] = validate_live_order_boundary_contract(result, generated_at=generated_at)

    write_json(paths["safety_contract"], safety_contract)
    write_json(paths["redaction_policy"], redaction_policy)
    write_json(paths["checklist"], checklist)
    write_json(paths["interfaces"], interfaces)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_live_order_boundary_contract_markdown(result))
    return result


def render_live_order_boundary_contract_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Live order boundary contract 065B completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            "Boundary executable: false",
            "Allowed for live: false",
            "Signer boundary available: false",
            "Signer instantiated: false",
            "Private key read: false",
            "Credential value read: false",
            "Signed payload generation: disabled",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Authenticated trading: blocked",
            "Wallet connection: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_live_order_boundary_contract_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Live Order Boundary Contract 065B",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `non-executable signer/order boundary skeleton`",
        "- execution_mode: `preflight`",
        "- boundary_is_executable: `false`",
        "- allowed_for_live: `false`",
        "- signer_boundary_available: `false`",
        "- signer_instantiated: `false`",
        "- private_key_read: `false`",
        "- credential_value_read: `false`",
        "- signed_payload_generation_enabled: `false`",
        "- order_submission_enabled: `false`",
        "- order_cancel_enabled: `false`",
        "- authenticated_trading_enabled: `false`",
        "- wallet_connection_enabled: `false`",
        "",
        "## Boundary Meaning",
        "",
        "- interface/spec scaffold only",
        "- no signer instance exists",
        "- no credential values are read or redacted from runtime input",
        "- no signed material or order payload is generated",
        "- no submit/cancel endpoint path exists",
        "- no authenticated trading call or wallet connection exists",
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
            "live order boundary contract is interface-only; unsupported live/auth/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _build_non_executable_interfaces(
    *,
    market_symbol: str,
    strategy_name: str,
    signer_boundary: Mapping[str, Any],
    order_submission_boundary: Mapping[str, Any],
    order_cancel_boundary: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": LIVE_ORDER_NON_EXECUTABLE_INTERFACES_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "interfaces": [
            dict(signer_boundary),
            dict(order_submission_boundary),
            dict(order_cancel_boundary),
        ],
        "interface_count": 3,
        "all_boundaries_non_executable": True,
        "all_boundaries_interface_only": True,
        "generated_at": generated_at,
    }
    value.update(live_boundary_safety_flags())
    return value


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    path_refs: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": LIVE_ORDER_BOUNDARY_LATEST_STATUS_CONTRACT,
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
        "checklist_path": clean_text(path_refs.get("checklist")),
        "interfaces_path": clean_text(path_refs.get("interfaces")),
        "operator_markdown_path": clean_text(path_refs.get("operator_md")),
        "operator_summary": "Non-executable signer/order boundary scaffold generated; all live execution remains blocked.",
        "generated_at": generated_at,
    }
    value.update(live_boundary_safety_flags())
    return value
