from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.first_live_order_blocker_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    FIRST_LIVE_ORDER_LATEST_STATUS_CONTRACT,
    FORCED_FALSE_EXECUTION_FIELDS,
    MODE,
    REQUIRED_UNRESOLVED_BLOCKER_IDS,
    STATUS_BLOCKED,
    TASK_ID,
    FirstLiveOrderAbortConditions,
    FirstLiveOrderBlocker,
    FirstLiveOrderBlockerMatrix,
    FirstLiveOrderBlockerMatrixResult,
    FirstLiveOrderPreconditions,
    FirstLiveOrderRequiredArtifacts,
    FirstLiveOrderTestPlan,
    first_live_order_blocker_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/first_live_order_blocker_matrix_065a")

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
    "--env-dump",
)


def first_live_order_blocker_matrix_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "first_live_order_blocker_matrix_065a_result.json",
        "latest_status": root / "latest_first_live_order_blocker_matrix_status_065a.json",
        "blockers": root / "first_live_order_blockers_065a.json",
        "preconditions": root / "first_live_order_preconditions_065a.json",
        "abort_conditions": root / "first_live_order_abort_conditions_065a.json",
        "required_artifacts": root / "first_live_order_required_artifacts_065a.json",
        "test_plan": root / "first_live_order_test_plan_065a.json",
        "operator_summary_md": root / "first_live_order_operator_summary_065a.md",
    }


