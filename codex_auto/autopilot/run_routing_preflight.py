import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
AUTOPILOT_ROOT = PROJECT_ROOT / "codex_auto" / "autopilot"
SCHEMA_PATH = AUTOPILOT_ROOT / "autopilot_routing_preflight_report.schema.v1.json"

from codex_auto.autopilot.classify_prompt_route import classify_prompt_route  # noqa: E402

REPORT_TYPE = "AUTOPILOT_ROUTING_PREFLIGHT_REPORT"
VALIDATION_REPORT_TYPE = "AUTOPILOT_ROUTING_PREFLIGHT_REPORT_VALIDATION"
SCHEMA_VERSION = "1.0"
GENERATED_BY = "codex_auto/autopilot/run_routing_preflight.py"
FORBIDDEN_BEFORE_PREFLIGHT = [
    "coding-agent skill use",
    "sessions_spawn",
    "subagent spawn",
    "shell/exec",
    "generated prompt execution",
    "project file writes",
    "runtime mutation",
    "queue mutation",
    "governance mutation",
    "dispatcher.py use",
    "run_codex.py use",
    "external Codex execution",
]
FORBIDDEN_NEXT_ACTIONS = {
    "EXECUTE_NOW",
    "SPAWN_SESSION",
    "RUN_CODEX",
    "MUTATE_RUNTIME",
    "MUTATE_QUEUE",
    "FINAL_ACCEPTED",
    "RUNTIME_DONE",
    "AUTO_APPROVE_EXECUTION",
    "AUTO_APPLY_RUNTIME_STATE",
}
OUTPUT_ALLOWLIST = [
    "codex_auto/autopilot/tests/output/",
    "codex_auto/autopilot/fixtures/output/",
    "codex_auto/autopilot/tmp/",
]
REQUIRED_FALSE_FLAGS = [
    "original_prompt_executed",
    "sessions_spawn_allowed",
    "runtime_mutation_allowed",
    "queue_mutation_allowed",
    "governance_mutation_allowed",
    "active_flocky_tool_integration",
    "runtime_wiring_allowed",
    "dispatcher_integration_allowed",
    "run_codex_integration_allowed",
]
EXACT_FORBIDDEN_CLAIMS = {
    "sessions_spawn_allowed": True,
    "original_prompt_executed": True,
    "active_flocky_tool_integration": True,
    "runtime_wiring_allowed": True,
    "dispatcher_integration_allowed": True,
    "run_codex_integration_allowed": True,
    "execution_approved": True,
    "final_accepted": True,
    "runtime_done": True,
    "source_of_truth": "codex_auto",
    "authoritative_runtime_owner": "codex_auto",
    "queue_bridge_active": True,
    "state_writeback_active": True,
}
FORBIDDEN_TEXT_CLAIMS = {
    "sessions_spawn_allowed=true": "forbidden_claim:sessions_spawn_allowed",
    "original_prompt_executed=true": "forbidden_claim:original_prompt_executed",
    "active_flocky_tool_integration=true": "forbidden_claim:active_flocky_tool_integration",
    "runtime_wiring_allowed=true": "forbidden_claim:runtime_wiring_allowed",
    "dispatcher_integration_allowed=true": "forbidden_claim:dispatcher_integration_allowed",
    "run_codex_integration_allowed=true": "forbidden_claim:run_codex_integration_allowed",
    "execution_approved=true": "forbidden_claim:execution_approved",
    "final_accepted=true": "forbidden_claim:final_accepted",
    "runtime_done=true": "forbidden_claim:runtime_done",
    "source_of_truth=codex_auto": "forbidden_claim:source_of_truth_codex_auto",
    "authoritative_runtime_owner=codex_auto": "forbidden_claim:authoritative_runtime_owner_codex_auto",
    "queue_bridge_active=true": "forbidden_claim:queue_bridge_active",
    "state_writeback_active=true": "forbidden_claim:state_writeback_active",
}
REQUIRED_FIELDS = [
    "type",
    "schema_version",
    "preflight_only",
    "receiver_agent",
    "prompt_source",
    "routing_decision",
    "preflight_passed",
    "safe_for_receiver_to_continue",
    "allowed_tool_scope",
    "forbidden_before_preflight",
    "required_behavior",
    "original_prompt_executed",
    "sessions_spawn_allowed",
    "code_changes_allowed_for_receiver",
    "runtime_mutation_allowed",
    "queue_mutation_allowed",
    "governance_mutation_allowed",
    "active_flocky_tool_integration",
    "runtime_wiring_allowed",
    "dispatcher_integration_allowed",
    "run_codex_integration_allowed",
    "single_runtime_source_rule_preserved",
    "next_action",
    "warnings",
    "errors",
    "generated_by",
    "deterministic_preflight",
]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_schema():
    return _load_json(SCHEMA_PATH)


