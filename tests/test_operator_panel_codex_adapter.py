from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.codex_queue.codex_executor_contract import expected_result_schema_for_packet
from ai_orchestrator.operator_panel.panel_actions import (
    create_codex_packet_action,
    ingest_codex_result_action,
    run_fake_steps_action,
)
from ai_orchestrator.operator_panel.panel_app import route_get, route_post
from codex_plan_helpers import write_plan


def test_panel_action_creates_codex_packet(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")
    run = run_fake_steps_action(plan_path, queue_root, max_steps=1)

    result = create_codex_packet_action(run["run_id"], queue_root, "manual_handoff")

    assert result["status"] == "requiring_operator_handoff"
    assert Path(result["execution_packet_path"]).exists()


def test_panel_renderer_shows_packet_prompt_and_template(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")
    run = run_fake_steps_action(plan_path, queue_root, max_steps=1)
    create_codex_packet_action(run["run_id"], queue_root, "manual_handoff")

    html = route_get("/codex-handoff", "", tmp_path, queue_root)

    assert "latest packet" in html
    assert "Expected result JSON" in html
    assert "Codex Execution Packet" in html


def test_panel_ingest_codex_result_action_updates_state(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")
    run = run_fake_steps_action(plan_path, queue_root, max_steps=1)
    packet_result = create_codex_packet_action(run["run_id"], queue_root, "manual_handoff")
    packet_path = Path(packet_result["execution_packet_path"])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    result_payload = expected_result_schema_for_packet(packet)
    result_payload["received_at"] = "2026-05-11T00:00:00Z"
    result_payload["status"] = "completed"
    result_payload["result_payload"]["status"] = "completed"

    result = ingest_codex_result_action(packet_path, json.dumps(result_payload), queue_root)

    assert result["status"] == "accepted"
    assert Path(result["report_paths"]["json"]).exists()


def test_panel_routes_include_codex_adapter_actions(tmp_path: Path) -> None:
    queue_root = tmp_path / "agent_tasks"
    plan_path = write_plan(queue_root / "plans" / "plan.json")
    run = run_fake_steps_action(plan_path, queue_root, max_steps=1)

    result = route_post("/actions/create-codex-packet", {"run_id": run["run_id"], "adapter_mode": "manual_handoff"}, tmp_path, queue_root)
    detail_html = route_get("/run", f"id={run['run_id']}", tmp_path, queue_root)

    assert result["status"] == "requiring_operator_handoff"
    assert "Create Codex packet" in detail_html
    assert "Ingest result JSON" in detail_html