def run_first_live_order_blocker_matrix(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("first live order blocker matrix requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = first_live_order_blocker_matrix_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    blockers = _build_blockers(generated_at=generated_at)
    blocker_matrix = FirstLiveOrderBlockerMatrix(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        blockers=tuple(blockers),
        generated_at=generated_at,
    ).to_dict()
    preconditions = FirstLiveOrderPreconditions(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        preconditions=tuple(_build_preconditions()),
        generated_at=generated_at,
    ).to_dict()
    abort_conditions = FirstLiveOrderAbortConditions(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        abort_conditions=tuple(_build_abort_conditions()),
        generated_at=generated_at,
    ).to_dict()
    required_artifacts = FirstLiveOrderRequiredArtifacts(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        required_artifacts=tuple(_build_required_artifacts()),
        generated_at=generated_at,
    ).to_dict()
    test_plan = FirstLiveOrderTestPlan(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        test_plan_items=tuple(_build_test_plan_items()),
        generated_at=generated_at,
    ).to_dict()
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        blocker_matrix=blocker_matrix,
        preconditions=preconditions,
        abort_conditions=abort_conditions,
        required_artifacts=required_artifacts,
        test_plan=test_plan,
        path_refs=path_refs,
        generated_at=generated_at,
    )
    result = FirstLiveOrderBlockerMatrixResult(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        blocker_matrix=blocker_matrix,
        preconditions=preconditions,
        abort_conditions=abort_conditions,
        required_artifacts=required_artifacts,
        test_plan=test_plan,
        latest_status=latest_status,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["blockers"], blocker_matrix)
    write_json(paths["preconditions"], preconditions)
    write_json(paths["abort_conditions"], abort_conditions)
    write_json(paths["required_artifacts"], required_artifacts)
    write_json(paths["test_plan"], test_plan)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_summary_md"], render_first_live_order_blocker_matrix_markdown(result))
    return result


def render_first_live_order_blocker_matrix_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "First live order blocker matrix completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Unresolved blockers: {int(value.get('blocker_count', 0) or 0)}",
            "Resolved blockers: 0",
            "Allowed for live: false",
            "Candidate executable: false",
            "Operator approved: false",
            "Live execution: blocked",
            "Signing: blocked",
            "Wallet: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Authenticated trading calls: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_first_live_order_blocker_matrix_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    preconditions = [
        dict(row)
        for row in dict(value.get("preconditions", {})).get("preconditions", [])
        if isinstance(row, Mapping)
    ]
    abort_conditions = [
        dict(row)
        for row in dict(value.get("abort_conditions", {})).get("abort_conditions", [])
        if isinstance(row, Mapping)
    ]
    required_artifacts = [
        dict(row)
        for row in dict(value.get("required_artifacts", {})).get("required_artifacts", [])
        if isinstance(row, Mapping)
    ]
    test_plan_items = [
        dict(row)
        for row in dict(value.get("test_plan", {})).get("test_plan_items", [])
        if isinstance(row, Mapping)
    ]
    lines = [
        "# PMBOT First Live Order Blocker Matrix 065A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        f"- Mode: `{MODE}`",
        "- execution_mode: `preflight`",
        "- preimplementation_only: `true`",
        "- scaffold_only: `true`",
        "- non_executable: `true`",
        "- allowed_for_live: `false`",
        "- candidate_is_executable: `false`",
        "- operator_approved: `false`",
        "- resolved_blocker_count: `0`",
        "",
        "## Unresolved Blockers",
        "",
        *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
        "",
        "## Preconditions",
        "",
        *bullet_lines(f"`{row.get('precondition_id')}` - {row.get('status')}" for row in preconditions),
        "",
        "## Abort Conditions",
        "",
        *bullet_lines(f"`{row.get('abort_condition_id')}` - {row.get('summary')}" for row in abort_conditions),
        "",
        "## Required Future Artifacts",
        "",
        *bullet_lines(f"`{row.get('artifact_id')}` - {row.get('purpose')}" for row in required_artifacts),
        "",
        "## Test Plan",
        "",
        *bullet_lines(f"`{row.get('test_id')}` - {row.get('coverage')}" for row in test_plan_items),
        "",
        "## Required False Flags",
        "",
        *bullet_lines(f"`{field}=false`" for field in FORCED_FALSE_EXECUTION_FIELDS),
        "",
        "## Safety Statement",
        "",
        "065A does not implement signing, wallet connection, order submission, cancellation, authenticated trading calls, "
        "secret reads, browser automation, schedulers, daemons, background loops, or live execution.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "first live order blocker matrix is pre-implementation only; unsupported live/auth/wallet/signing/order "
            "flag(s): "
            + ", ".join(requested)
        )


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    blocker_matrix: Mapping[str, Any],
    preconditions: Mapping[str, Any],
    abort_conditions: Mapping[str, Any],
    required_artifacts: Mapping[str, Any],
    test_plan: Mapping[str, Any],
    path_refs: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": FIRST_LIVE_ORDER_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "blocker_count": int(blocker_matrix.get("blocker_count", 0) or 0),
        "resolved_blocker_count": 0,
        "required_unresolved_blocker_ids": list(REQUIRED_UNRESOLVED_BLOCKER_IDS),
        "unresolved_blocker_ids": list(blocker_matrix.get("unresolved_blocker_ids", [])),
        "precondition_count": int(preconditions.get("precondition_count", 0) or 0),
        "abort_condition_count": int(abort_conditions.get("abort_condition_count", 0) or 0),
        "required_artifact_count": int(required_artifacts.get("required_artifact_count", 0) or 0),
        "test_plan_item_count": int(test_plan.get("test_plan_item_count", 0) or 0),
        "artifact_path": clean_text(path_refs.get("result")),
        "latest_status_path": clean_text(path_refs.get("latest_status")),
        "blockers_path": clean_text(path_refs.get("blockers")),
        "preconditions_path": clean_text(path_refs.get("preconditions")),
        "abort_conditions_path": clean_text(path_refs.get("abort_conditions")),
        "required_artifacts_path": clean_text(path_refs.get("required_artifacts")),
        "test_plan_path": clean_text(path_refs.get("test_plan")),
        "operator_summary_path": clean_text(path_refs.get("operator_summary_md")),
        "operator_summary": (
            "Pre-implementation matrix generated. Live execution remains blocked with allowed_for_live=false, "
            "candidate_is_executable=false, operator_approved=false, and resolved_blocker_count=0."
        ),
        "generated_at": generated_at,
    }
    value.update(first_live_order_blocker_safety_flags())
    return value


