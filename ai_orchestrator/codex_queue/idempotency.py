from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{7,191}$")
_PART_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class IdempotencyKey:
    namespace: str
    parts: tuple[str, ...]

    @property
    def value(self) -> str:
        return ":".join((self.namespace, *self.parts))

    def __str__(self) -> str:
        return self.value

    def is_valid(self) -> bool:
        return validate_idempotency_key(self.value)


def build_task_attempt_idempotency_key(run_id: str, task_id: str, attempt_id: str | int) -> IdempotencyKey:
    return IdempotencyKey(
        namespace="task_attempt",
        parts=(
            _normalize_key_part(run_id),
            _normalize_key_part(task_id),
            _normalize_key_part(str(attempt_id)),
        ),
    )


def fingerprint_payload(paths_or_payload: Any) -> str:
    payload = _fingerprint_material(paths_or_payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_codex_packet_fingerprint(packet_path: str | Path, prompt_path: str | Path) -> str:
    return fingerprint_payload([Path(packet_path), Path(prompt_path)])


def validate_idempotency_key(value: str | IdempotencyKey) -> bool:
    text = str(value).strip()
    if not text or len(text) > 200:
        return False
    if any(ch.isspace() for ch in text):
        return False
    return bool(_KEY_PATTERN.fullmatch(text))


def _fingerprint_material(value: Any) -> Any:
    if _is_existing_path(value):
        return _path_record(Path(value))
    if isinstance(value, Mapping):
        return {str(key): _fingerprint_material(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (str, bytes)):
        return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
    if isinstance(value, Iterable):
        values = list(value)
        if values and all(_is_existing_path(item) for item in values):
            return [_path_record(Path(item)) for item in sorted(values, key=lambda item: str(item))]
        return [_fingerprint_material(item) for item in values]
    return value


def _path_record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "path": path.as_posix(),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _is_existing_path(value: Any) -> bool:
    if not isinstance(value, (str, Path)):
        return False
    try:
        return Path(value).is_file()
    except OSError:
        return False


def _normalize_key_part(value: str) -> str:
    cleaned = _PART_PATTERN.sub("-", value.strip()).strip("-._")
    if not cleaned:
        cleaned = "empty"
    if len(cleaned) <= 48:
        return cleaned
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{cleaned[:31]}-{digest}"
