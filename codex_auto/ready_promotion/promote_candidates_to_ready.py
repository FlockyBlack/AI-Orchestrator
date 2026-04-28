import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
READY_ROOT = PROJECT_ROOT / "codex_auto" / "tasks" / "ready"
PROMOTION_DECISION_PATH = PROJECT_ROOT / "codex_auto" / "tasks" / "promotion_decisions" / "PMBOT-BATCH-001.promotion_decision.json"
PROMOTION_REQUEST_PATH = PROJECT_ROOT / "codex_auto" / "tasks" / "promotion_requests" / "PMBOT-BATCH-001.promotion_request.json"
PROMPT_MANIFEST_PATH = PROJECT_ROOT / "codex_auto" / "prompts" / "PMBOT-BATCH-001.prompt_manifest.json"
EXTERNAL_PLAN_PATH = PROJECT_ROOT / "codex_auto" / "external_cli" / "plans" / "PMBOT-BATCH-001.external_codex_plan.json"
COMMAND_PREVIEW_PATH = PROJECT_ROOT / "codex_auto" / "external_cli" / "plans" / "PMBOT-BATCH-001.command_preview.txt"
READY_MANIFEST_PATH = READY_ROOT / "PMBOT-BATCH-001.ready_manifest.json"
EXECUTION_PREVIEW_PATH = READY_ROOT / "PMBOT-BATCH-001.execution_preview.json"
READY_PROMOTION_ID = "PMBOT-BATCH-001-ready-promotion"
READY_TASK_NAMES = [
    "PMBOT-005-PAPER-SIMULATION.task.json",
    "PMBOT-006-RISK-LIMITS.task.json",
    "PMBOT-007-FEES-SLIPPAGE.task.json",
    "PMBOT-008-RESEARCH-DASHBOARD.task.json",
    "PMBOT-009-FIXTURE-POSTMORTEM.task.json",
    "PMBOT-010-STATIC-SAFETY-AUDIT.task.json",
]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_for_compare(value):
    if isinstance(value, dict):
        return {key: _normalize_for_compare(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_for_compare(item) for item in value]
    return value


def _write_json_if_same_or_missing(path: Path, payload):
    rendered = json.dumps(payload, indent=2) + "\n"
    if path.exists():
        if _normalize_for_compare(_load_json(path)) != _normalize_for_compare(payload):
            raise ValueError(f"artifact_conflict:{path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def _resolve_relpath(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _ensure_forbidden_scope(candidate):
    serialized = " ".join(candidate.get("forbidden_scope", [])).lower()
    required_terms = (
        "runtime wiring",
        "external codex cli execution",
        "network usage",
        "api usage",
        "wallet usage",
        "private key usage",
        "trading behavior",
        "real orders",
        "final flocky/openclaw done claim",
        "second runtime source of truth",
    )
    missing = [term for term in required_terms if term not in serialized]
    if missing:
        raise ValueError(f"candidate_forbidden_scope_missing:{candidate.get('materialized_task_id')}:{','.join(missing)}")


def _validate_candidate(candidate_path: Path):
    candidate = _load_json(candidate_path)
    if candidate.get("queue_state") != "candidate":
        raise ValueError(f"candidate_not_in_candidate_state:{_resolve_relpath(candidate_path)}")
    if candidate.get("approved_for_execution") is not False:
        raise ValueError(f"candidate_execution_must_be_false:{_resolve_relpath(candidate_path)}")
    if candidate.get("runtime_wiring_allowed") is not False:
        raise ValueError(f"candidate_runtime_wiring_must_be_false:{_resolve_relpath(candidate_path)}")
    if candidate.get("external_codex_cli_allowed") is not False:
        raise ValueError(f"candidate_external_codex_cli_must_be_false:{_resolve_relpath(candidate_path)}")
    if candidate.get("dry_run_default") is not True:
        raise ValueError(f"candidate_dry_run_default_must_be_true:{_resolve_relpath(candidate_path)}")
    if candidate.get("flocky_validation_required") is not True:
        raise ValueError(f"candidate_flocky_validation_required_must_be_true:{_resolve_relpath(candidate_path)}")
    _ensure_forbidden_scope(candidate)
    return candidate


def _build_ready_task(candidate_path: Path, candidate: dict):
    codex_task_id = candidate["codex_task_id"]
    return {
        "schema_version": "v1",
        "queue_task_id": f"QUEUE-{codex_task_id}",
        "codex_task_id": codex_task_id,
        "queue_state": "ready",
        "mode": candidate["mode"],
        "executor": candidate["executor"],
        "title": candidate["title"],
        "summary": candidate["summary"],
        "source_backlog_task_id": candidate["source_backlog_task_id"],
        "source_backlog_path": candidate["source_backlog_path"],
        "generated_prompt_ref": candidate["generated_prompt_ref"],
        "allowed_paths": candidate["allowed_paths"],
        "forbidden_paths": candidate["forbidden_paths"],
        "allowed_scope": candidate["allowed_scope"],
        "forbidden_scope": candidate["forbidden_scope"],
        "done_criteria": candidate["done_criteria"],
        "requires_human_approval": True,
        "approved_for_execution": False,
        "dry_run_default": True,
        "flocky_validation_required": True,
        "runtime_wiring_allowed": False,
        "external_codex_cli_allowed": False,
        "execution_allowed_now": False,
        "human_approval_required_before_execution": True,
        "flocky_review_required_before_execution": True,
        "source_candidate_path": _resolve_relpath(candidate_path),
        "source_promotion_decision": _resolve_relpath(PROMOTION_DECISION_PATH)
    }


def _build_ready_manifest(decision: dict, request: dict):
    ready_task_refs = [f"codex_auto/tasks/ready/{name}" for name in READY_TASK_NAMES]
    return {
        "schema_version": "ready_promotion.v1",
        "ready_promotion_id": READY_PROMOTION_ID,
        "source_promotion_decision": "codex_auto/tasks/promotion_decisions/PMBOT-BATCH-001.promotion_decision.json",
        "source_candidate_refs": request["candidate_task_refs"],
        "ready_task_refs": ready_task_refs,
        "ready_manifest_ref": "codex_auto/tasks/ready/PMBOT-BATCH-001.ready_manifest.json",
        "promoted_at": decision["decided_at"],
        "promoted_by": "codex_local_ready_promotion",
        "promotion_mode": "ready_only_no_execution",
        "approved_for_ready_promotion": True,
        "approved_for_execution": False,
        "execution_allowed_now": False,
        "external_codex_cli_allowed_now": False,
        "runtime_wiring_allowed": False,
        "human_approval_required_before_execution": True,
        "flocky_review_required_before_execution": True,
        "prompt_pack_ref": request["prompt_pack_ref"],
        "prompt_manifest_ref": request["prompt_manifest_ref"],
        "external_codex_plan_ref": "codex_auto/external_cli/plans/PMBOT-BATCH-001.external_codex_plan.json",
        "command_preview_ref": "codex_auto/external_cli/plans/PMBOT-BATCH-001.command_preview.txt",
        "safety_check": {
            "runtime_changed": False,
            "dispatcher_touched": False,
            "run_codex_touched": False,
            "active_task_files_touched": False,
            "freeze_record_modified": False,
            "result_records_modified": False,
            "checkpoint_records_modified": False,
            "network_used": False,
            "api_used": False,
            "wallet_used": False,
            "private_key_used": False,
            "trading_used": False,
            "external_codex_cli_invoked": False,
            "generated_prompt_executed": False,
            "single_runtime_source_rule_preserved": True
        },
        "notes": [
            "codex_auto-local ready promotion only.",
            "Ready PMBOT tasks remain non-executable until separate human approval and Flocky validation."
        ]
    }


def _build_execution_preview(manifest: dict):
    return {
        "schema_version": "execution_preview.v1",
        "preview_id": "PMBOT-BATCH-001-execution-preview",
        "ready_manifest_ref": manifest["ready_manifest_ref"],
        "prompt_pack_ref": manifest["prompt_pack_ref"],
        "command_preview_ref": manifest["command_preview_ref"],
        "ready_task_refs": manifest["ready_task_refs"],
        "execution_allowed_now": False,
        "external_codex_cli_allowed_now": False,
        "generated_prompt_executed": False,
        "runtime_wiring_allowed": False,
        "notes": [
            "preview_only",
            "do_not_execute_now",
            "requires human approval",
            "requires Flocky validation"
        ]
    }


def promote():
    if not PROMOTION_DECISION_PATH.exists():
        raise ValueError("missing_promotion_decision")
    if not PROMOTION_REQUEST_PATH.exists():
        raise ValueError("missing_promotion_request")
    if not PROMPT_MANIFEST_PATH.exists():
        raise ValueError("missing_prompt_manifest")
    if not EXTERNAL_PLAN_PATH.exists():
        raise ValueError("missing_external_plan")
    if not COMMAND_PREVIEW_PATH.exists():
        raise ValueError("missing_command_preview")

    decision = _load_json(PROMOTION_DECISION_PATH)
    request = _load_json(PROMOTION_REQUEST_PATH)
    prompt_manifest = _load_json(PROMPT_MANIFEST_PATH)
    external_plan = _load_json(EXTERNAL_PLAN_PATH)

    if decision.get("approved_for_ready_promotion") is not True:
        raise ValueError("promotion_decision_not_approved_for_ready")
    if decision.get("approved_for_execution") is not False:
        raise ValueError("promotion_decision_execution_must_be_false")
    if decision.get("external_codex_cli_allowed_now") is not False:
        raise ValueError("promotion_decision_external_codex_cli_must_be_false")
    if decision.get("runtime_wiring_allowed") is not False:
        raise ValueError("promotion_decision_runtime_wiring_must_be_false")

    if prompt_manifest.get("execution_allowed_now") is not False:
        raise ValueError("prompt_manifest_execution_allowed_now_must_be_false")
    if prompt_manifest.get("external_codex_cli_allowed_now") is not False:
        raise ValueError("prompt_manifest_external_codex_cli_must_be_false")
    if external_plan.get("execution_allowed_now") is not False:
        raise ValueError("external_plan_execution_allowed_now_must_be_false")
    if external_plan.get("external_codex_cli_allowed_now") is not False:
        raise ValueError("external_plan_external_codex_cli_allowed_now_must_be_false")

    created_or_validated = []
    for candidate_ref, ready_name in zip(request["candidate_task_refs"], READY_TASK_NAMES):
        candidate_path = PROJECT_ROOT / candidate_ref
        if not candidate_path.exists():
            raise ValueError(f"missing_candidate:{candidate_ref}")
        candidate = _validate_candidate(candidate_path)
        ready_payload = _build_ready_task(candidate_path, candidate)
        ready_path = READY_ROOT / ready_name
        _write_json_if_same_or_missing(ready_path, ready_payload)
        created_or_validated.append(_resolve_relpath(ready_path))

    manifest = _build_ready_manifest(decision, request)
    preview = _build_execution_preview(manifest)
    _write_json_if_same_or_missing(READY_MANIFEST_PATH, manifest)
    _write_json_if_same_or_missing(EXECUTION_PREVIEW_PATH, preview)

    return {
        "status": "done",
        "ready_tasks_created_or_validated": created_or_validated,
        "ready_manifest": _resolve_relpath(READY_MANIFEST_PATH),
        "execution_preview": _resolve_relpath(EXECUTION_PREVIEW_PATH),
        "execution_allowed_now": False,
        "external_codex_cli_allowed_now": False,
        "runtime_wiring_allowed": False
    }


def main(argv):
    if len(argv) != 1:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "errors": ["usage: promote_candidates_to_ready.py"],
                    "ready_tasks_created_or_validated": [],
                    "ready_manifest": None,
                    "execution_preview": None,
                    "execution_allowed_now": False,
                    "external_codex_cli_allowed_now": False,
                    "runtime_wiring_allowed": False
                },
                separators=(",", ":"),
            )
        )
        return 2
    try:
        result = promote()
    except ValueError as exc:
        result = {
            "status": "blocked",
            "errors": [str(exc)],
            "ready_tasks_created_or_validated": [],
            "ready_manifest": None,
            "execution_preview": None,
            "execution_allowed_now": False,
            "external_codex_cli_allowed_now": False,
            "runtime_wiring_allowed": False
        }
        print(json.dumps(result, separators=(",", ":")))
        return 1

    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
