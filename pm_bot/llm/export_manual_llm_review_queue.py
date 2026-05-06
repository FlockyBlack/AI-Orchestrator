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


TASK_ID = "PMBOT-LLM-014-MANUAL-PACKET-QUEUE-EXPANSION"
QUEUE_SCHEMA_VERSION = "manual_llm_review_queue.v1"
GENERATED_BY = "pm_bot/llm/export_manual_llm_review_queue.py"
DETERMINISTIC_GENERATED_AT = "deterministic-manual-llm-review-queue.v1"

READY_FOR_PACKET_EXPORT = "ready_for_manual_packet_export"
READY_FOR_PROMPT_EXPORT = "ready_for_manual_prompt_export"
WAITING_FOR_RESPONSE = "waiting_for_operator_pasted_response"
RESPONSE_ACCEPTED = "response_accepted_for_operator_review"
RESPONSE_REJECTED = "response_rejected_needs_operator_fix"
BLOCKED_MISSING_PACKET = "blocked_missing_packet"
BLOCKED_INVALID_ARTIFACT = "blocked_invalid_artifact"
BLOCKED_MISSING_SOURCE_ARTIFACT = "blocked_missing_source_artifact"

QUEUE_STATUSES = (
    READY_FOR_PACKET_EXPORT,
    READY_FOR_PROMPT_EXPORT,
    WAITING_FOR_RESPONSE,
    RESPONSE_ACCEPTED,
    RESPONSE_REJECTED,
    BLOCKED_MISSING_PACKET,
    BLOCKED_INVALID_ARTIFACT,
    BLOCKED_MISSING_SOURCE_ARTIFACT,
)

NOT_AVAILABLE = "not_available"
NOT_RUN = "not_run"
BATCH_PACKET_CONTRACT_VERSION = "manual_llm_packet_batch_packet.v1"
BATCH_PACKET_SOURCE_TYPE = "manual_llm_packet_batch_artifact"

DEFAULT_TRIAL_PATH = "pm_bot/llm/real_local_market_llm_trial.v1.json"
DEFAULT_PACKET_PATH = "pm_bot/llm/real_local_market_llm_trial_packet.v1.json"
DEFAULT_PROMPT_PATH = "pm_bot/llm/real_local_market_llm_trial_prompt.v1.md"
DEFAULT_OPERATOR_RESPONSE_PATH = "pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json"
DEFAULT_ACTUAL_TRIAL_PATH = "pm_bot/llm/actual_manual_llm_response_trial.v1.json"
DEFAULT_SURFACE_REVIEW_PATH = "pm_bot/llm/actual_manual_llm_response_surface_operator_review.v1.json"
DEFAULT_SELECTED_DOSSIERS_PATH = "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json"
DEFAULT_WORKBENCH_REVIEW_PACK_PATH = "pm_bot/workbench/operator_review_pack.v1.json"

APPROVED_RESEARCH_CANDIDATE_SOURCES = (
    {
        "artifact_id": "selected_ingest_final_dossier_drafts",
        "path": DEFAULT_SELECTED_DOSSIERS_PATH,
        "object_fields": (("final_dossier_drafts", "selected_ingest_final_dossier_draft"),),
        "market_id_fields": (("selected_market_ids", "selected_ingest_selected_market_id"),),
    },
    {
        "artifact_id": "final_dossier_drafts",
        "path": "pm_bot/research/final_dossier_drafts.v1.json",
        "object_fields": (("final_dossier_drafts", "final_dossier_draft"),),
        "market_id_fields": (("exported_market_ids", "final_dossier_exported_market_id"),),
    },
    {
        "artifact_id": "selected_ingest_merged_manual_research_packets",
        "path": "pm_bot/research/selected_ingest_merged_manual_research_packets.v1.json",
        "object_fields": (("packets", "selected_ingest_merged_manual_research_packet"),),
        "market_id_fields": (),
    },
    {
        "artifact_id": "merged_manual_research_packets",
        "path": "pm_bot/research/merged_manual_research_packets.v1.json",
        "object_fields": (("packets", "merged_manual_research_packet"),),
        "market_id_fields": (),
    },
    {
        "artifact_id": "selected_ingest_research_packet_stubs",
        "path": "pm_bot/research/selected_ingest_research_packet_stubs.v1.json",
        "object_fields": (("packet_stubs", "selected_ingest_research_packet_stub"),),
        "market_id_fields": (),
    },
    {
        "artifact_id": "operator_review_queue",
        "path": "pm_bot/research/operator_review_queue.v1.json",
        "object_fields": (),
        "market_id_fields": (),
        "group_source_type": "operator_review_queue_item",
    },
    {
        "artifact_id": "selected_ingest_operator_review_queue",
        "path": "pm_bot/research/selected_ingest_operator_review_queue.v1.json",
        "object_fields": (),
        "market_id_fields": (),
        "group_source_type": "selected_ingest_operator_review_queue_item",
    },
)

