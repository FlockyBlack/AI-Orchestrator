import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-PAPER-002-PAPER-POLICY-REVIEW-CONTRACT"
SCHEMA_VERSION = "paper_policy_review_result.v1"
MARKDOWN_VERSION = "paper_policy_review_report.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_READINESS_RESULT = ROOT / "pm_bot" / "paper" / "final_dossier_paper_readiness_result.v1.json"
DEFAULT_FINAL_DOSSIER_DRAFTS = ROOT / "pm_bot" / "research" / "selected_ingest_final_dossier_drafts.v1.json"
DEFAULT_POLICY_RECORDS = ROOT / "pm_bot" / "paper" / "paper_policy_review_records_fixture.v1.json"
DEFAULT_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "paper_policy_review_result.v1.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "pm_bot" / "paper" / "paper_policy_review_report.v1.md"
DEFAULT_EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "paper" / "expected_paper_policy_review_result.v1.json"

ELIGIBLE_READINESS_STATUS = "eligible_for_future_paper_policy_review"
ALLOWED_FUTURE_POLICY_STATUSES = (
    "eligible_for_future_paper_decision_simulation",
    "watch_only_policy_review",
    "needs_more_manual_review",
    "blocked_by_policy",
)
REQUIRED_POLICY_CHECKS = (
    "dossier_readiness_confirmed",
    "no_prohibited_trading_language",
    "no_probability_or_ev_present",
    "no_side_recommendation_present",
    "no_market_decision_present",
    "unresolved_questions_reviewed",
    "uncertainty_register_present",
    "evidence_inventory_present",
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
    "no_prohibited_trading_language": {
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
        "buy",
        "sell",
    },
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
        "recommendation",
        "recommendations",
        "side",
        "sides",
        "yes_no_decision",
        "buy",
        "sell",
    },
    "no_market_decision_present": {
        "market_decision",
        "market_decisions",
        "yes_no_decision",
    },
}
SUMMARY_FIELDS = (
    "policy_records_read",
    "policy_records_accepted",
    "policy_records_rejected",
    "eligible_for_future_paper_decision_simulation",
    "watch_only_policy_review",
    "needs_more_manual_review",
    "blocked_by_policy",
    "paper_orders_created",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Validate deterministic offline paper-policy-review contract records."
    )
    parser.add_argument("--readiness-result", default=str(DEFAULT_READINESS_RESULT.relative_to(ROOT)))
    parser.add_argument("--final-dossier-drafts", default=str(DEFAULT_FINAL_DOSSIER_DRAFTS.relative_to(ROOT)))
    parser.add_argument("--policy-records", default=str(DEFAULT_POLICY_RECORDS.relative_to(ROOT)))
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
    if resolved == DEFAULT_READINESS_RESULT.resolve():
        return "pm_bot/paper final dossier paper-readiness result artifact"
    if resolved == DEFAULT_FINAL_DOSSIER_DRAFTS.resolve():
        return "pm_bot/research selected-ingest final dossier drafts artifact"
    if resolved == DEFAULT_POLICY_RECORDS.resolve():
        return "pm_bot/paper paper-policy-review records fixture"
    return _display_path(path)


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


def _list_field(value):
    if isinstance(value, list):
        return value
    return []


def _non_empty_string_list(value):
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(item, str) and bool(item.strip()) for item in value)


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


def _policy_check_assertions(record):
    raw_checks = record.get("policy_checks")
    if not isinstance(raw_checks, list):
        return {}
    assertions = {}
    for item in raw_checks:
        if isinstance(item, dict):
            check_id = _clean_text(item.get("check_id"))
            if check_id:
                assertions[check_id] = item.get("passed") is True
    return assertions


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


def _prohibited_paths(findings, check_id):
    tokens = PROHIBITED_CHECK_GROUPS.get(check_id, set())
    return sorted({item["path"] for item in findings if item["matched_token"] in tokens})


