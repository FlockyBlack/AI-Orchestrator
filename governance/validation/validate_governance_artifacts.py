import json
import sys
from pathlib import Path

EXPECTED_WARNINGS = {
    "network_risk": "mixed",
    "api_risk": "mixed",
    "wallet_risk": "mixed",
    "private_key_risk": "mixed",
    "execution_risk": "mixed",
    "live_trading_risk": "mixed",
    "dependency_risk": "docs_only",
}
FORBIDDEN_TERMS = [
    "runtime execution authority",
    "wallet surface",
    "private key surface",
    "trading surface",
]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _errors_for_bundle(data):
    errors = []
    required = [
        "task_id",
        "source_run_id",
        "runtime_source",
        "adapter_envelope",
        "lifecycle_event_draft",
        "critic_input_draft",
        "critic_output",
        "governance_decision_record",
        "final_governance_status",
    ]
    for key in required:
        if key not in data:
            errors.append(f"missing:{key}")
    if errors:
        return errors

    task_id = data["task_id"]
    source_run_id = data["source_run_id"]

    runtime_source = data["runtime_source"]
    if runtime_source.get("runtime_truth") is not True:
        errors.append("runtime_source_not_reference_truth")
    if not runtime_source.get("path"):
        errors.append("missing_runtime_source_path")

    for section in ["adapter_envelope", "lifecycle_event_draft", "critic_input_draft", "governance_decision_record"]:
        obj = data[section]
        if obj.get("task_id") != task_id:
            errors.append(f"task_id_mismatch:{section}")
        if obj.get("source_run_id") != source_run_id:
            errors.append(f"source_run_id_mismatch:{section}")

    for section in ["lifecycle_event_draft", "critic_input_draft"]:
        if "safety_flags" not in data[section]:
            errors.append(f"missing_safety_flags:{section}")

    warnings_obj = data["governance_decision_record"].get("accepted_warnings")
    if warnings_obj != EXPECTED_WARNINGS:
        errors.append("accepted_warnings_not_preserved")
    if data["adapter_envelope"].get("accepted_warnings") != EXPECTED_WARNINGS:
        errors.append("adapter_warnings_not_preserved")
    if data["critic_input_draft"].get("accepted_warnings") != EXPECTED_WARNINGS:
        errors.append("critic_input_warnings_not_preserved")

    critic_output = data.get("critic_output", {})
    verdict = critic_output.get("critic_verdict")
    can_mark_done = critic_output.get("can_mark_done")
    governance_decision = data["governance_decision_record"].get("governance_decision")
    final_status_allowed = data["governance_decision_record"].get("final_status_allowed")
    final_status = data.get("final_governance_status")

    if final_status == "done":
        valid_done = (
            (verdict == "pass" and can_mark_done is True and governance_decision == "accept_final_done" and final_status_allowed is True)
            or (verdict == "warning" and can_mark_done is True and governance_decision == "accept_with_warnings" and final_status_allowed is True)
        )
        if not valid_done:
            errors.append("final_done_requires_valid_critic_gate")

    quarantine = data.get("quarantine_record")
    if isinstance(quarantine, dict) and quarantine.get("quarantine_present") is True and not quarantine.get("resolved", False) and final_status == "done":
        errors.append("quarantine_blocks_done")

    serialized = json.dumps(data, ensure_ascii=False).lower()
    if any(term in serialized for term in FORBIDDEN_TERMS):
        errors.append("forbidden_authority_or_surface_reference")

    return errors


def validate_file(path_str: str):
    path = Path(path_str)
    data = _load_json(path)
    artifact_type = "governance_review_bundle"
    errors = _errors_for_bundle(data)
    result = {
        "status": "valid" if not errors else "invalid",
        "file": str(path),
        "artifact_type": artifact_type,
        "errors": errors,
        "warnings_preserved": data.get("governance_decision_record", {}).get("accepted_warnings") == EXPECTED_WARNINGS if isinstance(data, dict) else False,
        "final_done_allowed": data.get("final_governance_status") == "done" and not errors if isinstance(data, dict) else False,
        "single_runtime_source_rule_preserved": True if isinstance(data, dict) and data.get("runtime_source", {}).get("runtime_truth") is True else False,
    }
    return result


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "invalid", "file": None, "artifact_type": None, "errors": ["usage: validate_governance_artifacts.py <file>"], "warnings_preserved": False, "final_done_allowed": False, "single_runtime_source_rule_preserved": False}, separators=(",", ":")))
        return 2
    result = validate_file(argv[1])
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
