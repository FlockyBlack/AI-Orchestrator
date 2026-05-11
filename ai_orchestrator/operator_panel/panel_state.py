from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PanelState:
    queue_root: str
    selected_plan_file: str = ""
    active_run_id: str = ""
    last_action: dict[str, Any] = field(default_factory=dict)
    action_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PanelState":
        return cls(
            queue_root=str(payload.get("queue_root") or "agent_tasks"),
            selected_plan_file=str(payload.get("selected_plan_file") or ""),
            active_run_id=str(payload.get("active_run_id") or ""),
            last_action=dict(payload.get("last_action") or {}),
            action_events=[
                dict(item)
                for item in payload.get("action_events", [])
                if isinstance(item, dict)
            ],
        )


def load_panel_state(queue_root: str | Path) -> PanelState:
    path = _state_path(queue_root)
    if not path.exists():
        return PanelState(queue_root=str(queue_root))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return PanelState(queue_root=str(queue_root))
    if not isinstance(payload, dict):
        return PanelState(queue_root=str(queue_root))
    return PanelState.from_dict(payload)


def save_panel_state(state: PanelState, queue_root: str | Path) -> Path:
    path = _state_path(queue_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def discover_runs(queue_root: str | Path) -> list[dict[str, Any]]:
    root = Path(queue_root)
    runs: list[dict[str, Any]] = []
    for manifest_path in sorted(root.glob("generated/*/*/manifest.json")):
        manifest = _read_json(manifest_path)
        state_path = manifest_path.parent / "state.json"
        state = _read_json(state_path)
        runs.append(
            {
                "plan_id": manifest.get("plan_id") or manifest_path.parent.parent.name,
                "run_id": manifest.get("run_id") or manifest_path.parent.name,
                "manifest_path": str(manifest_path),
                "state_path": str(state_path),
                "status": _run_status(manifest, state),
                "updated_at": str(state.get("updated_at") or manifest.get("updated_at") or ""),
                "task_count": manifest.get("task_count", 0),
                "completed_count": len(state.get("completed_task_ids", [])) if state else 0,
                "blocked_count": len(state.get("blocked_task_ids", [])) if state else 0,
                "failed_count": len(state.get("failed_task_ids", [])) if state else 0,
                "pending_count": _pending_count(manifest, state),
                "current_task_id": str(state.get("current_task_id") or "") if state else "",
                "latest_handoff_prompt_path": str(state.get("latest_handoff_prompt_path") or "") if state else "",
                "latest_recovery_report_path": str(state.get("latest_recovery_report_path") or "") if state else "",
                "latest_artifacts": list(state.get("artifact_paths", [])[-5:]) if state else [],
            }
        )
    return runs


def discover_plans(queue_root: str | Path) -> list[dict[str, Any]]:
    root = Path(queue_root)
    plans: list[dict[str, Any]] = []
    for plan_path in sorted((root / "plans").glob("*.json")):
        payload = _read_json(plan_path)
        plans.append(
            {
                "path": str(plan_path),
                "plan_id": str(payload.get("plan_id") or ""),
                "title": str(payload.get("title") or plan_path.name),
                "task_count": len(payload.get("tasks", [])) if isinstance(payload.get("tasks", []), list) else 0,
                "milestone_count": len(payload.get("milestones", [])) if isinstance(payload.get("milestones", []), list) else 0,
                "version": str(payload.get("version") or ""),
                "expected_head": str(payload.get("expected_head") or ""),
                "safety_boundaries": [
                    str(item.get("description") or item.get("boundary_id") or "")
                    for item in payload.get("safety_boundaries", [])
                    if isinstance(item, dict)
                ],
            }
        )
    return plans


def summarize_active_run(queue_root: str | Path) -> dict[str, Any]:
    runs = discover_runs(queue_root)
    if not runs:
        return {"status": "none", "run": None}
    active = next((run for run in reversed(runs) if run["status"] not in {"done", "missing_state"}), runs[-1])
    return {"status": "found", "run": active}


def _state_path(queue_root: str | Path) -> Path:
    return Path(queue_root) / "panel_state.json"


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _run_status(manifest: dict[str, Any], state: dict[str, Any]) -> str:
    if not state:
        return "missing_state"
    lifecycle = str(state.get("status") or "")
    if lifecycle and lifecycle not in {"initialized", "queued"}:
        return "done" if lifecycle == "completed" else lifecycle
    total = int(manifest.get("task_count", 0) or 0)
    if state.get("failed_task_ids"):
        return "failed"
    if state.get("blocked_task_ids"):
        return "blocked"
    if total and len(state.get("completed_task_ids", [])) >= total:
        return "done"
    return "running"


def _pending_count(manifest: dict[str, Any], state: dict[str, Any]) -> int:
    total = int(manifest.get("task_count", 0) or 0)
    if not state:
        return total
    terminal = (
        len(state.get("completed_task_ids", []))
        + len(state.get("blocked_task_ids", []))
        + len(state.get("failed_task_ids", []))
        + len(state.get("skipped_task_ids", []))
    )
    return max(0, total - terminal)
