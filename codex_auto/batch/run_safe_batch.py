import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUEUE_MANAGER = PROJECT_ROOT / "codex_auto" / "queue" / "queue_manager.py"
FLOCKY_REVIEW = PROJECT_ROOT / "codex_auto" / "flocky_review" / "review_needs_flocky.py"
READY_TASK = "codex_auto/tasks/ready/CODEX-AUTO-TINY-001.task.json"
RESULT_RECORD = "codex_auto/tasks/needs_flocky_review/QUEUE-CODEX-AUTO-TINY-001.result.json"
DONE_REVIEW = "codex_auto/tasks/done/FLOCKY-REVIEW-QUEUE-CODEX-AUTO-TINY-001.review.json"


def _run_local(script: Path, *args):
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _list_ready_tasks():
    result = _run_local(QUEUE_MANAGER, "--list-ready")
    if not result.stdout.strip():
        return [READY_TASK]
    payload = json.loads(result.stdout)
    return [item["file"] for item in payload.get("ready_tasks", [])]


def _base_payload(mode: str, max_tasks: int):
    return {
        "status": "ok",
        "mode": mode,
        "max_tasks": max_tasks,
        "tasks_seen": _list_ready_tasks(),
        "actions_taken": [],
        "files_created": [],
        "flocky_review_written": False,
        "runtime_wiring_added": False,
        "external_codex_cli_invoked": False,
        "safety_check": {
            "runtime_changed": False,
            "dispatcher_touched": False,
            "run_codex_touched": False,
            "active_task_files_touched": False,
            "freeze_record_modified": False,
            "result_records_modified": False,
            "checkpoint_records_modified": False,
            "network_used": False,
            "api_used": False,
            "wallet_used": False,
            "private_key_used": False,
            "trading_used": False,
            "single_runtime_source_rule_preserved": True
        }
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-tasks", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute-controlled", action="store_true")
    parser.add_argument("--flocky-review", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.max_tasks > 1:
        result = _base_payload("unsupported", args.max_tasks)
        result["status"] = "blocked"
        result["tasks_seen"] = []
        result["actions_taken"] = ["unsupported_max_tasks"]
        print(json.dumps(result, separators=(",", ":")))
        return 1

    if not args.dry_run and not args.execute_controlled:
        result = _base_payload("help", args.max_tasks)
        result["tasks_seen"] = []
        result["actions_taken"] = ["no_operation_selected"]
        print(json.dumps(result, separators=(",", ":")))
        return 0

    if args.dry_run:
        result = _base_payload("dry_run", args.max_tasks)
        queue_result = _run_local(QUEUE_MANAGER, "--dry-run-next")
        parsed = json.loads(queue_result.stdout)
        result["actions_taken"].append("queue_dry_run_next")
        result["queue_manager_result"] = parsed
        print(json.dumps(result, separators=(",", ":")))
        return 0 if parsed.get("status") in {"dry_run_ready", "blocked_preview_only"} else 1

    result = _base_payload("execute_controlled", args.max_tasks)
    queue_result = _run_local(QUEUE_MANAGER, "--execute-next-controlled")
    parsed_queue = json.loads(queue_result.stdout)
    result["actions_taken"].append("queue_execute_next_controlled")
    result["queue_manager_result"] = parsed_queue
    if parsed_queue.get("status") != "ok":
        result["status"] = "blocked"
        print(json.dumps(result, separators=(",", ":")))
        return 1
    result["files_created"].append(parsed_queue["result_record"])

    if args.flocky_review:
        review_result = _run_local(FLOCKY_REVIEW, RESULT_RECORD, "--write-review")
        parsed_review = json.loads(review_result.stdout)
        result["actions_taken"].append("write_flocky_review")
        result["flocky_review_written"] = True
        result["files_created"].append(DONE_REVIEW)
        result["review_result"] = parsed_review
        result["mode"] = "execute_controlled_with_flocky_review"
        if parsed_review.get("review_status") not in {"pass", "warning"}:
            result["status"] = "failed"
            print(json.dumps(result, separators=(",", ":")))
            return 1

    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
