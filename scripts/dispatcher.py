import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

from run_codex import (
    TASK_SCHEMA_PATH,
    build_failure_result,
    create_run_dir,
    load_json,
    validate_task,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
READY_DIR = TASKS_DIR / "ready"
RUNNING_DIR = TASKS_DIR / "running"
DONE_DIR = TASKS_DIR / "done"
FAILED_DIR = TASKS_DIR / "failed"
NEEDS_HUMAN_DIR = TASKS_DIR / "needs_human"
PROJECT_STATE_PATH = ROOT / "state" / "project_state.json"
BUDGET_PATH = ROOT / "state" / "budget.json"
LEDGER_PATH = ROOT / "state" / "task_ledger.jsonl"
VALIDATOR_PATH = ROOT / "scripts" / "validate_result.py"
RUNNER_PATH = ROOT / "scripts" / "run_codex.py"
LOCAL_AUDIT_RUNNER_PATH = ROOT / "scripts" / "run_local_audit.py"
TARGETED_REVIEW_RUNNER_PATH = ROOT / "scripts" / "run_targeted_review.py"
SETTINGS_PATH = ROOT / "config" / "settings.toml"
DEFAULT_CODEX_TIMEOUT_SECONDS = 120
DEFAULT_STALE_TASK_SECONDS = 120


def append_ledger(event: str, task_id: str, status: str, extra: dict | None = None) -> None:
    payload = {"event": event, "task_id": task_id, "status": status}
    if extra:
        payload.update(extra)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")


def count_ready_tasks() -> int:
    return len(sorted(READY_DIR.glob("*.task.json")))


def load_settings() -> dict:
    return tomllib.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def select_ready_tasks() -> list[Path]:
    candidates = sorted(READY_DIR.glob("*.task.json"))
    if len(candidates) <= 1:
        return candidates
    reserved = READY_DIR / "AI-ORCH-SMOKE-001.task.json"
    if reserved not in candidates:
        return candidates
    return [path for path in candidates if path != reserved] + [reserved]


def latest_run_dir(task_id: str) -> Path | None:
    base = ROOT / "runs" / task_id
    if not base.exists():
        return None
    run_dirs = sorted([path for path in base.iterdir() if path.is_dir()])
    if not run_dirs:
        return None
    return run_dirs[-1]


def run_validator(result_path: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--result", str(result_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = completed.stdout.strip()
    if not stdout:
        raise ValueError("validator produced no stdout")
    return json.loads(stdout)


def move_task(task_path: Path, target_dir: Path, new_status: str) -> Path:
    task = load_json(task_path)
    task["status"] = new_status
    write_json(task_path, task)
    target_path = target_dir / task_path.name
    return Path(shutil.move(str(task_path), str(target_path)))


def update_project_state(status: str, active_task: str | None, last_task_id: str | None, last_run_dir: str | None) -> None:
    state = load_json(PROJECT_STATE_PATH)
    state["status"] = status
    state["active_task"] = active_task
    state["last_task_id"] = last_task_id
    state["last_run_dir"] = last_run_dir
    state["ready_tasks_count"] = count_ready_tasks()
    write_json(PROJECT_STATE_PATH, state)


def update_budget(task_executed: bool, codex_launched: bool, final_status: str) -> None:
    budget = load_json(BUDGET_PATH)
    if task_executed:
        budget["tasks_run"] += 1
    if codex_launched:
        budget["codex_runs"] += 1
    if final_status == "failed":
        budget["failed_tasks"] += 1
    if final_status == "needs_human":
        budget["needs_human"] += 1
    write_json(BUDGET_PATH, budget)


def append_run_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.open("a", encoding="utf-8").write(text)


def get_task_age_seconds(task_path: Path) -> float:
    return (datetime.now(timezone.utc) - datetime.fromtimestamp(task_path.stat().st_mtime, tz=timezone.utc)).total_seconds()


def ensure_failure_artifacts(task: dict, task_path: Path, run_dir: Path, reason: str) -> tuple[Path, Path, Path, Path]:
    result_path = run_dir / "result.json"
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    metadata_path = run_dir / "metadata.json"

    if not result_path.exists():
        write_json(
            result_path,
            build_failure_result(
                task["task_id"],
                "task execution failed before a valid result was produced",
                reason,
                task.get("task_type"),
            ),
        )

    if not stdout_path.exists():
        append_run_file(stdout_path, "no stdout captured before recovery\n")
    if not stderr_path.exists():
        append_run_file(stderr_path, f"{reason}\n")

    if not metadata_path.exists():
        write_json(
            metadata_path,
            {
                "task_id": task["task_id"],
                "dry_run": False,
                "created_at": run_dir.name,
                "task_path": str(task_path),
                "run_dir": str(run_dir),
                "recovered": True,
                "recovery_reason": reason,
            },
        )

    return result_path, stdout_path, stderr_path, metadata_path


def fail_running_task(task_path: Path, task: dict, reason: str) -> dict:
    run_dir = latest_run_dir(task["task_id"])
    if run_dir is None:
        _, run_dir = create_run_dir(task["task_id"])

    result_path, stdout_path, stderr_path, metadata_path = ensure_failure_artifacts(task, task_path, run_dir, reason)
    final_path = move_task(task_path, FAILED_DIR, "failed")
    append_ledger("failed", task["task_id"], "failed", {"run_dir": str(run_dir), "reason": reason})
    update_project_state("failed", None, task["task_id"], str(run_dir))
    update_budget(False, False, "failed")

    return {
        "task_id": task["task_id"],
        "codex_launched": False,
        "final_status": "failed",
        "task_path": str(final_path),
        "run_dir": str(run_dir),
        "result_path": str(result_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "metadata_path": str(metadata_path),
        "reason": reason,
    }


def recover_stale_running_tasks(stale_after_seconds: int) -> list[dict]:
    recovered = []
    for task_path in sorted(RUNNING_DIR.glob("*.task.json")):
        if get_task_age_seconds(task_path) < stale_after_seconds:
            continue
        task = load_json(task_path)
        recovered.append(
            fail_running_task(
                task_path,
                task,
                f"stale running task recovered after exceeding {stale_after_seconds} seconds",
            )
        )
    return recovered


def handle_limited_task(task_path: Path, task: dict) -> dict:
    destination = move_task(task_path, NEEDS_HUMAN_DIR, "needs_human")
    append_ledger("needs_human", task["task_id"], "needs_human")
    update_project_state("needs_human", None, task["task_id"], None)
    update_budget(False, False, "needs_human")
    return {
        "task_id": task["task_id"],
        "codex_launched": False,
        "final_status": "needs_human",
        "task_path": str(destination),
        "result_valid": False,
        "run_dir": None,
    }


def execute_task(task_path: Path, task: dict, codex_timeout_seconds: int) -> dict:
    running_path = move_task(task_path, RUNNING_DIR, "running")
    append_ledger("running", task["task_id"], "running")
    update_project_state("running", task["task_id"], task["task_id"], None)

    task_type = task.get("task_type")
    used_local_executor = task_type in {"read_only_audit", "targeted_manual_review"}
    if task_type == "read_only_audit":
        command = [sys.executable, str(LOCAL_AUDIT_RUNNER_PATH), "--task", str(running_path)]
    elif task_type == "targeted_manual_review":
        command = [sys.executable, str(TARGETED_REVIEW_RUNNER_PATH), "--task", str(running_path)]
    else:
        command = [
            sys.executable,
            str(RUNNER_PATH),
            "--task",
            str(running_path),
            "--execute",
            "--timeout-seconds",
            str(codex_timeout_seconds),
        ]

    completed = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, check=False)

    runner_stdout = completed.stdout.strip()
    if not runner_stdout:
        return fail_running_task(running_path, task, "run_codex.py produced no stdout")
    runner_output = json.loads(runner_stdout)

    run_dir = latest_run_dir(task["task_id"])
    if run_dir is None:
        raise RuntimeError("no run directory found after execution")

    result_path = run_dir / "result.json"
    validator_output = run_validator(result_path) if result_path.exists() else {
        "status": "invalid",
        "result_path": str(result_path),
        "errors": ["result.json was not created"],
    }
    result_valid = validator_output["status"] == "valid"
    result_data = load_json(result_path) if result_valid else {}

    if result_valid and result_data.get("status") == "done" and result_data.get("needs_human") is False:
        final_status = "done"
        final_dir = DONE_DIR
    elif result_valid and result_data.get("status") == "needs_human":
        final_status = "needs_human"
        final_dir = NEEDS_HUMAN_DIR
    else:
        final_status = "failed"
        final_dir = FAILED_DIR

    final_path = move_task(running_path, final_dir, final_status)
    append_ledger(final_status, task["task_id"], final_status, {"run_dir": str(run_dir)})
    update_project_state(final_status, None, task["task_id"], str(run_dir))
    update_budget(True, not used_local_executor, final_status)

    return {
        "task_id": task["task_id"],
        "codex_launched": not used_local_executor,
        "runner_returncode": completed.returncode,
        "run_dir": str(run_dir),
        "result_valid": result_valid,
        "final_status": final_status,
        "task_path": str(final_path),
        "validator": validator_output,
        "runner": runner_output,
    }


def run_dispatch(max_tasks: int, stop_on_failure: bool, codex_timeout_seconds: int, stale_after_seconds: int) -> dict:
    executed = []
    recovered = recover_stale_running_tasks(stale_after_seconds)

    while len(executed) < max_tasks:
        ready_tasks = select_ready_tasks()
        if not ready_tasks:
            break

        task_path = ready_tasks[0]
        task = load_json(task_path)
        task_schema = load_json(TASK_SCHEMA_PATH)
        validate_task(task, task_schema)

        if task["safety_level"] in {"L3", "L4"}:
            outcome = handle_limited_task(task_path, task)
        else:
            outcome = execute_task(task_path, task, codex_timeout_seconds)

        executed.append(outcome)
        if outcome["final_status"] == "needs_human":
            break
        if stop_on_failure and outcome["final_status"] == "failed":
            break

    if not executed:
        update_project_state("idle", None, None, None)

    return {
        "recovered": recovered,
        "recovered_count": len(recovered),
        "executed": executed,
        "executed_count": len(executed),
        "ready_tasks_count": count_ready_tasks(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--max-tasks", type=int)
    parser.add_argument("--stop-on-failure", action="store_true")
    parser.add_argument("--recover-stale-only", action="store_true")
    parser.add_argument("--stale-after-seconds", type=int)
    parser.add_argument("--codex-timeout-seconds", type=int)
    args = parser.parse_args()

    settings = load_settings()
    max_tasks = settings["max_tasks_per_run"]
    codex_timeout_seconds = settings.get("codex_timeout_seconds", DEFAULT_CODEX_TIMEOUT_SECONDS)
    stale_after_seconds = settings.get("stale_task_timeout_seconds", codex_timeout_seconds)
    if args.max_tasks is not None:
        max_tasks = args.max_tasks
    if args.codex_timeout_seconds is not None:
        codex_timeout_seconds = args.codex_timeout_seconds
    if args.stale_after_seconds is not None:
        stale_after_seconds = args.stale_after_seconds
    if args.once:
        max_tasks = 1
    if max_tasks < 1:
        raise SystemExit("--max-tasks must be >= 1")
    if codex_timeout_seconds < 1:
        raise SystemExit("--codex-timeout-seconds must be >= 1")
    if stale_after_seconds < 1:
        raise SystemExit("--stale-after-seconds must be >= 1")

    if args.recover_stale_only:
        recovered = recover_stale_running_tasks(stale_after_seconds)
        print(json.dumps({"recovered": recovered, "recovered_count": len(recovered)}))
        return 0

    output = run_dispatch(
        max_tasks=max_tasks,
        stop_on_failure=args.stop_on_failure,
        codex_timeout_seconds=codex_timeout_seconds,
        stale_after_seconds=stale_after_seconds,
    )
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
