import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUTOPILOT_ROOT = PROJECT_ROOT / "codex_auto" / "autopilot"
SCHEMA_PATH = AUTOPILOT_ROOT / "autopilot_preview_handoff.schema.v1.json"

SCHEMA_VERSION = "autopilot_preview_handoff.v1"
GENERATED_BY = "codex_auto.autopilot.build_preview_handoff"

REQUIRED_FIELDS = [
    "schema_version",
    "preview_only",
    "runtime_authority",
    "final_acceptance_authority",
    "source_task_id",
    "authoritative_task_path",
    "authoritative_run_path_or_ref",
    "handoff_owner",
    "codex_executor",
    "allowed_paths",
    "forbidden_paths",
    "approval_required",
    "flocky_validation_required",
    "stop_conditions",
    "single_runtime_source_rule_preserved",
    "execution_allowed_now",
    "runtime_wiring_allowed",
    "status_ownership",
    "generated_by",
    "deterministic_preview",
]

REQUIRED_FLAGS = {
    "preview_only": True,
    "runtime_authority": False,
    "final_acceptance_authority": False,
    "approval_required": True,
    "flocky_validation_required": True,
    "execution_allowed_now": False,
    "runtime_wiring_allowed": False,
    "single_runtime_source_rule_preserved": True,
    "deterministic_preview": True,
}

REQUIRED_FORBIDDEN_PATHS = [
    "tasks/",
    "runs/",
    "state/",
    "runtime/",
    "results/",
    "freeze/",
    "checkpoint/",
    "scripts/dispatcher.py",
    "scripts/run_codex.py",
]

REQUIRED_STATUS_OWNERS = {
    "runtime_status": "AI-Orchestrator",
    "handoff_status": "codex_auto",
    "codex_execution_status": "Codex result envelope",
    "flocky_validation_status": "Flocky",
    "final_acceptance_status": "AI-Orchestrator",
}

DEFAULT_ALLOWED_PATHS = [
    "codex_auto/autopilot/",
    "codex_auto/autopilot/tests/",
    "codex_auto/autopilot/fixtures/",
    "docs/AUTOPILOT_V1_PREVIEW_HANDOFF_ADAPTER.md",
    "docs/ORCH_AUTOPILOT_V1_CODEX_002_RESULT.json",
]

OUTPUT_ALLOWLIST = [
    "codex_auto/autopilot/tests/output/",
    "codex_auto/autopilot/fixtures/output/",
    "codex_auto/autopilot/tmp/",
]

