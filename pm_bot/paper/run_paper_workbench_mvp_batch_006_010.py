import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-PAPER-BATCH-006-010-PAPER-WORKBENCH-MVP"
ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "pm_bot" / "paper"
DOCS_DIR = ROOT / "docs"

DEFAULT_GATE_INPUT = PAPER_DIR / "paper_decision_simulation_gate.v1.json"
DEFAULT_HUMAN_REVIEW_INPUT = PAPER_DIR / "paper_simulation_gate_human_review_records_input.v1.json"
DEFAULT_HUMAN_REVIEW_ACCEPTED = PAPER_DIR / "paper_simulation_gate_human_review_records_accepted.v1.json"
DEFAULT_HUMAN_REVIEW_REJECTED = PAPER_DIR / "paper_simulation_gate_human_review_records_rejected.v1.json"
DEFAULT_HUMAN_REVIEW_REPORT = PAPER_DIR / "paper_simulation_gate_human_review_records_report.v1.md"
DEFAULT_PLAN_DRAFT = PAPER_DIR / "paper_simulation_plan_draft.v1.json"
DEFAULT_PLAN_DRAFT_MD = PAPER_DIR / "paper_simulation_plan_draft.v1.md"
DEFAULT_PLAN_DRAFT_EXPECTED = PAPER_DIR / "expected_paper_simulation_plan_draft.v1.json"
DEFAULT_MANUAL_TEMPLATE = PAPER_DIR / "manual_paper_intent_template.v1.json"
DEFAULT_MANUAL_INPUT = PAPER_DIR / "manual_paper_intents_input.v1.json"
DEFAULT_MANUAL_ACCEPTED = PAPER_DIR / "manual_paper_intents_accepted.v1.json"
DEFAULT_MANUAL_REJECTED = PAPER_DIR / "manual_paper_intents_rejected.v1.json"
DEFAULT_MANUAL_LEDGER = PAPER_DIR / "manual_paper_intent_ledger.v1.json"
DEFAULT_MANUAL_REPORT = PAPER_DIR / "manual_paper_intent_report.v1.md"
DEFAULT_PREVIEW = PAPER_DIR / "paper_workbench_preview.v1.json"
DEFAULT_PREVIEW_MD = PAPER_DIR / "paper_workbench_preview.v1.md"
DEFAULT_PREVIEW_EXPECTED = PAPER_DIR / "expected_paper_workbench_preview.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_PAPER_BATCH_006_010_RESULT.json"

GATE_PASSED_STATUS = "paper_simulation_gate_passed_for_manual_review"
ALLOWED_REVIEW_OUTCOMES = (
    "approved_for_paper_simulation_plan_drafting",
    "needs_gate_revision",
    "rejected_by_policy",
    "watch_only",
)
ALLOWED_PLAN_STATUSES = (
    "paper_simulation_plan_draft_ready_for_manual_intent",
    "paper_simulation_plan_needs_revision",
    "paper_simulation_plan_watch_only",
    "paper_simulation_plan_blocked",
)
ALLOWED_PAPER_POSITION_STATUSES = (
    "manual_paper_intent_recorded",
    "manual_paper_intent_needs_fill_source",
    "manual_paper_intent_blocked",
    "manual_paper_position_watch_only",
)

HUMAN_REVIEW_INPUT_FIELDS = {
    "record_id",
    "market_id",
    "review_outcome",
    "reviewer",
    "review_notes",
}
MANUAL_INTENT_FIELDS = {
    "intent_id",
    "market_id",
    "source_plan_status",
    "operator_manual_outcome",
    "operator_manual_side",
    "operator_manual_limit_price",
    "operator_manual_size",
    "operator_manual_rationale",
    "operator_manual_attestation",
    "paper_only",
    "inert_only",
}
MANUAL_REQUIRED_FIELDS = (
    "market_id",
    "source_plan_status",
    "operator_manual_outcome",
    "operator_manual_side",
    "operator_manual_limit_price",
    "operator_manual_size",
    "operator_manual_rationale",
    "operator_manual_attestation",
    "paper_only",
    "inert_only",
)
PROHIBITED_FIELD_NAMES = (
    "probability",
    "implied_probability",
    "fair_probability",
    "ev",
    "expected_value",
    "edge",
    "score",
    "confidence_score",
    "recommendation",
    "trade_recommendation",
    "decision",
    "trade_decision",
    "bot_decision",
    "generated_side",
    "generated_outcome",
    "auto_side",
    "auto_outcome",
    "auto_size",
    "order",
    "real_order",
    "live_order",
    "wallet",
    "private_key",
    "api_key",
    "auth",
    "trading_endpoint",
)
PROHIBITED_FIELD_TOKENS = set(PROHIBITED_FIELD_NAMES)
BLOCKED_VALUE_MARKERS = (
    "bot-generated",
    "bot generated",
    "bot recommendation",
    "recommends",
    "recommendation",
    "live order",
    "real order",
    "place order",
    "execute trade",
    "wallet",
    "private key",
    "api key",
    "trading endpoint",
    "autonomous",
)

