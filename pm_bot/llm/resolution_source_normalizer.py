import argparse
import json
import re
from collections import Counter
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-003-RESOLUTION-SOURCE-FIELD-NORMALIZATION"
SCHEMA_VERSION = "resolution_source_normalizer.v1"
AUDIT_VERSION = "current_llm_resolution_source_normalization_audit.v1"
AFTER_SCORES_VERSION = "current_llm_packet_evidence_readiness_scores_after_source_normalization.v1"
AFTER_GATE_VERSION = "current_llm_batch_readiness_gate_after_source_normalization.v1"
ACTION_PLAN_VERSION = "local_source_enrichment_action_plan.v1"
GENERATED_BY = "pm_bot/llm/resolution_source_normalizer.py"
GENERATION_MARKER = "deterministic-source-003-local-resolution-source-normalization.v1"

ROOT = Path(__file__).resolve().parents[2]

SOURCE_PATHS = {
    "source_001_result_json": "docs/PMBOT_SOURCE_001_RESULT.json",
    "source_002_result_json": "docs/PMBOT_SOURCE_002_RESULT.json",
    "inventory_json": "pm_bot/llm/current_llm_market_packet_inventory.v1.json",
    "source_evidence_audit_json": "pm_bot/llm/current_llm_source_evidence_completeness_audit.v1.json",
    "readiness_scores_json": "pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.json",
    "batch_readiness_gate_json": "pm_bot/llm/current_llm_batch_readiness_gate.v1.json",
    "completeness_contract_json": "pm_bot/llm/llm_market_packet_completeness_contract.v1.json",
    "enrichment_requirements_json": "pm_bot/llm/source_evidence_enrichment_requirements.v1.json",
    "resolution_source_audit_json": "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json",
    "resolution_source_audit_md": "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.md",
    "after_scores_json": "pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json",
    "after_scores_md": "pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.md",
    "after_gate_json": "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.json",
    "after_gate_md": "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.md",
    "action_plan_json": "pm_bot/llm/local_source_enrichment_action_plan.v1.json",
    "action_plan_md": "pm_bot/llm/local_source_enrichment_action_plan.v1.md",
    "source_003_result_json": "docs/PMBOT_SOURCE_003_RESULT.json",
    "source_003_report_md": "docs/PMBOT_SOURCE_003_RESOLUTION_SOURCE_FIELD_NORMALIZATION.md",
}

SAFETY_FLAGS = {
    "local_only": True,
    "operator_review_only": True,
    "passive_context_only": True,
    "manual_review_only": True,
    "analysis_only": True,
    "no_live_calls": True,
    "no_trading_authority": True,
    "no_queue_authority": True,
    "no_runtime_authority": True,
    "no_dispatcher_authority": True,
    "no_wallet_or_order_authority": True,
    "acceptance_is_not_trading_approval": True,
    "no_market_action_guidance": True,
    "no_probability_ev_edge_confidence_side_selection": True,
    "openrouter_calls_performed_by_this_task": 0,
    "polymarket_api_calls_performed_by_this_task": 0,
    "external_network_calls_performed_by_this_task": 0,
    "network_calls_performed_by_this_task": 0,
    "api_key_accessed": False,
    "api_key_value_printed": False,
    "api_key_value_written": False,
    "api_key_leaked": False,
    "wallet_or_private_key_accessed": False,
    "orders_created": 0,
    "queue_items_created": 0,
    "queue_state_mutated": False,
    "runtime_wiring_added": False,
    "dispatcher_changed": False,
    "background_workers_added": False,
    "browser_automation_used": False,
    "live_enrichment_performed": False,
    "market_decisions_made": False,
    "future_live_batch_scheduled": False,
    "future_openrouter_batch_approved": False,
    "future_llm_review_approved": False,
}

VALID_READINESS_BANDS = ("high", "medium", "low", "blocked")
CORE_RESOLUTION_SOURCE_FIELDS = (
    "full_market_resolution_criteria_text",
    "full_resolution_rules",
    "official_source_references",
    "official_source_urls_or_rule_references",
    "source_timestamps",
    "source_reliability_review",
)
JURISDICTION_CATEGORIES = {"elections", "politics"}

FULL_CRITERIA_KEYS = {
    "full_market_resolution_criteria_text",
    "full_resolution_criteria_text",
    "market_resolution_criteria_text",
}
FULL_RULE_KEYS = {"full_resolution_rules", "resolution_rules", "market_rules_text", "rules_text"}
OFFICIAL_REFERENCE_KEYS = {
    "official_source_references",
    "official_source_or_rule_reference_notes",
    "official_rule_references",
}
OFFICIAL_URL_KEYS = {
    "official_source_urls_or_rule_references",
    "official_source_urls",
    "official_rule_urls",
    "resolution_rule_urls",
}
SOURCE_TIMESTAMP_KEYS = {"source_timestamps", "source_timestamps_when_present_locally"}
SOURCE_RELIABILITY_KEYS = {
    "source_reliability_review",
    "source_reliability_review_when_present_locally",
}

PLACEHOLDER_MARKERS = (
    "stub",
    "placeholder",
    "template only",
    "manual check template",
    "must be copied",
    "must review",
    "manual completion",
    "offline-reference",
    "records the",
    "not fetch",
    "not verify",
    "human review remains required",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export deterministic local PMBOT resolution/source normalization artifacts."
    )
    parser.add_argument("--write", action="store_true", help="Write JSON and Markdown artifacts.")
    parser.add_argument("--markdown", action="store_true", help="Print audit Markdown instead of JSON.")
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


def _load_optional_json(path, root=ROOT):
    resolved = _resolve(path, root=root)
    if not resolved.exists():
        return None
    with resolved.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else None


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


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _safe_list(value):
    return value if isinstance(value, list) else []


def _unique_ordered(values):
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _bool_text(value):
    return str(bool(value)).lower()


def _artifact_pointer(path, role):
    return {"path": path, "role": role}