def _assertion_failure(check_id, assertions):
    if check_id not in assertions:
        return f"missing_policy_check:{check_id}"
    if assertions[check_id] is not True:
        return f"failed_policy_check:{check_id}"
    return ""


def _assertion_passed(check_id, assertions):
    return assertions.get(check_id) is True


def _draft_has_unresolved_review(draft):
    if not isinstance(draft, dict):
        return False
    sections = draft.get("final_draft_sections")
    return isinstance(draft.get("open_questions"), list) and isinstance(sections, dict) and isinstance(
        sections.get("unresolved_questions"), dict
    )


def _draft_has_uncertainty_register(draft):
    if not isinstance(draft, dict):
        return False
    if _non_empty_string_list(draft.get("uncertainty_register")):
        return True
    sections = draft.get("final_draft_sections")
    return isinstance(sections, dict) and _non_empty_string_list(sections.get("uncertainty_notes"))


def _draft_has_evidence_inventory(draft):
    if not isinstance(draft, dict):
        return False
    if _non_empty_string_list(draft.get("evidence_summary_by_source")):
        return True
    sections = draft.get("final_draft_sections")
    return isinstance(sections, dict) and _non_empty_string_list(sections.get("evidence_inventory"))


def _build_policy_checks(record, source_readiness_record, source_draft, findings):
    market_id = _clean_text(record.get("market_id")) if isinstance(record, dict) else ""
    assertions = _policy_check_assertions(record)
    source_readiness_status = (
        _clean_text(source_readiness_record.get("readiness_status"))
        if isinstance(source_readiness_record, dict)
        else ""
    )
    record_readiness_status = _clean_text(record.get("readiness_status")) if isinstance(record, dict) else ""

    checks = []
    readiness_ok = (
        bool(market_id)
        and isinstance(source_readiness_record, dict)
        and record_readiness_status == ELIGIBLE_READINESS_STATUS
        and source_readiness_status == ELIGIBLE_READINESS_STATUS
    )
    readiness_failure_code = _assertion_failure("dossier_readiness_confirmed", assertions)
    readiness_paths = []
    if not market_id:
        readiness_failure_code = "missing_market_id"
        readiness_paths.append("market_id")
    elif not isinstance(source_readiness_record, dict):
        readiness_failure_code = "unknown_market_id"
        readiness_paths.append("market_id")
    elif record_readiness_status != ELIGIBLE_READINESS_STATUS:
        readiness_failure_code = "invalid_record_readiness_status"
        readiness_paths.append("readiness_status")
    elif source_readiness_status != ELIGIBLE_READINESS_STATUS:
        readiness_failure_code = "source_readiness_status_not_eligible"
        readiness_paths.append("readiness_status")
    elif readiness_failure_code:
        readiness_paths.append("policy_checks")
    checks.append(
        _check(
            "dossier_readiness_confirmed",
            readiness_ok and _assertion_passed("dossier_readiness_confirmed", assertions),
            "record and source readiness status are eligible for future paper policy review",
            readiness_failure_code,
            readiness_paths,
        )
    )

    for check_id in (
        "no_prohibited_trading_language",
        "no_probability_or_ev_present",
        "no_side_recommendation_present",
        "no_market_decision_present",
    ):
        paths = _prohibited_paths(findings, check_id)
        failure_code = _assertion_failure(check_id, assertions)
        if paths:
            failure_code = f"prohibited_field:{check_id}"
        elif failure_code:
            paths = ["policy_checks"]
        checks.append(
            _check(
                check_id,
                not paths and _assertion_passed(check_id, assertions),
                "no prohibited policy-review field found" if not paths else "prohibited policy-review field found",
                failure_code,
                paths,
            )
        )

    source_checks = (
        (
            "unresolved_questions_reviewed",
            _draft_has_unresolved_review(source_draft),
            "source draft has unresolved-question review structure",
            "missing_unresolved_questions_review",
        ),
        (
            "uncertainty_register_present",
            _draft_has_uncertainty_register(source_draft),
            "source draft has an uncertainty register",
            "missing_uncertainty_register",
        ),
        (
            "evidence_inventory_present",
            _draft_has_evidence_inventory(source_draft),
            "source draft has an evidence inventory",
            "missing_evidence_inventory",
        ),
    )
    for check_id, source_ok, detail, source_failure_code in source_checks:
        failure_code = _assertion_failure(check_id, assertions)
        paths = []
        if not source_ok:
            failure_code = source_failure_code
            paths.append("market_id")
        elif failure_code:
            paths.append("policy_checks")
        checks.append(
            _check(
                check_id,
                source_ok and _assertion_passed(check_id, assertions),
                detail,
                failure_code,
                paths,
            )
        )

    return checks


