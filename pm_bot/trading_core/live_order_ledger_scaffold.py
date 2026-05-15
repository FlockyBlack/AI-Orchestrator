from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.live_order_ledger_models import (
    STATUS_SCHEMA_ONLY,
    TASK_ID,
    LatestLiveOrderLedgerScaffoldStatus,
    LiveOrderFailureLedgerSchema,
    LiveOrderLedgerScaffoldResult,
    LiveOrderLedgerSchema,
    LiveOrderNoFakeExecutionPolicy,
    LiveOrderReconciliationPlan,
    LiveOrderResponseRedactionPolicy,
    live_order_ledger_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/live_order_ledger_scaffold_066")

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
    "--scheduler",
    "--daemon",
    "--background",
)


def live_order_ledger_scaffold_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "live_order_ledger_scaffold_066_result.json",
        "latest_status": root / "latest_live_order_ledger_scaffold_status_066.json",
        "ledger_schema": root / "live_order_ledger_schema_066.json",
        "reconciliation_plan": root / "live_order_reconciliation_plan_066.json",
        "redaction_policy": root / "live_order_response_redaction_policy_066.json",
        "failure_ledger_schema": root / "live_order_failure_ledger_schema_066.json",
        "no_fake_execution_policy": root / "live_order_no_fake_execution_policy_066.json",
        "operator_md": root / "live_order_ledger_operator_summary_066.md",
    }


def run_live_order_ledger_scaffold(
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("live order ledger scaffold requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    strategy_name = clean_text(strategy) or "tiny-momentum"
    paths = live_order_ledger_scaffold_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    ledger_schema = LiveOrderLedgerSchema(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    reconciliation_plan = LiveOrderReconciliationPlan(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    redaction_policy = LiveOrderResponseRedactionPolicy(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    failure_ledger_schema = LiveOrderFailureLedgerSchema(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    no_fake_execution_policy = LiveOrderNoFakeExecutionPolicy(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    latest_status = LatestLiveOrderLedgerScaffoldStatus(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()
    result = LiveOrderLedgerScaffoldResult(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        ledger_schema=ledger_schema,
        reconciliation_plan=reconciliation_plan,
        redaction_policy=redaction_policy,
        failure_ledger_schema=failure_ledger_schema,
        no_fake_execution_policy=no_fake_execution_policy,
        latest_status=latest_status,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["ledger_schema"], ledger_schema)
    write_json(paths["reconciliation_plan"], reconciliation_plan)
    write_json(paths["redaction_policy"], redaction_policy)
    write_json(paths["failure_ledger_schema"], failure_ledger_schema)
    write_json(paths["no_fake_execution_policy"], no_fake_execution_policy)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_live_order_ledger_scaffold_markdown(result))
    return result


def render_live_order_ledger_scaffold_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Live order ledger scaffold completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            "Schema only: true",
            f"Ledger records: {int(value.get('ledger_record_count', 0) or 0)}",
            f"Failure records: {int(value.get('failure_record_count', 0) or 0)}",
            "Authenticated fetch enabled: false",
            "Live order ledger executable: false",
            "Allowed for live: false",
            "Runner effect: artifacts only",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_live_order_ledger_scaffold_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}) or {})
    plan = dict(value.get("reconciliation_plan", {}) or {})
    redaction = dict(value.get("redaction_policy", {}) or {})
    fake_policy = dict(value.get("no_fake_execution_policy", {}) or {})
    lines = [
        "# PMBOT Live Order Ledger Scaffold 066",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `schema-only / review-only`",
        "- execution_mode: `preflight`",
        "- schema_only: `true`",
        "- live_order_ledger_executable: `false`",
        "- authenticated_fetch_enabled: `false`",
        "- allowed_for_live: `false`",
        "- ledger_record_count: `0`",
        "- failure_record_count: `0`",
        "",
        "## Generated Artifacts",
        "",
        *bullet_lines(
            [
                latest.get("artifact_path"),
                latest.get("latest_status_path"),
                latest.get("ledger_schema_path"),
                latest.get("reconciliation_plan_path"),
                latest.get("redaction_policy_path"),
                latest.get("failure_ledger_schema_path"),
                latest.get("no_fake_execution_policy_path"),
            ]
        ),
        "",
        "## Reconciliation Boundary",
        "",
        f"- descriptive_only: `{str(plan.get('descriptive_only') is True).lower()}`",
        "- runtime_collection_enabled: `false`",
        "- runtime_collection_steps: `[]`",
        "",
        "## Redaction Boundary",
        "",
        f"- redaction_policy_exists: `{str(redaction.get('redaction_policy_exists') is True).lower()}`",
        "- raw_response_storage_enabled: `false`",
        "- raw_values_emitted: `false`",
        "",
        "## No Fake Execution Policy",
        "",
        f"- fake_execution_values_allowed: `{str(fake_policy.get('fake_execution_values_allowed') is True).lower()}`",
        "- synthetic_runtime_identifiers_allowed: `false`",
        "- synthetic_account_values_allowed: `false`",
        "",
        "## Safety Statement",
        "",
        "- no live trading",
        "- no wallet connection or signing",
        "- no order submission or cancellation",
        "- no authenticated trading calls",
        "- no account runtime reads",
        "- no scheduler, daemon, background worker, or autonomous loop",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "live order ledger scaffold is schema-only; unsupported live/auth/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def build_result_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}) or {})
    return {
        "task_id": TASK_ID,
        "status": value.get("status") or STATUS_SCHEMA_ONLY,
        "market": value.get("market_symbol") or value.get("market"),
        "strategy": value.get("strategy_name"),
        "artifact_path": latest.get("artifact_path"),
        "latest_status_path": latest.get("latest_status_path"),
        "ledger_record_count": 0,
        "failure_record_count": 0,
        "validation_valid": dict(value.get("validation", {}) or {}).get("valid") is True,
        **live_order_ledger_safety_flags(),
    }
