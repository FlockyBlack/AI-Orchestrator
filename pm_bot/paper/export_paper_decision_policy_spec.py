import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-PAPER-004-PAPER-DECISION-POLICY-SPEC"
SCHEMA_VERSION = "paper_decision_policy_spec.v1"
MARKDOWN_VERSION = "paper_decision_policy_spec_report.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PREVIEW = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_preview.v1.json"
DEFAULT_POLICY_REVIEW_RESULT = ROOT / "pm_bot" / "paper" / "paper_policy_review_result.v1.json"
DEFAULT_FINAL_DOSSIER_DRAFTS = ROOT / "pm_bot" / "research" / "selected_ingest_final_dossier_drafts.v1.json"
DEFAULT_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "paper_decision_policy_spec.v1.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "pm_bot" / "paper" / "paper_decision_policy_spec.v1.md"
DEFAULT_EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "expected_paper_decision_policy_spec.v1.json"

ACCEPTED_PREVIEW_STATUS = "ready_for_future_paper_decision_policy_design"
POLICY_SPEC_STATUS = "paper_decision_policy_constraints_defined"
FUTURE_SIMULATION_STATUSES = (
    "paper_simulation_allowed",
    "paper_watch_only",
    "paper_blocked_needs_more_review",
    "paper_blocked_by_policy",
)
REQUIRED_FUTURE_INPUTS = (
    "market_id",
    "question/title",
    "resolution_criteria_summary",
    "evidence_inventory_summary",
    "uncertainty_register_summary",
    "missing_information_review",
    "open_questions",
    "current_yes_price",
    "liquidity",
    "volume",
    "paper_readiness_status",
    "paper_policy_status",
)
FUTURE_INPUT_SOURCE_FIELDS = {
    "market_id": "market_id",
    "question/title": "title_question",
    "resolution_criteria_summary": "resolution_criteria_summary",
    "evidence_inventory_summary": "evidence_inventory_summary",
    "uncertainty_register_summary": "uncertainty_register_summary",
    "missing_information_review": "missing_information_review",
    "open_questions": "open_questions",
    "current_yes_price": "current_yes_price",
    "liquidity": "liquidity",
    "volume": "volume",
    "paper_readiness_status": "paper_readiness_status",
    "paper_policy_status": "paper_policy_status",
}
ALLOWED_FUTURE_OUTPUT_FIELDS = (
    "market_id",
    "simulation_status",
    "policy_findings",
    "blocking_reasons",
    "watch_only_reasons",
    "required_manual_followup",
    "simulation_notes",
)
ALWAYS_FORBIDDEN_FUTURE_FIELDS = (
    "real_order",
    "live_order",
    "wallet",
    "private_key",
    "execution",
    "trade_execution",
    "authenticated_endpoint",
)
PAPER_004_FORBIDDEN_OUTPUT_FIELDS = (
    "side",
    "recommendation",
    "probability",
    "expected_value",
    "ev",
    "score",
    "signal",
    "stake",
    "size",
    "entry_price",
    "limit_price",
    "price_target",
    "market_decision",
    "buy",
    "sell",
)
POLICY_BLOCKERS = (
    "missing_resolution_criteria",
    "missing_evidence_inventory",
    "unresolved_critical_questions",
    "prohibited_trading_language_present",
    "probability_or_ev_present",
    "side_or_recommendation_present",
    "market_decision_present",
    "order_or_trade_present",
)
WATCH_ONLY_REASONS = (
    "insufficient_source_coverage",
    "high_unresolved_uncertainty",
    "stale_manual_review",
    "ambiguous_resolution_criteria",
)
SPEC_RECORD_FIELDS = (
    "market_id",
    "accepted_preview_status",
    "policy_spec_status",
    "source_policy_record_present",
    "source_final_dossier_draft_present",
    "future_input_source_fields",
    "policy_boundaries",
)
SUMMARY_FIELDS = (
    "preview_records_read",
    "policy_specs_written",
    "markets_covered",
    "paper_orders_created",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export a deterministic offline paper decision policy specification."
    )
    parser.add_argument("--preview", default=str(DEFAULT_PREVIEW.relative_to(ROOT)))
    parser.add_argument("--policy-review-result", default=str(DEFAULT_POLICY_REVIEW_RESULT.relative_to(ROOT)))
    parser.add_argument("--final-dossier-drafts", default=str(DEFAULT_FINAL_DOSSIER_DRAFTS.relative_to(ROOT)))
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


