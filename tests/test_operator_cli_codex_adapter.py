from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.codex_executor_contract import expected_result_schema_for_packet
from ai_orchestrator.codex_queue.operator_cli import main
from codex_plan_helpers import write_plan


def _latest_action(queue_root: Path) -> dict:
    return json.loads((queue_root / "reports" / "latest_operator_action.json").read_text(encoding="utf-8"))


def test_cli_create_codex_packet_works(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--max-steps", "1", "--executor", "fake"]) == 0
    run_id = _latest_action(queue_root)["run_id"]

    exit_code = main(["create-codex-packet", "--run-id", run_id, "--queue-root", str(queue_root), "--adapter-mode", "manual_handoff"])
    action = _latest_action(queue_root)

    assert exit_code == 0
    assert action["command"] == "create-codex-packet"
    assert Path(action["execution_packet_path"]).exists()


def test_cli_ingest_codex_result_works(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--max-steps", "1", "--executor", "fake"]) == 0
    run_id = _latest_action(queue_root)["run_id"]
    assert main(["create-codex-packet", "--run-id", run_id, "--queue-root", str(queue_root)]) == 0
    packet_path = Path(_latest_action(queue_root)["execution_packet_path"])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    result_payload = expected_result_schema_for_packet(packet)
    result_payload["received_at"] = "2026-05-11T00:00:00Z"
    result_payload["status"] = "completed"
    result_payload["result_payload"]["status"] = "completed"
    result_file = tmp_path / "result.json"
    result_file.write_text(json.dumps(result_payload), encoding="utf-8")

    exit_code = main(["ingest-codex-result", "--packet-path", str(packet_path), "--result-json", str(result_file), "--queue-root", str(queue_root)])
    action = _latest_action(queue_root)

    assert exit_code == 0
    assert action["command"] == "ingest-codex-result"
    assert action["codex_result_ingestion"]["status"] == "accepted"


def test_cli_codex_adapter_dry_run_writes_artifact(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path / "plan.json")
    queue_root = tmp_path / "agent_tasks"
    assert main(["run-plan", "--plan-file", str(plan_path), "--queue-root", str(queue_root), "--max-steps", "1", "--executor", "fake"]) == 0
    run_id = _latest_action(queue_root)["run_id"]

    exit_code = main(["codex-adapter-dry-run", "--run-id", run_id, "--queue-root", str(queue_root), "--adapter-mode", "codex_cli_dry_run"])
    action = _latest_action(queue_root)

    assert exit_code == 0
    assert action["run_status"] == "adapter_dry_run_ready"
    assert Path(action["plan_runner_result"]["payload"]["codex_cli_dry_run_path"]).exists()
