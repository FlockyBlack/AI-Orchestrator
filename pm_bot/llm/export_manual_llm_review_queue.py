import argparse
import json
import re
import sys
from json import JSONDecodeError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import evaluate_manual_llm_review_quality_gate as quality_gate  # noqa: E402
from pm_bot.llm import validate_llm_analysis_artifacts as validator  # noqa: E402


TASK_ID = "PMBOT-LLM-013-MULTI-MARKET-MANUAL-LLM-REVIEW-QUEUE"
QUEUE_SCHEMA_VERSION = "manual_llm_review_queue.v1"
GENERATED_BY = "pm_bot/llm/export_manual_llm_review_queue.py"
DETERMINISTIC_GENERATED_AT = "deterministic-manual-llm-review-queue.v1"

READY_FOR_PROMPT_EXPORT = "ready_for_manual_prompt_export"
WAITING_FOR_RESPONSE = "waiting_for_operator_pasted_response"
RESPONSE_ACCEPTED = "response_accepted_for_operator_review"
RESPONSE_REJECTED = "response_rejected_needs_operator_fix"
BLOCKED_MISSING_PACKET = "blocked_missing_packet"
BLOCKED_INVALID_ARTIFACT = "blocked_invalid_artifact"

QUEUE_STATUSES = (
    READY_FOR_PROMPT_EXPORT,
    WAITING_FOR_RESPONSE,
    RESPONSE_ACCEPTED,
    RESPONSE_REJECTED,
    BLOCKED_MISSING_PACKET,
    BLOCKED_INVALID_ARTIFACT,
)

NOT_AVAILABLE = "not_available"
NOT_RUN = "not_run"

DEFAULT_TRIAL_PATH = "pm_bot/llm/real_local_market_llm_trial.v1.json"
DEFAULT_PACKET_PATH = "pm_bot/llm/real_local_market_llm_trial_packet.v1.json"
DEFAULT_PROMPT_PATH = "pm_bot/llm/real_local_market_llm_trial_prompt.v1.md"
DEFAULT_OPERATOR_RESPONSE_PATH = "pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json"
DEFAULT_ACTUAL_TRIAL_PATH = "pm_bot/llm/actual_manual_llm_response_trial.v1.json"
DEFAULT_SURFACE_REVIEW_PATH = "pm_bot/llm/actual_manual_llm_response_surface_operator_review.v1.json"
DEFAULT_SELECTED_DOSSIERS_PATH = "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json"

DEFAULT_OUT_JSON = "pm_bot/llm/manual_llm_review_queue.v1.json"
DEFAULT_OUT_MD = "pm_bot/llm/manual_llm_review_queue.v1.md"
DEFAULT_EXPECTED_JSON = "pm_bot/llm/expected_manual_llm_review_queue.v1.json"
DEFAULT_DOC_RESULT_JSON = "docs/PMBOT_LLM_013_RESULT.json"
DEFAULT_DOC_MD = "docs/PMBOT_LLM_013_MULTI_MARKET_MANUAL_LLM_REVIEW_QUEUE.md"

SAFETY_FLAGS = {
    "offline_manual_only": True,
    "not_truth_source": True,
    "not_trading_advice": True,
    "not_execution_authority": True,
    "deterministic": True,
    "local_file_reads_only": True,
    "llm_api": False,
    "network_api": False,
    "browser_automation": False,
    "prompt_automation": False,
    "runtime_wiring": False,
    "dispatcher_run_codex_changes": False,
    "credentials_or_wallet": False,
    "real_orders_or_live_trading": False,
    "autonomous_paper_orders": False,
    "probability_ev_scoring_or_edge": False,
    "side_recommendations": False,
    "market_decision_logic": False,
    "truth_evaluation": False,
    "execution_authority": False,
}

NEXT_ACTION_BY_STATUS = {
    READY_FOR_PROMPT_EXPORT: (
        "Export the local manual prompt from the packet, then wait for a human-pasted JSON response."
    ),
    WAITING_FOR_RESPONSE: (
        "Save the human-pasted JSON response locally, then rerun the deterministic local checks."
    ),
    RESPONSE_ACCEPTED: (
        "Review the accepted local response context in the offline operator surface only."
    ),
    RESPONSE_REJECTED: (
        "Correct or replace the local response JSON, then rerun deterministic local checks."
    ),
    BLOCKED_MISSING_PACKET: (
        "Create the local packet through the existing offline packet generator before adding response artifacts."
    ),
    BLOCKED_INVALID_ARTIFACT: (
        "Repair the malformed or rejected local artifact, then rebuild the queue."
    ),
}

