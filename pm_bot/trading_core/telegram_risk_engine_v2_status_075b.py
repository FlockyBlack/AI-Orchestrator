from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.risk_engine_v2 import risk_engine_v2_review_artifact_paths
from pm_bot.trading_core.risk_engine_v2_models import (
    STATUS_BLOCKED,
    TASK_ID as RISK_ENGINE_V2_TASK_ID,
    risk_engine_v2_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, load_json_object, normalize_path, write_json

TASK_ID = "ORCH-PMBOT-TELEGRAM-075B-RISK-ENGINE-V2-OVERVIEW-NO-LIVE"

STATUS_CONTRACT = "pmbot_telegram_risk_engine_v2_status_075b.v1"
RESULT_CONTRACT = "pmbot_telegram_risk_engine_v2_status_075b_result.v1"
MINI_APP_SNAPSHOT_CONTRACT = "pmbot_telegram_risk_engine_v2_mini_app_snapshot_075b.v1"
SAFETY_SNAPSHOT_CONTRACT = "pmbot_telegram_risk_engine_v2_safety_snapshot_075b.v1"

ARTIFACT_DIR_NAME = "telegram_risk_engine_v2_status_075b"
RESULT_FILENAME = "telegram_risk_engine_v2_status_075b_result.json"
LATEST_STATUS_FILENAME = "latest_telegram_risk_engine_v2_status_075b.json"
MINI_APP_SNAPSHOT_FILENAME = "telegram_risk_engine_v2_mini_app_snapshot_075b.json"
SAFETY_SNAPSHOT_FILENAME = "telegram_risk_engine_v2_safety_snapshot_075b.json"

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / ARTIFACT_DIR_NAME
RISK_ENGINE_V2_REVIEW_074D_ARTIFACT_DIR_NAME = "risk_engine_v2_074d"
RISK_ENGINE_V2_REVIEW_074D_LATEST_STATUS_FILENAME = "latest_risk_engine_v2_074d_status.json"
LEGACY_RISK_ENGINE_V2_REVIEW_074D_ARTIFACT_DIR_NAME = "risk_engine_v2_review_074d"
LEGACY_RISK_ENGINE_V2_REVIEW_074D_LATEST_STATUS_FILENAME = "latest_risk_engine_v2_review_status_074d.json"
SAFE_CLI_COMMAND = (
    "python -m pm_bot.operator_runner.risk_engine_v2_review "
    "--market BTC --strategy tiny-momentum --dry-run"
)


def telegram_risk_engine_v2_status_artifact_paths(output_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(output_dir) if output_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / RESULT_FILENAME,
        "latest_status": root / LATEST_STATUS_FILENAME,
        "mini_app_snapshot": root / MINI_APP_SNAPSHOT_FILENAME,
        "safety_snapshot": root / SAFETY_SNAPSHOT_FILENAME,
    }


def build_telegram_risk_engine_v2_status(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    review = normalize_risk_engine_v2_review_status(
        build_risk_engine_v2_review_status(artifact_root=root, generated_at=generated_at)
    )
    status = {
        "contract_version": STATUS_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": clean_text(review.get("status") or "risk_engine_v2_review_live_blocked"),
        "title": "🛡 Risk Engine v2",
        "mode": "telegram_risk_engine_v2_status_review_only",
        "execution_mode": "local_artifact_read_only_display",
        "telegram_screen_title_ru": "🛡 Risk Engine v2",
        "telegram_screen_title_en": "Risk Engine v2",
        "artifact_root": normalize_path(root),
        "source_074d_artifact_dir_name": RISK_ENGINE_V2_REVIEW_074D_ARTIFACT_DIR_NAME,
        "source_074d_latest_status_filename": RISK_ENGINE_V2_REVIEW_074D_LATEST_STATUS_FILENAME,
        "risk_engine_v2_review_summary": review,
        "source_artifact_available": review["source_artifact_available"],
        "source_artifact_path": review["source_artifact_path"],
        "allowed_for_live": False,
        "first_supervised_tiny_order_blocked": True,
        "gate_count": review["gate_count"],
        "remaining_blocker_count": review["remaining_blocker_count"],
        "top_blockers": list(review["top_blockers"]),
        "top_blocker_reasons": list(review["top_blocker_reasons"]),
        "unknown_evidence_groups": list(review["unknown_evidence_groups"]),
        "unknown_group_count": review["unknown_group_count"],
        "last_artifact_timestamp": review["last_artifact_timestamp"],
        "last_artifact_path": review["last_artifact_path"],
        "safe_cli_command": SAFE_CLI_COMMAND,
        "screen_available": True,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "display_only": True,
        "execution_enabling": False,
        **telegram_risk_engine_v2_safety_flags(),
    }
    status["status_text_ru"] = render_telegram_risk_engine_v2_status_text(status, language="ru")
    status["status_text_en"] = render_telegram_risk_engine_v2_status_text(status, language="en")
    return status


def build_risk_engine_v2_review_status(
    *,
    artifact_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    latest_path = _first_existing_path(_risk_engine_v2_latest_status_paths(root))
    payload = _load_optional_json(latest_path, "Risk Engine v2 074D latest status")
    if payload:
        payload["_source_artifact_available"] = True
        payload["_source_artifact_path"] = normalize_path(latest_path) if latest_path else ""
        return normalize_risk_engine_v2_review_status(payload)
    fallback_paths = risk_engine_v2_review_artifact_paths(root / RISK_ENGINE_V2_REVIEW_074D_ARTIFACT_DIR_NAME)
    return normalize_risk_engine_v2_review_status(
        {
            "contract_version": "pmbot_latest_risk_engine_v2_review_074d.v1",
            "task_id": RISK_ENGINE_V2_TASK_ID,
            "generated_at": generated_at,
            "status": STATUS_BLOCKED,
            "market": "BTC",
            "strategy_name": "tiny-momentum",
            "gate_count": 0,
            "remaining_blocker_count": 1,
            "unknown_blocker_count": 1,
            "unknown_blocker_ids": ["risk_engine_v2_latest_status_missing"],
            "top_blockers": ["Risk Engine v2 local status artifact is missing; live remains blocked."],
            "latest_status_path": normalize_path(fallback_paths["latest_status"]),
            "_source_artifact_available": False,
            "_source_artifact_path": "",
        }
    )


def normalize_risk_engine_v2_review_status(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    source_path = clean_text(
        value.get("_source_artifact_path")
        or value.get("source_artifact_path")
        or value.get("last_artifact_path")
        or value.get("latest_status_path")
        or value.get("artifact_path")
    )
    top_blockers = _clean_list(
        value.get("top_blockers")
        or value.get("top_blocker_reasons")
        or value.get("blocker_ids")
    )[:8]
    unknown_groups = _clean_list(
        value.get("unknown_evidence_groups")
        or value.get("unknown_group_ids")
        or value.get("unknown_blocker_ids")
    )
    if not source_path and not top_blockers:
        top_blockers = ["Risk Engine v2 local status artifact is missing; live remains blocked."]
    if not source_path and not unknown_groups:
        unknown_groups = ["risk_engine_v2_latest_status_missing"]
    normalized = {
        "contract_version": clean_text(value.get("contract_version") or "pmbot_latest_risk_engine_v2_review_074d.v1"),
        "task_id": clean_text(value.get("task_id") or RISK_ENGINE_V2_TASK_ID),
        "generated_at": clean_text(value.get("generated_at")) or GENERATED_AT,
        "status": clean_text(value.get("status") or STATUS_BLOCKED),
        "title": "🛡 Risk Engine v2",
        "market": clean_text(value.get("market") or value.get("market_symbol") or "BTC").upper(),
        "strategy": clean_text(value.get("strategy") or value.get("strategy_name") or "tiny-momentum"),
        "gate_count": _int_or_zero(value.get("gate_count")),
        "remaining_blocker_count": _int_or_zero(
            value.get("remaining_blocker_count"),
            len(top_blockers),
            len(unknown_groups),
        ),
        "top_blockers": top_blockers,
        "top_blocker_reasons": top_blockers,
        "unknown_evidence_groups": unknown_groups,
        "unknown_group_count": _int_or_zero(
            value.get("unknown_group_count"),
            value.get("unknown_blocker_count"),
            len(unknown_groups),
        ),
        "last_artifact_timestamp": clean_text(value.get("last_artifact_timestamp") or value.get("generated_at")),
        "last_artifact_path": clean_text(value.get("last_artifact_path") or source_path),
        "source_artifact_available": value.get("_source_artifact_available") is True
        or value.get("source_artifact_available") is True,
        "source_artifact_path": source_path,
        "safe_cli_command": SAFE_CLI_COMMAND,
        "allowed_for_live": False,
        "first_supervised_tiny_order_blocked": True,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "execution_enabling": False,
    }
    normalized.update(risk_engine_v2_safety_flags())
    normalized["title"] = "🛡 Risk Engine v2"
    normalized["safe_cli_command"] = SAFE_CLI_COMMAND
    normalized["source_artifact_available"] = value.get("_source_artifact_available") is True or value.get(
        "source_artifact_available"
    ) is True
    normalized["source_artifact_path"] = source_path
    normalized["last_artifact_path"] = clean_text(value.get("last_artifact_path") or source_path)
    return normalized


def write_telegram_risk_engine_v2_status_075b_artifacts(
    *,
    artifact_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    status = build_telegram_risk_engine_v2_status(artifact_root=artifact_root, generated_at=generated_at)
    paths = telegram_risk_engine_v2_status_artifact_paths(output_dir)
    mini_app = build_telegram_risk_engine_v2_mini_app_snapshot(status, generated_at=generated_at)
    safety = build_telegram_risk_engine_v2_safety_snapshot(generated_at=generated_at)
    result = {
        "contract_version": RESULT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "completed_review_only",
        "latest_status_path": normalize_path(paths["latest_status"]),
        "mini_app_snapshot_path": normalize_path(paths["mini_app_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "telegram_risk_engine_v2_status_075b": status,
        "mini_app_snapshot": mini_app,
        "safety_snapshot": safety,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "display_only": True,
        "execution_enabling": False,
        **telegram_risk_engine_v2_safety_flags(),
    }
    write_json(paths["latest_status"], status)
    write_json(paths["mini_app_snapshot"], mini_app)
    write_json(paths["safety_snapshot"], safety)
    write_json(paths["result"], result)
    return {
        "result_path": normalize_path(paths["result"]),
        "latest_status_path": normalize_path(paths["latest_status"]),
        "mini_app_snapshot_path": normalize_path(paths["mini_app_snapshot"]),
        "safety_snapshot_path": normalize_path(paths["safety_snapshot"]),
        "result": result,
        "latest_status": status,
        "mini_app_snapshot": mini_app,
        "safety_snapshot": safety,
    }


def build_telegram_risk_engine_v2_mini_app_snapshot(
    status: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = normalize_telegram_risk_engine_v2_status_summary(status)
    return {
        "contract_version": MINI_APP_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "card_title_ru": "🛡 Risk Engine v2",
        "allowed_for_live": False,
        "first_supervised_tiny_order_blocked": True,
        "gate_count": value["gate_count"],
        "remaining_blocker_count": value["remaining_blocker_count"],
        "top_blockers": list(value["top_blockers"]),
        "unknown_evidence_groups": list(value["unknown_evidence_groups"]),
        "last_artifact_timestamp": value["last_artifact_timestamp"],
        "last_artifact_path": value["last_artifact_path"],
        "safe_cli_command": SAFE_CLI_COMMAND,
        "static_review_only": True,
        "local_static_artifacts_only": True,
        "no_network_fetch": True,
        "no_secret_forms": True,
        "no_secret_inputs": True,
        "no_secret_persistence": True,
        "no_live_controls": True,
        **telegram_risk_engine_v2_safety_flags(),
    }


def build_telegram_risk_engine_v2_safety_snapshot(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": SAFETY_SNAPSHOT_CONTRACT,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "status": "safe_risk_engine_v2_status_review_only",
        "allowed_inputs": [
            "local Risk Engine v2 074D review artifacts when present",
            "local real local-check evidence review 074A artifacts when present",
        ],
        "forbidden_actions": [
            "live controls",
            "order submit or cancel",
            "wallet connection",
            "signing",
            "secret forms or secret output",
            "Polymarket API calls",
            "network fetches from Mini App",
            "background workers",
        ],
        "telegram_primary_menu_unchanged": True,
        "same_message_navigation_preserved": True,
        "mini_app_static_no_fetch": True,
        "display_does_not_run_review": True,
        "review_only": True,
        "dry_run_only": True,
        "execution_enabling": False,
        **telegram_risk_engine_v2_safety_flags(),
    }


def render_telegram_risk_engine_v2_status_text(
    status: Mapping[str, Any],
    *,
    language: str = "ru",
) -> str:
    value = normalize_telegram_risk_engine_v2_status_summary(status)
    top_blockers = _display_list(value["top_blockers"], fallback="not_available")
    unknown_groups = _display_list(value["unknown_evidence_groups"], fallback="none")
    last_timestamp = value["last_artifact_timestamp"] or "not_available"
    last_path = value["last_artifact_path"] or "not_available"
    lines = [
        "🛡 Risk Engine v2",
        "allowed_for_live=false",
        "first_supervised_tiny_order_blocked=true",
        f"gate_count={value['gate_count']}",
        f"remaining_blocker_count={value['remaining_blocker_count']}",
        f"top_blockers={top_blockers}",
        f"unknown_evidence_groups={unknown_groups}",
        f"last_artifact_timestamp={last_timestamp}",
        f"last_artifact_path={last_path}",
        f"safe_cli_command={SAFE_CLI_COMMAND}",
    ]
    if clean_text(language).lower() == "en":
        return "\n".join(lines)
    return "\n".join(lines)


def normalize_telegram_risk_engine_v2_status_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(status or {})
    review = normalize_risk_engine_v2_review_status(
        value.get("risk_engine_v2_review_summary") if isinstance(value.get("risk_engine_v2_review_summary"), Mapping) else value
    )
    return {
        "contract_version": clean_text(value.get("contract_version") or STATUS_CONTRACT),
        "screen_available": True,
        "status": clean_text(value.get("status") or review["status"]),
        "title": "🛡 Risk Engine v2",
        "mode": clean_text(value.get("mode") or "telegram_risk_engine_v2_status_review_only"),
        "execution_mode": clean_text(value.get("execution_mode") or "local_artifact_read_only_display"),
        "telegram_screen_title_ru": "🛡 Risk Engine v2",
        "telegram_screen_title_en": "Risk Engine v2",
        "source_artifact_available": value.get("source_artifact_available") is True
        or review["source_artifact_available"],
        "source_artifact_path": clean_text(value.get("source_artifact_path") or review["source_artifact_path"]),
        "allowed_for_live": False,
        "first_supervised_tiny_order_blocked": True,
        "gate_count": _int_or_zero(value.get("gate_count"), review["gate_count"]),
        "remaining_blocker_count": _int_or_zero(
            value.get("remaining_blocker_count"),
            review["remaining_blocker_count"],
        ),
        "top_blockers": _clean_list(value.get("top_blockers") or review["top_blockers"])[:8],
        "top_blocker_reasons": _clean_list(value.get("top_blocker_reasons") or review["top_blocker_reasons"])[:8],
        "unknown_evidence_groups": _clean_list(
            value.get("unknown_evidence_groups") or review["unknown_evidence_groups"]
        ),
        "unknown_group_count": _int_or_zero(value.get("unknown_group_count"), review["unknown_group_count"]),
        "last_artifact_timestamp": clean_text(
            value.get("last_artifact_timestamp") or review["last_artifact_timestamp"]
        ),
        "last_artifact_path": clean_text(value.get("last_artifact_path") or review["last_artifact_path"]),
        "safe_cli_command": SAFE_CLI_COMMAND,
        "review_only": True,
        "dry_run_only": True,
        "local_artifact_read_only": True,
        "display_only": True,
        "execution_enabling": False,
        **telegram_risk_engine_v2_safety_flags(),
    }


def telegram_risk_engine_v2_safety_flags() -> dict[str, Any]:
    value = dict(risk_engine_v2_safety_flags())
    value.pop("mode", None)
    value.pop("execution_mode", None)
    for key in (
        "no_live",
        "no_submit",
        "no_cancel",
        "no_signing",
        "no_wallet",
        "no_private_material_reads",
    ):
        value.pop(key, None)
    value.update(
        {
            "display_only": True,
            "telegram_live_order_controls_added": False,
            "telegram_signing_controls_added": False,
            "telegram_wallet_controls_added": False,
            "mini_app_network_fetch": False,
        }
    )
    return value


def _risk_engine_v2_latest_status_paths(root: Path) -> tuple[Path, ...]:
    paths = [
        root / RISK_ENGINE_V2_REVIEW_074D_ARTIFACT_DIR_NAME / RISK_ENGINE_V2_REVIEW_074D_LATEST_STATUS_FILENAME,
        root
        / LEGACY_RISK_ENGINE_V2_REVIEW_074D_ARTIFACT_DIR_NAME
        / LEGACY_RISK_ENGINE_V2_REVIEW_074D_LATEST_STATUS_FILENAME,
    ]
    if root.name == RISK_ENGINE_V2_REVIEW_074D_ARTIFACT_DIR_NAME:
        paths.append(root / RISK_ENGINE_V2_REVIEW_074D_LATEST_STATUS_FILENAME)
    if root.name == LEGACY_RISK_ENGINE_V2_REVIEW_074D_ARTIFACT_DIR_NAME:
        paths.append(root / LEGACY_RISK_ENGINE_V2_REVIEW_074D_LATEST_STATUS_FILENAME)
    return _dedupe_paths(paths)


def _load_optional_json(path: Path | None, label: str) -> dict[str, Any]:
    if path is None or not path.exists() or not path.is_file():
        return {}
    try:
        return load_json_object(path, label=label)
    except (OSError, ValueError):
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


def _display_list(values: Sequence[Any], *, fallback: str) -> str:
    joined = "; ".join(clean_text(item) for item in values if clean_text(item))
    return joined or fallback


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


__all__ = [
    "ARTIFACT_DIR_NAME",
    "LATEST_STATUS_FILENAME",
    "SAFE_CLI_COMMAND",
    "TASK_ID",
    "build_telegram_risk_engine_v2_status",
    "normalize_telegram_risk_engine_v2_status_summary",
    "render_telegram_risk_engine_v2_status_text",
    "telegram_risk_engine_v2_status_artifact_paths",
    "write_telegram_risk_engine_v2_status_075b_artifacts",
]
