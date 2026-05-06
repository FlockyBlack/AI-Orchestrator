import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import evaluate_manual_llm_review_quality_gate as quality_gate  # noqa: E402
from pm_bot.llm import export_manual_llm_prompt as prompt_exporter  # noqa: E402
from pm_bot.llm import validate_llm_analysis_artifacts as validator  # noqa: E402
from pm_bot.llm import validate_manual_llm_paste_in_review as manual_review  # noqa: E402


TASK_ID = "PMBOT-LLM-008-REAL-LOCAL-MARKET-PACKET-TRIAL"
CONTRACT_VERSION = "real_local_market_llm_trial_contract.v1"
TRIAL_VERSION = "real_local_market_llm_trial.v1"
TRIAL_ID = "pmbot-llm-008-real-local-market-packet-trial"
DETERMINISTIC_GENERATED_AT = "deterministic-real-local-market-llm-trial.v1"
DETERMINISTIC_PACKET_GENERATED_AT = "deterministic-real-local-market-llm-trial-packet.v1"
TRIAL_PACKET_SOURCE_TYPE = "real_local_market_artifact"
NO_SOURCE_PACKET_SOURCE_TYPE = "no_suitable_real_local_market_artifact"

DEFAULT_OUT_PACKET_PATH = validator.LLM_DIR / "real_local_market_llm_trial_packet.v1.json"
DEFAULT_OUT_PROMPT_PATH = validator.LLM_DIR / "real_local_market_llm_trial_prompt.v1.md"
DEFAULT_RESPONSE_PATH = validator.LLM_DIR / "real_local_market_llm_trial_response_example.v1.json"
DEFAULT_OUT_JSON_PATH = validator.LLM_DIR / "real_local_market_llm_trial.v1.json"
DEFAULT_OUT_MD_PATH = validator.LLM_DIR / "real_local_market_llm_trial.v1.md"

QUALITY_PASS_STATUSES = {"quality_passed", "quality_passed_with_warnings"}

SOURCE_CANDIDATES = (
    {
        "path": "pm_bot/workbench/operator_review_pack.v1.json",
        "artifact_type": "operator_review_pack",
        "selector": "operator_review_pack",
    },
    {
        "path": "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json",
        "artifact_type": "selected_ingest_final_dossier_draft",
        "selector": "final_dossier_draft",
    },
    {
        "path": "pm_bot/research/final_dossier_drafts.v1.json",
        "artifact_type": "final_dossier_draft",
        "selector": "final_dossier_draft",
    },
    {
        "path": "pm_bot/research/selected_ingest_research_packet_stubs.v1.json",
        "artifact_type": "selected_ingest_research_packet_stub",
        "selector": "research_packet_stub",
    },
    {
        "path": "pm_bot/paper/real_market_triage_report.v1.json",
        "artifact_type": "local_snapshot_market_summary",
        "selector": "real_market_triage_report",
    },
)

SAFETY_FLAGS = {
    **quality_gate.SAFETY_FLAGS,
    "runtime_wiring": False,
    "network_api": False,
    "llm_api": False,
    "browser_automation": False,
    "prompt_automation": False,
    "credentials_or_wallet": False,
    "real_orders_or_live_trading": False,
    "autonomous_paper_orders": False,
    "probability_ev_scoring_or_edge": False,
    "side_recommendations": False,
    "market_decision_logic": False,
    "truth_evaluation": False,
    "dispatcher_or_run_codex_changed": False,
}

SAFETY_CONSTRAINTS = {
    "offline_only": True,
    "local_files_only": True,
    "manual_review_only": True,
    "no_network_calls": True,
    "no_llm_api_calls": True,
    "no_credentials": True,
    "no_wallet_or_key_material": True,
    "no_trading_endpoints": True,
    "no_real_orders": True,
    "no_live_trading": True,
    "no_autonomous_paper_orders": True,
    "no_outcome_estimates": True,
    "no_value_or_advantage_scoring": True,
    "no_side_selection": True,
    "no_market_decisions": True,
    "no_runtime_wiring": True,
    "no_dispatcher_changes": True,
    "no_prompt_automation": True,
}

