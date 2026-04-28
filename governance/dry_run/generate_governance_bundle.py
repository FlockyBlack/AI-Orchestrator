import argparse
import json
from pathlib import Path
from typing import Any, Dict

SCHEMA_VERSION = "v1"
ACCEPTED_WARNINGS = {
    "network_risk": "mixed",
    "api_risk": "mixed",
    "wallet_risk": "mixed",
    "private_key_risk": "mixed",
    "execution_risk": "mixed",
    "live_trading_risk": "mixed",
    "dependency_risk": "docs_only",
}
SAFETY_FLAGS = {
    "dispatcher_touched": False,
    "run_codex_touched": False,
    "execution_loop_started": False,
    "active_task_files_changed": False,
    "code_execution_enabled": False,
    "network_used": False,
    "credentials_touched": False,
}
FIXTURE_KEYS = {
    "task_id",
    "source_run_id",
    "runtime_status",
    "runtime_source_path",
    "blocking_issues",
    "accepted_warnings",
    "critic_verdict",
    "governance_decision",
    "final_status_allowed",
}
ALLOWED_RUNTIME_STATUSES = {"warning_accepted", "pass", "failed", "blocked"}
ALLOWED_CRITIC_VERDICTS = {"pass", "warning", "fail", "blocked"}
ALLOWED_GOVERNANCE_DECISIONS = {
    "accept_final_done",
    "accept_with_warnings",
    "blocked",
    "continue_review",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a dry-run governance bundle from a fixture.")
    parser.add_argument("fixture_path")
    parser.add_argument("--output")
    return parser.parse_args()


def _load_fixture(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("fixture must be a JSON object")
    extra_keys = set(data.keys()) - FIXTURE_KEYS
    if extra_keys:
        raise ValueError(f"unexpected fixture keys: {sorted(extra_keys)}")
    missing = [key for key in FIXTURE_KEYS if key not in data]
    if missing:
        raise ValueError(f"missing fixture keys: {missing}")
    return data


def _assert_expected_warnings(accepted_warnings: Dict[str, Any]) -> None:
    if accepted_warnings != ACCEPTED_WARNINGS:
        raise ValueError("accepted warnings must match the preserved governance warning set exactly")


def _derive_openclaw_next_status(runtime_status: str, blocking_issues: Any) -> str:
    if runtime_status == "blocked" or blocking_issues:
        return "blocked"
    return "review"


def _derive_final_status(critic_verdict: str, governance_decision: str, final_status_allowed: bool, blocking_issues: Any) -> str:
    if blocking_issues:
        return "blocked"
    if critic_verdict == "pass" and governance_decision == "accept_final_done" and final_status_allowed:
        return "done"
    if critic_verdict == "warning" and governance_decision == "accept_with_warnings" and final_status_allowed:
        return "done"
    if critic_verdict in {"fail", "blocked"} or governance_decision == "blocked":
        return "blocked"
    return "review"


def _build_bundle(source_fixture: Dict[str, Any]) -> Dict[str, Any]:
    runtime_status = source_fixture["runtime_status"]
    critic_verdict = source_fixture["critic_verdict"]
    governance_decision = source_fixture["governance_decision"]
    final_status_allowed = source_fixture["final_status_allowed"]
    blocking_issues = list(source_fixture["blocking_issues"])
    accepted_warnings = dict(source_fixture["accepted_warnings"])

    if runtime_status not in ALLOWED_RUNTIME_STATUSES:
        raise ValueError(f"unsupported runtime_status: {runtime_status}")
    if critic_verdict not in ALLOWED_CRITIC_VERDICTS:
        raise ValueError(f"unsupported critic_verdict: {critic_verdict}")
    if governance_decision not in ALLOWED_GOVERNANCE_DECISIONS:
        raise ValueError(f"unsupported governance_decision: {governance_decision}")
    if not isinstance(final_status_allowed, bool):
        raise ValueError("final_status_allowed must be boolean")
    if not isinstance(blocking_issues, list):
        raise ValueError("blocking_issues must be a list")
    _assert_expected_warnings(accepted_warnings)

    task_id = source_fixture["task_id"]
    source_run_id = source_fixture["source_run_id"]
    openclaw_next_status = _derive_openclaw_next_status(runtime_status, blocking_issues)
    final_governance_status = _derive_final_status(
        critic_verdict,
        governance_decision,
        final_status_allowed,
        blocking_issues,
    )
    can_mark_done = final_governance_status == "done"

    return {
        "schema_version": SCHEMA_VERSION,
        "bundle_id": f"gov_bundle_{source_run_id}",
        "task_id": task_id,
        "source_run_id": source_run_id,
        "created_at": "2026-04-25T04:58:00Z",
        "runtime_source": {
            "path": source_fixture["runtime_source_path"],
            "type": "freeze_record",
            "runtime_truth": True,
        },
        "adapter_envelope": {
            "ref": f"openclaw_envelope:{source_run_id}",
            "task_id": task_id,
            "source_run_id": source_run_id,
            "status": runtime_status,
            "openclaw_next_status": openclaw_next_status,
            "accepted_warnings": accepted_warnings,
        },
        "lifecycle_event_draft": {
            "ref": f"lifecycle_event_draft:lcd_{source_run_id}",
            "task_id": task_id,
            "source_run_id": source_run_id,
            "to_status": openclaw_next_status,
            "safety_flags": dict(SAFETY_FLAGS),
        },
        "critic_input_draft": {
            "ref": f"critic_input_draft:cid_{source_run_id}",
            "task_id": task_id,
            "source_run_id": source_run_id,
            "critic_required": True,
            "accepted_warnings": accepted_warnings,
            "safety_flags": dict(SAFETY_FLAGS),
        },
        "critic_output": {
            "critic_verdict": critic_verdict,
            "can_mark_done": can_mark_done,
        },
        "quarantine_record": None,
        "governance_decision_record": {
            "governance_decision": governance_decision,
            "final_status_allowed": final_status_allowed,
            "accepted_warnings": accepted_warnings,
            "task_id": task_id,
            "source_run_id": source_run_id,
        },
        "final_governance_status": final_governance_status,
    }


def _validate_output_path(output_path: Path, root: Path) -> None:
    dry_run_root = (root / "governance" / "dry_run").resolve()
    resolved_output = output_path.resolve()
    try:
        resolved_output.relative_to(dry_run_root)
    except ValueError as exc:
        raise ValueError("--output must stay under governance/dry_run/") from exc


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    fixture_path = Path(args.fixture_path)
    if not fixture_path.is_absolute():
        fixture_path = (root / fixture_path).resolve()

    fixture = _load_fixture(fixture_path)
    bundle = _build_bundle(fixture)
    rendered = json.dumps(bundle, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = (root / output_path).resolve()
        _validate_output_path(output_path, root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