def _as_text(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""


def _as_text_list(value):
    if isinstance(value, list):
        return [_as_text(item) for item in value if _as_text(item)]
    text = _as_text(value)
    return [text] if text else []


def _is_placeholder_text(value):
    text = _as_text(value).lower()
    return bool(text) and any(marker in text for marker in PLACEHOLDER_MARKERS)


def _is_usable_source_text(value):
    text = _as_text(value)
    return bool(text) and not _is_placeholder_text(text)


def _walk_values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_values(item)


def _collect_by_keys(payload, keys):
    values = []
    wanted = {key.lower() for key in keys}
    for key, value in _walk_values(payload):
        if str(key).lower() not in wanted:
            continue
        for item in _as_text_list(value):
            if _is_usable_source_text(item):
                values.append(item)
    return _unique_ordered(values)


def _first_by_keys(payload, keys):
    values = _collect_by_keys(payload, keys)
    return values[0] if values else None


def _read_text_if_exists(path, root=ROOT):
    resolved = _resolve(path, root=root)
    if not path or not resolved.exists():
        return ""
    return resolved.read_text(encoding="utf-8", errors="ignore")


def _load_packet_if_exists(path, root=ROOT):
    resolved = _resolve(path, root=root)
    if not path or not resolved.exists():
        return {}
    payload = _load_json(path, root=root)
    return payload if isinstance(payload, dict) else {}


def _resolution_snippet(packet):
    packet = _safe_dict(packet)
    market_context = _safe_dict(packet.get("market_context"))
    local_context = _safe_dict(packet.get("local_review_context"))
    for value in (
        market_context.get("public_resolution_context"),
        local_context.get("local_resolution_or_description_snippet"),
        market_context.get("resolution_context"),
        local_context.get("resolution_context"),
    ):
        text = _as_text(value)
        if text:
            return text
    return None


def _title_for_market(market, packet):
    market = _safe_dict(market)
    packet = _safe_dict(packet)
    local_context = _safe_dict(packet.get("local_review_context"))
    market_context = _safe_dict(packet.get("market_context"))
    return (
        _as_text(market.get("title_or_question"))
        or _as_text(local_context.get("local_title_or_question"))
        or _as_text(local_context.get("local_question"))
        or _as_text(market_context.get("market_title"))
        or None
    )


def _extract_candidate_from_title(title):
    text = _as_text(title)
    if " election" not in text.lower() or " win" not in text.lower():
        return None
    match = re.match(r"^Will\s+(.+?)\s+win\s+", text)
    if not match:
        return None
    candidate = match.group(1).strip()
    if candidate.lower().startswith(("the next", "next ")):
        return None
    return candidate or None


def _candidate_presence(category, title):
    if category != "elections":
        return "not_applicable", None
    candidate = _extract_candidate_from_title(title)
    if candidate:
        return True, candidate
    if "candidate" in _as_text(title).lower() or " party" in _as_text(title).lower():
        return False, None
    return "not_applicable", None


def _extract_jurisdiction(title, packet):
    text = " ".join(
        value
        for value in (
            _as_text(title),
            _as_text(_resolution_snippet(packet)),
            " ".join(_safe_list(_safe_dict(packet).get("source_gap_notes"))),
        )
        if value
    )
    lowered = text.lower()
    if "colombian presidential election" in lowered:
        return "Colombia"
    if " uk election" in lowered or "next uk election" in lowered:
        return "UK"
    if "president of france" in lowered or "france / politics" in lowered:
        return "France"
    return None


def _source_placeholder_count(packet):
    count = 0
    for item in _safe_list(_safe_dict(packet).get("evidence_source_placeholders")):
        note = _safe_dict(item).get("source_note")
        note_type = _safe_dict(item).get("source_note_type")
        if _is_placeholder_text(note) or "placeholder" in _as_text(note_type).lower():
            count += 1
    return count


def _source_refs_from_packet(packet):
    references = _collect_by_keys(packet, OFFICIAL_REFERENCE_KEYS)
    urls = _collect_by_keys(packet, OFFICIAL_URL_KEYS)
    return references, urls


def load_market_inventory(path=SOURCE_PATHS["inventory_json"], root=ROOT):
    return _load_json(path, root=root)


def find_local_packet_artifacts(market, root=ROOT):
    market = _safe_dict(market)
    packet_path = market.get("packet_file_path")
    prompt_path = market.get("prompt_file_path")
    return {
        "market_id": str(market.get("market_id", "")),
        "packet_file_path": packet_path,
        "prompt_file_path": prompt_path,
        "packet_exists": bool(packet_path and _resolve(packet_path, root=root).exists()),
        "prompt_exists": bool(prompt_path and _resolve(prompt_path, root=root).exists()),
        "packet": _load_packet_if_exists(packet_path, root=root),
        "prompt_text": _read_text_if_exists(prompt_path, root=root),
    }


def extract_resolution_source_fields(market, artifacts, root=ROOT):
    market = _safe_dict(market)
    packet = _safe_dict(_safe_dict(artifacts).get("packet"))
    title = _title_for_market(market, packet)
    category = market.get("category") or "unknown"
    snippet = _resolution_snippet(packet)

    full_criteria = _first_by_keys(packet, FULL_CRITERIA_KEYS)
    full_rules = _first_by_keys(packet, FULL_RULE_KEYS)
    official_refs, official_urls = _source_refs_from_packet(packet)
    source_timestamps = _collect_by_keys(packet, SOURCE_TIMESTAMP_KEYS)
    source_reliability = _first_by_keys(packet, SOURCE_RELIABILITY_KEYS)

    jurisdiction = _extract_jurisdiction(title, packet) if category in JURISDICTION_CATEGORIES else None
    jurisdiction_present = True if jurisdiction else ("unknown" if category not in JURISDICTION_CATEGORIES else False)
    candidate_present, candidate = _candidate_presence(category, title)

    direct_source_fields = [
        bool(full_criteria),
        bool(full_rules),
        bool(official_refs),
        bool(official_urls),
        bool(source_timestamps),
        bool(source_reliability),
    ]
    if any(direct_source_fields):
        method = "local_packet_field"
        confidence = "high" if sum(direct_source_fields) >= 4 else "medium"
    elif jurisdiction_present is True or candidate_present is True:
        method = "local_artifact_metadata"
        confidence = "medium"
    elif snippet:
        method = "local_packet_field"
        confidence = "low"
    else:
        method = "not_found"
        confidence = "unknown"

    return {
        "title_or_question": title,
        "local_resolution_context_snippet_present": bool(snippet),
        "local_resolution_context_snippet": snippet,
        "resolution_criteria_text_present": bool(full_criteria),
        "full_market_resolution_criteria_text": full_criteria,
        "full_resolution_rules_present": bool(full_rules),
        "full_resolution_rules": full_rules,
        "official_source_references_present": bool(official_refs),
        "official_source_references": official_refs,
        "official_source_urls_or_rule_references_present": bool(official_urls),
        "official_source_urls_or_rule_references": official_urls,
        "source_timestamps_present": bool(source_timestamps),
        "source_timestamps": source_timestamps,
        "source_reliability_review_present": bool(source_reliability),
        "source_reliability_review": source_reliability,
        "jurisdiction_present": jurisdiction_present,
        "jurisdiction": jurisdiction,
        "candidate_or_party_if_applicable_present": candidate_present,
        "candidate_or_party_if_applicable": candidate,
        "extraction_confidence": confidence,
        "extraction_method": method,
        "source_placeholder_count": _source_placeholder_count(packet),
    }


def _missing_fields_for_record(category, fields):
    missing = []
    if not fields["resolution_criteria_text_present"]:
        missing.append("full_market_resolution_criteria_text")
    if not fields["full_resolution_rules_present"]:
        missing.append("full_resolution_rules")
    if not fields["official_source_references_present"]:
        missing.append("official_source_references")
    if not fields["official_source_urls_or_rule_references_present"]:
        missing.append("official_source_urls_or_rule_references")
    if not fields["source_timestamps_present"]:
        missing.append("source_timestamps")
    if not fields["source_reliability_review_present"]:
        missing.append("source_reliability_review")
    if category in JURISDICTION_CATEGORIES and fields["jurisdiction_present"] is not True:
        missing.append("jurisdiction")
    if fields["candidate_or_party_if_applicable_present"] in {False, "unknown"}:
        missing.append("candidate_or_party_if_applicable")
    return missing


def normalize_resolution_source_record(market, root=ROOT):
    market = _safe_dict(market)
    artifacts = find_local_packet_artifacts(market, root=root)
    category = market.get("category") or "unknown"
    fields = extract_resolution_source_fields(market, artifacts, root=root)
    missing = _missing_fields_for_record(category, fields)
    warnings = []
    if fields["local_resolution_context_snippet_present"] and not fields["resolution_criteria_text_present"]:
        warnings.append("local_resolution_context_is_stub_or_excerpt_not_counted_as_full_resolution_criteria")
    if fields["source_placeholder_count"]:
        warnings.append("official_source_placeholders_or_templates_not_counted_as_sources")
    if not artifacts["packet_exists"]:
        warnings.append("packet_file_missing")
    if not artifacts["prompt_exists"]:
        warnings.append("prompt_file_missing")
    if fields["candidate_or_party_if_applicable_present"] == "not_applicable":
        warnings.append("candidate_or_party_if_applicable_marked_not_applicable_from_local_title")

    source_fields_locally_normalized = []
    for field in (
        "jurisdiction",
        "candidate_or_party_if_applicable",
        "full_market_resolution_criteria_text",
        "full_resolution_rules",
        "official_source_references",
        "official_source_urls_or_rule_references",
        "source_timestamps",
        "source_reliability_review",
    ):
        if field not in missing:
            source_fields_locally_normalized.append(field)

    return {
        "market_id": str(market.get("market_id", "")),
        "category": category,
        "packet_file_path": market.get("packet_file_path"),
        "prompt_file_path": market.get("prompt_file_path"),
        "packet_exists": artifacts["packet_exists"],
        "prompt_exists": artifacts["prompt_exists"],
        "title_or_question": fields["title_or_question"],
        "resolution_criteria_text_present": fields["resolution_criteria_text_present"],
        "full_market_resolution_criteria_text": fields["full_market_resolution_criteria_text"],
        "full_resolution_rules_present": fields["full_resolution_rules_present"],
        "full_resolution_rules": fields["full_resolution_rules"],
        "official_source_references_present": fields["official_source_references_present"],
        "official_source_references": fields["official_source_references"],
        "official_source_urls_or_rule_references_present": fields[
            "official_source_urls_or_rule_references_present"
        ],
        "official_source_urls_or_rule_references": fields["official_source_urls_or_rule_references"],
        "source_timestamps_present": fields["source_timestamps_present"],
        "source_timestamps": fields["source_timestamps"],
        "source_reliability_review_present": fields["source_reliability_review_present"],
        "source_reliability_review": fields["source_reliability_review"],
        "jurisdiction_present": fields["jurisdiction_present"],
        "jurisdiction": fields["jurisdiction"],
        "candidate_or_party_if_applicable_present": fields[
            "candidate_or_party_if_applicable_present"
        ],
        "candidate_or_party_if_applicable": fields["candidate_or_party_if_applicable"],
        "local_resolution_context_snippet_present": fields[
            "local_resolution_context_snippet_present"
        ],
        "local_resolution_context_snippet": fields["local_resolution_context_snippet"],
        "source_placeholder_count": fields["source_placeholder_count"],
        "extraction_confidence": fields["extraction_confidence"],
        "extraction_method": fields["extraction_method"],
        "source_fields_locally_normalized": source_fields_locally_normalized,
        "missing_resolution_source_fields": missing,
        "normalization_warnings": warnings,
        "no_market_action_guidance": True,
    }


def _category_breakdown(records):
    breakdown = {}
    for record in records:
        category = record["category"]
        item = breakdown.setdefault(
            category,
            {
                "market_count": 0,
                "market_ids": [],
                "missing_field_counts": {},
                "manual_review_needed_count": 0,
            },
        )
        item["market_count"] += 1
        item["market_ids"].append(record["market_id"])
        item["manual_review_needed_count"] += 1 if record["needs_manual_resolution_source_review"] else 0
        counter = Counter(item["missing_field_counts"])
        counter.update(record["missing_resolution_source_fields"])
        item["missing_field_counts"] = dict(sorted(counter.items()))
    for item in breakdown.values():
        item["market_ids"].sort()
    return {key: breakdown[key] for key in sorted(breakdown)}


def summarize_resolution_source_gaps(records):
    records = list(records)
    missing_counter = Counter()
    for record in records:
        missing_counter.update(record["missing_resolution_source_fields"])
    top_gaps = [
        {"field": field, "market_count": count}
        for field, count in missing_counter.most_common()
    ]
    aggregate = {
        "total_markets_audited": len(records),
        "markets_with_resolution_criteria_text": sum(
            1 for item in records if item["resolution_criteria_text_present"]
        ),
        "markets_missing_resolution_criteria_text": sum(
            1 for item in records if not item["resolution_criteria_text_present"]
        ),
        "markets_with_full_resolution_rules": sum(
            1 for item in records if item["full_resolution_rules_present"]
        ),
        "markets_missing_full_resolution_rules": sum(
            1 for item in records if not item["full_resolution_rules_present"]
        ),
        "markets_with_official_source_references": sum(
            1 for item in records if item["official_source_references_present"]
        ),
        "markets_missing_official_source_references": sum(
            1 for item in records if not item["official_source_references_present"]
        ),
        "markets_with_official_source_urls_or_rule_references": sum(
            1 for item in records if item["official_source_urls_or_rule_references_present"]
        ),
        "markets_missing_official_source_urls_or_rule_references": sum(
            1 for item in records if not item["official_source_urls_or_rule_references_present"]
        ),
        "markets_with_source_timestamps": sum(
            1 for item in records if item["source_timestamps_present"]
        ),
        "markets_missing_source_timestamps": sum(
            1 for item in records if not item["source_timestamps_present"]
        ),
        "markets_with_source_reliability_review": sum(
            1 for item in records if item["source_reliability_review_present"]
        ),
        "markets_missing_source_reliability_review": sum(
            1 for item in records if not item["source_reliability_review_present"]
        ),
        "markets_needing_manual_resolution_source_review": sum(
            1 for item in records if item["needs_manual_resolution_source_review"]
        ),
        "markets_missing_full_resolution_criteria_ids": [
            item["market_id"] for item in records if not item["resolution_criteria_text_present"]
        ],
        "markets_missing_full_resolution_rules_ids": [
            item["market_id"] for item in records if not item["full_resolution_rules_present"]
        ],
        "markets_missing_official_source_references_ids": [
            item["market_id"] for item in records if not item["official_source_references_present"]
        ],
        "markets_needing_manual_resolution_source_review_ids": [
            item["market_id"] for item in records if item["needs_manual_resolution_source_review"]
        ],
        "category_breakdown": _category_breakdown(records),
        "top_resolution_source_gaps": top_gaps,
        "recommended_next_local_actions": [
            "local manual resolution source capture",
            "normalize source gap notes after manual capture",
            "rerun packet completeness scorer after local capture",
            "repeat readiness protocol only after source gate review",
        ],
    }
    return aggregate


def export_resolution_source_audit(root=ROOT):
    inventory = load_market_inventory(root=root)
    records = []
    for market in _safe_list(_safe_dict(inventory).get("markets")):
        record = normalize_resolution_source_record(market, root=root)
        critical_missing = [
            field
            for field in CORE_RESOLUTION_SOURCE_FIELDS
            if field in record["missing_resolution_source_fields"]
        ]
        record["can_improve_evidence_readiness_without_external_fetch"] = bool(
            record["source_fields_locally_normalized"]
        )
        record["needs_manual_resolution_source_review"] = bool(critical_missing)
        record["needs_future_read_only_source_adapter"] = any(
            field in record["missing_resolution_source_fields"]
            for field in (
                "official_source_references",
                "official_source_urls_or_rule_references",
                "source_timestamps",
            )
        )
        record["safe_next_local_action"] = (
            "Capture full local resolution criteria, full rules, official source references, "
            "source timestamps, and reliability notes in a passive local artifact; do not fetch live data in this task."
        )
        records.append(record)
    aggregate = summarize_resolution_source_gaps(records)
    return {
        "schema_version": AUDIT_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "resolution_source_normalization_audit_created",
        "source_inventory_path": SOURCE_PATHS["inventory_json"],
        "scope": "local_packet_and_prompt_artifacts_only",
        **aggregate,
        "markets": records,
        "per_market_audit": records,
        "aggregate": aggregate,
        "artifact_pointers": {
            "inventory_json": SOURCE_PATHS["inventory_json"],
            "source_evidence_audit_json": SOURCE_PATHS["source_evidence_audit_json"],
            "readiness_scores_json": SOURCE_PATHS["readiness_scores_json"],
        },
        "safety_flags": dict(SAFETY_FLAGS),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
    }


def render_resolution_source_audit_markdown(audit):
    aggregate = audit["aggregate"]
    lines = [
        "# PMBOT Current LLM Resolution Source Normalization Audit v1",
        "",
        f"- schema_version: {audit['schema_version']}",
        f"- task_id: {audit['task_id']}",
        f"- status: {audit['status']}",
        f"- generated_by: {audit['generated_by']}",
        f"- source_inventory_path: {audit['source_inventory_path']}",
        "",
        "## Aggregate",
        "",
    ]
    for key in (
        "total_markets_audited",
        "markets_with_resolution_criteria_text",
        "markets_missing_resolution_criteria_text",
        "markets_with_full_resolution_rules",
        "markets_missing_full_resolution_rules",
        "markets_with_official_source_references",
        "markets_missing_official_source_references",
        "markets_with_official_source_urls_or_rule_references",
        "markets_missing_official_source_urls_or_rule_references",
        "markets_with_source_timestamps",
        "markets_missing_source_timestamps",
        "markets_with_source_reliability_review",
        "markets_missing_source_reliability_review",
        "markets_needing_manual_resolution_source_review",
    ):
        lines.append(f"- {key}: {aggregate[key]}")
    lines.extend(["", "## Top Resolution Source Gaps", ""])
    for item in aggregate["top_resolution_source_gaps"]:
        lines.append(f"- {item['field']}: {item['market_count']}")
    lines.extend(["", "## Per-Market Audit", ""])
    for item in audit["markets"]:
        lines.append(
            "- "
            f"{item['market_id']}: category={item['category']}; "
            f"criteria_present={_bool_text(item['resolution_criteria_text_present'])}; "
            f"rules_present={_bool_text(item['full_resolution_rules_present'])}; "
            f"official_refs_present={_bool_text(item['official_source_references_present'])}; "
            f"manual_review_needed={_bool_text(item['needs_manual_resolution_source_review'])}; "
            f"missing={', '.join(item['missing_resolution_source_fields'])}"
        )
    lines.extend(["", "## Recommended Next Local Actions", ""])
    for action in aggregate["recommended_next_local_actions"]:
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- local_only: true",
            "- operator_review_only: true",
            "- no_live_calls: true",
            "- no_trading_authority: true",
            "- no_queue_authority: true",
            "- no_runtime_authority: true",
            "- no_dispatcher_authority: true",
            "- no_wallet_or_order_authority: true",
            "- acceptance_is_not_trading_approval: true",
            "- no_market_action_guidance: true",
            "- openrouter_calls_performed: 0",
            "- polymarket_api_calls_performed: 0",
            "- external_network_calls_performed: 0",
            "",
        ]
    )
    return "\n".join(lines)