OPERATOR_TRIAL_STEPS = [
    "Open pm_bot/llm/real_local_market_llm_trial_prompt.v1.md.",
    "Paste into ChatGPT, Claude, or Gemini manually.",
    "Ask for strict JSON only, with no Markdown wrapper or extra prose.",
    "Save the response to a local JSON file matching llm_analysis_response_schema.v1.json.",
    (
        "Rerun python pm_bot/llm/export_real_local_market_llm_trial.py "
        "--response path/to/manual_response.json."
    ),
    "Review accepted/rejected and quality gate status in the JSON, Markdown, or workbench surface.",
]

BOUNDARY_NOTICE = (
    "No API calls, LLM API calls, browser automation, prompt automation, runtime integration, "
    "live trading, real orders, autonomous paper orders, trading advice, truth evaluation, "
    "outcome estimates, value scoring, advantage claims, side selection, or market decisions."
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export a deterministic offline/manual LLM trial from a real local PMBOT market artifact."
    )
    parser.add_argument("--out-packet", default=str(DEFAULT_OUT_PACKET_PATH.relative_to(ROOT)))
    parser.add_argument("--out-prompt", default=str(DEFAULT_OUT_PROMPT_PATH.relative_to(ROOT)))
    parser.add_argument("--response", default=str(DEFAULT_RESPONSE_PATH.relative_to(ROOT)))
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON_PATH.relative_to(ROOT)))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD_PATH.relative_to(ROOT)))
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path, root=ROOT):
    resolved = _resolve_path(path, root)
    return json.loads(resolved.read_text(encoding="utf-8"))


def _first_text(value, *keys):
    if not isinstance(value, dict):
        return ""
    for key in keys:
        item = value.get(key)
        if isinstance(item, str) and item.strip():
            return item.strip()
    return ""


def _safe_list(value):
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _source_type_for_evidence(index, text):
    lowered = text.lower()
    if "official" in lowered or "rule" in lowered:
        return "official_source_reference"
    if "news" in lowered:
        return "news_source_reference"
    if "operator" in lowered:
        return "operator_artifact"
    if index == 0:
        return "operator_artifact"
    return "manual_note"


def _build_evidence_items(draft, source_path):
    raw_items = _safe_list(draft.get("evidence_summary_by_source"))
    items = []
    for index, text in enumerate(raw_items, start=1):
        items.append(
            {
                "evidence_id": f"evidence-real-local-market-824952-{index:03d}",
                "claim_summary": text,
                "source_reference": source_path,
                "source_type": _source_type_for_evidence(index - 1, text),
                "relevance_note": "This local dossier field gives the operator source-coverage context for manual review.",
                "limitation_note": "The trial does not fetch, refresh, resolve, or verify the referenced source.",
            }
        )

    for index, text in enumerate(_safe_list(draft.get("uncertainty_register")), start=len(items) + 1):
        items.append(
            {
                "evidence_id": f"evidence-real-local-market-824952-{index:03d}",
                "claim_summary": text,
                "source_reference": source_path,
                "source_type": "manual_note",
                "relevance_note": "This local uncertainty note keeps unresolved review context visible.",
                "limitation_note": "The note is not a source check, truth check, estimate, score, or decision.",
            }
        )

    if items:
        return items
    return [
        {
            "evidence_id": "evidence-real-local-market-824952-001",
            "claim_summary": "The selected local artifact has market context but no structured evidence list.",
            "source_reference": source_path,
            "source_type": "operator_artifact",
            "relevance_note": "The source artifact still provides the packet market context.",
            "limitation_note": "Evidence details require separate manual review of the local artifact.",
        }
    ]


