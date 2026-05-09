from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from .schema import (
    HARD_BLOCK_RISK_FLAGS,
    MVP_ALLOWED_TASK_TYPES,
    SPECIAL_APPROVAL_RISK_FLAGS,
)
from .validator import ValidationResult, validate_packet

FORBIDDEN_INTENT_KEYWORDS = (
    "private key",
    "seed phrase",
    "wallet",
    "orders",
    "execute order",
    "place order",
    "buy",
    "sell",
    "trade",
    "trading",
    "stake amount",
    "position size",
    "payment",
    "production credential",
    "api key",
    "codex app-server",
    "dispatcher",
    "run_codex",
    "background worker",
    "scheduler",
    "task scheduler",
    "telegram",
    "openclaw",
    "openrouter",
    "polymarket api",
    "delete all",
    "remove repo",
    "rm -rf",
)

TEXT_INTENT_FIELDS = (
    "summary",
    "instructions",
    "operator_notes",
    "expected_outputs",
)

SEGMENT_SPLIT_RE = re.compile(r"[\r\n.;]+")
PROTECTIVE_NEGATION_RE = re.compile(
    r"(?:^|[\s([{])"
    r"(?:do\s+not|don't|dont|never|no|must\s+not|should\s+not|shall\s+not|not\s+to|not)\b"
)
CONTRAST_RE = re.compile(r"\b(?:but|except|however|then|also)\b")

SPECIAL_APPROVAL_TASK_TYPES = {
    "needs_network_approval",
    "needs_runtime_approval",
    "needs_external_tracker",
}

BLOCKED_TASK_TYPES = {
    "blocked_sensitive",
    "blocked_trading",
    "blocked_destructive",
}


@dataclass(frozen=True)
class SafetyClassification:
    allowed: bool
    status: str
    reasons: tuple[str, ...]
    hard_block_flags: tuple[str, ...]
    special_approval_flags: tuple[str, ...]
    forbidden_keywords: tuple[str, ...]
    requires_special_approval: bool = False
    blocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "status": self.status,
            "reasons": list(self.reasons),
            "hard_block_flags": list(self.hard_block_flags),
            "special_approval_flags": list(self.special_approval_flags),
            "forbidden_keywords": list(self.forbidden_keywords),
            "requires_special_approval": self.requires_special_approval,
            "blocked": self.blocked,
        }


def classify_packet(
    packet: Mapping[str, Any],
    validation: ValidationResult | None = None,
) -> SafetyClassification:
    validation = validation or validate_packet(packet)
    if not validation.valid:
        return SafetyClassification(
            allowed=False,
            status="invalid",
            reasons=("packet validation failed", *validation.errors),
            hard_block_flags=(),
            special_approval_flags=(),
            forbidden_keywords=(),
        )

    risk_flags = packet.get("risk_flags", {})
    hard_flags = tuple(flag for flag in HARD_BLOCK_RISK_FLAGS if risk_flags.get(flag) is True)
    special_flags = tuple(flag for flag in SPECIAL_APPROVAL_RISK_FLAGS if risk_flags.get(flag) is True)
    forbidden_keywords = _find_forbidden_intent(packet)

    if hard_flags or forbidden_keywords:
        reasons = []
        if hard_flags:
            reasons.append(f"hard-block risk flags set: {', '.join(hard_flags)}")
        if forbidden_keywords:
            reasons.append(f"forbidden intent detected: {', '.join(forbidden_keywords)}")
        return SafetyClassification(
            allowed=False,
            status="blocked",
            reasons=tuple(reasons),
            hard_block_flags=hard_flags,
            special_approval_flags=special_flags,
            forbidden_keywords=forbidden_keywords,
            blocked=True,
        )

    task_type = packet.get("task_type")
    if special_flags or task_type in SPECIAL_APPROVAL_TASK_TYPES:
        reasons = []
        if special_flags:
            reasons.append(f"special approval risk flags set: {', '.join(special_flags)}")
        if task_type in SPECIAL_APPROVAL_TASK_TYPES:
            reasons.append(f"task_type requires special approval: {task_type}")
        return SafetyClassification(
            allowed=False,
            status="requires_special_approval",
            reasons=tuple(reasons),
            hard_block_flags=(),
            special_approval_flags=special_flags,
            forbidden_keywords=(),
            requires_special_approval=True,
        )

    if task_type in BLOCKED_TASK_TYPES:
        return SafetyClassification(
            allowed=False,
            status="blocked",
            reasons=(f"task_type is blocked: {task_type}",),
            hard_block_flags=(),
            special_approval_flags=(),
            forbidden_keywords=(),
            blocked=True,
        )

    if task_type not in MVP_ALLOWED_TASK_TYPES:
        return SafetyClassification(
            allowed=False,
            status="not_allowed",
            reasons=(f"task_type is not allowed by MVP runner: {task_type}",),
            hard_block_flags=(),
            special_approval_flags=(),
            forbidden_keywords=(),
        )

    if packet.get("status") != "approved":
        return SafetyClassification(
            allowed=False,
            status="not_approved",
            reasons=("packet status must be approved for MVP dry-run planning",),
            hard_block_flags=(),
            special_approval_flags=(),
            forbidden_keywords=(),
        )

    return SafetyClassification(
        allowed=True,
        status="allowed",
        reasons=("approved local-only task is allowed by MVP dry-run planner",),
        hard_block_flags=(),
        special_approval_flags=(),
        forbidden_keywords=(),
    )


def _find_forbidden_intent(packet: Mapping[str, Any]) -> tuple[str, ...]:
    matches: list[str] = []
    for field in TEXT_INTENT_FIELDS:
        for text_item in _iter_text_items(packet.get(field, "")):
            for segment in _iter_segments(text_item):
                matches.extend(_find_segment_forbidden_intent(segment))
    return tuple(dict.fromkeys(matches))


def _find_segment_forbidden_intent(segment: str) -> list[str]:
    text = segment.lower()
    matches: list[str] = []
    for keyword in FORBIDDEN_INTENT_KEYWORDS:
        pattern = _keyword_pattern(keyword)
        for match in re.finditer(pattern, text):
            if _is_protective_match(text, match.start()):
                continue
            matches.append(keyword)
            break
    return matches


def _is_protective_match(segment: str, keyword_start: int) -> bool:
    before = segment[:keyword_start]
    negation_match = None
    for candidate in PROTECTIVE_NEGATION_RE.finditer(before):
        negation_match = candidate
    if negation_match is None:
        return False

    between = before[negation_match.end() :]
    if CONTRAST_RE.search(between):
        return False
    return True


def _iter_segments(text: str) -> tuple[str, ...]:
    return tuple(segment.strip() for segment in SEGMENT_SPLIT_RE.split(text) if segment.strip())


def _iter_text_items(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        items: list[str] = []
        for nested in value.values():
            items.extend(_iter_text_items(nested))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for nested in value:
            items.extend(_iter_text_items(nested))
        return tuple(items)
    return (_stringify(value),)


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return str(value)


def _keyword_pattern(keyword: str) -> str:
    escaped = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
    if re.fullmatch(r"[a-z0-9_ -]+", keyword.lower()):
        return rf"(?<![a-z0-9_]){escaped}(?![a-z0-9_])"
    return escaped