FORBIDDEN_STATUS_ACTION_TERMS = {
    "recommend",
    "recommends",
    "recommended",
    "recommendation",
    "recommendations",
    "probability",
    "probabilities",
    "ev",
    "edge",
    "score",
    "scores",
    "scoring",
    "side",
    "buy",
    "sell",
    "hold",
    "enter",
    "exit",
    "trade",
    "trades",
    "trading",
    "order",
    "orders",
    "wallet",
    "execution",
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export the deterministic offline manual LLM review queue."
    )
    parser.add_argument("--out-json", default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", default=DEFAULT_OUT_MD)
    parser.add_argument("--expected-json", default=DEFAULT_EXPECTED_JSON)
    parser.add_argument("--doc-result-json", default=DEFAULT_DOC_RESULT_JSON)
    parser.add_argument("--doc-md", default=DEFAULT_DOC_MD)
    return parser.parse_args(argv)


def _resolve_path(path, root=ROOT):
    if path is None:
        return None
    if isinstance(path, str) and not path.strip():
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(root) / candidate


def _display_path(path, root=ROOT):
    if path is None:
        return ""
    resolved = Path(path).resolve()
    try:
        value = resolved.relative_to(Path(root).resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _safe_dict(value):
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value):
    if isinstance(value, list):
        return value
    return []


def _artifact_check(path, artifact_id, required, root=ROOT, parse_json=True):
    resolved = _resolve_path(path, root)
    display = _display_path(resolved, root)
    status = {
        "artifact_id": artifact_id,
        "path": display,
        "required": required,
        "present": bool(resolved and resolved.exists()),
        "parse_status": "not_applicable" if not parse_json else "not_loaded",
    }
    if resolved is None:
        status["parse_status"] = "not_provided"
        return None, status
    if not resolved.exists():
        status["parse_status"] = "missing" if parse_json else "not_applicable"
        return None, status
    if not parse_json:
        return None, status
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        status["parse_status"] = "parse_failed"
        status["parse_error"] = f"JSONDecodeError:{exc.lineno}:{exc.colno}"
        return None, status
    except OSError as exc:
        status["parse_status"] = "read_failed"
        status["parse_error"] = exc.__class__.__name__
        return None, status
    if not isinstance(payload, dict):
        status["parse_status"] = "top_level_not_object"
        return None, status
    status["parse_status"] = "parsed"
    return payload, status


def _load_json_for_discovery(path, artifact_id, root=ROOT):
    return _artifact_check(path, artifact_id, required=False, root=root, parse_json=True)


def _string_field(payload, key, default=""):
    value = _safe_dict(payload).get(key)
    if isinstance(value, str):
        return value
    return default


def _bool_field(payload, key, default=False):
    value = _safe_dict(payload).get(key)
    if isinstance(value, bool):
        return value
    return default


def _candidate_from_actual_trial(actual_trial_payload):
    actual = _safe_dict(actual_trial_payload)
    if not actual:
        return None
    market_id = _string_field(actual, "market_id")
    if not market_id:
        return None
    return {
        "candidate_id": f"actual_manual_llm_response_trial_{market_id}",
        "candidate_source": "actual_manual_llm_response_trial",
        "market_id": market_id,
        "source_artifact_path": _string_field(actual, "source_artifact_path"),
        "trial_path": _string_field(actual, "trial_path", DEFAULT_TRIAL_PATH),
        "packet_path": _string_field(actual, "packet_path", DEFAULT_PACKET_PATH),
        "prompt_path": _string_field(actual, "prompt_path", DEFAULT_PROMPT_PATH),
        "operator_response_path": _string_field(
            actual,
            "operator_response_path",
            DEFAULT_OPERATOR_RESPONSE_PATH,
        ),
        "actual_trial_path": DEFAULT_ACTUAL_TRIAL_PATH,
        "surface_review_path": DEFAULT_SURFACE_REVIEW_PATH,
    }


def _selected_dossier_discovery(selected_payload):
    selected = _safe_dict(selected_payload)
    selected_market_ids = [str(item) for item in _safe_list(selected.get("selected_market_ids"))]
    final_drafts = [
        item for item in _safe_list(selected.get("final_dossier_drafts")) if isinstance(item, dict)
    ]
    final_draft_market_ids = sorted(
        {str(item.get("market_id")) for item in final_drafts if item.get("market_id")}
    )
    exported_market_ids = [str(item) for item in _safe_list(selected.get("exported_market_ids"))]
    return {
        "selected_ingest_markets_seen": len(selected_market_ids),
        "selected_ingest_market_ids": sorted(selected_market_ids),
        "final_dossier_drafts_seen": len(final_drafts),
        "final_dossier_draft_market_ids": final_draft_market_ids,
        "exported_market_ids": sorted(exported_market_ids),
    }


def discover_default_candidates(root=ROOT):
    actual_payload, actual_status = _load_json_for_discovery(
        DEFAULT_ACTUAL_TRIAL_PATH,
        "actual_manual_llm_response_trial",
        root,
    )
    selected_payload, selected_status = _load_json_for_discovery(
        DEFAULT_SELECTED_DOSSIERS_PATH,
        "selected_ingest_final_dossier_drafts",
        root,
    )
    surface_payload, surface_status = _load_json_for_discovery(
        DEFAULT_SURFACE_REVIEW_PATH,
        "actual_manual_llm_response_surface_operator_review",
        root,
    )

    candidates = []
    actual_candidate = _candidate_from_actual_trial(actual_payload)
    if actual_candidate is not None:
        candidates.append(actual_candidate)

    selected_discovery = _selected_dossier_discovery(selected_payload)
    existing_market_ids = {candidate["market_id"] for candidate in candidates}
    additional_ready_market_ids = [
        market_id
        for market_id in selected_discovery["final_dossier_draft_market_ids"]
        if market_id not in existing_market_ids
    ]

    discovery = {
        "source_artifacts_checked": [
            actual_status,
            selected_status,
            surface_status,
        ],
        "actual_trial_candidate_found": actual_candidate is not None,
        **selected_discovery,
        "candidate_policy": (
            "Only markets with an existing local LLM packet or accepted actual manual response artifact "
            "become queue items."
        ),
        "additional_ready_candidates_found": len(additional_ready_market_ids),
        "additional_ready_candidate_market_ids": additional_ready_market_ids,
    }
    return candidates, discovery, {
        "actual_manual_llm_response_trial": actual_payload,
        "selected_ingest_final_dossier_drafts": selected_payload,
        "actual_manual_llm_response_surface_operator_review": surface_payload,
    }


def _packet_validation_status(packet_payload, packet_artifact_status, root=ROOT):
    if not packet_artifact_status.get("present"):
        return NOT_RUN, [], []
    if packet_artifact_status.get("parse_status") != "parsed":
        return "rejected", [
            _queue_issue(
                "packet_json_not_parsed",
                packet_artifact_status["path"],
                "Packet JSON could not be parsed safely.",
            )
        ], []

    packet_schema, schema_status = _artifact_check(
        validator.PACKET_SCHEMA_PATH,
        "llm_analysis_packet_schema",
        required=True,
        root=root,
        parse_json=True,
    )
    if schema_status["parse_status"] != "parsed":
        return "rejected", [
            _queue_issue(
                "packet_schema_unavailable",
                schema_status["path"],
                "Packet schema could not be parsed safely.",
            )
        ], []

    result = validator.validate_packet_payload(packet_payload, packet_schema)
    return result["status"], result["errors"], result["warnings"]


def _response_validation_status(packet_path, response_path, response_payload, response_artifact_status, root=ROOT):
    if not response_artifact_status.get("present"):
        return NOT_RUN, NOT_RUN, [], []
    if response_artifact_status.get("parse_status") != "parsed":
        return "rejected", "quality_failed", [
            _queue_issue(
                "response_json_not_parsed",
                response_artifact_status["path"],
                "Response JSON could not be parsed safely.",
            )
        ], []

    response_schema, schema_status = _artifact_check(
        validator.RESPONSE_SCHEMA_PATH,
        "llm_analysis_response_schema",
        required=True,
        root=root,
        parse_json=True,
    )
    if schema_status["parse_status"] != "parsed":
        return "rejected", "quality_failed", [
            _queue_issue(
                "response_schema_unavailable",
                schema_status["path"],
                "Response schema could not be parsed safely.",
            )
        ], []

    response_result = validator.validate_response_payload(response_payload, response_schema)
    errors = list(response_result["errors"])
    warnings = list(response_result["warnings"])
    response_status = response_result["status"]
    gate_status = NOT_AVAILABLE

    if response_status == "accepted":
        gate = quality_gate.build_quality_gate(
            packet_path=packet_path,
            response_path=response_path,
            manual_review_path=None,
        )
        gate_status = gate["validation_status"]
        errors.extend(gate["errors"])
        warnings.extend(gate["warnings"])
    else:
        gate_status = "quality_failed"
    return response_status, gate_status, errors, warnings


def _queue_issue(code, path, message):
    return {"code": code, "path": path, "message": message}


def _surface_review_status(surface_payload, market_id):
    surface = _safe_dict(surface_payload)
    status = _string_field(surface, "operator_surface_review_status", NOT_AVAILABLE)
    snapshots = _safe_dict(surface.get("surface_snapshots"))
    if not snapshots:
        return status
    for snapshot in snapshots.values():
        if str(_safe_dict(snapshot).get("market_id") or "") == str(market_id):
            return status
    return NOT_AVAILABLE


def _effective_status_from_actual(actual_payload):
    actual = _safe_dict(actual_payload)
    if not actual:
        return {}
    return {
        "validation_status": _string_field(actual, "response_validation_status", NOT_AVAILABLE),
        "packet_validation_status": _string_field(actual, "packet_validation_status", NOT_AVAILABLE),
        "response_validation_status": _string_field(actual, "response_validation_status", NOT_AVAILABLE),
        "quality_gate_status": _string_field(actual, "quality_gate_status", NOT_AVAILABLE),
        "acceptance_status": _string_field(actual, "acceptance_status", NOT_AVAILABLE),
        "run_status": _string_field(actual, "run_status", NOT_AVAILABLE),
        "response_present": _bool_field(actual, "operator_response_present", False),
    }


def _status_from_known_values(
    packet_present,
    packet_status,
    prompt_present,
    response_present,
    validation_status,
    quality_gate_status,
    acceptance_status,
    operator_surface_review_status,
    artifact_errors,
):
    if artifact_errors:
        return BLOCKED_INVALID_ARTIFACT
    if not packet_present:
        return BLOCKED_MISSING_PACKET
    if packet_status != "accepted":
        return BLOCKED_INVALID_ARTIFACT
    if not prompt_present:
        return READY_FOR_PROMPT_EXPORT
    if not response_present:
        return WAITING_FOR_RESPONSE

    accepted_quality = quality_gate_status in {"quality_passed", "quality_passed_with_warnings"}
    accepted_surface = operator_surface_review_status in {NOT_AVAILABLE, "operator_surface_review_passed"}
    if (
        validation_status == "accepted"
        and acceptance_status in {NOT_AVAILABLE, "accepted_for_operator_review"}
        and accepted_quality
        and accepted_surface
    ):
        return RESPONSE_ACCEPTED
    return RESPONSE_REJECTED


def _tokens(text):
    return re.findall(r"[a-z0-9]+", str(text).lower())


def forbidden_status_action_findings(items):
    findings = []
    for item in items:
        for field in ("review_queue_status", "next_safe_operator_action"):
            tokens = set(_tokens(item.get(field, "")))
            bad_terms = sorted(tokens.intersection(FORBIDDEN_STATUS_ACTION_TERMS))
            if bad_terms:
                findings.append(
                    {
                        "market_id": item.get("market_id", ""),
                        "field": field,
                        "terms": bad_terms,
                        "text": str(item.get(field, "")),
                    }
                )
    return findings


def build_queue_item(candidate, preloaded_payloads=None, root=ROOT):
    root = Path(root)
    preloaded_payloads = preloaded_payloads or {}
    market_id = str(candidate.get("market_id") or "")
    actual_trial_path = candidate.get("actual_trial_path")
    actual_payload = None
    actual_status = None
    if actual_trial_path == DEFAULT_ACTUAL_TRIAL_PATH and preloaded_payloads.get(
        "actual_manual_llm_response_trial"
    ) is not None:
        actual_payload = preloaded_payloads["actual_manual_llm_response_trial"]
        actual_status = {
            "artifact_id": "actual_manual_llm_response_trial",
            "path": DEFAULT_ACTUAL_TRIAL_PATH,
            "required": False,
            "present": True,
            "parse_status": "parsed",
        }
    elif actual_trial_path:
        actual_payload, actual_status = _artifact_check(
            actual_trial_path,
            "actual_manual_llm_response_trial",
            required=False,
            root=root,
            parse_json=True,
        )
    else:
        actual_status = {
            "artifact_id": "actual_manual_llm_response_trial",
            "path": "",
            "required": False,
            "present": False,
            "parse_status": "not_provided",
        }

    source_artifact_path = (
        _string_field(actual_payload, "source_artifact_path")
        or str(candidate.get("source_artifact_path") or "")
    )
    packet_path = _string_field(actual_payload, "packet_path") or str(candidate.get("packet_path") or "")
    prompt_path = _string_field(actual_payload, "prompt_path") or str(candidate.get("prompt_path") or "")
    operator_response_path = (
        _string_field(actual_payload, "operator_response_path")
        or str(candidate.get("operator_response_path") or "")
    )

    source_payload, source_status = _artifact_check(
        source_artifact_path,
        "source_artifact",
        required=False,
        root=root,
        parse_json=True,
    )
    packet_payload, packet_status = _artifact_check(
        packet_path,
        "packet",
        required=True,
        root=root,
        parse_json=True,
    )
    response_payload, response_status = _artifact_check(
        operator_response_path,
        "operator_response",
        required=False,
        root=root,
        parse_json=True,
    )
    _prompt_payload, prompt_status = _artifact_check(
        prompt_path,
        "prompt",
        required=False,
        root=root,
        parse_json=False,
    )

    surface_review_path = candidate.get("surface_review_path")
    if surface_review_path == DEFAULT_SURFACE_REVIEW_PATH and preloaded_payloads.get(
        "actual_manual_llm_response_surface_operator_review"
    ) is not None:
        surface_payload = preloaded_payloads["actual_manual_llm_response_surface_operator_review"]
        surface_status = {
            "artifact_id": "operator_surface_review",
            "path": DEFAULT_SURFACE_REVIEW_PATH,
            "required": False,
            "present": True,
            "parse_status": "parsed",
        }
    elif surface_review_path:
        surface_payload, surface_status = _artifact_check(
            surface_review_path,
            "operator_surface_review",
            required=False,
            root=root,
            parse_json=True,
        )
    else:
        surface_payload = None
        surface_status = {
            "artifact_id": "operator_surface_review",
            "path": "",
            "required": False,
            "present": False,
            "parse_status": "not_provided",
        }

    artifact_checks = {
        "source_artifact": source_status,
        "packet": packet_status,
        "prompt": prompt_status,
        "operator_response": response_status,
        "actual_trial": actual_status,
        "operator_surface_review": surface_status,
    }

    artifact_errors = []
    for check in artifact_checks.values():
        if check["parse_status"] in {"parse_failed", "read_failed", "top_level_not_object"}:
            artifact_errors.append(
                _queue_issue(
                    f"{check['artifact_id']}_{check['parse_status']}",
                    check["path"],
                    "Referenced JSON artifact could not be parsed safely.",
                )
            )

    packet_validation_status, packet_errors, packet_warnings = _packet_validation_status(
        packet_payload,
        packet_status,
        root=root,
    )
    validation_status = NOT_RUN
    response_validation_status = NOT_RUN
    quality_gate_status = NOT_RUN
    acceptance_status = NOT_AVAILABLE
    run_status = NOT_AVAILABLE
    response_present = response_status["present"]

    actual_statuses = _effective_status_from_actual(actual_payload)
    if actual_statuses:
        validation_status = actual_statuses["validation_status"]
        packet_validation_status = actual_statuses["packet_validation_status"]
        response_validation_status = actual_statuses["response_validation_status"]
        quality_gate_status = actual_statuses["quality_gate_status"]
        acceptance_status = actual_statuses["acceptance_status"]
        run_status = actual_statuses["run_status"]
        response_present = actual_statuses["response_present"]
    elif response_status["present"] and packet_status["present"] and packet_validation_status == "accepted":
        response_validation_status, quality_gate_status, response_errors, response_warnings = (
            _response_validation_status(
                _resolve_path(packet_path, root),
                _resolve_path(operator_response_path, root),
                response_payload,
                response_status,
                root=root,
            )
        )
        validation_status = response_validation_status
        packet_errors.extend(response_errors)
        packet_warnings.extend(response_warnings)

    operator_surface_review_status = _surface_review_status(surface_payload, market_id)
    review_queue_status = _status_from_known_values(
        packet_present=packet_status["present"],
        packet_status=packet_validation_status,
        prompt_present=prompt_status["present"],
        response_present=response_present,
        validation_status=validation_status,
        quality_gate_status=quality_gate_status,
        acceptance_status=acceptance_status,
        operator_surface_review_status=operator_surface_review_status,
        artifact_errors=artifact_errors,
    )

    errors = sorted(
        artifact_errors + packet_errors,
        key=lambda item: (item["path"], item["code"], item["message"]),
    )
    warnings = sorted(
        packet_warnings,
        key=lambda item: (item.get("path", ""), item.get("code", ""), item.get("message", "")),
    )

    return {
        "market_id": market_id,
        "candidate_id": str(candidate.get("candidate_id") or f"manual_llm_review_{market_id}"),
        "candidate_source": str(candidate.get("candidate_source") or "local_candidate"),
        "source_artifact_path": _display_path(_resolve_path(source_artifact_path, root), root)
        if source_artifact_path
        else "",
        "packet_path": _display_path(_resolve_path(packet_path, root), root) if packet_path else "",
        "packet_present": packet_status["present"],
        "packet_parse_status": packet_status["parse_status"],
        "prompt_path": _display_path(_resolve_path(prompt_path, root), root) if prompt_path else "",
        "prompt_present": prompt_status["present"],
        "operator_response_path": _display_path(_resolve_path(operator_response_path, root), root)
        if operator_response_path
        else "",
        "operator_response_present": response_status["present"],
        "response_present": bool(response_present),
        "validation_status": validation_status,
        "packet_validation_status": packet_validation_status,
        "response_validation_status": response_validation_status,
        "quality_gate_status": quality_gate_status,
        "operator_surface_review_status": operator_surface_review_status,
        "acceptance_status": acceptance_status,
        "run_status": run_status,
        "review_queue_status": review_queue_status,
        "next_safe_operator_action": NEXT_ACTION_BY_STATUS[review_queue_status],
        "offline_manual_only": True,
        "not_truth_source": True,
        "not_trading_advice": True,
        "not_execution_authority": True,
        "artifact_checks": artifact_checks,
        "errors_count": len(errors),
        "warnings_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def _queue_status_counts(items):
    return {
        status: sum(1 for item in items if item["review_queue_status"] == status)
        for status in QUEUE_STATUSES
    }


def _build_discovery_for_explicit_candidates(candidates):
    return {
        "source_artifacts_checked": [],
        "actual_trial_candidate_found": any(
            candidate.get("candidate_source") == "actual_manual_llm_response_trial"
            for candidate in candidates
        ),
        "selected_ingest_markets_seen": 0,
        "selected_ingest_market_ids": [],
        "final_dossier_drafts_seen": 0,
        "final_dossier_draft_market_ids": [],
        "exported_market_ids": [],
        "candidate_policy": "Explicit local test candidates supplied.",
        "additional_ready_candidates_found": 0,
        "additional_ready_candidate_market_ids": [],
    }


def build_manual_llm_review_queue(root=ROOT, candidates=None):
    root = Path(root)
    if candidates is None:
        candidates, discovery, preloaded_payloads = discover_default_candidates(root)
    else:
        candidates = list(candidates)
        discovery = _build_discovery_for_explicit_candidates(candidates)
        preloaded_payloads = {}

    items = [build_queue_item(candidate, preloaded_payloads, root=root) for candidate in candidates]
    items = sorted(items, key=lambda item: (item["market_id"], item["candidate_id"]))
    forbidden_findings = forbidden_status_action_findings(items)
    status_counts = _queue_status_counts(items)
    errors = []
    if forbidden_findings:
        errors.append(
            _queue_issue(
                "forbidden_status_or_action_text",
                "manual_llm_review_queue.items",
                "Queue status or action text contains blocked behavior language.",
            )
        )

    warnings = []
    if not discovery["additional_ready_candidate_market_ids"]:
        warnings.append(
            _queue_issue(
                "no_additional_ready_candidates_found",
                DEFAULT_SELECTED_DOSSIERS_PATH,
                "No additional safe local packet candidates were found beyond existing queue items.",
            )
        )

    return {
        "schema_version": QUEUE_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "deterministic": True,
        "queue_items_total": len(items),
        "queue_status_counts": status_counts,
        "items": items,
        "candidate_discovery": discovery,
        "forbidden_status_action_findings": forbidden_findings,
        "errors": errors,
        "warnings": warnings,
        "safety_flags": dict(SAFETY_FLAGS),
        "network_calls": 0,
        "llm_api_calls": 0,
        "browser_automation": False,
        "prompt_automation": False,
        "runtime_wiring": False,
        "orders_created": 0,
        "truth_inference": False,
        "next_safe_operator_action": (
            "Add future markets only after an offline local packet exists, then rerun this queue exporter."
        ),
    }


def _compact_queue_item(item):
    return {
        "market_id": item.get("market_id", ""),
        "source_artifact_path": item.get("source_artifact_path", ""),
        "packet_path": item.get("packet_path", ""),
        "prompt_path": item.get("prompt_path", ""),
        "operator_response_path": item.get("operator_response_path", ""),
        "response_present": bool(item.get("response_present", False)),
        "validation_status": item.get("validation_status", NOT_AVAILABLE),
        "quality_gate_status": item.get("quality_gate_status", NOT_AVAILABLE),
        "operator_surface_review_status": item.get("operator_surface_review_status", NOT_AVAILABLE),
        "review_queue_status": item.get("review_queue_status", NOT_AVAILABLE),
        "next_safe_operator_action": item.get("next_safe_operator_action", NOT_AVAILABLE),
        "offline_manual_only": item.get("offline_manual_only") is True,
        "not_truth_source": item.get("not_truth_source") is True,
        "not_trading_advice": item.get("not_trading_advice") is True,
        "not_execution_authority": item.get("not_execution_authority") is True,
    }


def summarize_manual_llm_review_queue(artifact_path=DEFAULT_OUT_JSON, root=ROOT):
    payload, status = _artifact_check(
        artifact_path,
        "manual_llm_review_queue",
        required=False,
        root=root,
        parse_json=True,
    )
    base = {
        "contract_version": QUEUE_SCHEMA_VERSION,
        "generated_by": GENERATED_BY,
        "artifact_path": status["path"],
        "artifact_present": status["present"],
        "artifact_status": "present" if status["present"] else "missing",
        "parse_status": status["parse_status"],
        "queue_items_total": 0,
        "queue_status_counts": {status_name: 0 for status_name in QUEUE_STATUSES},
        "items": [],
        "warnings_count": 0,
        "errors_count": 0,
        "additional_ready_candidates_found": 0,
        "offline_manual_only": True,
        "not_truth_source": True,
        "not_trading_advice": True,
        "not_execution_authority": True,
        "safety_flags": dict(SAFETY_FLAGS),
        "llm_api_calls_added": False,
        "browser_automation_added": False,
        "runtime_integration_added": False,
        "prompt_automation_added": False,
        "safe_error_summary": [],
    }
    if not status["present"]:
        return {
            **base,
            "safe_error_summary": ["Manual LLM review queue artifact is not available locally."],
        }
    if status["parse_status"] != "parsed" or not isinstance(payload, dict):
        return {
            **base,
            "artifact_status": "invalid",
            "safe_error_summary": [
                "Manual LLM review queue artifact is present but could not be parsed safely."
            ],
        }
    discovery = _safe_dict(payload.get("candidate_discovery"))
    return {
        **base,
        "queue_items_total": int(payload.get("queue_items_total") or 0)
        if not isinstance(payload.get("queue_items_total"), bool)
        else 0,
        "queue_status_counts": {
            status_name: int(_safe_dict(payload.get("queue_status_counts")).get(status_name) or 0)
            if not isinstance(_safe_dict(payload.get("queue_status_counts")).get(status_name), bool)
            else 0
            for status_name in QUEUE_STATUSES
        },
        "items": [_compact_queue_item(item) for item in _safe_list(payload.get("items"))],
        "warnings_count": len(_safe_list(payload.get("warnings"))),
        "errors_count": len(_safe_list(payload.get("errors"))),
        "additional_ready_candidates_found": int(
            discovery.get("additional_ready_candidates_found") or 0
        )
        if not isinstance(discovery.get("additional_ready_candidates_found"), bool)
        else 0,
    }


def render_markdown(queue):
    lines = [
        "# PMBOT Manual LLM Review Queue v1",
        "",
        f"- task_id: {queue['task_id']}",
        f"- queue_items_total: {queue['queue_items_total']}",
        f"- generated_at: {queue['generated_at']}",
        f"- network_calls: {queue['network_calls']}",
        f"- llm_api_calls: {queue['llm_api_calls']}",
        f"- browser_automation: {str(queue['browser_automation']).lower()}",
        f"- prompt_automation: {str(queue['prompt_automation']).lower()}",
        f"- runtime_wiring: {str(queue['runtime_wiring']).lower()}",
        "",
        "## Queue Status Counts",
        "",
    ]
    for status, count in queue["queue_status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Queue Items", ""])
    if queue["items"]:
        for item in queue["items"]:
            lines.extend(
                [
                    f"- market_id: {item['market_id']}",
                    f"  status: {item['review_queue_status']}",
                    f"  source_artifact_path: {item['source_artifact_path'] or 'not_available'}",
                    f"  packet_path: {item['packet_path'] or 'not_available'}",
                    f"  packet_present: {str(item['packet_present']).lower()}",
                    f"  prompt_path: {item['prompt_path'] or 'not_available'}",
                    f"  prompt_present: {str(item['prompt_present']).lower()}",
                    f"  operator_response_path: {item['operator_response_path'] or 'not_available'}",
                    f"  response_present: {str(item['response_present']).lower()}",
                    f"  validation_status: {item['validation_status']}",
                    f"  quality_gate_status: {item['quality_gate_status']}",
                    f"  operator_surface_review_status: {item['operator_surface_review_status']}",
                    f"  next_safe_operator_action: {item['next_safe_operator_action']}",
                ]
            )
    else:
        lines.append("- none")
    discovery = queue["candidate_discovery"]
    lines.extend(
        [
            "",
            "## Candidate Discovery",
            "",
            f"- selected_ingest_markets_seen: {discovery['selected_ingest_markets_seen']}",
            f"- final_dossier_drafts_seen: {discovery['final_dossier_drafts_seen']}",
            f"- additional_ready_candidates_found: {discovery['additional_ready_candidates_found']}",
            "- candidate_policy: "
            f"{discovery['candidate_policy']}",
            "",
            "## Safety Boundary",
            "",
            "- offline_manual_only: true",
            "- not_truth_source: true",
            "- not_trading_advice: true",
            "- not_execution_authority: true",
            "",
            "## Warnings",
            "",
        ]
    )
    if queue["warnings"]:
        for warning in queue["warnings"]:
            lines.append(f"- {warning['code']}: {warning['message']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Errors", ""])
    if queue["errors"]:
        for error in queue["errors"]:
            lines.append(f"- {error['code']}: {error['message']}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def build_doc_result(queue):
    blocked = bool(queue["errors"])
    return {
        "task_id": TASK_ID,
        "status": "blocked" if blocked else "completed_ready_for_review",
        "queue_artifact": DEFAULT_OUT_JSON,
        "queue_markdown": DEFAULT_OUT_MD,
        "expected_queue_fixture": DEFAULT_EXPECTED_JSON,
        "doc_markdown": DEFAULT_DOC_MD,
        "queue_items_total": queue["queue_items_total"],
        "queue_status_counts": queue["queue_status_counts"],
        "candidate_discovery": queue["candidate_discovery"],
        "warnings": queue["warnings"],
        "blockers": queue["errors"],
        "safety_flags": dict(SAFETY_FLAGS),
        "network_calls": 0,
        "llm_api_calls": 0,
        "browser_automation": False,
        "prompt_automation": False,
        "runtime_wiring": False,
        "orders_created": 0,
        "truth_inference": False,
        "next_recommended_task": "PMBOT-LLM-014-MANUAL-PACKET-QUEUE-EXPANSION",
    }


def export_manual_llm_review_queue(
    root=ROOT,
    out_json=DEFAULT_OUT_JSON,
    out_md=DEFAULT_OUT_MD,
    expected_json=DEFAULT_EXPECTED_JSON,
    doc_result_json=DEFAULT_DOC_RESULT_JSON,
    doc_md=DEFAULT_DOC_MD,
):
    queue = build_manual_llm_review_queue(root=root)
    markdown = render_markdown(queue)
    doc_result = build_doc_result(queue)
    _write_json(_resolve_path(out_json, root), queue)
    _write_text(_resolve_path(out_md, root), markdown)
    _write_json(_resolve_path(expected_json, root), queue)
    _write_json(_resolve_path(doc_result_json, root), doc_result)
    _write_text(_resolve_path(doc_md, root), markdown)
    return queue


def main(argv):
    args = _parse_args(argv)
    queue = export_manual_llm_review_queue(
        out_json=args.out_json,
        out_md=args.out_md,
        expected_json=args.expected_json,
        doc_result_json=args.doc_result_json,
        doc_md=args.doc_md,
    )
    print(json.dumps(queue, indent=2, ensure_ascii=True))
    return 0 if not queue["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