def _draft_candidate_from_payload(payload, source_path, artifact_type):
    drafts = payload.get("final_dossier_drafts") if isinstance(payload, dict) else None
    if not isinstance(drafts, list) or not drafts:
        return None, "artifact has no final_dossier_drafts list"

    for draft in drafts:
        if not isinstance(draft, dict):
            continue
        market_id = _first_text(draft, "market_id")
        title = _first_text(draft, "title_question", "market_title", "market_question")
        rules = _first_text(draft, "resolution_criteria_summary", "resolution_criteria", "resolution_rules_summary")
        if market_id and title and rules:
            completed_sections = []
            sections = draft.get("final_draft_sections")
            if isinstance(sections, dict):
                completed_sections = sorted(str(key) for key in sections.keys())
            if not completed_sections:
                completed_sections = [
                    "market_overview",
                    "resolution_rules",
                    "evidence_inventory",
                    "uncertainty_notes",
                    "source_coverage_notes",
                ]
            return (
                {
                    "source_artifact_path": source_path,
                    "source_artifact_type": artifact_type,
                    "source_selection_reason": (
                        "Selected because it is an existing local final dossier draft with market_id, "
                        "title/question text, resolution context, evidence notes, and safety-friendly manual review notes."
                    ),
                    "market_id": market_id,
                    "market_title": title,
                    "question_text": title,
                    "market_status": "unknown",
                    "public_resolution_context": rules,
                    "resolution_rules_summary": rules,
                    "research_status": "manual_review_ready",
                    "research_summary": (
                        f"Local {artifact_type} artifact records market context, resolution notes, "
                        "source coverage placeholders, uncertainty notes, and human-review notes for manual review only."
                    ),
                    "completed_sections": completed_sections,
                    "open_questions": _safe_list(draft.get("open_questions")),
                    "market_context_notes": _first_text(draft, "market_context_notes"),
                    "resolution_criteria_notes": _first_text(draft, "resolution_criteria_notes"),
                    "missing_information_review": _first_text(draft, "missing_information_review"),
                    "operator_review_notes": _first_text(draft, "operator_review_notes"),
                    "human_review_notes": _first_text(draft, "human_review_notes"),
                    "evidence_summary": _build_evidence_items(draft, source_path),
                },
                "",
            )

    return None, "artifact has dossier drafts but none with market_id, title/question, and resolution context"


def _operator_pack_candidate_from_payload(payload, source_path, artifact_type):
    if not isinstance(payload, dict):
        return None, "artifact is not a JSON object"
    known_ids = []
    dashboard = payload.get("dashboard_state_summary")
    if isinstance(dashboard, dict):
        known_ids.extend(_safe_list(dashboard.get("known_market_ids")))
    portfolio = payload.get("portfolio_accounting_summary")
    if isinstance(portfolio, dict):
        known_ids.extend(_safe_list(portfolio.get("accepted_accounting_market_ids")))
    if known_ids:
        return (
            None,
            (
                "operator review pack has local market ids but not enough standalone title/question "
                "and resolution context for the LLM packet schema"
            ),
        )
    return None, "operator review pack has no suitable market context section"


def _research_packet_stub_candidate_from_payload(payload, source_path, artifact_type):
    if not isinstance(payload, dict):
        return None, "artifact is not a JSON object"
    packets = payload.get("research_packet_stubs")
    if not isinstance(packets, list):
        packets = payload.get("packets")
    if not isinstance(packets, list) or not packets:
        return None, "artifact has no research packet list"
    return None, "research packet stub exists but final dossier draft source is preferred when available"


def _triage_candidate_from_payload(payload, source_path, artifact_type):
    if not isinstance(payload, dict):
        return None, "artifact is not a JSON object"
    candidates = payload.get("supported_candidates")
    if not isinstance(candidates, list) or not candidates:
        return None, "triage report has no supported local market candidates"
    return None, "triage report is lower-preference because a final dossier draft source is available"


def _candidate_from_payload(payload, spec):
    selector = spec["selector"]
    path = spec["path"]
    artifact_type = spec["artifact_type"]
    if selector == "operator_review_pack":
        return _operator_pack_candidate_from_payload(payload, path, artifact_type)
    if selector == "final_dossier_draft":
        return _draft_candidate_from_payload(payload, path, artifact_type)
    if selector == "research_packet_stub":
        return _research_packet_stub_candidate_from_payload(payload, path, artifact_type)
    if selector == "real_market_triage_report":
        return _triage_candidate_from_payload(payload, path, artifact_type)
    return None, "unknown selector"