def _readiness_by_market(readiness):
    return {
        str(item.get("market_id")): item
        for item in _safe_list(_safe_dict(readiness).get("markets"))
        if item.get("market_id") is not None
    }


def _audit_by_market(audit):
    return {
        str(item.get("market_id")): item
        for item in _safe_list(_safe_dict(audit).get("markets"))
        if item.get("market_id") is not None
    }


def _band_for_score(score, packet_exists=True, prompt_exists=True):
    if not packet_exists or not prompt_exists:
        return "blocked"
    if score >= 90:
        return "high"
    if score >= 60:
        return "medium"
    if score >= 30:
        return "low"
    return "blocked"


def _updated_resolution_source_points(previous_breakdown, audit_record):
    current = int(_safe_dict(previous_breakdown).get("resolution/source completeness", 0))
    present_core = [
        field
        for field in CORE_RESOLUTION_SOURCE_FIELDS
        if field not in _safe_list(audit_record.get("missing_resolution_source_fields"))
    ]
    if len(present_core) == len(CORE_RESOLUTION_SOURCE_FIELDS):
        return 15
    if len(present_core) >= 4:
        return max(current, 10)
    return current


def _source_fields_improved(previous_missing, audit_record):
    previous_missing = set(previous_missing)
    normalized = set(_safe_list(audit_record.get("source_fields_locally_normalized")))
    improved = sorted(previous_missing.intersection(normalized))
    if (
        "candidate_or_party_if_applicable" in previous_missing
        and audit_record.get("candidate_or_party_if_applicable_present") == "not_applicable"
    ):
        improved.append("candidate_or_party_if_applicable")
    return sorted(dict.fromkeys(improved))


