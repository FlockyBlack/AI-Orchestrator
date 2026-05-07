import argparse
import json
import re
from pathlib import Path

from pm_bot.llm import manual_resolution_source_capture as capture


TASK_ID = "PMBOT-SOURCE-004-LOCAL-MANUAL-RESOLUTION-SOURCE-CAPTURE-PACKETS"
SCHEMA_VERSION = "manual_resolution_source_capture_validation.v1"
GENERATED_BY = "pm_bot/llm/manual_resolution_source_capture_validator.py"

ROOT = Path(__file__).resolve().parents[2]

VALIDATION_JSON = "pm_bot/llm/manual_resolution_source_capture_validation.v1.json"
VALIDATION_MD = "pm_bot/llm/manual_resolution_source_capture_validation.v1.md"

REQUIRED_TEMPLATE_FIELDS = (
    "contract_version",
    "schema_version",
    "market_id",
    "category",
    "market_title_or_question",
    "current_openrouter_review_status",
    "current_readiness_band",
    "source_capture_status",
    "capture_status",
    "full_market_resolution_criteria_text",
    "full_resolution_rules",
    "official_source_references",
    "official_source_urls_or_rule_references",
    "source_timestamps",
    "source_reliability_review",
    "reviewed_local_evidence_references",
    "non_placeholder_evidence_notes",
    "jurisdiction",
    "candidate_or_party_if_applicable",
    "manual_operator_notes",
    "unresolved_source_questions",
    "source_capture_author_or_operator",
    "source_capture_timestamp_local",
    "source_capture_provenance",
    "missing_fields_prefilled_from_source_003",
    "source_003_audit_reference",
    "packet_inventory_reference",
    "readiness_gate_reference",
    "operator_instructions",
    "safety_summary",
    *tuple(capture.NO_AUTHORITY_FLAGS),
)

PROHIBITION_MARKERS = (
    "do not",
    "no ",
    "not ",
    "without",
    "prohibited",
    "forbidden",
    "does not",
    "must not",
    "never",
)