def select_real_local_market_artifact(root=ROOT, source_candidates=SOURCE_CANDIDATES):
    inspected = []
    for rank, spec in enumerate(source_candidates, start=1):
        path = spec["path"]
        resolved = _resolve_path(path, root)
        item = {
            "path": path,
            "artifact_type": spec["artifact_type"],
            "preference_rank": rank,
            "present": resolved.exists(),
            "parse_status": "not_read",
            "suitable": False,
            "reason": "",
        }
        if not resolved.exists():
            item["reason"] = "artifact not found"
            inspected.append(item)
            continue
        try:
            payload = _load_json(path, root)
        except json.JSONDecodeError as exc:
            item["parse_status"] = "malformed"
            item["reason"] = f"JSON malformed at line {exc.lineno}, column {exc.colno}"
            inspected.append(item)
            continue
        except OSError as exc:
            item["parse_status"] = "load_error"
            item["reason"] = f"artifact could not be loaded: {exc.__class__.__name__}"
            inspected.append(item)
            continue

        item["parse_status"] = "parsed"
        candidate, reason = _candidate_from_payload(payload, spec)
        if candidate:
            item["suitable"] = True
            item["reason"] = reason or candidate["source_selection_reason"]
            inspected.append(item)
            return {
                "selection_status": "selected",
                "trial_packet_source_type": TRIAL_PACKET_SOURCE_TYPE,
                "used_example_packet_fallback": False,
                "fallback_reason": "",
                "source_artifact_path": path,
                "source_artifact_type": spec["artifact_type"],
                "source_preference_rank": rank,
                "market_id": candidate["market_id"],
                "market_title": candidate["market_title"],
                "candidate": candidate,
                "inspected_artifacts": inspected,
                "warnings": [],
                "errors": [],
            }
        item["reason"] = reason
        inspected.append(item)

    return {
        "selection_status": "not_found",
        "trial_packet_source_type": NO_SOURCE_PACKET_SOURCE_TYPE,
        "used_example_packet_fallback": False,
        "fallback_reason": "No suitable real local PMBOT market artifact was found; example packet fallback is disabled.",
        "source_artifact_path": "",
        "source_artifact_type": "",
        "source_preference_rank": None,
        "market_id": "",
        "market_title": "",
        "candidate": None,
        "inspected_artifacts": inspected,
        "warnings": [
            {
                "code": "no_suitable_real_local_market_artifact",
                "path": "source_selection",
                "message": "No suitable real local PMBOT market artifact was found; not falling back to example packet.",
            }
        ],
        "errors": [],
    }


def build_packet_from_selection(selection):
    candidate = selection.get("candidate")
    if not candidate:
        return None
    source_path = candidate["source_artifact_path"]
    market_id = candidate["market_id"]
    return {
        "contract_version": "llm_analysis_packet.v1",
        "packet_id": f"llm-analysis-packet-real-local-market-{market_id}",
        "generated_at": DETERMINISTIC_PACKET_GENERATED_AT,
        "source_artifacts": [
            {
                "artifact_type": candidate["source_artifact_type"],
                "path": source_path,
                "description": (
                    "Existing local PMBOT market/research artifact selected for the real-local-market "
                    "manual LLM trial; safe summary fields only are copied into this packet."
                ),
                "sanitization_status": "safe_public_or_local_artifact_reference_only",
            }
        ],
        "market_context": {
            "market_id": market_id,
            "market_title": candidate["market_title"],
            "market_status": candidate["market_status"],
            "public_resolution_context": candidate["public_resolution_context"],
            "outcome_labels": ["Yes", "No"],
        },
        "normalized_market_summary": {
            "question_text": candidate["question_text"],
            "status": candidate["market_status"],
            "outcome_labels": ["Yes", "No"],
            "resolution_rules_summary": candidate["resolution_rules_summary"],
            "data_freshness_note": (
                "Derived only from an existing local PMBOT artifact; no live data, API, or network refresh is used."
            ),
            "excluded_fields_note": (
                "Source numeric market fields and accounting fields are intentionally omitted. No credentials, "
                "wallet data, executable commands, endpoint data, order placement fields, outcome estimates, "
                "value metrics, or side selection requests are included."
            ),
        },
        "research_summary": {
            "research_status": candidate["research_status"],
            "summary": candidate["research_summary"],
            "completed_sections": candidate["completed_sections"],
            "open_questions": candidate["open_questions"],
        },
        "evidence_summary": candidate["evidence_summary"],
        "operator_questions": [
            "Which source gaps should the operator review first?",
            "Which local claims need source-date verification?",
            "Where do local artifact summaries remain ambiguous or incomplete?",
        ],
        "known_limitations": [
            "The packet is derived from a local artifact only and does not fetch or refresh external data.",
            "The packet omits numeric market fields and accounting values to stay within manual review boundaries.",
            "The packet is a review aid only and does not evaluate truth, select outcomes, or authorize action.",
        ],
        "forbidden_outputs": list(validator.REQUIRED_FORBIDDEN_OUTPUTS),
        "required_response_sections": list(validator.ALLOWED_RESPONSE_SECTIONS),
        "safety_constraints": dict(SAFETY_CONSTRAINTS),
    }


