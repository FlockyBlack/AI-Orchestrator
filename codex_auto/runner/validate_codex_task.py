import json
import sys
from pathlib import Path

ALLOWED_MODES = {
    "CODEX_SAFE_IMPLEMENTATION",
    "FIXTURE_ONLY",
    "PAPER_ONLY",
    "DESIGN_ONLY",
    "READ_ONLY_VALIDATION",
    "DRY_RUN_ONLY",
}

REQUIRED_FIELDS = [
    "schema_version",
    "task_id",
    "created_at",
    "mode",
    "executor",
    "project_path",
    "prompt",
    "allowed_paths",
    "forbidden_paths",
    "forbidden_behaviors",
    "requires_human_approval",
    "approved_for_execution",
    "dry_run_default",
    "expected_result_shape",
    "safety_flags_required",
]

FORBIDDEN_PATH_PATTERNS = {
    "scripts/dispatcher.py": "dispatcher_path_forbidden",
    "scripts/run_codex.py": "run_codex_path_forbidden",
    "tasks/": "active_task_path_forbidden",
    "state/": "state_path_forbidden",
    "runs/": "runtime_result_path_forbidden",
    "runtime": "runtime_path_forbidden",
    "loop": "runtime_loop_path_forbidden",
    "checkpoint": "checkpoint_path_forbidden",
    "freeze": "freeze_record_path_forbidden",
    "result": "result_record_path_forbidden",
}

FORBIDDEN_TERMS = {
    "runtime wiring": "forbidden_term:runtime_wiring",
    "dispatcher": "forbidden_term:dispatcher",
    "run_codex": "forbidden_term:run_codex",
    "runtime loop": "forbidden_term:runtime_loop",
    "active task": "forbidden_term:active_task",
    "task ledger": "forbidden_term:task_ledger",
    "checkpoint": "forbidden_term:checkpoint",
    "freeze record": "forbidden_term:freeze_record",
    "result record": "forbidden_term:result_record",
    "network": "forbidden_term:network",
    "api": "forbidden_term:api",
    "wallet": "forbidden_term:wallet",
    "private key": "forbidden_term:private_key",
    "trading": "forbidden_term:trading",
    "real order": "forbidden_term:real_order",
    "live polymarket": "forbidden_term:live_polymarket",
    "source of truth": "forbidden_term:second_runtime_source",
    "rewrite accepted warning": "forbidden_term:hidden_warning_rewrite",
}