FILES_CREATED = [
    "pm_bot/paper/run_paper_workbench_mvp_batch_006_010.py",
    "pm_bot/paper/paper_simulation_gate_human_review_records_input.v1.json",
    "pm_bot/paper/paper_simulation_gate_human_review_records_accepted.v1.json",
    "pm_bot/paper/paper_simulation_gate_human_review_records_rejected.v1.json",
    "pm_bot/paper/paper_simulation_gate_human_review_records_report.v1.md",
    "pm_bot/paper/paper_simulation_plan_draft.v1.json",
    "pm_bot/paper/paper_simulation_plan_draft.v1.md",
    "pm_bot/paper/expected_paper_simulation_plan_draft.v1.json",
    "pm_bot/paper/manual_paper_intent_template.v1.json",
    "pm_bot/paper/manual_paper_intents_input.v1.json",
    "pm_bot/paper/manual_paper_intents_accepted.v1.json",
    "pm_bot/paper/manual_paper_intents_rejected.v1.json",
    "pm_bot/paper/manual_paper_intent_ledger.v1.json",
    "pm_bot/paper/manual_paper_intent_report.v1.md",
    "pm_bot/paper/paper_workbench_preview.v1.json",
    "pm_bot/paper/paper_workbench_preview.v1.md",
    "pm_bot/paper/expected_paper_workbench_preview.v1.json",
    "pm_bot/paper/tests/test_paper_workbench_mvp_batch_006_010.py",
    "docs/PMBOT_PAPER_BATCH_006_010_RESULT.json",
]


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run deterministic offline PAPER-006 through PAPER-010 paper workbench MVP artifacts."
    )
    parser.add_argument("--gate-input", default=str(DEFAULT_GATE_INPUT.relative_to(ROOT)))
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


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


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


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _walk_string_values(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk_string_values(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_string_values(item)
    elif isinstance(value, str):
        yield value


def _blocked_keys(record, allowed_fields):
    blocked = []
    for key in _walk_keys(record):
        if key in allowed_fields:
            continue
        if _field_tokens(key) & PROHIBITED_FIELD_TOKENS:
            blocked.append(key)
    return sorted(set(blocked))


def _unexpected_keys(record, allowed_fields):
    return sorted({key for key in _walk_keys(record) if key not in allowed_fields})


def _blocked_value_markers(record):
    markers = []
    for value in _walk_string_values(record):
        lower = value.lower()
        for marker in BLOCKED_VALUE_MARKERS:
            if marker in lower:
                markers.append(marker)
    return sorted(set(markers))


def _records(payload, field):
    records = payload.get(field)
    if not isinstance(records, list):
        raise ValueError(f"payload must contain {field} list")
    return [record for record in records if isinstance(record, dict)]


def _gate_records(gate_payload):
    records = _records(gate_payload, "gate_records")
    if not records:
        raise ValueError("PAPER-005 gate artifact contains no gate_records")
    for record in records:
        if _clean_text(record.get("simulation_status")) not in {
            GATE_PASSED_STATUS,
            "paper_watch_only",
            "paper_blocked_needs_more_review",
            "paper_blocked_by_policy",
        }:
            raise ValueError("PAPER-005 gate artifact contains an unknown simulation_status")
        if record.get("paper_orders_created") != 0:
            raise ValueError("PAPER-005 gate artifact is inconsistent: paper_orders_created must be 0")
    return records


def _gate_by_market_id(gate_payload):
    return {
        _clean_text(record.get("market_id")): record
        for record in _gate_records(gate_payload)
        if _clean_text(record.get("market_id"))
    }


def _count_by_reason(records):
    counts = {}
    for record in records:
        for reason in record.get("rejection_reasons", []):
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def _render_list(items, indent="  "):
    if not items:
        return [f"{indent}- none"]
    return [f"{indent}- {item}" for item in items]


def build_human_review_input_fixture(source_gate_path=DEFAULT_GATE_INPUT):
    return {
        "schema_version": "paper_simulation_gate_human_review_records_input.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_gate_path": _display_path(source_gate_path),
        "records": [
            {
                "record_id": "human-review-001",
                "market_id": "824952",
                "review_outcome": "approved_for_paper_simulation_plan_drafting",
                "reviewer": "operator_fixture",
                "review_notes": [
                    "Operator approves the PAPER-005 gate record for a local paper simulation plan draft.",
                    "No executable action is authorized by this review record.",
                ],
            },
            {
                "record_id": "human-review-rejected-unknown-market",
                "market_id": "000000",
                "review_outcome": "approved_for_paper_simulation_plan_drafting",
                "reviewer": "operator_fixture",
                "review_notes": [
                    "Invalid fixture row: market is absent from the PAPER-005 gate artifact.",
                ],
            },
            {
                "record_id": "human-review-rejected-prohibited-field",
                "market_id": "824952",
                "review_outcome": "approved_for_paper_simulation_plan_drafting",
                "reviewer": "operator_fixture",
                "review_notes": [
                    "Invalid fixture row: includes a prohibited trading field.",
                ],
                "decision": "blocked_fixture_value",
            },
            {
                "record_id": "human-review-rejected-unknown-outcome",
                "market_id": "824952",
                "review_outcome": "unknown_review_outcome",
                "reviewer": "operator_fixture",
                "review_notes": [
                    "Invalid fixture row: review outcome is not in the allowed list.",
                ],
            },
        ],
    }


def build_human_review_records(gate_payload, review_payload, review_input_path=DEFAULT_HUMAN_REVIEW_INPUT):
    gate_by_market_id = _gate_by_market_id(gate_payload)
    accepted = []
    rejected = []

    for record in _records(review_payload, "records"):
        record_id = _clean_text(record.get("record_id"))
        market_id = _clean_text(record.get("market_id"))
        review_outcome = _clean_text(record.get("review_outcome"))
        reasons = []
        blocked_keys = _blocked_keys(record, HUMAN_REVIEW_INPUT_FIELDS)
        unexpected_keys = _unexpected_keys(record, HUMAN_REVIEW_INPUT_FIELDS)

        if market_id not in gate_by_market_id:
            reasons.append("unknown_market_id")
        if review_outcome not in ALLOWED_REVIEW_OUTCOMES:
            reasons.append("unknown_review_outcome")
        if blocked_keys:
            reasons.append("prohibited_or_execution_field_present")
        if unexpected_keys:
            reasons.append("unexpected_field_present")

        if reasons:
            rejected.append(
                {
                    "record_id": record_id,
                    "market_id": market_id,
                    "review_outcome": review_outcome,
                    "review_status": "rejected",
                    "rejection_reasons": reasons,
                    "blocked_keys": blocked_keys,
                    "unexpected_keys": unexpected_keys,
                }
            )
            continue

        source_gate = gate_by_market_id[market_id]
        accepted.append(
            {
                "record_id": record_id,
                "market_id": market_id,
                "source_gate_status": _clean_text(source_gate.get("simulation_status")),
                "review_outcome": review_outcome,
                "review_status": "accepted_for_paper_simulation_plan_processing",
                "reviewer": _clean_text(record.get("reviewer")),
                "review_notes": record.get("review_notes", []),
                "created_action_count": 0,
            }
        )

    accepted.sort(key=lambda item: (item["market_id"], item["record_id"]))
    rejected.sort(key=lambda item: item["record_id"])
    common = {
        "task_id": TASK_ID,
        "deterministic": True,
        "source_gate_path": _display_path(DEFAULT_GATE_INPUT),
        "input_path": _display_path(review_input_path),
        "allowed_review_outcomes": list(ALLOWED_REVIEW_OUTCOMES),
    }
    accepted_payload = {
        "schema_version": "paper_simulation_gate_human_review_records_accepted.v1",
        **common,
        "counts": {
            "records_read": len(_records(review_payload, "records")),
            "records_accepted": len(accepted),
            "created_action_count": 0,
        },
        "records": accepted,
    }
    rejected_payload = {
        "schema_version": "paper_simulation_gate_human_review_records_rejected.v1",
        **common,
        "counts": {
            "records_read": len(_records(review_payload, "records")),
            "records_rejected": len(rejected),
            "rejection_reason_counts": _count_by_reason(rejected),
        },
        "records": rejected,
    }
    return accepted_payload, rejected_payload


def render_human_review_markdown(accepted_payload, rejected_payload):
    lines = [
        "# PAPER-006 Human Review Record Gate",
        "",
        f"- task_id: {TASK_ID}",
        f"- source_gate_path: {accepted_payload['source_gate_path']}",
        f"- records_accepted: {accepted_payload['counts']['records_accepted']}",
        f"- records_rejected: {rejected_payload['counts']['records_rejected']}",
        f"- created_action_count: {accepted_payload['counts']['created_action_count']}",
        "",
        "## Accepted",
        "",
    ]
    if not accepted_payload["records"]:
        lines.append("- none")
    else:
        for record in accepted_payload["records"]:
            lines.append(
                f"- {record['record_id']}: market_id={record['market_id']} review_outcome={record['review_outcome']}"
            )
    lines.extend(["", "## Rejected", ""])
    if not rejected_payload["records"]:
        lines.append("- none")
    else:
        for record in rejected_payload["records"]:
            lines.append(
                f"- {record['record_id']}: market_id={record['market_id']} reasons={','.join(record['rejection_reasons'])}"
            )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Offline local review gate only.",
            "- Rejected rows are summarized without authorizing executable action.",
            "",
        ]
    )
    return "\n".join(lines)