def _market_id_set(records):
    return {
        _clean_text(record.get("market_id"))
        for record in records
        if _clean_text(record.get("market_id"))
    }


def _accepted_preview_records(preview_records):
    accepted = [
        record
        for record in preview_records
        if _clean_text(record.get("simulation_preview_status")) == ACCEPTED_PREVIEW_STATUS
    ]
    return sorted(accepted, key=lambda item: _clean_text(item.get("market_id")))


def _build_policy_spec_record(preview_record, policy_market_ids, draft_market_ids):
    market_id = _clean_text(preview_record.get("market_id"))
    return {
        "market_id": market_id,
        "accepted_preview_status": ACCEPTED_PREVIEW_STATUS,
        "policy_spec_status": POLICY_SPEC_STATUS,
        "source_policy_record_present": market_id in policy_market_ids,
        "source_final_dossier_draft_present": market_id in draft_market_ids,
        "future_input_source_fields": dict(FUTURE_INPUT_SOURCE_FIELDS),
        "policy_boundaries": [
            "PAPER-004 defines policy constraints only.",
            "A later PAPER-005 module may use this contract for paper-only simulation.",
            "This artifact does not run a simulation, choose an outcome direction, infer truth, score the market, calculate probability, calculate expected value, or create paper orders.",
        ],
    }


def _build_summary(preview_records_read, policy_specs_written, markets_covered):
    return {
        "preview_records_read": preview_records_read,
        "policy_specs_written": policy_specs_written,
        "markets_covered": markets_covered,
        "paper_orders_created": 0,
    }


