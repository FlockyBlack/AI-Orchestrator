from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.result_ingestor import ingest_result
from ai_orchestrator.codex_queue.result_schema import default_result
from ai_orchestrator.codex_queue.schema import default_packet


def _approved_packet(task_id: str = "ORCH-RESULT-TEST", allowed_paths: list[str] | None = None) -> dict:
    packet = default_packet()
    packet["task_id"] = task_id
    packet["title"] = "Result ingestion test packet"
    packet["status"] = "approved"
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    packet["repo"]["allowed_paths"] = allowed_paths or ["docs/"]
    packet["repo"]["forbidden_paths"] = ["ai_orchestrator/", "runtime/", "pm_bot/", "merchant_pipeline/"]
    return packet


def _result(task_id: str = "ORCH-RESULT-TEST", files_created: list[str] | None = None) -> dict:
    result = default_result()
    result["task_id"] = task_id
    result["summary"] = "Manual result for ingestion testing."
    result["files_created"] = files_created or ["docs/result.md"]
    return result


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_task(queue_root: Path, packet: dict) -> None:
    _write_json(queue_root / "approved" / f"{packet['task_id']}.task.json", packet)


def _write_result(queue_root: Path, result: dict) -> Path:
    result_path = queue_root / "review" / f"{result['task_id']}.result.json"
    _write_json(result_path, result)
    return result_path


def test_result_with_unknown_task_id_blocks_ingestion(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    result_path = _write_result(queue_root, _result(task_id="ORCH-UNKNOWN-TASK"))

    report = ingest_result(queue_root, result_path)

    assert report["accepted"] is False
    assert report["ingestion_status"] == "blocked"
    assert any("no matching task packet found" in error for error in report["errors"])


def test_result_with_path_outside_allowed_paths_blocks(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_task(queue_root, _approved_packet(allowed_paths=["docs/"]))
    result_path = _write_result(queue_root, _result(files_created=["tests/not-allowed.py"]))

    report = ingest_result(queue_root, result_path)

    assert report["accepted"] is False
    assert any("outside allowed_paths" in error for error in report["errors"])


def test_result_with_absolute_windows_path_blocks(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_task(queue_root, _approved_packet(allowed_paths=["docs/"]))
    result_path = _write_result(queue_root, _result(files_created=[r"C:\repo\docs\bad.md"]))

    report = ingest_result(queue_root, result_path)

    assert report["accepted"] is False
    assert any("absolute drive path" in error for error in report["errors"])


def test_result_with_path_traversal_blocks(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_task(queue_root, _approved_packet(allowed_paths=["docs/"]))
    result_path = _write_result(queue_root, _result(files_created=["docs/../ai_orchestrator/bad.py"]))

    report = ingest_result(queue_root, result_path)

    assert report["accepted"] is False
    assert any("path traversal" in error for error in report["errors"])


def test_result_with_docs_path_passes_when_allowed_paths_include_docs(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_task(queue_root, _approved_packet(allowed_paths=["docs/"]))
    result_path = _write_result(queue_root, _result(files_created=["docs/result.md"]))

    report = ingest_result(queue_root, result_path)

    assert report["accepted"] is True
    assert report["ingestion_status"] == "accepted"
    assert report["path_validation"]["valid"] is True


def test_ingestor_writes_latest_json_and_markdown_reports(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_task(queue_root, _approved_packet(allowed_paths=["docs/"]))
    result_path = _write_result(queue_root, _result(files_created=["docs/result.md"]))

    report = ingest_result(queue_root, result_path)

    latest_json = queue_root / "reports" / "latest_result_ingestion_report.json"
    latest_md = queue_root / "reports" / "latest_result_ingestion_report.md"
    assert latest_json.exists()
    assert latest_md.exists()
    assert report["report_paths"]["latest_report_json"] == str(latest_json)
    latest_payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert latest_payload["accepted"] is True
    assert "does not execute Codex" in latest_md.read_text(encoding="utf-8")


def test_ingestor_does_not_execute_commands_from_result(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    sentinel = tmp_path / "command_was_executed.txt"
    _write_task(queue_root, _approved_packet(allowed_paths=["docs/"]))
    result = _result(files_created=["docs/result.md"])
    result["commands_run"] = [f"python -c \"from pathlib import Path; Path(r'{sentinel}').write_text('bad')\""]
    result_path = _write_result(queue_root, result)

    report = ingest_result(queue_root, result_path)

    assert report["accepted"] is True
    assert report["commands_from_result_executed"] is False
    assert not sentinel.exists()
