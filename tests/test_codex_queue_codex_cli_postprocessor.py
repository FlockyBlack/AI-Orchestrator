from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.codex_cli_postprocessor import postprocess_codex_batch


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _compact_last_message(task_id: str, *, summary: str | None = None) -> dict:
    return {
        "task_id": task_id,
        "status": "completed",
        "summary": summary or f"Completed {task_id}.",
        "files_changed": [f"docs/{task_id}.md"],
        "validation_commands_run": ["pytest tests/test_example.py"],
        "tests_passed": True,
        "safety_notes": [
            "No network calls, external service calls, credentials, wallet, trading, runtime, scheduler, or destructive commands were used."
        ],
        "remaining_risks": ["Operator should inspect the bridged result before mark-done."],
    }


def _write_completed_execution(
    queue_root: Path,
    task_id: str,
    *,
    run_id: str = "20260509T010000Z",
    last_message: dict | str | None = None,
    write_last_message: bool = True,
) -> dict:
    execution_dir = queue_root / "reports" / "codex_cli_runs" / task_id / run_id
    execution_report_path = execution_dir / "execution_report.json"
    last_message_path = execution_dir / "last_message.md"
    execution_report = {
        "schema_version": "codex_cli_execution_report.v1",
        "run_id": run_id,
        "task_id": task_id,
        "status": "ok",
        "execution_status": "completed",
        "exit_code": 0,
        "execution_ended_at": "2026-05-09T01:05:00Z",
        "report_paths": {
            "execution_report_json": str(execution_report_path),
            "last_message": str(last_message_path),
        },
        "network_calls_performed": 0,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "wallet_or_private_key_access": False,
        "orders_or_trading_actions": False,
        "runtime_or_dispatcher_changes": False,
        "background_worker_created": False,
        "scheduler_created": False,
        "codex_app_server_used": False,
        "destructive_commands_used": False,
    }
    _write_json(execution_report_path, execution_report)
    if write_last_message:
        payload = _compact_last_message(task_id) if last_message is None else last_message
        text = json.dumps(payload) if isinstance(payload, dict) else payload
        last_message_path.write_text(text, encoding="utf-8")
    return {
        "task_id": task_id,
        "status": "ok",
        "execution_status": "completed",
        "exit_code": 0,
        "execution_report_json": str(execution_report_path),
        "errors": [],
        "warnings": [],
    }


def _write_batch_report(queue_root: Path, executions: list[dict], *, run_id: str = "20260509T020000Z") -> Path:
    batch_report_path = queue_root / "reports" / f"codex_cli_batch_report_{run_id}.json"
    _write_json(
        batch_report_path,
        {
            "schema_version": "codex_cli_batch_execution_report.v1",
            "run_id": run_id,
            "status": "ok",
            "execution_status": "completed",
            "ended_at": "2026-05-09T02:00:00Z",
            "task_executions": executions,
        },
    )
    return batch_report_path


