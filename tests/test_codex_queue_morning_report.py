from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.morning_report import generate_morning_report
from ai_orchestrator.codex_queue.schema import default_packet


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _packet(task_id: str, status: str) -> dict:
    packet = default_packet()
    packet["task_id"] = task_id
    packet["title"] = f"{task_id} morning report test"
    packet["status"] = status
    packet["created_at"] = "2026-05-09T00:00:00Z"
    packet["task_type"] = "local_docs_only"
    packet["priority"] = "low"
    packet["summary"] = "Safe local morning report test task."
    packet["instructions"] = ["Create a harmless docs note."]
    packet["repo"]["base_branch"] = "master"
    packet["repo"]["allowed_paths"] = ["docs/"]
    packet["repo"]["forbidden_paths"] = ["runtime/", "dispatcher/", "run_codex/", "pm_bot/"]
    packet["acceptance_checks"] = []
    packet["expected_outputs"] = ["docs/result.md"]
    if status in {"approved", "planned", "review", "done", "blocked"}:
        packet["approved_by"] = "operator"
        packet["approved_at"] = "2026-05-09T00:00:00Z"
    return packet


def _write_task(queue_root: Path, task_id: str, status: str) -> None:
    _write_json(queue_root / status / f"{task_id}.task.json", _packet(task_id, status))


def test_morning_report_writes_latest_json_markdown_and_timestamped_json(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_task(queue_root, "ORCH-MORNING-PLANNED", "planned")

    report = generate_morning_report(queue_root)

    latest_json = queue_root / "reports" / "latest_morning_report.json"
    latest_md = queue_root / "reports" / "latest_morning_report.md"
    timestamped = Path(report["report_paths"]["run_morning_report_json"])
    assert latest_json.exists()
    assert latest_md.exists()
    assert timestamped.exists()


def test_morning_report_includes_blocked_done_review_and_planned_counts(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    _write_task(queue_root, "ORCH-MORNING-PLANNED", "planned")
    _write_task(queue_root, "ORCH-MORNING-REVIEW", "review")
    _write_task(queue_root, "ORCH-MORNING-DONE", "done")
    _write_task(queue_root, "ORCH-MORNING-BLOCKED", "blocked")
    _write_json(
        queue_root / "reports" / "ORCH-MORNING-BLOCKED.blocked.json",
        {"task_id": "ORCH-MORNING-BLOCKED", "reason": "waiting on operator"},
    )

    report = generate_morning_report(queue_root)

    counts = report["queue_health"]["counts"]
    assert counts["planned"] == 1
    assert counts["review"] == 1
    assert counts["done"] == 1
    assert counts["blocked"] == 1
    assert report["blocked_tasks"][0]["reason"] == "waiting on operator"
    markdown = (queue_root / "reports" / "latest_morning_report.md").read_text(encoding="utf-8")
    assert "- planned: `1`" in markdown
    assert "- review: `1`" in markdown
    assert "- done: `1`" in markdown
    assert "- blocked: `1`" in markdown
