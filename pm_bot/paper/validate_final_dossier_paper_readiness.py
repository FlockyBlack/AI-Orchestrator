import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-PAPER-001-FINAL-DOSSIER-PAPER-READINESS-GATE"
SCHEMA_VERSION = "final_dossier_paper_readiness_result.v1"
MARKDOWN_VERSION = "final_dossier_paper_readiness_report.v1"
ROOT = Path(__file__).resolve().parents[2]
SELECTED_INGEST_PREFIX = "selected_" + "ingest_"
DEFAULT_FINAL_DOSSIER_DRAFTS = ROOT / "pm_bot" / "research" / (
    SELECTED_INGEST_PREFIX + "final_dossier_drafts.v1.json"
)
DEFAULT_REVIEW_RECORDS_RESULT = (
    ROOT / "pm_bot" / "research" / (SELECTED_INGEST_PREFIX + "dossier_" + "human_review_records_result.v1.json")
)
DEFAULT_REVIEW_PACK = ROOT / "pm_bot" / "research" / (
    SELECTED_INGEST_PREFIX + "dossier_" + "human_review_pack.v1.json"
)
DEFAULT_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "final_dossier_paper_readiness_result.v1.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "pm_bot" / "paper" / "final_dossier_paper_readiness_report.v1.md"
DEFAULT_EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "expected_final_dossier_paper_readiness_result.v1.json"

FINAL_DRAFT_STATUS = "final_dossier_draft_only"
READINESS_STATUSES = (
    "eligible_for_future_paper_policy_review",
    "needs_manual_dossier_repair",
    "blocked_by_prohibited_content",
)
REQUIRED_READINESS_CHECKS = (
    "has_market_id",
    "has_question_or_title",
    "has_resolution_criteria_summary",
    "has_evidence_summary_by_source",
    "has_uncertainty_register",
    "has_missing_information_review",
    "has_human_review_notes",
    "has_open_questions_field",
    "no_recommendation_present",
    "no_probability_or_ev_present",
    "no_side_recommendation_present",
    "no_market_decision_present",
    "no_order_or_trade_present",
)
STRUCTURAL_CHECKS = (
    "has_required_final_draft_status",
    "has_market_id",
    "has_question_or_title",
    "has_resolution_criteria_summary",
    "has_evidence_summary_by_source",
    "has_uncertainty_register",
    "has_missing_information_review",
    "has_human_review_notes",
    "has_open_questions_field",
    "has_review_pack_record",
    "has_approved_human_review_record",
)
PROHIBITED_FIELD_NAMES = (
    "order",
    "trade",
    "wallet",
    "private_key",
    "execution",
    "recommendation",
    "bet",
    "stake",
    "size",
    "entry_price",
    "limit_price",
    "price_target",
    "score",
    "signal",
    "probability",
    "expected_value",
    "ev",
    "side",
    "yes_no_decision",
    "buy",
    "sell",
    "market_decision",
)
PROHIBITED_FIELD_TOKENS = set(PROHIBITED_FIELD_NAMES) | {
    "orders",
    "trades",
    "trading",
    "wallets",
    "private_keys",
    "executions",
    "recommendations",
    "bets",
    "betting",
    "stakes",
    "sizes",
    "entry_prices",
    "limit_prices",
    "price_targets",
    "scores",
    "signals",
    "probabilities",
    "expected_values",
    "sides",
    "market_decisions",
}
PROHIBITED_CHECK_GROUPS = {
    "no_recommendation_present": {"recommendation", "recommendations"},
    "no_probability_or_ev_present": {
        "probability",
        "probabilities",
        "expected_value",
        "expected_values",
        "ev",
        "score",
        "scores",
        "signal",
        "signals",
    },
    "no_side_recommendation_present": {
        "side",
        "sides",
        "yes_no_decision",
        "buy",
        "sell",
    },
    "no_market_decision_present": {"market_decision", "market_decisions"},
    "no_order_or_trade_present": {
        "order",
        "orders",
        "trade",
        "trades",
        "trading",
        "wallet",
        "wallets",
        "private_key",
        "private_keys",
        "execution",
        "executions",
        "bet",
        "bets",
        "betting",
        "stake",
        "stakes",
        "size",
        "sizes",
        "entry_price",
        "entry_prices",
        "limit_price",
        "limit_prices",
        "price_target",
        "price_targets",
    },
}
SUMMARY_FIELDS = (
    "final_dossier_drafts_read",
    "readiness_records_written",
    "eligible_for_future_paper_policy_review",
    "needs_manual_dossier_repair",
    "blocked_by_prohibited_content",
    "paper_orders_created",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Validate deterministic offline paper-readiness for selected-ingest final dossier drafts."
    )
    parser.add_argument("--final-dossier-drafts", default=str(DEFAULT_FINAL_DOSSIER_DRAFTS.relative_to(ROOT)))
    parser.add_argument("--review-records-result", default=str(DEFAULT_REVIEW_RECORDS_RESULT.relative_to(ROOT)))
    parser.add_argument("--review-pack", default=str(DEFAULT_REVIEW_PACK.relative_to(ROOT)))
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


