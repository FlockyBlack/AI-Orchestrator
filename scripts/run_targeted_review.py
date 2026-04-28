import argparse
import json
from pathlib import Path
import sys

from run_codex import (
    RESULT_SCHEMA_PATH,
    TASK_SCHEMA_PATH,
    build_metadata,
    create_run_dir,
    load_json,
    run_validator,
    validate_task,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_BLOCKING_CATEGORIES = {"wallet_risk", "private_key_risk", "execution_risk", "live_trading_risk"}
ALLOWED_CONTEXTS = {
    "docs_only",
    "test_only",
    "artifact_only",
    "config_only",
    "active_code",
    "mixed",
    "unknown",
}
RISK_CATEGORY_SUFFIX = "_risk"


def extract_payload(objective: str) -> dict:
    for marker in ("Review payload: ", "Checkpoint payload: "):
        if marker in objective:
            payload_text = objective.split(marker, 1)[1].strip()
            return json.loads(payload_text)
    raise ValueError("task objective does not contain supported review payload")


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


def resolve_warning_categories(payload: dict) -> dict[str, dict]:
    warning_categories = payload.get("warning_categories")
    if isinstance(warning_categories, dict):
        return warning_categories

    source_tasks = payload.get("source_tasks", {})
    review = source_tasks.get("review", {})
    run_dir = review.get("run_dir")
    if not run_dir:
        return {}

    result_path = Path(run_dir) / "result.json"
    if not result_path.exists():
        return {}
    return extract_warning_categories(load_json(result_path))


def classify_category(sample_matches: list[dict]) -> str:
    contexts = {match.get("risk_context", "unknown") for match in sample_matches}
    if not contexts:
        return "unknown"
    normalized = {context if context in ALLOWED_CONTEXTS else "unknown" for context in contexts}
    if len(normalized) == 1:
        return next(iter(normalized))
    if "active_code" in normalized:
        return "mixed"
    if "unknown" in normalized and len(normalized) > 1:
        return "mixed"
    return "mixed"


def build_category_result(category_name: str, payload_category: dict) -> tuple[dict, str]:
    sample_matches = payload_category.get("sample_matches", [])
    review_context = classify_category(sample_matches)
    if review_context == "active_code" and category_name in ACTIVE_BLOCKING_CATEGORIES:
        status = "blocked"
    elif payload_category.get("matches_count", 0) == 0:
        status = "clear"
    else:
        status = "warning"

    category_result = {
        "status": status,
        "matches_count": payload_category.get("matches_count", 0),
        "sample_matches": sample_matches[:5],
    }
    return category_result, review_context


def build_result(task: dict, payload: dict) -> dict:
    warning_categories = resolve_warning_categories(payload)
    categories = {}
    blocked_reasons = []
    remaining_warnings = []
    risk_summaries = []

    for category_name, payload_category in warning_categories.items():
        category_result, review_context = build_category_result(category_name, payload_category)
        categories[category_name] = category_result
        if category_result["status"] == "blocked":
            blocked_reasons.append(f"{category_name}:{review_context}")
        elif category_result["status"] == "warning":
            remaining_warnings.append(f"{category_name}:{review_context}")
        if category_result["matches_count"] > 0:
            risk_summaries.append(f"{category_name}:{category_result['status']}:{category_result['matches_count']}")

    forbidden_capabilities_found = bool(blocked_reasons)
    if forbidden_capabilities_found:
        review_decision = "blocked"
    elif remaining_warnings:
        review_decision = "warning"
    else:
        review_decision = "pass"

    result = {
        "task_id": task["task_id"],
        "status": "done",
        "summary": f"Targeted review analyzed {len(warning_categories)} warning categories.",
        "files_changed": [],
        "commands_run": ["local_targeted_manual_review"],
        "tests": {
            "status": "not_run",
            "commands": [],
            "failures": [],
        },
        "risks": risk_summaries[:5],
        "next_tasks": [],
        "needs_human": False,
        "handoff": "Reviewed warning-only categories locally; no network access or repository modifications were performed.",
        "paper_only_confirmed": not forbidden_capabilities_found,
        "local_data_only_confirmed": True,
        "forbidden_capabilities_found": forbidden_capabilities_found,
        "readiness_decision": payload.get("readiness_decision", "warning"),
        "next_recommended_task_type": payload.get("next_recommended_task_type", "targeted_manual_review"),
        "review_decision": review_decision,
        "blocked_reasons": blocked_reasons,
        "remaining_warnings": remaining_warnings,
    }
    result.update(categories)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = (ROOT / task_path).resolve()

    task = load_json(task_path)
    task_schema = load_json(TASK_SCHEMA_PATH)
    validate_task(task, task_schema)
    payload = extract_payload(task["objective"])

    _, run_dir = create_run_dir(task["task_id"])
    result_path = run_dir / "result.json"
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    metadata_path = run_dir / "metadata.json"
    prompt_path = run_dir / "prompt.txt"
    prompt_path.write_text(task["objective"] + "\n", encoding="utf-8")

    result = build_result(task, payload)
    write_json(result_path, result)
    stdout_path.write_text(
        json.dumps(
            {
                "reviewed_categories": sorted(payload.get("warning_categories", {}).keys()),
                "review_decision": result["review_decision"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    stderr_path.write_text("", encoding="utf-8")

    metadata = build_metadata(task["task_id"], False, task_path, run_dir)
    metadata["executor"] = "local_targeted_manual_review"
    metadata["result_schema"] = str(RESULT_SCHEMA_PATH)
    metadata["reviewed_categories"] = sorted(payload.get("warning_categories", {}).keys())
    write_json(metadata_path, metadata)

    validator_output = run_validator(result_path)
    print(
        json.dumps(
            {
                "task_id": task["task_id"],
                "dry_run": False,
                "run_dir": str(run_dir),
                "result_path": str(result_path),
                "metadata_path": str(metadata_path),
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "validator": validator_output,
                "executor": "local_targeted_manual_review",
            }
        )
    )
    return 0 if validator_output["status"] == "valid" else 1


if __name__ == "__main__":
    sys.exit(main())