FORBIDDEN_GUIDANCE_PATTERNS = (
    re.compile(r"\b(buy|sell|hold|enter|exit)\b", re.IGNORECASE),
    re.compile(r"\bprobability\b|\bEV\b|\bedge\b|\bconfidence\b", re.IGNORECASE),
    re.compile(r"\bside selection\b", re.IGNORECASE),
    re.compile(r"\b(trading|market|order|position).*\brecommend", re.IGNORECASE),
    re.compile(r"\brecommend.*\b(trading|market|order|position|side)", re.IGNORECASE),
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Validate local manual PMBOT resolution/source capture templates."
    )
    parser.add_argument("--write", action="store_true", help="Write validation JSON and Markdown.")
    parser.add_argument("--markdown", action="store_true", help="Print validation Markdown instead of JSON.")
    return parser.parse_args(argv)


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _load_json(path, root=ROOT):
    with _resolve(path, root=root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _ascii(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def _write_text(path, text, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(_ascii(text), encoding="utf-8")


def _is_empty(value):
    return value is None or value == "" or value == [] or value == {}


def _capture_paths(root=ROOT):
    directory = _resolve(capture.SOURCE_PATHS["capture_dir"], root=root)
    return sorted(directory.glob("*_resolution_source_capture.v1.json"))


def _string_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _string_values(item)
    elif isinstance(value, str):
        yield value


def _is_prohibition_context(text):
    lowered = text.lower()
    return any(marker in lowered for marker in PROHIBITION_MARKERS)


def _market_action_guidance_findings(payload):
    findings = []
    for text in _string_values(payload):
        if _is_prohibition_context(text):
            continue
        for pattern in FORBIDDEN_GUIDANCE_PATTERNS:
            if pattern.search(text):
                findings.append(text)
                break
    return findings


def _validate_status(payload):
    statuses = set(capture.CAPTURE_STATUS_VALUES)
    capture_status = payload.get("capture_status")
    source_capture_status = payload.get("source_capture_status")
    errors = []
    if capture_status not in statuses:
        errors.append("capture_status_invalid")
    if source_capture_status not in statuses:
        errors.append("source_capture_status_invalid")
    if capture_status != source_capture_status:
        errors.append("capture_status_mismatch")
    return errors


def validate_capture_packet(payload, schema):
    market_id = str(payload.get("market_id") or "unknown")
    missing = [field for field in REQUIRED_TEMPLATE_FIELDS if field not in payload]
    errors = []
    if missing:
        errors.append("missing_required_template_fields")
    errors.extend(_validate_status(payload))
    for flag in capture.NO_AUTHORITY_FLAGS:
        if payload.get(flag) is not True:
            errors.append(f"missing_or_false_no_authority_flag:{flag}")

    findings = _market_action_guidance_findings(payload)
    if findings:
        errors.append("market_action_guidance_detected")

    high_fields = schema.get(
        "fields_required_for_high_completeness",
        list(capture.FIELDS_REQUIRED_FOR_HIGH_COMPLETENESS),
    )
    status = payload.get("capture_status")
    empty_high_fields = [field for field in high_fields if _is_empty(payload.get(field))]
    if empty_high_fields and status not in {"not_started", "draft"}:
        errors.append("empty_high_completeness_fields_for_review_status")

    return {
        "market_id": market_id,
        "valid": not errors,
        "errors": errors,
        "missing_required_template_fields": missing,
        "market_action_guidance_findings": findings,
        "empty_required_for_high_completeness_fields": empty_high_fields,
        "capture_status": payload.get("capture_status"),
    }


def build_validation_report(root=ROOT):
    schema = _load_json(capture.SOURCE_PATHS["schema_json"], root=root)
    packet_results = []
    for path in _capture_paths(root=root):
        payload = _load_json(path, root=root)
        result = validate_capture_packet(payload, schema)
        result["path"] = capture._display_path(path, root=root)
        packet_results.append(result)

    invalid = [item for item in packet_results if not item["valid"]]
    missing_fields = [
        {
            "market_id": item["market_id"],
            "path": item["path"],
            "missing_required_template_fields": item["missing_required_template_fields"],
        }
        for item in packet_results
        if item["missing_required_template_fields"]
    ]
    guidance = [
        {
            "market_id": item["market_id"],
            "path": item["path"],
            "findings": item["market_action_guidance_findings"],
        }
        for item in packet_results
        if item["market_action_guidance_findings"]
    ]
    ready = [
        item["market_id"]
        for item in packet_results
        if item["capture_status"] in {"ready_for_local_review", "reviewed"}
    ]
    not_started = [
        item["market_id"] for item in packet_results if item["capture_status"] == "not_started"
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "capture_schema_version": schema.get("schema_version"),
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "manual_resolution_source_capture_validation_passed"
        if not invalid
        else "manual_resolution_source_capture_validation_failed",
        "total_packets_validated": len(packet_results),
        "valid_count": len(packet_results) - len(invalid),
        "invalid_count": len(invalid),
        "packets_missing_required_template_fields": missing_fields,
        "packets_with_market_action_guidance": guidance,
        "packets_ready_for_local_review": ready,
        "packets_not_started": not_started,
        "packet_results": packet_results,
        "safety_summary": {
            **capture.SAFETY_SUMMARY,
            "required_template_fields_checked": True,
            "no_authority_flags_checked": True,
            "market_action_guidance_checked": True,
            "high_completeness_status_gate_checked": True,
        },
    }


def render_validation_markdown(report):
    lines = [
        "# PMBOT Manual Resolution Source Capture Validation v1",
        "",
        f"- schema_version: {report['schema_version']}",
        f"- capture_schema_version: {report['capture_schema_version']}",
        f"- task_id: {report['task_id']}",
        f"- status: {report['status']}",
        f"- total_packets_validated: {report['total_packets_validated']}",
        f"- valid_count: {report['valid_count']}",
        f"- invalid_count: {report['invalid_count']}",
        f"- packets_ready_for_local_review: {len(report['packets_ready_for_local_review'])}",
        f"- packets_not_started: {len(report['packets_not_started'])}",
        "",
        "## Missing Required Template Fields",
        "",
    ]
    if report["packets_missing_required_template_fields"]:
        for item in report["packets_missing_required_template_fields"]:
            lines.append(
                "- "
                f"{item['market_id']}: "
                + ", ".join(item["missing_required_template_fields"])
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Market Action Guidance Findings", ""])
    if report["packets_with_market_action_guidance"]:
        for item in report["packets_with_market_action_guidance"]:
            lines.append(f"- {item['market_id']}: {len(item['findings'])}")
    else:
        lines.append("- none")
    lines.extend(["", "## Packets Not Started", ""])
    lines.append("- " + ", ".join(report["packets_not_started"]))
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- openrouter_calls_performed: 0",
            "- polymarket_api_calls_performed: 0",
            "- external_network_calls_performed: 0",
            "- no_market_action_guidance: true",
            "- no_trading_authority: true",
            "- no_queue_authority: true",
            "- no_runtime_authority: true",
            "- no_wallet_or_order_authority: true",
            "",
        ]
    )
    return "\n".join(lines)


def write_validation_report(root=ROOT):
    report = build_validation_report(root=root)
    _write_json(VALIDATION_JSON, report, root=root)
    _write_text(VALIDATION_MD, render_validation_markdown(report), root=root)
    return {
        "task_id": TASK_ID,
        "status": report["status"],
        "files_written": [VALIDATION_JSON, VALIDATION_MD],
        "total_packets_validated": report["total_packets_validated"],
        "valid_count": report["valid_count"],
        "invalid_count": report["invalid_count"],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_validation_report(ROOT), indent=2, ensure_ascii=True))
        return 0
    report = build_validation_report(ROOT)
    if args.markdown:
        print(render_validation_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if report["invalid_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
