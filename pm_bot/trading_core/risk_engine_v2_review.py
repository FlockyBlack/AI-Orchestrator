from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.real_local_check_evidence_review import run_real_local_check_evidence_review
from pm_bot.trading_core.real_local_check_evidence_review_models import GROUP_IDS
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, mapping_rows, normalize_path, write_json

TASK_ID = "ORCH-PMBOT-RISK-ENGINE-V2-074D-REVIEW-NO-LIVE"

STATUS_CONTRACT = "pmbot_risk_engine_v2_review_074d.v1"
RESULT_CONTRACT = "pmbot_risk_engine_v2_review_074d_result.v1"
SAFETY_CONTRACT = "pmbot_risk_engine_v2_review_074d_safety.v1"

ARTIFACT_DIR_NAME = "risk_engine_v2_review_074d"
RESULT_FILENAME = "risk_engine_v2_review_074d_result.json"
LATEST_STATUS_FILENAME = "latest_risk_engine_v2_review_status_074d.json"
SAFETY_SNAPSHOT_FILENAME = "risk_engine_v2_review_safety_snapshot_074d.json"
SOURCE_074A_DIR_NAME = "source_real_local_check_evidence_review_074a"

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME

SAFE_CLI_COMMAND = (
    "python -m pm_bot.operator_runner.risk_engine_v2_review "
    "--market BTC --strategy tiny-momentum --dry-run"
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


def risk_engine_v2_review_artifact_paths(output_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(output_dir) if output_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / RESULT_FILENAME,
        "latest_status": root / LATEST_STATUS_FILENAME,
        "safety_snapshot": root / SAFETY_SNAPSHOT_FILENAME,
        "source_074a_dir": root / SOURCE_074A_DIR_NAME,
    }


def run_risk_engine_v2_review(
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("Risk Engine v2 review requires --dry-run; live execution is blocked")

    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = risk_engine_v2_review_artifact_paths(output_dir)
    source_result = run_real_local_check_evidence_review(
        market=market,
        strategy=strategy,
        dry_run=True,
        artifact_root=root,
        artifact_dir=paths["source_074a_dir"],
        generated_at=generated_at,
    )
    source_paths = dict(source_result.get("artifact_paths", {}))
    source_artifact_path = clean_text(source_paths.get("result")) or normalize_path(
        paths["source_074a_dir"] / "real_local_check_evidence_review_074a_result.json"
    )
    latest_status = _status_from_source_payload(
        source_result,
        artifact_root=root,
        source_artifact_path=source_artifact_path,
        generated_at=generated_at,
    )
    safety_snapshot = build_risk_engine_v2_safety_snapshot(
        artifact_root=root,
        source_artifact_path=source_artifact_path,
        generated_at=generated_at,
    )
    result = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": latest_status["status"],
        "artifact_root": normalize_path(root),
        "latest_status_path": normalize_path(paths["latest_status"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "source_real_local_check_evidence_review_074a_path": source_artifact_path,
        "latest_status": latest_status,
        "safety_snapshot": safety_snapshot,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **risk_engine_v2_safety_flags(),
    }
    write_json(paths["latest_status"], latest_status)
    write_json(paths["safety_snapshot"], safety_snapshot)
    write_json(paths["result"], result)
    return {
        "result_path": normalize_path(paths["result"]),
        "latest_status_path": normalize_path(paths["latest_status"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "result": result,
        "latest_status": latest_status,
        "safety_snapshot": safety_snapshot,
    }


def build_risk_engine_v2_review_status(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    latest_074d_path = _first_existing_path(_risk_engine_v2_latest_paths(root))
    latest_074d = _load_optional_json(latest_074d_path, "Risk Engine v2 074D latest status")
    if latest_074d:
        return normalize_risk_engine_v2_review_status(latest_074d)

    source_path = _first_existing_path(_real_local_check_evidence_review_paths(root))
    source = _load_optional_json(source_path, "real local-check evidence review 074A")
    return _status_from_source_payload(
        source,
        artifact_root=root,
        source_artifact_path=normalize_path(source_path) if source_path else "",
        generated_at=generated_at,
    )


def normalize_risk_engine_v2_review_status(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    unknown_groups = _clean_list(value.get("unknown_evidence_groups") or value.get("unknown_group_ids"))
    top_blockers = _clean_list(value.get("top_blockers") or value.get("top_blocker_reasons"))
    return {
        "contract_version": clean_text(value.get("contract_version") or STATUS_CONTRACT),
        "task_id": clean_text(value.get("task_id") or TASK_ID),
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        "status": clean_text(value.get("status") or "risk_engine_v2_review_missing_live_blocked"),
        "title": "🛡 Risk Engine v2",
        "market": clean_text(value.get("market") or value.get("market_symbol") or "BTC").upper(),
        "strategy": clean_text(value.get("strategy") or value.get("strategy_name") or "tiny-momentum"),
        "gate_count": _int_or_zero(value.get("gate_count"), value.get("group_count"), len(GROUP_IDS)),
        "remaining_blocker_count": _int_or_zero(value.get("remaining_blocker_count"), len(top_blockers)),
        "top_blockers": top_blockers[:8],
        "top_blocker_reasons": top_blockers[:8],
        "unknown_evidence_groups": unknown_groups,
        "unknown_group_count": _int_or_zero(value.get("unknown_group_count"), len(unknown_groups)),
        "last_artifact_timestamp": clean_text(
            value.get("last_artifact_timestamp") or value.get("source_artifact_generated_at")
        ),
        "last_artifact_path": clean_text(value.get("last_artifact_path") or value.get("source_artifact_path")),
        "source_artifact_available": value.get("source_artifact_available") is True,
        "source_artifact_path": clean_text(value.get("source_artifact_path") or value.get("last_artifact_path")),
        "safe_cli_command": SAFE_CLI_COMMAND,
        "allowed_for_live": False,
        "first_supervised_tiny_order_blocked": True,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **risk_engine_v2_safety_flags(),
    }


def build_risk_engine_v2_safety_snapshot(
    *,
    artifact_root: str | Path,
    source_artifact_path: str = "",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": SAFETY_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "risk_engine_v2_review_safety_active",
        "artifact_root": normalize_path(artifact_root),
        "source_artifact_path": clean_text(source_artifact_path),
        "safe_cli_command": SAFE_CLI_COMMAND,
        "allowed_inputs": [
            "local Risk Engine v2 074D review artifacts when present",
            "local real local-check evidence review 074A artifacts when present",
            "known local PMBOT JSON artifacts via 074A dry-run review when explicitly run",
        ],
        "forbidden_actions": [
            "network calls",
            "Polymarket API calls",
            "secret reads",
            "wallet connection",
            "signing",
            "order submission",
            "order cancellation",
            "background workers",
            "browser automation",
        ],
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **risk_engine_v2_safety_flags(),
    }


def render_risk_engine_v2_review_cli_summary(status: Mapping[str, Any]) -> str:
    value = normalize_risk_engine_v2_review_status(status)
    return "\n".join(
        [
            "Risk Engine v2 review completed.",
            f"status={value['status']}",
            "allowed_for_live=false",
            "first_supervised_tiny_order_blocked=true",
            f"gate_count={value['gate_count']}",
            f"remaining_blocker_count={value['remaining_blocker_count']}",
            "top_blockers=" + (_joined(value["top_blockers"]) or "not_available"),
            "unknown_evidence_groups=" + (_joined(value["unknown_evidence_groups"]) or "none"),
            f"last_artifact_timestamp={value['last_artifact_timestamp'] or 'not_available'}",
            f"last_artifact_path={value['last_artifact_path'] or 'not_available'}",
            f"safe_cli_command={SAFE_CLI_COMMAND}",
        ]
    )


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "Risk Engine v2 review is local-artifact-only/no-live; unsupported live/auth/wallet/sign/order/write flag(s): "
            + ", ".join(requested)
        )


def risk_engine_v2_safety_flags() -> dict[str, Any]:
    return {
        "paper_only": True,
        "review_only": True,
        "dry_run_only": True,
        "diagnosis_only": True,
        "local_artifact_only": True,
        "local_artifact_read_only": True,
        "safe_summary_only": True,
        "non_executable": True,
        "network_used": False,
        "external_api_calls_performed": False,
        "polymarket_api_calls_performed": 0,
        "authenticated_request_performed": False,
        "authenticated_endpoint_enabled": False,
        "authenticated_endpoints_enabled": False,
        "authenticated_polymarket_enabled": False,
        "private_key_read": False,
        "wallet_private_key_read": False,
        "seed_phrase_read": False,
        "mnemonic_read": False,
        "api_secret_read": False,
        "auth_token_read": False,
        "passphrase_read": False,
        "credential_values_read": False,
        "credentials_values_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "raw_values_emitted": False,
        "actual_secret_values_exposed": False,
        "wallet_enabled": False,
        "wallet_connection_enabled": False,
        "wallet_connection_attempted": False,
        "wallet_used": False,
        "wallet_signing_enabled": False,
        "wallet_signing_performed": False,
        "signing_enabled": False,
        "signing_attempted": False,
        "cryptographic_signing_enabled": False,
        "cryptographic_signing_performed": False,
        "signed_payload_available": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "order_submission_available": False,
        "order_submission_enabled": False,
        "order_submission_attempted": False,
        "order_cancel_enabled": False,
        "order_cancellation_attempted": False,
        "real_order_submitted": False,
        "real_order_cancelled": False,
        "live_trading_enabled": False,
        "allowed_for_live": False,
        "live_execution_allowed": False,
        "live_execution_approved": False,
        "live_execution_performed": False,
        "real_execution_available": False,
        "canary_executable_now": False,
        "first_supervised_tiny_order_blocked": True,
        "operator_approved": False,
        "candidate_is_executable": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "background_worker_added": False,
        "autonomous_live_trading_added": False,
        "resolved_blocker_count": 0,
    }


def _status_from_source_payload(
    payload: Mapping[str, Any],
    *,
    artifact_root: Path,
    source_artifact_path: str,
    generated_at: str,
) -> dict[str, Any]:
    source = dict(payload or {})
    source_available = bool(source)
    latest = dict(source.get("latest_status")) if isinstance(source.get("latest_status"), Mapping) else source
    groups = _group_rows(source, latest)
    blockers = _blocker_rows(source, latest)
    unknown_groups = _unknown_groups(groups, latest)
    top_blockers = _top_blocker_reasons(source, blockers)
    if not source_available:
        unknown_groups = list(GROUP_IDS)
        top_blockers = ["Risk Engine v2 local evidence artifacts are missing; live remains blocked."]
    gate_count = _int_or_zero(latest.get("group_count"), source.get("group_count"), len(groups), len(GROUP_IDS))
    remaining = _int_or_zero(
        latest.get("remaining_blocker_count"),
        source.get("remaining_blocker_count"),
        len(blockers),
        len(unknown_groups),
    )
    last_artifact_timestamp = clean_text(latest.get("generated_at") or source.get("generated_at") or generated_at)
    status_value = {
        "contract_version": STATUS_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": clean_text(latest.get("status") or source.get("status") or "risk_engine_v2_review_missing_live_blocked"),
        "title": "🛡 Risk Engine v2",
        "market": clean_text(latest.get("market") or source.get("market") or "BTC").upper(),
        "strategy": clean_text(latest.get("strategy") or source.get("strategy") or "tiny-momentum"),
        "artifact_root": normalize_path(artifact_root),
        "source_artifact_available": source_available,
        "source_artifact_path": clean_text(source_artifact_path),
        "gate_count": gate_count,
        "remaining_blocker_count": remaining,
        "top_blockers": top_blockers[:8],
        "top_blocker_reasons": top_blockers[:8],
        "unknown_evidence_groups": unknown_groups,
        "unknown_group_count": len(unknown_groups),
        "last_artifact_timestamp": last_artifact_timestamp if source_available else "",
        "last_artifact_path": clean_text(source_artifact_path),
        "safe_cli_command": SAFE_CLI_COMMAND,
        "allowed_for_live": False,
        "first_supervised_tiny_order_blocked": True,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
        **risk_engine_v2_safety_flags(),
    }
    return normalize_risk_engine_v2_review_status(status_value)


def _risk_engine_v2_latest_paths(root: Path) -> tuple[Path, ...]:
    paths = [root / ARTIFACT_DIR_NAME / LATEST_STATUS_FILENAME]
    if root.name == ARTIFACT_DIR_NAME:
        paths.append(root / LATEST_STATUS_FILENAME)
    return _dedupe_paths(paths)


def _real_local_check_evidence_review_paths(root: Path) -> tuple[Path, ...]:
    filenames = (
        "real_local_check_evidence_review_074a_result.json",
        "latest_real_local_check_evidence_review_status_074a.json",
    )
    paths: list[Path] = []
    for dirname in ("real_local_check_evidence_review_074a", ARTIFACT_DIR_NAME + "/" + SOURCE_074A_DIR_NAME):
        for filename in filenames:
            paths.append(root / dirname / filename)
    if root.name == "real_local_check_evidence_review_074a":
        for filename in filenames:
            paths.append(root / filename)
    return _dedupe_paths(paths)


def _load_optional_json(path: Path | None, label: str) -> dict[str, Any]:
    if path is None or not path.exists() or not path.is_file():
        return {}
    try:
        return load_json_object(path, label=label)
    except Exception:
        return {}


def _first_existing_path(paths: Sequence[Path]) -> Path | None:
    return next((path for path in paths if path.exists() and path.is_file()), None)


def _dedupe_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(path)
    return tuple(unique)


def _group_rows(source: Mapping[str, Any], latest: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups = [dict(row) for row in mapping_rows(source.get("groups"))]
    if groups:
        return groups
    groups_artifact = source.get("groups_artifact")
    if isinstance(groups_artifact, Mapping):
        groups = [dict(row) for row in mapping_rows(groups_artifact.get("groups"))]
        if groups:
            return groups
    return [dict(row) for row in mapping_rows(latest.get("groups"))]


def _blocker_rows(source: Mapping[str, Any], latest: Mapping[str, Any]) -> list[dict[str, Any]]:
    blockers = [dict(row) for row in mapping_rows(source.get("remaining_blockers"))]
    if blockers:
        return blockers
    blockers_artifact = source.get("blockers_artifact")
    if isinstance(blockers_artifact, Mapping):
        blockers = [dict(row) for row in mapping_rows(blockers_artifact.get("blockers"))]
        if blockers:
            return blockers
    return [dict(row) for row in mapping_rows(latest.get("remaining_blockers") or latest.get("blockers"))]


def _unknown_groups(groups: Sequence[Mapping[str, Any]], latest: Mapping[str, Any]) -> list[str]:
    direct = _clean_list(latest.get("unknown_group_ids") or latest.get("unknown_evidence_groups"))
    if direct:
        return direct
    unknown_statuses = {
        "unknown_artifact_evidence",
        "missing_artifact_evidence",
        "unreadable_artifact_evidence",
    }
    return [
        clean_text(row.get("group_id"))
        for row in groups
        if clean_text(row.get("group_id")) and clean_text(row.get("status")) in unknown_statuses
    ]


def _top_blocker_reasons(source: Mapping[str, Any], blockers: Sequence[Mapping[str, Any]]) -> list[str]:
    direct = _clean_list(source.get("top_blockers") or source.get("top_blocker_reasons"))
    if direct:
        return direct
    return _clean_list(
        row.get("reason") or row.get("blocker_id") or row.get("message")
        for row in blockers
    )


def _clean_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values] if clean_text(values) else []
    try:
        return [clean_text(item) for item in values if clean_text(item)]
    except TypeError:
        return []


def _int_or_zero(*values: Any) -> int:
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _joined(values: Sequence[Any]) -> str:
    return "; ".join(clean_text(item) for item in values if clean_text(item))


__all__ = [
    "ARTIFACT_DIR_NAME",
    "LATEST_STATUS_FILENAME",
    "SAFE_CLI_COMMAND",
    "TASK_ID",
    "build_risk_engine_v2_review_status",
    "fail_closed_for_forbidden_flags",
    "normalize_risk_engine_v2_review_status",
    "render_risk_engine_v2_review_cli_summary",
    "risk_engine_v2_review_artifact_paths",
    "run_risk_engine_v2_review",
]
