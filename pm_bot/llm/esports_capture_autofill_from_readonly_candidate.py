import argparse
import json
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-009B-ESPORTS-DRAFT-CAPTURE-AUTOFILL-FROM-READONLY-CANDIDATE"
SCHEMA_VERSION = "esports_capture_autofill_result_009b.v1"
GENERATED_BY = "pm_bot/llm/esports_capture_autofill_from_readonly_candidate.py"

ROOT = Path(__file__).resolve().parents[2]

MARKET_ID = "1987056"
MARKET_CLASS = "esports"
MARKET_TITLE = (
    "LoL: JD Gaming vs Anyone's Legend (BO5) - Esports World Cup China Qualifier Phase 2"
)
CAPTURE_STATUS = "draft"
READINESS_BAND = "draft_from_readonly_candidate"
LOCAL_TIMESTAMP = "2026-05-08 Asia/Tbilisi"

ARTIFACT_DIR = "pm_bot/live_readonly/esports_market_discovery"
RAW_FETCH_PATH = f"{ARTIFACT_DIR}/esports_market_raw_fetch_009a.v1.json"
NORMALIZED_CANDIDATE_PATH = (
    f"{ARTIFACT_DIR}/esports_market_normalized_candidate_009a.v1.json"
)
SOURCE_CANDIDATE_PATH = (
    f"{ARTIFACT_DIR}/esports_source_capture_candidate_009a.v1.json"
)
CHECKLIST_JSON_PATH = f"{ARTIFACT_DIR}/esports_operator_review_checklist_009a.v1.json"
CHECKLIST_MD_PATH = f"{ARTIFACT_DIR}/esports_operator_review_checklist_009a.v1.md"

TARGET_CAPTURE_JSON_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.json"
)
TARGET_CAPTURE_MD_PATH = (
    "pm_bot/llm/manual_resolution_source_capture/"
    f"{MARKET_ID}_resolution_source_capture.v1.md"
)
AUTOFILL_RESULT_JSON_PATH = "pm_bot/llm/esports_capture_autofill_result_009b.v1.json"
AUTOFILL_RESULT_MD_PATH = "pm_bot/llm/esports_capture_autofill_result_009b.v1.md"
OPERATOR_SURFACE_JSON_PATH = (
    "pm_bot/llm/esports_capture_operator_review_surface_009b.v1.json"
)
OPERATOR_SURFACE_MD_PATH = (
    "pm_bot/llm/esports_capture_operator_review_surface_009b.v1.md"
)
SOURCE_QUALITY_OBSERVATION_JSON_PATH = (
    "pm_bot/llm/source_quality_observation_candidate_1987056_009b.v1.json"
)
SOURCE_QUALITY_OBSERVATION_MD_PATH = (
    "pm_bot/llm/source_quality_observation_candidate_1987056_009b.v1.md"
)
DOC_RESULT_JSON_PATH = "docs/PMBOT_SOURCE_009B_RESULT.json"
DOC_RESULT_MD_PATH = (
    "docs/PMBOT_SOURCE_009B_ESPORTS_DRAFT_CAPTURE_AUTOFILL_FROM_READONLY_CANDIDATE.md"
)

NO_AUTHORITY_FLAGS = {
    "no_market_action_guidance": True,
    "operator_review_only": True,
    "no_trading_authority": True,
    "no_queue_authority": True,
    "no_runtime_authority": True,
    "no_wallet_or_order_authority": True,
}

SAFETY_SUMMARY = {
    **NO_AUTHORITY_FLAGS,
    "analysis_only": True,
    "local_only": True,
    "manual_review_only": True,
    "passive_context_only": True,
    "no_dispatcher_authority": True,
    "no_browser_automation": True,
    "no_probability_ev_edge_confidence_side_selection": True,
    "openrouter_calls_performed": 0,
    "polymarket_api_calls_performed": 0,
    "external_network_calls_performed": 0,
    "network_calls_performed": 0,
    "api_key_accessed": False,
    "api_key_value_printed": False,
    "api_key_value_written": False,
    "api_key_leaked": False,
    "authenticated_endpoints_used": False,
    "wallet_or_private_key_accessed": False,
    "orders_created": 0,
    "queue_items_created": 0,
    "queue_state_mutated": False,
    "runtime_wiring_added": False,
    "dispatcher_changed": False,
    "background_workers_added": False,
    "browser_automation_used": False,
    "market_decisions_made": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Autofill an esports manual source capture draft from SOURCE-009A local artifacts."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Build artifacts in memory only.")
    mode.add_argument("--write", action="store_true", help="Write local draft artifacts.")
    mode.add_argument(
        "--summary-only",
        action="store_true",
        help="Print a concise summary from local artifacts without writing.",
    )
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
    return _load_json(path, root=root)