def _plan_status_for_review_outcome(review_outcome):
    if review_outcome == "approved_for_paper_simulation_plan_drafting":
        return "paper_simulation_plan_draft_ready_for_manual_intent"
    if review_outcome == "needs_gate_revision":
        return "paper_simulation_plan_needs_revision"
    if review_outcome == "watch_only":
        return "paper_simulation_plan_watch_only"
    return "paper_simulation_plan_blocked"


def build_plan_draft(accepted_review_payload, source_path=DEFAULT_HUMAN_REVIEW_ACCEPTED):
    plan_records = []
    for record in _records(accepted_review_payload, "records"):
        plan_status = _plan_status_for_review_outcome(record["review_outcome"])
        if plan_status == "paper_simulation_plan_draft_ready_for_manual_intent":
            allowed_next_actions = [
                "prepare_blank_manual_paper_intent_template",
                "validate_operator_provided_manual_paper_intent",
            ]
            required_manual_followup = [
                "operator_must_supply_any_manual_paper_intent",
                "operator_must_confirm_paper_only_and_inert_only_flags",
            ]
        elif plan_status == "paper_simulation_plan_watch_only":
            allowed_next_actions = ["keep_under_manual_watch"]
            required_manual_followup = ["operator_must_complete_watch_only_review_before_continuing"]
        elif plan_status == "paper_simulation_plan_needs_revision":
            allowed_next_actions = ["revise_prior_gate_inputs_manually"]
            required_manual_followup = ["operator_must_resolve_gate_revision_notes"]
        else:
            allowed_next_actions = ["stop_local_paper_workbench_flow"]
            required_manual_followup = ["operator_must_not_continue_this_market_without_new_review"]

        plan_records.append(
            {
                "market_id": record["market_id"],
                "source_gate_status": record["source_gate_status"],
                "source_review_outcome": record["review_outcome"],
                "plan_status": plan_status,
                "required_inputs": [
                    "blank_manual_paper_intent_contract",
                    "operator_manual_attestation",
                    "paper_only_true",
                    "inert_only_true",
                ],
                "constraints": [
                    "offline_local_artifacts_only",
                    "operator_provided_manual_intent_only",
                    "no_strategy_generated_parameters",
                    "no_external_network_use",
                    "no_credential_use",
                    "no_live_execution",
                ],
                "allowed_next_actions": allowed_next_actions,
                "blocked_actions": [
                    "strategy_parameter_generation",
                    "automated_quantitative_scoring",
                    "live_or_real_execution",
                    "credential_or_endpoint_use",
                ],
                "required_manual_followup": required_manual_followup,
                "simulation_notes": [
                    "This draft only prepares local paperwork for a possible operator-provided paper intent.",
                    "The draft does not select any trade parameters or executable action.",
                ],
            }
        )
    plan_records.sort(key=lambda item: item["market_id"])
    return {
        "schema_version": "paper_simulation_plan_draft.v1",
        "markdown_version": "paper_simulation_plan_draft_report.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_accepted_human_review_path": _display_path(source_path),
        "allowed_plan_statuses": list(ALLOWED_PLAN_STATUSES),
        "plan_record_fields": [
            "market_id",
            "source_gate_status",
            "source_review_outcome",
            "plan_status",
            "required_inputs",
            "constraints",
            "allowed_next_actions",
            "blocked_actions",
            "required_manual_followup",
            "simulation_notes",
        ],
        "counts": {
            "accepted_human_review_records_read": len(_records(accepted_review_payload, "records")),
            "simulation_plans_written": len(plan_records),
        },
        "market_ids": [record["market_id"] for record in plan_records],
        "plan_records": plan_records,
        "limitations": [
            "Plan draft is local and inert.",
            "Plan draft requires later operator input before any manual paper intent can be recorded.",
        ],
    }


