import json
import sys
from pathlib import Path


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

REQUIRED_FORBIDDEN_PATHS = {
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
}

REQUIRED_EXPECTED_TESTS = {
    "python -m pytest pm_bot\\paper\\tests pm_bot\\risk\\tests pm_bot\\accounting\\tests pm_bot\\reports\\tests pm_bot\\postmortem\\tests pm_bot\\audit\\tests -q",
    "local deterministic command checks for created modules",
    "safety scan for no network/API/wallet/private key/trading",
    "safety scan for no dispatcher/run_codex/runtime mutation",
}

REQUIRED_FIELDS = [
    "schema_version",
    "approval_request_id",
    "target_batch_id",
    "approval_status",
    "approved_for_external_codex_cli_execution",
    "approved_by",
    "approved_at",
    "approval_reason",
    "approved_prompt_path",
    "approved_command_preview_path",
    "allowed_output_paths",
    "forbidden_paths",
    "expected_tests",
    "max_files_changed",
    "rollback_plan",
    "post_execution_flocky_validation_required",
    "execution_allowed_now",
    "external_codex_cli_allowed_now",
    "runtime_wiring_allowed",
    "generated_prompt_execution_allowed_now",
    "safety_check",
]

BANNED_TEXT_PATTERNS = [
    "network_allowed\": true",
    "api_allowed\": true",
    "wallet_allowed\": true",
    "private_key_allowed\": true",
    "trading_allowed\": true",
    "live polymarket",
    "real orders",
    "execution_allowed_now\": true",
    "external_codex_cli_allowed_now\": true",
    "generated_prompt_execution_allowed_now\": true",
    "runtime_wiring_allowed\": true",
    "final flocky/openclaw done",
    "final flocky done",
    "openclaw done",
    "second runtime source",
    "single_runtime_source_rule_preserved\": false",
]


class ValidationError(Exception):
    pass


def _error(message):
    raise ValidationError(message)


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _ensure_required_fields(data):
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        _error("missing required fields: " + ", ".join(missing))


def _ensure_paths_exist(base_dir, data):
    prompt_path = base_dir / data["approved_prompt_path"]
    command_path = base_dir / data["approved_command_preview_path"]
    if not prompt_path.is_file():
        _error("approved prompt path does not exist")
    if not command_path.is_file():
        _error("approved command preview path does not exist")


def _ensure_allowed_outputs(data):
    if data["allowed_output_paths"] != EXPECTED_ALLOWED_OUTPUT_PATHS:
        _error("allowed_output_paths must exactly match the approved list")
    for path in data["allowed_output_paths"]:
        normalized = path.replace("\\", "/")
        if normalized.startswith("/") or ".." in normalized.split("/"):
            _error("allowed_output_paths contains an invalid path")


def _ensure_forbidden_paths(data):
    forbidden = set(data["forbidden_paths"])
    missing = sorted(REQUIRED_FORBIDDEN_PATHS - forbidden)
    if missing:
        _error("forbidden_paths missing protected surfaces: " + ", ".join(missing))


def _ensure_expected_tests(data):
    tests = set(data["expected_tests"])
    missing = sorted(REQUIRED_EXPECTED_TESTS - tests)
    if missing:
        _error("expected_tests missing required entries: " + ", ".join(missing))


def _ensure_pending_cannot_execute(data):
    status = data["approval_status"]
    if status not in {"pending_human_approval", "approved_by_human", "rejected"}:
        _error("invalid approval_status")
    if status == "pending_human_approval":
        if data["approved_for_external_codex_cli_execution"]:
            _error("pending_human_approval cannot approve external codex cli execution")
        if data["execution_allowed_now"]:
            _error("pending_human_approval cannot set execution_allowed_now=true")
        if data["external_codex_cli_allowed_now"]:
            _error("pending_human_approval cannot set external_codex_cli_allowed_now=true")
        if data["generated_prompt_execution_allowed_now"]:
            _error("pending_human_approval cannot set generated_prompt_execution_allowed_now=true")
    if not data["approved_for_external_codex_cli_execution"]:
        if data["execution_allowed_now"] or data["external_codex_cli_allowed_now"] or data["generated_prompt_execution_allowed_now"]:
            _error("execution cannot be allowed when approved_for_external_codex_cli_execution is false")