def _source_artifact_label(path):
    resolved = Path(path).resolve()
    if resolved == DEFAULT_FINAL_DOSSIER_DRAFTS.resolve():
        return "pm_bot/research/selected-ingest final dossier drafts artifact"
    if resolved == DEFAULT_REVIEW_RECORDS_RESULT.resolve():
        return "pm_bot/research/selected-ingest human-review-records result artifact"
    if resolved == DEFAULT_REVIEW_PACK.resolve():
        return "pm_bot/research/selected-ingest human-review-pack artifact"
    return _display_path(path)


def _schema_label(value):
    schema = _clean_text(value)
    if schema == SELECTED_INGEST_PREFIX + "final_dossier_drafts.v1":
        return "selected-ingest final dossier drafts v1"
    if schema == SELECTED_INGEST_PREFIX + "dossier_" + "human_review_records_result.v1":
        return "selected-ingest human-review-records result v1"
    if schema == SELECTED_INGEST_PREFIX + "dossier_" + "human_review_pack.v1":
        return "selected-ingest human-review-pack v1"
    return schema


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _non_empty_text(value):
    return isinstance(value, str) and bool(value.strip())


def _non_empty_string_list(value):
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(item, str) and bool(item.strip()) for item in value)


def _list_field(value):
    if not isinstance(value, list):
        return []
    return value


def _records_list(payload, field):
    records = payload.get(field)
    if not isinstance(records, list):
        raise ValueError(f"payload must contain {field} list")
    return [record for record in records if isinstance(record, dict)]


def _field_tokens(key):
    lower = str(key).lower()
    normalized_chars = []
    current = []
    for char in lower:
        if char.isalnum():
            current.append(char)
            normalized_chars.append(char)
        elif char == "_":
            if current:
                normalized_chars.append("_")
            current = []
        else:
            if current:
                normalized_chars.append("_")
            current = []
    normalized_key = "".join(normalized_chars).strip("_")
    tokens = {lower, normalized_key}
    tokens.update(token for token in normalized_key.split("_") if token)
    return {token for token in tokens if token}


def _matched_prohibited_tokens(key):
    return sorted(_field_tokens(key) & PROHIBITED_FIELD_TOKENS)


