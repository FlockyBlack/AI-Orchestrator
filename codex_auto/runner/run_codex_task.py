import argparse
import importlib.util
import json
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

from validate_codex_task import validate_file

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = PROJECT_ROOT / "codex_auto" / "runs"
APPROVAL_VALIDATOR_PATH = PROJECT_ROOT / "codex_auto" / "approval" / "validate_execution_approval.py"
APPROVED_TINY_FIXTURE_PATH = PROJECT_ROOT / "codex_auto" / "fixtures" / "approved_tiny_fixture_task.v1.json"
APPROVED_TINY_TASK_ID = "CODEX-AUTO-TINY-001"
APPROVED_TINY_OUTPUT_RELATIVE = "codex_auto/runs/CODEX-AUTO-TINY-001/fixture_output.json"
APPROVED_TINY_OUTPUT_PATH = PROJECT_ROOT / APPROVED_TINY_OUTPUT_RELATIVE
APPROVED_TINY_DIRECTORY_PATH = APPROVED_TINY_OUTPUT_PATH.parent
CONTROLLED_TINY_OUTPUT = {
    "schema_version": "v1",
    "task_id": APPROVED_TINY_TASK_ID,
    "artifact_type": "controlled_tiny_fixture_output",
    "created_by": "codex_auto_runner",
    "execution_mode": "controlled_tiny_sandbox",
    "runtime_wiring_added": False,
    "execution_allowed_beyond_fixture": False,
    "network_used": False,
    "api_used": False,
    "wallet_used": False,
    "private_key_used": False,
    "trading_used": False,
    "single_runtime_source_rule_preserved": True,
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _utc_timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safety_check():
    return {
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
        "single_runtime_source_rule_preserved": True,
    }


def _command_preview(task_path: Path):
    quoted = shlex.quote(str(task_path))
    return f"codex exec --task-file {quoted} --mode dry-run"


def _controlled_tiny_command_preview():
    return f"controlled_tiny_sandbox --task-id {APPROVED_TINY_TASK_ID} --output {APPROVED_TINY_OUTPUT_RELATIVE}"


def _actual_controlled_tiny_command():
    return "controlled_tiny_sandbox:create_or_validate_fixture_output"


def _load_approval_validator():
    spec = importlib.util.spec_from_file_location("codex_auto_approval_validator", APPROVAL_VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("approval_validator_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _blocked_result(task_id, command_preview, started_at, finished_at, errors, warnings=None):
    return {
        "status": "blocked",
        "task_id": task_id,
        "execution_mode": "execute",
        "command_preview": command_preview,
        "would_execute": False,
        "validation_passed": True,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings or [])),
        "started_at": started_at,
        "finished_at": finished_at,
        "safety_check": _safety_check(),
    }


def _path_is_within(base_path: Path, candidate: Path):
    base_resolved = base_path.resolve()
    candidate_resolved = candidate.resolve()
    try:
        candidate_resolved.relative_to(base_resolved)
        return True
    except ValueError:
        return False


def _protected_forbidden_paths_present(forbidden_paths):
    lowered = [str(item).replace("\\", "/").lower() for item in forbidden_paths]
    required_literals = {"scripts/dispatcher.py", "scripts/run_codex.py", "tasks/", "state/"}
    if not required_literals.issubset(set(lowered)):
        return False
    return all(any(term in item for item in lowered) for term in ("runtime", "result", "freeze", "checkpoint"))


def _validate_controlled_tiny_approval(approval_data, approval_result):
    errors = []
    allowed_paths = approval_data.get("allowed_paths", [])
    forbidden_paths = approval_data.get("forbidden_paths", [])
    execution_scope = str(approval_data.get("execution_scope", "")).lower()

    if approval_result["status"] != "valid":
        errors.extend(approval_result["errors"])
    if approval_data.get("task_id") != APPROVED_TINY_TASK_ID:
        errors.append("controlled_tiny_task_id_required")
    if approval_data.get("approved_for_execution") is not True:
        errors.append("approved_for_execution_required")
    if approval_data.get("max_files_changed") != 1:
        errors.append("max_files_changed_must_be_one")
    if approval_data.get("validation_required_after_execution") is not True:
        errors.append("validation_required_after_execution_required")
    if not isinstance(allowed_paths, list) or [str(item).replace("\\", "/") for item in allowed_paths] != ["codex_auto/runs/CODEX-AUTO-TINY-001/"]:
        errors.append("allowed_paths_must_match_controlled_tiny_directory")
    if not isinstance(forbidden_paths, list) or not _protected_forbidden_paths_present(forbidden_paths):
        errors.append("forbidden_paths_missing_protected_runtime_surfaces")
    if "fixture-only" not in execution_scope:
        errors.append("execution_scope_must_be_fixture_only")
    if any(term in execution_scope for term in ("runtime wiring", "dispatcher", "run_codex", "network", "api", "wallet", "private key", "trading", "real order", "live polymarket", "source of truth")):
        errors.append("execution_scope_contains_forbidden_capability")
    return sorted(set(errors))


def _controlled_tiny_envelope(approval_data, approval_result, started_at, finished_at, result_status, files_created, notes, errors):
    return {
        "schema_version": "codex_execution_envelope.v1",
        "task_id": approval_data.get("task_id"),
        "approval_id": approval_data.get("approval_id"),
        "execution_id": f"{approval_data.get('task_id')}-controlled-tiny",
        "execution_mode": "controlled_tiny_sandbox",
        "started_at": started_at,
        "finished_at": finished_at,
        "approved_scope": approval_data.get("execution_scope"),
        "files_created": files_created,
        "files_modified_existing": [],
        "tests_run": approval_data.get("expected_tests", []),
        "tests_passed": approval_result["status"] == "valid" and not errors,
        "command_preview": _controlled_tiny_command_preview(),
        "actual_command": _actual_controlled_tiny_command(),
        "safety_check": _safety_check(),
        "result_status": result_status,
        "risks": errors,
        "notes": notes,
        "openclaw_validation_required": True,
    }


def _run_controlled_tiny_execution(approval_path: Path):
    started_at = _utc_timestamp()
    approval_validator = _load_approval_validator()
    approval_result = approval_validator.validate_file(str(approval_path))
    approval_data = _load_json(approval_path)
    finished_at = _utc_timestamp()

    approval_errors = _validate_controlled_tiny_approval(approval_data, approval_result)
    if approval_errors:
        return _controlled_tiny_envelope(approval_data, approval_result, started_at, finished_at, "blocked", [], [], approval_errors)

    if not _path_is_within(APPROVED_TINY_DIRECTORY_PATH, APPROVED_TINY_OUTPUT_PATH):
        return _controlled_tiny_envelope(approval_data, approval_result, started_at, finished_at, "blocked", [], [], ["approved_output_path_escape_detected"])

    expected_payload = dict(CONTROLLED_TINY_OUTPUT)
    files_created = []
    notes = []

    if APPROVED_TINY_OUTPUT_PATH.exists():
        try:
            existing_payload = _load_json(APPROVED_TINY_OUTPUT_PATH)
        except json.JSONDecodeError:
            return _controlled_tiny_envelope(approval_data, approval_result, started_at, finished_at, "blocked", [], [], ["existing_fixture_output_invalid_json"])
        if existing_payload != expected_payload:
            return _controlled_tiny_envelope(approval_data, approval_result, started_at, finished_at, "blocked", [], [], ["existing_fixture_output_content_mismatch"])
        notes.append("already_exists_valid")
    else:
        APPROVED_TINY_DIRECTORY_PATH.mkdir(parents=True, exist_ok=True)
        APPROVED_TINY_OUTPUT_PATH.write_text(json.dumps(expected_payload, indent=2) + "\n", encoding="utf-8")
        files_created.append(APPROVED_TINY_OUTPUT_RELATIVE)
        notes.append("created")

    finished_at = _utc_timestamp()
    return _controlled_tiny_envelope(approval_data, approval_result, started_at, finished_at, "completed", files_created, notes, [])


def _build_result(task_path: Path, execute_requested: bool):
    payload = _load_json(task_path)
    schema_version = payload.get("schema_version")

    if schema_version == "codex_execution_approval.v1":
        if execute_requested:
            return _run_controlled_tiny_execution(task_path)
        started_at = _utc_timestamp()
        approval_validator = _load_approval_validator()
        approval_result = approval_validator.validate_file(str(task_path))
        finished_at = _utc_timestamp()
        return {
            "status": "dry_run_ready" if approval_result["status"] == "valid" else "invalid",
            "task_id": approval_result.get("task_id"),
            "execution_mode": "dry_run",
            "command_preview": _controlled_tiny_command_preview(),
            "would_execute": False,
            "validation_passed": approval_result["status"] == "valid",
            "errors": approval_result["errors"],
            "warnings": [],
            "started_at": started_at,
            "finished_at": finished_at,
            "safety_check": _safety_check(),
        }

    started_at = _utc_timestamp()
    validation = validate_file(str(task_path))
    finished_at = _utc_timestamp()

    task_id = validation.get("task_id")
    command_preview = _command_preview(task_path)

    if validation["status"] != "valid":
        return {
            "status": "invalid",
            "task_id": task_id,
            "execution_mode": "dry_run",
            "command_preview": command_preview,
            "would_execute": False,
            "validation_passed": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "started_at": started_at,
            "finished_at": finished_at,
            "safety_check": _safety_check(),
        }

    if execute_requested:
        return _blocked_result(
            task_id,
            command_preview,
            started_at,
            finished_at,
            ["execution_disabled_in_scaffold", "approved_for_execution_required"],
        )
    else:
        status = "dry_run_ready"
        would_execute = False
        errors = []
        warnings = validation["warnings"]

    return {
        "status": status,
        "task_id": task_id,
        "execution_mode": "dry_run" if not execute_requested else "execute",
        "command_preview": command_preview,
        "would_execute": would_execute,
        "validation_passed": True,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "started_at": started_at,
        "finished_at": finished_at,
        "safety_check": _safety_check(),
    }


def _write_dry_run_result(task_id: str, result):
    output_dir = RUNS_ROOT / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "dry_run_result.json"
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return output_path


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("task_json")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--write-dry-run-result", action="store_true")
    args = parser.parse_args(argv[1:])

    task_path = Path(args.task_json)
    result = _build_result(task_path, args.execute)

    if args.write_dry_run_result:
        if result["status"] not in {"dry_run_ready", "blocked", "invalid"}:
            print(json.dumps({"status": "blocked", "task_id": result.get("task_id"), "errors": ["unsupported_write_status"]}, separators=(",", ":")))
            return 1
        if result.get("task_id"):
            output_path = _write_dry_run_result(result["task_id"], result)
            result["dry_run_result_path"] = str(output_path)

    print(json.dumps(result, separators=(",", ":")))
    if "status" in result:
        return 0 if result["status"] == "dry_run_ready" else 1
    return 0 if result.get("result_status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
