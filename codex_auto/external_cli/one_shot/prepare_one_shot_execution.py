import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ONE_SHOT_DIR = PROJECT_ROOT / "codex_auto" / "external_cli" / "one_shot"
APPROVAL_REQUEST_REF = "codex_auto/external_cli/approval/PMBOT-BATCH-001.approval_request.json"
APPROVAL_DECISION_REF = "codex_auto/external_cli/approval/PMBOT-BATCH-001.approval_decision.json"
PROMPT_REF = "codex_auto/prompts/PMBOT-BATCH-001.codex_prompt.txt"
COMMAND_PREVIEW_REF = "codex_auto/external_cli/plans/PMBOT-BATCH-001.command_preview.txt"
FINAL_COMMAND_PREVIEW_REF = "codex_auto/external_cli/one_shot/PMBOT-BATCH-001.final_command_preview.txt"
GATE_REF = "codex_auto/external_cli/one_shot/PMBOT-BATCH-001.one_shot_execution_gate.json"
GATE_ID = "PMBOT-BATCH-001-one-shot-execution-gate"
TARGET_BATCH_ID = "PMBOT-BATCH-001"
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
FORBIDDEN_TEXT_PATTERNS = (
    "\"execution_allowed_now\": true",
    "\"external_codex_cli_allowed_now\": true",
    "\"generated_prompt_execution_allowed_now\": true",
    "\"runtime_wiring_allowed\": true",
    "\"network_allowed\": true",
    "\"api_allowed\": true",
    "\"wallet_allowed\": true",
    "\"private_key_allowed\": true",
    "\"trading_allowed\": true",
    "\"live_api_allowed\": true",
    "\"real_orders_allowed\": true",
    "final flocky/openclaw done",
    "final flocky done",
    "final openclaw done",
    "second runtime source",
)


class PreparationError(Exception):
    pass


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _fail(message: str):
    raise PreparationError(message)


def _resolve_project_path(value: str):
    candidate = (PROJECT_ROOT / value).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None
    return candidate


def _ensure_file_exists(path_ref: str, label: str):
    resolved = _resolve_project_path(path_ref)
    if resolved is None or not resolved.is_file():
        _fail(label + " does not exist")


def _ensure_list_equals(actual, expected, label: str):
    if actual != expected:
        _fail(label + " does not match approved values")


def _ensure_non_empty_text(value, label: str):
    if not isinstance(value, str) or not value.strip():
        _fail(label + " must be present")


def _scan_forbidden_terms(data):
    serialized = json.dumps(data, ensure_ascii=False).lower()
    for pattern in FORBIDDEN_TEXT_PATTERNS:
        if pattern in serialized:
            _fail("forbidden content detected: " + pattern)


def _validate_request(request_data):
    if request_data.get("approval_request_id") != "PMBOT-BATCH-001-EXTERNAL-CODEX-APPROVAL":
        _fail("unexpected approval_request_id")
    if request_data.get("target_batch_id") != TARGET_BATCH_ID:
        _fail("approval request target_batch_id mismatch")
    if request_data.get("approved_prompt_path") != PROMPT_REF:
        _fail("approval request approved_prompt_path mismatch")
    if request_data.get("approved_command_preview_path") != COMMAND_PREVIEW_REF:
        _fail("approval request approved_command_preview_path mismatch")
    _ensure_list_equals(request_data.get("allowed_output_paths"), EXPECTED_ALLOWED_OUTPUT_PATHS, "allowed_output_paths")
    _ensure_list_equals(request_data.get("forbidden_paths"), EXPECTED_FORBIDDEN_PATHS, "forbidden_paths")
    _ensure_list_equals(request_data.get("expected_tests"), EXPECTED_TESTS, "expected_tests")
    _ensure_non_empty_text(request_data.get("rollback_plan"), "rollback_plan")
    if request_data.get("post_execution_flocky_validation_required") is not True:
        _fail("post_execution_flocky_validation_required must be true")
    if request_data.get("execution_allowed_now") is not False:
        _fail("execution_allowed_now must remain false")
    if request_data.get("external_codex_cli_allowed_now") is not False:
        _fail("external_codex_cli_allowed_now must remain false")
    if request_data.get("generated_prompt_execution_allowed_now") is not False:
        _fail("generated_prompt_execution_allowed_now must remain false")
    if request_data.get("runtime_wiring_allowed") is not False:
        _fail("runtime_wiring_allowed must remain false")


