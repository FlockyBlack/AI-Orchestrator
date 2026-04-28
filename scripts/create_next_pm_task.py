import argparse
import json
from pathlib import Path
import sys

from run_codex import TASK_SCHEMA_PATH, load_json, validate_task


ROOT = Path(__file__).resolve().parents[1]
READY_DIR = ROOT / "tasks" / "ready"
DEFAULT_CHECKPOINT_PATH = ROOT / "state" / "pm_checkpoint.json"
DEFAULT_TASK_ID = "PM-REVIEW-002"
DEFAULT_REPO_PATH = r"C:\Users\OpenC\Documents\Codex\2026-04-24-code-executor-openclaw-polymarket-research-paper"


def build_review_task(task_id: str, checkpoint: dict) -> dict:
    payload = {
        "checkpoint_id": checkpoint["checkpoint_id"],
        "source_tasks": checkpoint["source_tasks"],
        "overall_status": checkpoint["overall_status"],
        "remaining_warnings_count": checkpoint.get("remaining_warnings_count", 0),
        "review_decision": checkpoint.get("review_decision"),
    }
    payload_text = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)

    return {
        "task_id": task_id,
        "project": "polymarket-bot",
        "task_type": "targeted_manual_review",
        "type": "audit",
        "safety_level": "L1",
        "status": "ready",
        "repo_path": DEFAULT_REPO_PATH,
        "objective": (
            "Perform a local targeted review only using the current Polymarket checkpoint context. "
            "No network, API calls, wallet/private key access, live trading, or repository modifications. "
            f"Checkpoint payload: {payload_text}"
        ),
        "allowed_paths": ["."],
        "forbidden_paths": [
            ".env",
            ".env.*",
            "wallet*",
            "*wallet*",
            "secrets*",
            "*secret*",
            "browser_profiles",
            "*.key",
            "*.pem",
            "*.p12",
            "*private*key*",
        ],
        "success_criteria": [
            "review is limited to local repository inspection only",
            "checkpoint_id and source_tasks are referenced",
            "remaining warnings status/count is included in the payload",
            "no network access is used",
            "no API calls are made",
            "no wallet, private key, or credential files are accessed",
            "no live trading actions are attempted",
            "result is compact JSON only",
        ],
        "model_tier": "mini",
        "reasoning": "low",
        "max_report_chars": 1200,
        "requires_approval": False,
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--checkpoint-path", default=str(DEFAULT_CHECKPOINT_PATH))
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint_path)
    if not checkpoint_path.is_absolute():
        checkpoint_path = (ROOT / checkpoint_path).resolve()

    checkpoint = load_json(checkpoint_path)

    if checkpoint.get("overall_status") == "blocked":
        print(
            json.dumps(
                {
                    "status": "needs_human",
                    "checkpoint_path": str(checkpoint_path),
                    "reason": "blocked checkpoint prevents automatic task creation",
                    "blocked_checkpoint_respected": True,
                },
                separators=(",", ":"),
            )
        )
        return 0

    if checkpoint.get("next_recommended_task") != "targeted_manual_review":
        raise SystemExit("checkpoint next_recommended_task is not targeted_manual_review")

    task = build_review_task(args.task_id, checkpoint)
    schema = load_json(TASK_SCHEMA_PATH)
    validate_task(task, schema)

    READY_DIR.mkdir(parents=True, exist_ok=True)
    output_path = READY_DIR / f"{args.task_id}.task.json"
    if output_path.exists():
        raise SystemExit(f"task already exists: {output_path}")

    write_json(output_path, task)
    print(
        json.dumps(
            {
                "status": "done",
                "checkpoint_path": str(checkpoint_path),
                "task_id": args.task_id,
                "task_path": str(output_path),
                "validated": True,
                "blocked_checkpoint_respected": True,
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