def _build_blockers(*, generated_at: str) -> list[dict[str, Any]]:
    rows = [
        (
            "explicit_operator_authorization_missing",
            "operator_authorization",
            "Exact operator authorization for a first tiny live order has not been captured.",
        ),
        (
            "live_credentials_not_value_validated",
            "credential_boundary",
            "Live credential values were not read or value-validated; presence-only readiness is insufficient.",
        ),
        (
            "signer_boundary_not_implemented",
            "signing_boundary",
            "No isolated signer boundary exists for a supervised first live order.",
        ),
        (
            "wallet_connection_not_implemented",
            "wallet_boundary",
            "No wallet connection boundary exists for a supervised first live order.",
        ),
        (
            "order_submission_not_implemented",
            "submission_boundary",
            "No order submission boundary exists in this task.",
        ),
        (
            "order_cancel_not_implemented",
            "cancellation_boundary",
            "No order cancellation boundary exists in this task.",
        ),
        (
            "live_order_ledger_not_implemented",
            "ledger_boundary",
            "No append-only first live order ledger exists for safe one-shot accounting.",
        ),
        (
            "reconciliation_not_implemented",
            "reconciliation_boundary",
            "No reconciliation flow exists for accepted, rejected, or unknown venue state.",
        ),
        (
            "response_redaction_policy_not_implemented",
            "redaction_boundary",
            "No commit-safe response redaction policy exists for signing or submission boundaries.",
        ),
        (
            "first_live_order_task_not_authorized",
            "task_authorization",
            "This 065A task is not the separately authorized first live order implementation task.",
        ),
        (
            "candidate_non_executable",
            "candidate_boundary",
            "candidate_is_executable remains false and any candidate is a non-executable scaffold.",
        ),
        (
            "allowed_for_live_false",
            "live_execution",
            "allowed_for_live remains false.",
        ),
    ]
    return [
        FirstLiveOrderBlocker(
            blocker_id=blocker_id,
            blocker_category=category,
            reason=reason,
            generated_at=generated_at,
        ).to_dict()
        for blocker_id, category, reason in rows
    ]


def _build_preconditions() -> list[dict[str, Any]]:
    rows = [
        ("base_head_verified", "required base HEAD is inspected before implementation", True),
        ("design_reference_reviewed", "065 design branch is reviewed as a checklist only", True),
        ("accepted_063_gate_on_master", "063 supervised tiny live enablement gate accepted on master", False),
        ("accepted_064_gate_on_master", "064 explicit credentials readiness gate accepted on master", False),
        ("exact_operator_authorization_captured", "future task captures exact one-shot authorization text", False),
        ("live_credentials_value_validation_policy_ready", "credential value-validation policy is separately approved", False),
        ("signer_boundary_ready", "isolated signer boundary is implemented and verified", False),
        ("wallet_connection_boundary_ready", "wallet connection boundary is implemented and verified", False),
        ("submission_boundary_ready", "order submission boundary is implemented and verified", False),
        ("cancel_boundary_ready", "cancel boundary is implemented or explicitly unavailable by design", False),
        ("live_order_ledger_ready", "append-only first live order ledger is implemented", False),
        ("reconciliation_plan_ready", "reconciliation plan is implemented before any submission boundary", False),
        ("response_redaction_policy_ready", "response redaction policy is implemented and tested", False),
        ("static_safety_report_clean", "static safety invariant report has zero critical findings", False),
    ]
    return [
        {
            "precondition_id": precondition_id,
            "summary": summary,
            "satisfied": satisfied is True,
            "status": "satisfied" if satisfied is True else STATUS_BLOCKED,
        }
        for precondition_id, summary, satisfied in rows
    ]


