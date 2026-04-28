import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-PAPER-005-PAPER-DECISION-SIMULATION-GATE"
SCHEMA_VERSION = "paper_decision_simulation_gate.v1"
MARKDOWN_VERSION = "paper_decision_simulation_gate_report.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_SPEC = ROOT / "pm_bot" / "paper" / "paper_decision_policy_spec.v1.json"
DEFAULT_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_gate.v1.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_gate.v1.md"
DEFAULT_EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "expected_paper_decision_simulation_gate.v1.json"

ACCEPTED_POLICY_SPEC_STATUS = "paper_decision_policy_constraints_defined"
ACCEPTED_PREVIEW_STATUS = "ready_for_future_paper_decision_policy_design"
PASSED_STATUS = "paper_simulation_gate_passed_for_manual_review"
WATCH_ONLY_STATUS = "paper_watch_only"
NEEDS_MORE_REVIEW_STATUS = "paper_blocked_needs_more_review"
POLICY_BLOCKED_STATUS = "paper_blocked_by_policy"
ALLOWED_SIMULATION_STATUSES = (
    PASSED_STATUS,
    WATCH_ONLY_STATUS,
    NEEDS_MORE_REVIEW_STATUS,
    POLICY_BLOCKED_STATUS,
)
GATE_RECORD_FIELDS = (
    "market_id",
    "simulation_status",
    "policy_findings",
    "blocking_reasons",
    "watch_only_reasons",
    "required_manual_followup",
    "simulation_notes",
    "safety_flags",
    "paper_orders_created",
)
SUMMARY_FIELDS = (
    "policy_specs_read",
    "gate_records_written",
    PASSED_STATUS,
    WATCH_ONLY_STATUS,
    NEEDS_MORE_REVIEW_STATUS,
    POLICY_BLOCKED_STATUS,
    "paper_orders_created",
)
POLICY_SPEC_RECORD_FIELDS = {
    "market_id",
    "accepted_preview_status",
    "policy_spec_status",
    "source_policy_record_present",
    "source_final_dossier_draft_present",
    "future_input_source_fields",
    "policy_boundaries",
}
PREVIEW_RECORD_FIELDS = {
    "market_id",
    "title_question",
    "event_id",
    "event_title",
    "category",
    "packet_type",
    "deadline",
    "current_yes_price",
    "liquidity",
    "volume",
    "resolution_criteria_summary",
    "evidence_inventory_summary",
    "uncertainty_register_summary",
    "missing_information_review",
    "open_questions",
    "human_review_summary",
    "paper_readiness_status",
    "paper_policy_status",
    "simulation_preview_status",
    "blocked_reasons",
    "next_manual_action",
}
INPUT_FIELD_EXCEPTIONS = {"current_yes_price"}
OUTPUT_FIELD_EXCEPTIONS = {"paper_orders_created"}
PROHIBITED_FIELD_NAMES = (
    "side",
    "buy",
    "sell",
    "yes",
    "no",
    "outcome_side",
    "selected_outcome",
    "probability",
    "implied_probability",
    "fair_probability",
    "ev",
    "expected_value",
    "edge",
    "score",
    "confidence_score",
    "size",
    "stake",
    "quantity",
    "order",
    "order_plan",
    "paper_order",
    "recommendation",
    "decision",
    "trade_decision",
)
PROHIBITED_FIELD_TOKENS = set(PROHIBITED_FIELD_NAMES) | {
    "sides",
    "buys",
    "sells",
    "probabilities",
    "expected_values",
    "edges",
    "scores",
    "stakes",
    "quantities",
    "orders",
    "recommendations",
    "decisions",
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run a deterministic offline paper simulation gate for later manual review."
    )
    parser.add_argument("--policy-spec", default=str(DEFAULT_POLICY_SPEC.relative_to(ROOT)))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT.relative_to(ROOT)))
    parser.add_argument("--markdown-output", default=str(DEFAULT_MARKDOWN_OUTPUT.relative_to(ROOT)))
    parser.add_argument("--expected-json-output", default=str(DEFAULT_EXPECTED_JSON_OUTPUT.relative_to(ROOT)))
    return parser.parse_args(argv)