def build_paper_decision_policy_spec(
    preview_path=DEFAULT_PREVIEW,
    policy_review_result_path=DEFAULT_POLICY_REVIEW_RESULT,
    final_dossier_drafts_path=DEFAULT_FINAL_DOSSIER_DRAFTS,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    preview_path = _resolve_path(preview_path)
    policy_review_result_path = _resolve_path(policy_review_result_path)
    final_dossier_drafts_path = _resolve_path(final_dossier_drafts_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    preview_payload = _load_json(preview_path)
    policy_payload = _load_json(policy_review_result_path)
    drafts_payload = _load_json(final_dossier_drafts_path)

    preview_records = _records_list(preview_payload, "preview_records")
    policy_records = _records_list(policy_payload, "policy_records")
    draft_records = _records_list(drafts_payload, "final_dossier_drafts")
    policy_market_ids = _market_id_set(policy_records)
    draft_market_ids = _market_id_set(draft_records)

    accepted_records = _accepted_preview_records(preview_records)
    policy_specs = [
        _build_policy_spec_record(record, policy_market_ids, draft_market_ids)
        for record in accepted_records
    ]
    market_ids = sorted(record["market_id"] for record in policy_specs if record["market_id"])
    summary = _build_summary(
        preview_records_read=len(preview_records),
        policy_specs_written=len(policy_specs),
        markets_covered=len(market_ids),
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_preview_path": _display_path(preview_path),
        "source_preview_schema_version": _clean_text(preview_payload.get("schema_version")),
        "source_policy_review_result_path": _display_path(policy_review_result_path),
        "source_policy_review_result_schema_version": _clean_text(policy_payload.get("schema_version")),
        "source_final_dossier_drafts_path": _display_path(final_dossier_drafts_path),
        "source_final_dossier_drafts_schema_version": _clean_text(drafts_payload.get("schema_version")),
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "accepted_simulation_preview_status": ACCEPTED_PREVIEW_STATUS,
        "allowed_future_simulation_statuses": list(FUTURE_SIMULATION_STATUSES),
        "required_future_simulation_inputs": list(REQUIRED_FUTURE_INPUTS),
        "allowed_future_output_fields": list(ALLOWED_FUTURE_OUTPUT_FIELDS),
        "always_forbidden_future_fields": list(ALWAYS_FORBIDDEN_FUTURE_FIELDS),
        "paper_004_forbidden_output_fields": list(PAPER_004_FORBIDDEN_OUTPUT_FIELDS),
        "policy_blockers": list(POLICY_BLOCKERS),
        "watch_only_reasons": list(WATCH_ONLY_REASONS),
        "policy_spec_record_fields": list(SPEC_RECORD_FIELDS),
        "policy_spec_summary": summary,
        "market_ids": market_ids,
        "policy_specs": policy_specs,
        "limitations": [
            "Reads only local PAPER-003 preview, PAPER-002 policy-review result, and selected-ingest final dossier draft artifacts.",
            "PAPER-004 only defines policy constraints; it does not run a decision simulation.",
            "This specification does not choose YES or NO, recommend a trade, calculate probability, calculate expected value, score a market, infer truth, create paper orders, or create real orders.",
        ],
    }


def _render_nested_list(items):
    if not items:
        return ["  - none"]
    return [f"  - {item}" for item in items]


def render_markdown_report(payload):
    summary = payload["policy_spec_summary"]
    lines = [
        "# PMBOT Paper Decision Policy Spec v1",
        "",
        "## Summary",
        "",
        f"- task_id: {payload['task_id']}",
        f"- source_preview_path: {payload['source_preview_path']}",
        f"- source_policy_review_result_path: {payload['source_policy_review_result_path']}",
        f"- source_final_dossier_drafts_path: {payload['source_final_dossier_drafts_path']}",
    ]
    for field in SUMMARY_FIELDS:
        lines.append(f"- {field}: {summary[field]}")
    lines.extend(["- market_ids:"])
    lines.extend(_render_nested_list(payload["market_ids"]))
    lines.extend(
        [
            "- interpretation: PAPER-004 defines constraints only and does not authorize simulation, recommendations, execution, or orders.",
            "",
            "## Future Simulation Contract",
            "",
            "- accepted_simulation_preview_status:",
            f"  - {payload['accepted_simulation_preview_status']}",
            "- allowed_future_simulation_statuses:",
        ]
    )
    lines.extend(_render_nested_list(payload["allowed_future_simulation_statuses"]))
    lines.append("- required_future_simulation_inputs:")
    lines.extend(_render_nested_list(payload["required_future_simulation_inputs"]))
    lines.append("- allowed_future_output_fields:")
    lines.extend(_render_nested_list(payload["allowed_future_output_fields"]))
    lines.append("- always_forbidden_future_fields:")
    lines.extend(_render_nested_list(payload["always_forbidden_future_fields"]))
    lines.append("- paper_004_forbidden_output_fields:")
    lines.extend(_render_nested_list(payload["paper_004_forbidden_output_fields"]))
    lines.extend(["", "## Policy Constraint Codes", "", "- policy_blockers:"])
    lines.extend(_render_nested_list(payload["policy_blockers"]))
    lines.append("- watch_only_reasons:")
    lines.extend(_render_nested_list(payload["watch_only_reasons"]))
    lines.extend(["", "## Policy Specs", ""])

    if not payload["policy_specs"]:
        lines.extend(["- none", ""])
    else:
        for record in payload["policy_specs"]:
            lines.extend(
                [
                    f"### {record['market_id'] or 'missing-market-id'}",
                    f"- accepted_preview_status: {record['accepted_preview_status']}",
                    f"- policy_spec_status: {record['policy_spec_status']}",
                    f"- source_policy_record_present: {record['source_policy_record_present']}",
                    f"- source_final_dossier_draft_present: {record['source_final_dossier_draft_present']}",
                    "- policy_boundaries:",
                ]
            )
            lines.extend(_render_nested_list(record["policy_boundaries"]))
            lines.append("")

    lines.extend(["## Safety Boundary", ""])
    lines.extend(
        [
            "- live_fetchers: false",
            "- network_api_calls: false",
            "- credentials: false",
            "- wallet_private_keys: false",
            "- authenticated_endpoints: false",
            "- trading_endpoints: false",
            "- real_orders: false",
            "- live_trading: false",
            "- paper_orders: false",
            "- betting_recommendations: false",
            "- truth_inference: false",
            "- market_scoring: false",
            "- probability_estimates: false",
            "- expected_value_calculations: false",
            "- side_recommendations: false",
            "- market_decisions: false",
            "- runtime_wiring: false",
        ]
    )
    lines.extend(["", "## Limitations", ""])
    for item in payload["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def write_paper_decision_policy_spec_artifacts(
    preview_path=DEFAULT_PREVIEW,
    policy_review_result_path=DEFAULT_POLICY_REVIEW_RESULT,
    final_dossier_drafts_path=DEFAULT_FINAL_DOSSIER_DRAFTS,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    payload = build_paper_decision_policy_spec(
        preview_path=preview_path,
        policy_review_result_path=policy_review_result_path,
        final_dossier_drafts_path=final_dossier_drafts_path,
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
        "policy_spec_summary": payload["policy_spec_summary"],
        "market_ids": payload["market_ids"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_paper_decision_policy_spec_artifacts(
        preview_path=args.preview,
        policy_review_result_path=args.policy_review_result,
        final_dossier_drafts_path=args.final_dossier_drafts,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