def test_bridge_one_completed_task_from_last_message(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BRIDGE-ONE"
    batch_report = _write_batch_report(queue_root, [_write_completed_execution(queue_root, task_id)])

    report = postprocess_codex_batch(queue_root, batch_report_path=batch_report, bridge_results=True)

    result_path = queue_root / "review" / f"{task_id}.result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert report["status"] == "ok"
    assert report["bridged_count"] == 1
    assert result["schema_version"] == "codex_task_result.v1"
    assert result["task_id"] == task_id
    assert result["status"] == "completed"
    assert result["files_modified"] == [f"docs/{task_id}.md"]
    assert result["commands_run"] == ["pytest tests/test_example.py"]
    assert result["acceptance_checks_passed"] is True


def test_bridge_multiple_completed_tasks(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_ids = ["ORCH-BRIDGE-MULTI-1", "ORCH-BRIDGE-MULTI-2", "ORCH-BRIDGE-MULTI-3"]
    executions = [
        _write_completed_execution(queue_root, task_id, run_id=f"20260509T01000{index}Z")
        for index, task_id in enumerate(task_ids)
    ]
    batch_report = _write_batch_report(queue_root, executions)

    report = postprocess_codex_batch(queue_root, batch_report_path=batch_report, bridge_results=True)

    assert report["status"] == "ok"
    assert report["completed_execution_count"] == 3
    assert report["bridged_count"] == 3
    for task_id in task_ids:
        assert (queue_root / "review" / f"{task_id}.result.json").exists()


def test_reject_missing_last_message(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BRIDGE-MISSING-LAST"
    execution = _write_completed_execution(queue_root, task_id, write_last_message=False)
    batch_report = _write_batch_report(queue_root, [execution])

    report = postprocess_codex_batch(queue_root, batch_report_path=batch_report, bridge_results=True)

    assert report["status"] == "blocked"
    assert report["blocked_count"] == 1
    assert report["bridged_count"] == 0
    assert not (queue_root / "review" / f"{task_id}.result.json").exists()
    assert "last_message.md was not found" in report["task_results"][0]["errors"][0]


def test_reject_invalid_result_json(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BRIDGE-INVALID-RESULT"
    invalid_result = {
        "schema_version": "codex_task_result.v1",
        "task_id": task_id,
        "status": "completed",
    }
    execution = _write_completed_execution(queue_root, task_id, last_message=invalid_result)
    batch_report = _write_batch_report(queue_root, [execution])

    report = postprocess_codex_batch(queue_root, batch_report_path=batch_report, bridge_results=True)

    assert report["status"] == "blocked"
    assert report["blocked_count"] == 1
    assert not (queue_root / "review" / f"{task_id}.result.json").exists()
    assert any("missing required field" in error for error in report["task_results"][0]["errors"])


def test_postprocess_summary_written(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BRIDGE-SUMMARY"
    batch_report = _write_batch_report(queue_root, [_write_completed_execution(queue_root, task_id)])

    report = postprocess_codex_batch(queue_root, batch_report_path=batch_report, bridge_results=True)

    paths = report["report_paths"]
    assert Path(paths["post_batch_summary_json"]).exists()
    assert Path(paths["post_batch_summary_md"]).exists()
    assert Path(paths["latest_post_batch_summary_json"]).exists()
    assert Path(paths["latest_post_batch_summary_md"]).exists()
    assert "Codex CLI Batch Postprocess" in Path(paths["post_batch_summary_md"]).read_text(encoding="utf-8")


def test_review_mode_calls_ingest_and_review_helpers(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BRIDGE-REVIEW"
    batch_report = _write_batch_report(queue_root, [_write_completed_execution(queue_root, task_id)])
    calls: dict[str, list] = {"ingest": [], "review": []}

    def fake_ingest(queue_root_arg, result_path):  # type: ignore[no-untyped-def]
        calls["ingest"].append((queue_root_arg, result_path))
        return {
            "accepted": True,
            "ingestion_status": "accepted",
            "report_paths": {"latest_report_json": str(queue_root / "reports" / "latest_result_ingestion_report.json")},
            "errors": [],
        }

    def fake_review(queue_root_arg, task_id_arg):  # type: ignore[no-untyped-def]
        calls["review"].append((queue_root_arg, task_id_arg))
        return {
            "recommendation": "ready_for_operator_done",
            "report_paths": {"review_json": str(queue_root / "reports" / f"{task_id_arg}.review.json")},
        }

    report = postprocess_codex_batch(
        queue_root,
        batch_report_path=batch_report,
        bridge_results=True,
        review_results=True,
        ingest_result_func=fake_ingest,
        review_result_func=fake_review,
    )

    assert report["status"] == "ok"
    assert report["ingested_count"] == 1
    assert report["reviewed_count"] == 1
    assert calls["ingest"][0][1] == queue_root / "review" / f"{task_id}.result.json"
    assert calls["review"] == [(queue_root, task_id)]


def test_postprocess_does_not_mark_done_commit_or_push(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    task_id = "ORCH-BRIDGE-NO-AUTO"
    batch_report = _write_batch_report(queue_root, [_write_completed_execution(queue_root, task_id)])

    report = postprocess_codex_batch(queue_root, batch_report_path=batch_report, bridge_results=True)

    assert not list((queue_root / "done").glob("*.json"))
    assert report["task_marked_done_automatically"] is False
    assert report["review_approved_automatically"] is False
    assert report["git_commit_performed"] is False
    assert report["git_push_performed"] is False
    assert report["scheduler_created"] is False
    assert report["daemon_created"] is False
    assert report["background_worker_created"] is False
    assert report["infinite_loop_created"] is False
