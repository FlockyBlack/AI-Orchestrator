import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
READY_ROOT = PROJECT_ROOT / "codex_auto" / "tasks" / "ready"
REQUIRED_MANIFEST_FIELDS = [
    "schema_version",
    "ready_promotion_id",
    "source_promotion_decision",
    "source_candidate_refs",
    "ready_task_refs",
    "ready_manifest_ref",
    "promoted_at",
    "promoted_by",
    "promotion_mode",
    "approved_for_ready_promotion",
    "approved_for_execution",
    "execution_allowed_now",
    "external_codex_cli_allowed_now",
    "runtime_wiring_allowed",
    "human_approval_required_before_execution",
    "flocky_review_required_before_execution",
    "prompt_pack_ref",
    "prompt_manifest_ref",
    "external_codex_plan_ref",
    "command_preview_ref",
    "safety_check",
    "notes",
]
REQUIRED_READY_FIELDS = [
    "schema_version",
    "queue_task_id",
    "codex_task_id",
    "queue_state",
    "mode",
    "executor",
    "title",
    "summary",
    "source_backlog_task_id",
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
    "execution_allowed_now",
    "human_approval_required_before_execution",
    "flocky_review_required_before_execution",
    "source_candidate_path",
    "source_promotion_decision",
]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _resolve_project_path(value: str):
    raw = Path(value)
    candidate = raw.resolve() if raw.is_absolute() else (PROJECT_ROOT / raw).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return candidate if candidate.exists() else None
    return candidate


def _scan_claims(text: str, errors, prefix: str):
    lowered = text.lower()
    for term, code in {
        "final flocky/openclaw done": "final_done_claim_forbidden",
        "final flocky done": "final_done_claim_forbidden",
        "final openclaw done": "final_done_claim_forbidden",
        "runtime truth": "runtime_truth_claim_forbidden",
        "source of truth": "runtime_truth_claim_forbidden",
    }.items():
        if term in lowered:
            errors.append(f"{prefix}:{code}")


def _scan_authorization_terms(text: str, errors, prefix: str):
    lowered = text.lower()
    for term, code in {
        "network": "network_forbidden",
        "api": "api_forbidden",
        "wallet": "wallet_forbidden",
        "private key": "private_key_forbidden",
        "trading": "trading_forbidden",
        "real order": "real_order_forbidden",
    }.items():
        if term in lowered:
            errors.append(f"{prefix}:{code}")


