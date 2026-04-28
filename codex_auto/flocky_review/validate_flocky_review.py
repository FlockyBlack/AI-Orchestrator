import json
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "schema_version",
    "review_id",
    "queue_task_id",
    "codex_task_id",
    "reviewed_at",
    "reviewed_by",
    "source_result_path",
    "source_queue_state",
    "review_status",
    "validation_findings",
    "safety_check",
    "allowed_next_queue_state",
    "final_flocky_done_claimed",
    "runtime_wiring_allowed",
    "notes",
]

ALLOWED_REVIEW_STATUS = {"pass", "warning", "fail", "quarantine"}
ALLOWED_NEXT_STATES = {"done", "failed", "quarantine", "needs_flocky_review"}
FORBIDDEN_TERMS = {
    "final flocky done": "forbidden_term:final_flocky_done",
    "final openclaw done": "forbidden_term:final_openclaw_done",
    "runtime truth": "forbidden_term:runtime_truth",
    "source of truth": "forbidden_term:source_of_truth",
    "trading": "forbidden_term:trading",
    "wallet": "forbidden_term:wallet",
    "private key": "forbidden_term:private_key",
    "api": "forbidden_term:api",
    "runtime wiring": "forbidden_term:runtime_wiring",
    "dispatcher": "forbidden_term:dispatcher",
    "run_codex": "forbidden_term:run_codex",
}
REQUIRED_FALSE_FLAGS = {
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
    "external_codex_cli_invoked",
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _scan_text(value, errors):
    lowered = str(value).lower()
    for term, code in FORBIDDEN_TERMS.items():
        if term in lowered:
            errors.append(code)


def _validate_payload(data):
    errors = []

    if not isinstance(data, dict):
        return {
            "status": "invalid",
            "review_id": None,
            "queue_task_id": None,
            "codex_task_id": None,
            "errors": ["review_must_be_object"],
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")

    if errors:
        return {
            "status": "invalid",
            "review_id": data.get("review_id"),
            "queue_task_id": data.get("queue_task_id"),
            "codex_task_id": data.get("codex_task_id"),
            "errors": errors,
        }

    if data.get("schema_version") != "v1":
        errors.append("schema_version_must_be_v1")
    if data.get("review_status") not in ALLOWED_REVIEW_STATUS:
        errors.append("invalid_review_status")
    if data.get("allowed_next_queue_state") not in ALLOWED_NEXT_STATES:
        errors.append("invalid_allowed_next_queue_state")
    if data.get("final_flocky_done_claimed") is not False:
        errors.append("final_flocky_done_claimed_must_be_false")
    if data.get("runtime_wiring_allowed") is not False:
        errors.append("runtime_wiring_allowed_must_be_false")
    if data.get("source_queue_state") != "needs_flocky_review":
        errors.append("source_queue_state_must_be_needs_flocky_review")

    safety_check = data.get("safety_check")
    if not isinstance(safety_check, dict):
        errors.append("safety_check_must_be_object")
        safety_check = {}

    for key in REQUIRED_FALSE_FLAGS:
        if safety_check.get(key) is not False:
            errors.append(f"safety_check_{key}_must_be_false")
    if safety_check.get("single_runtime_source_rule_preserved") is not True:
        errors.append("single_runtime_source_rule_preserved_must_be_true")

    _scan_text(json.dumps(data.get("validation_findings", {}), ensure_ascii=False), errors)
    _scan_text(json.dumps(data.get("notes", []), ensure_ascii=False), errors)
    _scan_text(data.get("allowed_next_queue_state"), errors)

    return {
        "status": "valid" if not errors else "invalid",
        "review_id": data.get("review_id"),
        "queue_task_id": data.get("queue_task_id"),
        "codex_task_id": data.get("codex_task_id"),
        "errors": sorted(set(errors)),
    }


def validate_file(path_str: str):
    path = Path(path_str)
    result = _validate_payload(_load_json(path))
    result["file"] = str(path)
    return {
        "status": result["status"],
        "file": result["file"],
        "review_id": result["review_id"],
        "queue_task_id": result["queue_task_id"],
        "codex_task_id": result["codex_task_id"],
        "errors": result["errors"],
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "file": None, "review_id": None, "queue_task_id": None, "codex_task_id": None, "errors": ["usage: validate_flocky_review.py <review_record.json>"]}, separators=(",", ":")))
        return 2
    result = validate_file(argv[1])
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
