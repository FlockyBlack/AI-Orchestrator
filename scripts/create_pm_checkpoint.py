import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
STATE_PATH = ROOT / "state" / "pm_checkpoint.json"

DEFAULT_AUDIT_TASK_ID = "PM-AUDIT-006"
DEFAULT_REVIEW_TASK_ID = "PM-REVIEW-001"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_successful_result(task_id: str) -> tuple[Path, dict]:
    base = RUNS_DIR / task_id
    if not base.exists():
        raise FileNotFoundError(f"no runs found for task: {task_id}")

    for run_dir in sorted((path for path in base.iterdir() if path.is_dir()), reverse=True):
        result_path = run_dir / "result.json"
        if not result_path.exists():
            continue
        result = load_json(result_path)
        if result.get("status") == "done":
            return run_dir, result

    raise FileNotFoundError(f"no successful result.json found for task: {task_id}")


def build_checkpoint(audit_task_id: str, review_task_id: str) -> dict:
    audit_run_dir, audit_result = latest_successful_result(audit_task_id)
    review_run_dir, review_result = latest_successful_result(review_task_id)

    forbidden_capabilities_found = bool(audit_result.get("forbidden_capabilities_found")) or bool(
        review_result.get("forbidden_capabilities_found")
    )
    review_decision = review_result.get("review_decision", "warning")
    audit_readiness_decision = audit_result.get("readiness_decision", "warning")
    blocked_reasons_count = len(review_result.get("blocked_reasons", []))
    remaining_warnings_count = len(review_result.get("remaining_warnings", []))

    if review_decision == "blocked" or forbidden_capabilities_found:
        overall_status = "blocked"
    elif audit_readiness_decision == "warning" or review_decision == "warning":
        overall_status = "warning"
    elif audit_readiness_decision == "pass" and review_decision == "pass":
        overall_status = "pass"
    else:
        overall_status = "warning"

    if overall_status == "blocked":
        next_recommended_task = "human_review"
    elif overall_status == "warning":
        next_recommended_task = review_result.get("next_recommended_task_type", "targeted_manual_review")
    else:
        next_recommended_task = audit_result.get("next_recommended_task_type", "next_safe_local_audit")

    return {
        "project": "polymarket-bot",
        "checkpoint_id": f"pm-checkpoint-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "source_tasks": {
            "audit": {
                "task_id": audit_task_id,
                "run_dir": str(audit_run_dir),
            },
            "review": {
                "task_id": review_task_id,
                "run_dir": str(review_run_dir),
            },
        },
        "audit_readiness_decision": audit_readiness_decision,
        "review_decision": review_decision,
        "forbidden_capabilities_found": forbidden_capabilities_found,
        "paper_only_confirmed": bool(audit_result.get("paper_only_confirmed")) and bool(review_result.get("paper_only_confirmed")),
        "local_data_only_confirmed": bool(audit_result.get("local_data_only_confirmed")) and bool(review_result.get("local_data_only_confirmed")),
        "blocked_reasons_count": blocked_reasons_count,
        "remaining_warnings_count": remaining_warnings_count,
        "overall_status": overall_status,
        "next_recommended_task": next_recommended_task,
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-task-id", default=DEFAULT_AUDIT_TASK_ID)
    parser.add_argument("--review-task-id", default=DEFAULT_REVIEW_TASK_ID)
    args = parser.parse_args()

    checkpoint = build_checkpoint(args.audit_task_id, args.review_task_id)
    write_json(STATE_PATH, checkpoint)
    print(
        json.dumps(
            {
                "checkpoint_path": str(STATE_PATH),
                "overall_status": checkpoint["overall_status"],
                "next_recommended_task": checkpoint["next_recommended_task"],
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