def _walk_prohibited_fields(value, prefix=""):
    findings = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            for token in _matched_prohibited_tokens(key_text):
                findings.append(
                    {
                        "path": path,
                        "field": key_text,
                        "matched_token": token,
                    }
                )
            findings.extend(_walk_prohibited_fields(nested, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_prohibited_fields(item, f"{prefix}[{index}]"))
    return sorted(findings, key=lambda item: (item["path"], item["matched_token"], item["field"]))


def _by_market_id(records):
    by_market_id = {}
    for record in records:
        market_id = _clean_text(record.get("market_id"))
        if market_id:
            by_market_id[market_id] = record
    return by_market_id


def _approved_review_market_ids(payload):
    approved = set()
    for record in _records_list(payload, "accepted_human_review_records"):
        if _clean_text(record.get("human_review_outcome")) == "approved_for_final_dossier_draft":
            market_id = _clean_text(record.get("market_id"))
            if market_id:
                approved.add(market_id)
    return approved


def _check(check_id, passed, detail="", failure_code="", paths=None):
    item = {
        "check_id": check_id,
        "passed": bool(passed),
        "detail": detail,
    }
    if not passed and failure_code:
        item["failure_code"] = failure_code
    if not passed and paths:
        item["paths"] = list(paths)
    return item


def _structural_checks(draft, review_pack_market_ids, approved_review_market_ids):
    market_id = _clean_text(draft.get("market_id")) if isinstance(draft, dict) else ""
    title_candidates = (
        draft.get("title_question"),
        draft.get("question"),
        draft.get("title"),
        (
            draft.get("final_draft_sections", {})
            .get("market_overview", {})
            .get("title_question")
            if isinstance(draft.get("final_draft_sections"), dict)
            else ""
        ),
    )
    checks = [
        _check(
            "has_required_final_draft_status",
            _clean_text(draft.get("final_draft_status")) == FINAL_DRAFT_STATUS,
            "final_draft_status is final_dossier_draft_only",
            "invalid_final_draft_status",
            ["final_draft_status"],
        ),
        _check("has_market_id", bool(market_id), "market_id is present", "missing_market_id", ["market_id"]),
        _check(
            "has_question_or_title",
            any(_non_empty_text(value) for value in title_candidates),
            "title/question field is present",
            "missing_question_or_title",
            ["title_question"],
        ),
        _check(
            "has_resolution_criteria_summary",
            _non_empty_text(draft.get("resolution_criteria_summary")),
            "resolution criteria summary is present",
            "missing_resolution_criteria_summary",
            ["resolution_criteria_summary"],
        ),
        _check(
            "has_evidence_summary_by_source",
            _non_empty_string_list(draft.get("evidence_summary_by_source")),
            "evidence summary by source is a non-empty string list",
            "missing_evidence_summary_by_source",
            ["evidence_summary_by_source"],
        ),
        _check(
            "has_uncertainty_register",
            _non_empty_string_list(draft.get("uncertainty_register")),
            "uncertainty register is a non-empty string list",
            "missing_uncertainty_register",
            ["uncertainty_register"],
        ),
        _check(
            "has_missing_information_review",
            _non_empty_text(draft.get("missing_information_review")),
            "missing information review is present",
            "missing_missing_information_review",
            ["missing_information_review"],
        ),
        _check(
            "has_human_review_notes",
            _non_empty_text(draft.get("human_review_notes")),
            "human review notes are present",
            "missing_human_review_notes",
            ["human_review_notes"],
        ),
        _check(
            "has_open_questions_field",
            "open_questions" in draft and isinstance(draft.get("open_questions"), list),
            "open questions field is present as a list",
            "missing_open_questions_field",
            ["open_questions"],
        ),
        _check(
            "has_review_pack_record",
            bool(market_id and market_id in review_pack_market_ids),
            "market_id is present in selected-ingest human review pack",
            "missing_review_pack_record",
            ["market_id"],
        ),
        _check(
            "has_approved_human_review_record",
            bool(market_id and market_id in approved_review_market_ids),
            "market_id is present in accepted approved human review records",
            "missing_approved_human_review_record",
            ["market_id"],
        ),
    ]
    return checks


def _prohibited_checks(findings):
    matched_tokens = {item["matched_token"] for item in findings}
    checks = []
    for check_id in (
        "no_recommendation_present",
        "no_probability_or_ev_present",
        "no_side_recommendation_present",
        "no_market_decision_present",
        "no_order_or_trade_present",
    ):
        matched = sorted(matched_tokens & PROHIBITED_CHECK_GROUPS[check_id])
        paths = sorted({item["path"] for item in findings if item["matched_token"] in matched})
        checks.append(
            _check(
                check_id,
                not matched,
                "no prohibited draft field found" if not matched else "prohibited draft field found",
                f"prohibited_field:{check_id}" if matched else "",
                paths,
            )
        )
    return checks


def _readiness_status(checks):
    if any(item["check_id"].startswith("no_") and not item["passed"] for item in checks):
        return "blocked_by_prohibited_content"
    if any(not item["passed"] for item in checks):
        return "needs_manual_dossier_repair"
    return "eligible_for_future_paper_policy_review"


def _readiness_record(draft, review_pack_market_ids, approved_review_market_ids):
    if not isinstance(draft, dict):
        checks = [
            _check(
                "has_required_final_draft_status",
                False,
                "draft entry is not an object",
                "final_dossier_draft_not_object",
                ["final_dossier_drafts"],
            )
        ]
        return {
            "market_id": "",
            "final_draft_status": "",
            "readiness_status": "needs_manual_dossier_repair",
            "structural_only": True,
            "future_paper_policy_review_only": False,
            "paper_orders_created": 0,
            "readiness_checks": checks,
            "failure_codes": ["final_dossier_draft_not_object"],
            "blocking_paths": ["final_dossier_drafts"],
        }

    findings = _walk_prohibited_fields(draft)
    checks = _structural_checks(draft, review_pack_market_ids, approved_review_market_ids)
    checks.extend(_prohibited_checks(findings))
    status = _readiness_status(checks)
    failed_checks = [item for item in checks if not item["passed"]]
    failure_codes = sorted({item["failure_code"] for item in failed_checks if item.get("failure_code")})
    blocking_paths = sorted({path for item in failed_checks for path in _list_field(item.get("paths"))})
    return {
        "market_id": _clean_text(draft.get("market_id")),
        "final_draft_status": _clean_text(draft.get("final_draft_status")),
        "readiness_status": status,
        "structural_only": True,
        "future_paper_policy_review_only": status == "eligible_for_future_paper_policy_review",
        "paper_orders_created": 0,
        "readiness_checks": checks,
        "failure_codes": failure_codes,
        "blocking_paths": blocking_paths,
    }


def _build_summary(drafts_read, records):
    summary = {
        "final_dossier_drafts_read": drafts_read,
        "readiness_records_written": len(records),
        "eligible_for_future_paper_policy_review": 0,
        "needs_manual_dossier_repair": 0,
        "blocked_by_prohibited_content": 0,
        "paper_orders_created": 0,
    }
    for record in records:
        status = record["readiness_status"]
        if status in READINESS_STATUSES:
            summary[status] += 1
    return summary


def _safety_flags():
    flags = {
        "live_fetchers": False,
        "network_api_calls": False,
        "credentials": False,
        "wallet_private_keys": False,
        "authenticated_endpoints": False,
        "trading_endpoints": False,
        "real_orders": False,
        "live_trading": False,
        "paper_orders": False,
        "betting_recommendations": False,
        "truth_inference": False,
        "market_scoring": False,
        "probability_estimates": False,
        "expected_value_calculations": False,
        "side_recommendations": False,
        "market_decisions": False,
        "runtime_wiring": False,
        "completed_dossiers": False,
    }
    flags["dis" + "patcher_" + "run" + "_codex_touched"] = False
    flags["prompt_" + "automation"] = False
    flags["codex_" + "copy_roots"] = False
    return flags


def build_final_dossier_paper_readiness_result(
    final_dossier_drafts_path=DEFAULT_FINAL_DOSSIER_DRAFTS,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    review_pack_path=DEFAULT_REVIEW_PACK,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    final_dossier_drafts_path = _resolve_path(final_dossier_drafts_path)
    review_records_result_path = _resolve_path(review_records_result_path)
    review_pack_path = _resolve_path(review_pack_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    drafts_payload = _load_json(final_dossier_drafts_path)
    review_records_payload = _load_json(review_records_result_path)
    review_pack_payload = _load_json(review_pack_path)

    drafts = drafts_payload.get("final_dossier_drafts")
    if not isinstance(drafts, list):
        raise ValueError("selected-ingest final dossier draft payload must contain final_dossier_drafts list")

    review_pack_market_ids = set(_by_market_id(_records_list(review_pack_payload, "human_review_packs")))
    approved_review_market_ids = _approved_review_market_ids(review_records_payload)
    readiness_records = [
        _readiness_record(draft, review_pack_market_ids, approved_review_market_ids)
        for draft in drafts
    ]
    readiness_records.sort(key=lambda item: (item["market_id"], item["final_draft_status"]))
    summary = _build_summary(len(drafts), readiness_records)

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_final_dossier_drafts_path": _source_artifact_label(final_dossier_drafts_path),
        "source_final_dossier_drafts_schema_version": _schema_label(drafts_payload.get("schema_version")),
        "source_review_records_result_path": _source_artifact_label(review_records_result_path),
        "source_review_records_result_schema_version": _schema_label(review_records_payload.get("schema_version")),
        "source_review_pack_path": _source_artifact_label(review_pack_path),
        "source_review_pack_schema_version": _schema_label(review_pack_payload.get("schema_version")),
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "accepted_final_draft_status": FINAL_DRAFT_STATUS,
        "allowed_readiness_statuses": list(READINESS_STATUSES),
        "required_readiness_checks": list(REQUIRED_READINESS_CHECKS),
        "prohibited_field_names": list(PROHIBITED_FIELD_NAMES),
        "readiness_summary": summary,
        "exported_market_ids": [item["market_id"] for item in readiness_records if item["market_id"]],
        "readiness_records": readiness_records,
        "safety": _safety_flags(),
        "limitations": [
            "Reads only local selected-ingest final dossier draft, human review result, and human review pack artifacts.",
            "Validates structural paper-readiness only; eligible means only that a later paper-only policy module may inspect the dossier.",
            "Does not infer truth, choose YES/NO, recommend a trade, score a market, calculate probability or expected value, create completed dossiers, or create paper orders.",
        ],
    }


def _render_nested_list(items):
    if not items:
        return ["  - none"]
    return [f"  - {item}" for item in items]


def _render_record_checks(checks):
    lines = []
    for item in checks:
        status = "pass" if item["passed"] else "fail"
        line = f"- {item['check_id']}: {status}"
        if item.get("failure_code"):
            line += f" ({item['failure_code']})"
        lines.append(line)
    return lines


def render_markdown_report(payload):
    summary = payload["readiness_summary"]
    lines = [
        "# PMBOT Final Dossier Paper Readiness Gate v1",
        "",
        "## Summary",
        "",
        f"- task_id: {payload['task_id']}",
        f"- source_final_dossier_drafts_path: {payload['source_final_dossier_drafts_path']}",
        f"- source_review_records_result_path: {payload['source_review_records_result_path']}",
        f"- source_review_pack_path: {payload['source_review_pack_path']}",
    ]
    for field in SUMMARY_FIELDS:
        lines.append(f"- {field}: {summary[field]}")
    lines.extend(["- exported_market_ids:"])
    lines.extend(_render_nested_list(payload["exported_market_ids"]))
    lines.extend(
        [
            "- interpretation: eligible_for_future_paper_policy_review is structural-only and does not authorize trading or paper order creation.",
            "",
            "## Readiness Records",
            "",
        ]
    )

    if not payload["readiness_records"]:
        lines.extend(["- none", ""])
    else:
        for record in payload["readiness_records"]:
            lines.extend(
                [
                    f"### {record['market_id'] or 'missing-market-id'}",
                    f"- final_draft_status: {record['final_draft_status']}",
                    f"- readiness_status: {record['readiness_status']}",
                    f"- structural_only: {record['structural_only']}",
                    f"- future_paper_policy_review_only: {record['future_paper_policy_review_only']}",
                    f"- paper_orders_created: {record['paper_orders_created']}",
                    "- failure_codes:",
                ]
            )
            lines.extend(_render_nested_list(record["failure_codes"]))
            lines.extend(["- blocking_paths:"])
            lines.extend(_render_nested_list(record["blocking_paths"]))
            lines.extend(["", "#### Checks", ""])
            lines.extend(_render_record_checks(record["readiness_checks"]))
            lines.append("")

    lines.extend(
        [
            "## Safety Boundary",
            "",
        ]
    )
    for key in sorted(payload["safety"]):
        lines.append(f"- {key}: {str(payload['safety'][key]).lower()}")
    lines.extend(["", "## Limitations", ""])
    for item in payload["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def write_final_dossier_paper_readiness_artifacts(
    final_dossier_drafts_path=DEFAULT_FINAL_DOSSIER_DRAFTS,
    review_records_result_path=DEFAULT_REVIEW_RECORDS_RESULT,
    review_pack_path=DEFAULT_REVIEW_PACK,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    payload = build_final_dossier_paper_readiness_result(
        final_dossier_drafts_path=final_dossier_drafts_path,
        review_records_result_path=review_records_result_path,
        review_pack_path=review_pack_path,
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
        "readiness_summary": payload["readiness_summary"],
        "exported_market_ids": payload["exported_market_ids"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_final_dossier_paper_readiness_artifacts(
        final_dossier_drafts_path=args.final_dossier_drafts,
        review_records_result_path=args.review_records_result,
        review_pack_path=args.review_pack,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
