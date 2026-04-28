import json
import sys
from pathlib import Path

ALLOWED_STATES = {
    "ready",
    "running",
    "done",
    "failed",
    "needs_flocky_review",
    "quarantine",
}

REQUIRED_FIELDS = [
    "schema_version",
    "queue_task_id",
    "codex_task_id",
    "queue_state",
    "mode",
    "approved_for_execution",
    "approval_ref",
    "allowed_output",
    "max_files_changed",
    "flocky_validation_required",
    "runtime_wiring_allowed",
    "external_codex_cli_allowed",
    "network_allowed",
    "api_allowed",
    "wallet_allowed",
    "private_key_allowed",
    "trading_allowed",
    "allowed_paths",
    "forbidden_paths",
]

REQUIRED_FORBIDDEN_PATHS = {
    "scripts/dispatcher.py",
    "scripts/run_codex.py",
    "state/",
}

APPROVED_TINY_TASK_ID = "CODEX-AUTO-TINY-001"
APPROVED_TINY_APPROVAL_REF = "codex_auto/fixtures/approved_tiny_fixture_task.v1.json"
APPROVED_TINY_OUTPUT = "codex_auto/runs/CODEX-AUTO-TINY-001/fixture_output.json"
APPROVED_TINY_ALLOWED_PATH = "codex_auto/runs/CODEX-AUTO-TINY-001/"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _norm_path(value):
    return str(Path(value)).replace("\\", "/").lower()


def _is_under(base_path, candidate):
    base = base_path.rstrip("/")
    item = candidate.rstrip("/")
    return item == base or item.startswith(base + "/")


def _validate_payload(data):
    errors = []

    if not isinstance(data, dict):
        return {
            "status": "invalid",
            "queue_task_id": None,
            "codex_task_id": None,
            "queue_state": None,
            "errors": ["queue_task_must_be_object"],
            "flocky_validation_required": False,
            "runtime_wiring_allowed": False,
            "external_codex_cli_allowed": False,
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")

    if errors:
        return {
            "status": "invalid",
            "queue_task_id": data.get("queue_task_id"),
            "codex_task_id": data.get("codex_task_id"),
            "queue_state": data.get("queue_state"),
            "errors": errors,
            "flocky_validation_required": bool(data.get("flocky_validation_required")),
            "runtime_wiring_allowed": bool(data.get("runtime_wiring_allowed")),
            "external_codex_cli_allowed": bool(data.get("external_codex_cli_allowed")),
        }

    if data.get("schema_version") != "v1":
        errors.append("schema_version_must_be_v1")
    if data.get("queue_state") not in ALLOWED_STATES:
        errors.append("invalid_queue_state")
    if data.get("codex_task_id") != APPROVED_TINY_TASK_ID:
        errors.append("unsupported_codex_task_id")
    if data.get("approved_for_execution") is not True:
        errors.append("approved_for_execution_must_be_true")
    if data.get("flocky_validation_required") is not True:
        errors.append("flocky_validation_required_must_be_true")
    if data.get("runtime_wiring_allowed") is not False:
        errors.append("runtime_wiring_allowed_must_be_false")
    if data.get("external_codex_cli_allowed") is not False:
        errors.append("external_codex_cli_allowed_must_be_false")

    for flag_name in ("network_allowed", "api_allowed", "wallet_allowed", "private_key_allowed", "trading_allowed"):
        if data.get(flag_name) is not False:
            errors.append(f"{flag_name}_must_be_false")

    if data.get("allowed_output") != APPROVED_TINY_OUTPUT:
        errors.append("allowed_output_must_match_approved_tiny_output")
    if data.get("max_files_changed") != 1:
        errors.append("max_files_changed_must_be_one")
    if data.get("approval_ref") != APPROVED_TINY_APPROVAL_REF:
        errors.append("approval_ref_must_match_approved_tiny_fixture")

    approval_path = PROJECT_ROOT / data.get("approval_ref", "")
    if not approval_path.exists():
        errors.append("approval_ref_missing")

    allowed_paths = data.get("allowed_paths", [])
    forbidden_paths = data.get("forbidden_paths", [])
    if not isinstance(allowed_paths, list) or not allowed_paths:
        errors.append("allowed_paths_must_be_non_empty_list")
        allowed_paths = []
    if not isinstance(forbidden_paths, list) or not forbidden_paths:
        errors.append("forbidden_paths_must_be_non_empty_list")
        forbidden_paths = []

    normalized_allowed = [_norm_path(item) for item in allowed_paths]
    normalized_forbidden = [_norm_path(item) for item in forbidden_paths]
    normalized_output = _norm_path(data.get("allowed_output", ""))

    if normalized_allowed != [_norm_path(APPROVED_TINY_ALLOWED_PATH)]:
        errors.append("allowed_paths_must_match_approved_tiny_directory")
    if not any(_is_under(item, normalized_output) for item in normalized_allowed):
        errors.append("allowed_output_outside_allowed_paths")

    for required in REQUIRED_FORBIDDEN_PATHS:
        if _norm_path(required) not in normalized_forbidden:
            errors.append(f"missing_forbidden_path:{required}")

    protected_terms_present = {
        "runtime": any("runtime" in item for item in normalized_forbidden),
        "results": any("result" in item for item in normalized_forbidden),
        "freeze": any("freeze" in item for item in normalized_forbidden),
        "checkpoint": any("checkpoint" in item for item in normalized_forbidden),
    }
    for key, present in protected_terms_present.items():
        if not present:
            errors.append(f"missing_protected_surface:{key}")

    return {
        "status": "valid" if not errors else "invalid",
        "queue_task_id": data.get("queue_task_id"),
        "codex_task_id": data.get("codex_task_id"),
        "queue_state": data.get("queue_state"),
        "errors": sorted(set(errors)),
        "flocky_validation_required": data.get("flocky_validation_required") is True,
        "runtime_wiring_allowed": data.get("runtime_wiring_allowed") is True,
        "external_codex_cli_allowed": data.get("external_codex_cli_allowed") is True,
    }


def validate_file(path_str: str):
    path = Path(path_str)
    result = _validate_payload(_load_json(path))
    result["file"] = str(path)
    ordered = {
        "status": result["status"],
        "file": result["file"],
        "queue_task_id": result["queue_task_id"],
        "codex_task_id": result["codex_task_id"],
        "queue_state": result["queue_state"],
        "errors": result["errors"],
        "flocky_validation_required": result["flocky_validation_required"],
        "runtime_wiring_allowed": result["runtime_wiring_allowed"],
        "external_codex_cli_allowed": result["external_codex_cli_allowed"],
    }
    return ordered


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "file": None, "queue_task_id": None, "codex_task_id": None, "queue_state": None, "errors": ["usage: validate_queue_task.py <queue_task.json>"], "flocky_validation_required": False, "runtime_wiring_allowed": False, "external_codex_cli_allowed": False}, separators=(",", ":")))
        return 2
    result = validate_file(argv[1])
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
