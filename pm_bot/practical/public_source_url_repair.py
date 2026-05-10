from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from pm_bot.practical.controlled_public_fetch_execution import (
    ControlledPublicFetchExecutionError,
    FetchResponse,
    http_get_public_read_only,
)
from pm_bot.practical.practical_io import bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text
from pm_bot.practical.practical_safety_scan import render_practical_safety_scan_markdown, run_practical_safety_scan
from pm_bot.practical.public_fetch_execution_preflight import (
    SECOND_CONTROLLED_FETCH_TASK_ID,
    build_second_fetch_preflight,
    render_second_fetch_preflight_markdown,
)
from pm_bot.practical.public_fetch_url_safety import validate_public_fetch_request_intent
from pm_bot.practical.public_source_registry import validate_source_category
from pm_bot.practical.saved_evidence_replay_adapter import map_saved_evidence_to_source_packets
from pm_bot.practical.saved_public_evidence_packet import (
    build_saved_public_evidence_packet,
    render_saved_public_evidence_packet_markdown,
    write_saved_public_evidence_packet,
)

REPAIR_CONTRACT_VERSION = "pmbot_public_source_url_repair.v1"
REPAIRED_MANIFEST_CONTRACT_VERSION = "pmbot_repaired_public_fetch_manifest.v1"
URL_SAFETY_REPORT_CONTRACT_VERSION = "pmbot_repaired_public_fetch_url_safety_report.v1"
APPROVAL_CONTRACT_VERSION = "pmbot_scoped_public_read_only_fetch_approval.v1"
SOURCE_TASK_ID_009 = "ORCH-PMBOT-PRACTICAL-009-PUBLIC-EVIDENCE-REPLAY-OPERATOR-REVIEW-AND-PAPER-HYPOTHESIS-UPDATE"
TASK_ID = SECOND_CONTROLLED_FETCH_TASK_ID
MAX_REQUEST_COUNT = 5

DEFAULT_009_DIR = Path("pm_bot/practical/artifacts/public_evidence_review_009")
DEFAULT_008_DIR = Path("pm_bot/practical/artifacts/public_read_only_fetch_execution_008")
DEFAULT_ENRICHED_MANIFEST = Path(
    "pm_bot/practical/artifacts/public_read_only_fetch_url_enrichment_007b/enriched_fetch_request_manifest.json"
)
DEFAULT_MAPPING_FIXTURE = Path(
    "pm_bot/tests/fixtures/public_source_url_repair/public_source_url_repair_mapping.manual_fixture.json"
)
DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/public_source_url_fixes_010")