def render_plan_markdown(plan_payload):
    lines = [
        "# PAPER-007 Paper Simulation Plan Draft",
        "",
        f"- task_id: {plan_payload['task_id']}",
        f"- source_accepted_human_review_path: {plan_payload['source_accepted_human_review_path']}",
        f"- simulation_plans_written: {plan_payload['counts']['simulation_plans_written']}",
        "",
        "## Plan Records",
        "",
    ]
    if not plan_payload["plan_records"]:
        lines.append("- none")
    else:
        for record in plan_payload["plan_records"]:
            lines.extend(
                [
                    f"### {record['market_id']}",
                    f"- source_gate_status: {record['source_gate_status']}",
                    f"- source_review_outcome: {record['source_review_outcome']}",
                    f"- plan_status: {record['plan_status']}",
                    "- required_inputs:",
                ]
            )
            lines.extend(_render_list(record["required_inputs"]))
            lines.append("- constraints:")
            lines.extend(_render_list(record["constraints"]))
            lines.append("- allowed_next_actions:")
            lines.extend(_render_list(record["allowed_next_actions"]))
            lines.append("- blocked_actions:")
            lines.extend(_render_list(record["blocked_actions"]))
            lines.append("- required_manual_followup:")
            lines.extend(_render_list(record["required_manual_followup"]))
            lines.append("- simulation_notes:")
            lines.extend(_render_list(record["simulation_notes"]))
            lines.append("")
    lines.extend(["## Limitations", ""])
    for item in plan_payload["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def build_manual_paper_intent_template(source_plan_path=DEFAULT_PLAN_DRAFT):
    return {
        "schema_version": "manual_paper_intent_template.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "template_status": "blank_operator_manual_paper_intent_contract",
        "source_plan_path": _display_path(source_plan_path),
        "required_fields": list(MANUAL_REQUIRED_FIELDS),
        "field_contract": {
            "market_id": "required string matching a market in the plan draft",
            "source_plan_status": "required string copied from the plan draft",
            "operator_manual_outcome": "required operator-provided string",
            "operator_manual_side": "required operator-provided string",
            "operator_manual_limit_price": "required operator-provided local paper value",
            "operator_manual_size": "required operator-provided local paper value",
            "operator_manual_rationale": "required operator-provided text",
            "operator_manual_attestation": "required operator attestation text",
            "paper_only": "required boolean true",
            "inert_only": "required boolean true",
        },
        "blank_record": {
            "market_id": "",
            "source_plan_status": "",
            "operator_manual_outcome": "",
            "operator_manual_side": "",
            "operator_manual_limit_price": None,
            "operator_manual_size": None,
            "operator_manual_rationale": "",
            "operator_manual_attestation": "",
            "paper_only": True,
            "inert_only": True,
        },
        "constraints": [
            "operator_fields_only",
            "paper_only_must_be_true",
            "inert_only_must_be_true",
            "operator_manual_attestation_required",
            "no_live_execution",
            "no_credential_use",
            "no_external_network_use",
        ],
    }


def build_manual_paper_intents_input_fixture(source_plan_path=DEFAULT_PLAN_DRAFT, source_template_path=DEFAULT_MANUAL_TEMPLATE):
    return {
        "schema_version": "manual_paper_intents_input.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_plan_path": _display_path(source_plan_path),
        "source_template_path": _display_path(source_template_path),
        "records": [
            {
                "intent_id": "manual-intent-001",
                "market_id": "824952",
                "source_plan_status": "paper_simulation_plan_draft_ready_for_manual_intent",
                "operator_manual_outcome": "operator_fixture_outcome",
                "operator_manual_side": "operator_fixture_side",
                "operator_manual_limit_price": 0.42,
                "operator_manual_size": 10,
                "operator_manual_rationale": "Operator-entered offline paper workbench fixture with no bot guidance.",
                "operator_manual_attestation": "I attest this is operator-provided, paper-only, and inert.",
                "paper_only": True,
                "inert_only": True,
            },
            {
                "intent_id": "manual-intent-rejected-missing-attestation",
                "market_id": "824952",
                "source_plan_status": "paper_simulation_plan_draft_ready_for_manual_intent",
                "operator_manual_outcome": "operator_fixture_outcome",
                "operator_manual_side": "operator_fixture_side",
                "operator_manual_limit_price": 0.41,
                "operator_manual_size": 3,
                "operator_manual_rationale": "Invalid fixture row missing operator attestation.",
                "paper_only": True,
                "inert_only": True,
            },
            {
                "intent_id": "manual-intent-rejected-bot-live",
                "market_id": "824952",
                "source_plan_status": "paper_simulation_plan_draft_ready_for_manual_intent",
                "operator_manual_outcome": "operator_fixture_outcome",
                "operator_manual_side": "operator_fixture_side",
                "operator_manual_limit_price": 0.43,
                "operator_manual_size": 4,
                "operator_manual_rationale": "Bot-generated recommendation asks for a live order.",
                "operator_manual_attestation": "I attest this is operator-provided, paper-only, and inert.",
                "paper_only": True,
                "inert_only": True,
                "bot_recommendation": "blocked_fixture_value",
                "live_order": True,
            },
        ],
    }


def _plan_by_market_id(plan_payload):
    return {
        _clean_text(record.get("market_id")): record
        for record in _records(plan_payload, "plan_records")
        if _clean_text(record.get("market_id"))
    }


def _manual_record_for_output(record, status):
    return {
        "intent_id": _clean_text(record.get("intent_id")),
        "market_id": _clean_text(record.get("market_id")),
        "source_plan_status": _clean_text(record.get("source_plan_status")),
        "intent_status": status,
        "operator_manual_outcome": record.get("operator_manual_outcome"),
        "operator_manual_side": record.get("operator_manual_side"),
        "operator_manual_limit_price": record.get("operator_manual_limit_price"),
        "operator_manual_size": record.get("operator_manual_size"),
        "operator_manual_rationale": record.get("operator_manual_rationale"),
        "operator_manual_attestation": record.get("operator_manual_attestation"),
        "paper_only": record.get("paper_only"),
        "inert_only": record.get("inert_only"),
    }


def build_manual_intent_outputs(plan_payload, manual_input_payload, manual_input_path=DEFAULT_MANUAL_INPUT):
    plan_by_market_id = _plan_by_market_id(plan_payload)
    accepted = []
    rejected = []

    for record in _records(manual_input_payload, "records"):
        intent_id = _clean_text(record.get("intent_id"))
        market_id = _clean_text(record.get("market_id"))
        source_plan_status = _clean_text(record.get("source_plan_status"))
        reasons = []
        blocked_keys = _blocked_keys(record, MANUAL_INTENT_FIELDS)
        unexpected_keys = _unexpected_keys(record, MANUAL_INTENT_FIELDS)
        blocked_markers = _blocked_value_markers(record)
        plan_record = plan_by_market_id.get(market_id)

        if market_id not in plan_by_market_id:
            reasons.append("unknown_market_id")
        elif source_plan_status != _clean_text(plan_record.get("plan_status")):
            reasons.append("source_plan_status_mismatch")
        if record.get("paper_only") is not True:
            reasons.append("paper_only_true_required")
        if record.get("inert_only") is not True:
            reasons.append("inert_only_true_required")
        if not _clean_text(record.get("operator_manual_attestation")):
            reasons.append("operator_manual_attestation_required")
        for field in MANUAL_REQUIRED_FIELDS:
            if field not in record:
                reason = f"{field}_required"
                if reason not in reasons:
                    reasons.append(reason)
        if blocked_keys:
            reasons.append("prohibited_or_execution_field_present")
        if unexpected_keys:
            reasons.append("unexpected_field_present")
        if blocked_markers:
            reasons.append("blocked_language_present")

        if reasons:
            rejected.append(
                {
                    "intent_id": intent_id,
                    "market_id": market_id,
                    "source_plan_status": source_plan_status,
                    "intent_status": "rejected",
                    "rejection_reasons": reasons,
                    "blocked_keys": blocked_keys,
                    "unexpected_keys": unexpected_keys,
                    "blocked_language_markers": blocked_markers,
                }
            )
            continue

        accepted.append(_manual_record_for_output(record, "accepted_for_inert_manual_paper_intent_ledger"))

    accepted.sort(key=lambda item: (item["market_id"], item["intent_id"]))
    rejected.sort(key=lambda item: item["intent_id"])
    common = {
        "task_id": TASK_ID,
        "deterministic": True,
        "source_plan_path": _display_path(DEFAULT_PLAN_DRAFT),
        "input_path": _display_path(manual_input_path),
    }
    accepted_payload = {
        "schema_version": "manual_paper_intents_accepted.v1",
        **common,
        "counts": {
            "records_read": len(_records(manual_input_payload, "records")),
            "records_accepted": len(accepted),
        },
        "records": accepted,
    }
    rejected_payload = {
        "schema_version": "manual_paper_intents_rejected.v1",
        **common,
        "counts": {
            "records_read": len(_records(manual_input_payload, "records")),
            "records_rejected": len(rejected),
            "rejection_reason_counts": _count_by_reason(rejected),
        },
        "records": rejected,
    }
    ledger_entries = []
    for index, record in enumerate(accepted, start=1):
        ledger_entries.append(
            {
                "ledger_entry_id": f"manual-paper-intent-ledger-{index:03d}",
                "source_intent_id": record["intent_id"],
                "market_id": record["market_id"],
                "source_plan_status": record["source_plan_status"],
                "intent_source": "operator_manual",
                "execution_mode": "paper_only_inert",
                "generated_by_bot": False,
                "real_order_created": False,
                "live_order_created": False,
                "operator_manual_outcome": record["operator_manual_outcome"],
                "operator_manual_side": record["operator_manual_side"],
                "operator_manual_limit_price": record["operator_manual_limit_price"],
                "operator_manual_size": record["operator_manual_size"],
                "operator_manual_rationale": record["operator_manual_rationale"],
                "operator_manual_attestation": record["operator_manual_attestation"],
                "paper_only": True,
                "inert_only": True,
                "ledger_status": "inert_manual_paper_intent_recorded",
                "safety_flags": [
                    "paper_only",
                    "inert_only",
                    "operator_manual_intent",
                    "no_live_execution",
                    "no_real_execution",
                    "no_credential_or_endpoint_use",
                ],
            }
        )
    ledger_payload = {
        "schema_version": "manual_paper_intent_ledger.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_accepted_manual_intents_path": _display_path(DEFAULT_MANUAL_ACCEPTED),
        "ledger_status": "paper_only_inert_manual_intent_ledger",
        "counts": {
            "manual_paper_intent_ledger_entries": len(ledger_entries),
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        },
        "ledger_entries": ledger_entries,
    }
    return accepted_payload, rejected_payload, ledger_payload


def render_manual_intent_markdown(accepted_payload, rejected_payload, ledger_payload):
    lines = [
        "# PAPER-009 Manual Paper Intent Validation",
        "",
        f"- task_id: {TASK_ID}",
        f"- source_plan_path: {accepted_payload['source_plan_path']}",
        f"- records_accepted: {accepted_payload['counts']['records_accepted']}",
        f"- records_rejected: {rejected_payload['counts']['records_rejected']}",
        f"- ledger_entries: {ledger_payload['counts']['manual_paper_intent_ledger_entries']}",
        f"- real_orders_created: {ledger_payload['counts']['real_orders_created']}",
        f"- live_orders_created: {ledger_payload['counts']['live_orders_created']}",
        f"- autonomous_paper_orders_created: {ledger_payload['counts']['autonomous_paper_orders_created']}",
        "",
        "## Accepted",
        "",
    ]
    if not accepted_payload["records"]:
        lines.append("- none")
    else:
        for record in accepted_payload["records"]:
            lines.append(f"- {record['intent_id']}: market_id={record['market_id']} status={record['intent_status']}")
    lines.extend(["", "## Rejected", ""])
    if not rejected_payload["records"]:
        lines.append("- none")
    else:
        for record in rejected_payload["records"]:
            lines.append(
                f"- {record['intent_id']}: market_id={record['market_id']} reasons={','.join(record['rejection_reasons'])}"
            )
    lines.extend(
        [
            "",
            "## Ledger",
            "",
        ]
    )
    if not ledger_payload["ledger_entries"]:
        lines.append("- none")
    else:
        for record in ledger_payload["ledger_entries"]:
            lines.append(
                f"- {record['ledger_entry_id']}: market_id={record['market_id']} execution_mode={record['execution_mode']}"
            )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Paper-only inert ledger entries only.",
            "- The ledger preserves operator-provided manual fields and creates no real or live executable artifact.",
            "",
        ]
    )
    return "\n".join(lines)