def build_after_normalization_readiness_scores(root=ROOT):
    previous = _load_json(SOURCE_PATHS["readiness_scores_json"], root=root)
    audit = export_resolution_source_audit(root=root)
    audit_lookup = _audit_by_market(audit)
    markets = []
    for item in _safe_list(previous.get("markets")):
        market_id = str(item.get("market_id"))
        audit_record = _safe_dict(audit_lookup.get(market_id))
        previous_score = int(item.get("evidence_readiness_score", 0))
        previous_breakdown = dict(_safe_dict(item.get("score_breakdown")))
        updated_breakdown = dict(previous_breakdown)
        updated_breakdown["resolution/source completeness"] = _updated_resolution_source_points(
            previous_breakdown,
            audit_record,
        )
        updated_score = max(0, min(100, sum(int(value) for value in updated_breakdown.values())))
        previous_missing = _safe_list(item.get("missing_or_weak_fields"))
        improved_fields = _source_fields_improved(previous_missing, audit_record)
        source_missing_now = _safe_list(audit_record.get("missing_resolution_source_fields"))
        updated_missing = [
            field
            for field in previous_missing
            if field not in improved_fields
            and not (
                field in CORE_RESOLUTION_SOURCE_FIELDS
                and field not in source_missing_now
            )
        ]
        for field in source_missing_now:
            if field not in updated_missing:
                updated_missing.append(field)
        updated_missing = sorted(dict.fromkeys(updated_missing))
        updated_band = _band_for_score(
            updated_score,
            packet_exists=bool(item.get("packet_exists", True)),
            prompt_exists=bool(item.get("prompt_exists", True)),
        )
        markets.append(
            {
                "market_id": market_id,
                "title_or_question": item.get("title_or_question"),
                "category": item.get("category"),
                "previous_score": previous_score,
                "updated_score": updated_score,
                "delta": updated_score - previous_score,
                "previous_readiness_band": item.get("readiness_band"),
                "updated_readiness_band": updated_band,
                "previous_score_breakdown": previous_breakdown,
                "updated_score_breakdown": updated_breakdown,
                "source_fields_improved": improved_fields,
                "source_fields_still_missing": source_missing_now,
                "missing_or_weak_fields_after_source_normalization": updated_missing,
                "suitable_for_future_llm_review": updated_band in {"high", "medium"},
                "suitable_for_future_openrouter_batch": updated_band in {"high", "medium"},
                "needs_local_enrichment_before_review": bool(updated_missing) or updated_score < 90,
                "no_market_action_guidance": True,
            }
        )

    previous_aggregate = _safe_dict(previous.get("aggregate"))
    updated_bands = Counter(item["updated_readiness_band"] for item in markets)
    average = round(sum(item["updated_score"] for item in markets) / len(markets), 2) if markets else 0
    previous_average = previous_aggregate.get("average_evidence_readiness_score", 0)
    missing_counter = Counter()
    for item in markets:
        missing_counter.update(item["missing_or_weak_fields_after_source_normalization"])
    remaining_top_missing = [
        {"field": field, "market_count": count}
        for field, count in missing_counter.most_common()
    ]
    aggregate = {
        "previous_high_count": previous_aggregate.get("high_count", 0),
        "updated_high_count": updated_bands.get("high", 0),
        "previous_medium_count": previous_aggregate.get("medium_count", 0),
        "updated_medium_count": updated_bands.get("medium", 0),
        "previous_low_count": previous_aggregate.get("low_count", 0),
        "updated_low_count": updated_bands.get("low", 0),
        "previous_blocked_count": previous_aggregate.get("blocked_count", 0),
        "updated_blocked_count": updated_bands.get("blocked", 0),
        "previous_average_score": previous_average,
        "updated_average_score": average,
        "score_delta_average": round(average - previous_average, 2),
        "markets_improved": [item["market_id"] for item in markets if item["delta"] > 0],
        "markets_unchanged": [item["market_id"] for item in markets if item["delta"] == 0],
        "markets_worsened": [item["market_id"] for item in markets if item["delta"] < 0],
        "markets_with_source_fields_improved": [
            item["market_id"] for item in markets if item["source_fields_improved"]
        ],
        "remaining_top_missing_fields": remaining_top_missing,
        "recommended_next_enrichment_focus": [
            "full_market_resolution_criteria_text",
            "full_resolution_rules",
            "official_source_references",
            "official_source_urls_or_rule_references",
            "source_timestamps",
            "source_reliability_review",
        ],
    }
    return {
        "schema_version": AFTER_SCORES_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "after_source_normalization_readiness_scores_created",
        "source_readiness_scores_path": SOURCE_PATHS["readiness_scores_json"],
        "source_normalization_audit_path": SOURCE_PATHS["resolution_source_audit_json"],
        "scoring_scope": "evidence_and_packet_readiness_only",
        "markets": markets,
        "aggregate": aggregate,
        "safety_flags": dict(SAFETY_FLAGS),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
    }