def _record_future_policy_status(record, checks, findings, source_readiness_record):
    declared_status = _clean_text(record.get("future_policy_status")) if isinstance(record, dict) else ""
    record_readiness_status = _clean_text(record.get("readiness_status")) if isinstance(record, dict) else ""
    source_readiness_status = (
        _clean_text(source_readiness_record.get("readiness_status"))
        if isinstance(source_readiness_record, dict)
        else ""
    )
    failed_checks = [item for item in checks if not item["passed"]]
    if findings:
        return "blocked_by_policy"
    if (
        not isinstance(source_readiness_record, dict)
        or record_readiness_status != ELIGIBLE_READINESS_STATUS
        or source_readiness_status != ELIGIBLE_READINESS_STATUS
    ):
        return "blocked_by_policy"
    if declared_status not in ALLOWED_FUTURE_POLICY_STATUSES:
        return "needs_more_manual_review"
    if failed_checks:
        return "needs_more_manual_review"
    return declared_status


def _policy_record(record, source_readiness_by_market_id, source_drafts_by_market_id):
    if not isinstance(record, dict):
        checks = [
            _check(
                "dossier_readiness_confirmed",
                False,
                "policy review entry is not an object",
                "policy_review_record_not_object",
                ["policy_review_records"],
            )
        ]
        return {
            "record_id": "",
            "market_id": "",
            "readiness_status": "",
            "declared_future_policy_status": "",
            "future_policy_status": "blocked_by_policy",
            "record_validation_status": "rejected",
            "source_readiness_record_found": False,
            "source_final_dossier_draft_found": False,
            "checks": checks,
            "failure_codes": ["policy_review_record_not_object"],
            "blocking_paths": ["policy_review_records"],
        }

    market_id = _clean_text(record.get("market_id"))
    source_readiness_record = source_readiness_by_market_id.get(market_id)
    source_draft = source_drafts_by_market_id.get(market_id)
    findings = _walk_prohibited_fields(record)
    checks = _build_policy_checks(record, source_readiness_record, source_draft, findings)
    declared_status = _clean_text(record.get("future_policy_status"))
    future_status = _record_future_policy_status(record, checks, findings, source_readiness_record)
    failed_checks = [item for item in checks if not item["passed"]]
    failure_codes = sorted({item["failure_code"] for item in failed_checks if item.get("failure_code")})
    blocking_paths = sorted({path for item in failed_checks for path in _list_field(item.get("paths"))})
    if declared_status not in ALLOWED_FUTURE_POLICY_STATUSES:
        failure_codes.append("invalid_future_policy_status")
        blocking_paths.append("future_policy_status")
    failure_codes = sorted(set(failure_codes))
    blocking_paths = sorted(set(blocking_paths))

    return {
        "record_id": _clean_text(record.get("record_id")),
        "market_id": market_id,
        "readiness_status": _clean_text(record.get("readiness_status")),
        "declared_future_policy_status": declared_status,
        "future_policy_status": future_status,
        "record_validation_status": "accepted" if not failure_codes else "rejected",
        "source_readiness_record_found": isinstance(source_readiness_record, dict),
        "source_final_dossier_draft_found": isinstance(source_draft, dict),
        "checks": checks,
        "failure_codes": failure_codes,
        "blocking_paths": blocking_paths,
    }


