import json
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "schema_version",
    "approval_id",
    "task_id",
    "approved_for_execution",
    "approved_by",
    "approved_at",
    "approval_reason",
    "allowed_paths",
    "forbidden_paths",
    "max_files_changed",
    "expected_tests",
    "rollback_plan",
    "validation_required_after_execution",
    "execution_scope",
    "expires_at",
    "safety_flags_required",
]

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

REQUIRED_FORBIDDEN_PATHS = {
    "scripts/dispatcher.py",
    "scripts/run_codex.py",
    "tasks/",
    "state/",
}

FORBIDDEN_PATH_PATTERNS = {
    "scripts/dispatcher.py": "dispatcher_path_forbidden",
    "scripts/run_codex.py": "run_codex_path_forbidden",
    "tasks/": "active_task_path_forbidden",
    "state/": "state_path_forbidden",
    "runtime": "runtime_path_forbidden",
    "loop": "runtime_loop_path_forbidden",
    "result": "result_record_path_forbidden",
    "freeze": "freeze_record_path_forbidden",
    "checkpoint": "checkpoint_path_forbidden",
}

FORBIDDEN_TERMS = {
    "runtime wiring": "forbidden_term:runtime_wiring",
    "dispatcher": "forbidden_term:dispatcher",
    "run_codex": "forbidden_term:run_codex",
    "execution integration": "forbidden_term:execution_integration",
    "active task": "forbidden_term:active_task",
    "network": "forbidden_term:network",
    "api": "forbidden_term:api",
    "wallet": "forbidden_term:wallet",
    "private key": "forbidden_term:private_key",
    "trading": "forbidden_term:trading",
    "real order": "forbidden_term:real_order",
    "live polymarket": "forbidden_term:live_polymarket",
    "source of truth": "forbidden_term:second_runtime_source",
}

ALLOWED_PATH_PREFIX = "codex_auto/runs/"


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _norm_path(value):
    return str(Path(value)).replace("\\", "/").lower()


def _scan_text_for_terms(text, errors):
    lowered = str(text).lower()
    for term, code in FORBIDDEN_TERMS.items():
        if term in lowered:
            errors.append(code)


def _is_under(base_path, candidate):
    base = base_path.rstrip("/")
    item = candidate.rstrip("/")
    return item == base or item.startswith(base + "/")


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
        if not _is_under(ALLOWED_PATH_PREFIX, candidate):
            errors.append(f"allowed_path_outside_approved_sandbox:{candidate}")
        for pattern, code in FORBIDDEN_PATH_PATTERNS.items():
            if pattern in candidate:
                errors.append(code)

    for required in REQUIRED_FORBIDDEN_PATHS:
        if _norm_path(required) not in forbidden_norm:
            errors.append(f"missing_forbidden_path:{required}")

    protected_terms_present = {
        "runtime": any("runtime" in item for item in forbidden_norm),
        "results": any("result" in item or item.endswith("runs") or item.endswith("runs/") for item in forbidden_norm),
        "freeze": any("freeze" in item for item in forbidden_norm),
        "checkpoint": any("checkpoint" in item for item in forbidden_norm),
    }
    for key, present in protected_terms_present.items():
        if not present:
            errors.append(f"missing_protected_surface:{key}")

    for candidate in allowed_norm:
        for forbidden in forbidden_norm:
            if forbidden and (candidate == forbidden.rstrip("/") or candidate.startswith(forbidden.rstrip("/") + "/")):
                errors.append(f"allowed_path_overlaps_forbidden:{candidate}")


