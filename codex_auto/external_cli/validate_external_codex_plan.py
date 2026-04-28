import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_ROOT = PROJECT_ROOT / "codex_auto" / "prompts"
CANDIDATE_ROOT = PROJECT_ROOT / "codex_auto" / "tasks" / "candidates"

REQUIRED_FIELDS = [
    "schema_version",
    "plan_id",
    "created_at",
    "prompt_pack_ref",
    "prompt_manifest_ref",
    "candidate_task_refs",
    "command_preview",
    "execution_allowed_now",
    "external_codex_cli_allowed_now",
    "requires_human_approval_before_execution",
    "requires_flocky_review_before_execution",
    "expected_result_path",
    "expected_validation_after_execution",
    "allowed_paths",
    "forbidden_paths",
    "safety_check",
]

FORBIDDEN_TERMS = {
    "api key": "forbidden_term:api_key",
    "secret": "forbidden_term:secret",
    "wallet": "forbidden_term:wallet",
    "private key": "forbidden_term:private_key",
    "trading": "forbidden_term:trading",
    "live api": "forbidden_term:live_api",
    "final flocky/openclaw done": "forbidden_term:final_done_claim",
    "final flocky done": "forbidden_term:final_done_claim",
    "final openclaw done": "forbidden_term:final_done_claim",
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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
    lowered = json.dumps(value, ensure_ascii=False).lower() if not isinstance(value, str) else value.lower()
    for term, code in FORBIDDEN_TERMS.items():
        if term in lowered:
            errors.append(code)


def _validate_ref(value: str, root: Path, prefix: str, errors):
    resolved = _resolve_project_path(value)
    if resolved is None:
        errors.append(f"reference_escapes_project:{value}")
        return
    if not _is_under(resolved, root):
        errors.append(f"{prefix}_outside_allowed_root:{value}")
        return
    if not resolved.exists():
        errors.append(f"missing_{prefix}:{value}")


def _validate_data(data):
    errors = []
    if not isinstance(data, dict):
        return {
            "status": "invalid",
            "plan_id": None,
            "errors": ["external_codex_plan_must_be_object"],
            "execution_allowed_now": False,
            "external_codex_cli_allowed_now": False,
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")
    if errors:
        return {
            "status": "invalid",
            "plan_id": data.get("plan_id"),
            "errors": sorted(set(errors)),
            "execution_allowed_now": bool(data.get("execution_allowed_now")),
            "external_codex_cli_allowed_now": bool(data.get("external_codex_cli_allowed_now")),
        }

    if data.get("schema_version") != "external_codex_plan.v1":
        errors.append("schema_version_must_be_external_codex_plan.v1")
    if data.get("execution_allowed_now") is not False:
        errors.append("execution_allowed_now_must_be_false")
    if data.get("external_codex_cli_allowed_now") is not False:
        errors.append("external_codex_cli_allowed_now_must_be_false")
    if data.get("requires_human_approval_before_execution") is not True:
        errors.append("requires_human_approval_before_execution_must_be_true")
    if data.get("requires_flocky_review_before_execution") is not True:
        errors.append("requires_flocky_review_before_execution_must_be_true")

    _validate_ref(data.get("prompt_pack_ref", ""), PROMPT_ROOT, "prompt_pack_ref", errors)
    _validate_ref(data.get("prompt_manifest_ref", ""), PROMPT_ROOT, "prompt_manifest_ref", errors)

    if not isinstance(data.get("candidate_task_refs"), list) or not data["candidate_task_refs"]:
        errors.append("candidate_task_refs_must_be_non_empty_list")
    else:
        for candidate_ref in data["candidate_task_refs"]:
            _validate_ref(candidate_ref, CANDIDATE_ROOT, "candidate_task_ref", errors)

    command_preview = data.get("command_preview", "")
    if not isinstance(command_preview, str) or not command_preview.strip():
        errors.append("command_preview_must_be_non_empty")
    else:
        lowered_preview = command_preview.lower()
        if "preview_only" not in lowered_preview:
            errors.append("command_preview_missing_preview_only")
        if "do_not_execute_now" not in lowered_preview:
            errors.append("command_preview_missing_do_not_execute_now")

    if "runtime" in " ".join(data.get("forbidden_paths", [])).lower():
        pass
    else:
        errors.append("forbidden_paths_missing_runtime")

    safety = data.get("safety_check")
    if not isinstance(safety, dict):
        errors.append("safety_check_must_be_object")
    else:
        if safety.get("runtime_wiring_allowed") is not False:
            errors.append("runtime_wiring_allowed_must_be_false")
        if safety.get("preview_only") is not True:
            errors.append("preview_only_must_be_true")
        if safety.get("human_approval_required_before_execution") is not True:
            errors.append("safety_check_human_approval_must_be_true")
        if safety.get("flocky_review_required_before_execution") is not True:
            errors.append("safety_check_flocky_review_must_be_true")
        for key in ("network_used", "api_used", "wallet_used", "private_key_used", "trading_used"):
            if safety.get(key) is not False:
                errors.append(f"safety_check_{key}_must_be_false")
        if safety.get("single_runtime_source_rule_preserved") is not True:
            errors.append("single_runtime_source_rule_preserved_must_be_true")

    _scan_terms(command_preview, errors)

    return {
        "status": "valid" if not errors else "invalid",
        "plan_id": data.get("plan_id"),
        "errors": sorted(set(errors)),
        "execution_allowed_now": data.get("execution_allowed_now") is True,
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
        "plan_id": result["plan_id"],
        "errors": result["errors"],
        "execution_allowed_now": result["execution_allowed_now"],
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
                    "plan_id": None,
                    "errors": ["usage: validate_external_codex_plan.py <plan.json>"],
                    "execution_allowed_now": False,
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
