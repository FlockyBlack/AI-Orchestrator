import argparse
import json
from collections import Counter
from pathlib import Path

from pm_bot.llm import manual_resolution_source_capture as capture
from pm_bot.llm import manual_resolution_source_capture_validator as validator


TASK_ID = "PMBOT-SOURCE-004B-MANUAL-CAPTURE-OPERATOR-FILL-GUIDE"
CHECKLIST_VERSION = "manual_resolution_source_capture_operator_checklist.v1"
PROGRESS_VERSION = "manual_resolution_source_capture_progress.v1"
GENERATED_BY = "pm_bot/llm/manual_resolution_source_capture_operator_artifacts.py"

ROOT = Path(__file__).resolve().parents[2]

GUIDE_PATH = "docs/PMBOT_SOURCE_004B_MANUAL_CAPTURE_OPERATOR_FILL_GUIDE.md"
CHECKLIST_JSON = "pm_bot/llm/manual_resolution_source_capture_operator_checklist.v1.json"
CHECKLIST_MD = "pm_bot/llm/manual_resolution_source_capture_operator_checklist.v1.md"
PROGRESS_JSON = "pm_bot/llm/manual_resolution_source_capture_progress.v1.json"
PROGRESS_MD = "pm_bot/llm/manual_resolution_source_capture_progress.v1.md"
VALIDATION_COMMAND = (
    "python -m pm_bot.llm.manual_resolution_source_capture_validator --write"
)

