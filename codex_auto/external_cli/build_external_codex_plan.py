import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLAN_ROOT = PROJECT_ROOT / "codex_auto" / "external_cli" / "plans"
PROMPT_MANIFEST = PROJECT_ROOT / "codex_auto" / "prompts" / "PMBOT-BATCH-001.prompt_manifest.json"
PROMPT_PACK = PROJECT_ROOT / "codex_auto" / "prompts" / "PMBOT-BATCH-001.codex_prompt.txt"
PROMOTION_DECISION = PROJECT_ROOT / "codex_auto" / "tasks" / "promotion_decisions" / "PMBOT-BATCH-001.promotion_decision.json"
PLAN_PATH = PLAN_ROOT / "PMBOT-BATCH-001.external_codex_plan.json"
PREVIEW_PATH = PLAN_ROOT / "PMBOT-BATCH-001.command_preview.txt"


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_text_if_same_or_missing(path: Path, content: str):
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            if json.loads(existing) != json.loads(content):
                raise ValueError(f"artifact_conflict:{path}")
            return
        if existing != content:
            raise ValueError(f"artifact_conflict:{path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _command_preview():
    return (
        "preview_only\n"
        "do_not_execute_now\n"
        "requires_human_approval\n"
        "requires_flocky_validation\n"
        "future_command:\n"
        "codex exec --cd C:\\Users\\OpenC\\Documents\\AI-Orchestrator -- < codex_auto\\prompts\\PMBOT-BATCH-001.codex_prompt.txt\n"
    )


def build_plan():
    manifest = _load_json(PROMPT_MANIFEST)
    decision = _load_json(PROMOTION_DECISION)
    _ = PROMPT_PACK.read_text(encoding="utf-8")

    if decision.get("approved_for_ready_promotion") is not True:
        raise ValueError("promotion_decision_not_ready_only_approved")
    if decision.get("approved_for_execution") is not False:
        raise ValueError("promotion_decision_execution_must_remain_false")
    if manifest.get("execution_allowed_now") is not False:
        raise ValueError("manifest_execution_allowed_now_must_be_false")
    if manifest.get("external_codex_cli_allowed_now") is not False:
        raise ValueError("manifest_external_codex_cli_allowed_now_must_be_false")

    allowed_paths = []
    for candidate_ref in manifest["candidate_task_refs"]:
        candidate = _load_json(PROJECT_ROOT / candidate_ref)
        for allowed_path in candidate.get("allowed_paths", []):
            if allowed_path not in allowed_paths:
                allowed_paths.append(allowed_path)

    command_preview = _command_preview()
    plan = {
        "schema_version": "external_codex_plan.v1",
        "plan_id": "PMBOT-BATCH-001",
        "created_at": decision.get("decided_at"),
        "prompt_pack_ref": "codex_auto/prompts/PMBOT-BATCH-001.codex_prompt.txt",
        "prompt_manifest_ref": "codex_auto/prompts/PMBOT-BATCH-001.prompt_manifest.json",
        "candidate_task_refs": manifest["candidate_task_refs"],
        "command_preview": command_preview.strip(),
        "execution_allowed_now": False,
        "external_codex_cli_allowed_now": False,
        "requires_human_approval_before_execution": True,
        "requires_flocky_review_before_execution": True,
        "expected_result_path": "codex_auto/tasks/needs_flocky_review/PMBOT-BATCH-001.external_codex_result.json",
        "expected_validation_after_execution": [
            "Promotion to ready must remain a separate approved task.",
            "Future external execution output must enter Flocky review before any done claim.",
            "No runtime wiring is authorized by this plan."
        ],
        "allowed_paths": allowed_paths,
        "forbidden_paths": [
            "scripts/dispatcher.py",
            "scripts/run_codex.py",
            "tasks/",
            "state/",
            "runtime/",
            "results/",
            "freeze/",
            "checkpoint/"
        ],
        "safety_check": {
            "execution_allowed_now": False,
            "external_codex_cli_allowed_now": False,
            "runtime_wiring_allowed": False,
            "preview_only": True,
            "human_approval_required_before_execution": True,
            "flocky_review_required_before_execution": True,
            "network_used": False,
            "api_used": False,
            "wallet_used": False,
            "private_key_used": False,
            "trading_used": False,
            "single_runtime_source_rule_preserved": True
        }
    }
    return plan, command_preview


def main(argv):
    if len(argv) != 1:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "errors": ["usage: build_external_codex_plan.py"],
                },
                separators=(",", ":"),
            )
        )
        return 2

    try:
        plan, preview = build_plan()
        _write_text_if_same_or_missing(PLAN_PATH, json.dumps(plan, indent=2) + "\n")
        _write_text_if_same_or_missing(PREVIEW_PATH, preview)
    except ValueError as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}, separators=(",", ":")))
        return 1

    print(json.dumps({"status": "valid", "plan_path": str(PLAN_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"), "preview_path": str(PREVIEW_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/")}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
