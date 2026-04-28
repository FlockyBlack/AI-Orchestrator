import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "autopilot_preview_handoff.v1"

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

EXACT_FORBIDDEN_CLAIMS = {
    "final_accepted": True,
    "runtime_done": True,
    "runtime_truth_transferred": True,
    "authoritative_runtime_owner": "codex_auto",
    "source_of_truth": "codex_auto",
}

FORBIDDEN_TEXT_CLAIMS = {
    "codex_auto is source of truth": "forbidden_claim:codex_auto_source_of_truth",
    "source_of_truth=codex_auto": "forbidden_claim:codex_auto_source_of_truth",
    "source of truth transfer": "forbidden_claim:source_of_truth_transfer",
    "source_of_truth_transfer": "forbidden_claim:source_of_truth_transfer",
    "source-of-truth transfer": "forbidden_claim:source_of_truth_transfer",
    "final accepted": "forbidden_claim:final_accepted",
    "runtime done": "forbidden_claim:runtime_done",
    "runtime_truth_transferred": "forbidden_claim:runtime_truth_transferred",
    "authoritative_runtime_owner=codex_auto": "forbidden_claim:authoritative_runtime_owner_codex_auto",
}


def _normalize_path(value) -> str:
    return str(Path(str(value))).replace("\\", "/").lower()


def _sorted_unique(items):
    return sorted(set(items))


