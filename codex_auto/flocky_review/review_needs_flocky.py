import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ARTIFACT = PROJECT_ROOT / "codex_auto" / "runs" / "CODEX-AUTO-TINY-001" / "fixture_output.json"
DONE_ROOT = PROJECT_ROOT / "codex_auto" / "tasks" / "done"
FAILED_ROOT = PROJECT_ROOT / "codex_auto" / "tasks" / "failed"
QUARANTINE_ROOT = PROJECT_ROOT / "codex_auto" / "tasks" / "quarantine"
APPROVED_TASK_ID = "CODEX-AUTO-TINY-001"
APPROVED_QUEUE_TASK_ID = "QUEUE-CODEX-AUTO-TINY-001"


def _utc_timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _build_review(result_path: Path):
    resolved_result_path = result_path.resolve()
    result = _load_json(result_path)
    findings = {}

    if result.get("queue_task_id") != APPROVED_QUEUE_TASK_ID:
        findings["queue_task_id"] = "unsupported_queue_task_id"
    if result.get("codex_task_id") != APPROVED_TASK_ID:
        findings["codex_task_id"] = "unsupported_codex_task_id"
    if result.get("flocky_validation_required") is not True:
        findings["flocky_validation_required"] = "must_be_true"
    if result.get("next_queue_state") != "needs_flocky_review":
        findings["next_queue_state"] = "must_be_needs_flocky_review"

    safety_check = result.get("safety_check")
    if not isinstance(safety_check, dict):
        findings["safety_check"] = "missing_or_invalid"
        safety_check = {}
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
            if safety_check.get(key) is not False:
                findings[key] = "must_be_false"
        if safety_check.get("single_runtime_source_rule_preserved") is not True:
            findings["single_runtime_source_rule_preserved"] = "must_be_true"

    serialized_result = json.dumps(result, ensure_ascii=False).lower()
    if "final done" in serialized_result:
        findings["final_done"] = "forbidden_claim"
    if "runtime source of truth" in serialized_result or "runtime truth" in serialized_result:
        findings["runtime_truth"] = "forbidden_claim"
    if not OUTPUT_ARTIFACT.exists():
        findings["durable_artifact"] = "missing_fixture_output"

    if findings:
        review_status = "fail"
        next_state = "failed"
    else:
        review_status = "pass"
        next_state = "done"

    return {
        "schema_version": "v1",
        "review_id": "FLOCKY-REVIEW-QUEUE-CODEX-AUTO-TINY-001",
        "queue_task_id": APPROVED_QUEUE_TASK_ID,
        "codex_task_id": APPROVED_TASK_ID,
        "reviewed_at": _utc_timestamp(),
        "reviewed_by": "flocky_local_review",
        "source_result_path": str(resolved_result_path.relative_to(PROJECT_ROOT.resolve())).replace("\\", "/"),
        "source_queue_state": "needs_flocky_review",
        "review_status": review_status,
        "validation_findings": findings,
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
            "single_runtime_source_rule_preserved": True
        },
        "allowed_next_queue_state": next_state,
        "final_flocky_done_claimed": False,
        "runtime_wiring_allowed": False,
        "notes": []
    }


def _review_output_path(review_status: str):
    filename = "FLOCKY-REVIEW-QUEUE-CODEX-AUTO-TINY-001.review.json"
    if review_status == "pass":
        return DONE_ROOT / filename
    if review_status == "quarantine":
        return QUARANTINE_ROOT / filename
    return FAILED_ROOT / filename


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("result_record")
    parser.add_argument("--write-review", action="store_true")
    args = parser.parse_args(argv[1:])

    result_path = Path(args.result_record)
    review = _build_review(result_path)

    if args.write_review:
        _write_json(_review_output_path(review["review_status"]), review)

    print(json.dumps(review, separators=(",", ":")))
    return 0 if review["review_status"] in {"pass", "warning"} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
