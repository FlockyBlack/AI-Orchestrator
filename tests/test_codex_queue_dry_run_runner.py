from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.dry_run_runner import run_dry_run
from ai_orchestrator.codex_queue.schema import default_packet


def _approved_packet() -> dict:
    packet = default_packet()
    packet["status"] = "approved"
    packet["approved_by"] = "operator"
    packet["approved_at"] = "2026-05-09T00:00:00Z"
    packet["task_id"] = "ORCH-DRY-RUN-TEST"
    packet["title"] = "Dry-run test packet"
    return packet


def test_dry_run_runner_writes_latest_json_and_markdown_reports(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    approved_dir = queue_root / "approved"
    approved_dir.mkdir(parents=True)
    (approved_dir / "safe.task.json").write_text(json.dumps(_approved_packet()), encoding="utf-8")

    report = run_dry_run(queue_root)

    latest_json = queue_root / "reports" / "latest_dry_run_report.json"
    latest_md = queue_root / "reports" / "latest_dry_run_report.md"
    assert latest_json.exists()
    assert latest_md.exists()
    assert report["allowed_count"] == 1
    assert report["acceptance_checks_executed"] is False

    latest_payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert latest_payload["allowed_count"] == 1
    assert latest_payload["codex_app_server_used"] is False
    assert "did not execute acceptance checks" in latest_md.read_text(encoding="utf-8")


def test_dry_run_runner_writes_handoff_prompt_for_allowed_task(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    approved_dir = queue_root / "approved"
    approved_dir.mkdir(parents=True)
    (approved_dir / "safe.task.json").write_text(json.dumps(_approved_packet()), encoding="utf-8")

    report = run_dry_run(queue_root)

    plan_path = queue_root / "planned" / "ORCH-DRY-RUN-TEST.plan.json"
    handoff_prompt_path = queue_root / "planned" / "ORCH-DRY-RUN-TEST.handoff_prompt.md"
    assert plan_path.exists()
    assert handoff_prompt_path.exists()
    assert str(handoff_prompt_path) in report["handoff_prompt_paths"]
    assert "Do not start background processes" in handoff_prompt_path.read_text(encoding="utf-8")


def test_dry_run_runner_does_not_execute_acceptance_checks(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    approved_dir = queue_root / "approved"
    approved_dir.mkdir(parents=True)
    sentinel = tmp_path / "acceptance_check_was_executed.txt"
    packet = _approved_packet()
    packet["acceptance_checks"] = [
        f"python -c \"from pathlib import Path; Path(r'{sentinel}').write_text('bad')\""
    ]
    (approved_dir / "safe.task.json").write_text(json.dumps(packet), encoding="utf-8")

    run_dry_run(queue_root)

    assert not sentinel.exists()