def _write_json(path, payload, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _ascii(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def _strip_trailing_whitespace(text):
    return "\n".join(line.rstrip() for line in str(text).splitlines())


def _write_text(path, text, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(_ascii(_strip_trailing_whitespace(text)) + "\n", encoding="utf-8")


def _as_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _safe_list(value):
    return value if isinstance(value, list) else []


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _dedupe(values):
    output = []
    seen = set()
    for value in values:
        text = _as_text(value)
        if text and text not in seen:
            output.append(text)
            seen.add(text)
    return output


def _source_timestamps(candidate, normalized):
    source_timestamps = _safe_dict(candidate.get("source_timestamps"))
    values = []
    fetched_at = source_timestamps.get("fetched_at_marker")
    scheduled = (
        source_timestamps.get("scheduled_time_if_available")
        or normalized.get("scheduled_time_if_available")
    )
    if fetched_at:
        values.append(f"SOURCE-009A read-only fetch marker: {fetched_at}")
    if scheduled:
        values.append(f"Scheduled match time from normalized candidate: {scheduled}")
    values.append(
        f"SOURCE-009B local autofill timestamp: {LOCAL_TIMESTAMP}; no network calls performed."
    )
    return values


def _candidate_paths():
    return {
        "raw_fetch": RAW_FETCH_PATH,
        "normalized_candidate": NORMALIZED_CANDIDATE_PATH,
        "source_capture_candidate": SOURCE_CANDIDATE_PATH,
        "operator_checklist_json": CHECKLIST_JSON_PATH,
        "operator_checklist_md": CHECKLIST_MD_PATH,
    }


def load_source_009a_artifacts(root=ROOT):
    return {
        "raw_fetch": _load_json(RAW_FETCH_PATH, root=root),
        "normalized_candidate": _load_json(NORMALIZED_CANDIDATE_PATH, root=root),
        "source_capture_candidate": _load_json(SOURCE_CANDIDATE_PATH, root=root),
        "operator_checklist": _load_json(CHECKLIST_JSON_PATH, root=root),
    }


def _unresolved_questions(normalized, source_candidate):
    source_identified = bool(source_candidate.get("official_result_source_identified"))
    questions = [
        "Operator must verify exact Polymarket/Gamma rules text before any status promotion.",
        "Operator must verify match, tournament, game, team names, timezone, and event schedule.",
        "Operator must verify cancellation, reschedule, forfeit, walkover, delay, and name discrepancy handling.",
        "Operator must verify the official result source and fallback source hierarchy around event conclusion.",
    ]
    questions.extend(_safe_list(normalized.get("unresolved_source_questions")))
    questions.extend(_safe_list(source_candidate.get("unresolved_source_questions")))
    if not source_identified:
        questions.append(
            "Official result source was not identified in SOURCE-009A candidate; operator must identify it before promotion."
        )
    return _dedupe(questions)


def _direct_rules_text_captured(source_candidate):
    return bool(
        source_candidate.get("direct_rules_text_captured")
        and _as_text(source_candidate.get("full_resolution_rules"))
    )


def _official_result_source_identified(source_candidate):
    return bool(
        source_candidate.get("official_result_source_identified")
        and (
            _safe_list(source_candidate.get("official_source_references"))
            or _safe_list(source_candidate.get("official_source_urls_or_rule_references"))
        )
    )


def build_manual_capture_packet(root=ROOT):
    artifacts = load_source_009a_artifacts(root=root)
    normalized = artifacts["normalized_candidate"]
    source_candidate = artifacts["source_capture_candidate"]
    checklist = artifacts["operator_checklist"]

    full_criteria = _as_text(source_candidate.get("full_market_resolution_criteria_text"))
    full_rules = _as_text(source_candidate.get("full_resolution_rules"))
    official_references = _dedupe(
        [
            "SOURCE-009A read-only Gamma market metadata artifact for market-specific rules text",
            *_safe_list(source_candidate.get("official_source_references")),
        ]
    )
    official_urls = _dedupe(
        [
            *_safe_list(source_candidate.get("official_source_urls_or_rule_references")),
            SOURCE_CANDIDATE_PATH,
        ]
    )
    evidence_refs = _dedupe(
        [
            RAW_FETCH_PATH,
            NORMALIZED_CANDIDATE_PATH,
            SOURCE_CANDIDATE_PATH,
            CHECKLIST_JSON_PATH,
            CHECKLIST_MD_PATH,
            *_safe_list(source_candidate.get("reviewed_local_evidence_references")),
        ]
    )
    direct_rules = _direct_rules_text_captured(source_candidate)
    official_source = _official_result_source_identified(source_candidate)
    unresolved = _unresolved_questions(normalized, source_candidate)
    teams = _safe_list(normalized.get("teams_or_players"))

    packet = {
        "contract_version": "manual_resolution_source_capture.v1",
        "schema_version": "manual_resolution_source_capture_schema.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": "deterministic-source-009b-esports-readonly-candidate-autofill.v1",
        "market_id": MARKET_ID,
        "category": MARKET_CLASS,
        "market_class": MARKET_CLASS,
        "market_title_or_question": normalized.get("title_or_question") or MARKET_TITLE,
        "current_openrouter_review_status": "not_reviewed",
        "current_readiness_band": READINESS_BAND,
        "source_capture_status": CAPTURE_STATUS,
        "capture_status": CAPTURE_STATUS,
        "operator_review_required": True,
        "auto_promote_to_ready_for_local_review": False,
        "full_market_resolution_criteria_text": full_criteria,
        "full_resolution_rules": full_rules,
        "official_source_references": official_references,
        "official_source_urls_or_rule_references": official_urls,
        "source_timestamps": _source_timestamps(source_candidate, normalized),
        "source_reliability_review": (
            "SOURCE-009A provides locally stored public read-only Gamma metadata for rules text. "
            "The market metadata names https://gol.gg/esports/home as the official result source, "
            "but SOURCE-009B does not fetch or verify any live result page. Operator review must "
            "verify the exact rules text, source hierarchy, event identity, and timing before any "
            "status promotion."
        ),
        "reviewed_local_evidence_references": evidence_refs,
        "non_placeholder_evidence_notes": (
            "SOURCE-009A locally stored Gamma metadata contains the esports market description, "
            "rules text, named result source, event/tournament context, teams, game title, and "
            "scheduled time. SOURCE-009B copies that evidence into a manual capture draft only; "
            "operator review remains required and no market decision is made."
        ),
        "jurisdiction": "global_esports_competition_context",
        "candidate_or_party_if_applicable": "; ".join(teams) if teams else None,
        "manual_operator_notes": (
            "Draft autofilled from SOURCE-009A read-only candidate artifacts. Direct rules text "
            f"captured from stored candidate artifact: {str(direct_rules).lower()}. Official result "
            f"source identified by stored market metadata: {str(official_source).lower()}. Keep this "
            "capture as draft until an operator verifies the exact market rules and source hierarchy."
        ),
        "unresolved_source_questions": unresolved,
        "source_capture_author_or_operator": "local_autofill_from_source_009a_readonly_candidate",
        "source_capture_timestamp_local": LOCAL_TIMESTAMP,
        "source_capture_provenance": (
            "local_only_autofill_from_pm_bot_live_readonly_esports_market_discovery_009a_artifacts; "
            "direct_rules_text_captured="
            + str(direct_rules).lower()
            + "; official_result_source_identified="
            + str(official_source).lower()
            + "; no network calls in SOURCE-009B"
        ),
        **NO_AUTHORITY_FLAGS,
        "missing_fields_prefilled_from_source_003": [
            "full_market_resolution_criteria_text",
            "full_resolution_rules",
            "official_source_references",
            "official_source_urls_or_rule_references",
            "source_timestamps",
            "source_reliability_review",
            "reviewed_local_evidence_references",
            "non_placeholder_evidence_notes",
        ],
        "source_003_audit_reference": {
            "artifact_path": SOURCE_CANDIDATE_PATH,
            "market_id": MARKET_ID,
            "packet_file_path": NORMALIZED_CANDIDATE_PATH,
            "prompt_file_path": None,
            "missing_resolution_source_fields": _safe_list(normalized.get("missing_fields")),
            "normalization_warnings": [
                "source_009a_candidate_is_readonly_metadata_and_requires_operator_review",
                "capture_status_remains_draft",
                "ready_for_local_review_not_auto_set",
            ],
            "safe_next_local_action": (
                "Review exact market rules and official result source locally; keep draft until verified."
            ),
        },
        "packet_inventory_reference": {
            "artifact_path": NORMALIZED_CANDIDATE_PATH,
            "market_id": MARKET_ID,
            "packet_file_path": RAW_FETCH_PATH,
            "prompt_file_path": None,
            "warnings": [
                "pilot_discovered_market_not_part_of_original_source_003_inventory",
                "operator_review_required_before_promotion",
            ],
        },
        "readiness_gate_reference": {
            "artifact_path": "pm_bot/llm/post_capture_batch_readiness_gate.v1.json",
            "readiness_scores_path": "pm_bot/llm/post_capture_readiness_report.v1.json",
            "market_id": MARKET_ID,
            "current_readiness_band": READINESS_BAND,
            "suitable_for_future_openrouter_batch": False,
        },
        "operator_instructions": [
            "Verify exact Polymarket/Gamma rules text against the stored 009A candidate and any approved local source review surface.",
            "Verify official result source and fallback source hierarchy.",
            "Verify event identity, teams, scheduled time, and timezone.",
            "Verify cancellation, reschedule, forfeit, walkover, delay, and name discrepancy handling.",
            "Keep this capture as draft until operator review is complete.",
            "Do not add predictions, market action guidance, probability, EV, edge, confidence, or side selection.",
        ],
        "source_009a_candidate_reference": {
            "paths": _candidate_paths(),
            "direct_rules_text_captured": direct_rules,
            "official_result_source_identified": official_source,
            "operator_review_required": True,
            "auto_promote_to_ready_for_local_review": False,
        },
        "safety_summary": dict(SAFETY_SUMMARY),
    }
    return packet


def render_capture_markdown(packet):
    lines = [
        "# Manual Resolution Source Capture - 1987056",
        "",
        f"- contract_version: {packet['contract_version']}",
        f"- schema_version: {packet['schema_version']}",
        f"- task_id: {packet['task_id']}",
        f"- market_id: {packet['market_id']}",
        f"- market_class: {packet['market_class']}",
        f"- market_title_or_question: {packet['market_title_or_question']}",
        f"- current_openrouter_review_status: {packet['current_openrouter_review_status']}",
        f"- current_readiness_band: {packet['current_readiness_band']}",
        f"- source_capture_status: {packet['source_capture_status']}",
        f"- capture_status: {packet['capture_status']}",
        "- operator_review_required: true",
        "- auto_promote_to_ready_for_local_review: false",
        "",
        "## Source Capture",
        "",
        "### Full Market Resolution Criteria Text",
        "",
        packet["full_market_resolution_criteria_text"],
        "",
        "### Full Resolution Rules",
        "",
        packet["full_resolution_rules"],
        "",
        "### Official Source References",
        "",
    ]
    for item in packet["official_source_references"]:
        lines.append(f"- {item}")
    lines.extend(["", "### Source URLs Or Rule References", ""])
    for item in packet["official_source_urls_or_rule_references"]:
        lines.append(f"- {item}")
    lines.extend(["", "### Source Timestamps", ""])
    for item in packet["source_timestamps"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "### Source Reliability Review",
            "",
            packet["source_reliability_review"],
            "",
            "### Reviewed Local Evidence References",
            "",
        ]
    )
    for item in packet["reviewed_local_evidence_references"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "### Evidence Notes",
            "",
            packet["non_placeholder_evidence_notes"],
            "",
            "## Unresolved Source Questions",
            "",
        ]
    )
    for item in packet["unresolved_source_questions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Operator Instructions",
            "",
        ]
    )
    for item in packet["operator_instructions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- local-only draft from SOURCE-009A artifacts",
            "- no OpenRouter calls",
            "- no Polymarket API calls in SOURCE-009B",
            "- no external network calls",
            "- no market action guidance",
            "- no probability, EV, edge, confidence scoring, or side selection",
            "- no trading, queue, runtime, dispatcher, background, browser, wallet, or order authority",
            "",
        ]
    )
    return "\n".join(lines)


