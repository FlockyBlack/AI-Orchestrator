import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import signal
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TASK_SCHEMA_PATH = ROOT / "schemas" / "task.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas" / "codex-result.schema.json"
VALIDATOR_PATH = ROOT / "scripts" / "validate_result.py"
DEFAULT_TIMEOUT_SECONDS = 120


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_type_matches(value, schema_type: str) -> bool:
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "object":
        return isinstance(value, dict)
    return True


def validate_task(task: dict, schema: dict) -> None:
    if not isinstance(task, dict):
        raise ValueError("task must be a JSON object")

    required = schema.get("required", [])
    properties = schema.get("properties", {})

    missing = [key for key in required if key not in task]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    if schema.get("additionalProperties") is False:
        extra = sorted(set(task.keys()) - set(properties.keys()))
        if extra:
            raise ValueError(f"unexpected fields: {', '.join(extra)}")

    for key, prop in properties.items():
        if key not in task:
            continue
        value = task[key]
        schema_type = prop.get("type")
        if schema_type and not schema_type_matches(value, schema_type):
            raise ValueError(f"field {key} has invalid type: expected {schema_type}")
        enum = prop.get("enum")
        if enum is not None and value not in enum:
            raise ValueError(f"field {key} must be one of: {', '.join(enum)}")
        items = prop.get("items")
        if schema_type == "array" and items and "type" in items:
            bad = [item for item in value if not schema_type_matches(item, items["type"])]
            if bad:
                raise ValueError(f"field {key} contains invalid array item types")


def build_prompt(task: dict) -> str:
    lines = [
        f"task_id: {task['task_id']}",
        *( [f"task_type: {task['task_type']}"] if 'task_type' in task else [] ),
        f"objective: {task['objective']}",
        f"safety_level: {task['safety_level']}",
        f"repo_path: {task['repo_path']}",
        "allowed_paths:",
    ]
    lines.extend(f"- {item}" for item in task["allowed_paths"])
    lines.append("forbidden_paths:")
    lines.extend(f"- {item}" for item in task["forbidden_paths"])
    lines.append("success_criteria:")
    lines.extend(f"- {item}" for item in task["success_criteria"])
    lines.extend(
        [
            f"return_format: ONLY JSON matching {RESULT_SCHEMA_PATH.as_posix()}",
            "constraints:",
            "- avoid secrets, .env, wallets, tokens, private keys",
            "- avoid long human reports",
            "- keep output compact and machine-oriented",
        ]
    )
    return "\n".join(lines) + "\n"


def build_placeholder_result(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "status": "needs_human",
        "summary": "dry_run_only",
        "files_changed": [],
        "commands_run": [],
        "tests": {
            "status": "not_run",
            "commands": [],
            "failures": [],
        },
        "risks": [],
        "next_tasks": [],
        "needs_human": True,
        "handoff": "Dry run created prompt only; codex exec not launched.",
        "paper_only_confirmed": False,
        "local_data_only_confirmed": False,
        "forbidden_capabilities_found": False,
        "readiness_decision": "blocked",
        "next_recommended_task_type": "human_review",
        "review_decision": "blocked",
        "blocked_reasons": ["dry_run_only"],
        "remaining_warnings": [],
    }


def build_failure_result(task_id: str, summary: str, handoff: str, task_type: str | None = None) -> dict:
    blocked_reason = "local_runner_failed_or_empty_output" if task_type in {"read_only_audit", "targeted_manual_review"} else "execution_failed"
    result = {
        "task_id": task_id,
        "status": "failed",
        "summary": summary,
        "files_changed": [],
        "commands_run": [],
        "tests": {
            "status": "not_run",
            "commands": [],
            "failures": [],
        },
        "risks": [],
        "next_tasks": [],
        "needs_human": False,
        "handoff": handoff,
        "paper_only_confirmed": False,
        "local_data_only_confirmed": False,
        "forbidden_capabilities_found": False,
        "readiness_decision": "blocked",
        "next_recommended_task_type": "human_review",
        "review_decision": "blocked",
        "blocked_reasons": [blocked_reason],
        "remaining_warnings": [],
    }
    return result


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def create_run_dir(task_id: str) -> tuple[str, Path]:
    for _ in range(100):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run_dir = ROOT / "runs" / task_id / timestamp
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
            return timestamp, run_dir
        except FileExistsError:
            continue
    raise RuntimeError("could not allocate unique run directory")


def build_metadata(task_id: str, dry_run: bool, task_path: Path, run_dir: Path) -> dict:
    return {
        "task_id": task_id,
        "dry_run": dry_run,
        "created_at": run_dir.name,
        "task_path": str(task_path),
        "run_dir": str(run_dir),
    }


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


def resolve_codex_executable() -> str:
    for candidate in ("codex.cmd", "codex.exe", "codex"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError("could not resolve a launchable codex executable")


def append_text(path: Path, text: str) -> None:
    path.open("a", encoding="utf-8").write(text)


def kill_process_tree(process: subprocess.Popen) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        return
    try:
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)
    except Exception:
        process.kill()