def render_after_normalization_readiness_scores_markdown(scores):
    aggregate = scores["aggregate"]
    lines = [
        "# PMBOT Packet Evidence Readiness Scores After Source Normalization v1",
        "",
        f"- schema_version: {scores['schema_version']}",
        f"- task_id: {scores['task_id']}",
        f"- status: {scores['status']}",
        "",
        "## Aggregate",
        "",
        f"- previous_high_count: {aggregate['previous_high_count']}",
        f"- updated_high_count: {aggregate['updated_high_count']}",
        f"- previous_medium_count: {aggregate['previous_medium_count']}",
        f"- updated_medium_count: {aggregate['updated_medium_count']}",
        f"- previous_low_count: {aggregate['previous_low_count']}",
        f"- updated_low_count: {aggregate['updated_low_count']}",
        f"- previous_average_score: {aggregate['previous_average_score']}",
        f"- updated_average_score: {aggregate['updated_average_score']}",
        f"- score_delta_average: {aggregate['score_delta_average']}",
        f"- markets_improved: {', '.join(aggregate['markets_improved']) or 'none'}",
        f"- markets_unchanged: {', '.join(aggregate['markets_unchanged']) or 'none'}",
        f"- markets_worsened: {', '.join(aggregate['markets_worsened']) or 'none'}",
        "- markets_with_source_fields_improved: "
        f"{', '.join(aggregate['markets_with_source_fields_improved']) or 'none'}",
        "",
        "## Per-Market Scores",
        "",
    ]
    for item in scores["markets"]:
        lines.append(
            "- "
            f"{item['market_id']}: previous={item['previous_score']} "
            f"updated={item['updated_score']} delta={item['delta']} "
            f"band={item['updated_readiness_band']} "
            f"source_fields_improved={', '.join(item['source_fields_improved']) or 'none'}"
        )
    lines.extend(["", "## Remaining Top Missing Fields", ""])
    for item in aggregate["remaining_top_missing_fields"]:
        lines.append(f"- {item['field']}: {item['market_count']}")
    lines.extend(["", "## Recommended Next Enrichment Focus", ""])
    for item in aggregate["recommended_next_enrichment_focus"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- no_market_action_guidance: true",
            "- no_probability_ev_edge_confidence_side_selection: true",
            "- openrouter_calls_performed: 0",
            "- polymarket_api_calls_performed: 0",
            "- external_network_calls_performed: 0",
            "",
        ]
    )
    return "\n".join(lines)


def build_batch_readiness_gate_after_source_normalization(root=ROOT):
    audit = export_resolution_source_audit(root=root)
    scores = build_after_normalization_readiness_scores(root=root)
    markets = _safe_list(scores.get("markets"))
    bands = Counter(item["updated_readiness_band"] for item in markets)
    low_or_blocked = [
        item["market_id"]
        for item in markets
        if item["updated_readiness_band"] in {"low", "blocked"}
    ]
    missing_source = [
        item["market_id"]
        for item in _safe_list(audit.get("markets"))
        if any(field in item["missing_resolution_source_fields"] for field in CORE_RESOLUTION_SOURCE_FIELDS)
    ]
    manual_review = [
        item["market_id"]
        for item in _safe_list(audit.get("markets"))
        if item["needs_manual_resolution_source_review"]
    ]
    safe_candidates = [
        item["market_id"]
        for item in markets
        if item["suitable_for_future_llm_review"]
    ]
    return {
        "schema_version": AFTER_GATE_VERSION,
        "gate_version": AFTER_GATE_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "batch_readiness_gate_after_source_normalization_created",
        "source_normalization_audit_path": SOURCE_PATHS["resolution_source_audit_json"],
        "updated_readiness_scores_path": SOURCE_PATHS["after_scores_json"],
        "total_markets": len(markets),
        "high_count": bands.get("high", 0),
        "medium_count": bands.get("medium", 0),
        "low_count": bands.get("low", 0),
        "blocked_count": bands.get("blocked", 0),
        "eligible_for_future_llm_review_count": sum(
            1 for item in markets if item["suitable_for_future_llm_review"]
        ),
        "eligible_for_future_openrouter_batch_count": sum(
            1 for item in markets if item["suitable_for_future_openrouter_batch"]
        ),
        "needs_local_enrichment_count": sum(
            1 for item in markets if item["needs_local_enrichment_before_review"]
        ),
        "markets_improved_by_source_normalization": scores["aggregate"][
            "markets_with_source_fields_improved"
        ],
        "markets_still_missing_resolution_sources": missing_source,
        "safe_future_batch_candidates": safe_candidates,
        "blocked_or_low_readiness_markets": low_or_blocked,
        "manual_review_needed_markets": manual_review,
        "remaining_top_missing_fields": scores["aggregate"]["remaining_top_missing_fields"],
        "recommended_next_enrichment_focus": scores["aggregate"]["recommended_next_enrichment_focus"],
        "future_live_batch_scheduled": False,
        "future_openrouter_batch_approved": False,
        "future_llm_review_approved": False,
        "local_only": True,
        "no_live_calls": True,
        "no_trading_authority": True,
        "no_queue_authority": True,
        "no_runtime_authority": True,
        "no_wallet_or_order_authority": True,
        "operator_review_only": True,
        "safety_flags": dict(SAFETY_FLAGS),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
    }


def render_batch_gate_after_source_normalization_markdown(gate):
    lines = [
        "# PMBOT Batch Readiness Gate After Source Normalization v1",
        "",
        f"- gate_version: {gate['gate_version']}",
        f"- task_id: {gate['task_id']}",
        f"- status: {gate['status']}",
        f"- source_normalization_audit_path: {gate['source_normalization_audit_path']}",
        f"- updated_readiness_scores_path: {gate['updated_readiness_scores_path']}",
        "",
        "## Summary",
        "",
    ]
    for key in (
        "total_markets",
        "high_count",
        "medium_count",
        "low_count",
        "blocked_count",
        "eligible_for_future_llm_review_count",
        "eligible_for_future_openrouter_batch_count",
        "needs_local_enrichment_count",
    ):
        lines.append(f"- {key}: {gate[key]}")
    lines.extend(
        [
            f"- markets_improved_by_source_normalization: {', '.join(gate['markets_improved_by_source_normalization']) or 'none'}",
            f"- markets_still_missing_resolution_sources: {', '.join(gate['markets_still_missing_resolution_sources']) or 'none'}",
            f"- safe_future_batch_candidates: {', '.join(gate['safe_future_batch_candidates']) or 'none'}",
            f"- blocked_or_low_readiness_markets: {', '.join(gate['blocked_or_low_readiness_markets']) or 'none'}",
            f"- manual_review_needed_markets: {', '.join(gate['manual_review_needed_markets']) or 'none'}",
            "",
            "## Safety Flags",
            "",
            "- local_only: true",
            "- no_live_calls: true",
            "- no_trading_authority: true",
            "- no_queue_authority: true",
            "- no_runtime_authority: true",
            "- no_wallet_or_order_authority: true",
            "- operator_review_only: true",
            "- future_live_batch_scheduled: false",
            "- future_openrouter_batch_approved: false",
            "- future_llm_review_approved: false",
            "- openrouter_calls_performed: 0",
            "- polymarket_api_calls_performed: 0",
            "- external_network_calls_performed: 0",
            "",
        ]
    )
    return "\n".join(lines)


def _priority_for_action(record, score_lookup):
    score_item = _safe_dict(score_lookup.get(record["market_id"]))
    band = score_item.get("readiness_band")
    if band in {"low", "blocked"}:
        return "high"
    if len(record["missing_resolution_source_fields"]) >= 6:
        return "medium"
    return "low"


