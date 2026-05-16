from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.real_local_check_evidence_review_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    GROUPS,
    GROUP_IDS,
    MODE,
    STATUS_BLOCKED,
    STATUS_EVIDENCE_PRESENT,
    STATUS_MISSING,
    STATUS_REVIEW_REQUIRED,
    STATUS_UNKNOWN,
    STATUS_UNREADABLE,
    TASK_ID,
    RealLocalCheckEvidenceBlocker,
    RealLocalCheckEvidenceGroup,
    RealLocalCheckEvidenceLatestStatus,
    RealLocalCheckEvidenceReference,
    RealLocalCheckEvidenceReviewResult,
    build_blockers_artifact,
    build_groups_artifact,
    build_safety_snapshot,
    group_label_for,
    real_local_check_evidence_review_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, load_json_object, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "real_local_check_evidence_review_074a"

SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A = "local_real_check_snapshot_073a"
SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C = "local_real_check_bundle_072c"
SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C = "clob_l2_auth_readonly_probe_067c"
SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C = "live_account_readonly_state_probe_070c"
SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A = "guarded_signer_diagnostic_smoke_069a"
SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D = "discovery_to_token_resolver_bridge_071d"
SOURCE_FIRST_ORDER_MARKET_TOKEN_RESOLVER_070B = "first_order_market_token_resolver_070b"
SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B = "operator_token_selection_packet_073b"
SOURCE_SELECTED_TOKEN_PAYLOAD_READINESS_GATE_073C = "selected_token_payload_readiness_gate_073c"
SOURCE_FIRST_LIVE_ORDER_APPROVAL_CONTRACT_065D = "first_live_order_approval_contract_065d"
SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D = "first_live_order_final_blocker_reducer_072d"

SOURCE_SEQUENCE = (
    SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,
    SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C,
    SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C,
    SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C,
    SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A,
    SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D,
    SOURCE_FIRST_ORDER_MARKET_TOKEN_RESOLVER_070B,
    SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B,
    SOURCE_SELECTED_TOKEN_PAYLOAD_READINESS_GATE_073C,
    SOURCE_FIRST_LIVE_ORDER_APPROVAL_CONTRACT_065D,
    SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,
)

SOURCE_LABELS = {
    SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A: "073A local real-check snapshot",
    SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C: "072C local real-check bundle",
    SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C: "067C CLOB L2 auth read-only probe",
    SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C: "070C account/balance/allowance read-only probe",
    SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A: "069A guarded signer diagnostic",
    SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D: "071D discovery-to-token bridge",
    SOURCE_FIRST_ORDER_MARKET_TOKEN_RESOLVER_070B: "070B first order market token resolver",
    SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B: "073B operator token selection packet",
    SOURCE_SELECTED_TOKEN_PAYLOAD_READINESS_GATE_073C: "073C selected-token payload readiness gate",
    SOURCE_FIRST_LIVE_ORDER_APPROVAL_CONTRACT_065D: "065D first live order approval contract",
    SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D: "072D first live order final blocker reducer",
}

SOURCE_SPECS: dict[str, dict[str, tuple[str, ...]]] = {
    SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A: {
        "dir_names": ("local_real_check_snapshot_073a",),
        "filenames": ("latest_local_real_check_snapshot_status_073a.json", "local_real_check_snapshot_073a_result.json"),
    },
    SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C: {
        "dir_names": ("local_real_check_bundle_072c",),
        "filenames": ("latest_local_real_check_bundle_status_072c.json", "local_real_check_bundle_072c_result.json"),
    },
    SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C: {
        "dir_names": ("clob_l2_auth_readonly_probe_067c",),
        "filenames": ("latest_clob_l2_auth_readonly_probe_status_067c.json", "clob_l2_auth_readonly_probe_067c_result.json"),
    },
    SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C: {
        "dir_names": ("live_account_readonly_state_probe_070c",),
        "filenames": ("latest_live_account_readonly_state_status_070c.json", "live_account_readonly_state_probe_070c_result.json"),
    },
    SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A: {
        "dir_names": ("guarded_signer_diagnostic_smoke_069a",),
        "filenames": ("latest_guarded_signer_diagnostic_status_069a.json", "guarded_signer_diagnostic_smoke_069a_result.json"),
    },
    SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D: {
        "dir_names": ("discovery_to_token_resolver_bridge_071d",),
        "filenames": ("latest_discovery_to_token_resolver_bridge_status_071d.json", "discovery_to_token_resolver_bridge_071d_result.json"),
    },
    SOURCE_FIRST_ORDER_MARKET_TOKEN_RESOLVER_070B: {
        "dir_names": ("first_order_market_token_resolver_070b",),
        "filenames": (
            "latest_first_order_market_token_status_070b.json",
            "first_order_market_token_resolver_070b_result.json",
            "first_order_market_token_contract_070b.json",
        ),
    },
    SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B: {
        "dir_names": ("operator_token_selection_packet_073b",),
        "filenames": (
            "latest_operator_token_selection_status_073b.json",
            "operator_token_selection_packet_073b_result.json",
            "operator_token_selection_packet_073b.json",
        ),
    },
    SOURCE_SELECTED_TOKEN_PAYLOAD_READINESS_GATE_073C: {
        "dir_names": ("selected_token_payload_readiness_gate_073c",),
        "filenames": (
            "latest_selected_token_payload_readiness_status_073c.json",
            "selected_token_payload_readiness_gate_073c_result.json",
        ),
    },
    SOURCE_FIRST_LIVE_ORDER_APPROVAL_CONTRACT_065D: {
        "dir_names": ("first_live_order_approval_contract_065d",),
        "filenames": (
            "latest_first_live_order_approval_contract_status_065d.json",
            "first_live_order_approval_contract_065d_result.json",
        ),
    },
    SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D: {
        "dir_names": ("first_live_order_final_blocker_reducer_072d",),
        "filenames": (
            "latest_first_live_order_final_blockers_072d.json",
            "first_live_order_final_blocker_reducer_072d_result.json",
            "first_live_order_blocker_groups_072d.json",
        ),
    },
}