def _stage_messages(stage, messages):
    staged = []
    for message in messages:
        item = {"stage": stage, **message}
        staged.append(item)
    return sorted(
        staged,
        key=lambda item: (
            item.get("stage", ""),
            item.get("artifact", ""),
            item.get("check", ""),
            item.get("path", ""),
            item.get("code", ""),
            item.get("message", ""),
        ),
    )


def _safe_prompt_export(packet_path, out_prompt_path):
    try:
        return prompt_exporter.export_manual_prompt(packet_path, out_prompt_path)
    except prompt_exporter.ManualPromptExportError as exc:
        return {
            "status": "rejected",
            "manual_prompt_version": prompt_exporter.MANUAL_PROMPT_VERSION,
            "generated_at": prompt_exporter.DETERMINISTIC_GENERATED_AT,
            "packet_path": _display_path(_resolve_path(packet_path)),
            "out_md_path": _display_path(_resolve_path(out_prompt_path)),
            "errors": exc.errors,
            "warnings": [],
            "safety_flags": dict(SAFETY_FLAGS),
        }


def _packet_validation_from(review_result):
    packet_validation = review_result.get("packet_validation")
    if isinstance(packet_validation, dict):
        return packet_validation
    return {"status": "rejected", "errors": [], "warnings": []}


def _response_validation_from(review_result):
    response_validation = review_result.get("response_validation")
    if isinstance(response_validation, dict):
        return response_validation
    return {"status": "rejected", "errors": [], "warnings": []}


def _quality_gate_summary(result):
    return {
        "validation_status": result["validation_status"],
        "base_validator_status": result["base_validator_status"],
        "quality_counts": result["quality_counts"],
        "required_sections_status": result["required_sections_check"]["status"],
        "minimum_content_status": result["minimum_content_check"]["status"],
        "generic_or_placeholder_text_status": result["generic_or_placeholder_text_check"]["status"],
        "unsafe_certainty_status": result["unsafe_certainty_check"]["status"],
        "forbidden_content_status": result["forbidden_content_check"]["status"],
        "manual_review_input_status": result["manual_review_input_check"]["status"],
        "next_safe_operator_action": result["next_safe_operator_action"],
    }


def _manual_review_summary(result):
    return {
        "validation_status": result["validation_status"],
        "accepted_sections": result["accepted_sections"],
        "missing_sections": result["missing_sections"],
        "forbidden_content_detected": result["forbidden_content_detected"],
        "next_safe_operator_action": result["next_safe_operator_action"],
    }


def _source_artifacts(selection, packet_path, prompt_path, response_path, review_result, gate_result):
    declared = []
    review_source = review_result.get("source_artifacts")
    if isinstance(review_source, dict):
        declared = review_source.get("packet_declared_source_artifacts", [])
    return {
        "trial_packet_source_type": selection["trial_packet_source_type"],
        "source_artifact_path": selection["source_artifact_path"],
        "market_id": selection["market_id"],
        "packet_declared_source_artifacts": declared,
        "manual_artifacts": {
            "packet": _display_path(packet_path),
            "prompt": _display_path(prompt_path),
            "response": _display_path(response_path),
        },
        "component_artifacts": {
            "manual_review_flow": _display_path(validator.LLM_DIR / "validate_manual_llm_paste_in_review.py"),
            "quality_gate": _display_path(validator.LLM_DIR / "evaluate_manual_llm_review_quality_gate.py"),
        },
        "contract_artifacts": [
            _display_path(validator.PACKET_SCHEMA_PATH),
            _display_path(validator.RESPONSE_SCHEMA_PATH),
            _display_path(validator.LLM_DIR / "validate_llm_analysis_artifacts.py"),
        ],
        "quality_gate_source_artifacts": gate_result.get("source_artifacts", {}),
    }


def _next_safe_operator_action(validation_status, quality_status):
    if validation_status == "accepted" and quality_status in QUALITY_PASS_STATUSES:
        return (
            "Replace only the response path with a real manually saved JSON response when ready, "
            "then rerun the exporter and inspect the local result artifacts."
        )
    if validation_status == "blocked":
        return (
            "Add or regenerate a safe local PMBOT market/research/operator artifact with market_id, "
            "title/question text, and resolution context; do not use the example packet as a real source."
        )
    return (
        "Inspect the local validation and quality errors, edit only the local packet or response JSON, "
        "and rerun the exporter."
    )


