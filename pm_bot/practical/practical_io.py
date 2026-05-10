from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

GENERATED_AT = "2026-05-10T00:00:00Z"

SAFE_SUMMARY = {
    "authenticated_endpoints_used": False,
    "live_network_used": False,
    "market_recommendation_generated": False,
    "openrouter_calls_performed": 0,
    "orders_or_trading_actions": False,
    "polymarket_api_calls_performed": 0,
    "probability_ev_edge_or_side_selection_generated": False,
    "runtime_or_dispatcher_changes": False,
    "wallet_or_private_key_access": False,
}


class PracticalIOError(ValueError):
    pass


def load_json_object(path: str | Path, *, label: str = "input") -> dict[str, Any]:
    payload = load_json_any(path, label=label)
    if not isinstance(payload, dict):
        raise PracticalIOError(f"{label} JSON must be an object")
    return payload


def load_json_any(path: str | Path, *, label: str = "input") -> Any:
    path_obj = resolve_existing_path(path)
    try:
        return json.loads(path_obj.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PracticalIOError(f"{label} JSON is invalid: {exc}") from exc


def write_json(path: str | Path, value: Any) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str | Path, value: str) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(value, encoding="utf-8")


def normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def reject_network_path(path: str | Path) -> None:
    value = normalize_path(path).lower()
    if "://" in value or value.startswith(("http:", "https:")):
        raise PracticalIOError(f"path must be local: {normalize_path(path)}")


def resolve_existing_path(path: str | Path, *, base_dir: str | Path | None = None) -> Path:
    reject_network_path(path)
    candidate = Path(path)
    if candidate.exists():
        return candidate
    if base_dir is not None:
        nested = Path(base_dir) / candidate
        if nested.exists():
            return nested
    raise PracticalIOError(f"path does not exist: {normalize_path(path)}")


def optional_existing_path(path: Any, *, base_dir: str | Path | None = None) -> Path | None:
    if isinstance(path, Path):
        candidate: str | Path = path
    elif isinstance(path, str) and path.strip():
        candidate = path
    else:
        return None
    try:
        return resolve_existing_path(candidate, base_dir=base_dir)
    except PracticalIOError:
        return None


def path_exists(path: Any, *, base_dir: str | Path | None = None) -> bool:
    return optional_existing_path(path, base_dir=base_dir) is not None


def slug_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_.-]+", "_", value.lower()).strip("_")
    return normalized or "pmbot"


def clean_text(value: Any) -> str:
    return str(value).strip()


def clean_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [clean_text(item) for item in value if isinstance(item, str) and clean_text(item)]


def bullet_lines(items: Iterable[str]) -> list[str]:
    values = list(items)
    if not values:
        return ["- none"]
    return [f"- {item}" for item in values]


def safe_summary() -> dict[str, Any]:
    summary = dict(SAFE_SUMMARY)
    summary["no_autonomous_training_performed"] = True
    summary["no_real_trade_decision"] = True
    summary["paper_only"] = True
    return summary


def sorted_counter_dict(counter: Mapping[str, int]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}