def build_operator_review_surface(root=ROOT):
    artifacts = load_source_009a_artifacts(root=root)
    normalized = artifacts["normalized_candidate"]
    source_candidate = artifacts["source_capture_candidate"]
    checklist = artifacts["operator_checklist"]
    unresolved = _unresolved_questions(normalized, source_candidate)
    return {
        "schema_version": "esports_capture_operator_review_surface_009b.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "title": normalized.get("title_or_question") or MARKET_TITLE,
        "market_class": MARKET_CLASS,
        "capture_status": CAPTURE_STATUS,
        "source_capture_status": CAPTURE_STATUS,
        "operator_review_required": True,
        "auto_promote_to_ready_for_local_review": False,
        "missing_or_ambiguous_fields": unresolved,
        "checklist_items_from_009a": _safe_list(checklist.get("checklist")),
        "operator_next_actions": [
            "Verify exact rules text and source hierarchy.",
            "Verify match identity, teams, scheduled time, and timezone.",
            "Verify cancellation, reschedule, forfeit, walkover, delay, and name discrepancy handling.",
            "Keep capture as draft until review is complete.",
        ],
        "no_market_action_guidance": True,
        "operator_review_only": True,
        "no_trading_authority": True,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def render_operator_review_surface_markdown(surface):
    lines = [
        "# PMBOT SOURCE-009B Esports Operator Review Surface",
        "",
        f"- task_id: {surface['task_id']}",
        f"- market_id: {surface['market_id']}",
        f"- title: {surface['title']}",
        f"- market_class: {surface['market_class']}",
        f"- capture_status: {surface['capture_status']}",
        "- operator_review_required: true",
        "- auto_promote_to_ready_for_local_review: false",
        "",
        "## Missing Or Ambiguous Fields",
        "",
    ]
    for item in surface["missing_or_ambiguous_fields"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Checklist Items From 009A", ""])
    for item in surface["checklist_items_from_009a"]:
        lines.append(
            f"- [{item.get('status', 'unchecked')}] {item.get('check_id')}: {item.get('review_prompt')}"
        )
    lines.extend(["", "## Operator Next Actions", ""])
    for item in surface["operator_next_actions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- no market action guidance",
            "- operator review only",
            "- no trading, queue, runtime, dispatcher, background, browser, wallet, or order authority",
            "",
        ]
    )
    return "\n".join(lines)


def build_source_quality_observation_candidate(root=ROOT):
    artifacts = load_source_009a_artifacts(root=root)
    source_candidate = artifacts["source_capture_candidate"]
    references = _safe_list(source_candidate.get("official_source_references"))
    urls = _safe_list(source_candidate.get("official_source_urls_or_rule_references"))
    source_ids = _dedupe(
        [
            "source_009a_gamma_market_metadata_1987056",
            "source_009a_polymarket_gamma_rules_text_1987056",
            *references,
            *urls,
        ]
    )
    return {
        "schema_version": "source_quality_observation_candidate_009b.v1",
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "source_ids_observed": source_ids,
        "source_types_observed": [
            "public_readonly_gamma_market_metadata",
            "market_rules_text_from_source_009a_artifact",
            "official_result_source_reference_from_market_metadata",
        ],
        "source_roles": [
            {
                "source_id": "source_009a_gamma_market_metadata_1987056",
                "roles": ["market_metadata_source", "market_rules_source"],
            },
            {
                "source_id": "https://gol.gg/esports/home",
                "roles": ["official_result_source_candidate"],
            },
            {
                "source_id": "source_009a_operator_checklist_1987056",
                "roles": [
                    "tournament_or_match_context_source",
                    "unresolved_source",
                ],
            },
        ],
        "source_quality_status": "pending_resolution_outcome",
        "outcome_known": False,
        "source_scoring_performed": False,
        "trading_profit_used_for_scoring": False,
        "operator_review_required": True,
        "notes": [
            "Observation hook only; no source score is assigned.",
            "Outcome is not known in SOURCE-009B.",
            "Future review should compare source text to final resolution evidence after operator review.",
        ],
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def render_source_quality_observation_markdown(observation):
    lines = [
        "# PMBOT SOURCE-009B Source Quality Observation Candidate",
        "",
        f"- task_id: {observation['task_id']}",
        f"- market_id: {observation['market_id']}",
        f"- market_class: {observation['market_class']}",
        f"- source_quality_status: {observation['source_quality_status']}",
        "- outcome_known: false",
        "- source_scoring_performed: false",
        "- trading_profit_used_for_scoring: false",
        "- operator_review_required: true",
        "",
        "## Sources Observed",
        "",
    ]
    for item in observation["source_ids_observed"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Source Roles", ""])
    for item in observation["source_roles"]:
        roles = ", ".join(item["roles"])
        lines.append(f"- {item['source_id']}: {roles}")
    lines.extend(["", "## Notes", ""])
    for item in observation["notes"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- observation hook only",
            "- no market action guidance",
            "- no source performance score",
            "- no side selection",
            "",
        ]
    )
    return "\n".join(lines)


def _current_pipeline_snapshot(root=ROOT):
    ingest = _load_optional_json(
        "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json",
        root=root,
    )
    readiness = _load_optional_json(
        "pm_bot/llm/post_capture_readiness_report.v1.json",
        root=root,
    )
    gate = _load_optional_json("pm_bot/llm/post_capture_batch_readiness_gate.v1.json", root=root)
    return {
        "real_filled_template_count": (ingest or {}).get("real_filled_template_count"),
        "real_ingested_template_count": (ingest or readiness or {}).get(
            "real_ingested_template_count"
        ),
        "draft_ingested_template_count": (readiness or {}).get("draft_ingested_template_count"),
        "ready_ingested_template_count": (readiness or {}).get("ready_ingested_template_count"),
        "future_live_002_allowed": (gate or {}).get("future_live_002_allowed"),
        "source_overlay_market_ids": (readiness or {}).get("source_overlay_market_ids", []),
    }


def build_autofill_result(root=ROOT, dry_run=True, capture_written=False):
    packet = build_manual_capture_packet(root=root)
    surface = build_operator_review_surface(root=root)
    observation = build_source_quality_observation_candidate(root=root)
    pipeline = _current_pipeline_snapshot(root=root)
    direct_rules = packet["source_009a_candidate_reference"]["direct_rules_text_captured"]
    official_source = packet["source_009a_candidate_reference"][
        "official_result_source_identified"
    ]
    files_written = []
    if capture_written:
        files_written = [
            TARGET_CAPTURE_JSON_PATH,
            TARGET_CAPTURE_MD_PATH,
            AUTOFILL_RESULT_JSON_PATH,
            AUTOFILL_RESULT_MD_PATH,
            OPERATOR_SURFACE_JSON_PATH,
            OPERATOR_SURFACE_MD_PATH,
            SOURCE_QUALITY_OBSERVATION_JSON_PATH,
            SOURCE_QUALITY_OBSERVATION_MD_PATH,
            DOC_RESULT_JSON_PATH,
            DOC_RESULT_MD_PATH,
        ]
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "dry_run_no_write" if dry_run else "completed_local",
        "dry_run": dry_run,
        "source_candidate_path": SOURCE_CANDIDATE_PATH,
        "normalized_candidate_path": NORMALIZED_CANDIDATE_PATH,
        "target_capture_json_path": TARGET_CAPTURE_JSON_PATH,
        "target_capture_md_path": TARGET_CAPTURE_MD_PATH,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "market_title_or_question": packet["market_title_or_question"],
        "planned_capture_status": CAPTURE_STATUS,
        "capture_status": packet["capture_status"],
        "capture_written": capture_written,
        "operator_review_required": True,
        "direct_rules_text_captured": direct_rules,
        "official_result_source_identified": official_source,
        "unresolved_source_question_count": len(packet["unresolved_source_questions"]),
        "operator_review_surface_created": capture_written,
        "source_quality_observation_candidate_created": capture_written,
        "canonical_packets_mutated": False,
        "pipeline_snapshot_at_result_write": pipeline,
        "safety_summary": dict(SAFETY_SUMMARY),
        "files_written": files_written,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def render_autofill_result_markdown(result):
    pipeline = result["pipeline_snapshot_at_result_write"]
    lines = [
        "# PMBOT SOURCE-009B Esports Draft Capture Autofill Result",
        "",
        f"- task_id: {result['task_id']}",
        f"- status: {result['status']}",
        f"- dry_run: {str(result['dry_run']).lower()}",
        f"- market_id: {result['market_id']}",
        f"- market_class: {result['market_class']}",
        f"- planned_capture_status: {result['planned_capture_status']}",
        f"- capture_written: {str(result['capture_written']).lower()}",
        f"- operator_review_required: {str(result['operator_review_required']).lower()}",
        f"- direct_rules_text_captured: {str(result['direct_rules_text_captured']).lower()}",
        f"- official_result_source_identified: {str(result['official_result_source_identified']).lower()}",
        f"- unresolved_source_question_count: {result['unresolved_source_question_count']}",
        f"- canonical_packets_mutated: {str(result['canonical_packets_mutated']).lower()}",
        "",
        "## Pipeline Snapshot",
        "",
        f"- real_filled_template_count: {pipeline.get('real_filled_template_count')}",
        f"- real_ingested_template_count: {pipeline.get('real_ingested_template_count')}",
        f"- draft_ingested_template_count: {pipeline.get('draft_ingested_template_count')}",
        f"- ready_ingested_template_count: {pipeline.get('ready_ingested_template_count')}",
        f"- future_live_002_allowed: {pipeline.get('future_live_002_allowed')}",
        "",
        "## Safety Boundary",
        "",
        "- local-only",
        "- no OpenRouter calls",
        "- no Polymarket API calls in SOURCE-009B",
        "- no external network calls",
        "- no market action guidance",
        "- no probability, EV, edge, confidence scoring, or side selection",
        "- no trading, queue, runtime, dispatcher, background, browser, wallet, or order authority",
        "",
    ]
    return "\n".join(lines)


def build_docs_result(root=ROOT, dry_run=False, capture_written=True):
    result = build_autofill_result(root=root, dry_run=dry_run, capture_written=capture_written)
    pipeline = result["pipeline_snapshot_at_result_write"]
    validation = _load_optional_json(
        "pm_bot/llm/manual_resolution_source_capture_validation.v1.json",
        root=root,
    )
    validator_passed = (
        (validation or {}).get("status")
        == "manual_resolution_source_capture_validation_passed"
    )
    return {
        "task_id": TASK_ID,
        "status": "completed_local_validation_pending_commit",
        "head_before": "2b856b351fd773269518d5f7956c2a04b4953539",
        "head_after": "reported_in_final_response_after_commit",
        "pushed": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "trading_runtime_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "canonical_packets_mutated": False,
        "market_action_guidance_generated": False,
        "probability_ev_edge_confidence_generated": False,
        "side_selection_generated": False,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "draft_capture_created": capture_written,
        "capture_status": CAPTURE_STATUS,
        "operator_review_required": True,
        "manual_capture_validator_passed": validator_passed,
        "source_005_ingest_reran": pipeline.get("real_ingested_template_count") is not None,
        "source_006_readiness_reran": pipeline.get("future_live_002_allowed") is not None,
        "real_ingested_template_count_after": pipeline.get("real_ingested_template_count"),
        "draft_ingested_template_count_after": pipeline.get("draft_ingested_template_count"),
        "ready_ingested_template_count_after": pipeline.get("ready_ingested_template_count"),
        "future_live_002_allowed": pipeline.get("future_live_002_allowed"),
        "source_quality_observation_candidate_created": capture_written,
        "tests_run": [],
        "files_created": result["files_written"],
        "files_modified": [],
        "next_recommended_action": (
            "PMBOT-SOURCE-009C-ESPORTS-OPERATOR-REVIEW-SURFACE-AND-PAPERLIVE-PREPARATION"
        ),
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_docs_markdown(result):
    return "\n".join(
        [
            "# PMBOT SOURCE-009B Esports Draft Capture Autofill From Read-Only Candidate",
            "",
            "SOURCE-009B is local-only. It consumes stored SOURCE-009A public read-only candidate artifacts and creates a manual source capture draft for market 1987056.",
            "",
            "## Outcome",
            "",
            f"- market_id: {result['market_id']}",
            f"- market_class: {result['market_class']}",
            f"- draft_capture_created: {str(result['draft_capture_created']).lower()}",
            f"- capture_status: {result['capture_status']}",
            "- operator_review_required: true",
            f"- real_ingested_template_count_after: {result['real_ingested_template_count_after']}",
            f"- draft_ingested_template_count_after: {result['draft_ingested_template_count_after']}",
            f"- ready_ingested_template_count_after: {result['ready_ingested_template_count_after']}",
            f"- future_live_002_allowed: {str(result['future_live_002_allowed']).lower() if result['future_live_002_allowed'] is not None else 'null'}",
            "",
            "## Pipeline",
            "",
            "- SOURCE-009A read-only artifacts are copied into a SOURCE-004-compatible manual capture draft.",
            "- SOURCE-005 ingest can include the draft only with `--include-drafts`.",
            "- SOURCE-006 readiness remains blocked from future live approval while captures are draft-only.",
            "- ready_for_local_review is not auto-set.",
            "",
            "## Safety Boundary",
            "",
            "- no orders",
            "- no recommendations",
            "- no side choice",
            "- no probability, EV, edge, or confidence score",
            "- no OpenRouter calls",
            "- no Polymarket API calls in SOURCE-009B",
            "- no external network calls",
            "- no queue, runtime, dispatcher, background, browser, wallet, or order authority",
            "",
        ]
    )


def write_autofill_artifacts(root=ROOT):
    packet = build_manual_capture_packet(root=root)
    surface = build_operator_review_surface(root=root)
    observation = build_source_quality_observation_candidate(root=root)
    result = build_autofill_result(root=root, dry_run=False, capture_written=True)
    docs_result = build_docs_result(root=root, dry_run=False, capture_written=True)

    _write_json(TARGET_CAPTURE_JSON_PATH, packet, root=root)
    _write_text(TARGET_CAPTURE_MD_PATH, render_capture_markdown(packet), root=root)
    _write_json(AUTOFILL_RESULT_JSON_PATH, result, root=root)
    _write_text(AUTOFILL_RESULT_MD_PATH, render_autofill_result_markdown(result), root=root)
    _write_json(OPERATOR_SURFACE_JSON_PATH, surface, root=root)
    _write_text(
        OPERATOR_SURFACE_MD_PATH,
        render_operator_review_surface_markdown(surface),
        root=root,
    )
    _write_json(SOURCE_QUALITY_OBSERVATION_JSON_PATH, observation, root=root)
    _write_text(
        SOURCE_QUALITY_OBSERVATION_MD_PATH,
        render_source_quality_observation_markdown(observation),
        root=root,
    )
    _write_json(DOC_RESULT_JSON_PATH, docs_result, root=root)
    _write_text(DOC_RESULT_MD_PATH, render_docs_markdown(docs_result), root=root)
    return result


def build_summary_only(root=ROOT):
    result = _load_optional_json(AUTOFILL_RESULT_JSON_PATH, root=root)
    capture = _load_optional_json(TARGET_CAPTURE_JSON_PATH, root=root)
    pipeline = _current_pipeline_snapshot(root=root)
    return {
        "schema_version": "esports_capture_autofill_summary_009b.v1",
        "task_id": TASK_ID,
        "status": "summary_only",
        "capture_exists": capture is not None,
        "result_exists": result is not None,
        "market_id": MARKET_ID,
        "market_class": MARKET_CLASS,
        "capture_status": (capture or {}).get("capture_status"),
        "source_capture_status": (capture or {}).get("source_capture_status"),
        "operator_review_required": (capture or {}).get("operator_review_required", True),
        "real_ingested_template_count": pipeline.get("real_ingested_template_count"),
        "draft_ingested_template_count": pipeline.get("draft_ingested_template_count"),
        "ready_ingested_template_count": pipeline.get("ready_ingested_template_count"),
        "future_live_002_allowed": pipeline.get("future_live_002_allowed"),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.summary_only:
        payload = build_summary_only(ROOT)
    elif args.write:
        payload = write_autofill_artifacts(ROOT)
    else:
        payload = build_autofill_result(ROOT, dry_run=True, capture_written=False)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
