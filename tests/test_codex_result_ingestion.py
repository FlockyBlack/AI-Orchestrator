from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.codex_executor_contract import expected_result_schema_for_packet
from ai_orchestrator.codex_queue.codex_result_ingestion import ingest_codex_result_text
from ai_orchestrator.codex_queue.long_run_controller import LongRunController
from ai_orchestrator.codex_queue.plan_run_state import load_state
from codex_plan_helpers import write_plan


def _packet_run(tmp_path: Path, run_id: str = "RUN1") -> tuple[dict, Path, Path]:
    plan_path = write_plan(tmp_path / f"{run_id}_plan.json")
    queue_root = tmp_path / "agent_tasks"
    result = LongRunController(repo_root=tmp_path).run_plan(
        plan_path,
        queue_root,
        run_id=run_id,
        max_steps=1,
        executor="codex_packet",
    )
    return result, Path(result["execution_packet_path"]), queue_root


def _result_json(packet_path: Path, status: str = "completed", **updates: object) -> str:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    envelope = expected_result_schema_for_packet(packet)
    envelope["status"] = status
    envelope["received_at"] = "2026-05-11T00:00:00Z"
    envelope["acceptance_status"] = "pending_ingestion"
    envelope["result_payload"]["status"] = status
    envelope["result_payload"]["summary"] = f"{status} in test"
    envelope["result_payload"].update(updates)
    return json.dumps(envelope)


def test_ingest_accepted_result_marks_task_done(tmp_path: Path) -> None:
    run, packet_path, queue_root = _packet_run(tmp_path)

    result = ingest_codex_result_text(packet_path, _result_json(packet_path), queue_root)
    state = load_state(run["state_path"])

    assert result["status"] == "accepted"
    assert "TEST-TASK-001" in state.completed_task_ids


def test_ingest_blocked_result_marks_task_blocked(tmp_path: Path) -> None:
    run, packet_path, queue_root = _packet_run(tmp_path, "RUN_BLOCKED")

    result = ingest_codex_result_text(packet_path, _result_json(packet_path, "blocked"), queue_root)
    state = load_state(run["state_path"])

    assert result["status"] == "blocked"
    assert "TEST-TASK-001" in state.blocked_task_ids


def test_ingest_failed_result_marks_task_failed(tmp_path: Path) -> None:
    run, packet_path, queue_root = _packet_run(tmp_path, "RUN_FAILED")

    result = ingest_codex_result_text(packet_path, _result_json(packet_path, "failed"), queue_root)
    state = load_state(run["state_path"])

    assert result["status"] == "failed"
    assert "TEST-TASK-001" in state.failed_task_ids


def test_ingest_needs_retry_increments_retry(tmp_path: Path) -> None:
    run, packet_path, queue_root = _packet_run(tmp_path, "RUN_RETRY")

    result = ingest_codex_result_text(packet_path, _result_json(packet_path, "needs_retry"), queue_root)
    state = load_state(run["state_path"])

    assert result["status"] == "needs_retry"
    assert state.retry_counts["TEST-TASK-001"] == 1


def test_ingest_task_id_mismatch_is_rejected(tmp_path: Path) -> None:
    run, packet_path, queue_root = _packet_run(tmp_path, "RUN_MISMATCH")

    result = ingest_codex_result_text(packet_path, _result_json(packet_path, task_id="OTHER"), queue_root)
    state = load_state(run["state_path"])

    assert result["status"] == "rejected"
    assert state.completed_task_ids == []


def test_ingest_unsafe_claim_is_rejected(tmp_path: Path) -> None:
    run, packet_path, queue_root = _packet_run(tmp_path, "RUN_UNSAFE")

    result = ingest_codex_result_text(packet_path, _result_json(packet_path, wallet_used=True), queue_root)
    state = load_state(run["state_path"])

    assert result["status"] == "rejected"
    assert state.completed_task_ids == []