def _validate_decision(decision_data, request_data):
    if decision_data.get("target_batch_id") != TARGET_BATCH_ID:
        _fail("approval decision target_batch_id mismatch")
    if decision_data.get("approval_request_ref") != APPROVAL_REQUEST_REF:
        _fail("approval decision approval_request_ref mismatch")
    if decision_data.get("approved_for_external_codex_cli_execution") is not True:
        _fail("approved_for_external_codex_cli_execution must be true")
    if decision_data.get("approved_prompt_path") != request_data.get("approved_prompt_path"):
        _fail("approval decision approved_prompt_path mismatch")
    if decision_data.get("approved_command_preview_path") != request_data.get("approved_command_preview_path"):
        _fail("approval decision approved_command_preview_path mismatch")
    _ensure_list_equals(decision_data.get("allowed_output_paths"), request_data.get("allowed_output_paths"), "decision allowed_output_paths")
    _ensure_list_equals(decision_data.get("forbidden_paths"), request_data.get("forbidden_paths"), "decision forbidden_paths")
    _ensure_list_equals(decision_data.get("expected_tests"), request_data.get("expected_tests"), "decision expected_tests")
    if decision_data.get("post_execution_flocky_validation_required") is not True:
        _fail("decision post_execution_flocky_validation_required must be true")
    if decision_data.get("execution_allowed_now") is not False:
        _fail("decision execution_allowed_now must remain false")
    if decision_data.get("external_codex_cli_allowed_now") is not False:
        _fail("decision external_codex_cli_allowed_now must remain false")
    if decision_data.get("generated_prompt_execution_allowed_now") is not False:
        _fail("decision generated_prompt_execution_allowed_now must remain false")
    if decision_data.get("runtime_wiring_allowed") is not False:
        _fail("decision runtime_wiring_allowed must remain false")


def _build_final_command_preview():
    return "\n".join(
        [
            "MANUAL_RUN_ONLY",
            "DO_NOT_EXECUTE_FROM_THIS_SCRIPT",
            "REQUIRES_POST_EXECUTION_FLOCKY_VALIDATION",
            "NO_RUNTIME_WIRING_ALLOWED",
            "NO_WALLET_API_TRADING",
            "REQUIRES_FINAL_HUMAN_CONFIRMATION",
            "FINAL_COMMAND_PREVIEW:",
            "codex exec --cd C:\\Users\\OpenC\\Documents\\AI-Orchestrator -- < codex_auto\\prompts\\PMBOT-BATCH-001.codex_prompt.txt",
            "",
        ]
    )


def _build_gate(request_data):
    return {
        "schema_version": "one_shot_execution_gate.v1",
        "gate_id": GATE_ID,
        "target_batch_id": TARGET_BATCH_ID,
        "approval_request_ref": APPROVAL_REQUEST_REF,
        "approval_decision_ref": APPROVAL_DECISION_REF,
        "approved_prompt_path": PROMPT_REF,
        "command_preview_ref": COMMAND_PREVIEW_REF,
        "final_command_preview_path": FINAL_COMMAND_PREVIEW_REF,
        "allowed_output_paths": list(request_data["allowed_output_paths"]),
        "forbidden_paths": list(request_data["forbidden_paths"]),
        "expected_tests": list(request_data["expected_tests"]),
        "max_files_changed": request_data["max_files_changed"],
        "rollback_plan": request_data["rollback_plan"],
        "post_execution_flocky_validation_required": True,
        "execution_allowed_by_human": True,
        "execution_allowed_now": False,
        "external_codex_cli_allowed_now": False,
        "generated_prompt_execution_allowed_now": False,
        "runtime_wiring_allowed": False,
        "gate_status": "prepared_pending_manual_run",
        "safety_check": {
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
        },
    }


def prepare_one_shot_execution():
    request_path = PROJECT_ROOT / APPROVAL_REQUEST_REF
    decision_path = PROJECT_ROOT / APPROVAL_DECISION_REF
    prompt_path = PROJECT_ROOT / PROMPT_REF
    command_preview_path = PROJECT_ROOT / COMMAND_PREVIEW_REF
    gate_path = PROJECT_ROOT / GATE_REF
    final_preview_path = PROJECT_ROOT / FINAL_COMMAND_PREVIEW_REF

    request_data = _load_json(request_path)
    decision_data = _load_json(decision_path)
    _scan_forbidden_terms(request_data)
    _scan_forbidden_terms(decision_data)
    _validate_request(request_data)
    _validate_decision(decision_data, request_data)
    _ensure_file_exists(PROMPT_REF, "approved prompt path")
    _ensure_file_exists(COMMAND_PREVIEW_REF, "approved command preview path")
    if not prompt_path.is_file():
        _fail("approved prompt path does not exist")
    if not command_preview_path.is_file():
        _fail("approved command preview path does not exist")

    ONE_SHOT_DIR.mkdir(parents=True, exist_ok=True)
    final_preview = _build_final_command_preview()
    final_preview_path.write_text(final_preview, encoding="utf-8")

    gate_payload = _build_gate(request_data)
    gate_path.write_text(json.dumps(gate_payload, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "valid",
        "gate_path": GATE_REF,
        "final_command_preview_path": FINAL_COMMAND_PREVIEW_REF,
        "execution_allowed_by_human": gate_payload["execution_allowed_by_human"],
        "execution_allowed_now": gate_payload["execution_allowed_now"],
        "external_codex_cli_allowed_now": gate_payload["external_codex_cli_allowed_now"],
        "generated_prompt_execution_allowed_now": gate_payload["generated_prompt_execution_allowed_now"],
        "runtime_wiring_allowed": gate_payload["runtime_wiring_allowed"],
        "post_execution_flocky_validation_required": gate_payload["post_execution_flocky_validation_required"],
    }


def main(argv):
    if len(argv) != 1:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "error": "usage: prepare_one_shot_execution.py",
                },
                separators=(",", ":"),
            )
        )
        return 2
    try:
        result = prepare_one_shot_execution()
    except PreparationError as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, separators=(",", ":")))
        return 1
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