def _resolve_path(path):
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _display_path(path):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _records_list(payload, field):
    records = payload.get(field)
    if not isinstance(records, list):
        raise ValueError(f"payload must contain {field} list")
    return [record for record in records if isinstance(record, dict)]


def _by_market_id(records):
    by_market_id = {}
    for record in records:
        market_id = _clean_text(record.get("market_id"))
        if market_id:
            by_market_id[market_id] = record
    return by_market_id


def _field_tokens(key):
    lower = str(key).lower()
    normalized_chars = []
    previous_was_separator = False
    for char in lower:
        if char.isalnum():
            normalized_chars.append(char)
            previous_was_separator = False
        elif not previous_was_separator:
            normalized_chars.append("_")
            previous_was_separator = True
    normalized_key = "".join(normalized_chars).strip("_")
    parts = [part for part in normalized_key.split("_") if part]
    tokens = {lower, normalized_key}
    tokens.update(parts)
    for index in range(len(parts) - 1):
        tokens.add(f"{parts[index]}_{parts[index + 1]}")
    for index in range(len(parts) - 2):
        tokens.add(f"{parts[index]}_{parts[index + 1]}_{parts[index + 2]}")
    return {token for token in tokens if token}


def _walk_keys(value, prefix=""):
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            yield path, key_text
            yield from _walk_keys(nested, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_keys(item, f"{prefix}[{index}]")


def _has_prohibited_key(value, exceptions):
    for _path, key in _walk_keys(value):
        if key in exceptions:
            continue
        if _field_tokens(key) & PROHIBITED_FIELD_TOKENS:
            return True
    return False


def validate_simulation_status(status):
    if status not in ALLOWED_SIMULATION_STATUSES:
        raise ValueError(f"unknown simulation_status: {status}")
    return status


def validate_gate_payload(payload):
    for record in _records_list(payload, "gate_records"):
        validate_simulation_status(record.get("simulation_status"))
        if list(record) != list(GATE_RECORD_FIELDS):
            raise ValueError("gate record field order or field set is invalid")
        if record.get("paper_orders_created") != 0:
            raise ValueError("paper_orders_created must be exactly 0")
    summary = payload.get("gate_summary")
    if not isinstance(summary, dict) or summary.get("paper_orders_created") != 0:
        raise ValueError("gate summary must keep paper_orders_created at 0")
    if _has_prohibited_key(payload, OUTPUT_FIELD_EXCEPTIONS):
        raise ValueError("gate payload contains a prohibited output field")
    return payload


def _source_preview_path(policy_spec_payload, policy_spec_path):
    source_path = _clean_text(policy_spec_payload.get("source_preview_path"))
    if not source_path:
        raise ValueError("policy spec does not declare source_preview_path")
    return _resolve_path(source_path)


def _required_source_fields(policy_spec_record):
    mapping = policy_spec_record.get("future_input_source_fields")
    if not isinstance(mapping, dict):
        return {}
    return {
        _clean_text(input_name): _clean_text(source_name)
        for input_name, source_name in mapping.items()
        if _clean_text(input_name) and _clean_text(source_name)
    }


def _present(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return all(_present(item) for item in value)
    return True


def _missing_required_inputs(policy_spec_record, preview_record):
    missing = []
    for source_field in _required_source_fields(policy_spec_record).values():
        if source_field == "open_questions":
            if not isinstance(preview_record.get(source_field), list):
                missing.append(source_field)
            continue
        if not _present(preview_record.get(source_field)):
            missing.append(source_field)
    return sorted(set(missing))


def _source_has_extra_fields(record, allowed_fields):
    if not isinstance(record, dict):
        return False
    return any(key not in allowed_fields for key in record)


def _gate_record(policy_spec_record, preview_record):
    blocking_reasons = []
    watch_only_reasons = []
    policy_findings = []

    if _has_prohibited_key(policy_spec_record, INPUT_FIELD_EXCEPTIONS) or _has_prohibited_key(
        preview_record, INPUT_FIELD_EXCEPTIONS
    ):
        blocking_reasons.append("prohibited_source_field_present")
    if _source_has_extra_fields(policy_spec_record, POLICY_SPEC_RECORD_FIELDS):
        blocking_reasons.append("unexpected_policy_spec_field_present")
    if _source_has_extra_fields(preview_record, PREVIEW_RECORD_FIELDS):
        blocking_reasons.append("unexpected_preview_field_present")
    if _clean_text(policy_spec_record.get("policy_spec_status")) != ACCEPTED_POLICY_SPEC_STATUS:
        blocking_reasons.append("policy_spec_status_not_accepted")
    if _clean_text(policy_spec_record.get("accepted_preview_status")) != ACCEPTED_PREVIEW_STATUS:
        blocking_reasons.append("preview_status_not_accepted_by_spec")
    if not policy_spec_record.get("source_policy_record_present"):
        blocking_reasons.append("source_policy_record_missing")
    if not policy_spec_record.get("source_final_dossier_draft_present"):
        blocking_reasons.append("source_final_dossier_draft_missing")
    if not isinstance(preview_record, dict):
        blocking_reasons.append("source_preview_record_missing")
        preview_record = {}
    elif _clean_text(preview_record.get("simulation_preview_status")) != ACCEPTED_PREVIEW_STATUS:
        blocking_reasons.append("source_preview_status_not_accepted")

    if not blocking_reasons:
        missing_inputs = _missing_required_inputs(policy_spec_record, preview_record)
        if missing_inputs:
            blocking_reasons.append("required_local_inputs_missing")
    if not blocking_reasons and isinstance(preview_record.get("open_questions"), list) and preview_record["open_questions"]:
        watch_only_reasons.append("manual_questions_present")

    if blocking_reasons:
        if "prohibited_source_field_present" in blocking_reasons:
            simulation_status = POLICY_BLOCKED_STATUS
        else:
            simulation_status = NEEDS_MORE_REVIEW_STATUS
    elif watch_only_reasons:
        simulation_status = WATCH_ONLY_STATUS
    else:
        simulation_status = PASSED_STATUS

    if not blocking_reasons:
        policy_findings.extend(
            [
                "policy_spec_chain_present",
                "source_preview_chain_present",
                "manual_review_inputs_present",
                "local_artifact_gate_complete",
            ]
        )
    else:
        policy_findings.append("manual_review_gate_not_ready")

    return {
        "market_id": _clean_text(policy_spec_record.get("market_id")),
        "simulation_status": simulation_status,
        "policy_findings": policy_findings,
        "blocking_reasons": sorted(set(blocking_reasons)),
        "watch_only_reasons": sorted(set(watch_only_reasons)),
        "required_manual_followup": [
            "manual_review_required_before_later_paper_process",
            "confirm_gate_findings_outside_automation",
        ],
        "simulation_notes": [
            "Offline gate only; artifact permits later human review of a paper-only simulation workflow.",
            "Zero executable actions were produced.",
        ],
        "safety_flags": [
            "offline_only",
            "local_artifacts_only",
            "inert_review_artifact",
            "zero_executable_actions",
        ],
        "paper_orders_created": 0,
    }


def _accepted_policy_spec_records(policy_spec_records):
    accepted = [
        record
        for record in policy_spec_records
        if _clean_text(record.get("policy_spec_status")) == ACCEPTED_POLICY_SPEC_STATUS
        and _clean_text(record.get("accepted_preview_status")) == ACCEPTED_PREVIEW_STATUS
    ]
    return sorted(accepted, key=lambda item: _clean_text(item.get("market_id")))


def _build_summary(policy_specs_read, gate_records):
    summary = {
        "policy_specs_read": policy_specs_read,
        "gate_records_written": len(gate_records),
        PASSED_STATUS: 0,
        WATCH_ONLY_STATUS: 0,
        NEEDS_MORE_REVIEW_STATUS: 0,
        POLICY_BLOCKED_STATUS: 0,
        "paper_orders_created": 0,
    }
    for record in gate_records:
        status = validate_simulation_status(record["simulation_status"])
        summary[status] += 1
    return summary


def build_paper_decision_simulation_gate(
    policy_spec_path=DEFAULT_POLICY_SPEC,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    policy_spec_path = _resolve_path(policy_spec_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    policy_spec_payload = _load_json(policy_spec_path)
    preview_path = _source_preview_path(policy_spec_payload, policy_spec_path)
    preview_payload = _load_json(preview_path)

    policy_spec_records = _records_list(policy_spec_payload, "policy_specs")
    preview_by_market_id = _by_market_id(_records_list(preview_payload, "preview_records"))
    eligible_policy_specs = _accepted_policy_spec_records(policy_spec_records)
    gate_records = [
        _gate_record(record, preview_by_market_id.get(_clean_text(record.get("market_id"))))
        for record in eligible_policy_specs
    ]
    gate_records.sort(key=lambda item: item["market_id"])
    market_ids = sorted(record["market_id"] for record in gate_records if record["market_id"])
    payload = {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_policy_spec_path": _display_path(policy_spec_path),
        "source_policy_spec_schema_version": _clean_text(policy_spec_payload.get("schema_version")),
        "source_preview_path": _display_path(preview_path),
        "source_preview_schema_version": _clean_text(preview_payload.get("schema_version")),
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "allowed_simulation_statuses": list(ALLOWED_SIMULATION_STATUSES),
        "gate_record_fields": list(GATE_RECORD_FIELDS),
        "gate_summary": _build_summary(len(policy_spec_records), gate_records),
        "market_ids": market_ids,
        "gate_records": gate_records,
        "limitations": [
            "Reads local PAPER-004 spec and its local PAPER-003 preview source only.",
            "Gate status is limited to later manual review of an offline paper workflow.",
            "Artifact is inert and produces zero executable actions.",
        ],
    }
    return validate_gate_payload(payload)


def _render_nested_list(items):
    if not items:
        return ["  - none"]
    return [f"  - {item}" for item in items]


def render_markdown_report(payload):
    summary = payload["gate_summary"]
    lines = [
        "# PMBOT Paper Simulation Gate v1",
        "",
        "## Summary",
        "",
        f"- task_id: {payload['task_id']}",
        f"- source_policy_spec_path: {payload['source_policy_spec_path']}",
        f"- source_preview_path: {payload['source_preview_path']}",
    ]
    for field in SUMMARY_FIELDS:
        lines.append(f"- {field}: {summary[field]}")
    lines.extend(["- market_ids:"])
    lines.extend(_render_nested_list(payload["market_ids"]))
    lines.extend(["", "## Gate Records", ""])

    if not payload["gate_records"]:
        lines.extend(["- none", ""])
    else:
        for record in payload["gate_records"]:
            lines.extend(
                [
                    f"### {record['market_id'] or 'missing-market-id'}",
                    f"- simulation_status: {record['simulation_status']}",
                    f"- paper_orders_created: {record['paper_orders_created']}",
                    "- policy_findings:",
                ]
            )
            lines.extend(_render_nested_list(record["policy_findings"]))
            lines.append("- blocking_reasons:")
            lines.extend(_render_nested_list(record["blocking_reasons"]))
            lines.append("- watch_only_reasons:")
            lines.extend(_render_nested_list(record["watch_only_reasons"]))
            lines.append("- required_manual_followup:")
            lines.extend(_render_nested_list(record["required_manual_followup"]))
            lines.append("- simulation_notes:")
            lines.extend(_render_nested_list(record["simulation_notes"]))
            lines.append("- safety_flags:")
            lines.extend(_render_nested_list(record["safety_flags"]))
            lines.append("")

    lines.extend(["## Limitations", ""])
    for item in payload["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def write_paper_decision_simulation_gate_artifacts(
    policy_spec_path=DEFAULT_POLICY_SPEC,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    payload = build_paper_decision_simulation_gate(
        policy_spec_path=policy_spec_path,
        json_output_path=json_output_path,
        markdown_output_path=markdown_output_path,
        expected_json_output_path=expected_json_output_path,
    )
    rendered_json = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    rendered_markdown = render_markdown_report(payload)

    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
    expected_json_output_path.parent.mkdir(parents=True, exist_ok=True)
    json_output_path.write_text(rendered_json, encoding="utf-8")
    markdown_output_path.write_text(rendered_markdown, encoding="utf-8")
    expected_json_output_path.write_text(rendered_json, encoding="utf-8")
    return {
        "task_id": TASK_ID,
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "gate_summary": payload["gate_summary"],
        "market_ids": payload["market_ids"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_paper_decision_simulation_gate_artifacts(
        policy_spec_path=args.policy_spec,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
