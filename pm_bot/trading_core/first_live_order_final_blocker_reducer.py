from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.first_live_order_final_blocker_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    EXECUTION_MODE,
    FIRST_LIVE_ORDER_FINAL_BLOCKER_GROUPS_CONTRACT,
    FIRST_LIVE_ORDER_FINAL_LATEST_STATUS_CONTRACT,
    FIRST_LIVE_ORDER_FINAL_NEXT_ACTIONS_CONTRACT,
    GROUPS,
    GROUP_IDS,
    MODE,
    STATUS_BLOCKED,
    STATUS_REVIEW_REQUIRED,
    STATUS_UNKNOWN,
    TASK_ID,
    FirstLiveOrderFinalBlocker,
    FirstLiveOrderFinalBlockerGroup,
    FirstLiveOrderFinalBlockerResult,
    FirstLiveOrderFinalSafetySnapshot,
    first_live_order_final_blocker_safety_flags,
    group_label_for,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/first_live_order_final_blocker_reducer_072d")

DEFAULT_INPUT_ARTIFACT_CANDIDATES: dict[str, tuple[Path, ...]] = {
    "order_prep_packet": (
        Path("pm_bot/trading_core/artifacts/order_prep_packet_072a/order_prep_packet_072a_result.json"),
        Path("pm_bot/trading_core/artifacts/order_prep_packet_072a/latest_order_prep_packet_072a.json"),
        Path("pm_bot/trading_core/artifacts/first_live_order_prep_packet_072a/first_live_order_prep_packet_072a_result.json"),
        Path("pm_bot/trading_core/artifacts/first_live_order_prep_packet_072a/latest_first_live_order_prep_packet_072a.json"),
    ),
    "local_real_check_bundle": (
        Path("pm_bot/trading_core/artifacts/local_real_check_bundle_072c/local_real_check_bundle_072c_result.json"),
        Path("pm_bot/trading_core/artifacts/local_real_check_bundle_072c/latest_local_real_check_bundle_072c.json"),
    ),
    "credentials_auth": (
        Path("pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/latest_explicit_live_credentials_readiness_gate_status_064.json"),
        Path("pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/explicit_live_credentials_readiness_gate_064_result.json"),
    ),
    "account_state": (
        Path("pm_bot/trading_core/artifacts/live_account_readonly_state_probe_070c/latest_live_account_readonly_state_status_070c.json"),
        Path("pm_bot/trading_core/artifacts/live_account_readonly_state_probe_070c/live_account_readonly_state_probe_070c_result.json"),
    ),
    "signer_diagnostic": (
        Path("pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/latest_guarded_signer_diagnostic_status_069a.json"),
        Path("pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/guarded_signer_diagnostic_smoke_069a_result.json"),
    ),
    "token_selection": (
        Path("pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b/latest_first_order_market_token_status_070b.json"),
        Path("pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b/first_order_market_token_resolver_070b_result.json"),
    ),
    "signed_payload_dry_run": (
        Path("pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/latest_signed_order_payload_dry_run_status_070a.json"),
        Path("pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/signed_order_payload_dry_run_070a_result.json"),
    ),
    "approval_contract": (
        Path("pm_bot/trading_core/artifacts/first_live_order_approval_contract_065d/latest_first_live_order_approval_contract_status_065d.json"),
        Path("pm_bot/trading_core/artifacts/first_live_order_approval_contract_065d/first_live_order_approval_contract_065d_result.json"),
    ),
    "initial_blocker_matrix": (
        Path("pm_bot/trading_core/artifacts/first_live_order_blocker_matrix_065a/latest_first_live_order_blocker_matrix_status_065a.json"),
        Path("pm_bot/trading_core/artifacts/first_live_order_blocker_matrix_065a/first_live_order_blocker_matrix_065a_result.json"),
    ),
}

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
    "--approve",
    "--approve-live",
    "--record-approval",
    "--order",
    "--private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
    "--env-dump",
)