EXPECTED_SAFETY_FLAGS = {
    "runtime_changed",
    "dispatcher_touched",
    "run_codex_touched",
    "active_task_files_touched",
    "freeze_record_modified",
    "result_records_modified",
    "checkpoint_records_modified",
    "network_used",
    "api_used",
    "wallet_used",
    "private_key_used",
    "trading_used",
    "single_runtime_source_rule_preserved",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PROJECT_PATH = str(PROJECT_ROOT)


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _norm_path(value):
    return str(Path(value)).replace("\\", "/").lower()


def _is_within_forbidden(allowed_path, forbidden_path):
    allowed_norm = allowed_path.rstrip("/")
    forbidden_norm = forbidden_path.rstrip("/")
    return allowed_norm == forbidden_norm or allowed_norm.startswith(forbidden_norm + "/")


def _scan_text_for_terms(text, errors):
    lowered = str(text).lower()
    for term, code in FORBIDDEN_TERMS.items():
        if term in lowered:
            errors.append(code)


def _validate_paths(data, errors):
    allowed_paths = data.get("allowed_paths", [])
    forbidden_paths = data.get("forbidden_paths", [])

    if not isinstance(allowed_paths, list):
        errors.append("allowed_paths_must_be_list")
        allowed_paths = []
    if not isinstance(forbidden_paths, list):
        errors.append("forbidden_paths_must_be_list")
        forbidden_paths = []

    allowed_norm = [_norm_path(path) for path in allowed_paths]
    forbidden_norm = [_norm_path(path) for path in forbidden_paths]

    for candidate in allowed_norm:
        if candidate not in {"pm_bot/fixture_sandbox_example", "codex_auto/runs"} and not candidate.startswith("pm_bot/fixture_sandbox_example/") and not candidate.startswith("codex_auto/runs/"):
            errors.append(f"allowed_path_outside_safe_sandbox:{candidate}")
        for pattern, code in FORBIDDEN_PATH_PATTERNS.items():
            if pattern in candidate:
                errors.append(code)

    for candidate in forbidden_norm:
        for pattern, code in FORBIDDEN_PATH_PATTERNS.items():
            if pattern in candidate:
                break

    for candidate in allowed_norm:
        for forbidden in forbidden_norm:
            if _is_within_forbidden(candidate, forbidden):
                errors.append(f"allowed_path_overlaps_forbidden:{candidate}")


def _validate_task_data(data):
    errors = []
    warnings = []

    if not isinstance(data, dict):
        return {
            "status": "invalid",
            "task_id": None,
            "errors": ["task_must_be_object"],
            "warnings": warnings,
            "execution_allowed": False,
            "dry_run_default": False,
            "single_runtime_source_rule_preserved": False,
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")

    if errors:
        return {
            "status": "invalid",
            "task_id": data.get("task_id"),
            "errors": errors,
            "warnings": warnings,
            "execution_allowed": False,
            "dry_run_default": bool(data.get("dry_run_default")),
            "single_runtime_source_rule_preserved": False,
        }

    if data.get("schema_version") != "codex_task.v1":
        errors.append("schema_version_must_be_codex_task.v1")
    if data.get("mode") not in ALLOWED_MODES:
        errors.append("invalid_mode")
    if data.get("executor") != "codex":
        errors.append("executor_must_be_codex")

    provided_project = _norm_path(data.get("project_path", ""))
    expected_project = _norm_path(EXPECTED_PROJECT_PATH)
    if provided_project != expected_project:
        errors.append("project_path_mismatch")

    if data.get("requires_human_approval") is not True:
        errors.append("requires_human_approval_must_be_true")
    if data.get("approved_for_execution") is not False:
        errors.append("approved_for_execution_must_be_false_by_default")
    if data.get("dry_run_default") is not True:
        errors.append("dry_run_default_must_be_true")

    _validate_paths(data, errors)

    forbidden_behaviors = data.get("forbidden_behaviors", [])
    if not isinstance(forbidden_behaviors, list):
        errors.append("forbidden_behaviors_must_be_list")
        forbidden_behaviors = []

    prompt = data.get("prompt", "")
    _scan_text_for_terms(prompt, errors)

    for item in forbidden_behaviors:
        if not isinstance(item, str):
            errors.append("forbidden_behaviors_items_must_be_strings")
            continue
        if "allow " in item.lower():
            warnings.append(f"review_forbidden_behavior_text:{item}")

    expected_result_shape = data.get("expected_result_shape")
    if not isinstance(expected_result_shape, dict):
        errors.append("expected_result_shape_must_be_object")
    else:
        missing_shape = sorted({"schema_version", "status", "execution_mode", "safety_check"} - set(expected_result_shape.keys()))
        for key in missing_shape:
            errors.append(f"missing_expected_result_shape:{key}")

    safety_flags_required = data.get("safety_flags_required")
    if not isinstance(safety_flags_required, list):
        errors.append("safety_flags_required_must_be_list")
        safety_flags_required = []
    else:
        missing_flags = sorted(EXPECTED_SAFETY_FLAGS - set(safety_flags_required))
        for flag in missing_flags:
            warnings.append(f"missing_safety_flag:{flag}")

    single_runtime_source_rule_preserved = not any(
        code in errors
        for code in (
            "forbidden_term:runtime_wiring",
            "forbidden_term:dispatcher",
            "forbidden_term:run_codex",
            "forbidden_term:runtime_loop",
            "forbidden_term:active_task",
            "forbidden_term:checkpoint",
            "forbidden_term:freeze_record",
            "forbidden_term:result_record",
            "forbidden_term:second_runtime_source",
            "dispatcher_path_forbidden",
            "run_codex_path_forbidden",
            "active_task_path_forbidden",
            "state_path_forbidden",
            "runtime_result_path_forbidden",
            "runtime_path_forbidden",
            "runtime_loop_path_forbidden",
            "checkpoint_path_forbidden",
            "freeze_record_path_forbidden",
            "result_record_path_forbidden",
        )
    )

    return {
        "status": "valid" if not errors else "invalid",
        "task_id": data.get("task_id"),
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "execution_allowed": False,
        "dry_run_default": data.get("dry_run_default") is True,
        "single_runtime_source_rule_preserved": single_runtime_source_rule_preserved,
    }


def validate_file(path_str: str):
    path = Path(path_str)
    data = _load_json(path)
    result = _validate_task_data(data)
    result["file"] = str(path)
    ordered = {
        "status": result["status"],
        "file": result["file"],
        "task_id": result["task_id"],
        "errors": result["errors"],
        "warnings": result["warnings"],
        "execution_allowed": result["execution_allowed"],
        "dry_run_default": result["dry_run_default"],
        "single_runtime_source_rule_preserved": result["single_runtime_source_rule_preserved"],
    }
    return ordered


def main(argv):
    if len(argv) != 2:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "file": None,
                    "task_id": None,
                    "errors": ["usage: validate_codex_task.py <task.json>"],
                    "warnings": [],
                    "execution_allowed": False,
                    "dry_run_default": False,
                    "single_runtime_source_rule_preserved": False,
                },
                separators=(",", ":"),
            )
        )
        return 2

    result = validate_file(argv[1])
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