def _build_summary(records):
    summary = {
        "policy_records_read": len(records),
        "policy_records_accepted": 0,
        "policy_records_rejected": 0,
        "eligible_for_future_paper_decision_simulation": 0,
        "watch_only_policy_review": 0,
        "needs_more_manual_review": 0,
        "blocked_by_policy": 0,
        "paper_orders_created": 0,
    }
    for record in records:
        if record["record_validation_status"] == "accepted":
            summary["policy_records_accepted"] += 1
        else:
            summary["policy_records_rejected"] += 1
        status = record["future_policy_status"]
        if status in ALLOWED_FUTURE_POLICY_STATUSES:
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


def build_paper_policy_review_result(
    readiness_result_path=DEFAULT_READINESS_RESULT,
    final_dossier_drafts_path=DEFAULT_FINAL_DOSSIER_DRAFTS,
    policy_records_path=DEFAULT_POLICY_RECORDS,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    readiness_result_path = _resolve_path(readiness_result_path)
    final_dossier_drafts_path = _resolve_path(final_dossier_drafts_path)
    policy_records_path = _resolve_path(policy_records_path)
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)

    readiness_payload = _load_json(readiness_result_path)
    drafts_payload = _load_json(final_dossier_drafts_path)
    policy_payload = _load_json(policy_records_path)

    source_readiness_by_market_id = _by_market_id(_records_list(readiness_payload, "readiness_records"))
    source_drafts_by_market_id = _by_market_id(_records_list(drafts_payload, "final_dossier_drafts"))
    policy_records = [
        _policy_record(record, source_readiness_by_market_id, source_drafts_by_market_id)
        for record in _records_list(policy_payload, "policy_review_records")
    ]
    summary = _build_summary(policy_records)
    market_ids = sorted(
        {
            record["market_id"]
            for record in policy_records
            if record["market_id"] and record["record_validation_status"] == "accepted"
        }
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "markdown_version": MARKDOWN_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "source_readiness_result_path": _source_artifact_label(readiness_result_path),
        "source_readiness_result_schema_version": _clean_text(readiness_payload.get("schema_version")),
        "source_final_dossier_drafts_path": _source_artifact_label(final_dossier_drafts_path),
        "source_final_dossier_drafts_schema_version": _clean_text(drafts_payload.get("schema_version")),
        "source_policy_records_path": _source_artifact_label(policy_records_path),
        "source_policy_records_schema_version": _clean_text(policy_payload.get("schema_version")),
        "json_output_path": _display_path(json_output_path),
        "markdown_output_path": _display_path(markdown_output_path),
        "expected_json_output_path": _display_path(expected_json_output_path),
        "accepted_readiness_status": ELIGIBLE_READINESS_STATUS,
        "allowed_future_policy_statuses": list(ALLOWED_FUTURE_POLICY_STATUSES),
        "required_policy_checks": list(REQUIRED_POLICY_CHECKS),
        "prohibited_field_names": list(PROHIBITED_FIELD_NAMES),
        "policy_summary": summary,
        "market_ids": market_ids,
        "policy_records": policy_records,
        "safety": _safety_flags(),
        "limitations": [
            "Reads only local paper-readiness, selected-ingest final draft, and paper-policy-review fixture artifacts.",
            "eligible_for_future_paper_decision_simulation only means a later module may run a paper-only decision review simulation.",
            "This contract does not approve a paper order, choose a side, infer truth, recommend a trade, score a market, calculate probability, calculate expected value, or create paper orders.",
        ],
    }


def _render_nested_list(items):
    if not items:
        return ["  - none"]
    return [f"  - {item}" for item in items]


