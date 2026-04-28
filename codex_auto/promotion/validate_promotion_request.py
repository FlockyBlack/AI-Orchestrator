import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_ROOT = PROJECT_ROOT / "codex_auto" / "tasks" / "candidates"
PROMPT_ROOT = PROJECT_ROOT / "codex_auto" / "prompts"

REQUIRED_FIELDS = [
    "schema_version",
    "promotion_request_id",
    "source_materialization_report",
    "candidate_task_refs",
    "prompt_pack_ref",
    "prompt_manifest_ref",
    "requested_next_state",
    "requested_by",
    "requested_at",
    "reason",
    "safety_summary",
    "requires_flocky_review",
    "requires_human_approval",
    "execution_allowed_now",
    "runtime_wiring_allowed",
    "external_codex_cli_allowed_now",
]

FORBIDDEN_TERMS = {
    "network usage": "forbidden_term:network",
    "api usage": "forbidden_term:api",
    "wallet usage": "forbidden_term:wallet",
    "private key": "forbidden_term:private_key",
    "trading behavior": "forbidden_term:trading",
    "real order": "forbidden_term:real_order",
    "final flocky/openclaw done": "forbidden_term:final_done_claim",
    "final flocky done": "forbidden_term:final_done_claim",
    "final openclaw done": "forbidden_term:final_done_claim",
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_relpath(value: str) -> str:
    return str(Path(value)).replace("\\", "/")


def _resolve_project_path(value: str):
    candidate = (PROJECT_ROOT / value).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None
    return candidate


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _scan_terms(value, errors):
    lowered = value.lower()
    for term, code in FORBIDDEN_TERMS.items():
        if term in lowered:
            errors.append(code)


def _validate_candidate_ref(candidate_ref: str, errors):
    resolved = _resolve_project_path(candidate_ref)
    if resolved is None:
        errors.append(f"reference_escapes_project:{candidate_ref}")
        return
    if not _is_under(resolved, CANDIDATE_ROOT):
        errors.append(f"candidate_ref_outside_candidates:{candidate_ref}")
        return
    if resolved.suffixes[-2:] != [".task", ".json"]:
        errors.append(f"candidate_ref_invalid_suffix:{candidate_ref}")
    if not resolved.exists():
        errors.append(f"missing_candidate_ref:{candidate_ref}")


def _validate_prompt_ref(prompt_ref: str, errors):
    resolved = _resolve_project_path(prompt_ref)
    if resolved is None:
        errors.append(f"reference_escapes_project:{prompt_ref}")
        return
    if not _is_under(resolved, PROMPT_ROOT):
        errors.append(f"prompt_ref_outside_prompts:{prompt_ref}")
        return
    if not resolved.exists():
        errors.append(f"missing_prompt_ref:{prompt_ref}")


def _validate_materialization_ref(report_ref: str, errors):
    resolved = _resolve_project_path(report_ref)
    if resolved is None:
        errors.append(f"reference_escapes_project:{report_ref}")
        return
    if not _is_under(resolved, CANDIDATE_ROOT):
        errors.append(f"materialization_ref_outside_candidates:{report_ref}")
        return
    if not resolved.exists():
        errors.append(f"missing_materialization_ref:{report_ref}")


def _validate_data(data):
    errors = []
    if not isinstance(data, dict):
        return {
            "status": "invalid",
            "promotion_request_id": None,
            "errors": ["promotion_request_must_be_object"],
            "requested_next_state": None,
            "execution_allowed_now": False,
            "runtime_wiring_allowed": False,
            "external_codex_cli_allowed_now": False,
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")
    if errors:
        return {
            "status": "invalid",
            "promotion_request_id": data.get("promotion_request_id"),
            "errors": sorted(set(errors)),
            "requested_next_state": data.get("requested_next_state"),
            "execution_allowed_now": bool(data.get("execution_allowed_now")),
            "runtime_wiring_allowed": bool(data.get("runtime_wiring_allowed")),
            "external_codex_cli_allowed_now": bool(data.get("external_codex_cli_allowed_now")),
        }

    if data.get("schema_version") != "promotion_request.v1":
        errors.append("schema_version_must_be_promotion_request.v1")
    if data.get("requested_next_state") != "promotion_review":
        errors.append("requested_next_state_must_be_promotion_review")
    if data.get("execution_allowed_now") is not False:
        errors.append("execution_allowed_now_must_be_false")
    if data.get("runtime_wiring_allowed") is not False:
        errors.append("runtime_wiring_allowed_must_be_false")
    if data.get("external_codex_cli_allowed_now") is not False:
        errors.append("external_codex_cli_allowed_now_must_be_false")
    if data.get("requires_flocky_review") is not True:
        errors.append("requires_flocky_review_must_be_true")
    if data.get("requires_human_approval") is not True:
        errors.append("requires_human_approval_must_be_true")

    if not isinstance(data.get("candidate_task_refs"), list) or len(data["candidate_task_refs"]) != 6:
        errors.append("candidate_task_refs_must_list_all_six_candidates")
    else:
        normalized = [_normalize_relpath(item) for item in data["candidate_task_refs"]]
        if len(set(normalized)) != len(normalized):
            errors.append("candidate_task_refs_must_be_unique")
        for candidate_ref in normalized:
            _validate_candidate_ref(candidate_ref, errors)

    _validate_materialization_ref(_normalize_relpath(data.get("source_materialization_report", "")), errors)
    _validate_prompt_ref(_normalize_relpath(data.get("prompt_pack_ref", "")), errors)
    _validate_prompt_ref(_normalize_relpath(data.get("prompt_manifest_ref", "")), errors)

    for key in ("promotion_request_id", "requested_by", "requested_at", "reason"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f"{key}_must_be_non_empty")

    if not isinstance(data.get("safety_summary"), dict):
        errors.append("safety_summary_must_be_object")
    else:
        safety = data["safety_summary"]
        for key in (
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
        ):
            if safety.get(key) is not False:
                errors.append(f"safety_summary_{key}_must_be_false")
        if safety.get("single_runtime_source_rule_preserved") is not True:
            errors.append("safety_summary_single_runtime_source_rule_preserved_must_be_true")

    for field in ("reason", "requested_by"):
        if isinstance(data.get(field), str):
            _scan_terms(data[field], errors)

    return {
        "status": "valid" if not errors else "invalid",
        "promotion_request_id": data.get("promotion_request_id"),
        "errors": sorted(set(errors)),
        "requested_next_state": data.get("requested_next_state"),
        "execution_allowed_now": data.get("execution_allowed_now") is True,
        "runtime_wiring_allowed": data.get("runtime_wiring_allowed") is True,
        "external_codex_cli_allowed_now": data.get("external_codex_cli_allowed_now") is True,
    }


def validate_file(path_str: str):
    path = Path(path_str)
    data = _load_json(path)
    result = _validate_data(data)
    result["file"] = str(path)
    ordered = {
        "status": result["status"],
        "file": result["file"],
        "promotion_request_id": result["promotion_request_id"],
        "errors": result["errors"],
        "requested_next_state": result["requested_next_state"],
        "execution_allowed_now": result["execution_allowed_now"],
        "runtime_wiring_allowed": result["runtime_wiring_allowed"],
        "external_codex_cli_allowed_now": result["external_codex_cli_allowed_now"],
    }
    return ordered


def main(argv):
    if len(argv) != 2:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "file": None,
                    "promotion_request_id": None,
                    "errors": ["usage: validate_promotion_request.py <promotion_request.json>"],
                    "requested_next_state": None,
                    "execution_allowed_now": False,
                    "runtime_wiring_allowed": False,
                    "external_codex_cli_allowed_now": False,
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
