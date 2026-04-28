import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
AUTOPILOT_ROOT = PROJECT_ROOT / "codex_auto" / "autopilot"
SCHEMA_PATH = AUTOPILOT_ROOT / "autopilot_dry_run_report.schema.v1.json"

from codex_auto.autopilot.build_preview_handoff import build_preview_handoff
from codex_auto.autopilot.validate_preview_handoff import validate_preview_handoff_data

SCHEMA_VERSION = "autopilot_dry_run_report.v1"
GENERATED_BY = "codex_auto.autopilot.run_dry_run_flow"
VALIDATION_REPORT_TYPE = "AUTOPILOT_DRY_RUN_FLOW_REPORT_VALIDATION"
ALLOWED_NEXT_ACTIONS = [
    "ready_for_flocky_review",
    "repair_needed",
    "blocked",
    "approval_required",
]
FORBIDDEN_NEXT_ACTIONS = [
    "execute_now",
    "runtime_done",
    "final_accepted",
    "bridge_active",
    "auto_approve_execution",
    "auto_apply_runtime_state",
]
REQUIRED_FIELDS = [
    "schema_version",
    "dry_run_only",
    "runtime_authority",
    "final_acceptance_authority",
    "source_task_id",
    "authoritative_task_path",
    "authoritative_run_path_or_ref",
    "preview_handoff_ref_or_inline",
    "preview_validation_report",
    "flow_steps",
    "allowed_paths",
    "forbidden_paths",
    "stop_conditions",
    "approval_required_before_execution",
    "flocky_validation_required",
    "execution_allowed_now",
    "runtime_wiring_allowed",
    "queue_mutation_allowed",
    "final_acceptance_claimed",
    "single_runtime_source_rule_preserved",
    "status_ownership",
    "next_action_recommendation",
    "warnings",
    "errors",
    "generated_by",
    "deterministic_dry_run",
]
REQUIRED_FLAGS = {
    "dry_run_only": True,
    "runtime_authority": False,
    "final_acceptance_authority": False,
    "approval_required_before_execution": True,
    "flocky_validation_required": True,
    "execution_allowed_now": False,
    "runtime_wiring_allowed": False,
    "queue_mutation_allowed": False,
    "final_acceptance_claimed": False,
    "single_runtime_source_rule_preserved": True,
    "deterministic_dry_run": True,
}
REQUIRED_STATUS_OWNERS = {
    "runtime_status": "AI-Orchestrator",
    "final_acceptance_status": "AI-Orchestrator",
    "handoff_status": "codex_auto",
    "preview_validation_status": "codex_auto/autopilot validator",
    "dry_run_status": "codex_auto/autopilot dry-run reporter",
    "flocky_validation_status": "Flocky",
    "codex_execution_status": "Codex result envelope only after approved execution",
}
REQUIRED_FORBIDDEN_PATHS = [
    "tasks/",
    "runs/",
    "state/",
    "runtime/",
    "results/",
    "freeze/",
    "checkpoint/",
    "governance/",
    "scripts/dispatcher.py",
    "scripts/run_codex.py",
    "pm_bot/",
    "codex_auto/external_cli/",
    "codex_auto/tasks/",
    "codex_auto/queue/",
]
DEFAULT_ALLOWED_PATHS = [
    "codex_auto/autopilot/",
    "codex_auto/autopilot/tests/",
    "codex_auto/autopilot/fixtures/",
    "docs/AUTOPILOT_V1_DRY_RUN_FLOW.md",
    "docs/ORCH_AUTOPILOT_006_RESULT.json",
]
OUTPUT_ALLOWLIST = [
    "codex_auto/autopilot/tests/output/",
    "codex_auto/autopilot/fixtures/output/",
    "codex_auto/autopilot/tmp/",
]
STOP_CONDITIONS = [
    "Stop if any write is requested outside codex_auto/autopilot/, docs/AUTOPILOT_V1_DRY_RUN_FLOW.md, or docs/ORCH_AUTOPILOT_006_RESULT.json.",
    "Stop if runtime wiring is proposed or implied.",
    "Stop if dispatcher changes are proposed or implied.",
    "Stop if scripts/run_codex.py changes are proposed or implied.",
    "Stop if any active task mutation is proposed or implied.",
    "Stop if any task queue mutation is proposed or implied.",
    "Stop if any codex_auto queue mutation is proposed or implied.",
    "Stop if any state, result, freeze, or checkpoint mutation is proposed or implied.",
    "Stop if any governance mutation is proposed or implied.",
    "Stop if any external Codex execution is proposed or implied.",
    "Stop if any generated prompt execution is proposed or implied.",
    "Stop if any network or API access is proposed or implied.",
    "Stop if credentials, wallets, private keys, orders, or trading actions are requested or implied.",
    "Stop if any autonomous execution is proposed or implied.",
    "Stop if any PMBOT or external_cli/one_shot feature work is proposed or implied.",
    "Stop if final acceptance, execution approval, runtime done, truth transfer, queue bridge activation, or runtime writeback is claimed or implied.",
]
EXACT_FORBIDDEN_CLAIMS = {
    "final_accepted": True,
    "runtime_done": True,
    "execution_approved": True,
    "runtime_truth_transferred": True,
    "source_of_truth": "codex_auto",
    "authoritative_runtime_owner": "codex_auto",
    "queue_bridge_active": True,
    "dispatcher_integration_active": True,
    "run_codex_integration_active": True,
    "state_writeback_active": True,
    "runtime_wiring_complete": True,
}
FORBIDDEN_TEXT_CLAIMS = {
    "final_accepted=true": "forbidden_claim:final_accepted",
    "runtime_done=true": "forbidden_claim:runtime_done",
    "execution_approved=true": "forbidden_claim:execution_approved",
    "runtime_truth_transferred=true": "forbidden_claim:runtime_truth_transferred",
    "source_of_truth=codex_auto": "forbidden_claim:source_of_truth_codex_auto",
    "authoritative_runtime_owner=codex_auto": "forbidden_claim:authoritative_runtime_owner_codex_auto",
    "queue_bridge_active=true": "forbidden_claim:queue_bridge_active",
    "dispatcher_integration_active=true": "forbidden_claim:dispatcher_integration_active",
    "run_codex_integration_active=true": "forbidden_claim:run_codex_integration_active",
    "state_writeback_active=true": "forbidden_claim:state_writeback_active",
    "runtime_wiring_complete=true": "forbidden_claim:runtime_wiring_complete",
    "execute_now": "forbidden_claim:execute_now",
    "runtime_done": "forbidden_claim:runtime_done_text",
    "final accepted": "forbidden_claim:final_accepted_text",
    "auto approve execution": "forbidden_claim:auto_approve_execution",
    "auto apply runtime state": "forbidden_claim:auto_apply_runtime_state",
    "queue bridge active": "forbidden_claim:queue_bridge_active_text",
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_schema():
    return _load_json(SCHEMA_PATH)


def _normalize_path(value) -> str:
    return str(Path(str(value))).replace("\\", "/").lower()


def _sorted_unique(items):
    return sorted(set(items))


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
    for forbidden in REQUIRED_FORBIDDEN_PATHS:
        forbidden_norm = _normalize_path(forbidden).rstrip("/")
        if candidate_norm == forbidden_norm or candidate_norm.startswith(forbidden_norm + "/"):
            raise ValueError(f"output_path_forbidden:{candidate_ref}")
    for allowed_root in OUTPUT_ALLOWLIST:
        if _is_under(_normalize_path(allowed_root), candidate_norm):
            return candidate
    raise ValueError(f"output_path_not_in_allowed_dry_run_area:{candidate_ref}")


def write_dry_run_report(output_path: str, report):
    destination = validate_output_path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return destination


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


def _validate_authoritative_ref(field_name, value, expected_prefix, warnings, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field_name}_must_be_non_empty")
        return
    normalized = _normalize_path(value)
    if normalized.startswith(_normalize_path(expected_prefix)):
        return
    if "fixture" in normalized or "example" in normalized:
        warnings.append(f"example_reference_path:{field_name}")
        return
    errors.append(f"bad_authoritative_path_claim:{field_name}")


def _validate_report_object(data):
    errors = []
    warnings = []
    if not isinstance(data, dict):
        return {
            "type": VALIDATION_REPORT_TYPE,
            "valid": False,
            "errors": ["dry_run_report_must_be_object"],
            "warnings": [],
        }

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version_must_be:{SCHEMA_VERSION}")

    for field, expected in REQUIRED_FLAGS.items():
        if data.get(field) is not expected:
            errors.append(f"{field}_must_be_{str(expected).lower()}")

    for field in ("source_task_id", "generated_by"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field}_must_be_non_empty")

    _validate_authoritative_ref("authoritative_task_path", data.get("authoritative_task_path"), "tasks/", warnings, errors)
    _validate_authoritative_ref("authoritative_run_path_or_ref", data.get("authoritative_run_path_or_ref"), "runs/", warnings, errors)

    preview_handoff = data.get("preview_handoff_ref_or_inline")
    if isinstance(preview_handoff, dict):
        preview_report = validate_preview_handoff_data(preview_handoff)
        if not preview_report["valid"]:
            errors.extend(f"preview_handoff_invalid:{item}" for item in preview_report["errors"])
        warnings.extend(preview_report["warnings"])
    elif not isinstance(preview_handoff, str) or not preview_handoff.strip():
        errors.append("preview_handoff_ref_or_inline_must_be_object_or_non_empty_string")

    preview_validation_report = data.get("preview_validation_report")
    if not isinstance(preview_validation_report, dict):
        errors.append("preview_validation_report_must_be_object")
    else:
        if preview_validation_report.get("type") != "AUTOPILOT_PREVIEW_HANDOFF_VALIDATION_REPORT":
            errors.append("preview_validation_report_type_invalid")
        if preview_validation_report.get("valid") is False:
            preview_errors = preview_validation_report.get("errors") or []
            if any("forbidden_claim:" in str(item) for item in preview_errors):
                warnings.append("preview_validation_blocking_forbidden_claims_detected")

    flow_steps = data.get("flow_steps")
    if not isinstance(flow_steps, list) or not flow_steps or not all(isinstance(item, str) and item.strip() for item in flow_steps):
        errors.append("flow_steps_must_be_non_empty_list")

    allowed_paths = data.get("allowed_paths")
    if not isinstance(allowed_paths, list) or not allowed_paths or not all(isinstance(item, str) and item.strip() for item in allowed_paths):
        errors.append("allowed_paths_must_be_non_empty_list")

    forbidden_paths = data.get("forbidden_paths")
    if not isinstance(forbidden_paths, list):
        errors.append("forbidden_paths_must_be_list")
        forbidden_paths = []
    forbidden_norm = {_normalize_path(item) for item in forbidden_paths if isinstance(item, str)}
    for required in REQUIRED_FORBIDDEN_PATHS:
        if _normalize_path(required) not in forbidden_norm:
            errors.append(f"missing_forbidden_path:{required}")

    stop_conditions = data.get("stop_conditions")
    if not isinstance(stop_conditions, list) or not stop_conditions or not all(isinstance(item, str) and item.strip() for item in stop_conditions):
        errors.append("stop_conditions_must_be_non_empty_list")

    ownership = data.get("status_ownership")
    if not isinstance(ownership, dict):
        errors.append("status_ownership_must_be_object")
        ownership = {}
    for field, owner in REQUIRED_STATUS_OWNERS.items():
        nested = ownership.get(field)
        if not isinstance(nested, dict):
            errors.append(f"missing_status_ownership:{field}")
            continue
        if nested.get("owner") != owner:
            errors.append(f"{field}_owner_must_be:{owner}")

    recommendation = data.get("next_action_recommendation")
    if recommendation not in ALLOWED_NEXT_ACTIONS:
        errors.append("next_action_recommendation_invalid")
    if recommendation in FORBIDDEN_NEXT_ACTIONS:
        errors.append(f"forbidden_next_action:{recommendation}")

    warnings_field = data.get("warnings")
    if not isinstance(warnings_field, list) or not all(isinstance(item, str) for item in warnings_field):
        errors.append("warnings_must_be_list_of_strings")
    errors_field = data.get("errors")
    if not isinstance(errors_field, list) or not all(isinstance(item, str) for item in errors_field):
        errors.append("errors_must_be_list_of_strings")

    _scan_forbidden_claims(data, errors)
    return {
        "type": VALIDATION_REPORT_TYPE,
        "valid": not errors,
        "errors": _sorted_unique(errors),
        "warnings": _sorted_unique(warnings),
    }


def validate_dry_run_report(data):
    return _validate_report_object(data)


def _next_action_from_preview(preview_validation_report, report_errors):
    if any(item.startswith("forbidden_claim:") or item.startswith("forbidden_next_action:") for item in report_errors):
        return "blocked"
    if preview_validation_report.get("valid") and not report_errors:
        return "ready_for_flocky_review"
    preview_errors = preview_validation_report.get("errors") or []
    if any("forbidden_claim:" in str(item) for item in preview_errors):
        return "blocked"
    if preview_validation_report.get("valid") is False:
        return "repair_needed"
    return "approval_required"


def build_dry_run_flow_report(task_path: str, run_path: str, source_task_id: str):
    preview_handoff = build_preview_handoff(task_path=task_path, run_path=run_path, source_task_id=source_task_id)
    preview_validation_report = validate_preview_handoff_data(preview_handoff)

    report = {
        "schema_version": SCHEMA_VERSION,
        "dry_run_only": True,
        "runtime_authority": False,
        "final_acceptance_authority": False,
        "source_task_id": source_task_id,
        "authoritative_task_path": preview_handoff["authoritative_task_path"],
        "authoritative_run_path_or_ref": preview_handoff["authoritative_run_path_or_ref"],
        "preview_handoff_ref_or_inline": preview_handoff,
        "preview_validation_report": preview_validation_report,
        "flow_steps": [
            "Resolve authoritative AI-Orchestrator task and run references.",
            "Build preview-only handoff envelope.",
            "Validate preview handoff contract.",
            "Assemble deterministic dry-run-only flow report.",
            "Recommend the next gated manual action without enabling execution.",
        ],
        "allowed_paths": list(DEFAULT_ALLOWED_PATHS),
        "forbidden_paths": list(REQUIRED_FORBIDDEN_PATHS),
        "stop_conditions": list(STOP_CONDITIONS),
        "approval_required_before_execution": True,
        "flocky_validation_required": True,
        "execution_allowed_now": False,
        "runtime_wiring_allowed": False,
        "queue_mutation_allowed": False,
        "final_acceptance_claimed": False,
        "single_runtime_source_rule_preserved": True,
        "status_ownership": {
            key: {"owner": owner} for key, owner in REQUIRED_STATUS_OWNERS.items()
        },
        "next_action_recommendation": "approval_required",
        "warnings": [],
        "errors": [],
        "generated_by": GENERATED_BY,
        "deterministic_dry_run": True,
    }

    validation = _validate_report_object(report)
    report["warnings"] = validation["warnings"]
    report["errors"] = validation["errors"]
    report["next_action_recommendation"] = _next_action_from_preview(preview_validation_report, report["errors"])

    final_validation = _validate_report_object(report)
    report["warnings"] = final_validation["warnings"]
    report["errors"] = final_validation["errors"]
    report["next_action_recommendation"] = _next_action_from_preview(preview_validation_report, report["errors"])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build an Autopilot V1 dry-run-only flow report.")
    parser.add_argument("--task-path", required=True)
    parser.add_argument("--run-path", required=True)
    parser.add_argument("--source-task-id", required=True)
    parser.add_argument("--out", default="-")
    args = parser.parse_args(argv)

    try:
        report = build_dry_run_flow_report(
            task_path=args.task_path,
            run_path=args.run_path,
            source_task_id=args.source_task_id,
        )
        if args.out != "-":
            write_dry_run_report(args.out, report)
        print(json.dumps(report, indent=2))
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}, separators=(",", ":")))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
