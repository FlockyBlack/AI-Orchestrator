import argparse
import json
import re
import sys
from json import JSONDecodeError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import export_manual_llm_review_queue as review_queue  # noqa: E402


TASK_ID = "PMBOT-LLM-015-MANUAL-PACKET-BATCH-EXPORT"
CONTRACT_VERSION = "manual_llm_packet_batch_manifest.v1"
PACKET_CONTRACT_VERSION = review_queue.BATCH_PACKET_CONTRACT_VERSION
PROMPT_CONTRACT_VERSION = "manual_llm_packet_batch_prompt.v1"
DETERMINISTIC_GENERATED_AT = "deterministic-manual-llm-packet-batch.v1"
GENERATED_BY = "pm_bot/llm/export_manual_llm_packet_batch.py"

DEFAULT_QUEUE_PATH = "pm_bot/llm/manual_llm_review_queue.v1.json"
DEFAULT_OUTPUT_DIR = "pm_bot/llm/manual_packet_batch"
DEFAULT_MANIFEST_JSON = "pm_bot/llm/manual_llm_packet_batch_manifest.v1.json"
DEFAULT_MANIFEST_MD = "pm_bot/llm/manual_llm_packet_batch_manifest.v1.md"
DEFAULT_EXPECTED_MANIFEST_JSON = "pm_bot/llm/expected_manual_llm_packet_batch_manifest.v1.json"
DEFAULT_DOC_MD = "docs/PMBOT_LLM_015_MANUAL_PACKET_BATCH_EXPORT.md"
DEFAULT_DOC_RESULT_JSON = "docs/PMBOT_LLM_015_RESULT.json"

EXPORTABLE_STATUSES = {
    review_queue.READY_FOR_PACKET_EXPORT,
    review_queue.WAITING_FOR_RESPONSE,
}

SAFETY_FLAGS = {
    "offline_only": True,
    "local_only": True,
    "manual_review_only": True,
    "not_truth_source": True,
    "not_trading_advice": True,
    "not_execution_authority": True,
    "no_recommendations": True,
    "no_outcome_estimates": True,
    "no_value_scoring": True,
    "no_trade_or_wallet_instructions": True,
    "no_side_selection": True,
    "no_market_decision": True,
    "no_external_data": True,
    "no_internet_news_api": True,
    "no_prompt_automation": True,
    "no_browser_automation": True,
    "no_llm_api_calls": True,
    "no_network_calls": True,
    "no_runtime_wiring": True,
    "no_credentials": True,
    "no_wallet_private_key_access": True,
    "deterministic": True,
}

PROMPT_RESTRICTIONS = (
    "No trading guidance.",
    "No market-action instruction verbs.",
    "Do not repeat restriction wording in output fields.",
    "Avoid market-action verbs in checklist, risk note, and research question text.",
    "Describe candidate participation changes with neutral wording such as candidacy status changes.",
    "Use corner cases or special cases for neutral exceptions; do not use value-boundary wording.",
    "No numerical likelihood estimates.",
    "No abbreviated value terms.",
    "No value metrics.",
    "No scoring or rating labels.",
    "No betting certainty labels.",
    "No outcome selection.",
    "No market decision.",
    "No truth inference.",
    "No order instructions.",
    "No wallet, private key, or credential handling.",
    "No external data.",
    "No internet, news, or API.",
    "Use only the supplied packet.",
    "Mark uncertainty and missing evidence clearly.",
    "Output analysis-only JSON.",
)

NEXT_SAFE_OPERATOR_ACTION = (
    "Open each local prompt manually, paste it into an external/manual LLM chat, "
    "then save the returned strict JSON to the local response path listed for that market."
)

BOUNDARY_NOTICE = (
    "Offline/manual review context only. These artifacts are not truth sources, not trading advice, "
    "and not execution authority."
)