def run_codex_attempt(command: list[str], prompt_text: str, timeout_seconds: int) -> tuple[subprocess.Popen | None, str, str, bool]:
    creationflags = 0
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creationflags,
    )

    try:
        stdout, stderr = process.communicate(input=prompt_text, timeout=timeout_seconds)
        return process, stdout, stderr, False
    except subprocess.TimeoutExpired as exc:
        kill_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except Exception:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
        return process, stdout, stderr, True


def run_codex_execute(task: dict, task_path: Path, prompt_text: str, run_dir: Path, timeout_seconds: int) -> dict:
    result_path = run_dir / "result.json"
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    metadata_path = run_dir / "metadata.json"

    codex_executable = resolve_codex_executable()
    command = [
        codex_executable,
        "exec",
        "--cd",
        task["repo_path"],
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--output-schema",
        str(RESULT_SCHEMA_PATH),
        "--output-last-message",
        str(result_path),
        "--color",
        "never",
        "-",
    ]

    attempts = []
    validator_output = None

    for attempt in range(1, 3):
        process, stdout_text, stderr_text, timed_out = run_codex_attempt(command, prompt_text, timeout_seconds)

        stdout_chunk = f"=== attempt {attempt} ===\n{stdout_text}"
        stderr_chunk = f"=== attempt {attempt} ===\n{stderr_text}"
        append_text(stdout_path, stdout_chunk)
        append_text(stderr_path, stderr_chunk)

        attempt_info = {
            "attempt": attempt,
            "returncode": None if process is None else process.returncode,
            "timed_out": timed_out,
            "result_exists": result_path.exists(),
        }

        if timed_out and not result_path.exists():
            write_json(
                result_path,
                build_failure_result(
                    task["task_id"],
                    "codex execution timed out",
                    f"codex exec exceeded {timeout_seconds} seconds and was terminated.",
                ),
            )
            append_text(stderr_path, f"\ntimeout: codex exec exceeded {timeout_seconds} seconds and was terminated.\n")

        if result_path.exists():
            try:
                validator_output = run_validator(result_path)
                attempt_info["validator_status"] = validator_output.get("status")
                attempt_info["validator_errors"] = validator_output.get("errors", [])
            except json.JSONDecodeError:
                validator_output = {
                    "status": "invalid",
                    "result_path": str(result_path),
                    "errors": ["validator output was not valid JSON"],
                }
                attempt_info["validator_status"] = "invalid"
                attempt_info["validator_errors"] = validator_output["errors"]
            except ValueError as exc:
                validator_output = {
                    "status": "invalid",
                    "result_path": str(result_path),
                    "errors": [str(exc)],
                }
                attempt_info["validator_status"] = "invalid"
                attempt_info["validator_errors"] = validator_output["errors"]
        else:
            validator_output = {
                "status": "invalid",
                "result_path": str(result_path),
                "errors": ["result.json was not created"],
            }
            attempt_info["validator_status"] = "invalid"
            attempt_info["validator_errors"] = validator_output["errors"]

        attempts.append(attempt_info)
        if timed_out or validator_output["status"] == "valid":
            break

    metadata = build_metadata(task["task_id"], False, task_path, run_dir)
    metadata["codex_executable"] = codex_executable
    metadata["timeout_seconds"] = timeout_seconds
    metadata["execute_command"] = f"{Path(codex_executable).name} exec --cd <repo_path> --skip-git-repo-check --sandbox read-only --output-schema <schema> --output-last-message <result.json> --color never -"
    metadata["attempts"] = attempts
    write_json(metadata_path, metadata)

    return {
        "task_id": task["task_id"],
        "dry_run": False,
        "run_dir": str(run_dir),
        "result_path": str(result_path),
        "metadata_path": str(metadata_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "validator": validator_output,
        "execute_command": "python scripts/run_codex.py --task tasks/ready/AI-ORCH-SMOKE-001.task.json --execute",
        "codex_executable": codex_executable,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    if args.dry_run == args.execute:
        raise SystemExit("choose exactly one of --dry-run or --execute")

    task_path = Path(args.task)
    if not task_path.is_absolute():
        task_path = (ROOT / task_path).resolve()

    task = load_json(task_path)
    task_schema = load_json(TASK_SCHEMA_PATH)
    validate_task(task, task_schema)
    prompt_text = build_prompt(task)
    _, run_dir = create_run_dir(task["task_id"])

    prompt_path = run_dir / "prompt.txt"
    prompt_path.write_text(prompt_text, encoding="utf-8")

    if args.dry_run:
        placeholder_path = run_dir / "result.placeholder.json"
        write_json(placeholder_path, build_placeholder_result(task["task_id"]))

        metadata = build_metadata(task["task_id"], True, task_path, run_dir)
        metadata_path = run_dir / "metadata.json"
        write_json(metadata_path, metadata)

        print(
            json.dumps(
                {
                    "task_id": task["task_id"],
                    "dry_run": True,
                    "run_dir": str(run_dir),
                    "prompt_path": str(prompt_path),
                    "result_placeholder_path": str(placeholder_path),
                    "metadata_path": str(metadata_path),
                }
            )
        )
        return 0

    if args.timeout_seconds < 1:
        raise SystemExit("--timeout-seconds must be >= 1")

    execution_output = run_codex_execute(task, task_path, prompt_text, run_dir, args.timeout_seconds)
    print(json.dumps(execution_output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