def _validate_ready_task(ready_path: Path):
    errors = []
    task = _load_json(ready_path)
    for field in REQUIRED_READY_FIELDS:
        if field not in task:
            errors.append(f"missing:{field}")
    if errors:
        return {"status": "invalid", "file": str(ready_path), "errors": sorted(set(errors))}

    if task.get("queue_state") != "ready":
        errors.append("queue_state_must_be_ready")
    if task.get("approved_for_execution") is not False:
        errors.append("approved_for_execution_must_be_false")
    if task.get("execution_allowed_now") is not False:
        errors.append("execution_allowed_now_must_be_false")
    if task.get("external_codex_cli_allowed") is not False:
        errors.append("external_codex_cli_allowed_must_be_false")
    if task.get("runtime_wiring_allowed") is not False:
        errors.append("runtime_wiring_allowed_must_be_false")
    if task.get("requires_human_approval") is not True:
        errors.append("requires_human_approval_must_be_true")
    if task.get("human_approval_required_before_execution") is not True:
        errors.append("human_approval_required_before_execution_must_be_true")
    if task.get("flocky_review_required_before_execution") is not True:
        errors.append("flocky_review_required_before_execution_must_be_true")
    if task.get("flocky_validation_required") is not True:
        errors.append("flocky_validation_required_must_be_true")
    if task.get("dry_run_default") is not True:
        errors.append("dry_run_default_must_be_true")

    source_candidate = _resolve_project_path(task.get("source_candidate_path", ""))
    if source_candidate is None or not source_candidate.exists():
        errors.append("source_candidate_path_missing")
    source_decision = _resolve_project_path(task.get("source_promotion_decision", ""))
    if source_decision is None or not source_decision.exists():
        errors.append("source_promotion_decision_missing")

    forbidden_paths_text = " ".join(task.get("forbidden_paths", [])).lower()
    for required in ("scripts/dispatcher.py", "scripts/run_codex.py", "tasks/", "state/", "runtime", "result", "freeze", "checkpoint"):
        if required not in forbidden_paths_text:
            errors.append(f"forbidden_paths_missing:{required}")

    combined_claims = " ".join(
        [
            task.get("title", ""),
            task.get("summary", ""),
            " ".join(task.get("done_criteria", [])),
        ]
    )
    _scan_claims(combined_claims, errors, "content")
    _scan_authorization_terms(" ".join(task.get("allowed_scope", [])), errors, "allowed_scope")
    forbidden_scope_text = " ".join(task.get("forbidden_scope", [])).lower()
    for required in (
        "network usage",
        "api usage",
        "wallet usage",
        "private key usage",
        "trading behavior",
        "real orders",
        "final flocky/openclaw done claim",
        "second runtime source of truth",
        "runtime wiring",
    ):
        if required not in forbidden_scope_text:
            errors.append(f"forbidden_scope_missing:{required}")

    return {
        "status": "valid" if not errors else "invalid",
        "file": (
            str(ready_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
            if ready_path.is_relative_to(PROJECT_ROOT)
            else str(ready_path)
        ),
        "errors": sorted(set(errors)),
    }


def validate_manifest(path: Path):
    resolved_manifest_path = path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    manifest = _load_json(resolved_manifest_path)
    errors = []
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            errors.append(f"missing:{field}")
    if errors:
        return {
            "status": "invalid",
            "file": str(resolved_manifest_path),
            "errors": sorted(set(errors)),
            "ready_task_results": [],
        }

    if manifest.get("schema_version") != "ready_promotion.v1":
        errors.append("schema_version_must_be_ready_promotion.v1")
    if manifest.get("approved_for_ready_promotion") is not True:
        errors.append("approved_for_ready_promotion_must_be_true")
    if manifest.get("approved_for_execution") is not False:
        errors.append("approved_for_execution_must_be_false")
    if manifest.get("execution_allowed_now") is not False:
        errors.append("execution_allowed_now_must_be_false")
    if manifest.get("external_codex_cli_allowed_now") is not False:
        errors.append("external_codex_cli_allowed_now_must_be_false")
    if manifest.get("runtime_wiring_allowed") is not False:
        errors.append("runtime_wiring_allowed_must_be_false")
    if manifest.get("human_approval_required_before_execution") is not True:
        errors.append("human_approval_required_before_execution_must_be_true")
    if manifest.get("flocky_review_required_before_execution") is not True:
        errors.append("flocky_review_required_before_execution_must_be_true")

    for ref_field in (
        "source_promotion_decision",
        "prompt_pack_ref",
        "prompt_manifest_ref",
        "external_codex_plan_ref",
        "command_preview_ref",
    ):
        resolved = _resolve_project_path(manifest.get(ref_field, ""))
        if resolved is None or not resolved.exists():
            errors.append(f"missing_ref:{ref_field}")

    if _resolve_project_path(manifest.get("ready_manifest_ref", "")) != resolved_manifest_path:
        errors.append("ready_manifest_ref_must_match_manifest_path")

    serialized_manifest = json.dumps({"notes": manifest.get("notes", []), "promotion_mode": manifest.get("promotion_mode", "")}, ensure_ascii=False)
    _scan_claims(serialized_manifest, errors, "manifest")

    ready_task_results = []
    for ready_ref in manifest.get("ready_task_refs", []):
        ready_path = _resolve_project_path(ready_ref)
        if ready_path is None or not ready_path.exists():
            errors.append(f"missing_ready_task:{ready_ref}")
            continue
        ready_task_results.append(_validate_ready_task(ready_path))
    for result in ready_task_results:
        if result["status"] != "valid":
            errors.extend(result["errors"])

    return {
        "status": "valid" if not errors else "invalid",
        "file": (
            str(resolved_manifest_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
            if resolved_manifest_path.is_relative_to(PROJECT_ROOT)
            else str(resolved_manifest_path)
        ),
        "errors": sorted(set(errors)),
        "ready_task_results": ready_task_results,
    }


def main(argv):
    if len(argv) != 2:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "file": None,
                    "errors": ["usage: validate_ready_promotion.py <ready_manifest.json>"],
                    "ready_task_results": [],
                },
                separators=(",", ":"),
            )
        )
        return 2
    result = validate_manifest(Path(argv[1]))
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
