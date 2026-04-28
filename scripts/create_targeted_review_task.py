import argparse
import json
from pathlib import Path
import sys

from run_codex import TASK_SCHEMA_PATH, load_json, validate_task


ROOT = Path(__file__).resolve().parents[1]
READY_DIR = ROOT / "tasks" / "ready"
RUNS_DIR = ROOT / "runs"

DEFAULT_SOURCE_TASK_ID = "PM-AUDIT-006"
DEFAULT_TASK_ID = "PM-REVIEW-001"
RISK_CATEGORY_SUFFIX = "_risk"


def latest_run_dir(task_id: str) -> Path:
    base = RUNS_DIR / task_id
    if not base.exists():
        raise FileNotFoundError(f"no runs found for source task: {task_id}")
    run_dirs = sorted(path for path in base.iterdir() if path.is_dir())
    if not run_dirs:
        raise FileNotFoundError(f"no run directories found for source task: {task_id}")
    return run_dirs[-1]


def extract_warning_categories(result: dict) -> dict[str, dict]:
    categories = {}
    for key, value in result.items():
        if not key.endswith(RISK_CATEGORY_SUFFIX):
            continue
        if not isinstance(value, dict):
            continue
        if value.get("status") != "warning":
            continue
        categories[key] = {
            "status": "warning",
            "matches_count": value.get("matches_count", 0),
            "sample_matches": value.get("sample_matches", []),
        }
    return categories


def build_task(task_id: str, source_task_id: str, source_result: dict, warning_categories: dict[str, dict]) -> dict:
    repo_path = source_result["handoff"].split("under ", 1)[1].split(";", 1)[0]
    review_payload = {
        "source_task_id": source_task_id,
        "readiness_decision": source_result.get("readiness_decision"),
        "next_recommended_task_type": source_result.get("next_recommended_task_type"),
        "warning_categories": warning_categories,
    }
    payload_text = json.dumps(review_payload, separators=(",", ":"), ensure_ascii=True)

    return {
        "task_id": task_id,
        "project": "polymarket-bot",
        "task_type": "targeted_manual_review",
        "type": "audit",
        "safety_level": "L1",
        "status": "ready",
        "repo_path": repo_path,
        "objective": (
            "Perform a read-only targeted local review using only the warning categories from the prior audit. "
            "No network, API calls, wallet/private key access, live trading, or repository modifications. "
            f"Review payload: {payload_text}"
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
            "only warning categories from the source audit are reviewed",
            "clear categories are excluded from the review payload",
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
    parser.add_argument("--source-task-id", default=DEFAULT_SOURCE_TASK_ID)
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    args = parser.parse_args()

    run_dir = latest_run_dir(args.source_task_id)
    result_path = run_dir / "result.json"
    source_result = load_json(result_path)
    warning_categories = extract_warning_categories(source_result)

    task = build_task(args.task_id, args.source_task_id, source_result, warning_categories)
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
                "source_task_id": args.source_task_id,
                "warning_categories": sorted(warning_categories.keys()),
                "validated": True,
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