def build_workbench_preview(ledger_payload, source_ledger_path=DEFAULT_MANUAL_LEDGER):
    preview_records = []
    for entry in _records(ledger_payload, "ledger_entries"):
        preview_records.append(
            {
                "market_id": entry["market_id"],
                "intent_source": entry["intent_source"],
                "execution_mode": entry["execution_mode"],
                "paper_position_status": "manual_paper_intent_needs_fill_source",
                "operator_manual_outcome": entry["operator_manual_outcome"],
                "operator_manual_side": entry["operator_manual_side"],
                "operator_manual_limit_price": entry["operator_manual_limit_price"],
                "operator_manual_size": entry["operator_manual_size"],
                "open_questions": [
                    "deterministic_local_fill_source_required_before_any_position_state_update",
                ],
                "required_next_manual_action": "provide_deterministic_local_fill_source_or_keep_watch_only",
                "safety_flags": [
                    "paper_only",
                    "inert_only",
                    "operator_manual_intent",
                    "no_fill_simulated",
                    "no_live_execution",
                    "no_real_execution",
                ],
            }
        )
    preview_records.sort(key=lambda item: item["market_id"])
    return {
        "schema_version": "paper_workbench_preview.v1",
        "markdown_version": "paper_workbench_preview_report.v1",
        "task_id": TASK_ID,
        "deterministic": True,
        "source_manual_paper_intent_ledger_path": _display_path(source_ledger_path),
        "allowed_paper_position_statuses": list(ALLOWED_PAPER_POSITION_STATUSES),
        "counts": {
            "ledger_entries_read": len(_records(ledger_payload, "ledger_entries")),
            "paper_workbench_preview_records": len(preview_records),
            "fills_simulated": 0,
        },
        "preview_records": preview_records,
        "limitations": [
            "Preview records are inert and do not update paper portfolio state.",
            "No fill simulation is performed by this batch.",
            "No financial performance metric or automated quality metric is calculated.",
        ],
    }


