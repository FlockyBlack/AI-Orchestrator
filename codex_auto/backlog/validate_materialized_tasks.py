import json
import sys
from pathlib import Path

SAFE_MODES = {"DESIGN_ONLY", "FIXTURE_ONLY", "PAPER_ONLY", "READ_ONLY_VALIDATION", "DRY_RUN_ONLY"}
COMMON_FORBIDDEN_PATHS = {
    "scripts/dispatcher.py",
    "scripts/run_codex.py",
    "tasks/",
    "state/",
}
FORBIDDEN_SCOPE_TERMS = (
    "network",
    "api",
    "wallet",
    "private key",
    "trading",
    "real orders",
)
EXPECTED_ALLOWED_PATHS = {
    "PMBOT-005-PAPER-SIMULATION": {"pm_bot/paper/", "pm_bot/paper/tests/"},
    "PMBOT-006-RISK-LIMITS": {"pm_bot/risk/", "pm_bot/risk/tests/"},
    "PMBOT-007-FEES-SLIPPAGE": {"pm_bot/accounting/", "pm_bot/accounting/tests/"},
    "PMBOT-008-RESEARCH-DASHBOARD": {"pm_bot/reports/", "pm_bot/reports/tests/"},
    "PMBOT-009-FIXTURE-POSTMORTEM": {"pm_bot/postmortem/", "pm_bot/postmortem/tests/"},
    "PMBOT-010-STATIC-SAFETY-AUDIT": {"pm_bot/audit/", "pm_bot/audit/tests/"},
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_candidate(data):
    errors = []
    required = [
        "schema_version",
        "materialized_task_id",
        "source_backlog_task_id",
        "codex_task_id",
        "queue_state",
        "mode",
        "executor",
        "source_backlog_path",
        "generated_prompt_ref",
        "allowed_paths",
        "forbidden_paths",
        "allowed_scope",
        "forbidden_scope",
        "done_criteria",
        "requires_human_approval",
        "approved_for_execution",
        "dry_run_default",
        "flocky_validation_required",
        "runtime_wiring_allowed",
        "external_codex_cli_allowed",
        "safety_flags",
    ]
    for field in required:
        if field not in data:
            errors.append(f"missing:{field}")
    if errors:
        return errors

    if data.get("schema_version") != "v1":
        errors.append("schema_version_must_be_v1")
    if data.get("queue_state") != "candidate":
        errors.append("queue_state_must_be_candidate")
    if data.get("approved_for_execution") is not False:
        errors.append("approved_for_execution_must_be_false")
    if data.get("dry_run_default") is not True:
        errors.append("dry_run_default_must_be_true")
    if data.get("flocky_validation_required") is not True:
        errors.append("flocky_validation_required_must_be_true")
    if data.get("runtime_wiring_allowed") is not False:
        errors.append("runtime_wiring_allowed_must_be_false")
    if data.get("external_codex_cli_allowed") is not False:
        errors.append("external_codex_cli_allowed_must_be_false")
    if data.get("mode") not in SAFE_MODES:
        errors.append("invalid_mode")

    materialized_task_id = data.get("materialized_task_id")
    expected_allowed = EXPECTED_ALLOWED_PATHS.get(materialized_task_id)
    if expected_allowed is None:
        errors.append("unknown_materialized_task_id")
    elif set(data.get("allowed_paths", [])) != expected_allowed:
        errors.append("allowed_paths_must_match_candidate_slice")

    forbidden_paths = set(data.get("forbidden_paths", []))
    for required_path in COMMON_FORBIDDEN_PATHS:
        if required_path not in forbidden_paths:
            errors.append(f"missing_forbidden_path:{required_path}")
    serialized_forbidden_paths = " ".join(data.get("forbidden_paths", [])).lower()
    for term in ("runtime", "result", "freeze", "checkpoint"):
        if term not in serialized_forbidden_paths:
            errors.append(f"missing_protected_surface:{term}")

    serialized_scope = " ".join(data.get("forbidden_scope", [])).lower()
    for term in FORBIDDEN_SCOPE_TERMS:
        if term not in serialized_scope:
            errors.append(f"missing_forbidden_scope:{term}")
    if "final flocky/openclaw done claim" not in serialized_scope and "final flocky" not in serialized_scope:
        errors.append("missing_forbidden_scope:final_done_claim")
    if "second runtime source of truth" not in serialized_scope:
        errors.append("missing_forbidden_scope:second_runtime_source")

    serialized_claims = " ".join(
        [
            str(data.get("title", "")),
            str(data.get("summary", "")),
            " ".join(data.get("done_criteria", [])),
            " ".join(data.get("notes", [])),
        ]
    ).lower()
    if "final flocky done" in serialized_claims or "final openclaw done" in serialized_claims:
        errors.append("forbidden_final_done_claim")
    if "runtime truth" in serialized_claims or "source of truth" in serialized_claims:
        errors.append("forbidden_runtime_truth_claim")

    return errors


def _validate_report(data):
    errors = []
    required = [
        "schema_version",
        "report_id",
        "source_backlog_path",
        "generated_at",
        "candidates_created",
        "candidates_skipped",
        "prompts_created",
        "validation_summary",
        "safety_check",
        "recommended_next_action",
    ]
    for field in required:
        if field not in data:
            errors.append(f"missing:{field}")
    if errors:
        return errors

    if data.get("schema_version") != "v1":
        errors.append("schema_version_must_be_v1")
    if data.get("source_backlog_path") != "docs/PM_BOT_SAFE_BACKLOG_V1.json":
        errors.append("source_backlog_path_must_match")
    safety = data.get("safety_check", {})
    if not isinstance(safety, dict):
        errors.append("safety_check_must_be_object")
    else:
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
                errors.append(f"safety_check_{key}_must_be_false")
        if safety.get("single_runtime_source_rule_preserved") is not True:
            errors.append("single_runtime_source_rule_preserved_must_be_true")
    return errors


def validate_file(path_str: str):
    path = Path(path_str)
    data = _load_json(path)
    if "materialized_task_id" in data:
        errors = _validate_candidate(data)
        artifact_type = "materialized_task"
        artifact_id = data.get("materialized_task_id")
    else:
        errors = _validate_report(data)
        artifact_type = "materialization_report"
        artifact_id = data.get("report_id")
    return {
        "status": "valid" if not errors else "invalid",
        "file": str(path),
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "errors": sorted(set(errors)),
    }


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "file": None, "artifact_type": None, "artifact_id": None, "errors": ["usage: validate_materialized_tasks.py <candidate_or_report.json>"]}, separators=(",", ":")))
        return 2
    result = validate_file(argv[1])
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