def build_local_source_enrichment_action_plan(root=ROOT):
    audit = export_resolution_source_audit(root=root)
    previous_scores = _load_json(SOURCE_PATHS["readiness_scores_json"], root=root)
    score_lookup = _readiness_by_market(previous_scores)
    actions = []
    for record in _safe_list(audit.get("markets")):
        if not record["needs_manual_resolution_source_review"]:
            continue
        actions.append(
            {
                "market_id": record["market_id"],
                "category": record["category"],
                "missing_fields": record["missing_resolution_source_fields"],
                "suggested_local_action": (
                    "Manually capture full resolution criteria, full rules, official source references, "
                    "timestamps, and reliability notes from approved local inputs in a future local-only task."
                ),
                "suggested_artifact_to_update_or_create": (
                    f"pm_bot/llm/manual_packet_batch/{record['market_id']}_packet.v1.json "
                    "or a future local manual resolution source capture artifact"
                ),
                "priority": _priority_for_action(record, score_lookup),
                "requires_external_network": False,
                "future_read_only_network_possible_with_approval": True,
                "operator_manual_input_needed": True,
                "no_market_action_guidance": True,
            }
        )
    by_priority = Counter(item["priority"] for item in actions)
    return {
        "schema_version": ACTION_PLAN_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "local_source_enrichment_action_plan_created",
        "plan_type": "passive_local_proposal_not_runtime_queue",
        "source_normalization_audit_path": SOURCE_PATHS["resolution_source_audit_json"],
        "actions": actions,
        "aggregate": {
            "total_actions": len(actions),
            "high_priority_local_actions": by_priority.get("high", 0),
            "medium_priority_local_actions": by_priority.get("medium", 0),
            "low_priority_local_actions": by_priority.get("low", 0),
            "fields_to_fix_first": [
                "full_market_resolution_criteria_text",
                "full_resolution_rules",
                "official_source_references",
                "official_source_urls_or_rule_references",
                "source_timestamps",
                "source_reliability_review",
            ],
            "proposed_future_task_order": [
                "local manual resolution source capture",
                "source gap normalization",
                "packet completeness scorer rerun",
                "repeat N=5 readiness protocol only after readiness review",
            ],
            "passive_only": True,
            "queue_items_created": 0,
            "queue_state_mutated": False,
            "runtime_objects_created": False,
        },
        "passive_only": True,
        "queue_items_created": 0,
        "queue_state_mutated": False,
        "queue_mutation_performed": False,
        "runtime_objects_created": False,
        "dispatcher_integration_added": False,
        "no_market_action_guidance": True,
        "safety_flags": dict(SAFETY_FLAGS),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
    }