def first_live_order_final_blocker_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "first_live_order_final_blocker_reducer_072d_result.json",
        "latest_status": root / "latest_first_live_order_final_blockers_072d.json",
        "blocker_groups": root / "first_live_order_blocker_groups_072d.json",
        "next_actions": root / "first_live_order_next_actions_072d.json",
        "safety_snapshot": root / "first_live_order_final_blocker_safety_snapshot_072d.json",
        "operator_summary_md": root / "first_live_order_final_blocker_operator_summary_072d.md",
    }


def run_first_live_order_final_blocker_reducer(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    input_artifact_paths: Mapping[str, str | Path | Sequence[str | Path]] | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("first live order final blocker reducer requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = first_live_order_final_blocker_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    observed = _observe_input_artifacts(input_artifact_paths=input_artifact_paths)
    observations = [dict(row["summary"]) for row in observed.values()]
    groups = _build_blocker_groups(observed=observed, generated_at=generated_at)
    blocker_groups = _build_blocker_groups_artifact(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        groups=groups,
        generated_at=generated_at,
    )
    next_actions = _build_next_actions(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        groups=groups,
        generated_at=generated_at,
    )
    safety_snapshot = FirstLiveOrderFinalSafetySnapshot(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        observed_artifacts=tuple(observations),
        generated_at=generated_at,
    ).to_dict()
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        blocker_groups=blocker_groups,
        observations=observations,
        path_refs=path_refs,
        generated_at=generated_at,
    )
    result = FirstLiveOrderFinalBlockerResult(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        artifact_observations=tuple(observations),
        blocker_groups=blocker_groups,
        next_actions=next_actions,
        safety_snapshot=safety_snapshot,
        latest_status=latest_status,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["blocker_groups"], blocker_groups)
    write_json(paths["next_actions"], next_actions)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_summary_md"], render_first_live_order_final_blocker_markdown(result))
    return result


def render_first_live_order_final_blocker_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "First live order final blocker reducer 072D completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            f"Remaining blockers: {int(value.get('remaining_blocker_count', 0) or 0)}",
            f"Unknown groups: {int(value.get('unknown_group_count', 0) or 0)}",
            "Allowed for live: false",
            "Live execution authorization: blocked",
            "Signing: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Unknown evidence remains unknown.",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_first_live_order_final_blocker_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    groups = [dict(row) for row in value.get("groups", []) if isinstance(row, Mapping)]
    observations = [dict(row) for row in value.get("artifact_observations", []) if isinstance(row, Mapping)]
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT First Live Order Final Blocker Reducer 072D",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        f"- execution_mode: `{EXECUTION_MODE}`",
        "- allowed_for_live: `false`",
        "- live execution authorization: `blocked`",
        "- no submit, no cancel, no signing",
        "- unknown evidence remains unknown",
        "",
        "## Blocker Groups",
        "",
    ]
    for group in groups:
        blockers = [dict(row) for row in group.get("remaining_blockers", []) if isinstance(row, Mapping)]
        lines.extend(
            [
                f"### {group.get('group_label')}",
                "",
                f"- status: `{group.get('status')}`",
                f"- remaining blockers: `{group.get('remaining_blocker_count')}`",
                *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
                "",
            ]
        )
    lines.extend(
        [
            "## Input Artifact Evidence",
            "",
            *bullet_lines(
                f"`{row.get('artifact_key')}` exists={str(row.get('exists') is True).lower()} "
                f"parsed={str(row.get('parsed') is True).lower()} status=`{row.get('status') or 'unknown'}`"
                for row in observations
            ),
            "",
            "## Artifacts",
            "",
            *bullet_lines(f"`{path}`" for path in paths.values()),
            "",
            "## Safety Statement",
            "",
            "072D is a local reducer only. It reads known commit-safe JSON artifacts, writes grouped blocker artifacts, "
            "and does not read private material, sign payloads, submit orders, cancel orders, call trading endpoints, "
            "start browser automation, create schedulers, create daemons, or run background workers.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "first live order final blocker reducer is no-execution; unsupported live/auth/wallet/signing/order "
            "flag(s): "
            + ", ".join(requested)
        )


def _observe_input_artifacts(
    *,
    input_artifact_paths: Mapping[str, str | Path | Sequence[str | Path]] | None,
) -> dict[str, dict[str, Any]]:
    overrides = dict(input_artifact_paths or {})
    observed: dict[str, dict[str, Any]] = {}
    for artifact_key, default_candidates in DEFAULT_INPUT_ARTIFACT_CANDIDATES.items():
        candidates = _candidate_paths(overrides.get(artifact_key), default_candidates)
        selected = _first_existing(candidates)
        if selected is None:
            summary = _missing_artifact_summary(artifact_key, candidates)
            observed[artifact_key] = {"summary": summary, "payload": {}}
            continue
        summary, payload = _read_artifact_summary(artifact_key, selected, candidates)
        observed[artifact_key] = {"summary": summary, "payload": payload}
    return observed


def _build_blocker_groups(
    *,
    observed: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    grouped_blockers: dict[str, list[dict[str, Any]]] = {group_id: [] for group_id in GROUP_IDS}
    refs_by_group: dict[str, list[dict[str, Any]]] = {group_id: [] for group_id in GROUP_IDS}

    def add(
        group_id: str,
        blocker_id: str,
        reason: str,
        *,
        evidence_status: str,
        source_artifact_keys: Sequence[str],
    ) -> None:
        grouped_blockers[group_id].append(
            FirstLiveOrderFinalBlocker(
                blocker_id=blocker_id,
                group_id=group_id,
                reason=reason,
                evidence_status=evidence_status,
                source_artifact_keys=tuple(source_artifact_keys),
                generated_at=generated_at,
            ).to_dict()
        )

    for group_id, keys in _group_reference_keys().items():
        refs_by_group[group_id].extend(_reference_rows(observed, keys))

    credentials = _payload(observed, "credentials_auth")
    if _missing(observed, "credentials_auth"):
        add(
            "credentials_auth",
            "credentials_auth_artifact_missing",
            "Credentials/auth readiness evidence is missing; the reducer cannot infer auth readiness.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=("credentials_auth",),
        )
    else:
        add(
            "credentials_auth",
            "credentials_auth_not_live_authorization",
            "Credentials/auth artifacts are commit-safe readiness evidence only and do not authorize live execution.",
            evidence_status=_evidence_status_for_payload(credentials),
            source_artifact_keys=("credentials_auth",),
        )
    if _missing(observed, "local_real_check_bundle"):
        add(
            "credentials_auth",
            "local_real_check_auth_evidence_unknown",
            "The local real-check bundle is missing, so auth-side final checks remain unknown.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=("local_real_check_bundle",),
        )

    account = _payload(observed, "account_state")
    if _missing(observed, "account_state"):
        add(
            "account_balance",
            "account_state_artifact_missing",
            "Read-only account-state evidence is missing; account/balance readiness remains unknown.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=("account_state",),
        )
    elif _text_field(account, "status") != "account_state_probe_succeeded_live_blocked":
        add(
            "account_balance",
            "account_state_not_confirmed",
            "Read-only account-state artifact did not report a successful live-blocked probe; no account data is inferred.",
            evidence_status=_evidence_status_for_payload(account),
            source_artifact_keys=("account_state",),
        )
    add(
        "account_balance",
        "account_balance_values_not_execution_authorization",
        "Account/balance values are not emitted by this reducer and do not authorize a live order.",
        evidence_status=STATUS_REVIEW_REQUIRED,
        source_artifact_keys=("account_state", "local_real_check_bundle"),
    )

    signer = _payload(observed, "signer_diagnostic")
    diagnostic_status = _text_field(signer, "diagnostic_status")
    if _missing(observed, "signer_diagnostic"):
        add(
            "signer",
            "signer_diagnostic_artifact_missing",
            "Guarded signer diagnostic evidence is missing; signer readiness remains unknown.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=("signer_diagnostic",),
        )
    elif diagnostic_status != "diagnostic_ok":
        add(
            "signer",
            "signer_diagnostic_not_ok",
            "Guarded signer diagnostic has not completed with diagnostic_ok.",
            evidence_status=_evidence_status_for_payload(signer),
            source_artifact_keys=("signer_diagnostic",),
        )
    else:
        add(
            "signer",
            "signer_diagnostic_not_order_payload_authorization",
            "A diagnostic challenge is not authorization to sign an order payload.",
            evidence_status=STATUS_REVIEW_REQUIRED,
            source_artifact_keys=("signer_diagnostic",),
        )

    token = _payload(observed, "token_selection")
    if _missing(observed, "order_prep_packet"):
        add(
            "token_selection",
            "order_prep_packet_missing",
            "The order prep packet artifact is missing; token selection cannot be reduced to a final reviewed target.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=("order_prep_packet",),
        )
    if _missing(observed, "token_selection"):
        add(
            "token_selection",
            "token_selection_artifact_missing",
            "Market/token resolver evidence is missing; token selection remains unknown.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=("token_selection",),
        )
    elif _field(token, "token_id_present") is not True or _field(token, "token_id_format_valid") is not True:
        add(
            "token_selection",
            "token_selection_not_final",
            "Token selection evidence does not show an explicit format-valid token target.",
            evidence_status=_evidence_status_for_payload(token),
            source_artifact_keys=("token_selection",),
        )
    else:
        add(
            "token_selection",
            "token_selection_requires_final_operator_match_check",
            "A format-valid token target still needs final operator match review against the prep packet.",
            evidence_status=STATUS_REVIEW_REQUIRED,
            source_artifact_keys=("order_prep_packet", "token_selection"),
        )

    signed_dry_run = _payload(observed, "signed_payload_dry_run")
    if _missing(observed, "signed_payload_dry_run"):
        add(
            "signed_payload_dry_run",
            "signed_payload_dry_run_artifact_missing",
            "Signed payload dry-run evidence is missing; signed payload readiness remains unknown.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=("signed_payload_dry_run",),
        )
    else:
        add(
            "signed_payload_dry_run",
            "signed_payload_dry_run_non_executable",
            "Signed payload dry-run artifacts are non-executable and do not contain signed material or submit capability.",
            evidence_status=_evidence_status_for_payload(signed_dry_run),
            source_artifact_keys=("signed_payload_dry_run",),
        )

    approval = _payload(observed, "approval_contract")
    if _missing(observed, "approval_contract"):
        add(
            "approval",
            "approval_contract_artifact_missing",
            "Approval contract evidence is missing; exact operator approval status remains unknown.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=("approval_contract",),
        )
    add(
        "approval",
        "operator_approval_not_recorded",
        "The known approval contract defines required text but records no consumed operator approval.",
        evidence_status=_evidence_status_for_payload(approval) if approval else STATUS_UNKNOWN,
        source_artifact_keys=("approval_contract",),
    )

    unknown_keys = [key for key, row in observed.items() if dict(row.get("summary", {})).get("evidence_status") == STATUS_UNKNOWN]
    if _missing(observed, "initial_blocker_matrix"):
        add(
            "live_execution_authorization",
            "initial_blocker_matrix_missing",
            "Initial first-live-order blocker matrix evidence is missing; baseline blockers remain unknown.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=("initial_blocker_matrix",),
        )
    add(
        "live_execution_authorization",
        "allowed_for_live_false",
        "allowed_for_live remains false across the 072D reducer output.",
        evidence_status=STATUS_BLOCKED,
        source_artifact_keys=tuple(DEFAULT_INPUT_ARTIFACT_CANDIDATES),
    )
    add(
        "live_execution_authorization",
        "separate_live_execution_authorization_missing",
        "No separate operator-approved live execution authorization artifact is present or consumed.",
        evidence_status=STATUS_BLOCKED,
        source_artifact_keys=("approval_contract", "initial_blocker_matrix"),
    )
    add(
        "live_execution_authorization",
        "submit_cancel_signing_forbidden",
        "This task does not submit, cancel, sign, instantiate a signer, connect a wallet, or make trading calls.",
        evidence_status=STATUS_BLOCKED,
        source_artifact_keys=(),
    )
    if unknown_keys:
        add(
            "live_execution_authorization",
            "upstream_evidence_unknown",
            "One or more upstream prep/check artifacts are missing or unreadable; unknown evidence remains unknown.",
            evidence_status=STATUS_UNKNOWN,
            source_artifact_keys=tuple(unknown_keys),
        )

    return [
        FirstLiveOrderFinalBlockerGroup(
            group_id=group_id,
            blockers=tuple(grouped_blockers[group_id]),
            evidence_references=tuple(refs_by_group[group_id]),
            generated_at=generated_at,
        ).to_dict()
        for group_id, _ in GROUPS
    ]


def _build_blocker_groups_artifact(
    *,
    market_symbol: str,
    strategy_name: str,
    groups: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    group_rows = [dict(row) for row in groups]
    blockers = [
        dict(blocker)
        for group in group_rows
        for blocker in group.get("remaining_blockers", [])
        if isinstance(blocker, Mapping)
    ]
    value = {
        "contract_version": FIRST_LIVE_ORDER_FINAL_BLOCKER_GROUPS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "groups": group_rows,
        "group_count": len(group_rows),
        "required_group_ids": list(GROUP_IDS),
        "remaining_blockers": blockers,
        "remaining_blocker_count": len(blockers),
        "resolved_blocker_count": 0,
        "generated_at": generated_at,
    }
    value.update(first_live_order_final_blocker_safety_flags())
    return value


def _build_next_actions(
    *,
    market_symbol: str,
    strategy_name: str,
    groups: Sequence[Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    rows = []
    for group in groups:
        group_id = clean_text(group.get("group_id"))
        rows.append(
            {
                "action_id": f"review_{group_id}_blockers",
                "group_id": group_id,
                "group_label": group_label_for(group_id),
                "action": _next_action_text(group_id),
                "allowed_in_this_task": False,
                "requires_separate_operator_task": True,
                "must_not_include_secret_values": True,
                "must_not_execute_order": True,
                "status": STATUS_BLOCKED,
            }
        )
    value = {
        "contract_version": FIRST_LIVE_ORDER_FINAL_NEXT_ACTIONS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "next_actions": rows,
        "next_action_count": len(rows),
        "all_actions_require_separate_operator_task": True,
        "no_action_allowed_to_execute": True,
        "generated_at": generated_at,
    }
    value.update(first_live_order_final_blocker_safety_flags())
    return value


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    blocker_groups: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
    path_refs: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    groups = [dict(row) for row in blocker_groups.get("groups", []) if isinstance(row, Mapping)]
    unknown_group_ids = [
        clean_text(group.get("group_id"))
        for group in groups
        if int(group.get("unknown_evidence_count", 0) or 0) > 0
    ]
    missing_artifact_keys = [
        clean_text(row.get("artifact_key"))
        for row in observations
        if row.get("exists") is not True or row.get("parsed") is not True
    ]
    value = {
        "contract_version": FIRST_LIVE_ORDER_FINAL_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": STATUS_BLOCKED,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "remaining_blocker_count": int(blocker_groups.get("remaining_blocker_count", 0) or 0),
        "resolved_blocker_count": 0,
        "group_count": len(groups),
        "required_group_ids": list(GROUP_IDS),
        "unknown_group_ids": unknown_group_ids,
        "unknown_group_count": len(unknown_group_ids),
        "missing_or_unreadable_artifact_keys": missing_artifact_keys,
        "artifact_path": clean_text(path_refs.get("result")),
        "latest_status_path": clean_text(path_refs.get("latest_status")),
        "blocker_groups_path": clean_text(path_refs.get("blocker_groups")),
        "next_actions_path": clean_text(path_refs.get("next_actions")),
        "safety_snapshot_path": clean_text(path_refs.get("safety_snapshot")),
        "operator_summary_path": clean_text(path_refs.get("operator_summary_md")),
        "live_execution_authorization": "blocked",
        "signing": "blocked",
        "order_submission": "blocked",
        "order_cancellation": "blocked",
        "operator_summary": (
            "Remaining blockers grouped for final review. No group authorizes execution, and unknown evidence "
            "remains unknown."
        ),
        "generated_at": generated_at,
    }
    value.update(first_live_order_final_blocker_safety_flags())
    return value


def _candidate_paths(
    override: str | Path | Sequence[str | Path] | None,
    default_candidates: Sequence[Path],
) -> tuple[Path, ...]:
    if override is None:
        return tuple(default_candidates)
    if isinstance(override, (str, Path)):
        return (Path(override),)
    return tuple(Path(item) for item in override)


def _first_existing(paths: Sequence[Path]) -> Path | None:
    for path in paths:
        if path.exists() and path.is_file():
            return path
    return None


def _missing_artifact_summary(artifact_key: str, candidates: Sequence[Path]) -> dict[str, Any]:
    return {
        "artifact_key": artifact_key,
        "artifact_label": _artifact_label(artifact_key),
        "exists": False,
        "parsed": False,
        "evidence_status": STATUS_UNKNOWN,
        "status": STATUS_UNKNOWN,
        "contract_version": "",
        "validation_status": STATUS_UNKNOWN,
        "validation_valid": "unknown",
        "observed_allowed_for_live_status": "unknown",
        "observed_resolved_count_status": "unknown",
        "selected_path": "",
        "candidate_paths": [normalize_path(path) for path in candidates],
        "safe_for_reducer_output": True,
    }


def _read_artifact_summary(
    artifact_key: str,
    selected: Path,
    candidates: Sequence[Path],
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _invalid_artifact_summary(artifact_key, selected, candidates, "JSONDecodeError"), {}
    except OSError as exc:
        return _invalid_artifact_summary(artifact_key, selected, candidates, type(exc).__name__), {}
    if not isinstance(payload, dict):
        return _invalid_artifact_summary(artifact_key, selected, candidates, "NonObjectJSON"), {}

    validation = _find_mapping(payload, "validation")
    validation_valid = validation.get("valid") if validation else _field(payload, "valid")
    allowed_status = _safe_bool_status(_field(payload, "allowed_for_live"), safe_false="safe_false")
    resolved_status = _resolved_count_status(_field(payload, "resolved_blocker_count"))
    summary = {
        "artifact_key": artifact_key,
        "artifact_label": _artifact_label(artifact_key),
        "exists": True,
        "parsed": True,
        "evidence_status": "present",
        "status": _text_field(payload, "status") or "status_missing",
        "contract_version": _text_field(payload, "contract_version"),
        "validation_status": clean_text(validation.get("status")) if validation else "",
        "validation_valid": validation_valid if isinstance(validation_valid, bool) else "unknown",
        "observed_allowed_for_live_status": allowed_status,
        "observed_resolved_count_status": resolved_status,
        "selected_path": normalize_path(selected),
        "candidate_paths": [normalize_path(path) for path in candidates],
        "safe_for_reducer_output": True,
    }
    return summary, payload


def _invalid_artifact_summary(
    artifact_key: str,
    selected: Path,
    candidates: Sequence[Path],
    error_type: str,
) -> dict[str, Any]:
    return {
        "artifact_key": artifact_key,
        "artifact_label": _artifact_label(artifact_key),
        "exists": True,
        "parsed": False,
        "evidence_status": STATUS_UNKNOWN,
        "status": "invalid_or_unreadable",
        "contract_version": "",
        "validation_status": STATUS_UNKNOWN,
        "validation_valid": "unknown",
        "observed_allowed_for_live_status": "unknown",
        "observed_resolved_count_status": "unknown",
        "selected_path": normalize_path(selected),
        "candidate_paths": [normalize_path(path) for path in candidates],
        "read_error_type": clean_text(error_type),
        "safe_for_reducer_output": True,
    }


def _payload(observed: Mapping[str, Mapping[str, Any]], key: str) -> dict[str, Any]:
    payload = dict(observed.get(key, {}).get("payload", {}))
    return payload


def _missing(observed: Mapping[str, Mapping[str, Any]], key: str) -> bool:
    summary = dict(observed.get(key, {}).get("summary", {}))
    return summary.get("exists") is not True or summary.get("parsed") is not True


def _evidence_status_for_payload(payload: Mapping[str, Any]) -> str:
    if not payload:
        return STATUS_UNKNOWN
    if _field(payload, "allowed_for_live") is True:
        return "blocked_unsafe_activation_observed"
    return STATUS_BLOCKED


def _reference_rows(observed: Mapping[str, Mapping[str, Any]], keys: Sequence[str]) -> list[dict[str, Any]]:
    rows = []
    for key in keys:
        summary = dict(observed.get(key, {}).get("summary", {}))
        rows.append(
            {
                "artifact_key": key,
                "artifact_label": _artifact_label(key),
                "exists": summary.get("exists") is True,
                "parsed": summary.get("parsed") is True,
                "evidence_status": clean_text(summary.get("evidence_status")) or STATUS_UNKNOWN,
                "status": clean_text(summary.get("status")) or STATUS_UNKNOWN,
                "selected_path": clean_text(summary.get("selected_path")),
            }
        )
    return rows


def _group_reference_keys() -> dict[str, tuple[str, ...]]:
    return {
        "credentials_auth": ("credentials_auth", "local_real_check_bundle", "order_prep_packet"),
        "account_balance": ("account_state", "local_real_check_bundle"),
        "signer": ("signer_diagnostic", "local_real_check_bundle"),
        "token_selection": ("order_prep_packet", "token_selection"),
        "signed_payload_dry_run": ("signed_payload_dry_run", "order_prep_packet", "token_selection"),
        "approval": ("approval_contract", "order_prep_packet"),
        "live_execution_authorization": tuple(DEFAULT_INPUT_ARTIFACT_CANDIDATES),
    }


def _next_action_text(group_id: str) -> str:
    return {
        "credentials_auth": "collect commit-safe credentials/auth readiness evidence in a separate approved task",
        "account_balance": "review read-only account/balance evidence without emitting account values",
        "signer": "review signer diagnostic evidence; do not treat diagnostic signing as order signing",
        "token_selection": "match the order prep packet to an explicit token target without inventing IDs",
        "signed_payload_dry_run": "review non-executable signed payload dry-run evidence; do not emit signed material",
        "approval": "record exact operator approval only in a separate supervised task",
        "live_execution_authorization": "keep live execution blocked until a separate authorization task exists",
    }.get(group_id, "review blocker evidence in a separate supervised task")


def _artifact_label(artifact_key: str) -> str:
    return {
        "order_prep_packet": "order prep packet/check artifact",
        "local_real_check_bundle": "local real-check bundle",
        "credentials_auth": "credentials/auth readiness",
        "account_state": "account/balance read-only state",
        "signer_diagnostic": "guarded signer diagnostic",
        "token_selection": "market token selection",
        "signed_payload_dry_run": "signed payload dry-run",
        "approval_contract": "operator approval contract",
        "initial_blocker_matrix": "initial first live order blocker matrix",
    }.get(artifact_key, artifact_key)


def _field(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        if key in value:
            return value[key]
        for nested in value.values():
            found = _field(nested, key)
            if found is not _MISSING:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _field(nested, key)
            if found is not _MISSING:
                return found
    return _MISSING


def _text_field(value: Any, key: str) -> str:
    found = _field(value, key)
    if found is _MISSING:
        return ""
    return clean_text(found)


def _find_mapping(value: Any, key: str) -> dict[str, Any]:
    found = _field(value, key)
    return dict(found) if isinstance(found, Mapping) else {}


def _safe_bool_status(value: Any, *, safe_false: str) -> str:
    if value is False:
        return safe_false
    if value is True:
        return "unsafe_true"
    return "unknown"


def _resolved_count_status(value: Any) -> str:
    if value is _MISSING:
        return "unknown"
    try:
        return "zero" if int(value) == 0 else "nonzero"
    except (TypeError, ValueError):
        return "unknown"


class _Missing:
    pass


_MISSING = _Missing()
