import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_FIELDS = [
    "schema_version",
    "gate_id",
    "target_batch_id",
    "approval_request_ref",
    "approval_decision_ref",
    "approved_prompt_path",
    "command_preview_ref",
    "final_command_preview_path",
    "allowed_output_paths",
    "forbidden_paths",
    "expected_tests",
    "max_files_changed",
    "rollback_plan",
    "post_execution_flocky_validation_required",
    "execution_allowed_by_human",
    "execution_allowed_now",
    "external_codex_cli_allowed_now",
    "generated_prompt_execution_allowed_now",
    "runtime_wiring_allowed",
    "gate_status",
    "safety_check",
]
EXPECTED_ALLOWED_OUTPUT_PATHS = [
    "pm_bot/paper/",
    "pm_bot/paper/tests/",
    "pm_bot/risk/",
    "pm_bot/risk/tests/",
    "pm_bot/accounting/",
    "pm_bot/accounting/tests/",
    "pm_bot/reports/",
    "pm_bot/reports/tests/",
    "pm_bot/postmortem/",
    "pm_bot/postmortem/tests/",
    "pm_bot/audit/",
    "pm_bot/audit/tests/",
    "docs/PM_BOT_SAFE_BACKLOG_V2.json",
    "docs/PM_BOT_STAGE_SUMMARY_V2.md",
]
EXPECTED_FORBIDDEN_PATHS = [
    "scripts/dispatcher.py",
    "scripts/run_codex.py",
    "tasks/",
    "state/",
    "runtime/",
    "results/",
    "freeze/",
    "checkpoint/",
    "codex_auto/queue/",
    "codex_auto/approval/",
    "codex_auto/flocky_review/",
    "codex_auto/promotion/",
    "codex_auto/ready_promotion/",
    "codex_auto/external_cli/",
]
EXPECTED_TESTS = [
    "python -m pytest pm_bot\\paper\\tests pm_bot\\risk\\tests pm_bot\\accounting\\tests pm_bot\\reports\\tests pm_bot\\postmortem\\tests pm_bot\\audit\\tests -q",
    "local deterministic command checks for created modules",
    "safety scan for no network/API/wallet/private key/trading",
    "safety scan for no dispatcher/run_codex/runtime mutation",
]
FORBIDDEN_TERMS = {
    "api key": "forbidden_term:api_key",
    "secret": "forbidden_term:secret",
    "private key authorization": "forbidden_term:private_key",
    "private key enabled": "forbidden_term:private_key",
    "private key access": "forbidden_term:private_key",
    "live api": "forbidden_term:live_api",
    "live polymarket": "forbidden_term:live_polymarket",
    "real order": "forbidden_term:real_order",
    "real orders": "forbidden_term:real_order",
    "wallet authorization": "forbidden_term:wallet",
    "wallet enabled": "forbidden_term:wallet",
    "wallet access": "forbidden_term:wallet",
    "trading authorization": "forbidden_term:trading",
    "trading enabled": "forbidden_term:trading",
    "trading approved": "forbidden_term:trading",
    "runtime wiring allowed": "forbidden_term:runtime_wiring_allowed_text",
    "final flocky/openclaw done": "forbidden_term:final_done_claim",
    "final flocky done": "forbidden_term:final_done_claim",
    "final openclaw done": "forbidden_term:final_done_claim",
    "second runtime source": "forbidden_term:second_runtime_source",
    "source of truth": "forbidden_term:second_runtime_source",
}
REQUIRED_PREVIEW_MARKERS = [
    "MANUAL_RUN_ONLY",
    "DO_NOT_EXECUTE_FROM_THIS_SCRIPT",
    "REQUIRES_POST_EXECUTION_FLOCKY_VALIDATION",
    "NO_RUNTIME_WIRING_ALLOWED",
    "NO_WALLET_API_TRADING",
]
EXPECTED_PROMPT_REF = "codex_auto/prompts/PMBOT-BATCH-001.codex_prompt.txt"
EXPECTED_APPROVAL_REQUEST_REF = "codex_auto/external_cli/approval/PMBOT-BATCH-001.approval_request.json"
EXPECTED_APPROVAL_DECISION_REF = "codex_auto/external_cli/approval/PMBOT-BATCH-001.approval_decision.json"
EXPECTED_COMMAND_PREVIEW_REF = "codex_auto/external_cli/plans/PMBOT-BATCH-001.command_preview.txt"
EXPECTED_FINAL_COMMAND = "cmd /c \"codex exec --full-auto --skip-git-repo-check --cd C:\\Users\\OpenC\\Documents\\AI-Orchestrator -- < codex_auto\\prompts\\PMBOT-BATCH-001.codex_prompt.txt\""


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


