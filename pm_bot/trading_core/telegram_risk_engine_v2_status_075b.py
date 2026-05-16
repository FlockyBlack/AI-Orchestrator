from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.risk_engine_v2_review import (
    ARTIFACT_DIR_NAME as RISK_ENGINE_V2_REVIEW_074D_ARTIFACT_DIR_NAME,
    LATEST_STATUS_FILENAME as RISK_ENGINE_V2_REVIEW_074D_LATEST_STATUS_FILENAME,
    SAFE_CLI_COMMAND,
    build_risk_engine_v2_review_status,
    normalize_risk_engine_v2_review_status,
    risk_engine_v2_safety_flags,
)
from pm_bot.trading_core.schemas import GENERATED_AT, clean_text, normalize_path, write_json

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