REQUIRED_FIELDS_TO_FILL = tuple(capture.RECOMMENDED_OPERATOR_FILL_ORDER)
OPTIONAL_FIELDS_TO_FILL = (
    "jurisdiction",
    "candidate_or_party_if_applicable",
    "manual_operator_notes",
    "unresolved_source_questions",
    "source_capture_author_or_operator",
    "source_capture_timestamp_local",
)
NO_AUTHORITY_FLAGS = {
    **capture.NO_AUTHORITY_FLAGS,
    "passive_context_only": True,
    "no_dispatcher_authority": True,
    "acceptance_is_not_trading_approval": True,
}
SAFETY_DO_NOT_INCLUDE = (
    "no predictions",
    "no trading recommendations",
    "no probability",
    "no EV",
    "no edge",
    "no confidence score",
    "no side selection",
    "no buy/sell/hold/enter/exit",
)
READY_FOR_LOCAL_REVIEW_REQUIREMENTS = (
    "capture_status and source_capture_status are both ready_for_local_review",
    "full_market_resolution_criteria_text is filled from local operator review",
    "full_resolution_rules is filled from local operator review",
    "official_source_references has at least one manually verified item",
    "official_source_urls_or_rule_references has at least one manually verified item or rule reference",
    "source_timestamps records when the operator checked each source",
    "source_reliability_review states why the cited sources are suitable or what remains uncertain",
    "reviewed_local_evidence_references identifies local files or packet sections checked",
    "non_placeholder_evidence_notes contains substantive evidence notes or a clear missing-data note",
    "no-authority flags remain true",
    "validator passes with zero invalid templates",
)
REVIEWED_REQUIREMENTS = (
    "a separate local reviewer has inspected the ready_for_local_review template",
    "all ready_for_local_review requirements still hold",
    "manual_operator_notes records review-only acceptance or requested revision context",
    "reviewed status does not approve actions, queues, runtime behavior, wallets, orders, or market decisions",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Build local operator checklist and progress artifacts for manual source capture."
    )
    parser.add_argument("--write", action="store_true", help="Write checklist and progress artifacts.")
    parser.add_argument("--progress", action="store_true", help="Print progress JSON instead of checklist JSON.")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown instead of JSON.")
    return parser.parse_args(argv)


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        value = resolved.relative_to(Path(root).resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


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


def _packet_paths(root=ROOT):
    directory = _resolve(capture.SOURCE_PATHS["capture_dir"], root=root)
    return sorted(directory.glob("*_resolution_source_capture.v1.json"))


def _packet_payloads(root=ROOT):
    return [_load_json(path, root=root) for path in _packet_paths(root=root)]


def _packet_path_for_market(market_id):
    return (
        f"{capture.SOURCE_PATHS['capture_dir']}/"
        f"{market_id}_resolution_source_capture.v1.json"
    )


def _packet_markdown_path_for_market(market_id):
    return (
        f"{capture.SOURCE_PATHS['capture_dir']}/"
        f"{market_id}_resolution_source_capture.v1.md"
    )


def _validation_by_market(report):
    return {
        str(item.get("market_id")): item
        for item in report.get("packet_results", [])
        if item.get("market_id")
    }


def _operator_next_step(packet, validation_result):
    status = packet.get("capture_status")
    if validation_result and not validation_result.get("valid", False):
        return "Fix validator errors first, then rerun the local validator."
    if status == "not_started":
        return (
            "Open the JSON and Markdown template, fill the recommended fields from "
            "manual local review, then set both status fields to draft."
        )
    if status == "draft":
        return (
            "Finish required source fields; when ready, set both status fields to "
            "ready_for_local_review and rerun validation."
        )
    if status == "ready_for_local_review":
        return "Have a local reviewer inspect the filled evidence fields; this is review-only."
    if status == "reviewed":
        return "Keep as reviewed unless a later local reviewer requests revision."
    if status == "needs_revision":
        return "Address unresolved local source questions, then rerun validation."
    return "Set a valid capture_status and source_capture_status, then rerun validation."


def _per_field_checklist():
    return [
        {
            "field": "full_market_resolution_criteria_text",
            "priority": 1,
            "meaning": "The complete local text that defines how the market resolves.",
            "good_content": "Generic example: exact local rule text or a faithful operator summary with source note.",
            "bad_content": "A guess, prediction, paraphrase without source context, or placeholder.",
            "if_unknown": "Leave blank in not_started/draft and add the unresolved question.",
        },
        {
            "field": "full_resolution_rules",
            "priority": 2,
            "meaning": "All rule clauses needed to understand valid resolution conditions.",
            "good_content": "Generic example: local rule sections covering outcome definitions and tie/edge cases.",
            "bad_content": "Only a headline, short excerpt, unsupported inference, or market opinion.",
            "if_unknown": "Leave blank in not_started/draft and record which rule text is missing.",
        },
        {
            "field": "official_source_references",
            "priority": 3,
            "meaning": "Names of official sources or rule documents the operator manually checked.",
            "good_content": "Generic example: official rules document name, filing title, or source system label.",
            "bad_content": "Social posts, commentary, unverifiable claims, or invented references.",
            "if_unknown": "Use an unresolved_source_questions entry instead of inventing a reference.",
        },
        {
            "field": "official_source_urls_or_rule_references",
            "priority": 4,
            "meaning": "Local source URL strings or rule identifiers already known to the operator.",
            "good_content": "Generic example: manually verified URL or local rule reference identifier.",
            "bad_content": "Unvisited links, guessed URLs, search results, or stale placeholders.",
            "if_unknown": "Leave the array empty until the operator manually verifies a source.",
        },
        {
            "field": "source_timestamps",
            "priority": 5,
            "meaning": "When each source was checked or captured by the local operator.",
            "good_content": "Generic example: local timestamp plus which source or rule reference was checked.",
            "bad_content": "Missing timestamp, future timestamp, or timestamp copied from unrelated context.",
            "if_unknown": "Add the timestamp when the operator checks the source.",
        },
        {
            "field": "source_reliability_review",
            "priority": 6,
            "meaning": "Operator note on whether the cited sources are official and complete.",
            "good_content": "Generic example: source is official, complete, current, or has named gaps.",
            "bad_content": "Outcome speculation, certainty claims, or unsupported trust statements.",
            "if_unknown": "State that reliability remains unresolved and list the missing verification.",
        },
        {
            "field": "reviewed_local_evidence_references",
            "priority": 7,
            "meaning": "Local files, packet sections, or captured documents the operator reviewed.",
            "good_content": "Generic example: repo-relative file path and section label.",
            "bad_content": "External claims not present locally or broad notes like checked sources.",
            "if_unknown": "Leave empty until local evidence is actually reviewed.",
        },
        {
            "field": "non_placeholder_evidence_notes",
            "priority": 8,
            "meaning": "Substantive notes about what the local evidence contains or lacks.",
            "good_content": "Generic example: source confirms rule scope; one timestamp still missing.",
            "bad_content": "TODO, placeholder, prediction, recommendation, or market decision text.",
            "if_unknown": "Write a clear missing-data note in draft only after source review starts.",
        },
    ]


def build_operator_checklist(root=ROOT):
    manifest = _load_json(capture.SOURCE_PATHS["manifest_json"], root=root)
    validation = validator.build_validation_report(root=root)
    validation_by_market = _validation_by_market(validation)
    packets = _packet_payloads(root=root)
    market_entries = []
    for packet in packets:
        market_id = str(packet["market_id"])
        validation_result = validation_by_market.get(market_id, {})
        market_entries.append(
            {
                "market_id": market_id,
                "capture_json_path": _packet_path_for_market(market_id),
                "capture_markdown_path": _packet_markdown_path_for_market(market_id),
                "current_status": packet.get("capture_status"),
                "required_fields_to_fill": list(REQUIRED_FIELDS_TO_FILL),
                "optional_fields_to_fill": list(OPTIONAL_FIELDS_TO_FILL),
                "validation_status": "valid"
                if validation_result.get("valid")
                else "invalid",
                "operator_next_step": _operator_next_step(packet, validation_result),
                "no_market_action_guidance": True,
            }
        )

    return {
        "checklist_version": CHECKLIST_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "source_capture_schema_path": capture.SOURCE_PATHS["schema_json"],
        "capture_manifest_path": capture.SOURCE_PATHS["manifest_json"],
        "validation_report_path": validator.VALIDATION_JSON,
        "target_capture_directory": capture.SOURCE_PATHS["capture_dir"],
        "total_templates": manifest.get("total_capture_packets", len(market_entries)),
        "status_flow": list(capture.CAPTURE_STATUS_VALUES),
        "recommended_fill_order": list(capture.RECOMMENDED_OPERATOR_FILL_ORDER),
        "per_field_checklist": _per_field_checklist(),
        "per_market_checklist": market_entries,
        "validation_command": VALIDATION_COMMAND,
        "safety_do_not_include": list(SAFETY_DO_NOT_INCLUDE),
        "ready_for_local_review_requirements": list(READY_FOR_LOCAL_REVIEW_REQUIREMENTS),
        "reviewed_requirements": list(REVIEWED_REQUIREMENTS),
        "no_authority_flags": dict(NO_AUTHORITY_FLAGS),
        "operator_review_only": True,
        "passive_context_only": True,
        "no_trading_authority": True,
        "no_queue_authority": True,
        "no_runtime_authority": True,
        "no_dispatcher_authority": True,
        "no_wallet_or_order_authority": True,
        "acceptance_is_not_trading_approval": True,
        "no_market_action_guidance": True,
    }


def _field_counts(packets):
    filled = Counter()
    missing = Counter()
    for packet in packets:
        for field in capture.RECOMMENDED_OPERATOR_FILL_ORDER:
            if _is_empty(packet.get(field)):
                missing[field] += 1
            else:
                filled[field] += 1
    return (
        {field: filled[field] for field in capture.RECOMMENDED_OPERATOR_FILL_ORDER},
        {field: missing[field] for field in capture.RECOMMENDED_OPERATOR_FILL_ORDER},
    )


def build_capture_progress(root=ROOT):
    validation = validator.build_validation_report(root=root)
    packets = _packet_payloads(root=root)
    status_counts = Counter(packet.get("capture_status") for packet in packets)
    filled_counts, missing_counts = _field_counts(packets)
    markets_ready = [
        str(packet["market_id"])
        for packet in packets
        if packet.get("capture_status") == "ready_for_local_review"
    ]
    markets_needing_input = [
        str(packet["market_id"])
        for packet in packets
        if packet.get("capture_status") in {"not_started", "draft", "needs_revision"}
    ]
    next_fields = [
        field for field in capture.RECOMMENDED_OPERATOR_FILL_ORDER if missing_counts.get(field, 0)
    ]
    return {
        "schema_version": PROGRESS_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "total_templates": len(packets),
        "not_started_count": status_counts.get("not_started", 0),
        "draft_count": status_counts.get("draft", 0),
        "ready_for_local_review_count": status_counts.get("ready_for_local_review", 0),
        "reviewed_count": status_counts.get("reviewed", 0),
        "needs_revision_count": status_counts.get("needs_revision", 0),
        "valid_template_count": validation.get("valid_count", 0),
        "invalid_template_count": validation.get("invalid_count", 0),
        "fields_filled_counts": filled_counts,
        "fields_missing_counts": missing_counts,
        "next_fields_to_fill": next_fields,
        "markets_ready_for_local_review": markets_ready,
        "markets_needing_operator_input": markets_needing_input,
        "validation_command": VALIDATION_COMMAND,
        "recommended_operator_next_action": (
            "Open one not_started capture JSON and its Markdown companion, fill the "
            "recommended fields from manual local review, set both status fields to draft, "
            "then rerun validation."
        ),
        "safety_summary": {
            **capture.SAFETY_SUMMARY,
            "operator_review_only": True,
            "passive_context_only": True,
            "no_dispatcher_authority": True,
            "acceptance_is_not_trading_approval": True,
            "no_market_action_guidance": True,
        },
    }


def render_operator_checklist_markdown(checklist):
    lines = [
        "# PMBOT Manual Resolution Source Capture Operator Checklist v1",
        "",
        f"- checklist_version: {checklist['checklist_version']}",
        f"- task_id: {checklist['task_id']}",
        f"- source_capture_schema_path: {checklist['source_capture_schema_path']}",
        f"- capture_manifest_path: {checklist['capture_manifest_path']}",
        f"- validation_report_path: {checklist['validation_report_path']}",
        f"- target_capture_directory: {checklist['target_capture_directory']}",
        f"- total_templates: {checklist['total_templates']}",
        f"- validation_command: {checklist['validation_command']}",
        "",
        "## Status Flow",
        "",
    ]
    for status in checklist["status_flow"]:
        lines.append(f"- {status}")
    lines.extend(["", "## Recommended Fill Order", ""])
    for index, field in enumerate(checklist["recommended_fill_order"], start=1):
        lines.append(f"{index}. {field}")
    lines.extend(["", "## Field Checklist", ""])
    for item in checklist["per_field_checklist"]:
        lines.extend(
            [
                f"- {item['field']}",
                f"  priority: {item['priority']}",
                f"  meaning: {item['meaning']}",
                f"  good_content: {item['good_content']}",
                f"  bad_content: {item['bad_content']}",
                f"  if_unknown: {item['if_unknown']}",
            ]
        )
    lines.extend(["", "## Per Market Checklist", ""])
    for item in checklist["per_market_checklist"]:
        lines.extend(
            [
                f"- market_id: {item['market_id']}",
                f"  capture_json_path: {item['capture_json_path']}",
                f"  capture_markdown_path: {item['capture_markdown_path']}",
                f"  current_status: {item['current_status']}",
                f"  validation_status: {item['validation_status']}",
                f"  operator_next_step: {item['operator_next_step']}",
                f"  no_market_action_guidance: {str(item['no_market_action_guidance']).lower()}",
            ]
        )
    lines.extend(["", "## Safety Do Not Include", ""])
    for item in checklist["safety_do_not_include"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Ready For Local Review Requirements", ""])
    for item in checklist["ready_for_local_review_requirements"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Reviewed Requirements", ""])
    for item in checklist["reviewed_requirements"]:
        lines.append(f"- {item}")
    lines.extend(["", "## No Authority Flags", ""])
    for key in sorted(checklist["no_authority_flags"]):
        lines.append(f"- {key}: {str(checklist['no_authority_flags'][key]).lower()}")
    lines.append("")
    return "\n".join(lines)


def render_capture_progress_markdown(progress):
    lines = [
        "# PMBOT Manual Resolution Source Capture Progress v1",
        "",
        f"- schema_version: {progress['schema_version']}",
        f"- task_id: {progress['task_id']}",
        f"- total_templates: {progress['total_templates']}",
        f"- not_started_count: {progress['not_started_count']}",
        f"- draft_count: {progress['draft_count']}",
        f"- ready_for_local_review_count: {progress['ready_for_local_review_count']}",
        f"- reviewed_count: {progress['reviewed_count']}",
        f"- needs_revision_count: {progress['needs_revision_count']}",
        f"- valid_template_count: {progress['valid_template_count']}",
        f"- invalid_template_count: {progress['invalid_template_count']}",
        f"- validation_command: {progress['validation_command']}",
        "",
        "## Fields Filled Counts",
        "",
    ]
    for field, count in progress["fields_filled_counts"].items():
        lines.append(f"- {field}: {count}")
    lines.extend(["", "## Fields Missing Counts", ""])
    for field, count in progress["fields_missing_counts"].items():
        lines.append(f"- {field}: {count}")
    lines.extend(["", "## Next Fields To Fill", ""])
    for field in progress["next_fields_to_fill"]:
        lines.append(f"- {field}")
    lines.extend(["", "## Markets Ready For Local Review", ""])
    if progress["markets_ready_for_local_review"]:
        for market_id in progress["markets_ready_for_local_review"]:
            lines.append(f"- {market_id}")
    else:
        lines.append("- none")
    lines.extend(["", "## Markets Needing Operator Input", ""])
    for market_id in progress["markets_needing_operator_input"]:
        lines.append(f"- {market_id}")
    lines.extend(
        [
            "",
            "## Recommended Operator Next Action",
            "",
            f"- {progress['recommended_operator_next_action']}",
            "",
            "## Safety Summary",
            "",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no network calls",
            "- no trading",
            "- no wallet/orders",
            "- no runtime/dispatcher/background/browser/queue changes",
            "- no API key access",
            "- no market recommendations",
            "- no probability, EV, edge, confidence, or side selection",
            "",
        ]
    )
    return "\n".join(lines)


def write_operator_artifacts(root=ROOT):
    checklist = build_operator_checklist(root=root)
    progress = build_capture_progress(root=root)
    _write_json(CHECKLIST_JSON, checklist, root=root)
    _write_text(CHECKLIST_MD, render_operator_checklist_markdown(checklist), root=root)
    _write_json(PROGRESS_JSON, progress, root=root)
    _write_text(PROGRESS_MD, render_capture_progress_markdown(progress), root=root)
    return {
        "task_id": TASK_ID,
        "status": "manual_resolution_source_capture_operator_artifacts_written",
        "files_written": [CHECKLIST_JSON, CHECKLIST_MD, PROGRESS_JSON, PROGRESS_MD],
        "total_templates": checklist["total_templates"],
        "not_started_count": progress["not_started_count"],
        "ready_for_local_review_count": progress["ready_for_local_review_count"],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_operator_artifacts(ROOT), indent=2, ensure_ascii=True))
        return 0
    payload = build_capture_progress(ROOT) if args.progress else build_operator_checklist(ROOT)
    if args.markdown:
        text = (
            render_capture_progress_markdown(payload)
            if args.progress
            else render_operator_checklist_markdown(payload)
        )
        print(text, end="")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
