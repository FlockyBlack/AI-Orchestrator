from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .planner import create_plan, render_handoff_prompt
from .report_writer import ensure_queue_directories, utc_run_id, write_json, write_reports, write_text
from .safety import classify_packet
from .validator import validate_packet


def run_dry_run(queue_root: str | Path = "agent_tasks") -> dict[str, Any]:
    root = ensure_queue_directories(queue_root)
    approved_dir = root / "approved"
    planned_dir = root / "planned"
    entries: list[dict[str, Any]] = []
    plan_paths: list[str] = []
    handoff_prompt_paths: list[str] = []

    for packet_path in sorted(approved_dir.glob("*.json")):
        entry: dict[str, Any] = {
            "packet_path": str(packet_path),
            "task_id": None,
            "validation": {"valid": False, "errors": []},
            "classification": None,
            "classification_status": "unread",
            "errors": [],
            "plan_path": None,
            "handoff_prompt_path": None,
        }

        try:
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            entry["errors"].append(f"invalid JSON: {exc}")
            entries.append(entry)
            continue

        if isinstance(packet, dict):
            entry["task_id"] = packet.get("task_id")

        validation = validate_packet(packet)
        classification = classify_packet(packet, validation) if isinstance(packet, dict) else None
        entry["validation"] = validation.to_dict()
        entry["classification"] = classification.to_dict() if classification else None
        entry["classification_status"] = classification.status if classification else "invalid"
        if not validation.valid:
            entry["errors"].extend(validation.errors)

        if classification and classification.allowed:
            plan = create_plan(packet, root)
            task_id = packet["task_id"]
            plan_path = planned_dir / f"{task_id}.plan.json"
            handoff_prompt_path = planned_dir / f"{task_id}.handoff_prompt.md"
            plan["handoff_prompt_path"] = str(handoff_prompt_path)
            write_json(plan_path, plan)
            write_text(handoff_prompt_path, render_handoff_prompt(packet, plan))
            entry["plan_path"] = str(plan_path)
            entry["handoff_prompt_path"] = str(handoff_prompt_path)
            plan_paths.append(str(plan_path))
            handoff_prompt_paths.append(str(handoff_prompt_path))

        entries.append(entry)

    report = {
        "run_id": utc_run_id(),
        "queue_root": str(root),
        "dry_run": True,
        "automatic_execution_enabled": False,
        "codex_app_server_used": False,
        "codex_execution_added": False,
        "acceptance_checks_executed": False,
        "packets_seen": len(entries),
        "allowed_count": sum(1 for entry in entries if entry["classification_status"] == "allowed"),
        "blocked_count": sum(1 for entry in entries if entry["classification_status"] == "blocked"),
        "requires_special_approval_count": sum(
            1 for entry in entries if entry["classification_status"] == "requires_special_approval"
        ),
        "not_allowed_count": sum(
            1
            for entry in entries
            if entry["classification_status"] in {"not_allowed", "not_approved", "invalid", "unread"}
        ),
        "plan_paths": plan_paths,
        "handoff_prompt_paths": handoff_prompt_paths,
        "entries": entries,
    }
    report_paths = write_reports(root, report)
    report["report_paths"] = report_paths
    write_reports(root, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local Codex queue dry-run planner.")
    parser.add_argument("--queue-root", default="agent_tasks", help="Local queue root directory.")
    parser.add_argument("--dry-run", action="store_true", help="Required; this runner never executes tasks.")
    args = parser.parse_args(argv)

    if not args.dry_run:
        parser.error("--dry-run is required; this MVP only supports non-executing planning")

    report = run_dry_run(args.queue_root)
    print(json.dumps({"status": "ok", "report_paths": report["report_paths"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

