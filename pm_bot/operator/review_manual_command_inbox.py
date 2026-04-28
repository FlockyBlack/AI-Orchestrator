import argparse
import importlib.util
import json
from pathlib import Path


TASK_ID = "PMBOT-OPERATOR-002-MANUAL-COMMAND-INBOX-REVIEW-QUEUE"
REVIEW_SCHEMA_VERSION = "manual_command_inbox_review.v1"
DEFAULT_INBOX_PATH = Path(__file__).with_name("manual_command_inbox_fixture.v1.json")
CONTRACT_PATH = Path(__file__).with_name("manual_command_contract.v1.json")
VALIDATOR_PATH = Path(__file__).with_name("validate_manual_command_contract.py")

NEXT_ACTION_LABELS = {
    "human_review_only": "queue_for_human_review_only",
    "record_only": "record_for_audit_trail_only",
    "artifact_lookup_by_human": "human_artifact_lookup_only",
    "integration_review_only": "integration_review_only",
}


def _parse_args():
    parser = argparse.ArgumentParser(description="Review inert local PMBOT manual command inbox records.")
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX_PATH)
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def _load_validator():
    spec = importlib.util.spec_from_file_location("pmbot_manual_command_validator_for_inbox", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _display_path(path: Path, root: Path):
    resolved = path.resolve()
    try:
        value = resolved.relative_to(root.resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


def _field(record, name):
    if isinstance(record, dict) and isinstance(record.get(name), str):
        return record[name]
    return None


def _record_core(index, record, contract):
    return {
        "source_record_index": index,
        "command_id": _field(record, "command_id"),
        "command_type": _field(record, "command_type"),
        "source_type": _field(record, "source_type"),
        "source_label": _field(record, "source_label"),
        "market_id": _field(record, "market_id"),
        "artifact_pointer": _field(record, "artifact_pointer"),
        "allowed_next_action": _field(record, "allowed_next_action"),
        "execution_authority": record.get("execution_authority") if isinstance(record, dict) else None,
        "requires_human_review": record.get("requires_human_review") if isinstance(record, dict) else None,
        "record_safety_flags": _record_safety_flags(record, contract),
    }


def _record_safety_flags(record, contract):
    required_flags = contract["required_safety_flags_false"]
    flags = record.get("safety_flags") if isinstance(record, dict) else None
    if not isinstance(flags, dict):
        return {
            "all_required_flags_false": False,
            "required_false_flag_count": len(required_flags),
            "triggered_flags": list(required_flags),
            "unexpected_flags": [],
        }

    triggered = [flag for flag in required_flags if flags.get(flag) is not False]
    unexpected = sorted(flag for flag in flags if flag not in required_flags)
    return {
        "all_required_flags_false": not triggered and not unexpected,
        "required_false_flag_count": len(required_flags),
        "triggered_flags": triggered,
        "unexpected_flags": unexpected,
    }


def _accepted_record(index, record, contract):
    item = _record_core(index, record, contract)
    item["operator_next_action_label"] = NEXT_ACTION_LABELS[record["allowed_next_action"]]
    item["validation_status"] = "accepted_for_manual_review_only"
    return item


def _needs_human_review_record(index, record, contract):
    item = _record_core(index, record, contract)
    item["operator_next_action_label"] = "needs_human_review_only"
    item["validation_status"] = "needs_human_review"
    item["human_review_reasons"] = [
        "record_explicitly_marked_needs_human_review",
        "requires_human_review_true",
    ]
    return item


def _rejected_record(index, record, contract, errors):
    item = _record_core(index, record, contract)
    item["operator_next_action_label"] = "reject_do_not_route"
    item["validation_status"] = "rejected"
    item["rejection_reasons"] = errors
    return item


def _review_records(records, validator, contract):
    accepted = []
    rejected = []
    needs_human_review = []

    for index, record in enumerate(records):
        errors = validator.validate_command(record, contract)
        if errors:
            rejected.append(_rejected_record(index, record, contract, errors))
        elif record["command_type"] == "mark_needs_human_review":
            needs_human_review.append(_needs_human_review_record(index, record, contract))
        else:
            accepted.append(_accepted_record(index, record, contract))

    return accepted, rejected, needs_human_review


def review_manual_command_inbox(root: Path, inbox_path: Path = DEFAULT_INBOX_PATH):
    validator = _load_validator()
    contract = validator.load_contract(CONTRACT_PATH)
    inbox = _load_json(inbox_path)
    records = inbox.get("records")
    if not isinstance(records, list):
        raise ValueError("manual command inbox fixture must contain a records array")

    accepted, rejected, needs_human_review = _review_records(records, validator, contract)
    safety_flags = {flag: False for flag in contract["required_safety_flags_false"]}

    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "source_inbox_path": _display_path(inbox_path, root),
        "source_inbox_schema_version": inbox.get("schema_version"),
        "contract_path": _display_path(CONTRACT_PATH, root),
        "validator_path": _display_path(VALIDATOR_PATH, root),
        "records_seen": len(records),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "needs_human_review_count": len(needs_human_review),
        "accepted_records": accepted,
        "rejected_records": rejected,
        "needs_human_review_records": needs_human_review,
        "safety_flags": safety_flags,
        "execution_authority": False,
        "commands_executed": 0,
        "orders_created": 0,
        "network_calls": 0,
        "next_safe_action": "human_review_queue_only",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Manual Command Inbox Review",
        "",
        "Deterministic local-only review queue for inert manual operator command records.",
        "",
        f"- Task ID: {report['task_id']}",
        f"- Source inbox: {report['source_inbox_path']}",
        f"- Records seen: {report['records_seen']}",
        f"- Accepted: {report['accepted_count']}",
        f"- Rejected: {report['rejected_count']}",
        f"- Needs human review: {report['needs_human_review_count']}",
        f"- Execution authority: {str(report['execution_authority']).lower()}",
        f"- Commands executed: {report['commands_executed']}",
        f"- Orders created: {report['orders_created']}",
        f"- Network calls: {report['network_calls']}",
        f"- Next safe action: {report['next_safe_action']}",
        "",
        "## Accepted Records",
    ]
    if report["accepted_records"]:
        for record in report["accepted_records"]:
            artifact = record["artifact_pointer"] or "none"
            lines.append(
                f"- {record['command_id']}: {record['operator_next_action_label']}; artifact: {artifact}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "## Needs Human Review"])
    if report["needs_human_review_records"]:
        for record in report["needs_human_review_records"]:
            reasons = ", ".join(record["human_review_reasons"])
            lines.append(f"- {record['command_id']}: {record['operator_next_action_label']}; reasons: {reasons}")
    else:
        lines.append("- none")

    lines.extend(["", "## Rejected Records"])
    if report["rejected_records"]:
        for record in report["rejected_records"]:
            reasons = ", ".join(record["rejection_reasons"])
            lines.append(f"- {record['command_id']}: {record['operator_next_action_label']}; reasons: {reasons}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "This report is an inert queue artifact. It does not execute commands, create orders, call APIs, start Telegram, or authorize runtime wiring.",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = review_manual_command_inbox(root, args.inbox)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