def _validate_refs(data, errors):
    for field in (
        "approval_request_ref",
        "approval_decision_ref",
        "approved_prompt_path",
        "command_preview_ref",
        "final_command_preview_path",
    ):
        resolved = _resolve_project_path(data.get(field, ""))
        if resolved is None:
            errors.append("reference_escapes_project:" + field)
        elif not resolved.exists():
            errors.append("missing_ref:" + field)


def _scan_terms(value, errors):
    lowered = json.dumps(value, ensure_ascii=False).lower() if not isinstance(value, str) else value.lower()
    for term, code in FORBIDDEN_TERMS.items():
        if term in lowered:
            errors.append(code)
    boolean_markers = {
        "\"execution_allowed_now\": true": "execution_allowed_now_must_be_false",
        "\"external_codex_cli_allowed_now\": true": "external_codex_cli_allowed_now_must_be_false",
        "\"generated_prompt_execution_allowed_now\": true": "generated_prompt_execution_allowed_now_must_be_false",
        "\"runtime_wiring_allowed\": true": "runtime_wiring_allowed_must_be_false",
        "\"network_allowed\": true": "forbidden_term:network_enabled",
        "\"api_allowed\": true": "forbidden_term:api_enabled",
        "\"wallet_allowed\": true": "forbidden_term:wallet_enabled",
        "\"private_key_allowed\": true": "forbidden_term:private_key_enabled",
        "\"trading_allowed\": true": "forbidden_term:trading_enabled",
        "\"live_api_allowed\": true": "forbidden_term:live_api_enabled",
        "\"real_orders_allowed\": true": "forbidden_term:real_orders_enabled",
    }
    for marker, code in boolean_markers.items():
        if marker in lowered:
            errors.append(code)


def _validate_preview(data, errors):
    preview_path = _resolve_project_path(data.get("final_command_preview_path", ""))
    if preview_path is None or not preview_path.is_file():
        return
    preview_text = preview_path.read_text(encoding="utf-8")
    for marker in REQUIRED_PREVIEW_MARKERS:
        if marker not in preview_text:
            errors.append("missing_preview_marker:" + marker.lower())
    if EXPECTED_FINAL_COMMAND not in preview_text:
        errors.append("final_command_preview_missing_expected_command")
    if "--full-auto" not in preview_text:
        errors.append("final_command_preview_missing_full_auto")
    if "--skip-git-repo-check" not in preview_text:
        errors.append("final_command_preview_missing_skip_git_repo_check")
    _scan_terms(preview_text, errors)


