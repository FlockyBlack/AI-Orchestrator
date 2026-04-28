import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
RUNS_DIR = ROOT / "runs"
STATE_DIR = ROOT / "state"

CREATE_AUDIT_PATH = ROOT / "scripts" / "create_pm_audit_task.py"
DISPATCHER_PATH = ROOT / "scripts" / "dispatcher.py"
CREATE_CHECKPOINT_PATH = ROOT / "scripts" / "create_pm_checkpoint.py"
CREATE_NEXT_TASK_PATH = ROOT / "scripts" / "create_next_pm_task.py"


def run_json_command(command: list[str]) -> dict:
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = completed.stdout.strip()
    if completed.returncode != 0:
        raise RuntimeError(stdout or completed.stderr.strip() or "command failed")
    if not stdout:
        raise RuntimeError("command produced no stdout")
    return json.loads(stdout)


def next_task_id(prefix: str) -> str:
    seen = set()
    for base in (TASKS_DIR, RUNS_DIR):
        if not base.exists():
            continue
        pattern = f"{prefix}-*.task.json" if base == TASKS_DIR else f"{prefix}-*"
        for path in base.rglob(pattern):
            name = path.stem if base == TASKS_DIR else path.name
            token = name.split(".task", 1)[0]
            if token.startswith(prefix + "-"):
                seen.add(token)

    for index in range(1, 1000):
        candidate = f"{prefix}-{index:03d}"
        if candidate not in seen:
            return candidate
    raise RuntimeError(f"could not allocate task id for prefix {prefix}")


def ready_tasks_exist() -> bool:
    ready_dir = TASKS_DIR / "ready"
    return ready_dir.exists() and any(ready_dir.glob("*.task.json"))


def create_audit_task_if_needed() -> str | None:
    if ready_tasks_exist():
        return None
    task_id = next_task_id("PM-AUDIT")
    run_json_command([sys.executable, str(CREATE_AUDIT_PATH), "--task-id", task_id])
    return task_id


def create_checkpoint(audit_task_id: str, review_task_id: str) -> dict:
    return run_json_command(
        [
            sys.executable,
            str(CREATE_CHECKPOINT_PATH),
            "--audit-task-id",
            audit_task_id,
            "--review-task-id",
            review_task_id,
        ]
    )


def create_next_task(task_id: str) -> dict:
    return run_json_command(
        [
            sys.executable,
            str(CREATE_NEXT_TASK_PATH),
            "--task-id",
            task_id,
            "--checkpoint-path",
            str(STATE_DIR / "pm_checkpoint.json"),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-iterations", type=int, default=3)
    args = parser.parse_args()

    if args.max_iterations < 1:
        raise SystemExit("--max-iterations must be >= 1")

    iterations_run = 0
    tasks_executed: list[str] = []
    last_checkpoint_path = str(STATE_DIR / "pm_checkpoint.json")
    final_overall_status = ""
    stopped_reason = "max_iterations"
    latest_review_task_id = "PM-REVIEW-001"

    for _ in range(args.max_iterations):
        iterations_run += 1

        created_audit_task = create_audit_task_if_needed()
        if created_audit_task is not None:
            dispatcher_output = run_json_command([sys.executable, str(DISPATCHER_PATH), "--max-tasks", "1"])
            tasks_executed.extend(item["task_id"] for item in dispatcher_output.get("executed", []))
            latest_audit_task_id = created_audit_task
        else:
            latest_audit_task_id = next_task_id("PM-AUDIT")
            latest_audit_task_id = f"PM-AUDIT-{int(latest_audit_task_id.rsplit('-', 1)[1]) - 1:03d}"

        checkpoint_output = create_checkpoint(latest_audit_task_id, latest_review_task_id)
        last_checkpoint_path = checkpoint_output["checkpoint_path"]
        checkpoint = json.loads(Path(last_checkpoint_path).read_text(encoding="utf-8"))
        final_overall_status = checkpoint["overall_status"]
        if final_overall_status == "pass":
            stopped_reason = "pass"
            break

        next_review_task_id = next_task_id("PM-REVIEW")
        next_task_output = create_next_task(next_review_task_id)
        if next_task_output.get("status") == "needs_human":
            break

        dispatcher_output = run_json_command([sys.executable, str(DISPATCHER_PATH), "--max-tasks", "1"])
        tasks_executed.extend(item["task_id"] for item in dispatcher_output.get("executed", []))
        latest_review_task_id = next_review_task_id

        checkpoint_output = create_checkpoint(latest_audit_task_id, latest_review_task_id)
        last_checkpoint_path = checkpoint_output["checkpoint_path"]
        checkpoint = json.loads(Path(last_checkpoint_path).read_text(encoding="utf-8"))
        final_overall_status = checkpoint["overall_status"]
        if final_overall_status == "pass":
            stopped_reason = "pass"
            break

    print(
        json.dumps(
            {
                "iterations_run": iterations_run,
                "final_overall_status": final_overall_status,
                "tasks_executed": tasks_executed,
                "last_checkpoint_path": last_checkpoint_path,
                "stopped_reason": stopped_reason,
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
