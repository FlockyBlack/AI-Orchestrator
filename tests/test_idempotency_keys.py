from __future__ import annotations

from pathlib import Path

from ai_orchestrator.codex_queue.idempotency import (
    build_codex_packet_fingerprint,
    build_task_attempt_idempotency_key,
    fingerprint_payload,
    validate_idempotency_key,
)


def test_task_attempt_idempotency_key_is_deterministic() -> None:
    first = build_task_attempt_idempotency_key("RUN028", "ORCH-CODEX-AUTOMATION-028", 1)
    second = build_task_attempt_idempotency_key("RUN028", "ORCH-CODEX-AUTOMATION-028", 1)
    assert str(first) == str(second)
    assert first.is_valid()
    assert validate_idempotency_key(first)


def test_payload_fingerprint_is_deterministic_for_payloads_and_files(tmp_path: Path) -> None:
    payload = {"b": 2, "a": [1, 2, 3]}
    assert fingerprint_payload(payload) == fingerprint_payload({"a": [1, 2, 3], "b": 2})

    packet = tmp_path / "packet.json"
    prompt = tmp_path / "prompt.md"
    packet.write_text('{"task_id":"T1"}\n', encoding="utf-8")
    prompt.write_text("# prompt\n", encoding="utf-8")

    first = build_codex_packet_fingerprint(packet, prompt)
    second = build_codex_packet_fingerprint(packet, prompt)
    assert first == second
    assert len(first) == 64


def test_invalid_idempotency_key_is_rejected() -> None:
    assert not validate_idempotency_key("bad key with spaces")
    assert not validate_idempotency_key("")
