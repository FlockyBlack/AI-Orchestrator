import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DECISION_ROOT = PROJECT_ROOT / "codex_auto" / "tasks" / "promotion_decisions"
PROMPT_ROOT = PROJECT_ROOT / "codex_auto" / "prompts"
VALIDATOR_PATH = PROJECT_ROOT / "codex_auto" / "promotion" / "validate_promotion_request.py"
BACKLOG_VALIDATOR_PATH = PROJECT_ROOT / "codex_auto" / "backlog" / "validate_materialized_tasks.py"


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_module_function(module_path: Path, function_name: str):
    namespace = {"__name__": module_path.stem, "__file__": str(module_path)}
    exec(module_path.read_text(encoding="utf-8"), namespace)
    return namespace[function_name]


def _write_if_same_or_missing(path: Path, payload):
    rendered = json.dumps(payload, indent=2) + "\n"
    if path.exists():
        existing = _load_json(path)
        if _canonicalize(existing) != _canonicalize(payload):
            raise ValueError(f"decision_artifact_conflict:{path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def _canonicalize(value):
    if isinstance(value, dict):
        canonical = {}
        for key, item in value.items():
            if key == "file" and isinstance(item, str):
                canonical[key] = _normalize_result_file_field({"file": item})["file"]
            else:
                canonical[key] = _canonicalize(item)
        return canonical
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value


def _normalize_result_file_field(result):
    result = dict(result)
    file_value = result.get("file")
    if not file_value:
        return result
    file_path = Path(file_value)
    if not file_path.is_absolute():
        file_path = (PROJECT_ROOT / file_path).resolve()
    try:
        result["file"] = str(file_path.relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        result["file"] = str(file_path).replace("\\", "/")
    return result


def _collect_forbidden_scope(candidate_payloads, manifest, request):
    serialized = json.dumps(
        {
            "candidate_titles": [item.get("title", "") for item in candidate_payloads],
            "candidate_summaries": [item.get("summary", "") for item in candidate_payloads],
            "candidate_done_criteria": [item.get("done_criteria", []) for item in candidate_payloads],
            "request_reason": request.get("reason", ""),
            "request_requested_by": request.get("requested_by", ""),
            "manifest_prompt_id": manifest.get("prompt_id", ""),
        },
        ensure_ascii=False,
    ).lower()
    findings = {}
    for term in (
        "final flocky/openclaw done",
        "final flocky done",
        "final openclaw done",
        "runtime truth",
        "source of truth",
    ):
        if term in serialized:
            findings[f"forbidden_term:{term}"] = "present"
    return findings


def build_decision(request_path: Path):
    validate_request = _load_module_function(VALIDATOR_PATH, "validate_file")
    validate_materialized = _load_module_function(BACKLOG_VALIDATOR_PATH, "validate_file")

    request = _load_json(request_path)
    request_validation = _normalize_result_file_field(validate_request(str(request_path)))
    findings = {"promotion_request": request_validation}

    candidate_payloads = []
    if request_validation["status"] == "valid":
        for candidate_ref in request["candidate_task_refs"]:
            candidate_path = PROJECT_ROOT / candidate_ref
            candidate_result = _normalize_result_file_field(validate_materialized(str(candidate_path)))
            findings[candidate_ref] = candidate_result
            if candidate_path.exists():
                candidate_payloads.append(_load_json(candidate_path))

    manifest_path = PROJECT_ROOT / request.get("prompt_manifest_ref", "")
    prompt_path = PROJECT_ROOT / request.get("prompt_pack_ref", "")
    manifest = _load_json(manifest_path) if manifest_path.exists() else {}
    materialization_path = PROJECT_ROOT / request.get("source_materialization_report", "")
    materialization_report = _load_json(materialization_path) if materialization_path.exists() else {}

    manifest_findings = {}
    if not manifest_path.exists():
        manifest_findings["prompt_manifest_ref"] = "missing"
    else:
        if manifest.get("execution_allowed_now") is not False:
            manifest_findings["execution_allowed_now"] = "must_be_false"
        if manifest.get("requires_flocky_review_before_execution") is not True:
            manifest_findings["requires_flocky_review_before_execution"] = "must_be_true"
        if manifest.get("requires_human_approval_before_execution") is not True:
            manifest_findings["requires_human_approval_before_execution"] = "must_be_true"
        if manifest.get("runtime_wiring_allowed") is not False:
            manifest_findings["runtime_wiring_allowed"] = "must_be_false"
        if manifest.get("external_codex_cli_allowed_now") is not False:
            manifest_findings["external_codex_cli_allowed_now"] = "must_be_false"
        if request.get("candidate_task_refs") != manifest.get("candidate_task_refs"):
            manifest_findings["candidate_task_refs"] = "must_match_request"
    findings["prompt_manifest"] = manifest_findings

    prompt_findings = {}
    if not prompt_path.exists():
        prompt_findings["prompt_pack_ref"] = "missing"
    findings["prompt_pack"] = prompt_findings

    materialization_findings = {}
    if not materialization_path.exists():
        materialization_findings["source_materialization_report"] = "missing"
    else:
        expected_candidates = request.get("candidate_task_refs", [])
        if materialization_report.get("candidates_created") != expected_candidates:
            materialization_findings["candidates_created"] = "must_match_request"
        validation_summary = materialization_report.get("validation_summary", {})
        if validation_summary.get("generated_prompt_not_executed") is not True:
            materialization_findings["generated_prompt_not_executed"] = "must_be_true"
    findings["materialization_report"] = materialization_findings

    candidate_state_findings = {}
    if len(candidate_payloads) != 6:
        candidate_state_findings["candidate_count"] = "must_equal_6"
    for candidate in candidate_payloads:
        task_id = candidate.get("materialized_task_id", "unknown")
        if candidate.get("queue_state") != "candidate":
            candidate_state_findings[f"{task_id}:queue_state"] = "must_be_candidate"
        if candidate.get("approved_for_execution") is not False:
            candidate_state_findings[f"{task_id}:approved_for_execution"] = "must_be_false"
        if candidate.get("runtime_wiring_allowed") is not False:
            candidate_state_findings[f"{task_id}:runtime_wiring_allowed"] = "must_be_false"
        if candidate.get("external_codex_cli_allowed") is not False:
            candidate_state_findings[f"{task_id}:external_codex_cli_allowed"] = "must_be_false"
    findings["candidate_bundle"] = candidate_state_findings

    forbidden_scope_findings = _collect_forbidden_scope(candidate_payloads, manifest, request)
    findings["forbidden_scope"] = forbidden_scope_findings

    candidate_valid = all(
        findings.get(candidate_ref, {}).get("status") == "valid" for candidate_ref in request.get("candidate_task_refs", [])
    )
    request_valid = request_validation["status"] == "valid"
    manifest_valid = not manifest_findings
    prompt_valid = not prompt_findings
    materialization_valid = not materialization_findings
    candidate_state_valid = not candidate_state_findings
    forbidden_scope_valid = not forbidden_scope_findings

    approved_for_ready_promotion = all(
        (
            request_valid,
            candidate_valid,
            manifest_valid,
            prompt_valid,
            materialization_valid,
            candidate_state_valid,
            forbidden_scope_valid,
        )
    )
    decision = "approve_for_ready_promotion" if approved_for_ready_promotion else "hold_for_review"

    return {
        "schema_version": "promotion_decision.v1",
        "promotion_decision_id": f"{request.get('promotion_request_id', 'unknown')}-decision",
        "promotion_request_id": request.get("promotion_request_id"),
        "decided_at": request.get("requested_at"),
        "decided_by": "flocky_local_review",
        "decision": decision,
        "candidate_task_refs": request.get("candidate_task_refs", []),
        "prompt_pack_ref": request.get("prompt_pack_ref"),
        "validation_findings": findings,
        "approved_for_ready_promotion": approved_for_ready_promotion,
        "approved_for_execution": False,
        "runtime_wiring_allowed": False,
        "external_codex_cli_allowed_now": False,
        "human_approval_required_before_execution": True,
        "notes": [
            "Review-only decision. No candidate was promoted to ready.",
            "External Codex CLI remains disallowed in this phase."
        ],
        "recommended_next_action": (
            "Human approval and a separate promotion task are still required before any ready promotion."
            if approved_for_ready_promotion
            else "Resolve validation findings before any promotion review proceeds."
        ),
    }


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("promotion_request")
    parser.add_argument("--write-decision", action="store_true")
    args = parser.parse_args(argv[1:])

    request_path = Path(args.promotion_request)
    decision = build_decision(request_path)

    if args.write_decision:
        output_path = DECISION_ROOT / "PMBOT-BATCH-001.promotion_decision.json"
        try:
            _write_if_same_or_missing(output_path, decision)
        except ValueError as exc:
            print(
                json.dumps(
                    {
                        "status": "invalid",
                        "error": str(exc),
                        "decision": decision,
                    },
                    separators=(",", ":"),
                )
            )
            return 1

    print(json.dumps(decision, separators=(",", ":")))
    return 0 if decision["approved_for_ready_promotion"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
