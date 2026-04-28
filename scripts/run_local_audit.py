import argparse
import fnmatch
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
RISK_PATTERNS = {
    "network_risk": ["network", "requests", "aiohttp", "httpx", "websocket"],
    "api_risk": ["api", "requests", "httpx", "aiohttp"],
    "wallet_risk": ["wallet", "mnemonic", "seed phrase"],
    "private_key_risk": ["private_key", "private key", ".pem", ".key"],
    "execution_risk": ["execute", "execution", "subprocess", "os.system"],
    "live_trading_risk": ["order", "trade", "live", "signing"],
    "dependency_risk": ["requests", "aiohttp", "httpx", "websocket", "web3", "ccxt"],
}
MAX_CATEGORY_MATCHES = 5
ACTIVE_CODE_CATEGORIES = {"wallet_risk", "private_key_risk", "execution_risk", "live_trading_risk"}
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
    ".ini",
    ".cfg",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sh",
}


def classify_file_role(rel_path: str) -> str:
    normalized = rel_path.replace("/", "\\").lower()
    parts = normalized.split("\\")
    name = Path(normalized).name

    if "tests" in parts or name.startswith("test_") or name.endswith("_test.py"):
        return "test"
    if "docs" in parts or Path(normalized).suffix == ".md":
        return "docs"
    if parts and parts[0] in {"data", "runs", "artifacts"} or "artifact" in normalized or name.startswith("tmp_"):
        return "artifact"
    if Path(normalized).suffix in {".toml", ".yaml", ".yml", ".json", ".ini", ".cfg"}:
        return "config"
    if "src" in parts or Path(normalized).suffix in {".py", ".js", ".ts", ".tsx", ".jsx", ".sh"}:
        return "source"
    return "unknown"


def classify_risk_context(file_role: str) -> str:
    return {
        "source": "active_code",
        "test": "test_only",
        "docs": "docs_only",
        "config": "config_only",
        "artifact": "artifact_only",
        "unknown": "unknown",
    }.get(file_role, "unknown")


def should_skip(rel_path: str, forbidden_patterns: list[str]) -> bool:
    normalized = rel_path.replace("/", "\\")
    return any(fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(Path(normalized).name, pattern) for pattern in forbidden_patterns)


def iter_candidate_files(repo_path: Path, forbidden_patterns: list[str]):
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        rel_path = str(path.relative_to(repo_path))
        if should_skip(rel_path, forbidden_patterns):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        yield path, rel_path


def collect_matches(repo_path: Path, forbidden_patterns: list[str]) -> tuple[dict[str, list[dict]], int]:
    matches_by_category = {category: [] for category in RISK_PATTERNS}
    scanned_files = 0

    for path, rel_path in iter_candidate_files(repo_path, forbidden_patterns):
        scanned_files += 1
        file_role = classify_file_role(rel_path)
        risk_context = classify_risk_context(file_role)
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for line_no, line in enumerate(content.splitlines(), start=1):
            line_lower = line.lower()
            for category, terms in RISK_PATTERNS.items():
                if len(matches_by_category[category]) >= MAX_CATEGORY_MATCHES:
                    continue
                for term in terms:
                    if term in line_lower:
                        matches_by_category[category].append(
                            {
                                "path": rel_path,
                                "line": line_no,
                                "term": term,
                                "snippet": line.strip()[:160],
                                "file_role": file_role,
                                "risk_context": risk_context,
                            }
                        )
                        break

    return matches_by_category, scanned_files


def build_category(category_name: str, matches: list[dict]) -> dict:
    status = "clear"
    if matches:
        if category_name in ACTIVE_CODE_CATEGORIES and any(match["risk_context"] == "active_code" for match in matches):
            status = "blocked"
        else:
            status = "warning"
    return {
        "status": status,
        "matches_count": len(matches),
        "sample_matches": matches[:MAX_CATEGORY_MATCHES],
    }


