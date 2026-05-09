from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Mapping

from .schema import QUEUE_DIRECTORIES, SCHEMA_VERSION, TASK_ID_RE

QUEUE_STATE_DIRECTORIES = (
    "inbox",
    "approved",
    "planned",
    "running",
    "review",
    "done",
    "blocked",
)


def ensure_queue_directories(queue_root: str | Path) -> Path:
    root = Path(queue_root)
    root.mkdir(parents=True, exist_ok=True)
    for directory in QUEUE_DIRECTORIES:
        safe_queue_path(root, directory).mkdir(parents=True, exist_ok=True)
    return root


def validate_task_id(task_id: str) -> str:
    if not isinstance(task_id, str) or not TASK_ID_RE.match(task_id):
        raise ValueError("task_id must match safe uppercase identifier style")
    return task_id


def safe_queue_path(queue_root: str | Path, *parts: str | Path) -> Path:
    root = Path(queue_root).resolve(strict=False)
    target = root.joinpath(*parts).resolve(strict=False)
    if not _is_relative_to(target, root):
        raise ValueError(f"path escapes queue root: {target}")
    return target


def safe_existing_path_under_queue(queue_root: str | Path, path: str | Path) -> Path:
    root = Path(queue_root).resolve(strict=False)
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    target = candidate.resolve(strict=False)
    if not _is_relative_to(target, root):
        raise ValueError(f"path escapes queue root: {target}")
    return target


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_atomic(path: str | Path, payload: Mapping[str, Any], *, overwrite: bool = True) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        raise FileExistsError(f"file already exists: {target}")

    temp_name = f".{target.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    temp_path = target.with_name(temp_name)
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if target.exists() and not overwrite:
        raise FileExistsError(f"file already exists: {target}")
    temp_path.replace(target)
    return target


def write_text_atomic(path: str | Path, content: str, *, overwrite: bool = True) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        raise FileExistsError(f"file already exists: {target}")

    temp_name = f".{target.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    temp_path = target.with_name(temp_name)
    temp_path.write_text(content, encoding="utf-8")
    if target.exists() and not overwrite:
        raise FileExistsError(f"file already exists: {target}")
    temp_path.replace(target)
    return target


def task_packet_path(queue_root: str | Path, state: str, task_id: str) -> Path:
    if state not in QUEUE_STATE_DIRECTORIES:
        raise ValueError(f"unsupported queue state: {state}")
    return safe_queue_path(queue_root, state, f"{validate_task_id(task_id)}.task.json")


def find_task_packet(
    queue_root: str | Path,
    task_id: str,
    *,
    states: tuple[str, ...] = QUEUE_STATE_DIRECTORIES,
) -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    safe_task_id = validate_task_id(task_id)
    unreadable: list[str] = []

    for state in states:
        if state not in QUEUE_STATE_DIRECTORIES:
            raise ValueError(f"unsupported queue state: {state}")
        state_dir = safe_queue_path(root, state)
        for packet_path in sorted(state_dir.glob("*.json")):
            try:
                payload = read_json(packet_path)
            except json.JSONDecodeError as exc:
                unreadable.append(f"{packet_path}: invalid JSON: {exc}")
                continue
            if not isinstance(payload, Mapping):
                continue
            if payload.get("schema_version") != SCHEMA_VERSION:
                continue
            if payload.get("task_id") != safe_task_id:
                continue
            return {
                "found": True,
                "task_id": safe_task_id,
                "state": state,
                "path": packet_path,
                "packet": dict(payload),
                "errors": unreadable,
            }

    return {
        "found": False,
        "task_id": safe_task_id,
        "state": None,
        "path": None,
        "packet": None,
        "errors": unreadable,
    }


def count_task_packets(queue_root: str | Path, state: str) -> int:
    root = ensure_queue_directories(queue_root)
    if state not in QUEUE_STATE_DIRECTORIES:
        raise ValueError(f"unsupported queue state: {state}")

    count = 0
    for packet_path in safe_queue_path(root, state).glob("*.json"):
        try:
            payload = read_json(packet_path)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping) and payload.get("schema_version") == SCHEMA_VERSION:
            count += 1
    return count


def move_task_packet(
    queue_root: str | Path,
    source_path: str | Path,
    task_id: str,
    destination_state: str,
    packet: Mapping[str, Any],
    *,
    overwrite: bool = False,
) -> Path:
    root = ensure_queue_directories(queue_root)
    safe_task_id = validate_task_id(task_id)
    source = Path(source_path).resolve(strict=False)
    root_resolved = root.resolve(strict=False)
    if not _is_relative_to(source, root_resolved):
        raise ValueError(f"source path escapes queue root: {source}")
    destination = task_packet_path(root, destination_state, safe_task_id)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"destination already exists: {destination}")

    write_json_atomic(source, packet)
    source.rename(destination)
    return destination


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