_RESTRICTED_LITERAL_RE = re.compile(r"(?<![A-Za-z0-9])edge(?![A-Za-z0-9])", re.IGNORECASE)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export deterministic local/manual LLM packet and prompt artifacts for the PMBOT queue."
    )
    parser.add_argument("--queue", default=DEFAULT_QUEUE_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest-json", default=DEFAULT_MANIFEST_JSON)
    parser.add_argument("--manifest-md", default=DEFAULT_MANIFEST_MD)
    parser.add_argument("--expected-json", default=DEFAULT_EXPECTED_MANIFEST_JSON)
    parser.add_argument("--doc-md", default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-result-json", default=DEFAULT_DOC_RESULT_JSON)
    return parser.parse_args(argv)


def _resolve_path(path, root=ROOT):
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(root) / candidate


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(Path(root).resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _safe_list(value):
    return value if isinstance(value, list) else []


def _safe_string(value):
    if value is None:
        return ""
    return _sanitize_text(str(value).strip())


def _sanitize_text(text):
    return _RESTRICTED_LITERAL_RE.sub("value-boundary", str(text))


def _clip_text(value, max_chars=700):
    text = re.sub(r"\s+", " ", _safe_string(value)).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 16].rstrip() + " [truncated]"


def _first_text(payload, *keys):
    data = _safe_dict(payload)
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return _clip_text(value)
    return ""


def _string_list(value):
    items = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                items.append(_clip_text(item))
            elif isinstance(item, dict):
                compact = _compact_dict_text(item)
                if compact:
                    items.append(compact)
    elif isinstance(value, str) and value.strip():
        items.append(_clip_text(value))
    return items


def _compact_dict_text(value):
    data = _safe_dict(value)
    parts = []
    for key in sorted(data):
        item = data[key]
        if isinstance(item, (str, int, float, bool)) and not isinstance(item, bool):
            text = _safe_string(item)
            if text:
                parts.append(f"{_safe_string(key)}: {text}")
    return _clip_text("; ".join(parts), max_chars=700)


def _iter_dicts(value):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _iter_dicts(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_dicts(item)


def _find_market_record(payload, market_id):
    for item in _iter_dicts(payload):
        if str(item.get("market_id") or "") == str(market_id):
            return item
    return {}


def _artifact_load_status(path, root=ROOT):
    resolved = _resolve_path(path, root)
    status = {
        "path": _display_path(resolved, root),
        "present": resolved.exists(),
        "parse_status": "not_loaded",
        "error": "",
    }
    if not resolved.exists():
        status["parse_status"] = "missing"
        return None, status
    try:
        payload = _load_json(resolved)
    except JSONDecodeError as exc:
        status["parse_status"] = "parse_failed"
        status["error"] = f"JSONDecodeError:{exc.lineno}:{exc.colno}"
        return None, status
    except OSError as exc:
        status["parse_status"] = "read_failed"
        status["error"] = exc.__class__.__name__
        return None, status
    if not isinstance(payload, dict):
        status["parse_status"] = "top_level_not_object"
        return None, status
    status["parse_status"] = "parsed"
    return payload, status


def _packet_path_for_market(market_id, output_dir, root=ROOT):
    return _resolve_path(output_dir, root) / f"{market_id}_packet.v1.json"


def _prompt_path_for_market(market_id, output_dir, root=ROOT):
    return _resolve_path(output_dir, root) / f"{market_id}_prompt.v1.md"


def _response_path_for_market(market_id, output_dir, root=ROOT):
    return _resolve_path(output_dir, root) / f"{market_id}_response_operator.v1.json"


def _existing_batch_packet(item, output_dir, root=ROOT):
    market_id = str(item.get("market_id") or "")
    packet_path = _packet_path_for_market(market_id, output_dir, root)
    prompt_path = _prompt_path_for_market(market_id, output_dir, root)
    if not packet_path.exists() or not prompt_path.exists():
        return {}
    try:
        packet = _load_json(packet_path)
    except (OSError, JSONDecodeError):
        return {}
    if _safe_dict(packet).get("contract_version") != PACKET_CONTRACT_VERSION:
        return {}
    return packet


def _source_path_for_item(item, existing_packet):
    existing = _safe_dict(existing_packet)
    if existing.get("source_artifact_path"):
        return _safe_string(existing["source_artifact_path"])
    return _safe_string(item.get("source_artifact_path"))


def _candidate_source_type_for_item(item, existing_packet):
    existing = _safe_dict(existing_packet)
    if existing.get("candidate_source_type"):
        return _safe_string(existing["candidate_source_type"])
    return _safe_string(item.get("candidate_source_type") or item.get("candidate_source"))


def _source_notes_from_record(record):
    data = _safe_dict(record)
    notes = []
    source_fields = (
        ("evidence_summary_by_source", "local_evidence_summary"),
        ("evidence_slots", "local_evidence_slot"),
        ("official_sources_checked", "official_source_checked"),
        ("official_sources_to_check", "official_source_placeholder"),
        ("credible_news_sources_checked", "news_source_checked"),
        ("credible_news_sources_to_check", "news_source_placeholder"),
        ("source_plan", "source_plan"),
        ("source_ingest_artifacts", "source_ingest_artifact"),
    )
    for field, note_type in source_fields:
        for text in _string_list(data.get(field)):
            notes.append(
                {
                    "source_note_id": f"{note_type}_{len(notes) + 1:03d}",
                    "source_note_type": note_type,
                    "source_note": text,
                    "local_only": True,
                }
            )
    if notes:
        return notes
    return [
        {
            "source_note_id": "source_gap_001",
            "source_note_type": "source_gap",
            "source_note": "No structured local evidence/source placeholder was present in the source artifact.",
            "local_only": True,
        }
    ]


def _missing_evidence_from_record(record):
    data = _safe_dict(record)
    values = []
    for field in (
        "missing_information",
        "missing_information_review",
        "open_questions",
        "uncertainty_register",
        "operator_notes",
        "operator_review_notes",
        "human_review_notes",
    ):
        values.extend(_string_list(data.get(field)))
    if values:
        return values
    return ["No explicit local missing-evidence note was present in the source artifact."]


def _source_gap_notes_from_record(record):
    data = _safe_dict(record)
    values = []
    for field in (
        "official_sources_to_check",
        "credible_news_sources_to_check",
        "search_queries",
        "resolution_criteria_notes",
        "market_context_notes",
    ):
        values.extend(_string_list(data.get(field)))
    if values:
        return values
    return ["Operator must verify source coverage manually before using any response for review."]


def _market_context(record, market_id):
    title = _first_text(record, "title_question", "title", "question", "event_title")
    question = _first_text(record, "question", "title_question", "title", "event_title")
    resolution = _first_text(
        record,
        "resolution_criteria_summary",
        "resolution_criteria_notes",
        "public_resolution_context",
        "description",
    )
    if not title:
        title = f"Local market {market_id}"
    if not question:
        question = title
    if not resolution:
        resolution = "No local resolution or description snippet was present in the source artifact."
    return {
        "market_id": str(market_id),
        "local_title_or_question": title,
        "local_question": question,
        "local_resolution_or_description_snippet": resolution,
        "market_status": "unknown",
        "outcome_labels": ["Yes", "No"],
    }


def build_packet(item, source_payload, source_artifact_path, candidate_source_type, output_dir, root=ROOT):
    market_id = str(item["market_id"])
    record = _find_market_record(source_payload, market_id)
    context = _market_context(record, market_id)
    response_path = _response_path_for_market(market_id, output_dir, root)
    return {
        "contract_version": PACKET_CONTRACT_VERSION,
        "packet_id": f"llm-analysis-packet-manual-batch-{market_id}",
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "market_id": market_id,
        "source_artifact_path": source_artifact_path,
        "candidate_source_type": candidate_source_type,
        "source_artifacts": [
            {
                "artifact_type": candidate_source_type,
                "path": source_artifact_path,
                "description": "Existing local PMBOT artifact copied into a manual review packet.",
                "sanitization_status": "safe_public_or_local_artifact_reference_only",
            }
        ],
        "market_context": {
            "market_id": market_id,
            "market_title": context["local_title_or_question"],
            "market_status": context["market_status"],
            "public_resolution_context": context["local_resolution_or_description_snippet"],
            "outcome_labels": context["outcome_labels"],
        },
        "local_review_context": context,
        "evidence_source_placeholders": _source_notes_from_record(record),
        "missing_evidence": _missing_evidence_from_record(record),
        "source_gap_notes": _source_gap_notes_from_record(record),
        "response_schema_path": _display_path(review_queue.validator.RESPONSE_SCHEMA_PATH, root),
        "expected_response_path": _display_path(response_path, root),
        "safety_boundaries": dict(SAFETY_FLAGS),
    }


def _json_block(payload):
    return json.dumps(_sanitize_generated_payload(payload), indent=2, ensure_ascii=True, sort_keys=True)


def _sanitize_generated_payload(value):
    if isinstance(value, dict):
        return {_sanitize_text(key): _sanitize_generated_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_generated_payload(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def render_prompt(packet, root=ROOT):
    response_schema = _load_json(review_queue.validator.RESPONSE_SCHEMA_PATH)
    market_id = packet["market_id"]
    response_id = f"llm-analysis-response-manual-batch-{market_id}"
    restriction_lines = "\n".join(f"- {item}" for item in PROMPT_RESTRICTIONS)
    lines = [
        "# PMBOT Manual LLM Packet Batch Prompt v1",
        "",
        "## Boundary",
        BOUNDARY_NOTICE,
        "",
        "PMBOT has not called an LLM, API, browser, or external data source. A human operator may paste this prompt manually.",
        "",
        "## Output Contract",
        "Return only strict JSON compatible with `llm_analysis_response_schema.v1.json`.",
        "Return exactly one raw JSON object.",
        "The first character must be `{` and the last character must be `}`.",
        "Do not wrap the JSON in Markdown. Do not use ```json fences or any other code fences.",
        "Do not include prose before or after the JSON object. Any Markdown fencing makes the response invalid.",
        f"Use packet_id `{packet['packet_id']}`.",
        f"Use response_id `{response_id}`.",
        "Use contract_version `llm_analysis_response.v1`.",
        "",
        "## Restrictions",
        restriction_lines,
        "",
        "## Required Response Sections",
    ]
    for section in review_queue.validator.ALLOWED_RESPONSE_SECTIONS:
        lines.append(f"- {section}")
    lines.extend(
        [
            "",
            "## Response Schema",
            "```json",
            _json_block(response_schema),
            "```",
            "",
            "## Supplied Packet",
            "Use only this packet. Treat all gaps as unresolved unless the packet states otherwise.",
            "",
            "```json",
            _json_block(packet),
            "```",
            "",
            "## Final Instruction",
            (
                "Return one analysis-only JSON object that validates against the response schema. "
                "Acceptance is operator-review readiness only, never trading approval."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _queue_item_is_exportable(item, output_dir, root=ROOT):
    status = item.get("review_queue_status")
    if status == review_queue.READY_FOR_PACKET_EXPORT:
        return True
    if status != review_queue.WAITING_FOR_RESPONSE:
        return False
    existing = _existing_batch_packet(item, output_dir, root)
    return bool(existing)


def _skip_item(item, reason, detail=""):
    return {
        "market_id": _safe_string(item.get("market_id")),
        "candidate_source_type": _safe_string(item.get("candidate_source_type") or item.get("candidate_source")),
        "source_artifact_path": _safe_string(item.get("source_artifact_path")),
        "reason": reason,
        "detail": detail,
    }


def _export_item(item, output_dir, root=ROOT):
    market_id = str(item["market_id"])
    existing_packet = _existing_batch_packet(item, output_dir, root)
    source_artifact_path = _source_path_for_item(item, existing_packet)
    candidate_source_type = _candidate_source_type_for_item(item, existing_packet)
    source_payload, source_status = _artifact_load_status(source_artifact_path, root)
    if source_status["parse_status"] != "parsed":
        return None, _skip_item(item, f"source_artifact_{source_status['parse_status']}", source_status["path"])
    record = _find_market_record(source_payload, market_id)
    if not record:
        return None, _skip_item(item, "market_id_not_found_in_source_artifact", source_artifact_path)

    packet = _sanitize_generated_payload(
        build_packet(item, source_payload, source_artifact_path, candidate_source_type, output_dir, root)
    )
    packet_path = _packet_path_for_market(market_id, output_dir, root)
    prompt_path = _prompt_path_for_market(market_id, output_dir, root)
    prompt = _sanitize_text(render_prompt(packet, root=root))
    _write_json(packet_path, packet)
    _write_text(prompt_path, prompt)
    return {
        "market_id": market_id,
        "packet_path": _display_path(packet_path, root),
        "prompt_path": _display_path(prompt_path, root),
        "expected_response_path": _display_path(_response_path_for_market(market_id, output_dir, root), root),
        "queue_status_after_export": review_queue.WAITING_FOR_RESPONSE,
    }, None


def _queue_status_counts(items):
    return {
        status: sum(1 for item in items if item.get("review_queue_status") == status)
        for status in review_queue.QUEUE_STATUSES
    }


def _write_queue_outputs(root=ROOT):
    queue = review_queue.build_manual_llm_review_queue(root=root)
    queue_json = _resolve_path(review_queue.DEFAULT_OUT_JSON, root)
    queue_md = _resolve_path(review_queue.DEFAULT_OUT_MD, root)
    expected_queue_json = _resolve_path(review_queue.DEFAULT_EXPECTED_JSON, root)
    doc_result_json = _resolve_path(review_queue.DEFAULT_DOC_RESULT_JSON, root)
    doc_md = _resolve_path(review_queue.DEFAULT_DOC_MD, root)
    markdown = review_queue.render_markdown(queue)
    _write_json(queue_json, queue)
    _write_text(queue_md, markdown)
    _write_json(expected_queue_json, queue)
    _write_json(doc_result_json, review_queue.build_doc_result(queue))
    _write_text(doc_md, markdown)
    return queue


def build_manifest(source_queue, exported, skipped, source_queue_path, output_dir, queue_after, root=ROOT):
    exported_market_ids = [item["market_id"] for item in exported]
    considered_count = len(exported) + len(skipped)
    return {
        "contract_version": CONTRACT_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "source_queue_path": _display_path(_resolve_path(source_queue_path, root), root),
        "output_dir": _display_path(_resolve_path(output_dir, root), root),
        "queue_items_total": int(source_queue.get("queue_items_total") or 0),
        "candidates_considered_count": considered_count,
        "exported_count": len(exported),
        "skipped_count": len(skipped),
        "exported_market_ids": exported_market_ids,
        "skipped_items": skipped,
        "per_market_artifacts": exported,
        "queue_status_counts_after_export": _queue_status_counts(_safe_list(queue_after.get("items"))),
        "safety_flags": dict(SAFETY_FLAGS),
        "next_safe_operator_action": NEXT_SAFE_OPERATOR_ACTION,
    }


def render_manifest_markdown(manifest):
    lines = [
        "# PMBOT Manual LLM Packet Batch Export v1",
        "",
        f"- task_id: {manifest['task_id']}",
        f"- total candidates considered: {manifest['candidates_considered_count']}",
        f"- exported count: {manifest['exported_count']}",
        f"- skipped count: {manifest['skipped_count']}",
        f"- source queue: {manifest['source_queue_path']}",
        f"- output directory: {manifest['output_dir']}",
        "",
        "## Exported Markets",
        "",
    ]
    if manifest["per_market_artifacts"]:
        for item in manifest["per_market_artifacts"]:
            lines.extend(
                [
                    f"- market_id: {item['market_id']}",
                    f"  packet_path: {item['packet_path']}",
                    f"  prompt_path: {item['prompt_path']}",
                    f"  expected_response_path: {item['expected_response_path']}",
                    f"  queue_status_after_export: {item['queue_status_after_export']}",
                ]
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Skipped Items", ""])
    if manifest["skipped_items"]:
        for item in manifest["skipped_items"]:
            lines.append(f"- market_id: {item['market_id']} reason: {item['reason']}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Manual Step",
            "",
            (
                "Operator manually opens each prompt, pastes it into an external/manual LLM chat, "
                "and saves the returned strict JSON response into the expected local response path."
            ),
            "",
            "## Boundary",
            "",
            BOUNDARY_NOTICE,
            "",
        ]
    )
    return "\n".join(lines)


def build_doc_result(manifest):
    status = "completed_ready_for_review" if not manifest["skipped_items"] else "completed_with_skips"
    return {
        "task_id": TASK_ID,
        "status": status,
        "manifest_json": DEFAULT_MANIFEST_JSON,
        "manifest_markdown": DEFAULT_MANIFEST_MD,
        "expected_manifest_json": DEFAULT_EXPECTED_MANIFEST_JSON,
        "doc_markdown": DEFAULT_DOC_MD,
        "exported_count": manifest["exported_count"],
        "skipped_count": manifest["skipped_count"],
        "exported_market_ids": manifest["exported_market_ids"],
        "queue_items_total": manifest["queue_items_total"],
        "queue_status_counts_after_export": manifest["queue_status_counts_after_export"],
        "warnings": [],
        "blockers": manifest["skipped_items"],
        "safety_flags": dict(SAFETY_FLAGS),
        "network_calls": 0,
        "llm_api_calls": 0,
        "browser_automation": False,
        "prompt_automation": False,
        "runtime_wiring": False,
        "truth_inference": False,
        "next_recommended_task": "Manual operator response collection for exported prompts.",
    }


def export_manual_llm_packet_batch(
    root=ROOT,
    queue_path=DEFAULT_QUEUE_PATH,
    output_dir=DEFAULT_OUTPUT_DIR,
    manifest_json=DEFAULT_MANIFEST_JSON,
    manifest_md=DEFAULT_MANIFEST_MD,
    expected_json=DEFAULT_EXPECTED_MANIFEST_JSON,
    doc_md=DEFAULT_DOC_MD,
    doc_result_json=DEFAULT_DOC_RESULT_JSON,
):
    source_queue = _load_json(_resolve_path(queue_path, root))
    items = [
        item
        for item in _safe_list(source_queue.get("items"))
        if isinstance(item, dict) and _queue_item_is_exportable(item, output_dir, root)
    ]
    exported = []
    skipped = []
    for item in sorted(items, key=lambda value: str(value.get("market_id") or "")):
        artifact, skip = _export_item(item, output_dir, root)
        if artifact is not None:
            exported.append(artifact)
        if skip is not None:
            skipped.append(skip)

    queue_after = _write_queue_outputs(root)
    manifest = build_manifest(source_queue, exported, skipped, queue_path, output_dir, queue_after, root)
    manifest = _sanitize_generated_payload(manifest)
    markdown = _sanitize_text(render_manifest_markdown(manifest))
    doc_result = _sanitize_generated_payload(build_doc_result(manifest))

    _write_json(_resolve_path(manifest_json, root), manifest)
    _write_text(_resolve_path(manifest_md, root), markdown)
    _write_json(_resolve_path(expected_json, root), manifest)
    _write_text(_resolve_path(doc_md, root), markdown)
    _write_json(_resolve_path(doc_result_json, root), doc_result)
    return manifest


def main(argv):
    args = _parse_args(argv)
    manifest = export_manual_llm_packet_batch(
        queue_path=args.queue,
        output_dir=args.output_dir,
        manifest_json=args.manifest_json,
        manifest_md=args.manifest_md,
        expected_json=args.expected_json,
        doc_md=args.doc_md,
        doc_result_json=args.doc_result_json,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=True))
    return 0 if not manifest["skipped_items"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