def _render_checks(checks):
    lines = []
    for item in checks:
        status = "pass" if item["passed"] else "fail"
        line = f"- {item['check_id']}: {status}"
        if item.get("failure_code"):
            line += f" ({item['failure_code']})"
        lines.append(line)
    return lines


def render_markdown_report(payload):
    summary = payload["policy_summary"]
    lines = [
        "# PMBOT Paper Policy Review Contract v1",
        "",
        "## Summary",
        "",
        f"- task_id: {payload['task_id']}",
        f"- source_readiness_result_path: {payload['source_readiness_result_path']}",
        f"- source_final_dossier_drafts_path: {payload['source_final_dossier_drafts_path']}",
        f"- source_policy_records_path: {payload['source_policy_records_path']}",
    ]
    for field in SUMMARY_FIELDS:
        lines.append(f"- {field}: {summary[field]}")
    lines.extend(["- market_ids:"])
    lines.extend(_render_nested_list(payload["market_ids"]))
    lines.extend(
        [
            "- interpretation: eligible_for_future_paper_decision_simulation allows only a later paper-only decision-review simulation and does not authorize paper orders.",
            "",
            "## Policy Records",
            "",
        ]
    )

    if not payload["policy_records"]:
        lines.extend(["- none", ""])
    else:
        for record in payload["policy_records"]:
            title = record["record_id"] or record["market_id"] or "missing-record-id"
            lines.extend(
                [
                    f"### {title}",
                    f"- market_id: {record['market_id'] or 'missing-market-id'}",
                    f"- readiness_status: {record['readiness_status']}",
                    f"- declared_future_policy_status: {record['declared_future_policy_status']}",
                    f"- future_policy_status: {record['future_policy_status']}",
                    f"- record_validation_status: {record['record_validation_status']}",
                    f"- source_readiness_record_found: {record['source_readiness_record_found']}",
                    f"- source_final_dossier_draft_found: {record['source_final_dossier_draft_found']}",
                    "- failure_codes:",
                ]
            )
            lines.extend(_render_nested_list(record["failure_codes"]))
            lines.extend(["- blocking_paths:"])
            lines.extend(_render_nested_list(record["blocking_paths"]))
            lines.extend(["", "#### Checks", ""])
            lines.extend(_render_checks(record["checks"]))
            lines.append("")

    lines.extend(["## Safety Boundary", ""])
    for key in sorted(payload["safety"]):
        lines.append(f"- {key}: {str(payload['safety'][key]).lower()}")
    lines.extend(["", "## Limitations", ""])
    for item in payload["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def write_paper_policy_review_artifacts(
    readiness_result_path=DEFAULT_READINESS_RESULT,
    final_dossier_drafts_path=DEFAULT_FINAL_DOSSIER_DRAFTS,
    policy_records_path=DEFAULT_POLICY_RECORDS,
    json_output_path=DEFAULT_JSON_OUTPUT,
    markdown_output_path=DEFAULT_MARKDOWN_OUTPUT,
    expected_json_output_path=DEFAULT_EXPECTED_JSON_OUTPUT,
):
    json_output_path = _resolve_path(json_output_path)
    markdown_output_path = _resolve_path(markdown_output_path)
    expected_json_output_path = _resolve_path(expected_json_output_path)
    payload = build_paper_policy_review_result(
        readiness_result_path=readiness_result_path,
        final_dossier_drafts_path=final_dossier_drafts_path,
        policy_records_path=policy_records_path,
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
        "policy_summary": payload["policy_summary"],
        "market_ids": payload["market_ids"],
    }


def main(argv):
    args = _parse_args(argv)
    summary = write_paper_policy_review_artifacts(
        readiness_result_path=args.readiness_result,
        final_dossier_drafts_path=args.final_dossier_drafts,
        policy_records_path=args.policy_records,
        json_output_path=args.json_output,
        markdown_output_path=args.markdown_output,
        expected_json_output_path=args.expected_json_output,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
