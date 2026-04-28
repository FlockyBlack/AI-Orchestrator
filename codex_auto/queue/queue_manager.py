import argparse
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TASKS_ROOT = PROJECT_ROOT / "codex_auto" / "tasks"
READY_ROOT = Path(os.environ.get("CODEX_AUTO_READY_ROOT", str(TASKS_ROOT / "ready")))
NEEDS_FLOCKY_REVIEW_ROOT = TASKS_ROOT / "needs_flocky_review"
VALIDATOR_PATH = PROJECT_ROOT / "codex_auto" / "queue" / "validate_queue_task.py"
RUNNER_PATH = PROJECT_ROOT / "codex_auto" / "runner" / "run_codex_task.py"
APPROVED_TINY_TASK_ID = "CODEX-AUTO-TINY-001"
APPROVED_TINY_FIXTURE = PROJECT_ROOT / "codex_auto" / "fixtures" / "approved_tiny_fixture_task.v1.json"


def _utc_timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _load_validator():
    spec = importlib.util.spec_from_file_location("codex_auto_queue_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("queue_validator_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ready_task_paths():
    return sorted(READY_ROOT.glob("*.task.json"))


def _display_path(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/") if path.is_relative_to(PROJECT_ROOT) else str(path)


def _is_preview_only_ready_task(payload):
    return (
        payload.get("approved_for_execution") is False
        or payload.get("execution_allowed_now") is False
        or payload.get("external_codex_cli_allowed") is False and payload.get("codex_task_id") != APPROVED_TINY_TASK_ID
        or payload.get("human_approval_required_before_execution") is True
        or payload.get("flocky_review_required_before_execution") is True and payload.get("codex_task_id") != APPROVED_TINY_TASK_ID
    )


def _list_ready():
    ready_tasks = []
    for path in _ready_task_paths():
        payload = _load_json(path)
        ready_tasks.append(
            {
                "queue_task_id": payload.get("queue_task_id"),
                "codex_task_id": payload.get("codex_task_id"),
                "file": _display_path(path),
                "queue_state": payload.get("queue_state"),
            }
        )
    return {"status": "ok", "ready_tasks": ready_tasks}


def _validate_task(task_path: Path):
    validator = _load_validator()
    return validator.validate_file(str(task_path))


def _help_payload():
    return {
        "status": "ok",
        "message": "Provide --list-ready, --validate <task>, --dry-run-next, or --execute-next-controlled.",
    }


def _dry_run_next():
    ready_tasks = _ready_task_paths()
    if not ready_tasks:
        return {"status": "blocked", "errors": ["no_ready_tasks"]}
    task_path = ready_tasks[0]
    payload = _load_json(task_path)
    if payload.get("codex_task_id") != APPROVED_TINY_TASK_ID or _is_preview_only_ready_task(payload):
        return {
            "status": "blocked_preview_only",
            "queue_task_id": payload.get("queue_task_id"),
            "codex_task_id": payload.get("codex_task_id"),
            "task": _display_path(task_path),
            "reason": "PMBOT ready tasks remain preview-only until separate human approval, Flocky validation, and external plan execution gate.",
            "would_execute": False,
            "external_codex_cli_allowed_now": False,
            "runtime_wiring_allowed": False,
        }
    validation = _validate_task(task_path)
    if validation["status"] != "valid":
        return {"status": "invalid", "task": _display_path(task_path), "validation": validation, "would_execute": False}
    return {
        "status": "dry_run_ready",
        "queue_task_id": payload["queue_task_id"],
        "codex_task_id": payload["codex_task_id"],
        "task": _display_path(task_path),
        "plan": "validate -> dry_run_or_controlled_execute -> result_envelope -> needs_flocky_review",
        "would_execute": False,
        "moved_files": [],
    }


def _result_record_path(queue_task_id: str):
    return NEEDS_FLOCKY_REVIEW_ROOT / f"{queue_task_id}.result.json"


def _execute_next_controlled():
    ready_tasks = _ready_task_paths()
    if not ready_tasks:
        return {"status": "blocked", "errors": ["no_ready_tasks"]}

    task_path = ready_tasks[0]
    payload = _load_json(task_path)
    if payload.get("codex_task_id") != APPROVED_TINY_TASK_ID:
        return {"status": "blocked", "errors": ["unsupported_execute_next_controlled_task"]}
    validation = _validate_task(task_path)
    if validation["status"] != "valid":
        return {"status": "blocked", "validation": validation, "errors": ["queue_task_invalid"]}

    runner = subprocess.run(
        [sys.executable, str(RUNNER_PATH), str(APPROVED_TINY_FIXTURE), "--execute"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if not runner.stdout.strip():
        return {"status": "blocked", "errors": ["runner_produced_no_output"]}

    result_envelope = json.loads(runner.stdout)
    if result_envelope.get("execution_mode") != "controlled_tiny_sandbox":
        return {"status": "blocked", "errors": ["unexpected_runner_execution_mode"], "result_envelope": result_envelope}
    if result_envelope.get("openclaw_validation_required") is not True:
        return {"status": "blocked", "errors": ["flocky_validation_requirement_missing"], "result_envelope": result_envelope}

    record = {
        "schema_version": "queue_result_record.v1",
        "queue_task_id": payload["queue_task_id"],
        "codex_task_id": payload["codex_task_id"],
        "result_status": result_envelope.get("result_status"),
        "produced_at": _utc_timestamp(),
        "source_task_path": _display_path(task_path),
        "result_envelope": result_envelope,
        "files_created": result_envelope.get("files_created", []),
        "files_modified_existing": result_envelope.get("files_modified_existing", []),
        "tests_run": result_envelope.get("tests_run", []),
        "tests_passed": result_envelope.get("tests_passed"),
        "safety_check": result_envelope.get("safety_check", {}),
        "next_queue_state": "needs_flocky_review",
        "flocky_validation_required": True,
    }
    output_path = _result_record_path(payload["queue_task_id"])
    _write_json(output_path, record)
    return {
        "status": "ok",
        "queue_task_id": payload["queue_task_id"],
        "codex_task_id": payload["codex_task_id"],
        "result_record": str(output_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "next_queue_state": "needs_flocky_review",
        "flocky_validation_required": True,
        "ready_task_retained": True,
    }


def main(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--list-ready", action="store_true")
    parser.add_argument("--validate")
    parser.add_argument("--dry-run-next", action="store_true")
    parser.add_argument("--execute-next-controlled", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.list_ready:
        result = _list_ready()
    elif args.validate:
        result = _validate_task(Path(args.validate))
    elif args.dry_run_next:
        result = _dry_run_next()
    elif args.execute_next_controlled:
        result = _execute_next_controlled()
    else:
        result = _help_payload()

    print(json.dumps(result, separators=(",", ":")))
    return 0 if result.get("status") in {"ok", "valid", "dry_run_ready", "blocked_preview_only"} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