def _build_abort_conditions() -> list[dict[str, Any]]:
    rows = [
        ("operator_authorization_missing", "exact operator authorization is missing or paraphrased"),
        ("operator_authorization_expired", "operator authorization expired after an attempt, abort, completion, or day boundary"),
        ("market_or_strategy_mismatch", "market is not BTC or strategy is not tiny-momentum"),
        ("risk_limit_mismatch", "max notional exceeds 1.00 USD or max orders today differs from 1"),
        ("prior_order_attempt_detected", "an order was already attempted for the approved day"),
        ("credential_material_exposure_risk", "credential, private, or response material could be exposed"),
        ("signer_boundary_missing_or_uncertain", "signer boundary is missing, coupled, or logging cannot be proven safe"),
        ("wallet_boundary_missing_or_uncertain", "wallet boundary is missing or cannot be proven isolated"),
        ("submission_boundary_missing_or_uncertain", "submission endpoint behavior or scope is uncertain"),
        ("redaction_policy_missing", "signed material or response redaction policy is missing"),
        ("reconciliation_uncertain", "accepted, rejected, or unknown state cannot be safely reconciled"),
        ("scheduler_daemon_or_background_loop_detected", "scheduler, daemon, background loop, or autonomous repeat is present"),
        ("unsafe_artifact_path", "artifact path points to a sensitive location or contains sensitive material"),
    ]
    return [
        {
            "abort_condition_id": abort_id,
            "summary": summary,
            "blocks_before_live_boundary": True,
            "status": STATUS_BLOCKED,
        }
        for abort_id, summary in rows
    ]


def _build_required_artifacts() -> list[dict[str, Any]]:
    rows = [
        ("operator_approval_packet", "capture exact one-shot operator authorization and expiry"),
        ("live_order_intent_snapshot", "record non-secret operator-reviewed order intent before any signing boundary"),
        ("signed_material_redaction_policy", "record boolean-only signing boundary status without raw signed material"),
        ("submission_response_redaction_policy", "record response handling policy without raw request or response material"),
        ("first_live_order_ledger", "append-only one-shot ledger with branch, head, gates, and final status"),
        ("failure_ledger", "capture abort point, failure category, operator action, and no-repeat confirmation"),
        ("kill_switch_record", "capture reviewed kill switch plan and effect on signing, submission, cancellation, and retries"),
        ("reconciliation_record", "record accepted, rejected, or unknown status without inventing runtime outcomes"),
    ]
    return [
        {
            "artifact_id": artifact_id,
            "purpose": purpose,
            "commit_safe_required": True,
            "implemented_in_065a": False,
            "status": STATUS_BLOCKED,
        }
        for artifact_id, purpose in rows
    ]


def _build_test_plan_items() -> list[dict[str, Any]]:
    rows = [
        ("approval_missing_blocks", "no first live order boundary when exact approval is missing"),
        ("approval_paraphrase_blocks", "weaker or paraphrased approval text is rejected"),
        ("approval_expiry_blocks", "expired authorization cannot be reused"),
        ("risk_limit_blocks", "notional above 1.00 USD or daily order cap above one blocks"),
        ("market_strategy_scope_blocks", "non-BTC market or non-tiny-momentum strategy blocks"),
        ("no_secret_emission", "credential and private material are not read, emitted, stored, or transformed"),
        ("no_signed_material_in_artifacts", "commit-safe artifacts contain no raw signed material"),
        ("no_raw_submission_response", "commit-safe artifacts contain no raw submission request or response material"),
        ("no_runtime_outcome_invention", "fills, profit/loss, balances, positions, order references, and transaction hashes are not invented"),
        ("no_scheduler_daemon_loop", "scheduler, daemon, background loop, autonomous repeat, and automatic retry are absent"),
        ("redaction_policy_enforced", "signing and submission redaction policies are enforced before boundary entry"),
        ("reconciliation_unknown_blocks", "uncertain venue state remains unknown and requires operator review"),
        ("static_safety_blocks", "critical static safety findings block any later live path"),
    ]
    return [
        {
            "test_id": test_id,
            "coverage": coverage,
            "required_before_future_live_attempt": True,
            "implemented_in_065a": False,
            "status": STATUS_BLOCKED,
        }
        for test_id, coverage in rows
    ]