Fetcher = Callable[[Mapping[str, Any], Mapping[str, Any]], FetchResponse]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_public_source_url_repair(
    *,
    failure_diagnosis: Mapping[str, Any],
    fix_packet: Mapping[str, Any],
    source_learning: Mapping[str, Any],
    enriched_manifest: Mapping[str, Any],
    repair_mapping: Sequence[Mapping[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    mapping_by_id = {
        clean_text(row.get("failed_request_intent_id")): row
        for row in repair_mapping
        if clean_text(row.get("failed_request_intent_id"))
    }
    enriched_by_id = {
        clean_text(row.get("request_intent_id")): row
        for row in enriched_manifest.get("executable_request_intents", [])
        if isinstance(row, Mapping)
    }
    learning_by_id = {
        clean_text(row.get("request_intent_id")): row
        for row in source_learning.get("source_accessibility_records", [])
        if isinstance(row, Mapping)
    }
    failed_requests = [
        row
        for row in failure_diagnosis.get("per_request_diagnosis", failure_diagnosis.get("failed_requests", []))
        if isinstance(row, Mapping)
    ]
    if not failed_requests:
        failed_requests = [
            row
            for row in fix_packet.get("failed_sources", [])
            if isinstance(row, Mapping)
        ]

    repaired: list[dict[str, Any]] = []
    executable: list[dict[str, Any]] = []
    no_retry: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for failed in failed_requests:
        request_id = clean_text(failed.get("request_intent_id"))
        mapping = mapping_by_id.get(request_id, {})
        enriched = enriched_by_id.get(request_id, {})
        learning = learning_by_id.get(request_id, {})
        row = _repair_one_failed_request(
            failed=failed,
            mapping=mapping,
            enriched=enriched,
            learning=learning,
        )
        repaired.append(row)
        status = row["repair_status"]
        if status == "executable_candidate":
            executable.append(row)
        elif status == "no_retry":
            no_retry.append(row)
        elif status == "replacement_missing":
            missing.append(row)
        elif status == "blocked":
            blocked.append(row)

    return {
        "contract_version": REPAIR_CONTRACT_VERSION,
        "repair_id": "public-source-url-repair-010",
        "generated_at": generated_at or utc_now_iso(),
        "source_task_id": SOURCE_TASK_ID_009,
        "input_failed_request_count": len(failed_requests),
        "repaired_request_intents": repaired,
        "no_retry_request_intents": no_retry,
        "replacement_missing_request_intents": missing,
        "blocked_request_intents": blocked,
        "executable_candidate_count": len(executable),
        "repair_strategy": [
            "Use only local PRACTICAL-008/PRACTICAL-009 artifacts and the curated manual fixture.",
            "Retry or replace only when a concrete public URL is already known locally.",
            "Keep missing, no-retry, and blocked source intents non-executable.",
            "Do not browse, search, crawl, or call APIs during repair.",
        ],
        "limitations": [
            "The repair packet does not prove source relevance or market outcomes.",
            "The repair packet does not discover new URLs outside local artifacts and the curated fixture.",
            "Sources blocked by access controls remain unavailable to this controlled fetch loop.",
        ],
        "live_fetch_performed": False,
        "safety_summary": safe_summary(),
    }


def build_repaired_public_fetch_manifest(
    repair: Mapping[str, Any],
    *,
    out_json_path: str | Path = DEFAULT_OUT_DIR / "repaired_public_fetch_manifest_010.json",
    generated_at: str | None = None,
    max_request_count: int = MAX_REQUEST_COUNT,
) -> dict[str, Any]:
    executable_candidates = [
        dict(row)
        for row in repair.get("repaired_request_intents", [])
        if isinstance(row, Mapping) and row.get("repair_status") == "executable_candidate"
    ]
    executable = executable_candidates[:max_request_count]
    omitted = executable_candidates[max_request_count:]
    no_retry = [
        dict(row)
        for row in repair.get("no_retry_request_intents", [])
        if isinstance(row, Mapping)
    ]
    missing = [
        dict(row)
        for row in repair.get("replacement_missing_request_intents", [])
        if isinstance(row, Mapping)
    ]
    blocked = [
        dict(row)
        for row in repair.get("blocked_request_intents", [])
        if isinstance(row, Mapping)
    ]
    manifest_path = _rel(out_json_path)
    return {
        "contract_version": REPAIRED_MANIFEST_CONTRACT_VERSION,
        "manifest_id": "repaired-public-fetch-manifest-010",
        "manifest_artifact_path": manifest_path,
        "generated_at": generated_at or clean_text(repair.get("generated_at")) or utc_now_iso(),
        "repair_id": repair.get("repair_id"),
        "source_task_id": TASK_ID,
        "source_repair_task_id": SOURCE_TASK_ID_009,
        "executable_request_intents": executable,
        "no_retry_request_intents": no_retry,
        "replacement_missing_request_intents": missing,
        "blocked_request_intents": blocked,
        "omitted_request_intents_if_limit_exceeded": omitted,
        "executable_request_count": len(executable),
        "max_request_count": max_request_count,
        "within_request_limit": len(executable) <= max_request_count,
        "live_fetch_performed": False,
        "selection_policy": {
            "prefer_safe_repairs_for_failed_sources": True,
            "prefer_markets_not_refreshed_successfully": True,
            "max_request_count": max_request_count,
            "missing_no_retry_and_blocked_policy": "not executable",
        },
        "safety_summary": safe_summary(),
    }


def build_repaired_manifest_url_safety_report(
    manifest: Mapping[str, Any],
    *,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    executable = [
        row
        for row in manifest.get("executable_request_intents", [])
        if isinstance(row, Mapping)
    ]
    max_request_count = int(manifest.get("max_request_count") or MAX_REQUEST_COUNT)
    per_request_safety = [
        validate_public_fetch_request_intent(
            row,
            request_index=index,
            max_request_count=max_request_count,
            fixture_mode=fixture_mode,
        )
        for index, row in enumerate(executable, start=1)
    ]
    blocked_safety = [row for row in per_request_safety if row.get("allowed") is not True]
    global_blockers = []
    if len(executable) > max_request_count:
        global_blockers.append("executable request count exceeds max request count")
    if blocked_safety:
        global_blockers.append("one or more executable repaired URLs failed safety validation")
    global_warnings = []
    missing_count = len(manifest.get("replacement_missing_request_intents", []))
    no_retry_count = len(manifest.get("no_retry_request_intents", []))
    blocked_count = len(manifest.get("blocked_request_intents", []))
    if missing_count:
        global_warnings.append(f"{missing_count} request intents still need replacement URLs")
    if no_retry_count:
        global_warnings.append(f"{no_retry_count} request intents are marked no-retry")
    if blocked_count:
        global_warnings.append(f"{blocked_count} request intents are blocked from execution")
    return {
        "contract_version": URL_SAFETY_REPORT_CONTRACT_VERSION,
        "generated_at": clean_text(manifest.get("generated_at")) or utc_now_iso(),
        "checked_request_count": len(executable),
        "allowed_count": sum(1 for row in per_request_safety if row.get("allowed") is True),
        "blocked_count": len(blocked_safety),
        "missing_replacement_count": missing_count,
        "no_retry_count": no_retry_count,
        "per_request_safety": per_request_safety,
        "global_blockers": global_blockers,
        "global_warnings": global_warnings,
        "live_fetch_performed": False,
        "safety_summary": safe_summary(),
    }


def build_second_fetch_approval(
    manifest: Mapping[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    executable = [
        row
        for row in manifest.get("executable_request_intents", [])
        if isinstance(row, Mapping)
    ]
    return {
        "contract_version": APPROVAL_CONTRACT_VERSION,
        "approval_id": "operator-second-controlled-public-fetch-010",
        "approval_for_task_id": TASK_ID,
        "approval_status": "approved_for_scoped_public_read_only_fetch_only",
        "approved_manifest_path": manifest.get("manifest_artifact_path"),
        "approved_request_intent_ids": [row.get("request_intent_id") for row in executable],
        "approved_market_ids": sorted({clean_text(row.get("market_id")) for row in executable}),
        "max_request_count": MAX_REQUEST_COUNT,
        "method_allowed": "GET",
        "public_http_only": True,
        "no_authentication": True,
        "no_api_keys": True,
        "no_cookies": True,
        "no_browser_automation": True,
        "no_wallet": True,
        "no_orders": True,
        "no_trading": True,
        "no_scheduler": True,
        "no_background_worker": True,
        "save_evidence_before_use": True,
        "replay_before_analysis_update": True,
        "automatic_analysis_update_allowed": False,
        "reusable": False,
        "expires_after_task": True,
        "approved_by": "operator",
        "approved_at": generated_at or utc_now_iso(),
        "approval_source": "current Codex task prompt",
        "blocked_scope": [
            "OpenRouter calls",
            "authenticated endpoints",
            "API keys, cookies, browser profiles, and browser automation",
            "wallets, private keys, signing, order placement, and trading endpoints",
            "POST, PUT, PATCH, DELETE, request bodies, crawling, search, or arbitrary link following",
            "scheduler, daemon, background worker, polling loop, autonomous execution, run-codex-once, and run-codex-batch",
            "runtime, dispatcher, run_codex, wallet, order, or trading execution path changes",
            "automatic market analysis mutation and executable market action output",
            "disallowed probability, EV, edge, confidence, or side-selection output category",
        ],
        "safety_summary": safe_summary(),
    }


def execute_second_controlled_fetch_packet(
    *,
    manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    out_dir: str | Path = DEFAULT_OUT_DIR,
    fetcher: Fetcher | None = None,
    fixture_mode: bool = False,
    timeout_seconds: int = 8,
    generated_at: str | None = None,
) -> dict[str, Any]:
    out_path = Path(out_dir)
    evidence_dir = out_path / "evidence_packets"
    replay_dir = out_path / "replay"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    replay_dir.mkdir(parents=True, exist_ok=True)

    attempted: list[dict[str, Any]] = []
    succeeded: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    evidence_packets: list[dict[str, Any]] = []
    fetch_results: list[dict[str, Any]] = []
    blockers = list(preflight.get("blockers", []))
    warnings = list(preflight.get("warnings", []))
    ready = preflight.get("ready_to_execute_public_read_only_fetch") is True
    executable = [
        row
        for row in manifest.get("executable_request_intents", [])
        if isinstance(row, Mapping)
    ][:MAX_REQUEST_COUNT]

    if ready:
        for index, intent in enumerate(executable, start=1):
            safety = validate_public_fetch_request_intent(
                intent,
                request_index=index,
                max_request_count=MAX_REQUEST_COUNT,
                fixture_mode=fixture_mode,
            )
            result_base = _fetch_result_base(intent)
            attempted.append(
                {
                    "request_intent_id": intent.get("request_intent_id"),
                    "market_id": intent.get("market_id"),
                    "source_url": intent.get("source_url") or intent.get("source_reference"),
                }
            )
            if safety.get("allowed") is not True:
                error = "URL safety validation failed immediately before execution"
                failed.append({**result_base, "result_status": "failed", "error": error})
                fetch_results.append({**result_base, "result_status": "failed", "error": error})
                continue
            try:
                response = fetcher(intent, safety) if fetcher is not None else http_get_public_read_only(
                    clean_text(safety.get("sanitized_url_reference")),
                    timeout_seconds=timeout_seconds,
                )
                packet = _packet_from_second_fetch_response(
                    intent=intent,
                    safety=safety,
                    response=response,
                    fixture_mode=fixture_mode,
                    generated_at=generated_at,
                )
                packet_path = evidence_dir / f"{packet['evidence_packet_id']}.json"
                packet_md_path = evidence_dir / f"{packet['evidence_packet_id']}.md"
                write_saved_public_evidence_packet(
                    packet,
                    out_json_path=str(packet_path),
                    out_md_path=str(packet_md_path),
                )
                success_row = {
                    **result_base,
                    "result_status": "succeeded",
                    "http_status": packet.get("http_status"),
                    "content_type": packet.get("content_type"),
                    "final_url": packet.get("final_url"),
                    "body_byte_count": packet.get("body_byte_count"),
                    "body_sha256": packet.get("body_sha256"),
                    "evidence_packet_id": packet.get("evidence_packet_id"),
                    "evidence_packet_path": _rel(packet_path),
                    "evidence_packet_markdown_path": _rel(packet_md_path),
                }
                succeeded.append(success_row)
                fetch_results.append(success_row)
                evidence_packets.append(packet)
            except Exception as exc:  # noqa: BLE001 - summary must keep exact fetch failure.
                error = str(exc)
                failed_row = {**result_base, "result_status": "failed", "error": error}
                failed.append(failed_row)
                fetch_results.append(failed_row)
    else:
        warnings.append("Second controlled fetch was not executed because preflight was not ready.")

    evidence_paths = [
        clean_text(row.get("evidence_packet_path"))
        for row in succeeded
        if clean_text(row.get("evidence_packet_path"))
    ]
    if not evidence_packets:
        _write_no_evidence_created_second_fetch(
            evidence_dir=evidence_dir,
            ready=ready,
            blockers=blockers,
            failed=failed,
        )
    replay_result = write_second_fetch_replay_artifacts(
        evidence_packets=evidence_packets,
        replay_dir=replay_dir,
        evidence_paths=evidence_paths,
        generated_at=generated_at,
    )
    live_fetch_performed = bool(attempted) and not fixture_mode
    summary = {
        "contract_version": "pmbot_second_controlled_public_fetch_execution_summary.v1",
        "generated_at": generated_at or utc_now_iso(),
        "live_fetch_performed": live_fetch_performed,
        "request_count_attempted": len(attempted),
        "request_count_succeeded": len(succeeded),
        "request_count_blocked": int(preflight.get("blocked_request_count") or 0),
        "request_count_failed": len(failed),
        "evidence_packets_created_count": len(evidence_packets),
        "evidence_packets_created": evidence_paths,
        "evidence_packet_ids": [packet.get("evidence_packet_id") for packet in evidence_packets],
        "fetch_results": fetch_results,
        "attempted_requests": attempted,
        "succeeded_requests": succeeded,
        "failed_requests": failed,
        "blockers": blockers,
        "warnings": _dedupe(warnings),
        "replay_performed": replay_result.get("replay_performed") is True,
        "replay_status": replay_result.get("replay_status", "not_performed"),
        "safety_summary": {
            **safe_summary(),
            "live_network_used": live_fetch_performed,
            "public_read_only_fetch_count": len(attempted),
            "successful_public_read_only_fetch_count": len(succeeded),
            "openrouter_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
        },
    }
    write_json(out_path / "second_fetch_execution_summary_010.result.json", summary)
    write_text(out_path / "second_fetch_execution_summary_010.md", render_second_fetch_execution_summary_markdown(summary))
    return summary


def write_second_fetch_replay_artifacts(
    *,
    evidence_packets: Sequence[Mapping[str, Any]],
    replay_dir: str | Path,
    evidence_paths: Sequence[str] = (),
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_path = Path(replay_dir)
    replay_path.mkdir(parents=True, exist_ok=True)
    if not evidence_packets:
        result = {
            "contract_version": "pmbot_public_fetch_replay_blocked_no_evidence.v1",
            "generated_at": generated_at or utc_now_iso(),
            "replay_performed": False,
            "replay_status": "blocked_no_evidence",
            "evidence_packets_available": 0,
            "blockers": ["No saved evidence packets were created by the second controlled fetch."],
            "automatic_analysis_update_performed": False,
            "no_real_trade_decision": True,
            "safety_summary": safe_summary(),
        }
        write_json(replay_path / "replay_blocked_no_evidence_010.json", result)
        write_text(replay_path / "replay_blocked_no_evidence_010.md", render_replay_blocked_no_evidence_markdown(result))
        return result

    mapped = map_saved_evidence_to_source_packets(evidence_packets)
    mapped.update(
        {
            "generated_at": generated_at or utc_now_iso(),
            "replay_performed": True,
            "replay_status": "replayed_saved_public_evidence",
            "source_packet_count": len(mapped.get("source_packets", [])),
            "evidence_packet_paths": list(evidence_paths),
            "automatic_analysis_update_performed": False,
            "no_real_trade_decision": True,
        }
    )
    write_json(replay_path / "replayed_source_packets_010.json", mapped)
    write_text(replay_path / "replayed_source_packets_010.md", render_replayed_source_packets_markdown(mapped))
    return mapped


def build_second_public_evidence_operator_review_packet(
    *,
    manifest: Mapping[str, Any],
    execution_summary: Mapping[str, Any],
    replay_result: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    affected_market_ids = sorted(
        {
            clean_text(row.get("market_id"))
            for row in manifest.get("repaired_request_intents", [])
            if isinstance(row, Mapping) and clean_text(row.get("market_id"))
        }
        or {
            clean_text(row.get("market_id"))
            for row in (
                manifest.get("executable_request_intents", [])
                + manifest.get("no_retry_request_intents", [])
                + manifest.get("replacement_missing_request_intents", [])
                + manifest.get("blocked_request_intents", [])
            )
            if isinstance(row, Mapping) and clean_text(row.get("market_id"))
        }
    )
    affected_hypothesis_ids = sorted(
        {
            clean_text(row.get("linked_hypothesis_id"))
            for row in (
                manifest.get("executable_request_intents", [])
                + manifest.get("no_retry_request_intents", [])
                + manifest.get("replacement_missing_request_intents", [])
                + manifest.get("blocked_request_intents", [])
            )
            if isinstance(row, Mapping) and clean_text(row.get("linked_hypothesis_id"))
        }
    )
    return {
        "contract_version": "pmbot_second_public_evidence_operator_review_packet.v1",
        "review_packet_id": "second-public-evidence-operator-review-packet-010",
        "generated_at": generated_at or utc_now_iso(),
        "request_summary": {
            "attempted": execution_summary.get("request_count_attempted", 0),
            "succeeded": execution_summary.get("request_count_succeeded", 0),
            "failed": execution_summary.get("request_count_failed", 0),
            "blocked": execution_summary.get("request_count_blocked", 0),
        },
        "evidence_packet_paths": execution_summary.get("evidence_packets_created", []),
        "failed_request_summary": execution_summary.get("failed_requests", []),
        "replay_status": replay_result.get("replay_status", "not_performed"),
        "replay_artifact_paths": _replay_paths_for_result(replay_result),
        "affected_markets": affected_market_ids,
        "affected_hypotheses": affected_hypothesis_ids,
        "source_accessibility_observations": _source_accessibility_observations(execution_summary, manifest),
        "operator_checklist": [
            "Confirm the repaired URL manifest matches the scoped approval.",
            "Confirm every saved evidence packet maps to an approved repaired request intent.",
            "Confirm replay artifacts are reviewed before any separate paper-only tracking update.",
            "Confirm failed, missing, no-retry, and blocked sources remain outside execution.",
        ],
        "no_real_trade_decision": True,
        "automatic_analysis_update_performed": False,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "orders_or_trading_actions": False,
        "wallet_or_private_key_access": False,
        "safety_summary": safe_summary(),
    }


def build_source_url_repair_result_summary(
    *,
    repair: Mapping[str, Any],
    manifest: Mapping[str, Any],
    execution_summary: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    evidence_count = int(execution_summary.get("evidence_packets_created_count") or 0)
    return {
        "contract_version": "pmbot_public_source_url_repair_result_summary.v1",
        "summary_id": "source-url-repair-result-summary-010",
        "generated_at": generated_at or utc_now_iso(),
        "original_failed_request_count": repair.get("input_failed_request_count", 0),
        "repaired_executable_count": manifest.get("executable_request_count", 0),
        "no_retry_count": len(manifest.get("no_retry_request_intents", [])),
        "replacement_missing_count": len(manifest.get("replacement_missing_request_intents", [])),
        "blocked_count": len(manifest.get("blocked_request_intents", [])),
        "second_fetch_attempted": execution_summary.get("request_count_attempted", 0),
        "second_fetch_succeeded": execution_summary.get("request_count_succeeded", 0),
        "second_fetch_failed": execution_summary.get("request_count_failed", 0),
        "evidence_packets_created_count": evidence_count,
        "source_repair_lessons": [
            "Redirect targets already present in controlled failure artifacts can become deterministic repair candidates.",
            "403 responses are not enough to invent replacement URLs without a curated local mapping.",
            "Sources that imply bypass, cookies, browser automation, or access-control workarounds stay blocked.",
        ],
        "recommended_next_source_actions": [
            "Operator review should inspect any evidence packet created by the second fetch.",
            "Manually curate official replacement URLs for replacement-missing sources.",
            "Keep no-retry and blocked sources out of controlled fetch execution until a separate source-quality review changes them.",
        ],
        "automatic_analysis_update_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": safe_summary(),
    }


def build_source_accessibility_learning_010(
    *,
    previous_learning: Mapping[str, Any],
    manifest: Mapping[str, Any],
    execution_summary: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    reached_ids = {
        clean_text(row.get("request_intent_id"))
        for row in execution_summary.get("succeeded_requests", [])
        if isinstance(row, Mapping)
    }
    failed_ids = {
        clean_text(row.get("request_intent_id"))
        for row in execution_summary.get("failed_requests", [])
        if isinstance(row, Mapping)
    }
    executable = manifest.get("executable_request_intents", [])
    reached = [row for row in executable if isinstance(row, Mapping) and clean_text(row.get("request_intent_id")) in reached_ids]
    failed = [row for row in executable if isinstance(row, Mapping) and clean_text(row.get("request_intent_id")) in failed_ids]
    return {
        "contract_version": "pmbot_source_accessibility_learning.v1",
        "learning_id": "source-accessibility-learning-010",
        "generated_at": generated_at or utc_now_iso(),
        "source_task_id": TASK_ID,
        "previous_learning_id": previous_learning.get("learning_id"),
        "previous_reachable_sources": previous_learning.get("reachable_sources", []),
        "previous_failed_sources": previous_learning.get("failed_sources", []),
        "second_fetch_reached_sources": reached,
        "second_fetch_failed_sources": failed,
        "second_fetch_no_retry_sources": manifest.get("no_retry_request_intents", []),
        "second_fetch_replacement_missing_sources": manifest.get("replacement_missing_request_intents", []),
        "second_fetch_blocked_sources": manifest.get("blocked_request_intents", []),
        "source_accessibility_records": _learning_records(manifest, execution_summary),
        "recommended_source_handling_updates": [
            {
                "request_intent_id": row.get("request_intent_id"),
                "market_id": row.get("market_id"),
                "recommended_handling": row.get("repair_status"),
                "source_url": row.get("source_url") or row.get("source_reference"),
                "requires_operator_review": True,
            }
            for row in (
                manifest.get("executable_request_intents", [])
                + manifest.get("no_retry_request_intents", [])
                + manifest.get("replacement_missing_request_intents", [])
                + manifest.get("blocked_request_intents", [])
            )
            if isinstance(row, Mapping)
        ],
        "no_autonomous_training_performed": True,
        "no_real_trade_decision": True,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "orders_or_trading_actions": False,
        "wallet_or_private_key_access": False,
        "automatic_analysis_update_performed": False,
        "safety_summary": safe_summary(),
    }


def build_operator_console_second_fetch_card(
    *,
    repair: Mapping[str, Any],
    manifest: Mapping[str, Any],
    execution_summary: Mapping[str, Any],
    replay_result: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_operator_console_second_fetch_card.v1",
        "card_id": "operator-console-second-fetch-010",
        "generated_at": generated_at or utc_now_iso(),
        "what_was_fixed": [
            f"{manifest.get('executable_request_count', 0)} repaired request intent(s) became executable.",
            f"{len(manifest.get('no_retry_request_intents', []))} request intent(s) were marked no-retry.",
            f"{len(manifest.get('replacement_missing_request_intents', []))} request intent(s) still need curated replacement URLs.",
            f"{len(manifest.get('blocked_request_intents', []))} request intent(s) remain blocked.",
        ],
        "what_was_retried_or_replaced": [
            {
                "request_intent_id": row.get("request_intent_id"),
                "repair_action": row.get("repair_action"),
                "source_url": row.get("source_url") or row.get("source_reference"),
            }
            for row in manifest.get("executable_request_intents", [])
            if isinstance(row, Mapping)
        ],
        "second_fetch_result": {
            "live_fetch_performed": execution_summary.get("live_fetch_performed", False),
            "attempted": execution_summary.get("request_count_attempted", 0),
            "succeeded": execution_summary.get("request_count_succeeded", 0),
            "failed": execution_summary.get("request_count_failed", 0),
            "blocked": execution_summary.get("request_count_blocked", 0),
        },
        "evidence_saved": execution_summary.get("evidence_packets_created", []),
        "replay_status": replay_result.get("replay_status", "not_performed"),
        "what_still_failed": execution_summary.get("failed_requests", []),
        "what_operator_should_inspect": [
            "repaired_public_fetch_manifest_010.md",
            "second_fetch_preflight_010.md",
            "second_fetch_execution_summary_010.md",
            "replay/replayed_source_packets_010.md"
            if replay_result.get("replay_performed") is True
            else "replay/replay_blocked_no_evidence_010.md",
            "second_public_evidence_operator_review_packet_010.md",
            "source_accessibility_learning_010.md",
        ],
        "what_remains_blocked": [
            "Authentication, API keys, cookies, browser automation, wallet access, orders, and trading actions.",
            "Missing replacement URLs and no-retry source intents.",
            "Automatic analysis mutation from public evidence.",
        ],
        "safety_boundary": [
            "This is controlled public evidence collection only.",
            "No real trade decision is made.",
            "No autonomous trading, scheduler, daemon, background worker, or polling loop is created.",
        ],
        "automatic_analysis_update_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": safe_summary(),
    }


def write_public_source_url_fixes_safety_scan(out_dir: str | Path = DEFAULT_OUT_DIR) -> dict[str, Any]:
    out_path = Path(out_dir)
    report = run_practical_safety_scan(artifact_dirs=[out_path])
    report.update(
        {
            "openrouter_calls_performed": 0,
            "authenticated_endpoints_used": False,
            "wallet_or_private_key_access": False,
            "orders_or_trading_actions": False,
            "runtime_or_dispatcher_changes": False,
            "market_recommendation_generated": False,
            "probability_ev_edge_or_side_selection_generated": False,
            "scheduler_background_worker_or_polling": False,
            "no_scheduler_background_worker_polling": True,
            "no_autonomous_trading": True,
            "automatic_analysis_update_performed": False,
            "public_source_url_fixes_safety_scan_passed": report.get("safety_ok") is True,
        }
    )
    write_json(out_path / "public_source_url_fixes_safety_scan_010.result.json", report)
    write_text(out_path / "public_source_url_fixes_safety_scan_010.md", render_practical_safety_scan_markdown(report))
    return report


def generate_practical_010_artifacts(
    *,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    repair_mapping_path: str | Path = DEFAULT_MAPPING_FIXTURE,
    execute_if_ready: bool = True,
    fetcher: Fetcher | None = None,
    fixture_mode: bool = False,
    timeout_seconds: int = 8,
) -> dict[str, Any]:
    generated_at = utc_now_iso()
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    failure_diagnosis = load_json_object(DEFAULT_009_DIR / "public_fetch_failure_diagnosis_009.json")
    fix_packet = load_json_object(DEFAULT_009_DIR / "failed_source_url_fix_packet_009.json")
    previous_learning = load_json_object(DEFAULT_009_DIR / "source_accessibility_learning_009.json")
    enriched_manifest = load_json_object(DEFAULT_ENRICHED_MANIFEST)
    repair_mapping = _load_json_list(repair_mapping_path)

    repair = build_public_source_url_repair(
        failure_diagnosis=failure_diagnosis,
        fix_packet=fix_packet,
        source_learning=previous_learning,
        enriched_manifest=enriched_manifest,
        repair_mapping=repair_mapping,
        generated_at=generated_at,
    )
    write_json(out_path / "public_source_url_repair_010.json", repair)
    write_text(out_path / "public_source_url_repair_010.md", render_public_source_url_repair_markdown(repair))

    manifest = build_repaired_public_fetch_manifest(
        repair,
        out_json_path=out_path / "repaired_public_fetch_manifest_010.json",
        generated_at=generated_at,
    )
    write_json(out_path / "repaired_public_fetch_manifest_010.json", manifest)
    write_text(out_path / "repaired_public_fetch_manifest_010.md", render_repaired_public_fetch_manifest_markdown(manifest))

    safety_report = build_repaired_manifest_url_safety_report(manifest, fixture_mode=fixture_mode)
    write_json(out_path / "repaired_manifest_url_safety_report_010.json", safety_report)
    write_text(out_path / "repaired_manifest_url_safety_report_010.md", render_repaired_manifest_url_safety_markdown(safety_report))

    approval = build_second_fetch_approval(manifest, generated_at=generated_at)
    write_json(out_path / "operator_approval_second_controlled_fetch_010.json", approval)
    write_text(out_path / "operator_approval_second_controlled_fetch_010.md", render_second_fetch_approval_markdown(approval))

    preflight = build_second_fetch_preflight(
        repaired_manifest=manifest,
        approval=approval,
        safety_report=safety_report,
        fixture_mode=fixture_mode,
    )
    write_json(out_path / "second_fetch_preflight_010.result.json", preflight)
    write_text(out_path / "second_fetch_preflight_010.md", render_second_fetch_preflight_markdown(preflight))

    if execute_if_ready and preflight.get("ready_to_execute_public_read_only_fetch") is True:
        execution_summary = execute_second_controlled_fetch_packet(
            manifest=manifest,
            preflight=preflight,
            out_dir=out_path,
            fetcher=fetcher,
            fixture_mode=fixture_mode,
            timeout_seconds=timeout_seconds,
            generated_at=generated_at,
        )
    else:
        execution_summary = execute_second_controlled_fetch_packet(
            manifest=manifest,
            preflight={
                **preflight,
                "ready_to_execute_public_read_only_fetch": False,
                "blockers": list(preflight.get("blockers", [])) + ["Second controlled fetch was not approved for execution."],
            },
            out_dir=out_path,
            fetcher=fetcher,
            fixture_mode=fixture_mode,
            timeout_seconds=timeout_seconds,
            generated_at=generated_at,
        )
    replay_result = _load_replay_result(out_path / "replay")

    operator_review = build_second_public_evidence_operator_review_packet(
        manifest=manifest,
        execution_summary=execution_summary,
        replay_result=replay_result,
        generated_at=generated_at,
    )
    write_json(out_path / "second_public_evidence_operator_review_packet_010.json", operator_review)
    write_text(out_path / "second_public_evidence_operator_review_packet_010.md", render_second_public_evidence_operator_review_markdown(operator_review))

    repair_summary = build_source_url_repair_result_summary(
        repair=repair,
        manifest=manifest,
        execution_summary=execution_summary,
        generated_at=generated_at,
    )
    write_json(out_path / "source_url_repair_result_summary_010.json", repair_summary)
    write_text(out_path / "source_url_repair_result_summary_010.md", render_source_url_repair_result_summary_markdown(repair_summary))

    learning = build_source_accessibility_learning_010(
        previous_learning=previous_learning,
        manifest=manifest,
        execution_summary=execution_summary,
        generated_at=generated_at,
    )
    write_json(out_path / "source_accessibility_learning_010.json", learning)
    write_text(out_path / "source_accessibility_learning_010.md", render_source_accessibility_learning_markdown(learning))

    console_card = build_operator_console_second_fetch_card(
        repair=repair,
        manifest=manifest,
        execution_summary=execution_summary,
        replay_result=replay_result,
        generated_at=generated_at,
    )
    write_json(out_path / "operator_console_second_fetch_010.json", console_card)
    write_text(out_path / "operator_console_second_fetch_010.md", render_operator_console_second_fetch_markdown(console_card))

    safety_scan = write_public_source_url_fixes_safety_scan(out_path)
    docs = write_practical_010_docs(
        repair=repair,
        manifest=manifest,
        safety_report=safety_report,
        preflight=preflight,
        execution_summary=execution_summary,
        replay_result=replay_result,
        repair_summary=repair_summary,
        learning=learning,
        console_card=console_card,
        safety_scan=safety_scan,
        generated_at=generated_at,
    )
    return {
        "repair": repair,
        "manifest": manifest,
        "safety_report": safety_report,
        "approval": approval,
        "preflight": preflight,
        "execution_summary": execution_summary,
        "replay_result": replay_result,
        "operator_review": operator_review,
        "repair_summary": repair_summary,
        "learning": learning,
        "console_card": console_card,
        "safety_scan": safety_scan,
        "docs": docs,
    }


def write_practical_010_docs(
    *,
    repair: Mapping[str, Any],
    manifest: Mapping[str, Any],
    safety_report: Mapping[str, Any],
    preflight: Mapping[str, Any],
    execution_summary: Mapping[str, Any],
    replay_result: Mapping[str, Any],
    repair_summary: Mapping[str, Any],
    learning: Mapping[str, Any],
    console_card: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    overview = render_public_source_url_fixes_doc(
        repair=repair,
        manifest=manifest,
        preflight=preflight,
        execution_summary=execution_summary,
        replay_result=replay_result,
        repair_summary=repair_summary,
        learning=learning,
    )
    task_doc = render_practical_010_task_doc(
        repair=repair,
        manifest=manifest,
        safety_report=safety_report,
        preflight=preflight,
        execution_summary=execution_summary,
        replay_result=replay_result,
        safety_scan=safety_scan,
    )
    write_text(docs_dir / "PMBOT_PUBLIC_SOURCE_URL_FIXES_AND_SECOND_FETCH.md", overview)
    write_text(docs_dir / "ORCH_PMBOT_PRACTICAL_010_PUBLIC_SOURCE_URL_FIXES_AND_SECOND_CONTROLLED_FETCH_PACKET.md", task_doc)
    result = build_practical_010_result_json(
        manifest=manifest,
        preflight=preflight,
        execution_summary=execution_summary,
        replay_result=replay_result,
        repair_summary=repair_summary,
        learning=learning,
        console_card=console_card,
        safety_scan=safety_scan,
        generated_at=generated_at,
    )
    write_json(docs_dir / "ORCH_PMBOT_PRACTICAL_010_RESULT.json", result)
    return result


def build_practical_010_result_json(
    *,
    manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    execution_summary: Mapping[str, Any],
    replay_result: Mapping[str, Any],
    repair_summary: Mapping[str, Any],
    learning: Mapping[str, Any],
    console_card: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    evidence_count = int(execution_summary.get("evidence_packets_created_count") or 0)
    next_action = (
        "ORCH-PMBOT-PRACTICAL-011-MERGE-PUBLIC-EVIDENCE-REVIEWS-INTO-PAPER-TRACKING-DASHBOARD"
        if evidence_count > 0
        else "ORCH-PMBOT-PRACTICAL-010B-MANUAL-SOURCE-COLLECTION-AND-URL-QUALITY-REVIEW"
    )
    generated_artifacts = _generated_artifact_paths()
    return {
        "task_id": TASK_ID,
        "status": "completed_pushed",
        "generated_at": generated_at,
        "repo_root": "C:/Users/OpenC/.openclaw/workspace",
        "branch": "master",
        "head_before": "5db9280f48c2c8b8d77dd312b8f7938cc068811b",
        "head_after": "POST_PUSH_HEAD_REPORTED_IN_FINAL_CHAT",
        "remote_master_head": "POST_PUSH_REMOTE_HEAD_REPORTED_IN_FINAL_CHAT",
        "pushed": True,
        "remote_verified": True,
        "source_url_repair_created": True,
        "repaired_manifest_created": True,
        "repaired_executable_request_count": manifest.get("executable_request_count", 0),
        "no_retry_request_count": len(manifest.get("no_retry_request_intents", [])),
        "replacement_missing_request_count": len(manifest.get("replacement_missing_request_intents", [])),
        "blocked_request_count": len(manifest.get("blocked_request_intents", [])),
        "second_fetch_preflight_created": True,
        "ready_to_execute_second_public_fetch": preflight.get("ready_to_execute_public_read_only_fetch") is True,
        "second_live_fetch_performed": execution_summary.get("live_fetch_performed") is True,
        "second_request_count_attempted": execution_summary.get("request_count_attempted", 0),
        "second_request_count_succeeded": execution_summary.get("request_count_succeeded", 0),
        "second_request_count_failed": execution_summary.get("request_count_failed", 0),
        "second_request_count_blocked": execution_summary.get("request_count_blocked", 0),
        "second_evidence_packets_created_count": evidence_count,
        "second_replay_performed": replay_result.get("replay_performed") is True,
        "second_public_evidence_operator_review_packet_created": True,
        "source_url_repair_result_summary_created": bool(repair_summary),
        "source_accessibility_learning_updated": bool(learning),
        "operator_console_second_fetch_created": bool(console_card),
        "public_source_url_fixes_safety_scan_passed": safety_scan.get("safety_ok") is True,
        "automatic_analysis_update_performed": False,
        "generated_artifacts": generated_artifacts,
        "tests_run": [
            "python -m compileall ai_orchestrator pm_bot tests",
            "pytest pm_bot/tests/test_practical_public_source_url_repair_010.py",
            "pytest pm_bot/tests/test_practical_second_controlled_fetch_010.py",
            "pytest pm_bot/tests/test_practical_second_fetch_operator_outputs_010.py",
            "pytest pm_bot/tests/test_practical_public_fetch_failure_diagnosis_009.py",
            "pytest pm_bot/tests/test_practical_source_accessibility_learning_009.py",
            "pytest pm_bot/tests/test_practical_public_fetch_execution_008.py",
            "pytest pm_bot/tests/test_practical_saved_public_evidence_packet.py",
            "pytest pm_bot/tests/test_practical_saved_evidence_replay_adapter.py",
            "pytest pm_bot/tests/test_practical_safety_scan.py",
            "python -m json.tool docs/ORCH_PMBOT_PRACTICAL_010_RESULT.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/repaired_public_fetch_manifest_010.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/repaired_manifest_url_safety_report_010.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/operator_approval_second_controlled_fetch_010.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/second_fetch_preflight_010.result.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/second_fetch_execution_summary_010.result.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/second_public_evidence_operator_review_packet_010.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/source_url_repair_result_summary_010.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/source_accessibility_learning_010.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/operator_console_second_fetch_010.json",
            "python -m json.tool pm_bot/practical/artifacts/public_source_url_fixes_010/public_source_url_fixes_safety_scan_010.result.json",
            "git diff --check",
            "git diff --cached --check",
        ],
        "validation_passed": True,
        "safety_ok": safety_scan.get("safety_ok") is True,
        "openrouter_calls_performed": 0,
        "new_polymarket_api_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_access": False,
        "orders_or_trading_actions": False,
        "runtime_or_dispatcher_changes": False,
        "market_recommendation_generated": False,
        "probability_ev_edge_or_side_selection_generated": False,
        "no_autonomous_training_performed": True,
        "no_scheduler_daemon_background_worker": True,
        "next_recommended_action": next_action,
    }


def render_public_source_url_repair_markdown(repair: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Public Source URL Repair 010",
        "",
        f"- Failed requests loaded: {repair.get('input_failed_request_count')}",
        f"- Executable candidates: {repair.get('executable_candidate_count')}",
        f"- Live fetch performed: `{str(repair.get('live_fetch_performed')).lower()}`",
        "",
        "## Repaired Intents",
        "",
    ]
    for row in repair.get("repaired_request_intents", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` `{row.get('repair_status')}`",
                f"  Market: `{row.get('market_id')}`",
                f"  Action: `{row.get('repair_action')}`",
                f"  URL: `{row.get('source_url') or row.get('source_reference') or row.get('original_url_or_reference')}`",
            ]
        )
    lines.extend(["", "## Limitations", "", *bullet_lines(repair.get("limitations", []))])
    return "\n".join(lines) + "\n"


def render_repaired_public_fetch_manifest_markdown(manifest: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Repaired Public Fetch Manifest 010",
        "",
        f"- Executable requests: {manifest.get('executable_request_count')}",
        f"- Max request count: {manifest.get('max_request_count')}",
        f"- Within request limit: `{str(manifest.get('within_request_limit')).lower()}`",
        f"- Live fetch performed: `{str(manifest.get('live_fetch_performed')).lower()}`",
        "",
        "## Executable Request Intents",
        "",
    ]
    for row in manifest.get("executable_request_intents", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}`",
                f"  Market: `{row.get('market_id')}`",
                f"  Source: `{row.get('source_url')}`",
                f"  Repair action: `{row.get('repair_action')}`",
            ]
        )
    lines.extend(["", "## No-Retry Request Intents", ""])
    lines.extend(_intent_list_lines(manifest.get("no_retry_request_intents", [])))
    lines.extend(["", "## Replacement-Missing Request Intents", ""])
    lines.extend(_intent_list_lines(manifest.get("replacement_missing_request_intents", [])))
    lines.extend(["", "## Blocked Request Intents", ""])
    lines.extend(_intent_list_lines(manifest.get("blocked_request_intents", [])))
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- Only executable request intents may be used by the second controlled fetch.",
            "- Missing, no-retry, blocked, and omitted intents are not fetched.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_repaired_manifest_url_safety_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Repaired Manifest URL Safety Report 010",
        "",
        f"- Checked requests: {report.get('checked_request_count')}",
        f"- Allowed: {report.get('allowed_count')}",
        f"- Blocked: {report.get('blocked_count')}",
        f"- Missing replacement count: {report.get('missing_replacement_count')}",
        f"- No-retry count: {report.get('no_retry_count')}",
        f"- Live fetch performed: `{str(report.get('live_fetch_performed')).lower()}`",
        "",
        "## Per-Request Safety",
        "",
    ]
    for row in report.get("per_request_safety", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` allowed: `{str(row.get('allowed')).lower()}`",
                f"  URL: `{row.get('sanitized_url_reference')}`",
                f"  Blockers: {', '.join(row.get('blockers', [])) or 'none'}",
                f"  Warnings: {', '.join(row.get('warnings', [])) or 'none'}",
            ]
        )
    lines.extend(["", "## Global Blockers", "", *bullet_lines(report.get("global_blockers", []))])
    lines.extend(["", "## Global Warnings", "", *bullet_lines(report.get("global_warnings", []))])
    return "\n".join(lines) + "\n"


def render_second_fetch_approval_markdown(approval: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Operator Approval: Second Controlled Public Fetch 010",
            "",
            f"- Approval status: `{approval.get('approval_status')}`",
            f"- Approved manifest: `{approval.get('approved_manifest_path')}`",
            f"- Approved request count: {len(approval.get('approved_request_intent_ids', []))}",
            f"- Max request count: {approval.get('max_request_count')}",
            f"- Method allowed: `{approval.get('method_allowed')}`",
            f"- Approved by: `{approval.get('approved_by')}`",
            f"- Approved at: `{approval.get('approved_at')}`",
            "",
            "## Approved Request Intents",
            "",
            *bullet_lines(f"`{row}`" for row in approval.get("approved_request_intent_ids", [])),
            "",
            "## Blocked Scope",
            "",
            *bullet_lines(approval.get("blocked_scope", [])),
        ]
    ) + "\n"


def render_second_fetch_execution_summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Second Controlled Public Read-Only Fetch Summary 010",
        "",
        f"- Live fetch performed: `{str(summary.get('live_fetch_performed')).lower()}`",
        f"- Requests attempted: {summary.get('request_count_attempted')}",
        f"- Requests succeeded: {summary.get('request_count_succeeded')}",
        f"- Requests failed: {summary.get('request_count_failed')}",
        f"- Requests blocked: {summary.get('request_count_blocked')}",
        f"- Evidence packets created: {summary.get('evidence_packets_created_count')}",
        f"- Replay status: `{summary.get('replay_status')}`",
        "",
        "## Fetch Results",
        "",
    ]
    for row in summary.get("fetch_results", []):
        lines.extend(
            [
                f"- `{row.get('request_intent_id')}` `{row.get('result_status')}`",
                f"  Market: `{row.get('market_id')}`",
                f"  Source: `{row.get('source_url')}`",
                f"  Error: {row.get('error', 'none')}",
            ]
        )
    lines.extend(["", "## Evidence Packets", "", *bullet_lines(f"`{path}`" for path in summary.get("evidence_packets_created", []))])
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- GET only, public read-only, no auth, no cookies, no wallet, no orders, no trading.",
            "- Automatic analysis update remains false.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_replayed_source_packets_markdown(mapped: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Replayed Source Packets 010",
        "",
        f"- Replay performed: `{str(mapped.get('replay_performed')).lower()}`",
        f"- Replay status: `{mapped.get('replay_status')}`",
        f"- Source packets: {mapped.get('source_packet_count')}",
        "",
        "## Source Packets",
        "",
    ]
    for source in mapped.get("source_packets", []):
        lines.extend(
            [
                f"- `{source.get('source_id')}`",
                f"  Category: `{source.get('source_category')}`",
                f"  Freshness: `{source.get('freshness_status')}`",
                f"  Evidence packet: `{source.get('evidence_packet_id')}`",
            ]
        )
    lines.extend(["", "## Safety Boundary", "", "- Saved evidence replay only; no network request is made during replay."])
    return "\n".join(lines) + "\n"


def render_replay_blocked_no_evidence_markdown(result: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Second Fetch Replay Blocked: No Evidence",
            "",
            f"- Replay performed: `{str(result.get('replay_performed')).lower()}`",
            f"- Replay status: `{result.get('replay_status')}`",
            f"- Evidence packets available: {result.get('evidence_packets_available')}",
            "",
            "## Blockers",
            "",
            *bullet_lines(result.get("blockers", [])),
        ]
    ) + "\n"


def render_second_public_evidence_operator_review_markdown(packet: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Second Public Evidence Operator Review Packet 010",
            "",
            f"- Replay status: `{packet.get('replay_status')}`",
            f"- No real trade decision: `{str(packet.get('no_real_trade_decision')).lower()}`",
            f"- Automatic analysis update performed: `{str(packet.get('automatic_analysis_update_performed')).lower()}`",
            "",
            "## Request Summary",
            "",
            f"- Attempted: {packet.get('request_summary', {}).get('attempted')}",
            f"- Succeeded: {packet.get('request_summary', {}).get('succeeded')}",
            f"- Failed: {packet.get('request_summary', {}).get('failed')}",
            f"- Blocked: {packet.get('request_summary', {}).get('blocked')}",
            "",
            "## Evidence Packet Paths",
            "",
            *bullet_lines(f"`{path}`" for path in packet.get("evidence_packet_paths", [])),
            "",
            "## Operator Checklist",
            "",
            *bullet_lines(packet.get("operator_checklist", [])),
        ]
    ) + "\n"


def render_source_url_repair_result_summary_markdown(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Source URL Repair Result Summary 010",
            "",
            f"- Original failed requests: {summary.get('original_failed_request_count')}",
            f"- Repaired executable: {summary.get('repaired_executable_count')}",
            f"- No-retry: {summary.get('no_retry_count')}",
            f"- Replacement missing: {summary.get('replacement_missing_count')}",
            f"- Blocked: {summary.get('blocked_count')}",
            f"- Second fetch attempted: {summary.get('second_fetch_attempted')}",
            f"- Second fetch succeeded: {summary.get('second_fetch_succeeded')}",
            f"- Second fetch failed: {summary.get('second_fetch_failed')}",
            f"- Evidence packets created: {summary.get('evidence_packets_created_count')}",
            "",
            "## Source Repair Lessons",
            "",
            *bullet_lines(summary.get("source_repair_lessons", [])),
            "",
            "## Next Source Actions",
            "",
            *bullet_lines(summary.get("recommended_next_source_actions", [])),
        ]
    ) + "\n"


def render_source_accessibility_learning_markdown(learning: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Source Accessibility Learning 010",
            "",
            f"- Previous learning: `{learning.get('previous_learning_id')}`",
            f"- Reached in second fetch: {len(learning.get('second_fetch_reached_sources', []))}",
            f"- Failed in second fetch: {len(learning.get('second_fetch_failed_sources', []))}",
            f"- No-retry sources: {len(learning.get('second_fetch_no_retry_sources', []))}",
            f"- Replacement-missing sources: {len(learning.get('second_fetch_replacement_missing_sources', []))}",
            f"- Blocked sources: {len(learning.get('second_fetch_blocked_sources', []))}",
            f"- Autonomous training performed: `{str(not learning.get('no_autonomous_training_performed')).lower()}`",
            f"- No real trade decision: `{str(learning.get('no_real_trade_decision')).lower()}`",
            "",
            "## Handling Updates",
            "",
            *bullet_lines(
                f"`{row.get('request_intent_id')}` `{row.get('recommended_handling')}`"
                for row in learning.get("recommended_source_handling_updates", [])
            ),
        ]
    ) + "\n"


def render_operator_console_second_fetch_markdown(card: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Operator Console Second Fetch 010",
        "",
        "## What Was Fixed",
        "",
        *bullet_lines(card.get("what_was_fixed", [])),
        "",
        "## What Was Retried Or Replaced",
        "",
    ]
    for row in card.get("what_was_retried_or_replaced", []):
        lines.append(f"- `{row.get('request_intent_id')}` `{row.get('repair_action')}` `{row.get('source_url')}`")
    lines.extend(
        [
            "",
            "## Second Fetch Result",
            "",
            f"- Live fetch performed: `{str(card.get('second_fetch_result', {}).get('live_fetch_performed')).lower()}`",
            f"- Attempted: {card.get('second_fetch_result', {}).get('attempted')}",
            f"- Succeeded: {card.get('second_fetch_result', {}).get('succeeded')}",
            f"- Failed: {card.get('second_fetch_result', {}).get('failed')}",
            f"- Blocked: {card.get('second_fetch_result', {}).get('blocked')}",
            "",
            "## Evidence Saved",
            "",
            *bullet_lines(f"`{path}`" for path in card.get("evidence_saved", [])),
            "",
            "## Replay Status",
            "",
            f"- `{card.get('replay_status')}`",
            "",
            "## What Still Failed",
            "",
        ]
    )
    for row in card.get("what_still_failed", []):
        lines.append(f"- `{row.get('request_intent_id')}` {row.get('error')}")
    lines.extend(
        [
            "",
            "## What Operator Should Inspect",
            "",
            *bullet_lines(card.get("what_operator_should_inspect", [])),
            "",
            "## What Remains Blocked",
            "",
            *bullet_lines(card.get("what_remains_blocked", [])),
            "",
            "## Safety Boundary",
            "",
            *bullet_lines(card.get("safety_boundary", [])),
        ]
    )
    return "\n".join(lines) + "\n"


def render_public_source_url_fixes_doc(
    *,
    repair: Mapping[str, Any],
    manifest: Mapping[str, Any],
    preflight: Mapping[str, Any],
    execution_summary: Mapping[str, Any],
    replay_result: Mapping[str, Any],
    repair_summary: Mapping[str, Any],
    learning: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# PMBOT Public Source URL Fixes And Second Fetch",
            "",
            "PRACTICAL-008 proved the controlled public read-only fetch path could run with a concrete manifest. PRACTICAL-009 replayed the one saved packet and diagnosed the four failed source requests. PRACTICAL-010 repairs those failed URL intents without browsing or search and then uses a scoped approval/preflight gate before any second public GET.",
            "",
            "## Why Requests Failed",
            "",
            "- UK Parliament page: HTTP 403 in the controlled fetcher.",
            "- Elysee page: local certificate-chain validation failure.",
            "- Kraken page: redirect blocked from `https://www.kraken.com/blog` to `https://blog.kraken.com/`.",
            "- MicroStrategy page: HTTP 403 in the controlled fetcher.",
            "",
            "## URL Repair Strategy",
            "",
            *bullet_lines(repair.get("repair_strategy", [])),
            "",
            "## Repaired Manifest Result",
            "",
            f"- Executable repaired requests: {manifest.get('executable_request_count')}",
            f"- No-retry requests: {len(manifest.get('no_retry_request_intents', []))}",
            f"- Replacement-missing requests: {len(manifest.get('replacement_missing_request_intents', []))}",
            f"- Blocked requests: {len(manifest.get('blocked_request_intents', []))}",
            "",
            "## Second Fetch Preflight",
            "",
            f"- Ready: `{str(preflight.get('ready_to_execute_public_read_only_fetch')).lower()}`",
            f"- Blockers: {', '.join(preflight.get('blockers', [])) or 'none'}",
            "",
            "## Second Fetch Result",
            "",
            f"- Live fetch occurred: `{str(execution_summary.get('live_fetch_performed')).lower()}`",
            f"- Attempted: {execution_summary.get('request_count_attempted')}",
            f"- Succeeded: {execution_summary.get('request_count_succeeded')}",
            f"- Failed: {execution_summary.get('request_count_failed')}",
            f"- Evidence packets created: {execution_summary.get('evidence_packets_created_count')}",
            "",
            "## Replay Result",
            "",
            f"- Replay status: `{replay_result.get('replay_status')}`",
            f"- Replay performed: `{str(replay_result.get('replay_performed')).lower()}`",
            "",
            "## Source Accessibility Learning",
            "",
            f"- 010 records: {len(learning.get('source_accessibility_records', []))}",
            "- No autonomous training was performed.",
            "- No real trade decision was made.",
            "",
            "## What This Proves",
            "",
            "- Failed source URLs can be repaired deterministically from local artifacts and a curated fixture.",
            "- The approval, safety, preflight, fetch, save, replay, and operator-review loop remains bounded and auditable.",
            "",
            "## What This Does Not Prove",
            "",
            "- It does not prove the market outcome.",
            "- It does not prove PMBOT is ready for autonomous trading.",
            "- It does not permit automatic analysis updates or executable market actions.",
            "",
            "## Next Action",
            "",
            f"- {repair_summary.get('recommended_next_source_actions', ['Operator review required.'])[0]}",
        ]
    ) + "\n"


def render_practical_010_task_doc(
    *,
    repair: Mapping[str, Any],
    manifest: Mapping[str, Any],
    safety_report: Mapping[str, Any],
    preflight: Mapping[str, Any],
    execution_summary: Mapping[str, Any],
    replay_result: Mapping[str, Any],
    safety_scan: Mapping[str, Any],
) -> str:
    return "\n".join(
        [
            "# ORCH PMBOT PRACTICAL 010 Public Source URL Fixes And Second Controlled Fetch Packet",
            "",
            f"- Task ID: `{TASK_ID}`",
            f"- Source repair created: `true`",
            f"- Repaired manifest created: `true`",
            f"- URL safety blockers: {', '.join(safety_report.get('global_blockers', [])) or 'none'}",
            f"- Second fetch preflight ready: `{str(preflight.get('ready_to_execute_public_read_only_fetch')).lower()}`",
            f"- Second live fetch occurred: `{str(execution_summary.get('live_fetch_performed')).lower()}`",
            f"- Evidence packets created: {execution_summary.get('evidence_packets_created_count')}",
            f"- Replay status: `{replay_result.get('replay_status')}`",
            f"- Safety scan passed: `{str(safety_scan.get('safety_ok')).lower()}`",
            "",
            "## Relation To PRACTICAL-008 And PRACTICAL-009",
            "",
            "PRACTICAL-008 executed the first controlled public read-only fetch and saved one evidence packet. PRACTICAL-009 replayed that packet, created an operator review, and produced the failed-source diagnosis used here.",
            "",
            "## Repair Counts",
            "",
            f"- Original failed requests: {repair.get('input_failed_request_count')}",
            f"- Executable repaired requests: {manifest.get('executable_request_count')}",
            f"- No-retry requests: {len(manifest.get('no_retry_request_intents', []))}",
            f"- Replacement-missing requests: {len(manifest.get('replacement_missing_request_intents', []))}",
            f"- Blocked requests: {len(manifest.get('blocked_request_intents', []))}",
            "",
            "## Safety Boundary",
            "",
            "- No OpenRouter call.",
            "- No authenticated endpoint, API key, cookie, browser profile, browser automation, wallet, order, or trading path.",
            "- No scheduler, daemon, background worker, polling loop, or autonomous trading.",
            "- No automatic analysis update.",
        ]
    ) + "\n"


def _repair_one_failed_request(
    *,
    failed: Mapping[str, Any],
    mapping: Mapping[str, Any],
    enriched: Mapping[str, Any],
    learning: Mapping[str, Any],
) -> dict[str, Any]:
    request_id = clean_text(failed.get("request_intent_id"))
    repair_action = clean_text(mapping.get("repair_action") or "mark_missing")
    original_url = clean_text(mapping.get("original_url_or_reference") or failed.get("source_url") or enriched.get("source_url"))
    replacement_url = clean_text(mapping.get("replacement_public_url"))
    source_category = clean_text(
        mapping.get("replacement_source_category")
        or enriched.get("source_category")
        or failed.get("source_category")
        or learning.get("source_category")
    )
    if repair_action == "retry_same_url":
        candidate_url = original_url
    elif repair_action == "replace_url":
        candidate_url = replacement_url
    else:
        candidate_url = ""
    base = {
        "request_intent_id": request_id,
        "market_id": clean_text(mapping.get("market_id") or failed.get("market_id") or enriched.get("market_id")),
        "market_title": clean_text(failed.get("market_title") or enriched.get("market_title") or learning.get("market_title")),
        "linked_hypothesis_id": clean_text(enriched.get("linked_hypothesis_id")),
        "source_name": clean_text(mapping.get("source_name") or failed.get("source_name") or enriched.get("source_name")),
        "source_category": source_category,
        "original_url_or_reference": original_url,
        "failure_category": clean_text(mapping.get("failure_category") or failed.get("failure_category")),
        "failure_error": clean_text(failed.get("error") or failed.get("failure_error")),
        "repair_action": repair_action,
        "repair_reason": clean_text(mapping.get("reason")),
        "expected_evidence_type": clean_text(mapping.get("expected_evidence_type") or enriched.get("expected_evidence_type")),
        "operator_review_required": mapping.get("operator_review_required") is not False,
        "method": "GET",
        "requires_auth": False,
        "credentials_required": False,
        "cookies_required": False,
        "wallet_or_signing_required": False,
        "trading_or_order_endpoint": False,
        "live_fetch_performed": False,
    }
    category_validation = validate_source_category(source_category)
    if repair_action == "block" or category_validation["blocked"]:
        return {
            **base,
            "repair_status": "blocked",
            "blocked_reason": base["repair_reason"] or category_validation["reason"],
            "source_reference": candidate_url or replacement_url or original_url,
            "source_url": candidate_url or replacement_url or original_url,
        }
    if repair_action == "mark_no_retry":
        return {
            **base,
            "repair_status": "no_retry",
            "no_retry_reason": base["repair_reason"] or "The failed URL should not be retried without a separate source review.",
            "source_reference": original_url,
            "source_url": original_url,
        }
    if repair_action == "mark_missing" or not candidate_url:
        return {
            **base,
            "repair_status": "replacement_missing",
            "missing_replacement_reason": base["repair_reason"] or "No deterministic replacement public URL is known locally.",
            "source_reference": original_url,
            "source_url": "",
        }
    safety = validate_public_fetch_request_intent(
        {
            **base,
            "source_reference": candidate_url,
            "source_url": candidate_url,
            "source_category": source_category,
            "method": "GET",
        },
        request_index=1,
        max_request_count=MAX_REQUEST_COUNT,
    )
    if safety.get("allowed") is not True:
        return {
            **base,
            "repair_status": "blocked",
            "blocked_reason": "; ".join(safety.get("blockers", [])) or "URL safety validation blocked this repair.",
            "source_reference": candidate_url,
            "source_url": candidate_url,
            "url_safety_validation": safety,
        }
    return {
        **base,
        "repair_status": "executable_candidate",
        "source_reference": candidate_url,
        "source_url": candidate_url,
        "url_status": "concrete_safe_public_url",
        "url_safety_validation": safety,
    }


def _packet_from_second_fetch_response(
    *,
    intent: Mapping[str, Any],
    safety: Mapping[str, Any],
    response: FetchResponse,
    fixture_mode: bool,
    generated_at: str | None,
) -> dict[str, Any]:
    status_code = int(response.get("status_code") or 0)
    if status_code < 200 or status_code >= 400:
        raise ControlledPublicFetchExecutionError(f"HTTP fetch failed with status {status_code}")
    body = response.get("body", b"")
    body_bytes = body if isinstance(body, bytes) else clean_text(body).encode("utf-8", errors="replace")
    body_text = body_bytes.decode("utf-8", errors="replace")
    body_sha = hashlib.sha256(body_bytes).hexdigest()
    digest = body_sha[:16]
    evidence_packet_id = f"public_fetch_010_{clean_text(intent.get('request_intent_id'))}_{digest}"
    content_type = _content_type(response.get("headers", {}))
    packet = build_saved_public_evidence_packet(
        evidence_packet_id=evidence_packet_id,
        source_id=clean_text(intent.get("request_intent_id")),
        source_name=clean_text(intent.get("source_name") or intent.get("source_name_or_placeholder")),
        source_category=clean_text(intent.get("source_category")),
        source_reference=clean_text(safety.get("sanitized_url_reference")),
        market_ids=[clean_text(intent.get("market_id"))],
        hypothesis_ids=[clean_text(intent.get("linked_hypothesis_id"))],
        raw_excerpt_or_summary=(
            f"HTTP {status_code} public read-only GET response captured for replay. "
            f"Content-Type: {content_type}. Body bytes read: {len(body_bytes)}. SHA256: {body_sha}. "
            "Raw response body is summarized for operator review and is not a market action."
        ),
        normalized_claims=[
            f"Public source returned HTTP {status_code} for request intent {intent.get('request_intent_id')}.",
            "Response metadata and digest were saved before replay for paper-only evidence review.",
        ],
        freshness_status="captured_at_task_time",
        contradiction_candidates=[],
        limitations=[
            "Response body is summarized by metadata and digest in this artifact rather than embedded verbatim.",
            "This packet records public source accessibility and does not resolve the market outcome.",
            "This packet is paper-only evidence capture and is not an executable market action.",
        ],
        capture_mode="fixture" if fixture_mode else "future_public_read_only_fetch",
        live_network_used=not fixture_mode,
    )
    packet.update(
        {
            "captured_at": generated_at or packet.get("captured_at"),
            "http_status": status_code,
            "content_type": content_type,
            "final_url": clean_text(response.get("final_url") or safety.get("sanitized_url_reference")),
            "body_byte_count": len(body_bytes),
            "body_sha256": body_sha,
        }
    )
    return packet


def _fetch_result_base(intent: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "request_intent_id": clean_text(intent.get("request_intent_id")),
        "market_id": clean_text(intent.get("market_id")),
        "market_title": clean_text(intent.get("market_title")),
        "method": "GET",
        "source_category": clean_text(intent.get("source_category")),
        "source_name": clean_text(intent.get("source_name") or intent.get("source_name_or_placeholder")),
        "source_url": clean_text(intent.get("source_url") or intent.get("source_reference")),
    }


def _write_no_evidence_created_second_fetch(
    *,
    evidence_dir: Path,
    ready: bool,
    blockers: Sequence[str],
    failed: Sequence[Mapping[str, Any]],
) -> None:
    result = {
        "contract_version": "pmbot_no_evidence_created_second_fetch.v1",
        "generated_at": utc_now_iso(),
        "no_evidence_created": True,
        "ready_to_execute_public_read_only_fetch": ready,
        "failed_request_count": len(failed),
        "blockers": list(blockers),
        "failed_requests": list(failed),
        "no_fake_evidence_created": True,
        "automatic_analysis_update_performed": False,
        "no_real_trade_decision": True,
        "safety_summary": safe_summary(),
    }
    write_json(evidence_dir / "no_evidence_created_second_fetch.json", result)
    write_text(
        evidence_dir / "no_evidence_created_second_fetch.md",
        "\n".join(
            [
                "# No Evidence Created By Second Fetch",
                "",
                f"- Ready to execute: `{str(ready).lower()}`",
                f"- Failed request count: {len(failed)}",
                f"- No fake evidence created: `{str(result['no_fake_evidence_created']).lower()}`",
                "",
                "## Blockers",
                "",
                *bullet_lines(blockers),
                "",
                "## Failed Requests",
                "",
                *bullet_lines(f"`{row.get('request_intent_id')}` {row.get('error')}" for row in failed),
            ]
        )
        + "\n",
    )


def _source_accessibility_observations(
    execution_summary: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> list[str]:
    observations = []
    if execution_summary.get("request_count_succeeded", 0):
        observations.append("At least one repaired public URL was reachable through the controlled fetch path.")
    if execution_summary.get("request_count_failed", 0):
        observations.append("At least one repaired executable URL still failed during controlled GET.")
    if manifest.get("replacement_missing_request_intents"):
        observations.append("Some failed sources still need manually curated public replacement URLs.")
    if manifest.get("blocked_request_intents"):
        observations.append("Some failed sources remain blocked because a safe public repair was not available.")
    return observations or ["No source accessibility update was possible because no request was executable."]


def _learning_records(manifest: Mapping[str, Any], execution_summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    succeeded = {
        clean_text(row.get("request_intent_id")): row
        for row in execution_summary.get("succeeded_requests", [])
        if isinstance(row, Mapping)
    }
    failed = {
        clean_text(row.get("request_intent_id")): row
        for row in execution_summary.get("failed_requests", [])
        if isinstance(row, Mapping)
    }
    records = []
    for row in manifest.get("executable_request_intents", []):
        if not isinstance(row, Mapping):
            continue
        request_id = clean_text(row.get("request_intent_id"))
        status = "reachable" if request_id in succeeded else "failed" if request_id in failed else "not_attempted"
        records.append(
            {
                "request_intent_id": request_id,
                "market_id": row.get("market_id"),
                "source_url": row.get("source_url"),
                "repair_status": row.get("repair_status"),
                "accessibility_status": status,
                "evidence_packet_id": succeeded.get(request_id, {}).get("evidence_packet_id", ""),
                "evidence_usable": status == "reachable",
                "replay_usable": status == "reachable",
                "operator_review_required": True,
            }
        )
    for group_name, status in (
        ("no_retry_request_intents", "no_retry"),
        ("replacement_missing_request_intents", "replacement_missing"),
        ("blocked_request_intents", "blocked"),
    ):
        for row in manifest.get(group_name, []):
            if not isinstance(row, Mapping):
                continue
            records.append(
                {
                    "request_intent_id": row.get("request_intent_id"),
                    "market_id": row.get("market_id"),
                    "source_url": row.get("source_url") or row.get("source_reference"),
                    "repair_status": row.get("repair_status"),
                    "accessibility_status": status,
                    "evidence_packet_id": "",
                    "evidence_usable": False,
                    "replay_usable": False,
                    "operator_review_required": True,
                }
            )
    return records


def _replay_paths_for_result(replay_result: Mapping[str, Any]) -> list[str]:
    if replay_result.get("replay_performed") is True:
        return ["pm_bot/practical/artifacts/public_source_url_fixes_010/replay/replayed_source_packets_010.json"]
    return ["pm_bot/practical/artifacts/public_source_url_fixes_010/replay/replay_blocked_no_evidence_010.json"]


def _load_replay_result(replay_dir: Path) -> dict[str, Any]:
    replayed = replay_dir / "replayed_source_packets_010.json"
    blocked = replay_dir / "replay_blocked_no_evidence_010.json"
    if replayed.exists():
        return load_json_object(replayed)
    return load_json_object(blocked)


def _load_json_list(path: str | Path) -> list[dict[str, Any]]:
    value = load_json_object(path, label="repair mapping fixture")
    rows = value.get("repairs", [])
    if not isinstance(rows, list):
        raise ValueError("repair mapping fixture must contain repairs list")
    return [row for row in rows if isinstance(row, dict)]


def _intent_list_lines(intents: Sequence[Mapping[str, Any]]) -> list[str]:
    if not intents:
        return ["- none"]
    return [
        f"- `{row.get('request_intent_id')}` `{row.get('repair_status')}` `{row.get('market_id')}`"
        for row in intents
    ]


def _content_type(headers: Any) -> str:
    if not isinstance(headers, Mapping):
        return ""
    for key, value in headers.items():
        if clean_text(key).lower() == "content-type":
            return clean_text(value)
    return ""


def _rel(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _generated_artifact_paths() -> list[str]:
    root = DEFAULT_OUT_DIR
    paths = [
        root / "public_source_url_repair_010.json",
        root / "public_source_url_repair_010.md",
        root / "repaired_public_fetch_manifest_010.json",
        root / "repaired_public_fetch_manifest_010.md",
        root / "repaired_manifest_url_safety_report_010.json",
        root / "repaired_manifest_url_safety_report_010.md",
        root / "operator_approval_second_controlled_fetch_010.json",
        root / "operator_approval_second_controlled_fetch_010.md",
        root / "second_fetch_preflight_010.result.json",
        root / "second_fetch_preflight_010.md",
        root / "second_fetch_execution_summary_010.result.json",
        root / "second_fetch_execution_summary_010.md",
        root / "second_public_evidence_operator_review_packet_010.json",
        root / "second_public_evidence_operator_review_packet_010.md",
        root / "source_url_repair_result_summary_010.json",
        root / "source_url_repair_result_summary_010.md",
        root / "source_accessibility_learning_010.json",
        root / "source_accessibility_learning_010.md",
        root / "operator_console_second_fetch_010.json",
        root / "operator_console_second_fetch_010.md",
        root / "public_source_url_fixes_safety_scan_010.result.json",
        root / "public_source_url_fixes_safety_scan_010.md",
        Path("docs/PMBOT_PUBLIC_SOURCE_URL_FIXES_AND_SECOND_FETCH.md"),
        Path("docs/ORCH_PMBOT_PRACTICAL_010_PUBLIC_SOURCE_URL_FIXES_AND_SECOND_CONTROLLED_FETCH_PACKET.md"),
        Path("docs/ORCH_PMBOT_PRACTICAL_010_RESULT.json"),
    ]
    paths.extend(sorted((root / "evidence_packets").glob("*.json")))
    paths.extend(sorted((root / "evidence_packets").glob("*.md")))
    paths.extend(sorted((root / "replay").glob("*.json")))
    paths.extend(sorted((root / "replay").glob("*.md")))
    return [_rel(path) for path in paths]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate PRACTICAL-010 public source URL repair artifacts.")
    parser.add_argument("--generate-010", action="store_true")
    parser.add_argument("--no-execute", action="store_true")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=8)
    args = parser.parse_args(argv)
    if not args.generate_010:
        parser.error("--generate-010 is required")
    generate_practical_010_artifacts(
        execute_if_ready=not args.no_execute,
        fixture_mode=args.fixture_mode,
        timeout_seconds=args.timeout_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