def _sorted_unique(items):
    return sorted(set(items))


def _normalize_path(value) -> str:
    return str(Path(str(value))).replace("\\", "/").lower()


def _resolve_input_path(path_str: str) -> Path:
    candidate = Path(path_str)
    if not candidate.is_absolute():
        candidate = (PROJECT_ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"path_outside_project_root:{candidate}") from exc
    return candidate


def _to_project_ref(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _is_under(base_ref: str, candidate_ref: str) -> bool:
    base = base_ref.rstrip("/")
    candidate = candidate_ref.rstrip("/")
    return candidate == base or candidate.startswith(base + "/")


def validate_output_path(path_str: str) -> Path:
    candidate = _resolve_input_path(path_str)
    candidate_ref = _to_project_ref(candidate)
    candidate_norm = _normalize_path(candidate_ref)

    forbidden_roots = [
        "tasks/",
        "runs/",
        "state/",
        "runtime/",
        "results/",
        "freeze/",
        "checkpoint/",
        "governance/",
        "scripts/",
        "pm_bot/",
        "codex_auto/tasks/",
        "codex_auto/queue/",
        "codex_auto/external_cli/",
    ]
    for forbidden in forbidden_roots:
        forbidden_norm = _normalize_path(forbidden).rstrip("/")
        if candidate_norm == forbidden_norm or candidate_norm.startswith(forbidden_norm + "/"):
            raise ValueError(f"output_path_forbidden:{candidate_ref}")

    for allowed_root in OUTPUT_ALLOWLIST:
        if _is_under(_normalize_path(allowed_root), candidate_norm):
            return candidate
    raise ValueError(f"output_path_not_in_allowed_preflight_area:{candidate_ref}")


def write_preflight_report(output_path: str, report):
    destination = validate_output_path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return destination


def _read_prompt(prompt_path: str) -> str:
    if prompt_path == "-":
        return sys.stdin.read()
    return _resolve_input_path(prompt_path).read_text(encoding="utf-8")


def _build_prompt_source(prompt_path: str) -> str:
    if prompt_path == "-":
        return "stdin"
    return _to_project_ref(_resolve_input_path(prompt_path))


def _scan_forbidden_claims(value, errors):
    if isinstance(value, dict):
        for key, expected in EXACT_FORBIDDEN_CLAIMS.items():
            if key in value and value[key] == expected:
                errors.append(f"forbidden_claim:{key}")
        for nested in value.values():
            _scan_forbidden_claims(nested, errors)
        return
    if isinstance(value, list):
        for item in value:
            _scan_forbidden_claims(item, errors)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for term, code in FORBIDDEN_TEXT_CLAIMS.items():
            if term in lowered:
                errors.append(code)


def _base_report(receiver: str, prompt_source: str, routing_decision: dict):
    routing_class = routing_decision["routing_class"]
    required_behavior = "RETURN_ROUTING_MISMATCH"
    next_action = "CLARIFY_OR_RESEND_TO_CORRECT_AGENT"
    preflight_passed = False
    safe_for_receiver = False
    allowed_tool_scope = "none"

    if receiver == "Flocky" and routing_class in {"CODEX_CODE_CHANGING_TASK", "CODEX_REPAIR_TASK"}:
        required_behavior = "MISROUTED_CODEX_PROMPT_DETECTED"
        next_action = "RESEND_TO_CODEX"
    elif receiver == "Flocky" and routing_class == "FLOCKY_VALIDATION_TASK":
        required_behavior = "PROCEED_READ_ONLY_VALIDATION"
        next_action = "CONTINUE_READ_ONLY_VALIDATION"
        preflight_passed = True
        safe_for_receiver = True
        allowed_tool_scope = "read_only_validation_only"
    elif receiver == "Flocky" and routing_class == "FLOCKY_GOVERNANCE_TASK":
        required_behavior = "PROCEED_GOVERNANCE_DESIGN"
        next_action = "CONTINUE_GOVERNANCE_DESIGN"
        preflight_passed = True
        safe_for_receiver = True
        allowed_tool_scope = "read_only_governance_design_only"
    elif routing_class == "AMBIGUOUS_OR_MISROUTED_TASK":
        required_behavior = "RETURN_ROUTING_MISMATCH"
        next_action = "CLARIFY_OR_RESEND_TO_CORRECT_AGENT"
    elif routing_class == "UNSAFE_OR_APPROVAL_REQUIRED_TASK":
        required_behavior = "BLOCK_UNSAFE_OR_APPROVAL_REQUIRED"
        next_action = "REQUIRE_HUMAN_APPROVAL_OR_REWRITE_PROMPT"

    warnings = list(routing_decision.get("warnings") or [])
    errors = []
    if routing_decision.get("required_behavior") != required_behavior:
        warnings.append(
            f"classifier_behavior_mismatch:{routing_decision.get('required_behavior')}->{required_behavior}"
        )

    return {
        "type": REPORT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "preflight_only": True,
        "receiver_agent": receiver,
        "prompt_source": prompt_source,
        "routing_decision": routing_decision,
        "preflight_passed": preflight_passed,
        "safe_for_receiver_to_continue": safe_for_receiver,
        "allowed_tool_scope": allowed_tool_scope,
        "forbidden_before_preflight": list(FORBIDDEN_BEFORE_PREFLIGHT),
        "required_behavior": required_behavior,
        "original_prompt_executed": False,
        "sessions_spawn_allowed": False,
        "code_changes_allowed_for_receiver": False if receiver == "Flocky" else bool(routing_decision.get("code_changes_allowed_for_receiver")),
        "runtime_mutation_allowed": False,
        "queue_mutation_allowed": False,
        "governance_mutation_allowed": False,
        "active_flocky_tool_integration": False,
        "runtime_wiring_allowed": False,
        "dispatcher_integration_allowed": False,
        "run_codex_integration_allowed": False,
        "single_runtime_source_rule_preserved": True,
        "next_action": next_action,
        "warnings": _sorted_unique(warnings),
        "errors": errors,
        "generated_by": GENERATED_BY,
        "deterministic_preflight": True,
    }


def _validate_report_object(data):
    errors = []
    warnings = []

    if not isinstance(data, dict):
        return {
            "type": VALIDATION_REPORT_TYPE,
            "valid": False,
            "errors": ["preflight_report_must_be_object"],
            "warnings": [],
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")

    if data.get("type") != REPORT_TYPE:
        errors.append(f"type_must_be:{REPORT_TYPE}")
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version_must_be:{SCHEMA_VERSION}")
    if data.get("preflight_only") is not True:
        errors.append("preflight_only_must_be_true")
    if data.get("single_runtime_source_rule_preserved") is not True:
        errors.append("single_runtime_source_rule_preserved_must_be_true")
    if data.get("deterministic_preflight") is not True:
        errors.append("deterministic_preflight_must_be_true")
    if data.get("generated_by") != GENERATED_BY:
        errors.append(f"generated_by_must_be:{GENERATED_BY}")

    for field in REQUIRED_FALSE_FLAGS:
        if data.get(field) is not False:
            errors.append(f"{field}_must_be_false")

    if data.get("receiver_agent") == "Flocky" and data.get("code_changes_allowed_for_receiver") is not False:
        errors.append("code_changes_allowed_for_receiver_must_be_false_for_flocky")

    forbidden_list = data.get("forbidden_before_preflight")
    if not isinstance(forbidden_list, list):
        errors.append("forbidden_before_preflight_must_be_list")
        forbidden_list = []
    forbidden_norm = {str(item) for item in forbidden_list}
    for required in FORBIDDEN_BEFORE_PREFLIGHT:
        if required not in forbidden_norm:
            errors.append(f"missing_forbidden_before_preflight:{required}")

    next_action = data.get("next_action")
    if not isinstance(next_action, str) or not next_action.strip():
        errors.append("next_action_must_be_non_empty")
    elif next_action in FORBIDDEN_NEXT_ACTIONS:
        errors.append(f"forbidden_next_action:{next_action}")

    routing_decision = data.get("routing_decision")
    if not isinstance(routing_decision, dict):
        errors.append("routing_decision_must_be_object")
        routing_decision = {}

    warnings_field = data.get("warnings")
    if not isinstance(warnings_field, list) or not all(isinstance(item, str) for item in warnings_field):
        errors.append("warnings_must_be_list_of_strings")
    errors_field = data.get("errors")
    if not isinstance(errors_field, list) or not all(isinstance(item, str) for item in errors_field):
        errors.append("errors_must_be_list_of_strings")

    prompt_source = data.get("prompt_source")
    if not isinstance(prompt_source, str) or not prompt_source.strip():
        errors.append("prompt_source_must_be_non_empty")

    required_behavior = data.get("required_behavior")
    if not isinstance(required_behavior, str) or not required_behavior.strip():
        errors.append("required_behavior_must_be_non_empty")

    allowed_tool_scope = data.get("allowed_tool_scope")
    if not isinstance(allowed_tool_scope, str) or not allowed_tool_scope.strip():
        errors.append("allowed_tool_scope_must_be_non_empty")

    if routing_decision:
        routing_class = routing_decision.get("routing_class")
        if data.get("receiver_agent") == "Flocky":
            if routing_class in {"CODEX_CODE_CHANGING_TASK", "CODEX_REPAIR_TASK"}:
                if data.get("preflight_passed") is not False:
                    errors.append("preflight_passed_must_be_false_for_misrouted_codex_task")
                if data.get("safe_for_receiver_to_continue") is not False:
                    errors.append("safe_for_receiver_to_continue_must_be_false_for_misrouted_codex_task")
                if data.get("required_behavior") != "MISROUTED_CODEX_PROMPT_DETECTED":
                    errors.append("required_behavior_invalid_for_misrouted_codex_task")
                if data.get("next_action") != "RESEND_TO_CODEX":
                    errors.append("next_action_invalid_for_misrouted_codex_task")
            elif routing_class == "FLOCKY_VALIDATION_TASK":
                if data.get("preflight_passed") is not True:
                    errors.append("preflight_passed_must_be_true_for_flocky_validation")
                if data.get("safe_for_receiver_to_continue") is not True:
                    errors.append("safe_for_receiver_to_continue_must_be_true_for_flocky_validation")
                if data.get("required_behavior") != "PROCEED_READ_ONLY_VALIDATION":
                    errors.append("required_behavior_invalid_for_flocky_validation")
                if data.get("allowed_tool_scope") != "read_only_validation_only":
                    errors.append("allowed_tool_scope_invalid_for_flocky_validation")
            elif routing_class == "FLOCKY_GOVERNANCE_TASK":
                if data.get("preflight_passed") is not True:
                    errors.append("preflight_passed_must_be_true_for_flocky_governance")
                if data.get("safe_for_receiver_to_continue") is not True:
                    errors.append("safe_for_receiver_to_continue_must_be_true_for_flocky_governance")
                if data.get("required_behavior") != "PROCEED_GOVERNANCE_DESIGN":
                    errors.append("required_behavior_invalid_for_flocky_governance")
                if data.get("allowed_tool_scope") != "read_only_governance_design_only":
                    errors.append("allowed_tool_scope_invalid_for_flocky_governance")
            elif routing_class == "AMBIGUOUS_OR_MISROUTED_TASK":
                if data.get("preflight_passed") is not False:
                    errors.append("preflight_passed_must_be_false_for_ambiguous_task")
                if data.get("safe_for_receiver_to_continue") is not False:
                    errors.append("safe_for_receiver_to_continue_must_be_false_for_ambiguous_task")
                if data.get("required_behavior") != "RETURN_ROUTING_MISMATCH":
                    errors.append("required_behavior_invalid_for_ambiguous_task")
                if data.get("next_action") != "CLARIFY_OR_RESEND_TO_CORRECT_AGENT":
                    errors.append("next_action_invalid_for_ambiguous_task")
            elif routing_class == "UNSAFE_OR_APPROVAL_REQUIRED_TASK":
                if data.get("preflight_passed") is not False:
                    errors.append("preflight_passed_must_be_false_for_unsafe_task")
                if data.get("safe_for_receiver_to_continue") is not False:
                    errors.append("safe_for_receiver_to_continue_must_be_false_for_unsafe_task")
                if data.get("required_behavior") != "BLOCK_UNSAFE_OR_APPROVAL_REQUIRED":
                    errors.append("required_behavior_invalid_for_unsafe_task")
                if data.get("next_action") != "REQUIRE_HUMAN_APPROVAL_OR_REWRITE_PROMPT":
                    errors.append("next_action_invalid_for_unsafe_task")

    _scan_forbidden_claims(data, errors)
    return {
        "type": VALIDATION_REPORT_TYPE,
        "valid": not errors,
        "errors": _sorted_unique(errors),
        "warnings": _sorted_unique(warnings),
    }


def validate_preflight_report(data):
    return _validate_report_object(data)


def build_routing_preflight_report(receiver: str, prompt_text: str, prompt_source: str = "inline"):
    routing_decision = classify_prompt_route(receiver=receiver, prompt_text=prompt_text)
    report = _base_report(receiver=receiver, prompt_source=prompt_source, routing_decision=routing_decision)
    validation = _validate_report_object(report)
    report["warnings"] = _sorted_unique(list(report["warnings"]) + list(validation["warnings"]))
    report["errors"] = validation["errors"]
    return report


def build_routing_preflight_report_from_path(receiver: str, prompt_path: str):
    return build_routing_preflight_report(
        receiver=receiver,
        prompt_text=_read_prompt(prompt_path),
        prompt_source=_build_prompt_source(prompt_path),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a deterministic Autopilot routing preflight report.")
    parser.add_argument("--receiver", required=True)
    parser.add_argument("--prompt-path", required=True, help="Path to prompt text or '-' for stdin.")
    parser.add_argument("--out", default="-", help="Write to a safe autopilot output path or '-' for stdout only.")
    args = parser.parse_args(argv)

    try:
        report = build_routing_preflight_report_from_path(receiver=args.receiver, prompt_path=args.prompt_path)
        if args.out != "-":
            write_preflight_report(args.out, report)
        print(json.dumps(report, indent=2))
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}, separators=(",", ":")))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