def _blocked_result(selection, packet_path, prompt_path, response_path):
    warnings = _stage_messages("source_selection", selection["warnings"])
    return {
        "contract_version": CONTRACT_VERSION,
        "trial_version": TRIAL_VERSION,
        "trial_id": TRIAL_ID,
        "task_id": TASK_ID,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "trial_packet_source_type": selection["trial_packet_source_type"],
        "source_artifact_path": "",
        "market_id": "",
        "packet_path": _display_path(packet_path),
        "prompt_path": _display_path(prompt_path),
        "response_path": _display_path(response_path),
        "manual_review_status": "not_run",
        "quality_gate_status": "not_run",
        "validation_status": "blocked",
        "quality_status": "not_run",
        "errors": [],
        "warnings": warnings,
        "safety_flags": dict(SAFETY_FLAGS),
        "operator_trial_steps": list(OPERATOR_TRIAL_STEPS),
        "next_safe_operator_action": _next_safe_operator_action("blocked", "not_run"),
        "source_artifacts": {
            "trial_packet_source_type": selection["trial_packet_source_type"],
            "source_artifact_path": "",
            "market_id": "",
            "inspected_artifacts": selection["inspected_artifacts"],
        },
        "source_selection": selection,
        "prompt_export": {"status": "not_run"},
        "packet_validation": {"status": "not_run", "errors": [], "warnings": []},
        "response_validation": {"status": "not_run", "errors": [], "warnings": []},
        "manual_review": {"validation_status": "not_run"},
        "quality_gate": {"validation_status": "not_run"},
        "safety_boundary": BOUNDARY_NOTICE,
    }


def build_trial_result(
    out_packet_path=DEFAULT_OUT_PACKET_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    out_prompt_path=DEFAULT_OUT_PROMPT_PATH,
    root=ROOT,
):
    out_packet_path = _resolve_path(out_packet_path, root)
    response_path = _resolve_path(response_path, root)
    out_prompt_path = _resolve_path(out_prompt_path, root)

    selection = select_real_local_market_artifact(root)
    if selection["selection_status"] != "selected":
        return _blocked_result(selection, out_packet_path, out_prompt_path, response_path)

    packet_payload = build_packet_from_selection(selection)
    _write_json(out_packet_path, packet_payload)

    prompt_result = _safe_prompt_export(out_packet_path, out_prompt_path)
    review_result = manual_review.build_manual_review(out_packet_path, response_path, out_prompt_path)
    gate_result = quality_gate.build_quality_gate(out_packet_path, response_path, None)

    packet_validation = _packet_validation_from(review_result)
    response_validation = _response_validation_from(review_result)
    manual_review_status = review_result["validation_status"]
    quality_gate_status = gate_result["validation_status"]
    validation_status = (
        "accepted"
        if prompt_result["status"] == "accepted"
        and packet_validation["status"] == "accepted"
        and response_validation["status"] == "accepted"
        and manual_review_status == "accepted"
        and quality_gate_status in QUALITY_PASS_STATUSES
        else "rejected"
    )

    errors = []
    warnings = []
    errors.extend(_stage_messages("prompt_export", prompt_result.get("errors", [])))
    warnings.extend(_stage_messages("prompt_export", prompt_result.get("warnings", [])))
    errors.extend(_stage_messages("manual_review", review_result["errors"]))
    warnings.extend(_stage_messages("manual_review", review_result["warnings"]))
    errors.extend(_stage_messages("quality_gate", gate_result["errors"]))
    warnings.extend(_stage_messages("quality_gate", gate_result["warnings"]))
    errors = sorted(
        errors,
        key=lambda item: (
            item.get("stage", ""),
            item.get("artifact", ""),
            item.get("check", ""),
            item.get("path", ""),
            item.get("code", ""),
            item.get("message", ""),
        ),
    )
    warnings = sorted(
        warnings,
        key=lambda item: (
            item.get("stage", ""),
            item.get("artifact", ""),
            item.get("check", ""),
            item.get("path", ""),
            item.get("code", ""),
            item.get("message", ""),
        ),
    )

    return {
        "contract_version": CONTRACT_VERSION,
        "trial_version": TRIAL_VERSION,
        "trial_id": TRIAL_ID,
        "task_id": TASK_ID,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "trial_packet_source_type": selection["trial_packet_source_type"],
        "source_artifact_path": selection["source_artifact_path"],
        "market_id": selection["market_id"],
        "packet_path": _display_path(out_packet_path),
        "prompt_path": _display_path(out_prompt_path),
        "response_path": _display_path(response_path),
        "manual_review_status": manual_review_status,
        "quality_gate_status": quality_gate_status,
        "validation_status": validation_status,
        "quality_status": quality_gate_status,
        "errors": errors,
        "warnings": warnings,
        "safety_flags": dict(SAFETY_FLAGS),
        "operator_trial_steps": list(OPERATOR_TRIAL_STEPS),
        "next_safe_operator_action": _next_safe_operator_action(validation_status, quality_gate_status),
        "source_artifacts": _source_artifacts(
            selection, out_packet_path, out_prompt_path, response_path, review_result, gate_result
        ),
        "source_selection": {
            key: value for key, value in selection.items() if key != "candidate"
        },
        "prompt_export": {
            "status": prompt_result["status"],
            "manual_prompt_version": prompt_result["manual_prompt_version"],
            "generated_at": prompt_result["generated_at"],
            "out_md_path": prompt_result["out_md_path"],
        },
        "packet_validation": packet_validation,
        "response_validation": response_validation,
        "manual_review": _manual_review_summary(review_result),
        "quality_gate": _quality_gate_summary(gate_result),
        "safety_boundary": BOUNDARY_NOTICE,
    }