def _ensure_limits_and_flags(data):
    if not isinstance(data["max_files_changed"], int) or data["max_files_changed"] <= 0:
        _error("max_files_changed must be a positive integer")
    if data["max_files_changed"] > 24:
        _error("max_files_changed is excessive")
    if not isinstance(data["rollback_plan"], str) or not data["rollback_plan"].strip():
        _error("rollback_plan must be present")
    if data["post_execution_flocky_validation_required"] is not True:
        _error("post_execution_flocky_validation_required must be true")
    if data["runtime_wiring_allowed"] is not False:
        _error("runtime_wiring_allowed must be false")
    if data["execution_allowed_now"] is not False:
        _error("execution_allowed_now must be false")
    if data["external_codex_cli_allowed_now"] is not False:
        _error("external_codex_cli_allowed_now must be false")
    if data["generated_prompt_execution_allowed_now"] is not False:
        _error("generated_prompt_execution_allowed_now must be false")


def _ensure_safety_check(data):
    safety = data["safety_check"]
    required = {
        "runtime_wiring_allowed": False,
        "network_allowed": False,
        "api_allowed": False,
        "wallet_allowed": False,
        "private_key_allowed": False,
        "trading_allowed": False,
        "external_codex_cli_allowed_now": False,
        "generated_prompt_execution_allowed_now": False,
        "single_runtime_source_rule_preserved": True,
    }
    for key, expected in required.items():
        if safety.get(key) is not expected:
            _error(f"safety_check.{key} must be {str(expected).lower()}")


def _ensure_no_banned_claims(path, data):
    raw = Path(path).read_text(encoding="utf-8").lower()
    for pattern in BANNED_TEXT_PATTERNS:
        if pattern in raw:
            _error("approval request contains banned content: " + pattern)
    risky_text = " ".join(
        str(data.get(key, "")).lower()
        for key in ("approval_reason", "rollback_plan", "approved_by", "approved_at")
    )
    for pattern in ["wallet", "private key", "trading", "live polymarket", "real orders", "final flocky/openclaw done", "final flocky done", "openclaw done", "second runtime source"]:
        if pattern in risky_text:
            _error("approval request contains banned content: " + pattern)


def validate_approval_request(path):
    request_path = Path(path)
    base_dir = Path.cwd()
    data = _load_json(request_path)
    _ensure_required_fields(data)
    _ensure_pending_cannot_execute(data)
    _ensure_paths_exist(base_dir, data)
    _ensure_allowed_outputs(data)
    _ensure_forbidden_paths(data)
    _ensure_expected_tests(data)
    _ensure_limits_and_flags(data)
    _ensure_safety_check(data)
    _ensure_no_banned_claims(request_path, data)
    return {
        "ok": True,
        "approval_request_id": data["approval_request_id"],
        "approval_status": data["approval_status"],
        "approved_for_external_codex_cli_execution": data["approved_for_external_codex_cli_execution"],
        "execution_allowed_now": data["execution_allowed_now"],
        "external_codex_cli_allowed_now": data["external_codex_cli_allowed_now"],
        "generated_prompt_execution_allowed_now": data["generated_prompt_execution_allowed_now"],
        "runtime_wiring_allowed": data["runtime_wiring_allowed"],
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"ok": False, "error": "usage: validate_external_execution_approval.py <approval_request.json>"}, separators=(",", ":")))
        return 2
    try:
        result = validate_approval_request(argv[1])
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, separators=(",", ":")))
        return 1
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