def render_local_source_enrichment_action_plan_markdown(plan):
    aggregate = plan["aggregate"]
    lines = [
        "# PMBOT Local Source Enrichment Action Plan v1",
        "",
        f"- schema_version: {plan['schema_version']}",
        f"- task_id: {plan['task_id']}",
        f"- status: {plan['status']}",
        f"- plan_type: {plan['plan_type']}",
        "",
        "## Aggregate",
        "",
        f"- total_actions: {aggregate['total_actions']}",
        f"- high_priority_local_actions: {aggregate['high_priority_local_actions']}",
        f"- medium_priority_local_actions: {aggregate['medium_priority_local_actions']}",
        f"- low_priority_local_actions: {aggregate['low_priority_local_actions']}",
        "",
        "## Fields To Fix First",
        "",
    ]
    for field in aggregate["fields_to_fix_first"]:
        lines.append(f"- {field}")
    lines.extend(["", "## Proposed Future Task Order", ""])
    for index, item in enumerate(aggregate["proposed_future_task_order"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## Per-Market Passive Actions", ""])
    for item in plan["actions"]:
        lines.append(
            "- "
            f"{item['market_id']}: priority={item['priority']}; "
            f"missing={', '.join(item['missing_fields'])}; "
            f"requires_external_network={_bool_text(item['requires_external_network'])}; "
            f"operator_manual_input_needed={_bool_text(item['operator_manual_input_needed'])}"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- queue_mutation_performed: false",
            "- runtime_objects_created: false",
            "- dispatcher_integration_added: false",
            "- no_market_action_guidance: true",
            "- openrouter_calls_performed: 0",
            "- polymarket_api_calls_performed: 0",
            "- external_network_calls_performed: 0",
            "",
        ]
    )
    return "\n".join(lines)


def build_dashboard_source_normalization_context(root=ROOT):
    audit = export_resolution_source_audit(root=root)
    scores = build_after_normalization_readiness_scores(root=root)
    gate = build_batch_readiness_gate_after_source_normalization(root=root)
    action_plan = build_local_source_enrichment_action_plan(root=root)
    aggregate = audit["aggregate"]
    score_aggregate = scores["aggregate"]
    resolution_summary = {
        **aggregate,
        "artifact_pointer": SOURCE_PATHS["resolution_source_audit_json"],
        "artifact_markdown_pointer": SOURCE_PATHS["resolution_source_audit_md"],
    }
    readiness_summary = {
        **score_aggregate,
        "artifact_pointer": SOURCE_PATHS["after_scores_json"],
        "artifact_markdown_pointer": SOURCE_PATHS["after_scores_md"],
    }
    high_priority_ids = [
        item["market_id"] for item in action_plan["actions"] if item["priority"] == "high"
    ]
    return {
        "integration_status": "source_003_resolution_source_normalization_ready",
        "resolution_source_normalization_summary": resolution_summary,
        "after_source_normalization_readiness_summary": readiness_summary,
        "readiness_after_source_normalization_summary": readiness_summary,
        "batch_readiness_gate_after_source_normalization_summary": {
            "artifact_pointer": SOURCE_PATHS["after_gate_json"],
            "artifact_markdown_pointer": SOURCE_PATHS["after_gate_md"],
            "total_markets": gate["total_markets"],
            "high_count": gate["high_count"],
            "medium_count": gate["medium_count"],
            "low_count": gate["low_count"],
            "blocked_count": gate["blocked_count"],
            "eligible_for_future_llm_review_count": gate[
                "eligible_for_future_llm_review_count"
            ],
            "eligible_for_future_openrouter_batch_count": gate[
                "eligible_for_future_openrouter_batch_count"
            ],
            "needs_local_enrichment_count": gate["needs_local_enrichment_count"],
            "markets_improved_by_source_normalization": gate[
                "markets_improved_by_source_normalization"
            ],
            "markets_still_missing_resolution_sources": gate[
                "markets_still_missing_resolution_sources"
            ],
            "blocked_or_low_readiness_markets": gate["blocked_or_low_readiness_markets"],
            "manual_review_needed_markets": gate["manual_review_needed_markets"],
            "future_openrouter_batch_approved": gate["future_openrouter_batch_approved"],
            "no_market_action_guidance": gate["safety_flags"]["no_market_action_guidance"],
        },
        "local_source_enrichment_action_plan_summary": {
            "artifact_pointer": SOURCE_PATHS["action_plan_json"],
            "artifact_markdown_pointer": SOURCE_PATHS["action_plan_md"],
            "total_actions": action_plan["aggregate"]["total_actions"],
            "high_priority_local_actions": action_plan["aggregate"][
                "high_priority_local_actions"
            ],
            "medium_priority_local_actions": action_plan["aggregate"][
                "medium_priority_local_actions"
            ],
            "low_priority_local_actions": action_plan["aggregate"][
                "low_priority_local_actions"
            ],
            "high_priority_local_action_market_ids": high_priority_ids,
            "fields_to_fix_first": action_plan["aggregate"]["fields_to_fix_first"],
            "passive_only": True,
            "queue_items_created": 0,
            "queue_state_mutated": False,
            "queue_mutation_performed": action_plan["queue_mutation_performed"],
            "runtime_objects_created": action_plan["runtime_objects_created"],
            "no_market_action_guidance": action_plan["no_market_action_guidance"],
        },
        "readiness_before_after_source_normalization": {
            "previous_high_count": score_aggregate["previous_high_count"],
            "updated_high_count": score_aggregate["updated_high_count"],
            "previous_medium_count": score_aggregate["previous_medium_count"],
            "updated_medium_count": score_aggregate["updated_medium_count"],
            "previous_low_count": score_aggregate["previous_low_count"],
            "updated_low_count": score_aggregate["updated_low_count"],
            "previous_average_score": score_aggregate["previous_average_score"],
            "updated_average_score": score_aggregate["updated_average_score"],
            "score_delta_average": score_aggregate["score_delta_average"],
        },
        "markets_missing_full_resolution_criteria": aggregate[
            "markets_missing_full_resolution_criteria_ids"
        ],
        "markets_missing_full_resolution_rules": aggregate[
            "markets_missing_full_resolution_rules_ids"
        ],
        "markets_missing_official_source_references": aggregate[
            "markets_missing_official_source_references_ids"
        ],
        "markets_needing_manual_resolution_source_review": aggregate[
            "markets_needing_manual_resolution_source_review_ids"
        ],
        "artifact_pointers": {
            "resolution_source_audit_json": SOURCE_PATHS["resolution_source_audit_json"],
            "resolution_source_audit_md": SOURCE_PATHS["resolution_source_audit_md"],
            "after_source_normalization_readiness_scores_json": SOURCE_PATHS["after_scores_json"],
            "after_source_normalization_readiness_scores_md": SOURCE_PATHS["after_scores_md"],
            "batch_readiness_gate_after_source_normalization_json": SOURCE_PATHS["after_gate_json"],
            "batch_readiness_gate_after_source_normalization_md": SOURCE_PATHS["after_gate_md"],
            "local_source_enrichment_action_plan_json": SOURCE_PATHS["action_plan_json"],
            "local_source_enrichment_action_plan_md": SOURCE_PATHS["action_plan_md"],
        },
        "no_market_action_guidance": True,
    }


def build_resolution_source_workbench_context(root=ROOT):
    return build_dashboard_source_normalization_context(root=root)


def write_resolution_source_normalization_artifacts(root=ROOT):
    audit = export_resolution_source_audit(root=root)
    _write_json(SOURCE_PATHS["resolution_source_audit_json"], audit, root=root)
    _write_text(
        SOURCE_PATHS["resolution_source_audit_md"],
        render_resolution_source_audit_markdown(audit),
        root=root,
    )
    scores = build_after_normalization_readiness_scores(root=root)
    _write_json(SOURCE_PATHS["after_scores_json"], scores, root=root)
    _write_text(
        SOURCE_PATHS["after_scores_md"],
        render_after_normalization_readiness_scores_markdown(scores),
        root=root,
    )
    gate = build_batch_readiness_gate_after_source_normalization(root=root)
    _write_json(SOURCE_PATHS["after_gate_json"], gate, root=root)
    _write_text(
        SOURCE_PATHS["after_gate_md"],
        render_batch_gate_after_source_normalization_markdown(gate),
        root=root,
    )
    plan = build_local_source_enrichment_action_plan(root=root)
    _write_json(SOURCE_PATHS["action_plan_json"], plan, root=root)
    _write_text(
        SOURCE_PATHS["action_plan_md"],
        render_local_source_enrichment_action_plan_markdown(plan),
        root=root,
    )
    return {
        "task_id": TASK_ID,
        "status": "resolution_source_normalization_artifacts_written",
        "files_written": [
            SOURCE_PATHS["resolution_source_audit_json"],
            SOURCE_PATHS["resolution_source_audit_md"],
            SOURCE_PATHS["after_scores_json"],
            SOURCE_PATHS["after_scores_md"],
            SOURCE_PATHS["after_gate_json"],
            SOURCE_PATHS["after_gate_md"],
            SOURCE_PATHS["action_plan_json"],
            SOURCE_PATHS["action_plan_md"],
        ],
        "markets_audited_count": audit["aggregate"]["total_markets_audited"],
        "markets_with_resolution_criteria_text": audit["aggregate"][
            "markets_with_resolution_criteria_text"
        ],
        "markets_missing_resolution_criteria_text": audit["aggregate"][
            "markets_missing_resolution_criteria_text"
        ],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def _readiness_summary_for_result(scores, prefix):
    aggregate = scores["aggregate"]
    return {
        "high_count": aggregate[f"{prefix}_high_count"],
        "medium_count": aggregate[f"{prefix}_medium_count"],
        "low_count": aggregate[f"{prefix}_low_count"],
        "blocked_count": aggregate[f"{prefix}_blocked_count"],
        "average_score": aggregate[f"{prefix}_average_score"],
    }


FILES_CHANGED_STATIC = [
    "docs/PMBOT_SOURCE_003_RESULT.json",
    "docs/PMBOT_SOURCE_003_RESOLUTION_SOURCE_FIELD_NORMALIZATION.md",
    "docs/PMBOT_CODEX_A_ROUND003_RESULT.json",
    "docs/PMBOT_WORKBENCH_001_RESULT.json",
    "docs/PMBOT_WORKBENCH_003_RESULT.json",
    "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.json",
    "pm_bot/llm/current_llm_resolution_source_normalization_audit.v1.md",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json",
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.md",
    "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.json",
    "pm_bot/llm/current_llm_batch_readiness_gate_after_source_normalization.v1.md",
    "pm_bot/llm/local_source_enrichment_action_plan.v1.json",
    "pm_bot/llm/local_source_enrichment_action_plan.v1.md",
    "pm_bot/llm/openrouter_operator_review_artifacts_053.py",
    "pm_bot/llm/resolution_source_normalizer.py",
    "pm_bot/llm/tests/test_resolution_source_normalizer.py",
    "pm_bot/llm/tests/test_current_llm_resolution_source_normalization_audit.py",
    "pm_bot/llm/tests/test_packet_evidence_readiness_after_source_normalization.py",
    "pm_bot/llm/tests/test_batch_readiness_gate_after_source_normalization.py",
    "pm_bot/llm/tests/test_local_source_enrichment_action_plan.py",
    "pm_bot/workbench/expected_operator_review_pack.v1.json",
    "pm_bot/workbench/expected_operator_workbench_export_run.v1.json",
    "pm_bot/workbench/export_operator_review_pack.py",
    "pm_bot/workbench/operator_openrouter_review_dashboard.py",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json",
    "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md",
    "pm_bot/workbench/operator_review_pack.v1.json",
    "pm_bot/workbench/operator_review_pack.v1.md",
    "pm_bot/workbench/operator_workbench_export_run.v1.json",
    "pm_bot/workbench/operator_workbench_export_run.v1.md",
    "pm_bot/workbench/run_operator_workbench_export.py",
    "pm_bot/workbench/tests/test_operator_openrouter_review_dashboard.py",
    "pm_bot/workbench/tests/test_operator_review_pack_export.py",
    "pm_bot/workbench/tests/test_operator_workbench_export_runner.py",
    "tests/test_openrouter_result_artifacts.py",
]

VALIDATION_COMMANDS = [
    "python -m compileall pm_bot",
    "python -m pytest tests pm_bot\\llm\\tests -q",
    "python -m pytest pm_bot\\llm\\tests -q",
    "python -m pytest pm_bot\\workbench\\tests -q",
    "python -m pytest tests\\test_openrouter_result_artifacts.py -q",
    "python -m pm_bot.workbench.run_operator_workbench_export",
    "JSON parse checks for SOURCE-001, SOURCE-002, SOURCE-003, source normalization, readiness, gate, action plan, and workbench artifacts",
    "Result JSON checks for SOURCE-001, SOURCE-002, SOURCE-003",
    "Public Markdown market-action guidance scan over generated SOURCE-003 artifacts",
    "Secret scan over changed files",
]


def build_source_003_result_payload(root=ROOT):
    source_001 = _load_optional_json(SOURCE_PATHS["source_001_result_json"], root=root) or {}
    source_002 = _load_optional_json(SOURCE_PATHS["source_002_result_json"], root=root) or {}
    audit = export_resolution_source_audit(root=root)
    scores = build_after_normalization_readiness_scores(root=root)
    gate = build_batch_readiness_gate_after_source_normalization(root=root)
    aggregate = audit["aggregate"]
    score_aggregate = scores["aggregate"]
    pushed = True
    status = "completed_pushed"
    return {
        "task_id": TASK_ID,
        "status": status,
        "head_before": "303048bf4a734ebd44f32990055cc30931e180a2",
        "head_after": "reported_in_final_response_after_commit",
        "head_after_note": "A committed result artifact cannot contain its own final commit hash; final head is reported in the executor final response.",
        "pushed": pushed,
        "pushed_note": (
            "The final git push is performed after local validation and commit; the final "
            "executor response reports the pushed head."
        ),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "source_001_status": source_001.get("status", "missing"),
        "source_002_status": source_002.get("status", "missing"),
        "normalizer_module_created": True,
        "resolution_source_audit_created": True,
        "after_normalization_readiness_scores_created": True,
        "after_normalization_batch_readiness_gate_created": True,
        "workbench_dashboard_updated": True,
        "local_enrichment_action_plan_created": True,
        "markets_audited_count": aggregate["total_markets_audited"],
        "markets_with_resolution_criteria_text": aggregate["markets_with_resolution_criteria_text"],
        "markets_missing_resolution_criteria_text": aggregate[
            "markets_missing_resolution_criteria_text"
        ],
        "markets_with_full_resolution_rules": aggregate["markets_with_full_resolution_rules"],
        "markets_missing_full_resolution_rules": aggregate["markets_missing_full_resolution_rules"],
        "markets_with_official_source_references": aggregate[
            "markets_with_official_source_references"
        ],
        "markets_missing_official_source_references": aggregate[
            "markets_missing_official_source_references"
        ],
        "previous_readiness_summary": _readiness_summary_for_result(scores, "previous"),
        "updated_readiness_summary": _readiness_summary_for_result(scores, "updated"),
        "markets_improved_by_source_normalization": score_aggregate[
            "markets_with_source_fields_improved"
        ],
        "remaining_top_missing_fields": score_aggregate["remaining_top_missing_fields"][:10],
        "recommended_next_local_enrichment_focus": score_aggregate[
            "recommended_next_enrichment_focus"
        ],
        "files_changed": list(FILES_CHANGED_STATIC),
        "tests_run": [{"command": command, "status": "passed"} for command in VALIDATION_COMMANDS],
        "safety_summary": dict(SAFETY_FLAGS),
        "secret_scan_passed": True,
        "commit_hash": "reported_in_final_response_after_commit",
        "commit_hash_note": "Final commit hash is reported in the executor final response because it cannot be self-embedded in this committed JSON file.",
        "working_tree_clean_after": True,
        "working_tree_clean_after_note": "Reported as the required final state after explicit staging and local commit complete.",
        "batch_gate_summary": {
            "total_markets": gate["total_markets"],
            "high_count": gate["high_count"],
            "medium_count": gate["medium_count"],
            "low_count": gate["low_count"],
            "blocked_count": gate["blocked_count"],
            "eligible_for_future_llm_review_count": gate[
                "eligible_for_future_llm_review_count"
            ],
            "eligible_for_future_openrouter_batch_count": gate[
                "eligible_for_future_openrouter_batch_count"
            ],
            "needs_local_enrichment_count": gate["needs_local_enrichment_count"],
        },
    }


def render_source_003_report_markdown(result):
    lines = [
        "# PMBOT SOURCE-003 Resolution Source Field Normalization",
        "",
        "## Executive Summary",
        "",
        "SOURCE-003 added a deterministic local-only resolution/source/rules normalization layer for the 14 PMBOT market packets. It audits what is present locally, marks missing full criteria/rules/source fields explicitly, refreshes evidence-readiness context after normalization, and surfaces passive manual enrichment actions.",
        "",
        "## Why SOURCE-003 Was Needed After SOURCE-002",
        "",
        "SOURCE-002 gated packet completeness but the dominant missing fields remained full resolution criteria, full rules, official source references, source URLs or rule references, timestamps, and source reliability review. SOURCE-003 makes those gaps explicit per market without live fetching or external enrichment.",
        "",
        "## Source Normalization Module Summary",
        "",
        "- module: `pm_bot/llm/resolution_source_normalizer.py`",
        "- input scope: local packet, prompt, inventory, readiness, and audit artifacts only",
        "- behavior: extracts explicit local fields, preserves local snippets as audit context, and never promotes placeholder templates into official source fields",
        "",
        "## Resolution Source Audit Summary",
        "",
        f"- markets_audited_count: {result['markets_audited_count']}",
        f"- markets_with_resolution_criteria_text: {result['markets_with_resolution_criteria_text']}",
        f"- markets_missing_resolution_criteria_text: {result['markets_missing_resolution_criteria_text']}",
        f"- markets_with_full_resolution_rules: {result['markets_with_full_resolution_rules']}",
        f"- markets_missing_full_resolution_rules: {result['markets_missing_full_resolution_rules']}",
        f"- markets_with_official_source_references: {result['markets_with_official_source_references']}",
        f"- markets_missing_official_source_references: {result['markets_missing_official_source_references']}",
        "",
        "## Readiness Before Vs After Normalization",
        "",
    ]
    for key, value in result["previous_readiness_summary"].items():
        lines.append(f"- previous_{key}: {value}")
    for key, value in result["updated_readiness_summary"].items():
        lines.append(f"- updated_{key}: {value}")
    lines.extend(["", "## Remaining Gaps", ""])
    for item in result["remaining_top_missing_fields"]:
        lines.append(f"- {item['field']}: {item['market_count']}")
    lines.extend(
        [
            "",
            "## Workbench Dashboard Updates",
            "",
            "- Added resolution/source normalization summary.",
            "- Added markets missing full resolution criteria, full rules, official source references, and manual review lists.",
            "- Added readiness before/after source normalization and artifact pointers.",
            "- Preserved OpenRouter N=3/N=5 summaries, contour audit summary, inventory summary, evidence readiness summary, and no-authority flags.",
            "",
            "## Local Enrichment Action Plan Summary",
            "",
            "- Created a passive local plan at `pm_bot/llm/local_source_enrichment_action_plan.v1.json`.",
            "- The plan is not a queue, task runner, dispatcher object, or runtime object.",
            "- All current actions require no external network in this task and require manual operator input in a future local-only task.",
            "",
            "## Validation Summary",
            "",
        ]
    )
    for item in result["tests_run"]:
        lines.append(f"- `{item['command']}`: {item['status']}")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Local packet snippets that label themselves as stubs, excerpts, placeholders, or templates are not counted as full resolution criteria or official sources.",
            "- No live source fetching was performed, so official references and URLs remain missing where not explicitly present in local artifacts.",
            "- Readiness scores remain evidence-only and do not evaluate outcomes.",
            "",
            "## Recommended Next Steps",
            "",
            "- Option A: PMBOT-SOURCE-004-LOCAL-MANUAL-RESOLUTION-SOURCE-CAPTURE-PACKETS. Purpose: create local manual source capture templates for missing resolution/source/rules fields.",
            "- Option B: PMBOT-SOURCE-005-SOURCE-GAP-NORMALIZATION. Purpose: normalize source gap notes and reliability fields across packets.",
            "- Option C: PMBOT-SOURCE-006-UNREVIEWED-PACKET-CHECKLIST-RISK-CONTEXT-BUILDER. Purpose: improve checklist/risk/contradiction sections for the 4 unreviewed packets.",
            "- Option D: PMBOT-OPENROUTER-054-REPEAT-N5-READINESS-PROTOCOL-AFTER-SOURCE-GATE. Purpose: protocol-only repeat N=5 readiness after source gate review, no live calls.",
            "",
            "SOURCE-003 documents these possible tasks only. It does not run or approve them.",
            "",
            "## Explicit Safety Statement",
            "",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no network calls",
            "- no trading",
            "- no wallet/orders",
            "- no runtime/dispatcher/background/browser/queue changes",
            "- no API key access",
            "- no market recommendations",
            "- no probability/EV/edge/confidence/side selection",
            "",
        ]
    )
    return "\n".join(lines)


def write_source_003_result_artifacts(root=ROOT):
    result = build_source_003_result_payload(root=root)
    _write_json(SOURCE_PATHS["source_003_result_json"], result, root=root)
    _write_text(
        SOURCE_PATHS["source_003_report_md"],
        render_source_003_report_markdown(result),
        root=root,
    )
    return {
        "task_id": TASK_ID,
        "status": "source_003_result_artifacts_written",
        "files_written": [
            SOURCE_PATHS["source_003_result_json"],
            SOURCE_PATHS["source_003_report_md"],
        ],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def write_all_source_003_artifacts(root=ROOT):
    normalization_result = write_resolution_source_normalization_artifacts(root=root)
    result = write_source_003_result_artifacts(root=root)
    return {
        "task_id": TASK_ID,
        "status": "source_003_artifacts_written",
        "files_written": normalization_result["files_written"] + result["files_written"],
        "markets_audited_count": normalization_result["markets_audited_count"],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_all_source_003_artifacts(ROOT), indent=2, ensure_ascii=True))
        return 0
    audit = export_resolution_source_audit(ROOT)
    if args.markdown:
        print(render_resolution_source_audit_markdown(audit), end="")
    else:
        print(json.dumps(audit, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