def render_workbench_preview_markdown(preview_payload):
    lines = [
        "# PAPER-010 Paper Workbench Preview",
        "",
        f"- task_id: {preview_payload['task_id']}",
        f"- source_manual_paper_intent_ledger_path: {preview_payload['source_manual_paper_intent_ledger_path']}",
        f"- paper_workbench_preview_records: {preview_payload['counts']['paper_workbench_preview_records']}",
        f"- fills_simulated: {preview_payload['counts']['fills_simulated']}",
        "",
        "## Preview Records",
        "",
    ]
    if not preview_payload["preview_records"]:
        lines.append("- none")
    else:
        for record in preview_payload["preview_records"]:
            lines.extend(
                [
                    f"### {record['market_id']}",
                    f"- intent_source: {record['intent_source']}",
                    f"- execution_mode: {record['execution_mode']}",
                    f"- paper_position_status: {record['paper_position_status']}",
                    f"- operator_manual_outcome: {record['operator_manual_outcome']}",
                    f"- operator_manual_side: {record['operator_manual_side']}",
                    f"- operator_manual_limit_price: {record['operator_manual_limit_price']}",
                    f"- operator_manual_size: {record['operator_manual_size']}",
                    f"- required_next_manual_action: {record['required_next_manual_action']}",
                    "- open_questions:",
                ]
            )
            lines.extend(_render_list(record["open_questions"]))
            lines.append("- safety_flags:")
            lines.extend(_render_list(record["safety_flags"]))
            lines.append("")
    lines.extend(["## Limitations", ""])
    for item in preview_payload["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def _result_payload(counts, status="completed_ready_for_review", blockers=None, tests=None):
    return {
        "task_id": TASK_ID,
        "status": status,
        "summary": (
            "Implemented deterministic offline PAPER-006 through PAPER-010 workbench MVP artifacts "
            "from the PAPER-005 gate through operator-manual inert paper intent ledger and preview."
        )
        if status == "completed_ready_for_review"
        else "Blocked before completing deterministic offline paper workbench MVP artifacts.",
        "market_ids": ["824952"],
        "stages_completed": {
            "paper_006_human_review_record_gate": status == "completed_ready_for_review",
            "paper_007_simulation_plan_draft": status == "completed_ready_for_review",
            "paper_008_manual_paper_intent_contract": status == "completed_ready_for_review",
            "paper_009_manual_paper_intent_ledger": status == "completed_ready_for_review",
            "paper_010_paper_workbench_preview": status == "completed_ready_for_review",
        },
        "counts": counts,
        "files_created": FILES_CREATED,
        "files_modified": [],
        "tests": tests or [],
        "safety": {
            "offline_only": True,
            "network_api_calls": False,
            "credentials": False,
            "wallet_private_keys": False,
            "authenticated_endpoints": False,
            "trading_endpoints": False,
            "real_orders": False,
            "live_trading": False,
            "autonomous_paper_orders": False,
            "betting_recommendations": False,
            "truth_inference": False,
            "market_scoring": False,
            "probability_estimates": False,
            "ev_calculations": False,
            "side_recommendations": False,
            "market_decisions": False,
            "runtime_wiring": False,
            "dispatcher_run_codex_changes": False,
            "prompt_automation": False,
            "codex_copy_roots": False,
            "completed_dossiers": False,
            "broad_refactor": False,
        },
        "scope_expansion": {
            "manual_operator_paper_intent_fields_introduced": True,
            "manual_fields_are_operator_provided_only": True,
            "bot_generated_side_size_price": False,
            "paper_only_inert_ledger": True,
        },
        "blockers": blockers or [],
    }


def write_paper_workbench_mvp_artifacts(gate_input_path=DEFAULT_GATE_INPUT):
    gate_input_path = _resolve_path(gate_input_path)
    if not gate_input_path.exists():
        raise FileNotFoundError(f"missing PAPER-005 gate artifact: {_display_path(gate_input_path)}")
    gate_payload = _load_json(gate_input_path)
    gate_by_market_id = _gate_by_market_id(gate_payload)
    if "824952" not in gate_by_market_id:
        raise ValueError("PAPER-005 gate artifact does not contain required market_id 824952")
    if _clean_text(gate_by_market_id["824952"].get("simulation_status")) != GATE_PASSED_STATUS:
        raise ValueError("PAPER-005 market_id 824952 gate status is not passed for manual review")

    human_review_input = build_human_review_input_fixture(gate_input_path)
    _write_json(DEFAULT_HUMAN_REVIEW_INPUT, human_review_input)
    human_review_payload = _load_json(DEFAULT_HUMAN_REVIEW_INPUT)
    accepted_review, rejected_review = build_human_review_records(
        gate_payload,
        human_review_payload,
        DEFAULT_HUMAN_REVIEW_INPUT,
    )
    _write_json(DEFAULT_HUMAN_REVIEW_ACCEPTED, accepted_review)
    _write_json(DEFAULT_HUMAN_REVIEW_REJECTED, rejected_review)
    _write_text(DEFAULT_HUMAN_REVIEW_REPORT, render_human_review_markdown(accepted_review, rejected_review))

    plan_payload = build_plan_draft(accepted_review, DEFAULT_HUMAN_REVIEW_ACCEPTED)
    _write_json(DEFAULT_PLAN_DRAFT, plan_payload)
    _write_json(DEFAULT_PLAN_DRAFT_EXPECTED, plan_payload)
    _write_text(DEFAULT_PLAN_DRAFT_MD, render_plan_markdown(plan_payload))

    manual_template = build_manual_paper_intent_template(DEFAULT_PLAN_DRAFT)
    _write_json(DEFAULT_MANUAL_TEMPLATE, manual_template)
    manual_input = build_manual_paper_intents_input_fixture(DEFAULT_PLAN_DRAFT, DEFAULT_MANUAL_TEMPLATE)
    _write_json(DEFAULT_MANUAL_INPUT, manual_input)
    manual_input_payload = _load_json(DEFAULT_MANUAL_INPUT)
    accepted_manual, rejected_manual, ledger_payload = build_manual_intent_outputs(
        plan_payload,
        manual_input_payload,
        DEFAULT_MANUAL_INPUT,
    )
    _write_json(DEFAULT_MANUAL_ACCEPTED, accepted_manual)
    _write_json(DEFAULT_MANUAL_REJECTED, rejected_manual)
    _write_json(DEFAULT_MANUAL_LEDGER, ledger_payload)
    _write_text(DEFAULT_MANUAL_REPORT, render_manual_intent_markdown(accepted_manual, rejected_manual, ledger_payload))

    preview_payload = build_workbench_preview(ledger_payload, DEFAULT_MANUAL_LEDGER)
    _write_json(DEFAULT_PREVIEW, preview_payload)
    _write_json(DEFAULT_PREVIEW_EXPECTED, preview_payload)
    _write_text(DEFAULT_PREVIEW_MD, render_workbench_preview_markdown(preview_payload))

    counts = {
        "human_review_records_accepted": accepted_review["counts"]["records_accepted"],
        "human_review_records_rejected": rejected_review["counts"]["records_rejected"],
        "simulation_plans_written": plan_payload["counts"]["simulation_plans_written"],
        "manual_paper_intents_accepted": accepted_manual["counts"]["records_accepted"],
        "manual_paper_intents_rejected": rejected_manual["counts"]["records_rejected"],
        "manual_paper_intent_ledger_entries": ledger_payload["counts"]["manual_paper_intent_ledger_entries"],
        "paper_workbench_preview_records": preview_payload["counts"]["paper_workbench_preview_records"],
        "real_orders_created": 0,
        "live_orders_created": 0,
        "autonomous_paper_orders_created": 0,
    }
    result_payload = _result_payload(counts)
    _write_json(DEFAULT_RESULT, result_payload)
    return {
        "task_id": TASK_ID,
        "status": "completed_ready_for_review",
        "market_ids": ["824952"],
        "counts": counts,
        "result_path": _display_path(DEFAULT_RESULT),
    }


def main(argv):
    args = _parse_args(argv)
    try:
        summary = write_paper_workbench_mvp_artifacts(args.gate_input)
    except Exception as exc:
        blocked_counts = {
            "human_review_records_accepted": 0,
            "human_review_records_rejected": 0,
            "simulation_plans_written": 0,
            "manual_paper_intents_accepted": 0,
            "manual_paper_intents_rejected": 0,
            "manual_paper_intent_ledger_entries": 0,
            "paper_workbench_preview_records": 0,
            "real_orders_created": 0,
            "live_orders_created": 0,
            "autonomous_paper_orders_created": 0,
        }
        _write_json(DEFAULT_RESULT, _result_payload(blocked_counts, status="blocked", blockers=[str(exc)]))
        print(json.dumps({"task_id": TASK_ID, "status": "blocked", "blockers": [str(exc)]}, indent=2, ensure_ascii=True))
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
