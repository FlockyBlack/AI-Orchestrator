import argparse
import json
from pathlib import Path
import sys

from run_codex import TASK_SCHEMA_PATH, load_json, validate_task


ROOT = Path(__file__).resolve().parents[1]
READY_DIR = ROOT / "tasks" / "ready"

DEFAULT_TASK_ID = "PM-AUDIT-001"
DEFAULT_REPO_PATH = r"C:\Users\OpenC\Documents\Codex\2026-04-24-code-executor-openclaw-polymarket-research-paper"
DEFAULT_TITLE = "Polymarket paper-only safety audit"


def build_task(task_id: str, repo_path: str, title: str) -> dict:
    return {
        "task_id": task_id,
        "project": "polymarket-bot",
        "task_type": "read_only_audit",
        "type": "audit",
        "safety_level": "L1",
        "status": "ready",
        "repo_path": repo_path,
        "objective": (
            f"{title}. Perform a read-only paper-only audit of the local Polymarket repository. "
            "Do not use network access, API calls, wallets, private keys, live trading actions, "
            "or any file modifications. Return compact JSON only."
        ),
        "allowed_paths": [
            ".",
        ],
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
            "audit is limited to local repository inspection only",
            "no network access is used",
            "no API calls are made",
            "no wallet, private key, or credential files are accessed",
            "no live trading actions are attempted",
            "no files in the Polymarket repository are modified",
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
    parser.add_argument("--repo-path", default=DEFAULT_REPO_PATH)
    parser.add_argument("--title", default=DEFAULT_TITLE)
    args = parser.parse_args()

    task = build_task(args.task_id, args.repo_path, args.title)
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
                "task_id": args.task_id,
                "task_path": str(output_path),
                "status": "created",
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