def build_result(task: dict, scanned_files: int, matches_by_category: dict[str, list[dict]]) -> dict:
    total_matches = sum(len(matches) for matches in matches_by_category.values())
    summary = f"Local audit scanned {scanned_files} files and found {total_matches} categorized matches."
    categories = {
        category: build_category(category, matches_by_category[category])
        for category in RISK_PATTERNS
    }
    forbidden_capabilities_found = any(
        categories[category]["status"] == "blocked" for category in categories
    )
    if forbidden_capabilities_found:
        readiness_decision = "blocked"
    elif any(details["status"] == "warning" for details in categories.values()):
        readiness_decision = "warning"
    else:
        readiness_decision = "pass"

    next_recommended_task_type = {
        "blocked": "human_review",
        "warning": "targeted_manual_review",
        "pass": "next_safe_local_audit",
    }[readiness_decision]
    paper_only_confirmed = not forbidden_capabilities_found and categories["live_trading_risk"]["status"] != "blocked"
    local_data_only_confirmed = categories["network_risk"]["status"] != "blocked" and categories["api_risk"]["status"] != "blocked"
    risks = [
        f"{category}:{details['status']}:{details['matches_count']}"
        for category, details in categories.items()
        if details["matches_count"] > 0
    ][:5]
    next_tasks = []
    if total_matches:
        next_tasks.append("Review flagged files to confirm whether matches indicate real execution or credential exposure risks.")

    result = {
        "task_id": task["task_id"],
        "status": "done",
        "summary": summary,
        "files_changed": [],
        "commands_run": ["local_read_only_audit_scan"],
        "tests": {
            "status": "not_run",
            "commands": [],
            "failures": [],
        },
        "risks": risks,
        "next_tasks": next_tasks,
        "needs_human": False,
        "handoff": f"Scanned local files only under {task['repo_path']}; no network access or repository modifications were performed.",
        "paper_only_confirmed": paper_only_confirmed,
        "local_data_only_confirmed": local_data_only_confirmed,
        "forbidden_capabilities_found": forbidden_capabilities_found,
        "readiness_decision": readiness_decision,
        "next_recommended_task_type": next_recommended_task_type,
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

    repo_path = Path(task["repo_path"])
    _, run_dir = create_run_dir(task["task_id"])
    result_path = run_dir / "result.json"
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    metadata_path = run_dir / "metadata.json"
    prompt_path = run_dir / "prompt.txt"
    prompt_path.write_text(task["objective"] + "\n", encoding="utf-8")

    if not repo_path.exists():
        result = {
            "task_id": task["task_id"],
            "status": "failed",
            "summary": "Local audit repo path does not exist.",
            "files_changed": [],
            "commands_run": ["local_read_only_audit_scan"],
            "tests": {"status": "not_run", "commands": [], "failures": []},
            "risks": [],
            "next_tasks": [],
            "needs_human": False,
            "handoff": f"Configured repo_path was not found: {task['repo_path']}",
            "paper_only_confirmed": False,
            "local_data_only_confirmed": False,
            "forbidden_capabilities_found": False,
            "readiness_decision": "pass",
            "next_recommended_task_type": "next_safe_local_audit",
            "network_risk": {"status": "clear", "matches_count": 0, "sample_matches": []},
            "api_risk": {"status": "clear", "matches_count": 0, "sample_matches": []},
            "wallet_risk": {"status": "clear", "matches_count": 0, "sample_matches": []},
            "private_key_risk": {"status": "clear", "matches_count": 0, "sample_matches": []},
            "execution_risk": {"status": "clear", "matches_count": 0, "sample_matches": []},
            "live_trading_risk": {"status": "clear", "matches_count": 0, "sample_matches": []},
            "dependency_risk": {"status": "clear", "matches_count": 0, "sample_matches": []},
        }
        matches_by_category = {category: [] for category in RISK_PATTERNS}
        scanned_files = 0
    else:
        matches_by_category, scanned_files = collect_matches(repo_path, task.get("forbidden_paths", []))
        result = build_result(task, scanned_files, matches_by_category)

    write_json(result_path, result)
    stdout_path.write_text(
        json.dumps(
            {
                "scanned_files": scanned_files,
                "categories": {
                    category: len(matches_by_category[category]) for category in RISK_PATTERNS
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    stderr_path.write_text("", encoding="utf-8")

    metadata = build_metadata(task["task_id"], False, task_path, run_dir)
    metadata["executor"] = "local_read_only_audit"
    metadata["result_schema"] = str(RESULT_SCHEMA_PATH)
    metadata["scanned_files"] = scanned_files
    metadata["category_counts"] = {
        category: len(matches_by_category[category]) for category in RISK_PATTERNS
    }
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
                "executor": "local_read_only_audit",
            }
        )
    )
    return 0 if validator_output["status"] == "valid" else 1


if __name__ == "__main__":
    sys.exit(main())