FORBIDDEN_CLAIM_TERMS = {
    "final accepted": "forbidden_claim:final_accepted",
    "final_acceptance_claimed": "forbidden_claim:final_acceptance_claimed",
    "runtime done": "forbidden_claim:runtime_done",
    "source of truth transfer": "forbidden_claim:source_of_truth_transfer",
    "source-of-truth transfer": "forbidden_claim:source_of_truth_transfer",
    "authoritative runtime transferred": "forbidden_claim:runtime_transfer",
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def _normalize_path(value) -> str:
    return str(Path(str(value))).replace("\\", "/").lower()


def _is_under(base_ref: str, candidate_ref: str) -> bool:
    base = base_ref.rstrip("/")
    candidate = candidate_ref.rstrip("/")
    return candidate == base or candidate.startswith(base + "/")


def _scan_for_forbidden_claims(value, errors):
    if isinstance(value, dict):
        for item in value.values():
            _scan_for_forbidden_claims(item, errors)
        return
    if isinstance(value, list):
        for item in value:
            _scan_for_forbidden_claims(item, errors)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for term, code in FORBIDDEN_CLAIM_TERMS.items():
            if term in lowered:
                errors.append(code)


def _validate_source_payloads(task_data, run_data, source_task_id):
    if not isinstance(task_data, dict):
        raise ValueError("task_payload_must_be_object")
    if not isinstance(run_data, dict):
        raise ValueError("run_payload_must_be_object")
    task_id = task_data.get("task_id")
    if isinstance(task_id, str) and task_id.strip() and task_id != source_task_id:
        raise ValueError("source_task_id_mismatch:task")
    run_task_id = run_data.get("task_id")
    if isinstance(run_task_id, str) and run_task_id.strip() and run_task_id != source_task_id:
        raise ValueError("source_task_id_mismatch:run")


def validate_output_path(path_str: str) -> Path:
    candidate = _resolve_input_path(path_str)
    candidate_ref = _to_project_ref(candidate)
    candidate_norm = _normalize_path(candidate_ref)

    for forbidden in REQUIRED_FORBIDDEN_PATHS:
        forbidden_norm = _normalize_path(forbidden)
        if candidate_norm == forbidden_norm.rstrip("/") or candidate_norm.startswith(forbidden_norm.rstrip("/") + "/"):
            raise ValueError(f"output_path_forbidden:{candidate_ref}")

    for allowed_root in OUTPUT_ALLOWLIST:
        if _is_under(_normalize_path(allowed_root), candidate_norm):
            return candidate
    raise ValueError(f"output_path_not_in_allowed_preview_area:{candidate_ref}")


def build_preview_handoff(task_path: str, run_path: str, source_task_id: str):
    task_file = _resolve_input_path(task_path)
    run_file = _resolve_input_path(run_path)
    task_data = _load_json(task_file)
    run_data = _load_json(run_file)
    _validate_source_payloads(task_data, run_data, source_task_id)

    handoff = {
        "schema_version": SCHEMA_VERSION,
        "preview_only": True,
        "runtime_authority": False,
        "final_acceptance_authority": False,
        "source_task_id": source_task_id,
        "authoritative_task_path": _to_project_ref(task_file),
        "authoritative_run_path_or_ref": _to_project_ref(run_file),
        "handoff_owner": "codex_auto",
        "codex_executor": "Codex",
        "allowed_paths": list(DEFAULT_ALLOWED_PATHS),
        "forbidden_paths": list(REQUIRED_FORBIDDEN_PATHS),
        "approval_required": True,
        "flocky_validation_required": True,
        "stop_conditions": [
            "Stop if any write is requested outside codex_auto/autopilot/ or the documented result artifact path.",
            "Stop if runtime wiring, dispatcher edits, or run_codex edits are proposed.",
            "Stop if any step claims final acceptance, runtime completion transfer, or execution authorization now.",
        ],
        "single_runtime_source_rule_preserved": True,
        "execution_allowed_now": False,
        "runtime_wiring_allowed": False,
        "status_ownership": {
            "runtime_status": {"owner": "AI-Orchestrator"},
            "handoff_status": {"owner": "codex_auto"},
            "codex_execution_status": {"owner": "Codex result envelope"},
            "flocky_validation_status": {"owner": "Flocky"},
            "final_acceptance_status": {"owner": "AI-Orchestrator"},
        },
        "generated_by": GENERATED_BY,
        "deterministic_preview": True,
    }
    validate_preview_handoff(handoff)
    return handoff


def validate_preview_handoff(data):
    errors = []

    if not isinstance(data, dict):
        raise ValueError("preview_handoff_must_be_object")

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version_must_be:{SCHEMA_VERSION}")

    for field, expected_value in REQUIRED_FLAGS.items():
        if data.get(field) is not expected_value:
            errors.append(f"{field}_must_be_{str(expected_value).lower()}")

    for field in ("source_task_id", "authoritative_task_path", "authoritative_run_path_or_ref", "handoff_owner", "codex_executor", "generated_by"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field}_must_be_non_empty")

    allowed_paths = data.get("allowed_paths")
    if not isinstance(allowed_paths, list) or not allowed_paths or not all(isinstance(item, str) and item.strip() for item in allowed_paths):
        errors.append("allowed_paths_must_be_non_empty_list")

    forbidden_paths = data.get("forbidden_paths")
    if not isinstance(forbidden_paths, list):
        errors.append("forbidden_paths_must_be_list")
        forbidden_paths = []
    else:
        forbidden_norm = {_normalize_path(item) for item in forbidden_paths}
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

    _scan_for_forbidden_claims(data, errors)

    if errors:
        raise ValueError(";".join(sorted(set(errors))))
    return data


def load_schema():
    return _load_json(SCHEMA_PATH)


def write_preview_handoff(output_path: str, handoff):
    destination = validate_output_path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a preview-only Autopilot V1 handoff envelope.")
    parser.add_argument("--task-path", required=True)
    parser.add_argument("--run-path", required=True)
    parser.add_argument("--source-task-id", required=True)
    parser.add_argument("--out", default="-")
    args = parser.parse_args(argv)

    try:
        handoff = build_preview_handoff(
            task_path=args.task_path,
            run_path=args.run_path,
            source_task_id=args.source_task_id,
        )
        if args.out != "-":
            write_preview_handoff(args.out, handoff)
        print(json.dumps(handoff, indent=2))
    except ValueError as exc:
        print(json.dumps({"status": "invalid", "errors": str(exc).split(";")}, separators=(",", ":")))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