def _validate_data(data, file_path: Path):
    errors = []
    if not isinstance(data, dict):
        return {
            "status": "invalid",
            "file": str(file_path),
            "gate_id": None,
            "errors": ["one_shot_gate_must_be_object"],
            "execution_allowed_now": False,
            "external_codex_cli_allowed_now": False,
            "generated_prompt_execution_allowed_now": False,
            "runtime_wiring_allowed": False,
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append("missing:" + field)
    if errors:
        return {
            "status": "invalid",
            "file": str(file_path),
            "gate_id": data.get("gate_id"),
            "errors": sorted(set(errors)),
            "execution_allowed_now": bool(data.get("execution_allowed_now")),
            "external_codex_cli_allowed_now": bool(data.get("external_codex_cli_allowed_now")),
            "generated_prompt_execution_allowed_now": bool(data.get("generated_prompt_execution_allowed_now")),
            "runtime_wiring_allowed": bool(data.get("runtime_wiring_allowed")),
        }

    if data.get("schema_version") != "one_shot_execution_gate.v1":
        errors.append("schema_version_must_be_one_shot_execution_gate.v1")
    if data.get("target_batch_id") != "PMBOT-BATCH-001":
        errors.append("target_batch_id_must_match_pmbot_batch_001")
    if data.get("approval_request_ref") != EXPECTED_APPROVAL_REQUEST_REF:
        errors.append("approval_request_ref_mismatch")
    if data.get("approval_decision_ref") != EXPECTED_APPROVAL_DECISION_REF:
        errors.append("approval_decision_ref_mismatch")
    if data.get("approved_prompt_path") != EXPECTED_PROMPT_REF:
        errors.append("approved_prompt_path_mismatch")
    if data.get("command_preview_ref") != EXPECTED_COMMAND_PREVIEW_REF:
        errors.append("command_preview_ref_mismatch")
    if data.get("execution_allowed_by_human") is not True:
        errors.append("execution_allowed_by_human_must_be_true")
    if data.get("execution_allowed_now") is not False:
        errors.append("execution_allowed_now_must_be_false")
    if data.get("external_codex_cli_allowed_now") is not False:
        errors.append("external_codex_cli_allowed_now_must_be_false")
    if data.get("generated_prompt_execution_allowed_now") is not False:
        errors.append("generated_prompt_execution_allowed_now_must_be_false")
    if data.get("runtime_wiring_allowed") is not False:
        errors.append("runtime_wiring_allowed_must_be_false")
    if data.get("gate_status") != "prepared_pending_manual_run":
        errors.append("gate_status_must_be_prepared_pending_manual_run")
    if data.get("post_execution_flocky_validation_required") is not True:
        errors.append("post_execution_flocky_validation_required_must_be_true")
    if data.get("allowed_output_paths") != EXPECTED_ALLOWED_OUTPUT_PATHS:
        errors.append("allowed_output_paths_must_match_approved_list")
    if data.get("forbidden_paths") != EXPECTED_FORBIDDEN_PATHS:
        errors.append("forbidden_paths_must_match_approved_list")
    if data.get("expected_tests") != EXPECTED_TESTS:
        errors.append("expected_tests_must_match_approved_list")
    if not isinstance(data.get("max_files_changed"), int) or data["max_files_changed"] <= 0:
        errors.append("max_files_changed_must_be_positive_integer")
    rollback_plan = data.get("rollback_plan")
    if not isinstance(rollback_plan, str) or not rollback_plan.strip():
        errors.append("rollback_plan_must_be_present")

    safety = data.get("safety_check")
    if not isinstance(safety, dict):
        errors.append("safety_check_must_be_object")
    else:
        required_safety = {
            "manual_run_only": True,
            "do_not_execute_from_this_script": True,
            "requires_final_human_confirmation": True,
            "post_execution_flocky_validation_required": True,
            "runtime_wiring_allowed": False,
            "network_allowed": False,
            "api_allowed": False,
            "wallet_allowed": False,
            "private_key_allowed": False,
            "trading_allowed": False,
            "live_api_allowed": False,
            "real_orders_allowed": False,
            "external_codex_cli_allowed_now": False,
            "generated_prompt_execution_allowed_now": False,
            "single_runtime_source_rule_preserved": True,
        }
        for key, expected in required_safety.items():
            if safety.get(key) is not expected:
                errors.append("safety_check_" + key + "_mismatch")
        _scan_terms(safety, errors)

    _validate_refs(data, errors)
    _validate_preview(data, errors)
    _scan_terms(data, errors)

    return {
        "status": "valid" if not errors else "invalid",
        "file": str(file_path),
        "gate_id": data.get("gate_id"),
        "errors": sorted(set(errors)),
        "execution_allowed_now": data.get("execution_allowed_now") is True,
        "external_codex_cli_allowed_now": data.get("external_codex_cli_allowed_now") is True,
        "generated_prompt_execution_allowed_now": data.get("generated_prompt_execution_allowed_now") is True,
        "runtime_wiring_allowed": data.get("runtime_wiring_allowed") is True,
    }


def validate_file(path_str: str):
    path = Path(path_str)
    resolved = path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    data = _load_json(resolved)
    return _validate_data(data, resolved)


def main(argv):
    if len(argv) != 2:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "file": None,
                    "gate_id": None,
                    "errors": ["usage: validate_one_shot_execution_gate.py <gate.json>"],
                    "execution_allowed_now": False,
                    "external_codex_cli_allowed_now": False,
                    "generated_prompt_execution_allowed_now": False,
                    "runtime_wiring_allowed": False,
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