CANDIDATE_SOURCE_PRIORITY = {
    "actual_manual_llm_response_trial": 0,
    "llm_packet_artifact": 10,
    BATCH_PACKET_SOURCE_TYPE: 10,
    "selected_ingest_final_dossier_draft": 20,
    "final_dossier_draft": 30,
    "final_dossier_exported_market_id": 31,
    "selected_ingest_merged_manual_research_packet": 40,
    "merged_manual_research_packet": 50,
    "selected_ingest_operator_review_queue_item": 60,
    "operator_review_queue_item": 70,
    "selected_ingest_research_packet_stub": 80,
    "selected_ingest_selected_market_id": 90,
}

DEFAULT_OUT_JSON = "pm_bot/llm/manual_llm_review_queue.v1.json"
DEFAULT_OUT_MD = "pm_bot/llm/manual_llm_review_queue.v1.md"
DEFAULT_EXPECTED_JSON = "pm_bot/llm/expected_manual_llm_review_queue.v1.json"
DEFAULT_DOC_RESULT_JSON = "docs/PMBOT_LLM_014_RESULT.json"
DEFAULT_DOC_MD = "docs/PMBOT_LLM_014_MANUAL_PACKET_QUEUE_EXPANSION.md"

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
    "sensitive_access_material": False,
    "live_market_actions": False,
    "autonomous_simulated_actions": False,
    "value_estimate_or_advantage_analysis": False,
    "outcome_selection": False,
    "truth_evaluation": False,
    "execution_authority": False,
}