GROUP_SOURCE_IDS = {
    "l2_credentials_auth": (
        SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,
        SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C,
        SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C,
    ),
    "account_balance_allowance": (
        SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,
        SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C,
        SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C,
    ),
    "signer_private_key_diagnostic": (
        SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,
        SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C,
        SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A,
    ),
    "token_selection": (
        SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,
        SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D,
        SOURCE_FIRST_ORDER_MARKET_TOKEN_RESOLVER_070B,
        SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B,
    ),
    "selected_token_payload_readiness": (
        SOURCE_SELECTED_TOKEN_PAYLOAD_READINESS_GATE_073C,
        SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B,
        SOURCE_FIRST_ORDER_MARKET_TOKEN_RESOLVER_070B,
    ),
    "approval": (
        SOURCE_FIRST_LIVE_ORDER_APPROVAL_CONTRACT_065D,
    ),
    "final_blockers": (
        SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,
        SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,
    ),
}

GROUP_EVIDENCE_KEYS = {
    "l2_credentials_auth": ("l2_auth_status", "credential_presence_status", "auth_verified"),
    "account_balance_allowance": ("account_readonly_status", "account_status", "balance_allowance_status", "allowance_status"),
    "signer_private_key_diagnostic": (
        "signer_diagnostic_status",
        "diagnostic_status",
        "diagnostic_requested",
        "derived_wallet_matches_expected",
        "private_key_diagnostic_requested",
    ),
    "token_selection": (
        "token_bridge_status",
        "operator_selection_required",
        "target_token_id_present",
        "target_token_id_source_backed",
        "selected_token_id_present",
        "selected_token_source_backed",
        "source_backed_candidate_count",
    ),
    "selected_token_payload_readiness": (
        "ready_for_signed_payload_diagnostic",
        "selected_token_payload_ready_for_submit",
        "selected_token_present",
        "selected_token_verified",
        "signer_diagnostic_status",
        "approval_contract_status",
        "signed_payload_dry_run_status",
    ),
    "approval": (
        "operator_approval_recorded",
        "approval_consumed",
        "approval_contract_status",
        "required_approval_text_present",
    ),
    "final_blockers": (
        "remaining_blocker_count",
        "unknown_group_count",
        "unknown_group_ids",
        "live_execution_authorization",
        "signing",
        "order_submission",
        "order_cancellation",
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
    "--record-approval",
    "--post",
    "--put",
    "--patch",
    "--delete",
    "--browser",
    "--loop",
    "--daemon",
    "--scheduler",
)


def real_local_check_evidence_review_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "real_local_check_evidence_review_074a_result.json",
        "latest_status": root / "latest_real_local_check_evidence_review_status_074a.json",
        "evidence_groups": root / "real_local_check_evidence_review_groups_074a.json",
        "blockers": root / "real_local_check_evidence_review_blockers_074a.json",
        "safety_snapshot": root / "real_local_check_evidence_review_safety_snapshot_074a.json",
        "operator_diagnosis_md": root / "real_local_check_evidence_review_operator_diagnosis_074a.md",
    }