def _load_json_file(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_preview_data(preview_path: str):
    if preview_path == "-":
        return json.load(sys.stdin)

    candidate = Path(preview_path)
    if not candidate.is_absolute():
        candidate = (PROJECT_ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return _load_json_file(candidate)


def _scan_claims(value, errors):
    if isinstance(value, dict):
        for key, expected in EXACT_FORBIDDEN_CLAIMS.items():
            if key in value and value[key] == expected:
                errors.append(f"forbidden_claim:{key}")
        for key, nested in value.items():
            if key == "status_ownership" and isinstance(nested, dict):
                final_status = nested.get("final_acceptance_status")
                if isinstance(final_status, dict) and final_status.get("owner") in {"Flocky", "Codex result envelope", "codex_auto"}:
                    errors.append("forbidden_claim:final_acceptance_owner_drift")
                runtime_status = nested.get("runtime_status")
                if isinstance(runtime_status, dict) and runtime_status.get("owner") == "codex_auto":
                    errors.append("forbidden_claim:runtime_status_owner_drift")
            _scan_claims(nested, errors)
        return
    if isinstance(value, list):
        for item in value:
            _scan_claims(item, errors)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for term, code in FORBIDDEN_TEXT_CLAIMS.items():
            if term in lowered:
                errors.append(code)


def _validate_required_fields(data, errors):
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")


def _validate_required_flags(data, errors):
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version_must_be:{SCHEMA_VERSION}")

    for field, expected in REQUIRED_FLAGS.items():
        if data.get(field) is not expected:
            errors.append(f"{field}_must_be_{str(expected).lower()}")


def _validate_string_field(data, field, errors):
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field}_must_be_non_empty")


def _validate_forbidden_paths(data, errors):
    forbidden_paths = data.get("forbidden_paths")
    if not isinstance(forbidden_paths, list):
        errors.append("forbidden_paths_must_be_list")
        return

    forbidden_norm = {_normalize_path(item) for item in forbidden_paths if isinstance(item, str)}
    for required in REQUIRED_FORBIDDEN_PATHS:
        if _normalize_path(required) not in forbidden_norm:
            errors.append(f"missing_forbidden_path:{required}")


def _validate_allowed_paths(data, errors):
    allowed_paths = data.get("allowed_paths")
    if not isinstance(allowed_paths, list) or not allowed_paths or not all(isinstance(item, str) and item.strip() for item in allowed_paths):
        errors.append("allowed_paths_must_be_non_empty_list")


def _validate_stop_conditions(data, errors):
    stop_conditions = data.get("stop_conditions")
    if not isinstance(stop_conditions, list) or not stop_conditions or not all(isinstance(item, str) and item.strip() for item in stop_conditions):
        errors.append("stop_conditions_must_be_non_empty_list")


def _validate_status_ownership(data, errors):
    ownership = data.get("status_ownership")
    if not isinstance(ownership, dict):
        errors.append("status_ownership_must_be_object")
        return

    for status_key, owner in REQUIRED_STATUS_OWNERS.items():
        nested = ownership.get(status_key)
        if not isinstance(nested, dict):
            errors.append(f"missing_status_ownership:{status_key}")
            continue
        if nested.get("owner") != owner:
            errors.append(f"{status_key}_owner_must_be:{owner}")


def _validate_authoritative_ref(field_name, value, expected_prefix, warnings, errors):
    if not isinstance(value, str) or not value.strip():
        return

    normalized = _normalize_path(value)
    if normalized.startswith(_normalize_path(expected_prefix)):
        return

    if "fixture" in normalized or "example" in normalized:
        warnings.append(f"example_reference_path:{field_name}")
        return

    errors.append(f"bad_authoritative_path_claim:{field_name}")


def validate_preview_handoff_data(data):
    errors = []
    warnings = []

    if not isinstance(data, dict):
        errors.append("preview_handoff_must_be_object")
        return {
            "type": "AUTOPILOT_PREVIEW_HANDOFF_VALIDATION_REPORT",
            "valid": False,
            "preview_only": False,
            "runtime_authority": None,
            "final_acceptance_authority": None,
            "execution_allowed_now": None,
            "runtime_wiring_allowed": None,
            "single_runtime_source_rule_preserved": False,
            "errors": errors,
            "warnings": warnings,
        }

    _validate_required_fields(data, errors)
    _validate_required_flags(data, errors)
    for field in (
        "source_task_id",
        "authoritative_task_path",
        "authoritative_run_path_or_ref",
        "handoff_owner",
        "codex_executor",
        "generated_by",
    ):
        _validate_string_field(data, field, errors)

    _validate_allowed_paths(data, errors)
    _validate_forbidden_paths(data, errors)
    _validate_stop_conditions(data, errors)
    _validate_status_ownership(data, errors)
    _scan_claims(data, errors)

    _validate_authoritative_ref(
        "authoritative_task_path",
        data.get("authoritative_task_path"),
        "tasks/",
        warnings,
        errors,
    )
    _validate_authoritative_ref(
        "authoritative_run_path_or_ref",
        data.get("authoritative_run_path_or_ref"),
        "runs/",
        warnings,
        errors,
    )

    report = {
        "type": "AUTOPILOT_PREVIEW_HANDOFF_VALIDATION_REPORT",
        "valid": not errors,
        "preview_only": data.get("preview_only"),
        "runtime_authority": data.get("runtime_authority"),
        "final_acceptance_authority": data.get("final_acceptance_authority"),
        "execution_allowed_now": data.get("execution_allowed_now"),
        "runtime_wiring_allowed": data.get("runtime_wiring_allowed"),
        "single_runtime_source_rule_preserved": data.get("single_runtime_source_rule_preserved"),
        "errors": _sorted_unique(errors),
        "warnings": _sorted_unique(warnings),
    }
    return report


def validate_preview_handoff_file(preview_path: str):
    return validate_preview_handoff_data(_load_preview_data(preview_path))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate an Autopilot V1 preview handoff artifact.")
    parser.add_argument("--preview-path", required=True, help="Path to preview handoff JSON or '-' for stdin.")
    args = parser.parse_args(argv)

    try:
        report = validate_preview_handoff_file(args.preview_path)
    except json.JSONDecodeError as exc:
        report = {
            "type": "AUTOPILOT_PREVIEW_HANDOFF_VALIDATION_REPORT",
            "valid": False,
            "preview_only": False,
            "runtime_authority": None,
            "final_acceptance_authority": None,
            "execution_allowed_now": None,
            "runtime_wiring_allowed": None,
            "single_runtime_source_rule_preserved": False,
            "errors": [f"invalid_json:{exc.msg}"],
            "warnings": [],
        }
    except OSError as exc:
        report = {
            "type": "AUTOPILOT_PREVIEW_HANDOFF_VALIDATION_REPORT",
            "valid": False,
            "preview_only": False,
            "runtime_authority": None,
            "final_acceptance_authority": None,
            "execution_allowed_now": None,
            "runtime_wiring_allowed": None,
            "single_runtime_source_rule_preserved": False,
            "errors": [f"io_error:{exc}"],
            "warnings": [],
        }

    print(json.dumps(report, separators=(",", ":")))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