def _format_messages(messages):
    if not messages:
        return ["- none"]
    lines = []
    for message in messages:
        stage = f"[{message.get('stage', 'trial')}] "
        artifact = f"{message.get('artifact')}: " if message.get("artifact") else ""
        check = f"{message.get('check')}: " if message.get("check") else ""
        lines.append(
            f"- {stage}{artifact}{check}{message.get('path', '')}: "
            f"{message.get('code', 'message')} - {message.get('message', '')}"
        )
    return lines


def render_markdown_report(result):
    source_path = result["source_artifact_path"] or "not selected"
    market_id = result["market_id"] or "not available"
    lines = [
        "# PMBOT Real Local Market LLM Trial v1",
        "",
        f"- Trial status: {result['validation_status']}",
        f"- Packet source: {result['trial_packet_source_type']}",
        f"- Source artifact: {source_path}",
        f"- Market ID: {market_id}",
        f"- Packet path: {result['packet_path']}",
        f"- Prompt path: {result['prompt_path']}",
        f"- Response path: {result['response_path']}",
        f"- Manual review status: {result['manual_review_status']}",
        f"- Quality gate status: {result['quality_gate_status']}",
        "",
        "## Boundary",
        "",
        BOUNDARY_NOTICE,
        "",
        "## Errors",
        "",
        *_format_messages(result["errors"]),
        "",
        "## Warnings",
        "",
        *_format_messages(result["warnings"]),
        "",
        "## Manual Operator Steps For A Real Trial",
        "",
    ]
    for index, step in enumerate(OPERATOR_TRIAL_STEPS, start=1):
        lines.append(f"{index}. {step}")
    lines.extend(
        [
            "",
            "## Current Example Response Status",
            "",
            f"- Packet validation: {result['packet_validation']['status']}",
            f"- Response validation: {result['response_validation']['status']}",
            f"- Manual review: {result['manual_review_status']}",
            f"- Quality gate: {result['quality_gate_status']}",
            "",
            "## Source Notes",
            "",
            (
                "The packet is built from an existing local PMBOT market/research artifact and is labeled "
                "`real_local_market_artifact` when a suitable source is selected. It does not use "
                "`example_llm_analysis_packet.v1.json` as the market source."
            ),
            "",
            "## Next Safe Operator Action",
            "",
            result["next_safe_operator_action"],
            "",
        ]
    )
    return "\n".join(lines)


def export_trial(
    out_packet_path=DEFAULT_OUT_PACKET_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    out_json_path=DEFAULT_OUT_JSON_PATH,
    out_md_path=DEFAULT_OUT_MD_PATH,
    out_prompt_path=DEFAULT_OUT_PROMPT_PATH,
):
    result = build_trial_result(out_packet_path, response_path, out_prompt_path)
    out_json_path = _resolve_path(out_json_path)
    out_md_path = _resolve_path(out_md_path)
    _write_json(out_json_path, result)
    _write_text(out_md_path, render_markdown_report(result))
    return result


def main(argv):
    args = _parse_args(argv)
    result = export_trial(args.out_packet, args.response, args.out_json, args.out_md, args.out_prompt)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["validation_status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