def run_real_local_check_evidence_review(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("real local-check evidence review requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = real_local_check_evidence_review_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    source_rows, source_payloads = _load_sources(root=root, generated_at=generated_at)
    groups = _build_groups(
        source_rows=source_rows,
        source_payloads=source_payloads,
        generated_at=generated_at,
    )
    blockers = [
        dict(blocker)
        for group in groups
        for blocker in group.get("blockers", [])
        if isinstance(blocker, Mapping)
    ]
    groups_artifact = build_groups_artifact(
        groups=groups,
        market=market_symbol,
        strategy=strategy_name,
        generated_at=generated_at,
    )
    blockers_artifact = build_blockers_artifact(
        blockers=blockers,
        market=market_symbol,
        strategy=strategy_name,
        generated_at=generated_at,
    )
    safety_snapshot = build_safety_snapshot(
        market=market_symbol,
        strategy=strategy_name,
        artifact_root=_safe_path(root),
        generated_at=generated_at,
    )
    latest_status = RealLocalCheckEvidenceLatestStatus(
        market=market_symbol,
        strategy=strategy_name,
        groups=groups,
        blocker_count=len(blockers),
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()
    result = RealLocalCheckEvidenceReviewResult(
        market=market_symbol,
        strategy=strategy_name,
        artifact_root=_safe_path(root),
        groups_artifact=groups_artifact,
        blockers_artifact=blockers_artifact,
        safety_snapshot=safety_snapshot,
        latest_status=latest_status,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["evidence_groups"], groups_artifact)
    write_json(paths["blockers"], blockers_artifact)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_diagnosis_md"], render_real_local_check_evidence_review_markdown(result))
    return result


def render_real_local_check_evidence_review_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Real local-check evidence review 074A completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
            f"Evidence groups: {int(value.get('group_count', 0) or 0)}",
            f"Blocking groups: {int(value.get('blocking_group_count', 0) or 0)}",
            f"Unknown groups: {int(value.get('unknown_group_count', 0) or 0)}",
            f"Remaining blockers: {int(value.get('remaining_blocker_count', 0) or 0)}",
            "Allowed for live: false",
            "Live execution authorization: blocked",
            "Signing: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_real_local_check_evidence_review_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    groups = [dict(row) for row in value.get("groups", []) if isinstance(row, Mapping)]
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Real Local-Check Evidence Review 074A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        f"- execution_mode: `{value.get('execution_mode')}`",
        "- allowed_for_live: `false`",
        "- review_executable_for_live: `false`",
        "- local artifact evidence only",
        "- no submit, no cancel, no signing, no wallet, no live execution authorization",
        "",
        "## Diagnosis",
        "",
    ]
    for group in groups:
        references = [dict(row) for row in group.get("evidence_references", []) if isinstance(row, Mapping)]
        blockers = [dict(row) for row in group.get("blockers", []) if isinstance(row, Mapping)]
        lines.extend(
            [
                f"### {group.get('group_label')}",
                "",
                f"- status: `{group.get('status')}`",
                f"- diagnosis: {group.get('diagnosis')}",
                "- evidence:",
                *bullet_lines(
                    f"`{row.get('source_id')}` exists={str(row.get('exists') is True).lower()} "
                    f"parsed={str(row.get('parsed') is True).lower()} status=`{row.get('status')}` "
                    f"path=`{row.get('selected_path') or 'missing'}`"
                    for row in references
                ),
                "- blockers:",
                *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
                "",
            ]
        )
    lines.extend(
        [
            "## Artifacts",
            "",
            *bullet_lines(f"`{path}`" for path in paths.values()),
            "",
            "## Safety Statement",
            "",
            "074A reads known local JSON artifacts and emits a human-readable diagnosis. It does not run live checks, "
            "call networks, read environment secret values, read private material, sign payloads, generate executable "
            "orders, submit orders, cancel orders, connect wallets, create browser automation, create schedulers, "
            "create daemons, or run background workers.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "real local-check evidence review is local-artifact-only/no-live; unsupported live/auth/wallet/sign/order/write flag(s): "
            + ", ".join(requested)
        )


def _load_sources(
    *,
    root: Path,
    generated_at: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source_rows: dict[str, dict[str, Any]] = {}
    source_payloads: dict[str, dict[str, Any]] = {}
    for source_id in SOURCE_SEQUENCE:
        row, payload = _load_source(source_id, root=root, generated_at=generated_at)
        source_rows[source_id] = row
        source_payloads[source_id] = payload
    return source_rows, source_payloads


def _load_source(
    source_id: str,
    *,
    root: Path,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidates = _candidate_paths(source_id, root=root)
    selected = _first_existing(candidates)
    if selected is None:
        row = {
            "source_id": source_id,
            "source_label": SOURCE_LABELS.get(source_id, source_id),
            "exists": False,
            "parsed": False,
            "status": STATUS_MISSING,
            "selected_path": "",
            "candidate_paths": [_safe_path(path) for path in candidates],
            "contract_version_seen": "",
            "load_error": "",
            "generated_at": generated_at,
        }
        return row, {}
    try:
        payload = load_json_object(selected, label=SOURCE_LABELS.get(source_id, source_id))
    except Exception as exc:
        row = {
            "source_id": source_id,
            "source_label": SOURCE_LABELS.get(source_id, source_id),
            "exists": True,
            "parsed": False,
            "status": STATUS_UNREADABLE,
            "selected_path": _safe_path(selected),
            "candidate_paths": [_safe_path(path) for path in candidates],
            "contract_version_seen": "",
            "load_error": _safe_status(type(exc).__name__) or STATUS_UNREADABLE,
            "generated_at": generated_at,
        }
        return row, {}
    latest = _latest_payload(payload)
    row = {
        "source_id": source_id,
        "source_label": SOURCE_LABELS.get(source_id, source_id),
        "exists": True,
        "parsed": True,
        "status": _safe_status(latest.get("status") or payload.get("status")) or STATUS_EVIDENCE_PRESENT,
        "selected_path": _safe_path(selected),
        "candidate_paths": [_safe_path(path) for path in candidates],
        "contract_version_seen": _safe_status(latest.get("contract_version") or payload.get("contract_version")),
        "load_error": "",
        "generated_at": generated_at,
    }
    return row, payload


def _build_groups(
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    return [
        _build_group(
            group_id=group_id,
            source_rows=source_rows,
            source_payloads=source_payloads,
            generated_at=generated_at,
        )
        for group_id, _ in GROUPS
    ]


def _build_group(
    *,
    group_id: str,
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    source_ids = GROUP_SOURCE_IDS[group_id]
    references = tuple(
        _reference(
            source_id,
            source_rows=source_rows,
            source_payloads=source_payloads,
            evidence_keys=GROUP_EVIDENCE_KEYS[group_id],
            generated_at=generated_at,
        )
        for source_id in source_ids
    )
    blockers = _blockers_for_group(
        group_id,
        source_rows=source_rows,
        source_payloads=source_payloads,
        generated_at=generated_at,
    )
    return RealLocalCheckEvidenceGroup(
        group_id=group_id,
        status=_group_status(blockers),
        diagnosis=_diagnosis_for_group(group_id, blockers=blockers),
        evidence_references=references,
        blockers=tuple(blockers),
        generated_at=generated_at,
    ).to_dict()


def _blockers_for_group(
    group_id: str,
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    if group_id == "l2_credentials_auth":
        return _l2_credentials_blockers(source_rows, source_payloads, generated_at=generated_at)
    if group_id == "account_balance_allowance":
        return _account_blockers(source_rows, source_payloads, generated_at=generated_at)
    if group_id == "signer_private_key_diagnostic":
        return _signer_blockers(source_rows, source_payloads, generated_at=generated_at)
    if group_id == "token_selection":
        return _token_selection_blockers(source_rows, source_payloads, generated_at=generated_at)
    if group_id == "selected_token_payload_readiness":
        return _selected_token_payload_blockers(source_rows, source_payloads, generated_at=generated_at)
    if group_id == "approval":
        return _approval_blockers(source_rows, source_payloads, generated_at=generated_at)
    return _final_blockers(source_rows, source_payloads, generated_at=generated_at)


def _l2_credentials_blockers(
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    group_id = "l2_credentials_auth"
    statuses = _statuses(
        (
            (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A, ("l2_auth_status",)),
            (SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C, ("l2_auth_status", "status")),
            (SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C, ("l2_auth_status", "status")),
        ),
        source_rows=source_rows,
        source_payloads=source_payloads,
    )
    blockers = _missing_blockers(group_id, (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,), source_rows, generated_at=generated_at)
    if not _any_status_success(statuses, ("authenticated_readonly_probe_succeeded_live_blocked",)):
        blockers.append(
            _blocker(
                "l2_credentials_auth_not_confirmed",
                group_id,
                "L2 credentials/auth readiness is not confirmed by the local snapshot or read-only probe evidence.",
                _worst_status(statuses),
                (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A, SOURCE_CLOB_L2_AUTH_READONLY_PROBE_067C, SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C),
                generated_at=generated_at,
            )
        )
    return _dedupe_blockers(blockers)


def _account_blockers(
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    group_id = "account_balance_allowance"
    statuses = _statuses(
        (
            (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A, ("account_readonly_status",)),
            (SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C, ("account_readonly_status", "status")),
            (SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C, ("account_status", "balance_allowance_status", "status")),
        ),
        source_rows=source_rows,
        source_payloads=source_payloads,
    )
    blockers = _missing_blockers(group_id, (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,), source_rows, generated_at=generated_at)
    if not _any_status_success(statuses, ("account_state_probe_succeeded_live_blocked",)):
        blockers.append(
            _blocker(
                "account_balance_allowance_not_confirmed",
                group_id,
                "Account, balance, and allowance readiness is not confirmed by commit-safe read-only evidence.",
                _worst_status(statuses),
                (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A, SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C, SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C),
                generated_at=generated_at,
            )
        )
    blockers.append(
        _blocker(
            "account_values_not_execution_authorization",
            group_id,
            "Even successful read-only account evidence would not authorize a live order; this review emits no account values.",
            STATUS_REVIEW_REQUIRED,
            (SOURCE_LIVE_ACCOUNT_READONLY_STATE_PROBE_070C, SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C),
            generated_at=generated_at,
        )
    )
    return _dedupe_blockers(blockers)


def _signer_blockers(
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    group_id = "signer_private_key_diagnostic"
    statuses = _statuses(
        (
            (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A, ("signer_diagnostic_status",)),
            (SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C, ("signer_diagnostic_status", "status")),
            (SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A, ("diagnostic_status", "status")),
        ),
        source_rows=source_rows,
        source_payloads=source_payloads,
    )
    blockers = _missing_blockers(group_id, (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,), source_rows, generated_at=generated_at)
    if not _any_status_success(statuses, ("diagnostic_ok",)):
        blockers.append(
            _blocker(
                "signer_private_key_diagnostic_not_ok",
                group_id,
                "Guarded signer/private-key diagnostic evidence is not diagnostic_ok.",
                _worst_status(statuses),
                (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A, SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A, SOURCE_LOCAL_REAL_CHECK_BUNDLE_072C),
                generated_at=generated_at,
            )
        )
    blockers.append(
        _blocker(
            "signer_diagnostic_not_order_signing_authorization",
            group_id,
            "A diagnostic challenge is not authorization to sign an order payload, and 074A performs no signing.",
            STATUS_REVIEW_REQUIRED,
            (SOURCE_GUARDED_SIGNER_DIAGNOSTIC_SMOKE_069A,),
            generated_at=generated_at,
        )
    )
    return _dedupe_blockers(blockers)


def _token_selection_blockers(
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    group_id = "token_selection"
    statuses = _statuses(
        (
            (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A, ("token_bridge_status",)),
            (SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D, ("token_bridge_status", "status")),
            (SOURCE_FIRST_ORDER_MARKET_TOKEN_RESOLVER_070B, ("status",)),
            (SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B, ("status",)),
        ),
        source_rows=source_rows,
        source_payloads=source_payloads,
    )
    blockers = _missing_blockers(
        group_id,
        (SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A, SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B),
        source_rows,
        generated_at=generated_at,
    )
    if not (
        _any_status_success(statuses, ("selected_source_backed_candidate", "first_order_market_token_contract_ready_review_only"))
        or _safe_bool_from_source(SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B, "selected_token_source_backed", source_payloads) is True
    ):
        blockers.append(
            _blocker(
                "token_selection_not_final",
                group_id,
                "Token selection is not final and source-backed in the local evidence; no token is invented by this review.",
                _worst_status(statuses),
                (
                    SOURCE_LOCAL_REAL_CHECK_SNAPSHOT_073A,
                    SOURCE_DISCOVERY_TO_TOKEN_RESOLVER_BRIDGE_071D,
                    SOURCE_FIRST_ORDER_MARKET_TOKEN_RESOLVER_070B,
                    SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B,
                ),
                generated_at=generated_at,
            )
        )
    else:
        blockers.append(
            _blocker(
                "token_selection_requires_operator_match_review",
                group_id,
                "A source-backed token selection still needs final operator match review before any later live-capable task.",
                STATUS_REVIEW_REQUIRED,
                (SOURCE_OPERATOR_TOKEN_SELECTION_PACKET_073B, SOURCE_FIRST_ORDER_MARKET_TOKEN_RESOLVER_070B),
                generated_at=generated_at,
            )
        )
    return _dedupe_blockers(blockers)


def _selected_token_payload_blockers(
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    group_id = "selected_token_payload_readiness"
    status = _status_from_source(
        SOURCE_SELECTED_TOKEN_PAYLOAD_READINESS_GATE_073C,
        ("status",),
        source_rows=source_rows,
        source_payloads=source_payloads,
    )
    blockers = _missing_blockers(
        group_id,
        (SOURCE_SELECTED_TOKEN_PAYLOAD_READINESS_GATE_073C,),
        source_rows,
        generated_at=generated_at,
    )
    if status != "ready_for_signed_payload_diagnostic":
        blockers.append(
            _blocker(
                "selected_token_payload_readiness_not_ready",
                group_id,
                "Selected-token payload readiness is not ready for a future signed payload diagnostic.",
                status,
                (SOURCE_SELECTED_TOKEN_PAYLOAD_READINESS_GATE_073C,),
                generated_at=generated_at,
            )
        )
    blockers.append(
        _blocker(
            "selected_token_payload_not_submit_ready",
            group_id,
            "Selected-token payload readiness is not submit readiness; 074A does not generate or sign payloads.",
            STATUS_REVIEW_REQUIRED,
            (SOURCE_SELECTED_TOKEN_PAYLOAD_READINESS_GATE_073C,),
            generated_at=generated_at,
        )
    )
    return _dedupe_blockers(blockers)


def _approval_blockers(
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    group_id = "approval"
    status = _status_from_source(
        SOURCE_FIRST_LIVE_ORDER_APPROVAL_CONTRACT_065D,
        ("approval_contract_status", "status"),
        source_rows=source_rows,
        source_payloads=source_payloads,
    )
    blockers = _missing_blockers(
        group_id,
        (SOURCE_FIRST_LIVE_ORDER_APPROVAL_CONTRACT_065D,),
        source_rows,
        generated_at=generated_at,
    )
    if status != "approval_contract_defined_execution_blocked":
        blockers.append(
            _blocker(
                "approval_contract_not_confirmed",
                group_id,
                "The approval contract is missing or not the expected non-executable approval definition.",
                status,
                (SOURCE_FIRST_LIVE_ORDER_APPROVAL_CONTRACT_065D,),
                generated_at=generated_at,
            )
        )
    blockers.append(
        _blocker(
            "operator_approval_not_recorded_or_consumed",
            group_id,
            "No separate operator approval is recorded or consumed by this review.",
            STATUS_BLOCKED,
            (SOURCE_FIRST_LIVE_ORDER_APPROVAL_CONTRACT_065D,),
            generated_at=generated_at,
        )
    )
    return _dedupe_blockers(blockers)


def _final_blockers(
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    group_id = "final_blockers"
    blockers = _missing_blockers(
        group_id,
        (SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,),
        source_rows,
        generated_at=generated_at,
    )
    remaining = _safe_int_from_source(
        SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,
        "remaining_blocker_count",
        source_payloads,
    )
    status = _status_from_source(
        SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,
        ("status",),
        source_rows=source_rows,
        source_payloads=source_payloads,
    )
    if remaining > 0:
        blockers.append(
            _blocker(
                "final_blocker_reducer_reports_remaining_blockers",
                group_id,
                f"072D reports {remaining} remaining blocker(s); none are resolved by 074A.",
                status,
                (SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,),
                generated_at=generated_at,
            )
        )
    elif status not in {STATUS_MISSING, STATUS_UNREADABLE}:
        blockers.append(
            _blocker(
                "final_blocker_reducer_does_not_clear_execution",
                group_id,
                "Final blocker evidence does not provide live execution authorization.",
                status or STATUS_UNKNOWN,
                (SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,),
                generated_at=generated_at,
            )
        )
    blockers.append(
        _blocker(
            "separate_live_execution_authorization_missing",
            group_id,
            "No separate operator-approved live execution authorization artifact is present or consumed.",
            STATUS_BLOCKED,
            (SOURCE_FIRST_LIVE_ORDER_FINAL_BLOCKER_REDUCER_072D,),
            generated_at=generated_at,
        )
    )
    blockers.append(
        _blocker(
            "submit_cancel_signing_forbidden_in_074a",
            group_id,
            "074A is diagnosis-only and cannot submit, cancel, sign, connect a wallet, or make trading write calls.",
            STATUS_BLOCKED,
            (),
            generated_at=generated_at,
        )
    )
    return _dedupe_blockers(blockers)


def _missing_blockers(
    group_id: str,
    source_ids: Sequence[str],
    source_rows: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for source_id in source_ids:
        row = dict(source_rows.get(source_id, {}))
        if row.get("exists") is not True:
            blockers.append(
                _blocker(
                    f"{source_id}_missing",
                    group_id,
                    f"{SOURCE_LABELS.get(source_id, source_id)} is missing; no readiness was inferred.",
                    STATUS_MISSING,
                    (source_id,),
                    generated_at=generated_at,
                )
            )
        elif row.get("parsed") is not True:
            blockers.append(
                _blocker(
                    f"{source_id}_unreadable",
                    group_id,
                    f"{SOURCE_LABELS.get(source_id, source_id)} exists but is unreadable; no readiness was inferred.",
                    STATUS_UNREADABLE,
                    (source_id,),
                    generated_at=generated_at,
                )
            )
    return blockers


def _blocker(
    blocker_id: str,
    group_id: str,
    reason: str,
    evidence_status: str,
    source_ids: Sequence[str],
    *,
    generated_at: str,
) -> dict[str, Any]:
    return RealLocalCheckEvidenceBlocker(
        blocker_id=blocker_id,
        group_id=group_id,
        reason=reason,
        evidence_status=clean_text(evidence_status) or STATUS_UNKNOWN,
        source_ids=tuple(source_ids),
        generated_at=generated_at,
    ).to_dict()


def _reference(
    source_id: str,
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
    evidence_keys: Sequence[str],
    generated_at: str,
) -> dict[str, Any]:
    row = dict(source_rows.get(source_id, {}))
    evidence_fields = _safe_evidence_fields(source_id, evidence_keys, source_payloads)
    return RealLocalCheckEvidenceReference(
        source_id=source_id,
        source_label=SOURCE_LABELS.get(source_id, source_id),
        exists=row.get("exists") is True,
        parsed=row.get("parsed") is True,
        status=clean_text(row.get("status")) or STATUS_UNKNOWN,
        selected_path=clean_text(row.get("selected_path")),
        contract_version_seen=clean_text(row.get("contract_version_seen")),
        evidence_fields=evidence_fields,
        load_error=clean_text(row.get("load_error")),
        generated_at=generated_at,
    ).to_dict()


def _safe_evidence_fields(
    source_id: str,
    evidence_keys: Sequence[str],
    source_payloads: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    payload = dict(source_payloads.get(source_id, {}))
    latest = _latest_payload(payload)
    result: dict[str, Any] = {}
    for key in evidence_keys:
        found = _field(latest, key)
        if found is _MISSING:
            found = _field(payload, key)
        if found is _MISSING:
            continue
        result[key] = _safe_scalar(found)
    return result


def _statuses(
    specs: Sequence[tuple[str, Sequence[str]]],
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    return [
        _status_from_source(source_id, keys, source_rows=source_rows, source_payloads=source_payloads)
        for source_id, keys in specs
    ]


def _status_from_source(
    source_id: str,
    preferred_keys: Sequence[str],
    *,
    source_rows: Mapping[str, Mapping[str, Any]],
    source_payloads: Mapping[str, Mapping[str, Any]],
) -> str:
    row = dict(source_rows.get(source_id, {}))
    if row.get("exists") is not True:
        return STATUS_MISSING
    if row.get("parsed") is not True:
        return STATUS_UNREADABLE
    payload = dict(source_payloads.get(source_id, {}))
    latest = _latest_payload(payload)
    for key in preferred_keys:
        found = _field(latest, key)
        if found is _MISSING:
            found = _field(payload, key)
        if found is not _MISSING:
            return _safe_status(found) or STATUS_UNKNOWN
    return clean_text(row.get("status")) or STATUS_UNKNOWN


def _any_status_success(statuses: Sequence[str], expected_statuses: Sequence[str]) -> bool:
    lowered = {clean_text(status).lower() for status in statuses}
    return any(clean_text(expected).lower() in lowered for expected in expected_statuses)


def _worst_status(statuses: Sequence[str]) -> str:
    cleaned = [clean_text(status) for status in statuses if clean_text(status)]
    for status in cleaned:
        if status in {STATUS_UNREADABLE, STATUS_MISSING, STATUS_UNKNOWN}:
            return status
    for status in cleaned:
        lowered = status.lower()
        if "blocked" in lowered or "missing" in lowered or "required" in lowered or "unverified" in lowered:
            return status
    return cleaned[0] if cleaned else STATUS_UNKNOWN


def _group_status(blockers: Sequence[Mapping[str, Any]]) -> str:
    if not blockers:
        return STATUS_EVIDENCE_PRESENT
    statuses = {clean_text(row.get("evidence_status")) for row in blockers}
    if statuses <= {STATUS_MISSING, STATUS_UNREADABLE, STATUS_UNKNOWN}:
        return STATUS_UNKNOWN
    if STATUS_MISSING in statuses or STATUS_UNREADABLE in statuses or STATUS_UNKNOWN in statuses:
        return STATUS_UNKNOWN
    return STATUS_BLOCKED


def _diagnosis_for_group(group_id: str, *, blockers: Sequence[Mapping[str, Any]]) -> str:
    label = group_label_for(group_id)
    if not blockers:
        return f"{label} evidence is present, but it is still review evidence only and not live authorization."
    blocker_count = len(blockers)
    if _group_status(blockers) == STATUS_UNKNOWN:
        return f"{label} has unknown or missing local evidence and still blocks the first supervised tiny order."
    return f"{label} has {blocker_count} unresolved blocker(s) for the first supervised tiny order."


def _candidate_paths(source_id: str, *, root: Path) -> tuple[Path, ...]:
    spec = SOURCE_SPECS[source_id]
    paths: list[Path] = []
    for dir_name in spec["dir_names"]:
        for filename in spec["filenames"]:
            paths.append(root / clean_text(dir_name) / clean_text(filename))
    for filename in spec["filenames"]:
        paths.append(root / clean_text(filename))
    return _dedupe_paths(paths)


def _first_existing(paths: Sequence[Path]) -> Path | None:
    for path in paths:
        if path.exists() and path.is_file():
            return path
    return None


def _dedupe_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(path)
    return tuple(result)


def _latest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    latest = dict(payload or {}).get("latest_status")
    return dict(latest) if isinstance(latest, Mapping) else dict(payload or {})


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


def _safe_bool_from_source(
    source_id: str,
    key: str,
    source_payloads: Mapping[str, Mapping[str, Any]],
) -> bool | None:
    payload = dict(source_payloads.get(source_id, {}))
    latest = _latest_payload(payload)
    found = _field(latest, key)
    if found is _MISSING:
        found = _field(payload, key)
    return found if isinstance(found, bool) else None


def _safe_int_from_source(
    source_id: str,
    key: str,
    source_payloads: Mapping[str, Mapping[str, Any]],
) -> int:
    payload = dict(source_payloads.get(source_id, {}))
    latest = _latest_payload(payload)
    found = _field(latest, key)
    if found is _MISSING:
        found = _field(payload, key)
    try:
        return int(found)
    except (TypeError, ValueError):
        return 0


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value) if isinstance(value, int) else float(value)
    if isinstance(value, list):
        return [_safe_status(item) for item in value[:10]]
    if isinstance(value, Mapping):
        return "mapping_present_redacted"
    return _safe_status(value)


def _safe_status(value: Any) -> str:
    text = _redact_text(clean_text(value))
    if not text:
        return ""
    lowered = text.lower()
    sensitive_markers = (
        "private key",
        "private_key",
        "api secret",
        "api_secret",
        "passphrase",
        "mnemonic",
        "seed phrase",
        "seed_phrase",
        "auth token",
        "auth_token",
        "raw secret",
        "raw_secret",
        "secret",
    )
    if any(marker in lowered for marker in sensitive_markers):
        return "redacted_sensitive_status"
    if re.fullmatch(r"\d{24,}", text):
        return "present_redacted"
    if len(text) > 220:
        return "available_redacted"
    return text


def _safe_path(path: str | Path) -> str:
    return _redact_text(normalize_path(path))


def _redact_text(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    redacted = re.sub(r"0x[0-9a-fA-F]{64}", "[REDACTED_HEX_64]", text)
    redacted = re.sub(r"0x([0-9a-fA-F]{4})[0-9a-fA-F]{32}([0-9a-fA-F]{4})", r"0x\1...\2", redacted)
    redacted = re.sub(
        r"(?i)\b(private[_-]?key|api[_-]?secret|passphrase|mnemonic|seed[_-]?phrase|auth[_-]?token|secret)\s*[:=]\s*\S+",
        r"\1=[REDACTED]",
        redacted,
    )
    return redacted[:500]


def _dedupe_blockers(blockers: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in blockers:
        value = dict(row)
        blocker_id = clean_text(value.get("blocker_id"))
        if not blocker_id or blocker_id in seen:
            continue
        seen.add(blocker_id)
        result.append(value)
    return result


class _Missing:
    pass


_MISSING = _Missing()


__all__ = [
    "DEFAULT_ARTIFACT_DIR",
    "DEFAULT_ARTIFACT_ROOT",
    "fail_closed_for_forbidden_flags",
    "real_local_check_evidence_review_artifact_paths",
    "render_real_local_check_evidence_review_cli_summary",
    "render_real_local_check_evidence_review_markdown",
    "run_real_local_check_evidence_review",
    "TASK_ID",
]