def _validate_data(data):
    errors = []

    if not isinstance(data, dict):
        return {
            "status": "invalid",
            "task_id": None,
            "approval_id": None,
            "errors": ["approval_must_be_object"],
            "execution_approved": False,
            "runtime_wiring_allowed": False,
            "openclaw_validation_required": False,
            "single_runtime_source_rule_preserved": False,
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")

    if errors:
        return {
            "status": "invalid",
            "task_id": data.get("task_id"),
            "approval_id": data.get("approval_id"),
            "errors": errors,
            "execution_approved": False,
            "runtime_wiring_allowed": False,
            "openclaw_validation_required": False,
            "single_runtime_source_rule_preserved": False,
        }

    if data.get("schema_version") != "codex_execution_approval.v1":
        errors.append("schema_version_must_be_codex_execution_approval.v1")
    if data.get("approved_for_execution") is not True:
        errors.append("approved_for_execution_must_be_true")

    for key in ("approved_by", "approved_at", "approval_reason", "rollback_plan", "expires_at"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key}_must_be_non_empty")

    expected_tests = data.get("expected_tests")
    if not isinstance(expected_tests, list) or not expected_tests or not all(isinstance(item, str) and item.strip() for item in expected_tests):
        errors.append("expected_tests_must_be_non_empty_list")

    max_files_changed = data.get("max_files_changed")
    if not isinstance(max_files_changed, int) or max_files_changed <= 0:
        errors.append("max_files_changed_must_be_positive")
    elif max_files_changed > 3:
        errors.append("max_files_changed_exceeds_tiny_scope")

    if data.get("validation_required_after_execution") is not True:
        errors.append("validation_required_after_execution_must_be_true")

    _validate_paths(data, errors)

    execution_scope = data.get("execution_scope", "")
    if not isinstance(execution_scope, str) or not execution_scope.strip():
        errors.append("execution_scope_must_be_non_empty")
    else:
        _scan_text_for_terms(execution_scope, errors)

    _scan_text_for_terms(data.get("approval_reason", ""), errors)
    _scan_text_for_terms(data.get("rollback_plan", ""), errors)
    for test_command in expected_tests if isinstance(expected_tests, list) else []:
        _scan_text_for_terms(test_command, errors)

    safety_flags = data.get("safety_flags_required")
    if not isinstance(safety_flags, list):
        errors.append("safety_flags_required_must_be_list")
    else:
        missing_flags = sorted(EXPECTED_SAFETY_FLAGS - set(safety_flags))
        for flag in missing_flags:
            errors.append(f"missing_safety_flag:{flag}")

    single_runtime_source_rule_preserved = not any(
        code in errors
        for code in (
            "forbidden_term:runtime_wiring",
            "forbidden_term:dispatcher",
            "forbidden_term:run_codex",
            "forbidden_term:execution_integration",
            "forbidden_term:active_task",
            "forbidden_term:second_runtime_source",
            "dispatcher_path_forbidden",
            "run_codex_path_forbidden",
            "active_task_path_forbidden",
            "state_path_forbidden",
            "runtime_path_forbidden",
            "runtime_loop_path_forbidden",
            "result_record_path_forbidden",
            "freeze_record_path_forbidden",
            "checkpoint_path_forbidden",
        )
    )

    return {
        "status": "valid" if not errors else "invalid",
        "task_id": data.get("task_id"),
        "approval_id": data.get("approval_id"),
        "errors": sorted(set(errors)),
        "execution_approved": data.get("approved_for_execution") is True and not errors,
        "runtime_wiring_allowed": False,
        "openclaw_validation_required": data.get("validation_required_after_execution") is True,
        "single_runtime_source_rule_preserved": single_runtime_source_rule_preserved,
    }


def validate_file(path_str: str):
    path = Path(path_str)
    data = _load_json(path)
    result = _validate_data(data)
    result["file"] = str(path)
    ordered = {
        "status": result["status"],
        "file": result["file"],
        "task_id": result["task_id"],
        "approval_id": result["approval_id"],
        "errors": result["errors"],
        "execution_approved": result["execution_approved"],
        "runtime_wiring_allowed": result["runtime_wiring_allowed"],
        "openclaw_validation_required": result["openclaw_validation_required"],
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
                    "approval_id": None,
                    "errors": ["usage: validate_execution_approval.py <approval.json>"],
                    "execution_approved": False,
                    "runtime_wiring_allowed": False,
                    "openclaw_validation_required": False,
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