NEXT_ACTION_BY_STATUS = {
    READY_FOR_PACKET_EXPORT: (
        "Create the local manual packet from the referenced local artifact, then rebuild the queue."
    ),
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
    BLOCKED_MISSING_SOURCE_ARTIFACT: (
        "Restore or regenerate the referenced local source artifact, then rebuild the queue."
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
        "candidate_source_type": "actual_manual_llm_response_trial",
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


def _candidate_source_type(candidate):
    return str(
        candidate.get("candidate_source_type")
        or candidate.get("candidate_source")
        or "local_candidate"
    )


def _source_priority(candidate):
    return CANDIDATE_SOURCE_PRIORITY.get(_candidate_source_type(candidate), 999)


def _candidate_ref(candidate):
    return {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "candidate_source_type": _candidate_source_type(candidate),
        "source_artifact_path": str(candidate.get("source_artifact_path") or ""),
    }


def _ordered_unique_strings(values):
    seen = set()
    ordered = []
    for value in values:
        text = str(value or "")
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def _merge_candidate(existing, candidate):
    refs = list(existing.get("source_refs") or [_candidate_ref(existing)])
    refs.append(_candidate_ref(candidate))
    primary = dict(existing)
    if _source_priority(candidate) < _source_priority(existing):
        primary = {**candidate}
        for key in (
            "packet_path",
            "prompt_path",
            "operator_response_path",
            "actual_trial_path",
            "surface_review_path",
        ):
            if not primary.get(key) and existing.get(key):
                primary[key] = existing[key]
    else:
        for key in (
            "packet_path",
            "prompt_path",
            "operator_response_path",
            "actual_trial_path",
            "surface_review_path",
        ):
            if not primary.get(key) and candidate.get(key):
                primary[key] = candidate[key]
    source_refs = []
    seen_refs = set()
    for ref in refs:
        key = (
            ref.get("candidate_source_type", ""),
            ref.get("source_artifact_path", ""),
            ref.get("candidate_id", ""),
        )
        if key in seen_refs:
            continue
        seen_refs.add(key)
        source_refs.append(ref)
    primary["source_refs"] = sorted(
        source_refs,
        key=lambda ref: (
            CANDIDATE_SOURCE_PRIORITY.get(ref.get("candidate_source_type", ""), 999),
            ref.get("source_artifact_path", ""),
            ref.get("candidate_id", ""),
        ),
    )
    primary["source_artifact_paths"] = _ordered_unique_strings(
        ref["source_artifact_path"] for ref in primary["source_refs"]
    )
    primary["candidate_source_types"] = _ordered_unique_strings(
        ref["candidate_source_type"] for ref in primary["source_refs"]
    )
    primary["source_count"] = len(primary["source_refs"])
    return primary


def dedupe_candidates_by_market_id(candidates):
    by_market_id = {}
    for candidate in sorted(
        candidates,
        key=lambda item: (
            str(item.get("market_id") or ""),
            _source_priority(item),
            str(item.get("candidate_id") or ""),
        ),
    ):
        market_id = str(candidate.get("market_id") or "")
        if not market_id:
            continue
        candidate = {
            **candidate,
            "candidate_source": _candidate_source_type(candidate),
            "candidate_source_type": _candidate_source_type(candidate),
            "source_refs": list(candidate.get("source_refs") or [_candidate_ref(candidate)]),
        }
        if market_id not in by_market_id:
            candidate["source_artifact_paths"] = _ordered_unique_strings(
                ref["source_artifact_path"] for ref in candidate["source_refs"]
            )
            candidate["candidate_source_types"] = _ordered_unique_strings(
                ref["candidate_source_type"] for ref in candidate["source_refs"]
            )
            candidate["source_count"] = len(candidate["source_refs"])
            by_market_id[market_id] = candidate
            continue
        by_market_id[market_id] = _merge_candidate(by_market_id[market_id], candidate)
    return sorted(by_market_id.values(), key=lambda item: (str(item["market_id"]), item["candidate_id"]))


def _is_safe_market_id(value):
    text = str(value or "").strip()
    if not text:
        return False
    lowered = text.lower()
    if any(marker in lowered for marker in ("example", "demo", "fixture", "invalid")):
        return False
    return text.isdigit()


def _skip_candidate(skipped, reason, source_artifact_path, market_id="", candidate_source_type=""):
    skipped.append(
        {
            "reason": reason,
            "source_artifact_path": source_artifact_path,
            "market_id": str(market_id or ""),
            "candidate_source_type": candidate_source_type,
        }
    )


def _candidate_from_local_source(source_artifact_path, source_type, market_id):
    market_id = str(market_id or "")
    return {
        "candidate_id": f"{source_type}_{market_id}",
        "candidate_source": source_type,
        "candidate_source_type": source_type,
        "market_id": market_id,
        "source_artifact_path": source_artifact_path,
        "packet_path": "",
        "prompt_path": "",
        "operator_response_path": "",
    }


def _extract_group_candidates(payload, source_artifact_path, source_type, skipped):
    candidates = []
    groups = _safe_dict(_safe_dict(payload).get("groups"))
    for group_name in sorted(groups):
        group_items = _safe_list(groups.get(group_name))
        for item in group_items:
            if not isinstance(item, dict):
                _skip_candidate(
                    skipped,
                    "invalid_group_item_shape",
                    source_artifact_path,
                    "",
                    source_type,
                )
                continue
            market_id = item.get("market_id")
            if not _is_safe_market_id(market_id):
                _skip_candidate(
                    skipped,
                    "unsafe_or_invalid_market_id",
                    source_artifact_path,
                    market_id,
                    source_type,
                )
                continue
            candidates.append(_candidate_from_local_source(source_artifact_path, source_type, market_id))
    return candidates


def _discover_research_candidates(root=ROOT):
    candidates = []
    statuses = []
    skipped = []
    payloads_by_path = {}
    for source in APPROVED_RESEARCH_CANDIDATE_SOURCES:
        payload, status = _load_json_for_discovery(source["path"], source["artifact_id"], root)
        statuses.append(status)
        payloads_by_path[source["path"]] = payload
        if not status["present"]:
            continue
        if status["parse_status"] != "parsed":
            _skip_candidate(
                skipped,
                "source_artifact_not_parsed",
                status["path"],
                "",
                source["artifact_id"],
            )
            continue
        source_artifact_path = source["path"]
        for field, source_type in source.get("object_fields", ()):
            items = _safe_list(_safe_dict(payload).get(field))
            for item in items:
                if not isinstance(item, dict):
                    _skip_candidate(
                        skipped,
                        "invalid_candidate_item_shape",
                        source_artifact_path,
                        "",
                        source_type,
                    )
                    continue
                market_id = item.get("market_id")
                if not _is_safe_market_id(market_id):
                    _skip_candidate(
                        skipped,
                        "unsafe_or_invalid_market_id",
                        source_artifact_path,
                        market_id,
                        source_type,
                    )
                    continue
                candidates.append(
                    _candidate_from_local_source(source_artifact_path, source_type, market_id)
                )
        for field, source_type in source.get("market_id_fields", ()):
            for market_id in _safe_list(_safe_dict(payload).get(field)):
                if not _is_safe_market_id(market_id):
                    _skip_candidate(
                        skipped,
                        "unsafe_or_invalid_market_id",
                        source_artifact_path,
                        market_id,
                        source_type,
                    )
                    continue
                candidates.append(
                    _candidate_from_local_source(source_artifact_path, source_type, market_id)
                )
        if source.get("group_source_type"):
            candidates.extend(
                _extract_group_candidates(
                    payload,
                    source_artifact_path,
                    source["group_source_type"],
                    skipped,
                )
            )
    return candidates, statuses, skipped, payloads_by_path


def _is_example_or_demo_packet(path, payload):
    display = _display_path(path)
    lowered_path = display.lower()
    if any(marker in lowered_path for marker in ("example", "demo")):
        return True
    market_context = _safe_dict(_safe_dict(payload).get("market_context"))
    market_id = str(market_context.get("market_id") or "")
    if not _is_safe_market_id(market_id):
        return True
    source_artifacts = _safe_list(_safe_dict(payload).get("source_artifacts"))
    for source in source_artifacts:
        source = _safe_dict(source)
        source_text = " ".join(
            str(source.get(key) or "").lower()
            for key in ("artifact_type", "path", "description", "sanitization_status")
        )
        if any(marker in source_text for marker in ("example", "demo", "fixture_only")):
            return True
    return False


def _known_prompt_path_for_packet(packet_path, root=ROOT):
    path = Path(packet_path)
    name = path.name
    candidates = []
    if "_packet.v1.json" in name:
        candidates.append(path.with_name(name.replace("_packet.v1.json", "_prompt.v1.md")))
    if "packet.v1.json" in name:
        candidates.append(path.with_name(name.replace("packet.v1.json", "prompt.v1.md")))
    for candidate in candidates:
        if _resolve_path(_display_path(candidate, root), root).exists():
            return _display_path(candidate, root)
    return _display_path(candidates[0], root) if candidates else ""


def _known_response_path_for_packet(packet_path, root=ROOT):
    path = Path(packet_path)
    name = path.name
    candidates = []
    if "_packet.v1.json" in name:
        prefix = name.replace("_packet.v1.json", "")
        candidates.extend(
            [
                path.with_name(f"{prefix}_response_operator.v1.json"),
                path.with_name(f"{prefix}_response.v1.json"),
            ]
        )
    for candidate in candidates:
        lowered = candidate.name.lower()
        if "example" in lowered or "placeholder" in lowered:
            continue
        if _resolve_path(_display_path(candidate, root), root).exists():
            return _display_path(candidate, root)
    return ""


def _iter_llm_packet_paths(llm_dir):
    packet_paths = list(llm_dir.glob("*packet*.json"))
    batch_dir = llm_dir / "manual_packet_batch"
    if batch_dir.exists():
        packet_paths.extend(batch_dir.glob("*_packet.v1.json"))
    return sorted(set(packet_paths), key=lambda item: _display_path(item))


def _discover_llm_packet_candidates(root=ROOT):
    root = Path(root)
    candidates = []
    statuses = []
    skipped = []
    llm_dir = root / "pm_bot" / "llm"
    if not llm_dir.exists():
        return candidates, statuses, skipped
    allowed_contracts = {"llm_analysis_packet.v1", BATCH_PACKET_CONTRACT_VERSION}
    for packet_path in _iter_llm_packet_paths(llm_dir):
        if "manifest" in packet_path.name:
            continue
        display = _display_path(packet_path, root)
        if packet_path.name.endswith("_schema.v1.json"):
            _skip_candidate(skipped, "schema_packet_artifact_excluded", display, "", "llm_packet_artifact")
            continue
        payload, status = _load_json_for_discovery(display, "llm_packet_artifact", root)
        statuses.append(status)
        if status["parse_status"] != "parsed":
            _skip_candidate(skipped, "packet_artifact_not_parsed", display, "", "llm_packet_artifact")
            continue
        contract_version = _safe_dict(payload).get("contract_version")
        if contract_version not in allowed_contracts:
            _skip_candidate(skipped, "non_llm_analysis_packet_excluded", display, "", "llm_packet_artifact")
            continue
        market_id = _safe_dict(_safe_dict(payload).get("market_context")).get("market_id")
        if _is_example_or_demo_packet(packet_path, payload):
            _skip_candidate(
                skipped,
                "example_or_demo_packet_excluded",
                display,
                market_id,
                "llm_packet_artifact",
            )
            continue
        candidate_source_type = (
            BATCH_PACKET_SOURCE_TYPE
            if contract_version == BATCH_PACKET_CONTRACT_VERSION
            else "llm_packet_artifact"
        )
        candidates.append(
            {
                "candidate_id": f"{candidate_source_type}_{market_id}",
                "candidate_source": candidate_source_type,
                "candidate_source_type": candidate_source_type,
                "market_id": str(market_id),
                "source_artifact_path": display,
                "packet_path": display,
                "prompt_path": _known_prompt_path_for_packet(packet_path, root),
                "operator_response_path": _known_response_path_for_packet(packet_path, root),
            }
        )
    return candidates, statuses, skipped


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


def _source_count_by_type(candidates):
    counts = {}
    for candidate in candidates:
        for source_type in candidate.get("candidate_source_types") or [_candidate_source_type(candidate)]:
            counts[source_type] = counts.get(source_type, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _build_discovery(
    candidates,
    source_artifacts_checked,
    selected_payload,
    skipped_candidates,
    actual_candidate_found,
):
    candidate_market_ids = sorted(str(candidate["market_id"]) for candidate in candidates)
    accepted_market_ids = sorted(
        str(candidate["market_id"])
        for candidate in candidates
        if _candidate_source_type(candidate) == "actual_manual_llm_response_trial"
    )
    added_market_ids = [
        market_id for market_id in candidate_market_ids if market_id not in set(accepted_market_ids)
    ]
    selected_discovery = _selected_dossier_discovery(selected_payload)
    return {
        "source_artifacts_checked": source_artifacts_checked,
        "actual_trial_candidate_found": actual_candidate_found,
        **selected_discovery,
        "candidate_policy": (
            "Deterministically inventories non-example local PMBOT packet, research, dossier, "
            "and operator-review artifacts; no external data, ranking, or outcome inference is used."
        ),
        "candidate_market_ids": candidate_market_ids,
        "deduplicated_candidate_market_ids": candidate_market_ids,
        "deduplicated_candidates_total": len(candidates),
        "source_count_by_type": _source_count_by_type(candidates),
        "added_candidate_market_ids": added_market_ids,
        "additional_ready_candidates_found": len(added_market_ids),
        "additional_ready_candidate_market_ids": added_market_ids,
        "skipped_candidate_count": len(skipped_candidates),
        "skipped_candidates": sorted(
            skipped_candidates,
            key=lambda item: (
                item.get("source_artifact_path", ""),
                item.get("market_id", ""),
                item.get("reason", ""),
            ),
        ),
    }


def discover_default_candidates(root=ROOT):
    actual_payload, actual_status = _load_json_for_discovery(
        DEFAULT_ACTUAL_TRIAL_PATH,
        "actual_manual_llm_response_trial",
        root,
    )
    surface_payload, surface_status = _load_json_for_discovery(
        DEFAULT_SURFACE_REVIEW_PATH,
        "actual_manual_llm_response_surface_operator_review",
        root,
    )
    _workbench_payload, workbench_status = _load_json_for_discovery(
        DEFAULT_WORKBENCH_REVIEW_PACK_PATH,
        "operator_review_pack",
        root,
    )
    research_candidates, research_statuses, research_skipped, research_payloads = (
        _discover_research_candidates(root)
    )
    packet_candidates, packet_statuses, packet_skipped = _discover_llm_packet_candidates(root)

    candidates = []
    actual_candidate = _candidate_from_actual_trial(actual_payload)
    if actual_candidate is not None:
        candidates.append(actual_candidate)
    candidates.extend(packet_candidates)
    candidates.extend(research_candidates)

    deduped_candidates = dedupe_candidates_by_market_id(candidates)
    selected_payload = research_payloads.get(DEFAULT_SELECTED_DOSSIERS_PATH)
    discovery = _build_discovery(
        deduped_candidates,
        [
            actual_status,
            surface_status,
            workbench_status,
            *research_statuses,
            *packet_statuses,
        ],
        selected_payload,
        research_skipped + packet_skipped,
        actual_candidate is not None,
    )
    return deduped_candidates, discovery, {
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

    if _safe_dict(packet_payload).get("contract_version") == BATCH_PACKET_CONTRACT_VERSION:
        errors = _batch_packet_validation_errors(packet_payload, packet_artifact_status)
        return ("accepted" if not errors else "rejected"), errors, []

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
    source_artifact_expected,
    source_artifact_present,
    packet_path_known,
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
    if source_artifact_expected and not source_artifact_present:
        return BLOCKED_MISSING_SOURCE_ARTIFACT
    if not packet_path_known:
        return READY_FOR_PACKET_EXPORT
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
        source_artifact_expected=bool(source_artifact_path),
        source_artifact_present=source_status["present"],
        packet_path_known=bool(packet_path),
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
        "candidate_source": _candidate_source_type(candidate),
        "candidate_source_type": _candidate_source_type(candidate),
        "source_artifact_path": _display_path(_resolve_path(source_artifact_path, root), root)
        if source_artifact_path
        else "",
        "source_artifact_paths": _ordered_unique_strings(
            candidate.get("source_artifact_paths")
            or [
                ref.get("source_artifact_path", "")
                for ref in _safe_list(candidate.get("source_refs"))
            ]
            or [source_artifact_path]
        ),
        "candidate_source_types": _ordered_unique_strings(
            candidate.get("candidate_source_types")
            or [
                ref.get("candidate_source_type", "")
                for ref in _safe_list(candidate.get("source_refs"))
            ]
            or [_candidate_source_type(candidate)]
        ),
        "source_count": int(candidate.get("source_count") or 1)
        if not isinstance(candidate.get("source_count"), bool)
        else 1,
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
    market_ids = sorted(str(candidate.get("market_id") or "") for candidate in candidates)
    return {
        "source_artifacts_checked": [],
        "actual_trial_candidate_found": any(
            _candidate_source_type(candidate) == "actual_manual_llm_response_trial"
            for candidate in candidates
        ),
        "selected_ingest_markets_seen": 0,
        "selected_ingest_market_ids": [],
        "final_dossier_drafts_seen": 0,
        "final_dossier_draft_market_ids": [],
        "exported_market_ids": [],
        "candidate_policy": "Explicit local test candidates supplied.",
        "candidate_market_ids": market_ids,
        "deduplicated_candidate_market_ids": market_ids,
        "deduplicated_candidates_total": len(candidates),
        "source_count_by_type": _source_count_by_type(candidates),
        "added_candidate_market_ids": market_ids,
        "additional_ready_candidates_found": len(market_ids),
        "additional_ready_candidate_market_ids": market_ids,
        "skipped_candidate_count": 0,
        "skipped_candidates": [],
    }


def _batch_packet_validation_errors(packet_payload, packet_artifact_status):
    packet = _safe_dict(packet_payload)
    errors = []
    required_fields = (
        "contract_version",
        "packet_id",
        "market_id",
        "source_artifact_path",
        "candidate_source_type",
        "market_context",
        "local_review_context",
        "safety_boundaries",
        "expected_response_path",
    )
    for field in required_fields:
        value = packet.get(field)
        if value in ("", None, [], {}):
            errors.append(
                _queue_issue(
                    f"batch_packet_missing_{field}",
                    packet_artifact_status["path"],
                    f"Batch packet is missing required field {field}.",
                )
            )
    market_context = _safe_dict(packet.get("market_context"))
    if str(market_context.get("market_id") or "") != str(packet.get("market_id") or ""):
        errors.append(
            _queue_issue(
                "batch_packet_market_id_mismatch",
                packet_artifact_status["path"],
                "Batch packet market_context.market_id must match top-level market_id.",
            )
        )
    safety = _safe_dict(packet.get("safety_boundaries"))
    for field in (
        "offline_only",
        "local_only",
        "manual_review_only",
        "not_truth_source",
        "not_trading_advice",
        "not_execution_authority",
        "no_recommendations",
        "no_outcome_estimates",
        "no_value_scoring",
        "no_trade_or_wallet_instructions",
    ):
        if safety.get(field) is not True:
            errors.append(
                _queue_issue(
                    f"batch_packet_safety_boundary_not_true:{field}",
                    packet_artifact_status["path"],
                    f"Batch packet safety boundary {field} must be true.",
                )
            )
    return sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))


def build_manual_llm_review_queue(root=ROOT, candidates=None):
    root = Path(root)
    if candidates is None:
        candidates, discovery, preloaded_payloads = discover_default_candidates(root)
    else:
        candidates = dedupe_candidates_by_market_id(list(candidates))
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
        "truth_inference": False,
        "next_safe_operator_action": (
            "Use ready local candidates only for manual packet export, then rerun this queue exporter."
        ),
    }


def _compact_queue_item(item):
    return {
        "market_id": item.get("market_id", ""),
        "candidate_source_type": item.get("candidate_source_type", item.get("candidate_source", "")),
        "source_artifact_path": item.get("source_artifact_path", ""),
        "source_count": item.get("source_count", 1),
        "packet_path": item.get("packet_path", ""),
        "packet_present": bool(item.get("packet_present", False)),
        "prompt_path": item.get("prompt_path", ""),
        "prompt_present": bool(item.get("prompt_present", False)),
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
        "added_candidate_market_ids": [],
        "skipped_candidate_count": 0,
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
        "added_candidate_market_ids": [
            str(item) for item in _safe_list(discovery.get("added_candidate_market_ids"))
        ],
        "skipped_candidate_count": int(discovery.get("skipped_candidate_count") or 0)
        if not isinstance(discovery.get("skipped_candidate_count"), bool)
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
                    f"  candidate_source_type: {item['candidate_source_type']}",
                    f"  source_count: {item['source_count']}",
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
            f"- skipped_candidate_count: {discovery['skipped_candidate_count']}",
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
        "added_candidate_market_ids": queue["candidate_discovery"]["added_candidate_market_ids"],
        "skipped_candidate_count": queue["candidate_discovery"]["skipped_candidate_count"],
        "warnings": queue["warnings"],
        "blockers": queue["errors"],
        "safety_flags": dict(SAFETY_FLAGS),
        "network_calls": 0,
        "llm_api_calls": 0,
        "browser_automation": False,
        "prompt_automation": False,
        "runtime_wiring": False,
        "truth_inference": False,
        "next_recommended_task": "PMBOT-LLM-015-MANUAL-PACKET-BATCH-EXPORT",
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
